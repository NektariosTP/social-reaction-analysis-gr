"""Robustness: salvage Groq's malformed tool-call output into LocationMentions."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from enrich import geocode
from enrich.geocode import parse_locations_json

# The exact shape Groq returned in the A1 eval run (tool_use_failed):
WRAPPED = (
    '<function=_LlmLocations>{"locations": ['
    '{"city": "Athens", "region": "Attica", "venue": "Kifisias and Alexandras avenues intersection"}, '
    '{"city": "Athens", "region": "Attica", "venue": null}]}<function/_LlmLocations>'
)


def test_parse_salvages_wrapped_tool_call() -> None:
    ms = parse_locations_json(WRAPPED)
    assert len(ms) == 2
    assert ms[0].city == "Athens"
    assert ms[0].venue and "Kifisias" in ms[0].venue
    assert ms[1].venue is None


def test_parse_handles_json_fence() -> None:
    raw = '```json\n{"locations": [{"city": "Αθήνα"}]}\n```'
    ms = parse_locations_json(raw)
    assert len(ms) == 1 and ms[0].city == "Αθήνα"


def test_parse_garbage_returns_empty() -> None:
    assert parse_locations_json("no json here") == []
    assert parse_locations_json("") == []


def test_extract_locations_llm_recovers_from_failed_generation() -> None:
    failed_gen = (
        '<function=_LlmLocations>{"locations": [{"city": "Αθήνα"}]}<function/_LlmLocations>'
    )
    body = {"error": {"code": "tool_use_failed", "failed_generation": failed_gen}}
    err = Exception("litellm.BadRequestError: GroqException - " + json.dumps(body, ensure_ascii=False))

    client = MagicMock()
    client.chat.completions.create.side_effect = err
    with patch("enrich.llm_client.get_llm_client_and_model", return_value=(client, "groq/x")):
        mentions = geocode._extract_locations_llm("Συγκέντρωση στην Αθήνα")

    assert len(mentions) == 1 and mentions[0].city == "Αθήνα"
