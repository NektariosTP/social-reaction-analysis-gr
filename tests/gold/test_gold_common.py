from pathlib import Path

from scripts.gold_common import GREEK_TO_EN_REGION, REGION_NAMES, load_jsonl, validate_events


def test_load_jsonl_strips_trailing_note(tmp_path: Path):
    p = tmp_path / "x.jsonl"
    p.write_text(
        '{"a": 1, "true_region_code": "Attica"}   # Same as abc-123\n'
        '{"a": 2}\n',
        encoding="utf-8",
    )
    recs = load_jsonl(p)
    assert len(recs) == 2
    assert recs[0]["a"] == 1
    assert recs[0]["_trailing_note"] == "Same as abc-123"
    assert "_trailing_note" not in recs[1]

def test_region_vocab():
    assert "Attica" in REGION_NAMES and "Peloponnese" in REGION_NAMES
    assert len(REGION_NAMES) == 13
    assert GREEK_TO_EN_REGION["Περιφέρεια Πελοποννήσου"] == "Peloponnese"

def test_validate_events_flags_bad_region_and_missing_is_event():
    bad = [{"pipeline_event_id": "e1", "is_event": True, "is_foreign": False,
            "true_region_code": "Attiki", "action_forms": ["x"], "thematic_fields": ["y"],
            "channel": "Φυσικό", "intensity": "Ειρηνική", "true_lat": 1.0, "true_lon": 1.0}]
    violations = validate_events(bad)
    assert any("Attiki" in v for v in violations)  # not a canonical region

def test_validate_events_accepts_clean_record():
    ok = [{"pipeline_event_id": "e1", "is_event": True, "is_foreign": False,
           "true_region_code": "Attica", "true_municipality": "Δήμος Αθηναίων",
           "action_forms": ["Απεργία/Στάση εργασίας"], "thematic_fields": ["Εργασιακό"],
           "channel": "Φυσικό", "intensity": "Ειρηνική", "true_lat": 37.98, "true_lon": 23.73}]
    assert validate_events(ok) == []
