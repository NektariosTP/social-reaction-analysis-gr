"""The generated OpenAPI schema must expose the temporal fields the frontend reads."""
from __future__ import annotations

from api.main import app


def test_event_summary_schema_has_temporal_fields() -> None:
    schema = app.openapi()
    props = schema["components"]["schemas"]["EventSummary"]["properties"]
    assert "event_time" in props
    assert "temporal_status" in props
    assert "is_national" in props


def test_geojson_properties_schema_has_locations() -> None:
    schema = app.openapi()
    props = schema["components"]["schemas"]["GeoJSONProperties"]["properties"]
    assert "locations" in props
