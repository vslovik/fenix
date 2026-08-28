"""Chunking strategy for article text.

The strategy, and the reasoning behind each choice:

**Split on paragraphs first, not on a fixed character count.** Prose carries its
meaning in paragraphs; cutting mid-paragraph produces chunks that retrieve well
on keywords but read as fragments when quoted back as a citation. Paragraph
boundaries are free structure — the author already put them where the topic turns.

**Pack paragraphs up to a target size rather than one-per-chunk.** Single
paragraphs are often two sentences long. Embedded alone they are dominated by
whatever words happen to be in them, and retrieval gets noisy. Packing to roughly
`MAX_CHARS` gives each vector enough context to be about something.

**Overlap by carrying the tail of the previous chunk.** A fact stated at a chunk
boundary would otherwise be retrievable from neither side — the first chunk ends
before the claim, the second begins after its subject. `OVERLAP_CHARS` of carry
makes boundary-spanning statements reachable from both.

**Split oversized paragraphs on sentence boundaries.** A single paragraph longer
than the target still has to be cut, but cutting mid-sentence produces citations
that begin in the middle of a clause.

**Merge runt chunks into their neighbour.** A trailing 40-character chunk is
almost pure noise in a vector index: its embedding is unstable and it wins
retrievals it should not.

Sizes are in characters rather than tokens deliberately — the embedding model
here has a large enough window that token-exact packing buys nothing, and
characters keep the strategy legible and dependency-free.
"""

import re

MAX_CHARS = 1200
OVERLAP_CHARS = 200
MIN_CHARS = 100

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def _split_long_paragraph(para: str) -> list[str]:
    """Cut an oversized paragraph on sentence boundaries, packing to MAX_CHARS."""
    sentences = _SENTENCE_END.split(para)
    out, current = [], ""
    for sentence in sentences:
        if current and len(current) + 1 + len(sentence) > MAX_CHARS:
            out.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        out.append(current)
    return out


def chunk(text: str) -> list[str]:
    """Split article text into overlapping, paragraph-aligned chunks."""
    units: list[str] = []
    for para in _split_paragraphs(text):
        units.extend(_split_long_paragraph(para) if len(para) > MAX_CHARS else [para])

    packed: list[str] = []
    current = ""
    for unit in units:
        if current and len(current) + 2 + len(unit) > MAX_CHARS:
            packed.append(current)
            current = unit
        else:
            current = f"{current}\n\n{unit}" if current else unit
    if current:
        packed.append(current)

    # merge a runt tail into its predecessor rather than emitting it
    if len(packed) > 1 and len(packed[-1]) < MIN_CHARS:
        packed[-2] = f"{packed[-2]}\n\n{packed.pop()}"

    if not packed:
        return []

    # carry the tail of each chunk into the next
    with_overlap = [packed[0]]
    for previous, nxt in zip(packed, packed[1:]):
        carry = previous[-OVERLAP_CHARS:].lstrip()
        with_overlap.append(f"{carry}\n\n{nxt}")
    return with_overlap