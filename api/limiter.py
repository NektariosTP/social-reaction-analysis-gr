"""Shared SlowAPI rate limiter.

Lives in its own module (imported by both api.main and api.routes.health) so the
health route can mark itself exempt without a circular import back through
api.main.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from api.config import settings


def client_ip(request: Request) -> str:
    """Rate-limit key = the real client IP.

    The API runs behind Caddy, so ``request.client.host`` is the proxy's address
    and would put every visitor in one bucket. Caddy sets ``X-Forwarded-For``;
    trust its first hop (the original client), falling back to the direct peer.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    return get_remote_address(request)


limiter = Limiter(
    key_func=client_ip,
    default_limits=[settings.rate_limit] if settings.rate_limit_enabled else [],
    enabled=settings.rate_limit_enabled,
)
