"""Tests for stable event_id assignment via centroid cosine matching."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, call, patch

import numpy as np
import pytest

from nlp.event_registry import assign_event_id, match_existing_event


def _centroid(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.random(768).astype(np.float32)
    return v / np.linalg.norm(v)


def test_match_returns_none_for_empty_registry() -> None:
    centroid = _centroid(0)
    result = match_existing_event(centroid, existing_events=[], threshold=0.85)
    assert result is None


def test_match_returns_existing_event_above_threshold() -> None:
    centroid = _centroid(0)
    noise = np.random.default_rng(1).normal(0, 0.01, 768).astype(np.float32)
    near_centroid = centroid + noise
    near_centroid /= np.linalg.norm(near_centroid)

    existing_id = str(uuid.uuid4())
    existing = [(existing_id, near_centroid)]
    result = match_existing_event(centroid, existing_events=existing, threshold=0.85)
    assert result == existing_id


def test_match_returns_none_below_threshold() -> None:
    c1 = _centroid(0)
    c2 = _centroid(99)
    existing_id = str(uuid.uuid4())
    result = match_existing_event(c1, existing_events=[(existing_id, c2)], threshold=0.85)
    assert result is None


def test_match_returns_best_match() -> None:
    centroid = _centroid(0)
    rng = np.random.default_rng(42)

    close = centroid + rng.normal(0, 0.005, 768).astype(np.float32)
    close /= np.linalg.norm(close)
    distant = centroid + rng.normal(0, 0.1, 768).astype(np.float32)
    distant /= np.linalg.norm(distant)

    id_close = "close-id"
    id_distant = "distant-id"
    result = match_existing_event(
        centroid,
        existing_events=[(id_distant, distant), (id_close, close)],
        threshold=0.85,
    )
    assert result == id_close
