"""Geocoding eval vs events.jsonl + event_precision.jsonl:
  - foreign-detection precision/recall (is_foreign)
  - median distance error (km)
  - event-precision: % of detected 'events' that are real social reactions
Runs the real enrich_event_llm() + resolve_locations() (needs Nominatim + LLM available)."""
from __future__ import annotations

import asyncio
import statistics
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).parent.parent))
from enrich.config import settings  # noqa: E402
from enrich.enrich_llm import enrich_event_llm  # noqa: E402
from enrich.geocode import resolve_locations  # noqa: E402
from enrich.nli import NOISE_GATE_THRESHOLD, noise_gate_score  # noqa: E402
from scripts.gold_common import (  # noqa: E402
    binary_prf,
    haversine_km,
    load_jsonl,
)


def _first(v):
    return v[0] if isinstance(v, list) else v


async def main() -> None:
    events = [
        r for r in load_jsonl(Path("tests/fixtures/gold/events.jsonl"))
        if r.get("is_event")
    ]
    negatives = load_jsonl(Path("tests/fixtures/gold/event_precision.jsonl"))

    # event-precision (detector quality): real / (real + non-events sampled)
    ep_tp = ep_fp = ep_fn = 0
    for r in events + negatives:
        gtext = " ".join(r["article_titles"]) + " " + " ".join(r["article_bodies"])
        kept = noise_gate_score(gtext) >= NOISE_GATE_THRESHOLD
        gold_real = bool(r.get("is_event"))
        if kept and gold_real:
            ep_tp += 1
        elif kept and not gold_real:
            ep_fp += 1
        elif not kept and gold_real:
            ep_fn += 1
    ep = binary_prf(ep_tp, ep_fp, ep_fn)
    print(
        f"[geocode] event-precision P={ep['precision']:.3f} R={ep['recall']:.3f} "
        f"F1={ep['f1']:.3f} (tp={ep_tp} fp={ep_fp} fn={ep_fn}, "
        f"real={len(events)} non-events={len(negatives)})"
    )


    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    f_tp = f_fp = f_fn = 0
    dist_errors: list[float] = []
    async with session_factory() as session:
        for r in events:
            enr = enrich_event_llm(
                article_titles=r["article_titles"],
                article_bodies=r["article_bodies"],
                n_sources=len(r["article_titles"]),
                reference_date=r.get("published_at"),
            )
            if enr is None:
                continue
            results = await resolve_locations(
                enr.locations, national=enr.is_national, session=session
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
                dist_errors.append(
                    haversine_km(
                        primary.lat,
                        primary.lon,
                        _first(r["true_lat"]),
                        _first(r["true_lon"]),
                    )
                )
    await engine.dispose()
    fm = binary_prf(f_tp, f_fp, f_fn)
    print(
        f"[geocode] foreign P={fm['precision']:.3f} R={fm['recall']:.3f} "
        f"F1={fm['f1']:.3f}"
    )
    if dist_errors:
        print(
            f"[geocode] median_distance_error_km={statistics.median(dist_errors):.1f} "
            f"(n={len(dist_errors)})"
        )


if __name__ == "__main__":
    asyncio.run(main())
