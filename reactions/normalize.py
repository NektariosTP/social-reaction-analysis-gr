"""Strip feed boilerplate → clean Greek text for filtering/extraction."""
from __future__ import annotations

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
# WordPress RSS tails appended to <description>.
_TAIL_EL_RE = re.compile(r"\s*Το άρθρο .*?εμφανίστηκε.*$", re.DOTALL)
_TAIL_EN_RE = re.compile(r"\s*The post .*?appeared first on.*$", re.DOTALL)
# Leading press-release / protocol headers.
_HEADER_RE = re.compile(r"^\s*(ΔΕΛΤΙΟ ΤΥΠΟΥ|ΑΝΑΚΟΙΝΩΣΗ|Αρ\.?\s*Πρωτ\.?[^\n]*|Α\.Π\.?:?[^\n]*)\s*", re.IGNORECASE)


def clean_text(raw: str) -> str:
    if not raw:
        return ""
    txt = html.unescape(raw)
    txt = _TAG_RE.sub(" ", txt)
    txt = _TAIL_EL_RE.sub("", txt)
    txt = _TAIL_EN_RE.sub("", txt)
    txt = _WS_RE.sub(" ", txt).strip()
    txt = _HEADER_RE.sub("", txt).strip()
    return txt
