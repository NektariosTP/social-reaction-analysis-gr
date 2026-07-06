"""FastAPI application factory."""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import RequestResponseEndpoint

from api.config import settings
from api.routes import events, health, stats

app = FastAPI(
    title="Social Reaction Analysis GR",
    description="Real-time detection and visualisation of social reactions in Greece.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_cache_control(request: Request, call_next: RequestResponseEndpoint) -> Response:
    response = await call_next(request)
    if request.method == "GET" and response.status_code == 200:
        response.headers["Cache-Control"] = f"public, max-age={settings.cache_ttl_seconds}"
    return response


app.include_router(health.router)
app.include_router(events.router)
app.include_router(stats.router)