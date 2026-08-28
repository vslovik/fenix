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

Nothing above was argued from taste. Measure your own anchor the same way, using the
project's embedding helper:

```python
from fenix.embedding import embed, cosine_similarity
v = embed(anchor_text)
score = cosine_similarity(v, embed(posting_text))
```

Write your postings once, keep them in a scratch file, and re-score before and after each
edit.

**Include the unwanted ones — they are the control.** An edit that raises the wanted scores
*and* the unwanted ones has changed the document's verbosity, not its aim, and without a
control every edit looks like an improvement.

This is cheap enough to do for any prompt, any retrieval anchor, any embedded document. It
takes minutes, and here it overturned a document that read perfectly well.
