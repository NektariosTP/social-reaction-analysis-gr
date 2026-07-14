"""Tests for the enrichment pipeline orchestrator."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from enrich.classify import ClassificationResult
from enrich.pipeline import _enrich_event


def _fake_event(event_id: str = "evt-1") -> MagicMock:
    event = MagicMock()
    event.id = event_id
    event.centroid = None
    return event


async def test_enrich_event_sets_status_pending_review_not_enriched() -> None:
    session = AsyncMock()
    art_result = MagicMock()
    art_result.all.return_value = [("Τίτλος 1", "Σώμα 1")]
    session.execute = AsyncMock(return_value=art_result)

    with (
        patch(
            "enrich.pipeline.classify_with_llm_fallback",
            return_value=ClassificationResult(
                action_forms=["Απεργία/Στάση εργασίας"],
                thematic_fields=["Εργασιακό"],
                channel="Φυσικό (offline)",
                intensity="Ειρηνική",
                confidence={
                    "action_forms": 0.9,
                    "thematic_fields": 0.9,
                    "channel": 0.9,
                    "intensity": 0.9,
                },
            ),
        ),
        patch("enrich.pipeline.geocode_event", new_callable=AsyncMock, return_value=[]),
        patch(
            "enrich.pipeline.summarize_event",
            return_value=MagicMock(summary_el="Περίληψη", summary_en="Summary"),
        ),
    ):
        await _enrich_event(
            session,
            _fake_event(),
            needs_classify=True,
            needs_geocode=True,
            needs_summary=True,
        )

    update_call = session.execute.call_args_list[-1]
    executed_sql = str(update_call[0][0])
    assert "status = 'pending_review'" in executed_sql
    assert "status = 'enriched'" not in executed_sql
