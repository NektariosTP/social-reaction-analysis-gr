"""
backend/nlp/deduplication.py

Cross-source duplicate detection within event clusters.

After clustering, articles within the same cluster may originate from
different sources but describe the identical event.  This module identifies
such duplicates using cosine similarity + temporal proximity and marks
them in the vector store metadata.

Deduplication strategy:
  1. For each cluster, compute pairwise cosine similarity between all
     member embeddings.
  2. Pairs exceeding DEDUP_SIMILARITY_THRESHOLD *and* within
     DEDUP_MAX_TIME_DIFF_HOURS are linked as duplicates.
  3. Connected components within each cluster form "duplicate groups".
  4. The first record (by scraped_at) in each group is kept as the
     canonical representative; the rest are marked ``is_duplicate=True``
     with a ``canonical_id`` pointing to the representative.
"""

from __future__ import annotations

import logging
from datetime import datetime
from collections import defaultdict

import numpy as np

from backend.nlp.config import DEDUP_SIMILARITY_THRESHOLD, DEDUP_MAX_TIME_DIFF_HOURS
from backend.nlp import vectorstore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_datetime(dt_str: str | None) -> datetime | None:
    """Parse an ISO 8601 datetime string; return None on failure."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None


def _time_close(dt_a: datetime | None, dt_b: datetime | None) -> bool:
    """Return True if both datetimes are within DEDUP_MAX_TIME_DIFF_HOURS."""
    if dt_a is None or dt_b is None:
        # If either timestamp is missing, allow the pair (rely on similarity alone).
        return True
    diff_hours = abs((dt_a - dt_b).total_seconds()) / 3600.0
    return diff_hours <= DEDUP_MAX_TIME_DIFF_HOURS


def _connected_components(edges: list[tuple[int, int]], n: int) -> list[list[int]]:
    """Union-Find to compute connected components from edge pairs."""
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for a, b in edges:
        union(a, b)

    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)

    return list(groups.values())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def deduplicate_clusters() -> dict[str, str | None]:
    """
    Detect and mark duplicate records within each cluster.

    Returns
    -------
    dict[str, str | None]
        Mapping of record id → canonical_id.
        None means the record is itself canonical (or unclustered).
    """
    data = vectorstore.get_all(include=["embeddings", "metadatas"])
    ids: list[str] = data["ids"]
    embeddings = data["embeddings"]
    metadatas: list[dict] = data["metadatas"]

    if not ids:
        logger.warning("[dedup] No records in vector store.")
        return {}

    # Group records by cluster_id
    cluster_members: dict[int, list[int]] = defaultdict(list)
    for idx, meta in enumerate(metadatas):
        cid = meta.get("cluster_id", -1)
        if cid != -1:
            cluster_members[cid].append(idx)

    # Result map: id → canonical_id (None = canonical or unclustered)
    canonical_map: dict[str, str | None] = {rid: None for rid in ids}
    total_duplicates = 0

    for cid, member_indices in cluster_members.items():
        if len(member_indices) < 2:
            continue

        # Compute pairwise cosine similarity within the cluster
        emb_matrix = np.array([embeddings[i] for i in member_indices], dtype=np.float32)
        # Embeddings are L2-normalised → cosine sim = dot product
        sim_matrix = emb_matrix @ emb_matrix.T

        # Find duplicate edges
        edges: list[tuple[int, int]] = []
        for i in range(len(member_indices)):
            dt_i = _parse_datetime(metadatas[member_indices[i]].get("scraped_at"))
            for j in range(i + 1, len(member_indices)):
                if sim_matrix[i, j] >= DEDUP_SIMILARITY_THRESHOLD:
                    dt_j = _parse_datetime(metadatas[member_indices[j]].get("scraped_at"))
                    if _time_close(dt_i, dt_j):
                        edges.append((i, j))

        if not edges:
            continue

        # Connected components → duplicate groups
        groups = _connected_components(edges, len(member_indices))
        for group in groups:
            if len(group) < 2:
                continue

            # Sort by scraped_at (earliest first) to pick the canonical record
            group_sorted = sorted(
                group,
                key=lambda g: metadatas[member_indices[g]].get("scraped_at") or "",
            )
            canonical_idx = member_indices[group_sorted[0]]
            canonical_id = ids[canonical_idx]

            for g in group_sorted[1:]:
                dup_idx = member_indices[g]
                canonical_map[ids[dup_idx]] = canonical_id
                total_duplicates += 1

    # Write is_duplicate and canonical_id back to vector store metadata
    updated_ids: list[str] = []
    updated_metas: list[dict] = []

    for idx, rec_id in enumerate(ids):
        meta_copy = dict(metadatas[idx]) if metadatas[idx] else {}
        canon = canonical_map.get(rec_id)
        if canon is not None:
            meta_copy["is_duplicate"] = True
            meta_copy["canonical_id"] = canon
        else:
            meta_copy["is_duplicate"] = False
            meta_copy["canonical_id"] = ""
        updated_ids.append(rec_id)
        updated_metas.append(meta_copy)

    vectorstore.update_metadatas(updated_ids, updated_metas)

    logger.info(
        "[dedup] Marked %d duplicate records across %d clusters.",
        total_duplicates,
        len(cluster_members),
    )

    return canonical_map
