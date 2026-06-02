"""Tests for the Slice 1 surface of ``django_strawberry_framework/orders/inputs.py``.

Covers ``INPUTS_MODULE_PATH``, the ``Ordering`` enum (members +
``resolve`` semantics for ``ASC`` / ``DESC`` / ``NULLS_FIRST`` /
``NULLS_LAST`` shapes), ``_input_type_name_for`` (the
``ClassBasedTypeNameMixin`` delegate), and ``materialize_input_class``
(write-to-module-global, idempotent re-write on the same pair,
``ConfigurationError`` on collision against a different class).

Slice 2 / Slice 3 land their tests around
``convert_order_field_to_input_annotation`` / ``normalize_input_value`` /
``clear_order_input_namespace`` / ``order_input_type``; the TODO
anchors stay until then.
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
    """All six members from spec-028 Decision 5 lines 525-532 are present."""
    assert {m.name for m in Ordering} == {
        "ASC",
        "DESC",
        "ASC_NULLS_FIRST",
        "ASC_NULLS_LAST",
        "DESC_NULLS_FIRST",
        "DESC_NULLS_LAST",
    }


def test_ordering_member_values_are_string_names():
    """Members carry string values matching their names (Decision 5)."""
    assert Ordering.ASC.value == "ASC"
    assert Ordering.DESC.value == "DESC"
    assert Ordering.ASC_NULLS_FIRST.value == "ASC_NULLS_FIRST"
    assert Ordering.ASC_NULLS_LAST.value == "ASC_NULLS_LAST"
    assert Ordering.DESC_NULLS_FIRST.value == "DESC_NULLS_FIRST"
    assert Ordering.DESC_NULLS_LAST.value == "DESC_NULLS_LAST"


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


def test_ordering_resolve_asc_nulls_first_sets_nulls_first_true():
    """``ASC_NULLS_FIRST`` sets ``nulls_first=True`` only."""
    expr = Ordering.ASC_NULLS_FIRST.resolve("name")
    assert expr.descending is False
    assert expr.nulls_first is True
    assert expr.nulls_last is None


def test_ordering_resolve_asc_nulls_last_sets_nulls_last_true():
    """``ASC_NULLS_LAST`` sets ``nulls_last=True`` only."""
    expr = Ordering.ASC_NULLS_LAST.resolve("name")
    assert expr.descending is False
    assert expr.nulls_first is None
    assert expr.nulls_last is True


def test_ordering_resolve_desc_nulls_first_sets_nulls_first_true():
    """``DESC_NULLS_FIRST`` sets ``descending=True`` and ``nulls_first=True``."""
    expr = Ordering.DESC_NULLS_FIRST.resolve("name")
    assert expr.descending is True
    assert expr.nulls_first is True
    assert expr.nulls_last is None


def test_ordering_resolve_desc_nulls_last_sets_nulls_last_true():
    """``DESC_NULLS_LAST`` sets ``descending=True`` and ``nulls_last=True``."""
    expr = Ordering.DESC_NULLS_LAST.resolve("subtitle")
    assert expr.descending is True
    assert expr.nulls_first is None
    assert expr.nulls_last is True


def test_ordering_resolve_wraps_value_in_f_expression():
    """``resolve(value)`` produces ``F(value)``-backed expressions."""
    expr = Ordering.ASC.resolve("shelf__code")
    # ``OrderBy.expression`` holds the wrapped ``F("shelf__code")``.
    assert isinstance(expr.expression, F)
    assert expr.expression.name == "shelf__code"


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
    assert getattr(module, "FooInputType") is Foo
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
# Slice 2 — _get_concrete_field_names_for_order
# ---------------------------------------------------------------------------


def test_get_concrete_field_names_for_order_includes_forward_fk_column():
    """Forward ``ForeignKey`` columns appear in the column-backed list."""
    from apps.library.models import Book

    from django_strawberry_framework.orders.inputs import _get_concrete_field_names_for_order

    names = _get_concrete_field_names_for_order(Book)
    assert "shelf" in names


def test_get_concrete_field_names_for_order_excludes_m2m_managers():
    """``ManyToManyField`` managers do NOT appear (spec-028 Revision 4 B4)."""
    from apps.library.models import Book

    from django_strawberry_framework.orders.inputs import _get_concrete_field_names_for_order

    names = _get_concrete_field_names_for_order(Book)
    assert "genres" not in names


def test_get_concrete_field_names_for_order_excludes_reverse_fk():
    """Reverse FK accessors do NOT appear (no ``column`` attribute)."""
    from apps.library.models import Book

    from django_strawberry_framework.orders.inputs import _get_concrete_field_names_for_order

    names = _get_concrete_field_names_for_order(Book)
    assert "loans" not in names


# ---------------------------------------------------------------------------
# Slice 2 — convert_order_field_to_input_annotation
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
# Slice 2 — normalize_input_value
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


# ---------------------------------------------------------------------------
# Slice 2 — build_input_class
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
# Slice 2 — _build_input_fields populates _field_specs
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
# Slice 2 — clear_order_input_namespace
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
    """The materialized class stays on the module dict per spec-028 Revision 4 B2."""
    from django_strawberry_framework.orders.inputs import (
        INPUTS_MODULE_PATH,
        clear_order_input_namespace,
        materialize_input_class,
    )

    class FooParked:
        pass

    materialize_input_class("FooParkedOrderInputType", FooParked)
    module = sys.modules[INPUTS_MODULE_PATH]
    assert getattr(module, "FooParkedOrderInputType") is FooParked
    clear_order_input_namespace()
    # Class object stays parked -- parking is load-bearing per B2.
    assert getattr(module, "FooParkedOrderInputType") is FooParked


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
# Slice 2 — order_input_type consumer helper
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
# Slice 3 -- registry.clear() integration
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

    # Module global is left parked (parking is load-bearing per Decision 9 B2).
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
# Pass-2 B1 coverage closure -- inputs.py uncovered lines
# ---------------------------------------------------------------------------


def test_camel_case_returns_input_when_split_yields_no_parts():
    """Closes ``inputs.py:168`` -- ``if not parts: return name`` early return.

    ``_camel_case`` splits on ``"_"`` and filters empty strings; inputs
    that collapse to an empty parts list (``""`` / ``"_"`` / ``"__"``)
    return ``name`` unchanged.
    """
    from django_strawberry_framework.orders.inputs import _camel_case

    assert _camel_case("") == ""
    assert _camel_case("_") == "_"
    assert _camel_case("__") == "__"


def test_build_input_class_threads_description_through_strawberry_field():
    """Closes ``inputs.py:222`` -- ``description`` kwarg threads through ``strawberry.field``.

    ``build_input_class`` pops ``description`` from the field kwargs and
    forwards it to ``strawberry.field(description=...)`` so the GraphQL
    SDL carries the description.
    """
    from django_strawberry_framework.orders.inputs import build_input_class

    cls = build_input_class(
        "DescribedOrderInputType",
        [("foo", Ordering | None, {"description": "the foo direction"})],
    )
    fields = {f.python_name: f for f in cls.__strawberry_definition__.fields}
    assert fields["foo"].description == "the foo direction"


def test_normalize_input_value_returns_empty_for_non_dataclass_non_list_non_none_input():
    """Closes ``inputs.py:336`` -- ``if dataclass_fields is None: return []``.

    A non-list, non-None object that lacks ``__dataclass_fields__``
    short-circuits to an empty list. The orderset class is not consulted
    for this guard, so any existing ``OrderSet`` subclass works.
    """
    from django_strawberry_framework.orders.inputs import normalize_input_value

    class _NormalizeNoDataclassOrder(OrderSet):
        pass

    # Plain object -- no ``__dataclass_fields__``.
    assert normalize_input_value(_NormalizeNoDataclassOrder, object()) == []


def test_normalize_input_value_skips_attrs_with_no_field_spec_entry():
    """Closes ``inputs.py:344`` -- ``if spec is None: continue`` defensive skip.

    When the dataclass input carries an attribute that has no
    corresponding ``_field_specs`` entry for the orderset class, the
    walker skips it silently.
    """
    import dataclasses

    from django_strawberry_framework.orders.inputs import normalize_input_value

    class _NoSpecsOrder(OrderSet):
        class Meta:
            model = None
            fields = ["title"]

    @dataclasses.dataclass
    class _StubInput:
        title: Ordering | None = None

    # ``_field_specs`` is empty for ``(_NoSpecsOrder, "title")`` because
    # ``_build_input_fields`` was never called for it. The walker hits
    # the ``if spec is None: continue`` guard and emits no tuples.
    result = normalize_input_value(_NoSpecsOrder, _StubInput(title=Ordering.ASC))
    assert result == []


def test_normalize_input_value_skips_related_branch_when_child_orderset_is_none(
    _namespace_cleanup,
):
    """Closes ``inputs.py:352`` -- ``if child_orderset is None: continue`` skip.

    When a ``RelatedOrder`` resolves to ``None`` (placeholder shape),
    the walker skips the branch silently rather than recursing into it.
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
    """Closes ``inputs.py:410`` -- ``if cls in seen: continue`` diamond dedup.

    Mirror of
    ``tests/filters/test_inputs.py::test_iter_filterset_subclasses_dedupes_diamond_inheritance``
    (lines 1036-1056). A diamond inheritance hierarchy
    (``B(A)``, ``C(A)``, ``D(B, C)``) walks ``D`` twice through
    ``__subclasses__()`` -- once via ``B`` and once via ``C`` -- and the
    dedup guard collapses both visits to one entry in the returned list.
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
    """Closes ``inputs.py:461-462`` and ``inputs.py:476-477`` in ONE test.

    Mirror of
    ``tests/filters/test_inputs.py::test_clear_filter_input_namespace_tolerates_unimportable_submodules``
    (lines 1009-1028). Setting ``sys.modules[name] = None`` makes
    ``from ... import ...`` raise ``ImportError``, exercising BOTH
    ``except ImportError: pass`` guards in ``clear_order_input_namespace``.
    """
    from django_strawberry_framework.orders.inputs import clear_order_input_namespace

    factories_name = "django_strawberry_framework.orders.factories"
    sets_name = "django_strawberry_framework.orders.sets"
    saved = {name: sys.modules.get(name) for name in (factories_name, sets_name)}
    try:
        # Setting the module entry to ``None`` makes ``from ... import ...``
        # raise ImportError, exercising both ``except ImportError`` guards.
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
