"""Build the retrievable corpus: fetch articles, extract text, chunk, embed, store.

Distinct from `signal_scan`, which ranks the incoming stream against position
descriptions and keeps nothing. This keeps everything, so the corpus can be
questioned rather than only ranked.

The article body is fetched from the link rather than taken from the RSS summary
on purpose. A two-line summary cannot be meaningfully chunked, and retrieval over
summaries can only ever return what the feed already told you.
"""

import sys
from datetime import datetime, timezone

import feedparser
import trafilatura
import yaml

from . import store
from .chunking import chunk
from .embedding import embed

MIN_ARTICLE_CHARS = 400  # below this, extraction probably failed


def load_sources() -> dict:
    return yaml.safe_load(store.ROOT.joinpath("search", "sources.yaml").read_text())


def fetch_article(url: str) -> str | None:
    """Full article text, or None if the page could not be usefully extracted."""
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return None
    text = trafilatura.extract(
        downloaded, include_comments=False, include_tables=False, no_fallback=False
    )
    if not text or len(text) < MIN_ARTICLE_CHARS:
        return None
    return text


def ingest(limit_per_source: int | None = None) -> None:
    db = store.connect()
    sources = load_sources()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    added_docs = added_chunks = skipped = failed = 0

    for source in sources.get("signal_sources", []):
        name = source["name"]
        if source.get("status") != "active":
            print(f"[skip] {name} — status: {source.get('status')}")
            continue

        print(f"[fetch] {name} — {source['url']}")
        feed = feedparser.parse(source["url"])
        if feed.bozo and not feed.entries:
            print(f"  ! feed parse failed: {feed.bozo_exception}")
            continue

        entries = feed.entries[:limit_per_source] if limit_per_source else feed.entries
        for entry in entries:
            link = entry.get("link", "")
            if not link or store.document_exists(db, link):
                skipped += 1
                continue

            title = entry.get("title", "").strip()
            text = fetch_article(link)
            if text is None:
                print(f"  ! no article text: {title[:60]}")
                failed += 1
                continue

            doc_id = store.add_document(
                db, source=name, title=title, link=link,
                published=entry.get("published", ""), fetched_at=now, text=text,
            )
            pieces = chunk(text)
            for idx, piece in enumerate(pieces):
                store.add_chunk(db, doc_id=doc_id, idx=idx, text=piece, embedding=embed(piece))
            db.commit()

            added_docs += 1
            added_chunks += len(pieces)
            print(f"  + {len(pieces):2} chunks  {title[:64]}")

    print(f"\n{added_docs} document(s), {added_chunks} chunk(s) added; "
          f"{skipped} already present, {failed} not extractable")
    print("corpus:", store.stats(db))


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    ingest(limit)