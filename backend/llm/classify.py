"""
backend/llm/classify.py

Zero-shot embedding-based reaction category classification.

Classification uses cosine similarity between the event cluster's title
embedding and pre-computed category description embeddings.  No external
API calls are made; the project's own sentence-transformer model is reused.

When embedding confidence is HIGH the result is accepted directly.
When confidence is MEDIUM or LOW, the LLM summarization step in
``summarize.py`` handles re-classification via the full prompt in a single
combined API call (see ``_run_enrich_clusters`` in ``pipeline.py``).
"""

from __future__ import annotations

import logging
from typing import Literal

import numpy as np
from pydantic import BaseModel, field_validator

from backend.llm.config import (
    REACTION_CATEGORIES,
    CATEGORY_DESCRIPTIONS,
)

logger = logging.getLogger(__name__)

# Lazily computed category embeddings (one vector per category).
_CATEGORY_EMBEDDINGS: dict[str, np.ndarray] | None = None


# ---------------------------------------------------------------------------
# Structured output schema
# ---------------------------------------------------------------------------

class ClassificationResult(BaseModel):
    category: str
    confidence: Literal["high", "medium", "low"] = "medium"
    rationale: str = ""

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        # Accept exact match or closest prefix match (LLM may omit the emoji/ampersand).
        for cat in REACTION_CATEGORIES:
            if v.strip().lower() == cat.lower():
                return cat
        # Fallback: pick the category whose leading word appears in the value.
        v_lower = v.lower()
        for cat in REACTION_CATEGORIES:
            if cat.split()[0].lower() in v_lower:
                return cat
        # Give up and return as-is; the pipeline will log a warning.
        return v


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------


def _get_category_embeddings() -> dict[str, np.ndarray]:
    """
    Return the per-category embedding vectors, computing and caching them on
    first call.  Embeddings are L2-normalised (cosine sim = dot product).
    """
    global _CATEGORY_EMBEDDINGS
    if _CATEGORY_EMBEDDINGS is not None:
        return _CATEGORY_EMBEDDINGS

    # Import here to avoid loading the model at module import time.
    from backend.nlp.embeddings import embed_texts  # noqa: PLC0415

    logger.info("[classify] Computing category embeddings for zero-shot classifier…")
    categories = list(CATEGORY_DESCRIPTIONS.keys())
    descriptions = [CATEGORY_DESCRIPTIONS[c] for c in categories]
    vectors = embed_texts(descriptions)  # already L2-normalised
    _CATEGORY_EMBEDDINGS = {cat: np.array(vec, dtype=np.float32) for cat, vec in zip(categories, vectors)}
    logger.info("[classify] Category embeddings ready (%d categories).", len(_CATEGORY_EMBEDDINGS))
    return _CATEGORY_EMBEDDINGS


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_event(titles: list[str]) -> ClassificationResult | None:
    """Alias for classify_event_embedding() for backwards compatibility."""
    return classify_event_embedding(titles)


def classify_event_embedding(titles: list[str]) -> ClassificationResult | None:
    """
    Zero-shot classification using cosine similarity between the cluster's
    title embedding and pre-computed category description embeddings.

    No external API calls are made; uses the project's own sentence-transformer
    model (already loaded by the NLP phase).

    Parameters
    ----------
    titles : list[str]
        Article titles from one cluster (up to 20 used).

    Returns
    -------
    ClassificationResult | None
        Best-matching category with similarity-derived confidence,
        or None on failure.
    """
    if not titles:
        return None

    try:
        from backend.nlp.embeddings import embed_texts  # noqa: PLC0415

        combined = " ".join(titles[:20])
        vecs = embed_texts([combined])  # shape: (1, dim), L2-normalised
        query_vec = np.array(vecs[0], dtype=np.float32)

        cat_embeddings = _get_category_embeddings()
        best_cat = ""
        best_sim = -1.0
        for cat, cat_vec in cat_embeddings.items():
            sim = float(np.dot(query_vec, cat_vec))
            if sim > best_sim:
                best_sim = sim
                best_cat = cat

        if best_sim > 0.50:
            confidence: Literal["high", "medium", "low"] = "high"
        elif best_sim > 0.35:
            confidence = "medium"
        else:
            confidence = "low"

        logger.debug(
            "[classify] Embedding zero-shot → %s (sim=%.3f, %s)",
            best_cat, best_sim, confidence,
        )
        return ClassificationResult(
            category=best_cat,
            confidence=confidence,
            rationale=f"Embedding similarity {best_sim:.3f}",
        )

    except Exception as exc:
        logger.error("[classify] Embedding classification failed: %s", exc)
        return None
