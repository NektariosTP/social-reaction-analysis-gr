"""Tests for /boundaries/peripheries and /boundaries/municipalities."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_peripheries_returns_13_features(client: AsyncClient) -> None:
    resp = await client.get("/boundaries/peripheries")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 13


async def test_peripheries_feature_has_region_code_and_polygon(client: AsyncClient) -> None:
    resp = await client.get("/boundaries/peripheries")
    feat = resp.json()["features"][0]
    assert feat["properties"]["region_code"] == feat["properties"]["name"]
    assert feat["geometry"]["type"] in {"Polygon", "MultiPolygon"}
