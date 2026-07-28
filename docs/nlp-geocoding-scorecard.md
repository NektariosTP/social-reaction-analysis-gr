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

| Metric | Script | Baseline (2026-07-28) | Target / notes |
|---|---|---|---|
| **Clustering** ARI | `eval_clustering` | **0.447** | ↑ with single-pass (A4) |
| **Clustering** V-measure | `eval_clustering` | **0.929** | — |
| **Clustering** pairwise P | `eval_clustering` | **1.000** | keep high |
| **Clustering** pairwise R | `eval_clustering` | **0.291** | ↑↑ — over-fragments (254 pred vs 160 gold) |
| **Clustering** pairwise F1 | `eval_clustering` | **0.450** | ↑ with A4 |
| **Geocode** region accuracy | `eval_geocode` | **0.000** (0/17) | → ~high after M1 (region_code is a dead path today) |
| **Geocode** median distance err | `eval_geocode` | **112.6 km** (n=17) | ↓↓ after M1/M2 (mis-pin fix) |
| **Geocode** foreign P / R / F1 | `eval_geocode` | **0.50 / 0.50 / 0.50** | ↑ after M2 (point-in-Greece + is_foreign) |
| **Event-precision** | `eval_geocode` | **0.390** (23 real / 59) | ↑ after M5 (NLI noise gate) |
| **Relevance** P / R / F1 | `eval_relevance` | **0.275 / 1.000 / 0.432** | ↑↑ precision after M5 — gate passes 179/182 noise (tp=68 fp=179 tn=3 fn=0) |
| **Classify** action_forms | `eval_classify` | **0.537 / 0.879 / 0.667** | cosine-to-label; weak precision (M5) |
| **Classify** thematic_fields | `eval_classify` | **0.532 / 0.758 / 0.625** | ↑ after M5 (NLI) |
| **Classify** channel | `eval_classify` | **0.043 / 0.043 / 0.043** | broken: 1/23 correct — *worse than majority-class* (all gold = Φυσικό → trivial predictor scores 1.0). Cosine-to-label fails here; top M5 target |
| **Classify** intensity | `eval_classify` | **0.913 / 0.913 / 0.913** | strong |

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
