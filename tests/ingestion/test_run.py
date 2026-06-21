"""Tests for ingestion orchestrator."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ingestion.models import RawDocument
from ingestion.run import run_ingestion

_FAKE_DOC = RawDocument(
    source_id="test",
    source_type="rss",
    url="https://example.com/1",
    canonical_url="https://example.com/1",
    title="Απεργία σήμερα",
    body_text="Μεγάλη απεργία πραγματοποιείται σήμερα στο κέντρο της Αθήνας.",
    language="el",
    published_at=datetime(2026, 6, 13, 8, 0),
)

_IRRELEVANT_DOC = RawDocument(
    source_id="test",
    source_type="rss",
    url="https://example.com/2",
    canonical_url="https://example.com/2",
    title="Καλός καιρός αύριο",
    body_text="Αίθριος καιρός αναμένεται σε όλη τη χώρα.",
    language="el",
    published_at=None,
)


async def test_run_ingestion_returns_metrics() -> None:
    mock_connector = AsyncMock()
    mock_connector.fetch.return_value = [_FAKE_DOC]

    with (
        patch("ingestion.run.GoogleNewsConnector", return_value=mock_connector),
        patch("ingestion.run.upsert_article", new_callable=AsyncMock, return_value=True),
        patch("ingestion.run._make_session_factory") as mock_sf,
    ):
        mock_session = AsyncMock()
        mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_sf.return_value.__aexit__ = AsyncMock(return_value=None)

        metrics = await run_ingestion(engine=MagicMock())

    assert metrics["fetched"] >= 1
    assert metrics["inserted"] >= 1


async def test_run_ingestion_filters_irrelevant_docs() -> None:
    mock_news = AsyncMock()
    mock_news.fetch.return_value = [_IRRELEVANT_DOC]

    with (
        patch("ingestion.run.GoogleNewsConnector", return_value=mock_news),
        patch("ingestion.run.upsert_article", new_callable=AsyncMock, return_value=True) as mock_upsert,
        patch("ingestion.run._make_session_factory") as mock_sf,
    ):
        mock_session = AsyncMock()
        mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_sf.return_value.__aexit__ = AsyncMock(return_value=None)

        metrics = await run_ingestion(engine=MagicMock())

    mock_upsert.assert_not_called()
    assert metrics["inserted"] == 0
