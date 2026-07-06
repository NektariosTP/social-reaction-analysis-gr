"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import events, stats, health

app = FastAPI(
    title="Social Reaction Analysis GR",
    description="Real-time detection and visualisation of social reactions in Greece.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(stats.router)
app.include_router(health.router)
