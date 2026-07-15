"""Admin app factory: session middleware, exception handling, routers."""
from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from admin.auth import NotAuthenticated
from admin.config import settings
from admin.routes import events, login

app = FastAPI(title="Social Reaction Analysis GR — Admin")
app.add_middleware(SessionMiddleware, secret_key=settings.admin_secret_key)


@app.exception_handler(NotAuthenticated)
async def not_authenticated_handler(request: Request, exc: NotAuthenticated) -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=303)


app.include_router(login.router)
app.include_router(events.router)
