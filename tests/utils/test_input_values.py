"""Tests for the neutral set-input traversal substrate (``utils/input_values.py``).

The 0.0.9 DRY pass single-sited the runtime walk over a generated Strawberry
input value that the filter / order normalizers and the permission walkers had
each spelled inline (``docs/feedback.md`` Major 1 -- a divergence in the
active-input decision is a real bug class). These tests pin the shared mechanics
directly: the ``None`` / ``UNSET`` active-value rule, the dict-vs-dataclass walk,
the leaf / related / logic classification, and the order-side top-level-list
flattening. The deep family behavior (filter form-data, order flat tuples,
permission dispatch) lives in the ``filters`` / ``orders`` / ``utils.permissions``
suites that consume this substrate.
"""

import strawberry

from django_strawberry_framework.utils.input_values import (
    LEAF,
    LOGIC,
    RELATED,
    SetInputTraversal,
    is_inactive_value,
    iter_active_fields,
    iter_input_items,
)

# ---------------------------------------------------------------------------
# iter_input_items -- dict / dataclass / non-walkable
# ---------------------------------------------------------------------------


def test_iter_input_items_handles_dict_dataclass_and_non_walkable():
    assert iter_input_items({"a": 1}) == [("a", 1)]
    assert iter_input_items({}) == []
    assert iter_input_items(42) is None

    @strawberry.input
    class _In:
        a: int | None = None

    assert iter_input_items(_In(a=3)) == [("a", 3)]


# ---------------------------------------------------------------------------
# is_inactive_value -- the single active-input rule
# ---------------------------------------------------------------------------


def test_is_inactive_value_is_identity_based_not_truthiness():
    # ``None`` is always inactive; a configured sentinel collapses too.
    assert is_inactive_value(None) is True
    assert is_inactive_value(None, unset_sentinel=strawberry.UNSET) is True
    assert is_inactive_value(strawberry.UNSET, unset_sentinel=strawberry.UNSET) is True
    # Falsy-but-supplied values stay ACTIVE (identity, not truthiness).
    assert is_inactive_value(0) is False
    assert is_inactive_value("") is False
    assert is_inactive_value(False) is False
    # Order semantics (no sentinel configured): UNSET is a normal active value,
    # so the order normalizer never needs to reference ``strawberry.UNSET``.
    assert is_inactive_value(strawberry.UNSET) is False


# ---------------------------------------------------------------------------
# iter_active_fields -- classification + spec resolution + inactive skip
# ---------------------------------------------------------------------------


class _Spec:
    def __init__(self, path):
        self.django_source_path = path


def test_iter_active_fields_classifies_and_skips_inactive():
    related_obj = object()

    class _Set:
        related_filters = {"shelf": related_obj}

    specs = {(_Set, "title"): _Spec("title"), (_Set, "shelf"): _Spec("shelf")}
    config = SetInputTraversal(
        field_specs=specs,
        related_attr="related_filters",
        logic_keys=frozenset({"and_"}),
        unset_sentinel=strawberry.UNSET,
    )
    fields = list(
        iter_active_fields(
            _Set,
            {
                "title": "x",
                "shelf": {"code": "y"},
                "and_": [{"title": "z"}],
                "skip_none": None,
                "skip_unset": strawberry.UNSET,
            },
            config,
        ),
    )
    by_attr = {f.python_attr: f for f in fields}
    # ``None`` / ``UNSET`` fields are dropped entirely.
    assert set(by_attr) == {"title", "shelf", "and_"}
    # Leaf: spec resolved, no related_obj.
    assert by_attr["title"].kind == LEAF
    assert by_attr["title"].spec.django_source_path == "title"
    assert by_attr["title"].related_obj is None
    # Related: spec resolved AND the declared related object carried through.
    assert by_attr["shelf"].kind == RELATED
    assert by_attr["shelf"].spec.django_source_path == "shelf"
    assert by_attr["shelf"].related_obj is related_obj
    assert by_attr["shelf"].raw_value == {"code": "y"}
    # Logic: marked LOGIC; spec is None (no field-spec entry for an operator key).
    assert by_attr["and_"].kind == LOGIC
    assert by_attr["and_"].spec is None


def test_iter_active_fields_dict_and_dataclass_classify_identically():
    """The DRY intent: the dataclass and raw-dict shapes yield the same records."""

    class _Set:
        related_filters = {"shelf": object()}

    @strawberry.input
    class _In:
        title: str | None = None
        shelf: strawberry.scalars.JSON | None = None

    config = SetInputTraversal(
        field_specs={},
        related_attr="related_filters",
        unset_sentinel=strawberry.UNSET,
    )
    dataclass_view = [
        (f.python_attr, f.kind)
        for f in iter_active_fields(_Set, _In(title="x", shelf={"code": 1}), config)
    ]
    dict_view = [
        (f.python_attr, f.kind)
        for f in iter_active_fields(_Set, {"title": "x", "shelf": {"code": 1}}, config)
    ]
    assert dataclass_view == dict_view == [("title", LEAF), ("shelf", RELATED)]


def test_iter_active_fields_flattens_top_level_list_only_when_configured():
    class _Set:
        related_orders = {}

    with_list = SetInputTraversal(
        field_specs={},
        related_attr="related_orders",
        handle_top_level_list=True,
    )
    fields = list(iter_active_fields(_Set, [{"title": "a"}, {"subtitle": "b"}], with_list))
    assert [(f.python_attr, f.kind) for f in fields] == [("title", LEAF), ("subtitle", LEAF)]

    # Without the flag a bare list is non-walkable (no dict / dataclass shape)
    # so nothing is yielded -- the filter side, which never sends a top-level
    # list, relies on this.
    no_list = SetInputTraversal(field_specs={}, related_attr="related_orders")
    assert list(iter_active_fields(_Set, [{"title": "a"}], no_list)) == []


def test_iter_active_fields_inactive_or_non_walkable_top_level_yields_nothing():
    class _Set:
        related_orders = {}

    config = SetInputTraversal(
        field_specs={},
        related_attr="related_orders",
        unset_sentinel=strawberry.UNSET,
    )
    assert list(iter_active_fields(_Set, None, config)) == []
    assert list(iter_active_fields(_Set, strawberry.UNSET, config)) == []
    assert list(iter_active_fields(_Set, 42, config)) == []
