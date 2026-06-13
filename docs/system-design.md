# System Design & Architecture — Social Reaction Analysis GR

> **Status:** Proposed clean-slate design (greenfield)
> **Date:** 2026-06-09
> **Author:** NektariosTP
> **Scope:** Thesis implementation — a platform for detecting, classifying, and visualising social movements and civic reactions in Greece.

This document specifies the *ideal* architecture as if starting from scratch. The existing prototype is treated as **prior art only** — it informs what is hard, not what the design must keep. For each layer, the document presents a small comparison of candidate tools/services, a recommendation, and a one-line justification.

---

## Table of Contents

1. [Goals, Non-Goals & Quality Attributes](#1-goals-non-goals--quality-attributes)
2. [Design Principles](#2-design-principles)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Data Sources Layer](#4-data-sources-layer)
5. [Ingestion & Scraping](#5-ingestion--scraping)
6. [Data Model & Storage](#6-data-model--storage)
7. [NLP Layer](#7-nlp-layer)
8. [LLM Enrichment Layer](#8-llm-enrichment-layer)
9. [Geocoding & Geospatial](#9-geocoding--geospatial)
10. [Backend API](#10-backend-api)
11. [Frontend & Mapping](#11-frontend--mapping)
12. [Orchestration & Scheduling](#12-orchestration--scheduling)
13. [Deployment & Infrastructure](#13-deployment--infrastructure)
14. [Observability, Testing & CI/CD](#14-observability-testing--cicd)
15. [Evaluation & Methodological Rigor](#15-evaluation--methodological-rigor)
16. [Security & Secrets](#16-security--secrets)
17. [Cost Summary](#17-cost-summary)
18. [Phased Delivery Plan](#18-phased-delivery-plan)
19. [Appendix A — Alternative Architectures](#appendix-a--alternative-architectures)
20. [Appendix B — Lessons from the Prototype](#appendix-b--lessons-from-the-prototype)

---

## 1. Goals, Non-Goals & Quality Attributes

### Goals
- Continuously ingest Greek-language and Greece-related content from heterogeneous sources.
- Group related content into **events**, classify each across **four independent multi-label axes** (action form, thematic field, channel, intensity), geolocate it within Greece, and summarise it bilingually (EL/EN).
- Surface events on a polished, interactive map + dashboard.
- Be **reproducible and defensible** for a thesis committee, and **maintainable** beyond the defense.

### Non-Goals
- Hard real-time (sub-minute) delivery. **Scheduled batch (15–30 min cycles) is the target.**
- Multi-country support. Greece-only keeps geocoding, sources, and evaluation tractable.
- Public multi-tenant SaaS. Single-operator deployment.

### Quality Attributes (prioritised)
| Priority | Attribute | What it drives |
|---|---|---|
| 1 | **Defensibility / rigor** | Every design choice has a documented rationale and, where possible, a metric. Reproducible runs. |
| 2 | **Polish (deployed product)** | A live, attractive, fast, demonstrable system for the defense. |
| 3 | **Maintainability** | Typed code, clear module boundaries, tests, the opposite of "vibe-coded". |
| 4 | Cost | Small recurring budget acceptable (~€10–20/mo); avoid lock-in and runaway API costs. |
| 5 | Throughput | Modest. Hundreds–low-thousands of articles/day. No need for horizontal scale. |

---

## 2. Design Principles

1. **One datastore until proven otherwise.** A single Postgres instance (with `pgvector`) holds relational metadata *and* embeddings. Fewer moving parts = fewer failure modes to defend.
2. **Separate ingestion from serving.** The pipeline (write path) and the API (read path) are different processes with different failure and scaling characteristics. They share only the database.
3. **Deterministic core, probabilistic edges.** Clustering, dedup, and classification thresholds are config-driven and logged so a run can be reproduced and explained. LLM calls are isolated, cached, and never on the critical read path.
4. **Idempotent, incremental stages.** Every pipeline stage can be re-run safely; already-processed records are skipped via stable content hashes.
5. **Typed boundaries.** Pydantic models for Python I/O; a generated OpenAPI client + TypeScript types for the frontend. No untyped JSON crossing process boundaries.
6. **YAGNI.** No queue, no microservices, no Kubernetes, no streaming until a requirement forces it.

---

## 3. High-Level Architecture

**Chosen style: Modular monolith + background worker** (Appendix A compares queue-based and serverless alternatives).

```
                           ┌───────────────────────────────────────────────┐
                           │              Single VPS (Docker Compose)      │
                           │                                               │
  External sources         │   ┌────────────────┐      ┌────────────────┐  │
  ───────────────          │   │  Worker        │      │  Web API       │  │
  • Greek news (RSS/HTML)  │   │  (scheduler-   │      │  (FastAPI)     │  │
  • GDELT (eval'd)    ───► │   │   driven)      │      │                │  │
  • Reddit / IG / X        │   │                │      │  /events       │  │
  • apergia.gr & official  │   │  ingest →      │      │  /events/{id}  │  │
                           │   │  normalise →   │ ───► │  /stats        │  │
                           │   │  embed →       │      │  /health       │  │
                           │   │  cluster →     │      │                │  │
                           │   │  dedupe →      │      └───────┬────────┘  │
                           │   │  classify →    │              │           │
                           │   │  geocode →     │              │           │
                           │   │  summarise     │              │           │
                           │   └───────┬────────┘              │           │
                           │           │                       │           │
                           │           ▼                       ▼           │
                           │   ┌───────────────────────────────────────┐   │
                           │   │   PostgreSQL 16 + pgvector + PostGIS  │   │
                           │   │   (articles, events, embeddings, geo) │   │
                           │   └───────────────────────────────────────┘   │
                           └───────────────────────────────────────────────┘
                                          │ HTTPS (Caddy reverse proxy)
                                          ▼
                                ┌───────────────────────┐
                                │  Frontend (static SPA)│
                                │  MapLibre GL + charts │
                                └───────────────────────┘
```

### Runtime components
| Component | Responsibility | Runs as |
|---|---|---|
| **Worker** | The full ingest→enrich pipeline, triggered on a schedule. Pure batch, no HTTP. | Long-lived container with an internal scheduler (APScheduler) |
| **Web API** | Read-only serving of events/stats; OpenAPI docs. Never runs the pipeline. | Uvicorn/Gunicorn container |
| **Database** | Single source of truth: relational + vector + geometry. | Postgres container (or managed) |
| **Reverse proxy** | TLS termination, static frontend hosting, routing. | Caddy container |

**Why a worker, not API-triggered jobs:** keeps long-running CPU/GPU-ish work (embeddings, LLM calls) off the request path, so the API stays fast and the pipeline can fail/retry without affecting users. It is the simplest thing that cleanly separates the two concerns.

---

## 4. Data Sources Layer

You requested: Greek news (keep) + GDELT (evaluate) + social (Reddit posts, IG/X journalist profiles) + official (e.g. `apergia.gr`). Each source is modelled behind a common `SourceConnector` interface that yields normalised `RawDocument`s, so adding/removing a source never touches the pipeline.

### 4.1 Source comparison & decision

| Source | Signal quality | Coverage | Cost | Legal/ToS risk | Verdict |
|---|---|---|---|---|---|
| **Greek news via Google News RSS + article extraction** | High (editorial) | Broad | Free | Low (RSS is intended for syndication) | **Keep — primary backbone** |
| **GDELT 2.0 (Events + DOC API)** | Medium; English-skewed, machine-coded, noisy for Greece | Global, redundant with news | Free | Low | **Demote to optional/experimental** (see below) |
| **Reddit** (e.g. r/greece, r/europe threads) | Medium; strong for *Digital Reaction* | Targeted | Free API (OAuth, rate-limited) | Low (official API) | **Add — official API** |
| **X/Twitter journalist profiles** | High per-account; hard to access | Narrow, curated | API is expensive; scraping violates ToS | **High** | **Add cautiously** via curated allow-list + Nitter/RSS-bridge fallback; document limits |
| **Instagram journalist profiles** | Medium; visual, low text | Narrow | No viable official read API; scraping violates ToS | **High** | **Defer / manual-curation only** — document as a known limitation |
| **Official: `apergia.gr`, union/ministry feeds, civil protection** | Very high; structured, authoritative | Narrow but precise | Free | Low | **Add — high-value "upcoming events" + ground truth** |

### 4.2 The GDELT question (you were right to be skeptical)
**Recommendation: do not make GDELT a core source; keep it as an optional, clearly-labelled experimental connector.**

Reasoning:
- GDELT's value proposition is *global, pre-geocoded, pre-coded (CAMEO) events*. For a **Greece-only, Greek-language** thesis, that strength is largely wasted — most signal duplicates what Greek news already provides, in English, with coarser machine coding.
- Its noise (machine-translated, machine-coded) actively *hurts* your clustering and classification metrics, which are part of your rigor story.
- **However**, it has one defensible research use: as an **independent baseline/ground-truth comparator** — "how does my Greek-news pipeline's event detection compare to GDELT's coded events for the same period?" That's a genuine evaluation contribution, not an ingestion dependency.

So: **GDELT moves from the ingestion path to the evaluation chapter.**

### 4.3 Social media — honest framing
- **Reddit**: clean official OAuth API (`PRAW`), rate-limited but free. Use it. Strongest justified social source.
- **X/Twitter**: the official API tier that allows meaningful reads is expensive and changes often. For a thesis, use a **small curated allow-list of journalist handles** and access via RSS-bridge/Nitter-style gateways *if available at build time*; **document the fragility and ToS constraints explicitly** — committees value an honest limitations section over a brittle scraper.
- **Instagram**: no realistic compliant programmatic read path; treat as **out of scope / manual** and say so.

---

## 5. Ingestion & Scraping

### 5.1 Tooling comparison

| Tool | Best at | Headless browser? | Complexity | Verdict |
|---|---|---|---|---|
| **`feedparser` + `trafilatura`** | RSS discovery + main-text extraction from HTML | No | Low | **Primary** — covers Google News RSS → article body cleanly |
| **`httpx` + `selectolax`** | Fast static HTML fetch + parse for known sites (apergia.gr) | No | Low | **Primary** for structured/official sites |
| **Playwright** | JS-heavy sites, infinite scroll | Yes | Medium | **Fallback only**, per-source opt-in |
| **Scrapy** | Large-scale crawling, built-in pipelines | No | Medium-High | Overkill at this volume; skip |
| **Crawl4AI** (prototype's choice) | LLM-friendly markdown extraction | Yes (Playwright under hood) | Medium | Drop — heavyweight, opaque, and `trafilatura` extracts cleaner text deterministically |

**Decision:** `feedparser` + `trafilatura` + `httpx`/`selectolax` as the default stack; Playwright only where a specific source demands JS rendering. This is faster, more deterministic, and far easier to test than a browser-automation-first approach.

### 5.2 Greek-language relevance filter
- Keep a **lemma-based keyword filter** as a cheap pre-embedding gate, but implement it with **spaCy `el_core_news_md`** (or a Greek-tuned model) behind a `RelevanceFilter` interface so it can be swapped/benchmarked.
- Filter config (keywords per category) lives in version-controlled YAML, not code, so changes are auditable for the thesis.

### 5.3 Normalisation contract
Every connector emits a `RawDocument`:
```
RawDocument(
  source_id, source_type, url, canonical_url,
  title, body_text, language, published_at,
  author, raw_payload (jsonb), content_hash
)
```
`content_hash` (SHA-256 of canonical_url + normalised title) drives **idempotent ingestion** — re-running never double-inserts.

---

## 6. Data Model & Storage

### 6.1 Datastore decision

| Option | Relational | Vector | Geo | Ops burden | Verdict |
|---|---|---|---|---|---|
| **Postgres 16 + `pgvector` + `PostGIS`** | ✅ native | ✅ extension | ✅ extension | **One service** | **Chosen** |
| Qdrant (+ separate Postgres) | ❌ | ✅ best-in-class | partial | Two services to sync | Alternative if vector scale explodes (it won't here) |
| ChromaDB (prototype) | ❌ | ✅ | ❌ | Embedded, but bolt-on metadata, weak query/joins, fragile persistence | Drop |
| Pinecone / managed | ❌ | ✅ | ❌ | Managed but $$ + lock-in + hard to reproduce | Drop for thesis |

**Decision: Postgres + `pgvector` + `PostGIS`.** One backup, one connection string, SQL joins across events/articles/embeddings/geometry, trivial to reproduce in a Docker container for a committee. At your data scale (≤ ~10⁵ vectors), `pgvector` HNSW indexing is more than sufficient.

### 6.2 Core schema (simplified)

```sql
-- raw ingested documents (append-only, deduped by content_hash)
articles(
  id uuid pk, source_id text, source_type text,
  url text, canonical_url text unique, title text,
  body_text text, language text, published_at timestamptz,
  content_hash text unique, ingested_at timestamptz,
  embedding vector(768),            -- pgvector
  event_id uuid null references events(id),
  is_duplicate bool default false
)

-- detected events (stable across runs)
events(
  id uuid pk,                        -- stable cross-run id
  centroid vector(768),
  -- Multi-label classification: four independent axes (replaces single category field)
  action_forms    text[],            -- Axis 1: e.g. ['Διαδήλωση', 'Αποκλεισμός'] (multi-label)
  thematic_fields text[],            -- Axis 2: e.g. ['Εργασιακό', 'Οικονομικό'] (multi-label)
  channel         text,              -- Axis 3: Φυσικό | Ψηφιακό | Υβριδικό
  intensity       text,              -- Axis 4 (ordinal): Ειρηνική | Διαταρακτική | Βίαιη/Συγκρουσιακή
  classification_confidence jsonb,   -- per-axis confidence scores
  summary_el text, summary_en text,
  primary_location geography(Point,4326),  -- PostGIS
  region_code text,                  -- validated periphery
  article_count int, source_count int,
  first_seen timestamptz, last_seen timestamptz,
  status text                        -- detected | enriched | published
)

-- multi-location events
event_locations(
  id uuid pk, event_id uuid references events(id),
  location geography(Point,4326), region_code text, label text
)

-- per-run provenance for reproducibility (rigor!)
pipeline_runs(
  id uuid pk, started_at, finished_at,
  config_snapshot jsonb,             -- thresholds, model ids, versions
  metrics jsonb                      -- silhouette, n_clusters, n_dupes...
)
```

**`pipeline_runs.config_snapshot` + `metrics`** is the backbone of reproducibility: every run records the exact thresholds, model identifiers, and resulting quality metrics. This is what lets you write a credible evaluation chapter.

---

## 7. NLP Layer

### 7.1 Embedding model comparison

| Model | Multilingual/Greek | Dim | Quality (prototype silhouette) | Speed | Verdict |
|---|---|---|---|---|---|
| `paraphrase-multilingual-mpnet-base-v2` | Good | 768 | Best in prototype (0.49 w/ filters) | Medium | **Default** |
| `intfloat/multilingual-e5-large` | Strong | 1024 | Higher noise, lower silhouette in prototype | Slower | Benchmark candidate |
| BGE-M3 | Strong, long-context | 1024 | Untested here | Slower | Benchmark candidate |
| Greek-specific (e.g. Greek-BERT, fine-tuned) | Best for Greek | varies | Untested | — | **Research angle**: fine-tune & compare |

**Decision:** keep `paraphrase-multilingual-mpnet-base-v2` as the validated default, but the embedding model is a swappable interface and the **comparison of ≥3 models on your own labelled set is an explicit evaluation deliverable** (rigor).

### 7.2 Pipeline stages (each idempotent, each logged)
1. **Embed** — only un-embedded articles (incremental).
2. **Cluster** — HDBSCAN over recent window; quality gates: `min_articles`, `min_intra_similarity`, `min_relevance_to_category`. All thresholds in config, snapshotted per run.
3. **Deduplicate** — cosine + time-window; mark `is_duplicate`.
4. **Event registry** — centroid cosine matching against existing events → stable `event_id`, with `first_seen`/`last_seen` maintained for timeline features.

| Clustering choice | Why |
|---|---|
| **HDBSCAN** (chosen) | No need to predefine `k`; handles noise/outliers natively — right for "is this even an event?" |
| K-Means | Needs `k`; no noise concept | 
| Agglomerative + threshold | Viable baseline to compare against (good for the evaluation chapter) |

---

## 8. LLM Enrichment Layer

The LLM does three things: **(a) classify** uncertain clusters, **(b) extract locations**, **(c) summarise** (EL+EN). Classification's *primary* path stays **embedding-based zero-shot** (no tokens, deterministic, cheap); the LLM is the **fallback for low-confidence clusters only**.

### 8.0 Reaction classification model (four-axis, multi-label)

Instead of forcing each event into a single category, the model characterises each event with independent labels across four axes. This improves recall (a strike can also be a protest; an event can be both labour and political), enables granular dashboard filtering, and maps naturally to LLM structured output.

| Axis | Type | Values |
|---|---|---|
| **Axis 1 — Action Form** | multi-label | Διαδήλωση/Πορεία/Συγκέντρωση · Απεργία/Στάση εργασίας · Κατάληψη · Αποκλεισμός/Μπλόκο · Μποϊκοτάζ · Διαδικτυακή εκστρατεία (hashtag/petition) · Whistleblowing · Αποχή |
| **Axis 2 — Thematic Field** | multi-label | Εργασιακό · Πολιτικό/Θεσμικό · Οικονομικό · Περιβαλλοντικό · Δικαιώματα/Κοινωνικό · Εκπαίδευση · Αστυνομική Βία · Άλλο |
| **Axis 3 — Channel** | single-select | Φυσικό (offline) · Ψηφιακό (online) · Υβριδικό |
| **Axis 4 — Intensity** | ordinal | Ειρηνική → Διαταρακτική (μη βίαιη, παρεμποδιστική) → Βίαιη/Συγκρουσιακή |

Classification pipeline:
1. **Axes 1 & 2**: embedding zero-shot (multi-label cosine ranking against label descriptions) — primary path, no tokens.
2. **Axis 3**: heuristic rule (digital-only keywords → Ψηφιακό; physical location present → Φυσικό; both → Υβριδικό) with LLM fallback.
3. **Axis 4**: zero-shot ordinal classification; LLM fallback for uncertain clusters.
4. **LLM fallback (all axes)**: structured `instructor`/Pydantic output with retry-on-invalid, cached by `event_id + content_hash`.

### 8.1 Provider comparison

| Provider | Greek quality | Cost | Speed | Privacy/repro | Verdict |
|---|---|---|---|---|---|
| **Groq** (Llama/Qwen) | Good | Very cheap / free tier | Fastest | Cloud | **Primary** (cost + speed) |
| **Google Gemini** (Flash) | Very good Greek | Cheap | Fast | Cloud | **Fallback / quality tier** |
| **OpenAI** (gpt-class) | Excellent | Higher | Fast | Cloud | Optional quality ceiling |
| **Ollama** (local Llama/Qwen) | Decent | Free (self-host) | Hardware-bound | **Fully reproducible & offline** | **Reproducibility tier** — lets a committee re-run without API keys |

**Decision:** a provider-abstraction layer (`litellm` or a thin custom wrapper) with **Groq primary → Gemini fallback → Ollama for reproducible/offline runs**. The Ollama path is a deliberate rigor feature: the thesis can be reproduced with zero paid API access.

### 8.2 Structured output
Use **`instructor` + Pydantic** (or provider-native JSON mode) so every LLM response is schema-validated. No regex-parsing of free text. Invalid responses are retried with a repair prompt, then dropped to the deterministic fallback.

### 8.3 Cost & robustness controls
- **Batch** multiple cluster summaries per call where possible.
- **Cache** by `event_id + content_hash` so re-runs don't re-pay.
- **Exponential backoff** on 429s (not the prototype's hardcoded `sleep(2)`).
- Hard monthly token budget guard in config.

---

## 9. Geocoding & Geospatial

### 9.1 Pipeline: extract → resolve → validate

| Stage | Tool options | Decision |
|---|---|---|
| Location extraction | spaCy NER (`el`) · LLM extraction · gazetteer match | **Gazetteer-first** (Greek place names) → spaCy NER → LLM fallback. Cheaper & more precise than LLM-first. |
| Geocoding | **Nominatim (self-host)** · Nominatim public · Pelias · Google/Mapbox geocoding | **Self-hosted Nominatim** (Greece extract) — free, no rate limits, reproducible. Public Nominatim as dev fallback. |
| Validation | **PostGIS point-in-polygon** vs official periphery boundaries | PostGIS `ST_Contains` against the 13 peripheries — replaces the prototype's shapely+GeoJSON file with a proper spatial query/index. |

**Why self-hosted Nominatim:** the public instance's 1 req/s policy and ToS make a batch pipeline brittle and arguably non-compliant; a Greece-only Nominatim extract is small (~hundreds of MB) and runs in a container — removing a key fragility and a reproducibility blocker.

Boundary data: **official ELSTAT / Καλλικράτης periphery polygons** (authoritative) rather than ad-hoc GeoJSON, loaded into PostGIS once.

---

## 10. Backend API

### 10.1 Framework comparison

| Framework | Lang | Async | OpenAPI | Fit with Python NLP code | Verdict |
|---|---|---|---|---|---|
| **FastAPI** | Python | ✅ | ✅ auto | Native — shares models/DB layer with pipeline | **Chosen** |
| Litestar | Python | ✅ | ✅ | Same benefits, smaller ecosystem | Viable alternative |
| Node/Express or NestJS | TS | ✅ | manual/decorators | Forces a 2nd language + duplicate models for ML side | Rejected (polyglot tax) |
| Next.js API routes | TS | ✅ | manual | Couples API to frontend; awkward for heavy data layer | Rejected |

**Decision: FastAPI.** Even under a "fully open stack" mandate, the data/NLP core is unavoidably Python; a Python API shares the Pydantic models, DB layer, and types with the pipeline — eliminating an entire class of drift bugs. The frontend gets a **generated TypeScript client from the OpenAPI schema**, so cross-language type safety is preserved without a second backend language.

### 10.2 Endpoints
```
GET /events            ?category=&region=&from=&to=&bbox=   (paginated)
GET /events/{event_id}                                       (detail + articles)
GET /stats             (category / region / time distributions)
GET /events/geojson    (FeatureCollection for direct map consumption)
GET /health
```
- **Read-only**, no auth needed for public read; an optional Bearer token gates any future write/admin route.
- **Caching:** short TTL (60–300s) at the API plus HTTP `Cache-Control`; this is sufficient because the write path is batch.
- A dedicated **`/events/geojson`** endpoint lets the map load a single typed FeatureCollection instead of reshaping JSON client-side.

---

## 11. Frontend & Mapping

This is where "polished deployed product" is won or lost, and where you specifically asked about Mapbox GL JS.

### 11.1 Map rendering library — the key comparison

| Library | Rendering | Tiles | Cost / token | Polish | Verdict |
|---|---|---|---|---|---|
| **MapLibre GL JS** | **Vector, WebGL** | Bring-your-own (MapTiler, self-host, etc.) | **Free, no token** | High (smooth zoom, 3D, data-driven styling) | **Chosen** |
| Mapbox GL JS (v2+) | Vector, WebGL | Mapbox-hosted | **Requires token; usage-billed; restrictive license since v2** | Highest | Rejected — MapLibre is the open fork of GL JS v1 with ~the same API and no billing/lock-in |
| Leaflet (prototype) | **Raster**, DOM | Raster tile providers | Free | Dated feel; janky at scale; limited data-driven styling | Rejected for the headline map |
| deck.gl | WebGL data-viz overlay | pairs with MapLibre/Mapbox | Free | Excellent for large/animated datasets | **Optional overlay** for heatmaps/time animation |

**Decision: MapLibre GL JS** with **MapTiler** vector tiles (generous free dev tier; small paid tier within budget if needed), self-hostable later. This gives you Mapbox-GL-class polish (vector tiles, smooth interaction, data-driven styling, choropleth, 3D) **without a token, billing, or license lock-in** — the single best answer to your Mapbox question. deck.gl is held in reserve for the time-animation/heatmap features.

> **Direct answer on Mapbox GL JS:** functionally excellent, but since v2 it requires an access token, meters usage, and ships under a non-OSS license. **MapLibre GL JS is a drop-in open-source fork** that removes all three concerns while keeping the vector-WebGL polish. For a thesis you want reproducibility and zero surprise bills → MapLibre.

### 11.2 Frontend framework comparison

| Option | Maintainability | Mapping ecosystem | Learning/overhead | Verdict |
|---|---|---|---|---|
| **React + TypeScript + Vite** | High (typed, componentised) | `react-map-gl`, deck.gl, huge ecosystem | Familiar, well-documented | **Chosen** |
| SvelteKit + TS | High, less boilerplate | Good, smaller | New paradigm | Strong alternative |
| Vanilla JS (prototype) | **Low** — exactly what produced the "vibe-coded" mess | manual | none | Rejected |

**Decision: React + TypeScript + Vite.** TypeScript + components directly serve maintainability (your #3 priority) and kill the unstructured-DOM problems of the prototype. Charts via **Recharts** or **Chart.js**; bilingual UI via a light i18n layer (`i18next`).

### 11.3 Frontend architecture
- **Static SPA** built to static assets, served by Caddy — no Node server in production.
- Consumes the **generated OpenAPI TypeScript client** (type-safe API calls).
- Map state, filters, and the dashboard are independent components reading from a small typed store (Zustand/Context). No drag-and-drop-of-everything; deliberate, tested layout.

---

## 12. Orchestration & Scheduling

| Option | Complexity | Observability | Repro | Verdict |
|---|---|---|---|---|
| **APScheduler inside the worker** | Low | Basic, plus our `pipeline_runs` table | High | **Chosen** for the baseline |
| System `cron` | Lowest | Poor (no run history) | Medium | Fine but loses in-process state |
| Prefect / Dagster | Medium-High | **Excellent** (DAG UI, retries, lineage) | High | **Optional upgrade** — strong if you want a visual pipeline for the defense |

**Decision:** APScheduler in the worker for the baseline (one container, run history in Postgres). Document **Prefect** as the upgrade path — its run/lineage UI is genuinely compelling in a thesis demo and worth a sentence in the defense as "production-grade orchestration option."

Each cycle: ingest → embed → cluster → dedupe → register events → enrich (classify/geocode/summarise) → mark `published`. The whole cycle is one `pipeline_runs` row with a config snapshot and metrics.

---

## 13. Deployment & Infrastructure

### 13.1 Packaging
- **Docker Compose** with 4 services: `db` (Postgres+pgvector+PostGIS), `worker`, `api`, `caddy`. Optional `nominatim`, optional `ollama`.
- One `.env`, one `docker compose up` reproduces the entire system — the reproducibility story for the committee.
- **`uv`** for Python dependency management (fast, lockfile-based) → deterministic builds.

### 13.2 Hosting comparison

| Option | Cost | Control | Ease | Verdict |
|---|---|---|---|---|
| **Single VPS** (Hetzner/DigitalOcean), Docker Compose | ~€5–12/mo | Full | Medium | **Chosen** — cheap, reproducible, full control, no cold starts for heavy NLP |
| Render / Railway / Fly.io | Low-med, scales with use | Medium | High | Good alt; watch memory limits for embeddings |
| Serverless (Lambda/Cloud Run) | Variable | Low | Low for stateful NLP | Rejected — cold starts + model loading + statefulness fight the workload |
| Managed Postgres (Neon/Supabase) | Free–low tier | n/a | High | **Optional**: offload just the DB if VPS disk/backup is a concern |

**Decision:** a single small VPS running Docker Compose. Predictable cost, no cold starts, trivially reproducible, and you can demo it live. Managed Postgres is an easy swap if you prefer not to own backups.

---

## 14. Observability, Testing & CI/CD

### Testing (directly serves maintainability + rigor)
| Layer | Tooling | What's tested |
|---|---|---|
| Connectors | `pytest` + recorded fixtures (`vcr.py`) | Parsing/normalisation against frozen sample payloads |
| NLP | `pytest` | Threshold logic, dedup, event-registry matching on synthetic vectors |
| LLM | `pytest` with mocked provider | Schema validation, fallback path, cache behaviour |
| API | `pytest` + `httpx` ASGI client | All endpoints, filters, 404s, pagination |
| Frontend | Vitest + Playwright (smoke) | Component logic + a "map loads, markers render" e2e |

### Observability
- **Structured logging** (`structlog`) with a run id per cycle.
- `pipeline_runs` table = built-in metrics history (no extra infra).
- Optional **Prometheus + Grafana** or **Sentry** noted as upgrades; not required for the baseline.

### CI/CD
- **GitHub Actions**: `ruff` (lint+format) + `mypy` (types) + `pytest` on every push; build Docker images on tag.
- Pre-commit hooks mirror CI locally.

---

## 15. Evaluation & Methodological Rigor

This section is what turns an engineering project into a defensible thesis. It is a **first-class deliverable**, not an afterthought.

1. **Labelled gold set.** Hand-label a sample of articles/events (category + location + is-event). Used for all metrics below. Document inter-annotator agreement if multiple labellers.
2. **Clustering evaluation.** Silhouette + Davies-Bouldin on embeddings; plus extrinsic agreement of detected events vs gold events (precision/recall/F1 on event boundaries). Compare HDBSCAN vs an agglomerative baseline.
3. **Embedding comparison.** ≥3 models (mpnet / e5 / BGE-M3 / Greek-tuned) scored on the gold set — a clean comparative result.
4. **Classification evaluation.** Per-axis evaluation across the four axes: multi-label F1 and Jaccard similarity for Axes 1–2 (Action Form, Thematic Field); accuracy + confusion matrix for Axes 3–4 (Channel, Intensity). Compare embedding-zero-shot vs LLM-fallback per axis. Gold set annotated with all four axes.
5. **Geocoding evaluation.** % located, % correct region vs gold, error analysis.
6. **GDELT as comparator.** Compare your Greek-news event detection against GDELT's coded events over the same window — the defensible *research* use of GDELT.
7. **Reproducibility.** Every figure regenerable from a `pipeline_runs` snapshot + a notebook. Ollama path = no API keys needed to reproduce.

All of the above live in versioned notebooks under `notebooks/` and feed directly into the thesis evaluation chapter.

---

## 16. Security & Secrets

- Secrets only via environment / Docker secrets; **never** committed. `.env.example` documents every variable.
- API is read-only public; a Bearer token guards any admin/trigger route.
- Caddy provides automatic HTTPS (Let's Encrypt).
- Respect robots.txt / source ToS in connectors; rate-limit politely; store provenance (`raw_payload`, source, fetch time) for every record.
- PII: store only public content; no aggregation of private individuals beyond what sources publish.

---

## 17. Cost Summary

| Item | Baseline (chosen) | Notes |
|---|---|---|
| VPS | €5–12/mo | Hetzner CPX11/CPX21 class |
| Map tiles (MapTiler) | €0 dev tier | Paid tier ~€25/mo only if traffic grows |
| LLM (Groq/Gemini) | €0–~€5/mo | Free tiers + batching + caching; Ollama = €0 |
| Nominatim/PostGIS | €0 | Self-hosted in compose |
| Domain + TLS | ~€10/yr | TLS free via Caddy |
| **Total** | **~€5–15/mo** | Within "small budget"; reproducible at €0 for grading (local compose + Ollama) |

---

## 18. Phased Delivery Plan

| Phase | Deliverable | Exit criterion |
|---|---|---|
| **0. Foundations** | Repo skeleton, `uv`, Docker Compose (db/api/caddy), CI (ruff/mypy/pytest), schema migrations | `docker compose up` serves an empty typed API |
| **1. Ingestion** | News (RSS+trafilatura) + apergia.gr connectors, relevance filter, dedup by hash | Articles land in Postgres, idempotent re-runs |
| **2. NLP core** | Embeddings + HDBSCAN + dedup + event registry | Stable events with metrics in `pipeline_runs` |
| **3. Enrichment** | Zero-shot classify + LLM fallback + Nominatim/PostGIS geocode + bilingual summaries | Events fully enriched & validated in-region |
| **4. API** | `/events`, `/events/{id}`, `/stats`, `/events/geojson`, generated TS client | All endpoints tested |
| **5. Frontend** | React+TS SPA, MapLibre map, dashboard, charts, bilingual UI | Live demo: map loads, filters, event detail |
| **6. Social + official sources** | Reddit connector; curated X path (documented limits) | Digital-reaction signal present |
| **7. Evaluation** | Gold set + all metrics + GDELT comparator notebooks | Reproducible evaluation chapter |
| **8. Polish & ops** | Scheduler hardening, backups, observability, optional Prefect/deck.gl | Deployed, stable, demo-ready |

---

## Appendix A — Alternative Architectures

### A1. Queue-based services (Redis/RQ or Celery)
Separate scraper/NLP/LLM workers behind a broker.
- **Pros:** isolation, retries, a natural path to near-real-time.
- **Cons:** more services, more failure modes, more to defend — with **no driving requirement** (batch is fine). **Rejected for baseline; revisit only if real-time becomes a goal.**

### A2. Serverless / managed
Functions + managed vector DB (Pinecone/Qdrant Cloud) + managed Postgres + Vercel/Render.
- **Pros:** little ops, auto-scale.
- **Cons:** cold starts vs heavy model loading, recurring cost creep, vendor lock-in, harder to reproduce for a committee. **Rejected for baseline; documented for completeness.**

---

## Appendix B — Lessons from the Prototype (what *not* to repeat)

| Prototype pain | Root cause | This design's fix |
|---|---|---|
| Fragile persistence, weak queries | ChromaDB bolt-on metadata, no joins | Postgres + pgvector + PostGIS, real schema |
| Geocoding brittle / rate-limited | Public Nominatim + ad-hoc GeoJSON file | Self-hosted Nominatim + PostGIS + official boundaries |
| "Vibe-coded" frontend | Vanilla JS, no types, drag-everything | React + TypeScript + generated API client |
| Hard to reproduce runs | Implicit config, no run history | `pipeline_runs` config+metrics snapshots, Ollama offline path |
| GDELT noise hurting clusters | GDELT used as ingestion source | GDELT demoted to evaluation comparator |
| Heavyweight, opaque scraping | Crawl4AI/Playwright-first | trafilatura/httpx-first, Playwright only when needed |
| Hardcoded `sleep(2)`, no batching | No cost/robustness layer | Backoff, caching, batching, budget guard |
| 5 overlapping categories, poor recall | Single-label forced categorisation | Four-axis multi-label model (Action Form, Thematic Field, Channel, Intensity) |

---

*End of document.*
