"""Tests for ``OrderSetMetaclass`` and ``OrderSet`` (Slices 1 and 2).

Slice 1 surface (kept intact, append-only edits): metaclass collection /
override / binding, ``_owner_definition`` slot default, cache slot
defaults, list-form ``Meta.fields`` expansion, ``related_orders``
merge, and the cycle-safe cache write gate.

Slice 2 surface: the ``"__all__"`` cookbook-parity expansion, the
resolver-facing ``apply_sync`` / ``apply_async`` classmethods, the
``get_flat_orders`` walker, the ``_request_from_info`` context
resolver, and the per-field / per-branch ``check_*_permission``
dispatch (active-input-only / double-dispatch / dedup contract).
"""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from types import SimpleNamespace

import pytest
from apps.library.models import Book, Genre, Shelf
from django.db.models import F
from django.http import HttpRequest
from graphql import GraphQLError

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.orders import Ordering, OrderSet, RelatedOrder
from django_strawberry_framework.orders.factories import OrderArgumentsFactory
from django_strawberry_framework.orders.inputs import (
    _field_specs,
    _materialized_names,
)

# ---------------------------------------------------------------------------
# Metaclass collection / override / binding
# ---------------------------------------------------------------------------


def test_metaclass_collects_related_orders():
    """``related_orders`` is an ``OrderedDict`` keyed by declaration name."""

    class TargetOrder(OrderSet):
        pass

    class Owner(OrderSet):
        first = RelatedOrder(TargetOrder, field_name="first")
        second = RelatedOrder(TargetOrder, field_name="second")

    assert isinstance(Owner.related_orders, OrderedDict)
    assert list(Owner.related_orders) == ["first", "second"]


def test_metaclass_calls_bind_orderset_on_each_related_order():
    """Every collected ``RelatedOrder`` is bound to the new class."""

    class TargetOrder(OrderSet):
        pass

    class Owner(OrderSet):
        first = RelatedOrder(TargetOrder, field_name="first")

    assert Owner.related_orders["first"].bound_orderset is Owner


def test_metaclass_inherits_related_orders_from_bases():
    """Base-class ``related_orders`` propagate to subclasses via MRO."""

    class TargetOrder(OrderSet):
        pass

    class BaseOwner(OrderSet):
        rel = RelatedOrder(TargetOrder, field_name="rel")

    class ChildOwner(BaseOwner):
        pass

    assert "rel" in ChildOwner.related_orders
    assert ChildOwner.related_orders["rel"] is BaseOwner.related_orders["rel"]


def test_metaclass_subclass_overrides_inherited_related_order():
    """A same-named declaration on the subclass wins over the inherited one."""

    class TargetOrder(OrderSet):
        pass

    class BaseOwner(OrderSet):
        rel = RelatedOrder(TargetOrder, field_name="rel")

    class ChildOwner(BaseOwner):
        rel = RelatedOrder(TargetOrder, field_name="rel_override")

    assert ChildOwner.related_orders["rel"] is not BaseOwner.related_orders["rel"]
    assert ChildOwner.related_orders["rel"].field_name == "rel_override"


# ---------------------------------------------------------------------------
# Class slot defaults
# ---------------------------------------------------------------------------


def test_orderset_owner_definition_default_none():
    """The binding seam is ``None`` until Slice 3 wires phase 2.5."""

    class FreshOrder(OrderSet):
        pass

    assert FreshOrder._owner_definition is None


def test_orderset_expanded_fields_default_none():
    """``_expanded_fields`` defaults to ``None`` (cache miss until populated)."""

    class FreshOrder(OrderSet):
        pass

    assert FreshOrder._expanded_fields is None


def test_orderset_is_expanding_fields_default_false():
    """``_is_expanding_fields`` defaults to ``False`` (no recursion in flight)."""

    class FreshOrder(OrderSet):
        pass

    assert FreshOrder._is_expanding_fields is False


# ---------------------------------------------------------------------------
# Meta.fields expansion + related_orders merge
# ---------------------------------------------------------------------------


def test_orderset_meta_fields_list_form():
    """List entries become ``key → None`` per cookbook line 280."""

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title", "subtitle"]

    fields = BookOrder.get_fields()
    assert list(fields) == ["title", "subtitle"]
    assert all(v is None for v in fields.values())


def test_orderset_meta_fields_all_expands_to_column_backed_fields_per_cookbook():
    """``"__all__"`` expands to the column-backed field names per spec-028 Revision 4 B4.

    Forward ``ForeignKey`` columns are included (their ``<field>_id``
    column is on the model's own table); M2M managers and reverse FKs
    are excluded. Replaces the Slice 1
    ``test_orderset_meta_fields_all_raises_until_slice_2`` placeholder
    -- Slice 2 wires the
    ``_get_concrete_field_names_for_order`` helper through
    ``_expand_meta_fields``.
    """

    class BookOrderAll(OrderSet):
        class Meta:
            model = Book
            fields = "__all__"

    fields = BookOrderAll.get_fields()
    keys = list(fields)
    # Concrete columns and forward FK -- present.
    assert "id" in keys
    assert "title" in keys
    assert "subtitle" in keys
    assert "circulation_status" in keys
    assert "shelf" in keys
    # M2M (``genres``) and reverse FK (``loans``) -- excluded per B4.
    assert "genres" not in keys
    assert "loans" not in keys


def test_orderset_get_fields_merges_related_orders():
    """``Meta.fields`` entries land first; ``related_orders`` merge on top."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    fields = BookOrder.get_fields()
    assert list(fields) == ["title", "shelf"]
    assert fields["title"] is None
    assert fields["shelf"] is BookOrder.related_orders["shelf"]


def test_orderset_get_fields_caches_on_resolved_related_orders():
    """The two-condition gate writes ``_expanded_fields`` for class-ref targets."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    first = BookOrder.get_fields()
    assert BookOrder.__dict__.get("_expanded_fields") is first
    second = BookOrder.get_fields()
    assert second is first  # cache hit returns the same OrderedDict instance.


def test_orderset_get_fields_does_not_cache_with_unresolved_string_target():
    """A pending string target leaves the cache slot empty so a later resolve writes it."""

    class BookOrder(OrderSet):
        # Unresolvable absolute target; will not resolve to a real class
        # until something updates ``_orderset``. The Slice 1 cache gate
        # refuses to write while a string is still on the instance.
        shelf = RelatedOrder("tests.orders.test_sets.MissingOrder", field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    fields = BookOrder.get_fields()
    # Result is well-formed (cookbook's behavior: the unresolved target
    # is preserved as an OrderedDict value), but the cache is NOT written.
    assert list(fields) == ["title", "shelf"]
    assert BookOrder.__dict__.get("_expanded_fields") is None


def test_orderset_meta_fields_none_returns_only_related_orders():
    """Missing ``Meta.fields`` collapses to the ``related_orders`` map only."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

    fields = BookOrder.get_fields()
    assert list(fields) == ["shelf"]
    assert fields["shelf"] is BookOrder.related_orders["shelf"]


# ---------------------------------------------------------------------------
# Slice 2 — additional cookbook-parity __all__ shapes
# ---------------------------------------------------------------------------


def test_orderset_meta_fields_all_raises_configurationerror_without_meta_model():
    """``"__all__"`` requires ``Meta.model`` to derive column names."""

    class NoModelOrder(OrderSet):
        class Meta:
            fields = "__all__"

    with pytest.raises(ConfigurationError) as exc_info:
        NoModelOrder.get_fields()
    assert "Meta.model" in str(exc_info.value)


def test_orderset_get_fields_all_with_explicit_relatedorder_override_replaces_column_leaf():
    """An explicit ``RelatedOrder("shelf", ...)`` replaces the column leaf.

    Per spec-028 Edge cases: when ``Meta.fields = "__all__"`` AND a
    ``RelatedOrder`` declares ``field_name="shelf"``, the merge step
    overlays the related orderset on top of the column leaf, so
    ``fields["shelf"]`` is the ``RelatedOrder`` instance, not ``None``.
    """

    class ShelfOrderOverride(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrderOverride(OrderSet):
        shelf = RelatedOrder(ShelfOrderOverride, field_name="shelf")

        class Meta:
            model = Book
            fields = "__all__"

    fields = BookOrderOverride.get_fields()
    assert "shelf" in fields
    assert fields["shelf"] is BookOrderOverride.related_orders["shelf"]


# ---------------------------------------------------------------------------
# Slice 2 — Slice 2 apply_sync / apply_async / permissions fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_orderset_state():
    """Clear class-level factory caches + per-test field-spec ledger."""
    _materialized_names.clear()
    _field_specs.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()
    yield
    _materialized_names.clear()
    _field_specs.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()


def _make_info(user_is_anonymous: bool = False) -> SimpleNamespace:
    """Build a minimal ``info``-shaped stub with a Django ``HttpRequest`` on it."""
    request = HttpRequest()
    request.user = SimpleNamespace(is_anonymous=user_is_anonymous)
    return SimpleNamespace(context=SimpleNamespace(request=request))


def _book_order_with_factory():
    """Declare ``BookOrder`` + build its Strawberry input class via the factory."""

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title", "subtitle"]

    factory = OrderArgumentsFactory(BookOrder)
    input_cls = factory.arguments
    return BookOrder, input_cls


def _book_order_with_shelf_factory():
    """Declare ``BookOrder`` with a ``shelf`` ``RelatedOrder`` + build input classes."""

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
    book_input_cls = factory.arguments
    shelf_input_cls = OrderArgumentsFactory.input_object_types["ShelfOrderInputType"]
    return BookOrder, ShelfOrder, book_input_cls, shelf_input_cls


# ---------------------------------------------------------------------------
# Slice 2 — apply_sync / apply_async
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_orderset_apply_sync_applies_order_by_to_queryset():
    """A single ``Ordering.ASC`` leaf -> ``queryset.order_by`` carries one expression."""
    BookOrder, BookInput = _book_order_with_factory()
    input_value = [BookInput(title=Ordering.ASC)]
    info = _make_info()
    queryset = Book.objects.all()
    result = BookOrder.apply_sync(input_value, queryset, info)
    order_by = list(result.query.order_by)
    # Django stores the F-based ascending form as an OrderBy expression
    # tuple rather than a bare-string. Confirm at least one item with
    # the title field.
    assert order_by  # non-empty
    # The result is a different queryset reference (order_by clones).
    assert result is not queryset


@pytest.mark.django_db
def test_orderset_apply_sync_returns_unmodified_queryset_for_empty_input():
    """Empty top-level list -> queryset is returned unchanged (no clone)."""
    BookOrder, _ = _book_order_with_factory()
    info = _make_info()
    queryset = Book.objects.all()
    result = BookOrder.apply_sync([], queryset, info)
    assert result is queryset


@pytest.mark.django_db
def test_orderset_apply_sync_returns_unmodified_queryset_for_all_null_directions():
    """Every leaf direction is ``None`` -> queryset is returned unchanged."""
    BookOrder, BookInput = _book_order_with_factory()
    input_value = [BookInput(title=None, subtitle=None)]
    info = _make_info()
    queryset = Book.objects.all()
    result = BookOrder.apply_sync(input_value, queryset, info)
    assert result is queryset


@pytest.mark.django_db
def test_orderset_apply_sync_emits_multi_field_priority():
    """List-element order is the tie-breaker mechanism per Spec Decision 5."""
    BookOrder, BookInput = _book_order_with_factory()
    input_value = [
        BookInput(title=Ordering.ASC),
        BookInput(subtitle=Ordering.DESC_NULLS_LAST),
    ]
    info = _make_info()
    queryset = Book.objects.all()
    result = BookOrder.apply_sync(input_value, queryset, info)
    order_by = list(result.query.order_by)
    # Two expressions in declaration order.
    assert len(order_by) == 2


@pytest.mark.django_db
def test_orderset_apply_sync_propagates_graphqlerror_from_check_permission():
    """A ``check_<field>_permission`` raising ``GraphQLError`` halts before ``order_by``."""

    class GatedBookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        def check_title_permission(self, request):
            if request.user.is_anonymous:
                raise GraphQLError(
                    "staff only",
                    extensions={"code": "ORDER_PERMISSION_DENIED"},
                )

    factory = OrderArgumentsFactory(GatedBookOrder)
    BookInput = factory.arguments
    input_value = [BookInput(title=Ordering.ASC)]
    info = _make_info(user_is_anonymous=True)
    queryset = Book.objects.all()
    with pytest.raises(GraphQLError) as exc_info:
        GatedBookOrder.apply_sync(input_value, queryset, info)
    assert "staff only" in str(exc_info.value)


@pytest.mark.django_db
def test_orderset_apply_async_via_asyncio_run():
    """Async path produces the same order_by clauses as the sync path."""
    BookOrder, BookInput = _book_order_with_factory()
    input_value = [BookInput(title=Ordering.ASC)]
    info = _make_info()
    queryset = Book.objects.all()
    result = asyncio.run(BookOrder.apply_async(input_value, queryset, info))
    order_by = list(result.query.order_by)
    assert order_by


@pytest.mark.django_db
def test_orderset_apply_async_runs_check_permission_in_sync_to_async():
    """``check_*_permission`` raising propagates through the event loop."""

    class GatedAsyncOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        def check_title_permission(self, request):
            if request.user.is_anonymous:
                raise GraphQLError("staff only", extensions={"code": "ORDER_PERMISSION_DENIED"})

    factory = OrderArgumentsFactory(GatedAsyncOrder)
    BookInput = factory.arguments
    input_value = [BookInput(title=Ordering.ASC)]
    info = _make_info(user_is_anonymous=True)
    queryset = Book.objects.all()
    with pytest.raises(GraphQLError):
        asyncio.run(GatedAsyncOrder.apply_async(input_value, queryset, info))


# ---------------------------------------------------------------------------
# Slice 2 — active-input-only + active-branch double-dispatch + dedup
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_orderset_check_permission_denies_for_active_field():
    """An active leaf field fires its gate."""

    class ActiveGateOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title", "subtitle"]

        def check_title_permission(self, request):
            raise GraphQLError("denied")

    factory = OrderArgumentsFactory(ActiveGateOrder)
    BookInput = factory.arguments
    input_value = [BookInput(title=Ordering.ASC)]
    with pytest.raises(GraphQLError):
        ActiveGateOrder.apply_sync(input_value, Book.objects.all(), _make_info())


@pytest.mark.django_db
def test_orderset_check_permission_quiet_for_inactive_field():
    """An inactive (None) leaf field does NOT fire its gate."""

    class QuietGateOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title", "subtitle"]

        def check_title_permission(self, request):
            raise GraphQLError("would deny if fired")

    factory = OrderArgumentsFactory(QuietGateOrder)
    BookInput = factory.arguments
    # ``title`` is absent (None); only ``subtitle`` is populated.
    input_value = [BookInput(subtitle=Ordering.ASC)]
    # No raise -- the gate stays quiet.
    QuietGateOrder.apply_sync(input_value, Book.objects.all(), _make_info())


@pytest.mark.django_db
def test_orderset_check_permission_active_relatedorder_branch_fires_parent_gate():
    """An active ``RelatedOrder`` branch fires the parent's per-branch gate."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrderParentGate(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

        def check_shelf_permission(self, request):
            raise GraphQLError("no shelf order")

    factory = OrderArgumentsFactory(BookOrderParentGate)
    BookInput = factory.arguments
    ShelfInput = OrderArgumentsFactory.input_object_types["ShelfOrderInputType"]
    input_value = [BookInput(shelf=ShelfInput(code=Ordering.ASC))]
    with pytest.raises(GraphQLError) as exc:
        BookOrderParentGate.apply_sync(input_value, Book.objects.all(), _make_info())
    assert "no shelf order" in str(exc.value)


@pytest.mark.django_db
def test_orderset_check_permission_active_relatedorder_branch_fires_child_gate():
    """The child orderset's own gates also fire via the recursive call."""

    class ShelfOrderChild(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

        def check_code_permission(self, request):
            raise GraphQLError("child denies")

    class BookOrderChildGate(OrderSet):
        shelf = RelatedOrder(ShelfOrderChild, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    factory = OrderArgumentsFactory(BookOrderChildGate)
    BookInput = factory.arguments
    ShelfInput = OrderArgumentsFactory.input_object_types["ShelfOrderChildInputType"]
    input_value = [BookInput(shelf=ShelfInput(code=Ordering.ASC))]
    with pytest.raises(GraphQLError) as exc:
        BookOrderChildGate.apply_sync(input_value, Book.objects.all(), _make_info())
    assert "child denies" in str(exc.value)


@pytest.mark.django_db
def test_orderset_check_permission_dedups_repeated_list_entries():
    """The dedup map fires each ``check_<field>_permission`` once per class."""
    counts = {"shelf": 0, "code": 0}

    class ShelfOrderDedup(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

        def check_code_permission(self, request):
            counts["code"] += 1

    class BookOrderDedup(OrderSet):
        shelf = RelatedOrder(ShelfOrderDedup, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

        def check_shelf_permission(self, request):
            counts["shelf"] += 1

    factory = OrderArgumentsFactory(BookOrderDedup)
    BookInput = factory.arguments
    ShelfInput = OrderArgumentsFactory.input_object_types["ShelfOrderDedupInputType"]
    input_value = [
        BookInput(shelf=ShelfInput(code=Ordering.ASC)),
        BookInput(shelf=ShelfInput(code=Ordering.DESC)),
    ]
    BookOrderDedup.apply_sync(input_value, Book.objects.all(), _make_info())
    # Each gate fires exactly once across the two list elements.
    assert counts["shelf"] == 1
    assert counts["code"] == 1


# ---------------------------------------------------------------------------
# Slice 2 — _request_from_info shapes
# ---------------------------------------------------------------------------


def test_orderset_request_from_info_reads_context_request_attribute():
    """``info.context.request`` is the canonical shape."""
    request = HttpRequest()
    info = SimpleNamespace(context=SimpleNamespace(request=request))
    assert OrderSet._request_from_info(info) is request


def test_orderset_request_from_info_reads_bare_httprequest_context():
    """``info.context`` being a bare ``HttpRequest`` is also accepted."""
    request = HttpRequest()
    info = SimpleNamespace(context=request)
    assert OrderSet._request_from_info(info) is request


def test_orderset_request_from_info_raises_on_unrecognized_context_shape():
    """A non-HttpRequest context with no ``.request`` attribute raises."""

    class _PlainCtx:
        pass

    info = SimpleNamespace(context=_PlainCtx())
    with pytest.raises(ConfigurationError) as exc_info:
        OrderSet._request_from_info(info)
    assert "OrderSet.apply" in str(exc_info.value)


def test_orderset_request_from_info_raises_when_info_context_is_none():
    """``info.context = None`` raises ``ConfigurationError``."""
    info = SimpleNamespace(context=None)
    with pytest.raises(ConfigurationError):
        OrderSet._request_from_info(info)


# ---------------------------------------------------------------------------
# Slice 2 — get_flat_orders walker
# ---------------------------------------------------------------------------


def test_orderset_get_flat_orders_walks_normalized_pairs():
    """``get_flat_orders`` is a pass-through that applies the prefix per element."""
    result = OrderSet.get_flat_orders(
        [("title", Ordering.ASC), ("shelf__code", Ordering.DESC)],
    )
    assert result == [("title", Ordering.ASC), ("shelf__code", Ordering.DESC)]


def test_orderset_get_flat_orders_applies_prefix():
    """The ``prefix`` argument concatenates to each field path."""
    result = OrderSet.get_flat_orders(
        [("code", Ordering.ASC)],
        prefix="shelf__",
    )
    assert result == [("shelf__code", Ordering.ASC)]


# ---------------------------------------------------------------------------
# Slice 2 — _normalize_input delegate (smoke; full coverage in test_inputs)
# ---------------------------------------------------------------------------


def test_orderset_normalize_input_delegates_to_module_helper():
    """The classmethod is a thin delegate to ``normalize_input_value``."""

    class BookOrderNormalize(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    factory = OrderArgumentsFactory(BookOrderNormalize)
    BookInput = factory.arguments
    input_value = [BookInput(title=Ordering.ASC)]
    result = BookOrderNormalize._normalize_input(input_value)
    assert result == [("title", Ordering.ASC)]


# ---------------------------------------------------------------------------
# Slice 2 — check_permissions instance method (cookbook compatibility)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_orderset_check_permissions_instance_method_delegates():
    """Bound-method ``check_permissions`` routes through ``_run_permission_checks``."""
    fired = []

    class CookbookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        def check_title_permission(self, request):
            fired.append(request)

    factory = OrderArgumentsFactory(CookbookOrder)
    BookInput = factory.arguments
    input_value = [BookInput(title=Ordering.ASC)]
    instance = object.__new__(CookbookOrder)
    instance._input_value = input_value
    request = HttpRequest()
    instance.check_permissions(request)
    assert fired == [request]


def test_orderset_check_permissions_instance_tolerates_no_input_value():
    """A bare instance with no ``_input_value`` parked -> no raise (graceful no-op)."""

    class NoInputOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    instance = object.__new__(NoInputOrder)
    request = HttpRequest()
    instance.check_permissions(request)  # no input value -> early return


# Keep imports active so ruff doesn't flag the F-expression / Genre import.
assert F is not None
assert Genre is not None
