"""Backfill events.municipality from events.primary_location via the
municipalities table (ST_Covers) — requires scripts/import_municipalities.py
to have populated that table first.

Usage:
    uv run python scripts/backfill_municipalities.py           # only NULL municipality
    uv run python scripts/backfill_municipalities.py --force    # recompute all rows
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).parent.parent))
from enrich.config import settings  # noqa: E402


async def main(force: bool) -> None:
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    condition = "" if force else "AND e.municipality IS NULL"
    async with session_factory() as session:
        result = await session.execute(
            text(f"""
                UPDATE events e
                SET municipality = m.name
                FROM municipalities m
                WHERE e.primary_location IS NOT NULL
                  {condition}
                  AND ST_Covers(m.geom, e.primary_location)
            """)  # noqa: S608
        )
        await session.commit()
    await engine.dispose()
    print(f"[backfill_municipalities] updated {result.rowcount} event(s) (force={force})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    asyncio.run(main(args.force))
