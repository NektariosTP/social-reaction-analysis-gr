"""Tests for the event archival sweep."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from worker.archival import ARCHIVE_AFTER_HOURS, run_archival_sweep


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


async def test_run_archival_sweep_uses_24_hour_threshold() -> None:
    session = _mock_session_with_results([0])

    await run_archival_sweep(session)

    archive_sql = str(session.execute.call_args_list[0][0][0])
    archive_params = session.execute.call_args_list[0][0][1]

    assert ARCHIVE_AFTER_HOURS == 24
    assert "hours =>" in archive_sql
    assert archive_params["archive_after_hours"] == 24


async def test_run_archival_sweep_archives_24h_after_event_time() -> None:
    """A dated event is archived 24h after event_time, independent of last_seen."""
    session = _mock_session_with_results([0])

    await run_archival_sweep(session)

    archive_sql = str(session.execute.call_args_list[0][0][0])

    # Hour-precise trigger anchored on event_time (not a day-granular comparison).
    assert "event_time IS NOT NULL" in archive_sql
    assert "event_time + make_interval(hours => :archive_after_hours)" in archive_sql
    # The old 72h-quiet + day-boundary logic must be gone.
    assert "Europe/Athens" not in archive_sql


async def test_run_archival_sweep_targets_enriched_events() -> None:
    """Enriched events are swept once they age out."""
    session = _mock_session_with_results([0])

    await run_archival_sweep(session)

    archive_sql = str(session.execute.call_args_list[0][0][0])

    assert "'enriched'" in archive_sql
    assert "'announced'" not in archive_sql


async def test_run_archival_sweep_undated_events_fall_back_to_quiet_rule() -> None:
    """Events with no event_time archive after 24h of silence (last_seen)."""
    session = _mock_session_with_results([0])

    await run_archival_sweep(session)

    archive_sql = str(session.execute.call_args_list[0][0][0])

    assert "event_time IS NULL" in archive_sql
    assert "last_seen < now() - make_interval(hours => :archive_after_hours)" in archive_sql
