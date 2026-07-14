"""Event archival sweep: hide inactive events, prune stale article bodies, and
permanently close events that have been idle for a long time. Never deletes rows."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

ARCHIVE_AFTER_HOURS = 72
CLOSE_AFTER_DAYS = 10


async def run_archival_sweep(session: AsyncSession) -> dict[str, Any]:
    """Archive enriched events gone quiet 72h+, prune their article bodies, and
    permanently close events archived for a further 7 days (10 days total)."""
    archived_result = await session.execute(
        text("""
            UPDATE events SET status = 'archived'
            WHERE status = 'enriched'
              AND last_seen < now() - make_interval(hours => :archive_after_hours)
            RETURNING id
        """),
        {"archive_after_hours": ARCHIVE_AFTER_HOURS},
    )
    n_archived = len(archived_result.all())

    pruned_result = await session.execute(
        text("""
            UPDATE articles SET body_text = NULL
            WHERE body_text IS NOT NULL
              AND event_id IN (SELECT id FROM events WHERE status = 'archived')
            RETURNING id
        """)
    )
    n_pruned = len(pruned_result.all())

    closed_result = await session.execute(
        text("""
            UPDATE events SET status = 'closed'
            WHERE status = 'archived'
              AND last_seen < now() - make_interval(days => :close_after_days)
            RETURNING id
        """),
        {"close_after_days": CLOSE_AFTER_DAYS},
    )
    n_closed = len(closed_result.all())

    await session.commit()

    metrics = {"n_archived": n_archived, "n_pruned": n_pruned, "n_closed": n_closed}
    logger.info("[archival] sweep complete — %s", metrics)
    return metrics
