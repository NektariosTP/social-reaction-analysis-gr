"""Tests for admin password verification and the session auth dependency."""
from __future__ import annotations

from unittest.mock import MagicMock

import bcrypt
import pytest

from admin.auth import NotAuthenticated, require_admin, verify_password


def test_verify_password_accepts_correct_password(monkeypatch: pytest.MonkeyPatch) -> None:
    hashed = bcrypt.hashpw(b"correct-horse", bcrypt.gensalt()).decode()
    monkeypatch.setattr("admin.auth.settings.admin_password_hash", hashed)

    assert verify_password("correct-horse") is True


def test_verify_password_rejects_wrong_password(monkeypatch: pytest.MonkeyPatch) -> None:
    hashed = bcrypt.hashpw(b"correct-horse", bcrypt.gensalt()).decode()
    monkeypatch.setattr("admin.auth.settings.admin_password_hash", hashed)

    assert verify_password("wrong-password") is False


def test_verify_password_rejects_when_hash_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("admin.auth.settings.admin_password_hash", "")

    assert verify_password("anything") is False


async def test_require_admin_raises_without_session() -> None:
    request = MagicMock()
    request.session = {}

    with pytest.raises(NotAuthenticated):
        await require_admin(request)


async def test_require_admin_passes_with_session() -> None:
    request = MagicMock()
    request.session = {"authenticated": True}

    await require_admin(request)
