"""Tests for the neutral set-input traversal substrate (``utils/input_values.py``).

This module single-sites the runtime walk over a generated Strawberry input
value that the filter / order normalizers and the permission walkers had each
spelled inline; a divergence in the active-input decision between those copies
is a real bug class. These tests pin the shared mechanics
directly: the ``None`` / ``UNSET`` active-value rule, the dict-vs-dataclass walk,
the leaf / related / logic classification, and the order-side top-level-list
flattening. The deep family behavior (filter form-data, order flat tuples,
permission dispatch) lives in the ``filters`` / ``orders`` / ``utils.permissions``
suites that consume this substrate.
"""

from collections.abc import Mapping

import pytest
import strawberry

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters.sets import FilterSet
from django_strawberry_framework.utils.input_values import (
    DEFAULT_SET_INPUT_TRAVERSAL_DEPTH,
    LEAF,
    LOGIC,
    RELATED,
    SetInputTraversal,
    input_field_value,
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
    """The dataclass and raw-dict shapes yield the same records."""

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


def test_dict_subclass_overrides_cannot_replace_the_shared_walk():
    """The traversal uses the real dict operations, not consumer overrides."""

    class _HostileDict(dict):
        def items(self):
            raise RuntimeError("hostile items")

        def get(self, key, default=None):
            raise RuntimeError("hostile get")

    value = _HostileDict(name="x")
    assert iter_input_items(value) == [("name", "x")]
    assert input_field_value(value, "name") == "x"


def test_malformed_dataclass_metadata_fails_closed_with_configuration_error():
    """An unreadable ``__dataclass_fields__`` is a typed traversal error, not a raw one."""

    class _HostileMetadata:
        @property
        def __dataclass_fields__(self):
            raise RuntimeError("hostile metadata")

    with pytest.raises(ConfigurationError, match="dataclass metadata could not be read"):
        iter_input_items(_HostileMetadata())


def test_non_string_input_keys_fail_closed_before_permission_dispatch():
    """Input field names must be strings; a non-string key is refused at the walk."""
    with pytest.raises(ConfigurationError, match="field names must be strings"):
        iter_input_items({1: "unexpected"})


def test_hostile_list_iteration_cannot_escape_the_order_walk():
    """The top-level-list walk reads real list elements, not a subclass iterator."""

    class _HostileList(list):
        def __iter__(self):
            raise RuntimeError("hostile list iterator")

    class _Set:
        related_orders = {}

    value = _HostileList([{"title": "x"}])
    config = SetInputTraversal(
        field_specs={},
        related_attr="related_orders",
        handle_top_level_list=True,
    )
    fields = list(iter_active_fields(_Set, value, config))
    assert [(field.python_attr, field.raw_value) for field in fields] == [("title", "x")]


def test_nested_order_lists_fail_closed_instead_of_recursing_or_no_oping():
    """A list element must be a mapping or dataclass; a nested list is rejected."""

    class _Set:
        related_orders = {}

    config = SetInputTraversal(
        field_specs={},
        related_attr="related_orders",
        handle_top_level_list=True,
    )
    with pytest.raises(ConfigurationError, match="list elements must be mapping or dataclass"):
        list(iter_active_fields(_Set, [[{"title": "x"}]], config))


def test_hostile_field_spec_mapping_fails_closed_with_configuration_error():
    """A field-spec mapping that cannot answer a lookup aborts the walk with a typed error."""

    class _HostileMap(dict):
        def get(self, key, default=None):
            raise RuntimeError("hostile field-spec lookup")

    class _Set:
        related_orders = {}

    config = SetInputTraversal(
        field_specs=_HostileMap(),
        related_attr="related_orders",
        handle_top_level_list=True,
    )
    with pytest.raises(ConfigurationError, match="field provenance could not be resolved"):
        list(iter_active_fields(_Set, [{"title": "x"}], config))


def test_dataclass_metadata_must_be_an_enumerable_mapping():
    """``__dataclass_fields__`` must be a mapping and must enumerate without raising."""

    class _NotAMapping:
        __dataclass_fields__ = ("name",)

    class _UnreadableMapping(Mapping):
        def __getitem__(self, key):
            raise KeyError(key)

        def __iter__(self):
            raise RuntimeError("hostile field enumeration")

        def __len__(self):
            return 1

    class _UnreadableDataclass:
        __dataclass_fields__ = _UnreadableMapping()

    with pytest.raises(ConfigurationError, match="metadata is not a mapping"):
        iter_input_items(_NotAMapping())
    with pytest.raises(ConfigurationError, match="dataclass fields could not be enumerated"):
        iter_input_items(_UnreadableDataclass())


def test_dataclass_and_object_field_read_failures_are_typed():
    """Both the dataclass walk and the single-field read report their own typed failure."""

    class _UnreadableDataclass:
        __dataclass_fields__ = {"name": object()}

        @property
        def name(self):
            raise RuntimeError("hostile dataclass field")

    class _UnreadableObject:
        def __getattribute__(self, name):
            if name == "name":
                raise RuntimeError("hostile object field")
            return super().__getattribute__(name)

    with pytest.raises(ConfigurationError, match="dataclass field value could not be read"):
        iter_input_items(_UnreadableDataclass())
    with pytest.raises(ConfigurationError, match=r": a field value could not be read"):
        input_field_value(_UnreadableObject(), "name")


def test_active_field_configuration_and_related_metadata_fail_closed():
    """An unreadable traversal config, or unreadable/non-mapping related declarations, raise."""

    class _UnreadableConfig:
        @property
        def handle_top_level_list(self):
            raise RuntimeError("hostile traversal config")

        unset_sentinel = None

    class _UnreadableSentinelConfig:
        @property
        def unset_sentinel(self):
            raise RuntimeError("hostile unset_sentinel")

        handle_top_level_list = False

    class _HostileSetMeta(type):
        def __getattribute__(cls, name):
            if name == "related_orders":
                raise RuntimeError("hostile related declarations")
            return super().__getattribute__(name)

    class _UnreadableSet(metaclass=_HostileSetMeta):
        pass

    with pytest.raises(ConfigurationError, match="configuration could not be read"):
        list(iter_active_fields(object, {"name": "x"}, _UnreadableConfig()))
    with pytest.raises(ConfigurationError, match="configuration could not be read"):
        list(iter_active_fields(object, {"name": "x"}, _UnreadableSentinelConfig()))

    config = SetInputTraversal(field_specs={}, related_attr="related_orders")
    with pytest.raises(ConfigurationError, match="related-field declarations could not be read"):
        list(iter_active_fields(_UnreadableSet, {"name": "x"}, config))

    class _InvalidSet:
        related_orders = []

    with pytest.raises(ConfigurationError, match="declarations are not a mapping"):
        list(iter_active_fields(_InvalidSet, {"name": "x"}, config))


def test_active_field_related_mapping_operations_fail_closed():
    """Membership and lookup on a related-declaration mapping each fail as typed errors."""

    class _UnreadableContains(Mapping):
        def __getitem__(self, key):
            return object()

        def __iter__(self):
            return iter(("name",))

        def __len__(self):
            return 1

        def __contains__(self, key):
            raise RuntimeError("hostile membership")

    class _UnreadableGetitem(_UnreadableContains):
        def __contains__(self, key):
            return True

        def __getitem__(self, key):
            raise RuntimeError("hostile related lookup")

    config = SetInputTraversal(field_specs={}, related_attr="related_orders")
    contains_set = type("ContainsSet", (), {"related_orders": _UnreadableContains()})
    lookup_set = type("LookupSet", (), {"related_orders": _UnreadableGetitem()})

    with pytest.raises(ConfigurationError, match="declarations could not be checked"):
        list(iter_active_fields(contains_set, {"name": "x"}, config))
    with pytest.raises(ConfigurationError, match="declaration could not be read"):
        list(iter_active_fields(lookup_set, {"name": "x"}, config))


def test_active_field_list_skips_inactive_elements_and_accepts_none_related_mapping():
    """Inactive list elements are dropped; an absent related mapping leaves every field a leaf."""

    class _Set:
        related_orders = None

    config = SetInputTraversal(
        field_specs={},
        related_attr="related_orders",
        handle_top_level_list=True,
    )

    fields = list(iter_active_fields(_Set, [None, {"name": "x"}], config))

    assert [(field.python_attr, field.kind) for field in fields] == [("name", LEAF)]


def test_input_field_value_reads_dict_and_dataclass_fields():
    """``input_field_value`` reads single fields or returns None for missing fields/non-walkable inputs."""
    assert input_field_value({"a": 10}, "a") == 10
    assert input_field_value({"a": 10}, "missing") is None
    assert input_field_value(None, "a") is None
    assert input_field_value(42, "a") is None

    @strawberry.input
    class _In:
        title: str = "item"

    assert input_field_value(_In(), "title") == "item"
    assert input_field_value(_In(), "missing") is None


def test_field_name_bypasses_hostile_str_subclass_str_override():
    """``_field_name`` safely normalizes string subclass keys without calling overridden __str__."""

    class _HostileStr(str):
        def __str__(self):
            raise RuntimeError("hostile __str__ override")

    key = _HostileStr("field_name")
    assert iter_input_items({key: "value"}) == [("field_name", "value")]
    assert input_field_value({key: "value"}, key) == "value"


def test_order_list_elements_reject_primitive_values():
    """When handle_top_level_list is True, non-mapping list elements raise ConfigurationError."""

    class _Set:
        related_orders = {}

    config = SetInputTraversal(
        field_specs={},
        related_attr="related_orders",
        handle_top_level_list=True,
    )
    with pytest.raises(
        ConfigurationError,
        match="Order input list elements must be mapping or dataclass values",
    ):
        list(iter_active_fields(_Set, ["string_element"], config))

    with pytest.raises(
        ConfigurationError,
        match="Order input list elements must be mapping or dataclass values",
    ):
        list(iter_active_fields(_Set, [123], config))


def test_default_set_input_traversal_depth():
    """DEFAULT_SET_INPUT_TRAVERSAL_DEPTH provides a neutral recursion ceiling across set families."""
    assert DEFAULT_SET_INPUT_TRAVERSAL_DEPTH == 8
    assert FilterSet._MAX_LOGIC_DEPTH == DEFAULT_SET_INPUT_TRAVERSAL_DEPTH
