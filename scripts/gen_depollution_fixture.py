"""One-off: build the de-pollution eval fixture from live event c4f30e75.
Gold event-day is assigned by an INDEPENDENT rule (host + explicit keyword),
not by the resolver under test. Run once; the .jsonl is committed."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

_URL = "http://129.152.2.199/events/c4f30e75-66fd-4e55-af5e-28a4005d5f30"
_OUT = Path(__file__).parent.parent / "tests" / "nlp" / "fixtures" / "depollution_c4f30e75.jsonl"
# Cypriot sources whose 17/9 "Πέμπτη" strike pollutes the 16/9 Greek cluster.
_CY_HOSTS = {"cna.org.cy", "sigmalive.com", "economytoday.sigmalive.com",
             "philenews.com", "ant1live.com"}


def _gold_day(host: str, title: str) -> str | None:
    t = title.lower()
    if "30 σεπτεμ" in t or "30/9" in t:
        return "2026-09-30"
    if host in _CY_HOSTS:
        return "2026-09-17"  # Cyprus ωρομίσθιοι, Thursday 17/9
    if "16 σεπτεμ" in t or "16/9" in t or "την τετάρτη" in t:
        return "2026-09-16"
    return None  # unlabelled → invariant-only, excluded from precision/recall


def main() -> None:
    data = json.load(urllib.request.urlopen(_URL))  # noqa: S310 (trusted internal host)
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    with _OUT.open("w", encoding="utf-8") as fh:
        for a in data["articles"]:
            host = a["url"].split("/")[2].replace("www.", "")
            fh.write(json.dumps({
                "id": a["id"],
                "title": a["title"],
                "published_at": a["published_at"],
                "gold_event_day": _gold_day(host, a["title"]),
            }, ensure_ascii=False) + "\n")
    print(f"wrote {_OUT}")


if __name__ == "__main__":
    main()
