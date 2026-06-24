"""Within-cluster cosine + time-window deduplication."""
from __future__ import annotations

import logging
from datetime import datetime

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def find_duplicates_in_cluster(
    articles: list[tuple[str, np.ndarray, datetime]],
    cosine_threshold: float,
    time_window_hours: int,
) -> set[str]:
    """
    Return IDs of articles that are duplicates within a single cluster.

    Strategy: sort by published_at ascending; the first occurrence is canonical.
    Later articles within the time window and above the cosine threshold are marked duplicate.
    """
    if len(articles) < 2:
        return set()

    sorted_arts = sorted(articles, key=lambda t: t[2] or datetime.min)
    duplicates: set[str] = set()

    for i, (id_i, vec_i, ts_i) in enumerate(sorted_arts):
        if id_i in duplicates:
            continue
        for j in range(i + 1, len(sorted_arts)):
            id_j, vec_j, ts_j = sorted_arts[j]
            if id_j in duplicates:
                continue
            if ts_i is not None and ts_j is not None:
                delta_h = abs((ts_j - ts_i).total_seconds()) / 3600.0
                if delta_h > time_window_hours:
                    continue
            cosine = float(np.dot(vec_i, vec_j))
            if cosine >= cosine_threshold:
                duplicates.add(id_j)

    return duplicates


async def mark_duplicates(
    session: AsyncSession,
    duplicates: set[str],
) -> int:
    """Set is_duplicate=TRUE for the given article IDs. Returns count updated."""
    if not duplicates:
        return 0
    for article_id in duplicates:
        await session.execute(
            text("UPDATE articles SET is_duplicate = TRUE WHERE id = :id"),
            {"id": article_id},
        )
    logger.info("[dedup] Marked %d duplicates.", len(duplicates))
    return len(duplicates)
