"""Anchor metrics — pure arithmetic over (score, want) pairs. No Ollama, no network."""

from fenix.score import metrics


def test_separation_is_the_gap_between_group_means():
    result = metrics([(0.8, True), (0.6, True), (0.5, False), (0.3, False)])
    assert result["wanted_mean"] == 0.7
    assert result["unwanted_mean"] == 0.4
    assert abs(result["separation"] - 0.3) < 1e-9


def test_margin_is_worst_case_and_separation_can_hide_an_overlap():
    """One unwanted probe sitting among the wanted ones leaves separation healthy."""
    result = metrics([(0.9, True), (0.4, True), (0.6, False), (0.1, False)])
    assert result["separation"] > 0
    assert result["margin"] < 0


def test_margin_is_positive_only_when_a_threshold_separates_the_groups():
    result = metrics([(0.8, True), (0.7, True), (0.6, False)])
    assert abs(result["margin"] - 0.1) < 1e-9


def test_inversions_count_pairs_not_items():
    """One unwanted probe above two wanted ones is two pairs out of order."""
    result = metrics([(0.9, True), (0.4, True), (0.3, True), (0.5, False)])
    assert result["inversions"] == 2
    assert result["pairs"] == 3


def test_no_inversions_when_every_wanted_outranks_every_unwanted():
    result = metrics([(0.8, True), (0.7, True), (0.2, False), (0.1, False)])
    assert result["inversions"] == 0
    assert result["pairs"] == 4


def test_ties_do_not_count_as_inversions():
    assert metrics([(0.5, True), (0.5, False)])["inversions"] == 0


def test_none_without_a_control_group():
    """No unwanted probes means nothing to measure against — report nothing, not zero."""
    assert metrics([(0.8, True), (0.6, True)]) is None
    assert metrics([(0.8, False)]) is None
    assert metrics([]) is None