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

# Latin → Greek confusable homoglyphs. Applied ONLY inside a token that already contains
# a Greek letter, so pure-Latin words (English, acronyms) are never corrupted.
_LAT2GRK = str.maketrans({
    "A": "Α", "B": "Β", "E": "Ε", "Z": "Ζ", "H": "Η", "I": "Ι", "K": "Κ",
    "M": "Μ", "N": "Ν", "O": "Ο", "P": "Ρ", "T": "Τ", "X": "Χ", "Y": "Υ",
    "a": "α", "e": "ε", "o": "ο", "i": "ι", "k": "κ", "n": "ν", "p": "ρ",
    "t": "τ", "x": "χ", "y": "υ", "u": "υ", "v": "ν",
})
_GREEK_RE = re.compile(r"[Α-Ωα-ωΆ-ώΐ-ΰ]")
_TOKEN_RE = re.compile(r"\S+")


def _defang_homoglyphs(txt: str) -> str:
    def _fix(m: "re.Match[str]") -> str:
        tok = m.group(0)
        return tok.translate(_LAT2GRK) if _GREEK_RE.search(tok) else tok
    return _TOKEN_RE.sub(_fix, txt)


def clean_text(raw: str) -> str:
    if not raw:
        return ""
    txt = html.unescape(raw)
    txt = _TAG_RE.sub(" ", txt)
    txt = _defang_homoglyphs(txt)
    txt = _TAIL_EL_RE.sub("", txt)
    txt = _TAIL_EN_RE.sub("", txt)
    txt = _WS_RE.sub(" ", txt).strip()
    txt = _HEADER_RE.sub("", txt).strip()
    return txt
