"""Tests for KANBAN version-tuple parsing, placeholder resolvability, and truncation."""

import pytest

from scripts._kanban_lib import (
    placeholder_defects,
    truncation_defects,
    unresolvable_placeholders,
)
from scripts.build_kanban_html import (
    assert_nothing_truncated,
    assert_placeholders_resolve,
    version_tuple,
)


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


def _payload_card(number: int, item_count: int) -> dict:
    """A card as the GraphQL payload carries it, with ``item_count`` items."""
    return {"number": number, "items": [{"order": index} for index in range(item_count)]}


def _expected(cards: int, board_docs: int, items: dict) -> dict:
    return {"cards": cards, "board_docs": board_docs, "items": items}


def test_a_board_matching_the_database_reports_no_truncation() -> None:
    """The control: without it, an assertion that never fires reads as a passing proof."""
    assert (
        truncation_defects(
            [_payload_card(52, 101)],
            [{"key": "snapshot"}],
            _expected(cards=1, board_docs=1, items={52: 101}),
        )
        == []
    )


def test_a_card_whose_items_were_capped_is_reported() -> None:
    """The live defect: card 52 crossed ``max_list_rows`` and one item silently vanished."""
    assert truncation_defects(
        [_payload_card(52, 100)],
        [],
        _expected(cards=1, board_docs=0, items={52: 101}),
    ) == ["card 52 items: payload has 100, database has 101"]


def test_a_short_card_set_or_doc_set_is_reported() -> None:
    """The bound applies to the top-level lists too, and they are capped the same way."""
    defects = truncation_defects([], [], _expected(cards=71, board_docs=14, items={}))
    assert defects == [
        "allCards: payload has 0, database has 71",
        "allKanbanBoardDocs: payload has 0, database has 14",
    ]


def test_a_board_doc_surplus_is_not_a_defect() -> None:
    """Both exports inject synthetic docs, so only a SHORT doc list is truncation."""
    assert truncation_defects([], [{}, {}], _expected(cards=0, board_docs=1, items={})) == []


def test_the_build_refuses_a_board_that_came_back_short(monkeypatch: pytest.MonkeyPatch) -> None:
    """A silent cap must stop the build; the freshness checks cannot see one."""
    monkeypatch.setattr(
        "scripts.build_kanban_html.board_row_counts",
        lambda: _expected(cards=1, board_docs=0, items={52: 101}),
    )
    with pytest.raises(RuntimeError, match=r"came back short of the database"):
        assert_nothing_truncated([_payload_card(52, 100)], [])

    assert assert_nothing_truncated([_payload_card(52, 101)], []) is None
