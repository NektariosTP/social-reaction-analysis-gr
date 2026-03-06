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

from scrapers.news.protothema import ProtothemaScraper
from scrapers.news.kathimerini import KathimeriniScraper
from scrapers.news.iefimerida import IefimeriadaScraper
from scrapers.news.tanea import TaneaScraper
from scrapers.news.eleftherostypos import EleftherotyposScraper
from scrapers.news.googlenews import GoogleNewsRSSScraper
from scrapers.utils.storage import save_records

# Register all scraper classes here. As new spiders are added,
# import them and append to this list.
SCRAPER_CLASSES = [
    ProtothemaScraper,
    KathimeriniScraper,
    IefimeriadaScraper,
    TaneaScraper,
    EleftherotyposScraper,
    GoogleNewsRSSScraper,
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
