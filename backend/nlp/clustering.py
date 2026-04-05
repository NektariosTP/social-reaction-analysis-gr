"""
backend/nlp/clustering.py

Event clustering via HDBSCAN over article embeddings.

Groups articles from multiple sources that report on the same real-world
social reaction event.  Each cluster is assigned a unique ``cluster_id``
that is written back to the vector store metadata.

Records labelled -1 by HDBSCAN are considered noise (no cluster assignment).
"""

from __future__ import annotations

import logging

import numpy as np
import hdbscan
from sklearn.metrics import silhouette_score

from backend.nlp.config import (
    HDBSCAN_MIN_CLUSTER_SIZE,
    HDBSCAN_MIN_SAMPLES,
    CLUSTER_MIN_ARTICLES,
    CLUSTER_MIN_INTRA_SIM,
)
from backend.nlp.event_registry import EventRegistry
from backend.nlp import vectorstore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def cluster_articles() -> dict[str, int]:
    """
    Run HDBSCAN over all article embeddings in the vector store and assign
    cluster labels.

    Returns
    -------
    dict[str, int]
        Mapping of record id → cluster_id (-1 = noise / unclustered).
    """
    data = vectorstore.get_all(include=["embeddings", "metadatas"])
    ids: list[str] = data["ids"]
    embeddings = data["embeddings"]

    if not ids or embeddings is None or len(embeddings) == 0:
        logger.warning("[clustering] No records in vector store — nothing to cluster.")
        return {}

    X = np.array(embeddings, dtype=np.float32)
    logger.info(
        "[clustering] Running HDBSCAN on %d records (min_cluster_size=%d, min_samples=%d).",
        len(ids),
        HDBSCAN_MIN_CLUSTER_SIZE,
        HDBSCAN_MIN_SAMPLES,
    )

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=HDBSCAN_MIN_CLUSTER_SIZE,
        min_samples=HDBSCAN_MIN_SAMPLES,
        metric="euclidean",  # embeddings are L2-normalised → euclidean works well
    )
    labels = clusterer.fit_predict(X)

    # Build the id → cluster_id mapping
    id_to_cluster: dict[str, int] = {}
    for rec_id, label in zip(ids, labels):
        id_to_cluster[rec_id] = int(label)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int(np.sum(labels == -1))
    logger.info(
        "[clustering] Found %d clusters and %d noise records.",
        n_clusters,
        n_noise,
    )

    # ------------------------------------------------------------------
    # Stable cross-run event IDs via EventRegistry
    # ------------------------------------------------------------------
    registry = EventRegistry()
    id_to_event_id: dict[str, str] = {}
    seen_event_ids: set[str] = set()

    unique_labels = [lbl for lbl in set(labels.tolist()) if lbl != -1]
    n_filtered: int = 0

    for label in unique_labels:
        member_indices = np.where(labels == label)[0]
        member_embeddings = X[member_indices]
        member_ids = [ids[int(i)] for i in member_indices]

        # ------------------------------------------------------------------
        # Post-clustering quality filter
        # ------------------------------------------------------------------
        if len(member_ids) < CLUSTER_MIN_ARTICLES:
            for rid in member_ids:
                id_to_cluster[rid] = -1
            n_filtered += 1
            continue

        if CLUSTER_MIN_INTRA_SIM > 0.0 and len(member_ids) > 1:
            sim_matrix = member_embeddings @ member_embeddings.T
            n_m = len(member_ids)
            upper_tri = sim_matrix[np.triu_indices(n_m, k=1)]
            mean_intra = float(upper_tri.mean())
            if mean_intra < CLUSTER_MIN_INTRA_SIM:
                for rid in member_ids:
                    id_to_cluster[rid] = -1
                n_filtered += 1
                continue

        # L2-normalised centroid
        centroid = member_embeddings.mean(axis=0)
        norm = float(np.linalg.norm(centroid))
        if norm > 0:
            centroid = centroid / norm

        # Representative title: first non-empty title in the cluster
        rep_title = ""
        for idx in member_indices:
            t = (data["metadatas"][int(idx)] or {}).get("title", "")
            if t:
                rep_title = t
                break

        event_id = registry.assign(centroid, len(member_ids), rep_title)
        seen_event_ids.add(event_id)
        for rid in member_ids:
            id_to_event_id[rid] = event_id

    if n_filtered > 0:
        logger.info(
            "[clustering] Post-filter: %d cluster(s) demoted to noise "
            "(min_articles=%d, min_intra_sim=%.2f).",
            n_filtered,
            CLUSTER_MIN_ARTICLES,
            CLUSTER_MIN_INTRA_SIM,
        )
    closed = registry.close_unseen(seen_event_ids)
    registry.save()
    logger.info(
        "[clustering] Event registry: %d ongoing, %d newly closed.",
        registry.ongoing_count(),
        closed,
    )

    # ------------------------------------------------------------------
    # Cluster quality: silhouette score (uses post-filter labels)
    # ------------------------------------------------------------------
    post_filter_labels = np.array(
        [id_to_cluster[ids[i]] for i in range(len(ids))], dtype=np.int32
    )
    n_post_clusters = len(set(post_filter_labels.tolist())) - (1 if -1 in post_filter_labels else 0)
    if n_post_clusters > 1:
        non_noise_mask = post_filter_labels != -1
        if non_noise_mask.sum() >= 2:
            try:
                score = silhouette_score(
                    X[non_noise_mask], post_filter_labels[non_noise_mask], metric="cosine"
                )
                logger.info(
                    "[clustering] Silhouette score (cosine, non-noise records): %.4f",
                    score,
                )
            except Exception as exc:
                logger.warning("[clustering] Could not compute silhouette score: %s", exc)

    # ------------------------------------------------------------------
    # Write cluster_id + event_id back to vector store metadata
    # ------------------------------------------------------------------
    updated_metadatas: list[dict] = []
    for rec_id, meta in zip(ids, data["metadatas"]):
        meta_copy = dict(meta) if meta else {}
        meta_copy["cluster_id"] = id_to_cluster[rec_id]
        meta_copy["event_id"] = id_to_event_id.get(rec_id, "")
        updated_metadatas.append(meta_copy)

    vectorstore.update_metadatas(ids, updated_metadatas)

    return id_to_cluster


def get_cluster_summary() -> dict[int, list[str]]:
    """
    Return a mapping of cluster_id → list of record ids for all clusters.
    Noise records (cluster_id == -1) are included under key -1.
    """
    data = vectorstore.get_all(include=["metadatas"])
    ids: list[str] = data["ids"]
    metadatas: list[dict] = data["metadatas"]

    clusters: dict[int, list[str]] = {}
    for rec_id, meta in zip(ids, metadatas):
        cid = meta.get("cluster_id", -1)
        clusters.setdefault(cid, []).append(rec_id)

    return clusters
