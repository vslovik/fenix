# Discovery Pipeline — How It Works, and the Chaining Question

Written 2026-08-15 so this is documented before manual experiments start, not just in chat
history. Covers: what's built, what today's relevance-feedback experiment proved, and a direct
answer to "should this be a chained, multi-step pipeline with early stopping."

## What's built

**`positions/*.md`** — free-text descriptions of a role to match against (your own target
role, later maybe a team-recruiting need). Optional `tags:` frontmatter. Any file here is
picked up automatically, no code changes needed. See `positions/README.md`.

**`sources.yaml`** — RSS feed sources to scan. `status: active/blocked/manual`, always with a
reason if not active — a failure is information to react to, not a thing to hide.

**`src/fenix/signal_scan.py`** — the recurring loop. Fetches new items from active sources,
embeds each (local Ollama, `nomic-embed-text`), scores by cosine similarity against every
position vector, appends a ranked leaderboard per position to `signals_log.md`. Dedupes so
each item is only ever scored once (see `README.md` for the reset command when you want to
rescore the same batch, e.g. after editing a position file). **Run manually — no cron.**

**`src/fenix/source_similarity.py`** — a one-off discovery utility, not part of the recurring
loop. Scores candidate sources/items against a reference by the same embedding mechanism.
Used today for two different experiments:

1. **Source discovery**: is candidate site X close in character to a source you already trust
   (Latent Space)? Answer computed from real fetched content, not reputation — and it
   overturned my prose guess in two places (ThursdAI scored highest; Ahead of AI and The
   Neural Maze, which "sounded" close, scored near the bottom).
2. **Relevance feedback**: instead of asking "what's like Latent Space in general," ask "what's
   like the *specific item* that scored best against my position." Seeded a WebSearch from the
   top signal ("Ontologies Are So Back," 0.657 against `my_target_role`), found a niche cluster
   (Year of the Graph, Ken Huang's Substack, Context & Chaos) that scored 0.65–0.74 against that
   specific item — well above what the generic candidates (Simon Willison 0.606, ThursdAI
   0.587) scored against the *same* reference. Seeding from what actually matched beats seeding
   from the aggregator you started with.

## The chaining question

You asked: should this be chained — signal search → site search from what matched → signal
search on the new sites → repeat 2–3 times with early stopping? Direct answer: **the shape is
right, but it can't be a plain deterministic script the way `signal_scan.py` is, and I wouldn't
build the automated version yet.**

**Why it can't be pure script, honestly:** step 2 (site search from a matched signal) needed a
real web search — `source_similarity.py` can *score* candidates once it has URLs, but it can't
*generate* candidate URLs from nothing. Today that step was me, an agent, running WebSearch and
judgment-filtering results (dropping arXiv papers, an academic site with no feed, checking RSS
existence by hand). A script can't do that step without either (a) a programmatic search API
wired in, or (b) an LLM agent in the loop making the same judgment calls I just made by hand.
That's a materially bigger build than anything shipped so far — not a config change.

**Why I wouldn't automate it yet:** same reason nothing here is on a cron — one successful run
(one topic, one niche cluster found) doesn't prove the loop generalizes. It could easily drift
off-topic after 2–3 hops (chase "ontologies" into a knowledge-graph-vendor rabbit hole that has
nothing to do with what you're actually looking for) without a human eye checking each hop.
Early stopping needs a real stopping criterion — score threshold, marginal-new-candidate count,
topic drift — and none of those are calibrated yet from a single test.

**What I'd do instead:** keep running this step manually — when a run turns up a genuinely
interesting top signal, ask me to chase it with a `source_similarity.py`-style search, look at
the result together, decide by hand whether to add anything to `sources.yaml`. Do that a few
more times. If it keeps finding good sources, *then* it's worth building as a real agent loop —
and worth noting it would double as another instance of demo spec #1 (a real tool-calling
agent: plan → search → score → decide whether to continue), alongside the
monitoraggio-normativo/pacioli tandem. Not building that agent loop today.

## Current source set (2026-08-15)

Active: Latent Space, ThursdAI, Simon Willison's Newsletter, Coding with Intelligence,
Interconnects AI, Turing Post (the five added ones scored ≥0.70 similarity to Latent Space's
own content — see `sources.yaml` comments for the full ranked list and what wasn't added).
Blocked: r/LLMDevs (Reddit anti-bot). Manual-only: MLOps Community Slack (no feed).

First run on the broadened set already surfaced a different top cluster than Latent-Space-only
did — Turing Post's agent/enterprise-AI content dominated the top of `my_target_role`'s ranking
this time. Worth watching whether that holds up over more runs, or was one good day.
