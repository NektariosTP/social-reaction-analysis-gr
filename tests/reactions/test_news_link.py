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
