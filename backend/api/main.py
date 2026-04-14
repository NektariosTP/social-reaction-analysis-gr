"""
backend/api/main.py

FastAPI application factory for the Social Reaction Analysis GR REST API.

Usage:
    uvicorn backend.api.main:app --reload --port 8000

Endpoints:
    GET /events                     list all event clusters
    GET /events?category=X          filter by reaction_category
    GET /events?location_country=X  filter by dominant country
    GET /events/{cluster_id}        event detail with articles
    GET /stats                      aggregate statistics
    GET /docs                       Swagger UI (auto-generated)
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import events, health, stats

app = FastAPI(
    title="Social Reaction Analysis GR",
    description="REST API serving clustered Greek social reaction event data.",
    version="1.0.0",
)

# Allow cross-origin requests so the frontend can be opened as a local file
# or served from a different port during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(health.router)
app.include_router(stats.router)

# Serve the frontend at /ui (mounted after API routes so they take precedence).
_FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if _FRONTEND_DIR.exists():
    app.mount(
        "/ui",
        StaticFiles(directory=str(_FRONTEND_DIR), html=True),
        name="frontend",
    )
