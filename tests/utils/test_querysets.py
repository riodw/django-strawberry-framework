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
    _bake_deferred_filter_or_defect,
    _deferred_value_defect,
    _expr_graph_defect,
    _expr_sequence_defect,
    _is_inert_value,
    _join_defect,
    _query_container_defect,
    _query_genuineness_defect,
    _seal_or_defect,
    _sealed_prefetch_related_lookups,
    _type_is_genuinely_django,
    _where_tree_defect,
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
# clone attack cannot widen the served rows (docs/feedback.md P1, asserting
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
    """A hook whose ``query.chain`` is instance-replaced FAILS CLOSED (docs/feedback.md P1-1).

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

    Proves the fix is structural (``docs/feedback.md`` P1-1: "do not fix only the
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
# (a review found consumer objects riding through the seal one edge down: a
# ``Prefetch`` queryset and a combinator-branch ``Query`` subclass)
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

    Object identity is not immutability (``docs/feedback.md`` P1-2): the removed
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
# The hardened visibility boundary -- embedded AST-node trust (docs/feedback.md
# P1-3): every node ``sql.Query.clone`` clones or the compiler later executes
# must be a trusted Django implementation, else the seal fails closed.
# ---------------------------------------------------------------------------


def test_hostile_where_subclass_fails_closed():
    """A ``WhereNode`` SUBCLASS whose ``clone`` widens the query fails closed (P1-3).

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
    """A consumer annotation expression is not a trusted Django node - fail closed (P1-3).

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
    """A non-Django join object in the alias map fails closed (P1-3)."""
    source = Category.objects.filter(is_private=False)
    source.query.alias_map = {**source.query.alias_map, "bogus": object()}
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("untrusted", "join for alias 'bogus' is a object")


def test_non_dict_select_related_fails_closed():
    """A ``select_related`` that is neither bool nor dict fails closed (P1-3)."""
    source = Category.objects.filter(is_private=False)
    source.query.select_related = object()
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("untrusted", "select_related is a object")


def test_non_str_select_related_key_fails_closed():
    """A ``select_related`` dict with a non-str key fails closed (P1-3)."""
    source = Category.objects.filter(is_private=False)
    source.query.select_related = {1: {}}
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("untrusted", "select_related key is a int")


def test_nested_select_related_value_fails_closed():
    """A nested ``select_related`` value that is not a dict tree fails closed (P1-3)."""
    source = Category.objects.filter(is_private=False)
    source.query.select_related = {"category": object()}
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("untrusted", "select_related is a object")


def test_clean_annotation_and_select_related_seal_fine():
    """A plain Django annotation + ``select_related`` dict tree seals with no defect (P1-3).

    The complement of the fail-closed AST tests: trusted Django nodes (a ``Count``
    annotation, a ``{str: {}}`` select_related tree) pass the graph validation.
    """
    source = Item.objects.select_related("category").annotate(n=models.Count("id"))
    sealed, defect = _seal_or_defect(source, Item, None)
    assert defect is None
    assert type(sealed) is models.QuerySet


# ---------------------------------------------------------------------------
# The hardened visibility boundary -- a model-less select query (docs/feedback.md
# P2-1) escapes as malformed SQL, so it must fail closed as a table defect.
# ---------------------------------------------------------------------------


def test_query_model_none_fails_closed_as_table():
    """A result whose exact ``sql.Query.model`` is ``None`` fails closed as a table defect."""
    source = Category.objects.filter(name="x")
    source.query.model = None
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("table", "NoneType")


def test_combined_branch_missing_model_fails_closed_as_table():
    """A ``combined_queries`` branch with no model fails closed as a table defect (P2-1)."""
    source = Category.objects.filter(name="a").union(Category.objects.filter(name="b"))
    source.query.combined_queries[0].model = None
    _, defect = _seal_or_defect(source, Category, None)
    assert defect == ("table", "NoneType")


# ---------------------------------------------------------------------------
# The hardened visibility boundary -- Prefetch rebuild + child-alias threading
# (docs/feedback.md P1-4).
# ---------------------------------------------------------------------------


def test_prefetch_non_str_lookup_fails_closed():
    """A non-exact-``str`` prefetch lookup entry fails closed (P1-4a)."""

    class _StrSub(str):
        pass

    _, defect = _sealed_prefetch_related_lookups((_StrSub("items"),), "X", None)
    assert defect == ("untrusted", "X prefetch lookup is a _StrSub")


def test_prefetch_non_str_path_fails_closed():
    """A ``Prefetch`` whose ``prefetch_through`` is not an exact str fails closed (P1-4a)."""
    from django.db.models import Prefetch

    pf = Prefetch("items")
    pf.__dict__["prefetch_through"] = object()
    _, defect = _sealed_prefetch_related_lookups((pf,), "X", None)
    assert defect == ("untrusted", "X prefetch path is not an exact str")


def test_prefetch_non_str_to_attr_fails_closed():
    """A ``Prefetch`` whose ``to_attr`` is not an exact str / None fails closed (P1-4a)."""
    from django.db.models import Prefetch

    pf = Prefetch("items")
    pf.__dict__["to_attr"] = object()
    _, defect = _sealed_prefetch_related_lookups((pf,), "X", None)
    assert defect == ("untrusted", "X prefetch to_attr is not an exact str or None")


def test_prefetch_unrouted_child_inherits_outer_alias():
    """An unrouted prefetch child inherits the OUTER effective alias (P1-4b)."""
    from django.db.models import Prefetch

    sealed, defect = _sealed_prefetch_related_lookups(
        (Prefetch("items", queryset=Item.objects.all()),),
        "X",
        "default",
    )
    assert defect is None
    assert sealed[0].queryset._db == "default"


def test_prefetch_cross_alias_child_fails_closed():
    """A prefetch child pinned to a DIFFERENT alias than the outer fails closed (P1-4b)."""
    from django.db.models import Prefetch

    _, defect = _sealed_prefetch_related_lookups(
        (Prefetch("items", queryset=Item.objects.using("other")),),
        "X",
        "default",
    )
    # The inner child's own ``(code: detail)`` -- here the ``alias`` defect -- is
    # carried into the message rather than collapsed into a generic string.
    assert defect == ("untrusted", "X prefetch 'items' queryset cannot be sealed (alias: other)")


def test_sliced_prefetch_child_seals_successfully():
    """A legally sliced ``Prefetch`` child seals; the rebuilt child stays a plain, sliced qs.

    Django >= 4.2 supports a sliced prefetch queryset (top-N per parent). Nothing
    refilters a prefetch child, so the outer ``sliced`` rejection does not apply one
    edge down; the child seals through ``allow_sliced=True`` while still requiring
    model rows, and the rebuilt child is a fresh plain ``QuerySet`` whose slice
    marks are preserved.
    """
    from django.db.models import Prefetch

    sealed, defect = _sealed_prefetch_related_lookups(
        (Prefetch("items", queryset=Item.objects.all()[:5]),),
        "X",
        None,
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
    _, defect = _sealed_prefetch_related_lookups((Prefetch("items", queryset=inner),), "X", None)
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
    """Sync/async parity: the async runner also re-seals an identity return (P1-2).

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
# Second adversarial round (docs/feedback.md Findings 1-6): sql.Query.clone and
# add_q are NOT no-dispatch boundaries -- their bodies dispatch bound methods on
# the graph's sub-objects. The seal now proves EVERY compiler-reachable node is a
# genuine, unshadowed Django implementation (by object identity, not __module__)
# and bakes a deferred filter onto a DETACHED clone, so clone / add_q / compile
# dispatch only trusted code and the candidate is never mutated.
# ---------------------------------------------------------------------------


def test_exact_wherenode_shadowed_clone_never_dispatches():
    """Finding 1: an EXACT ``WhereNode`` whose ``__dict__`` shadows ``clone`` fails closed.

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
    """Finding 3: an exact Django lookup leaf whose ``__dict__`` shadows ``as_sql`` fails closed.

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


def test_hostile_order_by_expression_fails_closed():
    """Finding 3: a consumer ``order_by`` expression (never walked before) fails closed.

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
    """Finding 3 / H: a consumer expression nested inside a genuine ``Func`` fails closed.

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
    """Finding 3: ``__module__`` is spoofable, so provenance is proven by object identity.

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
    """Finding 3: a ``Subquery`` wrapping a foreign inner ``Query`` fails closed.

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
    """Finding 3: a consumer expression buried in a genuine subquery's ``where`` fails closed.

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
    """Finding 2: a deferred-filter value with a hostile ``resolve_expression`` fails closed.

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
    """Finding 6: baking a deferred filter mutates only the detached clone, repeatably.

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
    """Finding 5: a non-string ``Query.__dict__`` key becomes a typed defect, not a raise.

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
    """Finding 1: a container ``sql.Query.clone`` copies must be an exact builtin.

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
    """Finding 4: an UNROUTED parent fails closed on an explicitly cross-routed child.

    When the outer effective alias is unresolved (an unrouted parent), a prefetch
    child pinned to any explicit alias must fail closed rather than being accepted
    onto a divergent database -- otherwise one resolution schedules the parent and
    its related rows across two connections.
    """
    child = Category.objects.using("other").all()
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
# Third adversarial round (docs/feedback.md P1/P2 round 3): the validation-vs-
# execution divergences that survived the prove-then-clone walk -- a poisoned
# ``base_table`` cache, a stateful ``combined_queries`` iterator, isinstance-based
# inert typing, dynamic ``as_<vendor>`` compiler methods, un-walked ``Func`` metadata /
# ``filtered_relation`` / ``extra_order_by`` state, a consumer metaclass, and
# truthiness dispatch on retained ``QuerySet`` state.
# ---------------------------------------------------------------------------


def test_poisoned_base_table_cache_fails_closed_on_real_first_alias():
    """P1: the base table is recomputed from ``alias_map``, never the poisonable cache.

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
    """P1: ``combined_queries`` must be an exact tuple before any branch is walked.

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
    """P1: a ``str`` subclass carrying ``resolve_expression`` is NOT inert.

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
    """P1: a ``str``-subclass deferred value with ``resolve_expression`` fails closed.

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
    """P1: a model instance carrying an INSTANCE-level ``resolve_expression`` fails closed.

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
    """P1: an ``as_<vendor>`` instance shadow fails closed even absent from the node class.

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
    """P1: a genuine ``Func`` whose ``arg_joiner`` is a non-string object fails closed.

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


def test_where_node_non_string_connector_fails_closed():
    """P1: a ``WhereNode`` whose ``connector`` is a non-string object fails closed.

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
    """P1: ``extra_order_by`` (emitted as raw SQL) must be an exact sequence of strings."""
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
    """P1: a consumer expression in a join's ``filtered_relation.resolved_condition`` fails closed.

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
    """P1: a join carrying a non-Django ``filtered_relation`` object fails closed."""
    _frq, alias, join = _filtered_relation_join()
    join.filtered_relation = object()
    defect = _join_defect(join, alias, set())
    assert defect == ("untrusted", f"join for alias {alias!r} filtered_relation is a object")


def test_join_defect_shadowed_filtered_relation_fails_closed():
    """P1: a genuine ``filtered_relation`` with a shadowed ``as_sql`` method fails closed.

    ``as_sql`` is a genuine class method on ``FilteredRelation``, so a shadow of it
    reports as a plain method (the "compiler method" wording is reserved for a
    dynamically-resolved ``as_<vendor>`` emitter absent from the class).
    """
    _frq, alias, join = _filtered_relation_join()
    join.filtered_relation.__dict__["as_sql"] = lambda *a, **k: None
    defect = _join_defect(join, alias, set())
    assert defect == (
        "untrusted",
        f"join for alias {alias!r} filtered_relation shadows the 'as_sql' method",
    )


def test_join_defect_unresolved_filtered_relation_is_clean():
    """A genuine join whose ``filtered_relation`` is not yet resolved carries no defect."""
    _frq, alias, join = _filtered_relation_join()
    join.filtered_relation.resolved_condition = None
    assert _join_defect(join, alias, set()) is None


def test_module_spoofing_metaclass_is_not_invoked_and_fails_closed():
    """P2: provenance reads ``__module__`` / ``__qualname__`` via ``type.__getattribute__``.

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
    """P2: a metaclass whose ``__module__`` descriptor raises fails closed, not errors.

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
    """P2: each retained ``QuerySet`` state field is pinned to its exact shape."""
    source = Category.objects.all()
    str(source.query)
    setattr(source, field, value)
    sealed, defect = _seal_or_defect(source, Category, None)
    assert sealed is None
    assert defect == ("untrusted", detail)


def test_hostile_hints_bool_and_iter_never_dispatch():
    """P2: a ``_hints`` dict subclass with a hostile ``__bool__`` / ``__iter__`` fails closed."""
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
    """P2: a ``_hints`` dict with a non-string key fails closed before it is copied."""
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
    """P2: ``_prefetch_related_lookups`` must be an exact tuple / list before iteration."""

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
# Fourth adversarial round: deferred-filter truthiness and cyclic containers.
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


def test_expr_graph_walk_terminates_on_self_referential_containers():
    """A cyclic list / dict in an expression slot terminates instead of RecursionError."""
    cyclic_list: list = []
    cyclic_list.append(cyclic_list)
    assert _expr_graph_defect(cyclic_list, set(), "where clause") is None
    cyclic_dict: dict = {}
    cyclic_dict["self"] = cyclic_dict
    assert _expr_graph_defect(cyclic_dict, set(), "where clause") is None


def test_deferred_value_walk_terminates_on_self_referential_values():
    """A cyclic Q / list / dict deferred-filter value terminates instead of RecursionError."""
    cyclic_list: list = []
    cyclic_list.append(cyclic_list)
    assert _deferred_value_defect(cyclic_list, set(), "deferred arg") is None
    cyclic_dict: dict = {}
    cyclic_dict["self"] = cyclic_dict
    assert _deferred_value_defect(cyclic_dict, set(), "deferred arg") is None
    cyclic_q = models.Q(pk=1)
    cyclic_q.children.append(cyclic_q)
    assert _deferred_value_defect(cyclic_q, set(), "deferred arg") is None


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
    defect = _expr_graph_defect([_HostileLeaf()], set(), "annotation 'x'")
    assert defect == ("untrusted", "annotation 'x' carries a _HostileLeaf node")


def test_expr_graph_dict_non_string_key_fails_closed():
    """A non-string mapping key inside an expression-graph dict slot fails closed."""
    defect = _expr_graph_defect({1: "v"}, set(), "annotation 'x'")
    assert defect == ("untrusted", "annotation 'x' has a non-string mapping key")


def test_expr_graph_dict_value_defect_propagates():
    """A hostile value inside an expression-graph dict slot fails closed."""
    defect = _expr_graph_defect({"k": _HostileLeaf()}, set(), "annotation 'x'")
    assert defect == ("untrusted", "annotation 'x' carries a _HostileLeaf node")


def test_expr_graph_wherenode_routes_to_where_walker():
    """A ``WhereNode`` reached as an expression graph node routes to the where walker."""
    from django.db.models.sql.where import WhereNode

    assert _expr_graph_defect(WhereNode(), set(), "annotation 'x'") is None


def test_expr_sequence_non_sequence_holder_fails_closed():
    """An ``order_by`` slot that is neither None/bool nor list/tuple fails closed."""
    defect = _expr_sequence_defect(object(), set(), "order_by")
    assert defect == ("untrusted", "query order_by is a object")


def test_where_tree_shared_node_visited_once():
    """A ``WhereNode`` already in ``seen`` short-circuits to ``None`` (diamond / cycle safe)."""
    from django.db.models.sql.where import WhereNode

    node = WhereNode()
    seen = {id(node)}
    assert _where_tree_defect(node, seen) is None


def test_where_tree_non_sequence_children_fails_closed():
    """A ``WhereNode`` whose ``children`` is neither list nor tuple fails closed."""
    from django.db.models.sql.where import WhereNode

    node = WhereNode()
    node.__dict__["children"] = object()
    assert _where_tree_defect(node, set()) == ("untrusted", "where node children is a object")


def test_join_shadowed_method_fails_closed():
    """A genuine ``alias_map`` join whose ``__dict__`` shadows a method fails closed."""
    source = Category.objects.filter(name="keep")
    str(source.query)
    alias, join = next(iter(source.query.alias_map.items()))
    join.__dict__["as_sql"] = lambda *a, **k: None
    defect = _join_defect(join, alias, set())
    assert defect == ("untrusted", f"join for alias {alias!r} shadows the 'as_sql' method")


def test_query_container_none_dict_attr_is_clean():
    """A ``None`` dict-container attribute is skipped (the ``continue`` branch)."""
    query = Category.objects.all().query
    query.__dict__["extra"] = None
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

    assert _query_genuineness_defect(_Foreign(Category), set()) == (
        "untrusted",
        "embedded query is a _Foreign",
    )


def test_query_genuineness_shared_query_visited_once():
    """A genuine embedded query already in ``seen`` short-circuits to ``None``."""
    query = Category.objects.all().query
    assert _query_genuineness_defect(query, {id(query)}) is None


def test_query_genuineness_shadowed_query_fails_closed():
    """An embedded query whose ``__dict__`` shadows a method fails closed."""
    query = Category.objects.all().query
    query.__dict__["add_q"] = lambda *a, **k: None
    assert _query_genuineness_defect(query, set()) == (
        "untrusted",
        "subquery instance shadows the 'add_q' method",
    )


def test_query_genuineness_container_defect_fails_closed():
    """An embedded query with a non-exact container fails closed."""
    query = Category.objects.all().query
    query.__dict__["annotations"] = {1: "v"}
    assert _query_genuineness_defect(query, set()) == (
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
    assert _query_genuineness_defect(query, set()) == ("untrusted", "embedded query is a _Foreign")


def test_deferred_value_q_non_kv_child_fails_closed():
    """A ``Q`` child that is neither a nested ``Q`` nor a ``(str, value)`` pair fails closed."""
    bad = models.Q()
    bad.children.append(object())
    assert _deferred_value_defect(bad, set(), "deferred arg") == (
        "untrusted",
        "deferred arg Q child is a object",
    )


def test_deferred_value_nested_q_child_defect_propagates():
    """A hostile value inside a nested ``Q`` child fails closed."""
    assert _deferred_value_defect(models.Q(name=_HostileLeaf()), set(), "deferred arg") == (
        "untrusted",
        "deferred arg is a _HostileLeaf",
    )


def test_deferred_value_container_member_defect_propagates():
    """A hostile member inside a deferred-value container fails closed."""
    assert _deferred_value_defect([_HostileLeaf()], set(), "deferred arg") == (
        "untrusted",
        "deferred arg is a _HostileLeaf",
    )


def test_deferred_value_dict_non_string_key_fails_closed():
    """A non-string key inside a deferred-value dict fails closed."""
    assert _deferred_value_defect({1: "v"}, set(), "deferred arg") == (
        "untrusted",
        "deferred arg mapping key is a int",
    )


def test_deferred_value_dict_member_defect_propagates():
    """A hostile value inside a deferred-value dict fails closed."""
    assert _deferred_value_defect({"k": _HostileLeaf()}, set(), "deferred arg") == (
        "untrusted",
        "deferred arg is a _HostileLeaf",
    )


def test_deferred_value_arbitrary_object_fails_closed():
    """A plain non-model, non-expression object as a deferred value fails closed."""
    assert _deferred_value_defect(_HostileLeaf(), set(), "deferred arg") == (
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
    from django.db.models.query import PROHIBITED_FILTER_KWARGS

    prohibited = next(iter(PROHIBITED_FILTER_KWARGS))
    rebuilt = sql.Query.clone(Item.objects.all().query)
    assert _bake_deferred_filter_or_defect(
        rebuilt,
        (False, (), {prohibited: True}),
        "QuerySet",
    ) == ("untrusted", "QuerySet deferred filter carries prohibited kwargs")


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
