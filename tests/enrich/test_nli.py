"""NLI zero-shot axis classification + noise gate (mocked transformers pipeline —
the real ~1.5 GB mDeBERTa model is never downloaded in tests)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from enrich.nli import _NOISE_GATE_LABELS, classify_axis, noise_gate_score


def test_classify_axis_returns_label_to_score_map() -> None:
    fake_pipeline = MagicMock(return_value={
        "sequence": "...",
        "labels": ["Απεργία/Στάση εργασίας", "Κατάληψη"],
        "scores": [0.82, 0.11],
    })
    with patch("enrich.nli._load_nli_pipeline", return_value=fake_pipeline):
        scores = classify_axis(
            "Οι εργαζόμενοι κήρυξαν απεργία.",
            ["Απεργία/Στάση εργασίας", "Κατάληψη"],
            multi_label=True,
            hypothesis_template="Αυτό το κείμενο περιγράφει τη μορφή δράσης: {}.",
        )
    assert scores["Απεργία/Στάση εργασίας"] == 0.82
    _, kwargs = fake_pipeline.call_args
    assert kwargs["multi_label"] is True


def test_noise_gate_score_high_for_real_event() -> None:
    fake_pipeline = MagicMock(return_value={
        "sequence": "...",
        "labels": [_NOISE_GATE_LABELS[0], _NOISE_GATE_LABELS[1]],
        "scores": [0.93, 0.07],
    })
    with patch("enrich.nli._load_nli_pipeline", return_value=fake_pipeline):
        score = noise_gate_score("Χιλιάδες διαδηλωτές στο Σύνταγμα κατά του νομοσχεδίου.")
    assert score == 0.93


def test_noise_gate_score_low_for_off_topic_text() -> None:
    fake_pipeline = MagicMock(return_value={
        "sequence": "...",
        "labels": [_NOISE_GATE_LABELS[1], _NOISE_GATE_LABELS[0]],
        "scores": [0.88, 0.12],
    })
    with patch("enrich.nli._load_nli_pipeline", return_value=fake_pipeline):
        score = noise_gate_score("Η σκόνη από τη Σαχάρα εντείνεται στην Ευρώπη.")
    assert score == 0.12
