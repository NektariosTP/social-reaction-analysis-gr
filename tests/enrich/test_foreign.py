"""Foreign-location rejection + embassy mapping + point-in-Greece."""
from __future__ import annotations

from unittest.mock import patch

import respx
from httpx import Response

from enrich.geocode import (
    LocationMention,
    lookup_embassy,
    point_in_greece,
    resolve_locations,
)


def test_point_in_greece_true_for_syntagma() -> None:
    assert point_in_greece(37.9755, 23.7348) is True


def test_point_in_greece_false_for_tehran() -> None:
    assert point_in_greece(35.6892, 51.3890) is False


@respx.mock
async def test_tehran_marked_foreign() -> None:
    # Resolved Nominatim coords outside Greece → geofence flags is_foreign.
    respx.get("http://test-nominatim/search").mock(
        return_value=Response(
            200, json=[{"lat": "35.6892", "lon": "51.3890", "display_name": "Tehran, Iran"}]
        )
    )
    results = await resolve_locations(
        [LocationMention(city="Τεχεράνη")],
        national=False,
        nominatim_url="http://test-nominatim",
    )
    assert results and results[0].is_foreign is True


async def test_embassy_maps_to_athens_and_is_domestic() -> None:
    results = await resolve_locations(
        [LocationMention(city="Αθήνα", embassy_of="Ιράν")],
        national=False,
        nominatim_url="http://test-nominatim",
    )
    assert results
    assert results[0].is_foreign is False


def test_lookup_embassy_known() -> None:
    r = lookup_embassy("Ιράν")
    assert r is not None and point_in_greece(r.lat, r.lon)
