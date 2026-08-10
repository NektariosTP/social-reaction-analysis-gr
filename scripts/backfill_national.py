"""Backfill events.is_national on existing unlocated events from stored article text,
so national-scope events surface without waiting for a reprocess cycle.

Usage:
    uv run python scripts/backfill_national.py           # only not-yet-flagged unlocated events
    uv run python scripts/backfill_national.py --force    # recompute all unlocated events
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
from enrich.geocode import detect_national_scope  # noqa: E402


def _compute_is_national(event_text: str) -> bool:
    """True when the event's combined article text carries national-scope signals."""
    return detect_national_scope(event_text)


async def main(force: bool) -> None:
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    extra = "" if force else "AND e.is_national = FALSE"
    async with session_factory() as session:
        rows = (
            await session.execute(
                text(
                    "SELECT e.id::text, "
                    "string_agg(COALESCE(a.title, '') || ' ' || COALESCE(a.body_text, ''), ' ') "
                    "FROM events e "
                    "JOIN articles a ON a.event_id = e.id AND a.is_duplicate = FALSE "
                    f"WHERE e.primary_location IS NULL {extra} "
                    "GROUP BY e.id"
                )
            )
        ).all()
        updated = 0
        for event_id, event_text in rows:
            await session.execute(
                text("UPDATE events SET is_national = :v WHERE id = :id"),
                {"v": _compute_is_national(event_text or ""), "id": event_id},
            )
            updated += 1
        await session.commit()
    await engine.dispose()
    print(f"[backfill_national] updated {updated} event(s) (force={force})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    asyncio.run(main(args.force))
