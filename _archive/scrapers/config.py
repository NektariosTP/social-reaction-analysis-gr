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
# GDELT
# ------------------------------------------------------------------
# Number of 15-minute GDELT 2.0 update files to process per run.
# 4 = last 60 minutes. Increase for less frequent scheduled runs.
GDELT_LOOKBACK_FILES: int = int(os.getenv("GDELT_LOOKBACK_FILES", "4"))

# Time window (minutes) for the GDELT DOC API query.
# 1440 = last 24 hours. Increase to 2880 for a 48-hour window.
GDELT_TIMESPAN_MINUTES: int = int(os.getenv("GDELT_TIMESPAN_MINUTES", "1440"))

# ------------------------------------------------------------------
# ACLED
# ------------------------------------------------------------------
# myACLED account credentials (required for OAuth2 token authentication).
ACLED_EMAIL: str | None = os.getenv("ACLED_EMAIL")
ACLED_PASSWORD: str | None = os.getenv("ACLED_PASSWORD")

# Historical bulk-load mode.
# Set ACLED_HISTORICAL_MODE=true in .env to perform a one-time fetch of all
# accessible ACLED events (from ACLED_HISTORICAL_SINCE to today−12 months).
# Leave false for the recurring "rolling release" mode (default).
ACLED_HISTORICAL_MODE: bool = os.getenv("ACLED_HISTORICAL_MODE", "false").lower() == "true"

# Earliest date for the one-time historical bulk load.
ACLED_HISTORICAL_SINCE: str = os.getenv("ACLED_HISTORICAL_SINCE", "2018-01-01")

# Rolling-release window: number of days before the 12-month cutoff to fetch
# per scheduled run (i.e. how many newly-released ACLED days to retrieve).
ACLED_LOOKBACK_DAYS: int = int(os.getenv("ACLED_LOOKBACK_DAYS", "7"))

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


