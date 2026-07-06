"""Geocoding pipeline: LLM multi-location extraction → Nominatim → gazetteer fallback.

Primary path: LLM extracts all venues+cities → Nominatim geocodes each (parallel).
  - Returns list[GeocodeResult] ordered by prominence (primary first).
  - Enables both precise-location (zoom-in) and city-level (zoom-out) map views.
Fallback (no LLM or LLM fails): gazetteer → spaCy NER → raw-text Nominatim.
"""
from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
import yaml
from pydantic import BaseModel

from enrich.config import settings

logger = logging.getLogger(__name__)

_GAZETTEER_PATH = Path(__file__).parent / "data" / "gazetteer.yml"


class GeocodeResult(BaseModel):
    lat: float
    lon: float
    location_name: str
    city: str | None = None
    region_code: str | None = None
    is_primary: bool = True


class LocationMention(BaseModel):
    venue: str | None = None  # specific place (e.g. "Πλατεία Συντάγματος")
    city: str               # city (e.g. "Αθήνα") — always required
    region: str | None = None


class _LlmLocations(BaseModel):
    locations: list[LocationMention]


@lru_cache(maxsize=1)
def _load_gazetteer() -> dict[str, dict[str, float]]:
    raw: dict[str, dict[str, float]] = yaml.safe_load(_GAZETTEER_PATH.read_text(encoding="utf-8"))
    return {name.lower(): data for name, data in (raw or {}).items()}


def lookup_gazetteer(text: str) -> GeocodeResult | None:
    """Return first gazetteer match found in text, or None."""
    gazetteer = _load_gazetteer()
    text_lower = text.lower()
    for name, coords in gazetteer.items():
        if name in text_lower:
            city_name = name.title()
            return GeocodeResult(lat=coords["lat"], lon=coords["lon"], location_name=city_name, city=city_name)
    return None


async def geocode_text(
    text: str,
    city: str | None = None,
    nominatim_url: str | None = None,
    delay: float | None = None,
) -> GeocodeResult | None:
    """Call Nominatim search endpoint for the given text snippet."""
    base_url = nominatim_url or settings.nominatim_url
    _delay = delay if delay is not None else settings.nominatim_delay_seconds
    if _delay > 0:
        await asyncio.sleep(_delay)
    try:
        async with httpx.AsyncClient(
            timeout=10.0,
            headers={"User-Agent": "social-reaction-analysis-gr/1.0 (nektarios.tp@gmail.com)"},
        ) as client:
            resp = await client.get(
                f"{base_url}/search",
                params={
                    "q": text,
                    "format": "json",
                    "limit": 1,
                    "countrycodes": "gr",
                    "accept-language": "el",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return None
            first = data[0]
            return GeocodeResult(
                lat=float(first["lat"]),
                lon=float(first["lon"]),
                location_name=first.get("display_name", "").split(",")[0],
                city=city,
            )
    except Exception as exc:
        logger.debug("[geocode] Nominatim error for %r: %s", text[:50], exc)
        return None


def _extract_locations_llm(text: str) -> list[LocationMention]:
    """Extract all event locations via LLM structured output. Returns [] on failure."""
    try:
        from enrich.llm_client import get_llm_client_and_model
        client, _model = get_llm_client_and_model()
        result: _LlmLocations = client.chat.completions.create(
            response_model=_LlmLocations,
            messages=[{"role": "user", "content": (
                "Extract all distinct locations where this Greek social reaction event "
                "is taking place. Include specific venues (squares, streets, buildings) "
                "and their city. Return up to 5 locations ordered by prominence.\n\n"
                f"Text: {text[:800]}"
            )}],
        )
        return result.locations[:5]
    except Exception as exc:
        logger.debug("[geocode] LLM location extraction failed: %s", exc)
        return []


async def geocode_event(
    summary_el: str,
    article_titles: list[str],
    nominatim_url: str | None = None,
) -> list[GeocodeResult]:
    """
    Geocode all locations for an event. Returns list ordered by prominence (primary first).

    Primary path: LLM extracts venue+city for each location → Nominatim geocodes in parallel.
    Fallback: gazetteer (instant) → spaCy NER → Nominatim with raw text.
    """
    all_text = summary_el + " " + " ".join(article_titles[:5])

    # 1. LLM extraction → Nominatim (primary path, parallel requests)
    mentions = _extract_locations_llm(all_text)
    if mentions:
        queries = [f"{m.venue}, {m.city}" if m.venue else m.city for m in mentions]
        raw_results = await asyncio.gather(*[
            geocode_text(q, city=m.city, nominatim_url=nominatim_url)
            for q, m in zip(queries, mentions)
        ])
        results = [
            GeocodeResult(**{**r.model_dump(), "is_primary": i == 0})
            for i, r in enumerate(raw_results)
            if r is not None
        ]
        if results:
            logger.debug("[geocode] LLM+Nominatim resolved %d location(s).", len(results))
            return results

    # 2. Gazetteer fallback (no LLM or LLM found nothing)
    result = lookup_gazetteer(all_text)
    if result:
        logger.debug("[geocode] Gazetteer fallback hit: %s", result.location_name)
        return [result]

    # 3. spaCy NER fallback (no LLM key available)
    candidate = _extract_location_spacy(all_text)
    if candidate:
        result = await geocode_text(candidate, nominatim_url=nominatim_url)
        if result:
            return [result]

    # 4. Raw text Nominatim as last resort
    result = await geocode_text(all_text[:200], nominatim_url=nominatim_url)
    return [result] if result else []


@lru_cache(maxsize=1)
def _load_spacy() -> Any:
    import spacy
    try:
        return spacy.load("el_core_news_md", exclude=["parser", "senter"])
    except OSError:
        return spacy.load("el_core_news_sm", exclude=["parser", "senter"])


def _extract_location_spacy(text: str) -> str | None:
    """Return the first LOC/GPE entity from the text, or None."""
    try:
        nlp = _load_spacy()
        doc = nlp(text[:500])
        for ent in doc.ents:
            if ent.label_ in {"LOC", "GPE"}:
                return str(ent.text)
    except Exception as exc:
        logger.debug("[geocode] spaCy NER failed: %s", exc)
    return None
