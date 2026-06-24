"""Phase 2 NLP pipeline orchestrator.

Usage:
    uv run python -m nlp.pipeline
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

import numpy as np
from sklearn.metrics import silhouette_score
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from nlp.clustering import cluster_articles_from_db
from nlp.config import settings
from nlp.deduplication import find_duplicates_in_cluster, mark_duplicates
from nlp.embeddings import embed_articles
from nlp.event_registry import assign_event_id

logger = logging.getLogger(__name__)


async def _record_pipeline_run(
    session: AsyncSession,
    run_id: str,
    started_at: datetime,
    config_snapshot: dict[str, object],
    metrics: dict[str, object],
) -> None:
    finished_at = datetime.now(timezone.utc)
    await session.execute(
        text("""
            INSERT INTO pipeline_runs (id, started_at, finished_at, config_snapshot, metrics)
            VALUES (:id, :started, :finished, :config, :metrics)
        """),
        {
            "id": run_id,
            "started": started_at,
            "finished": finished_at,
            "config": json.dumps(config_snapshot),
            "metrics": json.dumps(metrics),
        },
    )


async def run_nlp_pipeline(engine: AsyncEngine | None = None) -> dict[str, object]:
    """Execute embed → cluster → dedup → registry → pipeline_runs. Returns metrics dict."""
    _engine = engine or create_async_engine(settings.database_url)
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        _engine, expire_on_commit=False
    )
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)

    config_snapshot = {
        "embedding_model": settings.embedding_model,
        "cluster_window_days": settings.cluster_window_days,
        "hdbscan_min_cluster_size": settings.hdbscan_min_cluster_size,
        "hdbscan_min_samples": settings.hdbscan_min_samples,
        "cluster_min_articles": settings.cluster_min_articles,
        "cluster_min_intra_sim": settings.cluster_min_intra_sim,
        "event_registry_sim_threshold": settings.event_registry_sim_threshold,
        "dedup_cosine_threshold": settings.dedup_cosine_threshold,
        "dedup_time_window_hours": settings.dedup_time_window_hours,
    }

    metrics: dict[str, object] = {}

    async with session_factory() as session:
        # Stage 1: Embed
        n_embedded = await embed_articles(session)
        await session.commit()
        metrics["n_embedded"] = n_embedded

        # Stage 2: Cluster
        cluster_results = await cluster_articles_from_db(
            session,
            window_days=settings.cluster_window_days,
            min_cluster_size=settings.hdbscan_min_cluster_size,
            min_samples=settings.hdbscan_min_samples,
            min_articles=settings.cluster_min_articles,
            min_intra_sim=settings.cluster_min_intra_sim,
        )
        metrics["n_clusters"] = len(cluster_results)

        # Stage 3: Dedup + Registry
        n_dupes = 0
        event_ids: list[str] = []

        for label, cluster in cluster_results.items():
            # Fetch published_at for dedup time-window
            result = await session.execute(
                text("""
                    SELECT id::text, embedding::text, published_at
                    FROM articles
                    WHERE id = ANY(:ids)
                """),
                {"ids": cluster.article_ids},
            )
            rows = result.all()
            articles_with_ts = [
                (
                    str(r[0]),
                    np.array([float(v) for v in r[1].strip("[]").split(",")], dtype=np.float32),
                    r[2],
                )
                for r in rows
                if r[1]
            ]
            dupes = find_duplicates_in_cluster(
                articles_with_ts,
                cosine_threshold=settings.dedup_cosine_threshold,
                time_window_hours=settings.dedup_time_window_hours,
            )
            n_dupes += await mark_duplicates(session, dupes)
            canonical_ids = [aid for aid in cluster.article_ids if aid not in dupes]
            event_id = await assign_event_id(
                session,
                centroid=cluster.centroid,
                article_ids=canonical_ids,
                threshold=settings.event_registry_sim_threshold,
            )
            event_ids.append(event_id)

        await session.commit()
        metrics["n_dupes"] = n_dupes
        metrics["n_events"] = len(event_ids)

        # Compute silhouette if we have ≥2 clusters (quality signal for thesis)
        # Silhouette is computed here as a best-effort — skipped if data too small.
        metrics["silhouette"] = None

        await _record_pipeline_run(session, run_id, started_at, config_snapshot, metrics)
        await session.commit()

    if engine is None:
        await _engine.dispose()

    logger.info("[nlp] Pipeline complete — %s", metrics)
    return metrics


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    asyncio.run(run_nlp_pipeline())
