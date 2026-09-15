from __future__ import annotations

from datetime import date

import numpy as np

from nlp.date_split import split_by_event_day

_V = np.ones(768, dtype=np.float32)  # embedding unused by the current logic


def _art(i, day):
    return (f"a{i}", _V, day)


def test_peels_well_populated_minority_bucket():
    # 5×16/9 (primary) + 3×17/9 (peels). tolerance 0.
    arts = [_art(i, date(2026, 9, 16)) for i in range(5)] + [
        _art(i, date(2026, 9, 17)) for i in range(5, 8)
    ]
    groups = split_by_event_day(arts, min_bucket=3, tolerance_days=0)
    assert len(groups) == 2
    g17 = next(g for g in groups if "a5" in g)
    assert set(g17) == {"a5", "a6", "a7"}
    g16 = next(g for g in groups if "a0" in g)
    assert set(g16) == {"a0", "a1", "a2", "a3", "a4"}


def test_below_threshold_bucket_stays_with_primary():
    # 5×16/9 + 1×30/9 → single article can't peel; stays in primary.
    arts = [_art(i, date(2026, 9, 16)) for i in range(5)] + [_art(99, date(2026, 9, 30))]
    groups = split_by_event_day(arts, min_bucket=3, tolerance_days=0)
    assert len(groups) == 1
    assert "a99" in groups[0]


def test_undated_articles_follow_primary():
    arts = (
        [_art(i, date(2026, 9, 16)) for i in range(5)]
        + [_art(i, date(2026, 9, 17)) for i in range(5, 8)]
        + [_art(50, None), _art(51, None)]
    )
    groups = split_by_event_day(arts, min_bucket=3, tolerance_days=0)
    primary = next(g for g in groups if "a0" in g)
    assert "a50" in primary and "a51" in primary


def test_clean_single_date_cluster_unchanged():
    arts = [_art(i, date(2026, 9, 16)) for i in range(6)]
    groups = split_by_event_day(arts, min_bucket=3, tolerance_days=0)
    assert len(groups) == 1 and len(groups[0]) == 6


def test_tolerance_merges_adjacent_days():
    # 16/9 and 17/9 within tolerance 1 → one bucket, no split.
    arts = [_art(i, date(2026, 9, 16)) for i in range(4)] + [
        _art(i, date(2026, 9, 17)) for i in range(4, 8)
    ]
    groups = split_by_event_day(arts, min_bucket=3, tolerance_days=1)
    assert len(groups) == 1


def test_no_dates_returns_single_group():
    arts = [_art(i, None) for i in range(4)]
    groups = split_by_event_day(arts, min_bucket=3, tolerance_days=0)
    assert groups == [["a0", "a1", "a2", "a3"]]


def test_tolerance_chains_three_consecutive_days():
    # Mon/Tue/Wed, 3 articles each, tolerance 1 → chain merge into ONE bucket
    # (regression: a fixed-anchor merge would incorrectly split Wed off from Mon).
    arts = (
        [_art(i, date(2026, 9, 14)) for i in range(3)]
        + [_art(i, date(2026, 9, 15)) for i in range(3, 6)]
        + [_art(i, date(2026, 9, 16)) for i in range(6, 9)]
    )
    groups = split_by_event_day(arts, min_bucket=3, tolerance_days=1)
    assert len(groups) == 1
    assert set(groups[0]) == {f"a{i}" for i in range(9)}
