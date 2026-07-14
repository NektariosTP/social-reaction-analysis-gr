"""Tests for the worker cycle runner."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from worker.run import run_worker_cycle


def _patched_session_factory(mock_sf: MagicMock) -> None:
    mock_session = AsyncMock()
    mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_sf.return_value.__aexit__ = AsyncMock(return_value=None)


async def test_scrape_only_mode_skips_nlp_and_enrich() -> None:
    with (
        patch(
            "worker.run.run_ingestion", new_callable=AsyncMock, return_value={"inserted": 1}
        ) as mock_ing,
        patch("worker.run.run_nlp_pipeline", new_callable=AsyncMock) as mock_nlp,
        patch("worker.run.run_enrich_pipeline", new_callable=AsyncMock) as mock_enrich,
        patch(
            "worker.run.run_archival_sweep",
            new_callable=AsyncMock,
            return_value={"n_archived": 0, "n_pruned": 0, "n_closed": 0},
        ),
        patch("worker.run._make_session_factory") as mock_sf,
        patch("worker.run.settings") as mock_settings,
    ):
        mock_settings.pipeline_mode = "scrape_only"
        _patched_session_factory(mock_sf)

        metrics = await run_worker_cycle(engine=MagicMock())

    mock_ing.assert_awaited_once()
    mock_nlp.assert_not_called()
    mock_enrich.assert_not_called()
    assert metrics["ingestion"] == {"inserted": 1}


async def test_full_mode_runs_all_phases() -> None:
    with (
        patch("worker.run.run_ingestion", new_callable=AsyncMock, return_value={}) as mock_ing,
        patch("worker.run.run_nlp_pipeline", new_callable=AsyncMock, return_value={}) as mock_nlp,
        patch(
            "worker.run.run_enrich_pipeline", new_callable=AsyncMock, return_value={}
        ) as mock_enrich,
        patch("worker.run.run_archival_sweep", new_callable=AsyncMock, return_value={}),
        patch("worker.run._make_session_factory") as mock_sf,
        patch("worker.run.settings") as mock_settings,
    ):
        mock_settings.pipeline_mode = "full"
        _patched_session_factory(mock_sf)

        await run_worker_cycle(engine=MagicMock())

    mock_ing.assert_awaited_once()
    mock_nlp.assert_awaited_once()
    mock_enrich.assert_awaited_once()


async def test_ingestion_failure_does_not_block_nlp_or_archival() -> None:
    with (
        patch(
            "worker.run.run_ingestion", new_callable=AsyncMock, side_effect=RuntimeError("boom")
        ),
        patch(
            "worker.run.run_nlp_pipeline", new_callable=AsyncMock, return_value={}
        ) as mock_nlp,
        patch(
            "worker.run.run_archival_sweep",
            new_callable=AsyncMock,
            return_value={"n_archived": 0, "n_pruned": 0, "n_closed": 0},
        ) as mock_sweep,
        patch("worker.run._make_session_factory") as mock_sf,
        patch("worker.run.settings") as mock_settings,
    ):
        mock_settings.pipeline_mode = "scrape_and_nlp"
        _patched_session_factory(mock_sf)

        metrics = await run_worker_cycle(engine=MagicMock())

    mock_nlp.assert_awaited_once()
    mock_sweep.assert_awaited_once()
    assert "ingestion" not in metrics


async def test_archival_sweep_always_runs_even_in_scrape_only_mode() -> None:
    with (
        patch("worker.run.run_ingestion", new_callable=AsyncMock, return_value={}),
        patch(
            "worker.run.run_archival_sweep",
            new_callable=AsyncMock,
            return_value={"n_archived": 1, "n_pruned": 0, "n_closed": 0},
        ) as mock_sweep,
        patch("worker.run._make_session_factory") as mock_sf,
        patch("worker.run.settings") as mock_settings,
    ):
        mock_settings.pipeline_mode = "scrape_only"
        _patched_session_factory(mock_sf)

        metrics = await run_worker_cycle(engine=MagicMock())

    mock_sweep.assert_awaited_once()
    assert metrics["archival"] == {"n_archived": 1, "n_pruned": 0, "n_closed": 0}
