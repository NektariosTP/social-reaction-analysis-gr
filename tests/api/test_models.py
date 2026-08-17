"""Unit tests for the P4 location models."""
from __future__ import annotations

from api.models import GeoJSONProperties, LocationPoint


def test_location_point_round_trips() -> None:
    p = LocationPoint(lat=37.98, lon=23.72, label="Αθήνα", is_primary=True)
    dumped = p.model_dump()
    assert dumped == {"lat": 37.98, "lon": 23.72, "label": "Αθήνα", "is_primary": True}


def test_location_point_label_optional() -> None:
    p = LocationPoint(lat=40.64, lon=22.94, is_primary=False)
    assert p.label is None


def test_geojson_properties_defaults_locations_empty() -> None:
    props = GeoJSONProperties(id="x", action_forms=[], thematic_fields=[], article_count=0)
    assert props.locations == []
