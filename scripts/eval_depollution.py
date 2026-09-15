"""Evaluate the date-coherence split over the labelled c4f30e75 article set.

Reports whether the 17/9 Cyprus block peels off the 16/9 primary, the
no-article-in-two-groups invariant, and a min_bucket sweep. Mirrors
scripts/eval_announcement_merge.py."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import numpy as np

from nlp.date_split import split_by_event_day
from nlp.event_dates import resolve_event_day

_FIXTURE = Path(__file__).parent.parent / "tests" / "nlp" / "fixtures" / "depollution_c4f30e75.jsonl"
_V = np.ones(768, dtype=np.float32)


def _load(path: Path = _FIXTURE) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def evaluate(rows: list[dict], min_bucket: int, tolerance_days: int = 0) -> dict:
    arts: list[tuple[str, np.ndarray, date | None]] = []
    gold: dict[str, str | None] = {}
    for r in rows:
        pub = datetime.fromisoformat(r["published_at"].replace("Z", "+00:00"))
        ed = resolve_event_day(r["title"], r.get("body_snippet"), pub)
        arts.append((r["id"], _V, ed.day if ed else None))
        gold[r["id"]] = r.get("gold_event_day")

    groups = split_by_event_day(arts, min_bucket=min_bucket, tolerance_days=tolerance_days)

    seen: set[str] = set()
    cross = 0
    for g in groups:
        for aid in g:
            if aid in seen:
                cross += 1
            seen.add(aid)

    # Cyprus peeled == the 17/9-gold ids share a group that holds no 16/9-gold id.
    cy = {aid for aid, d in gold.items() if d == "2026-09-17"}
    g16 = {aid for aid, d in gold.items() if d == "2026-09-16"}
    cyprus_peeled = bool(cy) and any(
        cy & set(g) and not (g16 & set(g)) for g in groups
    )
    return {"n_groups": len(groups), "cross_group_articles": cross, "cyprus_peeled": cyprus_peeled}


def sweep(rows: list[dict], buckets: list[int]) -> dict[int, dict]:
    return {b: evaluate(rows, b) for b in buckets}


def main() -> None:
    rows = _load()
    print(f"{'min_bucket':>10}  groups  cross  cyprus_peeled")
    for b, m in sweep(rows, [2, 3, 4, 5]).items():
        print(f"{b:>10}  {m['n_groups']:>6}  {m['cross_group_articles']:>5}  {m['cyprus_peeled']}")


if __name__ == "__main__":
    main()
