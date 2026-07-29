# NLP/Geocoding — Gold-Eval Scorecard

Before/after numbers for the enrichment & geocoding improvement work, scored
against the frozen fixtures in `tests/fixtures/gold/` via `scripts/eval_*.py`.
One column per landed milestone. See
`docs/superpowers/plans/2026-07-27-enrich-geocoding-improvements.md`.

## Fixtures (frozen 2026-07-28)

- `relevance.jsonl` — 250 articles (68 relevant / 182 noise)
- `clustering.jsonl` — 307 articles, 160 gold groups (118 singletons)
- `events.jsonl` — 23 real social reactions (4 foreign, 19 domestic, 2 multi-location)
- `event_precision.jsonl` — 36 non-events (negatives)

## Scorecard

| Metric | Script | Baseline (2026-07-28) | A1 + A1b (2026-07-30) | A2 · foreign + point-in-Greece (2026-07-30) | Target / notes |
|---|---|---|---|---|---|
| **Clustering** ARI | `eval_clustering` | **0.447** | — | — | ↑ with single-pass (A4) |
| **Clustering** V-measure | `eval_clustering` | **0.929** | — | — | — |
| **Clustering** pairwise P | `eval_clustering` | **1.000** | — | — | keep high |
| **Clustering** pairwise R | `eval_clustering` | **0.291** | — | — | ↑↑ — over-fragments (254 pred vs 160 gold) |
| **Clustering** pairwise F1 | `eval_clustering` | **0.450** | — | — | ↑ with A4 |
| **Geocode** region accuracy | `eval_geocode` | **0.000** (0/17) | **~0.53–0.67** (noisy) | **0.789** (15/19) | ↑; 4 misses are the national/venueless class → A5 target |
| **Geocode** median distance err | `eval_geocode` | **112.6 km** (n=17) | **2.6 km** (successful pins) | **3.2 km** (n=19) | venue-level, full domestic coverage |
| **Geocode** foreign P / R / F1 | `eval_geocode` | **0.50 / 0.50 / 0.50** | **0.75 / 0.75 / 0.75** | **1.00 / 1.00 / 1.00** | A2 goal met — point-in-Greece + is_foreign; all 4 foreign detected, no domestic misflagged |
| **Event-precision** | `eval_geocode` | **0.390** (23 real / 59) | **0.390** | **0.390** | unchanged — detection untouched; ↑ after M5 (NLI noise gate) |
| **Relevance** P / R / F1 | `eval_relevance` | **0.275 / 1.000 / 0.432** | — | — | ↑↑ precision after M5 — gate passes 179/182 noise (tp=68 fp=179 tn=3 fn=0) |
| **Classify** action_forms | `eval_classify` | **0.537 / 0.879 / 0.667** | — | — | cosine-to-label; weak precision (M5) |
| **Classify** thematic_fields | `eval_classify` | **0.532 / 0.758 / 0.625** | — | — | ↑ after M5 (NLI) |
| **Classify** channel | `eval_classify` | **0.043 / 0.043 / 0.043** | — | — | broken: 1/23 correct — *worse than majority-class* (all gold = Φυσικό → trivial predictor scores 1.0). Cosine-to-label fails here; top M5 target |
| **Classify** intensity | `eval_classify` | **0.913 / 0.913 / 0.913** | — | — | strong |

> **A1 + A1b — how these were captured (and two gotchas).** Numbers are the representative run: `NOMINATIM_URL=https://nominatim.openstreetmap.org GROQ_API_KEY=… LLM_MODEL=groq/llama-3.3-70b-versatile uv run python scripts/eval_geocode.py`.
> - **A1b (extraction robustness)** landed first: instructor JSON mode + salvage parser eliminated Groq's `tool_use_failed` drops, so extraction is reliable and the sample is stable (n=18 of 19 domestic-with-coords).
> - **Gotcha 1 — `NOMINATIM_URL`.** A bare `uv run …` uses the `.env` Docker hostname `http://nominatim:8080`, unreachable outside Compose → every geocode silently degrades to gazetteer-only (a deterministic `n=9 / 1.2 km / region 0.556` that must be discarded). Always override to public Nominatim for this eval.
> - **Gotcha 2 — the misses are mostly real, not the eval.** Fixed the `_first`-only region comparison (now matches the full `set(true_region_code)`), but a spot-check found only **1** multi-location artifact (`Αψίδα Γαλερίου` → Central Macedonia, 0.1 km, correct). The genuine failures are a **class the pipeline doesn't model: national / sector-wide strikes & statements with no single venue.** The geocoder then pins a spuriously-mentioned or hallucinated city (`Πανελλαδική απεργία στο εμπόριο` → Ηράκλειο, 320 km; national strike w/ one Patra headline → Πάτρα; teacher-evaluation statement → Θεσσαλονίκη gazetteer centroid) or returns nothing (5 venueless `Στάση εργασίας` events), while gold uses an organizing-HQ point (Athens/Komotini). Also one real venue-disambiguation bug (`Πλατεία Ελευθερίας, Ηράκλειο` → the Athens square). **A2 (foreign/point-in-Greece) does not address this class — it needs its own milestone (detect panhellenic scope → HQ/Attica or abstain, instead of hallucinating a venue).**
> - **Gotcha 3 — public Nominatim is non-reproducible.** Rate-limiting makes runs disagree (`12/18` then `10/19`, with 0 vs 5 no-geocodes). Trust median distance among successful pins (`~2.6 km`) over the region ratio; self-hosted Nominatim (M7) or LLM/geocode caching is a prerequisite for treating region deltas as signal.

## How the baselines were captured

- **Clustering** and **event-precision** run with no external services (sklearn +
  the frozen fixtures) — captured directly.
- **Geocode** was run with the real LLM extraction path enabled:
  `GROQ_API_KEY` (from `.env`), `LLM_MODEL=groq/llama-3.3-70b-versatile`, and
  `NOMINATIM_URL=https://nominatim.openstreetmap.org` (the `.env`'s
  `http://nominatim:8080` is the Docker service, unreachable outside Compose).
  Without the LLM key the script degrades to gazetteer-only and the numbers are
  not representative.
- **Relevance** was captured in the Docker worker image (which has spaCy +
  `el_core_news_md`), since this worktree's venv lacks the ML stack:
  `docker compose run --rm --no-deps -v "$PWD/scripts":/app/scripts
  -v "$PWD/tests":/app/tests worker .venv/bin/python scripts/eval_relevance.py`.
- **Classify** is still `_pending full env_`: run the same Docker command with
  `scripts/eval_classify.py` (downloads the ~1 GB mpnet model on first run).

## Reproduce

```bash
# no services needed
.venv/bin/python scripts/eval_clustering.py

# geocode: LLM + public Nominatim (one-off; respects Nominatim rate limits)
GROQ_API_KEY=... LLM_MODEL=groq/llama-3.3-70b-versatile \
  NOMINATIM_URL=https://nominatim.openstreetmap.org \
  .venv/bin/python scripts/eval_geocode.py

# relevance + classify: run in the Docker worker env
.venv/bin/python scripts/eval_relevance.py
.venv/bin/python scripts/eval_classify.py
```
