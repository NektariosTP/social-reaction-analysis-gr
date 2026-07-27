"""One-shot repair of events_todo.jsonl: lift trailing `#` notes into fields,
fix the unquoted-region typo, normalize region codes to canonical English.
Does NOT set is_event or fill coordinates — those are manual (see plan Task 2)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.gold_common import _DEC, GREEK_TO_EN_REGION, _skip_ws  # noqa: E402

SRC = Path("tests/fixtures/gold/events_todo.jsonl")
# Quote a bare unquoted region value (line 19: `"true_region_code": Attica`),
# but never the JSON literals null/true/false (those are valid, not typos).
_UNQUOTED_REGION = re.compile(
    r'("true_region_code":\s*)'
    r'(?!null[,}\s]|true[,}\s]|false[,}\s])'
    r'([A-Za-zΑ-Ωα-ω][^",}]*?)(\s*[,}])'
)
_SAME_AS = re.compile(r"[Ss]ame as ([0-9a-f-]{8,})")

def _requote(m: re.Match[str]) -> str:
    return f'{m.group(1)}"{m.group(2).strip()}"{m.group(3)}'

def _normalize_region(v):
    if v is None:
        return None
    if isinstance(v, list):
        return [GREEK_TO_EN_REGION.get(x, x) for x in v]
    return GREEK_TO_EN_REGION.get(v, v)

def repair() -> None:
    out_lines: list[str] = []
    for line in SRC.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        # fix bare unquoted region value (line 19: `"true_region_code": Attica`)
        fixed = _UNQUOTED_REGION.sub(_requote, line)
        start = _skip_ws(fixed, 0)
        obj, end = _DEC.raw_decode(fixed, start)
        rest = fixed[end:].strip()
        if rest.startswith("#"):
            note = rest.lstrip("#").strip()
            obj["notes"] = note
            merges = _SAME_AS.findall(note)
            if merges:
                obj["should_merge_with"] = merges
        obj["true_region_code"] = _normalize_region(obj.get("true_region_code"))
        out_lines.append(json.dumps(obj, ensure_ascii=False))
    SRC.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"repaired {len(out_lines)} records in {SRC}")

if __name__ == "__main__":
    repair()
