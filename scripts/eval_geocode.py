"""Geocoding eval vs events.jsonl + event_precision.jsonl:
  - foreign-detection precision/recall (is_foreign)
  - region_code accuracy (on coord'd real domestic events)
  - median distance error (km)
  - event-precision: % of detected 'events' that are real social reactions
Runs the real geocode_event() (needs Nominatim + LLM available)."""
from __future__ import annotations

import asyncio
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from enrich.geocode import geocode_event  # noqa: E402
from scripts.gold_common import (  # noqa: E402
    binary_prf,
    haversine_km,
    load_jsonl,
)


def _first(v):
    return v[0] if isinstance(v, list) else v


def _as_set(v) -> set:
    if v is None:
        return set()
    return set(v) if isinstance(v, list) else {v}


async def main() -> None:
    events = [
        r for r in load_jsonl(Path("tests/fixtures/gold/events.jsonl"))
        if r.get("is_event")
    ]
    negatives = load_jsonl(Path("tests/fixtures/gold/event_precision.jsonl"))

    # event-precision (detector quality): real / (real + non-events sampled)
    ep = binary_prf(tp=len(events), fp=len(negatives), fn=0)
    print(
        f"[geocode] event-precision={ep['precision']:.3f} "
        f"(real={len(events)} non-events={len(negatives)})"
    )

    f_tp = f_fp = f_fn = 0
    region_hits = region_total = 0
    dist_errors: list[float] = []
    for r in events:
        results = await geocode_event(
            summary_el=" ".join(r["article_bodies"])[:800],
            article_titles=r["article_titles"],
        )
        primary = results[0] if results else None
        pred_foreign = primary is not None and getattr(primary, "is_foreign", False)
        gold_foreign = bool(r.get("is_foreign"))
        if pred_foreign and gold_foreign:
            f_tp += 1
        elif pred_foreign and not gold_foreign:
            f_fn += 1  # missed a domestic event
        elif not pred_foreign and gold_foreign:
            f_fp += 1  # wrongly mapped a foreign event
        if primary and not gold_foreign and r.get("true_lat") is not None:
            # Multi-location gold events carry a list of regions; a primary that
            # lands in ANY of them is correct (not just the first-listed one).
            if getattr(primary, "region_code", None) in _as_set(
                r["true_region_code"]
            ):
                region_hits += 1
            region_total += 1
            dist_errors.append(
                haversine_km(
                    primary.lat,
                    primary.lon,
                    _first(r["true_lat"]),
                    _first(r["true_lon"]),
                )
            )
    fm = binary_prf(f_tp, f_fp, f_fn)
    print(
        f"[geocode] foreign P={fm['precision']:.3f} R={fm['recall']:.3f} "
        f"F1={fm['f1']:.3f}"
    )
    acc = region_hits / region_total if region_total else 0.0
    print(f"[geocode] region_accuracy={acc:.3f} ({region_hits}/{region_total})")
    if dist_errors:
        print(
            f"[geocode] median_distance_error_km={statistics.median(dist_errors):.1f} "
            f"(n={len(dist_errors)})"
        )


if __name__ == "__main__":
    asyncio.run(main())
