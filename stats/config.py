"""Stats pipeline settings."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class StatsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/social_reaction"
    )


settings = StatsSettings()
