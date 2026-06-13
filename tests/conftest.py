"""Shared pytest fixtures."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from api.db import get_db
from api.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()

    async def override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
