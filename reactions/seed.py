"""Announcement seed + cross-union merge decision (stance-free)."""
from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from reactions.db import (
    attach_reaction_to_event,
    insert_announced_event,
    load_announced_events,
)

_CHANNEL_DEFAULT = "Φυσικό (offline)"
_ATH = ZoneInfo("Europe/Athens")
_COORD_EPS = 1e-4  # ~11 m; gazetteer hits for the same place are identical, so this is a safe tie


def _place_agreement(
    lat: float | None, lon: float | None, is_national: bool,
    elat: float | None, elon: float | None, enat: bool,
) -> bool:
    if lat is not None and lon is not None and elat is not None and elon is not None:
        if abs(lat - elat) < _COORD_EPS and abs(lon - elon) < _COORD_EPS:
            return True
    return bool(is_national and enat)


def find_announced_duplicate(
    *, centroid: np.ndarray, action_forms: list[str],
    place_lat: float | None, place_lon: float | None, is_national: bool,
    existing: list[tuple[str, np.ndarray, str | None, date | None, list[str],
                         float | None, float | None, bool]],
    sim_threshold: float, event_day: date | None = None,
) -> str | None:
    af = set(action_forms)
    for eid, cen, _org, day, forms, elat, elon, enat in existing:
        if not (af & set(forms)):
            continue  # action-overlap prefilter (necessary, not sufficient)
        if event_day is not None and day is not None and day != event_day:
            continue  # DAY GATE: different Athens event-day never merges
        place_ok = _place_agreement(place_lat, place_lon, is_national, elat, elon, enat)
        sim = float(np.dot(centroid, cen))
        if sim >= sim_threshold or place_ok:
            return eid
    return None


async def seed_or_attach_event(
    session: AsyncSession, *, centroid: np.ndarray, event_time, action_forms: list[str],
    place, summary_el: str, sim_threshold: float, attach_only: bool = False,
) -> tuple[str | None, str]:
    existing = await load_announced_events(session)
    event_day = event_time.astimezone(_ATH).date() if event_time is not None else None
    match = find_announced_duplicate(
        centroid=centroid, event_day=event_day, action_forms=action_forms,
        place_lat=place.lat, place_lon=place.lon, is_national=place.is_national,
        existing=existing, sim_threshold=sim_threshold,
    )
    if match is not None:
        await attach_reaction_to_event(session, match, centroid)
        return match, "deduped"
    if attach_only:  # dateless joiner with no matching rally — record the reaction, seed nothing
        return None, "none"
    event_id = await insert_announced_event(
        session, centroid=centroid, event_time=event_time, action_forms=action_forms,
        channel=_CHANNEL_DEFAULT, lat=place.lat, lon=place.lon,
        is_national=place.is_national, summary_el=summary_el,
    )
    return event_id, "seeded"
