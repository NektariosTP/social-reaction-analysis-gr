"""
backend/nlp/embeddings.py

Text embedding generation using sentence-transformers.

Loads a multilingual model once and provides batch encoding of text strings
into dense vector embeddings suitable for similarity search and clustering.
"""

from __future__ import annotations

import logging

from sentence_transformers import SentenceTransformer

from backend.nlp.config import EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE, EMBEDDING_MAX_SEQ_LENGTH, EMBEDDING_PROMPT_PREFIX

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model singleton — loaded once, shared across all callers
# ---------------------------------------------------------------------------

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the sentence-transformer model."""
    global _model
    if _model is None:
        logger.info("[embeddings] Loading model: %s", EMBEDDING_MODEL)
        _model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
        _model.max_seq_length = EMBEDDING_MAX_SEQ_LENGTH
        logger.info(
            "[embeddings] Model loaded (dim=%d, max_seq_length=%d).",
            _model.get_sentence_embedding_dimension(),
            _model.max_seq_length,
        )
    return _model


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Encode a list of text strings into dense vector embeddings.

    Parameters
    ----------
    texts : list[str]
        Raw text strings (e.g. ``title + " " + body``).

    Returns
    -------
    list[list[float]]
        One embedding vector per input text. Dimension matches the
        configured model (logged at load time by _get_model()).
    """
    if not texts:
        return []

    model = _get_model()
    if EMBEDDING_PROMPT_PREFIX:
        texts = [EMBEDDING_PROMPT_PREFIX + t for t in texts]
    embeddings = model.encode(
        texts,
        batch_size=EMBEDDING_BATCH_SIZE,
        show_progress_bar=len(texts) > EMBEDDING_BATCH_SIZE,
        normalize_embeddings=True,  # L2-normalised → cosine sim = dot product
    )
    return embeddings.tolist()


def embedding_dimension() -> int:
    """Return the dimensionality of the embedding vectors."""
    return _get_model().get_sentence_embedding_dimension()
