"""Password check and session-based auth dependency for the admin app."""
from __future__ import annotations

import bcrypt
from fastapi import Request

from admin.config import settings


class NotAuthenticated(Exception):
    """Raised by require_admin when there is no valid admin session."""


def verify_password(password: str) -> bool:
    if not settings.admin_password_hash:
        return False
    return bcrypt.checkpw(
        password.encode("utf-8"), settings.admin_password_hash.encode("utf-8")
    )


async def require_admin(request: Request) -> None:
    if not request.session.get("authenticated"):
        raise NotAuthenticated()
