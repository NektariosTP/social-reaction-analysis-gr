"""Deterministic Greek date/time extraction (no LLM)."""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from pydantic import BaseModel

_ATH = ZoneInfo("Europe/Athens")

# month-root (accent-folded, lowercased) → month number. Longest roots first when scanning.
_MONTHS = {
    "ιανουαρ": 1, "γεναρ": 1, "φεβρουαρ": 2, "φλεβαρ": 2, "μαρτ": 3,
    "απριλ": 4, "μαιου": 5, "μαη": 5, "μαϊ": 5, "ιουνιου": 6, "ιουνη": 6,
    "ιουλιου": 7, "ιουλη": 7, "αυγουστ": 8, "σεπτεμβρ": 9, "οκτωβρ": 10,
    "νοεμβρ": 11, "δεκεμβρ": 12,
}
_MONTH_ALT = "|".join(sorted(_MONTHS, key=len, reverse=True))

_NUMERIC_RE = re.compile(r"\b(\d{1,2})[/.](\d{1,2})(?:[/.](\d{2,4}))?\b")
_WORD_RE = re.compile(rf"\b(\d{{1,2}})\s+({_MONTH_ALT})[α-ωό]*\b(?:\s+(\d{{4}}))?")
_TIME_RE = re.compile(r"\bστις\s*(\d{1,2})[:.](\d{2})\b|\b(\d{1,2})[:.](\d{2})\s*(?:π\.?μ\.?|μ\.?μ\.?)?")


class ExtractedDate(BaseModel):
    when: datetime
    is_future: bool
    has_time: bool


def _fold(s: str) -> str:
    nfd = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def _resolve_year(year: int | None, month: int, day: int, now: datetime) -> int:
    if year is not None:
        return year + 2000 if year < 100 else year
    candidate = now.year
    try:
        d = datetime(candidate, month, day, tzinfo=_ATH)
    except ValueError:
        return candidate
    return candidate + 1 if d.date() < (now - timedelta(days=30)).date() else candidate


def _parse_time(text: str) -> tuple[int, int] | None:
    m = _TIME_RE.search(text)
    if not m:
        return None
    h, mi = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
    return int(h), int(mi)


def extract_event_datetime(text: str, now: datetime | None = None) -> ExtractedDate | None:
    now = now or datetime.now(_ATH)
    folded = _fold(text)
    candidates: list[tuple[int, int, int | None]] = []  # (month, day, year|None)

    for m in _NUMERIC_RE.finditer(folded):
        day, month = int(m.group(1)), int(m.group(2))
        yr = int(m.group(3)) if m.group(3) else None
        if 1 <= month <= 12 and 1 <= day <= 31:
            candidates.append((month, day, yr))

    for m in _WORD_RE.finditer(folded):
        day = int(m.group(1))
        month = _MONTHS[m.group(2)]
        yr = int(m.group(3)) if m.group(3) else None
        candidates.append((month, day, yr))

    if not candidates:
        return None

    tod = _parse_time(folded)
    hour, minute = (tod if tod else (12, 0))  # midday default: boundary-safe + indicative

    resolved: list[datetime] = []
    for month, day, yr in candidates:
        year = _resolve_year(yr, month, day, now)
        try:
            resolved.append(datetime(year, month, day, hour, minute, tzinfo=_ATH))
        except ValueError:
            continue
    if not resolved:
        return None

    future = [d for d in resolved if d.date() >= now.date()]
    when = min(future) if future else min(resolved)
    return ExtractedDate(when=when, is_future=when.date() >= now.date(), has_time=tod is not None)


def all_event_days(text: str, now: datetime | None = None) -> list[date]:
    """Every calendar date mentioned in `text` (day granularity, Europe/Athens,
    year-resolved), WITH multiplicity, sorted ascending. Reuses the numeric +
    Greek-word extraction of extract_event_datetime; no relative-weekday logic here."""
    now = now or datetime.now(_ATH)
    folded = _fold(text)
    cands: list[tuple[int, int, int | None]] = []
    for m in _NUMERIC_RE.finditer(folded):
        day_, month = int(m.group(1)), int(m.group(2))
        yr = int(m.group(3)) if m.group(3) else None
        if 1 <= month <= 12 and 1 <= day_ <= 31:
            cands.append((month, day_, yr))
    for m in _WORD_RE.finditer(folded):
        yr = int(m.group(3)) if m.group(3) else None
        cands.append((_MONTHS[m.group(2)], int(m.group(1)), yr))
    out: list[date] = []
    for month, day_, yr in cands:
        year = _resolve_year(yr, month, day_, now)
        try:
            out.append(date(year, month, day_))
        except ValueError:
            continue
    return sorted(out)
