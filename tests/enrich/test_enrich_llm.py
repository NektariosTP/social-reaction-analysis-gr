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


def test_enrich_event_llm_returns_none_on_empty_summary() -> None:
    mock_result = EventEnrichment(
        action_forms=[AXIS_ACTION_FORMS[1]], thematic_fields=["Εργασιακό"],
        channel=AXIS_CHANNEL[0], intensity="Ειρηνική",
        summary_el="", summary_en="Strike.", event_date=None, locations=[], is_national=False,
    )
    client = MagicMock()
    client.chat.completions.create.return_value = mock_result
    with patch("enrich.enrich_llm.get_llm_client_and_model", return_value=(client, "m")):
        result = enrich_event_llm(
            article_titles=["x"], article_bodies=["y"], n_sources=1, reference_date=None,
        )
    assert result is None


def test_parse_event_date_date_only_defaults_to_noon_athens() -> None:
    # A date with no time means "that day" — anchor it at 12:00 noon, never midnight.
    assert parse_event_date("2026-09-15") == datetime(2026, 9, 15, 12, 0, tzinfo=_ATHENS)


def test_parse_event_date_preserves_explicit_time() -> None:
    assert parse_event_date("2026-09-15T18:30:00") == datetime(
        2026, 9, 15, 18, 30, tzinfo=_ATHENS
    )


def test_parse_event_date_falls_back_to_reference_date_at_noon() -> None:
    # LLM extracted no date → use the reference date (first article/reaction),
    # at noon Athens, rather than leaving event_time NULL.
    got = parse_event_date(None, "2026-09-28T12:54:00+00:00")
    assert got == datetime(2026, 9, 28, 12, 0, tzinfo=_ATHENS)


def test_parse_event_date_unparseable_falls_back_to_reference() -> None:
    assert parse_event_date("not a date", "2026-09-10") == datetime(
        2026, 9, 10, 12, 0, tzinfo=_ATHENS
    )


def test_parse_event_date_none_without_reference_returns_none() -> None:
    # Only truly anchorless input yields None (no articles, no reaction dates).
    assert parse_event_date(None) is None
    assert parse_event_date("") is None
    assert parse_event_date(None, None) is None
