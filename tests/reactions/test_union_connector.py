from pathlib import Path

from ingestion.connectors.union import ReactionItem, parse_feed, load_union_sources

RAW = Path("tests/reactions/fixtures/genop_sample.xml").read_bytes()


def test_parse_feed_yields_reaction_items():
    items = parse_feed("genop_dei", "ΓΕΝΟΠ/ΔΕΗ", RAW)
    assert items, "expected at least one item"
    first = items[0]
    assert isinstance(first, ReactionItem)
    assert first.source_org == "genop_dei"
    assert first.actor_name == "ΓΕΝΟΠ/ΔΕΗ"
    assert first.url.startswith("http")
    assert first.title
    assert first.observed_at is None or first.observed_at.tzinfo is not None


def test_load_union_sources_has_five_ready_feeds():
    sources = load_union_sources()
    slugs = {s["org_slug"] for s in sources if s.get("tier") == "ready"}
    assert {"genop_dei", "pame", "adedy", "poedhn", "oikodomon"} <= slugs
    for s in sources:
        assert s["feed_format"] in {"rss", "atom"}
