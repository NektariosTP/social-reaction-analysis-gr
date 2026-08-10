"""Sweep the NLI noise-gate threshold against events.jsonl (real) + event_precision.jsonl
(non-events) and report the operating point that maximizes F1. Do NOT hardcode the
threshold elsewhere; copy the winner into enrich/nli.py NOISE_GATE_THRESHOLD."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from enrich.nli import noise_gate_score  # noqa: E402
from scripts.gold_common import binary_prf, load_jsonl  # noqa: E402


def main() -> None:
    events = [r for r in load_jsonl(Path("tests/fixtures/gold/events.jsonl")) if r.get("is_event")]
    negatives = load_jsonl(Path("tests/fixtures/gold/event_precision.jsonl"))
    scored = []
    for r in events + negatives:
        text = " ".join(r["article_titles"]) + " " + " ".join(r["article_bodies"])
        scored.append((noise_gate_score(text), bool(r.get("is_event"))))

    best = (0.0, -1.0)  # (threshold, f1)
    for t in [round(0.30 + 0.05 * i, 2) for i in range(13)]:  # 0.30..0.90
        tp = sum(1 for s, gold in scored if s >= t and gold)
        fp = sum(1 for s, gold in scored if s >= t and not gold)
        fn = sum(1 for s, gold in scored if s < t and gold)
        m = binary_prf(tp, fp, fn)
        print(f"threshold={t:.2f}  P={m['precision']:.3f}  R={m['recall']:.3f}  "
              f"F1={m['f1']:.3f}  (tp={tp} fp={fp} fn={fn})")
        if m["f1"] > best[1]:
            best = (t, m["f1"])
    print(f"\nBEST threshold={best[0]:.2f} F1={best[1]:.3f} → set enrich/nli.py NOISE_GATE_THRESHOLD")


if __name__ == "__main__":
    main()
