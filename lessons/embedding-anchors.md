# What a similarity anchor actually does

*2026-08-28*

A position file in `search/positions/` is the free-text document `signal_scan` embeds and
scores every incoming item against. Write one the way you would write a profile — fluent,
balanced, explicit about what you want and what you don't — and it can measurably do the
opposite of what it says.

Here is one that did, what was wrong with it, and what fixed it. Every number below was
measured; you can run the same check on your own anchor in a couple of minutes.

---

## The symptom

Score your anchor against a handful of synthetic postings you *do* want and a few you
deliberately don't. This one, against nine, produced:

```
1. AI agent engineering             0.7332
2. Software architect               0.6769
3. ML research scientist            0.6687   <-- ruled out
4. Java/Spring backend              0.6148   <-- ruled out
5. LLM evaluation / observability   0.6126
6. RAG engineer                     0.6092
7. Founding engineer (seed)         0.5976
8. Full-stack JavaScript            0.5699   <-- ruled out
```

**Two of the three unwanted paths ranked third and fourth** — above three of the roles the
document was written to find. The one most firmly rejected, research science, was the
third-best match in the document rejecting it.

---

## Finding 1 — an embedding has no notion of negation

The anchor contained:

> I don't want to lead with full-stack JavaScript or enterprise Java backend work — both are
> real, demonstrated skills, but not where the next role should sit.

Embedded, that sentence contributes the tokens *JavaScript*, *Java*, *full-stack*, *backend*.
The vector moves **toward** them. There is no direction in the space that means "not this".

Deleting the sentence:

| posting | before | after | |
|---|---|---|---|
| Java/Spring backend | 0.6119 | 0.5865 | **−0.025** |
| Full-stack JavaScript | 0.5695 | 0.5432 | **−0.026** |
| AI agent engineering | 0.7296 | 0.7523 | **+0.023** |
| LLM eval / observability | 0.6091 | 0.6260 | **+0.017** |

Removing a sentence that rejected two technologies is what made the anchor reject them.

The same mechanism, worse, in the research paragraph — *"not an academic-research one"*, *"not
looking for a pure research-scientist path"*. Three research-flavoured phrases in service of
saying no. Rewritten to state the engineering use positively, research fell from 0.669 to 0.628.

**Rule: state what you want. Never name a thing in order to reject it.**

---

## Finding 2 — position in the document dominates

Founding engineer was 7th. Rewriting its paragraph to carry the target vocabulary —
*seed-stage startup*, *architecture from zero*, *first production system*, *salary plus
equity* — moved it 0.5941 → 0.6626.

Then moving that same paragraph to the **front** of the document, changing not one word:

```
0.6626 -> 0.7290        +0.066, and 5th -> 2nd
```

The reordering was worth as much as the rewrite. `nomic-embed-text` pools over a bounded
window, so leading text dominates the centroid.

**Rule: the first paragraph is the anchor's real subject. Put there what you most want to
match.**

---

## Finding 3 — meta-commentary is embedded too

`load_positions` strips YAML frontmatter and embeds everything after it. The file opened with:

```markdown
# Target role

The similarity-search anchor: prose, not a title.
```

That header was leading content — and by Finding 2, leading content is the heaviest. A note
*about* the document was competing with the document. Moving it into the frontmatter, where it
is stripped before embedding, recovered the loss and then some: the primary target rose from
0.7405 to 0.8055.

**Rule: anything not meant to be matched belongs above the fence.**

---

## Result

```
                                   before    after
AI agent engineering               0.7332   0.8055   1st -> 1st
Founding engineer (seed)           0.5976   0.7333   7th -> 2nd
Software architect                 0.6769   0.6879   2nd -> 4th
LLM evaluation / observability     0.6126   0.6706   5th -> 5th
ML research scientist   ruled out  0.6687   0.6280   3rd -> 6th
Java/Spring backend     ruled out  0.6148   0.6233   4th -> 7th
Full-stack JavaScript   ruled out  0.5699   0.5352   8th -> 9th
RAG engineer                       0.6092   0.5917   6th -> 8th
```

All three ruled-out paths now sit at the bottom. Both priority targets sit at the top.

RAG is the regression: it is mentioned once, in passing, and never becomes the centroid. The
proper fix is a second position file rather than more words in this one — which is the
"multiple personas, not one vector" idea already written in
`../search/discovery_mining_ideas.md` §5.

---

## Why this generalises

The single-vector anchor cannot serve four role families at once. Making the document sharper
for agent engineering necessarily made it worse for everything not adjacent to it: a longer,
more focused document has a tighter centroid. An earlier experiment with two anchors — one
agentic, one architecture — moved LLM evaluation +0.134 and founding engineer +0.109 over the
single anchor, at the cost of raising Java slightly, because *"service boundaries, API,
event-driven integration"* is genuinely shared vocabulary between "software architect" and
"backend engineer".

**Some overlaps cannot be written away, because they are real.** If you genuinely hold a
credential that resembles the thing you are avoiding, the resemblance comes with it — here,
hands-on NLP and Transformer work is why research postings still score 0.63. No wording fixes
that, because there is nothing to fix. Separate them outside the embedding instead: a position
taxonomy, a seniority filter, an explicit keyword.

---

## Method

Nothing above was argued from taste. It was done by hand, in a scratch file, with:

```python
from fenix.embedding import embed, cosine_similarity
v = embed(anchor_text)
score = cosine_similarity(v, embed(posting_text))
```

That is now a command. Write your postings into `search/probes/`, one per file, each marked
`want: true` or `want: false`, and run:

```bash
uv run fenix score
```

It prints the ranking, the separation between the two groups, the margin (lowest wanted minus
highest unwanted — the number that says whether any threshold could separate them), the count
of inverted pairs, and the change against the previous run.

**Include the unwanted ones — they are the control.** An edit that raises the wanted scores
*and* the unwanted ones has changed the document's verbosity, not its aim, and without a
control every edit looks like an improvement.

### The limit of this method

Everything above scores the anchor against **job postings**. The scanner uses the same anchor
to rank **articles**. Those are different genres, and an anchor that separates postings cleanly
can still rank industry news badly — nothing in a probe set will tell you, because no probe is
an article.

The only check for that is a person reading the scan output and saying what they would actually
have read. `fenix rate` collects exactly that, with the scores hidden and the order shuffled so
the judgement stays independent of the ranking it is judging.

Why this method needed to become a command at all — and what still cannot be measured, with the
reason — is in [`measuring-a-position.md`](measuring-a-position.md).

This is cheap enough to do for any prompt, any retrieval anchor, any embedded document. It
takes minutes, and here it overturned a document that read perfectly well.

---

# A second session

*2026-10-01. Five edits, each scored before the next was made. The anchor began the evening
ranking at chance and ended it one pair short of clean.*

```
                           inversions   separation   margin
start                         8/15        +0.036     -0.060
after the one good edit       1/15        +0.076     -0.007
```

Eight inversions out of fifteen pairs is what a random ordering produces. The document read well
and ranked nothing. Worth noting that the three rules above were all being followed — no negation,
no meta-commentary above the fold, the strongest material first. Following them is not sufficient.

## What fixed it was reading the file, not reasoning about it

The third paragraph described wanting to deepen *"data and ML modelling work — feature pipelines,
gradient boosting, model validation"*. That is close to a verbatim description of the
`ml-research-scientist` control, which is why a posting labelled `want: false` outranked three
labelled `want: true`. Rewriting that paragraph as evaluation substance, and adding one sentence of
retrieval substance to the paragraph above it:

| posting | before | after | |
|---|---|---|---|
| RAG engineer | 0.617 | 0.699 | **+0.081** |
| LLM evaluation / observability | 0.605 | 0.661 | **+0.056** |
| ML research scientist *(control)* | 0.665 | 0.657 | −0.008 |
| Founding engineer (seed) | 0.772 | 0.735 | **−0.037** |

Inversions 8/15 → 1/15. Note what it cost: founding engineer paid 0.037 for the space.

This also settles the RAG regression left open above, which was expected to need a second position
file. It did not. One sentence naming embeddings, vector search, chunking and ranking quality, in
the second paragraph, moved it +0.081 — because the previous anchor mentioned retrieval once, in a
subordinate clause.

## Adding emphasis is a transfer, never a gain

Four further edits all made it worse, the same way each time. The anchor genuinely omitted the work
this career is strongest in — rescuing a system that grew faster than its design — so a paragraph
was added saying so. It did exactly what it was aimed at, and cost more than it bought:

```
software architect   0.649 -> 0.669   now clears every control
LLM evaluation       0.661 -> 0.646   now below two of them
                     1/15 -> 3/15     margin -0.007 -> -0.021
```

Nothing was removed. A paragraph was added, and the paragraph beneath it lost 0.015 purely by being
pushed down the page. **The document has a fixed budget of weight.** Architecture can rank correctly
or evaluation can; buying one with new prose sells the other. This puts a number on the rule above —
leading paragraphs dominate — which until now had none.

## The wording inside an added paragraph barely matters

The first version of that paragraph was generic: *shipped under launch pressure, without adequate
tests, incident response, release discipline*. On the theory that genericness was the problem, it
was replaced with the most specific prose in the file — statutory breathing space, early-settlement
calculations written against consumer-credit legislation, a test suite larger than the production
codebase.

Every score moved by 0.007 or less. The paragraph's **presence and position** were the entire
effect; its content was close to irrelevant. An anchor is not improved by making a passage better
written.

## Cutting prose to weaken a control strengthened it

The last experiment cut the closing paragraph from roughly 400 characters to 110, on the theory that
its NLP-and-model language was holding `ml-research-scientist` up. The control rose 0.005, and
`llm-evaluation-observability` fell 0.021 into last place.

The deleted sentence — *"I found a validation defect in my own pipeline, quantified what it changed,
and restated every figure it had touched"* — was carrying **evaluation** signal, not research
signal. It reads as machine learning; it embeds as measurement discipline. Where a sentence sits in
the space is not where its subject matter suggests.

## Four predictions, three wrong

Recorded because they were stated before the runs: that the `software-architect` probe would prove
mislabelled — it is not, it is the best-matching posting in the set; that genericness drove the
regression — it did not; that cutting the ML paragraph would lower the research control — it raised
it. The one that held was that adding a paragraph would cost `llm-evaluation-observability` its
0.004 of headroom.

The instinct to reason about what an edit *should* do to a vector is worth having and worth
distrusting. **Run it.** Five runs took under ten minutes, and the anchor in the repository tonight
is the one the measurement chose rather than the one the argument preferred.

Reverting to the earlier text reproduced all eight scores to three decimals, so the pipeline is
deterministic and a delta between runs is attributable to the edit alone.

## The anchor is a query, not a portrait

The anchor that won does not mention the work this career is most defined by, and that is correct.
Its only job is to rank an incoming stream. The rescue-and-re-architecture story earns its keep in
the CV and in the HN post, where a person reads it and a vector does not. Completeness is a virtue
in a profile and a cost in a query.

## What is left at -0.007

One inversion remains: `software-architect` at 0.649, eight thousandths below the research control.
That gap is near the resolution of this probe set, because the control is deliberately adjacent —
it shares evaluation rigour with what is actually wanted, which is why it barely moved all evening.
Closing it by making the anchor less accurate would be the wrong trade. The honest next moves are
outside the anchor: a second position file for the architecture family, or an `ml-engineering` probe
labelled `want: true` placed deliberately close to the research control, to measure whether the
distinction between wanting ML engineering and not wanting ML research is expressible in this space
at all.
