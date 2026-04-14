"""
backend/llm/summarize.py

Per-cluster event summarization via LiteLLM.

Given a cluster of article titles and bodies, generates a concise, bilingual (Greek fact, English output)
summary covering:
  - What happened
  - Where it happened
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import litellm
from pydantic import BaseModel

from backend.llm.config import LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE, REACTION_CATEGORIES

logger = logging.getLogger(__name__)

litellm.suppress_debug_info = True


# ---------------------------------------------------------------------------
# Structured output schema
# ---------------------------------------------------------------------------

class SummaryResult(BaseModel):
    summary_el: str = ""   # short Greek summary (2-3 sentences)
    summary_en: str = ""   # short English summary (2-3 sentences)
    category: str = ""     # populated only when include_category=True


# ---------------------------------------------------------------------------
# System prompts (Greek-only LLM output; translation handled separately)
# ---------------------------------------------------------------------------

# Economic prompt: embedding already determined the category, LLM only summarises.
_SYSTEM_PROMPT_ECONOMIC = (
    "You are a news analyst and summarizer specialising in Greek civil society.\n"
    "Given a set of Greek news articles describing the same social reaction event, "
    "write a concise summary IN GREEK ONLY (1-2 sentences).\n\n"
    'Respond ONLY with a JSON object matching this schema:\n'
    '{"summary": "<1-2 sentence summary in Greek>"}'
)

# Full prompt: LLM classifies AND summarises in one call.
_SYSTEM_PROMPT_FULL = (
    "You are a news analyst and summarizer specialising in Greek civil society.\n"
    "Given a set of Greek news articles describing the same social reaction event:\n"
    "  1. Classify the event into exactly ONE of these categories:\n"
    + "\n".join(f"     {i+1}. {cat}" for i, cat in enumerate(REACTION_CATEGORIES))
    + "\n  2. Write a concise summary IN GREEK ONLY (1-2 sentences).\n\n"
    'Respond ONLY with a JSON object matching this schema:\n'
    '{"category": "<exact category name>", "summary": "<1-2 sentence summary in Greek>"}'
)

_MAX_ARTICLES = 5


def _build_user_message(
    titles: list[str],
    n_sources: int,
    bodies: list[str] | None = None,
) -> str:
    parts: list[str] = []
    for i, title in enumerate(titles[:_MAX_ARTICLES]):
        body = (
            bodies[i].strip()
            if bodies and i < len(bodies) and bodies[i]
            else ""
        )
        if body:
            parts.append(f"- Title: {title}\n  Body: {body}")
        else:
            parts.append(f"- {title}")
    # remaining titles (beyond MAX_ARTICLES) as plain bullets
    for title in titles[_MAX_ARTICLES:20]:
        parts.append(f"- {title}")
    bullet_articles = "\n".join(parts)
    return (
        f"The following {n_sources} article(s) report on the same event:\n"
        f"{bullet_articles}\n\n"
        "Summarize the event."
    )


# ---------------------------------------------------------------------------
# Translation helpers
# ---------------------------------------------------------------------------

# Matches Greek-uppercase acronyms in two formats:
#   - continuous:     ΑΔΕΔΥ, ΟΛΜΕ, ΚΚΕ
#   - dot-separated:  Α.Δ.Ε.Δ.Υ., Σ.Ε.Β., Κ.Κ.Ε (trailing dot optional)
_ACRONYM_RE = re.compile(
    r'[\u0391-\u03A9](?:\.[\u0391-\u03A9]){1,}\.?'   # dot-separated
    r'|'
    r'[\u0391-\u03A9]{2,}(?:\s[\u0391-\u03A9]{1,})*'  # continuous / space-separated
)


def _protect_acronyms(text: str) -> tuple[str, dict[str, str]]:
    """Replace Greek-uppercase acronyms with stable placeholders."""
    mapping: dict[str, str] = {}
    counter = 0

    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        nonlocal counter
        placeholder = f"ACRNM{counter}X"
        mapping[placeholder] = m.group(0)
        counter += 1
        return placeholder

    return _ACRONYM_RE.sub(_replace, text), mapping


def _restore_acronyms(text: str, mapping: dict[str, str]) -> str:
    for placeholder, original in mapping.items():
        text = text.replace(placeholder, original)
    return text


def _translate_el_to_en(text: str) -> str:
    """Translate Greek text → English via Google Translate, preserving Greek acronyms."""
    if not text:
        return ""
    try:
        from deep_translator import GoogleTranslator  # noqa: PLC0415
        protected, mapping = _protect_acronyms(text)
        translated = GoogleTranslator(source="el", target="en").translate(protected)
        return _restore_acronyms(translated or "", mapping)
    except Exception as exc:
        logger.warning("[summarize] EL→EN translation failed: %s", exc)
        return ""


def _translate_en_to_el(text: str) -> str:
    """Translate English text \u2192 Greek via Google Translate."""
    if not text:
        return ""
    try:
        from deep_translator import GoogleTranslator  # noqa: PLC0415
        translated = GoogleTranslator(source="en", target="el").translate(text)
        return translated or ""
    except Exception as exc:
        logger.warning("[summarize] EN\u2192EL translation failed: %s", exc)
        return ""


def _is_greek(text: str) -> bool:
    """Return True if >30% of alphabetic characters in *text* are Greek Unicode."""
    alpha = [c for c in text if c.isalpha()]
    if not alpha:
        return False
    greek_count = sum(
        1 for c in alpha
        if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF'
    )
    return greek_count / len(alpha) > 0.30


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def summarize_event(
    titles: list[str],
    bodies: list[str] | None = None,
    n_sources: int | None = None,
    include_category: bool = False,
) -> SummaryResult | None:
    """
    Generate a bilingual summary for an event cluster.

    Parameters
    ----------
    titles : list[str]
        Article titles for the cluster.
    bodies : list[str] | None
        Article body texts aligned with ``titles``. The first
        ``_MAX_ARTICLES`` bodies are truncated to ``_MAX_BODY_CHARS`` chars
        and appended below their respective titles in the user message.
    n_sources : int | None
        Number of distinct source outlets. Defaults to len(titles).
    include_category : bool
        When True, uses the full system prompt which also asks the LLM to
        classify the event category.  The result is returned in
        ``SummaryResult.category``.  When False (default), uses the economic
        prompt (no classification request, fewer tokens consumed).

    Returns
    -------
    SummaryResult | None
        Parsed summary, or None on LLM failure.
    """
    if not titles:
        return None

    if n_sources is None:
        n_sources = len(titles)

    system_prompt = _SYSTEM_PROMPT_FULL if include_category else _SYSTEM_PROMPT_ECONOMIC

    try:
        response = litellm.completion(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": _build_user_message(titles, n_sources, bodies)},
            ],
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or ""
        data: dict[str, Any] = json.loads(raw)
        # Accept the model's natural key name for the summary.
        summary_raw = (
            data.get("summary")
            or data.get("summary_el")
            or data.get("greek_summary")
            or data.get("el")
            or ""
        )
        category = data.get("category", "")
        if not summary_raw:
            logger.warning("[summarize] LLM returned empty summary \u2014 treating as failure.")
            return None
        if _is_greek(summary_raw):
            summary_el = summary_raw
            summary_en = _translate_el_to_en(summary_raw)
        else:
            # Model returned English despite the Greek-only instruction.
            logger.info("[summarize] LLM returned English summary \u2014 back-translating to Greek.")
            summary_en = summary_raw
            summary_el = _translate_en_to_el(summary_raw)
        return SummaryResult(summary_el=summary_el, summary_en=summary_en, category=category)

    except Exception as exc:
        logger.error("[summarize] LLM call failed: %s", exc)
        return None
