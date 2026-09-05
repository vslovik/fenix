# Probes — the control group for a position anchor

A probe is a short synthetic posting used to measure what a file in `../positions/` actually
matches. `fenix score` embeds every position, embeds every probe, and prints the ranking.

**The unwanted probes are the point.** An edit that raises the wanted scores *and* the unwanted
ones has changed the anchor's verbosity, not its aim — and without a control every edit looks
like an improvement. See `../../lessons/embedding-anchors.md`, where a well-written anchor turned
out to rank two of its three explicitly-rejected paths above three of the roles it was written to
find.

## Format

```markdown
---
label: AI agent engineering
want: true
---

Write the posting the way a company would write it. No meta-commentary.
```

| Field | |
|---|---|
| `label` | What appears in the output. Defaults to the filename stem. |
| `want` | `true` if a good anchor should rank it high, `false` if it is a control. Defaults to `true`. |

Everything above the `---` fence is stripped before embedding — the same rule as positions, and
for the same reason (Finding 3 in the lesson: a note *about* a document competes with the
document).

## Writing good probes

- **Write them as postings, not as descriptions of postings.** The anchor is scored against real
  incoming text, so the probes should look like real incoming text.
- **Keep them roughly the same length.** Length affects the centroid; wildly uneven probes measure
  length as much as aim.
- **Controls must be plausible.** A control that is obviously irrelevant scores low for free and
  proves nothing. The useful controls are the near-misses — the paths that genuinely resemble your
  background and that you have still ruled out.
- **Change them rarely.** The numbers are only comparable across runs if the probe set holds
  still. Editing a probe invalidates the baseline; editing an anchor is what the baseline is for.

## The set here

| Probe | | Why it is in the set |
|---|---|---|
| `ai-agent-engineering` | want | The primary target. |
| `founding-engineer-seed` | want | Target #2, and the shape no platform taxonomy has a word for. |
| `software-architect` | want | The title that travels furthest in the UK market. |
| `llm-evaluation-observability` | want | Adjacent target; historically under-matched. |
| `rag-engineer` | want | The known regression — mentioned once in the anchor, never the centroid. |
| `ml-research-scientist` | **control** | Ruled out, and the hardest control: the LREC paper and the Transformer work are real, so the resemblance is real too. |
| `java-spring-backend` | **control** | Ruled out. The segment the 2022 move was out of. |
| `fullstack-javascript` | **control** | Ruled out. Demonstrable skill, wrong direction. |

These were rewritten on 2026-09-05 and are **not** the exact texts behind the numbers in the
lesson, so absolute scores will differ from the ones printed there. That does not matter: what is
comparable is one run against the next, on the same probe set.