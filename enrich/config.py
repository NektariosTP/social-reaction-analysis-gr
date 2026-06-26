"""Enrichment pipeline settings."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnrichSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/social_reaction"
    )
    # LLM provider — auto-detected from available keys if omitted
    groq_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = ""
    llm_max_tokens: int = 512
    llm_temperature: float = 0.0

    # Nominatim
    nominatim_url: str = "http://nominatim:8080"
    nominatim_delay_seconds: float = 1.1

    # Embedding model (for zero-shot classification — same as Phase 2)
    embedding_model: str = (
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    )

    # Retry / batching
    llm_max_retries: int = 3
    llm_retry_base_delay: float = 2.0


settings = EnrichSettings()
