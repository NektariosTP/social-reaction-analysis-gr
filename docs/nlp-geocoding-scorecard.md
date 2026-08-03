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

| Metric | Script | Baseline (2026-07-28) | A1 + A1b (2026-07-30) | A2 · foreign + point-in-Greece (2026-07-30) | A3 · centroid running-mean + SQL match (2026-07-30) | A4 · single-pass clustering τ=0.72 (2026-07-30) ⚠️ in-sample | A5 · panhellenic-scope, no HQ fallback (2026-08-03) | B1 · NLI classifier + noise gate (2026-08-04) | Target / notes |
|---|---|---|---|---|---|---|---|---|---|
| **Clustering** ARI | `eval_clustering` | **0.447** | — | — | **0.447** | **0.879** | — | — | ↑ with single-pass — **met (A4)** |
| **Clustering** V-measure | `eval_clustering` | **0.929** | — | — | **0.929** | **0.978** | — | — | ↑ (A4) |
| **Clustering** pairwise P | `eval_clustering` | **1.000** | — | — | **1.000** | **0.952** | — | — | keep high — small dip, big R gain (A4) |
| **Clustering** pairwise R | `eval_clustering` | **0.291** | — | — | **0.291** | **0.819** | — | — | ↑↑ **met** — over-fragmentation fixed (170 pred vs 160 gold, was 254) (A4) |
| **Clustering** pairwise F1 | `eval_clustering` | **0.450** | — | — | **0.450** | **0.881** | — | — | ↑ **met (A4)** |
| **Geocode** region accuracy | `eval_geocode` | **0.000** (0/17) | **~0.53–0.67** (noisy) | **0.789** (15/19) | — | — | **0.750** (12/16) | **0.750** (12/16) | ↑; 4 misses are the national/venueless class → A5 target |
| **Geocode** median distance err | `eval_geocode` | **112.6 km** (n=17) | **2.6 km** (successful pins) | **3.2 km** (n=19) | — | — | **2.9 km** (n=16) | **2.9 km** (n=16) | venue-level, full domestic coverage |
| **Geocode** foreign P / R / F1 | `eval_geocode` | **0.50 / 0.50 / 0.50** | **0.75 / 0.75 / 0.75** | **1.00 / 1.00 / 1.00** | — | — | **1.00 / 1.00 / 1.00** | **1.00 / 1.00 / 1.00** | A2 goal met — point-in-Greece + is_foreign; all 4 foreign detected, no domestic misflagged |
| **Event-precision** P / R / F1 | `eval_geocode` | **0.390** (23 real / 59) | **0.390** | **0.390** | — | — | **0.390** | **0.590 / 1.000 / 0.742** (tp=23 fp=16 fn=0) | ↑ **met (B1)** — real noise gate replaces the placeholder formula; zero real events lost (R=1.0), 16/36 non-events still slip through |
| **Relevance** P / R / F1 | `eval_relevance` | **0.275 / 1.000 / 0.432** | — | — | — | — | — | — | ↑↑ precision after M5 — gate passes 179/182 noise (tp=68 fp=179 tn=3 fn=0) |
| **Classify** action_forms | `eval_classify` | **0.537 / 0.879 / 0.667** | — | — | — | — | — | **0.431 / 0.848 / 0.571** | NLI (B1) *regressed* F1 0.667→0.571 despite `_MULTILABEL_THRESHOLD` recalibration (0.35→0.50) — see B1 note |
| **Classify** thematic_fields | `eval_classify` | **0.532 / 0.758 / 0.625** | — | — | — | — | — | **0.429 / 0.727 / 0.539** | NLI (B1) *regressed* F1 0.625→0.539 — see B1 note |
| **Classify** channel | `eval_classify` | **0.043 / 0.043 / 0.043** | — | — | — | — | — | **0.435 / 0.435 / 0.435** | NLI (B1) **met** — 10x improvement, fixes the broken cosine-to-label primary (was worse than majority-class) |
| **Classify** intensity | `eval_classify` | **0.913 / 0.913 / 0.913** | — | — | — | — | — | **0.696 / 0.696 / 0.696** | NLI (B1) *regressed* F1 0.913→0.696 (7/23 wrong) — investigated, not fixed; see B1 note |

> **A1 + A1b — how these were captured (and two gotchas).** Numbers are the representative run: `NOMINATIM_URL=https://nominatim.openstreetmap.org GROQ_API_KEY=… LLM_MODEL=groq/llama-3.3-70b-versatile uv run python scripts/eval_geocode.py`.
> - **A1b (extraction robustness)** landed first: instructor JSON mode + salvage parser eliminated Groq's `tool_use_failed` drops, so extraction is reliable and the sample is stable (n=18 of 19 domestic-with-coords).
> - **Gotcha 1 — `NOMINATIM_URL`.** A bare `uv run …` uses the `.env` Docker hostname `http://nominatim:8080`, unreachable outside Compose → every geocode silently degrades to gazetteer-only (a deterministic `n=9 / 1.2 km / region 0.556` that must be discarded). Always override to public Nominatim for this eval.
> - **Gotcha 2 — the misses are mostly real, not the eval.** Fixed the `_first`-only region comparison (now matches the full `set(true_region_code)`), but a spot-check found only **1** multi-location artifact (`Αψίδα Γαλερίου` → Central Macedonia, 0.1 km, correct). The genuine failures are a **class the pipeline doesn't model: national / sector-wide strikes & statements with no single venue.** The geocoder then pins a spuriously-mentioned or hallucinated city (`Πανελλαδική απεργία στο εμπόριο` → Ηράκλειο, 320 km; national strike w/ one Patra headline → Πάτρα; teacher-evaluation statement → Θεσσαλονίκη gazetteer centroid) or returns nothing (5 venueless `Στάση εργασίας` events), while gold uses an organizing-HQ point (Athens/Komotini). Also one real venue-disambiguation bug (`Πλατεία Ελευθερίας, Ηράκλειο` → the Athens square). **A2 (foreign/point-in-Greece) does not address this class — it needs its own milestone (detect panhellenic scope → HQ/Attica or abstain, instead of hallucinating a venue).**
> - **Gotcha 3 — public Nominatim is non-reproducible.** Rate-limiting makes runs disagree (`12/18` then `10/19`, with 0 vs 5 no-geocodes). Trust median distance among successful pins (`~2.6 km`) over the region ratio; self-hosted Nominatim (M7) or LLM/geocode caching is a prerequisite for treating region deltas as signal.

> **A3 — no-regression gate (identical to baseline is the *correct* result here).** A3 is a registry determinism/drift fix in `nlp/event_registry.py` (`assign_event_id`: SQL nearest-match + `article_count`-weighted running-mean centroid) that runs against the **live DB**, not the frozen fixture. `eval_clustering.py` in its **default mode reads the frozen `pipeline_event_id`** stored in `clustering.jsonl` and scores it with sklearn — **no Nominatim, no LLM, no DB**, so no registry change *can* move the number. The run reproduced `n=307 / gold_groups=160 / pred_groups=254` (the same over-fragmentation the baseline recorded), confirming the fixture was really loaded and scored — not a silent degrade. This is unlike the A2 `NOMINATIM_URL` gotcha, which affected `eval_geocode.py`'s real Nominatim call; the clustering baseline eval has no such external dependency. Captured `2026-07-30` (deferred from the A3 landing due to a token limit) via `uv run python scripts/eval_clustering.py` at commit `bd0e85f`.
>
> **A4 — single-pass incremental clustering (τ=0.72).** First column that actually re-clusters the fixture: `uv run python scripts/eval_clustering.py --single-pass` embeds each fixture article with mpnet and groups via `single_pass_cluster` at the τ chosen by `scripts/tune_tau.py`. Over-fragmentation collapses (254→**170** predicted groups vs 160 gold): pairwise **R 0.291→0.819**, **F1 0.450→0.881**, **ARI 0.447→0.879**, **V-measure 0.929→0.978**, at a small precision cost (**P 1.000→0.952**). No external services — sklearn + mpnet over the frozen fixture, reproducible.
>
> ⚠️ **These A4 numbers are in-sample (optimistic).** τ=0.72 was selected by `tune_tau.py` to **maximize pairwise-F1 on `clustering.jsonl`**, then scored on the same fixture — train-on-test. The HDBSCAN baseline column was *not* tuned on this fixture (it's live-production `pipeline_event_id`), so part of the F1 jump is A4's tuning advantage, not pure algorithm. The τ-surface is a **narrow peak, not a plateau** (F1 by τ: 0.70→0.741, **0.72→0.881**, 0.74→0.868, 0.76→0.763, then ↓ to 0.23 by 0.90), so a held-out τ plausibly scores ~0.10–0.14 F1 lower. Read **0.881 as an upper bound**; the *direction* (≫ baseline 0.450) is robust — even the worst adjacent τ (0.741) beats it. A proper estimate needs a held-out / k-fold τ selection, blocked on there being no second labeled clustering fixture.

> **A5 — how this column was captured.** A5 makes domestic national-scope-no-venue events correctly return `[]` instead of pinning a stray/hallucinated city (e.g. `Πανελλαδική απεργία στο εμπόριο` no longer forces a guess between Ηράκλειο/Θεσσαλονίκη/Κέρκυρα/Βόλος). Validating it surfaced two bugs, both fixed before this column was recorded:
> - `eval_geocode.py`'s `pred_foreign = (primary is None) or is_foreign` treated *any* empty result as "predicted foreign" — harmless pre-A5 (every domestic event got some pin) but wrong now that A5 legitimately empties some domestic results. Fixed to `pred_foreign = primary is not None and is_foreign`.
> - `has_venue` originally required the LLM's `venue` field, so it wrongly suppressed a *correct* single-city hit (Κοζάνη ΚΕΠ office, a national campaign's one genuinely-locatable local instance) alongside the truly ambiguous multi-city cases. Loosened to also trust a single unambiguous mention: `has_venue = any(m.venue) or len(mentions) == 1`.
>
> Four full `eval_geocode.py` runs this session swung wildly (region_accuracy 0.714/0.800/0.692/0.733, n=7/15/13/15; median distance 1.2/2.6/9.4/3.2 km; foreign F1 0.000/0.857/0.667/0.857) — two of the four logged Groq/LiteLLM errors mid-run, i.e. this session hit real API rate/token limits from repeated back-to-back diagnostic calls, unrelated to A5's own logic. The table above instead reports one **clean, isolated single-pass trace** (no concurrent load, no API errors) scored against gold: `n=16` domestic events with a pin (of 19 total domestic), all 4 foreign events correctly flagged. Of the 3 domestic events with no pin, 2 are the intended abstentions (`41f3d6dd`, `6b723b5b` — genuinely ambiguous multi-city mentions); the third (`b38ecdcc`) also returned empty but wasn't traced for `national`/`has_venue` in this pass, so whether it's a third correct abstention or an unrelated miss is **not yet confirmed** — worth checking before treating `region_accuracy` as final. Same Gotcha 3 caveat as A1/A2 applies: this is one run, not a guaranteed-reproducible number.

> **B1 — NLI zero-shot classifier + noise gate: a mixed result, not a clean win.** `enrich/nli.py` replaces the cosine-embedding primary with `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` zero-shot NLI (22 forward passes/event: 8+8+3+3 labels across the four axes). Two calibrated constants: `NOISE_GATE_THRESHOLD=0.55` (from `scripts/tune_noise_gate.py`, highest-precision point in the zero-false-negative band) and `_MULTILABEL_THRESHOLD=0.50` (from `scripts/tune_multilabel_threshold.py`, run 2026-08-04 against the frozen `events.jsonl`).
>
> **Only two of the four target metrics actually improved.** `channel` — previously broken (0.043, worse than the trivial always-`Φυσικό` predictor) — is fixed (0.435, 10x). `event-precision` gained a real, gated measurement (P=0.590/R=1.000/F1=0.742) in place of the old placeholder formula. But `action_forms`, `thematic_fields`, and `intensity` all **regressed** in absolute F1 versus the cosine baseline, even after threshold recalibration — NLI entailment scores are simply not better-calibrated than cosine similarity for these three axes on this gold set.
>
> **`_MULTILABEL_THRESHOLD` calibration (`tune_multilabel_threshold.py`):** swept 0.20→0.90 using cached raw per-label scores (one NLI pass, ~1h47m on this 2-core/no-usable-GPU box — see hardware note below). Raw max-F1 peaked at threshold=0.99 (action_forms F1=0.627) with a cliff at 1.00 — treated as **overfit to n=23 events**, not adopted (same in-sample caution as A4's τ, [[project_a4_tau_in_sample]]). **0.50 was chosen instead**: the first point in the swept range where both `action_forms` and `thematic_fields` beat the 0.35 default, without chasing a razor-edge value.
>
> **Intensity regression (0.913→0.696) was investigated, not fixed.** It's single-label argmax (`_top_single`, no threshold involved), so `_MULTILABEL_THRESHOLD` tuning cannot touch it. Root cause: 6 of 7 errors are gold=`Ειρηνική` (peaceful) misclassified as `Διαταρακτική`/`Βίαιη` — article text about peaceful protests still contains conflict-adjacent vocabulary (police, tension) that the model reads as entailing higher intensity. Three fix attempts, all against the cached scores or a cheap intensity-only rerun (~15min each, since only 3 labels/event need rescoring):
> 1. **Lower-intensity tie-break** (prefer the less-severe label when top-2 scores are within a margin, since intensity is ordinal): best margin=0.05 → 17/23 (0.739), but fragile — net +1 correct (fixes 2 near-ties, breaks 1 previously-correct near-tie), and doesn't touch the 4 confidently-wrong (non-close) predictions that drive most of the loss.
> 2. **Reworded hypothesis template** (anchor on "the action itself, not the broader context"): 13/23 (0.565) — worse, and shifted the bias toward over-predicting `Διαταρακτική` as a catch-all instead of fixing it.
> 3. **Simplified single-word candidate labels** (drop the compound `"Διαταρακτική (μη βίαιη, παρεμποδιστική)"` / `"Βίαιη/Συγκρουσιακή"` phrasing): 13/23 (0.565) after correcting a same-session test-script bug (comparing `"Βίαιη"` against the unstripped gold string) — tied with attempt 2.
>
> Two independent interventions converging on the identical 0.565 score is a stronger signal than either alone: this isn't sensitive to prompt wording, it's the model conflating conflict-adjacent vocabulary with event intensity regardless of framing. Per systematic-debugging practice (3+ failed fixes on the same symptom ⇒ likely architectural, not tunable), stopped iterating. **Production code is unchanged from the original template/labels** — none of the three attempts were adopted. A real fix would need a different model or classifying on a curated summary instead of raw article text; out of scope for B1, tracked as a known limitation.
>
> **Hardware note (why this took so long):** this box has only 2 CPU cores and no usable GPU — `torch.cuda.is_available()` reports `True` (a GTX 1050 Ti is present) but the installed `torch 2.12.1+cu130` build only ships kernels for sm_75+ (Turing and newer); the 1050 Ti is sm_61 (Pascal) and throws `no kernel image is available for execution on the device` on any real op. All NLI inference in B1 ran CPU-only. A full `eval_classify.py` pass (506 forward passes) took ~56–60 min solo, ~1h47m when contending with a concurrent `eval_geocode.py` run (RAM is also tight — 5.8GB total, swap activity observed during the overlap).

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
- **Classify** (from B1 onward) runs directly in this worktree's venv —
  `transformers` + the `mDeBERTa-v3-base-mnli-xnli` NLI model are now direct
  dependencies (`uv run python scripts/eval_classify.py`, downloads the
  ~560 MB model on first run). No Docker needed for this one; see the B1
  hardware note above for why it's slow (~1hr on a 2-core CPU-only box).

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
