# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real-time platform for detecting, classifying, and visualising social movements and civic reactions in Greece. Ingests Greek-language content from news RSS feeds and social sources, groups it into events via NLP clustering, enriches each event with a four-axis multi-label classification (Action Form, Thematic Field, Channel, Intensity), geocodes it to a Greek periphery, and summarises it bilingually (EL/EN). Visualised on a MapLibre GL JS map + dashboard.

**Architecture:** modular monolith + background worker, single VPS, Docker Compose. The worker (write path) and API (read path) are separate processes sharing a single PostgreSQL database.

## Commands

### Setup
```bash
uv sync
cp .env.example .env  # add at least one LLM API key
```

### Development (all services)
```bash
docker compose up          # db + worker + api + caddy (+ optional nominatim, ollama)
docker compose up --build  # force rebuild images
```

### Run pipeline stages independently (dev/debug)
```bash
# Apply schema migrations
uv run alembic upgrade head

# Phase 1 — Ingest: fetch → normalise → dedup by content_hash → articles table
uv run python -m ingestion.run

# Phase 2 — NLP: embed → cluster (HDBSCAN) → deduplicate → event registry
uv run python -m nlp.pipeline

# Phase 3 — Enrichment: 4-axis classify → geocode → summarise (EL+EN)
uv run python -m enrich.pipeline

# Phase 4 — API server (http://localhost:8000, docs at /docs)
uvicorn api.main:app --reload --port 8000
```

### PIPELINE_MODE (controls what the worker runs each cycle)
- `scrape_only` — ingest only (default)
- `scrape_and_nlp` — ingest + Phase 2
- `full` — ingest + Phase 2 + Phase 3 (requires LLM key)

## Architecture

```
External sources
  → Ingestion (Phase 1): fetch → normalise → dedup (content_hash) → articles table
  → NLP (Phase 2): embed (pgvector) → HDBSCAN cluster → dedupe → event registry
  → Enrichment (Phase 3): 4-axis classify → geocode (Nominatim → PostGIS) → summarise
  → PostgreSQL 16 + pgvector + PostGIS  ←→  FastAPI (Phase 4): /events, /stats, /health
  → Frontend (Phase 5): React + TypeScript + MapLibre GL JS map + dashboard
```

### Data Sources
- **Primary:** Greek news via Google News RSS (`feedparser` + `trafilatura`)
- **Official:** `apergia.gr` and union/ministry feeds (`httpx` + `selectolax`)
- **Social:** Reddit (`PRAW` OAuth); curated X/journalist handles via RSS-bridge (ToS-limited)
- **Deferred:** Instagram (no compliant API path — documented limitation)
- **Evaluation only:** GDELT (not an ingestion source; used as event-detection comparator)

### Ingestion (`ingestion/`)
- `connectors/base.py` — `SourceConnector` interface → `RawDocument` contract
- `connectors/news.py` — Google News RSS + `trafilatura` article extraction
- `connectors/official.py` — `apergia.gr` and structured feeds
- `connectors/reddit.py` — `PRAW` OAuth connector
- `filters/relevance.py` — spaCy `el_core_news_md` lemma-based pre-embedding gate (YAML keyword config)
- `run.py` — orchestrator; idempotent via `content_hash` (SHA-256 of canonical URL + title)

### NLP Pipeline (`nlp/`)
- `pipeline.py` — orchestrator; incremental per-stage processing
- `embeddings.py` — sentence-transformers (`paraphrase-multilingual-mpnet-base-v2`), stored in `pgvector`
- `clustering.py` — HDBSCAN; quality gates: `min_articles`, `min_intra_similarity`, `min_relevance`
- `deduplication.py` — cosine + time-window; marks `is_duplicate`
- `event_registry.py` — centroid cosine matching → stable `event_id` (UUID), `first_seen`/`last_seen`

### Enrichment Pipeline (`enrich/`)
- `pipeline.py` — orchestrator; reads clusters from DB, writes back enriched metadata
- `classify.py` — four-axis multi-label classification (see Classification Model below); embedding zero-shot primary, LLM fallback via `instructor` + Pydantic
- `geocode.py` — gazetteer-first → spaCy NER → LLM fallback; self-hosted Nominatim → PostGIS `ST_Contains`
- `summarize.py` — bilingual LLM summaries (`summary_el`, `summary_en`)
- `config.py` — LLM provider abstraction: Groq → Gemini → Ollama (offline/reproducible path)

### API (`api/`)
- `main.py` — FastAPI; read-only; OpenAPI docs; CORS; static frontend at `/`
- `routes/events.py` — `GET /events` (paginated, filterable by all 4 axes, region, bbox, date), `GET /events/{id}`, `GET /events/geojson`
- `routes/stats.py` — `GET /stats` (axis/region/time distributions)
- `models.py` — Pydantic models shared with pipeline (single source of truth)
- Short-TTL cache (60–300 s) + HTTP `Cache-Control`

### Frontend (`web/`)
- React + TypeScript + Vite SPA; static assets served by Caddy
- MapLibre GL JS + MapTiler vector tiles (no billing/lock-in vs Mapbox GL JS v2+)
- Charts via Recharts/Chart.js; bilingual UI via `i18next` (EL/EN toggle)
- Generated TypeScript client from OpenAPI schema — no hand-written API calls

## Key Configuration (`.env`)

All variables optional with sensible defaults. Commonly changed:
- `GROQ_API_KEY` / `GEMINI_API_KEY` / `OPENAI_API_KEY` — LLM provider (Groq primary)
- `LLM_MODEL` — explicit model string (auto-detected if omitted)
- `PIPELINE_MODE` — worker cycle behaviour (default: `scrape_only`)
- `CLUSTER_MIN_ARTICLES=3`, `CLUSTER_MIN_INTRA_SIM=0.78` — HDBSCAN quality gates
- `DATABASE_URL` — Postgres connection string (default: Docker Compose `db` service)
- `NOMINATIM_URL` — self-hosted Nominatim base URL

## Data Storage

Single datastore: **PostgreSQL 16 + `pgvector` + `PostGIS`** (schema managed by Alembic)

Core tables:
- `articles` — raw ingested documents; `embedding vector(768)`; `content_hash unique` for idempotency
- `events` — detected events; four classification axis columns; `primary_location geography(Point,4326)`
- `event_locations` — multi-location sub-events
- `pipeline_runs` — per-cycle `config_snapshot` + `metrics` jsonb (reproducibility backbone)

## Classification Model (Four-Axis Multi-Label)

Each event is labelled independently across four axes — not forced into a single category:

| Axis | Type | Values |
|---|---|---|
| **Axis 1 — Action Form** | multi-label | Διαδήλωση/Πορεία/Συγκέντρωση · Απεργία/Στάση εργασίας · Κατάληψη · Αποκλεισμός/Μπλόκο · Μποϊκοτάζ · Διαδικτυακή εκστρατεία · Whistleblowing · Αποχή |
| **Axis 2 — Thematic Field** | multi-label | Εργασιακό · Πολιτικό/Θεσμικό · Οικονομικό · Περιβαλλοντικό · Δικαιώματα/Κοινωνικό · Εκπαίδευση · Αστυνομική Βία · Άλλο |
| **Axis 3 — Channel** | single | Φυσικό (offline) · Ψηφιακό (online) · Υβριδικό |
| **Axis 4 — Intensity** | ordinal | Ειρηνική → Διαταρακτική (μη βίαιη, παρεμποδιστική) → Βίαιη/Συγκρουσιακή |

Schema columns: `action_forms text[]`, `thematic_fields text[]`, `channel text`, `intensity text`, `classification_confidence jsonb`.

Primary path: embedding zero-shot, no LLM tokens. LLM fallback (all axes) via `instructor` + Pydantic structured output, cached by `event_id + content_hash`.
