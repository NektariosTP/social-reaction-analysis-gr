"""GET /events, GET /events/{id}, GET /events/geojson."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from api.db import get_db
from api.models import (
    ArticleSummary,
    EventContextResponse,
    EventDetail,
    EventSummary,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
    GeoJSONProperties,
    IndicatorValue,
    LocationPoint,
)
from api.routes.regions import latest_rows
from api.temporal import derive_temporal_status
from stats.catalog import load_catalog
from stats.context import assemble
from stats.crosswalk import canonical_region_name

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events", tags=["events"])

# Day-comparison operators reproducing api.temporal.derive_temporal_status in SQL.
# Keyed by a Literal-validated param, so the operator is never request-derived text.
_TEMPORAL_DAY_OPS: dict[str, str] = {"upcoming": ">", "today": "=", "past": "<"}

_ORDER_BY_SQL: dict[str, str] = {
    "recent": "last_seen DESC NULLS LAST",
    "event_time": "event_time ASC NULLS LAST",
}

# ---------------------------------------------------------------------------
# DB helpers (thin wrappers — mocked in tests)
# ---------------------------------------------------------------------------

def _parse_iso_datetime(value: str, field: str) -> datetime:
    """Parse to a native datetime — asyncpg needs the Python type, not a
    string cast on the SQL side, to bind against a timestamptz column."""
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid {field!r}: {value!r}") from exc


async def _fetch_events(
    session: AsyncSession,
    *,
    action_form: str | None = None,
    thematic_field: str | None = None,
    channel: str | None = None,
    intensity: str | None = None,
    region_code: str | None = None,
    municipality: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    bbox: str | None = None,
    temporal_status: str | None = None,
    is_national: bool | None = None,
    order_by: str = "recent",
    limit: int = 50,
    offset: int = 0,
) -> list[Row[Any]]:
    conditions = ["status = 'enriched'"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if action_form:
        conditions.append(":action_form = ANY(action_forms)")
        params["action_form"] = action_form
    if thematic_field:
        conditions.append(":thematic_field = ANY(thematic_fields)")
        params["thematic_field"] = thematic_field
    if channel:
        conditions.append("channel = :channel")
        params["channel"] = channel
    if intensity:
        conditions.append("intensity = :intensity")
        params["intensity"] = intensity
    if region_code:
        conditions.append("region_code = :region_code")
        params["region_code"] = region_code
    if municipality:
        conditions.append("municipality = :municipality")
        params["municipality"] = municipality
    if date_from:
        conditions.append("first_seen >= :date_from")
        params["date_from"] = _parse_iso_datetime(date_from, "date_from")
    if date_to:
        conditions.append("last_seen <= :date_to")
        params["date_to"] = _parse_iso_datetime(date_to, "date_to")
    if bbox:
        # bbox = "west,south,east,north"
        parts = [float(p) for p in bbox.split(",")]
        if len(parts) == 4:
            conditions.append(
                "primary_location && ST_MakeEnvelope(:west, :south, :east, :north, 4326)"
            )
            params.update(west=parts[0], south=parts[1], east=parts[2], north=parts[3])

    if temporal_status:
        op = _TEMPORAL_DAY_OPS[temporal_status]
        conditions.append(
            "event_time IS NOT NULL "
            f"AND (event_time AT TIME ZONE 'Europe/Athens')::date {op} "
            "(now() AT TIME ZONE 'Europe/Athens')::date"
        )
    if is_national is not None:
        conditions.append("is_national = :is_national")
        params["is_national"] = is_national

    where = " AND ".join(conditions)
    result = await session.execute(
        text(
            f"SELECT id::text, action_forms, thematic_fields, channel, intensity, "
            f"summary_el, summary_en, "
            f"ST_Y(primary_location::geometry) AS lat, "
            f"ST_X(primary_location::geometry) AS lon, "
            f"region_code, municipality, article_count, source_count, first_seen, last_seen, status, "
            f"event_time, is_national "
            f"FROM events WHERE {where} "
            f"ORDER BY {_ORDER_BY_SQL[order_by]} "
            f"LIMIT :limit OFFSET :offset"
        ),
        params,
    )
    return list(result.all())


async def _fetch_event_by_id(session: AsyncSession, event_id: str) -> Row[Any] | None:
    result = await session.execute(
        text(
            "SELECT id::text, action_forms, thematic_fields, channel, intensity, "
            "summary_el, summary_en, "
            "ST_Y(primary_location::geometry) AS lat, "
            "ST_X(primary_location::geometry) AS lon, "
            "region_code, municipality, article_count, source_count, first_seen, last_seen, status, "
            "event_time, is_national, "
            "classification_confidence "
            "FROM events WHERE id = :id"
        ),
        {"id": event_id},
    )
    return result.first()


async def _fetch_event_articles(session: AsyncSession, event_id: str) -> list[Row[Any]]:
    result = await session.execute(
        text(
            "SELECT id::text, source_id, source_type, url, title, published_at "
            "FROM articles WHERE event_id = :eid AND is_duplicate = FALSE "
            "ORDER BY published_at DESC LIMIT 20"
        ),
        {"eid": event_id},
    )
    return list(result.all())


async def _fetch_event_locations(
    session: AsyncSession, event_ids: list[str]
) -> dict[str, list[LocationPoint]]:
    """Batch-load all geocoded locations for the given events (primary first)."""
    if not event_ids:
        return {}
    result = await session.execute(
        text(
            "SELECT event_id::text AS event_id, "
            "ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lon, "
            "COALESCE(location_name, label, city) AS label, is_primary "
            "FROM event_locations "
            "WHERE event_id = ANY(:ids) AND location IS NOT NULL "
            "ORDER BY is_primary DESC"
        ),
        {"ids": event_ids},
    )
    out: dict[str, list[LocationPoint]] = {}
    for r in result.all():
        out.setdefault(r.event_id, []).append(
            LocationPoint(lat=r.lat, lon=r.lon, label=r.label, is_primary=bool(r.is_primary))
        )
    return out


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=list[EventSummary])
async def list_events(
    action_form: Annotated[str | None, Query()] = None,
    thematic_field: Annotated[str | None, Query()] = None,
    channel: Annotated[str | None, Query()] = None,
    intensity: Annotated[str | None, Query()] = None,
    region_code: Annotated[str | None, Query()] = None,
    municipality: Annotated[str | None, Query()] = None,
    date_from: Annotated[str | None, Query(description="ISO 8601 date")] = None,
    date_to: Annotated[str | None, Query(description="ISO 8601 date")] = None,
    bbox: Annotated[str | None, Query(description="west,south,east,north")] = None,
    temporal_status: Annotated[Literal["upcoming", "today", "past"] | None, Query()] = None,
    is_national: Annotated[bool | None, Query()] = None,
    order_by: Annotated[Literal["recent", "event_time"], Query()] = "recent",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> list[EventSummary]:
    rows = await _fetch_events(
        db,
        action_form=action_form,
        thematic_field=thematic_field,
        channel=channel,
        intensity=intensity,
        region_code=region_code,
        municipality=municipality,
        date_from=date_from,
        date_to=date_to,
        bbox=bbox,
        temporal_status=temporal_status,
        is_national=is_national,
        order_by=order_by,
        limit=limit,
        offset=offset,
    )
    now = datetime.now(ZoneInfo("Europe/Athens"))
    return [
        EventSummary(
            id=str(r.id),
            action_forms=list(r.action_forms or []),
            thematic_fields=list(r.thematic_fields or []),
            channel=r.channel,
            intensity=r.intensity,
            summary_el=r.summary_el,
            summary_en=r.summary_en,
            lat=r.lat,
            lon=r.lon,
            region_code=r.region_code,
            municipality=r.municipality,
            article_count=r.article_count or 0,
            source_count=r.source_count or 0,
            first_seen=r.first_seen,
            last_seen=r.last_seen,
            status=r.status,
            event_time=r.event_time,
            temporal_status=derive_temporal_status(r.event_time, now),
            is_national=bool(r.is_national),
        )
        for r in rows
    ]


@router.get("/geojson", response_model=GeoJSONFeatureCollection)
async def events_geojson(
    action_form: Annotated[str | None, Query()] = None,
    thematic_field: Annotated[str | None, Query()] = None,
    channel: Annotated[str | None, Query()] = None,
    db: AsyncSession = Depends(get_db),
) -> GeoJSONFeatureCollection:
    rows = await _fetch_events(db, action_form=action_form, thematic_field=thematic_field, channel=channel, limit=1000)
    located = [r for r in rows if r.lat is not None and r.lon is not None]
    locations_by_event = await _fetch_event_locations(db, [str(r.id) for r in located])
    features = []
    for r in located:
        features.append(
            GeoJSONFeature(
                geometry=GeoJSONGeometry(coordinates=[r.lon, r.lat]),
                properties=GeoJSONProperties(
                    id=str(r.id),
                    region_code=str(r.region_code) if r.region_code else None,
                    municipality=r.municipality,
                    action_forms=list(r.action_forms or []),
                    thematic_fields=list(r.thematic_fields or []),
                    channel=r.channel,
                    intensity=r.intensity,
                    summary_en=r.summary_en,
                    article_count=r.article_count or 0,
                    first_seen=r.first_seen,
                    locations=locations_by_event.get(str(r.id), []),
                ),
            )
        )
    return GeoJSONFeatureCollection(features=features)


@router.get("/{event_id}", response_model=EventDetail)
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)) -> EventDetail:
    row = await _fetch_event_by_id(db, event_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Event {event_id!r} not found.")
    articles_rows = await _fetch_event_articles(db, event_id)
    articles = [
        ArticleSummary(
            id=str(a.id), source_id=a.source_id, source_type=a.source_type,
            url=a.url, title=a.title, published_at=a.published_at,
        )
        for a in articles_rows
    ]
    now = datetime.now(ZoneInfo("Europe/Athens"))
    return EventDetail(
        id=str(row.id),
        action_forms=list(row.action_forms or []),
        thematic_fields=list(row.thematic_fields or []),
        channel=row.channel,
        intensity=row.intensity,
        summary_el=row.summary_el,
        summary_en=row.summary_en,
        lat=row.lat,
        lon=row.lon,
        region_code=row.region_code,
        municipality=row.municipality,
        article_count=row.article_count or 0,
        source_count=row.source_count or 0,
        first_seen=row.first_seen,
        last_seen=row.last_seen,
        status=row.status,
        event_time=row.event_time,
        temporal_status=derive_temporal_status(row.event_time, now),
        is_national=bool(row.is_national),
        classification_confidence=dict(row.classification_confidence) if row.classification_confidence else None,
        articles=articles,
    )


@router.get("/{event_id}/context", response_model=EventContextResponse)
async def event_context(event_id: str, db: AsyncSession = Depends(get_db)) -> EventContextResponse:
    row = (await db.execute(
        text("SELECT region_code, thematic_fields FROM events WHERE id = :id"),
        {"id": event_id},
    )).first()
    if row is None:
        raise HTTPException(status_code=404, detail="event not found")
    canonical = canonical_region_name(row[0])
    codes = [c for c in [canonical, "GR"] if c]
    value_rows = await latest_rows(db, codes) if codes else []
    catalog = load_catalog()
    always_on, thematic = assemble(catalog, value_rows, thematic_fields=list(row[1] or []))
    return EventContextResponse(
        region_code=canonical or "GR",
        always_on=[IndicatorValue(**i) for i in always_on],
        thematic=[IndicatorValue(**i) for i in thematic],
    )
