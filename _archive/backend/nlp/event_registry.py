"""
backend/nlp/event_registry.py

Stable cross-run event UUID registry.

HDBSCAN assigns cluster labels arbitrarily on each pipeline run.  This
module maintains a persistent mapping of stable 8-hex-character event
identifiers to cluster centroids across runs, so that the same real-world
event retains the same ID whether it is observed today or next week.

Matching logic (per cluster, per run):
  1. Compute centroid = L2-normalised mean of member embeddings.
  2. Compare cosine similarity with all existing event centroids in the
     registry.  Because embeddings are L2-normalised, cosine similarity
     equals the dot product.
  3. If the most similar existing event passes EVENT_ID_MATCH_THRESHOLD →
     reuse its ID and update its metadata (last_seen, article_count, centroid).
  4. Otherwise → assign a new random 8-hex UUID.

After each run, events that were not observed are marked "closed".

Registry persisted to: data/vectordb/event_registry.json
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from backend.nlp.config import VECTORDB_DIR, EVENT_ID_MATCH_THRESHOLD

logger = logging.getLogger(__name__)

_REGISTRY_PATH: Path = VECTORDB_DIR / "event_registry.json"


class EventRegistry:
    """
    Manages stable cross-run event UUIDs for event clusters.

    Persistence: JSON file at ``data/vectordb/event_registry.json``.
    Thread safety: single-process only (no locking).
    """

    def __init__(self) -> None:
        self._events: dict[str, dict] = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load the event registry from the JSON file on disk."""
        if not _REGISTRY_PATH.exists():
            return
        try:
            self._events = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
            logger.debug("[event_registry] Loaded %d events from registry.", len(self._events))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("[event_registry] Failed to load registry (%s) — starting fresh.", exc)
            self._events = {}

    def save(self) -> None:
        """Persist the registry to the JSON file on disk."""
        try:
            _REGISTRY_PATH.write_text(
                json.dumps(self._events, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("[event_registry] Failed to save registry: %s", exc)

    # ------------------------------------------------------------------
    # Stable ID assignment
    # ------------------------------------------------------------------

    def assign(
        self,
        centroid: np.ndarray,
        article_count: int,
        representative_title: str = "",
    ) -> str:
        """
        Return a stable event ID for the given cluster centroid.

        If an existing event's centroid has cosine similarity ≥
        EVENT_ID_MATCH_THRESHOLD with the supplied centroid, that event's
        ID is reused and its metadata is updated.  Otherwise a new 8-hex
        UUID is created and registered.

        Parameters
        ----------
        centroid : np.ndarray
            L2-normalised centroid of the cluster (shape ``(dim,)``).
        article_count : int
            Number of articles in this cluster during the current run.
        representative_title : str
            Title of the most representative article (stored for readability).

        Returns
        -------
        str
            Stable 8-hex event identifier.
        """
        now: str = datetime.now(timezone.utc).isoformat()

        # Guard: if persisted centroids have a different dimension (e.g. after
        # switching embedding models) the dot product would raise a ValueError.
        # Detect this on the first call and wipe the stale registry so the new
        # run starts fresh with correct dimensions.
        for _eid, _event in self._events.items():
            stored_dim = len(_event.get("centroid", []))
            if stored_dim and stored_dim != len(centroid):
                logger.warning(
                    "[event_registry] Centroid dimension mismatch: stored=%d, incoming=%d. "
                    "Clearing stale registry to start fresh.",
                    stored_dim,
                    len(centroid),
                )
                self._events = {}
            break  # only need to check the first entry

        # Find the most similar existing event
        best_id: str | None = None
        best_sim: float = -1.0

        for eid, event in self._events.items():
            existing = np.array(event["centroid"], dtype=np.float32)
            # L2-normalised → cosine_sim = dot product
            sim = float(np.dot(centroid, existing))
            if sim > best_sim:
                best_sim = sim
                best_id = eid

        if best_id is not None and best_sim >= EVENT_ID_MATCH_THRESHOLD:
            # Re-use the existing event and update its state
            self._events[best_id].update(
                {
                    "centroid":     centroid.tolist(),
                    "last_seen":    now,
                    "article_count": article_count,
                    "status":       "ongoing",
                }
            )
            logger.debug(
                "[event_registry] Matched event %s (similarity=%.3f).", best_id, best_sim
            )
            return best_id

        # Register a new event
        new_id = uuid.uuid4().hex[:8]
        self._events[new_id] = {
            "centroid":            centroid.tolist(),
            "first_seen":          now,
            "last_seen":           now,
            "article_count":       article_count,
            "representative_title": representative_title[:200],
            "status":              "ongoing",
        }
        logger.debug("[event_registry] Registered new event %s.", new_id)
        return new_id

    # ------------------------------------------------------------------
    # Lifecycle management
    # ------------------------------------------------------------------

    def close_unseen(self, seen_event_ids: set[str]) -> int:
        """
        Mark events that were not observed in the current run as "closed".

        "Closed" events are retained in the registry for historical
        reference (and to avoid re-using their IDs), but they will not
        be matched against future clusters.

        Parameters
        ----------
        seen_event_ids : set[str]
            Event IDs that were active in the current clustering run.

        Returns
        -------
        int
            Number of events newly closed.
        """
        closed = 0
        for eid, event in self._events.items():
            if eid not in seen_event_ids and event.get("status") == "ongoing":
                event["status"] = "closed"
                closed += 1
        return closed

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._events)

    def ongoing_count(self) -> int:
        """Return the number of events currently marked as 'ongoing'."""
        return sum(1 for e in self._events.values() if e.get("status") == "ongoing")
