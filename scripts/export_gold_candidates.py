"""Export candidate items for manual gold-eval labeling.

Pulls current DB content into `tests/fixtures/gold/*_todo.jsonl` with empty
label fields for hand-labeling. Never touches an already-finished (non-_todo)
fixture file. See tests/fixtures/gold/README.md for the labeling workflow.

Usage:
    uv run python scripts/export_gold_candidates.py
    uv run python scripts/export_gold_candidates.py --clustering-start 2026-07-16 --clustering-end 2026-07-17
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from ingestion.config import settings

OUT_DIR = _REPO_ROOT / "tests" / "fixtures" / "gold"

# Known failure modes from the improvement plan (§1) — oversample these so
# the gold set actually exercises the bugs being fixed, not just an average.
HARD_CASE_KEYWORDS = ["Πρεσβεία", "Προξενείο", "Τεχεράνη", "Άγκυρα", "Ισραήλ", "Ιράν", "Ευρώπη"]


def _excerpt(text_: str | None, n: int = 600) -> str:
    return (text_ or "")[:n]


async def export_relevance_candidates(engine, limit: int = 150) -> None:
    async with engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT title, body_text FROM articles "
                    "WHERE body_text IS NOT NULL ORDER BY random() LIMIT :limit"
                ),
                {"limit": limit},
            )
        ).all()

    out = OUT_DIR / "relevance_todo.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for title, body in rows:
            f.write(
                json.dumps(
                    {"title": title, "body_excerpt": _excerpt(body), "label": None},
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"[relevance] {len(rows)} candidates -> {out}")
    print(
        "  NOTE: the DB only contains articles that already passed the relevance gate — "
        "no true 'noise' examples exist here. See README.md's known caveat."
    )


async def export_clustering_window(engine, start: date, end: date) -> None:
    async with engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT id, title, body_text, event_id, ingested_at FROM articles "
                    "WHERE ingested_at >= :start AND ingested_at < :end "
                    "AND body_text IS NOT NULL "
                    "ORDER BY ingested_at ASC"
                ),
                {"start": start, "end": end},
            )
        ).all()

    out = OUT_DIR / "clustering_todo.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for aid, title, body, event_id, ingested_at in rows:
            f.write(
                json.dumps(
                    {
                        "article_id_local": str(aid),
                        "title": title,
                        "body_excerpt": _excerpt(body),
                        "ingested_at": ingested_at.isoformat(),
                        "pipeline_event_id": str(event_id) if event_id else None,
                        "gold_group": None,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"[clustering] {len(rows)} candidates ({start}..{end}) -> {out}")
    if len(rows) > 80:
        print(f"  NOTE: {len(rows)} articles is a lot to hand-group — consider narrowing the window.")
    elif len(rows) == 0:
        print("  NOTE: 0 articles in this window — pick a different date (see daily counts in the plan doc).")


async def export_event_candidates(engine, n: int = 40) -> None:
    keyword_clause = " OR ".join(f"a.title ILIKE '%{kw}%'" for kw in HARD_CASE_KEYWORDS)
    async with engine.connect() as conn:
        hard = (
            await conn.execute(
                text(
                    f"SELECT DISTINCT e.id FROM events e "
                    f"JOIN articles a ON a.event_id = e.id "
                    f"WHERE ({keyword_clause}) AND a.body_text IS NOT NULL LIMIT :n"
                ),
                {"n": n // 2},
            )
        ).all()
        hard_ids = [r[0] for r in hard]

        random_rows = (
            await conn.execute(
                text(
                    "SELECT id FROM events e WHERE NOT (id = ANY(:exclude)) "
                    "AND EXISTS (SELECT 1 FROM articles a WHERE a.event_id = e.id "
                    "AND a.body_text IS NOT NULL) "
                    "ORDER BY random() LIMIT :n"
                ),
                {"exclude": hard_ids or [], "n": max(n - len(hard_ids), 0)},
            )
        ).all()
        event_ids = hard_ids + [r[0] for r in random_rows]

        out = OUT_DIR / "events_todo.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for eid in event_ids:
                arts = (
                    await conn.execute(
                        text(
                            "SELECT title, body_text FROM articles WHERE event_id = :eid "
                            "AND body_text IS NOT NULL "
                            "ORDER BY published_at DESC LIMIT 5"
                        ),
                        {"eid": eid},
                    )
                ).all()
                f.write(
                    json.dumps(
                        {
                            "pipeline_event_id": str(eid),
                            "article_titles": [r[0] for r in arts],
                            "article_bodies": [_excerpt(r[1]) for r in arts],
                            "action_forms": None,
                            "thematic_fields": None,
                            "channel": None,
                            "intensity": None,
                            "true_lat": None,
                            "true_lon": None,
                            "true_region_code": None,
                            "true_municipality": None,
                            "is_foreign": None,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
    print(
        f"[events] {len(event_ids)} candidates "
        f"({len(hard_ids)} hard-case, {len(event_ids) - len(hard_ids)} random) -> {out}"
    )


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clustering-start", default="2026-07-22")
    parser.add_argument("--clustering-end", default="2026-07-23")
    parser.add_argument("--relevance-n", type=int, default=150)
    parser.add_argument("--events-n", type=int, default=40)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_async_engine(settings.database_url)
    try:
        await export_relevance_candidates(engine, limit=args.relevance_n)
        await export_clustering_window(
            engine,
            datetime.strptime(args.clustering_start, "%Y-%m-%d").date(),
            datetime.strptime(args.clustering_end, "%Y-%m-%d").date(),
        )
        await export_event_candidates(engine, n=args.events_n)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
