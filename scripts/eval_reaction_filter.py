"""Accuracy report: keyword-filter variants + date extraction vs gold (no stance).

Usage: uv run python -m scripts.eval_reaction_filter [path/to/gold.jsonl]
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

from reactions.dates import extract_event_datetime
from reactions.filters import FILTER_VARIANTS, passes_filter
from scripts.gold_common import binary_prf, load_jsonl

_GOLD_DEFAULT = Path("tests/fixtures/reactions_gold.jsonl")


def score_variant(gold: list[dict], keywords: list[str]) -> dict:
    tp = fp = fn = 0
    for row in gold:
        pred = passes_filter(row["text"], keywords)
        truth = bool(row["relevant"])
        if pred and truth:
            tp += 1
        elif pred and not truth:
            fp += 1
        elif not pred and truth:
            fn += 1
    return {"tp": tp, "fp": fp, "fn": fn, **binary_prf(tp, fp, fn)}


def _date_accuracy(gold: list[dict]) -> float:
    labeled = [r for r in gold if r.get("event_date")]
    if not labeled:
        return 0.0
    hits = 0
    for r in labeled:
        got = extract_event_datetime(r["text"])
        hits += got is not None and got.when.date().isoformat() == r["event_date"]
    return hits / len(labeled)


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else _GOLD_DEFAULT
    gold = load_jsonl(path)
    print(f"# Reaction filter scorecard ({len(gold)} labeled items)\n")
    print("| Variant | P | R | F1 | TP | FP | FN |")
    print("|---|---|---|---|---|---|---|")
    for name, kws in FILTER_VARIANTS.items():
        s = score_variant(gold, kws)
        print(f"| {name} | {s['precision']:.2f} | {s['recall']:.2f} | {s['f1']:.2f} "
              f"| {s['tp']} | {s['fp']} | {s['fn']} |")

    by_source: dict[str, list[dict]] = defaultdict(list)
    for r in gold:
        by_source[r.get("source_org", "?")].append(r)
    print("\n## Per-source (broad variant)\n")
    print("| Source | P | R | F1 | n |")
    print("|---|---|---|---|---|")
    for src, rows in sorted(by_source.items()):
        s = score_variant(rows, FILTER_VARIANTS["broad"])
        print(f"| {src} | {s['precision']:.2f} | {s['recall']:.2f} | {s['f1']:.2f} | {len(rows)} |")

    print(f"\n**Date-extraction exact-match:** {_date_accuracy(gold):.2f}")


if __name__ == "__main__":
    main()
