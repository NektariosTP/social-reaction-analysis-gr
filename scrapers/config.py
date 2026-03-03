"""
scrapers/config.py

Central configuration for all scrapers.
Values are loaded from the project .env file (project root) via python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ------------------------------------------------------------------
# Load environment variables from the project root .env file
# ------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

# ------------------------------------------------------------------
# Output
# ------------------------------------------------------------------
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(_ROOT / "data" / "raw")))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Crawl behaviour
# ------------------------------------------------------------------
# Seconds to wait between HTTP requests (politeness delay)
REQUEST_DELAY_SECONDS: float = float(os.getenv("REQUEST_DELAY_SECONDS", "2"))

# How often the scheduled crawl runs (seconds)
SCRAPE_INTERVAL_SECONDS: int = int(os.getenv("SCRAPE_INTERVAL_SECONDS", "3600"))

# ------------------------------------------------------------------
# Greek social-reaction keywords (used to seed crawls / filter results)
# ------------------------------------------------------------------
REACTION_KEYWORDS: list[str] = [
    # Mass Mobilization — noun + verb/derived forms (lemmatized at runtime by nlp.py)
    "διαδήλωση",
    "διαδηλωτής",   # spaCy lemma for: διαδηλωτές, διαδηλωτών, διαδηλωτή…
    "διαδηλώνω",    # spaCy lemma for: διαδηλώνουν, διαδηλώνει…
    "συγκέντρωση",
    "συγκεντρώνω",  # spaCy lemma for: συγκεντρώνει, συγκεντρώνουν…
    "πορεία",
    "μπλόκο",
    "κατάληψη",
    "πλατεία",
    # Labor & Economic
    "απεργία",
    "απεργούν",     # spaCy lemma→απεργώ: covers απεργούν, απεργεί, απεργούσαν…
    "απεργιακός",   # spaCy lemma for: απεργιακή, απεργιακό, απεργιακών…
    "στάση εργασίας",
    "μποϊκοτάζ",
    # Institutional & Political
    "αποχή",
    "λευκό",
    "άκυρο",
    # Digital
    "hacktivism",
    "καταγγελία",
    "whistleblower",
    # Conflict
    "επεισόδια",
    "συμπλοκές",
    "χημικά",
    "δακρυγόνα",
    "πετροπόλεμος",
]

# ------------------------------------------------------------------
# News source definitions
# Each entry: { "name": str, "seed_urls": list[str] }
# ------------------------------------------------------------------
NEWS_SOURCES: list[dict] = [
    {
        "name": "protothema",
        # Sitemap-based strategy — seed_urls are not used by ProtothemaScraper.
        # See scrapers/news/protothema.py for the sitemap-driven crawl() override.
        "seed_urls": [],
        "sitemap_index_url": "https://www.protothema.gr/sitemap/NewsArticles/sitemap_index.xml",
        # Number of most-recent individual sitemap files to scan per run.
        # Each file typically contains ~200 to ~400 articles published within a short time window.
        "sitemap_pages": 3,
    },
    {
        "name": "kathimerini",
        # RSS-based strategy — seed_urls are not used by KathimeriniScraper.
        # See scrapers/news/kathimerini.py for the RSS-driven crawl() override.
        "seed_urls": [],
        "rss_url": "https://www.kathimerini.gr/infeeds/rss/nx-rss-feed.xml",
    },
    {
        "name": "iefimerida",
        "seed_urls": [
            "https://www.iefimerida.gr/ellada",
            "https://www.iefimerida.gr/politiki",
        ],
    },
    {
        "name": "tanea",
        # Sitemap-based strategy — seed_urls are not used by TaneaScraper.
        # See scrapers/news/tanea.py for the sitemap-driven crawl() override.
        "seed_urls": [],
        # Single flat Google News sitemap (no sitemap index level).
        "sitemap_url": "https://www.tanea.gr/wp-content/uploads/json/sitemap-news.xml",
    },
]

# ------------------------------------------------------------------
# Twitter / X (populated from .env — never hard-code tokens here)
# ------------------------------------------------------------------
TWITTER_BEARER_TOKEN: str | None = os.getenv("TWITTER_BEARER_TOKEN")
