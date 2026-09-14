"""Reactions pipeline settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class ReactionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/social_reaction"
    request_delay_seconds: float = 2.0
    seed_dedup_sim: float = 0.9
    announcement_merge_sim: float = 0.72  # day-gated semantic merge threshold (tuned, Task 9)
    filter_variant: str = "broad"
    reactions_max_age_days: int = 14


settings = ReactionSettings()
