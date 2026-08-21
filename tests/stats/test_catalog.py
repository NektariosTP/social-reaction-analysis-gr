import pytest
from stats.catalog import load_catalog, IndicatorSpec

def test_catalog_loads_and_is_nonempty():
    specs = load_catalog()
    assert len(specs) >= 15
    assert all(isinstance(s, IndicatorSpec) for s in specs)

def test_catalog_keys_unique():
    specs = load_catalog()
    keys = [s.key for s in specs]
    assert len(keys) == len(set(keys))

def test_sources_and_geo_levels_valid():
    for s in load_catalog():
        assert s.source in {"eurostat", "worldbank"}
        assert s.geo_level in {"nuts2", "national"}
        assert isinstance(s.themes, tuple)

def test_has_expected_indicators():
    keys = {s.key for s in load_catalog()}
    assert {"unemployment_rate", "gdp_per_capita", "voice_accountability", "rule_of_law"} <= keys

def test_national_indicators_are_worldbank():
    for s in load_catalog():
        if s.geo_level == "national":
            assert s.source == "worldbank"
