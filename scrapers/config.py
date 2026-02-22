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
    # Mass Mobilization
    "διαδήλωση",
    "συγκέντρωση",
    "πορεία",
    "μπλόκο",
    "κατάληψη",
    "πλατεία",
    # Labor & Economic
    "απεργία",
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
        "seed_urls": [
            "https://www.protothema.gr/greece/",
            "https://www.protothema.gr/politics/",
        ],
    },
    {
        "name": "kathimerini",
        "seed_urls": [
            "https://www.kathimerini.gr/politics/",
            "https://www.kathimerini.gr/society/",
        ],
    },
    {
        "name": "iefimerida",
        "seed_urls": [
            "https://www.iefimerida.gr/ellada",
            "https://www.iefimerida.gr/politiki",
        ],
    },
]

# ------------------------------------------------------------------
# Twitter / X (populated from .env — never hard-code tokens here)
# ------------------------------------------------------------------
TWITTER_BEARER_TOKEN: str | None = os.getenv("TWITTER_BEARER_TOKEN")
