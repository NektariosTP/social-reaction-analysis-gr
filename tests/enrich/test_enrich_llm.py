"""Tests for the consolidated enrichment LLM call (mocked LLM)."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from enrich.axes import AXIS_ACTION_FORMS, AXIS_CHANNEL
from enrich.enrich_llm import EventEnrichment, enrich_event_llm, parse_event_date
from enrich.geocode import LocationMention

_ATHENS = ZoneInfo("Europe/Athens")


def test_enrich_event_llm_returns_model() -> None:
    mock_result = EventEnrichment(
        action_forms=[AXIS_ACTION_FORMS[1]],
        thematic_fields=["Εργασιακό"],
        channel=AXIS_CHANNEL[0],
        intensity="Ειρηνική",
        summary_el="Απεργία.",
        summary_en="Strike.",
        event_date="2026-09-15",
        locations=[LocationMention(venue="Πλατεία Συντάγματος", city="Αθήνα")],
        is_national=False,
    )
    client = MagicMock()
    client.chat.completions.create.return_value = mock_result
    with patch("enrich.enrich_llm.get_llm_client_and_model", return_value=(client, "m")):
        result = enrich_event_llm(
            article_titles=["48ωρη απεργία"], article_bodies=["σώμα"],
            n_sources=2, reference_date="2026-09-10",
        )
    assert isinstance(result, EventEnrichment)
    assert result.locations[0].city == "Αθήνα"
    assert result.event_date == "2026-09-15"


def test_enrich_event_llm_returns_none_on_error() -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("boom")
    with patch("enrich.enrich_llm.get_llm_client_and_model", return_value=(client, "m")):
        result = enrich_event_llm(
            article_titles=["x"], article_bodies=["y"], n_sources=1, reference_date=None,
        )
    assert result is None


def test_enrich_event_llm_drops_invalid_labels() -> None:
    mock_result = EventEnrichment(
        action_forms=["Απεργία/Στάση εργασίας", "NOT A LABEL"],
        thematic_fields=["Εργασιακό"],
        channel="bogus channel",
        intensity="Ειρηνική",
        summary_el="a", summary_en="b", event_date=None, locations=[], is_national=False,
    )
    client = MagicMock()
    client.chat.completions.create.return_value = mock_result
    with patch("enrich.enrich_llm.get_llm_client_and_model", return_value=(client, "m")):
        result = enrich_event_llm(
            article_titles=["x"], article_bodies=["y"], n_sources=1, reference_date=None,
        )
    assert result.action_forms == ["Απεργία/Στάση εργασίας"]  # invalid dropped
    assert result.channel in AXIS_CHANNEL  # coerced to a valid default


def test_parse_event_date_date_only_is_midnight_athens() -> None:
    assert parse_event_date("2026-09-15") == datetime(2026, 9, 15, 0, 0, tzinfo=_ATHENS)


def test_parse_event_date_none_returns_none() -> None:
    assert parse_event_date(None) is None
    assert parse_event_date("") is None
