"""Bilingual (EL + EN) event summarization via LLM."""
from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from enrich.llm_client import get_llm_client_and_model

logger = logging.getLogger(__name__)

_MAX_TITLES = 8
_MAX_BODY_CHARS = 400
_ATHENS = ZoneInfo("Europe/Athens")


def parse_event_date(value: str | None) -> datetime | None:
    """Parse an ISO 8601 date or date-time to a tz-aware Europe/Athens datetime.

    Date-only strings resolve to midnight Athens. Naive date-times are
    interpreted as Athens local time; strings carrying an explicit offset keep
    it. None/empty/unparseable → None (treated as undated — never fabricated).
    """
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_ATHENS)
    return dt


class SummaryResult(BaseModel):
    summary_el: str
    summary_en: str


def summarize_event(
    article_titles: list[str],
    article_bodies: list[str],
    n_sources: int,
) -> SummaryResult | None:
    """Generate bilingual (EL + EN) summary for a cluster of articles."""
    titles_text = "\n".join(f"- {t}" for t in article_titles[:_MAX_TITLES])
    bodies_text = "\n\n".join(b[:_MAX_BODY_CHARS] for b in article_bodies[:3])

    prompt = (
        "You are summarising a Greek social reaction event detected from multiple news sources.\n\n"
        f"Number of sources: {n_sources}\n\n"
        f"Article titles:\n{titles_text}\n\n"
        f"Article excerpts:\n{bodies_text}\n\n"
        "Write a concise factual summary of what happened in two languages:\n"
        "- summary_el: 2-3 sentences in Greek\n"
        "- summary_en: 2-3 sentences in English\n"
        "Focus on: what happened, who was involved, where, approximate date."
    )

    try:
        client, model = get_llm_client_and_model()
        result: SummaryResult = client.chat.completions.create(
            response_model=SummaryResult,
            messages=[{"role": "user", "content": prompt}],
        )
        return result
    except Exception as exc:
        logger.warning("[summarize] LLM summarization failed: %s", exc)
        return None
