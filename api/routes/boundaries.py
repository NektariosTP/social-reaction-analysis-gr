"""GET /boundaries/peripheries, GET /boundaries/municipalities."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from shapely.geometry import mapping, shape
from sqlalchemy import text
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models import BoundaryFeature, BoundaryFeatureCollection, BoundaryProperties

router = APIRouter(prefix="/boundaries", tags=["boundaries"])

_REGIONS_PATH = Path(__file__).resolve().parent.parent.parent / "enrich" / "data" / "regions.geojson"
# ~11m in degrees at Greek latitudes. Peripheries with dense island clusters (South
# Aegean, North Aegean, Ionian) need this fine a tolerance just to stay a sane payload
# size — anything coarser (e.g. 0.01) crushes small islands to a handful of points.
_PERIPHERY_TOLERANCE = 0.0001


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


# Municipalities with small offshore exclaves (e.g. Δήμος Μυκόνου includes Δήλος and ~30
# islets) lose real coastline detail well before 0.001 — verified against the live table:
# at 0.01 a 3.5km² island like Delos drops to 5 points, at 0.0001 it keeps ~180. No island
# above ~0.5km² anywhere in the table degrades below 6 points at this tolerance.
_MUNI_TOLERANCE = 0.0001


async def _fetch_municipalities(session: AsyncSession, periphery: str) -> list[Row[Any]]:
    result = await session.execute(
        text(
            "SELECT name, region_code, "
            "ST_AsGeoJSON(ST_SimplifyPreserveTopology(geom::geometry, :tol)) AS geometry "
            "FROM municipalities WHERE region_code = :periphery"
        ),
        {"tol": _MUNI_TOLERANCE, "periphery": periphery},
    )
    return list(result.all())


@router.get("/municipalities", response_model=BoundaryFeatureCollection)
async def list_municipalities(
    periphery: Annotated[str, Query(description="region_code of the parent periphery")],
    db: AsyncSession = Depends(get_db),
) -> BoundaryFeatureCollection:
    rows = await _fetch_municipalities(db, periphery)
    return BoundaryFeatureCollection(
        features=[
            BoundaryFeature(
                geometry=json.loads(r.geometry),
                properties=BoundaryProperties(name=r.name, region_code=r.region_code),
            )
            for r in rows
            if r.geometry
        ]
    )
