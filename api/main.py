"""FastAPI application factory."""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import RequestResponseEndpoint

from api.config import settings
from api.limiter import limiter
from api.routes import events, health

app = FastAPI(
    title="Social Reaction Analysis GR",
    description="Real-time detection and visualisation of social reactions in Greece.",
    version="0.1.0",
)

# Per-IP rate limiting. SlowAPIMiddleware applies `default_limits` to every route
# (except those marked @limiter.exempt, e.g. /health); the limiter reads the
# client IP via api.limiter.client_ip. A tripped limit returns HTTP 429.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)

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