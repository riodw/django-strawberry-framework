"""Tests for KANBAN version-tuple parsing and board-placeholder resolvability."""

import pytest

from scripts._kanban_lib import placeholder_defects, unresolvable_placeholders
from scripts.build_kanban_html import assert_placeholders_resolve, version_tuple


def test_version_tuple_ignores_non_ascii_digit_like_characters() -> None:
    assert version_tuple("1\u00b2.2") == (1, 2)
    assert version_tuple("\u00b2.2") == (0,)


def test_version_tuple_stops_at_an_oversized_decimal_segment() -> None:
    assert version_tuple(f"1.{'2' * 5000}.3") == (1,)


def _card(text: str, *, orders: tuple[int, ...] = ()) -> dict:
    """A minimal card carrying one scope item and the reference orders it may cite."""
    return {
        "cardId": "TODO-ALPHA-052-0.0.16",
        "planningNote": "",
        "outgoingReferences": [
            {"order": order, "rawText": "", "targetCard": {}} for order in orders
        ],
        "items": [{"order": 59, "section": {"key": "scope"}, "text": text}],
    }


def test_a_numeric_card_ref_backed_by_a_reference_row_resolves() -> None:
    assert unresolvable_placeholders("{{card_ref:0}}", reference_orders={0}) == []


@pytest.mark.parametrize(
    "text",
    [
        "{{card_ref:N}}",  # non-numeric index: the shell's pattern never matches it
        "{{card_ref:99}}",  # numeric but backed by no reference row
    ],
)
def test_a_card_ref_the_shell_cannot_resolve_is_reported(text: str) -> None:
    assert unresolvable_placeholders(text, reference_orders={0}) == [text]


def test_a_computed_token_resolves_in_a_board_doc_body_but_not_in_card_text() -> None:
    """Only ``BoardDoc`` bodies get the computed set; neither export fills card text."""
    assert unresolvable_placeholders("{{active_version}}", reference_orders=set()) == [
        "{{active_version}}",
    ]
    assert (
        unresolvable_placeholders(
            "{{active_version}}",
            reference_orders=set(),
            computed_tokens={"active_version"},
        )
        == []
    )


def test_a_defect_names_the_row_that_stores_it() -> None:
    """The token alone does not locate it; one placeholder can be on any card item."""
    assert placeholder_defects([_card("rewritten to {{card_ref:N}} placeholders")], []) == [
        "card TODO-ALPHA-052-0.0.16 item order=59 section=scope: {{card_ref:N}}",
    ]


def test_the_html_build_refuses_a_placeholder_that_resolves_nowhere() -> None:
    """``KANBAN.html`` embeds placeholders verbatim, so an unresolvable one would print."""
    snapshot = {"cards": [_card("see {{card_ref:N}}")], "boardDocs": []}
    with pytest.raises(RuntimeError, match=r"resolve nowhere"):
        assert_placeholders_resolve(snapshot)

    resolvable = {"cards": [_card("see {{card_ref:0}}", orders=(0,))], "boardDocs": []}
    assert assert_placeholders_resolve(resolvable) is None
