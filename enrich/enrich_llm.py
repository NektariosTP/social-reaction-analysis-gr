"""Consolidated enrichment: one structured LLM call → axes + summary + date + places."""
from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from enrich.axes import AXIS_ACTION_FORMS, AXIS_CHANNEL, AXIS_INTENSITY, AXIS_THEMATIC_FIELDS
from enrich.geocode import LocationMention
from enrich.llm_client import get_llm_client_and_model

logger = logging.getLogger(__name__)

_ATHENS = ZoneInfo("Europe/Athens")
_MAX_TITLES = 10
_MAX_BODY_CHARS = 500


class EventEnrichment(BaseModel):
    action_forms: list[str] = []
    thematic_fields: list[str] = []
    channel: str = ""
    intensity: str = ""
    summary_el: str = ""
    summary_en: str = ""
    event_date: str | None = None
    locations: list[LocationMention] = []
    is_national: bool = False


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _as_athens(dt: datetime) -> datetime:
    return dt.replace(tzinfo=_ATHENS) if dt.tzinfo is None else dt.astimezone(_ATHENS)


def parse_event_date(value: str | None, reference_date: str | None = None) -> datetime | None:
    """Parse an ISO 8601 date/date-time to a tz-aware Europe/Athens datetime.

    An event's time should never be NULL when any anchor date exists:
    - an explicit date-time is preserved as-is;
    - a date with no time means "that day" and is anchored at 12:00 noon Athens;
    - a missing/unparseable value falls back to the reference date (the first
      article/reaction date), also at noon Athens.
    Returns None only when neither value nor reference_date yields a date.
    """
    dt = _parse_iso(value)
    if dt is not None and value is not None and "T" in value:
        return _as_athens(dt)  # explicit time — keep it
    # Date-only value, or fall back to the reference date → noon of that Athens day.
    anchor = dt if dt is not None else _parse_iso(reference_date)
    if anchor is None:
        return None
    day = _as_athens(anchor).date()
    return datetime(day.year, day.month, day.day, 12, 0, tzinfo=_ATHENS)


def _coerce(result: EventEnrichment) -> EventEnrichment:
    """Drop out-of-vocabulary labels; coerce single-value axes to a valid default."""
    result.action_forms = [x for x in result.action_forms if x in AXIS_ACTION_FORMS][:3]
    result.thematic_fields = [x for x in result.thematic_fields if x in AXIS_THEMATIC_FIELDS][:3]
    if not result.action_forms:
        result.action_forms = [AXIS_ACTION_FORMS[0]]
    if not result.thematic_fields:
        result.thematic_fields = [AXIS_THEMATIC_FIELDS[-1]]
    if result.channel not in AXIS_CHANNEL:
        result.channel = AXIS_CHANNEL[0]
    if result.intensity not in AXIS_INTENSITY:
        result.intensity = AXIS_INTENSITY[0]
    return result


def enrich_event_llm(
    article_titles: list[str],
    article_bodies: list[str],
    n_sources: int,
    reference_date: str | None,
) -> EventEnrichment | None:
    """One structured LLM call returning all enrichment for a news cluster."""
    titles_text = "\n".join(f"- {t}" for t in article_titles[:_MAX_TITLES])
    bodies_text = "\n\n".join(b[:_MAX_BODY_CHARS] for b in article_bodies[:3])
    prompt = (
        "You are enriching a Greek social-reaction event detected from multiple news sources.\n\n"
        f"Number of sources: {n_sources}\n\n"
        f"Article titles:\n{titles_text}\n\n"
        f"Article excerpts:\n{bodies_text}\n\n"
        "Return, in one structured object:\n"
        f"  action_forms (multi-label, 1-3 of): {', '.join(AXIS_ACTION_FORMS)}\n"
        f"  thematic_fields (multi-label, 1-3 of): {', '.join(AXIS_THEMATIC_FIELDS)}\n"
        f"  channel (one of): {', '.join(AXIS_CHANNEL)}\n"
        f"  intensity (one of): {', '.join(AXIS_INTENSITY)}\n"
        "  summary_el: 2-3 factual sentences in Greek\n"
        "  summary_en: 2-3 factual sentences in English\n"
        "  locations: all distinct places (venue + city; set is_foreign=true if the place "
        "is outside Greece; set embassy_of to the country name when the place is a foreign "
        "embassy/consulate physically located in Greece)\n"
        "  is_national: true if this is a panhellenic/nationwide action\n"
        f"  event_date: the ISO 8601 date the event takes place; resolve relative cues "
        f"(αύριο, χθες, την Πέμπτη…) against the reference date {reference_date}; "
        "null if no date is stated. Never invent a date."
    )
    try:
        client, _model = get_llm_client_and_model()
        result: EventEnrichment = client.chat.completions.create(
            response_model=EventEnrichment,
            max_retries=2,
            messages=[{"role": "user", "content": prompt}],
        )
        coerced = _coerce(result)
        # summary_el/summary_en default to "" (not None) on a schema-valid-but-empty
        # response — treat that the same as a failed call so the event stays
        # 'approved' and is retried, instead of being written as 'enriched' with
        # permanently blank content that no later selection query would catch.
        if not coerced.summary_el.strip() or not coerced.summary_en.strip():
            logger.warning("[enrich_llm] LLM returned an empty summary — treating as failure.")
            return None
        return coerced
    except Exception as exc:  # noqa: BLE001
        logger.warning("[enrich_llm] consolidated call failed: %s", exc)
        return None
