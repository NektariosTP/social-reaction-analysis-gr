"""Shared helpers for gold-eval scoring: tolerant JSONL loader, region vocab, validators."""
from __future__ import annotations

import math
import re
from itertools import combinations
from json import JSONDecoder
from pathlib import Path

_DEC = JSONDecoder()

# Classifier axis vocabularies carry parenthetical annotations
# ("Φυσικό (offline)", "Διαταρακτική") that gold
# labels sometimes omit. Strip a trailing "(...)" so comparison is on the
# canonical label, not its annotation style.
_TRAILING_PAREN = re.compile(r"\s*\([^)]*\)\s*$")


def normalize_label(label: str) -> str:
    """Drop a trailing parenthetical annotation and surrounding whitespace."""
    return _TRAILING_PAREN.sub("", label).strip()

REGION_NAMES = frozenset({
    "East Macedonia and Thrace", "Central Macedonia", "West Macedonia", "Epirus",
    "Thessaly", "Ionian Islands", "Western Greece", "Central Greece", "Attica",
    "Peloponnese", "North Aegean", "South Aegean", "Crete",
})

GREEK_TO_EN_REGION = {
    "Ανατολική Μακεδονία και Θράκη": "East Macedonia and Thrace",
    "Κεντρική Μακεδονία": "Central Macedonia",
    "Δυτική Μακεδονία": "West Macedonia",
    "Ήπειρος": "Epirus",
    "Θεσσαλία": "Thessaly",
    "Ιόνια Νησιά": "Ionian Islands",
    "Δυτική Ελλάδα": "Western Greece",
    "Κεντρική Ελλάδα": "Central Greece",
    "Αττική": "Attica",
    "Πελοπόννησος": "Peloponnese",
    "Περιφέρεια Πελοποννήσου": "Peloponnese",
    "Βόρειο Αιγαίο": "North Aegean",
    "Νότιο Αιγαίο": "South Aegean",
    "Κρήτη": "Crete",
}

def _skip_ws(s: str, i: int) -> int:
    while i < len(s) and s[i] in " \t\r\n":
        i += 1
    return i

def load_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        start = _skip_ws(line, 0)
        obj, end = _DEC.raw_decode(line, start)
        rest = line[end:].strip()
        if rest.startswith("#"):
            obj["_trailing_note"] = rest.lstrip("#").strip()
        out.append(obj)
    return out

def _as_list(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]

def validate_events(records: list[dict]) -> list[str]:
    violations: list[str] = []
    for r in records:
        eid = r.get("pipeline_event_id", "?")
        if "is_event" not in r:
            violations.append(f"{eid}: missing is_event")
        for code in _as_list(r.get("true_region_code")):
            if code not in REGION_NAMES:
                violations.append(f"{eid}: non-canonical region_code {code!r}")
        if r.get("is_event") is True and not r.get("is_foreign"):
            if not r.get("action_forms") or not r.get("thematic_fields"):
                violations.append(f"{eid}: real domestic event missing axis labels")
    return violations


def binary_prf(tp: int, fp: int, fn: int) -> dict[str, float]:
    """Compute binary classification precision, recall, and F1.

    Args:
        tp: True positives
        fp: False positives
        fn: False negatives

    Returns:
        Dictionary with keys "precision", "recall", "f1" (float values 0.0-1.0).
    """
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def pairwise_f1(pred: list[int], gold: list[int]) -> dict[str, float]:
    """Compute pairwise F1 for clustering.

    Measures precision/recall/F1 over co-membership pairs: (i, j) pairs where
    pred[i] == pred[j] or gold[i] == gold[j].

    Args:
        pred: Predicted cluster labels
        gold: Gold standard cluster labels

    Returns:
        Dictionary with keys "precision", "recall", "f1" (float values 0.0-1.0).
    """
    assert len(pred) == len(gold)
    idx = range(len(pred))
    pred_pairs = {(i, j) for i, j in combinations(idx, 2) if pred[i] == pred[j]}
    gold_pairs = {(i, j) for i, j in combinations(idx, 2) if gold[i] == gold[j]}
    tp = len(pred_pairs & gold_pairs)
    return binary_prf(tp, len(pred_pairs) - tp, len(gold_pairs) - tp)


def multilabel_prf(pred: list[set], gold: list[set]) -> dict[str, float]:
    """Compute micro-averaged precision/recall/F1 for multi-label classification.

    Args:
        pred: List of predicted label sets
        gold: List of gold-standard label sets

    Returns:
        Dictionary with keys "precision", "recall", "f1" (float values 0.0-1.0).
    """
    tp = fp = fn = 0
    for p, g in zip(pred, gold, strict=True):
        tp += len(p & g)
        fp += len(p - g)
        fn += len(g - p)
    return binary_prf(tp, fp, fn)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in km.

    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees

    Returns:
        Distance in kilometers
    """
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))
