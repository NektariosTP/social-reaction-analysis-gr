"""
backend/api/routes/stats.py

GET /stats  — aggregate statistics over all event clusters.
"""

from __future__ import annotations

import re
from collections import Counter

from fastapi import APIRouter

from backend.api.models import DateCount, StatsResponse
from backend.nlp.vectorstore import get_all

router = APIRouter(prefix="/stats", tags=["stats"])

# Strip leading numeric prefixes that old LLM runs may have written into
# ChromaDB metadata (e.g. "1. Mass Mobilization & Street Actions" → canonical).
_NUMBERED_PREFIX = re.compile(r"^\d+\.\s*")


def _normalize_category(raw: str) -> str:
    return _NUMBERED_PREFIX.sub("", raw).strip()


@router.get("", response_model=StatsResponse)
def get_stats() -> StatsResponse:
    data = get_all(include=["metadatas"])
    metadatas: list[dict] = data["metadatas"]

    total_articles = len(metadatas)
    geocoded_articles = sum(1 for m in metadatas if m.get("lat") is not None)

    # One representative metadata per stable event_id (matches /events grouping).
    event_metas: dict[str, dict] = {}
    for meta in metadatas:
        eid = meta.get("event_id", "")
        if not eid:
            continue
        if eid not in event_metas:
            event_metas[eid] = meta

    total_events = len(event_metas)

    categories: Counter[str] = Counter()
    by_country: Counter[str] = Counter()
    by_date: Counter[str] = Counter()

    for meta in event_metas.values():
        raw_cat = meta.get("reaction_category", "Unknown")
        categories[_normalize_category(raw_cat)] += 1

        country = meta.get("location_country")
        if country:
            by_country[country] += 1

        # Prefer event_date; fall back to published_at date portion.
        date_str = (meta.get("event_date") or meta.get("published_at", ""))[:10]
        if date_str and len(date_str) == 10:
            by_date[date_str] += 1

    sorted_dates = [
        DateCount(date=d, count=c) for d, c in sorted(by_date.items())
    ]

    return StatsResponse(
        total_events=total_events,
        total_articles=total_articles,
        geocoded_articles=geocoded_articles,
        categories=dict(categories),
        by_country=dict(by_country),
        by_date=sorted_dates,
    )
