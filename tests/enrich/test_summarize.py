"""Tests for bilingual event summarization (mocked LLM)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from enrich.summarize import SummaryResult, summarize_event


def test_summarize_event_returns_summary_result() -> None:
    mock_result = SummaryResult(
        summary_el="Εργαζόμενοι πραγματοποίησαν απεργία.",
        summary_en="Workers held a strike.",
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_result

    with patch("enrich.summarize.get_llm_client_and_model", return_value=(mock_client, "test-model")):
        result = summarize_event(
            article_titles=["48ωρη απεργία στα νοσοκομεία"],
            article_bodies=["Εργαζόμενοι κήρυξαν απεργία…"],
            n_sources=2,
        )

    assert isinstance(result, SummaryResult)
    assert result.summary_el == "Εργαζόμενοι πραγματοποίησαν απεργία."
    assert result.summary_en == "Workers held a strike."


def test_summarize_event_returns_none_on_llm_error() -> None:
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("LLM error")

    with patch("enrich.summarize.get_llm_client_and_model", return_value=(mock_client, "test")):
        result = summarize_event(
            article_titles=["test"],
            article_bodies=["body"],
            n_sources=1,
        )

    assert result is None
