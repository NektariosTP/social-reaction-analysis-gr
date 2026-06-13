# Roadmap — Social Reaction Analysis GR

> **Legend**
> - Status: ✅ Done · ⚠️ Needs Testing · 🔄 In Progress · 🔲 Not Started · 🔁 Needs Revisit
> - Priority: 🔴 High · 🟡 Medium · 🟢 Low
> - Effort: S < 1 day · M 1–3 days · L > 3 days

---

## Phase 1 — Scope & Design

| Task | Status | Priority | Effort | Notes |
|---|---|---|---|---|
| Define 5 reaction categories | ✅ Done | — | — | Mass Mob, Labor, Institutional, Digital, Conflict |
| Define data sources | ✅ Done | — | — | 8 Greek news sources + GDELT |
| Design project structure | ✅ Done | — | — | scrapers / nlp / llm / api / frontend |

---

## Phase 2 — Data Acquisition (Scrapers)

| Task | Status | Priority | Effort | Notes |
|---|---|---|---|---|
| Base scraper + Crawl4AI integration | ✅ Done | — | — | `scrapers/base_scraper.py` |
| Greek NLP keyword filter (spaCy) | ✅ Done | — | — | Lemma-based, `el_core_news_sm` |
| googlenews (RSS per keyword + trafilatura) | ✅ Done | — | — | Sole broad-coverage scraper; cap raised to 30 articles/keyword |
| gdelt_doc (GDELT DOC API v2) | ✅ Done | — | — | |
| gdelt_events (GDELT 2.0 Event CSV — pre-classified & geocoded) | ✅ Done | — | — | |
| acled (ACLED API v2 — OAuth2, human-verified events) | ⚠️ Disabled | — | — | `scrapers/news/acled.py` implemented & tested; Research tier limits API access to data older than 12 months — not useful for current event monitoring. Removed from `run_all.py`. Re-enable when account tier is upgraded. |
| ~~protothema (sitemap)~~ | ~~✅ Done~~ | — | — | **Removed** — superseded by googlenews + trafilatura |
| ~~kathimerini (RSS)~~ | ~~✅ Done~~ | — | — | **Removed** — superseded by googlenews + trafilatura |
| ~~tanea (sitemap)~~ | ~~✅ Done~~ | — | — | **Removed** — superseded by googlenews + trafilatura |
| ~~eleftherostypos (sitemap + Playwright)~~ | ~~✅ Done~~ | — | — | **Removed** — superseded by googlenews + trafilatura |
| ~~iefimerida (seed URL)~~ | ~~⚠️ Needs Testing~~ | — | — | **Removed** — superseded by googlenews + trafilatura |
| `run_all.py` orchestrator | ✅ Done | — | — | Runs googlenews, gdelt_doc, gdelt_events |
| Scraper scheduler (`scrapers/scheduler.py`) | 🔁 Revisit | — | — | stdlib asyncio loop; `PIPELINE_MODE`: `scrape_only` \| `scrape_and_nlp` \| `full`; runs locally with `python -m scrapers.scheduler`; **needs deployment config (e.g. cron / APScheduler) before production use** |

---

## Phase 3 — NLP & Semantic Analysis

| Task | Status | Priority | Effort | Notes |
|---|---|---|---|---|
| Text embedding pipeline | ✅ Done | — | — | `backend/nlp/embeddings.py`; multilingual sentence-transformer |
| ChromaDB vector store integration | ✅ Done | — | — | `backend/nlp/vectorstore.py`; persists to `data/vectordb/` |
| HDBSCAN event clustering | ✅ Done | — | — | `backend/nlp/clustering.py` |
| Cross-source deduplication | ✅ Done | — | — | `backend/nlp/deduplication.py`; cosine similarity |
| Phase 3 pipeline orchestrator | ✅ Done | — | — | `backend/nlp/pipeline.py` |
| End-to-end Phase 3 run validation | ✅ Done | — | — | 854 records, 40 retained clusters (sil=0.4553), 137 duplicates; cluster quality validated |
| Incremental ingestion (skip already-embedded records) | ✅ Done | — | — | `get_existing_ids()` in `vectorstore.py`; new records only are embedded per cycle |
| Stable cross-run event IDs (EventRegistry) | ✅ Done | — | — | `backend/nlp/event_registry.py`; centroid cosine-similarity matching; stable 8-hex UUIDs persisted to `data/vectordb/event_registry.json` |
| Cluster quality analytics (silhouette score) | ✅ Done | — | — | Logged per clustering run in `clustering.py`; metric: cosine, non-noise records only |
| Cluster relevance filter (off-topic rejection) | ✅ Done | — | — | `CLUSTER_MIN_RELEVANCE_SIM` (default 0.35) in `nlp/config.py`; clusters scoring below threshold against all 5 category descriptions are demoted to noise during Phase 3 clustering |
| Embedding quality improvements | ✅ Done | — | — | Benchmarked 5 configurations in `notebooks/cluster_analytics.ipynb`; retained `paraphrase-multilingual-mpnet-base-v2, max_seq=128` — best silhouette (0.4911) achieved with post-filters `CLUSTER_MIN_ARTICLES=3 + CLUSTER_MIN_INTRA_SIM=0.78`; `multilingual-e5-large` gave 27.3% noise but lower silhouette (0.3728) and higher DB index |
| Data validation notebook | ✅ Done | — | — | `notebooks/cluster_analytics.ipynb`; cluster quality metrics, silhouette score baseline, embedding analysis |

---

## Phase 4 — LLM Processing

| Task | Status | Priority | Effort | Notes |
|---|---|---|---|---|
| LLM config + litellm integration | ✅ Done | — | — | `backend/llm/config.py`; auto-selects model from `.env` |
| Reaction category classification | ✅ Done | — | — | `backend/llm/classify.py`; structured JSON output via litellm |
| Location extraction + Nominatim geocoding | ✅ Done | — | — | `backend/llm/geocode.py`; spaCy NER → Nominatim → LLM fallback |
| Event summarization (Greek + English) | ✅ Done | — | — | `backend/llm/summarize.py` |
| Phase 4 pipeline orchestrator | ✅ Done | — | — | `backend/llm/pipeline.py` |
| Configure `.env` with LLM API key | ✅ Done | — | — | Groq (`llama-4-scout`) primary + Gemini fallback; `.env.example` created; `_auto_model()` updated |
| End-to-end Phase 4 run validation | ⚠️ Needs Testing | 🔴 High | S | Run `python -m backend.llm.pipeline`; re-run needed after classification + geocoding fixes |
| Skip LLM processing for duplicate articles | ✅ Done | — | — | Canonical-only filter in `_run_enrich_clusters()`; `is_duplicate=True` records are excluded from LLM prompt input but still receive category/summary in the metadata write step |
| Geocoding quality review | ✅ Done | — | — | Point-in-polygon validation via `geo_validate.py` using `greece-regions.geojson`; Nominatim bounded queries; multi-location support added |
| Classification quality improvements | ✅ Done | — | — | Tightened confidence thresholds (high >0.55, medium >0.40); improved category descriptions; fixed numbered-prefix prompt bug in `summarize.py` |
| Cluster relevance threshold tuning | ✅ Done | — | — | `CLUSTER_MIN_RELEVANCE_SIM` raised from 0.25 → 0.35 to reject off-topic international news |
| Multi-location event support | ✅ Done | — | — | `geocode_cluster()` returns list; `extra_locations` stored in metadata; API splits into sub-events with suffixed IDs |

---

## Phase 5 — Backend API

| Task | Status | Priority | Effort | Notes |
|---|---|---|---|---|
| FastAPI application (`backend/api/main.py`) | ✅ Done | — | — | CORS configured; frontend served at `/ui` |
| `GET /events` with category + country filters | ✅ Done | — | — | `backend/api/routes/events.py` |
| `GET /events/{event_id}` detail endpoint | ✅ Done | — | — | Switched from `cluster_id: int` to `event_id: str` (stable cross-run UUID); returns articles list |
| `GET /stats` aggregate statistics | ✅ Done | — | — | `backend/api/routes/stats.py` |
| Pydantic response models | ✅ Done | — | — | `backend/api/models.py`; `EventSummary` exposes both `event_id` (stable) and `cluster_id` (debug) |
| Response caching (`_build_event_list` TTL) | ✅ Done | — | — | 5-min in-process TTL cache using `time.monotonic()`; no extra deps |
| End-to-end API smoke test | ✅ Done | — | — | All endpoints verified: `/health`, `/events`, `/events/{id}`, `/stats`, 404 handling, category filter |
| Date range filter (`GET /events?from=&to=`) | 🔲 Not Started | 🟡 Medium | S | Filter by `event_date` or `published_at` |
| API authentication (read-only token) | 🔲 Not Started | 🟡 Medium | S | Simple Bearer token before any public deployment |
| Unit tests for API routes | 🔲 Not Started | 🟡 Medium | S | `pytest` + `httpx` ASGI client; cover list/detail/stats/health + 404 + filter correctness |

---

## Phase 6 — Frontend

| Task | Status | Priority | Effort | Notes |
|---|---|---|---|---|
| Leaflet map centred on Greece | ✅ Done | — | — | `frontend/app.js` + `index.html` |
| Colour-coded cluster markers by category | ✅ Done | — | — | Size scales with `article_count` |
| Synthetic coords for un-geocoded events | ✅ Done | — | — | Golden-angle spread around Greece centre |
| Popup detail (summary, date, sources) | ✅ Done | — | — | Includes "View in dashboard" link |
| Category legend with click-to-filter | ✅ Done | — | — | Horizontal bar at bottom-center of map; toggles markers + navigates dashboard |
| Stats sidebar (event / article / geocoded counts) | ✅ Done | — | — | Moved into dashboard Country view as stats grid |
| Horizontal bar chart (Chart.js) | ✅ Done | — | — | Distribution by category in dashboard Country view |
| **Full frontend revamp (worldmonitor.app-style)** | ✅ Done | — | — | Dark theme, dual-panel (60/40) layout, topbar with GitHub badge + fullscreen + settings |
| **Topbar** | ✅ Done | — | — | Project brand, GitHub stars badge (live API), LIVE indicator, fullscreen toggle, settings gear |
| **Multiple basemap providers** | ⚠️ Needs Testing | — | — | Dark (CartoDB), Streets (OSM), Satellite (Esri), Topographic (OpenTopoMap); switcher UI |
| **Settings modal** | 🔄 In Progress | — | — | API endpoint, map provider (free/MapTiler/Mapbox), language, regions overlay toggle; persists to `localStorage` |
| **Greece geographic regions overlay** | ✅ Done | — | — | 13 peripheries (Αττική, Κρήτη, etc.) rendered as semi-transparent circles with Greek labels |
| **Civic Response Map Layer** | 🔄 In Progress | — | — | Collapsible bottom-left control with checkboxes: solidarity networks, social clinics, community kitchens, post-disaster centres, volunteering programs (data layers TBD) |
| **Breaking news ticker** | ✅ Done | — | — | Horizontally scrolling bar of latest event summaries; pauses on hover; click navigates to event |
| **Dashboard navigation** | ✅ Done | — | — | Three-tab nav: Country, Social Reaction Categories, Events |
| **Country view (default)** | ✅ Done | — | — | 🇬🇷 flag, name, description; 9-field info grid (govt, language, population, area, GDP, currency, capital, president, PM); stats; distribution chart |
| **Category detail view** | ✅ Done | — | — | Category icon, name, description, event/article counts; list of recent events in category |
| **Event detail view** | ✅ Done | — | — | Summary (EN + EL), date, location, sources; article list fetched from `/events/{id}`; map fly-to |
| **Drag-and-drop panel reordering** | ✅ Done | — | — | Sortable.js; main panels (map/dashboard) and inner dashboard cards are drag-reorderable |
| End-to-end frontend smoke test | ⚠️ Needs Testing | 🔴 High | S | Open `/ui`; verify map loads, markers appear, popups work |
| Time slider for historical playback | 🔲 Not Started | 🟡 Medium | L | Filter visible events by date range |
| Timeline chart (events over time) | 🔲 Not Started | 🟡 Medium | M | Line/area chart; use `/stats` `by_date` data |

---

## Phase 7 — Infrastructure & DevOps

| Task | Status | Priority | Effort | Notes |
|---|---|---|---|---|
| `.env` template (`.env.example`) | ✅ Done | — | — | All env vars documented with defaults and descriptions; organized by phase |
| Scraper scheduler (APScheduler or cron) | 🔁 Revisit | — | — | Implemented as `scrapers/scheduler.py` (stdlib asyncio); `PIPELINE_MODE` env var controls scrape-only vs full chain; **currently local-only — needs APScheduler or cron integration for production deployment** |
| Docker Compose setup | 🔲 Not Started | 🟡 Medium | M | Services: api, scraper-cron |
| Health check endpoint (`GET /health`) | ✅ Done | — | — | Returns `{"status": "ok", "vector_store_count": N}`; calls `collection_count()` |
| Deployment (VPS / cloud) | 🔲 Not Started | 🟢 Low | L | Nginx + uvicorn, or cloud-run style container |

---

## Backlog & Ideas

> Unscoped tasks and ideas for future consideration. No commitment or ordering.

### Data Acquisition & Sources

| Item | Notes |
|---|---|
| Additional keyword coverage | Review `REACTION_KEYWORDS` for gaps; add terms for solidarity economy, volunteering categories |
| Multi-language support | Extend scraping to non-Greek sources reporting on Greek events (e.g. Reuters, AP) |
| Social media integration | Twitter/X or Reddit monitoring for digital reaction category |
| Cross-country events | Detect Greek diaspora / international reactions that reference Greece |
| ACLED historical bulk load (one-time) | Bootstrap ChromaDB with ~6,133 human-verified, geocoded events for Greece (2018–Apr 2025). Run once with `ACLED_HISTORICAL_MODE=true python -m scrapers.run_all`. Code is ready; scraper is disabled by default. |
| ACLED tier upgrade for real-time access | Upgrading the myACLED account beyond Research level would unlock individual event data for the past 12 months, making `AcledScraper` fully useful for current event monitoring. Re-add `AcledScraper` to `run_all.py` after upgrade. |

### NLP & ML

| Item | Notes |
|---|---|
| Named entity extraction per cluster | spaCy NER on cluster articles; surface persons, orgs, locations per event |
| Event timeline / persistence tracking | Track first_seen / last_seen per event_id; surface event age and recency in API |
| Clustering hyperparameter tuning | Tune `min_cluster_size`, `min_samples` based on actual data |
| Greek BERT for NER | Replace `el_core_news_sm` with a fine-tuned Greek BERT for better location extraction accuracy |

### LLM & Processing

| Item | Notes |
|---|---|
| Rate limiting robustness | Current hardcoded `time.sleep(2)` — consider exponential backoff on 429s |
| Batch / cost optimization | Group multiple cluster summaries per LLM call to reduce API cost |
| Source reliability weighting | Down-weight tabloid sources in cluster representative selection |

### API & Backend

| Item | Notes |
|---|---|
| Bounding box filter (`GET /events?bbox=…`) | Deferred — only useful for sub-national (city-level) queries or multi-country expansion; not needed while scope is Greece-only |
| SSE / WebSocket endpoint for real-time updates | Push new events as scrapers run |
| Export API | `GET /export?format=csv\|geojson` for offline analysis |

### Frontend & Visualization

| Item | Notes |
|---|---|
| Regional heatmap layer (Leaflet.heat) | Density layer toggled independently from markers |
| Responsive / mobile layout | Collapse sidebar on small screens |
| Greek / English language toggle | Switch `summary_el` / `summary_en` in popups |
| Admin UI | Simple dashboard to trigger pipeline runs and inspect raw data |

### Map Layers

| Item | Notes |
|---|---|
| Choropleth regional overlay | Regional (νομός / περιφέρεια) breakdown of event counts on the map |
| Civic Response Map Layer | Togglable map overlay for solidarity networks (Δίκτυα Αλληλεγγύης), social clinics, community kitchens, post-disaster help centers, and volunteering programs. Captures constructive civic reactions to state failure, not just oppositional ones. Source candidates: NGO directories, volunteergreece.gr, OSM, government civil protection records |
| Upcoming / Scheduled Events Layer | Map layer for planned protests, strikes, and marches before they occur. Source candidates: union announcements, political party press releases, scraped event calendars |

### Analytics & Insights

| Item | Notes |
|---|---|
| Sentiment scoring per article | Assign positive / negative / neutral tone alongside reaction category |
| Event intensity score | Composite score from article count + source diversity + geo spread |
| Named entity timeline | Track how often specific persons / orgs appear across events over time |
| Alert system | Push notification or email when a high-intensity event is detected |
| Regional Context Overlay | Socioeconomic data (unemployment, poverty rate, median income) per νομός / περιφέρεια as a dashboard panel shown alongside an event cluster — e.g., a cluster about a protest in Thessaloniki surfaces the regional unemployment figures for that area to contextualise why the event occurred there |

### Infrastructure & Ops

| Item | Notes |
|---|---|
| GitHub Actions CI (lint + test) | `ruff` lint, `pytest` on push |
| `pytest` test suite | Unit tests: scraper parsing, NLP keyword filter, API routes |
