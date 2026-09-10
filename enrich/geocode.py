"""Geocoding: deterministic resolution of LLM-extracted place mentions → Nominatim.

The LLM never emits coordinates — it names places (see enrich.enrich_llm); this
module resolves those names to coordinates via Nominatim/embassy gazetteer and
stamps the in-Greece geofence. Unresolved domestic names are kept with NULL
coordinates rather than dropped.
"""
from __future__ import annotations

import re
import asyncio
import logging
from functools import lru_cache
from pathlib import Path

import httpx
import yaml
from pydantic import BaseModel

from enrich.config import settings
from sqlalchemy.ext.asyncio import AsyncSession

import json
from shapely.geometry import Point, shape
from shapely.prepared import prep

logger = logging.getLogger(__name__)

_GAZETTEER_PATH = Path(__file__).parent / "data" / "gazetteer.yml"
_REGIONS_PATH = Path(__file__).parent / "data" / "regions.geojson"
_EMBASSIES_PATH = Path(__file__).parent / "data" / "embassies.yml"
_NATIONAL_SIGNALS_PATH = Path(__file__).parent / "data" / "national_signals.yml"


class GeocodeResult(BaseModel):
    lat: float | None
    lon: float | None
    location_name: str
    city: str | None = None
    is_foreign: bool = False
    is_primary: bool = True


class LocationMention(BaseModel):
    venue: str | None = None  # specific place (e.g. "Πλατεία Συντάγματος")
    city: str               # city (e.g. "Αθήνα") — always required
    region: str | None = None
    is_foreign: bool = False  # LLM-reported: place is outside Greece
    embassy_of: str | None = None  # country name if this is a foreign embassy on Greek soil


# Trailing Greek-letter run so a nominative key still matches its inflected forms
# (e.g. "θεσσαλονίκη" → "θεσσαλονίκης"). ς is within α-ω; accented vowels listed explicitly.
_GREEK_SUFFIX = "[α-ωάέήίόύώϊϋΐΰ]*"


@lru_cache(maxsize=1)
def _load_gazetteer() -> list[tuple[re.Pattern[str], float, float, str]]:
    """Compile each entry once into (word-boundary pattern, lat, lon, display_name).

    The YAML key is the surface form matched in text; optional `name` is the display
    label (defaults to the key). Leading \\b rejects mid-word hits (e.g. 'δεθ' inside
    'συνδεθείτε'); the trailing suffix keeps inflected matches.
    """
    raw: dict[str, dict] = yaml.safe_load(_GAZETTEER_PATH.read_text(encoding="utf-8")) or {}
    entries: list[tuple[re.Pattern[str], float, float, str]] = []
    for key, data in raw.items():
        pattern = re.compile(r"\b" + re.escape(key.lower()) + _GREEK_SUFFIX)
        display = data.get("name") or key
        entries.append((pattern, float(data["lat"]), float(data["lon"]), display))
    return entries


def lookup_gazetteer(text: str) -> GeocodeResult | None:
    """Return first gazetteer match found in text, or None."""
    text_lower = text.lower()
    for pattern, lat, lon, display in _load_gazetteer():
        if pattern.search(text_lower):
            return GeocodeResult(lat=lat, lon=lon, location_name=display, city=display)
    return None


@lru_cache(maxsize=1)
def _load_national_signals() -> list[str]:
    raw = yaml.safe_load(_NATIONAL_SIGNALS_PATH.read_text(encoding="utf-8")) or {}
    signals = list(raw.get("keywords", []))
    return [s.lower() for s in signals]


def detect_national_scope(text: str) -> bool:
    """True when the text carries panhellenic/national-scope signals."""
    t = text.lower()
    return any(sig in t for sig in _load_national_signals())


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


async def resolve_locations(
    mentions: list[LocationMention],
    *,
    national: bool,
    nominatim_url: str | None = None,
    session: AsyncSession | None = None,
) -> list[GeocodeResult]:
    """Resolve pre-extracted place mentions → coordinates (LLM never emits coords).

    National scope with no specific venue → unlocated. Embassies resolve to their
    Greek-soil coords. LLM-flagged-foreign mentions skip Nominatim entirely (our
    self-hosted instance is Greece-scoped: for a genuinely foreign name it either
    finds nothing or spuriously matches an unrelated same-named Greek place — the
    LLM's verdict is trusted directly instead of risking a bogus domestic pin). A
    domestic name Nominatim cannot resolve is KEPT with NULL coordinates (fixable
    later in the admin editor), never dropped.
    """
    has_venue = any(getattr(m, "venue", None) for m in mentions) or len(mentions) > 1
    if national and not has_venue:
        logger.debug("[geocode] National scope, no venue → leaving event unlocated.")
        return []
    if not mentions:
        return []

    results: list[GeocodeResult] = []
    for i, m in enumerate(mentions):
        is_primary = i == 0
        if m.embassy_of:
            emb = lookup_embassy(m.embassy_of)
            if emb:
                emb.is_primary = is_primary
                results.append(emb)
                continue
        if m.is_foreign:
            results.append(GeocodeResult(
                lat=None, lon=None, location_name=m.venue or m.city,
                city=m.city, is_foreign=True, is_primary=is_primary,
            ))
            continue
        query = f"{m.venue}, {m.city}" if m.venue else m.city
        r = await geocode_text(query, city=m.city, nominatim_url=nominatim_url)
        if r is not None:
            r.is_primary = is_primary
            results.append(r)
        else:  # keep the unresolved name with NULL coords (spec decision b)
            results.append(GeocodeResult(
                lat=None, lon=None, location_name=m.venue or m.city,
                city=m.city, is_primary=is_primary,
            ))
    return await _finalize(results, session)


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


def _region_for_point(lat: float, lon: float) -> str | None:
    """Return the canonical English periphery name containing (lat, lon), or None."""
    point = Point(lon, lat)
    for name, geom in _load_regions():
        if geom.contains(point):
            return name
    return None


def point_in_greece(lat: float, lon: float) -> bool:
    """True iff (lat, lon) falls inside any of the 13 peripheries (geofence only)."""
    return _region_for_point(lat, lon) is not None


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


async def _finalize(
    results: list[GeocodeResult], session: AsyncSession | None = None
) -> list[GeocodeResult]:
    """Stamp is_foreign via the in-Greece geofence; no region/municipality labels."""
    for r in results:
        if r.lat is None or r.lon is None:
            continue  # LLM-confirmed foreign, no coordinate to check
        if not r.is_foreign:
            r.is_foreign = not point_in_greece(r.lat, r.lon)
    return results
