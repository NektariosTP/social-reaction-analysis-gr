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
            "WHERE centroid IS NOT NULL AND status NOT IN ('rejected', 'merged', 'archived')"
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
    """Match or create an event; update the events table; link articles to the event.

    Match: single indexed nearest-neighbour query (pgvector `<=>` cosine distance);
    accept when distance <= 1 - threshold. On match, the centroid is updated by an
    article_count-weighted running mean (not overwritten), so it converges instead
    of drifting to the last batch.
    """
    centroid_str = f"[{','.join(str(v) for v in centroid.tolist())}]"
    now = datetime.now(timezone.utc)

    row = (
        await session.execute(
            text(
                "SELECT id::text, centroid::text, article_count, "
                "centroid <=> CAST(:vec AS vector) AS distance "
                "FROM events "
                "WHERE centroid IS NOT NULL AND status NOT IN ('rejected', 'merged', 'archived') "
                "ORDER BY centroid <=> CAST(:vec AS vector) "
                "LIMIT 1"
            ),
            {"vec": centroid_str},
        )
    ).first()

    matched = row is not None and float(row[3]) <= (1.0 - threshold)

    if not matched:
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
        event_id, old_centroid_str, old_count, _dist = row
        old_centroid = np.array(
            [float(v) for v in old_centroid_str.strip("[]").split(",")], dtype=np.float32
        )
        merged = running_mean(old_centroid, int(old_count), centroid, len(article_ids))
        merged_str = f"[{','.join(str(v) for v in merged.tolist())}]"
        await session.execute(
            text("""
                UPDATE events
                SET centroid = CAST(:centroid AS vector),
                    article_count = article_count + :count,
                    last_seen = :now
                WHERE id = :id
            """),
            {"id": event_id, "centroid": merged_str, "count": len(article_ids), "now": now},
        )
        logger.debug("[registry] Updated event %s (+%d articles, weighted)", event_id, len(article_ids))

    for article_id in article_ids:
        await session.execute(
            text("UPDATE articles SET event_id = :eid WHERE id = :aid"),
            {"eid": event_id, "aid": article_id},
        )

    return event_id


def running_mean(
    old_centroid: np.ndarray,
    old_count: int,
    batch_centroid: np.ndarray,
    batch_count: int,
) -> np.ndarray:
    """article_count-weighted mean of two centroids, L2-normalized."""
    total = old_count + batch_count
    merged = (old_centroid * old_count + batch_centroid * batch_count) / total
    norm = float(np.linalg.norm(merged))
    if norm > 0:
        merged = merged / norm
    return merged.astype(np.float32)


async def apply_merges(
    session: AsyncSession,
    merges: list[tuple[str, str]],
) -> int:
    """Fold each (absorbed_id, kept_id) pair produced by `find_merges` into one event.

    For each pair the absorbed event's articles are reassigned to the kept event, the
    kept centroid is folded via an article_count-weighted running mean (so it converges
    rather than jumping), and the absorbed event is marked 'merged' so it drops out of
    future matching (see the status filters in `load_existing_events` / `assign_event_id`).
    Pairs are applied in order, re-reading the kept event each time, so a kept event that
    absorbs several others accumulates correctly. Returns the number of events merged.
    """
    now = datetime.now(timezone.utc)
    n_merged = 0
    for absorbed_id, kept_id in merges:
        rows = (
            await session.execute(
                text(
                    "SELECT id::text, centroid::text, article_count FROM events "
                    "WHERE id IN (:kept, :absorbed)"
                ),
                {"kept": kept_id, "absorbed": absorbed_id},
            )
        ).all()
        by_id = {r[0]: r for r in rows}
        if kept_id not in by_id or absorbed_id not in by_id:
            logger.warning(
                "[registry] merge skipped: missing event (absorbed=%s kept=%s)",
                absorbed_id, kept_id,
            )
            continue

        kept_centroid = np.array(
            [float(v) for v in by_id[kept_id][1].strip("[]").split(",")], dtype=np.float32
        )
        kept_count = int(by_id[kept_id][2])
        absorbed_centroid = np.array(
            [float(v) for v in by_id[absorbed_id][1].strip("[]").split(",")], dtype=np.float32
        )
        absorbed_count = int(by_id[absorbed_id][2])

        merged = running_mean(kept_centroid, kept_count, absorbed_centroid, absorbed_count)
        merged_str = f"[{','.join(str(v) for v in merged.tolist())}]"

        await session.execute(
            text("UPDATE articles SET event_id = :kept WHERE event_id = :absorbed"),
            {"kept": kept_id, "absorbed": absorbed_id},
        )
        await session.execute(
            text("""
                UPDATE events
                SET centroid = CAST(:centroid AS vector),
                    article_count = article_count + :count,
                    last_seen = :now
                WHERE id = :id
            """),
            {"id": kept_id, "centroid": merged_str, "count": absorbed_count, "now": now},
        )
        await session.execute(
            text("UPDATE events SET status = 'merged', last_seen = :now WHERE id = :id"),
            {"id": absorbed_id, "now": now},
        )
        n_merged += 1
        logger.debug("[registry] merged %s → %s (weighted centroid fold)", absorbed_id, kept_id)
    return n_merged
