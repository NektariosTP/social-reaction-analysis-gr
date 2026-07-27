from pathlib import Path

import pytest

from scripts.gold_common import load_jsonl, validate_events

GOLD = Path("tests/fixtures/gold")

def _require(name):
    p = GOLD / name
    if not p.exists():
        pytest.skip(f"{name} not frozen yet")
    return load_jsonl(p)

def test_events_only_real_and_valid():
    recs = _require("events.jsonl")
    assert recs, "events.jsonl empty"
    assert all(r.get("is_event") is True for r in recs), "must be is_event=true"
    assert validate_events(recs) == [], validate_events(recs)

def test_event_precision_only_negatives():
    recs = _require("event_precision.jsonl")
    assert all(r.get("is_event") is False for r in recs), "must be is_event=false"

def test_domestic_real_events_have_coords_or_are_dropped():
    # real, non-foreign events kept in events.jsonl must be locatable
    for r in _require("events.jsonl"):
        if not r.get("is_foreign"):
            assert r.get("true_lat") is not None, f"{r['pipeline_event_id']} kept but unlocated"

def test_relevance_and_clustering_frozen():
    rel = _require("relevance.jsonl")
    assert all(r["label"] in {"relevant", "noise"} for r in rel)
    clu = _require("clustering.jsonl")
    assert all(isinstance(r["gold_group"], int) for r in clu)
