"""DjangoOptimizerExtension tests for root-gated planning and queryset optimization.

Covers, by topic code:

- **O3** - end-to-end relation traversal (forward FK ``select_related``,
  reverse FK ``prefetch_related``, combined), root-field gate,
  ``GraphQLNonNull`` / ``GraphQLList`` type tracing, passthrough cases,
  ``on_execute`` ContextVar lifecycle, async resolver parity.
- **O4** - nested prefetch chains and nested select-related chains.
- **O5** - ``only()`` projection collection.
- **O6** - ``plan_relation`` downgrade from ``select_related`` to
  ``Prefetch`` for target types with custom ``get_queryset`` hooks.
- **B1** - plan cache: hits, misses, eviction, named-fragment
  differentiation, directive-variable cache splitting, runtime-path
  inclusion.
- **B2** - forward FK-id elision (and the guards that disable it).
- **B3** - strictness API (``off`` / ``warn`` / ``raise``).
- **B4** - ``Meta.optimizer_hints`` (SKIP, force_select, force_prefetch,
  explicit ``Prefetch``).
- **B5** - plan introspection via ``info.context`` and the read/write
  symmetry of the ``_context`` helpers (dict, dict-subclass, non-dict
  mapping, frozen mapping, immutable ``dict`` subclass, ``None``).
- **B6** - schema-build-time optimization audit (``check_schema``,
  ``_collect_schema_reachable_types`` including union-type descent).
- **B8** - consumer-queryset-aware plan diffing.
- Extension construction surface (unknown-kwarg rejection, Strawberry
  ``execution_context`` keyword).
- ``hint_is_skip`` dispatch shapes.

Every test uses the autouse ``_isolate_registry`` fixture so the
global ``registry`` is cleared on entry and exit.
"""

import contextlib
import warnings
from collections import OrderedDict
from types import SimpleNamespace

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Entry, Item, Property
from strawberry import relay

from django_strawberry_framework import (
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.optimizer import logger as optimizer_logger
from django_strawberry_framework.optimizer.extension import (
    _named_children,
    _node_children_with_runtime_prefix,
    _optimizer_active,
    _resolve_model_from_return_type,
)
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


def _force_unregister_after_finalize(type_cls):
    """Test-only helper: drop ``type_cls`` from a *finalized* registry.

    The schema-audit tests in this module build a Strawberry schema, then
    want to simulate a missing registration so ``check_schema`` reports a
    gap. The public ``registry.unregister`` honours ``_check_mutable``
    and raises post-finalize because removing entries from a
    runtime-active registry would silently disable optimizer planning
    and produce false missing-target warnings; this helper exists only
    so the test fixtures can poke that exact state without smuggling
    the surgery into production code.
    """
    model = registry._models.pop(type_cls, None)
    if model is None:
        return
    types = registry._types.get(model, [])
    if type_cls in types:
        types.remove(type_cls)
    if not types:
        registry._types.pop(model, None)
    if registry._primaries.get(model) is type_cls:
        registry._primaries.pop(model, None)
    registry._definitions.pop(type_cls, None)


# ---------------------------------------------------------------------------
# End-to-end query-count tests (O3 unskips the first two)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimize_coerces_manager_through_all_records_cache_miss():
    """The optimizer's plan cache records a miss when coercing ``Manager`` -> ``.all()``.

    The behavioral half (1 SQL query, JOIN applied, data round-trips) is
    pinned end-to-end by
    ``examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_coerces_manager_to_queryset_in_http_query``.
    This test keeps the package-internal cache-state assertion that proves
    the plan was actually BUILT (cache miss recorded) rather than the
    Manager being short-circuited by the ``isinstance(QuerySet)`` gate -
    a guarantee unreachable from the live HTTP path because the project
    schema doesn't expose its extension instance for inspection.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            # Return the Manager itself, not ``Manager.all()``.
            return Item.objects  # type: ignore[return-value]

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    result = schema.execute_sync("{ allItems { name category { name } } }")
    assert result.errors is None
    # The plan was built (miss recorded), proving the Manager was NOT
    # short-circuited by the QuerySet-only gate.
    assert ext.cache_info().misses == 1


@pytest.mark.django_db(transaction=True)
def test_optimizer_prefetches_reverse_fk_without_related_name(django_assert_num_queries):
    """The optimizer plans a no-``related_name`` reverse FK via its ACCESSOR.

    Round-4 S3 follow-up: ``_plan_prefetch_relation`` used to emit the
    relation's QUERY name (``"plainissue"``) as the prefetch lookup, which
    Django's ``prefetch_related`` rejects for reverse relations without
    ``related_name`` - the whole optimized query died with
    ``AttributeError: ... 'plainissue' is an invalid parameter to
    prefetch_related()``. The lookup now uses ``get_accessor_name()``
    (``"plainissue_set"``), batching the relation into one prefetch query;
    ``strictness="raise"`` doubles as the no-false-N+1 assertion. Invisible
    to the rest of CI because every fakeshop fixture sets ``related_name``.

    Uses the ``managed=False`` + manual ``schema_editor`` pattern from
    ``test_relay_id_projection.py``; the app label must be an INSTALLED app
    because Django only wires reverse relations into ``_meta.get_fields()``
    for installed apps.
    """
    from django.db import connection as db_connection
    from django.db import models as djmodels

    class PlainPublisher(djmodels.Model):
        name = djmodels.CharField(max_length=32)

        class Meta:
            app_label = "products"
            managed = False

    class PlainIssue(djmodels.Model):
        title = djmodels.CharField(max_length=32)
        author = djmodels.ForeignKey(PlainPublisher, on_delete=djmodels.CASCADE)  # no related_name

        class Meta:
            app_label = "products"
            managed = False

    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(PlainPublisher)
        schema_editor.create_model(PlainIssue)
    try:

        class PlainIssueType(DjangoType):
            class Meta:
                model = PlainIssue
                fields = ("id", "title")

        class PlainPublisherType(DjangoType):
            class Meta:
                model = PlainPublisher
                fields = ("id", "name", "plainissue")

        @strawberry.type
        class Query:
            @strawberry.field
            def authors(self) -> list[PlainPublisherType]:
                return PlainPublisher.objects.all()  # type: ignore[return-value]

        finalize_django_types()
        for index in range(3):
            author = PlainPublisher.objects.create(name=f"a{index}")
            PlainIssue.objects.create(title=f"b{index}", author=author)

        ext = DjangoOptimizerExtension(strictness="raise")
        schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
        with django_assert_num_queries(2):  # parents + ONE batched prefetch
            result = schema.execute_sync("{ authors { name plainissue { title } } }")
        assert result.errors is None
        assert result.data == {
            "authors": [
                {"name": f"a{index}", "plainissue": [{"title": f"b{index}"}]} for index in range(3)
            ],
        }
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(PlainIssue)
            schema_editor.delete_model(PlainPublisher)


@pytest.mark.django_db
def test_optimizer_plans_merged_duplicate_root_field_nodes_plan_shape():
    """Merged duplicate root fields contribute all child selections to one plan.

    The behavioral half is pinned end-to-end by
    ``examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_merges_duplicate_root_field_nodes_over_http``.
    This package test keeps the plan-state assertion that the merged
    selection contributes ``category`` to the stashed optimizer plan.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension(strictness="raise")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    result = schema.execute_sync(
        "{ allItems { name } allItems { category { name } } }",
        context_value=ctx,
    )

    assert result.errors is None
    assert ctx.dst_optimizer_plan.select_related == ("category",)
    assert "ItemType.category@allItems.category" in ctx.dst_optimizer_planned


@pytest.mark.django_db
def test_optimizer_elides_forward_fk_id_only_selection_plan_shape():
    """B2 plan-state inspection: ``category { id }`` produces an elision plan.

    The behavioral half (1 SQL query, no JOIN, id round-trips) is pinned by
    ``examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_fk_id_elision_for_self_fk_in_http_query``.
    This test keeps the package-internal plan-state assertions that are
    unreachable from a live ``/graphql/`` request: ``plan.select_related``
    must be empty, ``plan.only_fields`` must include the source FK column,
    ``plan.fk_id_elisions`` must record the resolver key, and
    ``ctx.dst_optimizer_fk_id_elisions`` must mirror it (the set the
    forward-FK resolver consults at resolve time).
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    result = schema.execute_sync(
        "{ allItems { name category { id } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ()
    assert plan.prefetch_related == ()
    assert plan.only_fields == ("name", "category_id")
    assert plan.fk_id_elisions == ("ItemType.category@allItems.category",)
    assert ctx.dst_optimizer_fk_id_elisions == {"ItemType.category@allItems.category"}


@pytest.mark.django_db
def test_optimizer_elides_forward_fk_id_only_selection_for_each_alias_plan_shape():
    """B2/O4 plan-state inspection: duplicate aliases each register their own elision key.

    The behavioral half (1 SQL query, no JOIN, both aliases return the same
    FK id) is pinned by
    ``examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_fk_id_elision_for_each_alias_in_http_query``.
    This test keeps the package-internal plan-state assertions: the plan
    records BOTH alias resolver keys, ``only_fields`` projects exactly the
    source FK column (deduped), and the context-side elision set carries
    both keys for the per-alias forward-FK resolver to consult.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    result = schema.execute_sync(
        "{ allItems { first: category { id } second: category { id } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ()
    assert plan.prefetch_related == ()
    assert plan.only_fields == ("category_id",)
    assert plan.fk_id_elisions == (
        "ItemType.category@allItems.first",
        "ItemType.category@allItems.second",
    )
    assert ctx.dst_optimizer_fk_id_elisions == {
        "ItemType.category@allItems.first",
        "ItemType.category@allItems.second",
    }


@pytest.mark.django_db
def test_optimizer_does_not_elide_forward_fk_when_extra_scalar_selected_plan_shape():
    """B2 plan-state inspection: extra target scalar forces ``select_related`` over elision.

    The behavioral half (1 SQL query via JOIN, extra scalar populates from
    the joined row) is pinned by
    ``examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_no_fk_id_elision_when_extra_scalar_selected_in_http_query``.
    This test keeps the package-internal plan-state assertions: the
    optimizer plans ``select_related("category",)``, records NO elisions,
    and projects the full ``category__*`` chain in ``only_fields``.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    result = schema.execute_sync(
        "{ allItems { name category { id name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ("category",)
    assert plan.fk_id_elisions == ()
    assert plan.only_fields == (
        "name",
        "category_id",
        "category__id",
        "category__name",
    )


@pytest.mark.django_db
def test_optimizer_does_not_elide_forward_fk_when_target_has_custom_get_queryset_plan_shape():
    """B2/O6 plan-state inspection: custom ``get_queryset`` forces ``Prefetch`` even on id-only.

    The behavioral half (2 SQL queries, no JOIN on the root, prefetched
    SELECT with the consumer filter applied, inactive rows resolve to
    ``null`` on the source) is pinned by these HTTP tests in
    ``examples/fakeshop/test_query/test_scalars_api.py``:
    ``test_scalars_optimizer_o6_downgrade_to_prefetch_for_custom_get_queryset_in_http_query``
    and ``test_scalars_custom_get_queryset_filters_inactive_tag_to_null_in_http_query``.
    This test keeps the package-internal plan-state assertions: even though
    only ``id`` is selected on the FK target, the optimizer must NOT elide
    (``fk_id_elisions == ()``) and must NOT use ``select_related`` -
    instead it records exactly one ``Prefetch`` entry.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    result = schema.execute_sync(
        "{ allItems { name category { id } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ()
    assert plan.fk_id_elisions == ()
    assert plan.only_fields == ("name", "category_id")
    assert len(plan.prefetch_related) == 1


@pytest.mark.django_db
def test_optimizer_skips_when_no_relations_selected(django_assert_num_queries):
    """If the selection contains only scalars, only projection is applied."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])

    # 1 query, no select_related / prefetch_related applied.
    with django_assert_num_queries(1):
        result = schema.execute_sync("{ allCategories { name } }")
        assert result.errors is None


@pytest.mark.django_db
def test_optimizer_passes_through_non_queryset(django_assert_num_queries):
    """A resolver returning a plain ``list`` (not a ``QuerySet``) skips the optimizer."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def categories_as_list(self) -> list[CategoryType]:
            # Materializing the queryset turns it into a Python list, so the
            # optimizer's ``isinstance(result, QuerySet)`` check returns False.
            return list(Category.objects.all())

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])

    # The materialization issues 1 query; nothing else fires because
    # the optimizer hands the list straight back to Strawberry.
    with django_assert_num_queries(1):
        result = schema.execute_sync("{ categoriesAsList { name } }")
        assert result.errors is None


@pytest.mark.django_db
def test_optimizer_passes_through_unregistered_return_type(caplog):
    """If the return type isn't in the registry, the queryset is unchanged."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])

    # Drop the registry mid-test - schema is already built, but the optimizer
    # looks up the registry per resolver call, so the lookup misses.
    registry.clear()

    caplog.set_level("DEBUG", logger=optimizer_logger.name)
    result = schema.execute_sync("{ allCategories { name } }")
    assert result.errors is None
    # The optimizer logs a debug line when it falls through.
    assert any("no registered DjangoType" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# G1 (spec-035 Slice 1): evaluated-queryset guard
#
# A consumer root resolver that already EVALUATED its queryset (``len(qs)``,
# ``bool(qs)``, a slice) must pass through ``_optimize`` unchanged - the
# optimizer's ``.only()`` / ``select_related`` clone would otherwise silently
# re-execute the SQL (a doubled query) and discard the consumer's own prefetch
# work. No fakeshop resolver evaluates its root queryset before returning it,
# so G1 is not reachable from a live products query (Decision 8 unreachability
# reason) and is earned here at the package level.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimizer_passes_through_consumer_evaluated_queryset(django_assert_num_queries):
    """An evaluated root queryset is returned unchanged - no re-executing clone.

    The resolver applies its OWN ``select_related`` and evaluates the queryset
    (``len(qs)`` -> ``_result_cache`` populated), then returns it. With the G1
    guard the optimizer leaves it alone: the whole operation issues exactly ONE
    SQL query (the consumer's evaluation) and the ``category`` relation is
    served from the consumer's join. Without the guard the optimizer would
    clone the evaluated queryset with its own plan and re-execute - two queries
    total, and the consumer's prefetch work thrown away.
    """
    services.seed_data(2)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            qs = Item.objects.select_related("category").all()
            len(qs)  # consumer evaluates -> _result_cache populated
            return qs

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    with django_assert_num_queries(1):  # consumer's evaluation only; optimizer adds none
        result = schema.execute_sync("{ allItems { name category { name } } }")
    assert result.errors is None
    # The guard short-circuited BEFORE _get_or_build_plan, so no plan was built.
    assert ext.cache_info().misses == 0


@pytest.mark.django_db
def test_optimize_returns_same_instance_for_evaluated_queryset():
    """``_optimize`` returns the SAME evaluated queryset object, never a clone.

    Direct-call companion to the end-to-end test: it pins instance identity
    (the contract the doubled-query count implies but cannot observe through
    schema execution). ``_optimize`` never touches ``info`` for an evaluated
    queryset - the guard returns before return-type resolution - so a bare
    namespace suffices.
    """
    services.seed_data(1)
    ext = DjangoOptimizerExtension()

    qs = Category.objects.all()
    len(qs)  # evaluate -> _result_cache is a (non-None) list

    assert ext._optimize(qs, SimpleNamespace()) is qs
    assert ext.cache_info().misses == 0


@pytest.mark.django_db
def test_optimizer_still_optimizes_manager_after_evaluated_queryset_guard(
    django_assert_num_queries,
):
    """The guard sits AFTER the Manager coercion, so ``Model.objects`` still optimizes.

    ``normalize_query_source`` coerces a returned ``Manager`` to a fresh
    ``.all()`` whose ``_result_cache`` is ``None``; the guard must not pre-empt
    that path. A ``Model.objects``-returning resolver therefore still builds and
    applies a plan (cache miss recorded) and the ``category`` relation is joined
    in a single query - the un-evaluated counterpart to the test above.
    """
    services.seed_data(2)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects  # type: ignore[return-value]  # Manager, unevaluated post-coercion

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    with django_assert_num_queries(1):  # optimizer applied select_related -> single joined query
        result = schema.execute_sync("{ allItems { name category { name } } }")
    assert result.errors is None
    # The plan WAS built (guard did not fire on the un-evaluated coerced queryset).
    assert ext.cache_info().misses == 1


@pytest.mark.django_db
def test_resolve_async_passes_through_evaluated_queryset(monkeypatch):
    """Async mirror: the await -> ``_optimize`` wrapper inherits the G1 guard.

    The async path (``_async_optimize`` awaits the resolver then calls
    ``_optimize``) routes an evaluated queryset through the same guard. The
    tripwire on ``_resolve_model_from_return_type`` proves ``_optimize``
    short-circuits BEFORE return-type resolution / plan build - if the guard
    failed to fire, the tripwire would raise.
    """
    import asyncio

    from django_strawberry_framework.optimizer import extension as extension_module

    services.seed_data(1)
    ext = DjangoOptimizerExtension()

    qs = Category.objects.all()
    len(qs)  # evaluate synchronously, before the await -> no DB access in the coroutine

    def _tripwire(info):
        raise AssertionError("guard must short-circuit before return-type resolution")

    monkeypatch.setattr(extension_module, "_resolve_model_from_return_type", _tripwire)

    async def fake_next(root, info, *args, **kwargs):
        return qs

    info = SimpleNamespace(
        path=SimpleNamespace(prev=None, key="allCategories", typename="Query"),
        return_type=SimpleNamespace(),
        schema=None,
        field_name="allCategories",
        field_nodes=[],
    )
    result = ext.resolve(fake_next, None, info)
    assert asyncio.iscoroutine(result)
    resolved = asyncio.run(result)
    assert resolved is qs  # same instance, no clone
    assert ext.cache_info().misses == 0  # guard fired before plan build


# ---------------------------------------------------------------------------
# O3: type-tracing through graphql-core wrappers
# ---------------------------------------------------------------------------


def test_resolve_model_from_return_type_unwraps_nested_wrappers():
    """Recursive unwrap through NonNull(List(NonNull(ObjectType))) -> (origin, Django model)."""
    from graphql import GraphQLList, GraphQLNonNull

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    # Build a minimal schema so get_type_by_name works.
    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    # Simulate the graphql-core wrapper stack the resolve hook sees.
    inner = schema._schema.type_map["CategoryType"]
    wrapped = GraphQLNonNull(GraphQLList(GraphQLNonNull(inner)))

    info = SimpleNamespace(
        return_type=wrapped,
        schema=schema._schema,
    )
    result = _resolve_model_from_return_type(info)
    assert result is not None
    assert result.model is Category
    assert result.origin is CategoryType


def test_resolve_model_returns_none_for_non_object_leaf():
    """When the leaf type has no name (e.g. a scalar), returns None."""
    info = SimpleNamespace(
        return_type=SimpleNamespace(),  # no of_type, no name
        schema=None,
    )
    assert _resolve_model_from_return_type(info) is None


def test_resolve_model_returns_none_when_no_strawberry_schema():
    """When schema._strawberry_schema is missing, returns None."""
    info = SimpleNamespace(
        return_type=SimpleNamespace(name="SomeType"),
        schema=SimpleNamespace(),  # no _strawberry_schema
    )
    assert _resolve_model_from_return_type(info) is None


def test_resolve_model_returns_none_when_type_not_in_schema():
    """When get_type_by_name returns None (type not in schema), returns None."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    info = SimpleNamespace(
        return_type=SimpleNamespace(name="NonExistentType"),
        schema=schema._schema,
    )
    assert _resolve_model_from_return_type(info) is None


def test_resolve_model_returns_none_when_definition_has_no_origin():
    """When the schema's type definition lacks an ``origin`` (e.g. a scalar / interface), returns None."""
    fake_strawberry_schema = SimpleNamespace(
        get_type_by_name=lambda _name: SimpleNamespace(),  # definition without `origin`
    )
    info = SimpleNamespace(
        return_type=SimpleNamespace(name="SomeType"),
        schema=SimpleNamespace(_strawberry_schema=fake_strawberry_schema),
    )
    assert _resolve_model_from_return_type(info) is None


# ---------------------------------------------------------------------------
# O3: root-field gate
# ---------------------------------------------------------------------------


def test_resolve_passes_through_non_root_resolvers():
    """Non-root resolvers (info.path.prev is not None) bypass _optimize entirely."""
    ext = DjangoOptimizerExtension()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    # Simulate a non-root resolver: path.prev is not None.
    qs = Category.objects.all()
    called_with = {}

    def fake_next(root, info, *args, **kwargs):
        called_with["fired"] = True
        return qs

    info = SimpleNamespace(
        path=SimpleNamespace(prev=SimpleNamespace(key="parent", prev=None, typename="Query")),
    )
    result = ext.resolve(fake_next, None, info)
    # _next was called and result passed through unchanged (no _optimize).
    assert called_with["fired"] is True
    assert result is qs


# ---------------------------------------------------------------------------
# O3: async resolver parity
# ---------------------------------------------------------------------------


def test_resolve_handles_async_root_resolver():
    """An async root resolver's coroutine is awaited before optimization."""
    import asyncio

    ext = DjangoOptimizerExtension()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    qs = Category.objects.all()

    async def fake_next(root, info, *args, **kwargs):
        return qs

    # Root resolver: path.prev is None.
    info = SimpleNamespace(
        path=SimpleNamespace(prev=None, key="allCategories", typename="Query"),
        return_type=SimpleNamespace(),  # no name -> _resolve_model returns None
        schema=None,
        field_name="allCategories",
        field_nodes=[],
    )
    result = ext.resolve(fake_next, None, info)
    # result should be a coroutine (async wrapper)
    assert asyncio.iscoroutine(result)
    # Await it - _optimize will pass through because return_type has no name.
    resolved = asyncio.run(result)
    assert resolved is qs


# ---------------------------------------------------------------------------
# O3: defensive branches in _optimize
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimize_handles_empty_field_nodes(django_assert_num_queries):
    """If field_nodes is empty, _optimize returns the queryset unchanged."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])

    # Drive _optimize directly with a synthetic info that has empty field_nodes.
    ext = DjangoOptimizerExtension()

    info = SimpleNamespace(
        return_type=schema._schema.type_map["CategoryType"],
        schema=schema._schema,
        field_name="allCategories",
        field_nodes=[],
    )
    qs = Category.objects.all()
    result = ext._optimize(qs, info)
    # Should return the queryset unchanged (no field_nodes to plan from).
    assert result.query.select_related is False


@pytest.mark.django_db
def test_optimize_returns_original_queryset_for_empty_plan(monkeypatch):
    """If the walker produces an empty plan, _optimize returns the original queryset."""
    import django_strawberry_framework.optimizer.extension as extension_module
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    monkeypatch.setattr(
        extension_module,
        "plan_optimizations",
        lambda selected_fields, model, info=None, *, source_type=None: OptimizationPlan(),
    )
    ctx = SimpleNamespace()
    result = schema.execute_sync("{ allCategories { name } }", context_value=ctx)
    assert result.errors is None
    assert ctx.dst_optimizer_plan.is_empty


# ---------------------------------------------------------------------------
# O3: on_execute ContextVar lifecycle
# ---------------------------------------------------------------------------


def test_on_execute_sets_and_resets_context_var():
    """on_execute sets _optimizer_active to True, then resets on exit."""
    ext = DjangoOptimizerExtension()
    assert _optimizer_active.get() is False
    gen = ext.on_execute()
    next(gen)  # enter
    assert _optimizer_active.get() is True
    with contextlib.suppress(StopIteration):
        next(gen)
    assert _optimizer_active.get() is False


# ---------------------------------------------------------------------------
# B1: plan cache
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cache_hit_on_repeated_query(django_assert_num_queries):
    """B1: executing the same query twice produces a cache hit on the second call."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    query = "{ allItems { name category { name } } }"

    schema.execute_sync(query)
    assert ext.cache_info().misses == 1
    assert ext.cache_info().hits == 0

    schema.execute_sync(query)
    assert ext.cache_info().hits == 1
    assert ext.cache_info().misses == 1
    assert ext.cache_info().size == 1


@pytest.mark.django_db
def test_cache_differentiates_queries(django_assert_num_queries):
    """B1: different queries produce different cache entries."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])

    schema.execute_sync("{ allItems { name } }")
    schema.execute_sync("{ allItems { name category { name } } }")
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2


@pytest.mark.django_db
def test_cache_differentiates_reachable_named_fragment_bodies():
    """B1: matching operation text with different fragment bodies gets distinct plans."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    query_prefix = "query Q { allItems { ...ItemBits } }"
    ctx_scalar = SimpleNamespace()
    ctx_relation = SimpleNamespace()

    result_scalar = schema.execute_sync(
        f"{query_prefix} fragment ItemBits on ItemType {{ name }}",
        context_value=ctx_scalar,
    )
    result_relation = schema.execute_sync(
        f"{query_prefix} fragment ItemBits on ItemType {{ category {{ name }} }}",
        context_value=ctx_relation,
    )

    assert result_scalar.errors is None
    assert result_relation.errors is None
    assert ctx_scalar.dst_optimizer_plan.select_related == ()
    assert ctx_relation.dst_optimizer_plan.select_related == ("category",)
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2


@pytest.mark.django_db
def test_cache_differentiates_same_model_root_fields(django_assert_num_queries):
    """B1/O4: root fields returning the same model do not share one cached plan."""
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

        @strawberry.field
        def featured_categories(self) -> list[CategoryType]:
            return Category.objects.filter(is_private=False)

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    query = "{ allCategories { name items { name } } featuredCategories { name } }"

    with django_assert_num_queries(3):
        result = schema.execute_sync(query, context_value=ctx)

    assert result.errors is None
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2
    assert ctx.dst_optimizer_plan.prefetch_related == ()


def test_cache_key_includes_root_runtime_path_for_same_model_fields():
    """B1/O4: cache keys differ for root fields returning the same model."""
    from graphql import parse

    operation = parse("{ allCategories { name } featured { name } }").definitions[0]
    info_a = SimpleNamespace(
        operation=operation,
        fragments={},
        variable_values={},
        path=SimpleNamespace(key="allCategories", prev=None),
    )
    info_b = SimpleNamespace(
        operation=operation,
        fragments={},
        variable_values={},
        path=SimpleNamespace(key="featured", prev=None),
    )

    assert DjangoOptimizerExtension._build_cache_key(
        info_a,
        Category,
    ) != DjangoOptimizerExtension._build_cache_key(info_b, Category)


def test_cache_key_differs_for_named_operations_in_same_document():
    """B1: two named operations in one document must not share a plan cache entry."""
    from graphql import parse

    doc = parse("query A { allItems { name } } query B { allItems { category { name } } }")
    operation_a = next(d for d in doc.definitions if getattr(d.name, "value", None) == "A")
    operation_b = next(d for d in doc.definitions if getattr(d.name, "value", None) == "B")
    info_a = SimpleNamespace(
        operation=operation_a,
        fragments={},
        variable_values={},
        path=SimpleNamespace(key="allItems", prev=None),
    )
    info_b = SimpleNamespace(
        operation=operation_b,
        fragments={},
        variable_values={},
        path=SimpleNamespace(key="allItems", prev=None),
    )

    assert DjangoOptimizerExtension._build_cache_key(
        info_a,
        Item,
    ) != DjangoOptimizerExtension._build_cache_key(info_b, Item)


def test_cache_eviction_removes_old_entries(monkeypatch):
    """B1: the plan cache evicts least-recently-used entries when full."""
    from graphql import parse

    import django_strawberry_framework.optimizer.extension as extension_module

    ext = DjangoOptimizerExtension()
    monkeypatch.setattr(extension_module, "_MAX_PLAN_CACHE_SIZE", 4)

    def _cache_info_for(root_field: str) -> SimpleNamespace:
        operation = parse(f"query {root_field} {{ {root_field} {{ name }} }}").definitions[0]
        return SimpleNamespace(
            operation=operation,
            fragments={},
            variable_values={},
            path=SimpleNamespace(key=root_field, prev=None),
        )

    infos = [_cache_info_for(f"root{idx}") for idx in range(4)]
    keys = [DjangoOptimizerExtension._build_cache_key(info, Category, None) for info in infos]
    plans = [object() for _ in range(4)]
    ext._plan_cache = OrderedDict(zip(keys, plans, strict=True))

    assert ext._get_or_build_plan([], Category, infos[0], None) is plans[0]

    root4_info = _cache_info_for("root4")
    root4_key = DjangoOptimizerExtension._build_cache_key(root4_info, Category, None)
    ext._get_or_build_plan([], Category, root4_info, None)

    assert keys[0] in ext._plan_cache
    assert keys[1] not in ext._plan_cache
    assert root4_key in ext._plan_cache
    assert ext.cache_info().misses == 1
    assert ext.cache_info().hits == 1
    assert ext.cache_info().size == 4


@pytest.mark.django_db
def test_filter_vars_do_not_affect_cache():
    """B1: variables not used in @skip/@include don't split cache entries."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self, limit: int = 10) -> list[ItemType]:
            return Item.objects.all()[:limit]

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    query = "query Q($limit: Int!) { allItems(limit: $limit) { name category { name } } }"

    schema.execute_sync(query, variable_values={"limit": 5})
    schema.execute_sync(query, variable_values={"limit": 10})
    # Same query shape, different filter var - should be 1 miss + 1 hit.
    assert ext.cache_info().hits == 1
    assert ext.cache_info().size == 1


@pytest.mark.django_db
def test_cache_separates_operation_names_in_same_document():
    """B1: executing two named operations in one document yields two cache entries."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    document = "query A { allItems { name } } query B { allItems { name category { name } } }"

    result_a = schema.execute_sync(document, operation_name="A")
    result_b = schema.execute_sync(document, operation_name="B")

    assert result_a.errors is None
    assert result_b.errors is None
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2


def test_build_cache_key_is_stable_when_source_location_missing():
    """B1: cache key still works when the operation has no source body."""
    from graphql import parse

    operation = parse("{ allCategories { name } }", no_location=True).definitions[0]
    info = SimpleNamespace(
        operation=operation,
        fragments={},
        variable_values={},
        path=None,
    )

    key = DjangoOptimizerExtension._build_cache_key(info, Category)

    assert key[2] is Category
    assert isinstance(key[3], tuple)


def test_collect_directive_var_names_with_skip():
    """B1: _collect_directive_var_names finds vars in @skip directives."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse("query Q($show: Boolean!) { items @skip(if: $show) { name } }")
    names = _collect_directive_var_names(doc.definitions[0])
    assert names == frozenset({"show"})


def test_collect_directive_var_names_with_include():
    """B1: _collect_directive_var_names finds vars in @include directives."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse("query Q($v: Boolean!) { items @include(if: $v) { name } }")
    names = _collect_directive_var_names(doc.definitions[0])
    assert names == frozenset({"v"})


def test_collect_directive_var_names_ignores_non_directive_vars():
    """B1: variables in field arguments (not directives) are not collected."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse("query Q($limit: Int!) { items(limit: $limit) { name } }")
    names = _collect_directive_var_names(doc.definitions[0])
    assert names == frozenset()


def test_walk_cache_relevant_vars_ignores_non_directive_objects():
    """B1: directive collection skips defensive non-DirectiveNode entries."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _walk_cache_relevant_vars

    operation = parse("query Q($v: Boolean!) { items @skip(if: $v) { name } }").definitions[0]
    field = operation.selection_set.selections[0]

    directive_names: set[str] = set()
    pagination_names: set[str] = set()
    node = SimpleNamespace(directives=[object(), *field.directives], selection_set=None)
    _walk_cache_relevant_vars(node, {}, set(), 0, directive_names, pagination_names)
    assert directive_names == {"v"}


def test_walk_cache_relevant_vars_visits_each_fragment_once_across_sibling_spreads():
    """Sibling spreads of the same fragment do not re-walk the fragment subtree."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _walk_cache_relevant_vars

    doc = parse(
        "query Q($v: Boolean!) { "
        "a: items { ...F } "
        "b: items { ...F } "
        "} "
        "fragment F on Item { name @skip(if: $v) }",
    )
    operation = doc.definitions[0]
    fragments = {d.name.value: d for d in doc.definitions[1:]}
    directive_names: set[str] = set()
    pagination_names: set[str] = set()
    visited: set[tuple[str, int]] = set()
    _walk_cache_relevant_vars(operation, fragments, visited, 0, directive_names, pagination_names)
    assert directive_names == {"v"}
    # Fragment F was descended exactly once even though it was spread twice: both
    # spread sites sit at the same response-path depth (inside an ``items`` field),
    # so the depth-aware ``(name, depth)`` guard dedupes them to a single entry.
    assert visited == {("F", 1)}


def test_walk_cache_relevant_vars_handles_unresolved_fragment_name():
    """A spread referencing an unknown fragment name is skipped silently."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _walk_cache_relevant_vars

    doc = parse("query Q { items { ...Missing } }")
    operation = doc.definitions[0]
    directive_names: set[str] = set()
    pagination_names: set[str] = set()
    visited: set[str] = set()
    _walk_cache_relevant_vars(operation, {}, visited, 0, directive_names, pagination_names)
    assert directive_names == set()
    assert visited == set()


def test_collect_directive_var_names_ignores_other_directives():
    """B1: only @skip and @include directives split the plan cache."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse("query Q($v: Boolean!) { items @custom(if: $v) { name } }")
    names = _collect_directive_var_names(doc.definitions[0])
    assert names == frozenset()


def test_collect_directive_var_names_nested_fragments():
    """B1: vars in directives on nested fields are collected."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse(
        "query Q($a: Boolean!, $b: Boolean!) { "
        "items { name @skip(if: $a) entries @include(if: $b) { value } } }",
    )
    names = _collect_directive_var_names(doc.definitions[0])
    assert names == frozenset({"a", "b"})


def test_collect_directive_var_names_no_directives():
    """B1: a query with no directives returns an empty frozenset."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse("{ items { name } }")
    names = _collect_directive_var_names(doc.definitions[0])
    assert names == frozenset()


# ---------------------------------------------------------------------------
# B1: plan-cache key hygiene for nested pagination variables (spec-033 Slice 3,
# Decision 7). Nested ``first``/``last``/``before``/``after`` variables are
# baked into windowed prefetch plans by Slice 1, so their values must key the
# cache; root pagination variables stay out (root slicing is post-plan).
# ---------------------------------------------------------------------------


def _key_for(
    operation,
    *,
    variable_values,
    path_key,
    model=Category,
):
    """Build a ``_build_cache_key`` tuple for ``operation`` at root ``path_key``.

    Mirrors the ``SimpleNamespace`` info pattern used by the existing direct
    cache-key pins (``test_cache_key_includes_root_runtime_path_for_same_model_fields``).
    The two calls under test differ only in ``variable_values``, so any key
    inequality is attributable to the variable-collection rule.
    """
    info = SimpleNamespace(
        operation=operation,
        fragments={},
        variable_values=variable_values,
        path=SimpleNamespace(key=path_key, prev=None),
    )
    return DjangoOptimizerExtension._build_cache_key(info, model)


def test_nested_pagination_variable_keys_cache():
    """A nested ``first: $n`` value keys the plan cache: two values -> two keys."""
    from graphql import parse

    operation = parse(
        "query Q($n: Int!) { parents { booksConnection(first: $n) "
        "{ edges { node { title } } } } }",
    ).definitions[0]

    key_two = _key_for(operation, variable_values={"n": 2}, path_key="parents")
    key_five = _key_for(operation, variable_values={"n": 5}, path_key="parents")
    assert key_two != key_five


def test_root_pagination_variable_shares_cache():
    """A root ``first: $n`` value does NOT key the cache (root slicing post-plan)."""
    from graphql import parse

    operation = parse(
        "query Q($n: Int!) { someRootConnection(first: $n) { edges { node { name } } } }",
    ).definitions[0]

    key_two = _key_for(operation, variable_values={"n": 2}, path_key="someRootConnection")
    key_five = _key_for(operation, variable_values={"n": 5}, path_key="someRootConnection")
    assert key_two == key_five


def test_mixed_root_and_nested_pagination_variables():
    """Only the nested pagination variable keys: vary root -> share, vary nested -> split."""
    from graphql import parse

    operation = parse(
        "query Q($r: Int!, $n: Int!) { parents(first: $r) "
        "{ booksConnection(first: $n) { edges { node { title } } } } }",
    ).definitions[0]

    base = _key_for(operation, variable_values={"r": 1, "n": 2}, path_key="parents")
    vary_root = _key_for(operation, variable_values={"r": 9, "n": 2}, path_key="parents")
    vary_nested = _key_for(operation, variable_values={"r": 1, "n": 5}, path_key="parents")

    assert base == vary_root  # root pagination variable is invariant in the plan
    assert base != vary_nested  # nested pagination variable keys the cache


def test_root_fragment_pagination_variable_shares_cache():
    """A root connection through a ``Query`` fragment is still root: ``$n`` stays out.

    Decision 7 line 346: depth is preserved at the spread SITE. The fragment
    spreads at response-path depth 0, so its connection field is root and its
    pagination variable does not key the cache.
    """
    from graphql import parse

    doc = parse(
        "query Q($n: Int!) { ...RootFrag } "
        "fragment RootFrag on Query { someRootConnection(first: $n) "
        "{ edges { node { name } } } }",
    )
    operation = doc.definitions[0]
    fragments = {d.name.value: d for d in doc.definitions[1:]}
    info_two = SimpleNamespace(
        operation=operation,
        fragments=fragments,
        variable_values={"n": 2},
        path=SimpleNamespace(key="someRootConnection", prev=None),
    )
    info_five = SimpleNamespace(
        operation=operation,
        fragments=fragments,
        variable_values={"n": 5},
        path=SimpleNamespace(key="someRootConnection", prev=None),
    )
    assert DjangoOptimizerExtension._build_cache_key(
        info_two,
        Category,
    ) == DjangoOptimizerExtension._build_cache_key(info_five, Category)


def test_fragment_carried_nested_pagination_variable_collected():
    """A nested connection through a parent-node fragment is still nested: ``$n`` keys.

    The fragment spreads inside ``node`` (response-path depth >= 1), so its
    ``booksConnection`` field is nested and its pagination variable keys the
    cache - the positive spread-site-depth pin (Decision 7 line 346).
    """
    from graphql import parse

    doc = parse(
        "query Q($n: Int!) { parents { edges { node { ...BooksFrag } } } } "
        "fragment BooksFrag on ParentNode { booksConnection(first: $n) "
        "{ edges { node { title } } } }",
    )
    operation = doc.definitions[0]
    fragments = {d.name.value: d for d in doc.definitions[1:]}
    info_two = SimpleNamespace(
        operation=operation,
        fragments=fragments,
        variable_values={"n": 2},
        path=SimpleNamespace(key="parents", prev=None),
    )
    info_five = SimpleNamespace(
        operation=operation,
        fragments=fragments,
        variable_values={"n": 5},
        path=SimpleNamespace(key="parents", prev=None),
    )
    assert DjangoOptimizerExtension._build_cache_key(
        info_two,
        Category,
    ) != DjangoOptimizerExtension._build_cache_key(info_five, Category)


def test_fragment_spread_at_two_depths_collects_nested_pagination_variable():
    """A fragment spread at BOTH root and nested depth still keys on its nested ``$n``.

    Regression pin for the depth-aware fragment cycle guard. The same fragment is
    spread once at root depth (pagination excluded) and once inside ``node``
    (response-path depth >= 1, pagination collected). A name-only visited guard let
    the first-visited (root) spread suppress the nested spread, dropping ``$n`` from
    the cache key so two requests differing only in ``$n`` shared one cached plan --
    serving the wrong windowed prefetch (Decision 7: "under-collection would serve
    wrong data"). Both spread orders must collect ``$n``.
    """
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import (
        _collect_nested_pagination_var_names,
    )

    frag = "fragment F on Thing { booksConnection(first: $n) { edges { node { title } } } }"
    root_first = parse(
        "query Q($n: Int!) { ...F parents { edges { node { ...F } } } } " + frag,
    )
    nested_first = parse(
        "query Q($n: Int!) { parents { edges { node { ...F } } } ...F } " + frag,
    )
    for doc in (root_first, nested_first):
        operation = doc.definitions[0]
        fragments = {d.name.value: d for d in doc.definitions[1:]}
        names = _collect_nested_pagination_var_names(operation, fragments)
        assert names == frozenset({"n"})


def test_pagination_var_collection_is_syntactic_superset():
    """A non-connection nested field with ``first: $n`` is still collected (over-collection).

    Decision 7 line 347: the collection is a syntactic superset by design - any
    non-root field's pagination-named variable keys the cache, even on a plain
    resolver that is not a synthesized connection. Over-collection costs cheap
    duplicate cache entries; under-collection would serve wrong data.
    """
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import (
        _collect_nested_pagination_var_names,
    )

    doc = parse("{ parents { someField(first: $n) { value } } }")
    names = _collect_nested_pagination_var_names(doc.definitions[0])
    assert names == frozenset({"n"})


def test_collect_nested_pagination_var_names_excludes_root_field():
    """Root-field pagination variables are excluded from the collected name set."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import (
        _collect_nested_pagination_var_names,
    )

    doc = parse("query Q($n: Int!) { rootConn(first: $n) { edges { node { name } } } }")
    names = _collect_nested_pagination_var_names(doc.definitions[0])
    assert names == frozenset()


def test_collect_nested_pagination_var_names_all_arg_names():
    """All four pagination arg names collect; a non-pagination arg (``limit``) does not."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import (
        _collect_nested_pagination_var_names,
    )

    doc = parse(
        "query Q($f: Int, $l: Int, $b: String, $a: String, $lim: Int) { "
        "parents { conn(first: $f, last: $l, before: $b, after: $a, limit: $lim) "
        "{ edges { node { name } } } } }",
    )
    names = _collect_nested_pagination_var_names(doc.definitions[0])
    assert names == frozenset(
        {
            "f",
            "l",
            "b",
            "a",
        },
    )  # ``$lim`` (a filter var) stays out


def test_collect_nested_pagination_var_names_ignores_inline_literals():
    """A nested pagination arg with an inline literal (not a variable) is not collected.

    Inline literals already key the cache via the printed AST; the collector
    only tracks variable references (mirroring the directive collector).
    """
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import (
        _collect_nested_pagination_var_names,
    )

    doc = parse("{ parents { booksConnection(first: 3) { edges { node { title } } } } }")
    names = _collect_nested_pagination_var_names(doc.definitions[0])
    assert names == frozenset()


def _categories_list_schema(ext):
    """Build a ``DjangoListField(CategoryType)`` root over the reverse FK ``Category.items``.

    With the optimizer installed the parent ``Category`` queryset is planned, so
    the nested ``itemsConnection`` window lands on each category's ``to_attr``
    and the nested pagination value is baked into the cached plan - the
    end-to-end shape Slice 3's cache-key rule must keep honest. A non-visibility
    synthetic target (no ``get_queryset``), so the plan is cacheable (spec line
    350: the visibility-bearing library shape is uncacheable for an orthogonal
    reason and is covered by Slice 5, not here).
    """
    type(
        "ItemType",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": Item, "fields": ("id", "name"), "interfaces": (relay.Node,)},
            ),
        },
    )
    category_type = type(
        "CategoryType",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": Category,
                    "fields": ("id", "name", "items"),
                    "interfaces": (relay.Node,),
                },
            ),
        },
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"objs": list[category_type]},
                "objs": DjangoListField(category_type),
            },
        ),
    )
    return strawberry.Schema(
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: ext],
    )


@pytest.mark.django_db
def test_nested_pagination_variable_two_plans_two_windows():
    """End-to-end: a nested ``first: $n`` value varying yields two distinct cached plans.

    Executes the real synthesized ``itemsConnection`` under an optimizer-planned
    parent list with ``$n=2`` then ``$n=5``: two misses, two cache entries (each
    plan bakes its own window), no hit. The correctness rule of Decision 7
    observed through the live ``on_execute`` lifecycle and plan cache.
    """
    services.seed_data(2)
    ext = DjangoOptimizerExtension()
    schema = _categories_list_schema(ext)
    query = (
        "query Q($n: Int!) { objs { name itemsConnection(first: $n) "
        "{ edges { node { name } } } } }"
    )

    result_two = schema.execute_sync(query, variable_values={"n": 2})
    result_five = schema.execute_sync(query, variable_values={"n": 5})

    assert result_two.errors is None, result_two.errors
    assert result_five.errors is None, result_five.errors
    assert ext.cache_info().misses == 2
    assert ext.cache_info().hits == 0
    assert ext.cache_info().size == 2


@pytest.mark.django_db
def test_root_pagination_variable_one_plan_through_schema():
    """End-to-end: a ROOT connection's ``first: $n`` value shares one cached plan.

    The optimizer-on counterpart of ``test_filter_vars_do_not_affect_cache`` for
    pagination: a root list field whose own ``first: $n`` slices post-plan does
    not fragment the cache - one miss + one hit across two ``$n`` values.
    """
    services.seed_data(2)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self, first: int = 10) -> list[CategoryType]:
            return Category.objects.all()[:first]

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    query = "query Q($n: Int!) { allCategories(first: $n) { name } }"

    schema.execute_sync(query, variable_values={"n": 1})
    schema.execute_sync(query, variable_values={"n": 2})

    assert ext.cache_info().hits == 1
    assert ext.cache_info().size == 1


@pytest.mark.django_db
def test_cache_key_variable_name_collection_memoized_for_nested_fallbacks(monkeypatch):
    """The unified var-name AST walk runs once per operation, not per ``_build_cache_key``.

    Decision 7: nested fallback connections call ``_build_cache_key`` once per
    parent row, so the full-operation cache-relevant-variable walk must be
    memoized per ``id(operation)`` within one ``on_execute`` lifecycle. Wrap the
    unified collector (``_collect_cache_relevant_var_names`` -- which now folds
    both the directive and nested-pagination families into one traversal) with a
    call counter and assert repeated ``_build_cache_key`` calls on the SAME
    operation walk it only once.
    """
    from graphql import parse

    import django_strawberry_framework.optimizer.extension as extension_module

    calls = {"count": 0}
    real = extension_module._collect_cache_relevant_var_names

    def _counting(operation, fragments):
        calls["count"] += 1
        return real(operation, fragments)

    monkeypatch.setattr(extension_module, "_collect_cache_relevant_var_names", _counting)

    operation = parse(
        "query Q($n: Int!) { parents { booksConnection(first: $n) "
        "{ edges { node { title } } } } }",
    ).definitions[0]
    info = SimpleNamespace(
        operation=operation,
        fragments={},
        variable_values={"n": 2},
        path=SimpleNamespace(key="parents", prev=None),
    )

    ext = DjangoOptimizerExtension()
    gen = ext.on_execute()
    next(gen)  # enter the lifecycle: installs the per-execution var-name memo
    try:
        DjangoOptimizerExtension._build_cache_key(info, Category)
        DjangoOptimizerExtension._build_cache_key(info, Category)
        DjangoOptimizerExtension._build_cache_key(info, Category)
    finally:
        with contextlib.suppress(StopIteration):
            next(gen)  # exit the lifecycle: resets the memo

    assert calls["count"] == 1


def test_collect_cache_relevant_var_names_unifies_both_families_through_fragment():
    """B1: one traversal returns BOTH a directive var and a nested-pagination var.

    The unified ``_collect_cache_relevant_var_names`` walk collects the
    ``@skip``/``@include`` family and the non-root pagination family in a single
    descent, including through a fragment spread. ``$skip`` (a directive variable
    on a nested field) and ``$n`` (a ``first:`` pagination variable on a nested
    field) both reach the cache key from one walk; the root field ``parents``
    contributes neither.
    """
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_cache_relevant_var_names

    doc = parse(
        "query Q($skip: Boolean!, $n: Int!) { parents { ...F } } "
        "fragment F on Parent { booksConnection(first: $n) @skip(if: $skip) "
        "{ edges { node { title } } } }",
    )
    operation = doc.definitions[0]
    fragments = {d.name.value: d for d in doc.definitions[1:]}
    names = _collect_cache_relevant_var_names(operation, fragments)
    assert names == frozenset({"skip", "n"})


# ---------------------------------------------------------------------------
# B3: N+1 detection (strictness API)
# ---------------------------------------------------------------------------


def test_strictness_invalid_value_raises():
    """B3: passing an invalid strictness value raises ValueError."""
    with pytest.raises(ValueError, match="strictness must be"):
        DjangoOptimizerExtension(strictness="invalid")


@pytest.mark.django_db
def test_strictness_warn_logs_unplanned_relation(caplog):
    """B3: strictness='warn' logs a warning for unplanned uncached relation access."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return list(Item.objects.all()[:1])

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    ctx = SimpleNamespace(
        dst_optimizer_planned=set(),
        dst_optimizer_strictness="warn",
    )

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert any("Potential N+1 on category" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_strictness_off_does_not_stash_sentinel():
    """B3: strictness='off' does not stash the sentinel on context."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    ext = DjangoOptimizerExtension(strictness="off")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync("{ allCategories { name } }", context_value=ctx)
    assert result.errors is None
    # No sentinel stashed when strictness is off.
    assert not hasattr(ctx, "dst_optimizer_planned")


@pytest.mark.django_db
def test_strictness_warn_stashes_sentinel():
    """B3: strictness='warn' stashes the sentinel on context."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    ext = DjangoOptimizerExtension(strictness="warn")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    planned = getattr(ctx, "dst_optimizer_planned", None)
    assert planned is not None
    assert "ItemType.category@allItems.category" in planned
    assert ctx.dst_optimizer_strictness == "warn"


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["warn", "raise"])
def test_strictness_with_empty_plan_does_not_raise_or_warn(mode, caplog):
    """B3/M2: an empty plan plus strictness='warn'/'raise' must not raise or warn.

    ``_publish_plan_to_context`` stashes the strictness sentinels (planned set,
    lookup paths, mode) before ``_optimize`` short-circuits on ``plan.is_empty``.
    The invariant is that an empty plan implies no relation selections, so the
    downstream resolver path never compares against the empty planned set.  This
    test pins the invariant for the enabled-optimizer path under both ``warn``
    and ``raise`` - a scalar-only query against a registered type produces an
    empty plan and must resolve cleanly with no warning emitted and no
    exception raised.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    ext = DjangoOptimizerExtension(strictness=mode)
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    with caplog.at_level("WARNING", logger=optimizer_logger.name):
        result = schema.execute_sync("{ allCategories { name } }", context_value=ctx)
    # No GraphQL execution errors (would surface a "raise" strictness trip).
    assert result.errors is None
    # No optimizer-level warning logged (would surface a "warn" strictness trip).
    assert not any(
        record.name == optimizer_logger.name and record.levelname == "WARNING"
        for record in caplog.records
    )
    # Strictness sentinels are still stashed (the plan is published before the
    # is_empty short-circuit); the planned set is just empty.
    assert ctx.dst_optimizer_strictness == mode
    assert ctx.dst_optimizer_planned == set()


@pytest.mark.django_db
def test_strictness_includes_fk_id_elision_in_planned_paths(caplog):
    """B2+B3: FK-id-elided relations are planned and do not warn."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    ext = DjangoOptimizerExtension(strictness="warn")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = schema.execute_sync(
        "{ allItems { name category { id } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert "ItemType.category@allItems.category" in ctx.dst_optimizer_planned
    assert ctx.dst_optimizer_fk_id_elisions == {"ItemType.category@allItems.category"}
    assert not any("Potential N+1" in r.message for r in caplog.records)


def test_will_lazy_load_false_when_cached():
    """B3: pin the __dict__ compatibility seam used by synthetic test doubles."""
    from django_strawberry_framework.types.resolvers import _will_lazy_load_single

    root = SimpleNamespace(category="cached_value")
    assert _will_lazy_load_single(root, "category") is False


def test_will_lazy_load_false_when_in_fields_cache():
    """B3: _will_lazy_load_single returns False when a relation is in _state.fields_cache."""
    from django_strawberry_framework.types.resolvers import _will_lazy_load_single

    root = SimpleNamespace(_state=SimpleNamespace(fields_cache={"card": "cached"}))
    assert _will_lazy_load_single(root, "card") is False


@pytest.mark.django_db
def test_will_lazy_load_false_for_real_forward_fk_in_fields_cache():
    """B3: real forward FKs cache in _state.fields_cache, not __dict__."""
    from django_strawberry_framework.types.resolvers import _will_lazy_load_single

    services.seed_data(1)
    item = Item.objects.select_related("category").first()

    assert item is not None
    assert "category" not in item.__dict__
    assert "category" in item._state.fields_cache
    assert _will_lazy_load_single(item, "category") is False


@pytest.mark.django_db
def test_will_lazy_load_false_for_real_reverse_one_to_one_in_fields_cache():
    """B3: real reverse OneToOne relations also cache in _state.fields_cache."""
    from apps.library.models import MembershipCard, Patron

    from django_strawberry_framework.types.resolvers import _will_lazy_load_single

    patron = Patron.objects.create(name="Rio")
    MembershipCard.objects.create(patron=patron, barcode="1234")
    cached_patron = Patron.objects.select_related("card").get(pk=patron.pk)

    assert "card" not in cached_patron.__dict__
    assert "card" in cached_patron._state.fields_cache
    assert _will_lazy_load_single(cached_patron, "card") is False


def test_will_lazy_load_true_when_not_cached():
    """B3: _will_lazy_load_single returns True when the relation is not cached."""
    from django_strawberry_framework.types.resolvers import _will_lazy_load_single

    root = SimpleNamespace()
    assert _will_lazy_load_single(root, "category") is True


def test_will_lazy_load_false_when_prefetched():
    """B3: _will_lazy_load_many returns False when relation is in _prefetched_objects_cache."""
    from django_strawberry_framework.types.resolvers import _will_lazy_load_many

    root = SimpleNamespace()
    root._prefetched_objects_cache = {
        "items": [1, 2, 3],
    }
    assert _will_lazy_load_many(root, "items") is False


@pytest.mark.django_db
def test_strictness_raise_accepts_unplanned_cached_forward_fk():
    """B3: strictness='raise' accepts an unplanned forward FK that is already loaded."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return list(Item.objects.select_related("category").all()[:1])

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    ctx = SimpleNamespace(
        dst_optimizer_planned=set(),
        dst_optimizer_strictness="raise",
    )

    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert result.data["allItems"][0]["category"]["name"]


@pytest.mark.django_db
def test_strictness_raise_accepts_unplanned_cached_reverse_one_to_one():
    """B3: strictness='raise' accepts an unplanned reverse OneToOne already loaded."""
    from apps.library.models import MembershipCard, Patron

    patron = Patron.objects.create(name="Rio")
    MembershipCard.objects.create(patron=patron, barcode="1234")

    class CardType(DjangoType):
        class Meta:
            model = MembershipCard
            fields = ("id", "barcode")

    class PatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("id", "name", "card")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_patrons(self) -> list[PatronType]:
            return list(Patron.objects.select_related("card").all())

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    ctx = SimpleNamespace(
        dst_optimizer_planned=set(),
        dst_optimizer_strictness="raise",
    )

    result = schema.execute_sync(
        "{ allPatrons { name card { barcode } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert result.data == {
        "allPatrons": [
            {"name": "Rio", "card": {"barcode": "1234"}},
        ],
    }


@pytest.mark.django_db
def test_strictness_warn_planned_alias_no_warning(caplog):
    """B3: aliased relation that IS planned does not trigger a warning."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    ext = DjangoOptimizerExtension(strictness="warn")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    # Use an alias "cat" for the planned "category" relation.
    result = schema.execute_sync(
        "{ allItems { name cat: category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    # The plan includes "category" and the resolver uses field_name
    # (not the alias), so no false-positive warning.
    assert not any("Potential N+1" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_optimizer_strictness_accepts_nested_planned_relation():
    """O4+B3: strictness accepts resolver keys from nested plans."""
    services.seed_data(1)

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "entries")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    ext = DjangoOptimizerExtension(strictness="raise")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allCategories { items { entries { value } } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert "ItemType.entries@allCategories.items.entries" in ctx.dst_optimizer_planned


@pytest.mark.django_db
def test_optimizer_nested_prefetch_with_custom_get_queryset_marks_uncacheable():
    """O4+O6: nested request-dependent prefetch plans are not cached."""
    services.seed_data(1)
    calls = []

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            calls.append(info)
            return queryset

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "entries")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "items")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    query = "{ allCategories { items { entries { value } } } }"

    assert schema.execute_sync(query).errors is None
    assert schema.execute_sync(query).errors is None
    assert len(calls) == 2
    assert ext.cache_info().size == 0


def test_collect_directive_var_names_in_named_fragment():
    """B1: _collect_directive_var_names follows named fragment spreads."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse(
        "query Q($show: Boolean!) { allItems { ...ItemBits } } "
        "fragment ItemBits on ItemType { category @include(if: $show) { name } }",
    )
    operation = doc.definitions[0]
    fragments = {d.name.value: d for d in doc.definitions if hasattr(d, "type_condition")}
    names = _collect_directive_var_names(operation, fragments=fragments)
    assert names == frozenset({"show"})


def test_collect_directive_var_names_includes_fragment_spread_directives():
    """B1: directives on a ``...Spread`` itself feed the cache key, not just the body."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse(
        "query Q($show: Boolean!) { allItems { ...ItemBits @include(if: $show) } } "
        "fragment ItemBits on ItemType { category { name } }",
    )
    operation = doc.definitions[0]
    fragments = {d.name.value: d for d in doc.definitions if hasattr(d, "type_condition")}
    names = _collect_directive_var_names(operation, fragments=fragments)
    assert names == frozenset({"show"})


def test_cache_key_includes_fragment_spread_directive_variable_value():
    """B1: a variable on a fragment-spread ``@include`` splits the cache."""
    from graphql import parse

    doc = parse(
        "query Q($show: Boolean!) { allItems { ...ItemBits @include(if: $show) } } "
        "fragment ItemBits on ItemType { category { name } }",
    )
    operation = doc.definitions[0]
    fragments = {d.name.value: d for d in doc.definitions if hasattr(d, "type_condition")}
    info_false = SimpleNamespace(
        operation=operation,
        fragments=fragments,
        variable_values={"show": False},
        path=SimpleNamespace(key="allItems", prev=None),
    )
    info_true = SimpleNamespace(
        operation=operation,
        fragments=fragments,
        variable_values={"show": True},
        path=SimpleNamespace(key="allItems", prev=None),
    )

    assert DjangoOptimizerExtension._build_cache_key(
        info_false,
        Item,
    ) != DjangoOptimizerExtension._build_cache_key(info_true, Item)


# ---------------------------------------------------------------------------
# B6: Schema-build-time optimization audit
# ---------------------------------------------------------------------------


def test_collect_schema_reachable_types_returns_empty_without_graphql_schema():
    """B6: schemas without a graphql-core schema expose no reachable types."""
    from django_strawberry_framework.optimizer.extension import _collect_schema_reachable_types

    assert _collect_schema_reachable_types(SimpleNamespace()) == set()


def test_check_schema_skips_unreachable_and_missing_field_map(monkeypatch):
    """B6: check_schema skips orphan types and types without optimizer metadata."""
    import django_strawberry_framework.optimizer.extension as extension_module

    class ReachableWithoutFieldMap:
        pass

    class UnreachableType:
        pass

    registry.register(Category, ReachableWithoutFieldMap)
    registry.register(Item, UnreachableType)
    monkeypatch.setattr(
        extension_module,
        "_collect_schema_reachable_types",
        lambda schema: {ReachableWithoutFieldMap},
    )

    assert DjangoOptimizerExtension.check_schema(SimpleNamespace()) == []


def test_check_schema_warns_unregistered_target():
    """B6: check_schema warns when a relation's target has no registered DjangoType."""

    # Must register CategoryType first so ItemType's category relation resolves at finalize time,
    # then clear it from the registry so check_schema sees the gap.
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    # Clear Category's registration so the audit finds a gap.
    _force_unregister_after_finalize(CategoryType)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    assert any("category" in w and "no registered target" in w for w in warnings)


def test_check_schema_descends_into_union_types():
    """B6: union members are reachable in check_schema's audit walk.

    GraphQL unions expose their constituent object types via ``.types``,
    not ``.fields``. The schema walker must descend into ``.types`` so a
    ``DjangoType`` reachable only through a union (e.g.
    ``list[ItemType | CategoryType]``) still participates in the audit.
    Without that, ``check_schema`` silently skips missing-target warnings
    for any relation that lives on a union-member type.
    """
    from django_strawberry_framework.optimizer.extension import _collect_schema_reachable_types

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self) -> list[ItemType | CategoryType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    # Internal reachable set must include both union members.
    reachable = _collect_schema_reachable_types(schema)
    assert ItemType in reachable
    assert CategoryType in reachable

    # User-visible consequence: drop Category's registration and check_schema
    # must still surface the gap on ItemType.category. Without the union walk
    # ItemType is unreachable from the root, the audit skips it, and the
    # warning is silently lost.
    _force_unregister_after_finalize(CategoryType)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    assert any("category" in w and "no registered target" in w for w in warnings)


def test_check_schema_descends_into_interface_implementations():
    """B6: interface implementers are reachable in check_schema's audit walk.

    GraphQL interfaces expose their concrete implementers via
    ``schema.get_implementations(interface_type).objects``, not via
    ``.fields`` or ``.types``. When a root field is typed as an
    interface and the only ``DjangoType``s involved are the concrete
    implementations, the schema walker must descend into those
    implementations so each implementer's relations still participate
    in the audit. Without that, ``check_schema`` silently skips missing
    -target warnings for any relation that lives on an interface
    implementer.
    """
    from strawberry import relay

    from django_strawberry_framework.optimizer.extension import _collect_schema_reachable_types

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class ItemNode(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        @strawberry.field
        def some_node(self) -> relay.Node:  # type: ignore[valid-type]
            return None  # pragma: no cover

    finalize_django_types()
    schema = strawberry.Schema(query=Query, types=[CategoryNode, ItemNode])

    # Internal reachable set must include both implementers even though
    # the root field is typed as the ``Node`` interface.
    reachable = _collect_schema_reachable_types(schema)
    assert ItemNode in reachable
    assert CategoryNode in reachable

    # User-visible consequence: drop Category's registration and the
    # audit must still surface the gap on ItemNode.category. Without
    # interface descent ItemNode would not be reachable and the warning
    # would be silently lost.
    _force_unregister_after_finalize(CategoryNode)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    assert any("category" in w and "no registered target" in w for w in warnings)


def test_check_schema_no_warnings_when_all_covered():
    """B6: check_schema returns no warnings when all relations have registered targets."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    # category's target (Category) is registered, so no warnings for it.
    assert not any("category" in w for w in warnings)


def test_check_schema_skip_hint_suppresses_warning():
    """B6: relations with OptimizerHint.SKIP are not flagged."""
    from django_strawberry_framework import OptimizerHint

    # Register CategoryType so the ItemType.category PendingRelation resolves at finalize time.
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            optimizer_hints = {"category": OptimizerHint.SKIP}

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    # Clear Category so the audit would normally warn - but SKIP suppresses.
    _force_unregister_after_finalize(CategoryType)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    # SKIP means category is intentionally unoptimized - no warning.
    assert not any("category" in w for w in warnings)


def test_check_schema_hidden_fields_not_flagged():
    """B6: relations excluded by Meta.fields are not flagged."""

    # ItemType excludes "category" from Meta.fields.
    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    # category is not in the definition field map, so it is not flagged.
    assert not any("category" in w for w in warnings)


# ---------------------------------------------------------------------------
# B4: Meta.optimizer_hints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimizer_hint_skip_suppresses_relation(django_assert_num_queries):
    """B4: OptimizerHint.SKIP excludes a relation from the plan."""
    from django_strawberry_framework import OptimizerHint

    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            optimizer_hints = {"category": OptimizerHint.SKIP}

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    # SKIP means category is NOT in select_related.
    assert "category" not in plan.select_related


@pytest.mark.django_db
def test_optimizer_hint_skip_routes_through_hint_is_skip():
    """Pins ``rev-optimizer__hints.md`` Medium: the walker dispatches
    skip directives through ``hint_is_skip`` rather than open-coding the
    ``hint is SKIP or hint.skip`` test. A non-sentinel ``skip=True``
    instance must still be honoured.
    """
    from django_strawberry_framework import OptimizerHint

    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            # Construct a fresh skip-shaped hint instead of OptimizerHint.SKIP
            # so the dispatch path cannot rely on identity-equality alone.
            optimizer_hints = {"category": OptimizerHint(skip=True)}

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert "category" not in plan.select_related


@pytest.mark.django_db
def test_optimizer_hint_force_prefetch(django_assert_num_queries):
    """B4: OptimizerHint.prefetch_related() forces prefetch on a forward FK."""
    from django_strawberry_framework import OptimizerHint

    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            optimizer_hints = {"category": OptimizerHint.prefetch_related()}

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    # Force-prefetch overrides the default select_related for forward FK.
    assert [lookup.prefetch_to for lookup in plan.prefetch_related] == ["category"]
    assert "category" not in plan.select_related
    assert "category_id" in plan.only_fields


@pytest.mark.django_db
def test_optimizer_hint_force_select_does_not_bypass_custom_get_queryset(
    django_assert_num_queries,
):
    """B4+O6: ``force_select`` downgrades when the target type filters visibility."""
    from django.db.models import Prefetch

    from django_strawberry_framework import OptimizerHint

    services.seed_data(1)
    calls = []

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            calls.append(info)
            return queryset.filter(is_private=False)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            optimizer_hints = {"category": OptimizerHint.select_related()}

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def public_category_items(self) -> list[ItemType]:
            return Item.objects.filter(category__is_private=False)

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    with django_assert_num_queries(2):
        result = schema.execute_sync(
            "{ publicCategoryItems { name category { name } } }",
            context_value=ctx,
        )

    assert result.errors is None
    assert calls
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ()
    assert plan.cacheable is False
    assert ext.cache_info().size == 0
    assert len(plan.prefetch_related) == 1
    assert isinstance(plan.prefetch_related[0], Prefetch)
    assert plan.prefetch_related[0].prefetch_to == "category"
    assert plan.prefetch_related[0].queryset.query.where


def test_optimizer_hints_unknown_field_raises():
    """B4: unknown field name in optimizer_hints raises ConfigurationError."""
    from django_strawberry_framework import OptimizerHint
    from django_strawberry_framework.exceptions import ConfigurationError

    with pytest.raises(ConfigurationError, match="optimizer_hints names unknown fields"):

        class ItemType(DjangoType):
            class Meta:
                model = Item
                fields = ("id", "name")
                optimizer_hints = {"nonexistent": OptimizerHint.SKIP}


def test_optimizer_hints_non_hint_value_raises():
    """B4: non-OptimizerHint value in optimizer_hints raises ConfigurationError."""
    from django_strawberry_framework.exceptions import ConfigurationError

    with pytest.raises(ConfigurationError, match="OptimizerHint instances"):

        class ItemType(DjangoType):
            class Meta:
                model = Item
                fields = ("id", "name", "category")
                optimizer_hints = {"category": "skip"}  # string, not OptimizerHint


def test_optimizer_hint_importable_from_top_level():
    """B4: OptimizerHint is importable from the top-level package."""
    from django_strawberry_framework import OptimizerHint

    assert OptimizerHint.SKIP is not None
    assert OptimizerHint.select_related() is not None


# ---------------------------------------------------------------------------
# B5: plan introspection via context
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_plan_stashed_with_select_related(django_assert_num_queries):
    """B5: the stashed plan contains the expected select_related entries."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    # Build a synthetic info to drive _optimize directly.
    from graphql import GraphQLList, GraphQLNonNull

    inner = schema._schema.type_map["ItemType"]
    wrapped = GraphQLNonNull(GraphQLList(GraphQLNonNull(inner)))

    # We need a real field_nodes to convert selections from.
    # Execute the query to get a real result, but use a custom context
    # to capture the plan.
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = getattr(ctx, "dst_optimizer_plan", None)
    assert plan is not None
    assert "category" in plan.select_related


@pytest.mark.django_db
def test_plan_stashed_with_prefetch_related(django_assert_num_queries):
    """B5: the stashed plan contains the expected prefetch_related entries."""
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allCategories { name items { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = getattr(ctx, "dst_optimizer_plan", None)
    assert plan is not None
    assert [lookup.prefetch_to for lookup in plan.prefetch_related] == ["items"]


def test_publish_plan_to_context_reuses_finalized_metadata():
    """B5: context publish reuses finalized frozensets instead of rebuilding them."""
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    ext = DjangoOptimizerExtension(strictness="raise")
    plan = OptimizationPlan(
        select_related=["category"],
        fk_id_elisions=["ItemType.category@allItems.category"],
        planned_resolver_keys=["ItemType.category@allItems.category"],
    ).finalize()
    ctx = SimpleNamespace()

    ext._publish_plan_to_context(plan, SimpleNamespace(context=ctx))

    assert ctx.dst_optimizer_plan is plan
    assert ctx.dst_optimizer_fk_id_elisions is plan.finalized_fk_id_elisions
    assert ctx.dst_optimizer_planned is plan.finalized_planned_resolver_keys
    assert ctx.dst_optimizer_lookup_paths is plan.finalized_lookup_paths


def test_publish_plan_to_context_rebuilds_metadata_for_unfinalized_plan():
    """B5: an unfinalized plan published under strictness rebuilds the sentinel sets.

    Production plans are always finalized, but the publish path keeps a
    defensive fallback: when ``finalized_*`` is ``None`` it recomputes the
    frozensets from the live directive lists rather than stashing ``None``.
    """
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    ext = DjangoOptimizerExtension(strictness="raise")
    plan = OptimizationPlan(
        select_related=["category"],
        fk_id_elisions=["ItemType.category@allItems.category"],
        planned_resolver_keys=["ItemType.category@allItems.category"],
    )
    assert plan.finalized_planned_resolver_keys is None
    assert plan.finalized_lookup_paths is None
    ctx = SimpleNamespace()

    ext._publish_plan_to_context(plan, SimpleNamespace(context=ctx))

    assert ctx.dst_optimizer_fk_id_elisions == frozenset({"ItemType.category@allItems.category"})
    assert ctx.dst_optimizer_planned == frozenset({"ItemType.category@allItems.category"})
    assert ctx.dst_optimizer_lookup_paths == frozenset({"category"})


def test_named_children_skips_excluded_and_recurses_through_fragments():
    """Connection extraction: ``@skip`` children are dropped and fragments inlined."""
    skipped = SimpleNamespace(name="edges", directives={"skip": {"if": True}}, selections=[])
    inner_edges = SimpleNamespace(name="edges", alias=None, directives={}, selections=[])
    fragment = SimpleNamespace(
        type_condition="ItemConnectionEdge",
        directives={},
        selections=[inner_edges],
    )
    plain = SimpleNamespace(name="edges", alias=None, directives={}, selections=[])
    container = SimpleNamespace(selections=[skipped, fragment, plain])

    result = _named_children(container, "edges")

    # ``skipped`` excluded; the fragment's inner ``edges`` is inlined; ``plain`` kept.
    assert result == [inner_edges, plain]


def test_node_children_with_runtime_prefix_skips_excluded_and_clones_fragments():
    """Connection extraction: node children honor ``@include`` and clone fragments."""
    skipped = SimpleNamespace(name="name", directives={"include": {"if": False}}, selections=[])
    fragment = SimpleNamespace(type_condition="ItemNode", directives={}, selections=[])
    plain = SimpleNamespace(name="name", alias=None, directives={}, arguments={}, selections=[])
    node = SimpleNamespace(selections=[skipped, fragment, plain])
    prefixes = (("items", "edges", "node"),)

    result = _node_children_with_runtime_prefix(node, runtime_prefixes=prefixes)

    # ``skipped`` excluded; fragment cloned (carries its type condition); plain
    # cloned carrying the connection-aware runtime prefix for the walker.
    assert len(result) == 2
    assert result[0].type_condition == "ItemNode"
    assert result[1]._optimizer_runtime_prefixes == [("items", "edges", "node")]


def test_plan_stashed_on_dict_context():
    """B5: when context is a plain dict, plan is stashed via __setitem__."""
    from django_strawberry_framework.optimizer.extension import _stash_on_context

    ctx = {}
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    plan = OptimizationPlan(select_related=["category"])
    _stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert ctx["dst_optimizer_plan"] is plan


def test_stash_on_dict_subclass_writes_mapping_before_attributes():
    """rev-optimizer__context: dict-like contexts must use the mapping branch."""
    from django_strawberry_framework.optimizer._context import get_context_value, stash_on_context
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    class AttributeBackedDict(dict):
        def __init__(self) -> None:
            super().__init__()
            super().__setattr__("attributes", {})

        def __setattr__(self, key: str, value: object) -> None:
            self.attributes[key] = value

    ctx = AttributeBackedDict()
    plan = OptimizationPlan(select_related=["category"])
    stash_on_context(ctx, "dst_optimizer_plan", plan)

    assert ctx["dst_optimizer_plan"] is plan
    assert ctx.attributes == {}
    assert get_context_value(ctx, "dst_optimizer_plan") is plan


def test_stash_on_non_dict_mapping_reads_correctly():
    """get_context_value retrieves stashes from non-dict mappings via item access fallback."""
    from django_strawberry_framework.optimizer._context import get_context_value, stash_on_context
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    class NonDictMapping:
        __slots__ = ("_data",)

        def __init__(self):
            self._data = {}

        def __setitem__(self, key, value):
            self._data[key] = value

        def __getitem__(self, key):
            return self._data[key]

    ctx = NonDictMapping()
    plan = OptimizationPlan()
    stash_on_context(ctx, "dst_optimizer_plan", plan)

    # Assert stash bypassed setattr (because of __slots__) and populated _data
    assert ctx._data["dst_optimizer_plan"] is plan

    # Assert get_context_value safely falls back to item access and retrieves it
    assert get_context_value(ctx, "dst_optimizer_plan") is plan


def test_get_context_value_swallows_attribute_error_from_getitem():
    """rev-optimizer__context: ``__getitem__`` raising ``AttributeError`` on a missing key returns ``default``.

    ``strawberry-graphql-django``'s ``StrawberryDjangoContext`` bridges
    ``__getitem__`` to ``__getattribute__``, so reading a key that was never
    stashed raises ``AttributeError`` out of the item access path. The read
    helper's ``except`` tuple must catch ``AttributeError`` alongside
    ``KeyError`` / ``TypeError`` so the resolver chain sees ``default`` rather
    than a leaking ``AttributeError`` from deep inside item lookup.
    """
    from django_strawberry_framework.optimizer._context import get_context_value

    class BridgedItemAccess:
        """Mimics ``StrawberryDjangoContext.__getitem__`` shape."""

        def __getitem__(self, key):
            raise AttributeError(f"missing attribute {key!r}")

    sentinel = object()
    ctx = BridgedItemAccess()
    assert get_context_value(ctx, "dst_optimizer_plan", sentinel) is sentinel


def test_stash_on_none_context_is_silent():
    """B5: when context is None (Strawberry default), stash is silently skipped."""
    from django_strawberry_framework.optimizer.extension import _stash_on_context
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    plan = OptimizationPlan()
    # Should not raise.
    _stash_on_context(None, "dst_optimizer_plan", plan)


def test_plan_stashed_on_object_context_unit():
    """B5: when context is an object, plan is stashed via setattr."""
    from django_strawberry_framework.optimizer.extension import _stash_on_context

    ctx = SimpleNamespace()
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    plan = OptimizationPlan(prefetch_related=["items"])
    _stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert ctx.dst_optimizer_plan is plan


def test_stash_on_read_only_mapping_is_silent():
    """B5: a read-only ``MappingProxyType`` context must not abort the resolver chain.

    Pins the Medium fix from rev-optimizer__extension.md: ``setattr`` on a
    ``MappingProxyType`` raises ``TypeError`` (not ``AttributeError``), and
    ``__setitem__`` then raises ``TypeError`` again. Both must be swallowed
    so the optimizer's introspection-stash failure never crashes the
    request.
    """
    from types import MappingProxyType

    from django_strawberry_framework.optimizer.extension import _stash_on_context
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    ctx = MappingProxyType({})
    plan = OptimizationPlan(prefetch_related=["items"])
    # Should not raise.
    _stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert "dst_optimizer_plan" not in ctx


def test_stash_falls_back_to_setitem_on_typeerror():
    """B5: a ``dict`` subclass is still stashed through ``__setitem__``.

    Dict-like context objects take the mapping branch before attribute
    writes, so a subclass with hostile attribute assignment still stores
    the optimizer plan where ``get_context_value`` will read it.
    """
    from django_strawberry_framework.optimizer.extension import _stash_on_context
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    class TypeErrorOnSetattr(dict):
        def __setattr__(self, _key: str, _value: object) -> None:
            raise TypeError("read-only attribute access")

    ctx = TypeErrorOnSetattr()
    plan = OptimizationPlan(prefetch_related=["items"])
    _stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert ctx["dst_optimizer_plan"] is plan


def test_stash_on_immutable_dict_subclass_is_silent():
    """rev-optimizer__context: ``AttributeError`` from a frozen ``dict`` subclass is silently skipped.

    Django's ``QueryDict`` is a ``dict`` subclass that raises
    ``AttributeError("This QueryDict instance is immutable")`` from
    ``__setitem__`` when locked. The dict-first dispatch in
    ``stash_on_context`` routes subclasses through the mapping write
    path, so the trailing ``except`` must catch ``AttributeError`` in
    addition to ``TypeError`` - otherwise an immutable-``QueryDict``
    context would crash the resolver chain instead of being silently
    skipped, contradicting the docstring contract ("Frozen contexts ...
    raise on assignment; those stashes are silently skipped").
    """
    from django_strawberry_framework.optimizer._context import stash_on_context
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    class ImmutableDictSubclass(dict):
        def __setitem__(self, _key: str, _value: object) -> None:
            raise AttributeError("this dict is immutable")

    ctx = ImmutableDictSubclass()
    plan = OptimizationPlan(prefetch_related=["items"])
    stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert "dst_optimizer_plan" not in ctx


def test_stash_does_not_swallow_unexpected_exceptions_from_setitem():
    """rev-optimizer__context: keep the mapping-write ``except`` narrow.

    Read-only mapping failures are intentionally limited to ``TypeError``
    and ``AttributeError``. A guarded mapping that raises a different
    exception from ``__setitem__`` must surface the error rather than
    silently losing the optimizer stash.
    """
    from django_strawberry_framework.optimizer._context import stash_on_context

    class GuardedMapping(dict):
        def __setattr__(self, _key: str, _value: object) -> None:
            raise TypeError("no attribute writes")

        def __setitem__(self, _key: str, _value: object) -> None:
            raise RuntimeError("guarded write rejected")

    ctx = GuardedMapping()
    with pytest.raises(RuntimeError, match="guarded write rejected"):
        stash_on_context(ctx, "dst_optimizer_plan", object())


@pytest.mark.django_db
def test_empty_plan_still_stashed():
    """B5/O5: even when no relations are selected, the scalar-only plan is stashed."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync("{ allCategories { name } }", context_value=ctx)
    assert result.errors is None
    plan = getattr(ctx, "dst_optimizer_plan", None)
    assert plan is not None
    assert plan.only_fields == ("name",)
    assert plan.select_related == ()
    assert plan.prefetch_related == ()


# ---------------------------------------------------------------------------
# O5 - only() projection
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimizer_applies_only_for_selected_scalars(django_assert_num_queries):
    """O5: selected scalar fields are collected into the stashed plan."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "description")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    with django_assert_num_queries(1):
        result = schema.execute_sync(
            "{ allCategories { name } }",
            context_value=ctx,
        )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert plan.only_fields == ("name",)
    assert plan.select_related == ()
    assert plan.prefetch_related == ()


# ---------------------------------------------------------------------------
# O6 - get_queryset + Prefetch downgrade
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimizer_downgrades_select_related_for_custom_get_queryset(django_assert_num_queries):
    """O6: custom target ``get_queryset`` downgrades forward FK traversal to ``Prefetch``."""
    from django.db.models import Prefetch

    services.seed_data(1)
    calls = []

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            calls.append(info)
            return queryset

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    with django_assert_num_queries(2):
        result = schema.execute_sync(
            "{ allItems { name category { name } } }",
            context_value=ctx,
        )
    assert result.errors is None
    assert calls
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ()
    assert "category_id" in plan.only_fields
    assert "category__name" not in plan.only_fields
    assert plan.cacheable is False
    assert ext.cache_info().size == 0
    assert len(plan.prefetch_related) == 1
    assert isinstance(plan.prefetch_related[0], Prefetch)
    assert plan.prefetch_related[0].prefetch_to == "category"


@pytest.mark.django_db
def test_optimizer_does_not_cache_custom_get_queryset_prefetch_plans():
    """O6: request-dependent ``Prefetch`` querysets are rebuilt instead of cached."""
    services.seed_data(1)
    calls = []

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            calls.append(info)
            return queryset

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    query = "{ allItems { name category { name } } }"

    assert schema.execute_sync(query).errors is None
    assert schema.execute_sync(query).errors is None

    assert len(calls) == 2
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 0


def test_plan_relation_returns_prefetch_for_custom_get_queryset():
    """O6: the extension exposes the relation planner entry point."""

    field = Item._meta.get_field("category")
    info = SimpleNamespace()

    class FilteredCategoryType:
        @classmethod
        def has_custom_get_queryset(cls):
            return True

        @classmethod
        def get_queryset(cls, queryset, passed_info, **kwargs):
            assert passed_info is info
            return queryset

    kind, reason = DjangoOptimizerExtension().plan_relation(field, FilteredCategoryType, info)
    assert kind == "prefetch"
    assert reason == "custom_get_queryset"


# ---------------------------------------------------------------------------
# B8: queryset optimization diffing
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_b8_consumer_select_related_does_not_mutate_cached_plan():
    """B8: a consumer's pre-applied ``select_related`` must not mutate B1's cached plan."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.select_related("category")

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])

    # First request warms the plan cache. The plan is stashed pre-diff.
    ctx1 = SimpleNamespace()
    result1 = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx1,
    )
    assert result1.errors is None
    cached_plan = ctx1.dst_optimizer_plan
    assert cached_plan.select_related == ("category",)
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 1

    # Second request hits the cache. The cached plan must still carry
    # ["category"] - the diff must not have mutated it during request 1.
    ctx2 = SimpleNamespace()
    result2 = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx2,
    )
    assert result2.errors is None
    assert ctx2.dst_optimizer_plan is cached_plan
    assert cached_plan.select_related == ("category",)
    assert ext.cache_info().hits == 1


@pytest.mark.django_db
def test_b8_consumer_prefetch_object_suppresses_optimizer_entry():
    """B8: a consumer ``Prefetch("items", queryset=Item.objects.all())`` keeps its slot."""
    from django.db.models import Prefetch

    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    consumer_pf = Prefetch("items", queryset=Item.objects.all())
    captured: list[object] = []

    class _CaptureExt(DjangoOptimizerExtension):
        def _optimize(self, result, info):
            optimized = super()._optimize(result, info)
            captured.append(optimized)
            return optimized

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.prefetch_related(consumer_pf)

    finalize_django_types()
    capture_ext = _CaptureExt()
    schema = strawberry.Schema(query=Query, extensions=[lambda: capture_ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allCategories { name items { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    # Stashed plan still records the optimizer's intended ``items``
    # entry (B5 stashes the pre-diff plan).
    plan = ctx.dst_optimizer_plan
    assert [getattr(entry, "prefetch_to", entry) for entry in plan.prefetch_related] == ["items"]
    # The queryset that came out of ``_optimize`` carries exactly the
    # consumer's ``Prefetch`` - the optimizer entry was diffed away.
    optimized_qs = captured[0]
    lookups = optimized_qs._prefetch_related_lookups
    assert lookups == (consumer_pf,)


# The two B8 behavior-only collision tests (descendant prefetch and
# exact-plus-descendant) moved to the live fakeshop suite per feedback2.md:
# examples/fakeshop/test_query/test_library_api.py::
#   test_b8_consumer_descendant_prefetch_stays_flat_over_http and
#   test_b8_consumer_exact_plus_descendant_prefetch_stays_flat_over_http.
# Those run the real Genre -> books -> loans consumer prefetch through /graphql/
# and add HTTP + flat-query-count pressure the synthetic in-process schema could
# not. The plan/diff-asserting B8 tests below stay package-internal (they inspect
# the optimized queryset's _prefetch_related_lookups, which HTTP cannot expose).


@pytest.mark.django_db
def test_b8_consumer_plain_string_upgraded_to_optimizer_prefetch():
    """B8 P1: a consumer's plain ``"items"`` string is replaced by the optimizer's nested ``Prefetch``."""
    from django.db.models import Prefetch

    services.seed_data(1)

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "entries")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    captured: list[object] = []

    class _CaptureExt(DjangoOptimizerExtension):
        def _optimize(self, result, info):
            optimized = super()._optimize(result, info)
            captured.append(optimized)
            return optimized

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.prefetch_related("items")

    finalize_django_types()
    capture_ext = _CaptureExt()
    schema = strawberry.Schema(query=Query, extensions=[lambda: capture_ext])
    result = schema.execute_sync(
        "{ allCategories { name items { name entries { value } } } }",
    )
    assert result.errors is None
    optimized_qs = captured[0]
    lookups = optimized_qs._prefetch_related_lookups
    # Exactly one ``items`` lookup - the optimizer's ``Prefetch`` -
    # carrying the nested ``entries`` chain. The consumer's plain
    # ``"items"`` string was stripped.
    assert len(lookups) == 1
    items_pf = lookups[0]
    assert isinstance(items_pf, Prefetch)
    assert items_pf.prefetch_to == "items"
    nested = items_pf.queryset._prefetch_related_lookups
    assert any(getattr(entry, "prefetch_to", entry) == "entries" for entry in nested)


# ---------------------------------------------------------------------------
# Construction surface - unknown kwargs raise loudly
# ---------------------------------------------------------------------------


def test_extension_rejects_unknown_kwargs_at_construction():
    """Misspelled config (e.g. ``strict=`` instead of ``strictness=``) raises TypeError."""
    with pytest.raises(TypeError):
        DjangoOptimizerExtension(strict=True)  # type: ignore[call-arg]


def test_extension_accepts_strawberry_execution_context_kwarg():
    """Strawberry instantiates extension *classes* with ``execution_context=...``.

    When the *class* (not an instance) is registered, Strawberry calls
    ``ext(execution_context=None)`` internally to build the per-request instance.
    The extension must accept that keyword without ``TypeError``.
    """
    ext = DjangoOptimizerExtension(execution_context=None)
    assert ext.strictness == "off"


def test_singleton_factory_extensions_form_emits_no_deprecation_warning():
    """The migrated ``extensions=[lambda: _optimizer]`` form does not warn.

    Strawberry 0.316.0's ``Schema.__init__`` emits a ``DeprecationWarning``
    when an extension *instance* is passed in ``extensions=[...]``. The
    singleton-factory form passes a *callable*, so no such warning fires.
    ``simplefilter("always")`` is set inside the context so a warning that
    Strawberry already emitted-and-deduped earlier in the process cannot
    produce a false green. Pins spec-029 Slice 1 / DoD item 4.
    """

    @strawberry.type
    class Query:
        hello: str

    _optimizer = DjangoOptimizerExtension()
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        strawberry.Schema(query=Query, extensions=[lambda: _optimizer])

    instance_form_warnings = [
        w
        for w in recorded
        if issubclass(w.category, DeprecationWarning) and "instance" in str(w.message)
    ]
    assert instance_form_warnings == []


# ---------------------------------------------------------------------------
# hint_is_skip - centralised hint-shape dispatch
# ---------------------------------------------------------------------------


def test_hint_is_skip_handles_sentinel_record_and_unknown_shapes():
    """``hint_is_skip`` returns the documented bool for every supported shape."""
    from django_strawberry_framework.optimizer.hints import OptimizerHint, hint_is_skip

    assert hint_is_skip(None) is False
    assert hint_is_skip(OptimizerHint.SKIP) is True
    assert hint_is_skip(OptimizerHint(skip=True)) is True
    assert hint_is_skip(OptimizerHint.select_related()) is False
    # Unknown shape with no ``.skip`` attribute must not raise - the
    # schema audit's "never raises" contract depends on this.
    assert hint_is_skip(object()) is False


# ---------------------------------------------------------------------------
# Slice 4 - H2 plan-cache origin separation + H3 multi-type audit dedupe
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model():
    """H2: a primary-return resolver and a secondary-return resolver do not collide.

    Two root fields on the same schema return ``list[ItemType]`` and
    ``list[AdminItemType]`` respectively. Both target ``Item`` but
    carry different origin types, so the plan cache must hold two
    distinct entries. Without the origin component of the cache key
    the two queries would share one cached plan keyed by ``Item``
    alone.
    """
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

        @strawberry.field
        def all_admin_items(self) -> list[AdminItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    # Run the same selection through both root fields. Same response shape
    # so doc_key + relevant_vars + target_model agree; only response_path
    # and origin differ. With the new cache key both fields produce
    # distinct entries.
    schema.execute_sync("{ allItems { name } }")
    schema.execute_sync("{ allAdminItems { name } }")
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2


def test_schema_audit_warns_on_relation_field_exposed_only_on_secondary_type():
    """H3: a relation field only present on a secondary still surfaces a warning.

    ``ItemType`` (primary) excludes ``category``; ``AdminItemType``
    (secondary) includes ``category`` with an unregistered target. The
    audit must walk every reachable type so the secondary's relation is
    audited and the missing-target warning is produced. Switching to a
    primary-only iterator would silently drop this warning.
    """

    # Register CategoryType first so AdminItemType.category can resolve
    # during __init_subclass__, then clear it before check_schema runs.
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_admin_items(self) -> list[AdminItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query, types=[ItemType])
    # Clear Category's registration so the audit sees the gap.
    _force_unregister_after_finalize(CategoryType)

    warnings = DjangoOptimizerExtension.check_schema(schema)
    # Item.category is the secondary-only relation; the audit must surface it.
    assert any("Item.category" in w and "no registered target" in w for w in warnings)


def test_schema_audit_dedupes_when_same_relation_field_visited_via_multiple_types():
    """H3: identical (source_model, field_name) warnings collapse to one.

    Both ``ItemType`` (primary) and ``AdminItemType`` (secondary) expose
    ``category`` whose target ``Category`` has no registered
    ``DjangoType``. Without dedupe, ``registry.iter_types()`` (one
    yield per registered type) would produce two identical warnings.
    """

    # Register CategoryType so the type declarations succeed, then drop
    # its registration before check_schema runs.
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

        @strawberry.field
        def all_admin_items(self) -> list[AdminItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    _force_unregister_after_finalize(CategoryType)

    warnings = DjangoOptimizerExtension.check_schema(schema)
    item_category_warnings = [w for w in warnings if "Item.category" in w]
    assert len(item_category_warnings) == 1


def test_schema_audit_warning_names_the_source_type_for_multi_type_models():
    """B6/M1: the warning text includes ``type_cls.__name__`` for multi-type models.

    Per-source-model dedupe collapses warnings to one per ``(model, field_name)``
    even when two registered types for the same model expose the same relation.
    The warning string must still identify *which* type's audit produced the
    entry so a consumer can disambiguate; the source type's name is rendered
    alongside ``model.field`` so the dedupe artifact never loses provenance.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

        @strawberry.field
        def all_admin_items(self) -> list[AdminItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    _force_unregister_after_finalize(CategoryType)

    warnings = DjangoOptimizerExtension.check_schema(schema)
    item_category_warnings = [w for w in warnings if "Item.category" in w]
    # Dedupe still applies - one warning per (model, field_name).
    assert len(item_category_warnings) == 1
    # The surviving warning must name the source type (the first one iterated)
    # so the consumer can identify which type's audit produced the entry.
    [warning] = item_category_warnings
    assert "ItemType" in warning or "AdminItemType" in warning


def test_model_for_type_reverse_lookup_works_for_secondary_type():
    """Secondary types remain discoverable for the optimizer's reverse lookup.

    Both ``ItemType`` and ``AdminItemType`` are registered against
    ``Item``; ``registry.model_for_type`` returns the same ``Item`` for
    either origin. The optimizer's ``_resolve_model_from_return_type``
    composition surfaces both legs of the pair: ``origin`` is the
    secondary, ``model`` is the underlying Django model.
    """
    from graphql import GraphQLList, GraphQLNonNull

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.model_for_type(AdminItemType) is Item

    @strawberry.type
    class Query:
        @strawberry.field
        def all_admin_items(self) -> list[AdminItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query, types=[ItemType])
    inner = schema._schema.type_map["AdminItemType"]
    wrapped = GraphQLNonNull(GraphQLList(GraphQLNonNull(inner)))
    info = SimpleNamespace(return_type=wrapped, schema=schema._schema)
    resolved = _resolve_model_from_return_type(info)
    assert resolved is not None
    assert resolved.origin is AdminItemType
    assert resolved.model is Item


# ---------------------------------------------------------------------------
# Slice 2 - ``apply_connection_optimization`` helper extraction (no-regression)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimizer_helper_extraction_no_regression():
    """Extracting ``apply_to`` from ``_optimize`` leaves the middleware path identical.

    Spec Slice 2 / Decision 11: the plan-build-and-apply tail was extracted into
    ``DjangoOptimizerExtension.apply_to`` (shared with the connection field's
    ``apply_connection_optimization``). The existing B1-B8 suite in this module
    is the broad regression guard; this focused test pins that a non-connection
    root field still has its plan built and applied (``select_related`` lands)
    and that ``_optimize`` delegates to ``apply_to``.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension(strictness="raise")
    delegations: list[tuple] = []
    real_apply_to = ext.apply_to

    def _spy_apply_to(
        target_type,
        target_model,
        queryset,
        info,
    ):
        delegations.append((target_type, target_model))
        return real_apply_to(target_type, target_model, queryset, info)

    ext.apply_to = _spy_apply_to

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync("{ allItems { category { name } } }", context_value=ctx)

    assert result.errors is None
    # The plan was built and applied (the forward FK is select_related-ed) - the
    # middleware behavior is unchanged by the extraction.
    assert ctx.dst_optimizer_plan.select_related == ("category",)
    # ``_optimize`` delegated to ``apply_to`` with the resolved (origin, model),
    # NOT inferred inside the helper.
    assert delegations == [(ItemType, Item)]


@pytest.mark.django_db
def test_apply_connection_optimization_uses_active_optimizer_cache():
    """``apply_connection_optimization`` shares the active extension's plan cache.

    Decision 11 plan-cache-reuse route: ``on_execute`` publishes the active
    extension on the ``_active_optimizer`` ``ContextVar``; the connection helper
    discovers it so connection-field plans hit the SAME instance-bound cache the
    middleware uses (rather than a throwaway cache-less extension).
    """
    from django_strawberry_framework.optimizer.extension import (
        _active_optimizer,
        apply_connection_optimization,
    )

    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()
    captured: dict = {}

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self, info: strawberry.types.Info) -> list[ItemType]:
            # Inside a resolver the ``on_execute`` lifecycle has published the
            # active extension; the helper must discover it (not build a
            # throwaway). Apply twice so the second call is a cache hit on the
            # SAME instance.
            qs = Item.objects.all()
            apply_connection_optimization(ItemType, qs, info)
            captured["active"] = _active_optimizer.get()
            return qs

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    result = schema.execute_sync("{ allItems { id } }")
    assert result.errors is None
    # The helper saw the installed extension instance via the ContextVar.
    assert captured["active"] is ext


def test_publish_plan_to_context_unions_parent_and_nested_sentinel_sets():
    """A nested fallback publish UNIONS the correctness sentinels, never overwrites them.

    spec-033 Decision 8 foundation: a nested fallback connection pipeline is a
    real optimizer run that re-enters ``_publish_plan_to_context`` per parent.
    Its publish must not shrink the parent plan's planned / FK-id-elision /
    lookup-path sets - especially under ``"warn"``, where execution continues
    after the nested connection returns. ``DST_OPTIMIZER_PLAN`` stays last-wins
    introspection (not unioned).
    """
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    ext = DjangoOptimizerExtension(strictness="warn")
    parent_plan = OptimizationPlan(
        select_related=["category"],
        fk_id_elisions=["ItemType.category@allItems.category"],
        planned_resolver_keys=["ItemType.category@allItems.category"],
    ).finalize()
    nested_plan = OptimizationPlan(
        prefetch_related=["entries"],
        fk_id_elisions=["EntryType.property@allItems.entries.property"],
        planned_resolver_keys=["EntryType.property@allItems.entries.property"],
    ).finalize()
    ctx = SimpleNamespace()

    ext._publish_plan_to_context(parent_plan, SimpleNamespace(context=ctx))
    # The nested publish (a fallback pipeline re-entry) unions into the parent's stash.
    ext._publish_plan_to_context(nested_plan, SimpleNamespace(context=ctx))

    # The parent's resolver key + FK-id elision survive the nested publish.
    assert ctx.dst_optimizer_planned == frozenset(
        {"ItemType.category@allItems.category", "EntryType.property@allItems.entries.property"},
    )
    assert ctx.dst_optimizer_fk_id_elisions == frozenset(
        {"ItemType.category@allItems.category", "EntryType.property@allItems.entries.property"},
    )
    # Lookup paths union too (parent "category" + nested "entries").
    assert {"category", "entries"} <= ctx.dst_optimizer_lookup_paths
    # DST_OPTIMIZER_PLAN stays last-wins introspection data (not unioned).
    assert ctx.dst_optimizer_plan is nested_plan


def test_publish_plan_to_context_union_tolerates_non_set_existing_stash():
    """``_stash_union`` overwrites a non-set existing stash defensively (no crash)."""
    from django_strawberry_framework.optimizer._context import get_context_value

    ext = DjangoOptimizerExtension(strictness="raise")
    ctx = SimpleNamespace()
    # Pre-seed a non-set value under the planned key (defensive shape).
    DjangoOptimizerExtension._stash_union(ctx, "dst_optimizer_planned", frozenset({"a"}))
    # Existing is a frozenset -> union.
    DjangoOptimizerExtension._stash_union(ctx, "dst_optimizer_planned", frozenset({"b"}))
    assert get_context_value(ctx, "dst_optimizer_planned") == frozenset({"a", "b"})
    # A non-set existing value is overwritten rather than crashing the union.
    ctx.dst_optimizer_planned = "not-a-set"
    DjangoOptimizerExtension._stash_union(ctx, "dst_optimizer_planned", frozenset({"c"}))
    assert get_context_value(ctx, "dst_optimizer_planned") == frozenset({"c"})


@pytest.mark.django_db
def test_nested_connection_fallback_publish_unions_parent_planned_set_end_to_end():
    """End-to-end: a real nested-connection fallback publish UNIONS, never clobbers.

    spec-033 Slice 4 (Decision 8): the Slice-1 unit pin
    (``test_publish_plan_to_context_unions_parent_and_nested_sentinel_sets``)
    proves the helper unions; THIS pins the union holds through an actual nested
    -connection-fallback EXECUTION - the scenario that motivates the union. A
    sidecar-filtered ``itemsConnection(filter:)`` is a Decision-6 fallback: its
    per-parent pipeline is a real optimizer run that re-publishes, but the
    parent's planned ``items`` list-sibling resolver key must survive on the
    shared context (otherwise a planned sibling would spuriously strictness-flag
    after the nested connection returned).
    """
    from django.http import HttpRequest

    from django_strawberry_framework.filters import FilterSet
    from django_strawberry_framework.optimizer._context import (
        DST_OPTIMIZER_PLANNED,
        get_context_value,
    )

    services.seed_data(1)

    class ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = {"name": ["exact"]}

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = ItemFilter

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")
            interfaces = (relay.Node,)

    finalize_django_types()

    @strawberry.type
    class Query:
        objs: list[CategoryType] = DjangoListField(CategoryType)

    ext = DjangoOptimizerExtension(strictness="warn")
    schema = strawberry.Schema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: ext],
    )
    # An ``HttpRequest`` context: the sidecar filter pipeline needs a resolvable
    # request, and the optimizer stashes its sentinels onto the same object
    # (read back via ``get_context_value``). Warn mode so execution continues and
    # the post-return context can be inspected.
    ctx = HttpRequest()
    # ``items`` is the planned reverse-FK list sibling; ``itemsConnection(filter:)``
    # is the sidecar fallback (a real per-parent optimizer publish).
    result = schema.execute_sync(
        "{ objs { items { name } "
        '  itemsConnection(filter: { name: { exact: "nope" } }) '
        "{ edges { node { name } } } } }",
        context_value=ctx,
    )
    assert result.errors is None, result.errors
    planned = get_context_value(ctx, DST_OPTIMIZER_PLANNED, frozenset())
    # The parent's planned ``items`` resolver key survives the nested fallback's
    # publish (the union foundation) - it is NOT shrunk away.
    assert any(key.startswith("CategoryType.items@") for key in planned), planned
    # The sidecar fallback connection was left unplanned (Decision 6): no planned
    # key for the ``items`` relation keyed under the connection's runtime path.
    assert not any("@objs.itemsConnection" in key for key in planned), planned


# =============================================================================
# STAGED SEAM (spec-034 Slice 2): cascade <-> optimizer cooperation pins.
# NO optimizer source change - these pin that a type whose get_queryset CASCADES
# is, to the optimizer, just a type with a custom hook, so the shipped rules fire
# unchanged (Decision 7 / Goal 3). Fill in + drop the skips in Slice 2.
# =============================================================================


@pytest.mark.django_db
def test_cascading_target_downgrades_join_to_prefetch():
    """A relation whose target hook cascades plans a ``Prefetch`` (not ``select_related``).

    The target reports ``has_custom_get_queryset() is True``, so the shipped
    ``optimizer/walker.py::_target_has_custom_get_queryset`` rule fires the
    downgrade and bakes the cascade into the child queryset - no optimizer change.
    ``select_related`` is empty, the relation plans one ``Prefetch``, and the plan
    is ``cacheable is False``.

    LOAD-BEARING (spec-034 Decision 12 dependency to protect): the assertion that
    the prefetch CHILD queryset narrows by the LIVE request user, not merely that
    a ``Prefetch`` is planned. ``walker.py::_build_child_queryset`` threads the
    SAME ``info`` from the root walk into the target hook; a future refactor that
    dropped ``info`` would still plan a ``Prefetch`` while silently breaking
    cascade transitivity (the nested hook would lose ``info.context.user``). The
    cascading hook here both (a) cascades via ``apply_cascade_permissions`` AND
    (b) narrows by a user-derived predicate, so the child SQL carries the live
    user's value - a non-distinguishing ``Prefetch``-only assertion cannot pass.
    """
    from django.db.models import Prefetch

    from django_strawberry_framework.permissions import apply_cascade_permissions

    seen_users = []

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            user = getattr(info.context, "user", None)
            seen_users.append(user)
            # Cascade AND narrow by a user-derived predicate so the live request
            # user reaches the prefetch child queryset's compiled SQL.
            queryset = queryset.filter(name=user.name)
            return apply_cascade_permissions(cls, queryset, info)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    # One public category whose name matches the request user, one item under it.
    request_cat = Category.objects.create(name="request_user", is_private=False)
    Item.objects.create(name="i0", category=request_cat)

    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    request_user = SimpleNamespace(name="request_user")
    ctx = SimpleNamespace(user=request_user)

    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None

    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ()
    assert plan.cacheable is False
    assert ext.cache_info().size == 0
    assert len(plan.prefetch_related) == 1
    assert isinstance(plan.prefetch_related[0], Prefetch)
    assert plan.prefetch_related[0].prefetch_to == "category"

    # Load-bearing: the cascading hook saw the LIVE request user...
    assert seen_users
    assert seen_users[0] is request_user
    # ...and that user's narrowing is baked into the prefetch child queryset's SQL
    # (proving ``_build_child_queryset`` threaded the live ``info``, not a default).
    child_sql = str(plan.prefetch_related[0].queryset.query)
    assert "request_user" in child_sql


@pytest.mark.django_db
def test_plan_with_cascading_hook_uncacheable():
    """A plan baking a cascading hook is ``cacheable = False``; B1 counters unaffected otherwise.

    The shipped rule marks ANY plan baking a custom ``get_queryset`` uncacheable
    (it keys on the *presence* of a custom hook, not on whether the hook reads the
    request - the coarser walker.py rule); the cascade adds no new cache dimension.
    So executing a cascading query twice records ``misses == 2 / hits == 0 /
    size == 0`` - the plan is rebuilt each request (spec-034 Edge case
    "Plan-cache interaction").

    The non-cascading half pins that this uncacheability does NOT contaminate
    ordinary plan caching: a SIBLING non-cascading schema run twice on its own
    extension produces the normal ``miss-then-hit`` (``size == 1``, B1 counters
    unaffected for non-cascading types). Separate extension instances keep the two
    counter streams independently observable.
    """
    from django_strawberry_framework.permissions import apply_cascade_permissions

    public_cat = Category.objects.create(name="public_cat", is_private=False)
    Item.objects.create(name="pub_item", category=public_cat)

    # --- Cascading schema: plan is uncacheable, rebuilt each request. ---
    class CascadingCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)

    class CascadingItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    cascading_ext = DjangoOptimizerExtension()

    @strawberry.type
    class CascadingQuery:
        @strawberry.field
        def all_items(self) -> list[CascadingItemType]:
            return Item.objects.all()

    finalize_django_types()
    cascading_schema = strawberry.Schema(
        query=CascadingQuery,
        extensions=[lambda: cascading_ext],
    )
    query = "{ allItems { name category { name } } }"
    ctx_a = SimpleNamespace(user=None)
    ctx_b = SimpleNamespace(user=None)
    assert cascading_schema.execute_sync(query, context_value=ctx_a).errors is None
    assert cascading_schema.execute_sync(query, context_value=ctx_b).errors is None

    assert ctx_a.dst_optimizer_plan.cacheable is False
    assert cascading_ext.cache_info().hits == 0
    assert cascading_ext.cache_info().misses == 2
    assert cascading_ext.cache_info().size == 0

    # --- Non-cascading sibling: ordinary caching is unaffected (miss then hit). ---
    registry.clear()

    class PlainCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class PlainItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    plain_ext = DjangoOptimizerExtension()

    @strawberry.type
    class PlainQuery:
        @strawberry.field
        def all_items(self) -> list[PlainItemType]:
            return Item.objects.all()

    finalize_django_types()
    plain_schema = strawberry.Schema(query=PlainQuery, extensions=[lambda: plain_ext])
    assert plain_schema.execute_sync(query).errors is None
    assert plain_ext.cache_info().misses == 1
    assert plain_ext.cache_info().hits == 0

    assert plain_schema.execute_sync(query).errors is None
    assert plain_ext.cache_info().hits == 1
    assert plain_ext.cache_info().misses == 1
    assert plain_ext.cache_info().size == 1


# TODO(spec-035 Slice 2): add extension-level G2 cache and operation pins here.
# Pseudocode: execute textually similar query and mutation operations against
# one extension instance; assert the printed-AST cache stores distinct plans,
# the query plan carries ``only_fields``, and the mutation plan does not. Keep
# this package-internal because fakeshop exposes no mutation queryset surface
# until the 0.0.11 mutation cohort.

# TODO(spec-035 Slice 3): add the strictness no-false-fire package pin here if
# it needs real extension execution rather than pure walker inspection.
# Pseudocode: execute an abstract/interface-shaped query whose sibling fragment
# is correctly narrowed; assert strictness ``warn`` emits no optimizer warning
# and strictness ``raise`` returns no "Unplanned N+1" GraphQL error for the
# sibling branch the resolver never runs.
