"""Phase 1 ingestion orchestrator.

Usage:
    uv run python -m ingestion.run
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ingestion.config import settings
from ingestion.connectors.news import GoogleNewsConnector
from ingestion.db import upsert_article
from ingestion.filters.relevance import SpacyRelevanceFilter

logger = logging.getLogger(__name__)

_KEYWORDS_PATH = Path(__file__).parent / "filters" / "keywords.yml"


def _make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def run_ingestion(engine: AsyncEngine | None = None) -> dict[str, int]:
    _engine = engine or create_async_engine(settings.database_url)
    session_factory = _make_session_factory(_engine)

    relevance_filter = SpacyRelevanceFilter(
        keywords_path=_KEYWORDS_PATH,
        model=settings.spacy_model,
    )

    connectors = [
        GoogleNewsConnector(request_delay=settings.request_delay_seconds),
    ]

    total_fetched = 0
    total_relevant = 0
    total_inserted = 0

    async with session_factory() as session:
        for connector in connectors:
            docs = await connector.fetch()
            total_fetched += len(docs)
            for doc in docs:
                if relevance_filter.is_relevant(doc.title + " " + doc.body_text):
                    total_relevant += 1
                    inserted = await upsert_article(doc, session)
                    if inserted:
                        total_inserted += 1
        await session.commit()

    if engine is None:
        await _engine.dispose()

    metrics = {
        "fetched": total_fetched,
        "relevant": total_relevant,
        "inserted": total_inserted,
    }
    logger.info("[ingestion] complete — %s", metrics)
    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    asyncio.run(run_ingestion())
