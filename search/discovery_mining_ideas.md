# Discovery Mining — Creative Ideas

Triggered by the keyword-match failure in `signal_scan.py` (0/20 flagged, real). Keyword
matching is the boring, brittle version of this. The actual move: treat discovery as a data
mining problem — mine broadly, filter downstream with embeddings, not upfront with strings.

## 1. The core move: embeddings over keywords

Replace `matches_keywords()` with cosine similarity against an embedding. Not "does this
title contain the word 'agentic'" but "how semantically close is this item to what I'm
looking for." Fixes the recall problem structurally — a Latent Space post about multi-agent
orchestration patterns matches a "want agentic work" vector even with zero literal keyword
overlap.

Stack: `nomic-embed-text` via Ollama — already running on this machine, already used in
`homeserve/group-data-poc`. Zero new infra, no API keys, no rate limits, fully local.

## 2. Write your own fancy position — the query vector

Instead of embedding role titles, write 1-2 paragraphs of the role you actually want, in your
own words — the blend that no single title captures (agentic systems + architecture and
technical leadership + NLP/Transformer depth + production reliability, plus whatever you care
about in an environment). Embed *that*. Every mined item gets scored against it. This is the literal
implementation of "create our own fancy position" — a synthetic job description that exists
nowhere, used purely as a similarity anchor.

## 3. Broaden the net now that filtering is downstream

Keyword pre-filtering forced narrow sources (had to guess the right title upfront). Similarity
scoring doesn't — feed it anything text-shaped: RemoteOK, We Work Remotely, Himalayas, HN
Who's Hiring threads (Algolia API already confirmed working), YC jobs, plus the existing signal
sources. Collect broad, rank narrow.

## 4. A leaderboard, not a binary flag

Instead of `flagged: true/false`, output top-N by similarity score each run — a small ranked
list of "closest things to your fancy position this week." More fun to read than a filtered
log, and it surfaces near-misses you'd never have thought to search for.

## 5. Multiple personas, not one vector

Write 2-3 fancy positions instead of one — e.g. an "agentic architecture" flavor, an "SRE/
reliability" flavor, an "NLP-research-adjacent engineering" flavor (mirrors the Tier-1 spread
in the application-priority notes). Score every item against all of them. Turns each run into
a small multi-axis readout of where the market's leaning, not just a match/no-match.

## 6. Cluster the corpus — actual data mining

Once enough items are harvested, run k-means or HDBSCAN over the embeddings and look at what
clusters emerge on their own, unprompted by any title list. This is the part that could
surface a role/pattern nobody's named yet for you — real discovery, not filtering against
your own preconceptions.

## 7. This is also the RAG Engineer demo (spec #2), for free

Demo spec #2 needs "real embeddings in a queryable vector store, retrieval
traceable to source chunks." This tool, built for real, clears that bar as a side effect. One
build, two payoffs — a working discovery engine and a credible RAG Engineer artifact, not two
separate projects competing for the same evening.
