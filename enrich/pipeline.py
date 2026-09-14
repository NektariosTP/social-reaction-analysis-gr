"""Phase 3 enrichment pipeline orchestrator.

Usage:
    uv run python -m enrich.pipeline
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from enrich.config import settings
from enrich.enrich_llm import enrich_event_llm, parse_event_date
from enrich.geocode import detect_national_scope, resolve_locations
from reactions.config import settings as reaction_settings
from reactions.db import load_announced_events, merge_news_into_announced
from reactions.seed import find_announced_duplicate

logger = logging.getLogger(__name__)
_ATHENS = ZoneInfo("Europe/Athens")


def _parse_centroid(raw: str | None) -> np.ndarray | None:
    if not raw:
        return None
    return np.array([float(v) for v in raw.strip("[]").split(",")], dtype=np.float32)


async def _enrich_event(session: AsyncSession, event: Any) -> None:
    """Run the single consolidated call for one event, then link to announcements."""
    event_id = str(event.id)
    art_result = await session.execute(
        text(
            "SELECT title, body_text, published_at FROM articles "
            "WHERE event_id = :eid AND is_duplicate = FALSE "
            "ORDER BY published_at DESC LIMIT 10"
        ),
        {"eid": event_id},
    )
    articles = art_result.all()
    if not articles:
        return
    titles = [r[0] or "" for r in articles]
    bodies = [r[1] or "" for r in articles]
    reference_date = articles[0][2].isoformat() if articles[0][2] else None

    enr = enrich_event_llm(
        article_titles=titles, article_bodies=bodies,
        n_sources=len(articles), reference_date=reference_date,
    )
    if enr is None:
        logger.warning("[enrich] Event %s left 'approved' (LLM failed).", event_id[:8])
        return

    full_text = " ".join(titles) + " " + " ".join(bodies)
    national = bool(enr.is_national or detect_national_scope(full_text))
    geo = await resolve_locations(enr.locations, national=national, session=session)
    primary = geo[0] if geo else None
    event_time = parse_event_date(enr.event_date)

    await session.execute(
        text("""
            UPDATE events SET
                action_forms = :action_forms, thematic_fields = :thematic_fields,
                channel = :channel, intensity = :intensity,
                summary_el = :summary_el, summary_en = :summary_en,
                event_time = :event_time, is_national = :is_national,
                primary_location = CASE WHEN CAST(:lat AS double precision) IS NOT NULL
                    THEN ST_SetSRID(ST_MakePoint(CAST(:lon AS double precision),
                         CAST(:lat AS double precision)), 4326)::geography ELSE NULL END,
                status = 'enriched'
            WHERE id = :id
        """),
        {
            "action_forms": enr.action_forms, "thematic_fields": enr.thematic_fields,
            "channel": enr.channel, "intensity": enr.intensity,
            "summary_el": enr.summary_el, "summary_en": enr.summary_en,
            "event_time": event_time, "is_national": national,
            "lat": primary.lat if primary else None,
            "lon": primary.lon if primary else None, "id": event_id,
        },
    )
    for loc in geo:
        await session.execute(
            text("""
                INSERT INTO event_locations (event_id, location, location_name, city, is_primary)
                VALUES (:event_id,
                    CASE WHEN CAST(:lat AS double precision) IS NOT NULL
                        THEN ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography ELSE NULL END,
                    :location_name, :city, :is_primary)
                ON CONFLICT DO NOTHING
            """),
            {"event_id": event_id, "lat": loc.lat, "lon": loc.lon,
             "location_name": loc.location_name, "city": loc.city, "is_primary": loc.is_primary},
        )

    await _link_to_announcement(
        session, event_id=event_id, centroid=_parse_centroid(event.centroid),
        action_forms=enr.action_forms, event_time=event_time,
        lat=primary.lat if primary else None, lon=primary.lon if primary else None,
        is_national=national,
    )


async def _link_to_announcement(
    session: AsyncSession, *, event_id: str, centroid: np.ndarray | None,
    action_forms: list[str], event_time: datetime | None,
    lat: float | None, lon: float | None, is_national: bool,
) -> str | None:
    """After enrichment, merge this news event into a matching 'announced' union event."""
    if centroid is None:
        return None
    existing = await load_announced_events(session)
    if not existing:
        return None
    event_day = event_time.astimezone(_ATHENS).date() if event_time is not None else None
    match = find_announced_duplicate(
        centroid=centroid, action_forms=action_forms,
        place_lat=lat, place_lon=lon, is_national=is_national,
        existing=existing, sim_threshold=reaction_settings.announcement_merge_sim,
        event_day=event_day,
    )
    if match is None or match == event_id:
        return None
    await merge_news_into_announced(session, announced_id=match, news_id=event_id)
    logger.info("[enrich] Linked news event %s → announcement %s.", event_id[:8], match[:8])
    return match


async def run_enrich_pipeline(engine: AsyncEngine | None = None) -> dict[str, Any]:
    """Enrich all human-approved events, plus any 'enriched' rows left partial by a failure.

    Picks up:
      - status='approved' (human-approved, never enriched)
      - status='enriched' with NULL summary_el or channel (partial failure)

    `primary_location` is deliberately NOT part of the retry check: resolve_locations()
    legitimately leaves it NULL forever for a national-scope event with no named venue,
    and treating that as "needs retry" would re-run the full LLM call on every cycle
    indefinitely. `channel`/`summary_el` are always written together with location in
    the same UPDATE, so either is a reliable "never finished enriching" signal on its own.
    """
    _engine = engine or create_async_engine(settings.database_url)
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        _engine, expire_on_commit=False
    )

    async with session_factory() as session:
        result = await session.execute(
            text("""
                SELECT id, centroid FROM events
                WHERE status = 'approved'
                   OR (status = 'enriched' AND (summary_el IS NULL OR channel IS NULL))
            """)
        )
        events = result.all()
        logger.info("[enrich] %d event(s) to process.", len(events))
        n_enriched = 0
        n_failed = 0
        for event in events:
            try:
                async with session.begin_nested():
                    await _enrich_event(session, event)
                n_enriched += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("[enrich] Failed on event %s: %s", str(event.id)[:8], exc)
                n_failed += 1
        await session.commit()
    metrics = {"n_enriched": n_enriched, "n_failed": n_failed}
    logger.info("[enrich] Pipeline complete — %s", metrics)

    if engine is None:
        await _engine.dispose()

    return metrics


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    asyncio.run(run_enrich_pipeline())
