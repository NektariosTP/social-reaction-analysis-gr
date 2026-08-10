"""Backfill events.region_code from events.primary_location using the bundled
periphery polygons (pure Python — no ST_Contains, no regions table).

Usage:
    uv run python scripts/backfill_regions.py           # only NULL region_code
    uv run python scripts/backfill_regions.py --force    # recompute all rows
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
from enrich.geocode import region_for_point  # noqa: E402


async def main(force: bool) -> None:
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    where = "" if force else "WHERE region_code IS NULL"
    async with session_factory() as session:
        rows = (
            await session.execute(
                text(
                    "SELECT id::text, ST_Y(primary_location::geometry) AS lat, "
                    "ST_X(primary_location::geometry) AS lon "
                    f"FROM events WHERE primary_location IS NOT NULL "
                    f"{'AND region_code IS NULL' if not force else ''}"
                )
            )
        ).all()
        updated = 0
        for event_id, lat, lon in rows:
            region = region_for_point(float(lat), float(lon))
            await session.execute(
                text("UPDATE events SET region_code = :r WHERE id = :id"),
                {"r": region, "id": event_id},
            )
            updated += 1
        await session.commit()
    await engine.dispose()
    print(f"[backfill_regions] updated {updated} event(s) (force={force})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    asyncio.run(main(args.force))
