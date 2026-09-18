# -*- coding: utf-8 -*-
"""faster-whisper word-level transcription (CPU).

Usage:
    python transcribe_words.py <audio> <out_json> [--model small] [--language zh]

Output JSON: {"language": ..., "segments": [{"text","s","e","words":[{"w","s","e"}]}]}
Requires: pip install faster-whisper
"""
import argparse
import json
import time

from faster_whisper import WhisperModel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", help="path to the voiceover audio file")
    ap.add_argument("out", help="output JSON path")
    ap.add_argument("--model", default="small")
    ap.add_argument("--language", default="zh")
    args = ap.parse_args()

    t0 = time.time()
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    print("model loaded %.1fs" % (time.time() - t0), file=__import__("sys").stderr)

    segments, info = model.transcribe(
        args.audio,
        language=args.language,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=300),
    )

    result = {"language": info.language, "segments": []}
    for seg in segments:
        words = [
            {"w": w.word, "s": round(w.start, 3), "e": round(w.end, 3)}
            for w in (seg.words or [])
        ]
        result["segments"].append({
            "text": seg.text.strip(),
            "s": round(seg.start, 3),
            "e": round(seg.end, 3),
            "words": words,
        })

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print("DONE segments=%d  %.1fs" % (len(result["segments"]), time.time() - t0), file=__import__("sys").stderr)


if __name__ == "__main__":
    main()
