from unittest.mock import AsyncMock, patch

import pytest

from worker.run import run_worker_cycle


@pytest.mark.asyncio
async def test_reactions_phase_runs_in_full_mode():
    with patch("worker.run.settings") as s, \
         patch("worker.run.run_ingestion", new=AsyncMock(return_value={})), \
         patch("worker.run.run_nlp_pipeline", new=AsyncMock(return_value={})), \
         patch("worker.run.run_enrich_pipeline", new=AsyncMock(return_value={})), \
         patch("worker.run.run_archival_sweep", new=AsyncMock(return_value={})), \
         patch("worker.run.run_reactions_pipeline", new=AsyncMock(return_value={"seeded": 1})) as react:
        s.pipeline_mode = "full"
        metrics = await run_worker_cycle(engine=AsyncMock())
    react.assert_awaited_once()
    assert metrics["reactions"] == {"seeded": 1}


@pytest.mark.asyncio
async def test_reactions_phase_skipped_in_scrape_only():
    with patch("worker.run.settings") as s, \
         patch("worker.run.run_ingestion", new=AsyncMock(return_value={})), \
         patch("worker.run.run_archival_sweep", new=AsyncMock(return_value={})), \
         patch("worker.run.run_reactions_pipeline", new=AsyncMock()) as react:
        s.pipeline_mode = "scrape_only"
        await run_worker_cycle(engine=AsyncMock())
    react.assert_not_awaited()
