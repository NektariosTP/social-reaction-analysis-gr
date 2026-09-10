"""Event archival sweep: hide events gone quiet for a long time. Never deletes
rows or article bodies."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

ARCHIVE_AFTER_HOURS = 72


async def run_archival_sweep(session: AsyncSession) -> dict[str, Any]:
    """Archive enriched events gone quiet for ARCHIVE_AFTER_HOURS. Never deletes rows."""
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
    await session.commit()
    metrics = {"n_archived": n_archived}
    logger.info("[archival] sweep complete — %s", metrics)
    return metrics
