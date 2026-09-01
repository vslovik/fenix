# Positions

Each `.md` file here is one **query vector** — a free-text description of what you are looking
for, embedded once and used to rank every incoming item by similarity. Add or edit files
freely; the scan picks up whatever is in this directory, no code changes needed.

A position is prose, not a title. That is the point: you can describe the thing you actually
want, including the parts no job title captures, rather than guessing which keyword someone
else chose.

Any number can coexist. Each run scores every item against every position, so one scan reads
the market from several angles at once — a role you want, a role you are hiring for, a
technology you are watching.

## Writing one

**State what you want, never what you don't.** An embedding has no notion of negation: naming a
technology in order to reject it moves the vector *toward* it. Measured evidence for this, and
for how much paragraph order matters, is in [`../../lessons/embedding-anchors.md`](../../lessons/embedding-anchors.md).

**Leading paragraphs carry the most weight** — put what you most want to match first.

**Keep commentary in the frontmatter.** Everything below it is embedded verbatim, so a note
*about* the document ends up competing with the document.

## Frontmatter

Optional. A `tags:` list, and anything else you want kept out of the embedding:

```
---
tags: [job-search, ai-initiative]
note: >
  Notes here are stripped before embedding.
---
```

Tags do not affect scoring — they are labels carried into `../signals_log.md` so a
multi-position run stays readable. Not a fixed taxonomy; use whatever is meaningful.

## Current files

- `target_role.md` — AI, agentic and architecture roles (tags: job-search, ai-initiative)
