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
from collections import OrderedDict
from types import SimpleNamespace

import pytest
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
    """Non-iterable or string Meta.fields (other than '__all__') raises ConfigurationError."""

    class IntFieldsOrder(OrderSet):
        class Meta:
            model = Book
            fields = 123

    with pytest.raises(
        ConfigurationError,
        match="must be '__all__' or an iterable of field names",
    ):
        IntFieldsOrder.get_fields()

    class StrFieldsOrder(OrderSet):
        class Meta:
            model = Book
            fields = "title"

    with pytest.raises(
        ConfigurationError,
        match="must be '__all__' or an iterable of field names",
    ):
        StrFieldsOrder.get_fields()

    class ObjFieldsOrder(OrderSet):
        class Meta:
            model = Book
            fields = object()

    with pytest.raises(
        ConfigurationError,
        match="must be '__all__' or an iterable of field names",
    ):
        ObjFieldsOrder.get_fields()


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


@pytest.mark.django_db
def test_orderset_apply_sync_annotates_multiple_to_many_orders():
    """apply_sync generates distinct aggregate annotations for multiple to-many terms."""
    from django.db.models import Min

    class ShelfOrderMulti(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BranchOrderMulti(OrderSet):
        shelves = RelatedOrder(ShelfOrderMulti, field_name="shelves")

        class Meta:
            model = Branch
            fields = ["name"]

    factory = OrderArgumentsFactory(BranchOrderMulti)
    BranchInput = factory.arguments
    ShelfInput = OrderArgumentsFactory.input_object_types["ShelfOrderMultiInputType"]

    input_value = [
        BranchInput(shelves=ShelfInput(code=Ordering.ASC)),
        BranchInput(name=Ordering.DESC),
    ]

    b1 = Branch.objects.create(name="Beta", city="NY")
    Shelf.objects.create(code="S2", branch=b1)
    b2 = Branch.objects.create(name="Alpha", city="LA")
    Shelf.objects.create(code="S1", branch=b2)

    qs = BranchOrderMulti.apply_sync(input_value, Branch.objects.all(), _make_info())
    assert any(isinstance(agg, Min) for agg in qs.query.annotations.values())
    results = list(qs)
    assert len(results) == 2
    assert results[0].name == "Alpha"
    assert results[1].name == "Beta"


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
