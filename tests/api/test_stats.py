"""Tests for GET /stats."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


_FAKE_STATS = {
    "total_events": 42,
    "total_articles": 210,
    "by_action_form": [{"label": "Απεργία/Στάση εργασίας", "count": 15}],
    "by_thematic_field": [{"label": "Εργασιακό", "count": 20}],
    "by_channel": [{"label": "Φυσικό (offline)", "count": 30}],
    "by_intensity": [{"label": "Ειρηνική", "count": 35}],
    "by_region": [],
    "by_date": [],
}


async def test_stats_returns_200(client: AsyncClient) -> None:
    with patch("api.routes.stats._compute_stats", new_callable=AsyncMock, return_value=_FAKE_STATS):
        resp = await client.get("/stats")
    assert resp.status_code == 200


async def test_stats_response_shape(client: AsyncClient) -> None:
    with patch("api.routes.stats._compute_stats", new_callable=AsyncMock, return_value=_FAKE_STATS):
        resp = await client.get("/stats")
    data = resp.json()
    assert "total_events" in data
    assert "by_action_form" in data
    assert isinstance(data["by_action_form"], list)
    assert "by_date" in data
