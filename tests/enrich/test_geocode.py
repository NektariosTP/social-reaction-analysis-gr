"""Tests for the geocoding pipeline."""
from __future__ import annotations

from unittest.mock import patch

import pytest
import respx
from httpx import Response

from enrich.geocode import GeocodeResult, LocationMention, geocode_event, geocode_text, lookup_gazetteer


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


async def test_geocode_event_returns_multiple_locations_via_llm() -> None:
    """LLM returns two location mentions → geocode_event geocodes both."""
    athens = GeocodeResult(lat=37.9838, lon=23.7275, location_name="Πλατεία Συντάγματος", city="Αθήνα", is_primary=True)
    thessaloniki = GeocodeResult(lat=40.6401, lon=22.9444, location_name="Πλατεία Αριστοτέλους", city="Θεσσαλονίκη", is_primary=False)

    mentions = [
        LocationMention(venue="Πλατεία Συντάγματος", city="Αθήνα"),
        LocationMention(venue="Πλατεία Αριστοτέλους", city="Θεσσαλονίκη"),
    ]

    with patch("enrich.geocode._extract_locations_llm", return_value=mentions), \
         patch("enrich.geocode.geocode_text", side_effect=[athens, thessaloniki]):
        results = await geocode_event(
            summary_el="Πανελλαδική απεργία σε Αθήνα και Θεσσαλονίκη",
            article_titles=["Απεργία σε όλη την Ελλάδα"],
        )

    assert len(results) == 2
    assert results[0].city == "Αθήνα"
    assert results[0].is_primary is True
    assert results[1].city == "Θεσσαλονίκη"
    assert results[1].is_primary is False


async def test_geocode_event_falls_back_to_gazetteer_when_llm_fails() -> None:
    """LLM extraction returns empty → gazetteer picks up the city."""
    with patch("enrich.geocode._extract_locations_llm", return_value=[]):
        results = await geocode_event(
            summary_el="Συγκέντρωση στην Αθήνα",
            article_titles=[],
        )

    assert len(results) == 1
    assert results[0].location_name == "Αθήνα"
