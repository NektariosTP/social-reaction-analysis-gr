"""Tests for /events, /events/{id}, /events/geojson.
M8 field exposure: event_time, temporal_status, is_national on event responses.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app
from api.routes.events import list_events

_ATHENS = ZoneInfo("Europe/Athens")

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
    municipality=None,
    article_count=5,
    source_count=3,
    first_seen=None,
    last_seen=None,
    status="enriched",
    classification_confidence=None,
    event_time=None,
    is_national=False,
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


def _row(**over):
    base = dict(
        id="evt-1", action_forms=["Απεργία/Στάση εργασίας"], thematic_fields=["Εργασιακό"],
        channel="Φυσικό", intensity="Ειρηνική", summary_el="ε", summary_en="e",
        lat=None, lon=None, region_code=None, municipality=None, article_count=3, source_count=2,
        first_seen=None, last_seen=None, status="enriched",
        event_time=None, is_national=True,
    )
    base.update(over)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_list_events_exposes_is_national_and_null_temporal_status() -> None:
    with patch("api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[_row()]):
        out = await list_events(db=AsyncMock())
    assert out[0].is_national is True
    assert out[0].event_time is None
    assert out[0].temporal_status is None


@pytest.mark.asyncio
async def test_list_events_derives_upcoming_for_future_event_time() -> None:
    future = datetime.now(_ATHENS) + timedelta(days=3)
    with patch(
        "api.routes.events._fetch_events",
        new_callable=AsyncMock,
        return_value=[_row(event_time=future, is_national=False)],
    ):
        out = await list_events(db=AsyncMock())
    assert out[0].temporal_status == "upcoming"
    assert out[0].is_national is False


from api.routes.events import _ORDER_BY_SQL, _TEMPORAL_DAY_OPS


def test_temporal_day_ops_cover_all_statuses() -> None:
    assert _TEMPORAL_DAY_OPS == {"upcoming": ">", "today": "=", "past": "<"}


def test_order_by_sql_maps_to_safe_fragments() -> None:
    assert "last_seen DESC" in _ORDER_BY_SQL["recent"]
    assert _ORDER_BY_SQL["event_time"] == "event_time ASC NULLS LAST"


@pytest.mark.asyncio
async def test_list_events_passes_temporal_params(client: AsyncClient) -> None:
    mock = AsyncMock(return_value=[])
    with patch("api.routes.events._fetch_events", mock):
        resp = await client.get("/events?temporal_status=today&is_national=true&order_by=event_time")
    assert resp.status_code == 200
    kwargs = mock.call_args.kwargs
    assert kwargs["temporal_status"] == "today"
    assert kwargs["is_national"] is True
    assert kwargs["order_by"] == "event_time"


@pytest.mark.asyncio
async def test_list_events_rejects_bad_temporal_status(client: AsyncClient) -> None:
    resp = await client.get("/events?temporal_status=tomorrow")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_events_rejects_bad_order_by(client: AsyncClient) -> None:
    resp = await client.get("/events?order_by=random")
    assert resp.status_code == 422


async def test_list_events_exposes_municipality(client: AsyncClient) -> None:
    row = MagicMock(**{**_FAKE_EVENT_ROW.__dict__, "municipality": "Δήμος Αθηναίων"})
    with patch("api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[row]):
        resp = await client.get("/events")
    assert resp.status_code == 200
    assert resp.json()[0]["municipality"] == "Δήμος Αθηναίων"


@pytest.mark.asyncio
async def test_list_events_passes_municipality_filter(client: AsyncClient) -> None:
    mock = AsyncMock(return_value=[])
    with patch("api.routes.events._fetch_events", mock):
        resp = await client.get("/events?municipality=Δήμος Αθηναίων")
    assert resp.status_code == 200
    assert mock.call_args.kwargs["municipality"] == "Δήμος Αθηναίων"


async def test_geojson_exposes_region_and_municipality(client: AsyncClient) -> None:
    row = MagicMock(**{**_FAKE_EVENT_ROW.__dict__, "region_code": "Attica", "municipality": "Δήμος Αθηναίων"})
    with patch("api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[row]):
        resp = await client.get("/events/geojson")
    props = resp.json()["features"][0]["properties"]
    assert props["region_code"] == "Attica"
    assert props["municipality"] == "Δήμος Αθηναίων"