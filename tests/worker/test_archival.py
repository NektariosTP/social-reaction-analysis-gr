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
