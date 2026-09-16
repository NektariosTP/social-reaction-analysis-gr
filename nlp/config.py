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
    cluster_min_articles: int = 3
    cluster_min_intra_sim: float = 0.78
    event_registry_sim_threshold: float = 0.85
    event_merge_threshold: float = 0.92
    dedup_cosine_threshold: float = 0.95
    dedup_time_window_hours: int = 72
    cluster_tau: float = 0.72
    date_split_min_bucket: int = 3  # min dated articles for a bucket to peel into its own event
    date_split_tolerance_days: int = 0  # merge adjacent event-days (genuine multi-day events)
    embedding_dim: int = 768  # exposed for a future model swap: one line here + an Alembic step
    embedding_chunk_words: int = 100  # mpnet max_seq_length=128 tokens; conservative word window



settings = NlpSettings()
