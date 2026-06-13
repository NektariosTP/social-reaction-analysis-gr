"""
backend/llm/geo_validate.py

Geographic validation using the Greece regions GeoJSON polygon.

Provides a point-in-polygon check: any geocoded coordinate must fall inside
one of the 13 Greek periphery polygons (from frontend/greece-regions.geojson).
Coordinates that land in the sea or outside Greece are rejected.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from shapely.geometry import MultiPolygon, Point, shape
from shapely.ops import unary_union

logger = logging.getLogger(__name__)

_GEOJSON_PATH = Path(__file__).resolve().parent.parent.parent / "frontend" / "greece-regions.geojson"

_GREECE_POLYGON: MultiPolygon | None = None


def _load_polygon() -> MultiPolygon:
    """Load and merge all 13 Greek periphery polygons into one MultiPolygon."""
    global _GREECE_POLYGON
    if _GREECE_POLYGON is not None:
        return _GREECE_POLYGON

    with open(_GEOJSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    polygons = [shape(feature["geometry"]) for feature in data["features"]]
    merged = unary_union(polygons)

    if merged.geom_type == "Polygon":
        merged = MultiPolygon([merged])

    _GREECE_POLYGON = merged
    logger.info("[geo_validate] Loaded Greece polygon (%d peripheries).", len(data["features"]))
    return _GREECE_POLYGON


def is_within_greece(lat: float, lon: float, buffer_km: float = 5.0) -> bool:
    """
    Return True if the point (lat, lon) falls within the Greek territory
    polygons, with an optional buffer (in approximate km) to account for
    coastal locations and GeoJSON simplification.

    Parameters
    ----------
    lat : float
    lon : float
    buffer_km : float
        Buffer distance in approximate kilometres (converted to degrees).
        Default 5 km ≈ 0.045 degrees.
    """
    polygon = _load_polygon()
    point = Point(lon, lat)  # shapely uses (x=lon, y=lat)
    if polygon.contains(point):
        return True
    # Allow a small buffer for coastal/border locations
    buffer_deg = buffer_km / 111.0  # ~111 km per degree
    return polygon.buffer(buffer_deg).contains(point)
