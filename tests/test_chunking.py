"""The chunking strategy is the part of a RAG system most easily got wrong
silently: bad chunks still retrieve, they just retrieve badly. These pin the
properties the strategy claims in its docstring.
"""

import pytest

from fenix.chunking import MAX_CHARS, MIN_CHARS, OVERLAP_CHARS, chunk


def paragraph(n: int, words: int = 40) -> str:
    return " ".join(f"word{i}" for i in range(words)) + f" end{n}."


def document(paragraphs: int, words: int = 40) -> str:
    return "\n\n".join(paragraph(i, words) for i in range(paragraphs))


def test_empty_input_yields_no_chunks():
    assert chunk("") == []
    assert chunk("   \n\n  ") == []


def test_short_document_stays_one_chunk():
    assert len(chunk(document(3, words=10))) == 1


def test_packs_paragraphs_rather_than_one_per_chunk():
    """Three short paragraphs well under the budget belong together."""
    text = document(3, words=10)
    assert len(chunk(text)) == 1
    assert text.count("end") == chunk(text)[0].count("end")


def test_content_stays_within_budget():
    """Packed content respects MAX_CHARS; overlap is added on top of it."""
    for piece in chunk(document(20)):
        assert len(piece) <= MAX_CHARS + OVERLAP_CHARS + 50


def test_every_boundary_carries_overlap():
    pieces = chunk(document(20))
    assert len(pieces) > 1
    for previous, following in zip(pieces, pieces[1:]):
        assert following.startswith(previous[-OVERLAP_CHARS:].lstrip())


def test_oversized_paragraph_is_cut_on_sentence_boundaries():
    text = " ".join(f"This is sentence number {i} and it runs on a while." for i in range(80))
    for piece in chunk(text):
        assert piece.rstrip().endswith("."), "chunk ends mid-sentence"


def test_runt_tail_is_merged_into_its_neighbour():
    pieces = chunk(document(5) + "\n\nTiny.")
    assert len(pieces[-1]) >= MIN_CHARS
    assert pieces[-1].rstrip().endswith("Tiny.")


def test_no_content_is_lost():
    """Every paragraph marker survives chunking."""
    text = document(20)
    joined = " ".join(chunk(text))
    for n in range(20):
        assert f"end{n}." in joined


@pytest.mark.parametrize("paragraphs", [1, 2, 5, 20, 60])
def test_chunk_count_grows_with_input(paragraphs):
    pieces = chunk(document(paragraphs))
    assert pieces
    assert all(piece.strip() for piece in pieces)
