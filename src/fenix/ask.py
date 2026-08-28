"""Answer a question from the corpus, citing the chunks the answer came from.

Retrieval-augmented generation over the store built by `ingest`. The answer is
constrained to the retrieved chunks and every claim carries a citation, so it can
be checked against the source rather than trusted.

The model is told to say when the corpus does not contain the answer. That
instruction is the point of the exercise: a RAG system that always answers is
indistinguishable from one that is making things up.
"""

import sys
import textwrap

from . import store
from .embedding import embed, generate

DEFAULT_K = 6

PROMPT = """\
You are answering a question using only the numbered sources below. They are
excerpts from articles about AI engineering, agents and the surrounding industry.

Rules:
- Use only what the sources say. Do not add outside knowledge.
- Cite every claim with the bracketed number of the source it came from, like [2].
- A sentence may cite more than one source, like [1][4].
- If the sources do not answer the question, say so plainly and stop. Do not guess.
- Be concise. No preamble.

SOURCES
{context}

QUESTION
{question}

ANSWER"""


def build_context(hits: list[dict]) -> str:
    blocks = []
    for n, hit in enumerate(hits, 1):
        blocks.append(f"[{n}] {hit['title']}\n{hit['chunk_text']}")
    return "\n\n".join(blocks)


def ask(question: str, k: int = DEFAULT_K, show_chunks: bool = False) -> None:
    db = store.connect()
    counts = store.stats(db)
    if counts["chunks"] == 0:
        print("The corpus is empty. Run:  uv run python -m fenix.ingest")
        return

    hits = store.search(db, embed(question), k=k)
    if not hits:
        print("Nothing retrieved.")
        return

    if show_chunks:
        print("=== retrieved ===")
        for n, hit in enumerate(hits, 1):
            print(f"\n[{n}] distance {hit['distance']:.3f} — {hit['title']} "
                  f"(chunk {hit['chunk_idx']})")
            print(textwrap.indent(textwrap.fill(hit["chunk_text"][:300], 88), "    "))
        print("\n=== answer ===\n")

    answer = generate(PROMPT.format(context=build_context(hits), question=question))
    print(textwrap.fill(answer, 88, replace_whitespace=False))

    print("\nSources")
    for n, hit in enumerate(hits, 1):
        print(f"  [{n}] {hit['title']}  (chunk {hit['chunk_idx']}, {hit['source']})")
        print(f"      {hit['link']}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--show-chunks"]
    if not args:
        print('Usage: uv run python -m fenix.ask "your question" [--show-chunks]')
        sys.exit(1)
    ask(" ".join(args), show_chunks="--show-chunks" in sys.argv)