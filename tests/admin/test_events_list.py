"""Tests for the admin event queue/browse list and approve/reject actions."""
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


async def test_root_redirects_to_pending_review_queue(client) -> None:
    c, _ = client
    resp = await c.get("/", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/events?status=pending_review"


async def test_list_events_defaults_to_pending_review_filter(client) -> None:
    c, mock_session = client
    result = MagicMock()
    result.all.return_value = []
    mock_session.execute = AsyncMock(return_value=result)

    resp = await c.get("/events")

    assert resp.status_code == 200
    executed_sql = str(mock_session.execute.call_args[0][0])
    assert "status = :status" in executed_sql


async def test_list_events_empty_status_shows_all(client) -> None:
    c, mock_session = client
    result = MagicMock()
    result.all.return_value = []
    mock_session.execute = AsyncMock(return_value=result)

    resp = await c.get("/events", params={"status": ""})

    assert resp.status_code == 200
    executed_sql = str(mock_session.execute.call_args[0][0])
    assert "status = :status" not in executed_sql


async def test_approve_event_sets_enriched_and_redirects(client) -> None:
    c, mock_session = client
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    resp = await c.post("/events/evt-1/approve", follow_redirects=False)

    assert resp.status_code == 303
    executed_sql = str(mock_session.execute.call_args[0][0])
    assert "status = 'enriched'" in executed_sql
    mock_session.commit.assert_awaited_once()


async def test_reject_event_sets_rejected_and_redirects(client) -> None:
    c, mock_session = client
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    resp = await c.post("/events/evt-1/reject", follow_redirects=False)

    assert resp.status_code == 303
    executed_sql = str(mock_session.execute.call_args[0][0])
    assert "status = 'rejected'" in executed_sql
