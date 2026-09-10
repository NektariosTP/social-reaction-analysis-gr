"""Enrich pipeline: single-call orchestration + approved-only selection."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from enrich.enrich_llm import EventEnrichment
from enrich.geocode import GeocodeResult, LocationMention


@pytest.mark.asyncio
async def test_enrich_event_writes_enriched_status(monkeypatch) -> None:
    from enrich import pipeline

    enr = EventEnrichment(
        action_forms=["Απεργία/Στάση εργασίας"], thematic_fields=["Εργασιακό"],
        channel="Φυσικό (offline)", intensity="Ειρηνική",
        summary_el="Απεργία.", summary_en="Strike.", event_date="2026-09-15",
        locations=[LocationMention(venue="Σύνταγμα", city="Αθήνα")], is_national=False,
    )
    monkeypatch.setattr(pipeline, "enrich_event_llm", lambda **kw: enr)

    async def fake_resolve(mentions, **kw):
        return [GeocodeResult(lat=37.97, lon=23.72, location_name="Σύνταγμα", city="Αθήνα")]

    monkeypatch.setattr(pipeline, "resolve_locations", fake_resolve)
    monkeypatch.setattr(pipeline, "detect_national_scope", lambda t: False)
    monkeypatch.setattr(pipeline, "_link_to_announcement", AsyncMock(return_value=None))

    session = MagicMock()
    session.execute = AsyncMock()
    # articles fetch → one article; then all UPDATE/INSERTs
    articles = MagicMock()
    articles.all.return_value = [("48ωρη απεργία", "σώμα", None)]
    session.execute.return_value = articles

    event = MagicMock()
    event.id = "11111111-1111-1111-1111-111111111111"
    event.centroid = "[0.1,0.2]"

    await pipeline._enrich_event(session, event)

    executed = " ".join(str(c.args[0]) for c in session.execute.call_args_list)
    assert "status = 'enriched'" in executed
    assert "classification_confidence" not in executed


@pytest.mark.asyncio
async def test_run_enrich_pipeline_selection_excludes_primary_location_null() -> None:
    """primary_location IS NULL is legitimate/permanent for venueless national events —
    it must not be part of the retry-selection, or such events get re-enriched forever."""
    from enrich import pipeline

    mock_session = AsyncMock()
    result = MagicMock()
    result.all.return_value = []
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.commit = AsyncMock()

    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    with patch("enrich.pipeline.async_sessionmaker", return_value=mock_session_factory):
        await pipeline.run_enrich_pipeline(engine=MagicMock())

    executed_sql = str(mock_session.execute.call_args_list[0][0][0])
    assert "primary_location IS NULL" not in executed_sql
    assert "summary_el IS NULL OR channel IS NULL" in executed_sql
