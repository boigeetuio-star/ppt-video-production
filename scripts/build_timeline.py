# -*- coding: utf-8 -*-
"""Build word-level page bindings for a HyperFrames course-video composition.

Maps every page switch and every content unit to the start time of a spoken
word, snapped to frame boundaries (30fps), so nothing appears before it is
spoken.

Usage:
    python build_timeline.py --dump-words <timeline_final.json> [--limit 80]
    python build_timeline.py <timeline_final.json> <pages.json> <out_json>

pages.json shape:
{
  "fps": 30,
  "duration": 102.54,            // optional; falls back to timeline duration
  "pages": [
    {
      "id": "p01",
      "start_time": 0.2,         // optional; overrides word matching for this page
      "word": "同样",             // bind page switch to this spoken word/phrase
      "min_time": 0,             // optional; search this page's word only at s >= min_time
      "units": [
        {"id": "t", "word": "样"},             // content unit appears at this word (inside page window)
        {"id": "k", "time": 1.1}               // or give an absolute time directly
      ]
    },
    ...
  ]
}

Matching: exact word equality first, then word contained in the phrase, then
phrase contained in the word. For each page the search starts after the
previous page's matched word (and after min_time when given), so words that
occur earlier in the audio do not steal a later page's binding.

Out JSON: {"fps", "duration", "pages": {id: {"start","duration","units": {id: seconds}}}}
Also prints a human-readable binding table.
"""
import argparse
import json
import math
import sys


def load_words(timeline):
    words = []
    for seg in timeline["segments"]:
        for w in seg.get("words", []):
            wt = w["w"].strip()
            if wt:
                words.append({"w": wt, "s": w["s"], "e": w["e"]})
    words.sort(key=lambda x: x["s"])
    return words


def match_rank(w, q):
    """0 = exact, 1 = word is part of phrase, 2 = phrase is part of word, -1 = no match."""
    if w == q:
        return 0
    if w in q:
        return 1
    if q in w:
        return 2
    return -1


def find_word(words, lo, query, min_s=None):
    """First word at index >= lo (and s >= min_s) matching query; returns (index, word)."""
    q = query.strip()
    for i in range(lo, len(words)):
        wd = words[i]
        if min_s is not None and wd["s"] < min_s:
            continue
        r = match_rank(wd["w"], q)
        if r >= 0:
            return i, wd
    return None, None


def snap(t, fps):
    return math.ceil(t * fps) / fps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline_json", help="merged timeline (merge_timeline.py output)")
    ap.add_argument("pages_json", nargs="?", help="page plan with word bindings")
    ap.add_argument("out_json", nargs="?", help="binding table output path")
    ap.add_argument("--dump-words", action="store_true", help="print the global word stream and exit")
    ap.add_argument("--limit", type=int, default=80, help="words to print with --dump-words")
    args = ap.parse_args()

    with open(args.timeline_json, encoding="utf-8") as f:
        timeline = json.load(f)
    words = load_words(timeline)

    if args.dump_words:
        for i, wd in enumerate(words[: args.limit]):
            print("%4d %-6s %.3f" % (i, wd["w"], wd["s"]))
        print("... total words = %d" % len(words))
        return

    if not args.pages_json or not args.out_json:
        ap.error("pages_json and out_json are required unless --dump-words is used")
    with open(args.pages_json, encoding="utf-8") as f:
        plan = json.load(f)

    fps = plan.get("fps", 30)
    total = plan.get("duration", timeline.get("duration"))

    pages = []
    lo = 0
    errors = []
    for pg in plan["pages"]:
        pid = pg["id"]
        if pg.get("start_time") is not None:
            start = snap(pg["start_time"], fps)
        else:
            i, w = find_word(words, lo, pg["word"], pg.get("min_time"))
            if w is None:
                errors.append("page %s: start word %r not found (after index %d)"
                              % (pid, pg["word"], lo))
                start, lo = 0.0, lo
            else:
                start, lo = snap(w["s"], fps), i + 1
        pages.append({"id": pid, "start": start, "units": pg.get("units", []), "lo": lo})

    result = {"fps": fps, "duration": total, "pages": {}}
    for idx, pg in enumerate(pages):
        end = pages[idx + 1]["start"] if idx + 1 < len(pages) else total
        dur = round(end - pg["start"], 6)

        lo = pg["lo"]
        units = {}
        win_lo, win_hi = pg["start"], end
        # unit words are searched independently inside this page's window
        # (units may be listed in visual order, not chronological word order)
        wi = next((i for i in range(lo, len(words)) if words[i]["s"] >= win_lo - 1e-6), len(words))
        for u in pg["units"]:
            if u.get("time") is not None:
                t = snap(u["time"], fps) - pg["start"]
                if t < -1e-6:
                    errors.append("page %s unit %s: time %.3f before page start %.3f"
                                  % (pg["id"], u["id"], u["time"], pg["start"]))
                    continue
                units[u["id"]] = round(t, 6)
                continue
            i, w = find_word(words, wi, u["word"])
            if w is None:
                errors.append("page %s unit %s: word %r not found" % (pg["id"], u["id"], u["word"]))
                continue
            if not (win_lo - 1e-6 <= w["s"] < win_hi + 1e-6):
                errors.append("page %s unit %s: word %r at %.3fs outside page window [%.3f, %.3f)"
                              % (pg["id"], u["id"], u["word"], w["s"], win_lo, win_hi))
                continue
            units[u["id"]] = round(snap(w["s"], fps) - pg["start"], 6)

        result["pages"][pg["id"]] = {"start": pg["start"], "duration": dur, "units": units}

    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        sys.exit(1)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    print("fps=%d total=%.2f pages=%d" % (fps, total, len(pages)))
    for pid, p in result["pages"].items():
        us = " ".join("%s@%.4f" % (k, v) for k, v in p["units"].items())
        print("%s start=%.4f dur=%.4f | %s" % (pid, p["start"], p["duration"], us))


if __name__ == "__main__":
    main()
