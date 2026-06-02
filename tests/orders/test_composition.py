"""Cross-card composition smoke test for filters + orders (spec-028 Slice 6).

Pins the **package-internal** composition contract for a ``DjangoType`` that
declares BOTH ``Meta.filterset_class`` AND ``Meta.orderset_class``. The
Slice 4 live HTTP test ``test_library_books_filter_and_order_compose`` (at
``examples/fakeshop/test_query/test_library_api.py``) already pins the
consumer-visible behavior end-to-end through ``/graphql/``; this file pins
the complementary implementation-contract altitude:

1. Both subsystems' per-module input-class namespaces materialize the
   ``<X>FilterInputType`` AND ``<X>OrderInputType`` classes as module
   globals of their respective ``inputs.py`` modules in one
   ``finalize_django_types()`` pass.
2. Both factories' ``input_object_types`` dicts register the corresponding
   classes -- the materialization-ledger + factory-cache pair stays
   consistent across subsystems.
3. Strawberry's ``LazyType.resolve_type`` path (modeled here as a
   ``module.__dict__`` lookup over both inputs modules) finds both classes
   so the schema's ``filter:`` / ``orderBy:`` arguments resolve.
4. A resolver that consumes BOTH arguments produces a queryset whose
   ``query.where`` is non-empty (the filter pipeline ran) AND
   ``list(query.order_by)`` is non-empty (the order pipeline ran),
   inspected via ``django.test.utils.CaptureQueriesContext`` so the
   ``WHERE <filter>`` and ``ORDER BY <order>`` clauses are visible in the
   captured SQL too.
5. The shared ``django_strawberry_framework/sets_mixins.py::
   LazyRelatedClassMixin`` is the same class object in both
   ``RelatedFilter.__mro__`` and ``RelatedOrder.__mro__`` -- the
   sibling-import sharing does not duplicate the mixin between
   subsystems.

Fixture choice: reuses the fakeshop library ``Book`` model (per
``AGENTS.md`` line 8 carve-out -- "Library acceptance tests use inline
Model.objects.create; the library app has no services.py", so the
seed-helper rule does not apply here) but declares LOCAL ``BookFilter``,
``BookOrder``, and ``BookType`` classes inside each test function body
to avoid colliding with the already-schema-bound ``apps.library.*``
classes carried by the schema-module import.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest
from apps.library.models import Book
from django.db import connection
from django.http import HttpRequest
from django.test.utils import CaptureQueriesContext

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.filters import (
    FilterSet,
    RelatedFilter,
    _helper_referenced_filtersets,
)
from django_strawberry_framework.filters.factories import FilterArgumentsFactory
from django_strawberry_framework.filters.inputs import (
    INPUTS_MODULE_PATH as FILTER_INPUTS_MODULE_PATH,
)
from django_strawberry_framework.filters.inputs import (
    _field_specs as _filter_field_specs,
)
from django_strawberry_framework.filters.inputs import (
    _materialized_names as _filter_materialized_names,
)
from django_strawberry_framework.orders import (
    Ordering,
    OrderSet,
    RelatedOrder,
    _helper_referenced_ordersets,
)
from django_strawberry_framework.orders.factories import OrderArgumentsFactory
from django_strawberry_framework.orders.inputs import (
    INPUTS_MODULE_PATH as ORDER_INPUTS_MODULE_PATH,
)
from django_strawberry_framework.orders.inputs import (
    _field_specs as _order_field_specs,
)
from django_strawberry_framework.orders.inputs import (
    _materialized_names as _order_materialized_names,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.sets_mixins import LazyRelatedClassMixin


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Clear both subsystems' caches around every test.

    Mirrors ``tests/orders/test_finalizer.py::_isolate_registry`` extended
    to also reset the filter-side ledgers + factory caches so the
    composition test starts from a clean state on BOTH subsystems. The
    ``registry.clear()`` call already triggers
    ``clear_order_input_namespace()`` / ``clear_filter_input_namespace()``
    plus both ``_helper_referenced_*.clear()`` via the local-import dance
    (spec-028 Decision 9); the explicit per-ledger clears below pin the
    contract -- a regression in the ``registry.clear()`` lifecycle would
    surface as state bleed across tests, not as a silent test pass.
    """
    registry.clear()
    _filter_field_specs.clear()
    _filter_materialized_names.clear()
    _helper_referenced_filtersets.clear()
    FilterArgumentsFactory.input_object_types.clear()
    FilterArgumentsFactory._type_filterset_registry.clear()
    _order_field_specs.clear()
    _order_materialized_names.clear()
    _helper_referenced_ordersets.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()
    yield
    registry.clear()
    _filter_field_specs.clear()
    _filter_materialized_names.clear()
    _helper_referenced_filtersets.clear()
    FilterArgumentsFactory.input_object_types.clear()
    FilterArgumentsFactory._type_filterset_registry.clear()
    _order_field_specs.clear()
    _order_materialized_names.clear()
    _helper_referenced_ordersets.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()


def _make_info() -> SimpleNamespace:
    """Build a minimal ``info``-shaped stub with a Django ``HttpRequest`` on it.

    Mirrors ``tests/orders/test_sets.py::_make_info``; declared locally
    rather than sibling-imported because the cross-module test-helper
    coupling would entangle two otherwise-independent test files.
    """
    request = HttpRequest()
    request.user = SimpleNamespace(is_anonymous=False)
    return SimpleNamespace(context=SimpleNamespace(request=request))


@pytest.mark.django_db
def test_filter_and_order_compose_through_finalizer_and_apply_pipelines():
    """Filter + order compose cleanly through one ``finalize_django_types()`` pass.

    Pins the four-part contract from the module docstring: both factories
    materialize their input classes, both ``input_object_types`` carry
    them, the ``LazyType.resolve_type`` ``module.__dict__`` lookup finds
    both, and the apply pipeline produces a queryset whose ``query.where``
    carries the filter constraint AND ``query.order_by`` carries the
    order clause. The captured SQL string is inspected via
    ``CaptureQueriesContext`` so the ``WHERE`` and ``ORDER BY`` clauses
    are confirmed in the canonical resolver-chain order: filter narrows
    rows first, order arranges them second.
    """

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            # Single-lookup form so the dict-input apply pipeline accepts
            # a scalar value for ``title`` (the form maps ``title`` to
            # the default ``exact`` lookup); the per-field operator-bag
            # shape requires constructing a Strawberry dataclass instance
            # which adds fixture noise without changing the composition
            # contract this test pins.
            fields = {"title": ["exact"]}

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = BookFilter
            orderset_class = BookOrder

    finalize_django_types()

    # Assertion 1: both per-module inputs modules carry the materialized
    # classes (the ``LazyType.resolve_type`` path uses ``module.__dict__``
    # at schema-build time -- this assertion models that lookup).
    filter_inputs_mod = sys.modules[FILTER_INPUTS_MODULE_PATH]
    order_inputs_mod = sys.modules[ORDER_INPUTS_MODULE_PATH]
    assert hasattr(filter_inputs_mod, "BookFilterInputType")
    assert hasattr(order_inputs_mod, "BookOrderInputType")

    # Assertion 2: both ``_materialized_names`` ledgers register the names
    # (spec-028 Decision 9 / spec-027 Decision 9 -- the ledger is the
    # idempotence guard for ``materialize_input_class``).
    assert "BookFilterInputType" in _filter_materialized_names
    assert "BookOrderInputType" in _order_materialized_names

    # Assertion 3: both factories' class-level ``input_object_types``
    # dicts carry the materialized classes (Slice 2's factory-cache
    # contract on both subsystems).
    assert "BookFilterInputType" in FilterArgumentsFactory.input_object_types
    assert "BookOrderInputType" in OrderArgumentsFactory.input_object_types

    # Assertion 4: the apply pipeline composes -- filter narrows rows,
    # order arranges the survivors. Inspect ``query.where`` /
    # ``query.order_by`` on the unexecuted queryset for stable Django-
    # internal contracts, then execute it under
    # ``CaptureQueriesContext`` so the captured SQL string carries
    # ``WHERE`` AND ``ORDER BY`` clauses too.
    order_input_cls = OrderArgumentsFactory.input_object_types["BookOrderInputType"]
    # Dict-shape input is supported by ``FilterSet._normalize_input`` -- a
    # scalar value for a single-lookup field maps to the form's default
    # ``exact`` lookup. The order side receives a list of Strawberry
    # input dataclass instances per Spec Decision 5 list-of-non-null.
    filter_input = {"title": "Foundation"}
    order_input = [order_input_cls(title=Ordering.ASC)]
    info = _make_info()
    queryset = Book.objects.all()
    queryset = BookFilter.apply_sync(filter_input, queryset, info)
    queryset = BookOrder.apply_sync(order_input, queryset, info)

    # Django-internal attributes (no DB hit needed for these checks).
    assert bool(queryset.query.where), "filter pipeline did not populate WhereNode"
    order_by = list(queryset.query.order_by)
    assert order_by, "order pipeline did not populate order_by"
    assert any("title" in repr(item) for item in order_by), (
        f"ORDER BY does not reference the title column: {order_by!r}"
    )

    # SQL-string confirmation via ``CaptureQueriesContext`` -- execute
    # the queryset so the captured SQL carries BOTH clauses in the
    # canonical order (WHERE before ORDER BY).
    with CaptureQueriesContext(connection) as ctx:
        list(queryset)
    assert len(ctx.captured_queries) == 1
    sql = ctx.captured_queries[0]["sql"].upper()
    where_idx = sql.find("WHERE")
    order_idx = sql.find("ORDER BY")
    assert where_idx != -1, f"SQL missing WHERE clause: {sql!r}"
    assert order_idx != -1, f"SQL missing ORDER BY clause: {sql!r}"
    assert where_idx < order_idx, f"WHERE must precede ORDER BY in the SQL string: {sql!r}"


def test_filter_and_order_share_lazy_related_class_mixin_via_neutral_module():
    """Both subsystems' ``Related*`` primitives inherit the shared mixin.

    Spec-028 Revision 4 H1 pinned the mixin's neutral home at
    ``django_strawberry_framework/sets_mixins.py``. ``RelatedFilter``
    (declared at ``django_strawberry_framework.filters.base.RelatedFilter``)
    AND ``RelatedOrder`` (declared at
    ``django_strawberry_framework.orders.base.RelatedOrder``) BOTH inherit
    ``LazyRelatedClassMixin`` directly via sibling-imports from the
    neutral module -- the mixin object is shared, not duplicated. A
    future refactor that re-declares a sibling copy under either
    subsystem fails this MRO-identity pin loudly.
    """
    # Both ``Related*`` primitives inherit the shared mixin.
    assert LazyRelatedClassMixin in RelatedFilter.__mro__
    assert LazyRelatedClassMixin in RelatedOrder.__mro__
    # And it IS the same class object -- not a sibling-copy under each
    # subsystem.
    filter_mixin = next(
        cls for cls in RelatedFilter.__mro__ if cls.__name__ == "LazyRelatedClassMixin"
    )
    order_mixin = next(
        cls for cls in RelatedOrder.__mro__ if cls.__name__ == "LazyRelatedClassMixin"
    )
    assert filter_mixin is order_mixin is LazyRelatedClassMixin
