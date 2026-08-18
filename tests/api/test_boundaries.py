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


from types import SimpleNamespace


def _muni_row(name: str, region_code: str, geometry: str):
    return SimpleNamespace(name=name, region_code=region_code, geometry=geometry)


async def test_municipalities_filters_by_periphery(client: AsyncClient) -> None:
    rows = [_muni_row("Δήμος Αθηναίων", "Attica", '{"type":"Polygon","coordinates":[[[23.7,38.0],[23.8,38.0],[23.8,38.1],[23.7,38.0]]]}')]
    with patch("api.routes.boundaries._fetch_municipalities", new_callable=AsyncMock, return_value=rows):
        resp = await client.get("/boundaries/municipalities?periphery=Attica")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["name"] == "Δήμος Αθηναίων"
    assert data["features"][0]["geometry"]["type"] == "Polygon"


async def test_municipalities_unknown_periphery_is_empty(client: AsyncClient) -> None:
    with patch("api.routes.boundaries._fetch_municipalities", new_callable=AsyncMock, return_value=[]):
        resp = await client.get("/boundaries/municipalities?periphery=Nowhere")
    assert resp.status_code == 200
    assert resp.json()["features"] == []


async def test_municipalities_requires_periphery(client: AsyncClient) -> None:
    resp = await client.get("/boundaries/municipalities")
    assert resp.status_code == 422
