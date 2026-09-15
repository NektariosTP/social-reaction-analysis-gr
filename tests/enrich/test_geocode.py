"""Tests for the geocoding pipeline."""
from __future__ import annotations

import respx
from httpx import Response

from enrich.geocode import geocode_text, lookup_gazetteer


def test_gazetteer_hit_for_athens() -> None:
    result = lookup_gazetteer("Συγκέντρωση στην Αθήνα")
    assert result is not None
    assert abs(result.lat - 37.9838) < 0.01
    assert result.location_name == "Αθήνα"
    assert result.city == "Αθήνα"


def test_gazetteer_miss_for_unknown() -> None:
    result = lookup_gazetteer("Αγνώστη τοποθεσία χωρίς νόημα")
    assert result is None


@respx.mock
async def test_nominatim_geocode_returns_result() -> None:
    respx.get("http://test-nominatim/search").mock(
        return_value=Response(
            200,
            json=[{"lat": "37.9838", "lon": "23.7275", "display_name": "Πλατεία Συντάγματος, Αθήνα"}],
        )
    )
    result = await geocode_text(
        "Πλατεία Συντάγματος, Αθήνα", nominatim_url="http://test-nominatim", delay=0.0, city="Αθήνα"
    )
    assert result is not None
    assert abs(result.lat - 37.9838) < 0.01
    assert result.city == "Αθήνα"


@respx.mock
async def test_nominatim_geocode_returns_none_on_empty() -> None:
    respx.get("http://test-nominatim/search").mock(
        return_value=Response(200, json=[])
    )
    result = await geocode_text(
        "Αγνώστη τοποθεσία", nominatim_url="http://test-nominatim", delay=0.0
    )
    assert result is None


@respx.mock
async def test_nominatim_geocode_returns_none_on_http_error() -> None:
    respx.get("http://test-nominatim/search").mock(return_value=Response(503))
    result = await geocode_text(
        "Αθήνα", nominatim_url="http://test-nominatim", delay=0.0
    )
    assert result is None
