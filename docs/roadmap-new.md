# Roadmap — Social Reaction Analysis GR (Clean-Slate Rebuild)

> This roadmap tracks the **greenfield rebuild** described in [`system-design.md`](./system-design.md).
> The prototype (tracked in [`roadmap.md`](./roadmap.md)) is treated as **prior art only** — its learnings inform this plan, but the target architecture is built fresh.
>
> **Legend**
> - Status: ✅ Done · ⚠️ Needs Testing · 🔄 In Progress · 🔲 Not Started · 🔁 Needs Revisit
> - Priority: 🔴 High · 🟡 Medium · 🟢 Low
> - Effort: S < 1 day · M 1–3 days · L > 3 days
> - Carryover: 🧬 logic/approach transfers from prototype · ✨ net-new

---

## Target Architecture (summary)

| Layer | Decision | Replaces (prototype) |
|---|---|---|
| Datastore | PostgreSQL 16 + `pgvector` + `PostGIS` | ChromaDB + GeoJSON file |
| Architecture | Modular monolith + background worker | Ad-hoc scripts per phase |
| Scraping | `feedparser` + `trafilatura` + `httpx`/`selectolax`; Playwright fallback | Crawl4AI/Playwright-first |
| Embeddings | `paraphrase-multilingual-mpnet-base-v2` (swappable, benchmarked) | same model, no abstraction |
| Clustering | HDBSCAN + config-driven quality gates | same, hardened + snapshotted |
| LLM | provider abstraction: Groq → Gemini → Ollama (offline/repro) | litellm, no offline path |
| Geocoding | self-hosted Nominatim → PostGIS point-in-polygon | public Nominatim + shapely |
| API | FastAPI + generated TypeScript client | FastAPI (kept) |
| Frontend | React + TypeScript + Vite + **MapLibre GL JS** | vanilla JS + Leaflet |
| Map tiles | MapTiler vector tiles (free dev tier) | CartoDB/OSM raster |
| Scheduling | APScheduler in worker (Prefect = upgrade) | stdlib asyncio loop |
| Deploy | Docker Compose on single VPS + Caddy | local-only |
| Sources | Greek news + Reddit + official feeds; GDELT → evaluation only | news + GDELT ingested |

---

## Phase 0 — Foundations

| Task | Status | Priority | Effort | Carryover | Notes |
|---|---|---|---|---|---|
| Repo skeleton + module boundaries (`ingestion/`, `nlp/`, `enrich/`, `api/`, `web/`) | 🔲 Not Started | 🔴 High | S | ✨ | Clear, single-purpose packages |
| `uv` dependency management + lockfile | 🔲 Not Started | 🔴 High | S | ✨ | Deterministic builds |
| Docker Compose: `db` (PG+pgvector+PostGIS), `api`, `caddy` | 🔲 Not Started | 🔴 High | M | ✨ | `docker compose up` reproduces system |
| Postgres schema + migrations (Alembic) | 🔲 Not Started | 🔴 High | M | ✨ | `articles`, `events`, `event_locations`, `pipeline_runs` |
| CI: `ruff` + `mypy` + `pytest` on push (GitHub Actions) | 🔲 Not Started | 🔴 High | S | ✨ | Pre-commit hooks mirror CI |
| `.env.example` + secrets via env/Docker secrets | 🔲 Not Started | 🟡 Medium | S | 🧬 | Carry over documented vars |
| **Exit criterion:** `docker compose up` serves an empty, typed API | 🔲 Not Started | — | — | — | |

---

## Phase 1 — Ingestion

| Task | Status | Priority | Effort | Carryover | Notes |
|---|---|---|---|---|---|
| `SourceConnector` interface → `RawDocument` contract | 🔲 Not Started | 🔴 High | S | ✨ | Adding a source never touches the pipeline |
| Greek news connector: Google News RSS (`feedparser`) + `trafilatura` extraction | 🔲 Not Started | 🔴 High | M | 🧬 | Primary backbone; replaces Crawl4AI |
| Official connector: `apergia.gr` (`httpx` + `selectolax`) | 🔲 Not Started | 🔴 High | M | ✨ | Structured strike/protest announcements |
| Greek relevance filter (spaCy `el_core_news_md`, YAML keyword config) | 🔲 Not Started | 🟡 Medium | M | 🧬 | Lemma-based gate, behind `RelevanceFilter` interface |
| Idempotent ingestion via `content_hash` (SHA-256) | 🔲 Not Started | 🔴 High | S | 🧬 | Re-runs never double-insert |
| Playwright fallback (per-source opt-in) | 🔲 Not Started | 🟢 Low | M | 🧬 | Only for JS-heavy sources |
| Connector tests with recorded fixtures (`vcr.py`) | 🔲 Not Started | 🟡 Medium | S | ✨ | Parse/normalise against frozen payloads |
| **Exit criterion:** articles land in Postgres; idempotent re-runs | 🔲 Not Started | — | — | — | |

---

## Phase 2 — NLP Core

| Task | Status | Priority | Effort | Carryover | Notes |
|---|---|---|---|---|---|
| Embedding stage (incremental; only un-embedded rows) → `pgvector` | 🔲 Not Started | 🔴 High | M | 🧬 | `paraphrase-multilingual-mpnet-base-v2`, swappable interface |
| HDBSCAN clustering over recent window | 🔲 Not Started | 🔴 High | M | 🧬 | Quality gates: min articles, min intra-sim, min relevance |
| Deduplication (cosine + time-window) → `is_duplicate` | 🔲 Not Started | 🔴 High | S | 🧬 | |
| Event registry: centroid matching → stable `event_id` | 🔲 Not Started | 🔴 High | M | 🧬 | `first_seen`/`last_seen` maintained for timeline |
| `pipeline_runs` snapshot: config + metrics per cycle | 🔲 Not Started | 🔴 High | S | ✨ | Backbone of reproducibility (silhouette, n_clusters, n_dupes) |
| Config-driven thresholds (YAML/env, version-controlled) | 🔲 Not Started | 🟡 Medium | S | 🧬 | Auditable for thesis |
| NLP unit tests on synthetic vectors | 🔲 Not Started | 🟡 Medium | S | ✨ | Threshold logic, dedup, registry matching |
| **Exit criterion:** stable events with metrics recorded in `pipeline_runs` | 🔲 Not Started | — | — | — | |

---

## Phase 3 — Enrichment

| Task | Status | Priority | Effort | Carryover | Notes |
|---|---|---|---|---|---|
| LLM provider abstraction (Groq → Gemini → Ollama) | 🔲 Not Started | 🔴 High | M | 🧬 | Ollama = offline/reproducible path (no API keys) |
| Embedding zero-shot classification (primary, no tokens) | 🔲 Not Started | 🔴 High | M | 🧬 | Four-axis multi-label model: Action Form (multi-label), Thematic Field (multi-label), Channel (single), Intensity (ordinal) |
| LLM classification fallback (low-confidence clusters only) | 🔲 Not Started | 🟡 Medium | S | 🧬 | `instructor` + Pydantic structured output |
| Location extraction: gazetteer-first → spaCy NER → LLM fallback | 🔲 Not Started | 🔴 High | M | 🧬 | Cheaper/precise vs LLM-first |
| Self-hosted Nominatim (Greece extract) container | 🔲 Not Started | 🔴 High | M | ✨ | Removes public-API rate-limit fragility |
| PostGIS point-in-polygon validation (official ELSTAT periphery polygons) | 🔲 Not Started | 🔴 High | M | 🧬 | Replaces shapely + ad-hoc GeoJSON |
| Multi-location event support (`event_locations`) | 🔲 Not Started | 🟡 Medium | S | 🧬 | |
| Bilingual summaries (EL + EN) | 🔲 Not Started | 🔴 High | M | 🧬 | |
| Cost/robustness layer: batching, caching, exponential backoff, budget guard | 🔲 Not Started | 🟡 Medium | S | ✨ | Replaces hardcoded `sleep(2)` |
| **Exit criterion:** events fully enriched and validated in-region | 🔲 Not Started | — | — | — | |

---

## Phase 4 — API

| Task | Status | Priority | Effort | Carryover | Notes |
|---|---|---|---|---|---|
| FastAPI app (read-only), Pydantic models shared with pipeline | 🔲 Not Started | 🔴 High | S | 🧬 | |
| `GET /events` (category/region/from/to/bbox, paginated) | 🔲 Not Started | 🔴 High | M | 🧬 | Date + bbox filters now in-scope |
| `GET /events/{event_id}` (detail + articles) | 🔲 Not Started | 🔴 High | S | 🧬 | |
| `GET /stats` (category/region/time distributions) | 🔲 Not Started | 🔴 High | S | 🧬 | |
| `GET /events/geojson` (typed FeatureCollection) | 🔲 Not Started | 🟡 Medium | S | ✨ | Map loads one typed payload, no client reshaping |
| `GET /health` | 🔲 Not Started | 🟡 Medium | S | 🧬 | |
| Short-TTL cache + HTTP `Cache-Control` | 🔲 Not Started | 🟡 Medium | S | 🧬 | Sufficient because write path is batch |
| Optional Bearer token for future admin/write routes | 🔲 Not Started | 🟢 Low | S | ✨ | |
| Generated TypeScript client from OpenAPI schema | 🔲 Not Started | 🔴 High | S | ✨ | Cross-language type safety |
| API tests (`httpx` ASGI): endpoints, filters, 404s, pagination | 🔲 Not Started | 🟡 Medium | S | ✨ | |
| **Exit criterion:** all endpoints tested | 🔲 Not Started | — | — | — | |

---

## Phase 5 — Frontend

| Task | Status | Priority | Effort | Carryover | Notes |
|---|---|---|---|---|---|
| React + TypeScript + Vite scaffold (static SPA) | 🔲 Not Started | 🔴 High | M | ✨ | Replaces vanilla JS; served by Caddy |
| MapLibre GL JS map + MapTiler vector tiles | 🔲 Not Started | 🔴 High | M | ✨ | Replaces Leaflet; no token/lock-in |
| Category-coded markers + region overlay (vector, data-driven styling) | 🔲 Not Started | 🔴 High | M | 🧬 | |
| Event detail panel (summary EL/EN, date, location, sources, fly-to) | 🔲 Not Started | 🔴 High | M | 🧬 | |
| Dashboard: country/category/event views + charts (Recharts/Chart.js) | 🔲 Not Started | 🟡 Medium | M | 🧬 | |
| Click-to-filter legend + category filtering | 🔲 Not Started | 🟡 Medium | S | 🧬 | |
| Bilingual UI (i18next EL/EN toggle) | 🔲 Not Started | 🟡 Medium | S | ✨ | |
| Typed state store (Zustand/Context) consuming generated API client | 🔲 Not Started | 🟡 Medium | S | ✨ | |
| Frontend tests: Vitest (logic) + Playwright smoke ("map loads, markers render") | 🔲 Not Started | 🟡 Medium | S | ✨ | |
| **Exit criterion:** live demo — map loads, filters work, event detail opens | 🔲 Not Started | — | — | — | |

---

## Phase 6 — Social & Official Sources

| Task | Status | Priority | Effort | Carryover | Notes |
|---|---|---|---|---|---|
| Reddit connector (official OAuth API via `PRAW`) | 🔲 Not Started | 🔴 High | M | ✨ | Strongest justified social source; *Digital Reaction* signal |
| Curated X/Twitter journalist allow-list (RSS-bridge/Nitter fallback) | 🔲 Not Started | 🟡 Medium | M | ✨ | Document ToS fragility explicitly |
| Additional official feeds (union/ministry/civil-protection) | 🔲 Not Started | 🟡 Medium | M | ✨ | High-quality "upcoming events" signal |
| Instagram — **out of scope / manual curation only** | 🔲 Not Started | 🟢 Low | S | ✨ | No compliant programmatic read path; document as limitation |
| **Exit criterion:** Digital-reaction signal present in events | 🔲 Not Started | — | — | — | |

---

## Phase 7 — Evaluation & Methodological Rigor

> First-class thesis deliverable — turns the engineering project into a defensible study. All artifacts live in versioned notebooks.

| Task | Status | Priority | Effort | Carryover | Notes |
|---|---|---|---|---|---|
| Hand-labelled gold set (category + location + is-event) | 🔲 Not Started | 🔴 High | L | ✨ | Document inter-annotator agreement if multiple labellers |
| Clustering evaluation (silhouette, Davies-Bouldin + extrinsic P/R/F1 vs gold) | 🔲 Not Started | 🔴 High | M | 🧬 | Compare HDBSCAN vs agglomerative baseline |
| Embedding model comparison (≥3: mpnet / e5 / BGE-M3 / Greek-tuned) | 🔲 Not Started | 🔴 High | L | 🧬 | Scored on gold set |
| Classification evaluation (confusion matrix + macro-F1) | 🔲 Not Started | 🔴 High | M | ✨ | zero-shot vs LLM-fallback vs optional fine-tuned classifier |
| Geocoding evaluation (% located, % correct region, error analysis) | 🔲 Not Started | 🟡 Medium | M | ✨ | |
| **GDELT as comparator** (Greek-news event detection vs GDELT coded events) | 🔲 Not Started | 🟡 Medium | M | 🧬 | GDELT's defensible research use — *not* an ingestion source |
| Reproducibility check: figures regenerable from `pipeline_runs` + Ollama path | 🔲 Not Started | 🔴 High | S | ✨ | No API keys required to reproduce |
| **Exit criterion:** reproducible evaluation chapter | 🔲 Not Started | — | — | — | |

---

## Phase 8 — Polish & Ops

| Task | Status | Priority | Effort | Carryover | Notes |
|---|---|---|---|---|---|
| APScheduler in worker container (run history → `pipeline_runs`) | 🔲 Not Started | 🔴 High | M | 🧬 | Replaces stdlib asyncio loop |
| Worker container in Docker Compose (db/worker/api/caddy) | 🔲 Not Started | 🔴 High | M | ✨ | + optional `nominatim`, `ollama` |
| Caddy reverse proxy + automatic HTTPS (Let's Encrypt) | 🔲 Not Started | 🔴 High | S | ✨ | TLS termination + static frontend hosting |
| Database backups + restore runbook | 🔲 Not Started | 🟡 Medium | S | ✨ | Single `pg_dump` backup story |
| Structured logging (`structlog`) with per-cycle run id | 🔲 Not Started | 🟡 Medium | S | ✨ | |
| Deploy to single VPS (Hetzner/DO class) | 🔲 Not Started | 🔴 High | M | ✨ | ~€5–12/mo |
| **Exit criterion:** deployed, stable, demo-ready | 🔲 Not Started | — | — | — | |

---

## Backlog & Ideas

> Unscoped tasks and ideas for future consideration, re-based on the clean-slate architecture. No commitment or ordering.

### Data Acquisition & Sources

| Item | Notes |
|---|---|
| Keyword coverage gaps | Review category keyword YAML for solidarity-economy / volunteering terms |
| Bluesky connector | Open API, growing journalist presence; cleaner than X for *Digital Reaction* |
| Diaspora / international reactions | Detect non-Greek sources referencing Greek events |
| ACLED as evaluation comparator | Human-verified, geocoded Greek events — pair with GDELT as a second ground-truth baseline rather than an ingestion source |
| Source reliability weighting | Down-weight tabloid sources in cluster representative selection |
| **Social commentary enrichment** | Enrich news clusters with related hashtags, digital petitions, and social-media user comments (Twitter/X, Reddit threads); deepens *Ψηφιακό* channel signal and adds crowd sentiment context |
| **Political framing & official positions** | Link each event cluster to related political statements, party announcements, parliamentary questions, and government press releases; requires a political-speech connector (parliament.gr, party websites, official press-release feeds) |

### Orchestration & Pipeline

| Item | Notes |
|---|---|
| **Prefect / Dagster orchestration** | Visual DAG + lineage UI — compelling in the defense demo; documented upgrade from APScheduler |
| Queue-based decomposition (Redis/RQ) | Only if near-real-time becomes a requirement (see system-design Appendix A) |
| SSE / WebSocket push | Stream new events to the frontend as the worker publishes them |
| Incremental re-clustering strategy | Tune window size / re-cluster cadence for stability vs freshness |

### NLP & ML

| Item | Notes |
|---|---|
| Fine-tuned Greek embedding model | Greek-BERT or domain-tuned model as a research contribution; benchmark vs mpnet |
| Named entity extraction per cluster | spaCy/Greek-BERT NER → persons, orgs, locations per event |
| Sentiment / tone scoring per article | Positive / negative / neutral alongside reaction category |
| Event intensity score | Composite of article count + source diversity + geo spread |
| Clustering hyperparameter tuning | `min_cluster_size` / `min_samples` on real data |

### LLM & Processing

| Item | Notes |
|---|---|
| Fine-tuned classifier head | Supervised 5-category classifier as an alternative to zero-shot + LLM fallback |
| Prompt/version registry | Track prompt versions in `pipeline_runs` for reproducibility |
| Multi-summary batching tuning | Optimise tokens-per-call vs quality |

### API & Backend

| Item | Notes |
|---|---|
| Export endpoint | `GET /export?format=csv\|geojson` for offline analysis |
| Admin/trigger route | Token-gated endpoint to kick a pipeline run + inspect raw data |
| Rate limiting / API key tiers | Only if the API is opened beyond the demo |

### Frontend & Visualization

| Item | Notes |
|---|---|
| **deck.gl overlay** | Heatmaps + animated time playback over MapLibre for large/animated datasets |
| Time slider / historical playback | Filter visible events by date range (uses `first_seen`/`last_seen`) |
| Timeline chart (events over time) | Line/area from `/stats` time distribution |
| Choropleth regional overlay | Periphery-level event-count breakdown (PostGIS aggregation → vector tiles) |
| Responsive / mobile layout | Collapse panels on small screens |
| Breaking-news ticker | Latest event summaries; click navigates to event |
| **Multi-axis dashboard filters** | Cross-axis filtering on all four classification axes — e.g. "Βίαιη/Συγκρουσιακή (Axis 4) + Εκπαίδευση (Axis 2)"; requires API params `action_forms=`, `thematic_fields=`, `channel=`, `intensity=` |
| Petition display per cluster | Surface active petitions (e.g. change.org, βουλή.gr) related to each event cluster in the event detail panel |
| Comment system per cluster | Thread-style comments with replies and upvote/downvote per event; requires auth and moderation strategy |

### Map Layers

| Item | Notes |
|---|---|
| Civic Response layer | Solidarity networks, social clinics, community kitchens, post-disaster centres, volunteering — constructive (not only oppositional) reactions. Sources: NGO directories, volunteergreece.gr, OSM, civil-protection records |
| Upcoming / scheduled events layer | Planned protests/strikes/marches before they occur — from apergia.gr + union/party announcements |
| Regional socioeconomic context | Unemployment / poverty / median income per periphery shown alongside an event cluster |

### Analytics & Insights

| Item | Notes |
|---|---|
| Named-entity timeline | Track frequency of specific persons/orgs across events over time |
| Event persistence tracking | Surface event age/recency from `first_seen`/`last_seen` |
| Alert system | Notify when a high-intensity event is detected |

### Infrastructure & Ops

| Item | Notes |
|---|---|
| Managed Postgres (Neon/Supabase) | Offload DB backups/ops if VPS disk management is undesirable |
| Prometheus + Grafana / Sentry | Metrics dashboards + error tracking beyond `pipeline_runs` + `structlog` |
| Image build + release on git tag | Push Docker images on tag via GitHub Actions |
| Self-hosted MapTiler / tile server | Remove the last external map dependency for full reproducibility |
