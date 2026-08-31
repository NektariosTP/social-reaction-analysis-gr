"""Reactions pipeline settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class ReactionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/social_reaction"
    request_delay_seconds: float = 2.0
    seed_dedup_sim: float = 0.9
    filter_variant: str = "broad"


settings = ReactionSettings()
