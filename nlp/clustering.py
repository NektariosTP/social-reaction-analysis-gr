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
              AND event_id IS NULL
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


def single_pass_cluster(vectors: np.ndarray, tau: float) -> list[int]:
    """Greedy single-pass clustering by cosine similarity ≥ tau.

    Assumes L2-normalized row vectors (cosine == dot). Deterministic in row order:
    each vector joins the most-similar existing centroid if that similarity ≥ tau,
    else opens a new cluster. Joined centroids are updated by a count-weighted mean.
    """
    centroids: list[np.ndarray] = []
    counts: list[int] = []
    labels: list[int] = []
    for v in vectors:
        best_label = -1
        best_sim = -1.0
        for k, c in enumerate(centroids):
            sim = float(np.dot(v, c))
            if sim > best_sim:
                best_sim = sim
                best_label = k
        if best_label >= 0 and best_sim >= tau:
            n = counts[best_label]
            merged = (centroids[best_label] * n + v) / (n + 1)
            norm = float(np.linalg.norm(merged))
            centroids[best_label] = merged / norm if norm > 0 else merged
            counts[best_label] = n + 1
            labels.append(best_label)
        else:
            centroids.append(v.astype(np.float32))
            counts.append(1)
            labels.append(len(centroids) - 1)
    return labels


def find_merges(
    centroids: list[tuple[str, np.ndarray]],
    merge_threshold: float,
) -> list[tuple[str, str]]:
    """Return (absorbed_id, kept_id) pairs for event centroids with cosine ≥ threshold.

    Deterministic: for each close pair the later-listed event is absorbed into the
    earlier-listed one. Assumes L2-normalized centroids.
    """
    merges: list[tuple[str, str]] = []
    absorbed: set[str] = set()
    for i in range(len(centroids)):
        kept_id, kept_vec = centroids[i]
        if kept_id in absorbed:
            continue
        for j in range(i + 1, len(centroids)):
            other_id, other_vec = centroids[j]
            if other_id in absorbed:
                continue
            if float(np.dot(kept_vec, other_vec)) >= merge_threshold:
                merges.append((other_id, kept_id))
                absorbed.add(other_id)
    return merges


async def single_pass_cluster_from_db(
    session: object,
    window_days: int,
    tau: float,
    min_articles: int,
    min_intra_sim: float,
) -> dict[int, ClusterResult]:
    """DB-backed single-pass grouping of un-clustered articles. Drop-in for
    cluster_articles_from_db: returns the same quality-gated ClusterResult dict."""
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
              AND event_id IS NULL
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
    logger.info("[cluster] Single-pass over %d articles (tau=%.2f).", len(ids), tau)
    labels = single_pass_cluster(vecs, tau)

    raw: dict[int, tuple[list[str], list[np.ndarray]]] = {}
    for i, (article_id, label) in enumerate(zip(ids, labels)):
        raw.setdefault(label, ([], []))
        raw[label][0].append(article_id)
        raw[label][1].append(vecs[i])

    raw_arrays = {k: (v[0], np.array(v[1])) for k, v in raw.items()}
    results = apply_quality_gates(raw_arrays, min_articles, min_intra_sim)
    logger.info("[cluster] %d clusters (quality-gated from %d single-pass groups).",
                len(results), len(raw))
    return results
