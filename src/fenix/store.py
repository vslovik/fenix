"""SQLite-backed chunk store with vector search via sqlite-vec.

One file, no daemon, no server. Documents hold the full extracted article text;
chunks hold the retrievable units; chunk_vectors is the vec0 index.

Why sqlite-vec rather than FAISS/Chroma/Qdrant: at this corpus size brute-force
cosine would genuinely be correct, so the only honest reasons to use a vector
store are that it keeps metadata and vectors in one queryable place and that it
still works when the corpus stops being small. sqlite-vec is the smallest thing
that satisfies both — one file, one dependency, nothing to run.
"""

import sqlite3
from pathlib import Path

import sqlite_vec

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / ".state" / "corpus.db"

EMBED_DIM = 768  # nomic-embed-text

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS documents (
    id         INTEGER PRIMARY KEY,
    source     TEXT NOT NULL,
    title      TEXT NOT NULL,
    link       TEXT NOT NULL UNIQUE,
    published  TEXT,
    fetched_at TEXT NOT NULL,
    text       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id     INTEGER PRIMARY KEY,
    doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    idx    INTEGER NOT NULL,
    text   TEXT NOT NULL,
    UNIQUE (doc_id, idx)
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vectors USING vec0(
    chunk_id  INTEGER PRIMARY KEY,
    embedding FLOAT[{EMBED_DIM}] distance_metric=cosine
);
"""

# Cosine, not the vec0 default of L2. nomic-embed-text does not return unit
# vectors, so under L2 a longer document chunk is penalised for its magnitude
# rather than judged on its direction — and direction is what carries meaning
# here. It also keeps this consistent with signal_scan, which scores by cosine.


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    """Open the corpus database with the vector extension loaded."""
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    try:
        db.enable_load_extension(True)
    except AttributeError:
        raise RuntimeError(
            "This Python was built without SQLite extension support, so sqlite-vec "
            "cannot load. Use uv's managed interpreter: `uv python pin 3.13 && uv sync`."
        ) from None
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA)
    return db


def document_exists(db: sqlite3.Connection, link: str) -> bool:
    return db.execute("SELECT 1 FROM documents WHERE link = ?", (link,)).fetchone() is not None


def add_document(db: sqlite3.Connection, *, source: str, title: str, link: str,
                 published: str, fetched_at: str, text: str) -> int:
    cur = db.execute(
        "INSERT INTO documents (source, title, link, published, fetched_at, text) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (source, title, link, published, fetched_at, text),
    )
    return cur.lastrowid


def add_chunk(db: sqlite3.Connection, *, doc_id: int, idx: int, text: str,
              embedding: list[float]) -> int:
    cur = db.execute(
        "INSERT INTO chunks (doc_id, idx, text) VALUES (?, ?, ?)", (doc_id, idx, text)
    )
    chunk_id = cur.lastrowid
    db.execute(
        "INSERT INTO chunk_vectors (chunk_id, embedding) VALUES (?, ?)",
        (chunk_id, sqlite_vec.serialize_float32(embedding)),
    )
    return chunk_id


def search(db: sqlite3.Connection, embedding: list[float], k: int = 6) -> list[dict]:
    """Top-k chunks by vector distance, with their document metadata."""
    rows = db.execute(
        """
        SELECT c.id      AS chunk_id,
               c.idx     AS chunk_idx,
               c.text    AS chunk_text,
               v.distance AS distance,
               d.title, d.link, d.source, d.published
        FROM chunk_vectors v
        JOIN chunks    c ON c.id = v.chunk_id
        JOIN documents d ON d.id = c.doc_id
        WHERE v.embedding MATCH ? AND k = ?
        ORDER BY v.distance
        """,
        (sqlite_vec.serialize_float32(embedding), k),
    ).fetchall()
    return [dict(r) for r in rows]


def reindex(db: sqlite3.Connection, embed_fn) -> int:
    """Rebuild every vector from stored chunk text.

    Needed after changing the embedding model or the distance metric — the vec0
    table has to be recreated, but the text is already here, so nothing is
    re-fetched from the network.
    """
    db.execute("DROP TABLE IF EXISTS chunk_vectors")
    db.executescript(SCHEMA)
    rows = db.execute("SELECT id, text FROM chunks ORDER BY id").fetchall()
    for n, row in enumerate(rows, 1):
        db.execute(
            "INSERT INTO chunk_vectors (chunk_id, embedding) VALUES (?, ?)",
            (row["id"], sqlite_vec.serialize_float32(embed_fn(row["text"]))),
        )
        if n % 25 == 0:
            db.commit()
            print(f"  {n}/{len(rows)}")
    db.commit()
    return len(rows)


def stats(db: sqlite3.Connection) -> dict:
    docs = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    chunks = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    sources = db.execute("SELECT COUNT(DISTINCT source) FROM documents").fetchone()[0]
    return {"documents": docs, "chunks": chunks, "sources": sources}
