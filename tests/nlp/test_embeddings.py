"""Tests for the incremental embedding stage."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from nlp.embeddings import embed_articles, _chunk_words, _mean_pool, embed_texts


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


def test_chunk_words_short_text_single_chunk() -> None:
    assert _chunk_words("Σύντομο κείμενο.", chunk_words=100) == ["Σύντομο κείμενο."]


def test_chunk_words_splits_long_text() -> None:
    words = [f"λέξη{i}" for i in range(250)]
    chunks = _chunk_words(" ".join(words), chunk_words=100)
    assert len(chunks) == 3
    assert chunks[0].split() == words[:100]
    assert chunks[2].split() == words[200:]


def test_mean_pool_renormalizes_to_unit_vector() -> None:
    vecs = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    pooled = _mean_pool(vecs)
    assert abs(np.linalg.norm(pooled) - 1.0) < 1e-6


def test_mean_pool_weights_by_chunk_length() -> None:
    # a 100-word chunk and a 1-word leftover chunk must not be averaged equally —
    # the leftover chunk's direction should barely move the pooled vector.
    big = np.array([1.0, 0.0], dtype=np.float32)
    small = np.array([0.0, 1.0], dtype=np.float32)
    pooled = _mean_pool(np.array([big, small]), weights=[100, 1])
    assert pooled[0] > 0.99


def test_embed_texts_mean_pools_long_text_chunks() -> None:
    model = MagicMock()
    # text[0] is 1 chunk, text[1] is 2 identical chunks → 3 chunks total passed to encode()
    model.encode.return_value = np.array(
        [[1.0, 0.0], [0.0, 1.0], [0.0, 1.0]], dtype=np.float32
    )

    out = embed_texts(model, ["a b", "c d e f"], chunk_words=2)

    assert out.shape == (2, 2)
    assert np.allclose(out[0], [1.0, 0.0])
    assert np.allclose(out[1], [0.0, 1.0])
    encoded_texts = model.encode.call_args[0][0]
    assert len(encoded_texts) == 3  # confirms chunking happened, not a 1:1 pass-through
