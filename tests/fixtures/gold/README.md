# Gold-eval fixtures

Frozen, hand-labeled reference data for measuring pipeline quality (relevance
gate, clustering, classification, geocoding) against ground truth. See
`docs/nlp-geocoding-improvement-plan.md` §4 for why this exists.

## Why self-contained, not DB-referencing

`worker/archival.py` prunes `articles.body_text` to NULL 72h after an event
goes quiet. A fixture that stores only article/event IDs and re-pulls text
from the live DB would silently degrade as production data ages out. Every
file here embeds the actual labeled text inline — frozen, portable, never
re-read from the DB once written.

## Workflow

1. `uv run python scripts/export_gold_candidates.py` — pulls current candidates
   from the DB into `*_todo.jsonl` files with empty label fields.
2. Open each `*_todo.jsonl`, fill in the label fields by hand.
3. Rename the finished file to drop `_todo` (e.g. `relevance_todo.jsonl` →
   `relevance.jsonl`) — that's the frozen fixture. Never regenerate a
   finished file from the DB again.
4. Score pipeline output against the frozen fixture with a separate
   `scripts/eval_*.py` (not written yet — build once a fixture is finished).

## Files

| File | Sourced from | Label fields to fill |
|---|---|---|
| `relevance.jsonl` | random sample of stored articles | `label`: `"relevant"` \| `"noise"` |
| `clustering.jsonl` | one contiguous day/window of articles | `gold_group`: int — same number = same real-world event |
| `events.jsonl` | sampled events (weighted toward known hard cases: embassy protests, foreign mentions) | `action_forms`, `thematic_fields`, `channel`, `intensity`, `true_lat`, `true_lon`, `true_region_code`, `true_municipality`, `is_foreign` |

`events.jsonl` covers both the classification and geocoding metrics from
§4 in one file — same event sample, one reading pass per event is more
practical than labeling twice from two separate exports.

## Known caveat: relevance sampling

`ingestion/run.py` only stores articles that already passed the keyword
relevance gate (`filters/relevance.py`) — rejected candidates are discarded,
never inserted. So a DB sample is skewed almost entirely "relevant"; there
are currently no true noise examples sitting in the database to sample.
To get real noise examples for the gold set, either temporarily log rejected
candidates in the relevance filter during a labeling run, or manually source
known noise (sports/gossip/TV) headlines by hand.
