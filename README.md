# fenix

A local, no-API-key tool for reading the state of a market — and then asking it questions.

Two halves over one corpus:

- **Scan** ranks an incoming stream of articles against free-text *position* descriptions,
  surfacing what's closest to something you described in prose rather than something you
  guessed the keywords for.
- **Ask** answers a question from the same corpus with retrieval-augmented generation, citing
  the specific chunks each claim came from.

Embeddings and generation both run against a local [Ollama](https://ollama.com). No API keys,
no per-token cost, no rate limits.

It is a **market-intelligence tool**, not a job board or an applicant tracker: it reads the
state of a market against a description you write, and the description can be anything you want
to find more of.

## Why similarity rather than keywords

The first version filtered by keyword and scored **0 out of 20** on real data — the interesting
items never contained the words a job title would suggest. Replacing the filter with embedding
similarity produced meaningful separation on the first run: agent and architecture content
scored **0.58–0.66**, generic model-release news **0.36–0.49**.

A keyword filter answers *"does this contain the word I guessed"*. A similarity score answers
*"how close is this to the thing I described"* — and the description can be a paragraph of
prose rather than a title someone has already invented.

## Usage

```bash
uv sync                                   # installs Python 3.13 and dependencies

fenix ingest                              # fetch article text, chunk, embed, store
fenix ask "what changed in agent tooling this month?"
fenix ask "..." --show-chunks             # show what was retrieved, and how close
fenix scan                                # rank the stream against positions/
fenix stats                               # corpus size
fenix reindex                             # rebuild vectors after changing model or metric
```

**Requirements:** [uv](https://docs.astral.sh/uv/), and Ollama serving `nomic-embed-text`
(embeddings) and `qwen2.5:7b` (generation). Both models are configurable in
`src/fenix/embedding.py`.

## How the retrieval works

**Corpus.** `ingest` follows each feed link and extracts the article body with `trafilatura`,
rather than embedding the RSS summary. A two-line summary cannot be meaningfully chunked, and
retrieval over summaries can only ever return what the feed already told you.

**Chunking.** Paragraph-aligned, packed to ~1200 characters, with 200 characters of overlap
carried across each boundary. Oversized paragraphs are cut on sentence boundaries; runt tails
are merged into their neighbour. The reasoning for each of those choices is in
`src/fenix/chunking.py`, and the properties are pinned by tests.

**Storage.** SQLite with [sqlite-vec](https://github.com/asg017/sqlite-vec) — one file, no
daemon, no server. Vectors use `distance_metric=cosine`, not the `vec0` default of L2:
`nomic-embed-text` does not return unit vectors, so under L2 a longer chunk is penalised for
its magnitude rather than judged on its direction.

At this corpus size brute-force cosine in Python would genuinely be correct, and a vector
database is arguably over-engineering. sqlite-vec is the smallest thing that keeps metadata and
vectors in one queryable place and still works when the corpus stops being small.

**Answering.** The top *k* chunks are numbered and passed as the only permitted context. The
model is instructed to cite every claim with the bracketed source number, and to say plainly
when the corpus does not answer the question. That last instruction is the point: a RAG system
that always answers is indistinguishable from one that is making things up.

## Positions

A position is a plain `.md` file in `search/positions/` describing, in your own words, what
you're looking for — not a title, a paragraph. Format in `search/positions/README.md`.

Any number can coexist: each scan scores every item against every position, so one run reads
the market from several angles at once — a role you want, a role you're hiring for, a
technology you're watching. The tool doesn't know or care which; a position is a position.

Writing a good one is less obvious than it looks — an embedding has no notion of negation, so
naming a technology in order to reject it moves the anchor *toward* it. Measured findings on
that, and on how much paragraph order matters, are in
[`lessons/embedding-anchors.md`](lessons/embedding-anchors.md).

## Tests

```bash
uv run pytest
```

Covers the chunking strategy's stated properties and the store's retrieval guarantees —
including that vector search ranks by direction rather than magnitude, which is the reason the
cosine metric is declared explicitly.

## Deliberately not automated

No cron, no scheduling. Runs stay manual until the tool has proven useful over weeks of real
use — automating something that produces noise just produces noise on a schedule.

## Licence

MIT — see [`LICENSE`](LICENSE).
