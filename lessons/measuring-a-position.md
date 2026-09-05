# How do you know a position file is any good?

*2026-09-05*

`lessons/embedding-anchors.md` shows how to *tune* an anchor: score it against some postings,
edit, re-score, keep what helps. That worked — it overturned a document that read perfectly
well. But it was done once, by hand, in a scratch file that no longer exists, and that leaves
three problems the tuning session never had to face.

---

## Problem 1 — the tuning was not repeatable

The numbers in that lesson cannot be reproduced. The probe postings lived in a scratch file;
the anchor has been rewritten since; there is no record of which text produced which score.

An improvement you cannot re-measure is a claim, not a result. The moment the anchor changes
again, every number in the lesson becomes historical trivia.

**Fix:** the probes became files (`search/probes/`) and the measurement became a command
(`fenix score`), which compares each run against the previous one automatically. The comparison
is the default rather than something to remember, because the discipline the lesson depends on —
*re-score before and after each edit* — is exactly the discipline people skip.

---

## Problem 2 — the scanner cannot re-score anything

`signal_scan` keeps a seen-set and skips anything already in it. An item is scored **once**, at
the moment it first appears, and never again.

That is correct for a feed reader and wrong for a measurement instrument. It means the effect
of an anchor edit on the stream is unobservable: the 30 items scored this morning will never be
scored again, so there is no way to ask "what would these have looked like under the new
wording?"

**Consequence:** the anchor can only be measured against material held deliberately still — a
fixed probe set — or against a person's judgement of results already produced. Not against the
live stream, which moves for two reasons at once.

---

## Problem 3 — postings are not articles

This is the one most easily missed, because the tuning method looks like it generalises.

The probes are **job postings**. The scanner ranks **articles**. Different genre, different
vocabulary distribution, different task. An anchor that separates postings cleanly can rank
industry news badly, and no probe set will ever tell you, because no probe is an article.

Evidence from the 5 September scan, the first against the rewritten anchor:

```
0.686   Lovable CTO: The Future of SaaS Is Apps That Agents Can Use
0.667   PRs NOT Welcome: How Top AI Open Source Projects Are Managing
        Thousands of Contributors                                       <- 2nd
...
0.561   The Evolution of the Agent Harness                              <- 11th
```

Second place went to an article about managing open-source contributors — people management,
which this anchor was written to avoid. Agent architecture, squarely its subject, came 11th.
That is a candidate inversion the probe set cannot see, since neither item is a posting.

**Fix:** `fenix rate` asks the only source of truth there is. It replays a scan with the scores
hidden and the order shuffled, takes a rating per item, and reports precision@k. Hidden, because
seeing the ranker's answer first makes you agree with it; shuffled, because the log is written
in descending score order and file order would leak the ranking anyway.

---

## Three questions, three instruments

| Question | Instrument | Ground truth |
|---|---|---|
| Is the anchor **aimed** right? | `fenix score` | your `want:` labels on the probes |
| Does the **ranking** agree with you? | `fenix rate` | you, reading titles |
| Has the **market moved away** from it? | not yet possible | — |

They are not interchangeable, and the third one is missing for a reason.

---

## What is not measurable yet, and why

The natural third measurement is drift: has the anchor gone stale while the market moved? The
symptom is specific — the *intent* stays right while the *vocabulary* ages. An anchor written
in August's language ("agent orchestration") keeps scoring against September's text ("agent
harness", "programmable organization") but scores it slightly lower, and quietly becomes a
filter for last month's phrasing rather than this month's substance.

Three quantities would show it, and all three need a time series:

- **ceiling** — top score per scan. Falling means the market is moving away from the anchor.
- **spread** — top minus median. Collapsing means the anchor has stopped discriminating.
- **centroid distance** — similarity to the mean of everything scanned. Rising means the anchor
  is becoming generic: it will match everything and separate nothing.

There is no time series. `signals_log.md` holds seven scan blocks: one with no scores at all
(an earlier format, grouped by source), five from a single afternoon of development against
anchors that no longer exist, and one from three weeks later. Two usable points, differently
anchored.

**So drift was not built.** Building the dashboard before the data exists is the same mistake as
scheduling a scanner before it has produced anything worth reading.

What *was* built is the thing that cannot be added retroactively. Every scan now writes a
provenance line:

```
`ab12cd34` · nomic-embed-text · 3,412 chars · max 0.686 · median 0.512 · min 0.433
```

The hash is of the anchor body as embedded, after the frontmatter is stripped. Without it a
score that moved between two scans is ambiguous — the market may have shifted, or the anchor may
have been edited — and the log cannot tell you which. The summary statistics are the ceiling and
spread above, recorded per run so that the series exists when there is enough of it to read.

Revisit after roughly ten scans spread over weeks, not after ten scans in an afternoon.

---

## The general point

A retrieval anchor is a piece of prose that behaves like a parameter. It gets edited the way
prose is edited — by taste, by rereading, by "that sounds better" — and it changes the behaviour
of the system the way a parameter does.

Three things follow, none of them specific to this tool:

**Keep a control group.** An edit that raises the wanted scores and the unwanted ones has
changed the document's verbosity, not its aim. Without controls every edit looks like an
improvement.

**Measure on the genre you actually run on.** A proxy set is worth having and is not worth
trusting past its genre.

**Record what would let you tell two explanations apart, before you need to.** The anchor hash
costs one line per scan. Not having it costs the entire question.