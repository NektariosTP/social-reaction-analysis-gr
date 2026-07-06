"""Pydantic response models shared between API and pipeline."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    db: str


# ---------------------------------------------------------------------------
# Article
# ---------------------------------------------------------------------------

class ArticleSummary(BaseModel):
    id: str
    source_id: str | None = None
    source_type: str | None = None
    url: str | None = None
    title: str | None = None
    published_at: datetime | None = None


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------

class EventSummary(BaseModel):
    id: str
    action_forms: list[str]
    thematic_fields: list[str]
    channel: str | None = None
    intensity: str | None = None
    summary_el: str | None = None
    summary_en: str | None = None
    lat: float | None = None
    lon: float | None = None
    region_code: str | None = None
    article_count: int
    source_count: int
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    status: str


class EventDetail(EventSummary):
    classification_confidence: dict[str, Any] | None = None
    articles: list[ArticleSummary] = []


# ---------------------------------------------------------------------------
# GeoJSON
# ---------------------------------------------------------------------------

class GeoJSONGeometry(BaseModel):
    type: str = "Point"
    coordinates: list[float]


class GeoJSONProperties(BaseModel):
    id: str
    action_forms: list[str]
    thematic_fields: list[str]
    channel: str | None = None
    intensity: str | None = None
    summary_en: str | None = None
    article_count: int
    first_seen: datetime | None = None


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: GeoJSONProperties


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class DistributionItem(BaseModel):
    label: str
    count: int


class StatsResponse(BaseModel):
    total_events: int
    total_articles: int
    by_action_form: list[DistributionItem]
    by_thematic_field: list[DistributionItem]
    by_channel: list[DistributionItem]
    by_intensity: list[DistributionItem]
    by_region: list[DistributionItem]
    by_date: list[DistributionItem]