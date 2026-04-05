"""
backend/nlp/config.py

Central configuration for the NLP & Semantic Analysis pipeline (Phase 3).
Values are loaded from the project .env file via python-dotenv.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# ------------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env")

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
RAW_DATA_DIR = Path(os.getenv("OUTPUT_DIR", str(_ROOT / "data" / "raw")))
VECTORDB_DIR = Path(os.getenv("VECTORDB_DIR", str(_ROOT / "data" / "vectordb")))
VECTORDB_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Embedding model
# ------------------------------------------------------------------
# Multilingual sentence-transformer with good Greek support.
# E5 models (intfloat/multilingual-e5-*) require a prompt prefix — see
# EMBEDDING_PROMPT_PREFIX below.  For paraphrase-* / MiniLM-* use "".
EMBEDDING_MODEL: str = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
)

# Maximum token length for the embedding model.
# Texts longer than this are truncated by sentence-transformers automatically.
EMBEDDING_MAX_SEQ_LENGTH: int = int(os.getenv("EMBEDDING_MAX_SEQ_LENGTH", "128"))

# Prefix prepended to every text before encoding.
# E5 models require "passage: " for document embeddings; leave empty for
# paraphrase-* / MiniLM-* models where no prefix is expected.
EMBEDDING_PROMPT_PREFIX: str = os.getenv("EMBEDDING_PROMPT_PREFIX", "")

# Batch size for encoding (tune based on available GPU/CPU memory).
EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))

# ------------------------------------------------------------------
# ChromaDB
# ------------------------------------------------------------------
CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "articles")

# ------------------------------------------------------------------
# Clustering (HDBSCAN)
# ------------------------------------------------------------------
# Minimum cluster size — smallest group of articles considered an event.
HDBSCAN_MIN_CLUSTER_SIZE: int = int(os.getenv("HDBSCAN_MIN_CLUSTER_SIZE", "2"))

# Minimum samples — controls density threshold. Lower = more clusters.
HDBSCAN_MIN_SAMPLES: int = int(os.getenv("HDBSCAN_MIN_SAMPLES", "1"))

# ------------------------------------------------------------------
# Post-clustering quality filter
# ------------------------------------------------------------------
# Clusters that do not meet these thresholds are demoted to noise before
# being registered or forwarded to deduplication / LLM summarisation.

# Minimum number of articles required for a cluster to be retained.
# Set to 2 to disable (HDBSCAN min_cluster_size already enforces this).
CLUSTER_MIN_ARTICLES: int = int(os.getenv("CLUSTER_MIN_ARTICLES", "2"))

# Minimum mean pairwise cosine similarity within a cluster.
# Clusters below this threshold are treated as noise.  Set to 0.0 to disable.
CLUSTER_MIN_INTRA_SIM: float = float(os.getenv("CLUSTER_MIN_INTRA_SIM", "0.0"))

# ------------------------------------------------------------------
# Deduplication
# ------------------------------------------------------------------
# Cosine similarity threshold for considering two records as duplicates.
DEDUP_SIMILARITY_THRESHOLD: float = float(os.getenv("DEDUP_SIMILARITY_THRESHOLD", "0.85"))

# Maximum time difference (hours) between two records to be considered duplicates.
DEDUP_MAX_TIME_DIFF_HOURS: float = float(os.getenv("DEDUP_MAX_TIME_DIFF_HOURS", "96"))

# ------------------------------------------------------------------
# Stable event ID registry
# ------------------------------------------------------------------
# Cosine similarity threshold for matching a new cluster centroid to an
# existing event in the registry.  Higher = stricter matching → more new events.
EVENT_ID_MATCH_THRESHOLD: float = float(os.getenv("EVENT_ID_MATCH_THRESHOLD", "0.85"))
