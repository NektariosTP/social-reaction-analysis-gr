"""Stable event_id assignment: centroid cosine matching over existing events in DB."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def match_existing_event(
    centroid: np.ndarray,
    existing_events: list[tuple[str, np.ndarray]],
    threshold: float,
) -> str | None:
    """Return the event_id of the closest existing event above threshold, else None."""
    if not existing_events:
        return None
    best_id: str | None = None
    best_sim = -1.0
    for event_id, existing_centroid in existing_events:
        sim = float(np.dot(centroid, existing_centroid))
        if sim > best_sim:
            best_sim = sim
            best_id = event_id
    if best_sim >= threshold:
        return best_id
    return None


async def load_existing_events(session: AsyncSession) -> list[tuple[str, np.ndarray]]:
    """Load all event centroids from the DB, excluding permanently closed/rejected events."""
    result = await session.execute(
        text(
            "SELECT id::text, centroid::text FROM events "
            "WHERE centroid IS NOT NULL AND status NOT IN ('closed', 'rejected')"
        )
    )
    rows = result.all()
    existing: list[tuple[str, np.ndarray]] = []
    for event_id, centroid_text in rows:
        if centroid_text:
            vec = np.array(
                [float(v) for v in centroid_text.strip("[]").split(",")],
                dtype=np.float32,
            )
            existing.append((event_id, vec))
    return existing


async def assign_event_id(
    session: AsyncSession,
    centroid: np.ndarray,
    article_ids: list[str],
    threshold: float,
) -> str:
    """Match or create an event; update events table; link articles to event."""
    existing = await load_existing_events(session)
    event_id = match_existing_event(centroid, existing, threshold)

    centroid_str = f"[{','.join(str(v) for v in centroid.tolist())}]"
    now = datetime.now(timezone.utc)

    if event_id is None:
        event_id = str(uuid.uuid4())
        await session.execute(
            text("""
                INSERT INTO events (id, centroid, article_count, first_seen, last_seen, status)
                VALUES (:id, CAST(:centroid AS vector), :count, :now, :now, 'detected')
            """),
            {"id": event_id, "centroid": centroid_str, "count": len(article_ids), "now": now},
        )
        logger.debug("[registry] New event %s (%d articles)", event_id, len(article_ids))
    else:
        await session.execute(
            text("""
                UPDATE events
                SET centroid = CAST(:centroid AS vector),
                    article_count = article_count + :count,
                    last_seen = :now,
                    status = CASE WHEN status = 'archived' THEN 'enriched' ELSE status END
                WHERE id = :id
            """),
            {"id": event_id, "centroid": centroid_str, "count": len(article_ids), "now": now},
        )
        logger.debug("[registry] Updated event %s (+%d articles)", event_id, len(article_ids))

    for article_id in article_ids:
        await session.execute(
            text("UPDATE articles SET event_id = :eid WHERE id = :aid"),
            {"eid": event_id, "aid": article_id},
        )

    return event_id
