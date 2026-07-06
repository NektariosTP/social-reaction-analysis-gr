"""GET /stats — aggregated distributions for the dashboard."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models import DistributionItem, StatsResponse

router = APIRouter(tags=["stats"])


async def _compute_stats(session: AsyncSession) -> dict:
    total_events = (await session.execute(text("SELECT COUNT(*) FROM events WHERE status = 'enriched'"))).scalar() or 0
    total_articles = (await session.execute(text("SELECT COUNT(*) FROM articles WHERE is_duplicate = FALSE"))).scalar() or 0

    async def _unnest_dist(column: str, table: str = "events", condition: str = "status = 'enriched'") -> list[dict]:
        result = await session.execute(text(
            f"SELECT unnest({column}) AS label, COUNT(*) AS count "
            f"FROM {table} WHERE {condition} "
            f"GROUP BY label ORDER BY count DESC"
        ))
        return [{"label": r[0], "count": r[1]} for r in result.all() if r[0]]

    async def _single_dist(column: str, table: str = "events", condition: str = "status = 'enriched'") -> list[dict]:
        result = await session.execute(text(
            f"SELECT {column} AS label, COUNT(*) AS count "
            f"FROM {table} WHERE {condition} AND {column} IS NOT NULL "
            f"GROUP BY {column} ORDER BY count DESC"
        ))
        return [{"label": r[0], "count": r[1]} for r in result.all()]

    async def _date_dist() -> list[dict]:
        result = await session.execute(text(
            "SELECT DATE(first_seen) AS label, COUNT(*) AS count "
            "FROM events WHERE status = 'enriched' AND first_seen IS NOT NULL "
            "GROUP BY label ORDER BY label DESC LIMIT 90"
        ))
        return [{"label": str(r[0]), "count": r[1]} for r in result.all()]

    return {
        "total_events": total_events,
        "total_articles": total_articles,
        "by_action_form": await _unnest_dist("action_forms"),
        "by_thematic_field": await _unnest_dist("thematic_fields"),
        "by_channel": await _single_dist("channel"),
        "by_intensity": await _single_dist("intensity"),
        "by_region": await _single_dist("region_code"),
        "by_date": await _date_dist(),
    }


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)) -> StatsResponse:
    data = await _compute_stats(db)
    return StatsResponse(
        total_events=data["total_events"],
        total_articles=data["total_articles"],
        by_action_form=[DistributionItem(**d) for d in data["by_action_form"]],
        by_thematic_field=[DistributionItem(**d) for d in data["by_thematic_field"]],
        by_channel=[DistributionItem(**d) for d in data["by_channel"]],
        by_intensity=[DistributionItem(**d) for d in data["by_intensity"]],
        by_region=[DistributionItem(**d) for d in data["by_region"]],
        by_date=[DistributionItem(**d) for d in data["by_date"]],
    )
