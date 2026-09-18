# -*- coding: utf-8 -*-
"""Merge a segment-level ASR timeline with whisper word-level times.

ASR JSON (e.g. mediakit-cli video asr-subtitles result, may carry UTF-8 BOM):
    {"duration": <s>, "subtitles": [{"start_time": <s>, "end_time": <s>, "subtitle_text": "..."}]}

Usage:
    python merge_timeline.py <asr_json> <words_json> <out_json>

Output JSON: {"duration": <s>, "segments": [{"text","start","end","words":[{"w","s","e"}]}]}
Requires: pip install zhconv
"""
import argparse
import json
import sys

from zhconv import convert


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("asr_json", help="segment-level ASR timeline (utf-8-sig read)")
    ap.add_argument("words_json", help="whisper word-level transcription output")
    ap.add_argument("out_json", help="merged timeline output path")
    args = ap.parse_args()

    with open(args.asr_json, encoding="utf-8-sig") as f:
        byted = json.load(f)
    with open(args.words_json, encoding="utf-8") as f:
        whip = json.load(f)

    # global ordered word stream from whisper (zh-tw -> zh-cn)
    gwords = []
    for ws in whip["segments"]:
        for w in ws.get("words", []):
            wt = convert(w["w"].strip(), "zh-cn")
            if wt:
                gwords.append({"w": wt, "s": w["s"], "e": w["e"]})
    gwords.sort(key=lambda x: x["s"])

    EPS = 0.02
    final = []
    for b in byted["subtitles"]:
        lo, hi = b["start_time"], b["end_time"]
        words = [
            w for w in gwords
            if w["s"] < hi - 1e-6 and w["e"] > lo + EPS and w["s"] < hi - EPS
        ]
        final.append({"text": b["subtitle_text"].strip(), "start": lo, "end": hi, "words": words})

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump({"duration": byted["duration"], "segments": final}, f, ensure_ascii=False, indent=1)

    empty = [s["text"] for s in final if not s["words"]]
    print("segments=%d empty_words=%d" % (len(final), len(empty)), file=sys.stderr)
    for t in empty:
        print("EMPTY:", t, file=sys.stderr)


if __name__ == "__main__":
    main()
