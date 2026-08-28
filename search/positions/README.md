# Positions

Each `.md` file here is one query vector for `signal_scan.py` — a free-text description of a
position, embedded and used to rank incoming market/signal items by similarity. Add or edit
files freely; the scan picks up whatever's in this directory, no code changes needed.

Frontmatter (optional): a `tags:` list at the top, e.g.

```
---
tags: [job-search, ai-initiative]
---
```

Tags don't affect scoring — they're just labels carried through into `../signals_log.md` so a
multi-position run stays readable. Not a fixed taxonomy; use whatever's meaningful (e.g.
`job-search`, `team-recruiting`, `ai-initiative`).

Current files:
- `my_target_role.md` — your own target role (tags: job-search, ai-initiative)

To add a "recruiting for the current team" position: drop in a new file (e.g.
`team_role_x.md`) describing the role you're trying to fill. Same mechanism, different
purpose — the market-state discovery byproduct the repurposing conversation named.
