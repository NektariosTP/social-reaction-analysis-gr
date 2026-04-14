"""
backend/api/routes/health.py

GET /health  — lightweight liveness / readiness probe.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.nlp.vectorstore import collection_count

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    """Return API status and current vector store record count."""
    return {"status": "ok", "vector_store_count": collection_count()}
