"""Order input tests for Ordering enum, input materialization, reset, and normalization.

Covers ``INPUTS_MODULE_PATH``, the ``Ordering`` enum (members +
``resolve`` semantics for ``ASC`` / ``DESC`` / ``NULLS_FIRST`` /
``NULLS_LAST`` shapes), ``_input_type_name_for`` (the
``ClassBasedTypeNameMixin`` delegate), and ``materialize_input_class``
(write-to-module-global, idempotent re-write on the same pair,
``ConfigurationError`` on collision against a different class).

The sections below cover ``convert_order_field_to_input_annotation`` /
``normalize_input_value`` / ``clear_order_input_namespace`` /
``order_input_type``.
"""

from __future__ import annotations

import sys

import pytest
from django.db.models import F
from django.db.models.expressions import OrderBy

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.orders import Ordering, OrderSet
from django_strawberry_framework.orders.inputs import (
    INPUTS_MODULE_PATH,
    _input_type_name_for,
    _materialized_names,
    materialize_input_class,
)

# ---------------------------------------------------------------------------
# Module-path constant
# ---------------------------------------------------------------------------


def test_inputs_module_path_constant():
    """The hoisted constant matches the actual dotted path of ``inputs.py``."""
    assert INPUTS_MODULE_PATH == "django_strawberry_framework.orders.inputs"


# ---------------------------------------------------------------------------
# _input_type_name_for delegate
# ---------------------------------------------------------------------------


def test_input_type_name_for_returns_classname_inputtype():
    """The delegate flows through ``ClassBasedTypeNameMixin.type_name_for``."""

    class BookOrder(OrderSet):
        pass

    assert _input_type_name_for(BookOrder) == "BookOrderInputType"


# ---------------------------------------------------------------------------
# Ordering enum
# ---------------------------------------------------------------------------


def test_ordering_enum_has_six_members():
    """All six members from spec-028 Decision 5 are present."""
    assert {m.name for m in Ordering} == {
        "ASC",
        "DESC",
        "ASC_NULLS_FIRST",
        "ASC_NULLS_LAST",
        "DESC_NULLS_FIRST",
        "DESC_NULLS_LAST",
    }


def test_ordering_member_values_are_string_names():
    """Members carry string values matching their names (spec-028 Decision 5)."""
    assert Ordering.ASC.value == "ASC"
    assert Ordering.DESC.value == "DESC"
    assert Ordering.ASC_NULLS_FIRST.value == "ASC_NULLS_FIRST"
    assert Ordering.ASC_NULLS_LAST.value == "ASC_NULLS_LAST"
    assert Ordering.DESC_NULLS_FIRST.value == "DESC_NULLS_FIRST"
    assert Ordering.DESC_NULLS_LAST.value == "DESC_NULLS_LAST"


def test_ordering_is_ascending_classifies_all_six_members():
    """``is_ascending`` is the single ASC/DESC discriminator (resolve + to-many Min/Max)."""
    assert Ordering.ASC.is_ascending is True
    assert Ordering.ASC_NULLS_FIRST.is_ascending is True
    assert Ordering.ASC_NULLS_LAST.is_ascending is True
    assert Ordering.DESC.is_ascending is False
    assert Ordering.DESC_NULLS_FIRST.is_ascending is False
    assert Ordering.DESC_NULLS_LAST.is_ascending is False


def test_ordering_resolve_asc_returns_orderby_with_no_nulls_clause():
    """Bare ``ASC`` leaves both ``nulls_first`` and ``nulls_last`` as ``None``."""
    expr = Ordering.ASC.resolve("name")
    assert isinstance(expr, OrderBy)
    assert expr.descending is False
    assert expr.nulls_first is None
    assert expr.nulls_last is None


def test_ordering_resolve_desc_returns_orderby_with_descending_true():
    """Bare ``DESC`` produces ``descending=True`` with no nulls clause."""
    expr = Ordering.DESC.resolve("name")
    assert isinstance(expr, OrderBy)
    assert expr.descending is True
    assert expr.nulls_first is None
    assert expr.nulls_last is None


def test_ordering_resolve_wraps_value_in_f_expression():
    """``resolve(value)`` produces ``F(value)``-backed expressions."""
    expr = Ordering.ASC.resolve("shelf__code")
    # ``OrderBy.expression`` holds the wrapped ``F("shelf__code")``.
    assert isinstance(expr.expression, F)
    assert expr.expression.name == "shelf__code"


def test_ordering_resolve_nulls_variants():
    """``resolve(value)`` sets nulls_first and nulls_last flags appropriately."""
    asc_first = Ordering.ASC_NULLS_FIRST.resolve("col")
    assert isinstance(asc_first, OrderBy)
    assert asc_first.descending is False
    assert asc_first.nulls_first is True
    assert asc_first.nulls_last is None

    asc_last = Ordering.ASC_NULLS_LAST.resolve("col")
    assert isinstance(asc_last, OrderBy)
    assert asc_last.descending is False
    assert asc_last.nulls_first is None
    assert asc_last.nulls_last is True

    desc_first = Ordering.DESC_NULLS_FIRST.resolve("col")
    assert isinstance(desc_first, OrderBy)
    assert desc_first.descending is True
    assert desc_first.nulls_first is True
    assert desc_first.nulls_last is None

    desc_last = Ordering.DESC_NULLS_LAST.resolve("col")
    assert isinstance(desc_last, OrderBy)
    assert desc_last.descending is True
    assert desc_last.nulls_first is None
    assert desc_last.nulls_last is True


# ---------------------------------------------------------------------------
# materialize_input_class
# ---------------------------------------------------------------------------


@pytest.fixture
def _materialization_cleanup():
    """Strip any test-emitted ledger / module-global state after each test."""
    names_before = set(_materialized_names.keys())
    yield
    module = sys.modules[INPUTS_MODULE_PATH]
    for name in list(_materialized_names.keys()):
        if name in names_before:
            continue
        _materialized_names.pop(name, None)
        if hasattr(module, name):
            delattr(module, name)


def test_materialize_input_class_writes_to_module_global(_materialization_cleanup):
    """Materialization pins the class in ``sys.modules[INPUTS_MODULE_PATH]``."""

    class Foo:
        pass

    materialize_input_class("FooInputType", Foo)
    module = sys.modules[INPUTS_MODULE_PATH]
    assert module.FooInputType is Foo
    assert _materialized_names["FooInputType"] is Foo


def test_materialize_input_class_is_idempotent_on_same_pair(_materialization_cleanup):
    """Second call with the same ``(name, cls)`` short-circuits to no-op."""

    class Foo:
        pass

    materialize_input_class("FooInputType", Foo)
    materialize_input_class("FooInputType", Foo)  # idempotent.
    assert _materialized_names["FooInputType"] is Foo


def test_materialize_input_class_raises_on_collision(_materialization_cleanup):
    """A second class under the same name raises ``ConfigurationError``."""

    class FooA:
        pass

    class FooB:
        pass

    materialize_input_class("FooInputType", FooA)
    with pytest.raises(ConfigurationError) as exc_info:
        materialize_input_class("FooInputType", FooB)
    message = str(exc_info.value)
    assert "FooA" in message
    assert "FooB" in message


# ---------------------------------------------------------------------------
# convert_order_field_to_input_annotation
# ---------------------------------------------------------------------------


def test_convert_order_field_to_input_annotation_returns_ordering_or_none():
    """``Ordering | None`` regardless of the ``model_field`` argument."""
    from typing import get_args

    from apps.library.models import Book

    from django_strawberry_framework.orders.inputs import (
        convert_order_field_to_input_annotation,
    )

    title_field = Book._meta.get_field("title")
    annotation = convert_order_field_to_input_annotation(title_field, None)
    args = set(get_args(annotation))
    assert Ordering in args
    assert type(None) in args
    # Also accepts ``None`` for ``model_field`` -- same shape.
    annotation2 = convert_order_field_to_input_annotation(None, None)
    args2 = set(get_args(annotation2))
    assert args == args2


# ---------------------------------------------------------------------------
# normalize_input_value
# ---------------------------------------------------------------------------


def test_normalize_input_value_walks_nested_relatedorder_into_flat_field_paths():
    """Nested ``RelatedOrder`` input produces ``shelf__code`` flat paths."""
    from apps.library.models import Book, Shelf

    from django_strawberry_framework.orders import OrderSet, RelatedOrder
    from django_strawberry_framework.orders.factories import OrderArgumentsFactory
    from django_strawberry_framework.orders.inputs import normalize_input_value

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    factory = OrderArgumentsFactory(BookOrder)
    BookInput = factory.arguments
    ShelfInput = OrderArgumentsFactory.input_object_types["ShelfOrderInputType"]
    input_value = BookInput(shelf=ShelfInput(code=Ordering.ASC))
    flat = normalize_input_value(BookOrder, input_value)
    assert flat == [("shelf__code", Ordering.ASC)]


def test_normalize_input_value_passes_through_empty_list():
    """An empty top-level list yields an empty flat list."""
    from apps.library.models import Book

    from django_strawberry_framework.orders import OrderSet
    from django_strawberry_framework.orders.factories import OrderArgumentsFactory
    from django_strawberry_framework.orders.inputs import normalize_input_value

    class BookOrderEmpty(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    OrderArgumentsFactory(BookOrderEmpty).arguments  # populate _field_specs.
    assert normalize_input_value(BookOrderEmpty, []) == []


def test_normalize_input_value_skips_null_direction_leaves():
    """A leaf with ``direction=None`` is skipped (active-input-only)."""
    from apps.library.models import Book

    from django_strawberry_framework.orders import OrderSet
    from django_strawberry_framework.orders.factories import OrderArgumentsFactory
    from django_strawberry_framework.orders.inputs import normalize_input_value

    class BookOrderNull(OrderSet):
        class Meta:
            model = Book
            fields = ["title", "subtitle"]

    factory = OrderArgumentsFactory(BookOrderNull)
    BookInput = factory.arguments
    flat = normalize_input_value(
        BookOrderNull,
        [BookInput(title=None, subtitle=Ordering.ASC)],
    )
    # ``title=None`` -> skipped; ``subtitle=Ordering.ASC`` -> emitted.
    assert flat == [("subtitle", Ordering.ASC)]


def test_normalize_input_value_handles_top_level_list_of_dataclass_elements():
    """Multi-element top-level lists are flattened in declaration order."""
    from apps.library.models import Book

    from django_strawberry_framework.orders import OrderSet
    from django_strawberry_framework.orders.factories import OrderArgumentsFactory
    from django_strawberry_framework.orders.inputs import normalize_input_value

    class BookOrderMulti(OrderSet):
        class Meta:
            model = Book
            fields = ["title", "subtitle"]

    factory = OrderArgumentsFactory(BookOrderMulti)
    BookInput = factory.arguments
    flat = normalize_input_value(
        BookOrderMulti,
        [BookInput(title=Ordering.ASC), BookInput(subtitle=Ordering.DESC_NULLS_LAST)],
    )
    assert flat == [("title", Ordering.ASC), ("subtitle", Ordering.DESC_NULLS_LAST)]


def test_normalize_input_value_returns_empty_for_none_input():
    """``None`` input -> ``[]``."""
    from django_strawberry_framework.orders import OrderSet
    from django_strawberry_framework.orders.inputs import normalize_input_value

    assert normalize_input_value(OrderSet, None) == []


def test_normalize_input_value_builds_field_specs_for_direct_mapping_input():
    """Direct mapping callers must not silently lose an active order field."""
    from apps.library.models import Book

    from django_strawberry_framework.orders import Ordering, OrderSet
    from django_strawberry_framework.orders.inputs import normalize_input_value

    class DirectBookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    assert normalize_input_value(DirectBookOrder, {"title": Ordering.ASC}) == [
        ("title", Ordering.ASC),
    ]


def test_normalize_input_value_raw_dict_matches_dataclass_form():
    """A raw-dict order input flattens identically to the dataclass form.

    ``normalize_input_value`` routes through the shared
    ``utils/input_values.py::iter_active_fields`` classifier, whose
    ``iter_input_items`` walk accepts the dict shape as well as the Strawberry
    input dataclass. Both forms (including a nested ``RelatedOrder`` branch)
    must produce the same flattened ``(field_path, direction)`` tuples.
    """
    from apps.library.models import Book, Shelf

    from django_strawberry_framework.orders import OrderSet, RelatedOrder
    from django_strawberry_framework.orders.factories import OrderArgumentsFactory
    from django_strawberry_framework.orders.inputs import normalize_input_value

    # Distinct class names so the ``OrderArgumentsFactory`` collision registry
    # (not reset between tests in this module) does not clash with the sibling
    # ``BookOrder`` / ``ShelfOrder`` fixtures above.
    class ShelfOrderDictEq(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrderDictEq(OrderSet):
        shelf = RelatedOrder(ShelfOrderDictEq, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    factory = OrderArgumentsFactory(BookOrderDictEq)
    BookInput = factory.arguments
    ShelfInput = OrderArgumentsFactory.input_object_types["ShelfOrderDictEqInputType"]

    dataclass_form = normalize_input_value(
        BookOrderDictEq,
        BookInput(title=Ordering.ASC, shelf=ShelfInput(code=Ordering.DESC)),
    )
    dict_form = normalize_input_value(
        BookOrderDictEq,
        {"title": Ordering.ASC, "shelf": {"code": Ordering.DESC}},
    )
    assert dataclass_form == dict_form == [("title", Ordering.ASC), ("shelf__code", Ordering.DESC)]


# ---------------------------------------------------------------------------
# build_input_class
# ---------------------------------------------------------------------------


def test_build_input_class_decorates_with_strawberry_input():
    """The returned class carries Strawberry's ``__strawberry_definition__``."""
    from django_strawberry_framework.orders.inputs import build_input_class

    cls = build_input_class("FooOrderInputType", [("title", Ordering | None, None)])
    assert hasattr(cls, "__strawberry_definition__")
    # The annotation is preserved.
    fields = {f.python_name: f for f in cls.__strawberry_definition__.fields}
    assert "title" in fields


def test_build_input_class_handles_python_attr_to_graphql_alias_mapping():
    """``name=`` is preserved through the decorator so ``shelf_code`` -> ``shelfCode``."""
    from django_strawberry_framework.orders.inputs import build_input_class

    cls = build_input_class(
        "AliasOrderInputType",
        [("shelf_code", Ordering | None, {"name": "shelfCode"})],
    )
    fields = {f.python_name: f for f in cls.__strawberry_definition__.fields}
    assert fields["shelf_code"].graphql_name == "shelfCode"


# ---------------------------------------------------------------------------
# _build_input_fields populates _field_specs
# ---------------------------------------------------------------------------


def test_field_specs_populated_by_build_input_fields_for_leaf():
    """Leaf field -> ``FieldSpec(python_attr, graphql_name, django_source_path)``."""
    from apps.library.models import Book

    from django_strawberry_framework.orders import OrderSet
    from django_strawberry_framework.orders.inputs import (
        FieldSpec,
        _build_input_fields,
        _field_specs,
    )

    class BookOrderLeafSpec(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    _build_input_fields(BookOrderLeafSpec, None)
    spec = _field_specs[(BookOrderLeafSpec, "title")]
    assert isinstance(spec, FieldSpec)
    assert spec.python_attr == "title"
    assert spec.graphql_name == "title"
    assert spec.django_source_path == "title"


def test_field_specs_populated_by_build_input_fields_for_flat_shorthand():
    """``Meta.fields = ["shelf__code"]`` -> python attr ``shelf_code`` + graphql alias ``shelfCode``."""
    from apps.library.models import Book

    from django_strawberry_framework.orders import OrderSet
    from django_strawberry_framework.orders.inputs import _build_input_fields, _field_specs

    class BookOrderFlat(OrderSet):
        class Meta:
            model = Book
            fields = ["shelf__code"]

    _build_input_fields(BookOrderFlat, None)
    spec = _field_specs[(BookOrderFlat, "shelf_code")]
    assert spec.python_attr == "shelf_code"
    assert spec.graphql_name == "shelfCode"
    assert spec.django_source_path == "shelf__code"


def test_field_specs_populated_by_build_input_fields_for_relatedorder():
    """``RelatedOrder`` -> ``FieldSpec.django_source_path`` is the relation name."""
    from apps.library.models import Book, Shelf

    from django_strawberry_framework.orders import OrderSet, RelatedOrder
    from django_strawberry_framework.orders.inputs import _build_input_fields, _field_specs

    class ShelfOrderRelSpec(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrderRelSpec(OrderSet):
        shelf = RelatedOrder(ShelfOrderRelSpec, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    _build_input_fields(BookOrderRelSpec, None)
    spec = _field_specs[(BookOrderRelSpec, "shelf")]
    assert spec.django_source_path == "shelf"


# ---------------------------------------------------------------------------
# clear_order_input_namespace
# ---------------------------------------------------------------------------


@pytest.fixture
def _namespace_cleanup():
    """Strip test-emitted ledger / module-global state + factory caches."""
    from django_strawberry_framework.orders.factories import OrderArgumentsFactory
    from django_strawberry_framework.orders.inputs import (
        INPUTS_MODULE_PATH,
        _field_specs,
        _materialized_names,
    )

    names_before = set(_materialized_names.keys())
    yield
    module = sys.modules[INPUTS_MODULE_PATH]
    for name in list(_materialized_names.keys()):
        if name in names_before:
            continue
        _materialized_names.pop(name, None)
        if hasattr(module, name):
            delattr(module, name)
    _field_specs.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()


def test_clear_order_input_namespace_resets_materialized_names_ledger(_namespace_cleanup):
    """``_materialized_names`` is emptied."""
    from django_strawberry_framework.orders.inputs import (
        _materialized_names,
        clear_order_input_namespace,
        materialize_input_class,
    )

    class FooBar:
        pass

    materialize_input_class("FooBarOrderInputType", FooBar)
    assert "FooBarOrderInputType" in _materialized_names
    clear_order_input_namespace()
    assert _materialized_names == {}


def test_clear_order_input_namespace_leaves_module_globals_parked(_namespace_cleanup):
    """The materialized class stays on the module dict per spec-028 Decision 9."""
    from django_strawberry_framework.orders.inputs import (
        INPUTS_MODULE_PATH,
        clear_order_input_namespace,
        materialize_input_class,
    )

    class FooParked:
        pass

    materialize_input_class("FooParkedOrderInputType", FooParked)
    module = sys.modules[INPUTS_MODULE_PATH]
    assert module.FooParkedOrderInputType is FooParked
    clear_order_input_namespace()
    # Class object stays parked -- parking is load-bearing for the lazy
    # Strawberry annotation that still resolves this name.
    assert module.FooParkedOrderInputType is FooParked


def test_clear_order_input_namespace_clears_factory_class_level_caches(_namespace_cleanup):
    """``OrderArgumentsFactory`` class-level caches are emptied."""
    from django_strawberry_framework.orders.factories import OrderArgumentsFactory
    from django_strawberry_framework.orders.inputs import clear_order_input_namespace

    class _FakeOrder:
        pass

    class _FakeInput:
        pass

    OrderArgumentsFactory.input_object_types["FakeOrderInputType"] = _FakeInput
    OrderArgumentsFactory._type_orderset_registry["FakeOrderInputType"] = _FakeOrder
    clear_order_input_namespace()
    assert OrderArgumentsFactory.input_object_types == {}
    assert OrderArgumentsFactory._type_orderset_registry == {}


def test_clear_order_input_namespace_resets_orderset_subclass_binding_state(_namespace_cleanup):
    """Every ``OrderSet`` subclass's phase-2.5 binding slots are reset."""
    from collections import OrderedDict

    from django_strawberry_framework.orders import OrderSet
    from django_strawberry_framework.orders.inputs import clear_order_input_namespace

    class BindStateOrder(OrderSet):
        pass

    BindStateOrder._owner_definition = "stub_owner"  # type: ignore[assignment]
    BindStateOrder._expanded_fields = OrderedDict([("title", None)])
    BindStateOrder._is_expanding_fields = True
    assert "_owner_definition" in BindStateOrder.__dict__
    assert "_expanded_fields" in BindStateOrder.__dict__
    assert "_is_expanding_fields" in BindStateOrder.__dict__
    clear_order_input_namespace()
    assert "_owner_definition" not in BindStateOrder.__dict__
    assert "_expanded_fields" not in BindStateOrder.__dict__
    assert "_is_expanding_fields" not in BindStateOrder.__dict__
    # Inherited default restored.
    assert BindStateOrder._owner_definition is None


# ---------------------------------------------------------------------------
# order_input_type consumer helper
# ---------------------------------------------------------------------------


def test_order_input_type_returns_element_annotation_for_orderset_subclass():
    """``order_input_type(MyOrder)`` returns ``Annotated[ForwardRef("MyOrderInputType"), ...]``."""
    from typing import ForwardRef, get_args

    from django_strawberry_framework.orders import OrderSet, order_input_type

    class HelperOrderA(OrderSet):
        pass

    result = order_input_type(HelperOrderA)
    args = get_args(result)
    # First positional arg of Annotated is the (string-wrapped) forward
    # reference; Python stores it as a ForwardRef when the position is a
    # string literal.
    forward = args[0]
    name = forward.__forward_arg__ if isinstance(forward, ForwardRef) else str(forward)
    assert name == "HelperOrderAInputType"


def test_order_input_type_raises_typeerror_for_non_orderset():
    """Passing a non-``OrderSet`` argument raises ``TypeError``."""
    from django_strawberry_framework.orders import order_input_type

    with pytest.raises(TypeError):
        order_input_type(int)


def test_order_input_type_records_orderset_into_helper_referenced_set():
    """The helper writes its argument into ``_helper_referenced_ordersets``."""
    from django_strawberry_framework.orders import (
        OrderSet,
        _helper_referenced_ordersets,
        order_input_type,
    )

    class HelperOrderB(OrderSet):
        pass

    _helper_referenced_ordersets.discard(HelperOrderB)
    order_input_type(HelperOrderB)
    assert HelperOrderB in _helper_referenced_ordersets
    # Cleanup.
    _helper_referenced_ordersets.discard(HelperOrderB)


def test_order_input_type_is_idempotent_under_repeated_calls():
    """Calling the helper multiple times keeps the ledger size at one."""
    from django_strawberry_framework.orders import (
        OrderSet,
        _helper_referenced_ordersets,
        order_input_type,
    )

    class HelperOrderC(OrderSet):
        pass

    _helper_referenced_ordersets.discard(HelperOrderC)
    initial_size = len(_helper_referenced_ordersets)
    order_input_type(HelperOrderC)
    order_input_type(HelperOrderC)
    order_input_type(HelperOrderC)
    assert HelperOrderC in _helper_referenced_ordersets
    # The set grew by exactly 1 (set semantics dedup repeat adds).
    assert len(_helper_referenced_ordersets) == initial_size + 1
    _helper_referenced_ordersets.discard(HelperOrderC)


# ---------------------------------------------------------------------------
# registry.clear() integration
# ---------------------------------------------------------------------------


def test_registry_clear_invokes_clear_order_input_namespace():
    """``registry.clear()`` co-clears the order-input namespace ledgers."""
    import subprocess

    from django_strawberry_framework.orders.factories import OrderArgumentsFactory
    from django_strawberry_framework.orders.inputs import (
        _field_specs,
        materialize_input_class,
    )
    from django_strawberry_framework.registry import registry

    class _LedgerStub:
        pass

    materialize_input_class("LedgerStubOrderInputType", _LedgerStub)
    OrderArgumentsFactory.input_object_types["LedgerStubOrderInputType"] = _LedgerStub
    OrderArgumentsFactory._type_orderset_registry["LedgerStubOrderInputType"] = _LedgerStub
    _field_specs[("stub", "title")] = "fake"

    registry.clear()

    # Ledgers cleared.
    assert _materialized_names == {}
    assert _field_specs == {}
    assert OrderArgumentsFactory.input_object_types == {}
    assert OrderArgumentsFactory._type_orderset_registry == {}

    # Module global is left parked (parking is load-bearing per spec-028 Decision 9).
    module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(module, "LedgerStubOrderInputType")
    delattr(module, "LedgerStubOrderInputType")

    # Silence unused-import detector for the subprocess reference; see the
    # sibling test below which uses ``subprocess``.
    assert subprocess.run is not None


def test_registry_clear_clears_helper_referenced_ordersets():
    """``registry.clear()`` empties ``_helper_referenced_ordersets`` (separate block)."""
    from django_strawberry_framework.orders import (
        OrderSet,
        _helper_referenced_ordersets,
        order_input_type,
    )
    from django_strawberry_framework.registry import registry

    class HelperLedgerOrder(OrderSet):
        pass

    order_input_type(HelperLedgerOrder)
    assert HelperLedgerOrder in _helper_referenced_ordersets

    registry.clear()

    assert _helper_referenced_ordersets == set()


def test_registry_clear_works_without_orders_imported():
    """``registry.clear()`` must not raise when orders package was never imported."""
    import subprocess
    from pathlib import Path

    fakeshop = Path(__file__).resolve().parents[2] / "examples" / "fakeshop"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import django; "
                "import os; "
                f"import sys; sys.path.insert(0, {str(fakeshop)!r}); "
                "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); "
                "django.setup(); "
                "import django_strawberry_framework.registry as r; "
                "assert 'django_strawberry_framework.orders' not in sys.modules; "
                "r.registry.clear()"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"subprocess failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# inputs.py edge-case branches
# ---------------------------------------------------------------------------


def test_camel_case_returns_input_when_split_yields_no_parts():
    """Covers the all-underscore passthrough behind the ``_camel_case`` alias.

    The guard is ``utils/strings.py::graphql_camel_name`` #"if not core:".
    ``_camel_case`` strips the surrounding underscores before splitting;
    a name that strips to an empty core (``""`` / ``"_"`` / ``"__"``)
    returns ``name`` unchanged.
    """
    from django_strawberry_framework.orders.inputs import _camel_case

    assert _camel_case("") == ""
    assert _camel_case("_") == "_"
    assert _camel_case("__") == "__"


def test_build_input_class_threads_description_through_strawberry_field():
    """Covers the ``description`` kwarg threading through ``strawberry.field``.

    ``build_input_class`` is the ``orders/inputs.py`` alias of
    ``utils/inputs.py::build_strawberry_input_class``, which pops
    ``description`` from the field kwargs and forwards it to
    ``strawberry.field(description=...)`` so the GraphQL SDL carries the
    description.
    """
    from django_strawberry_framework.orders.inputs import build_input_class

    cls = build_input_class(
        "DescribedOrderInputType",
        [("foo", Ordering | None, {"description": "the foo direction"})],
    )
    fields = {f.python_name: f for f in cls.__strawberry_definition__.fields}
    assert fields["foo"].description == "the foo direction"


def test_normalize_input_value_returns_empty_for_non_dataclass_non_list_non_none_input():
    """Covers the non-walkable-input short-circuit to an empty list.

    ``utils/input_values.py::iter_input_items`` returns ``None`` for a
    non-list, non-None object that lacks ``__dataclass_fields__``, and
    ``utils/input_values.py::iter_active_fields`` #"if items is None:"
    then yields nothing, so ``normalize_input_value`` returns ``[]``. The
    orderset class is not consulted for this guard, so any existing
    ``OrderSet`` subclass works.
    """
    from django_strawberry_framework.orders.inputs import normalize_input_value

    class _NormalizeNoDataclassOrder(OrderSet):
        pass

    # Plain object -- no ``__dataclass_fields__``.
    assert normalize_input_value(_NormalizeNoDataclassOrder, object()) == []


def test_normalize_input_value_skips_attrs_with_no_field_spec_entry():
    """Covers ``orders/inputs.py::normalize_input_value`` #"if field.spec is None:".

    The defensive skip: when the dataclass input carries an attribute
    that has no corresponding ``_field_specs`` entry for the orderset
    class, the walker skips it silently.
    """
    import dataclasses

    from apps.library.models import Book

    from django_strawberry_framework.orders.inputs import normalize_input_value

    class _OrderWithSpecificFields(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    @dataclasses.dataclass
    class _StubInputWithExtraAttr:
        title: Ordering | None = None
        unmapped_extra_attr: Ordering | None = None

    result = normalize_input_value(
        _OrderWithSpecificFields,
        _StubInputWithExtraAttr(unmapped_extra_attr=Ordering.ASC),
    )
    assert result == []


def test_normalize_input_value_builds_field_specs_for_model_free_orderset():
    """Model-free OrderSet direct callers must lazily build specs and normalize."""
    from django_strawberry_framework.orders.inputs import (
        clear_order_input_namespace,
        normalize_input_value,
    )

    clear_order_input_namespace()

    class ModelFreeOrder(OrderSet):
        class Meta:
            fields = ["title", "shelf__code"]

    data = {"title": Ordering.ASC, "shelf_code": Ordering.DESC}
    normalized = normalize_input_value(ModelFreeOrder, data)
    assert ("title", Ordering.ASC) in normalized
    assert ("shelf__code", Ordering.DESC) in normalized


def test_normalize_input_value_ignores_unset_sentinel_in_mappings_and_lists():
    """strawberry.UNSET values in dicts, lists, and nested structures are inactive."""
    from apps.library.models import Book, Shelf
    from strawberry import UNSET

    from django_strawberry_framework.orders import RelatedOrder
    from django_strawberry_framework.orders.inputs import (
        clear_order_input_namespace,
        normalize_input_value,
    )

    clear_order_input_namespace()

    class ChildOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class ParentOrder(OrderSet):
        shelf = RelatedOrder(ChildOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title", "subtitle"]

    assert normalize_input_value(ParentOrder, UNSET) == []
    assert normalize_input_value(ParentOrder, [UNSET]) == []
    assert normalize_input_value(ParentOrder, [None, UNSET, None]) == []
    assert normalize_input_value(ParentOrder, {"title": UNSET, "subtitle": Ordering.ASC}) == [
        ("subtitle", Ordering.ASC),
    ]
    assert normalize_input_value(ParentOrder, {"shelf": {"code": UNSET}}) == []
    assert normalize_input_value(ParentOrder, {"shelf": {"code": Ordering.ASC}}) == [
        ("shelf__code", Ordering.ASC),
    ]


def test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration():
    """The warm-up gate asks the family classifier, not a hardcoded UNSET.

    ``_ensure_field_specs`` answers "is anything supplied?" through
    ``orderset_cls._input_traversal()`` -- the same derived grammar the
    normalizer and the permission walkers consume -- so a consumer subclass
    overriding ``_permission.traversal.unset_sentinel`` gets ONE classification
    everywhere. With the old hardcoded gate, a ``UNSET``-valued field was
    invisible to warm-up, so specs were never built and the normalizer
    silently discarded the field while its permission gate still fired.
    """
    from dataclasses import replace

    from apps.library.models import Book
    from strawberry import UNSET

    from django_strawberry_framework.orders.inputs import (
        clear_order_input_namespace,
        normalize_input_value,
    )

    clear_order_input_namespace()
    marker = object()
    fired: list[str] = []

    class OverrideOrder(OrderSet):
        _permission = replace(
            OrderSet._permission,
            traversal=replace(OrderSet._permission.traversal, unset_sentinel=marker),
        )

        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        def check_title_permission(cls, request):
            fired.append(request)

    # The override IS the family's unsupplied rule end-to-end.
    assert normalize_input_value(OverrideOrder, {"title": marker}) == []
    assert fired == []

    # Fresh ledger so the warm-up decision below is observed on its own.
    clear_order_input_namespace()
    fired.clear()

    # ``UNSET`` is SUPPLIED under the override: the derived gate builds the
    # specs and the field reaches leaf validation (a loud refusal of the
    # non-direction) instead of the silent ``spec is None`` discard ...
    with pytest.raises(ConfigurationError, match="invalid order direction"):
        normalize_input_value(OverrideOrder, {"title": UNSET})
    # ... and the permission side classifies the identical input identically;
    # apply-time / gate-time agreement is the invariant this pins.
    OverrideOrder._run_permission_checks({"title": UNSET}, "request")
    assert fired == ["request"]


def test_normalize_input_value_rejects_invalid_direction_type():
    """Invalid non-Ordering direction values raise ConfigurationError."""
    from apps.library.models import Book

    from django_strawberry_framework.orders.inputs import (
        clear_order_input_namespace,
        normalize_input_value,
    )

    clear_order_input_namespace()

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    with pytest.raises(ConfigurationError, match="received invalid order direction 'ASC'"):
        normalize_input_value(BookOrder, {"title": "ASC"})

    with pytest.raises(ConfigurationError, match="received invalid order direction 123"):
        normalize_input_value(BookOrder, {"title": 123})


def test_normalize_input_value_skips_related_branch_when_child_orderset_is_none(
    _namespace_cleanup,
):
    """Covers ``orders/inputs.py::normalize_input_value`` #"if child_orderset is None:".

    The placeholder-branch skip: when a ``RelatedOrder`` resolves to
    ``None``, the walker skips the branch silently rather than recursing
    into it.
    """
    import dataclasses

    from apps.library.models import Book

    from django_strawberry_framework.orders import OrderSet, RelatedOrder
    from django_strawberry_framework.orders.factories import OrderArgumentsFactory
    from django_strawberry_framework.orders.inputs import normalize_input_value

    class _TargetNoneChildOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class _ParentNoneChildOrder(OrderSet):
        shelf = RelatedOrder(_TargetNoneChildOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    # Populate ``_field_specs`` for both ordersets.
    OrderArgumentsFactory(_ParentNoneChildOrder).arguments

    # Force the related order's target to ``None`` so the
    # ``child_orderset is None`` guard fires.
    _ParentNoneChildOrder.related_orders["shelf"]._orderset = None

    @dataclasses.dataclass
    class _ChildStub:
        title: Ordering | None = None

    @dataclasses.dataclass
    class _ParentStub:
        title: Ordering | None = None
        shelf: object = None

    parent = _ParentStub(shelf=_ChildStub(title=Ordering.ASC))
    result = normalize_input_value(_ParentNoneChildOrder, parent)
    # The shelf branch is skipped (child orderset is None); only the
    # leaf entry (title=None) would emit, and it's skipped by the value-
    # is-None guard above the spec check.
    assert all(not path.startswith("shelf") for path, _ in result)


def test_iter_orderset_subclasses_dedupes_diamond_inheritance():
    """Covers ``utils/inputs.py::iter_set_subclasses`` #"if cls in seen:".

    The dedup runs behind the ``orders/inputs.py``
    ``_iter_orderset_subclasses`` alias. Mirror of
    ``tests/filters/test_inputs.py::test_iter_filterset_subclasses_dedupes_diamond_inheritance``.
    A diamond inheritance hierarchy (``B(A)``, ``C(A)``, ``D(B, C)``)
    walks ``D`` twice through ``__subclasses__()`` -- once via ``B`` and
    once via ``C`` -- and the dedup guard collapses both visits to one
    entry in the returned list.
    """
    from django_strawberry_framework.orders.inputs import _iter_orderset_subclasses

    class _DiamondA(OrderSet):
        class Meta:
            model = None
            fields = ["code"]

    class _DiamondB(_DiamondA):
        pass

    class _DiamondC(_DiamondA):
        pass

    class _DiamondD(_DiamondB, _DiamondC):
        pass

    found = _iter_orderset_subclasses(_DiamondA)
    assert found.count(_DiamondD) == 1
    assert {_DiamondB, _DiamondC, _DiamondD}.issubset(set(found))


def test_clear_order_input_namespace_tolerates_unimportable_submodules():
    """Covers both best-effort submodule lookups in ONE test.

    ``clear_order_input_namespace`` is a thin wrapper over
    ``utils/inputs.py::clear_generated_input_namespace``, which resolves
    the arguments factory and the set root through two independent
    ``utils/inputs.py::_safe_import`` calls. Setting
    ``sys.modules[name] = None`` makes each lookup return ``None``, so
    the ``if factory_cls is not None:`` and ``if set_root is not None:``
    blocks are both skipped while the reachable ledger reset still runs.
    Mirror of
    ``tests/filters/test_inputs.py::test_clear_filter_input_namespace_tolerates_unimportable_submodules``.
    """
    from django_strawberry_framework.orders.inputs import clear_order_input_namespace

    factories_name = "django_strawberry_framework.orders.factories"
    sets_name = "django_strawberry_framework.orders.sets"
    saved = {name: sys.modules.get(name) for name in (factories_name, sets_name)}
    try:
        # A ``None`` entry makes the ``_safe_import`` lookup return ``None``,
        # so both ``is not None`` blocks are skipped.
        sys.modules[factories_name] = None
        sys.modules[sets_name] = None
        # Must not raise even though neither submodule can be imported.
        clear_order_input_namespace()
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def test_get_concrete_field_names_for_order_direct():
    """_get_concrete_field_names_for_order extracts column-backed fields and rejects non-models."""
    from apps.library.models import Book

    from django_strawberry_framework.exceptions import ConfigurationError
    from django_strawberry_framework.orders.inputs import (
        _get_concrete_field_names_for_order,
    )

    names = _get_concrete_field_names_for_order(Book)
    assert "id" in names
    assert "title" in names
    assert "shelf" in names  # ForeignKey has column shelf_id on Book table

    with pytest.raises(ConfigurationError, match="Expected a Django Model class"):
        _get_concrete_field_names_for_order("InvalidModel")

    with pytest.raises(ConfigurationError, match="Expected a Django Model class"):
        _get_concrete_field_names_for_order(None)


def test_normalize_input_value_handles_3_tier_deep_related_order_chain():
    """Normalize walks deeply nested (3 tiers) RelatedOrder hierarchies."""
    from apps.library.models import Book, Shelf

    from django_strawberry_framework.orders import OrderSet, RelatedOrder
    from django_strawberry_framework.orders.factories import OrderArgumentsFactory
    from django_strawberry_framework.orders.inputs import normalize_input_value

    class Tier3Order(OrderSet):
        class Meta:
            fields = ["room"]

    class Tier2Order(OrderSet):
        tier3 = RelatedOrder(Tier3Order, field_name="tier3")

        class Meta:
            model = Shelf
            fields = ["code"]

    class Tier1Order(OrderSet):
        tier2 = RelatedOrder(Tier2Order, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    factory = OrderArgumentsFactory(Tier1Order)
    Tier1Input = factory.arguments
    Tier2Input = OrderArgumentsFactory.input_object_types["Tier2OrderInputType"]
    Tier3Input = OrderArgumentsFactory.input_object_types["Tier3OrderInputType"]

    val = Tier1Input(
        title=Ordering.ASC,
        tier2=Tier2Input(
            code=Ordering.DESC,
            tier3=Tier3Input(room=Ordering.ASC_NULLS_LAST),
        ),
    )

    flat = normalize_input_value(Tier1Order, [val])
    assert flat == [
        ("title", Ordering.ASC),
        ("shelf__code", Ordering.DESC),
        ("shelf__tier3__room", Ordering.ASC_NULLS_LAST),
    ]
