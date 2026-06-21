"""Ingestion pipeline settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/social_reaction"
    request_delay_seconds: float = 2.0
    max_articles_per_keyword: int = 15
    min_body_length: int = 50
    spacy_model: str = "el_core_news_md"


settings = IngestionSettings()
