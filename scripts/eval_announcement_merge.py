"""Sweep the day-gated semantic merge threshold over labelled announcement pairs.

Known gap (measured on the 3-pair fixture, 2026-09-14): raw announcement-title
similarity for a real same-day duplicate can be as low as ~0.40 — well under
announcement_merge_sim (0.72) — because raw text carries union-name and phrasing
noise that the design spec's LLM-summary-based similarity measurements didn't.
Recall on this fixture is 0.5 at every threshold from 0.60-0.90; the fixture has
no same-day/different-event pair, so it can't justify lowering the threshold
without risking false positives. Seed-time misses aren't permanent: Task 7's
post-enrichment `_link_to_announcement` pass gets a second chance to merge via
place/national-scope agreement once both sides are LLM-classified. Widening this
fixture with real pairs (including a same-day/different-event case) from the
live DB is the natural next step before retuning the threshold."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from nlp.embeddings import embed_query

_FIXTURE = Path(__file__).parent.parent / "tests" / "reactions" / "fixtures" / "merge_pairs.json"


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def _merges(pair: dict, threshold: float, day_gate: bool) -> bool:
    if day_gate and pair["day_a"] != pair["day_b"]:
        return False
    ea = np.asarray(embed_query(pair["a"]), dtype=np.float32)
    eb = np.asarray(embed_query(pair["b"]), dtype=np.float32)
    return _cos(ea, eb) >= threshold


def evaluate(pairs: list[dict], threshold: float, day_gate: bool = True) -> dict:
    tp = fp = fn = tn = 0
    for p in pairs:
        pred = _merges(p, threshold, day_gate)
        truth = bool(p["same_event"])
        tp += pred and truth
        fp += pred and not truth
        fn += (not pred) and truth
        tn += (not pred) and not truth
    prec = tp / (tp + fp) if (tp + fp) else 1.0
    rec = tp / (tp + fn) if (tp + fn) else 1.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": prec, "recall": rec}


def sweep(pairs: list[dict], thresholds: list[float]) -> dict[float, dict]:
    return {t: evaluate(pairs, t) for t in thresholds}


def main() -> None:
    pairs = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    print(f"{'thr':>5}  {'prec':>5}  {'rec':>5}  tp fp fn tn")
    for t, m in sweep(pairs, [round(0.60 + 0.02 * i, 2) for i in range(16)]).items():
        print(f"{t:>5.2f}  {m['precision']:>5.2f}  {m['recall']:>5.2f}  "
              f"{m['tp']} {m['fp']} {m['fn']} {m['tn']}")


if __name__ == "__main__":
    main()
