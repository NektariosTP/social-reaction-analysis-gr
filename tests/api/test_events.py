"""Tests for /events, /events/{id}, /events/geojson.
M8 field exposure: event_time, temporal_status, is_national on event responses.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app
from api.models import LocationPoint
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
            with patch("api.routes.events._fetch_event_reactions", new_callable=AsyncMock, return_value=[]):
                resp = await client.get("/events/evt-uuid-1")
    assert resp.status_code == 200
    assert resp.json()["id"] == "evt-uuid-1"


async def test_geojson_returns_feature_collection(client: AsyncClient) -> None:
    with patch("api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[_FAKE_EVENT_ROW]), \
         patch("api.routes.events._fetch_event_locations", new_callable=AsyncMock, return_value={}):
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
        lat=None, lon=None, article_count=3, source_count=2,
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


from api.routes.events import (
    _ORDER_BY_SQL,
    _TEMPORAL_DAY_OPS,
    _fetch_event_by_id,
    _fetch_events,
)


def _executed_sql(mock_session: AsyncMock) -> str:
    """The SQL text of the last execute() call on a mocked session."""
    return str(mock_session.execute.call_args.args[0])


@pytest.mark.asyncio
async def test_detail_query_derives_counts_from_attached_rows() -> None:
    """article_count/source_count must be counted live from the rows the UI lists,
    never read from the drift-prone stored events.* counter columns — otherwise a
    news-into-announcement merge leaves a phantom "1 άρθρα" over 0 real articles."""
    session = AsyncMock()
    session.execute.return_value = MagicMock(first=MagicMock(return_value=None))
    await _fetch_event_by_id(session, "evt-1")
    sql = _executed_sql(session)
    assert "count(*) FROM articles a" in sql
    assert "count(*) FROM event_reactions r" in sql
    assert "is_duplicate = FALSE" in sql
    # The stored counters must not be the display source.
    assert "article_count, source_count," not in sql
    # Union announcements count as articles: the article_count expression itself
    # folds in the event_reactions subquery.
    assert "+ (SELECT count(*) FROM event_reactions r WHERE r.event_id = events.id)) AS article_count" in sql


@pytest.mark.asyncio
async def test_list_query_derives_counts_from_attached_rows() -> None:
    session = AsyncMock()
    session.execute.return_value = MagicMock(all=MagicMock(return_value=[]))
    await _fetch_events(session, limit=10)
    sql = _executed_sql(session)
    assert "count(*) FROM articles a" in sql
    assert "count(*) FROM event_reactions r" in sql
    assert "article_count, source_count," not in sql
    assert "+ (SELECT count(*) FROM event_reactions r WHERE r.event_id = events.id)) AS article_count" in sql


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


async def test_geojson_embeds_locations(client: AsyncClient) -> None:
    locs = {
        "evt-uuid-1": [
            LocationPoint(lat=37.98, lon=23.72, label="Αθήνα", is_primary=True),
            LocationPoint(lat=40.64, lon=22.94, label="Θεσσαλονίκη", is_primary=False),
        ]
    }
    with patch("api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[_FAKE_EVENT_ROW]), \
         patch("api.routes.events._fetch_event_locations", new_callable=AsyncMock, return_value=locs):
        resp = await client.get("/events/geojson")
    assert resp.status_code == 200
    props = resp.json()["features"][0]["properties"]
    assert len(props["locations"]) == 2
    assert props["locations"][0]["is_primary"] is True
    assert props["locations"][1]["label"] == "Θεσσαλονίκη"


async def test_geojson_locations_empty_when_none(client: AsyncClient) -> None:
    with patch("api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[_FAKE_EVENT_ROW]), \
         patch("api.routes.events._fetch_event_locations", new_callable=AsyncMock, return_value={}):
        resp = await client.get("/events/geojson")
    assert resp.json()["features"][0]["properties"]["locations"] == []


async def test_get_event_detail_includes_reactions_in_observed_order(client: AsyncClient) -> None:
    r0 = MagicMock(id="r-1", actor_name="ΑΔΕΔΥ", source_org="adedy",
                   url="http://adedy/1", observed_at=None, text="Ανακοίνωση")
    r1 = MagicMock(id="r-2", actor_name="ΠΑΜΕ", source_org="pame",
                   url="http://pame/1", observed_at=None, text="Στήριξη")
    with patch("api.routes.events._fetch_event_by_id", new_callable=AsyncMock, return_value=_FAKE_EVENT_ROW):
        with patch("api.routes.events._fetch_event_articles", new_callable=AsyncMock, return_value=[]):
            with patch("api.routes.events._fetch_event_reactions", new_callable=AsyncMock, return_value=[r0, r1]):
                resp = await client.get("/events/evt-uuid-1")
    assert resp.status_code == 200
    data = resp.json()
    assert [x["actor_name"] for x in data["reactions"]] == ["ΑΔΕΔΥ", "ΠΑΜΕ"]
    assert data["reactions"][0]["url"] == "http://adedy/1"


from api.routes.events import _fetch_events, _fetch_event_by_id


def _mock_session_capturing():
    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = []
    result.first.return_value = None
    session.execute = AsyncMock(return_value=result)
    return session


@pytest.mark.asyncio
async def test_list_orders_announcer_by_seeded_reaction():
    session = _mock_session_capturing()
    await _fetch_events(session)
    sql = session.execute.call_args.args[0].text
    assert "match_method = 'seeded'" in sql
    assert "ORDER BY u.is_seed DESC, u.first_seen ASC" in sql


@pytest.mark.asyncio
async def test_detail_orders_announcer_by_seeded_reaction():
    session = _mock_session_capturing()
    await _fetch_event_by_id(session, "evt-1")
    sql = session.execute.call_args.args[0].text
    assert "match_method = 'seeded'" in sql
    assert "ORDER BY u.is_seed DESC, u.first_seen ASC" in sql


from api.routes.events import _fetch_event_reactions


@pytest.mark.asyncio
async def test_reactions_list_orders_seeded_reaction_first():
    # A union can have multiple event_reactions rows for the same event (e.g. a
    # 'seeded' announcement plus a later 'deduped' article). observed_at alone can
    # put the non-seeded row first, which mislabels the announcer downstream.
    session = _mock_session_capturing()
    await _fetch_event_reactions(session, "evt-1")
    sql = session.execute.call_args.args[0].text
    assert "ORDER BY (match_method = 'seeded') DESC, observed_at ASC NULLS LAST, created_at ASC" in sql


from api.routes.events import _parse_iso_date  # noqa: E402
from fastapi import HTTPException  # noqa: E402


@pytest.mark.asyncio
async def test_fetch_events_filters_by_event_date() -> None:
    session = _mock_session_capturing()
    await _fetch_events(session, event_date="2026-09-16")
    call = session.execute.call_args
    sql = call.args[0].text
    assert "(event_time AT TIME ZONE 'Europe/Athens')::date = :event_date" in sql
    assert call.args[1]["event_date"] == date(2026, 9, 16)


@pytest.mark.asyncio
async def test_fetch_events_day_filter_includes_archived_events() -> None:
    # The archival sweep (worker/archival.py) flips events to status='archived'
    # 24h after their event_time — which is often *before* a user time-travels
    # back to that day. Live (no event_date) must still hide archived events;
    # only the day-filtered query should see through the sweep.
    session = _mock_session_capturing()
    await _fetch_events(session, event_date="2026-09-15")
    sql = session.execute.call_args.args[0].text
    assert "status IN ('enriched', 'archived')" in sql


@pytest.mark.asyncio
async def test_fetch_events_live_excludes_archived_events() -> None:
    session = _mock_session_capturing()
    await _fetch_events(session)
    sql = session.execute.call_args.args[0].text
    assert "status = 'enriched'" in sql
    assert "archived" not in sql


@pytest.mark.asyncio
async def test_fetch_events_rejects_bad_event_date() -> None:
    session = _mock_session_capturing()
    with pytest.raises(HTTPException) as exc:
        await _fetch_events(session, event_date="not-a-date")
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_list_events_passes_event_date(client: AsyncClient) -> None:
    mock = AsyncMock(return_value=[])
    with patch("api.routes.events._fetch_events", mock):
        resp = await client.get("/events?event_date=2026-09-16")
    assert resp.status_code == 200
    assert mock.call_args.kwargs["event_date"] == "2026-09-16"


@pytest.mark.asyncio
async def test_geojson_passes_event_date(client: AsyncClient) -> None:
    mock = AsyncMock(return_value=[])
    with patch("api.routes.events._fetch_events", mock), \
         patch("api.routes.events._fetch_event_locations", new_callable=AsyncMock, return_value={}):
        resp = await client.get("/events/geojson?event_date=2026-09-16")
    assert resp.status_code == 200
    assert mock.call_args.kwargs["event_date"] == "2026-09-16"


@pytest.mark.asyncio
async def test_fetch_events_window_days_builds_past_only_hybrid_sql() -> None:
    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = []
    session.execute.return_value = result

    await _fetch_events(session, window_days=7)

    sql = str(session.execute.call_args.args[0])
    params = session.execute.call_args.args[1]
    # Past-only: excludes upcoming (event_time <= today) and reaches back N days.
    assert "make_interval" in sql
    assert "event_time IS NULL AND last_seen" in sql
    assert "<= (now() AT TIME ZONE 'Europe/Athens')::date" in sql
    assert params["window_days"] == 7
    # A preset opens up archived events, like the single-day path does.
    assert "status IN ('enriched', 'archived')" in sql


@pytest.mark.asyncio
async def test_fetch_events_event_date_overrides_window_days() -> None:
    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = []
    session.execute.return_value = result

    await _fetch_events(session, window_days=7, event_date="2026-09-18")

    sql = str(session.execute.call_args.args[0])
    params = session.execute.call_args.args[1]
    assert "window_days" not in params          # window ignored
    assert "make_interval" not in sql
    assert params["event_date"] == date(2026, 9, 18)


@pytest.mark.asyncio
async def test_list_events_passes_window_days(client: AsyncClient) -> None:
    with patch(
        "api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[]
    ) as mock:
        resp = await client.get("/events?window_days=15")
    assert resp.status_code == 200
    assert mock.await_args.kwargs["window_days"] == 15


async def test_geojson_passes_intensity(client: AsyncClient) -> None:
    mock = AsyncMock(return_value=[])
    with patch("api.routes.events._fetch_events", mock), \
         patch("api.routes.events._fetch_event_locations", new_callable=AsyncMock, return_value={}):
        resp = await client.get("/events/geojson?intensity=Ειρηνική")
    assert resp.status_code == 200
    assert mock.call_args.kwargs["intensity"] == "Ειρηνική"