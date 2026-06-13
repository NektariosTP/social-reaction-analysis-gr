"""
backend/llm/geocode.py

Location extraction and geocoding for Phase 4.

Strategy (cluster-level — one LLM call per cluster, not per article):
  1. Ask the LLM to extract the primary Greek location from the best
     canonical article (title + body) in the cluster.
  2. Pass the extracted place name to Nominatim with country_codes=gr
     (Greece-only; no global fallback).
  3. Accept the result only if it falls within GREECE_BBOX.

The geocoding result is cached by cluster_id so that all member articles
in the cluster receive the same coordinates without additional API calls.

The final output for each record includes:
  - lat (float | None)
  - lon (float | None)
  - location_name (str)   — human-readable place (city, region, …)
  - location_country (str) — full country name
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass

import litellm
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from backend.llm.config import (
    NOMINATIM_USER_AGENT,
    NOMINATIM_DELAY_SECONDS,
    GREECE_BBOX,
    LLM_MODEL,
    LLM_TEMPERATURE,
)
from backend.llm.geo_validate import is_within_greece

logger = logging.getLogger(__name__)

litellm.suppress_debug_info = True


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class GeocodeResult:
    lat: float | None = None
    lon: float | None = None
    location_name: str = ""
    location_country: str = ""


# ---------------------------------------------------------------------------
# Cluster-level cache: cluster_id → GeocodeResult
# This is the primary cache. A resolved result for a cluster is reused for
# all member articles, avoiding redundant LLM and Nominatim calls.
# ---------------------------------------------------------------------------

_cluster_geo_cache: dict[int, list[GeocodeResult]] = {}

# Secondary cache for Nominatim calls: place string → GeocodeResult | None
_nominatim_cache: dict[str, GeocodeResult | None] = {}


# ---------------------------------------------------------------------------
# Nominatim client singleton
# ---------------------------------------------------------------------------

_GEOCODER: Nominatim | None = None


def _get_geocoder() -> Nominatim:
    global _GEOCODER
    if _GEOCODER is None:
        _GEOCODER = Nominatim(user_agent=NOMINATIM_USER_AGENT)
    return _GEOCODER


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _within_greece(lat: float, lon: float) -> bool:
    """Return True if the coordinate falls within Greece's territory polygon."""
    return is_within_greece(lat, lon)


# Nominatim OSM classes that represent actual geographic places.
# Results with other classes (e.g. 'office', 'railway', 'natural') are skipped
# so that embassy/station hits for foreign-sounding names are rejected.
_ACCEPTED_OSM_CLASSES: frozenset[str] = frozenset({"place", "boundary", "amenity"})


def _nominatim_query(place: str) -> GeocodeResult | None:
    """
    Query Nominatim for *place* with country_codes=gr (no global fallback).

    Returns the first result whose OSM class is a genuine geographic place
    (place / boundary / amenity) and lies within GREECE_BBOX.
    Result is cached to avoid duplicate API calls.
    """
    if place in _nominatim_cache:
        return _nominatim_cache[place]

    geocoder = _get_geocoder()
    time.sleep(NOMINATIM_DELAY_SECONDS)
    try:
        results = geocoder.geocode(
            place,
            exactly_one=False,
            addressdetails=True,
            language="el",
            country_codes="gr",
            viewbox=[(GREECE_BBOX[1], GREECE_BBOX[0]), (GREECE_BBOX[3], GREECE_BBOX[2])],
            bounded=True,
        )
        if not results:
            _nominatim_cache[place] = None
            return None

        for location in results:
            raw = location.raw
            osm_class = raw.get("class", "")
            if osm_class not in _ACCEPTED_OSM_CLASSES:
                continue
            lat, lon = location.latitude, location.longitude
            if not _within_greece(lat, lon):
                continue
            addr = raw.get("address", {})
            # Prefer specific place names over administrative units
            location_name = (
                addr.get("city")
                or addr.get("town")
                or addr.get("village")
                or addr.get("suburb")
                or addr.get("neighbourhood")
                or addr.get("municipality")
                or addr.get("county")
                or addr.get("state")
                or location.address.split(",")[0]
            )
            country = addr.get("country", "")
            result = GeocodeResult(lat=lat, lon=lon, location_name=location_name, location_country=country)
            _nominatim_cache[place] = result
            return result

        # No acceptable result found (e.g. only embassies / stations returned)
        _nominatim_cache[place] = None
        return None
    except (GeocoderTimedOut, GeocoderServiceError) as exc:
        logger.warning("[geocode] Nominatim error for %r: %s", place, exc)
        _nominatim_cache[place] = None
        return None


# LLM system prompt for location extraction.
_LOCATION_SYSTEM_PROMPT = (
    "Given a Greek news article, return ALL distinct Greek places where the event is happening.\n"
    "Each place can be an address, city, region, municipality, landmark, or institution "
    "(e.g. 'Θεσσαλονίκη', 'Κρήτη', 'ΑΠΘ', 'Πολυτεχνείο', 'Ακρόπολη').\n"
    "If the event is outside Greece or no specific place can be found, return null.\n"
    'Respond ONLY with JSON: {"locations": ["<place1 in Greek>", "<place2 in Greek>"]} '
    'or {"locations": null}'
)


def _llm_extract_location(title: str, body: str) -> list[str]:
    """
    Use the LLM to extract Greek locations from *title* + *body*.

    Returns a list of place name strings (in Greek), or an empty list if the
    LLM could not identify any location within Greece.
    Body is truncated to 500 characters to keep token usage low.
    """
    body_snippet = body[:500] if body else ""
    user_content = f"Title: {title}\n\nBody: {body_snippet}"
    try:
        response = litellm.completion(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _LOCATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=128,
        )
        raw = response.choices[0].message.content or ""
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
        parsed = json.loads(raw)
        # Support both new {"locations": [...]} and legacy {"location": "..."}
        locations = parsed.get("locations") or parsed.get("location")
        if locations is None:
            return []
        if isinstance(locations, str):
            locations = [locations]
        return [loc.strip() for loc in locations if isinstance(loc, str) and loc.strip()]
    except Exception as exc:
        logger.warning("[geocode] LLM location extraction failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def geocode_cluster(cluster_id: int, title: str, body: str) -> list[GeocodeResult]:
    """
    Resolve location(s) for an entire cluster using one LLM call + Nominatim.

    This is the primary entry point for the geocoding pipeline step.
    Results are cached by *cluster_id* — call this once per cluster, then
    use ``geocode_record`` to retrieve the cached result for each member.

    Parameters
    ----------
    cluster_id : int
        The cluster ID (used as cache key).
    title : str
        Title of the best canonical article in the cluster.
    body : str
        Body text of the best canonical article in the cluster.

    Returns
    -------
    list[GeocodeResult]
        One or more resolved locations. Empty list if no Greek location found.
    """
    if cluster_id in _cluster_geo_cache:
        return _cluster_geo_cache[cluster_id]

    results: list[GeocodeResult] = []

    places = _llm_extract_location(title, body)
    logger.debug("[geocode] Cluster %d — LLM extracted: %r", cluster_id, places)

    for place in places:
        nominatim_result = _nominatim_query(place)
        if nominatim_result and nominatim_result.lat is not None:
            results.append(nominatim_result)
            logger.info(
                "[geocode] Cluster %d — %r → lat=%.4f lon=%.4f (%s)",
                cluster_id, place, nominatim_result.lat, nominatim_result.lon,
                nominatim_result.location_name,
            )
        else:
            logger.debug(
                "[geocode] Cluster %d — %r did not resolve within Greece.",
                cluster_id, place,
            )

    if not results and not places:
        logger.debug("[geocode] Cluster %d — LLM returned no locations.", cluster_id)

    _cluster_geo_cache[cluster_id] = results
    return results


def geocode_record(meta: dict, text: str) -> GeocodeResult:
    """
    Retrieve the primary cached geocoding result for the cluster this record
    belongs to (first location in the list).

    This function is called per-record by the pipeline's metadata write step.
    It assumes ``geocode_cluster`` has already been called for the cluster and
    the result is stored in ``_cluster_geo_cache``.

    If no cached result exists (e.g. noise record with cluster_id=-1), an
    empty GeocodeResult is returned.

    Parameters
    ----------
    meta : dict
        ChromaDB metadata dict for the record.
    text : str
        Unused — kept for interface compatibility with the pipeline.

    Returns
    -------
    GeocodeResult
    """
    cluster_id = meta.get("cluster_id", -1)
    if cluster_id == -1:
        return GeocodeResult()
    results = _cluster_geo_cache.get(cluster_id, [])
    return results[0] if results else GeocodeResult()
