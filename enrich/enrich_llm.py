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


def parse_event_date(value: str | None) -> datetime | None:
    """Parse ISO 8601 date/date-time → tz-aware Europe/Athens. None/unparseable → None."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_ATHENS)
    return dt


def _coerce(result: EventEnrichment) -> EventEnrichment:
    """Drop out-of-vocabulary labels; coerce single-value axes to a valid default."""
    result.action_forms = [x for x in result.action_forms if x in AXIS_ACTION_FORMS][:3]
    result.thematic_fields = [x for x in result.thematic_fields if x in AXIS_THEMATIC_FIELDS][:3]
    if not result.action_forms:
        result.action_forms = [AXIS_ACTION_FORMS[0]]
    if not result.thematic_fields:
        result.thematic_fields = ["Άλλο"]
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
        "  locations: all distinct places (venue + city; set embassy_of to the country name "
        "when the place is a foreign embassy/consulate in Greece)\n"
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
        return _coerce(result)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[enrich_llm] consolidated call failed: %s", exc)
        return None
