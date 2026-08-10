"""Day-granular temporal status derived from an event's stored time.

Dependency-light (datetime + zoneinfo only) so the read path never imports the
heavy enrich/LLM stack. Status is a pure function of event_time vs now, so it is
never stale and can also be reproduced in SQL when a milestone needs to filter.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

_ATHENS = ZoneInfo("Europe/Athens")


def derive_temporal_status(event_time: datetime | None, now: datetime) -> str | None:
    """upcoming | today | past | None, compared by calendar day in Europe/Athens."""
    if event_time is None:
        return None
    event_day = event_time.astimezone(_ATHENS).date()
    today = now.astimezone(_ATHENS).date()
    if event_day > today:
        return "upcoming"
    if event_day == today:
        return "today"
    return "past"
