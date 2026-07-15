"""GET/POST /login, POST /logout."""
from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse, Response

from admin.auth import verify_password

router = APIRouter()
templates = Jinja2Templates(directory="admin/templates")


@router.get("/login", response_class=Response)
async def login_form(request: Request) -> Response:
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login", response_class=Response)
async def login_submit(request: Request, password: str = Form(...)) -> Response:
    if verify_password(password):
        request.session["authenticated"] = True
        return RedirectResponse(url="/events?status=pending_review", status_code=303)
    return templates.TemplateResponse(
        request, "login.html", {"error": "Wrong password."}, status_code=401
    )


@router.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
