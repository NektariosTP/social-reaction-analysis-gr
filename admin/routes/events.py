"""Admin event queue, browse, editor, and delete routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse, Response

from admin.auth import require_admin
from admin.db import get_db

router = APIRouter(dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory="admin/templates")

ALL_STATUSES = ["detected", "pending_review", "enriched", "archived", "closed", "rejected"]


async def _fetch_admin_events(
    session: AsyncSession,
    *,
    status: str | None,
    region_code: str | None,
    limit: int = 50,
    offset: int = 0,
) -> list[Any]:
    conditions: list[str] = []
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if status:
        conditions.append("status = :status")
        params["status"] = status
    if region_code:
        conditions.append("region_code = :region_code")
        params["region_code"] = region_code

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    result = await session.execute(
        text(f"""
            SELECT id, action_forms, thematic_fields, channel, intensity,
                   summary_el, article_count, first_seen, last_seen, status, region_code
            FROM events
            {where_clause}
            ORDER BY first_seen DESC NULLS LAST
            LIMIT :limit OFFSET :offset
        """),  # noqa: S608
        params,
    )
    return result.all()


@router.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/events?status=pending_review", status_code=303)


@router.get("/events", response_class=Response)
async def list_events(
    request: Request,
    session: AsyncSession = Depends(get_db),
    status: str = "pending_review",
    region_code: str | None = None,
) -> Response:
    status_filter = status if status in ALL_STATUSES else None
    rows = await _fetch_admin_events(session, status=status_filter, region_code=region_code)
    return templates.TemplateResponse(
        request,
        "events.html",
        {
            "events": rows,
            "statuses": ALL_STATUSES,
            "selected_status": status,
            "region_code": region_code or "",
        },
    )


@router.post("/events/{event_id}/approve")
async def approve_event(
    event_id: str, session: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    await session.execute(
        text("UPDATE events SET status = 'enriched' WHERE id = :id AND status = 'pending_review'"),
        {"id": event_id},
    )
    await session.commit()
    return RedirectResponse(url="/events?status=pending_review", status_code=303)


@router.post("/events/{event_id}/reject")
async def reject_event(
    event_id: str, session: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    await session.execute(
        text("UPDATE events SET status = 'rejected' WHERE id = :id AND status = 'pending_review'"),
        {"id": event_id},
    )
    await session.commit()
    return RedirectResponse(url="/events?status=pending_review", status_code=303)
