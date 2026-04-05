"""
backend/nlp/vectorstore.py

ChromaDB integration for storing and querying article embeddings.

Provides a thin wrapper around a persistent ChromaDB collection that stores
article records with their embeddings and metadata, and supports similarity
queries for deduplication and downstream retrieval.
"""

from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.config import Settings

from backend.nlp.config import VECTORDB_DIR, CHROMA_COLLECTION_NAME

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client / collection singletons
# ---------------------------------------------------------------------------

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None


def _get_client() -> chromadb.ClientAPI:
    """Return a persistent ChromaDB client (created once, reused)."""
    global _client
    if _client is None:
        logger.info("[vectorstore] Initialising ChromaDB at %s", VECTORDB_DIR)
        _client = chromadb.PersistentClient(
            path=str(VECTORDB_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_collection() -> chromadb.Collection:
    """Return (or create) the articles collection."""
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "[vectorstore] Collection '%s' ready (%d records).",
            CHROMA_COLLECTION_NAME,
            _collection.count(),
        )
    return _collection


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def upsert_records(
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict[str, Any]],
) -> None:
    """
    Upsert article records into the ChromaDB collection.

    Parameters
    ----------
    ids : list[str]
        Unique identifiers for each record (typically a hash of the URL).
    embeddings : list[list[float]]
        Pre-computed embedding vectors.
    documents : list[str]
        The text that was embedded (title + body).
    metadatas : list[dict]
        Record metadata (source, url, title, published_at, scraped_at, etc.).
    """
    collection = get_collection()

    # ChromaDB supports batch upsert up to ~41666 records at a time.
    batch_size = 5000
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.upsert(
            ids=ids[start:end],
            embeddings=embeddings[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )

    logger.info(
        "[vectorstore] Upserted %d records. Collection now has %d total.",
        len(ids),
        collection.count(),
    )


def get_all(include: list[str] | None = None) -> dict:
    """
    Retrieve all records from the collection.

    Parameters
    ----------
    include : list[str] | None
        Fields to include (default: embeddings + metadatas + documents).

    Returns
    -------
    dict
        ChromaDB get result with keys: ids, embeddings, metadatas, documents.
    """
    collection = get_collection()
    if include is None:
        include = ["embeddings", "metadatas", "documents"]
    return collection.get(include=include)


def update_metadatas(ids: list[str], metadatas: list[dict[str, Any]]) -> None:
    """
    Update metadata for existing records (e.g. to add cluster_id or is_duplicate).
    """
    collection = get_collection()
    batch_size = 5000
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.update(
            ids=ids[start:end],
            metadatas=metadatas[start:end],
        )

    logger.info("[vectorstore] Updated metadata for %d records.", len(ids))


def get_existing_ids(ids: list[str]) -> set[str]:
    """
    Return the subset of ``ids`` that already exist in the collection.

    Used by the pipeline to skip re-embedding records that are already stored.

    Parameters
    ----------
    ids : list[str]
        Candidate record IDs to check.

    Returns
    -------
    set[str]
        The IDs from ``ids`` that are already present in the collection.
    """
    if not ids:
        return set()
    collection = get_collection()
    result = collection.get(ids=ids, include=[])
    return set(result["ids"])


def collection_count() -> int:
    """Return the number of records in the collection."""
    return get_collection().count()


def reset_collection() -> None:
    """Delete and recreate the collection (destructive — use with caution)."""
    global _collection
    client = _get_client()
    try:
        client.delete_collection(CHROMA_COLLECTION_NAME)
    except Exception:
        pass
    _collection = None
    logger.info("[vectorstore] Collection '%s' reset.", CHROMA_COLLECTION_NAME)
