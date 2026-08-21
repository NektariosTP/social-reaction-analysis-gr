"""Standalone slow-cadence refresh of region_indicators. Run: python -m stats.refresh"""
from __future__ import annotations

import asyncio
import logging

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from stats.catalog import IndicatorSpec, load_catalog
from stats.config import settings
from stats.models import IndicatorRow
from stats.sources.base import IndicatorSource
from stats.sources.eurostat import EurostatSource
from stats.sources.worldbank import WorldBankSource

logger = logging.getLogger(__name__)

UPSERT_SQL = """
INSERT INTO region_indicators
    (region_code, indicator, period, value, unit, source, source_url, released_at, fetched_at)
VALUES
    (:region_code, :indicator, :period, :value, :unit, :source, :source_url, :released_at, now())
ON CONFLICT (region_code, indicator, period) DO UPDATE SET
    value = EXCLUDED.value, unit = EXCLUDED.unit, source = EXCLUDED.source,
    source_url = EXCLUDED.source_url, released_at = EXCLUDED.released_at, fetched_at = now()
"""


def row_params(row: IndicatorRow) -> dict:
    return {
        "region_code": row.region_code, "indicator": row.indicator, "period": row.period,
        "value": row.value, "unit": row.unit, "source": row.source,
        "source_url": row.source_url, "released_at": row.released_at,
    }


async def upsert_rows(session: AsyncSession, rows: list[IndicatorRow]) -> int:
    n = 0
    for row in rows:
        await session.execute(text(UPSERT_SQL), row_params(row))
        n += 1
    return n


async def refresh(
    session: AsyncSession,
    client: httpx.AsyncClient | None,
    specs: list[IndicatorSpec],
    sources: dict[str, IndicatorSource],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for spec in specs:
        source = sources.get(spec.source)
        if source is None:
            logger.warning("no source for %s (%s)", spec.key, spec.source)
            counts[spec.key] = 0
            continue
        try:
            rows = await source.fetch(spec, client)
            counts[spec.key] = await upsert_rows(session, rows)
        except Exception as exc:  # noqa: BLE001 — one failure must not abort the batch
            logger.exception("refresh failed for %s: %s", spec.key, exc)
            counts[spec.key] = 0
    await session.commit()
    return counts


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    async def _run() -> None:
        engine = create_async_engine(settings.database_url)
        maker = async_sessionmaker(engine, expire_on_commit=False)
        sources: dict[str, IndicatorSource] = {
            "eurostat": EurostatSource(), "worldbank": WorldBankSource(),
        }
        async with httpx.AsyncClient() as client, maker() as session:
            counts = await refresh(session, client, load_catalog(), sources)
        await engine.dispose()
        logger.info("refresh complete: %s", counts)

    asyncio.run(_run())


if __name__ == "__main__":
    main()
