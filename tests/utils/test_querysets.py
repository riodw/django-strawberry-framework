"""Tests for the shared query-source / visibility substrate (``utils/querysets.py``).

This module single-sites the query-source contract the list field, connection
field, optimizer middleware, Relay node defaults, and filter
related-visibility derive had each spelled separately:
``Manager`` -> ``QuerySet`` coercion, the is-queryset decision, and the sync /
async ``DjangoType.get_queryset`` visibility routing. ``get_queryset`` is the
visibility hook, so a divergence between those copies is a data-leak bug class;
these tests pin the neutral mechanics directly. The deep behavioral coverage
(through-schema list / connection / node / filter visibility) lives in the
surface suites (``tests/test_list_field.py``, ``tests/test_connection.py``,
``tests/test_relay_node_field.py``, ``tests/filters/test_sets.py``).

Visibility-boundary decision references below resolve to
``docs/SPECS/spec-045-visibility_boundary-0_0_14.md #"## Architectural decisions"``.

``coerce_field_value_or_none`` is the sibling "raw
literal -> Django field value, or nothing" primitive shared by the Relay id
decode, the raw relation-pk decode, and the ``__in`` filter member decode; its
own through-schema coverage lives in the same surface suites plus
``examples/fakeshop/test_query/test_scalars_filter_api.py`` (the out-of-range
``__in`` member drop).
"""

import asyncio
import datetime
import enum
import uuid
import zoneinfo
from decimal import Decimal
from types import SimpleNamespace

import pytest
from apps.products.models import Category, Entry, Item, Property
from django.db import models
from django.db.models import FilteredRelation, Prefetch, Q
from django.db.models.expressions import RawSQL
from django.db.models.functions import Coalesce, Trunc

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations import resolvers as mutation_resolvers
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils.querysets import (
    _BOUND_VALUE_NORMALIZERS,
    _CASCADE_SEAL_POLICY,
    _DEFAULT_SEAL_POLICY,
    _INERT_VALUE_TYPES,
    _LIST_ARGUMENT_VISIBILITY_POLICY,
    _PLAIN_CONTAINER_TYPES,
    _PREFETCH_CHILD_POLICY,
    _RETAINED_TYPES,
    _UNRECOMPOSED_CHILD_POLICY,
    SyncMisuseError,
    _bake_deferred_filter_or_defect,
    _base_table_defect,
    _coerced_manager_queryset,
    _concrete_or_none,
    _defect_message,
    _deferred_value_defect,
    _expr_graph_defect,
    _expr_sequence_defect,
    _GraphWalk,
    _is_inert_value,
    _is_plain_container,
    _join_defect,
    _normalized_visibility_result,
    _prefetch_relation_target_or_none,
    _prepared_visibility_source,
    _query_container_defect,
    _query_genuineness_defect,
    _reconstructed_value,
    _safe_class_name,
    _seal_or_defect,
    _sealed_prefetch_related_lookups,
    _SealPolicy,
    _type_is_genuinely_django,
    _validate_post_orderset_result,
    _visibility_result_error,
    _where_tree_defect,
    apply_type_visibility_async,
    apply_type_visibility_sync,
    coerce_field_value_or_none,
    initial_queryset,
    is_async_only_iterable,
    normalize_query_source,
    pks_all_present,
    post_process_queryset_result_async,
    post_process_queryset_result_sync,
    reject_async_in_sync_context,
    reject_async_iterable_in_sync_context,
    reject_awaitable_sync_source,
    run_in_one_sync_boundary,
    visible_related_object,
    visible_related_objects,
)
from django_strawberry_framework.utils.write_transaction import write_pipeline


def test_safe_class_name_falls_back_for_non_string_metaclass_name_metadata():
    """A non-string ``__name__`` degrades to the metaclass name instead of a raw label."""

    class _NonStringNameMeta(type):
        def __getattribute__(cls, name: str):
            if name == "__name__":
                return 42
            return super().__getattribute__(name)

    class _MalformedName(metaclass=_NonStringNameMeta):
        pass

    assert _safe_class_name(_MalformedName) == "_NonStringNameMeta"


class _QsBoundaryBase(models.Model):
    """Boundary-contract fixture base (proxy / MTI table checks; no table needed)."""

    name = models.TextField()

    class Meta:
        app_label = "products"
        managed = False


class _QsBoundaryChild(_QsBoundaryBase):
    """MTI child of the fixture base - an INCOMPATIBLE concrete table."""

    extra = models.TextField()

    class Meta:
        app_label = "products"
        managed = False


class _QsBoundaryProxy(_QsBoundaryBase):
    """Proxy sibling of the fixture base - a COMPATIBLE concrete table."""

    class Meta:
        app_label = "products"
        proxy = True


def _stub_type(model, hook):
    """Build a duck-typed ``DjangoType`` stub over ``model`` with ``hook`` as its visibility hook."""
    return type(
        "_StubType",
        (),
        {
            "__django_strawberry_definition__": SimpleNamespace(model=model),
            "get_queryset": classmethod(hook),
        },
    )


class _SyncType:
    """Duck-typed ``DjangoType`` stub with a sync ``get_queryset``."""

    __django_strawberry_definition__ = SimpleNamespace(model=Category)

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.exclude(name="__never__")


class _AsyncType:
    """Duck-typed ``DjangoType`` stub with an ``async def`` ``get_queryset``."""

    __django_strawberry_definition__ = SimpleNamespace(model=Category)

    @classmethod
    async def get_queryset(cls, queryset, info):
        return queryset


# ---------------------------------------------------------------------------
# normalize_query_source -- the single Manager-coercion / is-queryset decision
# ---------------------------------------------------------------------------


def test_normalize_query_source_coerces_manager_to_queryset():
    """A ``Manager`` becomes a ``QuerySet`` and reports ``is_queryset=True``."""
    source, is_queryset = normalize_query_source(Category.objects)
    assert isinstance(source, models.QuerySet)
    assert is_queryset is True


def test_normalize_query_source_passes_queryset_through():
    """A ``QuerySet`` passes through unchanged with ``is_queryset=True``."""
    qs = Category.objects.all()
    source, is_queryset = normalize_query_source(qs)
    assert source is qs
    assert is_queryset is True


def test_normalize_query_source_passes_non_queryset_through():
    """A non-queryset iterable passes through with ``is_queryset=False``."""
    payload = [1, 2, 3]
    source, is_queryset = normalize_query_source(payload)
    assert source is payload
    assert is_queryset is False


def test_initial_queryset_uses_default_manager():
    """``initial_queryset`` returns the declared model's ``_default_manager.all()``."""
    qs = initial_queryset(_SyncType)
    assert isinstance(qs, models.QuerySet)
    assert qs.model is Category


# ---------------------------------------------------------------------------
# coerce_field_value_or_none -- the shared "raw literal -> field value" coercion
# ---------------------------------------------------------------------------


def test_coerce_field_value_or_none_returns_coerced_value():
    """A well-formed literal coerces through ``to_python`` + ``run_validators``."""
    assert coerce_field_value_or_none(Category._meta.pk, "3") == 3


def test_coerce_field_value_or_none_drops_non_numeric_literal():
    """A non-numeric literal fails ``to_python`` (wrapped as ``ValidationError``) -> ``None``."""
    assert coerce_field_value_or_none(Category._meta.pk, "not-a-number") is None


def test_coerce_field_value_or_none_drops_out_of_range_literal():
    """A syntactically-valid but out-of-range literal fails ``run_validators`` -> ``None``.

    ``to_python`` alone would cast ``2**63`` (one past the ``BigAutoField`` pk's
    signed-64-bit range) to a plain Python ``int`` with no error; only
    ``run_validators`` catches the range violation, which is the whole point of
    running both steps rather than ``to_python`` alone (never a raw backend
    ``OverflowError`` at ``pk__in``).
    """
    assert coerce_field_value_or_none(Category._meta.pk, 2**63) is None


@pytest.mark.django_db
def test_relation_write_visibility_boundary_is_controlled_by_type_registration():
    """Unregistered targets use their default manager; registered targets apply visibility."""
    registry.clear()
    category = Category.objects.create(name="VisibilityBoundary")
    try:
        assert visible_related_objects(Category, [category.pk], info=None) == {str(category.pk)}

        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "name")
                primary = True

            @classmethod
            def get_queryset(cls, queryset, info):
                return queryset.exclude(pk=category.pk)

        del CategoryType
        assert visible_related_objects(Category, [category.pk], info=None) == set()
    finally:
        registry.clear()


# ---------------------------------------------------------------------------
# apply_type_visibility_sync / _async -- the colored visibility routing
# ---------------------------------------------------------------------------


def test_apply_type_visibility_sync_runs_sync_get_queryset():
    """The sync path invokes ``get_queryset`` and returns its queryset."""
    base = Category.objects.all()
    result = apply_type_visibility_sync(_SyncType, base, info=None)
    assert isinstance(result, models.QuerySet)


def test_apply_type_visibility_sync_rejects_async_hook_loudly():
    """An ``async def`` ``get_queryset`` under the sync path raises ``SyncMisuseError``.

    The coroutine is closed before the raise (the ``filterwarnings = error``
    pytest config would fail the test on an unawaited-coroutine warning), and the
    typed marker is both a ``ConfigurationError`` and a ``RuntimeError``.
    """
    base = Category.objects.all()
    with pytest.raises(SyncMisuseError, match="returned a coroutine in a sync"):
        apply_type_visibility_sync(_AsyncType, base, info=None)
    assert issubclass(SyncMisuseError, ConfigurationError)
    assert issubclass(SyncMisuseError, RuntimeError)


async def test_apply_type_visibility_async_awaits_async_hook():
    """The async path awaits an ``async def`` ``get_queryset`` to a real queryset."""
    base = Category.objects.all()
    result = await apply_type_visibility_async(_AsyncType, base, info=None)
    assert isinstance(result, models.QuerySet)


async def test_apply_type_visibility_async_passes_sync_hook_through():
    """The async path passes a sync ``get_queryset`` return through without awaiting."""
    base = Category.objects.all()
    result = await apply_type_visibility_async(_SyncType, base, info=None)
    assert isinstance(result, models.QuerySet)


# ---------------------------------------------------------------------------
# post_process_queryset_result_* -- the list-field consumer-resolver shape
# ---------------------------------------------------------------------------


def test_post_process_sync_coerces_manager_then_applies_visibility():
    """A ``Manager`` return is coerced then run through ``get_queryset`` (sync)."""
    result = post_process_queryset_result_sync(_SyncType, Category.objects, info=None)
    assert isinstance(result, models.QuerySet)


def test_post_process_sync_passes_python_list_through():
    """A non-queryset Python list is returned unchanged (no visibility hook)."""
    payload = [object(), object()]
    result = post_process_queryset_result_sync(_SyncType, payload, info=None)
    assert result is payload


async def test_post_process_async_coerces_manager_then_applies_visibility():
    """A ``Manager`` return is coerced then awaited through ``get_queryset`` (async)."""
    result = await post_process_queryset_result_async(_AsyncType, Category.objects, info=None)
    assert isinstance(result, models.QuerySet)


async def test_post_process_async_passes_python_list_through():
    """A non-queryset Python list is returned unchanged on the async path."""
    payload = [object()]
    result = await post_process_queryset_result_async(_AsyncType, payload, info=None)
    assert result is payload


# ---------------------------------------------------------------------------
# run_in_one_sync_boundary -- the shared off-event-loop worker primitive
# ---------------------------------------------------------------------------


def test_run_in_one_sync_boundary_is_single_sourced_from_utils():
    """Mutations re-exports the utils owner; sites must not re-inline the wrapper.

    The byte-identical ``sync_to_async(fn, thread_sensitive=True)(*args, **kwargs)``
    shape was promoted out of ``mutations/resolvers.py`` into this module so filters / orders /
    permissions / auth share one boundary. Pin the re-export identity so a
    future split cannot silently fork a second definition.
    """
    assert mutation_resolvers.run_in_one_sync_boundary is run_in_one_sync_boundary


async def test_run_in_one_sync_boundary_runs_callable_off_event_loop():
    """The primitive executes ``fn`` on a worker thread, not the event-loop thread."""
    import threading

    captured: dict[str, int] = {}

    def _body() -> str:
        captured["worker"] = threading.get_ident()
        return "ok"

    async def _run() -> str:
        captured["loop"] = threading.get_ident()
        return await run_in_one_sync_boundary(_body)

    assert await _run() == "ok"
    assert captured["worker"] != captured["loop"]


# ---------------------------------------------------------------------------
# The hardened visibility boundary -- source preparation
# (the get_queryset-visibility-boundary decision)
# ---------------------------------------------------------------------------


def test_visibility_source_must_be_a_queryset():
    """A non-queryset source fails closed BEFORE the hook runs (fires no consumer code)."""

    def _boom(cls, queryset, info):  # pragma: no cover - must never run
        raise AssertionError("hook ran on an invalid source")

    with pytest.raises(ConfigurationError, match="requires a QuerySet of Category rows"):
        apply_type_visibility_sync(_stub_type(Category, _boom), [1, 2], info=None)


def test_visibility_source_must_use_registered_concrete_table():
    """A source over the wrong model fails closed - the hook would narrow the wrong table."""
    with pytest.raises(ConfigurationError, match="concrete table"):
        apply_type_visibility_sync(_SyncType, Item.objects.all(), info=None)


@pytest.mark.django_db
def test_evaluated_source_is_refreshed_before_hook(django_assert_num_queries):
    """An evaluated source is ``.all()``-refreshed before consumer code sees it - zero SQL.

    Cached rows must never reach (or bypass) the hook: the hook receives a
    fresh unevaluated clone, and the refresh itself composes lazily (the
    security carve-out from the optimizer's G1 same-instance guarantee).
    """
    seen: dict[str, object] = {}

    def _capture(cls, queryset, info):
        seen["qs"] = queryset
        return queryset

    evaluated = Category.objects.all()
    list(evaluated)  # materialize the cache
    with django_assert_num_queries(0):
        result = apply_type_visibility_sync(_stub_type(Category, _capture), evaluated, info=None)
    assert seen["qs"] is not evaluated
    assert seen["qs"]._result_cache is None
    assert result._result_cache is None


def test_active_write_pipeline_pins_source_and_repins_result():
    """Under an active write pipeline the source is pre-pinned and an unpinned result repinned."""
    hook = _stub_type(Category, lambda cls, qs, info: Category.objects.filter(name="x"))
    with write_pipeline("default", lock=False):
        result = apply_type_visibility_sync(hook, Category.objects.all(), info=None)
    assert result._db == "default"


def test_active_write_pipeline_rejects_divergent_source_alias():
    """An explicitly divergent SOURCE alias under a write pipeline fails closed (pre-pin)."""
    with (
        write_pipeline("default", lock=False),
        pytest.raises(ConfigurationError, match="routed to alias 'other'"),
    ):
        apply_type_visibility_sync(_SyncType, Category.objects.using("other"), info=None)


def test_hostile_source_all_override_is_neutralized_by_sealing():
    """A source subclass overriding ``.all()`` is neutralized - the override never runs.

    The predicate-erasure vector: a hostile ``.all()`` that would return a fresh
    unfiltered queryset. The boundary never dispatches through the consumer
    object; it seals the source into a fresh framework-owned plain ``QuerySet``
    rebuilt from the extracted query state, so the overridden ``.all()`` is never
    called and the visibility ``WHERE`` survives. The hook (``_SyncType``) then
    runs on that sealed plain queryset.
    """

    class _StickySource(models.QuerySet):
        def all(self):  # would be a predicate-dropping clone if ever dispatched
            return Category.objects.all()

    sticky = models.QuerySet.filter(_StickySource(model=Category), name="visible")
    result = apply_type_visibility_sync(_SyncType, sticky, info=None)
    assert type(result) is models.QuerySet  # sealed - not the hostile subclass
    assert "visible" in str(result.query)  # the source predicate survived sealing


def test_unsealable_source_fails_closed():
    """A SOURCE that cannot be sealed fails closed before the hook runs.

    Where the source's state cannot be faithfully rebuilt (here a foreign
    row-iterable class injected after construction), source preparation fails
    closed with the ``untrusted`` defect - "cannot be sealed" - so the hook never
    runs on an unsealable source.
    """

    def _boom(cls, queryset, info):  # pragma: no cover - must never run
        raise AssertionError("hook ran on an unsealable source")

    source = Category.objects.filter(name="visible")
    source._iterable_class = list  # a foreign row synthesizer
    with pytest.raises(ConfigurationError, match="cannot be sealed"):
        apply_type_visibility_sync(_stub_type(Category, _boom), source, info=None)


# ---------------------------------------------------------------------------
# The hardened visibility boundary -- hook-result normalization
# ---------------------------------------------------------------------------


def _sync_hook_type(result):
    """A Category stub type whose hook returns ``result`` verbatim."""
    return _stub_type(Category, lambda cls, qs, info: result)


def test_hook_manager_result_is_coerced_sync():
    """A ``Manager`` hook return is coerced exactly once through ``.all()`` (sync path)."""
    result = apply_type_visibility_sync(
        _sync_hook_type(Category.objects),
        Category.objects.all(),
        info=None,
    )
    assert isinstance(result, models.QuerySet)
    assert result.model is Category


async def test_hook_manager_result_is_coerced_async():
    """An async-path ``Manager`` return is coerced too - previously it flowed through verbatim."""

    class _ManagerAsyncType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

        @classmethod
        async def get_queryset(cls, queryset, info):
            return Category.objects

    result = await apply_type_visibility_async(
        _ManagerAsyncType,
        Category.objects.all(),
        info=None,
    )
    assert isinstance(result, models.QuerySet)


def _async_generator_result():
    async def _agen():
        yield 1  # pragma: no cover - never iterated

    return _agen()


@pytest.mark.parametrize(
    ("bad", "detail"),
    [
        (None, "NoneType"),
        ([], "list"),
        ((n for n in ()), "generator"),
        (_async_generator_result(), "async_generator"),
        (object(), "object"),
    ],
)
def test_invalid_hook_results_fail_closed(bad, detail):
    """``None`` / list / generator / async-generator / custom-iterable returns fail closed."""
    with pytest.raises(
        ConfigurationError,
        match=f"must return a QuerySet or Manager.*got {detail}",
    ):
        apply_type_visibility_sync(_sync_hook_type(bad), Category.objects.all(), info=None)


def test_wrong_model_hook_result_fails_closed():
    """A queryset over an unrelated model fails closed (wrong concrete table)."""
    with pytest.raises(ConfigurationError, match="concrete table"):
        apply_type_visibility_sync(
            _sync_hook_type(Item.objects.all()),
            Category.objects.all(),
            info=None,
        )


def test_mti_child_hook_result_fails_closed():
    """An MTI-child queryset lives on ITS OWN concrete table - incompatible."""
    hook = _stub_type(_QsBoundaryBase, lambda cls, qs, info: _QsBoundaryChild.objects.all())
    with pytest.raises(ConfigurationError, match="concrete table"):
        apply_type_visibility_sync(hook, _QsBoundaryBase.objects.all(), info=None)


def test_combined_query_branch_over_another_model_fails_closed():
    """A union whose branch reads another model's table fails closed.

    ``QuerySet.model`` reports the outer (registered) model, but a
    ``combined_queries`` branch reads ``Item``'s table; with a compatible
    projection those rows would materialize as ``Category`` and cross the
    visibility boundary. The recursive branch check (``_combined_query_table_defect``)
    catches the divergent branch the public ``.model`` hides. Constructing the
    union composes lazy query state only - no SQL runs.
    """
    hostile = Category.objects.all().union(Item.objects.all())
    with pytest.raises(ConfigurationError, match="concrete table"):
        apply_type_visibility_sync(_sync_hook_type(hostile), Category.objects.all(), info=None)


def test_mutable_public_model_disagreeing_with_query_model_fails_closed():
    """A queryset whose public ``.model`` matches but ``query.model`` does not fails closed.

    ``QuerySet.model`` is a mutable public attribute that can disagree with the
    SQL-bearing ``query.model``; validating only the public model would let the
    SQL read another table. The boundary validates ``Query.model`` too, so the
    disagreement is caught. No SQL runs.
    """
    hostile = Category.objects.all()
    hostile.query.model = Item
    with pytest.raises(ConfigurationError, match="concrete table"):
        apply_type_visibility_sync(_sync_hook_type(hostile), Category.objects.all(), info=None)


def test_proxy_hook_result_is_accepted():
    """A proxy-sibling queryset shares the concrete table and passes the boundary."""
    hook = _stub_type(_QsBoundaryBase, lambda cls, qs, info: _QsBoundaryProxy.objects.all())
    result = apply_type_visibility_sync(hook, _QsBoundaryBase.objects.all(), info=None)
    assert result.model is _QsBoundaryProxy


def test_unpinned_result_is_repinned_to_explicit_source_alias():
    """A routed source's alias is required: an unpinned hook result is normalized onto it.

    Alias-state only - the alias never resolves a connection, so no secondary
    database is needed.
    """
    hook = _stub_type(Category, lambda cls, qs, info: Category.objects.filter(name="x"))
    result = apply_type_visibility_sync(hook, Category.objects.using("other"), info=None)
    assert result._db == "other"


def test_matching_explicit_result_alias_is_accepted():
    """A hook result explicitly routed to the required alias passes through."""
    result = apply_type_visibility_sync(
        _SyncType,
        Category.objects.using("other").all(),
        info=None,
    )
    assert result._db == "other"


def test_divergent_explicit_result_alias_fails_closed():
    """A hook result explicitly routed OFF the required alias fails closed."""
    hook = _stub_type(Category, lambda cls, qs, info: Category.objects.using("elsewhere"))
    with pytest.raises(
        ConfigurationError,
        match="routed to alias 'elsewhere'.*pinned to alias 'other'",
    ):
        apply_type_visibility_sync(hook, Category.objects.using("other"), info=None)


def test_unpinned_read_hook_keeps_documented_alias_routing():
    """With no required alias, an unpinned read hook may still choose ``.using(alias)`` itself."""
    hook = _stub_type(Category, lambda cls, qs, info: qs.using("other"))
    result = apply_type_visibility_sync(hook, Category.objects.all(), info=None)
    assert result._db == "other"


@pytest.mark.django_db
def test_evaluated_hook_result_is_refreshed(django_assert_num_queries):
    """An evaluated hook result is re-cloned so cached rows never survive the boundary."""
    evaluated = Category.objects.all()
    list(evaluated)
    with django_assert_num_queries(0):
        result = apply_type_visibility_sync(
            _sync_hook_type(evaluated),
            Category.objects.all(),
            info=None,
        )
    assert result is not evaluated
    assert result._result_cache is None


def test_normalization_preserves_lazy_query_state():
    """Sealing preserves lazy query state: filters / annotations / ordering survive.

    The sealed queryset is a fresh framework-owned plain ``QuerySet`` (subclass
    identity is deliberately dropped), but every piece of SQL state that decides
    which rows are selected - the filter, the annotation, the ordering - is
    rebuilt from the cloned query and preserved.
    """

    class _CustomQuerySet(models.QuerySet):
        pass

    shaped = (
        _CustomQuerySet(model=Category)
        .filter(name__startswith="a")
        .annotate(flag=models.Value(1))
        .order_by("-name")
    )
    result = apply_type_visibility_sync(_sync_hook_type(shaped), Category.objects.all(), info=None)
    assert type(result) is models.QuerySet  # sealed - the subclass identity is dropped
    assert result is not shaped
    assert "flag" in result.query.annotations
    assert result.query.order_by == ("-name",)
    assert "a" in str(result.query)  # the startswith filter survived


def test_hostile_result_all_override_is_neutralized_by_sealing():
    """A hook-result subclass overriding ``.all()`` is neutralized by sealing.

    The predicate-erasure vector (a hostile ``.all()`` returning a fresh
    unfiltered queryset) is defused because the boundary never dispatches the
    override: it seals the hook result into a fresh plain ``QuerySet`` rebuilt
    from the result's query state, so the visibility predicate survives.
    """

    class _StickyResult(models.QuerySet):
        def all(self):  # a predicate-dropping clone if ever dispatched
            return Category.objects.all()

    sticky = models.QuerySet.filter(_StickyResult(model=Category), name="visible")
    result = apply_type_visibility_sync(_sync_hook_type(sticky), Category.objects.all(), info=None)
    assert type(result) is models.QuerySet
    assert "visible" in str(result.query)


def test_hostile_result_using_override_repin_is_neutralized_by_sealing():
    """A hook-result subclass overriding ``.using()`` cannot dodge the alias pin.

    The boundary pins the required alias at CONSTRUCTION (``using=`` on the fresh
    sealed queryset), never by calling ``.using()`` on the consumer object, so a
    ``.using()`` that returns an unrouted self can never dodge the repin.
    """

    class _PinDodger(models.QuerySet):
        def using(self, alias):  # would return an unrouted self if dispatched
            return self

    hook = _stub_type(Category, lambda cls, qs, info: _PinDodger(model=Category))
    result = apply_type_visibility_sync(hook, Category.objects.using("other"), info=None)
    assert type(result) is models.QuerySet
    assert result._db == "other"  # pinned at construction, not via the override


def test_predicate_dropping_all_override_source_is_neutralized_by_sealing():
    """A source ``.all()`` that would return a fresh UNFILTERED queryset is neutralized.

    The core predicate-erasure vector: the override would return a same-model,
    same-alias, unevaluated queryset with NO ``WHERE`` clause. Because the seal
    rebuilds from the source's extracted query state and never dispatches the
    override, the visibility predicate is preserved.
    """

    class _DropFilter(models.QuerySet):
        def all(self):
            return Category.objects.all()  # would drop whatever WHERE the source carried

    hostile = models.QuerySet.filter(_DropFilter(model=Category), name="visible")
    result = apply_type_visibility_sync(_SyncType, hostile, info=None)
    assert type(result) is models.QuerySet
    assert "visible" in str(result.query)


def test_foreign_query_class_result_fails_closed():
    """A hook result whose ``_query`` is a foreign ``Query`` subclass cannot be sealed.

    The seal clones the query through the unbound ``sql.Query.clone`` and rebuilds
    a plain ``QuerySet``; a foreign ``Query`` class cannot be faithfully rebuilt
    (its SQL-assembly behavior is unknown), so it fails closed with the
    ``untrusted`` defect - "cannot be sealed".
    """
    from django.db.models import sql

    class _ForeignQuery(sql.Query):
        pass

    result = Category.objects.filter(name="visible")
    result._query = _ForeignQuery(Category)
    hook = _sync_hook_type(result)
    with pytest.raises(ConfigurationError, match="cannot be sealed"):
        apply_type_visibility_sync(hook, Category.objects.all(), info=None)


def test_unresolved_deferred_filter_subclass_result_fails_closed():
    """A SUBCLASS result carrying an unresolved ``_deferred_filter`` cannot be sealed.

    A pending deferred filter holds a predicate not yet baked into the query.
    Resolution is gated on ``type(candidate) is models.QuerySet`` exactly, so a
    SUBCLASS is left unresolved and fails closed at the unresolved-filter check --
    the seal never bakes a subclass's pending predicate. Only an EXACT plain
    ``QuerySet`` is resolved (see
    ``test_exact_queryset_pending_deferred_filter_is_resolved``).
    """

    class _DeferredSub(models.QuerySet):
        pass

    result = _DeferredSub(model=Category)
    result._deferred_filter = (False, (), {"name": "later"})
    hook = _sync_hook_type(result)
    with pytest.raises(ConfigurationError, match="cannot be sealed"):
        apply_type_visibility_sync(hook, Category.objects.all(), info=None)


def test_exact_queryset_pending_deferred_filter_is_resolved():
    """An EXACT plain ``QuerySet`` carrying a pending ``_deferred_filter`` seals cleanly.

    Django's ``RelatedManager._apply_rel_filters`` leaves the relation predicate as
    a pending ``_deferred_filter`` that is only baked into ``_query`` on first
    ``.query`` access, so ``instance.rel.all()`` reaches the seal with the flag set.
    The seal bakes the predicate through the UNBOUND ``sql.Query.add_q`` -- onto the
    DETACHED clone, never Django's getter (whose bound helpers are instance-
    shadowable) and never the candidate. The predicate lands in the sealed SQL while
    the candidate's ``_deferred_filter`` is left UNTOUCHED (observational immutability:
    a concurrent caller reusing the same source queryset sees no mutation).
    """
    result = Category.objects.all()
    result._deferred_filter = (False, (), {"name": "later"})
    sealed, defect = _seal_or_defect(result, Category, None)
    assert defect is None
    # The candidate is never mutated -- the pending flag is left exactly as it was.
    assert result.__dict__.get("_deferred_filter") == (False, (), {"name": "later"})
    sql_str, params = sealed.query.get_compiler(using="default").as_sql()
    assert "name" in sql_str
    assert "later" in params


def test_pending_deferred_filter_over_foreign_query_never_dispatches():
    """Resolving a pending deferred filter must not dispatch a foreign ``_query``.

    An EXACT plain ``QuerySet`` whose ``_query`` is a foreign ``sql.Query`` SUBCLASS
    and which also carries a pending ``_deferred_filter`` must fail closed on the
    exact-``sql.Query`` gate WITHOUT ever running the deferred resolution -- that
    resolution dispatches ``self._query.add_q(...)``, so a hostile ``add_q`` would
    execute consumer code during validation if the type gate did not precede it.
    """
    from django.db.models import sql

    dispatched = []

    class _AddQSpy(sql.Query):
        def add_q(self, q):  # pragma: no cover - must never run
            dispatched.append(q)
            return super().add_q(q)

    result = models.QuerySet(model=Category)
    result._query = _AddQSpy(Category)
    result._deferred_filter = (False, (), {"name": "later"})
    _, defect = _seal_or_defect(result, Category, None)
    assert defect == ("untrusted", "QuerySet.query is _AddQSpy")
    assert dispatched == []


def test_deferred_filter_never_dispatches_instance_shadowed_inplace():
    """Resolving a pending deferred filter must not dispatch a shadowed inplace helper.

    An EXACT plain ``QuerySet`` whose ``_query`` is a genuine ``sql.Query`` clears the
    exact-type gate, but its instance ``__dict__`` shadows ``_filter_or_exclude_inplace``
    (a non-data descriptor, so the instance entry wins over the class method even for an
    exact ``QuerySet``). Django's ``QuerySet.query`` getter would dispatch that shadow to
    run consumer code mid-seal; the seal must NOT -- it bakes the predicate through the
    unbound ``sql.Query.add_q`` and never looks the helper up on the candidate. The spy
    must never fire, and the clean genuine query still seals with the predicate baked in.
    """
    dispatched = []

    def _spy_inplace(negate, args, kwargs):  # pragma: no cover - must never run
        dispatched.append((negate, args, kwargs))

    result = Category.objects.all()
    result._deferred_filter = (False, (), {"name": "later"})
    result.__dict__["_filter_or_exclude_inplace"] = _spy_inplace
    sealed, defect = _seal_or_defect(result, Category, None)
    assert dispatched == []
    assert defect is None
    sql_str, params = sealed.query.get_compiler(using="default").as_sql()
    assert "name" in sql_str
    assert "later" in params


def test_deferred_filter_never_dispatches_instance_shadowed_add_q():
    """A pending deferred filter over a query that shadows ``add_q`` never dispatches it.

    An EXACT plain ``QuerySet`` whose ``_query`` is a GENUINE ``sql.Query`` (clears the
    exact-type gate) but whose query ``__dict__`` shadows ``add_q`` must fail closed on
    the pre-bake genuineness walk BEFORE the predicate is baked. Baking runs
    ``sql.Query.add_q(query, ...)`` unbound, whose own call tree dispatches ``self.*`` --
    so the query must be proven shadow-free first. The shadow spy must never fire.
    """
    from django.db.models import sql

    dispatched = []

    def _spy_add_q(q):  # pragma: no cover - must never run
        dispatched.append(q)

    query = sql.Query(Category)
    query.__dict__["add_q"] = _spy_add_q
    result = models.QuerySet(model=Category)
    result._query = query
    result._deferred_filter = (False, (), {"name": "later"})
    _, defect = _seal_or_defect(result, Category, None)
    assert defect == ("untrusted", "query instance shadows the 'add_q' method")
    assert dispatched == []


def test_malformed_deferred_filter_fails_closed_instead_of_leaking():
    """A malformed ``_deferred_filter`` fails closed as ``untrusted``, never raises.

    An EXACT plain ``QuerySet`` with a genuine ``sql.Query`` but a hand-crafted
    ``_deferred_filter`` naming a nonexistent field -- a shape Django never
    produces -- passes the exact-``sql.Query`` gate, so resolution is attempted and
    the unbound ``sql.Query.add_q`` raises a raw ``FieldError``. The seal wraps the
    resolution so that raw exception becomes a typed ``untrusted`` defect instead of
    leaking past the boundary's typed defect contract.
    """
    result = Category.objects.all()
    result._deferred_filter = (False, (), {"nonexistent_field": 1})
    sealed, defect = _seal_or_defect(result, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet carries a deferred filter that cannot be resolved")


@pytest.mark.django_db
def test_related_manager_queryset_seals_and_scopes_to_its_parent():
    """A related-manager queryset seals and its baked relation predicate is preserved.

    ``instance.rel.all()`` reaches the seal as an EXACT plain ``QuerySet`` whose
    relation predicate is still a pending ``_deferred_filter``; the seal resolves
    it and rebuilds a fresh queryset that selects ONLY the parent's children. Two
    parents each get a child; sealing parent A's ``items.all()`` and evaluating it
    must return A's child alone (a lost predicate would leak B's child too).
    """
    parent_a = Category.objects.create(name="RelParentA")
    parent_b = Category.objects.create(name="RelParentB")
    item_a = Item.objects.create(name="ChildA", category=parent_a)
    Item.objects.create(name="ChildB", category=parent_b)
    sealed, defect = _seal_or_defect(parent_a.items.all(), Item, None)
    assert defect is None
    assert type(sealed) is models.QuerySet
    assert list(sealed) == [item_a]


def test_values_projection_result_fails_closed_on_read_surface():
    """A hook returning a ``.values()`` projection fails closed on a read surface.

    A read surface composes over model rows; a ``.values()`` return yields dicts,
    not ``Category`` instances. ``require_model_rows`` (the default) rejects it.
    """
    hook = _sync_hook_type(Category.objects.values("name"))
    with pytest.raises(ConfigurationError, match="the visibility contract composes over"):
        apply_type_visibility_sync(hook, Category.objects.all(), info=None)


def test_injected_custom_iterable_result_fails_closed():
    """A hook result with a hostile ``_iterable_class`` (custom row synthesizer) fails closed.

    ``QuerySet.__init__`` resets ``_iterable_class`` to ``ModelIterable``, so the
    real attack injects a custom row iterable AFTER construction; a genuine
    ``_fetch_all`` would still call it, synthesizing rows the SQL never selected.
    The seal only carries forward one of Django's OWN row iterables, so a foreign
    iterable class cannot be sealed and fails closed with the ``untrusted``
    defect ("cannot be sealed") - not the ``projection`` code (that stays for a
    genuine ``.values()`` projection).
    """
    injected = Category.objects.filter(name="visible")
    injected._iterable_class = list
    with pytest.raises(ConfigurationError, match="cannot be sealed"):
        apply_type_visibility_sync(_sync_hook_type(injected), Category.objects.all(), info=None)


def test_values_projection_source_fails_closed_on_read_surface():
    """A ``.values()`` SOURCE is rejected on a read surface before the hook runs."""
    with pytest.raises(ConfigurationError, match="the visibility contract composes over"):
        apply_type_visibility_sync(_SyncType, Category.objects.values("name"), info=None)


def test_spoofed_base_table_over_frozen_alias_map_fails_closed():
    """A queryset that bakes ``Item``'s alias map then spoofs its model to ``Category`` fails closed.

    ``QuerySet.model`` / ``Query.model`` are mutable and only govern SQL until
    the alias map is initialized; afterwards the base table is frozen there.
    A hostile queryset bakes its alias map against ``Item``, then reassigns both
    model attributes to the registered ``Category`` so every metadata check
    passes - while its SQL still reads ``Item``'s table. The boundary reads the
    authoritative base table from ``Query.alias_map`` and rejects the mismatch.
    Baking the alias map composes lazy query state only; no SQL runs.
    """

    def _spoof(cls, queryset, info):
        hostile = Item.objects.all()
        hostile.query.get_initial_alias()  # freeze the alias map against Item's table
        hostile.model = Category
        hostile.query.model = Category
        return hostile

    with pytest.raises(ConfigurationError, match=Item._meta.db_table):
        apply_type_visibility_sync(_stub_type(Category, _spoof), Category.objects.all(), info=None)


def test_baked_alias_map_matching_table_is_accepted():
    """A queryset whose alias map is already baked against the CORRECT table passes.

    The base-table check reads the frozen alias map; when it agrees with the
    registered model's concrete table there is no defect. Baking composes lazy
    query state only; no SQL runs.
    """
    baked = Category.objects.all()
    baked.query.get_initial_alias()  # freeze the alias map against Category's table
    result = apply_type_visibility_sync(_sync_hook_type(baked), Category.objects.all(), info=None)
    assert result.model is Category


def test_malformed_non_model_query_model_fails_closed_typed():
    """A non-model ``QuerySet.model`` fails as a typed ``ConfigurationError``, not ``AttributeError``.

    Direct ``._meta.concrete_model`` access on a spoofed non-model attribute
    would leak a raw ``AttributeError`` past the boundary's error contract;
    ``_concrete_or_none`` folds it into the fail-closed table defect instead.
    """

    def _malformed(cls, queryset, info):
        hostile = Category.objects.all()
        hostile.model = object()
        return hostile

    with pytest.raises(ConfigurationError, match="concrete table"):
        apply_type_visibility_sync(
            _stub_type(Category, _malformed),
            Category.objects.all(),
            info=None,
        )


def test_cross_model_union_source_fails_closed():
    """A cross-model ``union()`` SOURCE (not just a hook return) fails closed.

    The recursive branch check inspects the source too: a union whose branch
    reads ``Item``'s table cannot seed a ``Category`` visibility resolution.
    """
    hostile = Category.objects.all().union(Item.objects.all())
    with pytest.raises(ConfigurationError, match="concrete table"):
        apply_type_visibility_sync(_SyncType, hostile, info=None)


def test_manager_result_degrading_to_list_fails_closed():
    """A hook returning a Manager whose ``.all()`` yields a list fails closed (never a bypass)."""

    class _ListManager(models.Manager):
        def all(self):
            return ["secret"]

    manager = _ListManager()
    manager.model = Category
    manager._db = None
    with pytest.raises(ConfigurationError, match="must produce a QuerySet"):
        apply_type_visibility_sync(_sync_hook_type(manager), Category.objects.all(), info=None)


def _alias_drift_manager(explicit):
    """A Manager pinned to ``explicit`` whose ``.all()`` drifts to a different alias."""

    class _DriftManager(models.Manager):
        def get_queryset(self):
            return Category.objects.using("elsewhere")

    manager = _DriftManager()
    manager.model = Category
    manager._db = explicit
    return manager


def test_manager_result_alias_drift_fails_closed_sync():
    """A hook Manager pinned to ``other`` whose ``.all()`` routes to ``elsewhere`` fails closed.

    Even with an unpinned source (no required alias yet), the Manager's own
    explicit routing must be preserved by ``.all()`` - a silent cross-database
    move is a leak. Alias state only; no SQL runs on either phantom alias.
    """
    manager = _alias_drift_manager("other")
    with pytest.raises(ConfigurationError, match="preserve the manager's explicit routing"):
        apply_type_visibility_sync(_sync_hook_type(manager), Category.objects.all(), info=None)


def test_hostile_foreign_query_type_name_cannot_escape_typed_defect():
    """A foreign query metaclass cannot replace the typed boundary error with a raw one."""
    from django.db.models import sql

    class _ExplodingMeta(type):
        def __getattribute__(cls, name):
            if name in {"__name__", "__qualname__", "__module__"}:
                raise RuntimeError("hostile type-name read")
            return super().__getattribute__(name)

    class _HostileQuery(sql.Query, metaclass=_ExplodingMeta):
        pass

    source = Category.objects.all()
    source._query = _HostileQuery(Category)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet.query is object")


def test_hostile_manager_routing_metadata_cannot_escape_coercion_boundary():
    """Manager routing failures become a typed coercion error, not a raw exception."""

    class _HostileManager(models.Manager):
        def __getattribute__(self, name):
            if name == "_db":
                raise RuntimeError("hostile manager routing read")
            return super().__getattribute__(name)

    manager = _HostileManager()
    manager.model = Category
    with pytest.raises(ConfigurationError, match="could not produce a QuerySet"):
        normalize_query_source(manager)


def test_unrouted_manager_result_self_routing_fails_closed():
    """An UNROUTED hook Manager whose ``.all()`` self-routes fails closed (must stay unrouted)."""
    manager = _alias_drift_manager(None)
    with pytest.raises(ConfigurationError, match="preserve the manager's explicit routing"):
        apply_type_visibility_sync(_sync_hook_type(manager), Category.objects.all(), info=None)


async def test_manager_result_alias_drift_fails_closed_async():
    """The async runner enforces the same Manager alias preservation as the sync runner."""
    manager = _alias_drift_manager("other")
    with pytest.raises(ConfigurationError, match="preserve the manager's explicit routing"):
        await apply_type_visibility_async(
            _sync_hook_type(manager),
            Category.objects.all(),
            info=None,
        )


async def test_predicate_dropping_override_result_is_neutralized_async():
    """The async runner seals an override-subclass hook result, same as the sync runner."""

    class _DropFilter(models.QuerySet):
        def all(self):
            return Category.objects.all()

    shaped = models.QuerySet.filter(_DropFilter(model=Category), name="visible")
    hook = _stub_type(Category, lambda cls, qs, info: shaped)
    result = await apply_type_visibility_async(hook, Category.objects.all(), info=None)
    assert type(result) is models.QuerySet
    assert "visible" in str(result.query)


# ---------------------------------------------------------------------------
# Row-survival proof of the seal: an instance-shadowed refresh / query-level
# clone attack cannot widen the served rows (Decisions 1-2, asserting
# WHICH ROWS SURVIVE rather than only the composed query text).
# ---------------------------------------------------------------------------


def _shadowed_all_hook(cls, qs, info):
    """Return a plain visible-only queryset whose instance ``all`` is predicate-dropping."""
    source = Category.objects.filter(is_private=False)
    source.all = lambda: Category.objects.all()  # instance shadow (would drop the predicate)
    return source


def _shadowed_chain_hook(cls, qs, info):
    """Return a plain visible-only queryset whose ``query.chain`` is instance-replaced."""
    source = Category.objects.filter(is_private=False)
    unfiltered = Category.objects.all().query
    source.query.chain = lambda *args, **kwargs: unfiltered  # instance shadow
    return source


@pytest.mark.django_db
def test_instance_shadowed_all_hook_serves_only_visible_rows_sync():
    """A hook whose instance ``.all()`` is shadowed still serves only the visible rows (sync).

    The seal reads state from ``__dict__`` via ``object.__getattribute__``, never
    calling ``.all()``, so the shadow is inert - only ``is_private=False`` rows survive.
    """
    Category.objects.create(name="visible_row", is_private=False)
    Category.objects.create(name="hidden_row", is_private=True)
    result = apply_type_visibility_sync(
        _stub_type(Category, _shadowed_all_hook),
        Category.objects.all(),
        info=None,
    )
    assert set(result.values_list("is_private", flat=True)) == {False}
    assert sorted(result.values_list("name", flat=True)) == ["visible_row"]


@pytest.mark.django_db(transaction=True)
async def test_instance_shadowed_all_hook_serves_only_visible_rows_async():
    """Sync/async parity: the async runner seals the instance-shadowed ``.all()`` too."""
    await Category.objects.acreate(name="visible_row", is_private=False)
    await Category.objects.acreate(name="hidden_row", is_private=True)
    result = await apply_type_visibility_async(
        _stub_type(Category, _shadowed_all_hook),
        Category.objects.all(),
        info=None,
    )
    names = [row.name async for row in result]
    assert names == ["visible_row"]


def test_query_chain_shadow_hook_fails_closed_sync():
    """A hook whose ``query.chain`` is instance-replaced FAILS CLOSED (spec-045 Decision 2).

    ``sql.Query.clone`` shallow-copies the source ``Query.__dict__``, so an
    instance ``chain`` shadow would ride into the sealed query and dispatch on the
    first post-seal ``QuerySet._clone()`` / transform, erasing the predicate. The
    structural no-shadow check rejects ANY ``__dict__`` key naming a callable
    ``sql.Query`` method, so the seal fails closed with the typed ``untrusted``
    error rather than serving the shadow's rows.
    """
    with pytest.raises(ConfigurationError, match="cannot be sealed"):
        apply_type_visibility_sync(
            _stub_type(Category, _shadowed_chain_hook),
            Category.objects.all(),
            info=None,
        )


def test_query_shadow_defect_is_name_agnostic():
    """The no-shadow check rejects any shadowed ``sql.Query`` method, not just ``chain``.

    Proves the fix is structural (spec-045 Decision 2: "do not fix only the
    literal ``chain`` name") -- a shadowed ``get_compiler`` fails closed identically.
    """
    source = Category.objects.filter(is_private=False)
    source.query.get_compiler = lambda *a, **k: None  # shadow a different Query method
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("untrusted", "query instance shadows the 'get_compiler' method")


@pytest.mark.django_db
def test_clean_queryset_transforms_after_seal():
    """A clean (unshadowed) queryset seals fine and keeps composing post-seal.

    The complement of the fail-closed shadow tests: once sealed, an ordinary
    queryset still transforms normally -- ``values_list`` keeps the visibility
    predicate and serves only the visible rows.
    """
    Category.objects.create(name="visible_row", is_private=False)
    Category.objects.create(name="hidden_row", is_private=True)
    result = apply_type_visibility_sync(
        _sync_hook_type(Category.objects.filter(is_private=False)),
        Category.objects.all(),
        info=None,
    )
    assert "is_private" in str(result.values_list("name").query)
    assert sorted(result.values_list("name", flat=True)) == ["visible_row"]


def test_additive_only_subclass_result_is_sealed_to_plain_queryset():
    """A subclass that only ADDS methods is now accepted but returns a SEALED plain QuerySet.

    The old contract passed an additive-only subclass through unchanged (same
    object, same class). The sealed-execution contract instead rebuilds a plain
    ``QuerySet`` from the validated query state: the subclass identity is
    deliberately dropped (it is not needed to select rows), while the SQL
    predicate is preserved. This closes the vector where an "additive-only"
    subclass could still override an unlisted downstream method.
    """

    class _AddOnly(models.QuerySet):
        def published(self):  # additive only
            return self.filter(name="published")

    shaped = _AddOnly(model=Category).filter(name="ok")
    result = apply_type_visibility_sync(_sync_hook_type(shaped), Category.objects.all(), info=None)
    assert type(result) is models.QuerySet  # sealed - no longer an _AddOnly instance
    assert not isinstance(result, _AddOnly)
    assert "ok" in str(result.query)


def test_hook_exception_propagates_unchanged():
    """An exception raised INSIDE the hook propagates as-is - the boundary never masks it."""

    class _BoomError(RuntimeError):
        pass

    def _raise(cls, queryset, info):
        raise _BoomError("consumer bug")

    with pytest.raises(_BoomError, match="consumer bug"):
        apply_type_visibility_sync(_stub_type(Category, _raise), Category.objects.all(), info=None)


# ---------------------------------------------------------------------------
# The hardened visibility boundary -- objects embedded in the query graph
# consumer objects can ride through the seal one edge down: a ``Prefetch``
# queryset and a combinator-branch ``Query`` subclass
# ---------------------------------------------------------------------------


def _identity_hook_type():
    """A Category stub whose hook returns its argument (the sealed source) verbatim."""
    return _stub_type(Category, lambda cls, queryset, info: queryset)


def test_hostile_prefetch_queryset_is_neutralized_to_plain():
    """A ``Prefetch`` carrying a hostile ``QuerySet`` subclass is sealed to a plain child.

    At evaluation Django dispatches into a prefetch queryset's own
    ``_fetch_all`` / ``__iter__`` to populate the related descriptor, so a
    hostile subclass could seed a synthetic in-memory row the SQL never selected
    (the exact vector the seal exists to kill, one edge down the object graph).
    The seal recursively rebuilds each ``Prefetch`` with a plain child queryset -
    the subclass identity of both the inner queryset AND the ``Prefetch`` wrapper
    is dropped - so the hostile ``_fetch_all`` is never dispatched.
    """
    from django.db.models import Prefetch

    class _HostileItemQS(models.QuerySet):
        def _fetch_all(self):  # pragma: no cover - never dispatched after sealing
            self._result_cache = [Item(name="SYNTHETIC-HIDDEN")]

    hostile = _HostileItemQS(model=Item).filter(name="real")
    source = Category.objects.all().prefetch_related(Prefetch("items", queryset=hostile))
    sealed = apply_type_visibility_sync(_identity_hook_type(), source, info=None)
    (entry,) = sealed._prefetch_related_lookups
    assert type(entry) is Prefetch  # rebuilt wrapper, subclass identity dropped
    assert type(entry.queryset) is models.QuerySet  # plain child - hostile subclass dropped
    assert "real" in str(entry.queryset.query)  # the genuine predicate survives


@pytest.mark.django_db
def test_hostile_prefetch_synthetic_row_never_materializes():
    """Evaluating the sealed queryset runs Django's own prefetch - no synthetic row appears.

    The end-to-end proof of the neutralization: with the sealed queryset actually
    evaluated against the database, the ``to_attr`` list holds only the real
    related row the SQL selected. The hostile ``_fetch_all`` (which would seed a
    synthetic hidden row) is never dispatched because the sealed child is a plain
    ``QuerySet``.
    """
    from django.db.models import Prefetch

    category = Category.objects.create(name="c-real")
    Item.objects.create(name="item-real", category=category)

    class _HostileItemQS(models.QuerySet):
        def _fetch_all(self):  # pragma: no cover - never dispatched after sealing
            self._result_cache = [Item(name="SYNTHETIC-HIDDEN", category_id=category.pk)]

    hostile = _HostileItemQS(model=Item)
    source = Category.objects.filter(pk=category.pk).prefetch_related(
        Prefetch("items", queryset=hostile, to_attr="pf"),
    )
    sealed = apply_type_visibility_sync(_identity_hook_type(), source, info=None)
    (materialized,) = list(sealed)
    assert [item.name for item in materialized.pf] == ["item-real"]


def test_string_and_default_prefetch_lookups_pass_through():
    """Plain string lookups and a ``Prefetch`` with no queryset seal through unchanged.

    Only a ``Prefetch`` carrying a consumer queryset is a dispatch vector; a bare
    string lookup (Django builds the related queryset itself) and a
    ``Prefetch(queryset=None)`` carry no consumer code, so they pass through.
    """
    from django.db.models import Prefetch

    source = Category.objects.all().prefetch_related("items", Prefetch("items"))
    sealed = apply_type_visibility_sync(_identity_hook_type(), source, info=None)
    string_lookup, default_prefetch = sealed._prefetch_related_lookups
    assert string_lookup == "items"
    assert isinstance(default_prefetch, Prefetch)
    assert default_prefetch.queryset is None


def test_prefetch_with_non_queryset_queryset_fails_closed():
    """A ``Prefetch`` whose ``.queryset`` is not a QuerySet cannot be sealed - fail closed.

    ``Prefetch.__init__`` only rejects a queryset that advertises a non-model
    ``_iterable_class``; a plain object slips construction, so the seal must
    reject a non-queryset child rather than trust it.
    """
    from django.db.models import Prefetch

    source = Category.objects.all().prefetch_related(Prefetch("items", queryset=object()))
    with pytest.raises(ConfigurationError, match="cannot be sealed"):
        apply_type_visibility_sync(_SyncType, source, info=None)


def test_prefetch_with_foreign_inner_query_fails_closed():
    """A ``Prefetch`` child whose ``_query`` is a foreign ``Query`` subclass fails closed.

    The child seal applies the same exact-``sql.Query`` discipline as the outer
    seal, so an unsealable child fails the whole seal closed (never silently
    dropped, which would evaluate a default child and hide the tampering).
    """
    from django.db.models import Prefetch, sql

    class _ForeignQuery(sql.Query):
        pass

    inner = Item.objects.filter(name="x")
    prefetch = Prefetch("items", queryset=inner)
    inner._query = _ForeignQuery(Item)
    source = Category.objects.all().prefetch_related(prefetch)
    with pytest.raises(ConfigurationError, match="cannot be sealed"):
        apply_type_visibility_sync(_SyncType, source, info=None)


def test_combined_query_foreign_branch_subclass_fails_closed():
    """A ``combined_queries`` branch that is a foreign ``Query`` SUBCLASS fails closed.

    The outer exact-``sql.Query`` check never reaches the branches, yet
    ``sql.Query.clone`` preserves them, so at compile time Django would call each
    branch's consumer-overridable SQL synthesis. The branch walk applies the same
    exact-type check to every branch, matching the outer discipline.
    """
    from django.db.models import sql

    class _HostileBranch(sql.Query):
        pass

    result = Category.objects.filter(name="a").union(Category.objects.filter(name="b"))
    result.query.combined_queries = (_HostileBranch(Category),)
    with pytest.raises(ConfigurationError, match="cannot be sealed"):
        apply_type_visibility_sync(_sync_hook_type(result), Category.objects.all(), info=None)


def test_sliced_source_fails_closed_with_typed_error():
    """A pre-sliced SOURCE fails closed with a typed ConfigurationError, not a raw TypeError.

    The hook and surface compose further filters / ordering onto the source, and
    Django forbids refiltering or reordering a sliced query. Without this check
    the next transform would raise a raw ``TypeError`` outside the typed defect
    contract (the cascade already rejects a sliced target subquery).
    """
    with pytest.raises(ConfigurationError, match="sliced"):
        apply_type_visibility_sync(_SyncType, Category.objects.all()[:5], info=None)


def test_sliced_hook_result_fails_closed_with_typed_error():
    """A hook returning a pre-sliced queryset fails closed with a typed error."""
    hook = _sync_hook_type(Category.objects.filter(name="visible")[:3])
    with pytest.raises(ConfigurationError, match="sliced"):
        apply_type_visibility_sync(hook, Category.objects.all(), info=None)


def test_seal_copies_hints_into_a_fresh_dict():
    """The sealed queryset's ``_hints`` is a distinct dict, never the candidate's own.

    Sharing the candidate's ``_hints`` would leave the sealed queryset holding a
    mutable dict the untrusted object can still write to - a routing-control
    surface when a custom router consults hints on an unrouted read.
    """
    source = Category.objects.all()
    hints = {"instance": object()}
    source._hints = hints
    sealed = apply_type_visibility_sync(_identity_hook_type(), source, info=None)
    assert sealed._hints == hints
    assert sealed._hints is not hints


@pytest.mark.django_db
def test_identity_hook_result_is_resealed_dropping_injected_cache_sync():
    """A hook that mutates the received source's ``_result_cache`` and returns it is re-sealed.

    Object identity is not immutability (spec-045 Decision 3): the removed
    identity fast path let a hook inject a synthetic unsaved row into the sealed
    source's ``_result_cache`` and return the SAME object, serving that row with
    zero SQL. The result is now ALWAYS re-sealed, so the returned queryset has
    ``_result_cache is None`` and only the real visible rows survive on evaluation.
    """
    Category.objects.create(name="visible_row", is_private=False)

    def _hook(cls, queryset, info):
        queryset._result_cache = [Category(name="synthetic-hidden", is_private=True)]
        return queryset

    result = apply_type_visibility_sync(
        _stub_type(Category, _hook),
        Category.objects.filter(is_private=False),
        info=None,
    )
    assert result._result_cache is None
    assert sorted(row.name for row in result) == ["visible_row"]


# ---------------------------------------------------------------------------
# The hardened visibility boundary -- embedded AST-node trust (Decision 2): every node
# ``sql.Query.clone`` clones or the compiler later executes
# must be a trusted Django implementation, else the seal fails closed.
# ---------------------------------------------------------------------------


def test_hostile_where_subclass_fails_closed():
    """A ``WhereNode`` SUBCLASS whose ``clone`` widens the query fails closed.

    ``sql.Query.clone`` dispatches ``self.where.clone()``; a consumer subclass
    could strip the predicate during sealing, so any non-exact ``WhereNode`` in
    the tree is rejected before the clone runs.
    """
    from django.db.models.sql.where import WhereNode

    class _WideningWhere(WhereNode):
        def clone(self):  # pragma: no cover - never dispatched; rejected first
            return WhereNode()

    source = Category.objects.filter(is_private=False)
    source.query.where = _WideningWhere()
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("untrusted", "where clause carries a _WideningWhere node")


def test_non_django_where_leaf_fails_closed():
    """A consumer (non-``django.``) leaf lurking in the where tree fails closed."""
    source = Category.objects.filter(is_private=False)
    source.query.where.children.append(object())
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("untrusted", "where clause carries a object node")


def test_hostile_annotation_expression_fails_closed():
    """A consumer annotation expression is not a trusted Django node - fail closed.

    The recursive genuineness walk reaches annotation values through
    ``_expr_graph_defect``, so a top-level consumer annotation is rejected with the
    unified ``carries a ... node`` wording (the same the where-tree and order-by
    walks use).
    """
    source = Category.objects.filter(is_private=False)
    source.query.annotations = {"x": object()}
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("untrusted", "annotation 'x' carries a object node")


def test_hostile_alias_join_fails_closed():
    """A non-Django join object in the alias map fails closed."""
    source = Category.objects.filter(is_private=False)
    source.query.alias_map = {**source.query.alias_map, "bogus": object()}
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("untrusted", "join for alias 'bogus' is a object")


def test_non_dict_select_related_fails_closed():
    """A ``select_related`` that is neither bool nor dict fails closed."""
    source = Category.objects.filter(is_private=False)
    source.query.select_related = object()
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("untrusted", "select_related is a object")


def test_non_str_select_related_key_fails_closed():
    """A ``select_related`` dict with a non-str key fails closed."""
    source = Category.objects.filter(is_private=False)
    source.query.select_related = {1: {}}
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("untrusted", "select_related key is a int")


def test_nested_select_related_value_fails_closed():
    """A nested ``select_related`` value that is not a dict tree fails closed."""
    source = Category.objects.filter(is_private=False)
    source.query.select_related = {"category": object()}
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("untrusted", "select_related is a object")


def test_clean_annotation_and_select_related_seal_fine():
    """A plain Django annotation + ``select_related`` dict tree seals with no defect.

    The complement of the fail-closed AST tests: trusted Django nodes (a ``Count``
    annotation, a ``{str: {}}`` select_related tree) pass the graph validation.
    """
    source = Item.objects.select_related("category").annotate(n=models.Count("id"))
    sealed, defect = _seal_or_defect(source, Item, None)
    assert defect is None
    assert type(sealed) is models.QuerySet


# ---------------------------------------------------------------------------
# The hardened visibility boundary -- under spec-045 Decision 5 a model-less select
# query escapes as malformed SQL, so it must fail closed as a table defect.
# ---------------------------------------------------------------------------


def test_query_model_none_fails_closed_as_table():
    """A result whose exact ``sql.Query.model`` is ``None`` fails closed as a table defect."""
    source = Category.objects.filter(name="x")
    source.query.model = None
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("table", "NoneType")


def test_combined_branch_missing_model_fails_closed_as_table():
    """A ``combined_queries`` branch with no model fails closed as a table defect."""
    source = Category.objects.filter(name="a").union(Category.objects.filter(name="b"))
    source.query.combined_queries[0].model = None
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("table", "NoneType")


# ---------------------------------------------------------------------------
# The hardened visibility boundary -- Prefetch rebuild + child-alias threading
# (Decision 4).
# ---------------------------------------------------------------------------


def test_prefetch_non_str_lookup_fails_closed():
    """A non-exact-``str`` prefetch lookup entry fails closed."""

    class _StrSub(str):
        pass

    _, defect = _sealed_prefetch_related_lookups((_StrSub("items"),), "X", None, Category)
    assert defect == ("untrusted", "X prefetch lookup is a _StrSub")


def test_prefetch_non_str_path_fails_closed():
    """A ``Prefetch`` whose ``prefetch_through`` is not an exact str fails closed."""
    from django.db.models import Prefetch

    pf = Prefetch("items")
    pf.__dict__["prefetch_through"] = object()
    _, defect = _sealed_prefetch_related_lookups((pf,), "X", None, Category)
    assert defect == ("untrusted", "X prefetch path is not an exact str")


def test_prefetch_non_str_to_attr_fails_closed():
    """A ``Prefetch`` whose ``to_attr`` is not an exact str / None fails closed."""
    from django.db.models import Prefetch

    pf = Prefetch("items")
    pf.__dict__["to_attr"] = object()
    _, defect = _sealed_prefetch_related_lookups((pf,), "X", None, Category)
    assert defect == ("untrusted", "X prefetch to_attr is not an exact str or None")


def test_prefetch_unrouted_child_inherits_outer_alias():
    """An unrouted prefetch child inherits the OUTER effective alias."""
    from django.db.models import Prefetch

    sealed, defect = _sealed_prefetch_related_lookups(
        (Prefetch("items", queryset=Item.objects.all()),),
        "X",
        "default",
        Category,
    )
    assert defect is None
    assert sealed[0].queryset._db == "default"


def test_prefetch_cross_alias_child_fails_closed():
    """A prefetch child pinned to a DIFFERENT alias than the outer fails closed."""
    from django.db.models import Prefetch

    _, defect = _sealed_prefetch_related_lookups(
        (Prefetch("items", queryset=Item.objects.using("other")),),
        "X",
        "default",
        Category,
    )
    # The inner child's own ``(code: detail)`` -- here the ``alias`` defect -- is
    # carried into the message rather than collapsed into a generic string.
    assert defect == ("untrusted", "X prefetch 'items' queryset cannot be sealed (alias: other)")


def test_sliced_prefetch_child_seals_successfully():
    """A legally sliced ``Prefetch`` child seals; the rebuilt child stays a plain, sliced qs.

    Django >= 4.2 supports a sliced prefetch queryset (top-N per parent). Nothing
    refilters a prefetch child, so the outer ``sliced`` rejection does not apply one
    edge down; the child seals under ``_PREFETCH_CHILD_POLICY`` (``reject_sliced``
    off) while still requiring model rows, and the rebuilt child is a fresh plain
    ``QuerySet`` whose slice marks are preserved.
    """
    from django.db.models import Prefetch

    sealed, defect = _sealed_prefetch_related_lookups(
        (Prefetch("items", queryset=Item.objects.all()[:5]),),
        "X",
        None,
        Category,
    )
    assert defect is None
    child = sealed[0].queryset
    assert type(child) is models.QuerySet
    assert child.query.is_sliced
    assert child.query.high_mark == 5


def test_prefetch_child_defect_detail_appears_in_message():
    """A prefetch child's inner defect ``(code: detail)`` is surfaced, not masked.

    A child whose ``_query`` is a foreign ``Query`` subclass fails the child seal
    with the ``untrusted`` defect; that inner code + detail is carried into the
    outer message so the failure is diagnosable rather than a generic string.
    """
    from django.db.models import Prefetch, sql

    class _ForeignInnerQuery(sql.Query):
        pass

    inner = Item.objects.all()
    inner._query = _ForeignInnerQuery(Item)
    _, defect = _sealed_prefetch_related_lookups(
        (Prefetch("items", queryset=inner),),
        "X",
        None,
        Category,
    )
    code, detail = defect
    assert code == "untrusted"
    assert (
        detail
        == "X prefetch 'items' queryset cannot be sealed (untrusted: QuerySet.query is _ForeignInnerQuery)"
    )


# ---------------------------------------------------------------------------
# The hardened visibility boundary -- awaitable discipline
# ---------------------------------------------------------------------------


class _AwaitableOf:
    """A custom (non-coroutine) awaitable resolving to a fixed value."""

    def __init__(self, value):
        self.value = value

    def __await__(self):
        return self.value
        yield  # pragma: no cover - marks this as a generator function


def test_sync_boundary_rejects_custom_awaitable_hook():
    """A custom awaitable at the sync boundary raises ``SyncMisuseError`` (not a coroutine)."""
    hook = _stub_type(Category, lambda cls, qs, info: _AwaitableOf(qs))
    with pytest.raises(SyncMisuseError, match="returned an awaitable in a sync"):
        apply_type_visibility_sync(hook, Category.objects.all(), info=None)


async def test_async_custom_awaitable_hook_is_awaited_once():
    """The async runner awaits a custom awaitable hook return to its queryset."""
    hook = _stub_type(Category, lambda cls, qs, info: _AwaitableOf(qs))
    result = await apply_type_visibility_async(hook, Category.objects.all(), info=None)
    assert isinstance(result, models.QuerySet)


async def test_async_nested_awaitable_fails_closed():
    """An async hook resolving to ANOTHER awaitable fails closed after exactly one await."""

    class _NestedType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

        @classmethod
        async def get_queryset(cls, queryset, info):
            async def _inner():
                return queryset  # pragma: no cover - disposed, never awaited

            return _inner()

    with pytest.raises(ConfigurationError, match="nested awaitable"):
        await apply_type_visibility_async(_NestedType, Category.objects.all(), info=None)


async def test_async_generator_hook_result_fails_closed():
    """An async hook resolving to an async generator is not awaitable - a type rejection."""

    class _AgenType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

        @classmethod
        async def get_queryset(cls, queryset, info):
            return _async_generator_result()

    with pytest.raises(ConfigurationError, match="got async_generator"):
        await apply_type_visibility_async(_AgenType, Category.objects.all(), info=None)


async def test_post_process_async_rejects_residual_awaitable():
    """An already-awaited async consumer resolver resolving to another awaitable fails closed.

    This closes the shape where the residual awaitable would otherwise pass
    the non-queryset branch and skip visibility entirely.
    """

    async def _residual():
        return Category.objects.all()  # pragma: no cover - disposed, never awaited

    with pytest.raises(ConfigurationError, match="resolved to another awaitable"):
        await post_process_queryset_result_async(_SyncType, _residual(), info=None)


@pytest.mark.django_db(transaction=True)
async def test_identity_hook_result_is_resealed_dropping_injected_cache_async():
    """Sync/async parity: the async runner also re-seals an identity return.

    An async hook injects a synthetic unsaved row into the received sealed
    source's ``_result_cache`` and returns the SAME object; the async runner
    re-seals it, dropping the cache, so only the real visible row survives.
    """
    await Category.objects.acreate(name="visible_row", is_private=False)

    class _CaptureAsyncType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

        @classmethod
        async def get_queryset(cls, queryset, info):
            queryset._result_cache = [Category(name="synthetic-hidden", is_private=True)]
            return queryset

    result = await apply_type_visibility_async(
        _CaptureAsyncType,
        Category.objects.filter(is_private=False),
        info=None,
    )
    assert result._result_cache is None
    names = [row.name async for row in result]
    assert names == ["visible_row"]


# ---------------------------------------------------------------------------
# Decision 2: sql.Query.clone and
# add_q are NOT no-dispatch boundaries -- their bodies dispatch bound methods on
# the graph's sub-objects. The seal now proves EVERY compiler-reachable node is a
# genuine, unshadowed Django implementation (by object identity, not __module__)
# and bakes a deferred filter onto a DETACHED clone, so clone / add_q / compile
# dispatch only trusted code and the candidate is never mutated.
# ---------------------------------------------------------------------------


def test_exact_wherenode_shadowed_clone_never_dispatches():
    """An EXACT ``WhereNode`` whose ``__dict__`` shadows ``clone`` fails closed.

    ``sql.Query.clone`` dispatches ``self.where.clone()``. A non-data-descriptor
    shadow on an exact ``WhereNode`` instance would win over the class method and,
    if dispatched, could return an empty node and strip the visibility predicate
    (the reproduced vector: the shadow fired mid-seal and the sealed SQL lost its
    WHERE). The pre-clone shadow walk rejects it before any clone runs.
    """
    from django.db.models.sql.where import WhereNode

    fired = []

    def _spy_clone():  # pragma: no cover - must never run
        fired.append("clone")
        return WhereNode()

    source = Category.objects.filter(is_private=False)
    str(source.query)
    source.query.where.__dict__["clone"] = _spy_clone
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "where node shadows the 'clone' method")
    assert fired == []


def test_shadowed_leaf_as_sql_never_dispatches():
    """An exact Django lookup leaf whose ``__dict__`` shadows ``as_sql`` fails closed.

    Exact-type discipline on the leaf is not enough: a non-data-descriptor shadow
    of ``as_sql`` on an otherwise-genuine ``Value`` / lookup would be dispatched at
    compile time. The recursive leaf walk shadow-checks every node.
    """
    from django.db.models import Value

    fired = []

    def _spy_as_sql(compiler, connection):  # pragma: no cover - must never run
        fired.append("as_sql")
        return "1", []

    source = Category.objects.filter(name="keep")
    str(source.query)
    leaf = source.query.where.children[0]
    leaf.rhs = Value("keep")
    leaf.rhs.__dict__["as_sql"] = _spy_as_sql
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "where clause shadows the 'as_sql' method")
    assert fired == []


def test_lookup_direct_rhs_attribute_hook_never_dispatches():
    """A direct lookup RHS carrying an attribute hook fails closed, hook unfired.

    Discovering a lookup's children through ``get_source_expressions`` would call
    ``rhs_is_direct_value`` -> ``hasattr(self.rhs, "as_sql")``, running the RHS
    object's own ``__getattr__`` while the query is still un-cloned; and a direct
    RHS is then omitted from the returned operands entirely. The raw ``lhs`` /
    ``rhs`` walk classifies the value statically instead.
    """
    fired = []

    class _HookedRhs:
        def __init__(self, log):
            self.log = log

        def __getattr__(self, name):  # pragma: no cover - must never run
            self.log.append(name)
            return None

    source = Category.objects.filter(name="keep")
    str(source.query)
    source.query.where.children[0].rhs = _HookedRhs(fired)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == (
        "untrusted",
        "where clause lookup rhs defines the '__getattr__' attribute hook",
    )
    assert fired == []


def test_lookup_direct_rhs_plain_object_fails_closed():
    """A direct lookup RHS that is not plain query data fails closed.

    An arbitrary object reaches the database adapter as a bound parameter; only values
    descending from a plain-data base are admitted.
    """

    class _PlainRhs:
        """Hookless, but no plain-data ancestry."""

    source = Category.objects.filter(name="keep")
    str(source.query)
    source.query.where.children[0].rhs = _PlainRhs()
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "where clause lookup rhs is a _PlainRhs")


def test_lookup_direct_rhs_sequence_members_are_walked():
    """An ``__in`` lookup's direct RHS list is walked member-wise.

    The sequence itself is plain state, so each member is proven under the same
    direct-RHS rule; a hostile member fails the whole seal closed.
    """
    source = Category.objects.filter(pk__in=[1, 2])
    str(source.query)
    assert type(source.query.where.children[0].rhs) is list
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert type(sealed) is models.QuerySet

    hostile = Category.objects.filter(pk__in=[1, 2])
    str(hostile.query)
    hostile.query.where.children[0].rhs = [1, object()]
    sealed, defect = _seal_or_defect(hostile, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "where clause lookup rhs is a object")


def test_lookup_direct_rhs_enum_member_seals():
    """A ``TextChoices`` member in RHS position is plain query data and seals cleanly.

    Enum members are ``str`` / ``int`` SUBCLASSES, so the exact-type inert rule that
    governs expression leaves would fail-close ordinary consumer schemas here; a direct
    RHS is admitted on plain-data ancestry plus the absence of its own attribute hooks.
    """

    class _SealChoices(models.TextChoices):
        KEEP = "keep", "Keep"

    source = Category.objects.filter(name=_SealChoices.KEEP)
    str(source.query)
    assert type(source.query.where.children[0].rhs) is _SealChoices
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert type(sealed) is models.QuerySet


def test_lookup_direct_rhs_date_subclass_normalizes_to_exact_date():
    """A date-subclass RHS is bound as an EXACT ``datetime.date``, its override unfired.

    Admitting a plain-data subclass is not retaining it. Django and the database adapter
    invoke ordinary methods on a bound parameter (``str(value)`` during date adaptation,
    ``__int__`` / ``__index__``, an adapter hook), none of which an attribute-hook scan
    can enumerate, so a subclass instance left in the sealed query would run consumer code
    at compile time and could change the bound visibility value AFTER sealing. Canonical
    reconstruction replaces it with a framework-owned exact ``datetime.date`` whose
    methods are the interpreter's own.
    """
    fired = []

    class _LoudDate(datetime.date):
        def __str__(self):  # pragma: no cover - must never run
            fired.append("__str__")
            return "1999-12-31"

    source = Category.objects.filter(created_date__date=_LoudDate(2020, 1, 2))
    assert type(source.query.where.children[0].rhs) is _LoudDate
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    sealed_rhs = sealed.query.where.children[0].rhs
    assert type(sealed_rhs) is datetime.date
    assert sealed_rhs == datetime.date(2020, 1, 2)
    assert fired == []

    expected = Category.objects.filter(created_date__date=datetime.date(2020, 1, 2))
    assert sealed.query.sql_with_params() == expected.query.sql_with_params()
    assert fired == []
    # The candidate keeps its own value: normalization applies to the sealed query only.
    assert type(source.query.where.children[0].rhs) is _LoudDate


def test_lookup_direct_rhs_str_subclass_normalizes_to_exact_str():
    """A ``TextChoices`` member RHS binds as an exact ``str`` with unchanged SQL.

    Enum members are ``str`` / ``int`` SUBCLASSES, so normalizing one to its underlying
    exact scalar keeps the bound parameter byte-identical while removing every
    consumer-defined method from the compile path.
    """

    class _NormChoices(models.TextChoices):
        KEEP = "keep", "Keep"

    source = Category.objects.filter(name=_NormChoices.KEEP)
    assert type(source.query.where.children[0].rhs) is _NormChoices
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    sealed_rhs = sealed.query.where.children[0].rhs
    assert type(sealed_rhs) is str
    assert sealed_rhs == "keep"

    expected = Category.objects.filter(name="keep")
    assert sealed.query.sql_with_params() == expected.query.sql_with_params()


def test_lookup_direct_rhs_property_shadowed_subclass_normalizes_safely():
    """A subclass PROPERTY shadowing a base field name never runs during normalization.

    A plain-data subclass can shadow ``year`` (or any other field name) with a property
    even though it defines no attribute hook, so normalization reads the BASE type's own
    slot descriptors explicitly rather than by attribute name -- the shadowing property is
    never resolved, and the exact value rebuilt from the base slots is the one the
    interpreter itself would report.
    """
    fired = []

    class _ShadowedDate(datetime.date):
        @property
        def year(self):  # pragma: no cover - must never run
            fired.append("year")
            return 1999

        @property
        def month(self):  # pragma: no cover - must never run
            fired.append("month")
            return 12

        @property
        def day(self):  # pragma: no cover - must never run
            fired.append("day")
            return 31

    source = Category.objects.filter(created_date__date=_ShadowedDate(2020, 1, 2))
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    sealed_rhs = sealed.query.where.children[0].rhs
    assert type(sealed_rhs) is datetime.date
    assert sealed_rhs == datetime.date(2020, 1, 2)
    assert fired == []


def test_lookup_direct_rhs_every_plain_data_base_normalizes_to_its_exact_type():
    """Every admitted plain-data base normalizes to the exact inert type of that base.

    One member per base, carried in an ``__in`` sequence so the whole set is proven and
    reconstructed in a single seal. Each rebuilt value is an exact inert type and compares
    equal to the subclass instance it replaced, so the bound parameter is unchanged while
    every consumer-defined method leaves the compile path. ``bool`` is absent because it
    cannot be subclassed, and a model instance is the bound value itself so it is retained.
    """

    class _Str(str):
        pass

    class _Bytes(bytes):
        pass

    class _ByteArray(bytearray):
        pass

    class _Int(int):
        pass

    class _Float(float):
        pass

    class _Complex(complex):
        pass

    class _Dec(Decimal):
        pass

    class _DateTime(datetime.datetime):
        pass

    class _Time(datetime.time):
        pass

    class _Delta(datetime.timedelta):
        pass

    class _Uuid(uuid.UUID):
        pass

    class _PlainChoices(enum.Enum):
        KEEP = "keep"

    members = [
        _Str("keep"),
        _Bytes(b"keep"),
        _ByteArray(b"keep"),
        _Int(3),
        _Float(1.5),
        _Complex(1, 2),
        _Dec("1.50"),
        _DateTime(2020, 1, 2, 3, 4, 5, 6),
        _Time(3, 4, 5, 6),
        _Delta(days=1, seconds=2, microseconds=3),
        _Uuid(int=5),
        _PlainChoices.KEEP,
    ]
    expected_types = [
        str,
        bytes,
        bytearray,
        int,
        float,
        complex,
        Decimal,
        datetime.datetime,
        datetime.time,
        datetime.timedelta,
        uuid.UUID,
        str,
    ]

    source = Category.objects.filter(name__in=["keep"])
    str(source.query)
    source.query.where.children[0].rhs = members
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    sealed_rhs = sealed.query.where.children[0].rhs
    assert [type(item) for item in sealed_rhs] == expected_types
    assert sealed_rhs[:11] == members[:11]
    assert sealed_rhs[11] == "keep"


def test_lookup_direct_rhs_unnormalizable_enum_member_fails_closed():
    """An enum member whose underlying value is not inert data fails the seal closed.

    A hookless ``enum.Enum`` member with no scalar base is normalized to its ``_value_``,
    read straight from the member's instance state. When that value cannot itself be
    reduced to an exact inert leaf there is no framework-owned parameter to bind, so the
    seal reports a typed defect rather than retaining the member by reference.
    """

    class _OpaqueValue:
        """Plain data to the enum machinery, not an inert bound parameter."""

    class _OpaqueChoices(enum.Enum):
        KEEP = _OpaqueValue()

    source = Category.objects.filter(name="keep")
    str(source.query)
    source.query.where.children[0].rhs = _OpaqueChoices.KEEP
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet binds a _OpaqueValue bound value")


def test_lookup_expression_rhs_still_recurses():
    """A hostile expression hidden in lookup-RHS position fails closed.

    An RHS whose type exposes ``as_sql`` is what Django dispatches at compile time, so
    it recurses through the ordinary expression walk rather than the inert-data rules.
    """
    fired = []

    class _HostileRhs(models.Func):
        def as_sql(self, compiler, connection):  # pragma: no cover - must never run
            fired.append("rhs.as_sql")
            return "1", []

    source = Category.objects.filter(name="keep")
    str(source.query)
    source.query.where.children[0].rhs = _HostileRhs(models.F("name"))
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "where clause carries a _HostileRhs node")
    assert fired == []


def test_lookup_hostile_lhs_fails_closed():
    """A hostile expression in lookup-LHS position fails closed.

    The LHS is always an expression the compiler dispatches, so the raw-state operand
    walk recurses it under the same rule as any other node.
    """
    fired = []

    class _HostileLhs(models.Func):
        def as_sql(self, compiler, connection):  # pragma: no cover - must never run
            fired.append("lhs.as_sql")
            return "1", []

    source = Category.objects.filter(name="keep")
    str(source.query)
    source.query.where.children[0].lhs = _HostileLhs(models.F("name"))
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "where clause carries a _HostileLhs node")
    assert fired == []


def test_hostile_order_by_expression_fails_closed():
    """A consumer ``order_by`` expression (never walked before) fails closed.

    ``order_by`` holds field-reference strings and expressions the compiler
    dispatches ``as_sql`` on; the old inventory never walked it, so a consumer
    ordering expression rode through to compile time.
    """
    fired = []

    class _HostileOrder(models.Func):
        def as_sql(self, compiler, connection):  # pragma: no cover - must never run
            fired.append("order_by.as_sql")
            return "1", []

    source = Category.objects.filter(is_private=False)
    str(source.query)
    source.query.order_by = (_HostileOrder(models.F("name")),)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "order_by carries a _HostileOrder node")
    assert fired == []


def test_consumer_expression_nested_in_genuine_func_fails_closed():
    """A consumer expression nested inside a genuine ``Func`` fails closed.

    The old top-level check trusted a genuine ``Func`` annotation without walking
    its operands, so a consumer expression in operand position reached compile. The
    recursive operand walk (``get_source_expressions``) rejects it.
    """
    from django.db.models.functions import Upper

    class _NestedHostile(models.Func):
        def as_sql(self, compiler, connection):  # pragma: no cover - must never run
            return "1", []

    source = Category.objects.filter(is_private=False)
    source.query.annotations = {"x": Upper(_NestedHostile(models.F("name")))}
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "annotation 'x' carries a _NestedHostile node")


def test_module_spoofed_type_is_not_genuine_django():
    """``__module__`` is spoofable, so provenance is proven by object identity.

    A consumer class declaring ``__module__ = "django.db.models.functions"`` is NOT
    the object Django exposes at ``sys.modules[module].<qualname>``, so identity
    provenance rejects it where the old ``__module__.startswith("django.")`` check
    accepted it.
    """

    class _SpoofFunc(models.Func):
        pass

    _SpoofFunc.__module__ = "django.db.models.functions"
    assert _type_is_genuinely_django(_SpoofFunc) is False
    # And a genuine Django expression type is still accepted.
    assert _type_is_genuinely_django(models.Value) is True


def test_hostile_subquery_inner_query_fails_closed():
    """A ``Subquery`` wrapping a foreign inner ``Query`` fails closed.

    ``Subquery.get_source_expressions()`` surfaces the wrapped ``sql.Query``, so the
    walk reaches it and requires it to be a genuine Django type -- a consumer
    ``Query`` subclass whose SQL synthesis the compiler would dispatch is rejected.
    """
    from django.db.models import Subquery, sql

    class _HostileInner(sql.Query):
        pass

    inner = Subquery(Item.objects.filter(category=models.OuterRef("pk")).values("pk"))
    inner.query = _HostileInner(Item)
    source = Category.objects.filter(is_private=False)
    source.query.annotations = {"x": inner}
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "annotation 'x' carries a _HostileInner node")


def test_hostile_expression_inside_genuine_subquery_where_fails_closed():
    """A consumer expression buried in a genuine subquery's ``where`` fails closed.

    The subquery node and its inner query are both genuine Django, but a consumer
    leaf hidden in the inner query's ``where`` tree would have its ``as_sql``
    dispatched at compile time. The walk must recurse into the subquery's inner
    query graph (not treat the inner ``sql.Query`` as an opaque leaf), so the buried
    node is rejected.
    """

    class _BuriedHostile(models.Func):
        def as_sql(self, compiler, connection):  # pragma: no cover - must never run
            return "1", []

    inner = models.Subquery(Item.objects.filter(name="x").values("pk"))
    inner.query.where.children.append(_BuriedHostile(models.F("name")))
    source = Category.objects.filter(is_private=False)
    source.query.annotations = {"y": inner}
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "where clause carries a _BuriedHostile node")


def test_deferred_filter_hostile_resolve_expression_never_dispatches():
    """A deferred-filter value with a hostile ``resolve_expression`` fails closed.

    ``add_q`` -> ``build_filter`` dispatches ``resolve_expression(self=query)`` on an
    expression value; a consumer expression could there erase the predicate and
    return a genuine-looking ``Value`` the post-bake walk cannot detect. Every
    argument is proven genuine-Django BEFORE the bake, so the hostile
    ``resolve_expression`` never runs.
    """
    from django.db.models import Value

    fired = []

    class _HostileValue:
        conditional = True

        def resolve_expression(self, query, *args, **kwargs):  # pragma: no cover
            fired.append("resolve_expression")
            from django.db.models.sql.where import WhereNode

            query.where = WhereNode()
            return Value(1)

    result = Category.objects.all()
    result._deferred_filter = (False, (), {"name": _HostileValue()})
    sealed, defect = _seal_or_defect(result, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet deferred filter 'name' carries a _HostileValue node")
    assert fired == []


def test_deferred_filter_bake_leaves_candidate_unmutated_and_is_repeatable():
    """Baking a deferred filter mutates only the detached clone, repeatably.

    The candidate's ``_deferred_filter`` is left untouched (observational
    immutability), so a concurrent caller sees no half-baked state -- and sealing
    the SAME source twice yields identical SQL with no duplicated predicate.
    """
    result = Category.objects.all()
    result._deferred_filter = (False, (), {"name": "later"})
    sealed_one, defect_one = _seal_or_defect(result, Category, None)
    sealed_two, defect_two = _seal_or_defect(result, Category, None)
    assert defect_one is None and defect_two is None
    assert result.__dict__.get("_deferred_filter") == (False, (), {"name": "later"})
    sql_one, params_one = sealed_one.query.get_compiler(using="default").as_sql()
    sql_two, params_two = sealed_two.query.get_compiler(using="default").as_sql()
    assert sql_one == sql_two
    assert list(params_one) == list(params_two)
    # Exactly one "later" parameter -- the predicate was baked once, not accumulated.
    assert list(params_one).count("later") == 1


def test_non_string_query_dict_key_is_typed_defect_not_raise():
    """A non-string ``Query.__dict__`` key becomes a typed defect, not a raise.

    ``_shadow_defect`` passes every ``__dict__`` key to ``getattr``; a non-string
    key would raise ``TypeError`` past the boundary's typed contract. It is rejected
    as a typed ``untrusted`` defect first.
    """
    source = Category.objects.filter(is_private=False)
    str(source.query)
    object.__getattribute__(source.query, "__dict__")[object()] = 1
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "query instance has a non-string __dict__ key")


def test_hostile_query_container_subclass_fails_closed():
    """A container ``sql.Query.clone`` copies must be an exact builtin.

    ``Query.clone`` calls ``self.alias_refcount.copy()`` (and ``.copy()`` on the
    other containers); a ``dict`` SUBCLASS with an overridden ``.copy()`` would
    dispatch mid-clone. Each container is required to be exactly the builtin.
    """
    fired = []

    class _HostileRefcount(dict):
        def copy(self):  # pragma: no cover - must never run
            fired.append("copy")
            return {}

    source = Category.objects.filter(is_private=False)
    str(source.query)
    source.query.alias_refcount = _HostileRefcount(source.query.alias_refcount)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "query alias_refcount is a _HostileRefcount")
    assert fired == []


def test_unrouted_parent_rejects_cross_routed_prefetch_child():
    """An UNROUTED parent fails closed on an explicitly cross-routed child.

    When the outer effective alias is unresolved (an unrouted parent), a prefetch
    child pinned to any explicit alias must fail closed rather than being accepted
    onto a divergent database -- otherwise one resolution schedules the parent and
    its related rows across two connections.
    """
    # The child is over the relation's own target model (Item for 'items') so the
    # ALIAS contract is what fires -- not the relation-target proof, which runs first.
    child = Item.objects.using("other").all()
    str(child.query)
    parent = Category.objects.all()
    str(parent.query)
    parent._prefetch_related_lookups = (models.Prefetch("items", queryset=child),)
    sealed, defect = _seal_or_defect(parent, Category, None)
    assert sealed is None
    assert defect == (
        "untrusted",
        "QuerySet prefetch 'items' queryset cannot be sealed (alias: other)",
    )


# ---------------------------------------------------------------------------
# Decisions 1-2: the validation-vs-
# execution divergences that survived the prove-then-clone walk -- a poisoned
# ``base_table`` cache, a stateful ``combined_queries`` iterator, isinstance-based
# inert typing, dynamic ``as_<vendor>`` compiler methods, un-walked ``Func`` metadata /
# ``filtered_relation`` / ``extra_order_by`` state, a consumer metaclass, and
# truthiness dispatch on retained ``QuerySet`` state.
# ---------------------------------------------------------------------------


def test_poisoned_base_table_cache_fails_closed_on_real_first_alias():
    """The base table is recomputed from ``alias_map``, never the poisonable cache.

    ``Query.base_table`` is a ``@cached_property``; ``Query.clone`` DELETES the cache and
    recomputes the first alias. A hostile query bakes its alias map against ``Item``,
    injects a spoof alias whose ``table_name`` is ``Category``'s, and poisons the
    ``base_table`` cache to name it -- validation reading the cache would see ``Category``
    while the clone compiles the real first alias (``Item``). Deriving the base table
    from ``next(iter(alias_map))`` inspects exactly what the cache-free clone will.
    """
    from django.db.models.sql.datastructures import BaseTable

    hostile = Item.objects.filter(name="x")
    str(hostile.query)
    hostile.query.get_initial_alias()
    hostile.model = Category
    hostile.query.model = Category
    hostile.query.alias_map = dict(hostile.query.alias_map)
    spoof_alias = Category._meta.db_table
    hostile.query.alias_map[spoof_alias] = BaseTable(Category._meta.db_table, spoof_alias)
    hostile.query.__dict__["base_table"] = spoof_alias  # poison the cached_property
    sealed, defect = _seal_or_defect(hostile, Category, None)
    assert sealed is None
    assert defect == ("table", Item._meta.db_table)


def test_stateful_combined_queries_tuple_subclass_fails_closed():
    """``combined_queries`` must be an exact tuple before any branch is walked.

    ``Query.clone`` re-iterates ``combined_queries`` to rebuild it, so a tuple SUBCLASS
    with a stateful ``__iter__`` could yield ``Category`` branches at validation and a
    foreign model's branches at clone / compile. Requiring an exact tuple makes the two
    iterations identical.
    """

    class _StatefulTuple(tuple):
        _calls = [0]

        def __iter__(self):  # pragma: no cover - must never be iterated
            self._calls[0] += 1
            if self._calls[0] == 1:
                return iter((Category.objects.all().query,))
            return iter((Item.objects.all().query,))

    source = Category.objects.all()
    str(source.query)
    source.query.combined_queries = _StatefulTuple()
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "query combined_queries is a _StatefulTuple")


def test_is_inert_value_uses_exact_types_not_isinstance():
    """A ``str`` subclass carrying ``resolve_expression`` is NOT inert.

    ``isinstance`` would treat a ``str`` subclass as an inert parameter; exact-type
    membership does not, so a subclass defining an expression / compiler protocol falls
    through to the genuine-Django walk and fails closed. Exact builtins and
    ``datetime`` / ``Decimal`` stay inert.
    """
    import datetime
    from decimal import Decimal

    class _EvilStr(str):
        def resolve_expression(self, query, *args, **kwargs):  # pragma: no cover
            from django.db.models import Value

            return Value(1)

    assert _is_inert_value(_EvilStr("x")) is False
    assert _is_inert_value("x") is True
    assert _is_inert_value(5) is True
    assert _is_inert_value(datetime.datetime(2020, 1, 1)) is True
    assert _is_inert_value(datetime.date(2020, 1, 1)) is True
    assert _is_inert_value(Decimal("1.5")) is True
    assert _is_inert_value(None) is True


def test_deferred_str_subclass_expression_never_dispatches():
    """A ``str``-subclass deferred value with ``resolve_expression`` fails closed.

    The exact-type inert check refuses to short-circuit the subclass, so it reaches the
    genuine-Django proof and is rejected before ``add_q`` can dispatch its
    ``resolve_expression``.
    """
    fired = []

    class _EvilStr(str):
        def resolve_expression(self, query, *args, **kwargs):  # pragma: no cover
            fired.append("resolve_expression")
            from django.db.models import Value

            return Value(1)

    result = Category.objects.all()
    result._deferred_filter = (False, (), {"name": _EvilStr("later")})
    sealed, defect = _seal_or_defect(result, Category, None)
    assert sealed is None
    assert defect[0] == "untrusted"
    assert fired == []


def test_deferred_model_instance_with_instance_resolve_expression_fails_closed():
    """A model instance carrying an INSTANCE-level ``resolve_expression`` fails closed.

    ``build_filter`` dispatches when ``hasattr(value, "resolve_expression")`` -- which
    finds an instance-level attribute too. A model instance whose own ``__dict__`` shadows
    ``resolve_expression`` is therefore rejected, where a class-level one is caught by the
    earlier expression branch.
    """
    from django.db.models import Value

    inst = Category(name="p")
    inst.resolve_expression = lambda query, *a, **k: Value(1)  # instance-level shadow
    result = Category.objects.all()
    result._deferred_filter = (False, (), {"parent": inst})
    sealed, defect = _seal_or_defect(result, Category, None)
    assert sealed is None
    assert defect == (
        "untrusted",
        "QuerySet deferred filter 'parent' model instance shadows resolve_expression",
    )


def test_deferred_plain_model_instance_still_seals():
    """A plain model instance (no expression protocol) remains a valid reverse-rel value.

    This is exactly the ``RelatedManager._apply_rel_filters`` shape: ``category.items``
    ``.all()`` leaves a deferred ``{"category": <Category instance>}`` filter on an
    ``Item`` queryset. The instance carries no ``resolve_expression``, so Django
    extracts its pk to a bound parameter; the bake resolves against ``Item``'s real
    ``category`` FK and seals cleanly.
    """
    result = Item.objects.all()
    result._deferred_filter = (False, (), {"category": Category(name="p", pk=7)})
    sealed, defect = _seal_or_defect(result, Item, None)
    assert defect is None
    assert sealed is not None


def test_dynamic_as_vendor_shadow_never_dispatches():
    """An ``as_<vendor>`` instance shadow fails closed even absent from the node class.

    The compiler resolves the emitter as ``getattr(node, "as_" + vendor, node.as_sql)``,
    so an ``as_sqlite`` shadow Django never defined on the class would still be dispatched.
    ``_shadow_defect`` rejects every instance key beginning ``as_``.
    """
    from django.db.models import Value

    fired = []

    def _spy_as_sqlite(compiler, connection):  # pragma: no cover - must never run
        fired.append("as_sqlite")
        return "1", []

    source = Category.objects.filter(name="keep")
    str(source.query)
    leaf = source.query.where.children[0]
    leaf.rhs = Value("keep")
    leaf.rhs.__dict__["as_sqlite"] = _spy_as_sqlite
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "where clause shadows the 'as_sqlite' compiler method")
    assert fired == []


def test_func_arg_joiner_metadata_non_string_fails_closed():
    """A genuine ``Func`` whose ``arg_joiner`` is a non-string object fails closed.

    ``Func.as_sql`` runs ``self.arg_joiner.join(...)`` and formats ``self.template``; these
    are never reached via ``get_source_expressions``. An instance override with a non-string
    ``arg_joiner`` would dispatch that object's ``join`` at compile time, so the metadata
    walk requires each SQL-template attribute to be exactly ``str``.
    """
    from django.db.models.functions import Concat

    class _EvilJoiner:
        def join(self, parts):  # pragma: no cover - must never run
            return "x"

    source = Category.objects.all()
    ann = Concat(models.F("name"), models.Value("!"), output_field=models.TextField())
    ann.arg_joiner = _EvilJoiner()
    source.query.annotations = {"c": ann}
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "annotation 'c' arg_joiner is a _EvilJoiner")


def test_func_extra_template_parameter_object_fails_closed():
    """A ``Func`` carrying a dispatchable object under ``extra`` never reaches the compiler.

    ``Func.__init__`` routes every surplus constructor keyword into ``self.extra`` -- so
    ``function=<object>`` lands in the mapping, not on the ``function`` slot the named
    template-attribute rule pins -- and ``Func.as_sql`` formats ``self.template %
    {**self.extra, **extra_context}``, which invokes each interpolated value's ``__str__``
    while the compiler assembles SQL, after the seal returned. The template-parameter rule
    admits only exact inert scalars there, so the seal fails closed and nothing dispatches.
    """
    fired = []

    class _HostileTemplateParam:
        def __str__(self):  # pragma: no cover - must never run
            fired.append("__str__")
            return "UPPER"

    source = Category.objects.all()
    ann = models.Func(
        models.Value("x"),
        function=_HostileTemplateParam(),
        output_field=models.TextField(),
    )
    source.query.annotations = {"c": ann}
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "annotation 'c' extra['function'] is a _HostileTemplateParam")
    assert fired == []


def test_func_extra_string_template_parameter_seals():
    """A legitimate string ``function=`` keyword -- real Django usage -- still seals.

    Inert scalar template parameters beside it (a number, an explicit ``None``) are equally
    admitted: they are rendered by the interpreter's own formatting, not by consumer code.
    """
    source = Category.objects.all()
    source.query.annotations = {
        "c": models.Func(
            models.Value("x"),
            function="UPPER",
            output_field=models.TextField(),
            precision=1,
            suffix=None,
        ),
    }
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed is not None
    assert sealed.query.annotations["c"].extra == {
        "function": "UPPER",
        "precision": 1,
        "suffix": None,
    }
    assert type(sealed.query.annotations["c"].extra) is dict
    assert sealed.query.annotations["c"].extra is not source.query.annotations["c"].extra


@pytest.mark.parametrize(
    ("extra", "detail"),
    [
        (SimpleNamespace(), "annotation 'c' extra is a SimpleNamespace"),
        ({5: "UPPER"}, "annotation 'c' extra has a non-string key"),
        ({"function": b"UPPER"}, "annotation 'c' extra['function'] is a bytes"),
    ],
)
def test_func_extra_non_inert_template_state_fails_closed(extra, detail):
    """The ``extra`` mapping itself, its keys, and its values are each pinned exactly.

    A ``dict`` SUBCLASS would run its own ``items`` when ``as_sql`` unpacks the format
    context, a non-string key is not a template format name, and a value outside the exact
    inert scalars is state the ``%`` interpolation would render through its own protocol.
    """
    source = Category.objects.all()
    ann = models.Func(models.Value("x"), output_field=models.TextField())
    ann.__dict__["extra"] = extra
    source.query.annotations = {"c": ann}
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", detail)


def test_where_node_non_string_connector_fails_closed():
    """A ``WhereNode`` whose ``connector`` is a non-string object fails closed.

    ``WhereNode.as_sql`` interpolates ``self.connector`` into the emitted SQL, so a
    non-string override would run its ``__str__`` at compile time.
    """

    class _EvilConnector:
        def __str__(self):  # pragma: no cover - must never run
            return "OR"

    source = Category.objects.filter(is_private=False)
    str(source.query)
    source.query.where.__dict__["connector"] = _EvilConnector()
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "where node connector is a _EvilConnector")


@pytest.mark.parametrize(
    ("holder", "detail"),
    [
        (object(), "query extra_order_by is a object"),
        (["name", 5], "query extra_order_by carries a int"),
    ],
)
def test_extra_order_by_non_string_state_fails_closed(holder, detail):
    """``extra_order_by`` (emitted as raw SQL) must be an exact sequence of strings."""
    source = Category.objects.all()
    str(source.query)
    source.query.extra_order_by = holder
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", detail)


def test_extra_order_by_none_and_string_sequence_seal():
    """A ``None`` or all-string ``extra_order_by`` seals -- the raw-SQL slot is accepted."""
    none_source = Category.objects.all()
    str(none_source.query)
    none_source.query.extra_order_by = None
    sealed, defect = _seal_or_defect(none_source, Category, None)
    assert defect is None and sealed is not None

    str_source = Category.objects.all()
    str(str_source.query)
    str_source.query.extra_order_by = ("name",)
    sealed, defect = _seal_or_defect(str_source, Category, None)
    assert defect is None and sealed is not None


def test_query_extra_select_executable_sql_fails_closed_before_clone():
    """A tampered ``Query.extra`` SQL object cannot execute during sealing or compilation."""
    fired = []

    class _HostileSQL:
        def __str__(self):  # pragma: no cover - must never run
            fired.append("str")
            return "1"

    source = Category.objects.all()
    source.query.extra = {"hostile": (_HostileSQL(), [])}
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "query extra['hostile'] SQL is a _HostileSQL")
    assert fired == []


@pytest.mark.parametrize(
    "payload",
    [
        ["1", ()],
        ("1",),
        ("1", (), ()),
    ],
)
def test_query_extra_select_malformed_payload_fails_closed(payload):
    """A ``Query.extra`` payload that is not an exact ``(sql, params)`` 2-tuple fails closed.

    The scan unpacks ``statement, params = payload`` to type each half, so the SHAPE gate
    has to run first: a list payload would unpack fine and let a subclass ``__iter__``
    dispatch during the unpack, and a 1- or 3-element tuple would raise a raw
    ``ValueError`` out of the unpack past the boundary's typed ``(code, detail)``
    contract. The neighbouring rows cannot see this arm -- they carry a well-shaped
    2-tuple and are rejected one line later on the SQL half's type -- so each of the
    three malformed shapes here is pinned to the same refusal rather than to a crash.
    """
    source = Category.objects.all()
    source.query.extra = {"hostile": payload}
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "query extra['hostile'] has a malformed payload")


def test_query_extra_select_hostile_params_fail_closed():
    """A hostile parameter inside a ``Query.extra`` payload propagates the params defect.

    ``.extra(select=...)`` params are handed straight to the database adapter, so the
    payload scan delegates the params half to ``_raw_sql_params_defect`` and returns
    whatever that reports. Reaching the delegation requires a payload that survives BOTH
    earlier gates (an exact 2-tuple whose SQL half is an exact ``str``), which every
    other ``extra`` row deliberately fails, so this is the only row that proves the
    delegated defect is propagated rather than swallowed -- and that it is re-labelled
    with the offending alias (``query extra['hostile']``) rather than a bare
    ``RawSQL``-style label.
    """

    class _HostileParameter:
        pass

    source = Category.objects.all()
    source.query.extra = {"hostile": ("%s", [_HostileParameter()])}
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "query extra['hostile'] params carries a _HostileParameter")


def test_extra_where_executable_sql_fails_closed_before_clone():
    """An ``ExtraWhere`` raw fragment is validated despite having no expression children."""
    fired = []

    class _HostileSQL:
        def __str__(self):  # pragma: no cover - must never run
            fired.append("str")
            return "1"

    source = Category.objects.extra(where=[_HostileSQL()])
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "where clause sqls carries a _HostileSQL")
    assert fired == []


def test_extra_where_non_sequence_sqls_fails_closed():
    """An ``ExtraWhere`` whose ``sqls`` is a sequence-LIKE object is refused before iteration.

    ``ExtraWhere.as_sql`` iterates ``self.sqls`` to build its raw fragment, so a
    consumer-supplied iterable would run its ``__iter__`` at compile time and could yield
    different statements than any validation pass saw. The neighbouring row carries a
    genuine ``list`` and is caught per-ELEMENT, which cannot see this arm: the
    whole-container type gate runs first, so a hostile ``__iter__`` never fires at all
    (asserted) -- an element-wise walk would already have dispatched it.
    """
    fired = []

    class _EvilSqls:
        def __iter__(self):  # pragma: no cover - must never run
            fired.append("iter")
            return iter(["1 = 1"])

    source = Category.objects.extra(where=_EvilSqls())
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "where clause sqls is a _EvilSqls")
    assert fired == []


def test_extra_where_non_sequence_params_fails_closed():
    """An ``ExtraWhere`` with genuine ``sqls`` still has its ``params`` validated.

    ``ExtraWhere`` carries TWO raw-SQL slots and the statement walk guards only the
    first; reaching the params slot requires every statement in ``sqls`` to be an exact
    ``str``, so a row with a hostile statement (the neighbour above) short-circuits and
    can never prove the branch validates params too. This row supplies a legitimate
    ``where`` fragment precisely so the walk falls through to the params delegation,
    where a sequence-like object -- whose ``__iter__`` would otherwise run when
    ``as_sql`` builds ``list(self.params or ())`` -- fails closed untouched.
    """
    fired = []

    class _EvilParams:
        def __iter__(self):  # pragma: no cover - must never run
            fired.append("iter")
            return iter(["keep"])

    source = Category.objects.extra(where=["name = %s"], params=_EvilParams())
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "where clause params is a _EvilParams")
    assert fired == []


def test_raw_sql_executable_parameter_fails_closed_before_clone():
    """A ``RawSQL`` parameter cannot defer consumer dispatch to backend adaptation."""
    from django.db.models.expressions import RawSQL

    class _HostileParameter:
        pass

    source = Category.objects.annotate(hostile=RawSQL("%s", [_HostileParameter()]))
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "annotation 'hostile' params carries a _HostileParameter")


def _filtered_relation_join():
    """Return a genuine ``Join`` carrying a resolved ``filtered_relation`` (compiled)."""
    from django.db.models import FilteredRelation, Q

    frq = Category.objects.annotate(
        vi=FilteredRelation("items", condition=Q(items__name="keep")),
    ).filter(vi__name="keep")
    frq.query.get_compiler(using="default").as_sql()  # populate alias_map + resolved_condition
    for alias, join in frq.query.alias_map.items():
        if getattr(join, "filtered_relation", None) is not None:
            return frq, alias, join
    raise AssertionError("no filtered_relation join was produced")


def test_legit_filtered_relation_seals_byte_identical():
    """A legitimate ``FilteredRelation`` query seals and compiles to identical SQL."""
    frq, _alias, _join = _filtered_relation_join()
    expected_sql, expected_params = frq.query.get_compiler(using="default").as_sql()
    sealed, defect = _seal_or_defect(frq, Category, None)
    assert defect is None and sealed is not None
    got_sql, got_params = sealed.query.get_compiler(using="default").as_sql()
    assert got_sql == expected_sql
    assert list(got_params) == list(expected_params)


def test_filtered_relation_hostile_resolved_condition_never_dispatches():
    """A consumer expression in a join's ``filtered_relation.resolved_condition`` fails closed.

    ``Join.as_sql`` compiles ``filtered_relation.resolved_condition`` (a ``WhereNode``),
    which is not reachable from ``alias_map`` alone. The join walk recurses it through the
    ``where``-tree walk, so a buried hostile leaf is rejected.
    """
    fired = []

    class _BuriedHostile(models.Func):
        def as_sql(self, compiler, connection):  # pragma: no cover - must never run
            fired.append("as_sql")
            return "1", []

    frq, _alias, join = _filtered_relation_join()
    join.filtered_relation.resolved_condition.children.append(_BuriedHostile(models.F("name")))
    sealed, defect = _seal_or_defect(frq, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "where clause carries a _BuriedHostile node")
    assert fired == []


def test_join_defect_non_genuine_filtered_relation_fails_closed():
    """A join carrying a non-Django ``filtered_relation`` object fails closed."""
    _frq, alias, join = _filtered_relation_join()
    join.filtered_relation = object()
    defect = _join_defect(join, alias, _GraphWalk())
    assert defect == ("untrusted", f"join for alias {alias!r} filtered_relation is a object")


def test_join_defect_shadowed_filtered_relation_fails_closed():
    """A genuine ``filtered_relation`` with a shadowed ``as_sql`` method fails closed.

    ``as_sql`` is a genuine class method on ``FilteredRelation``, so a shadow of it
    reports as a plain method (the "compiler method" wording is reserved for a
    dynamically-resolved ``as_<vendor>`` emitter absent from the class).
    """
    _frq, alias, join = _filtered_relation_join()
    join.filtered_relation.__dict__["as_sql"] = lambda *a, **k: None
    defect = _join_defect(join, alias, _GraphWalk())
    assert defect == (
        "untrusted",
        f"join for alias {alias!r} filtered_relation shadows the 'as_sql' method",
    )


def test_join_defect_unresolved_filtered_relation_is_clean():
    """A genuine join whose ``filtered_relation`` is not yet resolved carries no defect."""
    _frq, alias, join = _filtered_relation_join()
    join.filtered_relation.resolved_condition = None
    assert _join_defect(join, alias, _GraphWalk()) is None


def test_module_spoofing_metaclass_is_not_invoked_and_fails_closed():
    """Provenance reads ``__module__`` / ``__qualname__`` via ``type.__getattribute__``.

    A consumer metaclass overriding ``__getattribute__`` would otherwise run during the
    provenance read that is meant to reject the type; ``type.__getattribute__`` resolves
    both names without dispatching the metaclass hook.
    """
    fired = []

    class _NoisyMeta(type):
        def __getattribute__(cls, name):  # pragma: no cover - must never run for provenance
            fired.append(name)
            return super().__getattribute__(name)

    class _NoisyType(metaclass=_NoisyMeta):
        __module__ = "django.db.models.functions"

    assert _type_is_genuinely_django(_NoisyType) is False
    assert fired == []
    assert _type_is_genuinely_django(models.Value) is True


def test_provenance_of_type_with_raising_module_descriptor_fails_closed():
    """A metaclass whose ``__module__`` descriptor raises fails closed, not errors.

    ``type.__getattribute__`` still consults a metaclass DATA descriptor, so a hostile
    ``__module__`` property that raises would propagate past the typed contract; the
    provenance read catches it and fails closed.
    """

    class _RaisingMeta(type):
        @property
        def __module__(cls):
            raise AttributeError("no module")

    class _Raiser(metaclass=_RaisingMeta):
        pass

    assert _type_is_genuinely_django(_Raiser) is False


@pytest.mark.parametrize(
    ("field", "value", "detail"),
    [
        ("_db", object(), "QuerySet._db is a object"),
        ("_hints", object(), "QuerySet._hints is a object"),
        ("_fields", object(), "QuerySet._fields is a object"),
        ("_fields", (1,), "QuerySet._fields carries a int"),
        ("_sticky_filter", object(), "QuerySet._sticky_filter is a object"),
        ("_for_write", object(), "QuerySet._for_write is a object"),
    ],
)
def test_retained_state_field_wrong_shape_fails_closed(field, value, detail):
    """Each retained ``QuerySet`` state field is pinned to its exact shape."""
    source = Category.objects.all()
    str(source.query)
    setattr(source, field, value)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", detail)


def test_hostile_hints_bool_and_iter_never_dispatch():
    """A ``_hints`` dict subclass with a hostile ``__bool__`` / ``__iter__`` fails closed."""
    fired = []

    class _EvilHints(dict):
        def __bool__(self):  # pragma: no cover - must never run
            fired.append("bool")
            return True

        def __iter__(self):  # pragma: no cover - must never run
            fired.append("iter")
            return super().__iter__()

    source = Category.objects.all()
    str(source.query)
    source._hints = _EvilHints()
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet._hints is a _EvilHints")
    assert fired == []


def test_hints_non_string_key_fails_closed():
    """A ``_hints`` dict with a non-string key fails closed before it is copied."""
    source = Category.objects.all()
    str(source.query)
    source._hints = {object(): 1}
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet._hints has a non-string key")


def test_none_hints_seals_to_fresh_dict():
    """A ``None`` ``_hints`` seals to a fresh empty dict rather than erroring."""
    source = Category.objects.all()
    str(source.query)
    source._hints = None
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed._hints == {}


def test_prefetch_lookups_wrong_shape_fails_closed():
    """``_prefetch_related_lookups`` must be an exact tuple / list before iteration."""

    class _EvilLookups:
        def __bool__(self):  # pragma: no cover - must never run
            raise RuntimeError("dispatched")

    source = Category.objects.all()
    str(source.query)
    source._prefetch_related_lookups = _EvilLookups()
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet prefetch lookups is a _EvilLookups")


def test_missing_prefetch_lookups_key_seals():
    """An absent ``_prefetch_related_lookups`` key (``None``) seals with no prefetch."""
    source = Category.objects.all()
    str(source.query)
    source.__dict__.pop("_prefetch_related_lookups", None)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed._prefetch_related_lookups == ()


# ---------------------------------------------------------------------------
# Deferred-filter truthiness and cyclic containers.
# ---------------------------------------------------------------------------


def test_deferred_filter_slot_never_truth_tested():
    """The ``_deferred_filter`` slot is gated on ``is not None``, never ``__bool__``.

    A hostile object planted in the slot must fail closed as a malformed deferred
    filter without its ``__bool__`` (or ``__iter__``, via the unpack) ever running --
    a falsy ``__bool__`` would otherwise silently skip the bake.
    """

    class _EvilDeferred:
        def __bool__(self):  # pragma: no cover - must never run
            raise RuntimeError("dispatched __bool__")

        def __iter__(self):  # pragma: no cover - must never run
            raise RuntimeError("dispatched __iter__")

    source = Category.objects.all()
    str(source.query)
    source._deferred_filter = _EvilDeferred()
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet deferred filter is malformed")


def test_deferred_filter_wrong_arity_tuple_fails_closed():
    """A non-3-tuple deferred filter is rejected before any unpack."""
    source = Category.objects.all()
    str(source.query)
    source._deferred_filter = (False, ())
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet deferred filter is malformed")


def test_expr_graph_walk_rejects_self_referential_containers():
    """A cyclic list / dict in an expression slot fails closed as a typed defect.

    Django never produces a cyclic query graph, so a container reached again while
    it is still being validated is untrusted state -- not a shared diamond. Accepting
    it would report the graph trusted and leave the unbounded recursion to resurface
    downstream as a raw ``RecursionError`` outside the typed contract.
    """
    cyclic_list: list = []
    cyclic_list.append(cyclic_list)
    assert _expr_graph_defect(cyclic_list, _GraphWalk(), "where clause") == (
        "untrusted",
        "where clause contains a reference cycle",
    )
    cyclic_dict: dict = {}
    cyclic_dict["self"] = cyclic_dict
    assert _expr_graph_defect(cyclic_dict, _GraphWalk(), "where clause") == (
        "untrusted",
        "where clause contains a reference cycle",
    )


def test_expr_graph_walk_accepts_shared_diamond():
    """A node reached twice AFTER it validated is a legitimate shared diamond, not a cycle."""
    shared = models.Value(1)
    shared_list = [shared]
    shared_map = {"k": shared}
    assert (
        _expr_graph_defect(
            [
                shared,
                shared_list,
                shared_list,
                shared_map,
                shared_map,
            ],
            _GraphWalk(),
            "where clause",
        )
        is None
    )


def test_deferred_value_walk_rejects_self_referential_values():
    """A cyclic Q / list / dict deferred-filter value fails closed as a typed defect."""
    cyclic_list: list = []
    cyclic_list.append(cyclic_list)
    assert _deferred_value_defect(cyclic_list, _GraphWalk(), "deferred arg") == (
        "untrusted",
        "deferred arg contains a reference cycle",
    )
    cyclic_dict: dict = {}
    cyclic_dict["self"] = cyclic_dict
    assert _deferred_value_defect(cyclic_dict, _GraphWalk(), "deferred arg") == (
        "untrusted",
        "deferred arg contains a reference cycle",
    )
    cyclic_q = models.Q(pk=1)
    cyclic_q.children.append(cyclic_q)
    assert _deferred_value_defect(cyclic_q, _GraphWalk(), "deferred arg") == (
        "untrusted",
        "deferred arg contains a reference cycle",
    )


def test_deferred_value_walk_accepts_shared_diamond():
    """A value reached twice after validating stays cheap and is not reported a cycle."""
    shared: list = [1, 2]
    shared_map = {"k": 1}
    shared_q = models.Q(pk=1)
    assert (
        _deferred_value_defect(
            [
                shared,
                shared,
                shared_map,
                shared_map,
                shared_q,
                shared_q,
            ],
            _GraphWalk(),
            "deferred arg",
        )
        is None
    )


def test_concrete_or_none_rejects_the_abstract_model_base():
    """``models.Model`` itself carries no ``_meta``, so it resolves to no concrete model."""
    assert _concrete_or_none(models.Model) is None


def test_where_tree_walk_rejects_self_referential_node():
    """A ``WhereNode`` that contains itself fails closed rather than validating."""
    from django.db.models.sql.where import WhereNode

    node = WhereNode()
    node.children.append(node)
    assert _where_tree_defect(node, _GraphWalk()) == (
        "untrusted",
        "where node contains a reference cycle",
    )


def test_embedded_query_walk_rejects_self_referential_subquery():
    """An ``sql.Query`` reachable from its own graph fails closed rather than validating."""
    query = Category.objects.filter(is_private=False).query
    walk = _GraphWalk()
    walk.enter(id(query))
    assert _query_genuineness_defect(query, walk) == (
        "untrusted",
        "embedded query contains a reference cycle",
    )


def test_self_referential_genuine_expression_fails_closed():
    """A genuine expression that lists itself as its own operand fails closed."""
    expression = Coalesce(models.Value(1), models.Value(2))
    expression.source_expressions = [expression]
    assert _expr_graph_defect(expression, _GraphWalk(), "annotation 'x'") == (
        "untrusted",
        "annotation 'x' contains a reference cycle",
    )


def test_self_referential_combined_queries_fails_closed():
    """A ``combined_queries`` branch that is the query itself fails closed, not unbounded.

    The combined-branch recursion is its own three-state walk: without it the seal
    recursed the self-reference until a raw ``RecursionError`` escaped past the typed
    ``(code, detail)`` contract, and ``sql.Query.clone`` would have done the same.
    """
    source = Category.objects.filter(is_private=False)
    str(source.query)
    source.query.combined_queries = (source.query,)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "combined-query branches contain a reference cycle")


def test_shared_combined_query_branch_is_validated_once():
    """The same branch object listed twice is a shared reference, not a cycle."""
    source = Category.objects.filter(is_private=False)
    branch = Category.objects.filter(is_private=False).query
    str(source.query)
    str(branch)
    source.query.combined_queries = (branch, branch)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed is not None


def test_slotted_genuine_django_node_fails_closed():
    """A provenance-genuine Django class whose instances have no ``__dict__`` fails closed.

    ``django.utils.safestring.SafeString`` is exported by a ``django.`` module, so it
    passes the identity provenance proof, and it is a ``str`` SUBCLASS so it is not inert.
    Its instances are slotted, so the instance-state reads must fail it closed instead of
    raising a raw ``AttributeError`` past the typed contract.
    """
    from django.utils.safestring import SafeString

    source = Category.objects.filter(is_private=False)
    str(source.query)
    source.query.annotations["flag"] = SafeString("1")
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "annotation 'flag' is a SafeString with no instance state")


def test_slotted_django_namedtuple_in_an_unenumerated_slot_fails_closed():
    """A Django namedtuple carrying a MUTABLE member is refused, not retained by reference.

    ``sql.Query.explain_info`` is one of the query slots the graph proofs do not
    enumerate -- they walk the compiler-reachable EXPRESSION slots -- so the ownership
    decision for whatever sits there is made by canonical reconstruction alone. Its real
    Django value type is ``ExplainInfo``, a provenance-genuine namedtuple whose instances
    are slotted, and a namedtuple is not inert just because the tuple itself is immutable:
    its ``options`` member is a plain dict. The compiler prepends
    ``explain_query_prefix(format, **options)`` to the emitted SQL of ANY query carrying an
    ``explain_info``, so retaining the namedtuple by reference would leave the candidate
    holding a live handle into the sealed query's SQL, defeating the whole reconstruction.
    A slotted object has no slot-by-slot rebuild, so it takes the admitted-bound-value
    rule, which has no representation for a namedtuple and refuses it.
    """
    from django.db.models.sql.query import ExplainInfo

    source = Category.objects.filter(is_private=False)
    str(source.query)
    source.query.explain_info = ExplainInfo("text", {"analyze": True})
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet binds a ExplainInfo bound value")


def test_slotted_django_str_subclass_in_an_unenumerated_slot_is_normalized():
    """A slotted genuine-Django ``str`` subclass is normalized to an exact ``str``.

    The other half of the slotted rule. ``select_for_update_of`` is likewise unenumerated
    and likewise compiler-consumed (its members are emitted into ``FOR UPDATE OF ...``),
    and its members are consumer-supplied strings a hook can hand over as
    ``SafeString``. Being Django's own class does not make an instance safe to share -- the
    bound-value rule replaces it with an exact ``str`` whose every method is the
    interpreter's own, exactly as it would a consumer ``str`` subclass, so the seal keeps
    the query runnable instead of failing a legitimate value closed.
    """
    from django.utils.safestring import SafeString

    source = Category.objects.filter(is_private=False)
    str(source.query)
    source.query.select_for_update_of = (SafeString("self"),)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed is not None
    assert sealed.query.select_for_update_of == ("self",)
    assert [type(member) for member in sealed.query.select_for_update_of] == [str]


def test_reconstruction_never_grows_the_retained_type_set_with_a_planted_type():
    """The retained-by-reference set grows only with schema, never with a planted type.

    A type inside ``_RETAINED_TYPES`` wins the INLINE retain test at every traversal step
    of every LATER seal in the process, so a hostile hook that could add to it would buy
    permanent by-reference sharing for that type process-wide -- long after its own
    request ended. The single writer is the ``_RETAINED_SCHEMA_BASES`` branch of
    ``_is_reconstructable_node``, which admits only ``models.Field`` subclasses, model
    classes, and relation descriptors; the slotted-node path deliberately has none.
    """
    from django.db.models.sql.query import ExplainInfo
    from django.utils.safestring import SafeString

    before = frozenset(_RETAINED_TYPES)
    for planted in (ExplainInfo("text", {"analyze": True}), SafeString("self")):
        source = Category.objects.filter(is_private=False)
        str(source.query)
        source.query.explain_info = planted
        _seal_or_defect(source, Category, None)
    assert frozenset(_RETAINED_TYPES) - before == frozenset()


def test_hostile_case_container_fails_closed_before_its_iterator_runs():
    """An exact Django ``Case`` whose ``cases`` is a list SUBCLASS fails closed unrun.

    ``Case.get_source_expressions`` star-unpacks ``self.cases``, so calling that
    genuine accessor during the proof would run a hostile container's iterator --
    after the outer ``where`` tree has already been accepted and before
    ``sql.Query.clone`` runs, which is exactly when a mutation of the accepted tree
    goes unnoticed. Expression-owned state is validated first, so the iterator never
    runs.
    """
    fired = []

    class _HostileCases(list):
        def __iter__(self):  # pragma: no cover - must never run
            fired.append("iter")
            return super().__iter__()

    source = Category.objects.filter(is_private=False).annotate(
        flag=models.Case(
            models.When(is_private=True, then=models.Value(1)),
            default=models.Value(0),
            output_field=models.IntegerField(),
        ),
    )
    str(source.query)
    source.query.annotations["flag"].cases = _HostileCases(
        source.query.annotations["flag"].cases,
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "annotation 'flag' cases is a _HostileCases")
    assert fired == []


def test_hostile_alias_refcount_payload_fails_closed():
    """An ``int`` SUBCLASS stored as an ``alias_refcount`` value fails closed unrun.

    The value survives ``sql.Query.clone``'s shallow ``.copy()``, and Django's alias
    bookkeeping invokes its arithmetic on ordinary downstream ``.filter()``
    composition -- a consumer callback holding the sealed query. Payloads are pinned
    to their exact Django shape, not only the container type and its keys.
    """
    fired = []

    class _HostileCount(int):
        def __add__(self, other):  # pragma: no cover - must never run
            fired.append("add")
            return self

        def __sub__(self, other):  # pragma: no cover - must never run
            fired.append("sub")
            return self

    source = Category.objects.filter(is_private=False)
    str(source.query)
    alias = next(iter(source.query.alias_refcount))
    source.query.alias_refcount[alias] = _HostileCount(1)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", f"query alias_refcount[{alias!r}] is a _HostileCount")
    assert fired == []


def test_hostile_external_alias_payload_fails_closed():
    """A non-``bool`` ``external_aliases`` value fails closed."""
    source = Category.objects.filter(is_private=False)
    str(source.query)
    source.query.external_aliases["evil"] = 1
    assert _query_container_defect(source.query) == (
        "untrusted",
        "query external_aliases['evil'] is a int",
    )


def test_hostile_table_map_payload_fails_closed():
    """A ``table_map`` entry that is not an exact list of exact alias strings fails closed."""
    source = Category.objects.filter(is_private=False)
    str(source.query)
    table = next(iter(source.query.table_map))
    source.query.table_map[table] = (source.query.table_map[table][0],)
    assert _query_container_defect(source.query) == (
        "untrusted",
        f"query table_map[{table!r}] is a tuple",
    )
    source.query.table_map[table] = [object()]
    assert _query_container_defect(source.query) == (
        "untrusted",
        f"query table_map[{table!r}] carries a object",
    )


def test_hostile_set_container_member_fails_closed():
    """A non-``str`` member of a retained alias set fails closed."""
    source = Category.objects.filter(is_private=False)
    str(source.query)
    source.query.used_aliases = {object()}
    assert _query_container_defect(source.query) == (
        "untrusted",
        "query used_aliases carries a object",
    )


def test_hostile_filtered_relation_payload_fails_closed():
    """A ``_filtered_relations`` value must be a genuine, unshadowed Django object."""
    source = Category.objects.filter(is_private=False)
    str(source.query)
    source.query._filtered_relations = {"rel": object()}
    assert _query_container_defect(source.query) == (
        "untrusted",
        "query _filtered_relations['rel'] is a object",
    )
    relation = models.FilteredRelation("items", condition=models.Q(pk=1))
    relation.as_sql = lambda *args, **kwargs: None  # pragma: no cover - must never run
    source.query._filtered_relations = {"rel": relation}
    assert _query_container_defect(source.query) == (
        "untrusted",
        "query _filtered_relations['rel'] shadows the 'as_sql' method",
    )


def test_sealed_queryset_keeps_its_predicate_through_filter_composition():
    """Ordinary downstream ``.filter()`` composition keeps the sealed predicate."""
    source = Category.objects.filter(is_private=False)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    composed_sql = str(sealed.filter(name="visible").query)
    assert "is_private" in composed_sql
    assert "name" in composed_sql


def test_sealed_query_table_map_payload_is_not_shared_with_the_candidate():
    """The sealed query's ``table_map`` lists are fresh, not the candidate's own objects."""
    source = Category.objects.filter(is_private=False)
    str(source.query)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    table = next(iter(source.query.table_map))
    source.query.table_map[table].append("injected")
    assert "injected" not in sealed.query.table_map[table]


def _join_with_filtered_relation(query):
    """Return the one ``alias_map`` join carrying a ``FilteredRelation``."""
    return next(join for join in query.alias_map.values() if join.filtered_relation is not None)


def test_mutating_a_candidate_where_leaf_cannot_change_the_sealed_predicate():
    """A retained ``where`` leaf's ``rhs`` mutation shows on the candidate, never on the seal."""
    source = Category.objects.filter(is_private=False)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    before = sealed.query.sql_with_params()
    source_before = source.query.sql_with_params()
    source.query.where.children[0].rhs = True
    assert sealed.query.sql_with_params() == before
    assert source.query.sql_with_params() != source_before


def test_mutating_a_candidate_annotation_expression_cannot_change_the_sealed_sql():
    """A retained annotation expression cannot rewrite the sealed SQL or its params."""
    source = Category.objects.annotate(
        bonus=RawSQL("1 + %s", [7], output_field=models.IntegerField()),
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    before = sealed.query.sql_with_params()
    annotation = source.query.annotations["bonus"]
    annotation.sql = "1 + %s + 1000"
    annotation.params[0] = 99
    assert sealed.query.sql_with_params() == before
    assert before[1] == (7,)


def test_mutating_a_candidate_filtered_relation_cannot_change_the_sealed_join():
    """A retained ``FilteredRelation`` condition mutation shows on the candidate, not the seal."""
    source = Category.objects.annotate(
        visible=FilteredRelation("items", condition=Q(items__is_private=False)),
    ).filter(visible__name="widget")
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    before = sealed.query.sql_with_params()
    source_before = source.query.sql_with_params()
    source_join = _join_with_filtered_relation(source.query)
    source_join.filtered_relation.resolved_condition.children[0].rhs = True
    assert sealed.query.sql_with_params() == before
    assert source.query.sql_with_params() != source_before


def test_mutating_a_candidate_raw_sql_parameter_container_cannot_change_the_sealed_params():
    """A retained ``ExtraWhere`` sql / params container cannot rewrite the sealed statement."""
    source = Category.objects.extra(where=["is_private = %s"], params=[False])
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    before = sealed.query.sql_with_params()
    extra_where = source.query.where.children[0]
    extra_where.sqls[0] = "1 = 1"
    extra_where.params[0] = True
    assert sealed.query.sql_with_params() == before
    assert before[1] == (False,)


def test_sealed_query_shares_no_ast_node_with_the_candidate():
    """No sealed ``where`` node, annotation, join, or filtered relation IS the candidate's."""
    source = (
        Category.objects.annotate(
            visible=FilteredRelation("items", condition=Q(items__is_private=False)),
            bonus=RawSQL("1 + %s", [7], output_field=models.IntegerField()),
        )
        .filter(visible__name="widget")
        .filter(is_private=False)
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed.query.where is not source.query.where
    for sealed_child, source_child in zip(
        sealed.query.where.children,
        source.query.where.children,
        strict=True,
    ):
        assert sealed_child is not source_child
    assert sealed.query.annotations["bonus"] is not source.query.annotations["bonus"]
    assert sealed.query.annotations["bonus"].params is not source.query.annotations["bonus"].params
    assert (
        sealed.query._filtered_relations["visible"]
        is not source.query._filtered_relations["visible"]
    )
    sealed_join = _join_with_filtered_relation(sealed.query)
    source_join = _join_with_filtered_relation(source.query)
    assert sealed_join is not source_join
    assert sealed_join.filtered_relation is not source_join.filtered_relation
    assert (
        sealed_join.filtered_relation.resolved_condition
        is not source_join.filtered_relation.resolved_condition
    )


def test_sealed_query_retains_its_schema_objects_by_reference():
    """Reconstruction rebuilds AST, never the model's own fields / classes."""
    source = Category.objects.filter(is_private=False)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    sealed_lhs = sealed.query.where.children[0].lhs
    source_lhs = source.query.where.children[0].lhs
    assert sealed_lhs is not source_lhs
    assert sealed_lhs.target is source_lhs.target
    assert sealed_lhs.output_field is source_lhs.output_field
    assert sealed.query.model is Category


def test_mutating_a_candidate_bytearray_parameter_cannot_change_the_sealed_params():
    """The one MUTABLE inert parameter type is copied, never shared with the candidate."""
    source = Category.objects.extra(where=["is_private = %s"], params=[bytearray(b"\x00")])
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    sealed_param = sealed.query.where.children[0].params[0]
    source_param = source.query.where.children[0].params[0]
    assert sealed_param == source_param
    assert sealed_param is not source_param
    source_param[0] = 1
    assert sealed.query.where.children[0].params[0] == bytearray(b"\x00")


def test_query_state_that_cannot_be_reconstructed_fails_closed_typed():
    """A reconstruction failure surfaces as a typed defect, never a raw exception.

    A plain-data subclass instance holding no base-type state (allocated past
    ``__init__``) is admitted by the direct-RHS rule on its ancestry, but its
    normalizer's base-slot read raises -- an incidental failure, not the deliberate
    bound-value refusal, so the defect keeps the generic wording.
    """

    class _HollowUuid(uuid.UUID):
        pass

    source = Category.objects.filter(name="keep")
    str(source.query)
    source.query.where.children[0].rhs = object.__new__(_HollowUuid)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet query state cannot be reconstructed")


def test_reconstruction_hostile_mapping_key_fails_closed():
    """A consumer-owned object planted as a mapping KEY is refused, never retained.

    A rebuilt dict that kept a consumer key by reference would still share a mutable
    object with the candidate -- the same ownership violation as a retained value -- so
    keys take the admitted-bound-value rule too. ``_constructor_args`` is deconstruction
    bookkeeping no compiler path reaches, so the graph proofs never constrain its mapping
    keys; reconstruction is where the ownership invariant catches it.
    """

    class _HostileKey:
        """Hashable, but neither inert plain data nor trusted schema."""

    annotation = RawSQL("1", [], output_field=models.IntegerField())
    annotation._constructor_args = ((), {_HostileKey(): 1})
    source = Category.objects.filter(is_private=False)
    source.query.annotations["boom"] = annotation
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet binds a _HostileKey bound value")


def test_value_payload_mapping_key_plain_data_subclass_normalizes():
    """A plain-data SUBCLASS mapping key normalizes to its exact base, like a value.

    A rebuilt mapping that kept a subclass KEY by reference would leave consumer methods
    (``__hash__`` / ``__eq__`` / ``__str__`` under JSON encoding) on the compile path, so
    keys take the same normalize-or-refuse rule as values in the same slot.
    """

    class _KeyStr(str):
        pass

    source = Category.objects.filter(is_private=False).annotate(
        probe=models.Value({_KeyStr("a"): 1}),
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    (sealed_key,) = sealed.query.annotations["probe"].value
    assert type(sealed_key) is str
    assert sealed_key == "a"


def test_value_payload_mapping_key_enum_member_normalizes():
    """An enum-member mapping key normalizes to its underlying exact scalar."""

    class _KeyChoices(models.TextChoices):
        KEEP = "keep", "Keep"

    source = Category.objects.filter(is_private=False).annotate(
        probe=models.Value({_KeyChoices.KEEP: 1}),
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    (sealed_key,) = sealed.query.annotations["probe"].value
    assert type(sealed_key) is str
    assert sealed_key == "keep"


def test_value_payload_opaque_object_fails_closed():
    """An opaque consumer object bound as ``Value(<obj>)`` is refused, never retained.

    A ``Value``'s ``get_source_expressions()`` returns no children, so the graph walk
    never reaches its ``value`` slot; the admitted-bound-value rule catches the payload at
    reconstruction instead, so the verdict is the same one a direct lookup RHS gets --
    an object that is neither inert plain data nor trusted schema fails closed rather
    than surviving into the sealed query by reference.
    """

    class _OpaquePayload:
        pass

    payload = _OpaquePayload()
    source = Category.objects.filter(is_private=False).annotate(probe=models.Value(payload))
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet binds a _OpaquePayload bound value")
    # The candidate keeps its own payload: the seal never mutates the candidate graph.
    assert source.query.annotations["probe"].value is payload


def test_value_payload_mutable_container_subclass_fails_closed():
    """A ``list`` / ``dict`` SUBCLASS bound as a ``Value`` payload fails closed.

    A container subclass is not a plain container (its methods are consumer-owned), and
    retaining one by reference would make every post-seal mutation of the candidate's
    payload observable inside the sealed query. The direct-RHS rule already refuses the
    shape; the payload slot takes the identical verdict.
    """

    class _HostileList(list):
        pass

    class _HostileDict(dict):
        pass

    source = Category.objects.filter(is_private=False).annotate(
        probe=models.Value(_HostileList([1, 2, 3])),
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet binds a _HostileList bound value")

    source = Category.objects.filter(is_private=False).annotate(
        probe=models.Value(_HostileDict({"a": 1})),
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet binds a _HostileDict bound value")


def test_value_payload_plain_containers_rebuild_without_sharing():
    """An exact plain ``dict`` / ``list`` payload seals as a fresh framework-owned copy.

    Exact builtin containers are legitimate JSON-shaped bound payloads, so they are
    admitted -- but rebuilt member-wise, never shared, so a post-seal mutation of the
    candidate's payload cannot reach the sealed query. A non-``str`` inert mapping key
    (JSON encoders coerce one) is retained like any other inert leaf.
    """
    payload = {"a": 1, 2: "x"}
    source = Category.objects.filter(is_private=False).annotate(probe=models.Value(payload))
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    sealed_payload = sealed.query.annotations["probe"].value
    assert type(sealed_payload) is dict
    assert sealed_payload == payload
    assert sealed_payload is not payload
    payload["a"] = 99
    assert sealed.query.annotations["probe"].value["a"] == 1

    members = ["a", "b"]
    source = Category.objects.filter(is_private=False).annotate(probe=models.Value(members))
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    sealed_members = sealed.query.annotations["probe"].value
    assert type(sealed_members) is list
    assert sealed_members == members
    assert sealed_members is not members
    members.append("c")
    assert sealed.query.annotations["probe"].value == ["a", "b"]


def test_value_payload_plain_data_subclass_normalizes_to_exact_value():
    """A plain-data subclass bound as a ``Value`` payload normalizes to its exact base.

    The same replacement a direct lookup RHS gets: a ``TextChoices`` member becomes an
    exact ``str`` and a date subclass an exact ``datetime.date``, with no subclass
    override fired during normalization, so no consumer method survives into the sealed
    query's compile path.
    """
    fired = []

    class _PayloadChoices(models.TextChoices):
        KEEP = "keep", "Keep"

    class _LoudDate(datetime.date):
        def __str__(self):  # pragma: no cover - must never run
            fired.append("__str__")
            return "1999-12-31"

    source = Category.objects.filter(is_private=False).annotate(
        choice=models.Value(_PayloadChoices.KEEP),
        day=models.Value(_LoudDate(2020, 1, 2)),
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    sealed_choice = sealed.query.annotations["choice"].value
    assert type(sealed_choice) is str
    assert sealed_choice == "keep"
    sealed_day = sealed.query.annotations["day"].value
    assert type(sealed_day) is datetime.date
    assert sealed_day == datetime.date(2020, 1, 2)
    assert fired == []
    # The candidate keeps its own instances: normalization applies to the sealed query only.
    assert type(source.query.annotations["choice"].value) is _PayloadChoices
    assert type(source.query.annotations["day"].value) is _LoudDate


def test_value_payload_field_instance_is_retained_schema():
    """A ``models.Field`` instance in a bound-value slot is trusted schema, kept by reference.

    The bound-value rule retains schema deliberately: a field is the model's own column
    definition, not state the hook injected, and rebuilding one would detach it from the
    descriptors the compiler resolves against. A fresh local field class proves the
    retention verdict itself, not a memo of an earlier traversal.
    """

    class _LocalField(models.TextField):
        pass

    field = _LocalField()
    source = Category.objects.filter(is_private=False).annotate(probe=models.Value(field))
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed.query.annotations["probe"].value is field


def test_enum_member_with_model_value_fails_closed():
    """An enum member whose ``_value_`` is a model instance cannot bind and fails closed.

    The member normalizes to its underlying ``_value_``; a model instance is retained
    schema, not an inert leaf, so the member reduces to no framework-owned bound
    parameter and the seal refuses it with the member type named.
    """

    class _ModelChoices(enum.Enum):
        KEEP = Category(name="enum-carrier")

    source = Category.objects.filter(name="keep")
    str(source.query)
    source.query.where.children[0].rhs = _ModelChoices.KEEP
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet binds a _ModelChoices bound value")


def test_hostile_tzinfo_subclass_fails_closed():
    """A consumer ``tzinfo`` subclass on a genuine ``Trunc`` node fails closed.

    ``Trunc`` keeps its timezone on an ordinary instance slot the graph walk never
    reaches; the admitted-bound-value rule still governs it, so only the exact stdlib
    timezone types are retained and a consumer implementation is refused -- the payload
    slot's spelling (``tzinfo`` here, ``Value.value`` elsewhere) never changes the
    verdict.
    """

    class _HostileTz(datetime.tzinfo):
        def utcoffset(self, dt):  # pragma: no cover - must never run
            return datetime.timedelta(0)

        def tzname(self, dt):  # pragma: no cover - must never run
            return "X"

        def dst(self, dt):  # pragma: no cover - must never run
            return datetime.timedelta(0)

    source = Category.objects.filter(is_private=False).annotate(
        day=Trunc("created_date", "day", tzinfo=_HostileTz()),
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "QuerySet binds a _HostileTz bound value")


@pytest.mark.django_db
def test_trunc_tzinfo_is_retained_and_rows_survive():
    """Exact stdlib timezone objects are retained by reference and cost no rows.

    ``Trunc(..., tzinfo=zoneinfo.ZoneInfo(...))`` and ``tzinfo=datetime.timezone.utc``
    are ordinary consumer annotations; the seal must keep the timezone (an immutable
    interpreter-owned value) and the annotated queryset must still return its rows.
    """
    Category.objects.create(name="tz_row", is_private=False)
    tz = zoneinfo.ZoneInfo("UTC")
    source = Category.objects.filter(is_private=False).annotate(
        day=Trunc("created_date", "day", tzinfo=tz),
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed.query.annotations["day"].tzinfo is tz
    assert [row.name for row in sealed] == ["tz_row"]

    source = Category.objects.filter(is_private=False).annotate(
        day=Trunc("created_date", "day", tzinfo=datetime.timezone.utc),
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    assert sealed.query.annotations["day"].tzinfo is datetime.timezone.utc
    assert [row.name for row in sealed] == ["tz_row"]


@pytest.mark.django_db
def test_value_payload_literals_seal_and_rows_survive():
    """Ordinary ``Value`` literals seal and the annotated queryset still returns rows."""
    Category.objects.create(name="lit_row", is_private=False)
    source = Category.objects.filter(is_private=False).annotate(
        flag=models.Value(1),
        label=models.Value("x"),
    )
    sealed, defect = _seal_or_defect(source, Category, None)
    assert defect is None
    rows = list(sealed)
    assert [row.name for row in rows] == ["lit_row"]
    assert rows[0].flag == 1
    assert rows[0].label == "x"


def test_non_class_model_with_convincing_meta_fails_closed():
    """An OBJECT exposing ``_meta.concrete_model`` is not a model and fails closed unrun."""
    fired = []

    class _HookedMeta:
        @property
        def concrete_model(self):  # pragma: no cover - must never run
            fired.append("concrete_model")
            return Category

    class _FakeModel:
        _meta = _HookedMeta()

    source = Category.objects.filter(is_private=False)
    source.model = _FakeModel()
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("table", "_FakeModel")
    assert fired == []


def test_non_model_class_with_convincing_meta_fails_closed():
    """A non-model CLASS exposing ``_meta.concrete_model`` fails closed unrun."""
    fired = []

    class _HookedMeta:
        @property
        def concrete_model(self):  # pragma: no cover - must never run
            fired.append("concrete_model")
            return Category

    class _FakeModelClass:
        _meta = _HookedMeta()

    source = Category.objects.filter(is_private=False)
    source.model = _FakeModelClass
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("table", "_FakeModelClass")
    assert fired == []


class _HostileLeaf:
    """A consumer object that is neither inert, a container, nor a genuine Django node."""


def test_type_is_genuinely_django_absent_module_fails_closed():
    """A ``__module__`` naming a ``django.`` module absent from ``sys.modules`` fails closed."""

    class _Spoof:
        pass

    _Spoof.__module__ = "django.this_module_does_not_exist_zzz"
    _Spoof.__qualname__ = "Spoof"
    assert _type_is_genuinely_django(_Spoof) is False


def test_expr_graph_list_member_defect_propagates():
    """A hostile node inside a plain list slot fails closed through the container walk."""
    defect = _expr_graph_defect([_HostileLeaf()], _GraphWalk(), "annotation 'x'")
    assert defect == ("untrusted", "annotation 'x' carries a _HostileLeaf node")


def test_expr_graph_dict_non_string_key_fails_closed():
    """A non-string mapping key inside an expression-graph dict slot fails closed."""
    defect = _expr_graph_defect({1: "v"}, _GraphWalk(), "annotation 'x'")
    assert defect == ("untrusted", "annotation 'x' has a non-string mapping key")


def test_expr_graph_dict_value_defect_propagates():
    """A hostile value inside an expression-graph dict slot fails closed."""
    defect = _expr_graph_defect({"k": _HostileLeaf()}, _GraphWalk(), "annotation 'x'")
    assert defect == ("untrusted", "annotation 'x' carries a _HostileLeaf node")


def test_expr_graph_wherenode_routes_to_where_walker():
    """A ``WhereNode`` reached as an expression graph node routes to the where walker."""
    from django.db.models.sql.where import WhereNode

    assert _expr_graph_defect(WhereNode(), _GraphWalk(), "annotation 'x'") is None


def test_expr_sequence_non_sequence_holder_fails_closed():
    """An ``order_by`` slot that is neither None/bool nor list/tuple fails closed."""
    defect = _expr_sequence_defect(object(), _GraphWalk(), "order_by")
    assert defect == ("untrusted", "query order_by is a object")


def test_where_tree_shared_node_visited_once():
    """A ``WhereNode`` already VALIDATED short-circuits to ``None`` (shared diamond)."""
    from django.db.models.sql.where import WhereNode

    node = WhereNode()
    walk = _GraphWalk()
    walk.leave(id(node))
    assert _where_tree_defect(node, walk) is None


def test_where_tree_non_sequence_children_fails_closed():
    """A ``WhereNode`` whose ``children`` is neither list nor tuple fails closed."""
    from django.db.models.sql.where import WhereNode

    node = WhereNode()
    node.__dict__["children"] = object()
    assert _where_tree_defect(node, _GraphWalk()) == (
        "untrusted",
        "where node children is a object",
    )


def test_join_shadowed_method_fails_closed():
    """A genuine ``alias_map`` join whose ``__dict__`` shadows a method fails closed."""
    source = Category.objects.filter(name="keep")
    str(source.query)
    alias, join = next(iter(source.query.alias_map.items()))
    join.__dict__["as_sql"] = lambda *a, **k: None
    defect = _join_defect(join, alias, _GraphWalk())
    assert defect == ("untrusted", f"join for alias {alias!r} shadows the 'as_sql' method")


def test_query_container_none_dict_attr_is_clean():
    """A ``None`` dict-container attribute is skipped (the ``continue`` branch)."""
    query = Category.objects.all().query
    query.__dict__["extra"] = None
    assert _query_container_defect(query) is None


def test_query_container_none_exact_dict_attr_is_clean():
    """A ``None`` ``_EXACT_DICT_QUERY_ATTRS`` attribute is skipped (the ``continue`` branch).

    The sibling above covers the ``extra`` raw-SQL loop's ``continue``; this
    pins the dict-container loop's, whose members are validated for exact type
    when present.
    """
    query = Category.objects.all().query
    query.__dict__["annotations"] = None
    assert _query_container_defect(query) is None


def test_query_container_non_string_dict_key_fails_closed():
    """A dict-container attribute with a non-string key fails closed."""
    query = Category.objects.all().query
    query.__dict__["annotations"] = {1: "v"}
    assert _query_container_defect(query) == (
        "untrusted",
        "query annotations has a non-string key",
    )


def test_query_container_non_dict_attr_fails_closed():
    """A dict-container attribute that is not an exact dict fails closed."""
    query = Category.objects.all().query
    query.__dict__["annotations"] = ["not", "a", "dict"]
    assert _query_container_defect(query) == ("untrusted", "query annotations is a list")


def test_query_container_non_dict_extra_select_cache_fails_closed():
    """A non-dict ``_extra_select_cache`` fails closed."""
    query = Category.objects.all().query
    query.__dict__["_extra_select_cache"] = object()
    assert _query_container_defect(query) == ("untrusted", "query _extra_select_cache is a object")


def test_extra_select_cache_non_string_key_fails_closed():
    """A non-string ``_extra_select_cache`` alias fails closed inside the raw-SQL scan.

    Neither raw-SQL dict is in ``_EXACT_DICT_QUERY_ATTRS``, so the payload scan is
    the ONLY place their keys are typed -- and it must type them, because the alias
    is interpolated into the emitted ``SELECT`` list and is ``repr``'d into the
    defect detail. Uses ``_query_container_defect`` directly (like its
    ``_extra_select_cache`` neighbour above) because no public queryset API
    populates that private compiler cache.
    """
    query = Category.objects.all().query
    query.__dict__["_extra_select_cache"] = {object(): ("1", ())}
    assert _query_container_defect(query) == (
        "untrusted",
        "query _extra_select_cache has a non-string key",
    )


def test_query_ast_having_tree_defect_fails_closed():
    """A hostile node in the ``having`` tree fails closed."""
    from django.db.models.sql.where import WhereNode

    source = Category.objects.filter(name="keep")
    str(source.query)
    hostile_having = WhereNode()
    hostile_having.children.append(_HostileLeaf())
    source.query.__dict__["having"] = hostile_having
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", "where clause carries a _HostileLeaf node")


def test_query_genuineness_foreign_embedded_query_fails_closed():
    """A foreign embedded query type fails ``_query_genuineness_defect`` closed."""
    from django.db.models import sql

    class _Foreign(sql.Query):
        pass

    assert _query_genuineness_defect(_Foreign(Category), _GraphWalk()) == (
        "untrusted",
        "embedded query is a _Foreign",
    )


def test_query_genuineness_shared_query_visited_once():
    """A genuine embedded query already VALIDATED short-circuits to ``None``."""
    query = Category.objects.all().query
    walk = _GraphWalk()
    walk.leave(id(query))
    assert _query_genuineness_defect(query, walk) is None


def test_query_genuineness_shadowed_query_fails_closed():
    """An embedded query whose ``__dict__`` shadows a method fails closed."""
    query = Category.objects.all().query
    query.__dict__["add_q"] = lambda *a, **k: None
    assert _query_genuineness_defect(query, _GraphWalk()) == (
        "untrusted",
        "subquery instance shadows the 'add_q' method",
    )


def test_query_genuineness_container_defect_fails_closed():
    """An embedded query with a non-exact container fails closed."""
    query = Category.objects.all().query
    query.__dict__["annotations"] = {1: "v"}
    assert _query_genuineness_defect(query, _GraphWalk()) == (
        "untrusted",
        "query annotations has a non-string key",
    )


def test_query_genuineness_combined_branch_defect_fails_closed():
    """A hostile ``combined_queries`` branch fails ``_query_genuineness_defect`` closed."""
    from django.db.models import sql

    class _Foreign(sql.Query):
        pass

    query = Category.objects.all().query
    query.__dict__["combined_queries"] = (_Foreign(Category),)
    assert _query_genuineness_defect(query, _GraphWalk()) == (
        "untrusted",
        "embedded query is a _Foreign",
    )


def test_deferred_value_q_non_kv_child_fails_closed():
    """A ``Q`` child that is neither a nested ``Q`` nor a ``(str, value)`` pair fails closed."""
    bad = models.Q()
    bad.children.append(object())
    assert _deferred_value_defect(bad, _GraphWalk(), "deferred arg") == (
        "untrusted",
        "deferred arg Q child is a object",
    )


def test_deferred_value_nested_q_child_defect_propagates():
    """A hostile value inside a nested ``Q`` child fails closed."""
    assert _deferred_value_defect(models.Q(name=_HostileLeaf()), _GraphWalk(), "deferred arg") == (
        "untrusted",
        "deferred arg is a _HostileLeaf",
    )


def test_deferred_value_container_member_defect_propagates():
    """A hostile member inside a deferred-value container fails closed."""
    assert _deferred_value_defect([_HostileLeaf()], _GraphWalk(), "deferred arg") == (
        "untrusted",
        "deferred arg is a _HostileLeaf",
    )


def test_deferred_value_dict_non_string_key_fails_closed():
    """A non-string key inside a deferred-value dict fails closed."""
    assert _deferred_value_defect({1: "v"}, _GraphWalk(), "deferred arg") == (
        "untrusted",
        "deferred arg mapping key is a int",
    )


def test_deferred_value_dict_member_defect_propagates():
    """A hostile value inside a deferred-value dict fails closed."""
    assert _deferred_value_defect({"k": _HostileLeaf()}, _GraphWalk(), "deferred arg") == (
        "untrusted",
        "deferred arg is a _HostileLeaf",
    )


def test_deferred_value_arbitrary_object_fails_closed():
    """A plain non-model, non-expression object as a deferred value fails closed."""
    assert _deferred_value_defect(_HostileLeaf(), _GraphWalk(), "deferred arg") == (
        "untrusted",
        "deferred arg is a _HostileLeaf",
    )


def test_bake_deferred_non_dict_kwargs_fails_closed():
    """A deferred filter whose kwargs is not a dict fails closed."""
    from django.db.models import sql

    rebuilt = sql.Query.clone(Item.objects.all().query)
    assert _bake_deferred_filter_or_defect(rebuilt, (False, (), ["bad"]), "QuerySet") == (
        "untrusted",
        "QuerySet deferred filter kwargs is a list",
    )


def test_bake_deferred_non_sequence_args_fails_closed():
    """A deferred filter whose args is neither tuple nor list fails closed."""
    from django.db.models import sql

    rebuilt = sql.Query.clone(Item.objects.all().query)
    assert _bake_deferred_filter_or_defect(rebuilt, (False, object(), {}), "QuerySet") == (
        "untrusted",
        "QuerySet deferred filter args is a object",
    )


def test_bake_deferred_prohibited_kwargs_fails_closed():
    """A deferred filter carrying a prohibited ``_connector`` / ``_negated`` kwarg fails closed."""
    from django.db.models import sql

    from django_strawberry_framework.utils.querysets import PROHIBITED_FILTER_KWARGS

    prohibited = next(iter(PROHIBITED_FILTER_KWARGS))
    rebuilt = sql.Query.clone(Item.objects.all().query)
    assert _bake_deferred_filter_or_defect(
        rebuilt,
        (False, (), {prohibited: True}),
        "QuerySet",
    ) == ("untrusted", "QuerySet deferred filter carries prohibited kwargs")


def test_prohibited_filter_kwargs_matches_django_when_available():
    """The Django<6.0 import fallback stays byte-identical to Django 6.0's constant.

    ``django_strawberry_framework.utils.querysets`` guards the Django 6.0-only
    ``django.db.models.query.PROHIBITED_FILTER_KWARGS`` import with a verbatim
    fallback so the package imports at the declared ``Django>=5.2.16`` floor. On
    Django versions that DO expose the constant this pins the fallback literal
    against upstream drift; on the 5.2.x floor it pins the expected value.
    """
    import django.db.models.query as django_query

    from django_strawberry_framework.utils import querysets as querysets_module

    upstream = getattr(django_query, "PROHIBITED_FILTER_KWARGS", None)
    if upstream is not None:
        assert upstream == querysets_module.PROHIBITED_FILTER_KWARGS
    assert frozenset({"_connector", "_negated"}) == querysets_module.PROHIBITED_FILTER_KWARGS


def test_bake_deferred_hostile_arg_fails_closed():
    """A hostile positional deferred-filter arg fails closed before the bake."""
    from django.db.models import sql

    rebuilt = sql.Query.clone(Item.objects.all().query)
    assert _bake_deferred_filter_or_defect(
        rebuilt,
        (False, (_HostileLeaf(),), {}),
        "QuerySet",
    ) == ("untrusted", "QuerySet deferred filter arg is a _HostileLeaf")


def test_bake_deferred_non_string_kwarg_key_fails_closed():
    """A deferred filter with a non-string kwarg key fails closed."""
    from django.db.models import sql

    rebuilt = sql.Query.clone(Item.objects.all().query)
    assert _bake_deferred_filter_or_defect(rebuilt, (False, (), {1: "v"}), "QuerySet") == (
        "untrusted",
        "QuerySet deferred filter kwarg key is a int",
    )


def test_query_container_non_set_attr_fails_closed():
    """A ``_EXACT_SET_QUERY_ATTRS`` container that is not a set / frozenset fails closed."""
    query = Category.objects.all().query
    query.__dict__["used_aliases"] = ["not", "a", "set"]
    assert _query_container_defect(query) == ("untrusted", "query used_aliases is a list")


def test_base_table_defect_labels_a_non_string_table_name():
    """A non-string base table is reported as a defect naming the offending type."""
    table_name = object()
    query = SimpleNamespace(
        alias_map={"base": SimpleNamespace(table_name=table_name)},
    )

    assert _base_table_defect(query, Category) == "object"


def test_manager_coercion_rejects_unreadable_routing_state():
    """A manager without routing state is refused by the coercion boundary."""

    class _NoRoutingState:
        __slots__ = ()

    with pytest.raises(ConfigurationError, match="could not read the manager's routing state"):
        _coerced_manager_queryset(_NoRoutingState())  # type: ignore[arg-type]


def test_concrete_model_probe_fails_closed_for_unreadable_model_metadata(monkeypatch):
    """A model whose ``_meta`` cannot be read resolves to no concrete model."""
    model_base = type(models.Model)

    class _HostileModelBase(model_base):
        def __getattribute__(self, name):
            if name == "_meta" and type.__getattribute__(self, "_hostile_meta"):
                raise RuntimeError("model metadata exploded")
            return super().__getattribute__(name)

    class _HostileModel(models.Model, metaclass=_HostileModelBase):
        _hostile_meta = False

        class Meta:
            app_label = "test_querysets_hostile_meta"
            managed = False

    monkeypatch.setattr(_HostileModel, "_hostile_meta", True)

    assert _concrete_or_none(_HostileModel) is None


class _AsyncOnlyIterable:
    """An async-only iterable: ``__aiter__`` with no ``__iter__`` (no cleanup debt)."""

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


def test_is_async_only_iterable_arms():
    """The async-only predicate: AsyncIterable without Iterable; a QuerySet is BOTH."""
    assert is_async_only_iterable(_AsyncOnlyIterable()) is True
    assert is_async_only_iterable(Category.objects.all()) is False
    assert is_async_only_iterable([1, 2]) is False
    assert is_async_only_iterable(None) is False


def test_reject_async_iterable_in_sync_context_names_the_flavor():
    """An async-only source under sync execution raises SyncMisuseError naming the flavor."""

    with pytest.raises(SyncMisuseError, match="A DjangoListField resolver returned"):
        reject_async_iterable_in_sync_context(
            _AsyncOnlyIterable(),
            flavor_noun="DjangoListField",
        )
    with pytest.raises(SyncMisuseError, match="A connection resolver returned"):
        reject_async_iterable_in_sync_context(
            _AsyncOnlyIterable(),
            flavor_noun="connection",
        )


def test_reject_async_iterable_in_sync_context_passes_sync_sources():
    """Sync-iterable sources (lists, QuerySets) pass through untouched."""
    reject_async_iterable_in_sync_context([1, 2], flavor_noun="connection")
    reject_async_iterable_in_sync_context(Category.objects.none(), flavor_noun="connection")


async def test_reject_async_iterable_in_sync_context_noop_under_async_execution():
    """Under async execution the guard is a no-op: the async executor consumes it."""
    source = _AsyncOnlyIterable()
    reject_async_iterable_in_sync_context(source, flavor_noun="connection")


def test_reject_async_in_sync_context_cancels_future():
    """An unawaited future passed to reject_async_in_sync_context is cancelled before raising."""
    loop = asyncio.new_event_loop()
    future = loop.create_future()
    try:
        with pytest.raises(SyncMisuseError, match="returned an awaitable"):
            reject_async_in_sync_context(
                future,
                owner="TestOwner",
                method="test_method",
                context="test_context",
                recourse="test_recourse",
            )
        assert future.cancelled() is True
    finally:
        loop.close()


def test_coerce_field_value_or_none_returns_none_for_non_field():
    """Passing a non-Field object returns None rather than raising an error."""
    assert coerce_field_value_or_none(None, 42) is None
    assert coerce_field_value_or_none("not_a_field", 42) is None


def test_query_genuineness_defect_with_clean_combined_branches():
    """_query_genuineness_defect recurses clean combined_queries branches and succeeds."""
    qs1 = Category.objects.filter(id=1)
    qs2 = Category.objects.filter(id=2)
    combined_qs = qs1.union(qs2)
    walk = _GraphWalk()
    assert _query_genuineness_defect(combined_qs.query, walk) is None


def test_prepared_visibility_source_with_custom_render_error():
    """_prepared_visibility_source formats defect with custom render_error callable."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    def custom_render(code, detail):
        return f"custom source error: {code} -> {detail}"

    with pytest.raises(ConfigurationError, match="custom source error: type -> list"):
        _prepared_visibility_source(DummyType, [1, 2, 3], render_error=custom_render)


def test_normalized_visibility_result_with_custom_render_error():
    """_normalized_visibility_result formats defect with custom render_error callable."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    def custom_render(code, detail):
        return f"custom result error: {code} -> {detail}"

    with pytest.raises(ConfigurationError, match="custom result error: type -> list"):
        _normalized_visibility_result(
            DummyType,
            [1, 2, 3],
            required_alias=None,
            render_error=custom_render,
        )


def test_pks_all_present_subset_check():
    """pks_all_present stringifies declared pks and tests subset against present set."""
    assert pks_all_present([1, 2], {"1", "2", "3"}) is True
    assert pks_all_present(["1", "2"], {"1", "2"}) is True
    assert pks_all_present([1, 4], {"1", "2", "3"}) is False


@pytest.mark.django_db
def test_visible_related_object_resolution():
    """visible_related_object resolves the visible object or returns None."""
    cat = Category.objects.create(name="Electronics")
    info = SimpleNamespace(context=SimpleNamespace(request=None))

    resolved = visible_related_object(Category, cat.pk, info)
    assert resolved == cat

    missing = visible_related_object(Category, 999999, info)
    assert missing is None


def test_reject_awaitable_sync_source_noop_for_non_awaitable():
    """reject_awaitable_sync_source passes non-awaitables without raising."""
    reject_awaitable_sync_source([1, 2, 3], Category)
    reject_awaitable_sync_source(Category.objects.none(), Category)


def test_reject_awaitable_sync_source_raises_for_awaitable():
    """reject_awaitable_sync_source raises SyncMisuseError for an awaitable source."""

    async def sample():
        return Category.objects.all()

    coro = sample()
    with pytest.raises(SyncMisuseError, match="consumer resolver returned an awaitable"):
        reject_awaitable_sync_source(coro, Category)


# --------------------------------------------------------------------------
# Prefetch child relation-target proof (Django ticket #37267 vector)
#
# Django's prefetch machinery accepts a Prefetch child whose model is unrelated
# to the lookup's relation target whenever both models carry a same-named FK
# (Item.category and Property.category both point at Category), and populates the
# related cache with the foreign table's rows. Sealed, that means the `items`
# relation serves rows no Item-side visibility hook ever saw. The seal proves the
# child's model is the lookup path's relation target (or a subclass) before
# admitting the entry.
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_prefetch_child_over_unrelated_model_fails_closed():
    """A Prefetch child over an unrelated same-FK-name model fails closed.

    Pre-fix this sealed clean and the fetch populated ``category.items`` with
    Property rows from ``products_property`` (Django ticket #37267) -- foreign-table
    rows no Item visibility hook ever ran on.
    """
    from apps.products.services import seed_data

    seed_data(2)
    qs = Category.objects.prefetch_related(Prefetch("items", queryset=Property.objects.all()))
    code, detail = _seal_or_defect(qs, Category, None)[1]
    assert code == "untrusted"
    assert "'items'" in detail
    assert "Property" in detail and "Item" in detail


@pytest.mark.django_db
def test_prefetch_child_over_relation_target_seals_and_fetches_model_rows():
    """A prefetch child over the lookup's own relation target still seals and fetches."""
    from apps.products.services import seed_data

    seed_data(2)
    qs = Category.objects.prefetch_related(Prefetch("items", queryset=Item.objects.all()))
    sealed, defect = _seal_or_defect(qs, Category, None)
    assert defect is None, defect
    rows = list(sealed)
    assert rows
    assert all(type(row) is Category for row in rows)
    assert all(type(item) is Item for row in rows for item in row.items.all())


def test_prefetch_child_over_target_subclass_seals():
    """A proxy of the relation target is directionally compatible (Django #36432)."""

    class _ItemProxy(Item):
        class Meta:
            proxy = True
            app_label = "products"

    qs = Category.objects.prefetch_related(Prefetch("items", queryset=_ItemProxy.objects.all()))
    _, defect = _seal_or_defect(qs, Category, None)
    assert defect is None, defect


@pytest.mark.django_db
def test_prefetch_child_wrong_model_nested_path_fails_closed():
    """The relation-target proof walks MULTI-SEGMENT paths to the final relation."""

    # "items__entries" terminates on Entry (Item.entries reverse FK), so a
    # child over the WRONG table fails closed even though the FIRST segment
    # (items -> Item) matches the child's would-be shape.
    wrong = Category.objects.prefetch_related(
        Prefetch("items__entries", queryset=Property.objects.all()),
    )
    code, detail = _seal_or_defect(wrong, Category, None)[1]
    assert code == "untrusted"
    assert "'items__entries'" in detail
    assert "Property" in detail and "Entry" in detail


@pytest.mark.django_db
def test_prefetch_child_nested_path_correct_model_seals():
    """items__entries resolves to Entry; an Entry child seals unchanged."""

    qs = Category.objects.prefetch_related(
        Prefetch("items__entries", queryset=Entry.objects.all()),
    )
    _, defect = _seal_or_defect(qs, Category, None)
    assert defect is None, defect


@pytest.mark.django_db
def test_forward_fk_prefetch_child_model_mismatch_fails_closed():
    """The forward-FK direction is guarded too: Item.category expects Category rows."""

    qs = Item.objects.prefetch_related(Prefetch("category", queryset=Property.objects.all()))
    code, detail = _seal_or_defect(qs, Item, None)[1]
    assert code == "untrusted"
    assert "Category" in detail


def test_prefetch_relation_target_unresolvable_paths_fail_open():
    """Unresolvable relation paths fail OPEN to Django, never raw-raise.

    The proof only ever NARROWS shapes Django itself mishandles; a path it
    cannot resolve here (unknown segment, plain column, unresolved lazy FK
    string) returns ``None`` and the entry is left to Django's own fetch-time
    traversal, exactly as before the guard existed.
    """

    class _BrokenFkHolder(models.Model):
        """A model whose only relation is an unresolvable lazy FK string."""

        name = models.TextField(default="")
        rel = models.ForeignKey("missing_app.Missing", on_delete=models.CASCADE)

        class Meta:
            app_label = "products"
            db_table = "probe_broken_fk_holder"

    assert _prefetch_relation_target_or_none(Category, object()) is None
    assert _prefetch_relation_target_or_none(Category, "bogus_rel") is None
    assert _prefetch_relation_target_or_none(Category, "name") is None
    # A resolved segment followed by an unknown one: the accessor scan runs on
    # Item (which carries FORWARD relations) and still finds nothing.
    assert _prefetch_relation_target_or_none(Category, "items__nope") is None
    # A dangling string FK keeps ``related_model`` a STRING (no raise): the
    # exact-type check fails, the helper returns None, Django keeps ownership.
    assert _prefetch_relation_target_or_none(_BrokenFkHolder, "rel") is None


@pytest.mark.django_db
def test_prefetch_child_non_str_path_fails_closed():
    """A non-str path on a queryset-CARRYING Prefetch still fails closed at the path check."""

    pf = Prefetch("items", queryset=Item.objects.all())
    pf.__dict__["prefetch_through"] = object()
    qs = Category.objects.all()
    qs._prefetch_related_lookups = (pf,)
    code, detail = _seal_or_defect(qs, Category, None)[1]
    assert code == "untrusted"
    assert "path is not an exact str" in detail


@pytest.mark.django_db
def test_prefetch_child_unresolvable_relation_paths_fail_open():
    """Unresolvable relation paths (unknown / column / lazy-string) stay with Django.

    The relation-target proof only ever NARROWS shapes Django itself mishandles
    (a wrong-model child); a path whose target cannot be resolved here keeps the
    pre-guard behavior -- the child seal runs, the entry passes through, and any
    failure surfaces from Django's own fetch-time traversal.
    """

    class _LazyRefHolder(models.Model):
        name = models.TextField(default="")
        rel = models.ForeignKey("missing_app.Missing", on_delete=models.CASCADE)

        class Meta:
            app_label = "products"
            db_table = "probe_lazy_ref_holder"

    # Unknown first segment: get_field raises, resolution returns None.
    unknown = Category.objects.prefetch_related(
        Prefetch("bogus_rel", queryset=Item.objects.all()),
    )
    _, defect = _seal_or_defect(unknown, Category, None)
    assert defect is None, defect

    # Plain-column segment: not a relation, resolution returns None.
    column = Category.objects.prefetch_related(
        Prefetch("name", queryset=Item.objects.all()),
    )
    _, defect = _seal_or_defect(column, Category, None)
    assert defect is None, defect

    # Unresolved lazy reference: ``related_model`` stays the raw string, so the
    # path target is unprovable and the entry is left to Django unchanged.
    lazy = _LazyRefHolder.objects.prefetch_related(
        Prefetch("rel", queryset=Item.objects.all()),
    )
    sealed, defect = _seal_or_defect(lazy, _LazyRefHolder, None)
    assert defect is None, defect
    assert sealed is not None


@pytest.mark.django_db
def test_prefetch_child_default_accessor_wrong_model_fails_closed():
    """The DEFAULT ``<model>_set`` spelling is proven too (no ``related_name`` needed).

    ``Permission.content_type`` and ``LogEntry.content_type`` are both FKs to
    ``ContentType`` and neither declares a ``related_name``, so both are reached
    through the default ``permission_set`` / ``logentry_set`` ACCESSOR spellings
    -- which ``_meta.get_field`` does not know (it registers the reverse field
    under the bare child model name). A ``LogEntry`` child here sealed clean
    before the accessor scan existed, and the fetch populated
    ``ContentType.permission_set`` with admin ``LogEntry`` rows -- the same
    #37267 leak, one spelling over.
    """
    from django.contrib.admin.models import LogEntry
    from django.contrib.contenttypes.models import ContentType

    qs = ContentType.objects.prefetch_related(
        Prefetch("permission_set", queryset=LogEntry.objects.all()),
    )
    code, detail = _seal_or_defect(qs, ContentType, None)[1]
    assert code == "untrusted"
    assert "'permission_set'" in detail
    assert "LogEntry" in detail and "Permission" in detail


@pytest.mark.django_db
def test_prefetch_child_default_accessor_correct_model_seals():
    """The correct-model child over a default accessor still seals (no over-block)."""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    qs = ContentType.objects.prefetch_related(
        Prefetch("permission_set", queryset=Permission.objects.all()),
    )
    _, defect = _seal_or_defect(qs, ContentType, None)
    assert defect is None, defect


@pytest.mark.django_db
def test_prefetch_relation_target_default_accessors_resolve():
    """The reverse-accessor map resolves every spelling Django's prefetch accepts.

    Covers the installed apps' default ``<model>_set`` relations (FK and M2M
    reverse), a multi-segment path THROUGH an accessor, and the reverse
    ``OneToOne`` accessor (the bare child model name, no ``_set``).
    """
    from django.contrib.admin.models import LogEntry
    from django.contrib.auth.models import Group, Permission, User
    from django.contrib.contenttypes.models import ContentType

    # Relations declared WITHOUT a related_name, reached by the default
    # ``<model>_set`` accessor (the spelling ``get_field`` alone cannot see).
    assert _prefetch_relation_target_or_none(ContentType, "permission_set") is Permission
    assert _prefetch_relation_target_or_none(ContentType, "logentry_set") is LogEntry
    assert _prefetch_relation_target_or_none(User, "logentry_set") is LogEntry
    assert _prefetch_relation_target_or_none(Group, "user_set") is User
    assert _prefetch_relation_target_or_none(Permission, "user_set") is User
    assert _prefetch_relation_target_or_none(Permission, "group_set") is Group
    # An accessor can be an INTERMEDIATE segment like any relation name.
    assert (
        _prefetch_relation_target_or_none(ContentType, "permission_set__content_type")
        is ContentType
    )

    class _AccessorParent(models.Model):
        name = models.TextField(default="")

        class Meta:
            app_label = "products"
            managed = False

    class _AccessorO2oChild(models.Model):
        parent = models.OneToOneField(_AccessorParent, on_delete=models.CASCADE)

        class Meta:
            app_label = "products"
            managed = False

    # Reverse OneToOne accessors are the BARE child model name (no ``_set``).
    assert (
        _prefetch_relation_target_or_none(_AccessorParent, "_accessoro2ochild")
        is _AccessorO2oChild
    )

    class _AccessorM2mChild(models.Model):
        name = models.TextField(default="")
        parents = models.ManyToManyField(_AccessorParent, blank=True)

        class Meta:
            app_label = "products"
            managed = False

    # A reverse M2M without a related_name uses the same ``<model>_set`` spelling.
    assert (
        _prefetch_relation_target_or_none(_AccessorParent, "_accessorm2mchild_set")
        is _AccessorM2mChild
    )


@pytest.mark.django_db
def test_prefetch_relation_target_resolves_every_installed_default_accessor():
    """EVERY installed default-accessor relation resolves to its own target.

    The proof must hold project-wide: any reverse relation reachable through a
    ``<model>_set`` spelling (FK, M2M, or reverse OneToOne) whose target the
    guard cannot resolve would fail OPEN exactly where the #37267 leak is
    reachable, so the accessor map must cover them all.
    """
    from django.apps import apps

    unresolved = []
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if not (field.is_relation and field.auto_created and not field.concrete):
                continue
            accessor = field.get_accessor_name()
            if not accessor or not accessor.endswith("_set"):
                continue
            if _prefetch_relation_target_or_none(model, accessor) is not field.related_model:
                unresolved.append((model.__name__, accessor, field.related_model.__name__))
    assert unresolved == []


@pytest.mark.django_db
def test_prefetch_queryset_none_and_string_lookups_still_seal():
    """queryset=None Prefetch and plain string lookups are untouched by the new guard."""

    qs = Category.objects.prefetch_related(
        Prefetch("items"),
        "items",
        Prefetch("items", queryset=Item.objects.all(), to_attr="top_items"),
    )
    _, defect = _seal_or_defect(qs, Category, None)
    assert defect is None, defect


@pytest.mark.django_db
def test_seal_policy_presets_answer_slice_and_combinator_independently():
    """Each preset rejects exactly the shapes its surface cannot recompose onto.

    ``reject_sliced`` and ``require_model_rows`` are deliberately independent
    fields: fusing them is what forced the cascade to re-implement the slice
    rejection at both of its own entry points, and it is why a
    ``require_model_rows=False`` surface used to get the slice licence it never
    asked for. The four presets pin the four answers in one place - a read
    surface rejects a slice and admits a combinator (nothing in a read pipeline
    re-projects one), the two one-edge-down children admit a slice because
    nothing recomposes onto them, and the cascade rejects both because it
    narrows by ``.filter(...)`` and re-projects to a single column.
    """
    base = Category.objects.all()
    sliced = base[:5]
    combined = base.union(base)

    assert _seal_or_defect(sliced, Category, None, _DEFAULT_SEAL_POLICY)[1] == (
        "sliced",
        "rows 0:5",
    )
    assert _seal_or_defect(sliced, Category, None, _UNRECOMPOSED_CHILD_POLICY)[1] is None
    assert _seal_or_defect(sliced, Category, None, _PREFETCH_CHILD_POLICY)[1] is None
    assert _seal_or_defect(sliced, Category, None, _CASCADE_SEAL_POLICY)[1] == (
        "sliced",
        "rows 0:5",
    )
    assert _seal_or_defect(combined, Category, None, _DEFAULT_SEAL_POLICY)[1] is None
    assert _seal_or_defect(combined, Category, None, _CASCADE_SEAL_POLICY)[1] == (
        "combined",
        "union",
    )
    # ``require_model_rows`` still answers only the projection question.
    assert _seal_or_defect(base.values("id"), Category, None, _DEFAULT_SEAL_POLICY)[1] == (
        "projection",
        "ValuesIterable",
    )
    assert _seal_or_defect(base.values("id"), Category, None, _CASCADE_SEAL_POLICY)[1] is None


def test_unrendered_defect_code_says_so_instead_of_mislabelling():
    """A code with no arm at a site names itself; it never borrows another code's prose.

    Every message-building site renders only the subset of codes IT can reach,
    so each ladder used to end in an unconditional branch for its own last code.
    That shape cannot fail loudly: a code added to the seal without an arm here
    would be reported to the schema author as an alias mismatch or a wrong-table
    error - a false description of a real rejection. Dispatch is exhaustive
    instead, and the fallback is legible on both halves: it names the code and
    carries the detail, so the rejection still fails closed.
    """
    message = _defect_message({"type": "arm for type"}, ("type", "list"), "Subject")
    assert message == "arm for type"

    unrendered = _defect_message({"type": "arm for type"}, ("brand_new", "detail"), "Subject")
    assert "'brand_new'" in unrendered
    assert "detail" in unrendered
    assert "no wording" in unrendered
    # The point of the fallback: no other code's prose is borrowed.
    assert "arm for type" not in unrendered


def test_every_admitted_plain_container_has_a_rebuild_branch():
    """The prove side and the rebuild side share one container inventory.

    The two are halves of one round trip, and the dangerous direction is
    prover-accepted / rebuilder-unhandled: such a value passes every proof,
    reaches ``_reconstructed_value``, matches no branch, and fails the seal
    CLOSED - a rejection with no hint that the two inventories disagree. This
    walks the admitted set and requires the rebuild side to answer for each
    member with a FRESH object of the same type, which is the actual contract
    (the sealed query must share no mutable container with the candidate).
    """
    samples = {
        list: [1, 2],
        tuple: (1, 2),
        set: {1, 2},
        frozenset: frozenset({1, 2}),
        dict: {"a": 1},
    }
    assert set(samples) == set(_PLAIN_CONTAINER_TYPES)
    for container_type, sample in samples.items():
        assert _is_plain_container(container_type)
        rebuilt = _reconstructed_value(sample, {})
        assert type(rebuilt) is container_type
        assert rebuilt == sample
        assert rebuilt is not sample


def test_bound_value_normalizers_mirror_the_inert_inventory():
    """Every inert type (except ``bool``) has a normalizer, and nothing extra does.

    ``_BOUND_VALUE_NORMALIZERS`` is hand-ordered on purpose - ``datetime`` before
    ``date`` because the first subclasses the second - so it cannot be derived
    from the frozenset. What it can be is CHECKED against it. An inert type
    admitted with no normalizer entry makes SUBCLASS instances of that type fail
    the seal closed; exact instances short-circuit before the normalizer runs, so
    nothing surfaces the gap until such a subclass appears. ``bool`` is excluded
    deliberately (it cannot be subclassed).
    """
    assert set(_INERT_VALUE_TYPES) - {bool} == {base for base, _ in _BOUND_VALUE_NORMALIZERS}


def test_seal_require_unevaluated():
    """Populated _result_cache produces an 'unevaluated' defect when require_unevaluated=True."""
    qs = Category.objects.all()
    policy_uneval = _SealPolicy(
        require_model_rows=True,
        reject_sliced=True,
        reject_combined=True,
        require_shared_alias=False,
        require_unevaluated=True,
    )
    # When cache is None: no defect
    assert qs._result_cache is None
    sealed, defect = _seal_or_defect(qs, Category, None, policy_uneval)
    assert defect is None
    assert sealed is not None

    # When cache is populated: ("unevaluated", "the result cache is populated")
    qs_eval = Category.objects.all()
    qs_eval._result_cache = []
    sealed, defect = _seal_or_defect(qs_eval, Category, None, policy_uneval)
    assert sealed is None
    assert defect == ("unevaluated", "the result cache is populated")


def test_visibility_defect_messages():
    """Visibility helpers format actionable error messages for 'unevaluated' and 'combined' defects."""

    class BookType:
        pass

    err_msg_uneval = str(
        _visibility_result_error(
            BookType,
            Category,
            None,
            ("unevaluated", "the result cache is populated"),
            None,
        ),
    )
    assert (
        "BookType.get_queryset returned an evaluated queryset (the result cache is populated)"
        in err_msg_uneval
    )
    assert "Return an unevaluated QuerySet." in err_msg_uneval

    err_msg_comb = str(
        _visibility_result_error(
            BookType,
            Category,
            None,
            ("combined", "union"),
            None,
        ),
    )
    assert "BookType.get_queryset returned a combined queryset (union)" in err_msg_comb
    assert "Return a plain uncombined QuerySet." in err_msg_comb

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    evaluated_qs = Category.objects.all()
    evaluated_qs._result_cache = []
    policy_uneval = _SealPolicy(require_unevaluated=True)
    with pytest.raises(
        ConfigurationError,
        match="apply_type_visibility for DummyType requires an unevaluated QuerySet",
    ):
        _prepared_visibility_source(DummyType, evaluated_qs, policy=policy_uneval)

    combined_qs = Category.objects.all().union(Category.objects.all())
    with pytest.raises(
        ConfigurationError,
        match="apply_type_visibility for DummyType requires an uncombined QuerySet",
    ):
        _prepared_visibility_source(
            DummyType,
            combined_qs,
            policy=_LIST_ARGUMENT_VISIBILITY_POLICY,
        )


def test_apply_type_visibility_sync_combined_result_error():
    """apply_type_visibility_sync formats combined defect error using _visibility_result_error."""

    class CombinedType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

        @classmethod
        def get_queryset(cls, queryset, info):
            return queryset.union(Category.objects.all())

    with pytest.raises(
        ConfigurationError,
        match=r"CombinedType\.get_queryset returned a combined queryset \(union\); active list arguments forbid combined queries",
    ):
        apply_type_visibility_sync(
            CombinedType,
            Category.objects.all(),
            SimpleNamespace(),
            policy=_LIST_ARGUMENT_VISIBILITY_POLICY,
        )


def test_validate_post_orderset_result_valid():
    """_validate_post_orderset_result accepts valid, ordered candidate querysets."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    source_qs = Category.objects.all()
    valid_candidate = Category.objects.all().order_by("name")
    sealed = _validate_post_orderset_result(
        DummyType,
        source_qs,
        valid_candidate,
        "MyOrderSet.apply_sync",
    )
    assert isinstance(sealed, models.QuerySet)


def test_validate_post_orderset_result_rejects_non_queryset():
    """_validate_post_orderset_result rejects non-queryset collections."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    source_qs = Category.objects.all()
    with pytest.raises(
        ConfigurationError,
        match=r"MyOrderSet\.apply_sync must return an unevaluated, unsliced, uncombined QuerySet of Category rows; got type defect",
    ):
        _validate_post_orderset_result(DummyType, source_qs, [1, 2, 3], "MyOrderSet.apply_sync")


def test_validate_post_orderset_result_rejects_none():
    """_validate_post_orderset_result rejects None return values."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    source_qs = Category.objects.all()
    with pytest.raises(
        ConfigurationError,
        match=r"MyOrderSet\.apply_sync must return an unevaluated, unsliced, uncombined QuerySet of Category rows; got type defect",
    ):
        _validate_post_orderset_result(DummyType, source_qs, None, "MyOrderSet.apply_sync")


def test_validate_post_orderset_result_rejects_wrong_model():
    """_validate_post_orderset_result rejects querysets of an unrelated model."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    source_qs = Category.objects.all()
    wrong_model_qs = Item.objects.all()
    with pytest.raises(
        ConfigurationError,
        match=r"MyOrderSet\.apply_sync must return an unevaluated, unsliced, uncombined QuerySet of Category rows; got table defect",
    ):
        _validate_post_orderset_result(
            DummyType,
            source_qs,
            wrong_model_qs,
            "MyOrderSet.apply_sync",
        )


def test_validate_post_orderset_result_rejects_evaluated():
    """_validate_post_orderset_result rejects querysets with evaluated result cache."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    source_qs = Category.objects.all()
    eval_qs = Category.objects.all()
    eval_qs._result_cache = []
    with pytest.raises(
        ConfigurationError,
        match=r"MyOrderSet\.apply_sync must return an unevaluated, unsliced, uncombined QuerySet of Category rows; got unevaluated defect",
    ):
        _validate_post_orderset_result(DummyType, source_qs, eval_qs, "MyOrderSet.apply_sync")


def test_validate_post_orderset_result_rejects_sliced():
    """_validate_post_orderset_result rejects sliced querysets."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    source_qs = Category.objects.all()
    sliced_qs = Category.objects.all()[:5]
    with pytest.raises(
        ConfigurationError,
        match=r"MyOrderSet\.apply_sync must return an unevaluated, unsliced, uncombined QuerySet of Category rows; got sliced defect",
    ):
        _validate_post_orderset_result(DummyType, source_qs, sliced_qs, "MyOrderSet.apply_sync")


def test_validate_post_orderset_result_rejects_combined():
    """_validate_post_orderset_result rejects combined querysets."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    source_qs = Category.objects.all()
    comb_qs = Category.objects.all().union(Category.objects.all())
    with pytest.raises(
        ConfigurationError,
        match=r"MyOrderSet\.apply_sync must return an unevaluated, unsliced, uncombined QuerySet of Category rows; got combined defect",
    ):
        _validate_post_orderset_result(DummyType, source_qs, comb_qs, "MyOrderSet.apply_sync")


def test_validate_post_orderset_result_rejects_projection():
    """_validate_post_orderset_result rejects values/projection querysets."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    source_qs = Category.objects.all()
    values_qs = Category.objects.values("id")
    with pytest.raises(
        ConfigurationError,
        match=r"MyOrderSet\.apply_sync must return an unevaluated, unsliced, uncombined QuerySet of Category rows; got projection defect",
    ):
        _validate_post_orderset_result(DummyType, source_qs, values_qs, "MyOrderSet.apply_sync")


def test_validate_post_orderset_result_rejects_db_routing_mismatch():
    """_validate_post_orderset_result rejects querysets routed to a different database."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    source_qs = Category.objects.all()
    diff_db_qs = Category.objects.using("other")
    with pytest.raises(
        ConfigurationError,
        match="changed database routing intent",
    ):
        _validate_post_orderset_result(DummyType, source_qs, diff_db_qs, "MyOrderSet.apply_sync")


def test_validate_post_orderset_result_rejects_hints_routing_mismatch():
    """_validate_post_orderset_result rejects querysets with divergent database routing hints."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    source_qs = Category.objects.all()
    diff_hints_qs = Category.objects.all()
    diff_hints_qs._hints = {"instance": 123}
    with pytest.raises(
        ConfigurationError,
        match="changed database routing intent",
    ):
        _validate_post_orderset_result(
            DummyType,
            source_qs,
            diff_hints_qs,
            "MyOrderSet.apply_sync",
        )


def test_validate_post_orderset_result_zero_consumer_dispatch_on_getattribute():
    """_validate_post_orderset_result accesses _db and _hints without consumer __getattribute__."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    class HostileGetattributeQuerySet(models.QuerySet):
        def __getattribute__(self, name):
            if name in ("_db", "_hints"):
                raise AssertionError(f"Hostile consumer __getattribute__ invoked for '{name}'")
            return super().__getattribute__(name)

    source_qs = HostileGetattributeQuerySet(model=Category)
    # Should safely read _db and _hints via raw instance __dict__ without invoking HostileQuerySet.__getattribute__
    sealed = _validate_post_orderset_result(
        DummyType,
        source_qs,
        source_qs,
        "MyOrderSet.apply_sync",
    )
    assert sealed is not None


def test_validate_post_orderset_result_routing_hints_hostile_eq_repr():
    """_validate_post_orderset_result compares and reports routing hints without consumer __eq__ or __repr__."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    class HostileValue:
        def __eq__(self, other):
            raise AssertionError("Hostile consumer __eq__ invoked")

        def __repr__(self):
            raise AssertionError("Hostile consumer __repr__ invoked")

    val_a = HostileValue()
    val_b = HostileValue()

    source_qs = Category.objects.all()
    source_qs._hints = {"tag": val_a}

    cand_same = Category.objects.all()
    cand_same._hints = {"tag": val_a}  # Same instance (identity)

    # Comparing identical non-primitive hints must not invoke __eq__
    sealed = _validate_post_orderset_result(
        DummyType,
        source_qs,
        cand_same,
        "MyOrderSet.apply_sync",
    )
    assert sealed is not None

    cand_diff = Category.objects.all()
    cand_diff._hints = {"tag": val_b}  # Different instance

    # Rejection formatting must not invoke HostileValue.__repr__
    with pytest.raises(
        ConfigurationError,
        match="changed database routing intent",
    ) as exc_info:
        _validate_post_orderset_result(
            DummyType,
            source_qs,
            cand_diff,
            "MyOrderSet.apply_sync",
        )
    assert "HostileValue at 0x" in str(exc_info.value)


def test_validate_post_orderset_result_routing_hints_none_vs_empty():
    """_validate_post_orderset_result preserves distinction between absent (None) and empty ({}) hints."""

    class DummyType:
        __django_strawberry_definition__ = SimpleNamespace(model=Category)

    source_qs = Category.objects.all()
    source_qs._hints = None

    cand_qs = Category.objects.all()
    cand_qs._hints = {}

    with pytest.raises(
        ConfigurationError,
        match=r"expected db='default', hints=None, got db='default', hints=\{\}",
    ):
        _validate_post_orderset_result(
            DummyType,
            source_qs,
            cand_qs,
            "MyOrderSet.apply_sync",
        )
