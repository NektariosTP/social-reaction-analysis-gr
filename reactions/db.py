"""Async DB helpers for the reactions pipeline (stance-free; roster-ready)."""
from __future__ import annotations

import uuid as uuid_mod
from datetime import datetime
from datetime import timezone as _tz

import numpy as np
from sqlalchemy import text as sa_text  # aliased so the `text` reaction-body arg can't shadow it
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from nlp.event_registry import running_mean


def _vec_str(v: np.ndarray) -> str:
    return f"[{','.join(str(x) for x in v.tolist())}]"


async def upsert_reaction(
    session: AsyncSession, *, source_org: str, actor_name: str,
    text: str, url: str, observed_at: datetime | None, event_id: str | None,
    match_score: float | None, match_method: str,
) -> bool:
    try:
        async with session.begin_nested():
            result = await session.execute(
                sa_text("""
                    INSERT INTO event_reactions (
                        id, event_id, source_org, actor_name, actor_role,
                        text, url, observed_at, match_score, match_method
                    ) VALUES (
                        :id, :event_id, :source_org, :actor_name, 'union',
                        :text, :url, :observed_at, :match_score, :match_method
                    )
                    ON CONFLICT (source_org, url) DO NOTHING
                """),
                {
                    "id": str(uuid_mod.uuid4()), "event_id": event_id,
                    "source_org": source_org, "actor_name": actor_name,
                    "text": text, "url": url, "observed_at": observed_at,
                    "match_score": match_score, "match_method": match_method,
                },
            )
    except IntegrityError:
        return False
    return result.rowcount > 0


async def insert_announced_event(
    session: AsyncSession, *, centroid: np.ndarray, event_time: datetime | None,
    action_forms: list[str], channel: str, lat: float | None, lon: float | None,
    is_national: bool, summary_el: str,
) -> str:
    now = datetime.now(_tz.utc)
    loc = None if (lat is None or lon is None) else f"SRID=4326;POINT({lon} {lat})"
    row = (await session.execute(
        sa_text("""
            INSERT INTO events (
                centroid, action_forms, channel, primary_location,
                event_time, is_national, summary_el, article_count, source_count,
                first_seen, last_seen, status
            ) VALUES (
                CAST(:centroid AS vector), :action_forms, :channel,
                CAST(:loc AS geography), :event_time, :is_national, :summary_el,
                0, 1, :now, :now, 'announced'
            )
            RETURNING id::text
        """),
        {
            "centroid": _vec_str(centroid), "action_forms": action_forms,
            "channel": channel, "loc": loc, "event_time": event_time,
            "is_national": is_national, "summary_el": summary_el, "now": now,
        },
    )).first()
    return row[0]


async def load_announced_events(session: AsyncSession):
    """Return one row per announced event, with the seeding reaction's org, the
    event day (Athens), action_forms, and the event's place coords + national flag —
    everything find_announced_duplicate needs for the cross-union merge key."""
    result = await session.execute(sa_text("""
        SELECT e.id::text, e.centroid::text,
               (SELECT r.source_org FROM event_reactions r
                 WHERE r.event_id = e.id ORDER BY r.observed_at NULLS LAST LIMIT 1),
               (e.event_time AT TIME ZONE 'Europe/Athens')::date,
               e.action_forms,
               ST_Y(e.primary_location::geometry),
               ST_X(e.primary_location::geometry),
               COALESCE(e.is_national, FALSE)
        FROM events e
        WHERE e.status = 'announced' AND e.centroid IS NOT NULL
    """))
    out = []
    for eid, cen, org, day, forms, lat, lon, nat in result.all():
        vec = np.array([float(v) for v in cen.strip("[]").split(",")], dtype=np.float32)
        out.append((
            eid, vec, org, day, list(forms or []),
            float(lat) if lat is not None else None,
            float(lon) if lon is not None else None,
            bool(nat),
        ))
    return out


async def attach_reaction_to_event(
    session: AsyncSession, event_id: str, centroid: np.ndarray, batch_count: int = 1
) -> None:
    now = datetime.now(_tz.utc)
    row = (await session.execute(
        sa_text("SELECT centroid::text, source_count FROM events WHERE id = :id"),
        {"id": event_id},
    )).first()
    old = np.array([float(v) for v in row[0].strip("[]").split(",")], dtype=np.float32)
    merged = running_mean(old, int(row[1]) or 1, centroid, batch_count)
    await session.execute(
        sa_text("""UPDATE events SET centroid = CAST(:c AS vector),
                 source_count = source_count + :n, last_seen = :now WHERE id = :id"""),
        {"c": _vec_str(merged), "n": batch_count, "now": now, "id": event_id},
    )
