"""Tests for the admin event delete action."""
from __future__ import annotations

from unittest.mock import AsyncMock

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


async def test_delete_event_issues_delete_and_redirects(client) -> None:
    c, mock_session = client
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    resp = await c.post("/events/evt-1/delete", follow_redirects=False)

    assert resp.status_code == 303
    assert resp.headers["location"] == "/events"
    executed_sql = str(mock_session.execute.call_args[0][0])
    assert "DELETE FROM events" in executed_sql
    mock_session.commit.assert_awaited_once()
