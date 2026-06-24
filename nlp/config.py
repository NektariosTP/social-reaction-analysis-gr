"""NLP pipeline settings loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class NlpSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/social_reaction"
    )
    embedding_model: str = (
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    )
    embedding_batch_size: int = 32
    cluster_window_days: int = 14
    hdbscan_min_cluster_size: int = 3
    hdbscan_min_samples: int = 2
    cluster_min_articles: int = 3
    cluster_min_intra_sim: float = 0.78
    event_registry_sim_threshold: float = 0.85
    dedup_cosine_threshold: float = 0.95
    dedup_time_window_hours: int = 72


settings = NlpSettings()
