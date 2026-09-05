"""Log parsing and precision, both pure — no Ollama, no network."""

from fenix.rate import parse_scans, precision_at_k

LOG = """# Signals log

## Scan — 2026-08-15T07:38+00:00

### Latent Space

- [An unscored item](https://example.com/a) — Fri, 14 Aug 2026 05:30:39 GMT

## Scan — 2026-09-05T06:09+00:00
(2 new item(s) this run)

### target_role (job-search, ai-initiative)
`ab12cd34` · nomic-embed-text · 3,412 chars · max 0.686 · median 0.600 · min 0.600

- **0.686** [Lovable CTO: The Future of SaaS](https://example.com/b) — Latent Space, Wed, 26 Aug 2026 16:16:25 GMT
- **0.600** [[AINews] Andrew Ng gets into AI Engineering](https://example.com/c) — Latent Space, Tue, 25 Aug 2026 02:50:57 GMT
"""


def test_unscored_scans_are_skipped():
    """The earliest logged scans predate scoring and were grouped by source."""
    scans = parse_scans(LOG)
    assert len(scans) == 1
    assert scans[0]["at"] == "2026-09-05T06:09+00:00"


def test_parses_items_under_their_position():
    items = parse_scans(LOG)[0]["positions"]["target_role"]
    assert [i["score"] for i in items] == [0.686, 0.600]
    assert items[0]["link"] == "https://example.com/b"


def test_source_and_published_split_on_the_first_comma_only():
    """Published dates contain commas; source names do not."""
    item = parse_scans(LOG)[0]["positions"]["target_role"][0]
    assert item["source"] == "Latent Space"
    assert item["published"] == "Wed, 26 Aug 2026 16:16:25 GMT"


def test_title_containing_brackets_survives():
    """AINews titles are bracketed, so the title group has to be greedy."""
    item = parse_scans(LOG)[0]["positions"]["target_role"][1]
    assert item["title"] == "[AINews] Andrew Ng gets into AI Engineering"


def test_provenance_line_is_not_mistaken_for_an_item():
    assert len(parse_scans(LOG)[0]["positions"]["target_role"]) == 2


def test_precision_denominator_is_capped_by_what_exists():
    """Three relevant items in the set means 3/3 is perfect, not 3/5."""
    ranked = [{"rating": r} for r in (2, 2, 2, 0, 0, 0)]
    assert precision_at_k(ranked, 5) == (3, 3)


def test_precision_counts_only_the_top_k():
    ranked = [{"rating": r} for r in (2, 0, 0, 0, 0, 2)]
    assert precision_at_k(ranked, 5) == (1, 2)


def test_borderline_items_do_not_count_as_relevant_by_default():
    ranked = [{"rating": r} for r in (1, 1, 1)]
    assert precision_at_k(ranked, 5) == (0, 0)


def test_threshold_can_include_borderline():
    ranked = [{"rating": r} for r in (1, 1, 0)]
    assert precision_at_k(ranked, 5, threshold=1) == (2, 2)