from unittest.mock import AsyncMock, patch

import numpy as np
import pytest

from ingestion.connectors.union import ReactionItem
from reactions.pipeline import _process_item


@pytest.mark.asyncio
async def test_process_item_future_dated_seeds_event():
    session = AsyncMock()
    item = ReactionItem(
        source_org="oikodomon", actor_name="Οικοδόμων",
        title="Πανελλαδικό Συλλαλητήριο 5 Σεπτεμβρίου 2099 στη Θεσσαλονίκη",
        body_text="", url="http://x/1", observed_at=None,
    )
    with patch("reactions.pipeline.reaction_already_linked", new=AsyncMock(return_value=False)), \
         patch("reactions.pipeline.embed_query", return_value=np.zeros(768, dtype="float32")), \
         patch("reactions.pipeline.seed_or_attach_event", new=AsyncMock(return_value=("evt-9", "seeded"))) as seed, \
         patch("reactions.pipeline.upsert_reaction", new=AsyncMock(return_value=True)) as upsert:
        outcome = await _process_item(session, item, sim_threshold=0.9)
    assert outcome == "seeded"
    seed.assert_awaited_once()
    # upsert must be called WITHOUT a stance kwarg
    assert "stance" not in upsert.await_args.kwargs
    upsert.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_item_already_linked_reaction_is_skipped():
    # Same feed item reappears in a later pipeline cycle after it was already matched
    # to an event — must not re-run seed/attach (which would double-count source_count
    # and re-skew the event centroid) or re-upsert.
    session = AsyncMock()
    item = ReactionItem(
        source_org="pame", actor_name="ΠΑΜΕ",
        title="Πανελλαδικό Συλλαλητήριο 5 Σεπτεμβρίου 2099 στη Θεσσαλονίκη",
        body_text="", url="http://x/1", observed_at=None,
    )
    with patch("reactions.pipeline.reaction_already_linked", new=AsyncMock(return_value=True)), \
         patch("reactions.pipeline.seed_or_attach_event", new=AsyncMock()) as seed, \
         patch("reactions.pipeline.upsert_reaction", new=AsyncMock()) as upsert:
        outcome = await _process_item(session, item, sim_threshold=0.9)
    assert outcome == "duplicate"
    seed.assert_not_awaited()
    upsert.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_item_filtered_out_writes_nothing():
    session = AsyncMock()
    item = ReactionItem(source_org="olme", actor_name="ΟΛΜΕ",
                        title="Αποχαιρετάμε τον συνάδελφο", body_text="",
                        url="http://x/2", observed_at=None)
    with patch("reactions.pipeline.reaction_already_linked", new=AsyncMock(return_value=False)), \
         patch("reactions.pipeline.upsert_reaction", new=AsyncMock()) as upsert:
        outcome = await _process_item(session, item, sim_threshold=0.9)
    assert outcome == "filtered"
    upsert.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_item_dateless_joiner_attaches_by_place():
    from reactions.place import PlaceResult
    session = AsyncMock()
    item = ReactionItem(
        source_org="trofimon_fthiotidas", actor_name="Συνδικάτο Τροφίμων Φθιώτιδας",
        title="Συμμετέχουμε στο πανελλαδικό συλλαλητήριο στη Θεσσαλονίκη",
        body_text="", url="http://x/3", observed_at=None,  # note: NO date in the text
    )
    with patch("reactions.pipeline.reaction_already_linked", new=AsyncMock(return_value=False)), \
         patch("reactions.pipeline.embed_query", return_value=np.zeros(768, dtype="float32")), \
         patch("reactions.pipeline.resolve_place",
               return_value=PlaceResult(lat=40.64, lon=22.94, name="Θεσσαλονίκη", is_national=False)), \
         patch("reactions.pipeline.seed_or_attach_event",
               new=AsyncMock(return_value=("evt-1", "deduped"))) as seed, \
         patch("reactions.pipeline.upsert_reaction", new=AsyncMock(return_value=True)) as upsert:
        outcome = await _process_item(session, item, sim_threshold=0.9)
    assert outcome == "deduped"
    assert seed.await_args.kwargs.get("attach_only") is True   # attach-only path taken
    assert seed.await_args.kwargs.get("event_time") is None    # no date → inherits event's
    upsert.assert_awaited_once()
