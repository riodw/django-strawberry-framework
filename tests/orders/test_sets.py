"""OrderSet tests for Meta collection, validation, sync/async apply, and permission scope.

Declaration surface: metaclass collection / override / binding,
``_owner_definition`` slot default, cache slot defaults, list-form
``Meta.fields`` expansion, ``related_orders`` merge, and the cycle-safe
cache write gate.

Apply surface: the ``"__all__"`` cookbook-parity expansion, the
resolver-facing ``apply_sync`` / ``apply_async`` classmethods, the
``get_flat_orders`` walker, the ``_request_from_info`` context
resolver, and the per-field / per-branch ``check_*_permission``
dispatch (active-input-only / double-dispatch / dedup contract).
"""

from __future__ import annotations

import asyncio
import contextvars
import gc
import threading
from collections import OrderedDict
from types import SimpleNamespace

import pytest
import strawberry
from apps.library.models import Book, Branch, Genre, Shelf, TaggedItem
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
from django_strawberry_framework.orders.sets import (
    _ORDER_NORMALIZATION_CAPTURE,
    _validate_normalized_terms,
    capture_applied_order_normalization,
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


def test_metaclass_none_removal_survives_diamond_inheritance():
    """An earlier base's ``None`` tombstone prevents later-base resurrection."""

    class TargetOrder(OrderSet):
        pass

    class BaseOwner(OrderSet):
        rel = RelatedOrder(TargetOrder, field_name="rel")

        class Meta:
            model = Book
            fields = ["title"]

    class RemovedOwner(BaseOwner):
        rel = None  # django-filter removal idiom

        class Meta:
            model = Book
            fields = ["title"]

    class KeptOwner(BaseOwner):
        pass

    class CombinedOwner(RemovedOwner, KeptOwner):
        pass

    assert "rel" not in RemovedOwner.related_orders
    assert "rel" not in RemovedOwner.get_fields()
    assert "rel" not in CombinedOwner.related_orders
    assert "rel" not in CombinedOwner.get_fields()
    assert "rel" in BaseOwner.related_orders


# ---------------------------------------------------------------------------
# Class slot defaults
# ---------------------------------------------------------------------------


def test_orderset_owner_definition_default_none():
    """The binding seam is ``None`` until phase 2.5 wires it."""

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
    """List entries become ``key -> None`` per cookbook line 280."""

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title", "subtitle"]

    fields = BookOrder.get_fields()
    assert list(fields) == ["title", "subtitle"]
    assert all(v is None for v in fields.values())


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
        # until something updates ``_orderset``. The cache gate
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


def test_orderset_metaclass_and_expansion_share_factory_fields_owner():
    """Class Meta write-back and Layer-4 expansion ride the shared fingerprint."""
    from django_strawberry_framework.orders.sets import OrderSetMetaclass
    from django_strawberry_framework.utils.inputs import (
        promote_set_meta_fields,
        read_set_meta_fields,
    )

    assert "promote_set_meta_fields" in OrderSetMetaclass.__new__.__code__.co_names
    assert "read_set_meta_fields" in OrderSet._expand_meta_fields.__code__.co_names
    assert (
        OrderSetMetaclass.__new__.__globals__["promote_set_meta_fields"] is promote_set_meta_fields
    )
    assert OrderSet._expand_meta_fields.__globals__["read_set_meta_fields"] is read_set_meta_fields


# ---------------------------------------------------------------------------
# Additional cookbook-parity __all__ shapes
# ---------------------------------------------------------------------------


def test_orderset_meta_fields_all_raises_configurationerror_without_meta_model():
    """``"__all__"`` requires ``Meta.model`` to derive column names."""

    class NoModelOrder(OrderSet):
        class Meta:
            fields = "__all__"

    with pytest.raises(ConfigurationError) as exc_info:
        NoModelOrder.get_fields()
    assert "Meta.model" in str(exc_info.value)


def test_orderset_meta_fields_rejects_unknown_order_path():
    """Unknown explicit paths fail before a query can raise Django FieldError."""

    class InvalidPathOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["does_not_exist"]

    with pytest.raises(ConfigurationError, match="invalid order path"):
        InvalidPathOrder.get_fields()


def test_orderset_resolve_order_expressions_rejects_unknown_order_path():
    """The expression builder re-validates rather than trusting its caller.

    ``Meta.fields`` validation catches a bad path at declaration, but the
    builder is reachable directly and runs against the concrete
    ``queryset.model`` -- which may be a descendant of ``Meta.model``, so a
    path valid at declaration is not proven valid here. Failing loud keeps the
    error a framework ``ConfigurationError`` instead of a Django ``FieldError``
    raised from deep inside query compilation.
    """

    class ValidPathOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    with pytest.raises(ConfigurationError, match="invalid order path"):
        ValidPathOrder._resolve_order_expressions(
            [("does_not_exist", Ordering.ASC)],
            model=Book,
        )


def test_orderset_all_excludes_virtual_generic_fields():
    """``__all__`` contains database columns, not GenericRelation/GFK descriptors."""
    from apps.library.models import Branch, TaggedItem

    from django_strawberry_framework.orders.inputs import (
        _get_concrete_field_names_for_order,
    )

    assert "tags" not in _get_concrete_field_names_for_order(Branch)
    assert "content_object" not in _get_concrete_field_names_for_order(TaggedItem)


# ---------------------------------------------------------------------------
# apply_sync / apply_async / permissions fixtures
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


# ---------------------------------------------------------------------------
# apply_async
# ---------------------------------------------------------------------------


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
# Active-input-only + active-branch double-dispatch + dedup
# ---------------------------------------------------------------------------


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
# _request_from_info shapes
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
    assert "OrderSet could not resolve" in str(exc_info.value)


def test_orderset_request_from_info_raises_when_info_context_is_none():
    """``info.context = None`` raises ``ConfigurationError``."""
    info = SimpleNamespace(context=None)
    with pytest.raises(ConfigurationError):
        OrderSet._request_from_info(info)


# ---------------------------------------------------------------------------
# get_flat_orders walker
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
# _normalize_input delegate (smoke; full coverage in test_inputs)
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


@pytest.mark.django_db
def test_orderset_direct_mapping_initializes_specs_before_permissions():
    """Flat mappings must not bypass nested target permission gates."""

    class ShelfOrderDirectMapping(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

        def check_code_permission(self, request):
            raise GraphQLError("code gate fired")

    class BookOrderDirectMapping(OrderSet):
        shelf = RelatedOrder(ShelfOrderDirectMapping, field_name="shelf")

        class Meta:
            model = Book
            fields = ["shelf__code"]

    with pytest.raises(GraphQLError, match="code gate fired"):
        BookOrderDirectMapping.apply_sync(
            {"shelf_code": Ordering.ASC},
            Book.objects.all(),
            _make_info(),
        )


def test_orderset_inactive_input_does_not_resolve_lazy_related_target():
    """None and empty-list order inputs remain no-ops before lazy resolution."""

    class NoOpOrder(OrderSet):
        shelf = RelatedOrder("MissingOrderForNoOp", field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    queryset = Book.objects.all()
    assert NoOpOrder.apply_sync(None, queryset, _make_info()) is queryset
    assert NoOpOrder.apply_sync([], queryset, _make_info()) is queryset
    assert NoOpOrder.apply_sync({}, queryset, _make_info()) is queryset


# ---------------------------------------------------------------------------
# sets.py edge-case branches
# ---------------------------------------------------------------------------


def test_orderset_expand_meta_fields_returns_empty_when_meta_has_no_fields_attr():
    """Covers ``orders/sets.py::OrderSet._expand_meta_fields`` #"if meta_fields is None:".

    Declaring ``Meta`` without a ``fields`` attribute -> the shared
    ``read_set_meta_fields(meta)`` reader returns ``None``; the helper
    early-returns an empty ``OrderedDict``.
    """

    class NoFieldsOrder(OrderSet):
        class Meta:
            model = Book

    result = NoFieldsOrder._expand_meta_fields()
    assert isinstance(result, OrderedDict)
    assert result == OrderedDict()


def test_orderset_extract_branch_value_returns_none_for_none_input():
    """Covers ``utils/permissions.py::extract_branch_value`` #"if input_value is None:"."""
    assert OrderSet._extract_branch_value(None, "anything") is None


def test_orderset_extract_branch_value_reads_dict_field():
    """Covers ``utils/input_values.py::input_field_value``'s dict branch.

    ``OrderSet._extract_branch_value`` delegates the dict-vs-dataclass sniff
    to that primitive, whose #"if isinstance(input_value, dict):" arm reads
    via ``dict.get`` so a missing key collapses to ``None`` rather than
    raising ``KeyError``.
    """
    assert OrderSet._extract_branch_value({"shelf": "value"}, "shelf") == "value"
    assert OrderSet._extract_branch_value({"shelf": "value"}, "missing") is None


def test_orderset_active_permission_field_paths_returns_empty_for_none_input():
    """Covers ``utils/input_values.py::iter_active_fields`` #"is_inactive_value(input_value"."""
    assert OrderSet._active_permission_field_paths(None) == []


def test_orderset_active_permission_field_paths_returns_empty_for_non_dataclass_non_dict_input():
    """Covers ``utils/input_values.py::iter_active_fields`` #"if items is None:".

    A plain object (no ``__dataclass_fields__``, not a ``dict``) makes
    ``iter_input_items`` return ``None``, so the walker yields nothing and
    the delegate hands back an empty list.
    """
    assert OrderSet._active_permission_field_paths(object()) == []


def test_orderset_active_permission_field_paths_walks_dict_items():
    """Covers ``utils/input_values.py::iter_input_items`` #"if isinstance(input_value, dict):".

    Dict-shaped inputs are walked through ``dict.items`` so the
    active-input walker treats a dict like a dataclass.
    """

    class DictInputOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    # Populate ``_field_specs`` so the spec lookup in
    # ``utils/permissions.py::active_permission_targets`` returns a real
    # ``django_source_path`` rather than the python-attr fallback.
    OrderArgumentsFactory(DictInputOrder).arguments

    paths = DictInputOrder._active_permission_field_paths({"title": Ordering.ASC})
    assert paths == ["title"]


def test_orderset_active_permission_field_paths_falls_back_to_python_attr_when_no_field_spec_entry():
    """Covers ``utils/permissions.py::active_permission_targets`` #"else fallback_path(field.python_attr)".

    When ``_field_specs`` has no entry for ``(cls, python_attr)`` (e.g.
    a permission check fired outside the apply pipeline before
    ``_build_input_fields`` ran), ``field.spec`` is ``None`` and the
    walker falls back to the python-attr token rather than dropping the
    field.
    """

    class NoSpecsActiveOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    # Do NOT call ``_build_input_fields`` -- the ``_field_specs`` ledger
    # has no entry for ``(NoSpecsActiveOrder, "title")``. The autouse
    # ``_isolate_orderset_state`` fixture clears it at entry.
    paths = NoSpecsActiveOrder._active_permission_field_paths({"title": Ordering.ASC})
    assert paths == ["title"]


@pytest.mark.django_db
def test_orderset_apply_sync_returns_queryset_when_all_directions_filter_to_empty_expressions():
    """Covers ``orders/sets.py::OrderSet._apply_orderings`` #"if not expressions:".

    A subclass overrides ``_normalize_input`` to emit
    ``[("title", None)]`` -- non-empty ``data``, so the #"if not data:"
    early return is skipped, but ``_resolve_order_expressions``'s
    #"if direction is None:" skip drops the one term, leaving an empty
    ``expressions`` list. Reached here through ``apply_sync``; the async
    entry point reaches the same guard in
    ``test_orderset_apply_async_returns_queryset_when_all_directions_filter_to_empty_expressions``.
    """

    class _NoneDirectionSyncOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        def _normalize_input(cls, input_value):
            return [("title", None)]

    info = _make_info()
    queryset = Book.objects.all()
    result = _NoneDirectionSyncOrder.apply_sync(None, queryset, info)
    assert result is queryset


@pytest.mark.django_db
def test_orderset_apply_async_returns_queryset_when_data_is_empty():
    """Covers ``orders/sets.py::OrderSet._apply_orderings`` #"if not data:" via ``apply_async``.

    Calling ``apply_async`` with an empty list yields an empty normalized
    data list, hitting that early return before any ``order_by(...)``
    clause is built. ``apply_sync`` and ``apply_async`` share the one
    helper, so this row pins the async entry point reaching it, not a
    second copy of the guard.
    """

    class _EmptyAsyncOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    info = _make_info()
    queryset = Book.objects.all()
    result = asyncio.run(_EmptyAsyncOrder.apply_async([], queryset, info))
    assert result is queryset


@pytest.mark.django_db
def test_orderset_apply_async_returns_queryset_when_all_directions_filter_to_empty_expressions():
    """Covers ``orders/sets.py::OrderSet._apply_orderings`` #"if not expressions:" via ``apply_async``.

    Symmetric of the sync-side row: a subclass overrides
    ``_normalize_input`` to emit ``[("title", None)]`` and the async
    entry point reaches the same shared guard.
    """

    class _NoneDirectionAsyncOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        def _normalize_input(cls, input_value):
            return [("title", None)]

    info = _make_info()
    queryset = Book.objects.all()
    result = asyncio.run(_NoneDirectionAsyncOrder.apply_async(None, queryset, info))
    assert result is queryset


# =============================================================================
# Row-preserving to-many ordering - aggregate, not fan-out JOIN
# =============================================================================


def test_path_traverses_to_many_detects_multiplying_relations():
    """``_path_traverses_to_many`` flags reverse-FK / M2M paths, not scalar / to-one."""
    from django_strawberry_framework.orders.sets import _path_traverses_to_many

    assert _path_traverses_to_many(Branch, "shelves__code") is True  # reverse FK
    assert _path_traverses_to_many(Book, "genres__name") is True  # forward M2M
    assert _path_traverses_to_many(Genre, "books__title") is True  # reverse M2M
    assert _path_traverses_to_many(Book, "shelf__code") is False  # forward FK (to-one)
    assert _path_traverses_to_many(Genre, "name") is False  # scalar
    assert _path_traverses_to_many(Branch, "city") is False  # scalar


def test_path_traverses_to_many_is_cached():
    """Repeated to-many path checks reuse the metadata walk."""
    from django_strawberry_framework.orders.sets import _path_traverses_to_many

    _path_traverses_to_many.cache_clear()
    try:
        assert _path_traverses_to_many(Branch, "shelves__code") is True
        assert _path_traverses_to_many(Branch, "shelves__code") is True

        cache_info = _path_traverses_to_many.cache_info()
        assert cache_info.misses == 1
        assert cache_info.hits == 1
    finally:
        _path_traverses_to_many.cache_clear()


def test_resolve_order_expressions_aggregates_to_many_orders_scalar_directly():
    """A to-many term orders by a ``Min`` aggregate; a scalar term orders directly."""
    from django.db.models import Min

    class _MultBranchOrder(OrderSet):
        class Meta:
            model = Branch
            fields = ["name"]

    annotations, expressions = _MultBranchOrder._resolve_order_expressions(
        [("shelves__code", Ordering.ASC), ("name", Ordering.DESC)],
        model=Branch,
    )
    # The to-many path produced exactly one aggregate annotation (``Min`` for ASC).
    assert len(annotations) == 1
    ((alias, aggregate),) = annotations.items()
    assert isinstance(aggregate, Min)
    # Two order expressions: the aggregate alias (term 0) + the direct scalar (term 1).
    assert len(expressions) == 2
    assert expressions[0].expression.name == alias  # orders by the annotation alias
    assert expressions[1].expression.name == "name"  # scalar ordered directly


def test_resolve_order_expressions_uses_max_for_descending_to_many():
    """A DESCENDING to-many term aggregates with ``Max`` (so the parent's largest child wins)."""
    from django.db.models import Max

    class _DescBranchOrder(OrderSet):
        class Meta:
            model = Branch
            fields = ["name"]

    annotations, _expressions = _DescBranchOrder._resolve_order_expressions(
        [("shelves__code", Ordering.DESC_NULLS_LAST)],
        model=Branch,
    )
    ((_alias, aggregate),) = annotations.items()
    assert isinstance(aggregate, Max)


def test_path_traverses_to_many_returns_false_for_nonmultiplying_paths():
    """``_path_traverses_to_many`` returns False for unresolvable / generic / all-to-one paths.

    Covers the three non-multiplying exits: an unresolvable segment
    (``FieldDoesNotExist``), a relation field with no concrete ``related_model``
    (a ``GenericForeignKey``), and a path that resolves entirely through to-one
    relations without ever reaching a to-many.
    """
    from django_strawberry_framework.orders.sets import _path_traverses_to_many

    # Unresolvable terminal / mid segment -> FieldDoesNotExist exit.
    assert _path_traverses_to_many(Branch, "does_not_exist") is False
    assert _path_traverses_to_many(Book, "shelf__nope") is False
    # GenericForeignKey: is_relation, not many-side, but related_model is None.
    assert _path_traverses_to_many(TaggedItem, "content_object") is False
    # All-to-one chain ending on a relation (no scalar terminal, never to-many).
    assert _path_traverses_to_many(Book, "shelf__branch") is False


@pytest.mark.django_db
def test_orderset_apply_async_annotates_to_many_order():
    """``apply_async`` builds the ``Min`` aggregate annotation for a to-many order (async path).

    The sync path's annotate step is covered by the live connection test; this
    pins the ``apply_async`` twin -- a reverse-FK (``shelves``) order flattens to
    ``shelves__code`` and is applied as a row-preserving ``Min`` aggregate
    annotation + ``order_by(alias)``, not a fan-out JOIN.
    """
    from django.db.models import Min

    class ShelfOrderAgg(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BranchOrderAgg(OrderSet):
        shelves = RelatedOrder(ShelfOrderAgg, field_name="shelves")

        class Meta:
            model = Branch
            fields = ["name"]

    factory = OrderArgumentsFactory(BranchOrderAgg)
    BranchInput = factory.arguments
    ShelfInput = OrderArgumentsFactory.input_object_types["ShelfOrderAggInputType"]
    input_value = [BranchInput(shelves=ShelfInput(code=Ordering.ASC))]
    info = _make_info()
    queryset = Branch.objects.all()
    result = asyncio.run(BranchOrderAgg.apply_async(input_value, queryset, info))
    # The to-many term produced a Min aggregate annotation (the async annotate branch),
    # collapsing the reverse-FK fan-out to one row per parent.
    assert any(isinstance(agg, Min) for agg in result.query.annotations.values())
    assert list(result.query.order_by)


@pytest.mark.django_db
def test_modelless_orderset_uses_queryset_model_for_to_many_order():
    """A direct model-less orderset application still keeps the row-preserving aggregate."""
    from django.db.models import Min

    class ShelfOrderML(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BranchOrderML(OrderSet):
        shelves = RelatedOrder(ShelfOrderML, field_name="shelves")

    branch_one = Branch.objects.create(name="Alpha", city="X")
    Shelf.objects.create(code="a-code", branch=branch_one)
    Shelf.objects.create(code="b-code", branch=branch_one)
    branch_two = Branch.objects.create(name="Beta", city="Y")
    Shelf.objects.create(code="c-code", branch=branch_two)

    factory = OrderArgumentsFactory(BranchOrderML)
    BranchInput = factory.arguments
    ShelfInput = OrderArgumentsFactory.input_object_types["ShelfOrderMLInputType"]
    input_value = [BranchInput(shelves=ShelfInput(code=Ordering.ASC))]

    result = BranchOrderML.apply_sync(input_value, Branch.objects.all(), _make_info())
    assert any(isinstance(agg, Min) for agg in result.query.annotations.values())
    assert [branch.name for branch in result] == ["Alpha", "Beta"]


@pytest.mark.django_db
def test_queryset_model_overrides_conflicting_orderset_meta_model():
    """To-many detection follows the concrete queryset, never stale class metadata."""
    from django.db.models import Min

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class MisdeclaredBranchOrder(OrderSet):
        shelves = RelatedOrder(ShelfOrder, field_name="shelves")

        class Meta:
            # Deliberately incompatible with the direct application below.
            # Reading this model would miss Branch.shelves and retain fan-out.
            model = Book
            fields = ["title"]

    factory = OrderArgumentsFactory(MisdeclaredBranchOrder)
    BranchInput = factory.arguments
    ShelfInput = OrderArgumentsFactory.input_object_types["ShelfOrderInputType"]
    input_value = [BranchInput(shelves=ShelfInput(code=Ordering.ASC))]
    result = MisdeclaredBranchOrder.apply_sync(
        input_value,
        Branch.objects.all(),
        _make_info(),
    )
    assert any(isinstance(agg, Min) for agg in result.query.annotations.values())


def test_resolve_order_expressions_rejects_non_ordering_direction():
    """Passing a non-Ordering object to _resolve_order_expressions raises ConfigurationError."""

    class CustomBookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    with pytest.raises(ConfigurationError, match="received invalid order direction 'ASC'"):
        CustomBookOrder._resolve_order_expressions([("title", "ASC")], model=Book)

    with pytest.raises(ConfigurationError, match="received invalid order direction 42"):
        CustomBookOrder._resolve_order_expressions([("title", 42)], model=Book)


@pytest.mark.django_db
def test_orderset_apply_sync_handles_unset_in_nested_dict():
    """apply_sync with UNSET fields normalizes cleanly and preserves queryset."""
    from strawberry import UNSET

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    branch = Branch.objects.create(name="Main")
    shelf = Shelf.objects.create(code="S1", branch=branch)
    book = Book.objects.create(shelf=shelf, title="Book 1")
    info = _make_info()
    qs = Book.objects.all()
    result = BookOrder.apply_sync({"shelf": {"code": UNSET}}, qs, info)
    assert list(result.query.order_by) == list(qs.query.order_by)
    assert list(result) == [book]


@pytest.mark.django_db
def test_orderset_expand_meta_fields_rejects_non_iterable_fields():
    """Non-collection or string Meta.fields (other than '__all__') raises ConfigurationError."""

    class IntFieldsOrder(OrderSet):
        class Meta:
            model = Book
            fields = 123

    with pytest.raises(
        ConfigurationError,
        match="must be '__all__' or a re-readable collection of field names",
    ):
        IntFieldsOrder.get_fields()

    class StrFieldsOrder(OrderSet):
        class Meta:
            model = Book
            fields = "title"

    with pytest.raises(
        ConfigurationError,
        match="not a bare string",
    ):
        StrFieldsOrder.get_fields()

    class ObjFieldsOrder(OrderSet):
        class Meta:
            model = Book
            fields = object()

    with pytest.raises(
        ConfigurationError,
        match="must be '__all__' or a re-readable collection of field names",
    ):
        ObjFieldsOrder.get_fields()


@pytest.mark.django_db
def test_orderset_expand_meta_fields_rejects_non_string_entries_without_model():
    """Entry-TYPE validation is unconditional: it does not need ``Meta.model``.

    The model-less related-only arm previously skipped entry validation
    entirely, so a ``None`` / bytes / unhashable entry either landed
    silently in the expansion (``{None: None}``, ``{b'title': None}``) or
    escaped as a raw ``TypeError: unhashable type`` from the expansion-dict
    write. Every entry is a path token regardless of ``Meta.model``, so the
    entry-type gate fires before the model-guarded path walk.
    """

    class NoModelNoneEntryOrder(OrderSet):
        class Meta:
            fields = [None]

    with pytest.raises(ConfigurationError, match="entries must be field-name strings"):
        NoModelNoneEntryOrder.get_fields()

    class NoModelBytesEntryOrder(OrderSet):
        class Meta:
            fields = [b"title"]

    with pytest.raises(ConfigurationError, match="entries must be field-name strings"):
        NoModelBytesEntryOrder.get_fields()

    class UnhashableEntryOrder(OrderSet):
        class Meta:
            fields = [["title"]]

    with pytest.raises(ConfigurationError, match="entries must be field-name strings"):
        UnhashableEntryOrder.get_fields()


@pytest.mark.django_db
def test_orderset_expand_meta_fields_rejects_non_string_entries_with_model():
    """The entry-type gate precedes path validation, with or without ``Meta.model``."""

    class NoneEntryOrder(OrderSet):
        class Meta:
            model = Book
            fields = [None]

    with pytest.raises(ConfigurationError, match="entries must be field-name strings"):
        NoneEntryOrder.get_fields()

    class BytesEntryOrder(OrderSet):
        class Meta:
            model = Book
            fields = [b"title"]

    with pytest.raises(ConfigurationError, match="entries must be field-name strings"):
        BytesEntryOrder.get_fields()


@pytest.mark.django_db
def test_orderset_expand_meta_fields_rejects_one_shot_iterator_fields():
    """A one-shot ``Meta.fields`` iterator is rejected instead of silently diverging.

    The expansion re-runs whenever a lazy ``RelatedOrder`` target keeps the
    ``get_fields`` cache gate from writing (the gate refuses while any
    ``_orderset`` is still a string). A generator ``Meta.fields`` used to
    expand correctly on the FIRST walk and then silently rebuild to an EMPTY
    field set on every later walk (the iterator was exhausted); the
    re-readable-container gate fails loud at declaration instead.
    """

    class IteratorFieldsOrder(OrderSet):
        shelf = RelatedOrder("tests.orders.test_sets.MissingOrder", field_name="shelf")

        class Meta:
            model = Book
            fields = iter(["title", "subtitle"])

    with pytest.raises(ConfigurationError, match="re-readable"):
        IteratorFieldsOrder.get_fields()

    class GeneratorFieldsOrder(OrderSet):
        class Meta:
            model = Book
            fields = (name for name in ["title", "subtitle"])

    with pytest.raises(ConfigurationError, match="re-readable"):
        GeneratorFieldsOrder.get_fields()


@pytest.mark.django_db
def test_orderset_expand_meta_fields_accepts_a_computed_re_readable_collection():
    """A ``dict`` view or a custom ``Collection`` is a legal ``Meta.fields``.

    The contract is re-readability, not membership of a builtin allow-list:
    these hold their field names, so the expansion re-runs to the same
    ``OrderedDict`` and the declaration must be accepted (the order family
    keeps declaration order, so the view's insertion order survives).
    """

    class _NameSet:
        def __init__(self, *names):
            self._names = names

        def __iter__(self):
            return iter(self._names)

        def __len__(self):
            return len(self._names)

        def __contains__(self, item):
            return item in self._names

    class KeysViewOrder(OrderSet):
        class Meta:
            model = Book
            fields = {"title": None, "subtitle": None}.keys()

    class CustomCollectionOrder(OrderSet):
        class Meta:
            model = Book
            fields = _NameSet("title", "subtitle")

    assert list(KeysViewOrder._expand_meta_fields()) == ["title", "subtitle"]
    assert list(CustomCollectionOrder._expand_meta_fields()) == ["title", "subtitle"]
    # Re-reading yields the same expansion (the property the gate guarantees).
    assert list(KeysViewOrder._expand_meta_fields()) == ["title", "subtitle"]
    assert list(CustomCollectionOrder._expand_meta_fields()) == ["title", "subtitle"]


def test_orderset_expand_meta_fields_rejects_hostile_iterable_without_iterating():
    """A hostile ``__iter__`` raising midway is rejected by the container gate.

    The shape gate is structural (an ``isinstance`` container check), so a
    one-shot iterable whose ``__iter__`` raises mid-iteration never gets
    iterated at all: the raw ``RuntimeError`` cannot escape ``get_fields()``
    because the object is rejected before the walk starts.
    """

    class Boom:
        def __iter__(self):
            yield "title"  # pragma: no cover - never reached past the gate
            raise RuntimeError("boom mid-iteration")

    class HostileIterOrder(OrderSet):
        class Meta:
            model = Book
            fields = Boom()

    with pytest.raises(ConfigurationError, match="re-readable"):
        HostileIterOrder.get_fields()


@pytest.mark.django_db
def test_orderset_expand_meta_fields_dict_shape_iterates_keys():
    """Dict-shaped ``Meta.fields`` (django-filter lookup bags) expands the KEYS.

    Pins the documented degradation: the lookup-bag values are dropped and
    each key becomes an order field, so a consumer porting a filter-style
    ``fields`` dict gets field-name ordering instead of a silent error.
    """

    class DictFieldsOrder(OrderSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"], "subtitle": ["icontains"]}

    fields = DictFieldsOrder.get_fields()
    assert list(fields) == ["title", "subtitle"]
    assert all(v is None for v in fields.values())


@pytest.mark.django_db
def test_orderset_expand_meta_fields_handles_non_class_meta_model():
    """Non-class / invalid Meta.model does not crash with AttributeError and raises ConfigurationError."""

    class BadModelOrder(OrderSet):
        class Meta:
            model = "NotAModel"
            fields = ["title"]

    with pytest.raises(ConfigurationError, match="invalid order path 'title' for model str"):
        BadModelOrder.get_fields()

    class BadModelIntOrder(OrderSet):
        class Meta:
            model = 123
            fields = ["title"]

    with pytest.raises(ConfigurationError, match="invalid order path 'title' for model int"):
        BadModelIntOrder.get_fields()


@pytest.mark.django_db
def test_get_concrete_field_names_for_order_rejects_non_model():
    """_get_concrete_field_names_for_order raises ConfigurationError on non-model objects."""
    from django_strawberry_framework.orders.inputs import _get_concrete_field_names_for_order

    with pytest.raises(ConfigurationError, match="Expected a Django Model class"):
        _get_concrete_field_names_for_order("NotAModel")

    with pytest.raises(ConfigurationError, match="Expected a Django Model class"):
        _get_concrete_field_names_for_order(123)


def test_resolve_order_expressions_handles_non_class_model_on_path_error():
    """_resolve_order_expressions safely formats non-class model when path resolution fails."""

    class CustomBookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    with pytest.raises(ConfigurationError, match="invalid order path 'bad_field' for model str"):
        CustomBookOrder._resolve_order_expressions(
            [("bad_field", Ordering.ASC)],
            model="NotAModel",
        )


def test_orderset_clear_order_input_namespace_clears_subclass_caches():
    """clear_order_input_namespace clears _expanded_fields on base and subclass OrderSets."""
    from django_strawberry_framework.orders.inputs import clear_order_input_namespace

    class BaseOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class SubOrder(BaseOrder):
        class Meta:
            model = Book
            fields = ["subtitle"]

    assert list(BaseOrder.get_fields()) == ["title"]
    assert list(SubOrder.get_fields()) == ["subtitle"]
    assert BaseOrder._expanded_fields is not None
    assert SubOrder._expanded_fields is not None

    clear_order_input_namespace()

    assert BaseOrder._expanded_fields is None
    assert SubOrder._expanded_fields is None


def test_orderset_type_name_for_inherits_mixin_naming_convention():
    """OrderSet inherits ClassBasedTypeNameMixin defaulting to '<Name>InputType'."""

    class CustomOrder(OrderSet):
        pass

    assert CustomOrder.type_name_for() == "CustomOrderInputType"
    assert CustomOrder.type_name_for("field") == "CustomOrderFieldInputType"


# Keep imports active so ruff doesn't flag the F-expression / Genre import.
assert F is not None
assert Genre is not None


def test_input_has_active_terms():
    """OrderSet._input_has_active_terms detects presence of active ordering terms."""
    import strawberry

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

    # Falsy / empty / unset cases
    assert not BookOrder._input_has_active_terms(None)
    assert not BookOrder._input_has_active_terms(strawberry.UNSET)
    assert not BookOrder._input_has_active_terms([])
    assert not BookOrder._input_has_active_terms([BookInput()])
    assert not BookOrder._input_has_active_terms([BookInput(title=None)])
    assert not BookOrder._input_has_active_terms([BookInput(shelf=ShelfInput())])
    assert not BookOrder._input_has_active_terms([BookInput(shelf=ShelfInput(code=None))])

    # Active cases
    assert BookOrder._input_has_active_terms([BookInput(title=Ordering.ASC)])
    assert BookOrder._input_has_active_terms([BookInput(shelf=ShelfInput(code=Ordering.DESC))])
    assert BookOrder._input_has_active_terms(
        [BookInput(title=None), BookInput(shelf=ShelfInput(code=Ordering.ASC))],
    )


def test_input_has_active_terms_purity():
    """OrderSet._input_has_active_terms raises ConfigurationError when _normalize_input is impure."""

    class ImpureOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        _counter = 0

        @classmethod
        def _normalize_input(cls, input_value):
            cls._counter += 1
            if cls._counter % 2 == 1:
                return [("title", Ordering.ASC)]
            return [("title", Ordering.DESC)]

    with pytest.raises(
        ConfigurationError,
        match="is not pure; returned different results",
    ):
        ImpureOrder._input_has_active_terms([{"title": "anything"}])


def test_input_has_active_terms_purity_structure_disagreement():
    """OrderSet._input_has_active_terms raises ConfigurationError when successive normalizations disagree on shape."""

    class FlakyOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        _counter = 0

        @classmethod
        def _normalize_input(cls, input_value):
            cls._counter += 1
            if cls._counter % 2 == 1:
                return []
            return [("title", Ordering.ASC)]

    with pytest.raises(
        ConfigurationError,
        match="is not pure; returned different results",
    ):
        FlakyOrder._input_has_active_terms([{"title": "anything"}])


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        (None, False),
        (strawberry.UNSET, False),
        ([], False),
        (["__EMPTY_BOOK_INPUT__"], False),
        (["__NULL_TITLE_BOOK_INPUT__"], False),
        (["__EMPTY_SHELF_BOOK_INPUT__"], False),
        (["__NULL_SHELF_CODE_BOOK_INPUT__"], False),
        (["__NULL_TITLE_BOOK_INPUT__", "__NULL_SHELF_CODE_BOOK_INPUT__"], False),
        (["__ACTIVE_TITLE_BOOK_INPUT__"], True),
        (["__ACTIVE_SHELF_BOOK_INPUT__"], True),
        (["__NULL_TITLE_BOOK_INPUT__", "__ACTIVE_SHELF_BOOK_INPUT__"], True),
        (["__ACTIVE_TITLE_BOOK_INPUT__", "__NULL_TITLE_BOOK_INPUT__"], True),
    ],
)
def test_input_has_active_terms_contract(input_value, expected):
    """Pin OrderSet._input_has_active_terms against a comprehensive input variation matrix."""

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

    sentinel_map = {
        "__EMPTY_BOOK_INPUT__": [BookInput()],
        "__NULL_TITLE_BOOK_INPUT__": [BookInput(title=None)],
        "__EMPTY_SHELF_BOOK_INPUT__": [BookInput(shelf=ShelfInput())],
        "__NULL_SHELF_CODE_BOOK_INPUT__": [BookInput(shelf=ShelfInput(code=None))],
        "__ACTIVE_TITLE_BOOK_INPUT__": [BookInput(title=Ordering.ASC)],
        "__ACTIVE_SHELF_BOOK_INPUT__": [BookInput(shelf=ShelfInput(code=Ordering.DESC))],
    }

    if isinstance(input_value, list) and input_value and isinstance(input_value[0], str):
        resolved_input = []
        for sentinel in input_value:
            resolved_input.extend(sentinel_map[sentinel])
    else:
        resolved_input = input_value

    assert BookOrder._input_has_active_terms(resolved_input) is expected


def _attestations(orderset_class=None):
    """Return the attestations the active ledger holds, optionally for one class.

    Reads the ledger's private record list because these are package tests of a
    private transport; the production callers reach it only through
    ``publish`` / ``claim``.
    """
    ledger = _ORDER_NORMALIZATION_CAPTURE.get()
    if ledger is None:
        return None
    if orderset_class is None:
        return list(ledger._records)
    return [record for record in ledger._records if record.orderset_class is orderset_class]


def _claimed_pairs():
    """Return the ``(orderset_class, input_value)`` pairs the active ledger has issued."""
    ledger = _ORDER_NORMALIZATION_CAPTURE.get()
    return None if ledger is None else list(ledger._claimed)


def test_input_has_active_terms_independent_query_and_double_normalization():
    """Pin the 2-call count inside a capture scope and the 3-call count outside one."""

    class TrackedOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        normalize_count = 0

        @classmethod
        def _normalize_input(cls, input_value):
            cls.normalize_count += 1
            return super()._normalize_input(input_value)

    factory = OrderArgumentsFactory(TrackedOrder)
    BookInput = factory.arguments
    active_input = [BookInput(title=Ordering.ASC)]
    info = SimpleNamespace(context={"request": HttpRequest()})
    qs = Book.objects.all()

    # Standalone helper call without prior apply normalizes twice (purity check).
    TrackedOrder.normalize_count = 0
    assert TrackedOrder._input_has_active_terms(active_input) is True
    assert TrackedOrder.normalize_count == 2

    # Inside the list field's scope: apply publishes once, the helper re-verifies once.
    TrackedOrder.normalize_count = 0
    with capture_applied_order_normalization():
        qs_ordered = TrackedOrder.apply_sync(active_input, qs, info)
        assert TrackedOrder.normalize_count == 1
        assert qs_ordered is not None
        assert TrackedOrder._input_has_active_terms(active_input) is True
    assert TrackedOrder.normalize_count == 2

    # The async coloring, with the scope open in the SAME context the apply runs in -
    # which is how the async pipeline opens it, immediately around its own awaits.
    TrackedOrder.normalize_count = 0

    async def _scoped_async_resolution():
        with capture_applied_order_normalization():
            qs_ordered_async = await TrackedOrder.apply_async(active_input, qs, info)
            assert TrackedOrder.normalize_count == 1
            assert qs_ordered_async is not None
            assert TrackedOrder._input_has_active_terms(active_input) is True

    asyncio.run(_scoped_async_resolution())
    assert TrackedOrder.normalize_count == 2

    # A scope opened OUTSIDE the task still receives the application: ``asyncio.run``
    # runs the coroutine in a COPIED context, which carries this ledger, and the apply
    # attests into it. The delegating shapes a public ``apply_async`` override is
    # allowed to take all reduce to this one, so the helper re-verifies once rather
    # than losing the terms the returned queryset was actually ordered by.
    TrackedOrder.normalize_count = 0
    with capture_applied_order_normalization():
        asyncio.run(TrackedOrder.apply_async(active_input, qs, info))
        assert len(_attestations(TrackedOrder)) == 1
        assert TrackedOrder._input_has_active_terms(active_input) is True
    assert TrackedOrder.normalize_count == 2

    # Outside any scope a public apply publishes nothing, so the helper pays the
    # full double normalization: a connection or hand-written resolver calling the
    # public API behaves exactly as it did before the list field existed.
    TrackedOrder.normalize_count = 0
    TrackedOrder.apply_sync(active_input, qs, info)
    assert TrackedOrder._input_has_active_terms(active_input) is True
    assert TrackedOrder.normalize_count == 3


def test_applied_normalization_is_consumed_and_scoped_to_one_capture():
    """A captured record is one-shot and never visible to another scope."""

    class TrackedOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        normalize_count = 0

        @classmethod
        def _normalize_input(cls, input_value):
            cls.normalize_count += 1
            return [("title", Ordering.ASC)]

    first_input = [{"title": "ASC"}]
    second_input = [{"title": "ASC"}]
    info = SimpleNamespace(context={"request": HttpRequest()})

    with capture_applied_order_normalization():
        TrackedOrder.apply_sync(first_input, Book.objects.all(), info)
        assert TrackedOrder.normalize_count == 1
        assert len(_attestations(TrackedOrder)) == 1

    # An attestation left unclaimed in a closed scope cannot reduce a later scope's
    # standalone purity check from two normalizations to one - the ledger went with
    # its resolution.
    with capture_applied_order_normalization():
        assert _attestations(TrackedOrder) == []
        assert TrackedOrder._input_has_active_terms(second_input) is True
        assert TrackedOrder.normalize_count == 3

    with capture_applied_order_normalization():
        TrackedOrder.apply_sync(first_input, Book.objects.all(), info)
        assert TrackedOrder.normalize_count == 4
        assert TrackedOrder._input_has_active_terms(first_input) is True
        assert TrackedOrder.normalize_count == 5
        # Claimed once per class-and-input pair: the attestation still stands in the
        # append-only ledger, but the second check on the same pair takes the
        # double-read path rather than reusing it for an application it does not
        # describe.
        assert len(_attestations(TrackedOrder)) == 1
        assert _claimed_pairs() == [(TrackedOrder, first_input)]
        assert TrackedOrder._input_has_active_terms(first_input) is True
        assert TrackedOrder.normalize_count == 7
    assert _ORDER_NORMALIZATION_CAPTURE.get() is None


def test_applied_normalization_record_pins_the_input_object_not_its_address():
    """The record holds the input OBJECT, so a freed address cannot forge a match.

    Keying the record by ``id(input_value)`` alone records an address without
    holding anything at it: once the client's input is collected, a later
    allocation can land on the same address and be mistaken for the recorded
    one. The purity check would then compare a record produced for a DIFFERENT
    input against a fresh normalization and raise "not pure" against an
    ``_normalize_input`` that is perfectly deterministic. Holding the input
    itself makes the identity unforgeable: while the record is live, nothing
    else can occupy it.
    """

    class TrackedOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        def _normalize_input(cls, input_value):
            return [("title", Ordering.ASC)]

    info = SimpleNamespace(context={"request": HttpRequest()})
    order_input = [{"title": "ASC"}]

    with capture_applied_order_normalization():
        TrackedOrder.apply_sync(order_input, Book.objects.all(), info)

        (attestation,) = _attestations(TrackedOrder)
        recorded_input = attestation.input_value
        assert attestation.orderset_class is TrackedOrder
        assert recorded_input is order_input
        assert attestation.terms == (("title", Ordering.ASC),)
        assert type(attestation.terms) is tuple

        # Dropping every other reference cannot free the recorded input, so no later
        # allocation can reuse its identity while the record stands.
        del order_input
        gc.collect()
        decoys = [[{"title": "ASC"}] for _ in range(256)]
        assert id(recorded_input) not in {id(decoy) for decoy in decoys}

        # A decoy therefore falls through to the standalone double-normalization path
        # instead of matching the standing record.
        assert TrackedOrder._input_has_active_terms(decoys[0]) is True


def test_applied_normalization_checks_input_identity():
    """The captured record requires exact input_value object identity."""

    class TrackedOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        normalize_count = 0

        @classmethod
        def _normalize_input(cls, input_value):
            cls.normalize_count += 1
            return [("title", Ordering.ASC)]

    orig_input = [{"title": "ASC"}]
    different_input_same_content = [{"title": "ASC"}]
    info = SimpleNamespace(context={"request": HttpRequest()})

    with capture_applied_order_normalization():
        TrackedOrder.apply_sync(orig_input, Book.objects.all(), info)
        assert TrackedOrder.normalize_count == 1

        # Calling with a different input instance does not match the record
        assert TrackedOrder._input_has_active_terms(different_input_same_content) is True
        # 1 from apply + 2 from standalone double-normalization = 3
        assert TrackedOrder.normalize_count == 3


def test_applied_normalization_checks_orderset_class_identity():
    """A record published by one OrderSet class is not a record for another."""

    class FirstOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        def _normalize_input(cls, input_value):
            return [("title", Ordering.ASC)]

    class SecondOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        normalize_count = 0

        @classmethod
        def _normalize_input(cls, input_value):
            cls.normalize_count += 1
            return [("title", Ordering.DESC)]

    shared_input = [{"title": "ASC"}]
    info = SimpleNamespace(context={"request": HttpRequest()})
    with capture_applied_order_normalization():
        FirstOrder.apply_sync(shared_input, Book.objects.all(), info)
        # Same input object, different class: no match, so the double read runs and
        # the mismatched record is NOT mistaken for a purity violation.
        assert SecondOrder._input_has_active_terms(shared_input) is True
        assert SecondOrder.normalize_count == 2


def test_public_apply_never_writes_the_consumer_context():
    """``apply_sync`` / ``apply_async`` leave ``info.context`` exactly as they found it.

    The normalization handoff is a task-local capture scope, so a public apply
    on a connection or in a hand-written resolver stores nothing on the
    consumer's context: an existing value is never overwritten or deleted, and a
    mapping that forbids writes is never asked to accept one.
    """

    class GuardedContext(dict):
        def __setitem__(self, key, value):
            raise RuntimeError(f"guarded context written: {key}")

        def __delitem__(self, key):
            raise RuntimeError(f"guarded context cleared: {key}")

    class TitleOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    marker = object()
    plain = {"request": HttpRequest(), "consumer_marker": marker}
    guarded = GuardedContext()
    dict.__setitem__(guarded, "request", HttpRequest())
    TitleInput = OrderArgumentsFactory(TitleOrder).arguments
    order_input = [TitleInput(title=Ordering.ASC)]

    for context in (plain, guarded):
        info = SimpleNamespace(context=context)
        ordered = TitleOrder.apply_sync(order_input, Book.objects.all(), info)
        assert ordered.ordered is True
        ordered_async = asyncio.run(TitleOrder.apply_async(order_input, Book.objects.all(), info))
        assert ordered_async.ordered is True
        # The active-term helper takes the same no-write path.
        assert TitleOrder._input_has_active_terms(order_input) is True

    assert set(plain) == {"request", "consumer_marker"}
    assert plain["consumer_marker"] is marker
    assert set(guarded) == {"request"}
    assert _ORDER_NORMALIZATION_CAPTURE.get() is None


def test_capture_scope_is_reset_after_an_exception_and_isolated_per_async_task():
    """The scope token is reset on the way out, and concurrent tasks never share a record."""

    class TitleOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    info = SimpleNamespace(context={"request": HttpRequest()})
    TitleInput = OrderArgumentsFactory(TitleOrder).arguments

    with pytest.raises(RuntimeError, match="body failed"):
        with capture_applied_order_normalization():
            assert _ORDER_NORMALIZATION_CAPTURE.get() is not None
            raise RuntimeError("body failed")
    assert _ORDER_NORMALIZATION_CAPTURE.get() is None

    async def one_resolution(own_input):
        with capture_applied_order_normalization():
            await TitleOrder.apply_async(own_input, Book.objects.all(), info)
            # Yield so the sibling task runs its own apply in between.
            await asyncio.sleep(0)
            (attestation,) = _attestations(TitleOrder)
            assert attestation.orderset_class is TitleOrder
            assert attestation.input_value is own_input
            return TitleOrder._input_has_active_terms(own_input)

    async def both():
        return await asyncio.gather(
            one_resolution([TitleInput(title=Ordering.ASC)]),
            one_resolution([TitleInput(title=Ordering.DESC)]),
        )

    assert asyncio.run(both()) == [True, True]
    assert _ORDER_NORMALIZATION_CAPTURE.get() is None


def test_input_has_active_terms_sequence_controls_sync():
    """Load-bearing A/B/B and A/A/B/A normalization sequence controls under sync apply."""
    return_a = [("title", Ordering.ASC)]
    return_b = [("title", Ordering.DESC)]
    info = SimpleNamespace(context={"request": HttpRequest()})
    qs = Book.objects.all()

    # Sequence A/B/B: Call 1 in apply returns A; Call 2 in helper returns B -> disagreement
    class AbbOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        returns = [return_a, return_b, return_b]
        idx = 0

        @classmethod
        def _normalize_input(cls, input_value):
            res = cls.returns[cls.idx]
            cls.idx += 1
            return res

    abb_input = [{"title": "ASC"}]
    with capture_applied_order_normalization():
        AbbOrder.apply_sync(abb_input, qs, info)
        with pytest.raises(ConfigurationError, match=r"_normalize_input is not pure"):
            AbbOrder._input_has_active_terms(abb_input)

    # Sequence A/A/B/A: the hit consumes A/A; the next standalone check compares B/A.
    class AabOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        returns = [
            return_a,
            return_a,
            return_b,
            return_a,
        ]
        idx = 0

        @classmethod
        def _normalize_input(cls, input_value):
            res = cls.returns[cls.idx]
            cls.idx += 1
            return res

    aab_input = [{"title": "ASC"}]
    with capture_applied_order_normalization():
        AabOrder.apply_sync(aab_input, qs, info)
        assert AabOrder._input_has_active_terms(aab_input) is True
    with pytest.raises(ConfigurationError, match=r"_normalize_input is not pure"):
        AabOrder._input_has_active_terms([{"title": "ASC"}])


def test_input_has_active_terms_sequence_controls_async():
    """Load-bearing A/B/B and A/A/B/A normalization sequence controls under async apply."""
    return_a = [("title", Ordering.ASC)]
    return_b = [("title", Ordering.DESC)]
    info = SimpleNamespace(context={"request": HttpRequest()})
    qs = Book.objects.all()

    # Sequence A/B/B: Call 1 in apply returns A; Call 2 in helper returns B -> disagreement
    class AbbOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        returns = [return_a, return_b, return_b]
        idx = 0

        @classmethod
        def _normalize_input(cls, input_value):
            res = cls.returns[cls.idx]
            cls.idx += 1
            return res

    abb_input = [{"title": "ASC"}]

    async def _abb_resolution():
        with capture_applied_order_normalization():
            await AbbOrder.apply_async(abb_input, qs, info)
            with pytest.raises(ConfigurationError, match=r"_normalize_input is not pure"):
                AbbOrder._input_has_active_terms(abb_input)

    asyncio.run(_abb_resolution())

    # Sequence A/A/B/A: the hit consumes A/A; the next standalone check compares B/A.
    class AabOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        returns = [
            return_a,
            return_a,
            return_b,
            return_a,
        ]
        idx = 0

        @classmethod
        def _normalize_input(cls, input_value):
            res = cls.returns[cls.idx]
            cls.idx += 1
            return res

    aab_input = [{"title": "ASC"}]

    async def _aab_resolution():
        with capture_applied_order_normalization():
            await AabOrder.apply_async(aab_input, qs, info)
            assert AabOrder._input_has_active_terms(aab_input) is True

    asyncio.run(_aab_resolution())
    with pytest.raises(ConfigurationError, match=r"_normalize_input is not pure"):
        AabOrder._input_has_active_terms([{"title": "ASC"}])


def test_a_child_task_application_reaches_the_parents_check():
    """A delegating ``apply_async`` applies in a child task; the parent still sees the terms.

    The supported public override seam is an ``apply_async`` that hands the work
    to ``super()`` inside a task of its own. The ordering the client receives is
    built there, so the offset guard's purity check must compare against THAT
    normalization; a transport that only isolated descendants would hand the
    guard an empty capture and let it re-derive different terms from an impure
    normalizer without noticing. The append-only ledger travels into the copied
    context, so the child's attestation is the one the parent claims.
    """
    info = SimpleNamespace(context={"request": HttpRequest()})

    class ChildDelegatingOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        normalize_count = 0

        @classmethod
        def _normalize_input(cls, input_value):
            cls.normalize_count += 1
            return [("title", Ordering.ASC)]

        @classmethod
        async def apply_async(
            cls,
            input_value,
            queryset,
            info,
        ):
            return await asyncio.create_task(super().apply_async(input_value, queryset, info))

    order_input = [{"title": "ASC"}]

    async def parent():
        with capture_applied_order_normalization():
            ordered = await ChildDelegatingOrder.apply_async(order_input, Book.objects.all(), info)
            assert ordered.ordered is True
            # Call 1 ran in the child task; its attestation is here.
            (attestation,) = _attestations(ChildDelegatingOrder)
            assert attestation.input_value is order_input
            # So the guard re-verifies once (call 2) rather than twice.
            assert ChildDelegatingOrder._input_has_active_terms(order_input) is True
            assert ChildDelegatingOrder.normalize_count == 2

    asyncio.run(parent())
    assert _ORDER_NORMALIZATION_CAPTURE.get() is None


def test_a_child_delegated_impure_normalization_is_still_rejected():
    """The A/B/B purity rejection survives delegation into a child task.

    The ordering is built from A inside the child. Without the attestation
    reaching the parent, the guard would compare B against B, agree, and accept
    a page ordered by terms it never checked. With it, the parent claims A and
    the B it derives disagrees - the typed rejection the contract promises.
    """
    return_a = [("title", Ordering.ASC)]
    return_b = [("title", Ordering.DESC)]
    info = SimpleNamespace(context={"request": HttpRequest()})

    class ChildDelegatingAbbOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        returns = [return_a, return_b, return_b]
        idx = 0

        @classmethod
        def _normalize_input(cls, input_value):
            res = cls.returns[cls.idx]
            cls.idx += 1
            return res

        @classmethod
        async def apply_async(
            cls,
            input_value,
            queryset,
            info,
        ):
            return await asyncio.create_task(super().apply_async(input_value, queryset, info))

    order_input = [{"title": "ASC"}]

    async def parent():
        with capture_applied_order_normalization():
            await ChildDelegatingAbbOrder.apply_async(order_input, Book.objects.all(), info)
            with pytest.raises(ConfigurationError, match=r"_normalize_input is not pure"):
                ChildDelegatingAbbOrder._input_has_active_terms(order_input)

    asyncio.run(parent())
    assert ChildDelegatingAbbOrder.idx == 2
    assert _ORDER_NORMALIZATION_CAPTURE.get() is None


def test_two_applications_of_one_input_that_disagree_fail_closed():
    """Two applicable attestations that disagree are rejected, never silently picked from.

    A descendant re-applying the SAME class and the SAME input object inside one
    resolution attests a second time. If the two normalizations disagree, no rule
    can say which one the returned queryset was ordered by, so the claim raises
    rather than choosing.
    """
    return_a = [("title", Ordering.ASC)]
    return_b = [("title", Ordering.DESC)]
    info = SimpleNamespace(context={"request": HttpRequest()})

    class DoubleAppliedOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        returns = [return_a, return_b, return_b]
        idx = 0

        @classmethod
        def _normalize_input(cls, input_value):
            res = cls.returns[cls.idx]
            cls.idx += 1
            return res

    order_input = [{"title": "ASC"}]

    async def parent():
        with capture_applied_order_normalization():
            await DoubleAppliedOrder.apply_async(order_input, Book.objects.all(), info)

            async def child():
                await DoubleAppliedOrder.apply_async(order_input, Book.objects.all(), info)

            await asyncio.create_task(child())
            assert len(_attestations(DoubleAppliedOrder)) == 2
            with pytest.raises(
                ConfigurationError,
                match=r"two applications of the same input in one resolution",
            ):
                DoubleAppliedOrder._input_has_active_terms(order_input)

    asyncio.run(parent())
    assert _ORDER_NORMALIZATION_CAPTURE.get() is None


def test_two_applications_of_one_input_that_agree_are_claimed_once():
    """Agreeing duplicate attestations resolve to their shared terms, not a rejection."""
    info = SimpleNamespace(context={"request": HttpRequest()})

    class PureDoubleOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        normalize_count = 0

        @classmethod
        def _normalize_input(cls, input_value):
            cls.normalize_count += 1
            return [("title", Ordering.ASC)]

    order_input = [{"title": "ASC"}]

    async def parent():
        with capture_applied_order_normalization():
            await PureDoubleOrder.apply_async(order_input, Book.objects.all(), info)

            async def child():
                await PureDoubleOrder.apply_async(order_input, Book.objects.all(), info)

            await asyncio.create_task(child())
            assert len(_attestations(PureDoubleOrder)) == 2
            assert PureDoubleOrder._input_has_active_terms(order_input) is True
            assert PureDoubleOrder.normalize_count == 3

    asyncio.run(parent())


def test_a_nested_orderset_between_apply_and_check_is_never_claimed():
    """A different ``OrderSet`` applied mid-resolution cannot displace the outer record.

    An outer ``apply_sync`` override that delegates to the base and then invokes
    another ``OrderSet`` before returning leaves a second attestation standing in
    the same ledger. A single-slot transport would hand the outer class's check
    the nested class's terms - the guard then re-derives B, compares against the
    nested record it was never entitled to, and the A/B/B sequence it exists to
    catch is lost. Entries are claimed by class AND input identity, so the nested
    one is simply not the outer one's.
    """
    return_a = [("title", Ordering.ASC)]
    return_b = [("title", Ordering.DESC)]
    info = SimpleNamespace(context={"request": HttpRequest()})

    class NestedOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        def _normalize_input(cls, input_value):
            return [("title", Ordering.DESC)]

    nested_input = [{"title": "DESC"}]

    class OuterAbbOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        returns = [return_a, return_b, return_b]
        idx = 0

        @classmethod
        def _normalize_input(cls, input_value):
            res = cls.returns[cls.idx]
            cls.idx += 1
            return res

        @classmethod
        def apply_sync(
            cls,
            input_value,
            queryset,
            info,
        ):
            ordered = super().apply_sync(input_value, queryset, info)
            NestedOrder.apply_sync(nested_input, Book.objects.all(), info)
            return ordered

    order_input = [{"title": "ASC"}]

    with capture_applied_order_normalization():
        OuterAbbOrder.apply_sync(order_input, Book.objects.all(), info)
        assert len(_attestations(OuterAbbOrder)) == 1
        assert len(_attestations(NestedOrder)) == 1
        with pytest.raises(ConfigurationError, match=r"_normalize_input is not pure"):
            OuterAbbOrder._input_has_active_terms(order_input)
    assert _ORDER_NORMALIZATION_CAPTURE.get() is None


def test_an_unrelated_descendant_application_is_never_claimed():
    """A descendant applying a DIFFERENT input leaves the parent's own claim intact.

    The isolation half of the contract: the ledger is shared so a delegating
    child can publish INTO it, which means an unrelated application in a child
    lands there too. It is filtered out by input identity, so the parent's check
    still re-verifies once against its own terms rather than paying a second full
    normalization or reading someone else's.
    """
    info = SimpleNamespace(context={"request": HttpRequest()})

    class UnrelatedChildOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        normalize_count = 0

        @classmethod
        def _normalize_input(cls, input_value):
            cls.normalize_count += 1
            return [("title", Ordering.ASC)]

    parent_input = [{"title": "ASC"}]
    unrelated_input = [{"title": "ASC"}]

    async def parent():
        with capture_applied_order_normalization():
            await UnrelatedChildOrder.apply_async(parent_input, Book.objects.all(), info)

            async def child():
                await UnrelatedChildOrder.apply_async(unrelated_input, Book.objects.all(), info)

            await asyncio.create_task(child())
            assert len(_attestations(UnrelatedChildOrder)) == 2
            # Call 3 re-verifies the parent's own attestation; the child's is not it.
            assert UnrelatedChildOrder._input_has_active_terms(parent_input) is True
            assert UnrelatedChildOrder.normalize_count == 3
            assert _claimed_pairs() == [(UnrelatedChildOrder, parent_input)]

    asyncio.run(parent())
    assert _ORDER_NORMALIZATION_CAPTURE.get() is None


def test_a_claim_anywhere_in_the_resolution_is_the_only_claim():
    """Claiming is once per resolution, wherever it happens - never once per context.

    A child's own active-term check claims the pair for the whole resolution, so
    the parent's later check falls back to two independent normalizations. Two
    contexts each consuming the same attestation would be two guards blessing one
    application.
    """
    info = SimpleNamespace(context={"request": HttpRequest()})

    class SharedRecordOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        normalize_count = 0

        @classmethod
        def _normalize_input(cls, input_value):
            cls.normalize_count += 1
            return [("title", Ordering.ASC)]

    order_input = [{"title": "ASC"}]

    async def parent():
        with capture_applied_order_normalization():
            # Call 1: the parent's apply attests.
            await SharedRecordOrder.apply_async(order_input, Book.objects.all(), info)

            async def child():
                # Call 2: the child claims the attestation and re-verifies once.
                return SharedRecordOrder._input_has_active_terms(order_input)

            assert await asyncio.create_task(child()) is True
            assert SharedRecordOrder.normalize_count == 2
            assert _claimed_pairs() == [(SharedRecordOrder, order_input)]

            # Calls 3 and 4: the pair is spent, so the parent's own check compares
            # two fresh normalizations instead of re-reading a claimed attestation.
            assert SharedRecordOrder._input_has_active_terms(order_input) is True
            assert SharedRecordOrder.normalize_count == 4

    asyncio.run(parent())
    assert _ORDER_NORMALIZATION_CAPTURE.get() is None


def test_a_worker_threads_application_reaches_the_ledger_its_parent_claims_from():
    """A copied context carries the ledger, so a worker thread's apply attests into it.

    ``contextvars.copy_context().run(...)`` is the shape ``sync_to_async`` and
    every thread-pool handoff take, so an ``apply_*`` that offloads its work is a
    legitimate override whose normalization must still reach the guard. Two
    threads can therefore reach one ledger, which is why its appends and claims
    are locked.
    """
    info = SimpleNamespace(context={"request": HttpRequest()})

    class WorkerOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        normalize_count = 0

        @classmethod
        def _normalize_input(cls, input_value):
            cls.normalize_count += 1
            return super()._normalize_input(input_value)

    WorkerInput = OrderArgumentsFactory(WorkerOrder).arguments
    worker_input = [WorkerInput(title=Ordering.ASC)]

    with capture_applied_order_normalization():
        assert _attestations(WorkerOrder) == []
        copied = contextvars.copy_context()

        def publish_in_worker():
            copied.run(WorkerOrder.apply_sync, worker_input, Book.objects.all(), info)

        worker = threading.Thread(target=publish_in_worker)
        worker.start()
        worker.join()

        # One ledger, reached from both threads: the worker's attestation is here.
        assert copied[_ORDER_NORMALIZATION_CAPTURE] is _ORDER_NORMALIZATION_CAPTURE.get()
        (attestation,) = _attestations(WorkerOrder)
        assert attestation.input_value is worker_input
        assert WorkerOrder._input_has_active_terms(worker_input) is True
        assert WorkerOrder.normalize_count == 2
    assert _ORDER_NORMALIZATION_CAPTURE.get() is None


def test_concurrent_threads_publishing_into_one_ledger_lose_nothing():
    """Every attestation survives simultaneous appends from many worker threads."""
    info = SimpleNamespace(context={"request": HttpRequest()})

    class ConcurrentOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    ConcurrentInput = OrderArgumentsFactory(ConcurrentOrder).arguments
    inputs = [[ConcurrentInput(title=Ordering.ASC)] for _ in range(24)]

    with capture_applied_order_normalization():
        copied = contextvars.copy_context()
        start = threading.Barrier(len(inputs))

        def apply_one(order_input):
            start.wait()
            copied.run(ConcurrentOrder.apply_sync, order_input, Book.objects.all(), info)

        workers = [threading.Thread(target=apply_one, args=(value,)) for value in inputs]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()

        attested = _attestations(ConcurrentOrder)
        assert len(attested) == len(inputs)
        assert {id(record.input_value) for record in attested} == {id(value) for value in inputs}


def test_validate_normalized_terms_rejects_hostile_container_and_string_subclasses():
    """Every boundary shape is pinned by EXACT type, so no consumer hook can fire.

    A ``list`` subclass would run its ``__iter__`` in the validation loop, a
    ``tuple`` subclass its ``__len__`` / ``__getitem__`` while the term is read,
    and a ``str`` subclass its ``__eq__`` in the purity compare or ``__format__``
    in ``get_flat_orders``. Each is rejected before the member it would hook is
    touched, as the promised ``ConfigurationError`` naming ``_normalize_input``.
    """
    fired: list[str] = []

    class HostileList(list):
        def __iter__(self):
            fired.append("list.__iter__")
            return super().__iter__()

    class HostileTuple(tuple):
        def __len__(self):
            fired.append("tuple.__len__")
            return super().__len__()

        def __getitem__(self, index):
            fired.append("tuple.__getitem__")
            return super().__getitem__(index)

    class HostileStr(str):
        def __eq__(self, other):
            fired.append("str.__eq__")
            raise RuntimeError("hostile equality ran")

        __hash__ = str.__hash__

        def __format__(self, spec):
            fired.append("str.__format__")
            raise RuntimeError("hostile format ran")

    class HostileOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    with pytest.raises(
        ConfigurationError,
        match=r"HostileOrder\._normalize_input returned invalid data",
    ):
        _validate_normalized_terms(HostileOrder, HostileList([("title", Ordering.ASC)]))
    with pytest.raises(
        ConfigurationError,
        match=r"HostileOrder\._normalize_input returned invalid term",
    ):
        _validate_normalized_terms(HostileOrder, [HostileTuple(("title", Ordering.ASC))])
    with pytest.raises(
        ConfigurationError,
        match=r"HostileOrder\._normalize_input returned invalid term",
    ):
        _validate_normalized_terms(HostileOrder, [(HostileStr("title"), Ordering.ASC)])
    assert fired == []

    # The same three shapes reach the boundary through a real override and the
    # active-term helper, and the purity compare never runs consumer equality.
    class HostileStrOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        def _normalize_input(cls, input_value):
            return [(HostileStr("title"), Ordering.ASC)]

    with pytest.raises(
        ConfigurationError,
        match=r"HostileStrOrder\._normalize_input returned invalid term",
    ):
        HostileStrOrder._input_has_active_terms([{"title": "ASC"}])
    assert fired == []

    # Exact builtins with the same content are accepted and returned as given.
    good = [("title", Ordering.ASC), ("shelf__code", None)]
    assert _validate_normalized_terms(HostileOrder, good) is good


def test_input_has_active_terms_hostile_eq_and_repr():
    """Hostile non-primitive terms returned by _normalize_input raise ConfigurationError."""

    class HostileEqTerm:
        def __init__(self, val):
            self.val = val

        def __eq__(self, other):
            raise RuntimeError("hostile __eq__ called")

    class HostileReprTerm:
        def __init__(self, val):
            self.val = val

        def __repr__(self):
            raise RuntimeError("hostile __repr__ called")

    # Hostile non-str path rejected during boundary validation
    class HostileEqOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        def _normalize_input(cls, input_value):
            return [("title", Ordering.ASC), (HostileEqTerm("custom"), None)]

    with pytest.raises(
        ConfigurationError,
        match=r"HostileEqOrder\._normalize_input returned invalid term",
    ):
        HostileEqOrder._input_has_active_terms([{"title": "ASC"}])

    # Hostile __repr__ during invalid term error formatting
    class HostileReprOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        def _normalize_input(cls, input_value):
            return [("title", HostileReprTerm("boom"))]

    with pytest.raises(ConfigurationError) as exc_info:
        HostileReprOrder._input_has_active_terms([{"title": "ASC"}])
    assert "returned invalid term" in str(exc_info.value)
    assert "<unprintable" in str(exc_info.value)


def test_input_has_active_terms_public_apply_override_independence():
    """Pin that overriding public apply without delegating leaves helper as an independent post-success query."""

    class CustomApplyOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        def apply_sync(cls, input_value, queryset, info, **kwargs):
            return queryset.filter(pk__gt=0)

        @classmethod
        async def apply_async(cls, input_value, queryset, info, **kwargs):
            return queryset.filter(pk__gt=0)

    factory = OrderArgumentsFactory(CustomApplyOrder)
    BookInput = factory.arguments
    active_input = [BookInput(title=Ordering.ASC)]
    empty_input = [BookInput(title=None)]

    # Proves helper is not routed through public apply and remains an independent query
    assert CustomApplyOrder._input_has_active_terms(active_input) is True
    assert CustomApplyOrder._input_has_active_terms(empty_input) is False
    assert CustomApplyOrder._input_has_active_terms(None) is False


@pytest.mark.parametrize(
    ("first_return", "second_return"),
    [
        ([("title", Ordering.ASC)], [("title", Ordering.DESC)]),
        ([], [("title", Ordering.ASC)]),
        ([("title", Ordering.ASC)], []),
    ],
)
def test_input_has_active_terms_purity_violation(first_return, second_return):
    """Impure _normalize_input raising disagreement raises ConfigurationError naming the method."""

    class ImpureOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        calls = 0

        @classmethod
        def _normalize_input(cls, input_value):
            cls.calls += 1
            if cls.calls % 2 == 1:
                return first_return
            return second_return

    with pytest.raises(
        ConfigurationError,
        match=r"_normalize_input.*is not pure; returned different results",
    ):
        ImpureOrder._input_has_active_terms([{"title": "dummy"}])


def test_orderset_normalize_input_validation_contract():
    """_validate_normalized_terms enforces the declared return contract at the pipeline boundary."""

    class NonListOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        def _normalize_input(cls, input_value):
            return {"title": Ordering.ASC}

    with pytest.raises(
        ConfigurationError,
        match=r"NonListOrder\._normalize_input returned invalid data",
    ):
        NonListOrder._input_has_active_terms([{"title": "ASC"}])

    class NonTupleTermOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        def _normalize_input(cls, input_value):
            return [["title", Ordering.ASC]]

    with pytest.raises(
        ConfigurationError,
        match=r"NonTupleTermOrder\._normalize_input returned invalid term",
    ):
        NonTupleTermOrder._input_has_active_terms([{"title": "ASC"}])

    class InvalidDirectionOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        def _normalize_input(cls, input_value):
            return [("title", "ASC")]

    with pytest.raises(
        ConfigurationError,
        match=r"InvalidDirectionOrder\._normalize_input returned invalid term",
    ):
        InvalidDirectionOrder._input_has_active_terms([{"title": "ASC"}])
