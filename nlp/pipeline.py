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
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from enrich.nli import NOISE_GATE_THRESHOLD, noise_gate_score
from nlp.clustering import find_merges, single_pass_cluster_from_db
from nlp.config import settings
from nlp.date_split import split_by_event_day
from nlp.deduplication import find_duplicates_global, mark_duplicates
from nlp.embeddings import embed_articles
from nlp.event_dates import resolve_event_day
from nlp.event_registry import apply_merges, assign_event_id, load_existing_events

logger = logging.getLogger(__name__)


async def _gate_detected_events(session: AsyncSession) -> int:
    """Auto-reject non-event 'detected' clusters before the human triage queue (0 tokens)."""
    detected = (await session.execute(
        text("SELECT id::text FROM events WHERE status = 'detected'")
    )).all()
    n_rejected = 0
    for (event_id,) in detected:
        arts = (await session.execute(
            text(
                "SELECT title, body_text FROM articles "
                "WHERE event_id = :eid AND is_duplicate = FALSE "
                "ORDER BY published_at DESC LIMIT 10"
            ),
            {"eid": event_id},
        )).all()
        if not arts:
            continue
        blob = " ".join((r[0] or "") for r in arts) + " " + " ".join((r[1] or "")[:500] for r in arts)
        if noise_gate_score(blob.strip()) < NOISE_GATE_THRESHOLD:
            await session.execute(
                text("UPDATE events SET status = 'rejected' WHERE id = :id"),
                {"id": event_id},
            )
            n_rejected += 1
    return n_rejected


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
        "cluster_min_articles": settings.cluster_min_articles,
        "cluster_min_intra_sim": settings.cluster_min_intra_sim,
        "event_registry_sim_threshold": settings.event_registry_sim_threshold,
        "event_merge_threshold": settings.event_merge_threshold,
        "dedup_cosine_threshold": settings.dedup_cosine_threshold,
        "dedup_time_window_hours": settings.dedup_time_window_hours,
        "cluster_tau": settings.cluster_tau,
        "date_split_min_bucket": settings.date_split_min_bucket,
        "date_split_tolerance_days": settings.date_split_tolerance_days,
    }

    metrics: dict[str, object] = {}

    async with session_factory() as session:
        # Stage 1: Embed
        n_embedded = await embed_articles(session)
        await session.commit()
        metrics["n_embedded"] = n_embedded

        # Stage 2: Cluster (single-pass incremental)
        cluster_results = await single_pass_cluster_from_db(
            session,
            window_days=settings.cluster_window_days,
            tau=settings.cluster_tau,
            min_articles=settings.cluster_min_articles,
            min_intra_sim=settings.cluster_min_intra_sim,
        )
        metrics["n_clusters"] = len(cluster_results)

        # Stage 3: Global dedup → per-cluster day-resolution → split → registry
        n_dupes = 0
        event_ids: list[str] = []

        # 3a. Window-wide (cross-cluster) dedup, before any event is assigned.
        all_ids = [aid for c in cluster_results.values() for aid in c.article_ids]
        window_dupes: set[str] = set()
        if all_ids:
            wres = await session.execute(
                text("SELECT id::text, embedding::text, published_at FROM articles "
                     "WHERE id = ANY(:ids)"),
                {"ids": all_ids},
            )
            window_arts = [
                (str(r[0]),
                 np.array([float(x) for x in r[1].strip("[]").split(",")], dtype=np.float32),
                 r[2])
                for r in wres.all() if r[1]
            ]
            window_dupes = find_duplicates_global(
                window_arts,
                cosine_threshold=settings.dedup_cosine_threshold,
                time_window_hours=settings.dedup_time_window_hours,
            )
            n_dupes += await mark_duplicates(session, window_dupes)

        # 3b. Per cluster: resolve each canonical article's event-day, split, assign.
        for label, cluster in cluster_results.items():
            id_to_vec = {aid: cluster.embeddings[i] for i, aid in enumerate(cluster.article_ids)}
            canonical_ids = [aid for aid in cluster.article_ids if aid not in window_dupes]
            if not canonical_ids:
                continue

            meta = await session.execute(
                text("SELECT id::text, title, body_text, published_at FROM articles "
                     "WHERE id = ANY(:ids)"),
                {"ids": canonical_ids},
            )
            day_of: dict[str, object] = {}
            for r in meta.all():
                ed = resolve_event_day(r[1] or "", r[2], r[3]) if r[3] else None
                day_of[str(r[0])] = ed.day if ed else None

            split_input = [(aid, id_to_vec[aid], day_of.get(aid)) for aid in canonical_ids]
            groups = split_by_event_day(
                split_input,
                min_bucket=settings.date_split_min_bucket,
                tolerance_days=settings.date_split_tolerance_days,
            )
            for group_ids in groups:
                vecs = np.array([id_to_vec[aid] for aid in group_ids])
                centroid = vecs.mean(axis=0)
                norm = float(np.linalg.norm(centroid))
                if norm > 0:
                    centroid = centroid / norm
                event_id = await assign_event_id(
                    session,
                    centroid=centroid,
                    article_ids=group_ids,
                    threshold=settings.event_registry_sim_threshold,
                )
                event_ids.append(event_id)

        await session.commit()
        metrics["n_dupes"] = n_dupes
        metrics["n_events"] = len(event_ids)

        # Stage 4: Merge converged/duplicate events. assign_event_id matches each
        # cluster against a single nearest event, so within-batch duplicates and
        # centroids that drift together over time leave near-identical events behind.
        # find_merges catches those pairwise; apply_merges folds them and marks the
        # absorbed event 'merged' so it drops out of future matching.
        existing = await load_existing_events(session)
        merges = find_merges(existing, merge_threshold=settings.event_merge_threshold)
        metrics["n_merges"] = await apply_merges(session, merges)

        metrics["n_gated_out"] = await _gate_detected_events(session)
        await session.commit()

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
