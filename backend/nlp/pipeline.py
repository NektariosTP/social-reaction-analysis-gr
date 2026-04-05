"""
backend/nlp/pipeline.py

Full Phase 3 orchestrator: ingest → embed → store → cluster → deduplicate.

Usage:
    python -m backend.nlp.pipeline
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from backend.nlp.config import RAW_DATA_DIR
from backend.nlp.embeddings import embed_texts
from backend.nlp.vectorstore import upsert_records, collection_count, get_existing_ids
from backend.nlp.clustering import cluster_articles
from backend.nlp.deduplication import deduplicate_clusters

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data ingestion
# ---------------------------------------------------------------------------

def _record_id(record: dict) -> str:
    """Deterministic ID for a record based on its URL (SHA-256 hex digest)."""
    url = record.get("url", "")
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]


def _load_raw_records(data_dir: Path | None = None) -> list[dict]:
    """
    Read all .ndjson files from data/raw/ and return a flat list of records.
    Skips records with empty title *and* empty body.
    """
    data_dir = data_dir or RAW_DATA_DIR
    records: list[dict] = []
    seen_urls: set[str] = set()

    for ndjson_path in sorted(data_dir.rglob("*.ndjson")):
        with ndjson_path.open("r", encoding="utf-8") as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    logger.warning(
                        "Skipping malformed JSON in %s line %d: %s",
                        ndjson_path, line_num, exc,
                    )
                    continue

                url = record.get("url", "")
                title = record.get("title", "")
                body = record.get("body", "")

                # Skip empty records and duplicates within the raw files
                if not title and not body:
                    continue
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                records.append(record)

    logger.info("[pipeline] Loaded %d unique records from %s", len(records), data_dir)
    return records


# ---------------------------------------------------------------------------
# Embedding + ingestion into vector store
# ---------------------------------------------------------------------------

def _ingest_records(records: list[dict]) -> None:
    """Embed records and upsert them into the ChromaDB vector store."""
    if not records:
        logger.info("[pipeline] No records to ingest.")
        return

    # Prepare texts for embedding: title + body
    texts: list[str] = []
    ids: list[str] = []
    metadatas: list[dict] = []

    for record in records:
        title = record.get("title", "")
        body = record.get("body", "")
        text = f"{title} {body}".strip()
        if not text:
            continue

        rec_id = _record_id(record)
        ids.append(rec_id)
        texts.append(text)

        # Metadata stored alongside embedding (ChromaDB requires flat str/int/float/bool values)
        meta = {
            "source": record.get("source", ""),
            "url": record.get("url", ""),
            "title": title[:500],  # truncate for metadata storage
            "published_at": record.get("published_at") or "",
            "scraped_at": record.get("scraped_at") or "",
            "lang": record.get("lang", "el"),
            "category_hint": record.get("category_hint") or "",
        }

        # GDELT events carry extra geospatial fields
        if record.get("lat") is not None:
            meta["lat"] = float(record["lat"])
        if record.get("lon") is not None:
            meta["lon"] = float(record["lon"])
        if record.get("location_name"):
            meta["location_name"] = record["location_name"]
        if record.get("cameo_code"):
            meta["cameo_code"] = record["cameo_code"]

        metadatas.append(meta)

    # Incremental embedding: only embed records not already in the store
    already_in_store = get_existing_ids(ids)
    new_indices = [i for i, rid in enumerate(ids) if rid not in already_in_store]

    if not new_indices:
        logger.info(
            "[pipeline] All %d records already in store — skipping embedding.",
            len(ids),
        )
        return

    new_ids = [ids[i] for i in new_indices]
    new_texts = [texts[i] for i in new_indices]
    new_metas = [metadatas[i] for i in new_indices]

    logger.info(
        "[pipeline] Embedding %d new records (%d already in store — skipped).",
        len(new_ids),
        len(already_in_store),
    )
    embeddings = embed_texts(new_texts)

    logger.info("[pipeline] Upserting %d new records into vector store…", len(new_ids))
    upsert_records(new_ids, embeddings, new_texts, new_metas)


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def run_pipeline(data_dir: Path | None = None) -> None:
    """
    Execute the complete Phase 3 pipeline:
      1. Load raw .ndjson records
      2. Generate embeddings
      3. Store in ChromaDB
      4. Cluster articles into events (HDBSCAN)
      5. Deduplicate within clusters
    """
    logger.info("=" * 60)
    logger.info("Phase 3 — NLP & Semantic Analysis Pipeline")
    logger.info("=" * 60)

    # Step 1+2+3: Ingest
    records = _load_raw_records(data_dir)
    _ingest_records(records)
    logger.info("[pipeline] Vector store contains %d records.", collection_count())

    # Step 4: Cluster
    logger.info("[pipeline] --- Clustering ---")
    id_to_cluster = cluster_articles()
    n_clusters = len(set(id_to_cluster.values()) - {-1})
    logger.info("[pipeline] %d clusters formed.", n_clusters)

    # Step 5: Deduplicate
    logger.info("[pipeline] --- Deduplication ---")
    canonical_map = deduplicate_clusters()
    n_dupes = sum(1 for v in canonical_map.values() if v is not None)
    logger.info("[pipeline] %d duplicates identified.", n_dupes)

    logger.info("=" * 60)
    logger.info("Phase 3 pipeline complete.")
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_pipeline()
