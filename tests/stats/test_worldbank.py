import json
from pathlib import Path

from stats.catalog import IndicatorSpec
from stats.sources.worldbank import build_url, parse_worldbank

SPEC = IndicatorSpec(
    key="voice_accountability", label_el="Λ", label_en="VA", unit="pctile",
    source="worldbank", dataset="VA.PER.RNK", geo_level="national",
    cadence="annual", always_on=False, themes=("Πολιτικό/Θεσμικό",),
)

def test_build_url_targets_grc_and_json():
    url = build_url(SPEC)
    assert "country/GRC/indicator/VA.PER.RNK" in url
    assert "format=json" in url

def test_parse_skips_null_values_and_tags_national():
    doc = json.loads(Path("tests/stats/fixtures/worldbank_va.json").read_text(encoding="utf-8"))
    rows = parse_worldbank(doc, SPEC)
    assert len(rows) == 1
    assert rows[0].region_code == "GR"
    assert rows[0].period == "2023"
    assert rows[0].value == 71.2
    assert rows[0].source == "worldbank"

def test_parse_handles_empty_payload():
    assert parse_worldbank([{"message": "x"}, None], SPEC) == []
