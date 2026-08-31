from unittest.mock import AsyncMock, MagicMock
import numpy as np
import pytest
from reactions.db import upsert_reaction, insert_announced_event

@pytest.mark.asyncio
async def test_upsert_reaction_uses_on_conflict_and_has_no_stance():
    session = AsyncMock()
    # begin_nested() is sync in AsyncSession (returns an async CM); a bare AsyncMock
    # would make the call itself a coroutine, breaking `async with session.begin_nested():`.
    session.begin_nested = MagicMock(return_value=MagicMock())
    session.begin_nested.return_value.__aenter__ = AsyncMock()
    session.begin_nested.return_value.__aexit__ = AsyncMock(return_value=False)
    res = AsyncMock(); res.rowcount = 1
    session.execute.return_value = res
    ok = await upsert_reaction(
        session, source_org="pame", actor_name="ΠΑΜΕ",
        text="Απεργία", url="http://x/1", observed_at=None,
        event_id=None, match_score=None, match_method="none",
    )
    sql = session.execute.call_args.args[0].text
    assert "INSERT INTO event_reactions" in sql
    assert "ON CONFLICT (source_org, url) DO NOTHING" in sql
    assert "stance" not in sql
    assert ok is True

@pytest.mark.asyncio
async def test_insert_announced_event_sets_status_announced():
    session = AsyncMock()
    # Result.first() is sync in SQLAlchemy; use MagicMock so the call doesn't return a coroutine.
    row = MagicMock(); row.first.return_value = ("evt-1",)
    session.execute.return_value = row
    eid = await insert_announced_event(
        session, centroid=np.zeros(768, dtype=np.float32),
        event_time=None, action_forms=["Απεργία/Στάση εργασίας"],
        channel="Φυσικό (offline)", lat=None, lon=None, is_national=True,
        summary_el="Απεργία 5 Σεπτέμβρη",
    )
    sql = session.execute.call_args.args[0].text
    assert "INSERT INTO events" in sql and "'announced'" in sql
    assert eid == "evt-1"
