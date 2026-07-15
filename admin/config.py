"""Admin app settings loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class AdminSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/social_reaction"
    )
    admin_password_hash: str = ""
    admin_secret_key: str = ""


settings = AdminSettings()
