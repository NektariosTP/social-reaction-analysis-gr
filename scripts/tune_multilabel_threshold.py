"""Cache raw per-label NLI scores across events.jsonl once, then:
  - report per-event intensity (single-label, argmax — not threshold-tunable) errors
  - sweep _MULTILABEL_THRESHOLD for action_forms/thematic_fields against the cache

The NLI pass (~1hr on 2 CPU cores, same cost as eval_classify.py) runs at most once;
results are cached to scripts/.nli_raw_scores_cache.json so re-sweeping thresholds
is instant. Delete the cache file to force a fresh NLI pass. Do NOT hardcode the
winning threshold elsewhere; copy it into enrich/classify.py _MULTILABEL_THRESHOLD.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from enrich.classify import (  # noqa: E402
    AXIS_ACTION_FORMS,
    AXIS_CHANNEL,
    AXIS_INTENSITY,
    AXIS_THEMATIC_FIELDS,
    _HYPOTHESIS_TEMPLATES,
    _MULTILABEL_MAX,
)
from enrich.nli import classify_axis  # noqa: E402
from scripts.gold_common import load_jsonl, multilabel_prf, normalize_label  # noqa: E402

CACHE_PATH = Path("scripts/.nli_raw_scores_cache.json")

_AXES = {
    "action_forms": (AXIS_ACTION_FORMS, True),
    "thematic_fields": (AXIS_THEMATIC_FIELDS, True),
    "channel": (AXIS_CHANNEL, False),
    "intensity": (AXIS_INTENSITY, False),
}


def _to_set(v) -> set:
    if v is None:
        return set()
    items = v if isinstance(v, list) else [v]
    return {normalize_label(x) for x in items}


def compute_or_load_cache() -> dict:
    if CACHE_PATH.exists():
        print(f"[cache] loading {CACHE_PATH}")
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    recs = [r for r in load_jsonl(Path("tests/fixtures/gold/events.jsonl")) if r.get("is_event")]
    cache: dict = {}
    for i, r in enumerate(recs):
        text = " ".join(r["article_titles"]) + " " + " ".join(r["article_bodies"])
        print(f"[nli] scoring event {i + 1}/{len(recs)}: {r['pipeline_event_id']}")
        entry = {}
        for axis, (labels, multi_label) in _AXES.items():
            entry[axis] = classify_axis(
                text, labels, multi_label=multi_label,
                hypothesis_template=_HYPOTHESIS_TEMPLATES[axis],
            )
        entry["gold"] = {axis: sorted(_to_set(r.get(axis))) for axis in _AXES}
        cache[r["pipeline_event_id"]] = entry
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[cache] wrote {CACHE_PATH}")
    return cache


def report_intensity_errors(cache: dict) -> None:
    print("\n=== intensity: per-event gold vs predicted (argmax, not threshold-tunable) ===")
    wrong = 0
    for eid, entry in cache.items():
        scores = entry["intensity"]
        pred = normalize_label(max(scores, key=scores.__getitem__))
        gold = entry["gold"]["intensity"]
        gold_label = gold[0] if gold else "(none)"
        mark = "OK " if pred in gold else "ERR"
        wrong += mark == "ERR"
        rounded = {k: round(v, 3) for k, v in scores.items()}
        print(f"[{mark}] {eid}: gold={gold_label!r} pred={pred!r} scores={rounded}")
    print(f"\n{wrong}/{len(cache)} intensity mispredictions")


def sweep_multilabel_threshold(cache: dict, axis: str, thresholds: list[float]) -> None:
    print(f"\n=== {axis}: threshold sweep (max {_MULTILABEL_MAX} labels/event) ===")
    for t in thresholds:
        pred_sets, gold_sets = [], []
        for entry in cache.values():
            ranked = sorted(entry[axis].items(), key=lambda kv: kv[1], reverse=True)
            selected = [normalize_label(lbl) for lbl, s in ranked if s >= t][:_MULTILABEL_MAX]
            if not selected:
                selected = [normalize_label(ranked[0][0])]
            pred_sets.append(set(selected))
            gold_sets.append(set(entry["gold"][axis]))
        m = multilabel_prf(pred_sets, gold_sets)
        print(f"threshold={t:.2f}  P={m['precision']:.3f}  R={m['recall']:.3f}  F1={m['f1']:.3f}")


def main() -> None:
    cache = compute_or_load_cache()
    report_intensity_errors(cache)
    sweep_multilabel_threshold(cache, "action_forms", [0.20, 0.25, 0.30, 0.35, 0.40, 0.50])
    sweep_multilabel_threshold(cache, "thematic_fields", [0.20, 0.25, 0.30, 0.35, 0.40, 0.50])


if __name__ == "__main__":
    main()
