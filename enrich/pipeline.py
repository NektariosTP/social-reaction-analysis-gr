"""Phase 3 enrichment pipeline orchestrator.

Usage:
    uv run python -m enrich.pipeline
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from enrich.classify import classify_with_llm_fallback
from enrich.config import settings
from enrich.geocode import geocode_event
from enrich.summarize import summarize_event

logger = logging.getLogger(__name__)


async def _enrich_event(session: AsyncSession, event: Any) -> None:
    """Classify, geocode, and summarize a single event row."""
    event_id = str(event.id)

    # Fetch article titles + bodies for this event
    art_result = await session.execute(
        text(
            "SELECT title, body_text FROM articles "
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

    # 1. Classify
    centroid_text = getattr(event, "centroid", None)
    if centroid_text:
        centroid = np.array(
            [float(v) for v in str(centroid_text).strip("[]").split(",")],
            dtype=np.float32,
        )
    else:
        centroid = np.zeros(768, dtype=np.float32)

    classification = classify_with_llm_fallback(centroid=centroid, article_titles=titles)

    # 2. Geocode (returns all locations for this event, primary first)
    summary_el_hint = " ".join(titles[:3])
    geo_results = await geocode_event(summary_el=summary_el_hint, article_titles=titles)
    primary_geo = geo_results[0] if geo_results else None

    # 3. Summarize
    summary = summarize_event(
        article_titles=titles, article_bodies=bodies, n_sources=len(articles)
    )

    # Write-back: classification + summary + primary location → events table
    update_params: dict[str, Any] = {
        "id": event_id,
        "action_forms": classification.action_forms,
        "thematic_fields": classification.thematic_fields,
        "channel": classification.channel,
        "intensity": classification.intensity,
        "confidence": str(classification.confidence),
        "summary_el": summary.summary_el if summary else None,
        "summary_en": summary.summary_en if summary else None,
        "lat": primary_geo.lat if primary_geo else None,
        "lon": primary_geo.lon if primary_geo else None,
        "location_name": primary_geo.location_name if primary_geo else None,
    }

    await session.execute(
        text("""
            UPDATE events
            SET action_forms = :action_forms,
                thematic_fields = :thematic_fields,
                channel = :channel,
                intensity = :intensity,
                classification_confidence = :confidence::jsonb,
                summary_el = :summary_el,
                summary_en = :summary_en,
                primary_location = CASE WHEN :lat IS NOT NULL
                    THEN ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                    ELSE NULL END,
                status = 'enriched'
            WHERE id = :id
        """),
        update_params,
    )

    # Write all geocoded locations to event_locations (primary + secondaries)
    for loc in geo_results:
        await session.execute(
            text("""
                INSERT INTO event_locations (event_id, location, location_name, city, is_primary)
                VALUES (
                    :event_id,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                    :location_name,
                    :city,
                    :is_primary
                )
                ON CONFLICT DO NOTHING
            """),
            {
                "event_id": event_id,
                "lat": loc.lat,
                "lon": loc.lon,
                "location_name": loc.location_name,
                "city": loc.city,
                "is_primary": loc.is_primary,
            },
        )

    logger.debug("[enrich] Event %s enriched (%d location(s)).", event_id[:8], len(geo_results))


async def run_enrich_pipeline(engine: AsyncEngine | None = None) -> dict[str, Any]:
    """Enrich all events that haven't been enriched yet. Returns metrics dict."""
    _engine = engine or create_async_engine(settings.database_url)
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        _engine, expire_on_commit=False
    )

    metrics: dict[str, Any] = {}

    async with session_factory() as session:
        result = await session.execute(
            text("SELECT id, centroid FROM events WHERE status = 'detected'")
        )
        events = result.all()
        logger.info("[enrich] %d unenriched events to process.", len(events))

        n_enriched = 0
        n_failed = 0
        for event in events:
            try:
                await _enrich_event(session, event)
                n_enriched += 1
            except Exception as exc:
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
