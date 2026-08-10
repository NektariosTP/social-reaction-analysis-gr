"""Deterministic day-granular temporal status (frozen now, no LLM, no DB)."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from api.temporal import derive_temporal_status

_ATHENS = ZoneInfo("Europe/Athens")
_NOW = datetime(2026, 8, 10, 12, 0, tzinfo=_ATHENS)


def test_none_event_time_returns_none() -> None:
    assert derive_temporal_status(None, _NOW) is None


def test_future_date_is_upcoming() -> None:
    assert derive_temporal_status(datetime(2026, 8, 11, 9, 0, tzinfo=_ATHENS), _NOW) == "upcoming"


def test_same_day_is_today_regardless_of_hour() -> None:
    # earlier in the day than `now` — still "today" (day-granular, no duration)
    assert derive_temporal_status(datetime(2026, 8, 10, 8, 0, tzinfo=_ATHENS), _NOW) == "today"


def test_past_date_is_past() -> None:
    assert derive_temporal_status(datetime(2026, 8, 9, 23, 0, tzinfo=_ATHENS), _NOW) == "past"


def test_compared_in_athens_not_utc() -> None:
    # 2026-08-10T23:30 UTC == 2026-08-11T02:30 Athens → next calendar day → upcoming
    utc = ZoneInfo("UTC")
    assert derive_temporal_status(datetime(2026, 8, 10, 23, 30, tzinfo=utc), _NOW) == "upcoming"
