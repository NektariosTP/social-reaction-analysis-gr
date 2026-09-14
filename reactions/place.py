# reactions/place.py
"""Offline place resolution for announcements: gazetteer lookup + national-scope flag."""
from __future__ import annotations

from pydantic import BaseModel

from enrich.geocode import detect_national_scope


class PlaceResult(BaseModel):
    lat: float | None = None
    lon: float | None = None
    name: str | None = None
    is_national: bool = False


def resolve_place(text: str) -> PlaceResult:
    # Gazetteer coords are deliberately NOT used at seed time — the LLM geocoder owns
    # primary_location after approval. We only need the cheap national-scope flag here.
    return PlaceResult(is_national=detect_national_scope(text))
