# reactions/place.py
"""Offline place resolution for announcements: gazetteer lookup + national-scope flag."""
from __future__ import annotations

from pydantic import BaseModel

from enrich.geocode import detect_national_scope, lookup_gazetteer


class PlaceResult(BaseModel):
    lat: float | None = None
    lon: float | None = None
    name: str | None = None
    is_national: bool = False


def resolve_place(text: str) -> PlaceResult:
    national = detect_national_scope(text)
    hit = lookup_gazetteer(text)
    if hit is None:
        return PlaceResult(is_national=national)
    return PlaceResult(lat=hit.lat, lon=hit.lon, name=hit.location_name, is_national=national)
