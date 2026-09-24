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


def test_events_endpoint_exposes_event_date_param() -> None:
    schema = app.openapi()
    params = schema["paths"]["/events"]["get"]["parameters"]
    assert any(p["name"] == "event_date" for p in params)


def test_events_endpoints_expose_window_days_param() -> None:
    schema = app.openapi()
    for path in ("/events", "/events/geojson"):
        params = schema["paths"][path]["get"]["parameters"]
        assert any(p["name"] == "window_days" for p in params), path
