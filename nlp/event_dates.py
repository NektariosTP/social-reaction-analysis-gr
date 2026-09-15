"""Per-article dominant event-day resolution for news clustering (LLM-free).

Unlike reactions/dates.py (announcement datetime, 12:00 default), this reads the
whole article, resolves relative weekdays/deictics against publication time, and
returns ONE dominant Athens calendar day used to de-pollute fused clusters."""
from __future__ import annotations

import re
from collections import Counter
from datetime import date, datetime, timedelta

from pydantic import BaseModel

from reactions.dates import _ATH, _fold, all_event_days

# Accent-folded, lowercased Greek weekday roots → Python weekday() (Mon=0).
_WEEKDAYS = {
    "δευτερα": 0, "τριτη": 1, "τεταρτη": 2, "πεμπτη": 3,
    "παρασκευη": 4, "σαββατο": 5, "κυριακη": 6,
}
_WD_RE = re.compile(r"\b(" + "|".join(sorted(_WEEKDAYS, key=len, reverse=True)) + r")\b")
_DEICTIC = {"σημερα": 0, "αυριο": 1, "μεθαυριο": 2}
_DE_RE = re.compile(r"\b(" + "|".join(sorted(_DEICTIC, key=len, reverse=True)) + r")\b")


class EventDay(BaseModel):
    day: date
    source: str  # "title" | "weekday" | "body"


def _pub_day(published_at: datetime) -> date:
    return published_at.astimezone(_ATH).date()


def _relative_day(folded: str, published_at: datetime) -> date | None:
    pub = _pub_day(published_at)
    m = _DE_RE.search(folded)
    if m:
        return pub + timedelta(days=_DEICTIC[m.group(1)])
    m = _WD_RE.search(folded)
    if m:
        target = _WEEKDAYS[m.group(1)]
        return pub + timedelta(days=(target - pub.weekday()) % 7)
    return None


def _earliest_future(days: list[date], today: date) -> date | None:
    if not days:
        return None
    future = [d for d in days if d >= today]
    return min(future) if future else min(days)


def resolve_event_day(
    title: str, body_text: str | None, published_at: datetime
) -> EventDay | None:
    today = _pub_day(published_at)

    # 1. explicit date in title
    d = _earliest_future(all_event_days(title or "", published_at), today)
    if d is not None:
        return EventDay(day=d, source="title")

    # 2. relative weekday / deictic in title
    d = _relative_day(_fold(title or ""), published_at)
    if d is not None:
        return EventDay(day=d, source="weekday")

    # 3. explicit dates in body → most frequent (tie: earliest-future)
    bdays = all_event_days(body_text or "", published_at)
    if bdays:
        counts = Counter(bdays)
        top = max(counts.values())
        tied = [d for d in counts if counts[d] == top]
        return EventDay(day=_earliest_future(tied, today), source="body")

    # 4. relative weekday / deictic in body
    d = _relative_day(_fold(body_text or ""), published_at)
    if d is not None:
        return EventDay(day=d, source="body")

    return None
