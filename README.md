# fenix

A discovery tool for reading the state of a job market, built because keyword matching
doesn't work.

It mines signal sources broadly, embeds every new item locally, and ranks them by cosine
similarity against one or more free-text *position* descriptions — a role you want, a role
you're hiring for, a direction you're watching. No API keys, no cloud inference: embeddings
run against a local Ollama model.

## Why similarity rather than keywords

The first version filtered by keyword and scored **0 out of 20** on real data — the interesting
items never contained the words a job title would suggest. Replacing the filter with embedding
similarity produced meaningful separation on the first run: agent and architecture content
scored **0.58–0.66**, generic model-release news **0.36–0.49**.

That gap is the whole point. A keyword filter answers "does this contain the word I guessed";
a similarity score answers "how close is this to the thing I described" — and the description
can be a paragraph of prose rather than a title someone has already invented.

## Running the scan

```
uv run python src/fenix/signal_scan.py
```

Fetches new items from the active sources in `search/sources.yaml`, scores each against every
position file in `search/positions/`, and appends a ranked leaderboard to
`search/signals_log.md` (the latest run is the last `## Scan — <timestamp>` section).

**Requirements:** [uv](https://docs.astral.sh/uv/), and a local
[Ollama](https://ollama.com) serving `nomic-embed-text`.

**Dedupe:** each item is scored once, ever — items are marked seen in
`.state/signal_scan_seen.json` after their first scan, so a second run usually reports zero new
items unless something was actually published in between. To force a rescore — for example to
compare results before and after editing a position file — reset the state first:

```
rm .state/signal_scan_seen.json
uv run python src/fenix/signal_scan.py
```

## Writing a position

A position is a plain `.md` file in `search/positions/` describing, in your own words, what
you're looking for. Not a title — a paragraph. The format is documented in
`search/positions/README.md`.

Any number can coexist: each run scores every item against every position, so one scan reads
the market from several angles at once.

## Design notes

- `search/discovery_mining_ideas.md` — why embeddings over keyword matching, and the ideas not
  yet built
- `search/discovery_pipeline.md` — the full mechanism, the source-discovery experiments, and
  the open question about chaining runs

## Deliberately not automated

No cron, no scheduling. Runs stay manual until the tool has proven useful over weeks of real
use — automating something that produces noise just produces noise on a schedule.