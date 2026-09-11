"""Event archival sweep: hide events that are over or long gone quiet. Never
deletes rows or article bodies."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

ARCHIVE_AFTER_HOURS = 72

# The event's day (Athens) is strictly before today's — i.e. the event is over.
# NULL event_time yields NULL (never true), so this also acts as an "is dated"
# guard. Mirrors the 'past' predicate in api.routes.events._TEMPORAL_DAY_OPS so
# archival and the frontend's temporal split agree on the day boundary.
_EVENT_DAY_PAST = (
    "(event_time AT TIME ZONE 'Europe/Athens')::date "
    "< (now() AT TIME ZONE 'Europe/Athens')::date"
)


async def run_archival_sweep(session: AsyncSession) -> dict[str, Any]:
    """Archive events that should no longer surface as active. Never deletes rows.

    Two populations, one pass:
    - Enriched news events gone quiet for ARCHIVE_AFTER_HOURS, guarded so an event
      whose day is still upcoming is never retired before it happens.
    - Announced events whose event day (Athens) has passed, so a lapsed announcement
      stops showing as ongoing/upcoming. Undated announcements have no day to lapse,
      so they fall back to the same quiet rule.
    """
    archived_result = await session.execute(
        text(f"""
            UPDATE events SET status = 'archived'
            WHERE (
                status = 'enriched'
                AND last_seen < now() - make_interval(hours => :archive_after_hours)
                AND (event_time IS NULL OR {_EVENT_DAY_PAST})
              )
              OR (
                status = 'announced'
                AND (
                    {_EVENT_DAY_PAST}
                    OR (event_time IS NULL
                        AND last_seen < now() - make_interval(hours => :archive_after_hours))
                )
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
