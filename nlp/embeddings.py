"""Incremental embedding stage: embed un-embedded articles → pgvector."""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import cast

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from nlp.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    logger.info("[embed] Loading model: %s", settings.embedding_model)
    return cast(SentenceTransformer, SentenceTransformer(settings.embedding_model, device="cpu"))


def _chunk_words(text: str, chunk_words: int | None = None) -> list[str]:
    n = chunk_words if chunk_words is not None else settings.embedding_chunk_words
    words = text.split()
    if not words:
        return [""]
    return [" ".join(words[i : i + n]) for i in range(0, len(words), n)]


def _mean_pool(vecs: np.ndarray, weights: list[int] | None = None) -> np.ndarray:
    """Pool chunk embeddings, weighted by chunk length. Without weights, a 100-word
    chunk and a 1-word leftover chunk would count equally and the leftover — often
    a stray sentence fragment — could drag the pooled direction off the dominant
    chunk's meaning."""
    w = None if weights is None else np.asarray(weights, dtype=np.float64)
    mean = np.average(vecs, axis=0, weights=w)
    norm = np.linalg.norm(mean)
    return mean / norm if norm > 0 else mean


def embed_texts(
    model: SentenceTransformer, texts: list[str], chunk_words: int | None = None
) -> np.ndarray:
    """Embed texts of any length. mpnet silently truncates past its 128-token
    max_seq_length (~100 Greek words), so texts longer than chunk_words are split
    into word-chunks, each embedded separately, then mean-pooled + renormalized
    back into one unit vector of the model's native dimension — no schema change."""
    chunk_lists = [_chunk_words(t, chunk_words) for t in texts]
    flat_chunks = [c for chunks in chunk_lists for c in chunks]
    flat_vecs = np.asarray(
        model.encode(
            flat_chunks,
            batch_size=settings.embedding_batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        ),
        dtype=np.float32,
    )
    out = np.empty((len(texts), flat_vecs.shape[1]), dtype=np.float32)
    offset = 0
    for i, chunks in enumerate(chunk_lists):
        n = len(chunks)
        out[i] = (
            flat_vecs[offset]
            if n == 1
            else _mean_pool(
                flat_vecs[offset : offset + n],
                weights=[len(c.split()) for c in chunks],
            )
        )
        offset += n
    return out


def embed_query(text: str) -> np.ndarray:
    """Embed a single short text into one L2-normalized vector.

    Reuses the cached model and the same chunk+mean-pool path as embed_texts,
    so reaction text lands in the same space as article/event centroids.
    """
    model = _load_model()
    return embed_texts(model, [text])[0]


async def embed_articles(session: AsyncSession) -> int:
    """Embed all articles where embedding IS NULL. Returns count of newly embedded rows."""
    result = await session.execute(
        text(
            "SELECT id, title, body_text FROM articles "
            "WHERE embedding IS NULL AND is_duplicate = FALSE "
            "ORDER BY ingested_at ASC"
        )
    )
    rows = result.all()
    if not rows:
        logger.info("[embed] No un-embedded articles found.")
        return 0

    logger.info("[embed] Embedding %d articles…", len(rows))
    model = _load_model()

    texts = [
        f"{r.title} {r.body_text}".strip() if r.title else r.body_text
        for r in rows
    ]
    embeddings: np.ndarray = embed_texts(model, texts)

    for row, vec in zip(rows, embeddings):
        await session.execute(
            text(
                "UPDATE articles SET embedding = CAST(:vec AS vector) WHERE id = :id"
            ),
            {"vec": f"[{','.join(str(v) for v in vec.tolist())}]", "id": str(row.id)},
        )

    await session.flush()
    logger.info("[embed] Embedded %d articles.", len(rows))
    return len(rows)
