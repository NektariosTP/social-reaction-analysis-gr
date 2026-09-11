"""Tests for the admin event editor (GET/POST /events/{id})."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import IntegrityError

from admin.auth import require_admin
from admin.db import get_db
from admin.main import app
from admin.routes.events import _parse_event_time


@pytest.fixture
async def client():
    mock_session = AsyncMock()

    async def override_get_db():
        yield mock_session

    async def override_require_admin() -> None:
        return None

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin] = override_require_admin
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, mock_session
    app.dependency_overrides.clear()


def _valid_form() -> dict[str, object]:
    return {
        "action_forms": ["Απεργία/Στάση εργασίας"],
        "thematic_fields": ["Εργασιακό"],
        "channel": "Φυσικό (offline)",
        "intensity": "Ειρηνική",
        "status": "enriched",
        "summary_el": "Περίληψη",
        "summary_en": "Summary",
        "lat": "37.98",
        "lon": "23.72",
        "event_time": "",
        # is_national omitted -> unchecked
    }


def _captured_update_params(mock_session):
    """Return the params dict of the first execute() call whose SQL updates events."""
    for call in mock_session.execute.await_args_list:
        sql = str(call.args[0]).lower()
        if "update events set" in sql:
            return call.args[1]
    raise AssertionError("no UPDATE events call captured")


def test_parse_event_time_blank_is_none():
    assert _parse_event_time("") is None


def test_parse_event_time_naive_is_athens_local():
    dt = _parse_event_time("2026-09-01T18:30")
    assert dt == datetime(2026, 9, 1, 18, 30, tzinfo=ZoneInfo("Europe/Athens"))
    assert dt.tzinfo is not None


def test_parse_event_time_garbage_raises():
    with pytest.raises(ValueError):
        _parse_event_time("not-a-date")


async def test_edit_event_form_404_for_missing_event(client) -> None:
    c, mock_session = client
    result = MagicMock()
    result.first.return_value = None
    mock_session.execute = AsyncMock(return_value=result)

    resp = await c.get("/events/does-not-exist")

    assert resp.status_code == 404


async def test_edit_event_submit_rejects_invalid_axis_value(client) -> None:
    c, mock_session = client
    detail_result = MagicMock()
    detail_result.first.return_value = MagicMock(status="pending_review", event_time=None)
    empty_result = MagicMock()
    empty_result.all.return_value = []
    mock_session.execute = AsyncMock(side_effect=[detail_result, empty_result, empty_result])

    form = _valid_form()
    form["action_forms"] = ["Not a real axis value"]

    resp = await c.post("/events/evt-1", data=form)

    assert resp.status_code == 422


async def test_edit_event_form_renders_new_fields(client):
    c, mock_session = client
    detail = MagicMock()
    detail.first.return_value = MagicMock(
        id="evt-1", action_forms=[], thematic_fields=[], channel="Φυσικό (offline)",
        intensity="Ειρηνική", summary_el="", summary_en="", classification_confidence=None,
        lat=37.98, lon=23.72, article_count=1, source_count=1,
        first_seen=None, last_seen=None, status="pending_review",
        event_time=None, is_national=False,
    )
    locations = MagicMock()
    locations.all.return_value = []
    articles = MagicMock()
    articles.all.return_value = []
    reactions = MagicMock()
    reactions.all.return_value = []
    mock_session.execute = AsyncMock(side_effect=[detail, locations, articles, reactions])

    resp = await c.get("/events/evt-1")

    assert resp.status_code == 200
    body = resp.text
    assert 'name="event_time"' in body
    assert 'name="is_national"' in body
    assert 'name="actor_name"' in body  # reactions add form present


async def test_edit_event_submit_saves_valid_data(client) -> None:
    c, mock_session = client
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    resp = await c.post("/events/evt-1", data=_valid_form(), follow_redirects=False)

    assert resp.status_code == 303
    mock_session.commit.assert_awaited_once()


async def test_submit_persists_event_time_and_is_national(client):
    c, mock_session = client
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    form = _valid_form()
    form["event_time"] = "2026-09-01T18:30"
    form["is_national"] = "1"

    resp = await c.post("/events/evt-1", data=form, follow_redirects=False)

    assert resp.status_code == 303
    params = _captured_update_params(mock_session)
    assert params["is_national"] is True
    assert params["event_time"] == datetime(2026, 9, 1, 18, 30, tzinfo=ZoneInfo("Europe/Athens"))
    mock_session.commit.assert_awaited_once()


async def test_submit_rejects_unparseable_event_time(client):
    c, mock_session = client
    detail = MagicMock()
    detail.first.return_value = MagicMock(event_time=None)
    empty = MagicMock()
    empty.all.return_value = []
    # error-path re-fetch: detail, locations, articles
    mock_session.execute = AsyncMock(side_effect=[detail, empty, empty])
    form = _valid_form()
    form["event_time"] = "not-a-date"

    resp = await c.post("/events/evt-1", data=form)

    assert resp.status_code == 422


async def test_submit_persists_new_location(client):
    c, mock_session = client
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    form = _valid_form()
    # one new location row (blank loc_id -> INSERT)
    form["loc_id"] = ""
    form["loc_lat"] = "40.64"
    form["loc_lon"] = "22.94"
    form["loc_name"] = "Πλατεία"
    form["loc_city"] = "Θεσσαλονίκη"

    resp = await c.post("/events/evt-1", data=form, follow_redirects=False)

    assert resp.status_code == 303
    inserted = [
        call.args[1] for call in mock_session.execute.await_args_list
        if "insert into event_locations" in str(call.args[0]).lower()
    ]
    assert inserted and inserted[0]["city"] == "Θεσσαλονίκη"


async def test_add_reaction_inserts_and_redirects(client) -> None:
    c, mock_session = client
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    resp = await c.post(
        "/events/evt-1/reactions",
        data={"actor_name": "ΑΔΕΔΥ", "source_org": "adedy",
              "url": "http://adedy/1", "text": "Απεργία", "observed_at": ""},
        follow_redirects=False,
    )

    assert resp.status_code == 303
    assert resp.headers["location"] == "/events/evt-1"
    inserted = [
        call.args[1] for call in mock_session.execute.await_args_list
        if "insert into event_reactions" in str(call.args[0]).lower()
    ]
    assert inserted and inserted[0]["actor"] == "ΑΔΕΔΥ"
    mock_session.commit.assert_awaited_once()


async def test_add_reaction_conflict_rerenders_422(client) -> None:
    c, mock_session = client
    detail = MagicMock()
    detail.first.return_value = MagicMock(
        id="evt-1", action_forms=[], thematic_fields=[], channel="Φυσικό (offline)",
        intensity="Ειρηνική", summary_el="", summary_en="", classification_confidence=None,
        lat=None, lon=None, article_count=0, source_count=1,
        first_seen=None, last_seen=None, status="detected",
        event_time=None, is_national=False,
    )
    empty = MagicMock(); empty.all.return_value = []
    mock_session.execute = AsyncMock(
        side_effect=[IntegrityError("x", {}, Exception()), detail, empty, empty, empty]
    )
    mock_session.rollback = AsyncMock()

    resp = await c.post(
        "/events/evt-1/reactions",
        data={"actor_name": "ΑΔΕΔΥ", "source_org": "adedy",
              "url": "http://dup/1", "text": "x", "observed_at": ""},
    )

    assert resp.status_code == 422
    mock_session.rollback.assert_awaited_once()


async def test_edit_reaction_updates_and_redirects(client) -> None:
    c, mock_session = client
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    resp = await c.post(
        "/events/evt-1/reactions/r-9",
        data={"actor_name": "ΠΑΜΕ", "source_org": "pame",
              "url": "http://pame/1", "text": "y", "observed_at": ""},
        follow_redirects=False,
    )

    assert resp.status_code == 303
    updated = [
        call.args[1] for call in mock_session.execute.await_args_list
        if "update event_reactions" in str(call.args[0]).lower()
    ]
    assert updated and updated[0]["rid"] == "r-9" and updated[0]["eid"] == "evt-1"


async def test_delete_reaction_deletes_and_redirects(client) -> None:
    c, mock_session = client
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    resp = await c.post("/events/evt-1/reactions/r-9/delete", follow_redirects=False)

    assert resp.status_code == 303
    deleted = [
        call.args[1] for call in mock_session.execute.await_args_list
        if "delete from event_reactions" in str(call.args[0]).lower()
    ]
    assert deleted and deleted[0]["rid"] == "r-9" and deleted[0]["eid"] == "evt-1"
