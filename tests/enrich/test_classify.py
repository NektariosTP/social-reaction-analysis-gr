"""Tests for four-axis classification (mocked model + mocked LLM)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from enrich.classify import (
    AXIS_ACTION_FORMS,
    AXIS_CHANNEL,
    AXIS_INTENSITY,
    AXIS_THEMATIC_FIELDS,
    ClassificationResult,
    classify_zero_shot,
    _cosine_sim,
)


def _unit_vec(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.random(768).astype(np.float32)
    return v / np.linalg.norm(v)


def test_cosine_sim_identical_vectors() -> None:
    v = _unit_vec(0)
    assert abs(_cosine_sim(v, v) - 1.0) < 1e-5


def test_cosine_sim_orthogonal_vectors() -> None:
    v1 = np.zeros(768, dtype=np.float32)
    v2 = np.zeros(768, dtype=np.float32)
    v1[0] = 1.0
    v2[1] = 1.0
    assert abs(_cosine_sim(v1, v2)) < 1e-5


def test_classify_zero_shot_returns_classification_result() -> None:
    centroid = _unit_vec(42)
    all_labels = AXIS_ACTION_FORMS + AXIS_THEMATIC_FIELDS + AXIS_CHANNEL + AXIS_INTENSITY
    fake_embeddings = {label: _unit_vec(i) for i, label in enumerate(all_labels)}

    with patch("enrich.classify._get_axis_embeddings", return_value=fake_embeddings):
        result = classify_zero_shot(centroid=centroid)

    assert isinstance(result, ClassificationResult)
    assert isinstance(result.action_forms, list)
    assert isinstance(result.thematic_fields, list)
    assert result.channel in {"Φυσικό (offline)", "Ψηφιακό (online)", "Υβριδικό"}
    assert result.intensity in {"Ειρηνική", "Διαταρακτική (μη βίαιη, παρεμποδιστική)", "Βίαιη/Συγκρουσιακή"}


def test_classification_result_is_pydantic_model() -> None:
    result = ClassificationResult(
        action_forms=["Απεργία/Στάση εργασίας"],
        thematic_fields=["Εργασιακό"],
        channel="Φυσικό (offline)",
        intensity="Ειρηνική",
        confidence={"action_forms": 0.9, "channel": 0.85},
        used_llm_fallback=False,
    )
    assert result.used_llm_fallback is False
