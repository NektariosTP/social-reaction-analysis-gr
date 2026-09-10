"""Temporal-extraction eval vs tests/fixtures/gold/temporal.jsonl:
  - has-date precision/recall/F1 (did we emit a date iff gold has one)
  - date-exact accuracy (day match among records where both have a date)
  - median day-offset error (|predicted - gold| in days, over agreed-date records)
Runs the real enrich_event_llm() with each record's published_at as reference_date
(needs an LLM available)."""
from __future__ import annotations

import os
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from enrich.enrich_llm import enrich_event_llm, parse_event_date  # noqa: E402
from scripts.gold_common import binary_prf, load_jsonl  # noqa: E402

# Groq on_demand free tier caps at 12k tokens/min; each enrich_event_llm call
# burns ~1.5k tokens, so a burst of records trips the TPM limit and drops a
# result (counted as a false negative). Space calls out to keep the run clean.
_THROTTLE_SECONDS = float(os.getenv("EVAL_THROTTLE_SECONDS", "5"))


def main() -> None:
    records = load_jsonl(Path("tests/fixtures/gold/temporal.jsonl"))

    tp = fp = fn = 0
    exact_hits = 0
    exact_total = 0
    offsets: list[int] = []

    for i, r in enumerate(records):
        if i:
            time.sleep(_THROTTLE_SECONDS)
        gold_raw = r.get("true_event_date")
        gold = parse_event_date(gold_raw) if gold_raw else None

        result = enrich_event_llm(
            article_titles=r["article_titles"],
            article_bodies=r["article_bodies"],
            n_sources=len(r["article_titles"]),
            reference_date=r.get("published_at"),
        )
        pred = parse_event_date(result.event_date) if result and result.event_date else None

        # has-date confusion matrix
        if pred is not None and gold is not None:
            tp += 1
        elif pred is not None and gold is None:
            fp += 1
        elif pred is None and gold is not None:
            fn += 1

        # date accuracy + offset among agreed-date records
        if pred is not None and gold is not None:
            exact_total += 1
            offset = abs((pred.date() - gold.date()).days)
            offsets.append(offset)
            if offset == 0:
                exact_hits += 1

    prf = binary_prf(tp, fp, fn)
    exact_acc = exact_hits / exact_total if exact_total else 0.0
    median_offset = statistics.median(offsets) if offsets else float("nan")

    print(
        f"[temporal] has-date P={prf['precision']:.3f} R={prf['recall']:.3f} "
        f"F1={prf['f1']:.3f} (tp={tp} fp={fp} fn={fn})"
    )
    print(f"[temporal] date-exact accuracy={exact_acc:.3f} ({exact_hits}/{exact_total})")
    print(f"[temporal] median day-offset error={median_offset} (n={len(offsets)})")


if __name__ == "__main__":
    main()
