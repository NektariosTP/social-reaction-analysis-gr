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


# ~1km simplify; ST_SimplifyPreserveTopology keeps δήμος borders valid.
_MUNI_TOLERANCE = 0.01


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
