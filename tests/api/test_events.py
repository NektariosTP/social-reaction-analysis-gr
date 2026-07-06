"""Tests for /events, /events/{id}, /events/geojson."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


_FAKE_EVENT_ROW = MagicMock(
    id="evt-uuid-1",
    action_forms=["Απεργία/Στάση εργασίας"],
    thematic_fields=["Εργασιακό"],
    channel="Φυσικό (offline)",
    intensity="Ειρηνική",
    summary_el="Απεργία στα νοσοκομεία.",
    summary_en="Hospital workers' strike.",
    lat=37.9838,
    lon=23.7275,
    region_code=None,
    article_count=5,
    source_count=3,
    first_seen=None,
    last_seen=None,
    status="enriched",
    classification_confidence=None,
)


async def test_list_events_returns_200(client: AsyncClient) -> None:
    with patch("api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[]):
        resp = await client.get("/events")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_events_returns_array(client: AsyncClient) -> None:
    with patch("api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[_FAKE_EVENT_ROW]):
        resp = await client.get("/events")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "evt-uuid-1"
    assert data[0]["channel"] == "Φυσικό (offline)"


async def test_list_events_filter_by_channel(client: AsyncClient) -> None:
    with patch("api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[_FAKE_EVENT_ROW]):
        resp = await client.get("/events?channel=Φυσικό (offline)")
    assert resp.status_code == 200


async def test_get_event_detail_returns_404_for_unknown(client: AsyncClient) -> None:
    with patch("api.routes.events._fetch_event_by_id", new_callable=AsyncMock, return_value=None):
        resp = await client.get("/events/nonexistent-id")
    assert resp.status_code == 404


async def test_get_event_detail_returns_200(client: AsyncClient) -> None:
    with patch("api.routes.events._fetch_event_by_id", new_callable=AsyncMock, return_value=_FAKE_EVENT_ROW):
        with patch("api.routes.events._fetch_event_articles", new_callable=AsyncMock, return_value=[]):
            resp = await client.get("/events/evt-uuid-1")
    assert resp.status_code == 200
    assert resp.json()["id"] == "evt-uuid-1"


async def test_geojson_returns_feature_collection(client: AsyncClient) -> None:
    with patch("api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[_FAKE_EVENT_ROW]):
        resp = await client.get("/events/geojson")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    assert isinstance(data["features"], list)


async def test_geojson_skips_events_without_coordinates(client: AsyncClient) -> None:
    no_coords = MagicMock(**{**_FAKE_EVENT_ROW.__dict__, "lat": None, "lon": None})
    with patch("api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[no_coords]):
        resp = await client.get("/events/geojson")
    assert resp.status_code == 200
    assert resp.json()["features"] == []


async def test_list_events_pagination(client: AsyncClient) -> None:
    with patch("api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[]):
        resp = await client.get("/events?limit=10&offset=0")
    assert resp.status_code == 200
