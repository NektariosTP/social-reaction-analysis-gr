"""Tests for stable event_id assignment via centroid cosine matching."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import numpy as np

from nlp.event_registry import (
    apply_merges,
    assign_event_id,
    load_existing_events,
    match_existing_event,
    running_mean,
)


def _centroid(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.random(768).astype(np.float32)
    return v / np.linalg.norm(v)


def test_match_returns_none_for_empty_registry() -> None:
    centroid = _centroid(0)
    result = match_existing_event(centroid, existing_events=[], threshold=0.85)
    assert result is None


def test_match_returns_existing_event_above_threshold() -> None:
    centroid = _centroid(0)
    noise = np.random.default_rng(1).normal(0, 0.01, 768).astype(np.float32)
    near_centroid = centroid + noise
    near_centroid /= np.linalg.norm(near_centroid)

    existing_id = str(uuid.uuid4())
    existing = [(existing_id, near_centroid)]
    result = match_existing_event(centroid, existing_events=existing, threshold=0.85)
    assert result == existing_id


def test_match_returns_none_below_threshold() -> None:
    c1 = _centroid(0)
    c2 = _centroid(99)
    existing_id = str(uuid.uuid4())
    result = match_existing_event(c1, existing_events=[(existing_id, c2)], threshold=0.85)
    assert result is None


def test_match_returns_best_match() -> None:
    centroid = _centroid(0)
    rng = np.random.default_rng(42)

    close = centroid + rng.normal(0, 0.005, 768).astype(np.float32)
    close /= np.linalg.norm(close)
    distant = centroid + rng.normal(0, 0.1, 768).astype(np.float32)
    distant /= np.linalg.norm(distant)

    id_close = "close-id"
    id_distant = "distant-id"
    result = match_existing_event(
        centroid,
        existing_events=[(id_distant, distant), (id_close, close)],
        threshold=0.85,
    )
    assert result == id_close


async def test_load_existing_events_excludes_rejected_merged_and_archived() -> None:
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    await load_existing_events(mock_session)

    executed_sql = str(mock_session.execute.call_args[0][0])
    assert "status NOT IN ('rejected', 'merged', 'archived')" in executed_sql


def test_running_mean_is_weighted_and_normalized() -> None:
    old = np.array([1.0, 0.0], dtype=np.float32)
    batch = np.array([0.0, 1.0], dtype=np.float32)
    # equal weights → direction (0.5, 0.5), normalized → (0.707, 0.707)
    out = running_mean(old, 1, batch, 1)
    assert np.allclose(out, [0.70710678, 0.70710678], atol=1e-5)
    assert abs(float(np.linalg.norm(out)) - 1.0) < 1e-5


def test_running_mean_respects_counts() -> None:
    old = np.array([1.0, 0.0], dtype=np.float32)
    batch = np.array([0.0, 1.0], dtype=np.float32)
    # old outweighs batch 3:1 → x-component dominates
    out = running_mean(old, 3, batch, 1)
    assert out[0] > out[1]


async def test_assign_matches_via_sql_and_writes_weighted_centroid() -> None:
    existing_id = "11111111-1111-1111-1111-111111111111"
    old = np.array([1.0, 0.0] + [0.0] * 766, dtype=np.float32)
    batch = np.array([1.0, 0.0] + [0.0] * 766, dtype=np.float32)  # identical → distance 0
    old_str = "[" + ",".join(str(v) for v in old.tolist()) + "]"

    session = AsyncMock()
    # First execute() = nearest-match SELECT → return one row (id, centroid, count, distance)
    select_result = MagicMock()
    select_result.first.return_value = (existing_id, old_str, 4, 0.0)
    session.execute = AsyncMock(return_value=select_result)

    got = await assign_event_id(session, centroid=batch, article_ids=["a1"], threshold=0.85)
    assert got == existing_id

    # The UPDATE must carry the weighted centroid (old_count=4, batch_count=1), not raw batch.
    update_calls = [c for c in session.execute.await_args_list if "UPDATE events" in str(c.args[0])]
    assert update_calls, "expected an UPDATE events call"
    written = update_calls[0].args[1]["centroid"]
    expected = running_mean(old, 4, batch, 1)
    expected_str = "[" + ",".join(str(v) for v in expected.tolist()) + "]"
    assert written == expected_str


def _vec_str(v: np.ndarray) -> str:
    return "[" + ",".join(str(x) for x in v.tolist()) + "]"


def _merge_session(kept_id: str, kept: np.ndarray, kept_count: int,
                   absorbed_id: str, absorbed: np.ndarray, absorbed_count: int) -> AsyncMock:
    """Mock session whose SELECT returns the kept + absorbed event rows."""
    select_result = MagicMock()
    select_result.all.return_value = [
        (kept_id, _vec_str(kept), kept_count),
        (absorbed_id, _vec_str(absorbed), absorbed_count),
    ]
    session = AsyncMock()
    session.execute = AsyncMock(return_value=select_result)
    return session


async def test_apply_merges_empty_returns_zero_and_writes_nothing() -> None:
    session = AsyncMock()
    session.execute = AsyncMock()
    n = await apply_merges(session, merges=[])
    assert n == 0
    session.execute.assert_not_awaited()


async def test_apply_merges_reassigns_articles_to_kept() -> None:
    kept_id = "11111111-1111-1111-1111-111111111111"
    absorbed_id = "22222222-2222-2222-2222-222222222222"
    kept = _centroid(0)
    absorbed = _centroid(1)
    session = _merge_session(kept_id, kept, 4, absorbed_id, absorbed, 1)

    n = await apply_merges(session, merges=[(absorbed_id, kept_id)])
    assert n == 1

    reassign = [
        c for c in session.execute.await_args_list if "UPDATE articles" in str(c.args[0])
    ]
    assert reassign, "expected an UPDATE articles call"
    params = reassign[0].args[1]
    assert params["kept"] == kept_id
    assert params["absorbed"] == absorbed_id


async def test_apply_merges_folds_weighted_centroid_into_kept() -> None:
    kept_id = "11111111-1111-1111-1111-111111111111"
    absorbed_id = "22222222-2222-2222-2222-222222222222"
    kept = _centroid(0)
    absorbed = _centroid(7)
    session = _merge_session(kept_id, kept, 4, absorbed_id, absorbed, 1)

    await apply_merges(session, merges=[(absorbed_id, kept_id)])

    kept_update = [
        c for c in session.execute.await_args_list
        if "UPDATE events" in str(c.args[0]) and "article_count = article_count" in str(c.args[0])
    ]
    assert kept_update, "expected an UPDATE events call folding the centroid"
    expected = running_mean(kept, 4, absorbed, 1)
    assert kept_update[0].args[1]["centroid"] == _vec_str(expected)


async def test_apply_merges_marks_absorbed_event_merged() -> None:
    kept_id = "11111111-1111-1111-1111-111111111111"
    absorbed_id = "22222222-2222-2222-2222-222222222222"
    session = _merge_session(kept_id, _centroid(0), 4, absorbed_id, _centroid(1), 1)

    await apply_merges(session, merges=[(absorbed_id, kept_id)])

    absorbed_update = [
        c for c in session.execute.await_args_list
        if "UPDATE events" in str(c.args[0]) and "status = 'merged'" in str(c.args[0])
    ]
    assert absorbed_update, "expected the absorbed event to be marked 'merged'"
    assert absorbed_update[0].args[1]["id"] == absorbed_id
