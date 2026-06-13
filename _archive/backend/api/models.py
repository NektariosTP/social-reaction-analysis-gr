"""
backend/api/models.py

Pydantic response models for the Phase 5 REST API.
"""

from __future__ import annotations

from pydantic import BaseModel


class ArticleSummary(BaseModel):
    id: str
    source: str
    url: str
    title: str
    published_at: str
    lat: float | None = None
    lon: float | None = None


class EventSummary(BaseModel):
    event_id: str
    cluster_id: int
    reaction_category: str
    summary_en: str
    summary_el: str
    event_date: str
    lat: float | None = None
    lon: float | None = None
    location_name: str | None = None
    location_country: str | None = None
    article_count: int
    sources: list[str]


class EventDetail(EventSummary):
    articles: list[ArticleSummary]


class DateCount(BaseModel):
    date: str
    count: int


class StatsResponse(BaseModel):
    total_events: int
    total_articles: int
    geocoded_articles: int
    categories: dict[str, int]
    by_country: dict[str, int]
    by_date: list[DateCount]
