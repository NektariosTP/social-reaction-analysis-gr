"""Tests for the enrichment pipeline orchestrator."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from enrich.classify import ClassificationResult
from enrich.pipeline import _enrich_event, run_enrich_pipeline
from enrich.nli import NOISE_GATE_THRESHOLD  # noqa: F401


def _fake_event(event_id: str = "evt-1") -> MagicMock:
    event = MagicMock()
    event.id = event_id
    event.centroid = None
    return event


async def test_enrich_event_sets_status_pending_review_not_enriched() -> None:
    session = AsyncMock()
    art_result = MagicMock()
    art_result.all.return_value = [("Τίτλος 1", "Σώμα 1", datetime(2026, 8, 9, 10, 0))]
    session.execute = AsyncMock(return_value=art_result)

    with (
        patch("enrich.pipeline.noise_gate_score", return_value=0.9),
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
            return_value=MagicMock(summary_el="Περίληψη", summary_en="Summary", event_date=None),
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


async def test_run_enrich_pipeline_uses_channel_is_null_for_needs_classify() -> None:
    """action_forms is TEXT[] NOT NULL DEFAULT '{}', so it's never NULL — using it
    as the needs_classify signal means classification never runs. channel has no
    default and is the reliable signal instead."""
    mock_session = AsyncMock()
    result = MagicMock()
    result.all.return_value = []
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.commit = AsyncMock()

    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    with patch("enrich.pipeline.async_sessionmaker", return_value=mock_session_factory):
        await run_enrich_pipeline(engine=MagicMock())

    executed_sql = str(mock_session.execute.call_args_list[0][0][0])
    assert "channel IS NULL AS needs_classify" in executed_sql
    assert "action_forms IS NULL" not in executed_sql


async def test_enrich_event_rejects_noise_before_classify() -> None:
    session = AsyncMock()
    art_result = MagicMock()
    art_result.all.return_value = [
        ("Εντείνονται τα επεισόδια σκόνης", "Σκόνη από τη Σαχάρα", datetime(2026, 8, 9, 10, 0))
    ]
    session.execute = AsyncMock(return_value=art_result)

    with (
        patch("enrich.pipeline.noise_gate_score", return_value=0.1),
        patch("enrich.pipeline.classify_with_llm_fallback") as mock_classify,
        patch("enrich.pipeline.geocode_event", new_callable=AsyncMock) as mock_geocode,
        patch("enrich.pipeline.summarize_event") as mock_summarize,
    ):
        await _enrich_event(
            session, _fake_event(), needs_classify=True, needs_geocode=True, needs_summary=True
        )

    mock_classify.assert_not_called()
    mock_geocode.assert_not_called()
    mock_summarize.assert_not_called()
    reject_call = session.execute.call_args_list[-1]
    assert "status = 'rejected'" in str(reject_call[0][0])


async def test_enrich_event_proceeds_when_not_noise() -> None:
    session = AsyncMock()
    art_result = MagicMock()
    art_result.all.return_value = [
        ("Απεργία στο Μετρό", "Οι εργαζόμενοι κήρυξαν απεργία", datetime(2026, 8, 9, 10, 0))
    ]
    session.execute = AsyncMock(return_value=art_result)

    with (
        patch("enrich.pipeline.noise_gate_score", return_value=0.9),
        patch(
            "enrich.pipeline.classify_with_llm_fallback",
            return_value=ClassificationResult(
                action_forms=["Απεργία/Στάση εργασίας"], thematic_fields=["Εργασιακό"],
                channel="Φυσικό (offline)", intensity="Ειρηνική",
                confidence={"action_forms": 0.9, "thematic_fields": 0.9, "channel": 0.9, "intensity": 0.9},
            ),
        ),
        patch("enrich.pipeline.geocode_event", new_callable=AsyncMock, return_value=[]),
        patch(
            "enrich.pipeline.summarize_event",
            return_value=MagicMock(summary_el="Π", summary_en="S", event_date=None),
        ),
    ):
        await _enrich_event(
            session, _fake_event(), needs_classify=True, needs_geocode=True, needs_summary=True
        )

    update_call = session.execute.call_args_list[-1]
    assert "status = 'pending_review'" in str(update_call[0][0])


async def test_enrich_event_passes_session_to_geocode() -> None:
    session = AsyncMock()
    art_result = MagicMock()
    art_result.all.return_value = [("Τίτλος 1", "Σώμα 1", datetime(2026, 8, 9, 10, 0))]
    session.execute = AsyncMock(return_value=art_result)

    geo_result = MagicMock(
        lat=37.9755,
        lon=23.7348,
        location_name="Σύνταγμα",
        is_primary=True,
        city="Αθήνα",
    )

    with (
        patch("enrich.pipeline.noise_gate_score", return_value=0.9),
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
        patch(
            "enrich.pipeline.geocode_event",
            new_callable=AsyncMock,
            return_value=[geo_result],
        ) as mock_geocode,
        patch(
            "enrich.pipeline.summarize_event",
            return_value=MagicMock(summary_el="Περίληψη", summary_en="Summary", event_date=None),
        ),
    ):
        await _enrich_event(
            session,
            _fake_event(),
            needs_classify=True,
            needs_geocode=True,
            needs_summary=True,
        )

    assert mock_geocode.call_args.kwargs["session"] is session
    update_call = [c for c in session.execute.call_args_list if "UPDATE events" in str(c.args[0])][0]
    assert update_call.args[1]["lat"] == 37.9755
    insert_call = [
        c for c in session.execute.call_args_list if "INSERT INTO event_locations" in str(c.args[0])
    ][0]
    assert insert_call.args[1]["location_name"] == "Σύνταγμα"


async def test_enrich_event_persists_event_time_from_summary() -> None:
    session = AsyncMock()
    art_result = MagicMock()
    art_result.all.return_value = [
        ("Απεργία στο Μετρό", "Οι εργαζόμενοι κήρυξαν απεργία", datetime(2026, 8, 9, 10, 0))
    ]
    session.execute = AsyncMock(return_value=art_result)

    with (
        patch("enrich.pipeline.noise_gate_score", return_value=0.9),
        patch(
            "enrich.pipeline.classify_with_llm_fallback",
            return_value=ClassificationResult(
                action_forms=["Απεργία/Στάση εργασίας"], thematic_fields=["Εργασιακό"],
                channel="Φυσικό (offline)", intensity="Ειρηνική",
                confidence={"action_forms": 0.9, "thematic_fields": 0.9, "channel": 0.9, "intensity": 0.9},
            ),
        ),
        patch("enrich.pipeline.geocode_event", new_callable=AsyncMock, return_value=[]),
        patch(
            "enrich.pipeline.summarize_event",
            return_value=MagicMock(summary_el="Π", summary_en="S", event_date="2026-09-15"),
        ),
    ):
        await _enrich_event(
            session, _fake_event(), needs_classify=True, needs_geocode=True, needs_summary=True
        )

    update_call = [c for c in session.execute.call_args_list if "UPDATE events" in str(c.args[0])][0]
    assert "event_time = :event_time" in str(update_call.args[0])
    et = update_call.args[1]["event_time"]
    assert et is not None and et.date() == datetime(2026, 9, 15).date()


async def test_enrich_event_event_time_none_when_summary_undated() -> None:
    session = AsyncMock()
    art_result = MagicMock()
    art_result.all.return_value = [
        ("Απεργία στο Μετρό", "Οι εργαζόμενοι κήρυξαν απεργία", datetime(2026, 8, 9, 10, 0))
    ]
    session.execute = AsyncMock(return_value=art_result)

    with (
        patch("enrich.pipeline.noise_gate_score", return_value=0.9),
        patch(
            "enrich.pipeline.classify_with_llm_fallback",
            return_value=ClassificationResult(
                action_forms=["Απεργία/Στάση εργασίας"], thematic_fields=["Εργασιακό"],
                channel="Φυσικό (offline)", intensity="Ειρηνική",
                confidence={"action_forms": 0.9, "thematic_fields": 0.9, "channel": 0.9, "intensity": 0.9},
            ),
        ),
        patch("enrich.pipeline.geocode_event", new_callable=AsyncMock, return_value=[]),
        patch(
            "enrich.pipeline.summarize_event",
            return_value=MagicMock(summary_el="Π", summary_en="S", event_date=None),
        ),
    ):
        await _enrich_event(
            session, _fake_event(), needs_classify=True, needs_geocode=True, needs_summary=True
        )

    update_call = [c for c in session.execute.call_args_list if "UPDATE events" in str(c.args[0])][0]
    assert update_call.args[1]["event_time"] is None


async def test_enrich_event_national_venueless_persists_is_national_true_and_null_location() -> None:
    session = AsyncMock()
    art_result = MagicMock()
    art_result.all.return_value = [
        ("Πανελλαδική απεργία στο εμπόριο", "24ωρη απεργία σε όλη τη χώρα", datetime(2026, 8, 9, 10, 0))
    ]
    session.execute = AsyncMock(return_value=art_result)

    with (
        patch("enrich.pipeline.noise_gate_score", return_value=0.9),
        patch(
            "enrich.pipeline.classify_with_llm_fallback",
            return_value=ClassificationResult(
                action_forms=["Απεργία/Στάση εργασίας"], thematic_fields=["Εργασιακό"],
                channel="Φυσικό (offline)", intensity="Ειρηνική",
                confidence={"action_forms": 0.9, "thematic_fields": 0.9, "channel": 0.9, "intensity": 0.9},
            ),
        ),
        patch("enrich.pipeline.geocode_event", new_callable=AsyncMock, return_value=[]),
        patch(
            "enrich.pipeline.summarize_event",
            return_value=MagicMock(summary_el="Π", summary_en="S", event_date=None),
        ),
    ):
        await _enrich_event(
            session, _fake_event(), needs_classify=True, needs_geocode=True, needs_summary=True
        )

    update_call = [c for c in session.execute.call_args_list if "UPDATE events" in str(c.args[0])][0]
    assert "is_national = :is_national" in str(update_call.args[0])
    assert update_call.args[1]["is_national"] is True
    assert update_call.args[1]["lat"] is None  # primary_location stays NULL


async def test_enrich_event_local_located_persists_is_national_false() -> None:
    session = AsyncMock()
    art_result = MagicMock()
    art_result.all.return_value = [
        ("Κατάληψη στο δημαρχείο Ηρακλείου", "Συγκέντρωση στην πλατεία", datetime(2026, 8, 9, 10, 0))
    ]
    session.execute = AsyncMock(return_value=art_result)

    geo_result = MagicMock(
        lat=35.34, lon=25.13, location_name="Ηράκλειο", is_primary=True, city="Ηράκλειο",
    )

    with (
        patch("enrich.pipeline.noise_gate_score", return_value=0.9),
        patch(
            "enrich.pipeline.classify_with_llm_fallback",
            return_value=ClassificationResult(
                action_forms=["Κατάληψη"], thematic_fields=["Πολιτικό/Θεσμικό"],
                channel="Φυσικό (offline)", intensity="Ειρηνική",
                confidence={"action_forms": 0.9, "thematic_fields": 0.9, "channel": 0.9, "intensity": 0.9},
            ),
        ),
        patch("enrich.pipeline.geocode_event", new_callable=AsyncMock, return_value=[geo_result]),
        patch(
            "enrich.pipeline.summarize_event",
            return_value=MagicMock(summary_el="Π", summary_en="S", event_date=None),
        ),
    ):
        await _enrich_event(
            session, _fake_event(), needs_classify=True, needs_geocode=True, needs_summary=True
        )

    update_call = [c for c in session.execute.call_args_list if "UPDATE events" in str(c.args[0])][0]
    assert update_call.args[1]["is_national"] is False
    assert update_call.args[1]["lat"] == 35.34
