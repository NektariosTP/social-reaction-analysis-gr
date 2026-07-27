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
| `events.jsonl` | sampled events (weighted toward known hard cases: embassy protests, foreign mentions) | `action_forms`, `thematic_fields`, `channel`, `intensity`, `true_lat`, `true_lon`, `true_region_code`, `true_municipality`, `is_foreign`, `is_event` |
| `event_precision.jsonl` | non-events split out of the events sample during triage | negatives only (`is_event: false`) — powers the event-precision metric |

`events.jsonl` covers both the classification and geocoding metrics from
§4 in one file — same event sample, one reading pass per event is more
practical than labeling twice from two separate exports.

### `events.jsonl` schema notes (added during finalization)

- **`is_event`** (bool) — triage label: `true` = a genuine social/civic
  reaction (an action form from the model: strike, rally, march, occupation,
  blockade, boycott, abstention); `false` = noise that leaked into the
  `events` table (sports, TV, celebrity, corporate "πορεία", legal/diplomatic
  "μπλόκο" homonyms, crime, weather). Every `false` record lives in
  `event_precision.jsonl`, not here; `events.jsonl` holds only `is_event:true`.
- **`true_region_code`** — canonical English periphery name (the 13 `name`
  values in `_archive/frontend/greece-regions.geojson`), not the Greek label.
- **`notes`** (str, optional) — free-text labeler note lifted out of a trailing
  `# …` comment on the JSON line (kept out of the JSON body so the file stays
  valid JSONL).
- **`should_merge_with`** (list[str], optional) — pipeline event-ids of other
  fixture rows that refer to the *same* real-world event (the clusterer should
  have merged them). Feeds the clustering/registry metric.
- **Foreign real events** stay here with `is_foreign:true` and null coords —
  they score foreign-detection, not distance/region. **Real-but-unlocatable**
  domestic events were dropped during finalization.
- **Multi-location** events carry list-valued `true_lat`/`true_lon`/
  `true_region_code`/`true_municipality`.

## Known caveat: relevance sampling

`ingestion/run.py` only stores articles that already passed the keyword
relevance gate (`filters/relevance.py`) — rejected candidates are discarded,
never inserted. So a DB sample is skewed almost entirely "relevant"; there
are currently no true noise examples sitting in the database to sample.
To get real noise examples for the gold set, either temporarily log rejected
candidates in the relevance filter during a labeling run, or manually source
known noise (sports/gossip/TV) headlines by hand.
