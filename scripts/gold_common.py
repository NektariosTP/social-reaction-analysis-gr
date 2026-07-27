"""Shared helpers for gold-eval scoring: tolerant JSONL loader, region vocab, validators."""
from __future__ import annotations

from json import JSONDecoder
from pathlib import Path

_DEC = JSONDecoder()

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
