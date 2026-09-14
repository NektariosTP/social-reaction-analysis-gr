"""Phase-A reactions orchestrator: fetch union feeds → filter → extract → write (stance-free)."""
from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine,
)

from ingestion.connectors.union import UnionFeedConnector, load_union_sources
from nlp.embeddings import embed_query
from reactions.actions import map_action_forms
from reactions.config import settings
from reactions.dates import extract_event_datetime
from reactions.db import reaction_already_linked, upsert_reaction
from reactions.filters import FILTER_VARIANTS, passes_filter
from reactions.normalize import clean_text
from reactions.place import resolve_place
from reactions.seed import seed_or_attach_event

logger = logging.getLogger(__name__)


async def _process_item(session: AsyncSession, item, sim_threshold: float) -> str:
    """Returns one of: 'filtered', 'duplicate', 'reaction', 'seeded', 'deduped'."""
    max_age = timedelta(days=settings.reactions_max_age_days)
    if item.observed_at is not None and (datetime.now(UTC) - item.observed_at) > max_age:
        return "filtered"

    # Feed items reappear across pipeline cycles until they age out. If this
    # (source_org, url) is already linked to an event, re-running seed/attach would
    # double-count source_count and re-skew the event centroid for zero new information.
    if await reaction_already_linked(session, source_org=item.source_org, url=item.url):
        return "duplicate"

    title = clean_text(item.title)
    body = clean_text(item.body_text)
    blob = f"{title}. {body}".strip()
    keywords = FILTER_VARIANTS.get(settings.filter_variant, FILTER_VARIANTS["broad"])
    if not passes_filter(blob, keywords):
        return "filtered"

    action_forms = map_action_forms(blob)
    extracted = extract_event_datetime(blob, now=None)

    event_id: str | None = None
    match_method = "none"
    outcome = "reaction"
    if action_forms and extracted is not None and extracted.is_future:
        # Future-dated announcement: may seed a new announced event or merge onto one.
        place = resolve_place(blob)
        centroid = embed_query(blob)
        event_id, match_method = await seed_or_attach_event(
            session, centroid=centroid, event_time=extracted.when,
            action_forms=action_forms, place=place,
            summary_el=title or blob[:200], sim_threshold=sim_threshold,
        )
        outcome = match_method  # 'seeded' | 'deduped'
    elif action_forms and extracted is None:
        # Dateless joiner ("Συμμετέχουμε στο συλλαλητήριο στη ΔΕΘ"): attach to an existing
        # dated rally by place+action only — never seed. It inherits the event's date.
        place = resolve_place(blob)
        if place.lat is not None or place.is_national:
            centroid = embed_query(blob)
            event_id, match_method = await seed_or_attach_event(
                session, centroid=centroid, event_time=None,
                action_forms=action_forms, place=place,
                summary_el=title or blob[:200], sim_threshold=sim_threshold,
                attach_only=True,
            )
            if match_method == "deduped":
                outcome = "deduped"

    await upsert_reaction(
        session, source_org=item.source_org, actor_name=item.actor_name,
        text=blob, url=item.url, observed_at=item.observed_at,
        event_id=event_id, match_score=None, match_method=match_method,
    )
    return outcome


async def run_reactions_pipeline(engine: AsyncEngine | None = None) -> dict[str, int]:
    _engine = engine or create_async_engine(settings.database_url)
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        _engine, expire_on_commit=False
    )
    counts = {
        "fetched": 0, "filtered": 0, "duplicate": 0,
        "reactions_written": 0, "seeded": 0, "deduped": 0,
    }
    async with session_factory() as session:
        for src in load_union_sources():
            connector = UnionFeedConnector(
                source_org=src["org_slug"], actor_name=src["actor_name"],
                feed_url=src["feed_url"], feed_format=src.get("feed_format", "rss"),
                request_delay=settings.request_delay_seconds,
            )
            items = await connector.fetch()
            counts["fetched"] += len(items)
            for item in items:
                outcome = await _process_item(session, item, settings.seed_dedup_sim)
                if outcome == "filtered":
                    counts["filtered"] += 1
                    continue
                if outcome == "duplicate":
                    counts["duplicate"] += 1
                    continue
                counts["reactions_written"] += 1
                if outcome in ("seeded", "deduped"):
                    counts[outcome] += 1
            await asyncio.sleep(settings.request_delay_seconds)
        await session.commit()
    if engine is None:
        await _engine.dispose()
    logger.info("[reactions] complete — %s", counts)
    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    asyncio.run(run_reactions_pipeline())
