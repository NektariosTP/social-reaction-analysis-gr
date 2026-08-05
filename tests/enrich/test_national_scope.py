"""Panhellenic-scope detection + Athens-HQ default for venueless national events."""
from __future__ import annotations

import respx
from httpx import Response

from unittest.mock import patch

from enrich.geocode import GeocodeResult, LocationMention, detect_national_scope, geocode_event


def test_detects_panhellenic_keywords() -> None:
    assert detect_national_scope("Πανελλαδική απεργία στο εμπόριο") is True
    assert detect_national_scope("24ωρη απεργία της ΓΣΕΕ σε όλη τη χώρα") is True


def test_localized_event_not_national() -> None:
    assert detect_national_scope("Συγκέντρωση στα Προπύλαια για το μετρό Θεσσαλονίκης") is False
    assert detect_national_scope("Κατάληψη στο δημαρχείο Ηρακλείου") is False


async def test_national_multiple_cities_returns_no_location() -> None:
    # national text, LLM found several competing cities as examples (no venue for any) —
    # picking one would be a coin-flip hallucination. geocode_text is mocked to SUCCEED
    # (simulates a real reachable Nominatim resolving "Ηράκλειο" just fine) so this only
    # passes if geocode_event short-circuits before ever calling it — an unreachable URL
    # would make this pass for the wrong reason (network failure, not the intended guard).
    with (
        patch(
            "enrich.geocode._extract_locations_llm",
            return_value=[
                LocationMention(city="Ηράκλειο"),
                LocationMention(city="Θεσσαλονίκη"),
                LocationMention(city="Βόλος"),
            ],
        ),
        patch(
            "enrich.geocode.geocode_text",
            return_value=GeocodeResult(lat=35.34, lon=25.13, location_name="Ηράκλειο", city="Ηράκλειο"),
        ) as mock_geocode_text,
    ):
        results = await geocode_event(
            summary_el="Πανελλαδική απεργία στο εμπόριο, κλειστά καταστήματα",
            article_titles=["Μαζική η απεργία στο εμπόριο"],
        )
    assert results == []
    mock_geocode_text.assert_not_called()


async def test_national_single_city_mention_still_geocoded() -> None:
    # national text, but LLM found exactly one, unambiguous city (no separate venue) — e.g.
    # a local ΚΕΠ office covered as part of a nationwide campaign. A single specific mention
    # is trustworthy (nothing to hallucinate between), so it should still be geocoded.
    with patch(
        "enrich.geocode._extract_locations_llm",
        return_value=[LocationMention(city="Κοζάνη")],
    ), patch(
        "enrich.geocode.geocode_text",
        return_value=GeocodeResult(lat=40.30, lon=21.79, location_name="Κοζάνη", city="Κοζάνη"),
    ) as mock_geocode_text:
        results = await geocode_event(
            summary_el="Πανελλαδική κινητοποίηση, χθες στο ΚΕΠ Κοζάνης",
            article_titles=["Κινητοποίηση στο ΚΕΠ Κοζάνης"],
        )
    assert results
    assert results[0].location_name == "Κοζάνη"
    mock_geocode_text.assert_called_once()


@respx.mock
async def test_national_with_named_venue_keeps_venue() -> None:
    respx.get("http://test-nominatim/search").mock(
        return_value=Response(
            200, json=[{"lat": "37.9756", "lon": "23.7348", "display_name": "Προπύλαια, Αθήνα"}]
        )
    )
    with patch(
        "enrich.geocode._extract_locations_llm",
        return_value=[LocationMention(venue="Προπύλαια", city="Αθήνα")],
    ):
        results = await geocode_event(
            summary_el="Πανελλαδική απεργία, συγκέντρωση στα Προπύλαια",
            article_titles=["Συγκέντρωση στα Προπύλαια"],
            nominatim_url="http://test-nominatim",
        )
    assert results  # venue pin wins, national scope doesn't suppress a real venue
    assert results[0].region_code == "Attica"
    assert results[0].location_name == "Προπύλαια"
