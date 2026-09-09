"""Panhellenic-scope detection + venue-vs-no-venue geocoding suppression."""
from __future__ import annotations

import respx
from httpx import Response

from unittest.mock import patch

from enrich.geocode import LocationMention, detect_national_scope, geocode_event


def test_detects_panhellenic_keywords() -> None:
    assert detect_national_scope("Πανελλαδική απεργία στο εμπόριο") is True
    assert detect_national_scope("24ωρη απεργία της ΓΣΕΕ σε όλη τη χώρα") is True


def test_localized_event_not_national() -> None:
    assert detect_national_scope("Συγκέντρωση στα Προπύλαια για το μετρό Θεσσαλονίκης") is False
    assert detect_national_scope("Κατάληψη στο δημαρχείο Ηρακλείου") is False


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
    assert results[0].location_name == "Προπύλαια"
