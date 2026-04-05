"""
scrapers/scheduler.py

Automated pipeline scheduler for local use.

Runs the configured pipeline chain immediately on start, then repeats
at SCRAPE_INTERVAL_SECONDS intervals.  No additional dependencies — uses
only stdlib asyncio.

Usage:
    python -m scrapers.scheduler

Environment variables (all optional; set in .env or shell):
    SCRAPE_INTERVAL_SECONDS   How often to run the pipeline (default: 3600).
    PIPELINE_MODE             What to execute each cycle:
                                scrape_only     (default) — scrapers only
                                scrape_and_nlp  — scrape → Phase 3 NLP pipeline
                                full            — scrape → NLP → Phase 4 LLM pipeline
                                                  (requires a free Groq / Gemini API key)

Any unhandled exception in a pipeline step is logged and the remainder of
that cycle is skipped; the scheduler then waits for the next interval and
retries automatically.
"""

from __future__ import annotations

import asyncio
import logging
import os

from scrapers.config import SCRAPE_INTERVAL_SECONDS
from scrapers.run_all import main as _scrape

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_PIPELINE_MODE: str = os.getenv("PIPELINE_MODE", "scrape_only").strip().lower()

_VALID_MODES = {"scrape_only", "scrape_and_nlp", "full"}
if _PIPELINE_MODE not in _VALID_MODES:
    logger.warning(
        "Unknown PIPELINE_MODE=%r — falling back to 'scrape_only'. "
        "Valid values: %s",
        _PIPELINE_MODE,
        ", ".join(sorted(_VALID_MODES)),
    )
    _PIPELINE_MODE = "scrape_only"


async def _run_cycle() -> None:
    """Execute one full pipeline cycle according to PIPELINE_MODE."""
    logger.info("=" * 60)
    logger.info("Scheduler: starting pipeline cycle  [mode=%s]", _PIPELINE_MODE)
    logger.info("=" * 60)

    # -----------------------------------------------------------------
    # Step 1 — Scrapers (always runs)
    # -----------------------------------------------------------------
    try:
        logger.info("[cycle] Step 1 — scraping …")
        await _scrape()
    except Exception:
        logger.exception("[cycle] Scraper run failed; skipping rest of cycle.")
        return

    # -----------------------------------------------------------------
    # Step 2 — NLP pipeline (scrape_and_nlp | full)
    # -----------------------------------------------------------------
    if _PIPELINE_MODE in ("scrape_and_nlp", "full"):
        try:
            from backend.nlp.pipeline import run_pipeline as _nlp  # noqa: PLC0415
            logger.info("[cycle] Step 2 — NLP pipeline …")
            _nlp()
        except Exception:
            logger.exception("[cycle] NLP pipeline failed; skipping LLM step.")
            return

    # -----------------------------------------------------------------
    # Step 3 — LLM pipeline (full only)
    # -----------------------------------------------------------------
    if _PIPELINE_MODE == "full":
        try:
            from backend.llm.pipeline import run_pipeline as _llm  # noqa: PLC0415
            logger.info("[cycle] Step 3 — LLM pipeline …")
            _llm()
        except Exception:
            logger.exception("[cycle] LLM pipeline failed.")

    logger.info("[cycle] Pipeline cycle complete.")


async def _loop() -> None:
    """Run the pipeline immediately, then repeat every SCRAPE_INTERVAL_SECONDS."""
    logger.info(
        "Scheduler started — mode=%s, interval=%ds (%d min)",
        _PIPELINE_MODE,
        SCRAPE_INTERVAL_SECONDS,
        SCRAPE_INTERVAL_SECONDS // 60,
    )
    while True:
        await _run_cycle()
        logger.info(
            "Scheduler: sleeping %ds — next run in %d min.",
            SCRAPE_INTERVAL_SECONDS,
            SCRAPE_INTERVAL_SECONDS // 60,
        )
        await asyncio.sleep(SCRAPE_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(_loop())
