"""Incremental embedding stage: embed un-embedded articles → pgvector."""
from __future__ import annotations

import logging
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from nlp.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    logger.info("[embed] Loading model: %s", settings.embedding_model)
    return SentenceTransformer(settings.embedding_model)


async def embed_articles(session: AsyncSession) -> int:
    """Embed all articles where embedding IS NULL. Returns count of newly embedded rows."""
    result = await session.execute(
        text(
            "SELECT id, title, body_text FROM articles "
            "WHERE embedding IS NULL AND is_duplicate = FALSE "
            "ORDER BY ingested_at ASC"
        )
    )
    rows = result.scalars().all()
    if not rows:
        logger.info("[embed] No un-embedded articles found.")
        return 0

    logger.info("[embed] Embedding %d articles…", len(rows))
    model = _load_model()

    texts = [
        f"{r.title} {r.body_text}".strip() if r.title else r.body_text
        for r in rows
    ]
    embeddings: np.ndarray = model.encode(
        texts,
        batch_size=settings.embedding_batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
    )

    for row, vec in zip(rows, embeddings):
        await session.execute(
            text(
                "UPDATE articles SET embedding = :vec::vector WHERE id = :id"
            ),
            {"vec": f"[{','.join(str(v) for v in vec.tolist())}]", "id": str(row.id)},
        )

    await session.flush()
    logger.info("[embed] Embedded %d articles.", len(rows))
    return len(rows)
