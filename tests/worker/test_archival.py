"""Tests for the event archival sweep."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from worker.archival import run_archival_sweep


def _mock_session_with_results(row_counts: list[int]) -> AsyncMock:
    """Mock session whose session.execute() calls yield RETURNING results with
    the given row counts, in call order."""
    session = AsyncMock()
    results = []
    for count in row_counts:
        result = MagicMock()
        result.all.return_value = [MagicMock()] * count
        results.append(result)
    session.execute = AsyncMock(side_effect=results)
    return session


async def test_run_archival_sweep_returns_metrics() -> None:
    session = _mock_session_with_results([2])

    metrics = await run_archival_sweep(session)

    assert metrics == {"n_archived": 2}
    session.commit.assert_awaited_once()


async def test_run_archival_sweep_handles_zero_matches() -> None:
    session = _mock_session_with_results([0])

    metrics = await run_archival_sweep(session)

    assert metrics == {"n_archived": 0}


async def test_run_archival_sweep_uses_72_hour_threshold() -> None:
    session = _mock_session_with_results([0])

    await run_archival_sweep(session)

    archive_sql = str(session.execute.call_args_list[0][0][0])
    archive_params = session.execute.call_args_list[0][0][1]

    assert "hours =>" in archive_sql
    assert archive_params["archive_after_hours"] == 72


async def test_run_archival_sweep_guards_upcoming_enriched_events() -> None:
    """Enriched events whose day is still upcoming must never be archived on the
    quiet rule alone — the event_time day-guard has to gate the enriched branch."""
    session = _mock_session_with_results([0])

    await run_archival_sweep(session)

    archive_sql = str(session.execute.call_args_list[0][0][0])

    assert "status = 'enriched'" in archive_sql
    # The quiet branch only fires for undated or already-past events.
    assert "event_time IS NULL" in archive_sql
    assert "Europe/Athens" in archive_sql


async def test_run_archival_sweep_retires_lapsed_announced_events() -> None:
    """Announced events whose event day (Athens) has passed must be archived so a
    lapsed announcement stops showing as ongoing/upcoming."""
    session = _mock_session_with_results([0])

    await run_archival_sweep(session)

    archive_sql = str(session.execute.call_args_list[0][0][0])

    assert "status = 'announced'" in archive_sql
    # Uses the same day-boundary predicate the API's temporal_status filter uses.
    assert "(event_time AT TIME ZONE 'Europe/Athens')::date" in archive_sql
    assert "(now() AT TIME ZONE 'Europe/Athens')::date" in archive_sql
