"""Tests for HDBSCAN clustering + quality gates (no DB — synthetic numpy vectors)."""
from __future__ import annotations

import numpy as np
import pytest

from nlp.clustering import (
    ClusterResult,
    apply_quality_gates,
    compute_intra_similarity,
    run_hdbscan,
)


def _make_tight_cluster(n: int = 5, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    base = rng.random(768).astype(np.float32)
    base /= np.linalg.norm(base)
    noise = rng.normal(0, 0.005, (n, 768)).astype(np.float32)
    vecs = base + noise
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / norms


def test_hdbscan_finds_two_well_separated_clusters() -> None:
    cluster_a = _make_tight_cluster(6, seed=0)
    cluster_b = _make_tight_cluster(6, seed=99)
    X = np.vstack([cluster_a, cluster_b])
    labels = run_hdbscan(X, min_cluster_size=3, min_samples=2)
    unique = set(labels) - {-1}
    assert len(unique) == 2


def test_compute_intra_similarity_high_for_tight_cluster() -> None:
    vecs = _make_tight_cluster(5)
    sim = compute_intra_similarity(vecs)
    assert sim > 0.95


def test_compute_intra_similarity_low_for_random() -> None:
    rng = np.random.default_rng(42)
    vecs = rng.standard_normal((5, 768)).astype(np.float32)
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    sim = compute_intra_similarity(vecs)
    assert sim < 0.3


def test_quality_gate_rejects_small_cluster() -> None:
    vecs = _make_tight_cluster(2)
    ids = ["a", "b"]
    results = apply_quality_gates(
        {0: (ids, vecs)}, min_articles=3, min_intra_sim=0.5
    )
    assert results == {}


def test_quality_gate_rejects_low_intra_sim() -> None:
    rng = np.random.default_rng(7)
    vecs = rng.random((5, 768)).astype(np.float32)
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    ids = [f"id{i}" for i in range(5)]
    results = apply_quality_gates(
        {0: (ids, vecs)}, min_articles=3, min_intra_sim=0.9
    )
    assert results == {}


def test_quality_gate_passes_tight_cluster() -> None:
    vecs = _make_tight_cluster(5)
    ids = [f"id{i}" for i in range(5)]
    results = apply_quality_gates(
        {0: (ids, vecs)}, min_articles=3, min_intra_sim=0.7
    )
    assert 0 in results
    assert results[0].centroid.shape == (768,)
