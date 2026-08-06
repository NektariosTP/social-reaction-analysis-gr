"""Municipality (δήμος) derivation via ST_Covers against the municipalities table."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import respx
from httpx import Response

from enrich.geocode import GeocodeResult, LocationMention, geocode_event, municipality_for_point


async def test_municipality_for_point_returns_name_on_match() -> None:
    session = AsyncMock()
    result = MagicMock()
    result.first.return_value = ("Δήμος Αθηναίων",)
    session.execute = AsyncMock(return_value=result)

    name = await municipality_for_point(session, 37.9755, 23.7348)

    assert name == "Δήμος Αθηναίων"
    executed_sql = str(session.execute.await_args.args[0])
    assert "ST_Covers" in executed_sql
    assert "municipalities" in executed_sql


async def test_municipality_for_point_returns_none_when_no_match() -> None:
    session = AsyncMock()
    result = MagicMock()
    result.first.return_value = None
    session.execute = AsyncMock(return_value=result)

    assert await municipality_for_point(session, 0.0, 0.0) is None


async def test_municipality_for_point_fails_soft_on_db_error() -> None:
    session = AsyncMock()
    session.execute = AsyncMock(side_effect=RuntimeError("connection refused"))

    # A DB failure must degrade to None, not propagate (it would otherwise abort
    # the whole eval loop, taking region_accuracy/distance down with it).
    assert await municipality_for_point(session, 37.9755, 23.7348) is None


@respx.mock
async def test_geocode_event_stamps_municipality_when_session_given() -> None:
    respx.get("http://test-nominatim/search").mock(
        return_value=Response(
            200,
            json=[{"lat": "37.9755", "lon": "23.7348", "display_name": "Σύνταγμα, Αθήνα"}],
        )
    )
    session = AsyncMock()
    result = MagicMock()
    result.first.return_value = ("Δήμος Αθηναίων",)
    session.execute = AsyncMock(return_value=result)

    with patch(
        "enrich.geocode._extract_locations_llm",
        return_value=[LocationMention(venue="Σύνταγμα", city="Αθήνα")],
    ):
        results = await geocode_event(
            summary_el="Συγκέντρωση στο Σύνταγμα",
            article_titles=["Πορεία στην Αθήνα"],
            nominatim_url="http://test-nominatim",
            session=session,
        )

    assert results and results[0].municipality == "Δήμος Αθηναίων"


async def test_geocode_event_without_session_leaves_municipality_none() -> None:
    with patch(
        "enrich.geocode._extract_locations_llm",
        return_value=[LocationMention(city="Αθήνα", embassy_of="Ιράν")],
    ):
        results = await geocode_event(
            summary_el="Συγκέντρωση έξω από την Πρεσβεία του Ιράν",
            article_titles=["Διαμαρτυρία στην Αθήνα"],
        )
    assert results and results[0].municipality is None
