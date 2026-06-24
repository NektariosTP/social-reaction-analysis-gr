"""Tests for the incremental embedding stage."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from nlp.embeddings import embed_articles


async def test_embed_articles_skips_already_embedded() -> None:
    mock_session = AsyncMock()
    # Simulate: no un-embedded articles
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    with patch("nlp.embeddings._load_model") as mock_model:
        count = await embed_articles(mock_session)

    mock_model.assert_not_called()
    assert count == 0


async def test_embed_articles_calls_model_for_unembedded() -> None:
    mock_session = AsyncMock()

    fake_row = MagicMock()
    fake_row.id = "uuid-1"
    fake_row.title = "Απεργία στο Μετρό"
    fake_row.body_text = "Μεγάλη απεργία"

    mock_result = MagicMock()
    mock_result.all.return_value = [fake_row]
    mock_session.execute.return_value = mock_result

    fake_embedding = np.random.rand(768).astype(np.float32)
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([fake_embedding])

    with patch("nlp.embeddings._load_model", return_value=mock_model):
        count = await embed_articles(mock_session)

    assert count == 1
    mock_model.encode.assert_called_once()
