"""Tests for within-cluster cosine+time-window deduplication."""
from __future__ import annotations

import numpy as np
from datetime import datetime, timedelta, timezone

from nlp.deduplication import find_duplicates_in_cluster, find_duplicates_global


def _vec(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.random(768).astype(np.float32)
    return v / np.linalg.norm(v)


def _base_vec() -> np.ndarray:
    v = np.ones(768, dtype=np.float32)
    return v / np.linalg.norm(v)


def test_near_identical_same_day_is_duplicate() -> None:
    t0 = datetime(2026, 6, 13, 10, 0, tzinfo=timezone.utc)
    base = _base_vec()
    noise = np.random.default_rng(0).normal(0, 0.001, 768).astype(np.float32)
    near_dup = base + noise
    near_dup /= np.linalg.norm(near_dup)
    articles = [
        ("id-1", base, t0),
        ("id-2", near_dup, t0 + timedelta(hours=1)),
    ]
    dupes = find_duplicates_in_cluster(articles, cosine_threshold=0.98, time_window_hours=72)
    assert "id-2" in dupes


def test_different_article_not_duplicate() -> None:
    t0 = datetime(2026, 6, 13, tzinfo=timezone.utc)
    v1 = _vec(1)
    v2 = _vec(99)
    articles = [("a", v1, t0), ("b", v2, t0)]
    dupes = find_duplicates_in_cluster(articles, cosine_threshold=0.98, time_window_hours=72)
    assert dupes == set()


def test_outside_time_window_not_duplicate() -> None:
    t0 = datetime(2026, 6, 13, tzinfo=timezone.utc)
    base = _base_vec()
    noise = np.random.default_rng(0).normal(0, 0.001, 768).astype(np.float32)
    near_dup = base + noise
    near_dup /= np.linalg.norm(near_dup)
    articles = [
        ("id-1", base, t0),
        ("id-2", near_dup, t0 + timedelta(hours=120)),  # outside 72h window
    ]
    dupes = find_duplicates_in_cluster(articles, cosine_threshold=0.98, time_window_hours=72)
    assert "id-2" not in dupes


def test_global_dedup_catches_near_dup_regardless_of_cluster():
    t0 = datetime(2026, 9, 14, 10, 0, tzinfo=timezone.utc)
    base = _base_vec()
    noise = np.random.default_rng(1).normal(0, 0.001, 768).astype(np.float32)
    near_dup = base + noise
    near_dup /= np.linalg.norm(near_dup)
    other = _vec(42)  # unrelated article, should NOT be flagged
    # Flat window list — the function is agnostic to cluster membership.
    articles = [
        ("cy-1", base, t0),
        ("cy-2", near_dup, t0 + timedelta(hours=2)),
        ("unrelated", other, t0 + timedelta(hours=1)),
    ]
    dupes = find_duplicates_global(articles, cosine_threshold=0.98, time_window_hours=72)
    assert dupes == {"cy-2"}