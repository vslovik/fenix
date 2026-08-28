"""Store behaviour that the retrieval path depends on: dedupe, cascade, and
that vector search ranks by direction rather than magnitude.
"""

import math
import random

import pytest

from fenix import store


@pytest.fixture
def db(tmp_path):
    return store.connect(tmp_path / "corpus.db")


def unit_vector(seed: int, dim: int = store.EMBED_DIM) -> list[float]:
    rng = random.Random(seed)
    v = [rng.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in v))
    return [x / norm for x in v]


def add_doc(db, link="https://example.com/a", **kw):
    return store.add_document(
        db, source=kw.get("source", "test"), title=kw.get("title", "Title"),
        link=link, published="", fetched_at="2026-01-01", text=kw.get("text", "body"),
    )


def test_document_dedupe_by_link(db):
    add_doc(db)
    assert store.document_exists(db, "https://example.com/a")
    assert not store.document_exists(db, "https://example.com/b")


def test_duplicate_link_is_rejected(db):
    add_doc(db)
    with pytest.raises(Exception):
        add_doc(db)


def test_search_returns_document_metadata_with_each_chunk(db):
    doc = add_doc(db, title="The Title", source="Feed")
    store.add_chunk(db, doc_id=doc, idx=0, text="chunk text", embedding=unit_vector(1))
    db.commit()
    hit = store.search(db, unit_vector(1), k=1)[0]
    assert hit["title"] == "The Title"
    assert hit["source"] == "Feed"
    assert hit["link"] == "https://example.com/a"
    assert hit["chunk_text"] == "chunk text"
    assert hit["chunk_idx"] == 0


def test_search_ranks_by_direction_not_magnitude(db):
    """The reason for distance_metric=cosine: a scaled copy of the query must
    rank as close as the query itself, not be penalised for its length."""
    doc = add_doc(db)
    query = unit_vector(7)
    store.add_chunk(db, doc_id=doc, idx=0, text="same direction, 10x longer",
                    embedding=[x * 10 for x in query])
    store.add_chunk(db, doc_id=doc, idx=1, text="unrelated", embedding=unit_vector(99))
    db.commit()

    hits = store.search(db, query, k=2)
    assert hits[0]["chunk_text"] == "same direction, 10x longer"
    assert hits[0]["distance"] < 1e-4, "magnitude leaked into the distance"


def test_search_respects_k(db):
    doc = add_doc(db)
    for i in range(10):
        store.add_chunk(db, doc_id=doc, idx=i, text=f"c{i}", embedding=unit_vector(i))
    db.commit()
    assert len(store.search(db, unit_vector(0), k=3)) == 3


def test_deleting_a_document_removes_its_chunks(db):
    doc = add_doc(db)
    store.add_chunk(db, doc_id=doc, idx=0, text="c", embedding=unit_vector(1))
    db.commit()
    db.execute("DELETE FROM documents WHERE id = ?", (doc,))
    db.commit()
    assert store.stats(db)["chunks"] == 0


def test_stats_counts_distinct_sources(db):
    for i, src in enumerate(["a", "a", "b"]):
        add_doc(db, link=f"https://example.com/{i}", source=src)
    db.commit()
    assert store.stats(db) == {"documents": 3, "chunks": 0, "sources": 2}


def test_reindex_rebuilds_every_vector(db):
    doc = add_doc(db)
    for i in range(5):
        store.add_chunk(db, doc_id=doc, idx=i, text=f"chunk {i}", embedding=unit_vector(i))
    db.commit()

    calls = []

    def fake_embed(text):
        calls.append(text)
        return unit_vector(hash(text) % 1000)

    assert store.reindex(db, fake_embed) == 5
    assert sorted(calls) == [f"chunk {i}" for i in range(5)]
    assert len(store.search(db, unit_vector(1), k=5)) == 5
