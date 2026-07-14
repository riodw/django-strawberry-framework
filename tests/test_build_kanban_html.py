"""Focused tests for the shared KANBAN export helpers."""

from scripts.build_kanban_html import version_tuple


def test_version_tuple_ignores_non_ascii_digit_like_characters() -> None:
    assert version_tuple("1\u00b2.2") == (1, 2)
    assert version_tuple("\u00b2.2") == (0,)


def test_version_tuple_stops_at_an_oversized_decimal_segment() -> None:
    assert version_tuple(f"1.{'2' * 5000}.3") == (1,)
