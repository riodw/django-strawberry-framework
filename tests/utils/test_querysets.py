"""Tests for the shared query-source / visibility substrate (``utils/querysets.py``).

The 0.0.9 DRY pass (``docs/feedback.md`` Major 1) single-sited the query-source
contract the list field, connection field, optimizer middleware, Relay node
defaults, and filter related-visibility derive had each spelled separately:
``Manager`` -> ``QuerySet`` coercion, the is-queryset decision, and the sync /
async ``DjangoType.get_queryset`` visibility routing. ``get_queryset`` is the
visibility hook, so a divergence between those copies is a data-leak bug class;
these tests pin the neutral mechanics directly. The deep behavioral coverage
(through-schema list / connection / node / filter visibility) lives in the
surface suites (``tests/test_list_field.py``, ``tests/test_connection.py``,
``tests/test_relay_node_field.py``, ``tests/filters/test_sets.py``).

``coerce_field_value_or_none`` (the 0.0.13 DRY pass) is the sibling "raw
literal -> Django field value, or nothing" primitive shared by the Relay id
decode, the raw relation-pk decode, and the ``__in`` filter member decode; its
own through-schema coverage lives in the same surface suites plus
``examples/fakeshop/test_query/test_scalars_filter_api.py`` (the out-of-range
``__in`` member drop).
"""

from types import SimpleNamespace

import pytest
from apps.products.models import Category, Item
from django.db import models

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations import resolvers as mutation_resolvers
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils.querysets import (
    SyncMisuseError,
    apply_type_visibility_async,
    apply_type_visibility_sync,
    coerce_field_value_or_none,
    initial_queryset,
    normalize_query_source,
    post_process_queryset_result_async,
    post_process_queryset_result_sync,
    run_in_one_sync_boundary,
    visible_related_objects,
)
from django_strawberry_framework.utils.write_transaction import write_pipeline


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

    The 0.0.13 DRY pass promoted the byte-identical
    ``sync_to_async(fn, thread_sensitive=True)(*args, **kwargs)`` shape out of
    ``mutations/resolvers.py`` into this module so filters / orders /
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


def test_hostile_source_refresh_fails_closed():
    """A source whose ``.all()`` preserves its cache cannot smuggle rows past the refresh."""

    class _StickySource(models.QuerySet):
        def all(self):
            return self

    sticky = _StickySource(model=Category)
    sticky._result_cache = []
    with pytest.raises(ConfigurationError, match="preserved cached rows"):
        apply_type_visibility_sync(_SyncType, sticky, info=None)


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
    """Normalization composes lazily: filters / annotations / ordering / subclass survive."""

    class _CustomQuerySet(models.QuerySet):
        pass

    shaped = (
        _CustomQuerySet(model=Category)
        .filter(name__startswith="a")
        .annotate(flag=models.Value(1))
        .order_by("-name")
    )
    result = apply_type_visibility_sync(_sync_hook_type(shaped), Category.objects.all(), info=None)
    assert result is shaped  # no clone needed: unevaluated, unrouted requirement, right table
    assert "flag" in result.query.annotations


def test_hostile_result_clone_preserving_cache_fails_closed():
    """A hostile subclass whose ``.all()`` returns its evaluated self fails closed."""

    class _StickyResult(models.QuerySet):
        def all(self):
            return self

    sticky = _StickyResult(model=Category)
    sticky._result_cache = []
    with pytest.raises(ConfigurationError, match="preserved cached rows"):
        apply_type_visibility_sync(_sync_hook_type(sticky), Category.objects.all(), info=None)


def test_hostile_result_clone_dodging_repin_fails_closed():
    """A hostile subclass whose ``.using()`` returns its unrouted self fails closed."""

    class _PinDodger(models.QuerySet):
        def using(self, alias):
            return self

    hook = _stub_type(Category, lambda cls, qs, info: _PinDodger(model=Category))
    with pytest.raises(ConfigurationError, match="pinned to alias 'other'"):
        apply_type_visibility_sync(hook, Category.objects.using("other"), info=None)


def test_hostile_result_clone_returning_non_queryset_fails_closed():
    """A hostile subclass whose ``.using()`` returns a non-queryset fails closed."""

    class _GarbageCloner(models.QuerySet):
        def using(self, alias):
            return object()

    hook = _stub_type(Category, lambda cls, qs, info: _GarbageCloner(model=Category))
    with pytest.raises(ConfigurationError, match="must return a QuerySet or Manager.*got object"):
        apply_type_visibility_sync(hook, Category.objects.using("other"), info=None)


def test_hook_exception_propagates_unchanged():
    """An exception raised INSIDE the hook propagates as-is - the boundary never masks it."""

    class _BoomError(RuntimeError):
        pass

    def _raise(cls, queryset, info):
        raise _BoomError("consumer bug")

    with pytest.raises(_BoomError, match="consumer bug"):
        apply_type_visibility_sync(_stub_type(Category, _raise), Category.objects.all(), info=None)


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
