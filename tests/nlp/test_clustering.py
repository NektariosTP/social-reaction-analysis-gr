"""Tests for HDBSCAN clustering + quality gates (no DB — synthetic numpy vectors)."""
from __future__ import annotations

import numpy as np
from nlp.clustering import single_pass_cluster, find_merges

from nlp.clustering import (
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


def _unit(v: list[float]) -> np.ndarray:
    a = np.array(v, dtype=np.float32)
    return a / np.linalg.norm(a)


def test_single_pass_two_clusters_and_singleton() -> None:
    # two tight groups near orthogonal axes + one clearly separate vector
    vectors = np.stack([
        _unit([1.0, 0.02, 0.0]),
        _unit([1.0, 0.00, 0.0]),   # joins group A
        _unit([0.02, 1.0, 0.0]),
        _unit([0.00, 1.0, 0.0]),   # joins group B
        _unit([0.0, 0.0, 1.0]),    # singleton
    ])
    labels = single_pass_cluster(vectors, tau=0.9)
    assert labels[0] == labels[1]
    assert labels[2] == labels[3]
    assert labels[0] != labels[2]
    assert labels[4] not in (labels[0], labels[2])
    assert len(set(labels)) == 3


def test_find_merges_absorbs_near_duplicate_events() -> None:
    a = _unit([1.0, 0.0, 0.0])
    b = _unit([1.0, 0.01, 0.0])   # ~identical to a
    c = _unit([0.0, 1.0, 0.0])
    merges = find_merges([("A", a), ("B", b), ("C", c)], merge_threshold=0.95)
    assert merges == [("B", "A")]
