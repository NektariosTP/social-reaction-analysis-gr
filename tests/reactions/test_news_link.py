"""News-cluster → union-announcement linking (structural match reuse)."""
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from reactions.seed import find_announced_duplicate


def test_structural_match_fires_below_centroid_threshold() -> None:
    # Different orgs' short blurbs → low cosine, but same day+action+place must still match.
    news = np.array([1.0, 0.0], dtype=np.float32)
    announced = np.array([0.0, 1.0], dtype=np.float32)  # cosine 0 << 0.9
    existing = [(
        "announced-id", announced, "PAME", date(2026, 9, 5),
        ["Διαδήλωση/Πορεία/Συγκέντρωση"], 40.62, 22.95, False,
    )]
    match = find_announced_duplicate(
        centroid=news, action_forms=["Διαδήλωση/Πορεία/Συγκέντρωση"],
        place_lat=40.62, place_lon=22.95, is_national=False,
        existing=existing, sim_threshold=0.9, event_day=date(2026, 9, 5),
    )
    assert match == "announced-id"


def test_no_match_when_place_disagrees() -> None:
    news = np.array([1.0, 0.0], dtype=np.float32)
    announced = np.array([0.0, 1.0], dtype=np.float32)
    existing = [(
        "announced-id", announced, "PAME", date(2026, 9, 5),
        ["Διαδήλωση/Πορεία/Συγκέντρωση"], 37.97, 23.72, False,  # Athens, not Thessaloniki
    )]
    match = find_announced_duplicate(
        centroid=news, action_forms=["Διαδήλωση/Πορεία/Συγκέντρωση"],
        place_lat=40.62, place_lon=22.95, is_national=False,
        existing=existing, sim_threshold=0.9, event_day=date(2026, 9, 5),
    )
    assert match is None


@pytest.mark.asyncio
async def test_merge_marks_news_merged_and_announced_enriched() -> None:
    from reactions.db import merge_news_into_announced

    session = MagicMock()
    news_row = ("[0.1,0.2]", 3, ["Απεργία/Στάση εργασίας"], ["Εργασιακό"],
                "Φυσικό (offline)", "Ειρηνική", "el", "en", None, False, 37.97, 23.72)
    ann_row = ("[0.3,0.4]", 0, ["Διαδήλωση/Πορεία/Συγκέντρωση"])
    session.execute = AsyncMock(side_effect=[
        MagicMock(first=lambda: news_row),
        MagicMock(first=lambda: ann_row),
        MagicMock(), MagicMock(), MagicMock(), MagicMock(),
    ])
    await merge_news_into_announced(session, announced_id="A", news_id="N")
    sql = " ".join(str(c.args[0]) for c in session.execute.call_args_list)
    assert "status = 'merged'" in sql
    assert "status = 'enriched'" in sql


@pytest.mark.asyncio
async def test_merge_zero_article_count_announced_fully_adopts_news_centroid() -> None:
    """A freshly-seeded announced event has article_count=0 (no news backing it yet);
    weight-0 in running_mean means the merge should fully adopt the news centroid,
    not blend it as if the announced side carried 1 unit of evidence."""
    from nlp.event_registry import running_mean
    from reactions.db import _vec_str, merge_news_into_announced

    ann_cen = np.array([1.0, 0.0], dtype=np.float32)
    news_cen = np.array([0.0, 1.0], dtype=np.float32)

    session = MagicMock()
    news_row = (_vec_str(news_cen), 2, ["Απεργία/Στάση εργασίας"], ["Εργασιακό"],
                "Φυσικό (offline)", "Ειρηνική", "el", "en", None, False, None, None)
    ann_row = (_vec_str(ann_cen), 0, ["Διαδήλωση/Πορεία/Συγκέντρωση"])
    session.execute = AsyncMock(side_effect=[
        MagicMock(first=lambda: news_row),
        MagicMock(first=lambda: ann_row),
        MagicMock(), MagicMock(), MagicMock(), MagicMock(),
    ])
    await merge_news_into_announced(session, announced_id="A", news_id="N")

    update_call = [
        c for c in session.execute.call_args_list if "centroid = CAST" in str(c.args[0])
    ][0]
    expected = running_mean(ann_cen, 0, news_cen, 2)
    assert update_call.args[1]["c"] == _vec_str(expected) == _vec_str(news_cen)
