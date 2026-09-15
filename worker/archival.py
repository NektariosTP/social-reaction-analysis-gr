"""Event archival sweep: hide events once they are over. Never deletes rows or
article bodies."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

ARCHIVE_AFTER_HOURS = 24


async def run_archival_sweep(session: AsyncSession) -> dict[str, Any]:
    """Archive events ARCHIVE_AFTER_HOURS after they happen. Never deletes rows.

    A live event (enriched or announced) is retired once it is over:
    - Dated events: archived exactly ARCHIVE_AFTER_HOURS after event_time
      (hour-precise), regardless of when the last article arrived.
    - Undated events (no event_time): no scheduled moment to measure from, so they
      fall back to the same window of silence — archived once last_seen is older
      than ARCHIVE_AFTER_HOURS.
    """
    archived_result = await session.execute(
        text("""
            UPDATE events SET status = 'archived'
            WHERE status = 'enriched'
              AND (
                (event_time IS NOT NULL
                    AND now() >= event_time + make_interval(hours => :archive_after_hours))
                OR
                (event_time IS NULL
                    AND last_seen < now() - make_interval(hours => :archive_after_hours))
              )
            RETURNING id
        """),
        {"archive_after_hours": ARCHIVE_AFTER_HOURS},
    )
    n_archived = len(archived_result.all())
    await session.commit()
    metrics = {"n_archived": n_archived}
    logger.info("[archival] sweep complete — %s", metrics)
    return metrics
