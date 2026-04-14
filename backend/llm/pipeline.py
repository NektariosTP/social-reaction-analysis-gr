"""
backend/llm/pipeline.py

Full Phase 4 orchestrator: classify → geocode → summarize.

Reads event clusters from the Phase 3 ChromaDB vector store, runs the
three LLM/NLP enrichment steps over each cluster, and writes the results
back to the vector store metadata.

Usage:
    python -m backend.llm.pipeline

Environment variables required for LLM steps (set in .env):
    OPENAI_API_KEY   — or equivalent key for your chosen provider
"""

from __future__ import annotations

import argparse
import logging
import os
import time
from collections import defaultdict

from backend.nlp.vectorstore import get_all, update_metadatas
from backend.llm.classify import classify_event_embedding
from backend.llm.geocode import geocode_cluster, geocode_record
from backend.llm.summarize import summarize_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_llm_key() -> bool:
    """Return True if at least one LLM API key is configured, or a local Ollama model is set."""
    if os.getenv("LLM_MODEL", "").startswith("ollama/"):
        return True
    keys = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GROQ_API_KEY",
        "GEMINI_API_KEY",
        "COHERE_API_KEY",
        "AZURE_API_KEY",
    ]
    return any(os.getenv(k) for k in keys)


def _group_by_cluster(
    ids: list[str],
    documents: list[str],
    metadatas: list[dict],
) -> dict[int, list[tuple[str, str, dict]]]:
    """
    Group (id, document, metadata) triples by cluster_id.
    Returns {cluster_id: [(id, document, metadata), …]}.
    Cluster -1 contains noise / unclustered records.
    """
    groups: dict[int, list[tuple[str, str, dict]]] = defaultdict(list)
    for rec_id, doc, meta in zip(ids, documents, metadatas):
        cid = meta.get("cluster_id", -1)
        groups[cid].append((rec_id, doc, meta))
    return groups


# ---------------------------------------------------------------------------
# Sub-steps
# ---------------------------------------------------------------------------

def _run_embedding_classification(
    groups: dict[int, list[tuple[str, str, dict]]],
) -> dict[int, tuple[str, str]]:
    """
    Run zero-shot embedding classification for every cluster (no LLM calls).

    Returns
    -------
    dict[int, tuple[str, str]]
        Mapping of cluster_id → (category, confidence).
        confidence is "high" | "medium" | "low".
    """
    cid_to_embed: dict[int, tuple[str, str]] = {}
    for cid, members in groups.items():
        if cid == -1:
            continue
        titles = [meta.get("title", "") for _, _, meta in members if meta.get("title")]
        result = classify_event_embedding(titles)
        if result:
            cid_to_embed[cid] = (result.category, result.confidence)
            logger.debug(
                "[classify] Cluster %s → %s [%s, embedding]",
                cid, result.category, result.confidence,
            )
        else:
            cid_to_embed[cid] = ("Unknown", "low")
    logger.info(
        "[classify] Embedding classification done for %d clusters.", len(cid_to_embed)
    )
    return cid_to_embed


def _run_enrich_clusters(
    groups: dict[int, list[tuple[str, str, dict]]],
    cid_to_embed: dict[int, tuple[str, str]],
) -> tuple[dict[str, str], dict[int, dict]]:
    """
    Combined LLM classification + summarization with hybrid prompt selection.

    For clusters where embedding confidence is "high", the economic LLM
    prompt is used (no category classification requested — fewer tokens).
    For medium / low confidence clusters, the full prompt is used and the
    LLM provides both the category and the summary in one API call.

    Returns
    -------
    tuple[dict[str, str], dict[int, dict]]
        (id_to_category, cid_to_summary)
    """
    id_to_category: dict[str, str] = {}
    cid_to_summary: dict[int, dict] = {}

    for cid, members in groups.items():
        if cid == -1:
            continue

        # Only use canonical (non-duplicate) articles to feed the LLM.
        # Duplicate records are still members of the cluster and will receive
        # the same category / summary in the metadata write step — they just
        # don't contribute to the prompt to avoid redundant LLM token usage.
        canonical_members = [
            (rec_id, doc, meta)
            for rec_id, doc, meta in members
            if not meta.get("is_duplicate", False)
        ]
        # Fall back to all members if deduplication hasn't run yet.
        llm_members = canonical_members if canonical_members else members

        title_body_pairs = [
            (meta.get("title", ""), doc)
            for _, doc, meta in llm_members
            if meta.get("title")
        ]
        titles = [t for t, _ in title_body_pairs]
        bodies = [b for _, b in title_body_pairs]
        sources = {meta.get("source", "") for _, _, meta in members}
        embed_cat, embed_conf = cid_to_embed.get(cid, ("Unknown", "low"))

        if embed_conf == "high":
            # Economic path: embedding already nailed the category.
            # Ask LLM for summary only (shorter prompt, fewer tokens).
            category = embed_cat
            summary = summarize_event(titles, bodies=bodies, n_sources=len(sources), include_category=False)
            logger.info(
                "[pipeline] Cluster %s → %s [high-conf embed, economic prompt]",
                cid, category,
            )
        else:
            # Full path: embedding uncertain — let the LLM classify AND summarize
            # in a single call to minimise total API requests.
            summary = summarize_event(titles, bodies=bodies, n_sources=len(sources), include_category=True)
            category = (
                summary.category
                if summary and summary.category
                else embed_cat  # fall back to embedding category if LLM omits it
            )
            logger.info(
                "[pipeline] Cluster %s → %s [%s-conf embed, full prompt]",
                cid, category, embed_conf,
            )

        for rec_id, _, _ in members:
            id_to_category[rec_id] = category

        if summary:
            cid_to_summary[cid] = {
                "summary_el": summary.summary_el,
                "summary_en": summary.summary_en,
            }
        else:
            logger.warning("[pipeline] Cluster %s — summarization failed.", cid)
            cid_to_summary[cid] = {"summary_el": "", "summary_en": ""}

        time.sleep(2)  # stay within 30 RPM free-tier limit

    return id_to_category, cid_to_summary


def _run_geocoding(
    groups: dict[int, list[tuple[str, str, dict]]],
    ids: list[str],
    documents: list[str],
    metadatas: list[dict],
) -> dict[str, dict]:
    """
    Run geocoding once per cluster (not per article).

    For each cluster, the best canonical article (longest body among
    non-duplicates, or first member as fallback) is selected and passed to
    ``geocode_cluster``.  The resolved GeocodeResult is cached by cluster_id
    inside ``geocode.py``; subsequent calls to ``geocode_record`` in the
    metadata write step retrieve the cached result for every member article.

    Returns mapping {record_id: {lat, lon, location_name, location_country}}.
    """
    id_to_geo: dict[str, dict] = {}

    for cid, members in groups.items():
        if cid == -1:
            # Noise records get no geocoding result.
            for rec_id, _, _ in members:
                id_to_geo[rec_id] = {"lat": None, "lon": None, "location_name": "", "location_country": ""}
            continue

        # Pick the best canonical article: prefer non-duplicates, longest body.
        canonical = [
            (rec_id, doc, meta)
            for rec_id, doc, meta in members
            if not meta.get("is_duplicate", False)
        ] or members  # fall back to all if deduplication hasn't run yet

        best_rec_id, best_doc, best_meta = max(canonical, key=lambda t: len(t[1]))
        title = best_meta.get("title", "")

        result = geocode_cluster(cid, title, best_doc)

        geo_dict = {
            "lat": result.lat,
            "lon": result.lon,
            "location_name": result.location_name,
            "location_country": result.location_country,
        }
        for rec_id, _, _ in members:
            id_to_geo[rec_id] = geo_dict

    resolved_clusters = sum(
        1 for cid, members in groups.items()
        if cid != -1 and any(id_to_geo.get(rec_id, {}).get("lat") for rec_id, _, _ in members)
    )
    total_clusters = sum(1 for k in groups if k != -1)
    logger.info("[geocode] Resolved %d / %d clusters.", resolved_clusters, total_clusters)
    return id_to_geo


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def run_pipeline(cluster_ids: set[int] | None = None) -> None:
    """
    Execute the complete Phase 4 pipeline:
      1. Load all records from ChromaDB (populated by Phase 3)
      2. Embedding classification for all clusters (zero tokens, always runs)
         — skipped when cluster_ids is provided
      3. Geocode each record → lat, lon, location_name, location_country
         — skipped when cluster_ids is provided
      4. LLM enrichment (summarize + re-classify uncertain clusters)
         — filtered to cluster_ids when provided
      5. Write enriched metadata back to ChromaDB

    Parameters
    ----------
    cluster_ids : set[int] | None
        When provided, only the LLM enrichment step is (re-)run and only for
        the listed cluster IDs.  Embedding classification, geocoding, and all
        other metadata for the remaining clusters are left unchanged.
    """
    logger.info("=" * 60)
    logger.info("Phase 4 — LLM Processing Pipeline")
    logger.info("=" * 60)

    # --- Load Phase 3 output --------------------------------------------------
    data = get_all(include=["metadatas", "documents"])
    ids: list[str] = data["ids"]
    documents: list[str] = data["documents"]
    metadatas: list[dict] = data["metadatas"]

    if not ids:
        logger.warning("[pipeline] Vector store is empty — run Phase 3 first.")
        return

    logger.info("[pipeline] Loaded %d records from vector store.", len(ids))

    groups = _group_by_cluster(ids, documents, metadatas)
    n_clusters = sum(1 for k in groups if k != -1)
    n_noise = len(groups.get(-1, []))
    logger.info("[pipeline] %d clusters + %d noise records.", n_clusters, n_noise)

    targeted = cluster_ids is not None
    if targeted:
        logger.info(
            "[pipeline] Targeted re-run for clusters: %s — skipping embedding "
            "classification and geocoding.",
            sorted(cluster_ids),
        )

    # --- Step 1: Embedding classification (always runs — no LLM tokens) -------
    cid_to_embed: dict[int, tuple[str, str]] = {}
    id_to_category: dict[str, str] = {}

    if not targeted:
        logger.info("[pipeline] --- Embedding Classification (zero-shot) ---")
        cid_to_embed = _run_embedding_classification(groups)
        for cid, members in groups.items():
            if cid == -1:
                continue
            embed_cat, _ = cid_to_embed.get(cid, ("Unknown", "low"))
            for rec_id, _, _ in members:
                id_to_category[rec_id] = embed_cat

    # --- Step 2: Geocoding (cluster-level, one LLM call per cluster) ---------
    id_to_geo: dict[str, dict] = {}
    if not targeted:
        logger.info("[pipeline] --- Geocoding (LLM location extraction + Nominatim) ---")
        id_to_geo = _run_geocoding(groups, ids, documents, metadatas)

    # --- Step 3: LLM enrichment (summarization + optional re-classification) --
    cid_to_summary: dict[int, dict] = {}

    if _has_llm_key():
        logger.info("[pipeline] --- LLM Enrichment (summarize + classify uncertain) ---")
        enrich_groups = (
            {cid: v for cid, v in groups.items() if cid in cluster_ids}
            if targeted
            else groups
        )
        id_to_category, cid_to_summary = _run_enrich_clusters(enrich_groups, cid_to_embed)
    else:
        logger.warning(
            "[pipeline] No LLM API key found — skipping summarization. "
            "Embedding classifications are still stored. "
            "Set OPENAI_API_KEY (or equivalent) in .env to enable summarization."
        )

    # --- Write enriched metadata back to ChromaDB -----------------------------
    logger.info("[pipeline] Writing enriched metadata back to vector store …")
    updated_metas: list[dict] = []

    for rec_id, meta in zip(ids, metadatas):
        meta_copy = dict(meta)
        cid = meta_copy.get("cluster_id", -1)

        if not targeted:
            # Full run: apply geocoding and classification to all records.
            geo = id_to_geo.get(rec_id, {})
            if geo.get("lat") is not None:
                meta_copy["lat"] = geo["lat"]
                meta_copy["lon"] = geo["lon"]
            if geo.get("location_name"):
                meta_copy["location_name"] = geo["location_name"]
            if geo.get("location_country"):
                meta_copy["location_country"] = geo["location_country"]
            if id_to_category:
                meta_copy["reaction_category"] = id_to_category.get(rec_id, "Unknown")

        # Summarization result — only update if this cluster was processed in
        # this run (cid_to_summary only contains processed clusters).
        summary = cid_to_summary.get(cid)
        if summary:
            meta_copy["summary_el"] = summary.get("summary_el", "")
            meta_copy["summary_en"] = summary.get("summary_en", "")

        updated_metas.append(meta_copy)

    update_metadatas(ids, updated_metas)
    logger.info("[pipeline] Metadata update complete.")

    logger.info("=" * 60)
    logger.info("Phase 4 pipeline complete.")
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 4 LLM pipeline: classify, geocode, and summarize event clusters."
    )
    parser.add_argument(
        "--clusters",
        metavar="IDS",
        type=str,
        default=None,
        help=(
            "Comma-separated cluster IDs to re-process with the LLM only "
            "(skips embedding classification and geocoding). "
            "Example: --clusters 22,75,91,113"
        ),
    )
    args = parser.parse_args()

    target_ids: set[int] | None = None
    if args.clusters:
        target_ids = {int(x.strip()) for x in args.clusters.split(",") if x.strip()}

    run_pipeline(cluster_ids=target_ids)
