"""Per-IP API rate limiting (SlowAPI).

Uses the mocked-DB `client` fixture from tests/conftest.py; `_fetch_events` is
patched so /events is cheap to hammer. The autouse `_reset_rate_limiter` fixture
guarantees each test starts with a fresh per-IP budget.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from api.config import settings

# Requests permitted per window, parsed from the configured limit (e.g. "60/minute").
_LIMIT = int(settings.rate_limit.split("/")[0])
_HEADERS_A = {"X-Forwarded-For": "203.0.113.7"}
_HEADERS_B = {"X-Forwarded-For": "198.51.100.9"}


async def test_events_returns_429_past_the_limit(client: AsyncClient) -> None:
    with patch("api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[]):
        oks = [(await client.get("/events", headers=_HEADERS_A)).status_code for _ in range(_LIMIT)]
        over = await client.get("/events", headers=_HEADERS_A)
    assert oks == [200] * _LIMIT
    assert over.status_code == 429


async def test_limit_is_per_client_ip(client: AsyncClient) -> None:
    """A second IP has its own budget — proves X-Forwarded-For keying."""
    with patch("api.routes.events._fetch_events", new_callable=AsyncMock, return_value=[]):
        for _ in range(_LIMIT):
            await client.get("/events", headers=_HEADERS_A)
        exhausted = await client.get("/events", headers=_HEADERS_A)
        fresh = await client.get("/events", headers=_HEADERS_B)
    assert exhausted.status_code == 429
    assert fresh.status_code == 200


async def test_health_is_exempt(client: AsyncClient) -> None:
    """/health must never be rate limited (Docker/uptime probes hit it often)."""
    statuses = [
        (await client.get("/health", headers=_HEADERS_A)).status_code
        for _ in range(_LIMIT + 5)
    ]
    assert statuses == [200] * (_LIMIT + 5)
