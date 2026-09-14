from unittest.mock import AsyncMock, MagicMock
import numpy as np
import pytest
from reactions.db import (
    upsert_reaction, insert_announced_event, load_announced_events, reaction_already_linked,
    merge_news_into_announced,
)

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
    assert "ON CONFLICT (source_org, url) DO UPDATE" in sql
    assert "event_id = COALESCE(event_reactions.event_id, EXCLUDED.event_id)" in sql
    assert "match_method = EXCLUDED.match_method" in sql
    assert "stance" not in sql
    assert ok is True

@pytest.mark.asyncio
async def test_insert_announced_event_sets_status_detected():
    session = AsyncMock()
    row = MagicMock(); row.first.return_value = ("evt-1",)
    session.execute.return_value = row
    eid = await insert_announced_event(
        session, centroid=np.zeros(768, dtype=np.float32),
        event_time=None, action_forms=["Απεργία/Στάση εργασίας"],
        channel="Φυσικό (offline)", lat=None, lon=None, is_national=True,
        summary_el="Απεργία 5 Σεπτέμβρη",
    )
    sql = session.execute.call_args.args[0].text
    assert "INSERT INTO events" in sql and "'detected'" in sql
    assert "'announced'" not in sql
    assert eid == "evt-1"

@pytest.mark.asyncio
async def test_load_announced_events_includes_pending_detected_seeds():
    session = AsyncMock()
    result = MagicMock(); result.all.return_value = []
    session.execute = AsyncMock(return_value=result)

    await load_announced_events(session)

    sql = session.execute.call_args.args[0].text
    assert "status = 'announced'" in sql
    assert "status = 'detected'" in sql
    assert "article_count = 0" in sql

@pytest.mark.asyncio
async def test_reaction_already_linked_true_when_row_has_event_id():
    session = AsyncMock()
    result = MagicMock(); result.first.return_value = (1,)
    session.execute = AsyncMock(return_value=result)
    linked = await reaction_already_linked(session, source_org="pame", url="http://x/1")
    sql = session.execute.call_args.args[0].text
    assert "FROM event_reactions" in sql
    assert "event_id IS NOT NULL" in sql
    assert linked is True

@pytest.mark.asyncio
async def test_reaction_already_linked_false_when_no_matching_row():
    session = AsyncMock()
    result = MagicMock(); result.first.return_value = None
    session.execute = AsyncMock(return_value=result)
    linked = await reaction_already_linked(session, source_org="pame", url="http://x/1")
    assert linked is False

@pytest.mark.asyncio
async def test_load_announced_events_includes_enriched_zero_article():
    session = AsyncMock()
    result = MagicMock(); result.all.return_value = []
    session.execute = AsyncMock(return_value=result)
    await load_announced_events(session)
    sql = session.execute.call_args.args[0].text
    assert "status = 'enriched'" in sql
    assert "article_count = 0" in sql

@pytest.mark.asyncio
async def test_merge_reparents_reactions():
    session = AsyncMock()
    news = ("[0,0]", 1, ["Απεργία/Στάση εργασίας"], [], "Φυσικό (offline)",
            None, "sel", "sen", None, False, None, None)
    ann = ("[0,0]", 0, ["Απεργία/Στάση εργασίας"])
    first_calls = iter([MagicMock(first=MagicMock(return_value=news)),
                        MagicMock(first=MagicMock(return_value=ann))])
    session.execute = AsyncMock(side_effect=lambda *a, **k: next(first_calls, MagicMock()))
    await merge_news_into_announced(session, announced_id="A", news_id="N")
    executed = " ".join(c.args[0].text for c in session.execute.call_args_list)
    assert "UPDATE event_reactions SET event_id = :a WHERE event_id = :n" in executed
