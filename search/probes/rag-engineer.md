---
label: RAG engineer
want: true
---

We are building retrieval-augmented question answering over a large body of internal documents and
need an engineer to own the retrieval half of it. You will design the ingestion pipeline, decide how
documents are split into retrievable units, choose and tune the embedding model, and build the index
that serves queries at low latency.

Retrieval quality is the job. That means measuring recall against a labelled query set, diagnosing
whether a bad answer came from retrieval or from generation, handling documents whose structure
carries meaning, and making the citations back to source text accurate enough that a reader can
check them.

Our stack is Python with a vector database and a document store; the generation layer is already in
place. You will work with the team that owns it, but the corpus, the chunking strategy and the index
are yours.

Useful background: information retrieval, embedding models, hybrid search, and a habit of measuring
before tuning.