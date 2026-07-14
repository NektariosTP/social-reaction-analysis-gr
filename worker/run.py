"""Worker loop: runs ingestion -> NLP -> enrichment per PIPELINE_MODE on an
interval, plus an archival sweep every cycle regardless of mode.

Usage:
    uv run python -m worker.run
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from enrich.pipeline import run_enrich_pipeline
from ingestion.run import run_ingestion
from nlp.pipeline import run_nlp_pipeline
from worker.archival import run_archival_sweep
from worker.config import settings

logger = logging.getLogger(__name__)


def _make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def run_worker_cycle(engine: AsyncEngine) -> dict[str, object]:
    """Run one worker cycle. Each phase is isolated: a failing phase is logged
    and does not stop the others or the always-on archival sweep."""
    metrics: dict[str, object] = {}

    try:
        metrics["ingestion"] = await run_ingestion(engine=engine)
    except Exception:
        logger.exception("[worker] ingestion phase failed")

    if settings.pipeline_mode in ("scrape_and_nlp", "full"):
        try:
            metrics["nlp"] = await run_nlp_pipeline(engine=engine)
        except Exception:
            logger.exception("[worker] nlp phase failed")

    if settings.pipeline_mode == "full":
        try:
            metrics["enrich"] = await run_enrich_pipeline(engine=engine)
        except Exception:
            logger.exception("[worker] enrich phase failed")

    session_factory = _make_session_factory(engine)
    try:
        async with session_factory() as session:
            metrics["archival"] = await run_archival_sweep(session)
    except Exception:
        logger.exception("[worker] archival sweep failed")

    logger.info("[worker] cycle complete — %s", metrics)
    return metrics


async def run_forever() -> None:
    engine = create_async_engine(settings.database_url)
    try:
        while True:
            await run_worker_cycle(engine)
            await asyncio.sleep(settings.pipeline_interval_seconds)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    asyncio.run(run_forever())
