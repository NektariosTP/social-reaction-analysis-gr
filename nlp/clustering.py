"""HDBSCAN clustering over article embeddings with configurable quality gates."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import hdbscan
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ClusterResult:
    article_ids: list[str]
    embeddings: np.ndarray
    centroid: np.ndarray
    intra_sim: float


def run_hdbscan(
    X: np.ndarray,
    min_cluster_size: int,
    min_samples: int,
) -> np.ndarray:
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
    )
    return np.asarray(clusterer.fit_predict(X))


def compute_intra_similarity(vecs: np.ndarray) -> float:
    n = len(vecs)
    if n < 2:
        return 1.0
    sim_matrix = vecs @ vecs.T
    upper = sim_matrix[np.triu_indices(n, k=1)]
    return float(upper.mean())


def apply_quality_gates(
    raw_clusters: dict[int, tuple[list[str], np.ndarray]],
    min_articles: int,
    min_intra_sim: float,
) -> dict[int, ClusterResult]:
    results: dict[int, ClusterResult] = {}
    for label, (ids, vecs) in raw_clusters.items():
        if len(ids) < min_articles:
            logger.debug("[cluster] label=%d rejected: %d < min_articles=%d", label, len(ids), min_articles)
            continue
        sim = compute_intra_similarity(vecs)
        if sim < min_intra_sim:
            logger.debug("[cluster] label=%d rejected: intra_sim=%.3f < %.3f", label, sim, min_intra_sim)
            continue
        centroid = vecs.mean(axis=0)
        norm = float(np.linalg.norm(centroid))
        if norm > 0:
            centroid = centroid / norm
        results[label] = ClusterResult(
            article_ids=ids,
            embeddings=vecs,
            centroid=centroid,
            intra_sim=sim,
        )
    return results


async def cluster_articles_from_db(
    session: object,
    window_days: int,
    min_cluster_size: int,
    min_samples: int,
    min_articles: int,
    min_intra_sim: float,
) -> dict[int, ClusterResult]:
    """Fetch embeddings from DB and run full cluster pipeline. Returns quality-gated results."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession

    assert isinstance(session, AsyncSession)
    result = await session.execute(
        text(
            """
            SELECT id, embedding::text
            FROM articles
            WHERE embedding IS NOT NULL
              AND is_duplicate = FALSE
              AND ingested_at >= NOW() - INTERVAL '1 day' * :window_days
            ORDER BY ingested_at ASC
            """
        ),
        {"window_days": window_days},
    )
    rows = result.all()
    if not rows:
        logger.info("[cluster] No embedded articles in window.")
        return {}

    ids = [str(r[0]) for r in rows]
    vecs = np.array(
        [[float(v) for v in r[1].strip("[]").split(",")] for r in rows],
        dtype=np.float32,
    )
    logger.info("[cluster] Running HDBSCAN on %d articles.", len(ids))
    labels = run_hdbscan(vecs, min_cluster_size, min_samples)

    raw: dict[int, tuple[list[str], list[np.ndarray]]] = {}
    for i, (article_id, label) in enumerate(zip(ids, labels)):
        if label == -1:
            continue
        if label not in raw:
            raw[label] = ([], [])
        raw[label][0].append(article_id)
        raw[label][1].append(vecs[i])

    raw_arrays = {k: (v[0], np.array(v[1])) for k, v in raw.items()}
    results = apply_quality_gates(raw_arrays, min_articles, min_intra_sim)

    n_noise = int((labels == -1).sum())
    logger.info(
        "[cluster] %d clusters (quality-gated from %d raw), %d noise.",
        len(results), len(raw), n_noise,
    )
    return results
