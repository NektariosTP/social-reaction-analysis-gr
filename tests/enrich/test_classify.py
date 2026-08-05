"""Tests for four-axis classification (mocked NLI pipeline + mocked LLM fallback)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from enrich.classify import (
    AXIS_ACTION_FORMS,
    AXIS_CHANNEL,
    AXIS_THEMATIC_FIELDS,
    ClassificationResult,
    classify_nli,
    classify_with_llm_fallback,
)


def _scores(labels: list[str], top: str, top_score: float, rest_score: float = 0.05) -> dict[str, float]:
    return {lbl: (top_score if lbl == top else rest_score) for lbl in labels}


def test_classify_nli_returns_classification_result() -> None:
    def fake_classify_axis(text, labels, *, multi_label, hypothesis_template):
        if labels == AXIS_ACTION_FORMS:
            return _scores(labels, "Απεργία/Στάση εργασίας", 0.91)
        if labels == AXIS_THEMATIC_FIELDS:
            return _scores(labels, "Εργασιακό", 0.88)
        if labels == AXIS_CHANNEL:
            return _scores(labels, "Φυσικό (offline)", 0.95)
        return _scores(labels, "Ειρηνική", 0.93)  # AXIS_INTENSITY

    with patch("enrich.classify.classify_axis", side_effect=fake_classify_axis):
        result = classify_nli("Οι εργαζόμενοι κήρυξαν απεργία στο κέντρο της Αθήνας.")

    assert isinstance(result, ClassificationResult)
    assert result.action_forms == ["Απεργία/Στάση εργασίας"]
    assert result.channel == "Φυσικό (offline)"
    assert result.intensity == "Ειρηνική"
    assert result.used_llm_fallback is False


def test_classify_with_llm_fallback_skips_llm_when_confident() -> None:
    confident = ClassificationResult(
        action_forms=["Απεργία/Στάση εργασίας"], thematic_fields=["Εργασιακό"],
        channel="Φυσικό (offline)", intensity="Ειρηνική",
        confidence={"action_forms": 0.9, "thematic_fields": 0.9, "channel": 0.9, "intensity": 0.9},
    )
    with (
        patch("enrich.classify.classify_nli", return_value=confident) as mock_nli,
        patch("enrich.llm_client.get_llm_client_and_model") as mock_llm,
    ):
        result = classify_with_llm_fallback(article_titles=["Τίτλος"], article_bodies=["Σώμα"])

    mock_nli.assert_called_once()
    mock_llm.assert_not_called()
    assert result.used_llm_fallback is False


def test_classify_with_llm_fallback_calls_llm_when_low_confidence() -> None:
    unsure = ClassificationResult(
        action_forms=["Κατάληψη"], thematic_fields=["Άλλο"],
        channel="Φυσικό (offline)", intensity="Ειρηνική",
        confidence={"action_forms": 0.2, "thematic_fields": 0.2, "channel": 0.9, "intensity": 0.9},
    )
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = MagicMock(
        action_forms=["Διαδήλωση/Πορεία/Συγκέντρωση"], thematic_fields=["Πολιτικό/Θεσμικό"],
        channel="Φυσικό (offline)", intensity="Ειρηνική",
    )
    with (
        patch("enrich.classify.classify_nli", return_value=unsure),
        patch("enrich.llm_client.get_llm_client_and_model", return_value=(fake_client, "groq/x")),
    ):
        result = classify_with_llm_fallback(article_titles=["Τίτλος"], article_bodies=["Σώμα"])

    assert result.used_llm_fallback is True
    assert result.action_forms == ["Διαδήλωση/Πορεία/Συγκέντρωση"]
