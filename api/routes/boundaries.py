"""GET /boundaries/peripheries, GET /boundaries/municipalities."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter
from shapely.geometry import mapping, shape

from api.models import BoundaryFeature, BoundaryFeatureCollection, BoundaryProperties

router = APIRouter(prefix="/boundaries", tags=["boundaries"])

_REGIONS_PATH = Path(__file__).resolve().parent.parent.parent / "enrich" / "data" / "regions.geojson"
# Chosen against the rendered outline: ~1km in degrees. Small enough that the 13
# periphery shapes read cleanly at country zoom, large enough to shed vertices.
_PERIPHERY_TOLERANCE = 0.01


@lru_cache(maxsize=4)
def _simplified_peripheries(tol: float) -> BoundaryFeatureCollection:
    raw = json.loads(_REGIONS_PATH.read_text(encoding="utf-8"))
    features: list[BoundaryFeature] = []
    for f in raw["features"]:
        name = f["properties"]["name"]
        geom = shape(f["geometry"]).simplify(tol, preserve_topology=True)
        features.append(
            BoundaryFeature(
                geometry=mapping(geom),
                properties=BoundaryProperties(name=name, region_code=name),
            )
        )
    return BoundaryFeatureCollection(features=features)


@router.get("/peripheries", response_model=BoundaryFeatureCollection)
async def list_peripheries() -> BoundaryFeatureCollection:
    return _simplified_peripheries(_PERIPHERY_TOLERANCE)
