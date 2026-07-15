"""Tests for the admin event editor (GET/POST /events/{id})."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from admin.auth import require_admin
from admin.db import get_db
from admin.main import app


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
        "region_code": "",
        "lat": "37.98",
        "lon": "23.72",
    }


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
    detail_result.first.return_value = MagicMock(status="pending_review")
    empty_result = MagicMock()
    empty_result.all.return_value = []
    mock_session.execute = AsyncMock(side_effect=[detail_result, empty_result, empty_result])

    form = _valid_form()
    form["action_forms"] = ["Not a real axis value"]

    resp = await c.post("/events/evt-1", data=form)

    assert resp.status_code == 422


async def test_edit_event_submit_saves_valid_data(client) -> None:
    c, mock_session = client
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    resp = await c.post("/events/evt-1", data=_valid_form(), follow_redirects=False)

    assert resp.status_code == 303
    mock_session.commit.assert_awaited_once()
