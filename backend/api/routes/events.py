"""
backend/api/routes/events.py

GET /events          — list all event clusters with optional filters
GET /events/{event_id}     — detail for a single event by stable event_id
"""

from __future__ import annotations

import time
from collections import Counter, defaultdict
from statistics import mean
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from backend.api.models import ArticleSummary, EventDetail, EventSummary
from backend.nlp.vectorstore import get_all

router = APIRouter(prefix="/events", tags=["events"])

_CACHE_TTL: float = 300.0  # seconds
_event_cache: list[dict] | None = None
_event_cache_ts: float = 0.0


def _build_event_list() -> list[dict]:
    """Return all event dicts, rebuilt at most once every _CACHE_TTL seconds."""
    global _event_cache, _event_cache_ts
    now = time.monotonic()
    if _event_cache is not None and (now - _event_cache_ts) < _CACHE_TTL:
        return _event_cache

    data = get_all(include=["metadatas", "documents"])
    ids: list[str] = data["ids"]
    metadatas: list[dict] = data["metadatas"]

    groups: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for rec_id, meta in zip(ids, metadatas):
        eid = meta.get("event_id", "")
        if not eid:
            continue
        groups[eid].append((rec_id, meta))

    computed_events: list[dict] = []
    for eid, members in sorted(groups.items()):
        lats = [float(m["lat"]) for _, m in members if m.get("lat") is not None]
        lons = [float(m["lon"]) for _, m in members if m.get("lon") is not None]

        countries = [m["location_country"] for _, m in members if m.get("location_country")]
        dominant_country = Counter(countries).most_common(1)[0][0] if countries else None

        # Prefer a member that has an LLM-generated summary as representative.
        rep_meta = next(
            (m for _, m in members if m.get("summary_en")),
            members[0][1],
        )

        # cluster_id: most common cluster_id among members (usually one value)
        cids = [int(m.get("cluster_id", -1)) for _, m in members]
        dominant_cid = Counter(cids).most_common(1)[0][0]

        computed_events.append(
            {
                "event_id": eid,
                "cluster_id": dominant_cid,
                "reaction_category": rep_meta.get("reaction_category", "Unknown"),
                "summary_en": rep_meta.get("summary_en", ""),
                "summary_el": rep_meta.get("summary_el", ""),
                "event_date": rep_meta.get("event_date", ""),
                "lat": mean(lats) if lats else None,
                "lon": mean(lons) if lons else None,
                "location_name": rep_meta.get("location_name"),
                "location_country": dominant_country,
                "article_count": len(members),
                "sources": sorted({m.get("source", "") for _, m in members}),
                "articles": [
                    {
                        "id": rec_id,
                        "source": m.get("source", ""),
                        "url": m.get("url", ""),
                        "title": m.get("title", ""),
                        "published_at": m.get("published_at", ""),
                        "lat": float(m["lat"]) if m.get("lat") is not None else None,
                        "lon": float(m["lon"]) if m.get("lon") is not None else None,
                    }
                    for rec_id, m in members
                ],
            }
        )

    _event_cache = computed_events
    _event_cache_ts = now
    return _event_cache


@router.get("", response_model=list[EventSummary])
def list_events(
    category: Annotated[
        str | None,
        Query(description="Filter by reaction_category (exact match)"),
    ] = None,
    location_country: Annotated[
        str | None,
        Query(description="Filter by dominant location_country (case-insensitive)"),
    ] = None,
) -> list[EventSummary]:
    events = _build_event_list()

    if category:
        events = [e for e in events if e["reaction_category"] == category]

    if location_country:
        lc_lower = location_country.lower()
        events = [
            e
            for e in events
            if (e.get("location_country") or "").lower() == lc_lower
        ]

    return [
        EventSummary(**{k: v for k, v in e.items() if k != "articles"})
        for e in events
    ]


@router.get("/{event_id}", response_model=EventDetail)
def get_event(event_id: str) -> EventDetail:
    events = _build_event_list()
    event = next((e for e in events if e["event_id"] == event_id), None)
    if event is None:
        raise HTTPException(
            status_code=404,
            detail=f"Event {event_id!r} not found.",
        )
    articles = [ArticleSummary(**a) for a in event["articles"]]
    return EventDetail(
        **{k: v for k, v in event.items() if k != "articles"},
        articles=articles,
    )
