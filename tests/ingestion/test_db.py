"""Tests for the ingestion DB upsert helper."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.exc import IntegrityError

from ingestion.db import upsert_article
from ingestion.models import RawDocument


def _doc() -> RawDocument:
    return RawDocument(
        source_id="google_news_rss",
        source_type="rss",
        url="https://example.gr/a",
        canonical_url="https://example.gr/a",
        title="Τίτλος",
        body_text="Σώμα",
        language="el",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _mock_session_with_nested() -> AsyncMock:
    session = AsyncMock()
    nested_cm = AsyncMock()
    nested_cm.__aenter__ = AsyncMock(return_value=None)
    nested_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin_nested = MagicMock(return_value=nested_cm)
    return session


async def test_upsert_article_returns_true_on_insert() -> None:
    session = _mock_session_with_nested()
    result = MagicMock()
    result.rowcount = 1
    session.execute = AsyncMock(return_value=result)

    inserted = await upsert_article(_doc(), session)

    assert inserted is True


async def test_upsert_article_returns_false_on_content_hash_conflict() -> None:
    session = _mock_session_with_nested()
    result = MagicMock()
    result.rowcount = 0
    session.execute = AsyncMock(return_value=result)

    inserted = await upsert_article(_doc(), session)

    assert inserted is False


async def test_upsert_article_returns_false_on_canonical_url_conflict() -> None:
    session = _mock_session_with_nested()
    session.execute = AsyncMock(
        side_effect=IntegrityError("INSERT", {}, Exception("duplicate canonical_url"))
    )

    inserted = await upsert_article(_doc(), session)

    assert inserted is False
