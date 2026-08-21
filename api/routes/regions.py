"""Regional statistics/context read endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models import (
    ChoroplethResponse, ChoroplethValue, IndicatorValue, RegionIndicatorsResponse,
)
from stats.catalog import load_catalog
from stats.context import assemble

router = APIRouter(tags=["regions"])

# latest period per indicator for a set of region codes
_LATEST_SQL = """
SELECT DISTINCT ON (indicator) indicator, value, unit, period, source, source_url
FROM region_indicators
WHERE region_code = ANY(:codes)
ORDER BY indicator, period DESC
"""


async def latest_rows(session: AsyncSession, codes: list[str]) -> list[dict]:
    result = await session.execute(text(_LATEST_SQL), {"codes": codes})
    return [
        {"indicator": r[0], "value": r[1], "unit": r[2], "period": r[3],
         "source": r[4], "source_url": r[5]}
        for r in result.all()
    ]


@router.get("/regions/{region_code}/indicators", response_model=RegionIndicatorsResponse)
async def region_indicators(
    region_code: str, db: AsyncSession = Depends(get_db)
) -> RegionIndicatorsResponse:
    rows = await latest_rows(db, [region_code, "GR"])
    catalog = load_catalog()
    # For a bare region (no event) treat every non-always_on indicator as "thematic".
    all_themes = sorted({t for s in catalog for t in s.themes})
    always_on, thematic = assemble(catalog, rows, thematic_fields=all_themes)
    return RegionIndicatorsResponse(
        region_code=region_code,
        always_on=[IndicatorValue(**i) for i in always_on],
        thematic=[IndicatorValue(**i) for i in thematic],
    )


@router.get("/stats/choropleth", response_model=ChoroplethResponse)
async def choropleth(
    indicator: str = Query(...), db: AsyncSession = Depends(get_db)
) -> ChoroplethResponse:
    result = await db.execute(text("""
        SELECT DISTINCT ON (region_code) region_code, value, period
        FROM region_indicators
        WHERE indicator = :indicator AND region_code <> 'GR'
        ORDER BY region_code, period DESC
    """), {"indicator": indicator})
    values = [ChoroplethValue(region_code=r[0], value=r[1], period=r[2]) for r in result.all()]
    return ChoroplethResponse(indicator=indicator, values=values)
