"""Admin event queue, browse, editor, and delete routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse, Response

from admin.auth import require_admin
from admin.db import get_db
from enrich.classify import AXIS_ACTION_FORMS, AXIS_CHANNEL, AXIS_INTENSITY, AXIS_THEMATIC_FIELDS

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


async def _fetch_event_detail(session: AsyncSession, event_id: str) -> Any | None:
    result = await session.execute(
        text("""
            SELECT id, action_forms, thematic_fields, channel, intensity,
                   summary_el, summary_en, classification_confidence,
                   ST_Y(primary_location::geometry) AS lat,
                   ST_X(primary_location::geometry) AS lon,
                   region_code, article_count, source_count,
                   first_seen, last_seen, status
            FROM events WHERE id = :id
        """),
        {"id": event_id},
    )
    return result.first()


async def _fetch_event_locations(session: AsyncSession, event_id: str) -> list[Any]:
    result = await session.execute(
        text("""
            SELECT id, ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lon,
                   location_name, city, is_primary
            FROM event_locations WHERE event_id = :id ORDER BY is_primary DESC, id
        """),
        {"id": event_id},
    )
    return result.all()


async def _fetch_event_articles(session: AsyncSession, event_id: str) -> list[Any]:
    result = await session.execute(
        text("""
            SELECT id, title, url, source_type, published_at
            FROM articles WHERE event_id = :id ORDER BY published_at DESC
        """),
        {"id": event_id},
    )
    return result.all()


def _edit_form_context(event: Any, locations: list[Any], articles: list[Any], error: str | None) -> dict[str, Any]:
    return {
        "event": event,
        "locations": locations,
        "articles": articles,
        "statuses": ALL_STATUSES,
        "axis_action_forms": AXIS_ACTION_FORMS,
        "axis_thematic_fields": AXIS_THEMATIC_FIELDS,
        "axis_channel": AXIS_CHANNEL,
        "axis_intensity": AXIS_INTENSITY,
        "error": error,
    }


@router.get("/events/{event_id}", response_class=Response)
async def edit_event_form(
    request: Request, event_id: str, session: AsyncSession = Depends(get_db)
) -> Response:
    event = await _fetch_event_detail(session, event_id)
    if event is None:
        return HTMLResponse("Event not found", status_code=404)
    locations = await _fetch_event_locations(session, event_id)
    articles = await _fetch_event_articles(session, event_id)
    return templates.TemplateResponse(
        request, "event_edit.html", _edit_form_context(event, locations, articles, None)
    )


async def _save_event_locations(session: AsyncSession, event_id: str, form: Any) -> None:
    loc_ids = form.getlist("loc_id")
    loc_lats = form.getlist("loc_lat")
    loc_lons = form.getlist("loc_lon")
    loc_names = form.getlist("loc_name")
    loc_cities = form.getlist("loc_city")
    loc_primaries = set(form.getlist("loc_is_primary"))
    loc_deletes = set(form.getlist("loc_delete"))

    for i, loc_id in enumerate(loc_ids):
        idx = str(i)
        if idx in loc_deletes and loc_id:
            await session.execute(text("DELETE FROM event_locations WHERE id = :id"), {"id": loc_id})
            continue

        lat_raw = loc_lats[i] if i < len(loc_lats) else ""
        lon_raw = loc_lons[i] if i < len(loc_lons) else ""
        if not lat_raw or not lon_raw:
            continue

        lat = float(lat_raw)
        lon = float(lon_raw)
        name = loc_names[i] if i < len(loc_names) else ""
        city = loc_cities[i] if i < len(loc_cities) else ""
        is_primary = idx in loc_primaries

        if loc_id:
            await session.execute(
                text("""
                    UPDATE event_locations SET
                        location = ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                        location_name = :name, city = :city, is_primary = :is_primary
                    WHERE id = :id
                """),
                {"lat": lat, "lon": lon, "name": name or None, "city": city or None,
                 "is_primary": is_primary, "id": loc_id},
            )
        else:
            await session.execute(
                text("""
                    INSERT INTO event_locations (event_id, location, location_name, city, is_primary)
                    VALUES (:event_id, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :name, :city, :is_primary)
                """),
                {"event_id": event_id, "lat": lat, "lon": lon, "name": name or None,
                 "city": city or None, "is_primary": is_primary},
            )


@router.post("/events/{event_id}", response_class=Response)
async def edit_event_submit(
    request: Request, event_id: str, session: AsyncSession = Depends(get_db)
) -> Response:
    form = await request.form()

    action_forms = form.getlist("action_forms")
    thematic_fields = form.getlist("thematic_fields")
    channel = form.get("channel", "")
    intensity = form.get("intensity", "")
    status = form.get("status", "")
    summary_el = form.get("summary_el", "") or None
    summary_en = form.get("summary_en", "") or None
    region_code = form.get("region_code", "") or None
    lat_raw = form.get("lat", "")
    lon_raw = form.get("lon", "")

    errors: list[str] = []
    if not set(action_forms).issubset(set(AXIS_ACTION_FORMS)):
        errors.append("Invalid action form selected.")
    if not set(thematic_fields).issubset(set(AXIS_THEMATIC_FIELDS)):
        errors.append("Invalid thematic field selected.")
    if channel not in AXIS_CHANNEL:
        errors.append("Invalid channel.")
    if intensity not in AXIS_INTENSITY:
        errors.append("Invalid intensity.")
    if status not in ALL_STATUSES:
        errors.append("Invalid status.")

    lat: float | None = None
    lon: float | None = None
    try:
        lat = float(lat_raw) if lat_raw else None
        lon = float(lon_raw) if lon_raw else None
    except ValueError:
        errors.append("Latitude/longitude must be numbers.")

    if errors:
        event = await _fetch_event_detail(session, event_id)
        locations = await _fetch_event_locations(session, event_id)
        articles = await _fetch_event_articles(session, event_id)
        return templates.TemplateResponse(
            request,
            "event_edit.html",
            _edit_form_context(event, locations, articles, " ".join(errors)),
            status_code=422,
        )

    await session.execute(
        text("""
            UPDATE events SET
                action_forms = :action_forms,
                thematic_fields = :thematic_fields,
                channel = :channel,
                intensity = :intensity,
                summary_el = :summary_el,
                summary_en = :summary_en,
                region_code = :region_code,
                status = :status,
                primary_location = CASE WHEN CAST(:lat AS double precision) IS NOT NULL
                    THEN ST_SetSRID(ST_MakePoint(CAST(:lon AS double precision), CAST(:lat AS double precision)), 4326)::geography
                    ELSE NULL END
            WHERE id = :id
        """),
        {
            "action_forms": action_forms,
            "thematic_fields": thematic_fields,
            "channel": channel,
            "intensity": intensity,
            "summary_el": summary_el,
            "summary_en": summary_en,
            "region_code": region_code,
            "status": status,
            "lat": lat,
            "lon": lon,
            "id": event_id,
        },
    )

    await _save_event_locations(session, event_id, form)
    await session.commit()
    return RedirectResponse(url=f"/events/{event_id}", status_code=303)
