"""Foreign-location rejection + embassy mapping + point-in-Greece."""
from __future__ import annotations

from unittest.mock import patch

import respx
from httpx import Response

from enrich.geocode import (
    LocationMention,
    geocode_event,
    lookup_embassy,
    point_in_greece,
)


def test_point_in_greece_true_for_syntagma() -> None:
    assert point_in_greece(37.9755, 23.7348) is True


def test_point_in_greece_false_for_tehran() -> None:
    assert point_in_greece(35.6892, 51.3890) is False


@respx.mock
async def test_tehran_marked_foreign() -> None:
    # country lock removed → Nominatim now resolves real Tehran coords (outside Greece)
    respx.get("http://test-nominatim/search").mock(
        return_value=Response(
            200, json=[{"lat": "35.6892", "lon": "51.3890", "display_name": "Tehran, Iran"}]
        )
    )
    with patch(
        "enrich.geocode._extract_locations_llm",
        return_value=[LocationMention(city="Τεχεράνη")],
    ):
        results = await geocode_event(
            summary_el="Διαδήλωση στην Τεχεράνη",
            article_titles=["Ένταση στο Ιράν"],
            nominatim_url="http://test-nominatim",
        )
    assert results and results[0].is_foreign is True
    assert results[0].region_code is None


@respx.mock
async def test_llm_flagged_foreign_skips_nominatim() -> None:
    # Greece-only Nominatim can't resolve foreign places: it either finds
    # nothing or spuriously matches an unrelated same-named Greek entity.
    # An LLM-confirmed-foreign mention must never reach it.
    route = respx.get("http://test-nominatim/search").mock(
        return_value=Response(200, json=[])
    )
    with patch(
        "enrich.geocode._extract_locations_llm",
        return_value=[LocationMention(city="Μπολόνια", is_foreign=True)],
    ):
        results = await geocode_event(
            summary_el="Βίαια επεισόδια στη Μπολόνια",
            article_titles=["Επεισόδια στη Μπολόνια"],
            nominatim_url="http://test-nominatim",
        )
    assert not route.called
    assert results and results[0].is_foreign is True
    assert results[0].lat is None
    assert results[0].lon is None
    assert results[0].region_code is None


async def test_embassy_maps_to_athens_and_is_domestic() -> None:
    with patch(
        "enrich.geocode._extract_locations_llm",
        return_value=[LocationMention(city="Αθήνα", embassy_of="Ιράν")],
    ):
        results = await geocode_event(
            summary_el="Συγκέντρωση έξω από την Πρεσβεία του Ιράν",
            article_titles=["Διαμαρτυρία στην Αθήνα"],
            nominatim_url="http://test-nominatim",
        )
    assert results
    assert results[0].is_foreign is False
    assert results[0].region_code == "Attica"


def test_lookup_embassy_known() -> None:
    r = lookup_embassy("Ιράν")
    assert r is not None and point_in_greece(r.lat, r.lon)
