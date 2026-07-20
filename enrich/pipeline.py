"""Phase 3 enrichment pipeline orchestrator.

Usage:
    uv run python -m enrich.pipeline
"""
from __future__ import annotations

import asyncio
import json
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


async def _enrich_event(
    session: AsyncSession,
    event: Any,
    *,
    needs_classify: bool = True,
    needs_geocode: bool = True,
    needs_summary: bool = True,
) -> None:
    """Classify, geocode, and/or summarize a single event row (skipping completed steps)."""
    event_id = str(event.id)

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

    update_params: dict[str, Any] = {"id": event_id}
    set_clauses: list[str] = []

    # 1. Classify
    if needs_classify:
        centroid_text = getattr(event, "centroid", None)
        if centroid_text:
            centroid = np.array(
                [float(v) for v in str(centroid_text).strip("[]").split(",")],
                dtype=np.float32,
            )
        else:
            centroid = np.zeros(768, dtype=np.float32)

        classification = classify_with_llm_fallback(centroid=centroid, article_titles=titles)
        update_params.update(
            {
                "action_forms": classification.action_forms,
                "thematic_fields": classification.thematic_fields,
                "channel": classification.channel,
                "intensity": classification.intensity,
                "confidence": json.dumps(classification.confidence),
            }
        )
        set_clauses.extend(
            [
                "action_forms = :action_forms",
                "thematic_fields = :thematic_fields",
                "channel = :channel",
                "intensity = :intensity",
                "classification_confidence = CAST(:confidence AS jsonb)",
            ]
        )

    # 2. Geocode
    geo_results: list[Any] = []
    if needs_geocode:
        summary_el_hint = " ".join(titles[:3])
        geo_results = await geocode_event(summary_el=summary_el_hint, article_titles=titles)
        primary_geo = geo_results[0] if geo_results else None
        update_params.update(
            {
                "lat": primary_geo.lat if primary_geo else None,
                "lon": primary_geo.lon if primary_geo else None,
                "location_name": primary_geo.location_name if primary_geo else None,
            }
        )
        set_clauses.append(
            "primary_location = CASE WHEN CAST(:lat AS double precision) IS NOT NULL "
            "THEN ST_SetSRID(ST_MakePoint(CAST(:lon AS double precision), CAST(:lat AS double precision)), 4326)::geography "
            "ELSE NULL END"
        )

    # 3. Summarize
    if needs_summary:
        summary = summarize_event(
            article_titles=titles, article_bodies=bodies, n_sources=len(articles)
        )
        update_params.update(
            {
                "summary_el": summary.summary_el if summary else None,
                "summary_en": summary.summary_en if summary else None,
            }
        )
        set_clauses.extend(["summary_el = :summary_el", "summary_en = :summary_en"])

    set_clauses.append("status = 'pending_review'")

    await session.execute(
        text(f"UPDATE events SET {', '.join(set_clauses)} WHERE id = :id"),  # noqa: S608
        update_params,
    )

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

    steps = (
        ("classify" if needs_classify else "")
        + (" geocode" if needs_geocode else "")
        + (" summarize" if needs_summary else "")
    ).strip()
    logger.debug(
        "[enrich] Event %s done (%s, %d location(s)).",
        event_id[:8],
        steps or "no-op",
        len(geo_results),
    )


async def run_enrich_pipeline(engine: AsyncEngine | None = None) -> dict[str, Any]:
    """Enrich all events that haven't been enriched yet or are partially enriched.

    Picks up:
      - status='detected' (never enriched)
      - status='pending_review' or 'enriched' with NULL channel, summary_el, or
        primary_location (partial failure)
    Skips steps already completed to avoid unnecessary LLM calls.

    Uses `channel IS NULL` (not `action_forms IS NULL`) to detect "not yet
    classified": action_forms is `TEXT[] NOT NULL DEFAULT '{}'`, so it's never
    actually NULL. channel has no default and stays NULL until classification
    runs, then is always set to a non-null value — a reliable signal.
    """
    _engine = engine or create_async_engine(settings.database_url)
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        _engine, expire_on_commit=False
    )

    metrics: dict[str, Any] = {}

    async with session_factory() as session:
        result = await session.execute(
            text("""
                SELECT id, centroid,
                       channel IS NULL AS needs_classify,
                       summary_el IS NULL    AS needs_summary,
                       primary_location IS NULL AS needs_geocode
                FROM events
                WHERE status = 'detected'
                   OR (status IN ('pending_review', 'enriched')
                       AND (channel IS NULL OR summary_el IS NULL OR primary_location IS NULL))
            """)
        )
        events = result.all()
        logger.info("[enrich] %d event(s) to process.", len(events))

        n_enriched = 0
        n_failed = 0
        for event in events:
            try:
                async with session.begin_nested():
                    await _enrich_event(
                        session,
                        event,
                        needs_classify=bool(event.needs_classify),
                        needs_geocode=bool(event.needs_geocode),
                        needs_summary=bool(event.needs_summary),
                    )
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
