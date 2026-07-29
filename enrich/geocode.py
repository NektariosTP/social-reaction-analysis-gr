"""Geocoding pipeline: LLM multi-location extraction → Nominatim → gazetteer fallback.

Primary path: LLM extracts all venues+cities → Nominatim geocodes each (parallel).
  - Returns list[GeocodeResult] ordered by prominence (primary first).
  - Enables both precise-location (zoom-in) and city-level (zoom-out) map views.
Fallback (no LLM or LLM fails): gazetteer → spaCy NER → raw-text Nominatim.
"""
from __future__ import annotations

import re
import asyncio
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
import yaml
from pydantic import BaseModel

from enrich.config import settings

import json
from shapely.geometry import Point, shape
from shapely.prepared import prep

logger = logging.getLogger(__name__)

_GAZETTEER_PATH = Path(__file__).parent / "data" / "gazetteer.yml"
_REGIONS_PATH = Path(__file__).parent / "data" / "regions.geojson"
_EMBASSIES_PATH = Path(__file__).parent / "data" / "embassies.yml"


class GeocodeResult(BaseModel):
    lat: float
    lon: float
    location_name: str
    city: str | None = None
    region_code: str | None = None
    is_foreign: bool = False
    is_primary: bool = True


class LocationMention(BaseModel):
    venue: str | None = None  # specific place (e.g. "Πλατεία Συντάγματος")
    city: str               # city (e.g. "Αθήνα") — always required
    region: str | None = None
    is_foreign: bool = False
    embassy_of: str | None = None  # country name if this is a foreign embassy on Greek soil

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
            max_retries=2,
            messages=[{"role": "user", "content": (
                "Extract all distinct locations where this Greek social reaction event "
                "is taking place. Include specific venues (squares, streets, buildings) "
                "and their city. For each location set is_foreign=true if it is outside "
                "Greece, and set embassy_of to the country name if the location is a "
                "foreign embassy/consulate on Greek soil. Return up to 5 locations "
                "ordered by prominence.\n\n"
                f"Text: {text[:800]}"
            )}],
        )
        return result.locations[:5]
    except Exception as exc:
        raw = _extract_failed_generation(exc)
        if raw:
            salvaged = parse_locations_json(raw)
            if salvaged:
                logger.info("[geocode] Salvaged %d location(s) from a failed tool call.", len(salvaged))
                return salvaged
        logger.debug("[geocode] LLM location extraction failed: %s", exc)
        return []



def parse_locations_json(raw: str) -> list[LocationMention]:
    """Best-effort recover LocationMentions from a raw/malformed model string.

    Handles Groq's `<function=…>{…}<function/…>` wrapper and ```json fences by
    slicing from the first `{` to the last `}` and validating via _LlmLocations.
    Returns [] on any failure.
    """
    if not raw:
        return []
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        return []
    try:
        data = json.loads(raw[start : end + 1])
        return _LlmLocations(**data).locations[:5]
    except Exception:  # noqa: BLE001 — any malformed payload → give up cleanly
        return []


def _extract_failed_generation(exc: Exception) -> str | None:
    """Recover `error.failed_generation` from a litellm/Groq BadRequestError string."""
    match = re.search(r"\{.*\}", str(exc), re.DOTALL)
    if not match:
        return None
    try:
        body = json.loads(match.group(0))
    except Exception:  # noqa: BLE001
        return None
    fg = body.get("error", {}).get("failed_generation")
    return fg if isinstance(fg, str) else None


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
        results: list[GeocodeResult] = []
        for i, m in enumerate(mentions):
            if m.embassy_of:
                emb = lookup_embassy(m.embassy_of)
                if emb:
                    emb.is_primary = i == 0
                    results.append(emb)
                    continue
            query = f"{m.venue}, {m.city}" if m.venue else m.city
            r = await geocode_text(query, city=m.city, nominatim_url=nominatim_url)
            if r is not None:
                r.is_primary = i == 0
                r.is_foreign = m.is_foreign  # _finalize confirms via point_in_greece
                results.append(r)
        if results:
            logger.debug("[geocode] LLM+Nominatim resolved %d location(s).", len(results))
            return _finalize(results)

    # 2. Gazetteer fallback (no LLM or LLM found nothing)
    result = lookup_gazetteer(all_text)
    if result:
        logger.debug("[geocode] Gazetteer fallback hit: %s", result.location_name)
        return _finalize([result])

    # 3. spaCy NER fallback (no LLM key available)
    candidate = _extract_location_spacy(all_text)
    if candidate:
        result = await geocode_text(candidate, nominatim_url=nominatim_url)
        if result:
            return _finalize([result])

    # 4. Raw text Nominatim as last resort
    result = await geocode_text(all_text[:200], nominatim_url=nominatim_url)
    return _finalize([result]) if result else []


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


@lru_cache(maxsize=1)
def _load_regions() -> list[tuple[str, object]]:
    """Load the 13 periphery polygons once, prepared for fast point queries.

    Returns list of (canonical English name, prepared geometry). Coordinates in
    the GeoJSON are [lon, lat] (GeoJSON standard), so query with Point(lon, lat).
    """
    data = json.loads(_REGIONS_PATH.read_text(encoding="utf-8"))
    out: list[tuple[str, object]] = []
    for feature in data["features"]:
        name = feature["properties"]["name"]
        out.append((name, prep(shape(feature["geometry"]))))
    return out


def region_for_point(lat: float, lon: float) -> str | None:
    """Return the canonical English periphery name containing (lat, lon), or None."""
    point = Point(lon, lat)
    for name, geom in _load_regions():
        if geom.contains(point):
            return name
    return None


def point_in_greece(lat: float, lon: float) -> bool:
    """True iff (lat, lon) falls inside any of the 13 peripheries."""
    return region_for_point(lat, lon) is not None


@lru_cache(maxsize=1)
def _load_embassies() -> dict[str, dict[str, float]]:
    raw = yaml.safe_load(_EMBASSIES_PATH.read_text(encoding="utf-8")) or {}
    return {k.lower(): v for k, v in raw.items()}


def lookup_embassy(country: str) -> GeocodeResult | None:
    """Return the Greek-soil coords of the given country's embassy, or None."""
    data = _load_embassies().get(country.strip().lower())
    if not data:
        return None
    return GeocodeResult(
        lat=data["lat"],
        lon=data["lon"],
        location_name=f"Πρεσβεία ({country})",
        city=data.get("city_name", "Αθήνα"),
    )


def _finalize(results: list[GeocodeResult]) -> list[GeocodeResult]:
    """Stamp region_code + is_foreign on each geocoded result."""
    for r in results:
        r.region_code = region_for_point(r.lat, r.lon)
        if not r.is_foreign:
            r.is_foreign = not point_in_greece(r.lat, r.lon)
    return results
