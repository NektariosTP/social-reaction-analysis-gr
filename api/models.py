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
    municipality: str | None = None
    article_count: int
    source_count: int
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    status: str
    event_time: datetime | None = None
    temporal_status: str | None = None
    is_national: bool = False


class EventDetail(EventSummary):
    classification_confidence: dict[str, Any] | None = None
    articles: list[ArticleSummary] = []


class LocationPoint(BaseModel):
    lat: float
    lon: float
    label: str | None = None
    is_primary: bool


# ---------------------------------------------------------------------------
# GeoJSON
# ---------------------------------------------------------------------------

class GeoJSONGeometry(BaseModel):
    type: str = "Point"
    coordinates: list[float]


class GeoJSONProperties(BaseModel):
    id: str
    region_code: str | None = None
    municipality: str | None = None
    action_forms: list[str]
    thematic_fields: list[str]
    channel: str | None = None
    intensity: str | None = None
    summary_en: str | None = None
    article_count: int
    first_seen: datetime | None = None
    locations: list[LocationPoint] = []


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: GeoJSONProperties


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]


# ---------------------------------------------------------------------------
# Boundaries
# ---------------------------------------------------------------------------

class BoundaryProperties(BaseModel):
    name: str
    region_code: str | None = None


class BoundaryFeature(BaseModel):
    type: str = "Feature"
    geometry: dict[str, Any]
    properties: BoundaryProperties


class BoundaryFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[BoundaryFeature]


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


# ---------------------------------------------------------------------------
# Region indicators / context
# ---------------------------------------------------------------------------

class IndicatorValue(BaseModel):
    key: str
    label_el: str
    label_en: str
    unit: str | None = None
    value: float | None = None
    period: str | None = None
    source: str | None = None
    source_url: str | None = None


class RegionIndicatorsResponse(BaseModel):
    region_code: str
    always_on: list[IndicatorValue] = []
    thematic: list[IndicatorValue] = []


class EventContextResponse(RegionIndicatorsResponse):
    pass


class ChoroplethValue(BaseModel):
    region_code: str
    value: float | None = None
    period: str | None = None


class ChoroplethResponse(BaseModel):
    indicator: str
    values: list[ChoroplethValue] = []