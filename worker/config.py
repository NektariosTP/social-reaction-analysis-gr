"""Worker settings loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/social_reaction"
    )
    pipeline_mode: str = "scrape_only"
    pipeline_interval_seconds: int = 1800


settings = WorkerSettings()
