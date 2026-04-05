"""
scrapers/run_all.py

Entrypoint that instantiates every registered scraper, runs each one,
and persists the collected records to data/raw/.

Usage:
    python -m scrapers.run_all
"""

from __future__ import annotations

import asyncio
import logging

from scrapers.news.googlenews import GoogleNewsRSSScraper
from scrapers.news.gdelt_doc import GDELTDocScraper
from scrapers.news.gdelt_events import GDELTEventsScraper
from scrapers.utils.storage import save_records

# Register all active scraper classes here.
# Note: AcledScraper is implemented (scrapers/news/acled.py) but disabled — the
# Research API tier only provides data older than 12 months (not useful for
# current event monitoring). Re-enable when the ACLED account tier is upgraded,
# or run the one-time historical bulk load manually:
#   ACLED_HISTORICAL_MODE=true python -m scrapers.run_all
SCRAPER_CLASSES = [
    GoogleNewsRSSScraper,
    GDELTDocScraper,
    GDELTEventsScraper,
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    for cls in SCRAPER_CLASSES:
        scraper = cls()
        logger.info("--- Starting scraper: %s ---", scraper.source_name)
        records = await scraper.crawl()
        save_records(records, scraper.source_name)
        logger.info("--- Finished scraper: %s (%d records) ---", scraper.source_name, len(records))


if __name__ == "__main__":
    asyncio.run(main())
