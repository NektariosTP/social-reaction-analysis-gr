"""Tests for /login and /logout."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from admin.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_login_form_renders(client: AsyncClient) -> None:
    resp = await client.get("/login")
    assert resp.status_code == 200
    assert "Password" in resp.text


async def test_login_with_correct_password_sets_session_and_redirects(
    client: AsyncClient,
) -> None:
    with patch("admin.routes.login.verify_password", return_value=True):
        resp = await client.post(
            "/login", data={"password": "correct"}, follow_redirects=False
        )

    assert resp.status_code == 303
    assert resp.headers["location"] == "/events?status=pending_review"


async def test_login_with_wrong_password_shows_error(client: AsyncClient) -> None:
    with patch("admin.routes.login.verify_password", return_value=False):
        resp = await client.post("/login", data={"password": "wrong"})

    assert resp.status_code == 401
    assert "Wrong password" in resp.text


async def test_logout_clears_session_and_redirects(client: AsyncClient) -> None:
    resp = await client.post("/logout", follow_redirects=False)

    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"
