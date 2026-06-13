"""
scrapers/news/acled.py

Spider that queries the ACLED API v2 (OAuth2) to produce pre-classified,
geocoded social reaction records for Greece.

ACLED (Armed Conflict Location & Event Data Project) provides manually
curated, verified records of political violence and protest events globally.
It complements GDELT Events by providing higher-quality, human-verified data
with richer metadata (actor names, fatalities, admin hierarchy, source notes).

Authentication (OAuth2 password grant):
  POST https://acleddata.com/oauth/token
  Body (form-urlencoded): username, password, grant_type="password", client_id="acled"
  Response: {"access_token": "...", "refresh_token": "...", "expires_in": 86400}
  Token cached to .acled_token.json (project root) for 24-hour reuse.

Data endpoint:
  GET https://acleddata.com/api/acled/read
  Authorization: Bearer {access_token}
  Parameters: country=Greece, event_date range, _format=json

ACLED → project category_hint mapping:
  Protests / Peaceful protest            → mass_mobilization
  Protests / Labor dispute or strike     → labor_economic
  Protests / Violent demonstration       → conflict
  Protests / Protest with intervention   → conflict
  Riots (any sub-type)                   → conflict
  Battles (any sub-type)                 → conflict
  Violence against civilians             → conflict
  Strategic developments                 → institutional_political
  Explosions/Remote violence             → conflict

Access tier: Research level
  - Individual event records are accessible ONLY for dates older than 12 months.
  - The 12-month blackout is enforced server-side; queries for recent dates
    return 0 rows without error.
  - ~6,133 events available for Greece from 2018 to today−365 days.

Two operating modes (set via ACLED_HISTORICAL_MODE in .env):

  Historical bulk-load (ACLED_HISTORICAL_MODE=true):
    One-time fetch of all events from ACLED_HISTORICAL_SINCE through today−365 days.
    Iterated year-by-year to stay under the API's 5,000-row limit.
    Run this once to populate ChromaDB with the full historical baseline (~6,133 records).

  Rolling release (ACLED_HISTORICAL_MODE=false, default — recurring):
    Fetches events from today−365−ACLED_LOOKBACK_DAYS through today−365.
    As the 12-month blackout window advances each day, ~2 new events become
    accessible per day (~17/week).  Run via the scheduler at each cycle.

Environment variables (set in .env):
  ACLED_EMAIL              myACLED account email address
  ACLED_PASSWORD           myACLED account password
  ACLED_HISTORICAL_MODE    'true' for one-time bulk load; 'false' for rolling (default)
  ACLED_HISTORICAL_SINCE   Start date for bulk load (default: '2018-01-01')
  ACLED_LOOKBACK_DAYS      Rolling-release window in days (default: 7)
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx

from scrapers.base_scraper import BaseScraper
from scrapers.config import (
    ACLED_EMAIL,
    ACLED_PASSWORD,
    ACLED_LOOKBACK_DAYS,
    ACLED_HISTORICAL_MODE,
    ACLED_HISTORICAL_SINCE,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TOKEN_URL = "https://acleddata.com/oauth/token"
_DATA_URL = "https://acleddata.com/api/acled/read"

# Token cache file path (project root).
_TOKEN_CACHE_PATH = Path(__file__).resolve().parent.parent.parent / ".acled_token.json"

# Re-authenticate if the cached token has fewer than this many seconds remaining.
_REFRESH_MARGIN_SECONDS: int = 300

_HTTP_HEADERS: dict[str, str] = {
    "User-Agent": "SocialReactionAnalysisBot/1.0",
}

# Fields to request from ACLED (reduces payload size).
_ACLED_FIELDS = (
    "event_id_cnty|event_date|event_type|sub_event_type"
    "|actor1|actor2|location|admin1|admin2"
    "|latitude|longitude|fatalities|notes|source"
)

# ---------------------------------------------------------------------------
# Category mapping
# ---------------------------------------------------------------------------

# (event_type_lower, sub_event_type_lower) → category_hint
_SUBTYPE_CATEGORY: dict[tuple[str, str], str] = {
    # Protests
    ("protests", "peaceful protest"):              "mass_mobilization",
    ("protests", "labor dispute/strike"):          "labor_economic",
    ("protests", "violent demonstration"):         "conflict",
    ("protests", "protest with intervention"):     "conflict",
    ("protests", "mob violence"):                  "conflict",
    # Riots
    ("riots", "violent demonstration"):            "conflict",
    ("riots", "mob violence"):                     "conflict",
    # Strategic developments
    ("strategic developments", "looting/property destruction"): "conflict",
    ("strategic developments", "agreement"):                    "institutional_political",
    ("strategic developments", "arrests"):                      "institutional_political",
    ("strategic developments", "change to group/activity"):     "institutional_political",
    ("strategic developments", "disrupted weapons use"):        "institutional_political",
    ("strategic developments", "headquarters or base established"): "institutional_political",
    ("strategic developments", "non-violent transfer of territory"): "institutional_political",
    ("strategic developments", "other"):                        "institutional_political",
    ("strategic developments", "takeover"):                     "institutional_political",
}

# Fallback: event_type_lower → category_hint (when sub_event_type is unknown)
_TYPE_FALLBACK: dict[str, str] = {
    "protests":                   "mass_mobilization",
    "riots":                      "conflict",
    "battles":                    "conflict",
    "explosions/remote violence": "conflict",
    "violence against civilians": "conflict",
    "strategic developments":     "institutional_political",
}


def _map_category(event_type: str, sub_event_type: str) -> str:
    """Map ACLED event_type + sub_event_type to a project category_hint string."""
    key = (event_type.strip().lower(), sub_event_type.strip().lower())
    if key in _SUBTYPE_CATEGORY:
        return _SUBTYPE_CATEGORY[key]
    return _TYPE_FALLBACK.get(event_type.strip().lower(), "conflict")


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------

def _load_token_cache() -> dict:
    """Load the token cache file.  Returns {} if the file is missing or corrupt."""
    try:
        return json.loads(_TOKEN_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_token_cache(token_data: dict) -> None:
    """Persist token_data dict (access_token, refresh_token, expires_at) to disk."""
    try:
        _TOKEN_CACHE_PATH.write_text(json.dumps(token_data), encoding="utf-8")
    except OSError as exc:
        logger.warning("[acled] Could not write token cache to %s: %s", _TOKEN_CACHE_PATH, exc)


async def _request_token(client: httpx.AsyncClient, **form_fields: str) -> dict:
    """
    POST to the ACLED OAuth2 token endpoint and return parsed JSON.
    `form_fields` must include at minimum: grant_type, and credentials.
    """
    payload = {"client_id": "acled", **form_fields}
    resp = await client.post(
        _TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=payload,
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


async def _get_bearer_token(client: httpx.AsyncClient) -> str:
    """
    Return a valid ACLED Bearer access token, with multi-level fallback:

    1. Cached access token — used if fresh (not expiring within REFRESH_MARGIN_SECONDS).
    2. Refresh token grant — used if the cache has a refresh token.
    3. Password grant — used as a last resort with ACLED_EMAIL / ACLED_PASSWORD.

    The resolved token (and its refresh counterpart) is always written back to
    the cache file to minimise future authentication round-trips.
    """
    cache = _load_token_cache()

    # -- 1. Valid cached access token -----------------------------------------
    if (
        cache.get("access_token")
        and cache.get("expires_at", 0) > time.time() + _REFRESH_MARGIN_SECONDS
    ):
        remaining = int(cache["expires_at"] - time.time())
        logger.debug("[acled] Using cached Bearer token (%d s remaining).", remaining)
        return cache["access_token"]

    # -- 2. Refresh token grant -----------------------------------------------
    if cache.get("refresh_token"):
        try:
            data = await _request_token(
                client,
                grant_type="refresh_token",
                refresh_token=cache["refresh_token"],
            )
            token_cache = {
                "access_token":  data["access_token"],
                "refresh_token": data.get("refresh_token", cache["refresh_token"]),
                "expires_at":    time.time() + int(data.get("expires_in", 86400)),
            }
            _save_token_cache(token_cache)
            logger.info("[acled] Bearer token refreshed successfully.")
            return data["access_token"]
        except Exception as exc:
            logger.warning(
                "[acled] Token refresh failed (%s) — falling back to password grant.", exc
            )

    # -- 3. Password grant ----------------------------------------------------
    if not ACLED_EMAIL or not ACLED_PASSWORD:
        raise RuntimeError(
            "ACLED_EMAIL and ACLED_PASSWORD must be set in .env to authenticate with ACLED."
        )

    data = await _request_token(
        client,
        grant_type="password",
        username=ACLED_EMAIL,
        password=ACLED_PASSWORD,
    )
    token_cache = {
        "access_token":  data["access_token"],
        "refresh_token": data.get("refresh_token", ""),
        "expires_at":    time.time() + int(data.get("expires_in", 86400)),
    }
    _save_token_cache(token_cache)
    logger.info("[acled] New Bearer token obtained (valid %d s).", data.get("expires_in", 86400))
    return data["access_token"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(value: object) -> float | None:
    try:
        return float(value) if value not in (None, "", "nan") else None  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return None


def _safe_int(value: object) -> int | None:
    try:
        return int(value) if value not in (None, "", "nan") else None  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Spider
# ---------------------------------------------------------------------------

class AcledScraper(BaseScraper):
    """
    Scraper for ACLED data (OAuth2 authenticated) — Greece events.

    Fetches events from the last ACLED_LOOKBACK_DAYS days for Greece
    across all event types relevant to the project's 5 reaction categories.

    Output records carry pre-classified category_hint, geocoordinates, and
    actor/fatality metadata.  The ``notes`` field serves as the body text
    for NLP processing in Phase 3; no Phase 4 geocoding is needed.
    """

    @property
    def source_name(self) -> str:
        return "acled"

    @property
    def seed_urls(self) -> list[str]:
        return []  # Not used — crawl() is fully overridden.

    async def parse(self, result) -> list[dict]:  # noqa: ARG002
        """Not used — crawl() is fully overridden."""
        return []

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    async def crawl(self) -> list[dict]:
        """
        Dispatch to historical bulk-load or rolling-release mode based on
        ACLED_HISTORICAL_MODE.  Both modes clamp the upper date bound to
        today − 365 days to respect the Research-tier 12-month blackout.

        Historical mode (ACLED_HISTORICAL_MODE=true):
            One-time fetch of all Greece events from ACLED_HISTORICAL_SINCE
            through the 12-month cutoff, iterated year-by-year.

        Rolling mode (default):
            Fetches events in the window [cutoff − ACLED_LOOKBACK_DAYS, cutoff],
            retrieving the events that newly became accessible since the last run.
        """
        if not ACLED_EMAIL or not ACLED_PASSWORD:
            logger.error(
                "[acled] ACLED_EMAIL / ACLED_PASSWORD not set in .env — skipping."
            )
            return []

        scraped_at = datetime.now(timezone.utc).isoformat()
        # Strict upper bound: 12-month blackout cutoff
        cutoff_dt = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=365)
        cutoff: str = cutoff_dt.strftime("%Y-%m-%d")

        async with httpx.AsyncClient(headers=_HTTP_HEADERS, timeout=60.0) as client:
            try:
                token = await _get_bearer_token(client)
            except Exception as exc:
                logger.error("[acled] Authentication failed: %s", exc)
                return []

            if ACLED_HISTORICAL_MODE:
                logger.info(
                    "[acled] Historical bulk-load mode: %s → %s",
                    ACLED_HISTORICAL_SINCE,
                    cutoff,
                )
                records = await self._crawl_historical(client, token, scraped_at, cutoff_dt)
            else:
                records = await self._crawl_rolling(client, token, scraped_at, cutoff, cutoff_dt)

        logger.info("[acled] Crawl complete: %d records total.", len(records))
        return records

    # ------------------------------------------------------------------
    # Mode-specific crawl helpers
    # ------------------------------------------------------------------

    async def _crawl_historical(
        self,
        client: httpx.AsyncClient,
        token: str,
        scraped_at: str,
        cutoff_dt: datetime,
    ) -> list[dict]:
        """
        One-time bulk fetch of all accessible ACLED events for Greece.
        Iterates year-by-year to stay under the 5,000-row API limit.
        """
        since_dt = datetime.strptime(ACLED_HISTORICAL_SINCE, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        all_records: list[dict] = []

        current = since_dt
        while current <= cutoff_dt:
            year_end = min(
                datetime(current.year, 12, 31, tzinfo=timezone.utc),
                cutoff_dt,
            )
            since_str = current.strftime("%Y-%m-%d")
            until_str = year_end.strftime("%Y-%m-%d")
            logger.info("[acled] Fetching %s → %s", since_str, until_str)
            batch = await self._fetch_range(client, token, since_str, until_str, scraped_at)
            logger.info("[acled] Batch yielded %d records.", len(batch))
            all_records.extend(batch)
            current = datetime(current.year + 1, 1, 1, tzinfo=timezone.utc)

        return all_records

    async def _crawl_rolling(
        self,
        client: httpx.AsyncClient,
        token: str,
        scraped_at: str,
        cutoff: str,
        cutoff_dt: datetime,
    ) -> list[dict]:
        """
        Rolling-release fetch: retrieves events from the window
        [cutoff − ACLED_LOOKBACK_DAYS, cutoff], picking up newly-published
        events as the 12-month blackout advances.
        """
        since_dt = cutoff_dt - timedelta(days=ACLED_LOOKBACK_DAYS)
        since_str = since_dt.strftime("%Y-%m-%d")
        logger.info("[acled] Rolling release fetch: %s → %s", since_str, cutoff)
        return await self._fetch_range(client, token, since_str, cutoff, scraped_at)

    async def _fetch_range(
        self,
        client: httpx.AsyncClient,
        token: str,
        since: str,
        until: str,
        scraped_at: str,
    ) -> list[dict]:
        """
        Fetch all ACLED events for Greece in [since, until] with pagination.
        Each request fetches up to 5,000 rows; pages continue until the last
        page returns fewer than 5,000 rows.
        """
        all_events: list[dict] = []
        page = 1

        while True:
            params: dict[str, str] = {
                "_format": "json",
                "country": "Greece",
                "event_date": f"{since}|{until}",
                "event_date_where": "BETWEEN",
                "limit": "5000",
                "page": str(page),
                "fields": _ACLED_FIELDS,
            }
            try:
                resp = await client.get(
                    _DATA_URL,
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
                resp.raise_for_status()
                payload = resp.json()
            except Exception as exc:
                logger.error("[acled] Request failed (page %d): %s", page, exc)
                break

            if payload.get("status") != 200:
                logger.error(
                    "[acled] API error (page %d): %s",
                    page,
                    payload.get("messages"),
                )
                break

            rows: list[dict] = payload.get("data") or []
            all_events.extend(rows)

            if len(rows) < 5000:
                break  # Final page
            page += 1

        return self._parse_events(all_events, scraped_at)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_events(self, events: list[dict], scraped_at: str) -> list[dict]:
        """Convert ACLED event dicts to the project's standard record schema."""
        records: list[dict] = []
        seen_ids: set[str] = set()

        for ev in events:
            event_id = str(ev.get("event_id_cnty", "")).strip()
            if not event_id or event_id in seen_ids:
                continue
            seen_ids.add(event_id)

            event_type = (ev.get("event_type") or "").strip()
            sub_event_type = (ev.get("sub_event_type") or "").strip()
            location = (ev.get("location") or "").strip()
            admin1 = (ev.get("admin1") or "").strip()
            notes = (ev.get("notes") or "").strip()
            actor1 = (ev.get("actor1") or "").strip()
            event_date_raw = (ev.get("event_date") or "").strip()  # "YYYY-MM-DD"

            # Descriptive synthetic title.
            location_str = ", ".join(x for x in (location, admin1) if x) or "Greece"
            title = f"{sub_event_type or event_type} in {location_str}"

            # Geocoordinates.
            lat = _safe_float(ev.get("latitude"))
            lon = _safe_float(ev.get("longitude"))

            # ISO 8601 timestamp.
            published_at: str = ""
            if event_date_raw:
                try:
                    published_at = (
                        datetime.strptime(event_date_raw, "%Y-%m-%d")
                        .replace(tzinfo=timezone.utc)
                        .isoformat()
                    )
                except ValueError:
                    published_at = event_date_raw

            record: dict = {
                # --- Standard project schema ---
                "source": self.source_name,
                "url": f"https://acleddata.com/data-export/?event_id={event_id}",
                "title": title,
                "body": notes,
                "published_at": published_at,
                "scraped_at": scraped_at,
                "lang": "el",
                "category_hint": _map_category(event_type, sub_event_type),
                # Geocoordinates pre-resolved — Phase 4 geocoding not required.
                "lat": lat,
                "lon": lon,
                "location_name": location_str,
                # --- ACLED-specific metadata ---
                "acled_event_id": event_id,
                "acled_event_type": event_type,
                "acled_sub_event_type": sub_event_type,
                "acled_actor1": actor1,
                "acled_actor2": (ev.get("actor2") or "").strip(),
                "acled_fatalities": _safe_int(ev.get("fatalities")),
                "acled_source": (ev.get("source") or "").strip(),
            }
            records.append(record)

        return records
