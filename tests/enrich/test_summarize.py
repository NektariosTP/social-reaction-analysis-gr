"""Tests for bilingual event summarization (mocked LLM)."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from enrich.summarize import SummaryResult, parse_event_date, summarize_event

_ATHENS = ZoneInfo("Europe/Athens")

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


def test_parse_event_date_date_only_is_midnight_athens() -> None:
    dt = parse_event_date("2026-09-15")
    assert dt == datetime(2026, 9, 15, 0, 0, tzinfo=_ATHENS)


def test_parse_event_date_with_time_keeps_hour_athens() -> None:
    dt = parse_event_date("2026-09-15T18:30")
    assert dt == datetime(2026, 9, 15, 18, 30, tzinfo=_ATHENS)


def test_parse_event_date_none_and_empty_return_none() -> None:
    assert parse_event_date(None) is None
    assert parse_event_date("") is None


def test_parse_event_date_malformed_returns_none() -> None:
    assert parse_event_date("αύριο") is None
    assert parse_event_date("next Thursday") is None


def test_parse_event_date_preserves_explicit_offset() -> None:
    dt = parse_event_date("2026-09-15T18:00:00+03:00")
    assert dt.utcoffset().total_seconds() == 3 * 3600


def test_summary_result_carries_event_date() -> None:
    r = SummaryResult(summary_el="ε", summary_en="e", event_date="2026-09-15")
    assert r.event_date == "2026-09-15"


def test_summary_result_event_date_defaults_none() -> None:
    r = SummaryResult(summary_el="ε", summary_en="e")
    assert r.event_date is None


def test_summarize_event_puts_reference_date_in_prompt() -> None:
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = SummaryResult(
        summary_el="ε", summary_en="e", event_date="2026-09-15"
    )
    with patch(
        "enrich.summarize.get_llm_client_and_model",
        return_value=(mock_client, "test-model"),
    ):
        summarize_event(
            article_titles=["Απεργία αύριο"],
            article_bodies=["..."],
            n_sources=1,
            reference_date="2026-09-14",
        )
    sent_prompt = mock_client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert "2026-09-14" in sent_prompt
    assert "event_date" in sent_prompt
