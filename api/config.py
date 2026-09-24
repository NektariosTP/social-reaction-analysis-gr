"""Application settings loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/social_reaction"
    )
    cache_ttl_seconds: int = 120
    cors_origins: list[str] = ["*"]
    # Per-IP API rate limit (limits syntax, e.g. "60/minute"). Applied to all
    # routes except /health; keyed by the real client IP (X-Forwarded-For behind
    # Caddy). Set rate_limit_enabled=False to turn it off entirely.
    rate_limit: str = "60/minute"
    rate_limit_enabled: bool = True


settings = Settings()