"""Score the production geocoding path against curator-verified event locations.

The geocoding analogue of ``eval_classify_prod.py``. Each curated event's stored
``primary_location`` is human-verified ground truth (approved or corrected by the
curator); a NULL location is a deliberate abstention (venueless / national action).
This re-runs the exact production path — ``enrich_event_llm`` to extract place
mentions, then ``resolve_locations`` (public Nominatim + in-process Greek geofence,
no DB session needed) — and reports, over N runs:

  - localisation-decision accuracy: did it locate-vs-abstain the same way the curator did?
  - median distance error (km) on events both located (haversine to the curated point);
  - the error breakdown (missed a location / fabricated one for a venueless event).

Usage:
    uv run python -m scripts.eval_geocode_prod <export.jsonl> [runs]
"""
from __future__ import annotations

import asyncio
import os
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from enrich.enrich_llm import enrich_event_llm  # noqa: E402
from enrich.geocode import detect_national_scope, resolve_locations  # noqa: E402
from scripts.gold_common import haversine_km, load_jsonl  # noqa: E402

_DELAY = float(os.environ.get("EVAL_DELAY", "40"))
_RETRY_WAIT = float(os.environ.get("EVAL_RETRY_WAIT", "35"))


def _first(v):
    return v[0] if isinstance(v, list) else v


async def _predict_point(r: dict):
    """Return (located: bool, lat, lon) from the production path, or None on LLM failure."""
    for attempt in (1, 2):
        enr = enrich_event_llm(
            article_titles=r["article_titles"],
            article_bodies=r["article_bodies"],
            n_sources=len(r["article_titles"]),
            reference_date=r.get("published_at"),
        )
        if enr is not None:
            break
        if attempt == 2:
            return None
        time.sleep(_RETRY_WAIT)
    full_text = " ".join(r["article_titles"]) + " " + " ".join(r["article_bodies"])
    national = bool(enr.is_national or detect_national_scope(full_text))
    results = await resolve_locations(enr.locations, national=national, session=None)
    primary = results[0] if results else None
    if primary is None or getattr(primary, "is_foreign", False) or primary.lat is None:
        return (False, None, None)
    return (True, primary.lat, primary.lon)


async def _score_once(recs: list[dict]) -> tuple[int, int, list[float], int, int, int]:
    correct = ok = 0
    dists: list[float] = []
    missed = fabricated = 0  # gold-located→pred-abstain ; gold-abstain→pred-located
    for i, r in enumerate(recs):
        if i:
            time.sleep(_DELAY)
        pred = await _predict_point(r)
        if pred is None:
            continue
        ok += 1
        pred_located, plat, plon = pred
        gold_located = r.get("true_lat") is not None
        if pred_located == gold_located:
            correct += 1
        if gold_located and not pred_located:
            missed += 1
        if pred_located and not gold_located:
            fabricated += 1
        if gold_located and pred_located:
            dists.append(haversine_km(plat, plon, _first(r["true_lat"]), _first(r["true_lon"])))
    return correct, ok, dists, missed, fabricated, len(recs)


async def main() -> None:
    if len(sys.argv) < 2:
        print("usage: eval_geocode_prod <export.jsonl> [runs]", file=sys.stderr)
        raise SystemExit(2)
    path = Path(sys.argv[1])
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    recs = [r for r in load_jsonl(path) if r.get("is_event", True)]
    print(f"[eval_geocode_prod] {len(recs)} curated events x {runs} runs (delay {_DELAY}s/call)\n")
    accs: list[float] = []
    all_dists: list[float] = []
    tot_missed = tot_fabricated = 0
    for run in range(runs):
        correct, ok, dists, missed, fabricated, n = await _score_once(recs)
        if ok:
            accs.append(correct / ok)
        all_dists += dists
        tot_missed += missed
        tot_fabricated += fabricated
        print(f"  run {run + 1}: {ok} ok, decision acc {correct}/{ok}, "
              f"{len(dists)} co-located, missed {missed}, fabricated {fabricated}")
        if run < runs - 1:
            time.sleep(_DELAY)
    print()
    if accs:
        mean = statistics.mean(accs)
        sd = statistics.pstdev(accs) if len(accs) > 1 else 0.0
        print(f"[decision] locate-vs-abstain accuracy = {mean:.3f} ± {sd:.3f}")
    if all_dists:
        print(f"[distance] median error = {statistics.median(all_dists):.1f} km "
              f"(n={len(all_dists)} co-located pins; max {max(all_dists):.1f})")
    print(f"[errors] missed={tot_missed} fabricated-for-venueless={tot_fabricated} "
          f"(summed over {runs} runs)")


if __name__ == "__main__":
    asyncio.run(main())
