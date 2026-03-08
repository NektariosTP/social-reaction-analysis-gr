"""
scrapers/news/gdelt_events.py

Spider that consumes the GDELT 2.0 Event stream CSV archives to produce
pre-classified, geocoded social reaction records for Greece.

Crawl strategy:
  1. Fetch the GDELT 2.0 master file list (lastupdate.txt) to identify the
     most recent 15-minute export CSV archive URL and timestamp.
  2. Generate URLs for the previous GDELT_LOOKBACK_FILES − 1 update windows
     (each window is 15 minutes earlier) to cover a configurable lookback.
  3. For each archive: download the ZIP via httpx, decompress in-memory,
     and parse the tab-separated events CSV.
  4. Filter rows where:
       a. ActionGeo_CountryCode == 'GR'  (event physically located in Greece)
       b. EventRootCode ∈ {14, 17, 18, 19}  (Protest / Coerce / Assault / Fight)
  5. Map EventCode to category_hint using the CAMEO code taxonomy.
  6. Produce structured records conforming to the project's base schema,
     extended with GDELT-specific geospatial and event metadata:
       lat, lon, location_name, cameo_code, goldstein_scale, avg_tone,
       num_mentions.

Note on body text:
  Body text is NOT crawled by this scraper — records contain the SOURCEURL
  (triggering news article) for optional downstream retrieval.  Keyword-
  filtered article text for overlapping events is available via GDELTDocScraper.

Note on coverage:
  GDELT detects events algorithmically from its indexed news corpus; it misses
  events that are not widely reported or not yet indexed.  The pre-classified,
  geocoded output of this scraper directly feeds Phase 4 (LLM geocoding
  verification) and Phase 5 (map visualisation) without a separate NLP
  classification step.
"""

from __future__ import annotations

import asyncio
import csv
import io
import logging
import zipfile
from datetime import datetime, timezone, timedelta

import httpx

from scrapers.base_scraper import BaseScraper
from scrapers.config import REQUEST_DELAY_SECONDS, GDELT_LOOKBACK_FILES

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_GDELT_LASTUPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
_GDELT_EXPORT_BASE    = "http://data.gdeltproject.org/gdeltv2/"

# GDELT 2.0 Events CSV: column indices (0-based, tab-separated, no header row)
# Source: GDELT 2.0 Event Database Codebook v2.1
_COL_GLOBAL_EVENT_ID = 0
_COL_DAY             = 1    # YYYYMMDD (Day of event)
_COL_EVENT_CODE      = 26   # Full CAMEO code (e.g. "1413")
_COL_EVENT_ROOT_CODE = 28   # Root CAMEO code (e.g. "14")
_COL_GOLDSTEIN       = 30   # GoldsteinScale (float, −10 to +10)
_COL_NUM_MENTIONS    = 31   # Number of document mentions
_COL_AVG_TONE        = 34   # Average tone of source articles
_COL_ACTION_GEO_NAME = 52   # ActionGeo_FullName
_COL_ACTION_GEO_CC   = 53   # ActionGeo_CountryCode (ISO 2-letter)
_COL_ACTION_GEO_LAT  = 56   # ActionGeo_Lat (float)
_COL_ACTION_GEO_LON  = 57   # ActionGeo_Long (float)
_COL_SOURCE_URL      = 60   # SOURCEURL (triggering article URL)

_TOTAL_COLS = 61             # Sanity check — discard malformed rows below this

# Greece filter
_GREECE_CC = "GR"

# CAMEO root codes of interest (Protest, Coerce, Assault, Fight)
_RELEVANT_ROOT_CODES: frozenset[str] = frozenset({"14", "17", "18", "19"})

# CAMEO code → project category_hint mapping
# Reference: CAMEO Conflict and Mediation Event Observations codebook
_CAMEO_CATEGORY: dict[str, str] = {
    # Protest (14xx)
    "14":   "mass_mobilization",
    "141":  "mass_mobilization",
    "1411": "mass_mobilization",   # Demonstrate or rally
    "1412": "mass_mobilization",   # Hunger strike
    "1413": "labor_economic",      # Strike (labor)
    "1414": "labor_economic",      # Boycott
    "1415": "mass_mobilization",   # Obstruct passage / blockade
    "1416": "conflict",            # Protest violently / riot
    # Coerce (17xx)
    "17":   "mass_mobilization",
    "171":  "mass_mobilization",
    "172":  "mass_mobilization",
    # Assault (18xx)
    "18":   "conflict",
    "181":  "conflict",
    "182":  "conflict",
    "183":  "conflict",
    "184":  "conflict",
    "185":  "conflict",
    "186":  "conflict",
    # Fight (19xx)
    "19":   "conflict",
    "190":  "conflict",
    "191":  "conflict",
    "192":  "conflict",
    "193":  "conflict",
    "194":  "conflict",
    "195":  "conflict",
    "196":  "conflict",
}

_HTTP_HEADERS: dict[str, str] = {
    "User-Agent": "SocialReactionAnalysisBot/1.0",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cameo_to_category(code: str) -> str:
    """
    Map a full CAMEO code to a category_hint string.
    Falls back to progressively shorter prefix lookups (3-char, then 2-char)
    before returning "conflict" as a safe default for matched root codes.
    """
    if code in _CAMEO_CATEGORY:
        return _CAMEO_CATEGORY[code]
    for length in (3, 2):
        prefix = code[:length]
        if prefix in _CAMEO_CATEGORY:
            return _CAMEO_CATEGORY[prefix]
    return "conflict"


def _day_to_iso(day_str: str) -> str | None:
    """Convert GDELT Day field (YYYYMMDD) to ISO 8601 UTC datetime string."""
    try:
        return (
            datetime.strptime(day_str, "%Y%m%d")
            .replace(tzinfo=timezone.utc)
            .isoformat()
        )
    except ValueError:
        return None


def _gdelt_file_url(dt: datetime) -> str:
    """Build the download URL for the GDELT 2.0 export CSV at the given UTC datetime."""
    name = dt.strftime("%Y%m%d%H%M%S") + ".export.CSV.zip"
    return _GDELT_EXPORT_BASE + name


def _safe_float(value: str) -> float | None:
    """Parse a CSV field to float, returning None on empty or invalid input."""
    try:
        return float(value) if value.strip() else None
    except ValueError:
        return None


def _safe_int(value: str) -> int | None:
    """Parse a CSV field to int, returning None on empty or invalid input."""
    try:
        return int(value) if value.strip() else None
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Spider
# ---------------------------------------------------------------------------

class GDELTEventsScraper(BaseScraper):
    """
    Scraper for the GDELT 2.0 Event stream — Greece filter, relevant CAMEO codes.

    Processes the last GDELT_LOOKBACK_FILES 15-minute CSV archives and extracts
    events physically located in Greece with CAMEO root codes 14, 17, 18, or 19.

    Output records carry pre-classified category_hint values and geospatial
    coordinates (lat / lon) derived directly from GDELT — no downstream NLP
    classification or geocoding step is required for these records.
    """

    @property
    def source_name(self) -> str:
        return "gdelt_events"

    @property
    def seed_urls(self) -> list[str]:
        # Not used — crawl() is fully overridden.
        return []

    # ------------------------------------------------------------------
    # Public entry-point (overrides BaseScraper.crawl)
    # ------------------------------------------------------------------

    async def crawl(self) -> list[dict]:
        """
        Full pipeline:
          1. Resolve the last GDELT_LOOKBACK_FILES export archive URLs.
          2. Download, decompress, and filter each CSV in sequence.
          3. Deduplicate events across overlapping file windows.
          4. Return flat list of structured record dicts.
        """
        file_urls = await self._resolve_file_urls()
        if not file_urls:
            logger.error("[%s] Could not resolve GDELT export file URLs.", self.source_name)
            return []

        logger.info(
            "[%s] Processing %d GDELT export archive(s) (lookback: %d × 15 min).",
            self.source_name, len(file_urls), len(file_urls),
        )

        all_records: list[dict] = []
        seen_event_ids: set[str] = set()
        scraped_at = datetime.now(timezone.utc).isoformat()

        async with httpx.AsyncClient(headers=_HTTP_HEADERS, timeout=120.0) as client:
            for i, url in enumerate(file_urls):
                if i > 0:
                    await asyncio.sleep(REQUEST_DELAY_SECONDS)

                records = await self._process_export_file(
                    url, client, scraped_at, seen_event_ids
                )
                all_records.extend(records)
                logger.info(
                    "[%s] %s → %d Greece/relevant events (total so far: %d).",
                    self.source_name,
                    url.split("/")[-1],
                    len(records),
                    len(all_records),
                )

        logger.info(
            "[%s] Crawl complete: %d events collected.", self.source_name, len(all_records)
        )
        return all_records

    # ------------------------------------------------------------------
    # File URL resolution
    # ------------------------------------------------------------------

    async def _resolve_file_urls(self) -> list[str]:
        """
        Fetch lastupdate.txt to identify the most recent export archive URL
        and timestamp, then derive the previous GDELT_LOOKBACK_FILES − 1
        file URLs by stepping back 15 minutes each time.

        Returns a list of ZIP URLs ordered newest-first.
        """
        async with httpx.AsyncClient(headers=_HTTP_HEADERS, timeout=15.0) as client:
            try:
                resp = await client.get(_GDELT_LASTUPDATE_URL, follow_redirects=True)
                resp.raise_for_status()
                text = resp.text
            except Exception as exc:
                logger.error(
                    "[%s] Failed to fetch lastupdate.txt: %s", self.source_name, exc
                )
                return []

        # lastupdate.txt: "SIZE HASH URL" — one line per file type.
        # The export CSV line contains ".export.CSV.zip".
        export_url: str | None = None
        for line in text.strip().splitlines():
            parts = line.strip().split()
            if len(parts) >= 3 and ".export.CSV.zip" in parts[2]:
                export_url = parts[2]
                break

        if not export_url:
            logger.error(
                "[%s] Could not parse export URL from lastupdate.txt content.",
                self.source_name,
            )
            return []

        # Extract the UTC datetime from the filename (YYYYMMDDHHMMSS.export.CSV.zip)
        filename = export_url.split("/")[-1]
        try:
            latest_dt = datetime.strptime(filename[:14], "%Y%m%d%H%M%S").replace(
                tzinfo=timezone.utc
            )
        except ValueError as exc:
            logger.error(
                "[%s] Failed to parse datetime from filename %s: %s",
                self.source_name, filename, exc,
            )
            return []

        # Generate URLs for the last GDELT_LOOKBACK_FILES 15-minute windows
        return [
            _gdelt_file_url(latest_dt - timedelta(minutes=15 * i))
            for i in range(GDELT_LOOKBACK_FILES)
        ]

    # ------------------------------------------------------------------
    # CSV processing
    # ------------------------------------------------------------------

    async def _process_export_file(
        self,
        url: str,
        client: httpx.AsyncClient,
        scraped_at: str,
        seen_event_ids: set[str],
    ) -> list[dict]:
        """
        Download a GDELT 2.0 export ZIP, decompress it in-memory, parse the
        tab-separated CSV, and return matching events as record dicts.
        """
        try:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning(
                "[%s] Failed to download %s: %s", self.source_name, url, exc
            )
            return []

        try:
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                csv_name = next(
                    (n for n in zf.namelist() if n.endswith(".export.CSV")), None
                )
                if csv_name is None:
                    logger.warning(
                        "[%s] No .export.CSV found inside %s",
                        self.source_name, url,
                    )
                    return []
                with zf.open(csv_name) as fh:
                    csv_text = fh.read().decode("utf-8", errors="replace")
        except Exception as exc:
            logger.warning(
                "[%s] Failed to decompress/read ZIP %s: %s", self.source_name, url, exc
            )
            return []

        return self._filter_and_build(csv_text, scraped_at, seen_event_ids)

    def _filter_and_build(
        self,
        csv_text: str,
        scraped_at: str,
        seen_event_ids: set[str],
    ) -> list[dict]:
        """
        Parse the GDELT TSV and return record dicts for Greece / relevant
        CAMEO events.  Deduplicates by GLOBALEVENTID across overlapping
        file windows via the shared seen_event_ids set.
        """
        records: list[dict] = []
        reader = csv.reader(io.StringIO(csv_text), delimiter="\t")

        for row in reader:
            if len(row) < _TOTAL_COLS:
                continue   # malformed / incomplete row

            action_geo_cc = row[_COL_ACTION_GEO_CC].strip()
            root_code     = row[_COL_EVENT_ROOT_CODE].strip()

            # Apply geography and CAMEO filters
            if action_geo_cc != _GREECE_CC:
                continue
            if root_code not in _RELEVANT_ROOT_CODES:
                continue

            event_id = row[_COL_GLOBAL_EVENT_ID]
            if event_id in seen_event_ids:
                continue
            seen_event_ids.add(event_id)

            event_code    = row[_COL_EVENT_CODE].strip()
            location_name = row[_COL_ACTION_GEO_NAME].strip()
            source_url    = row[_COL_SOURCE_URL].strip()
            lat           = _safe_float(row[_COL_ACTION_GEO_LAT])
            lon           = _safe_float(row[_COL_ACTION_GEO_LON])
            goldstein     = _safe_float(row[_COL_GOLDSTEIN])
            avg_tone      = _safe_float(row[_COL_AVG_TONE])
            num_mentions  = _safe_int(row[_COL_NUM_MENTIONS])

            records.append({
                # Base schema fields
                "source":        self.source_name,
                "url":           source_url,
                "title":         "",    # not available in GDELT Events table
                "body":          "",    # not crawled; see GDELTDocScraper for text
                "published_at":  _day_to_iso(row[_COL_DAY]),
                "scraped_at":    scraped_at,
                "lang":          "el",
                "category_hint": _cameo_to_category(event_code),
                # GDELT-specific extensions
                "lat":           lat,
                "lon":           lon,
                "location_name": location_name,
                "cameo_code":    event_code,
                "goldstein_scale": goldstein,
                "avg_tone":      avg_tone,
                "num_mentions":  num_mentions,
            })

        return records

    async def parse(self, result) -> list[dict]:  # pragma: no cover
        # crawl() is fully overridden; parse() is never called.
        return []
