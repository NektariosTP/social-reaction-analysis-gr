# tests/enrich/test_regions.py
"""Point-in-polygon region derivation over the bundled 13-periphery GeoJSON."""
from __future__ import annotations

from unittest.mock import patch

import pytest
import respx
from httpx import Response

from enrich.geocode import region_for_point, LocationMention, geocode_event


def test_syntagma_is_attica() -> None:
    # Πλατεία Συντάγματος, Αθήνα
    assert region_for_point(37.9755, 23.7348) == "Attica"


def test_thessaloniki_is_central_macedonia() -> None:
    assert region_for_point(40.6401, 22.9444) == "Central Macedonia"


def test_heraklion_is_crete() -> None:
    assert region_for_point(35.3387, 25.1442) == "Crete"


def test_open_sea_is_none() -> None:
    # a point well south of Crete, outside every periphery
    assert region_for_point(33.0, 20.0) is None


@respx.mock
async def test_geocode_event_stamps_region_code() -> None:
    respx.get("http://test-nominatim/search").mock(
        return_value=Response(
            200,
            json=[{"lat": "37.9755", "lon": "23.7348", "display_name": "Σύνταγμα, Αθήνα"}],
        )
    )
    with patch(
        "enrich.geocode._extract_locations_llm",
        return_value=[LocationMention(venue="Σύνταγμα", city="Αθήνα")],
    ):
        results = await geocode_event(
            summary_el="Συγκέντρωση στο Σύνταγμα",
            article_titles=["Πορεία στην Αθήνα"],
            nominatim_url="http://test-nominatim",
        )
    assert results and results[0].region_code == "Attica"
