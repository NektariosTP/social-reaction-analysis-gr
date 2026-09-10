"""Tests for resolve_locations (deterministic resolution of LLM place mentions)."""
from __future__ import annotations

import pytest

from enrich.geocode import GeocodeResult, LocationMention, resolve_locations


@pytest.mark.asyncio
async def test_national_without_venue_is_unlocated() -> None:
    out = await resolve_locations([LocationMention(city="Ελλάδα")], national=True)
    assert out == []


@pytest.mark.asyncio
async def test_unresolved_domestic_kept_with_null_coords(monkeypatch) -> None:
    async def fake_geocode_text(*args, **kwargs):
        return None  # Nominatim miss

    monkeypatch.setattr("enrich.geocode.geocode_text", fake_geocode_text)
    out = await resolve_locations(
        [LocationMention(venue="Άγνωστο Στέκι", city="Τρίκαλα")], national=False,
    )
    assert len(out) == 1
    assert out[0].lat is None and out[0].lon is None
    assert out[0].location_name == "Άγνωστο Στέκι"
    assert out[0].is_primary is True


@pytest.mark.asyncio
async def test_resolved_domestic_gets_coords(monkeypatch) -> None:
    async def fake_geocode_text(query, city=None, nominatim_url=None):
        return GeocodeResult(lat=37.97, lon=23.72, location_name="Σύνταγμα", city=city)

    monkeypatch.setattr("enrich.geocode.geocode_text", fake_geocode_text)
    out = await resolve_locations(
        [LocationMention(venue="Σύνταγμα", city="Αθήνα")], national=False,
    )
    assert out[0].lat == pytest.approx(37.97)
    assert out[0].is_primary is True


@pytest.mark.asyncio
async def test_llm_flagged_foreign_skips_nominatim(monkeypatch) -> None:
    # Greece-only Nominatim can't resolve foreign places: it either finds nothing
    # or spuriously matches an unrelated same-named Greek entity. An LLM-confirmed
    # foreign mention must never reach it.
    called = False

    async def fake_geocode_text(*args, **kwargs):
        nonlocal called
        called = True
        return GeocodeResult(lat=0.0, lon=0.0, location_name="wrong match")

    monkeypatch.setattr("enrich.geocode.geocode_text", fake_geocode_text)
    out = await resolve_locations(
        [LocationMention(city="Μπολόνια", is_foreign=True)], national=False,
    )
    assert called is False
    assert out[0].is_foreign is True
    assert out[0].lat is None and out[0].lon is None
