import json
from pathlib import Path

from stats.catalog import IndicatorSpec
from stats.sources.eurostat import build_url, parse_jsonstat

SPEC = IndicatorSpec(
    key="gdp_per_capita", label_el="ΑΕΠ", label_en="GDP", unit="EUR",
    source="eurostat", dataset="nama_10r_2gdp", geo_level="nuts2",
    cadence="annual", always_on=True, themes=("Οικονομικό",),
)

def test_build_url_includes_dataset_geolevel_and_format():
    url = build_url(SPEC)
    assert "statistics/1.0/data/nama_10r_2gdp" in url
    assert "geoLevel=nuts2" in url
    assert "format=JSON" in url

def test_build_url_appends_filters_to_pin_auxiliary_dimensions():
    spec = IndicatorSpec(
        key="gdp_per_capita", label_el="ΑΕΠ", label_en="GDP", unit="EUR",
        source="eurostat", dataset="nama_10r_2gdp", geo_level="nuts2",
        cadence="annual", always_on=True, themes=(), filters=(("unit", "EUR_HAB"),),
    )
    assert "&unit=EUR_HAB" in build_url(spec)

def test_parse_picks_latest_period_per_region_and_maps_names():
    doc = json.loads(Path("tests/stats/fixtures/eurostat_gdp.json").read_text(encoding="utf-8"))
    rows = {r.region_code: r for r in parse_jsonstat(doc, SPEC)}
    assert set(rows) == {"Attica", "Central Macedonia"}
    assert rows["Attica"].period == "2022"
    assert rows["Attica"].value == 110.0
    assert rows["Central Macedonia"].value == 55.0
    assert rows["Attica"].source == "eurostat"
    assert rows["Attica"].indicator == "gdp_per_capita"

def test_parse_skips_non_greek_geo():
    doc = json.loads(Path("tests/stats/fixtures/eurostat_gdp.json").read_text(encoding="utf-8"))
    doc["dimension"]["geo"]["category"]["index"]["FR10"] = 2
    doc["size"] = [1, 3, 2]
    rows = parse_jsonstat(doc, SPEC)
    assert all(r.region_code in {"Attica", "Central Macedonia"} for r in rows)
