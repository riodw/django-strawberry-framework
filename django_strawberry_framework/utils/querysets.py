"""Shared query-source, field-coercion, sync/async hook, and visibility contracts.

The neutral query-source mechanics every resolver surface shares: coerce a
``Manager`` to a ``QuerySet`` exactly once, decide whether a value is a
queryset, run the ``DjangoType.get_queryset`` visibility hook through the sync
or async path, and combine those into the list-field consumer-resolver shape.
Extracted here (the 0.0.9 DRY pass, ``docs/feedback.md`` Major 1) so list
fields, connection fields, the optimizer middleware, the Relay node defaults,
and the filter related-visibility derive all reach ONE implementation of the
contract -- ``get_queryset`` is the visibility hook, and a visibility-hook
mistake is a data-leak bug, so the routing must not be re-decided per surface.

``coerce_field_value_or_none`` (0.0.13 DRY pass) is the sibling neutral
primitive for the "raw literal -> Django field value, or nothing" safety
wrapper the Relay id decode, the raw relation-pk decode, and the ``__in``
filter member decode each need against a DIFFERENT field - single-sourcing the
coercion mechanics while leaving the field selection to each caller.

``run_in_one_sync_boundary`` (0.0.13 DRY pass) is the sibling neutral
primitive for "run a sync callable in exactly one
``sync_to_async(thread_sensitive=True)`` worker" - shared by filters /
orders / cascade permissions / mutation-form pipelines / session auth so
the off-event-loop boundary cannot drift.

The two colored visibility runners are the package's hardened ``get_queryset``
security boundary (the get_queryset-visibility-boundary decision): every
framework-owned invocation of the hook routes through them, so source
preparation (queryset shape, concrete-table, required-alias resolution,
write-pipeline pinning, evaluated refresh) and result normalization (Manager
coercion, fail-closed shape rejection, alias normalization, evaluated
refresh, hostile-clone revalidation) live in exactly one place rather than
per surface.

Caller-specific tails stay with their caller: the connection field keeps its
GraphQL non-queryset error (it calls ``normalize_query_source`` then guards),
the Relay node defaults keep their id filter, the optimizer keeps plan
building, and the filter related derive keeps its per-branch recursion. This
module owns only the source normalization + the colored visibility calls.

Cycle-safe by construction: it depends on ``django``, ``asgiref``,
``..exceptions``, and the write-transaction ContextVar helpers, so
``types/relay.py`` (imported at module top by ``types/base.py``) can import
from here without closing a load cycle, and it never imports back into
filters / orders / mutations / permissions.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any

from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.db import models

from ..exceptions import ConfigurationError
from .write_transaction import base_locked_queryset, current_write_pipeline, pin_write_queryset


class SyncMisuseError(ConfigurationError, RuntimeError):
    """Raised when a sync resolver context encounters an async ``get_queryset``.

    Typed marker for the "async ``get_queryset`` hook invoked from a
    sync resolver" misuse. Multiple-inherits ``ConfigurationError``
    AND ``RuntimeError`` so callers catching either base class still
    match:

    - ``except ConfigurationError`` (the package's convention for
      configuration-time errors).
    - ``except RuntimeError`` (consumer code catching ``RuntimeError``
      after the ``FilterSet.apply`` dispatcher rethrow continues to
      work).

    The dispatcher in ``filters/sets.py::FilterSet.apply`` catches
    this subclass directly. Consumers who want a focused catch should
    also match the subclass. Exported through
    ``django_strawberry_framework`` (and re-exported from
    ``django_strawberry_framework.types.relay`` for back-compat) so it
    can be imported without reaching into this private ``utils`` module.
    """


def reject_async_in_sync_context(
    value: Any,
    *,
    owner: str,
    method: str,
    context: str,
    recourse: str,
) -> Any:
    """Guard a synchronous hook result against any awaitable return.

    Three sync pipeline seams invoke a consumer-overridable hook that
    Decision 9 / Decision 15 allow to be sync OR async: the ``get_queryset``
    visibility hook (``apply_type_visibility_sync``) and the two write
    authorization hooks (``check_permission`` / a ``permission_classes``
    entry's ``has_permission``). None can await - the whole ORM pipeline runs
    synchronously (under one ``sync_to_async`` worker on the async surface),
    so an ``async def`` override returns an orphaned coroutine. Treating that
    truthy coroutine as success would be a silent bug - an authorization
    BYPASS for the permission hooks - so it is rejected loudly.

    Awaitables cannot be consumed by these sync pipelines. Native coroutines
    are closed and futures are cancelled before ``SyncMisuseError`` is raised;
    other awaitables have no standard cleanup protocol. Native-coroutine error
    text is preserved for compatibility. Otherwise ``value`` is returned
    unchanged, so callers read ``x = reject_async_in_sync_context(x, ...)``.
    """
    if inspect.isawaitable(value):
        kind = "a coroutine" if inspect.iscoroutine(value) else "an awaitable"
        _dispose_sync_awaitable(value)
        raise SyncMisuseError(
            f"{owner}.{method} returned {kind} in a sync {context} context. {recourse}",
        )
    return value


def _dispose_sync_awaitable(value: Any) -> None:
    """Release a rejected awaitable without awaiting it, when possible.

    Native coroutines are closed and futures cancelled; other awaitables have
    no standard cleanup protocol. Used by every boundary that refuses an
    awaitable - the sync misuse guards AND the async runners' nested /
    residual awaitable rejections (those must not recursively await an
    unbounded chain, so disposal is the only safe handling there too).
    """
    if inspect.iscoroutine(value):
        value.close()
    elif asyncio.isfuture(value):
        value.cancel()


def model_for(type_cls: type) -> type[models.Model]:
    """Return the Django model registered to a ``DjangoType``.

    Centralizes the ``type_cls.__django_strawberry_definition__.model`` lookup
    so every model-only read shares one source of truth with the
    queryset-variant seed below - the Relay node / id helpers, the connection
    total-order derive, the write pipeline's target-model reads, and the
    cascade-permission walk. Callers are responsible for ``type_cls`` being a
    registered ``DjangoType``; a missing definition surfaces as a raw
    ``AttributeError``.
    """
    return type_cls.__django_strawberry_definition__.model


def initial_queryset(type_cls: type) -> models.QuerySet:
    """Return ``model._default_manager.all()`` for a ``DjangoType``'s model.

    Step 1 of the Relay node defaults' four-step shape and the default
    resolver seed for list / connection fields. Seeds from
    ``model_for(type_cls)`` so the model lookup stays single-sited; every
    surface that needs a fresh unevaluated base queryset shares this one
    source. Callers are responsible for ``type_cls`` being a registered
    ``DjangoType``; a missing definition surfaces as a raw ``AttributeError``.
    """
    return model_for(type_cls)._default_manager.all()


def normalize_query_source(source: Any) -> tuple[Any, bool]:
    """Coerce a ``Manager`` to its ``QuerySet`` and report whether the result is one.

    The single Manager-to-QuerySet coercion shared by every resolver surface
    that accepts a consumer-supplied source (``DjangoListField`` /
    ``DjangoConnectionField`` consumer ``resolver=`` returns, the optimizer
    middleware's root return). A ``Manager`` (the ``Model.objects`` shorthand)
    becomes a fresh unevaluated ``QuerySet`` via ``.all()``; a ``QuerySet``
    passes through; a non-queryset iterable (a Python list / generator) passes
    through unchanged with ``is_queryset=False`` so the caller can short-circuit
    (pass it through, or raise its own GraphQL-specific error before pagination).

    Returns ``(source, is_queryset)`` rather than deciding the tail itself so
    each caller keeps its colored steps (``apply_type_visibility_*`` / the
    connection sidecar guard / the optimizer plan) explicit, never hidden behind
    a maybe-await abstraction.
    """
    if isinstance(source, models.Manager):
        source = source.all()
    return source, isinstance(source, models.QuerySet)


def coerce_field_value_or_none(field: models.Field, value: Any) -> Any:
    """Coerce ``value`` through ``field``'s ``to_python`` + ``run_validators``; ``None`` if invalid.

    The single "raw literal -> Django field value, or nothing" safety wrapper
    three independent call sites each grew their own copy of: the Relay
    ``GlobalID`` id-attr coercion (``relay.py::_coerce_pk_or_none``), the raw
    relation-pk coercion (``utils/write_values.py::coerce_relation_pk_or_none``),
    and the ``__in`` filter member coercion
    (``filters/base.py::_coerce_int_in_members``). ``to_python`` is a pure type
    cast that does NOT range-check, so a syntactically-valid but out-of-range
    literal (e.g. a pk past a backend's signed-64-bit column range) would
    otherwise reach a ``pk__in`` / ``filter`` call and raise a raw backend
    ``OverflowError`` (``Python int too large to convert to SQLite INTEGER``);
    the field's own validators (``integer_field_range`` Min/MaxValueValidators,
    etc.) reject it here as a ``ValidationError`` instead, and a non-numeric
    literal fails ``to_python`` itself. Every Django core field wraps its
    ``to_python`` failure in ``ValidationError`` already; ``TypeError`` /
    ``ValueError`` are caught too as a defensive superset for a field whose
    ``to_python`` raises one of those directly.

    Every caller treats ``None`` the same way - "identifies no row": dropped
    from a query, or mapped to a not-found / invalid sentinel - never a raw
    crash. WHICH field to coerce against is a genuine per-caller decision (a
    Relay type's resolved id field, a related model's pk, an arbitrary filtered
    column) and stays at each call site; only the coercion mechanics are
    single-sourced here.
    """
    try:
        coerced = field.to_python(value)
        field.run_validators(coerced)
    except (TypeError, ValueError, ValidationError):
        return None
    return coerced


_RELAY_ASYNC_RECOURSE = (
    "The Relay node defaults only await async get_queryset hooks on the async "
    "branch; either invoke the Relay node default from an async resolver, or "
    "redefine get_queryset as a sync method."
)


def sync_pipeline_recourse(flavor_noun: str) -> str:
    """Build the ``SyncMisuseError`` recourse a sync write pipeline appends (spec-039 Md2).

    The three write flavors (model / form / serializer) each raise a
    ``SyncMisuseError`` naming the SAME recourse when an ``async def get_queryset`` is
    met inside their (synchronous) ORM pipeline - byte-identical except the flavor
    subject. Single-sites that sentence so the three ``*_ASYNC_RECOURSE`` module
    constants cannot drift; each flavor still keeps its own named constant
    (``_MUTATION_ASYNC_RECOURSE`` / ``_FORM_ASYNC_RECOURSE`` /
    ``_SERIALIZER_ASYNC_RECOURSE``), now computed from this template. NOT used for the
    Relay recourse (``_RELAY_ASYNC_RECOURSE`` - async IS possible there) or the
    permission recourse (about ``has_permission`` / ``check_permission``, not
    ``get_queryset``), which are genuinely different wordings.
    """
    return (
        f"A {flavor_noun} runs its ORM pipeline synchronously (under one sync_to_async "
        "call on the async surface), so it cannot await an async get_queryset hook; "
        "redefine the target type's get_queryset as a sync method."
    )


async def run_in_one_sync_boundary(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Run ``fn(*args, **kwargs)`` in ONE ``sync_to_async(thread_sensitive=True)`` worker.

    The generic one-boundary primitive (spec-040 D17 / P3): every async surface
    that must keep a consumer-overridable sync hook (permission check, form
    filter body, cascade walk, mutation/form write pipeline, session auth) off
    the event loop shares this call, so the boundary discipline (one worker per
    resolution, ``thread_sensitive=True``, never per-step hops) cannot drift.
    A ``sync_to_async`` worker is itself a sync context, so the standing
    ``SyncMisuseError`` guards still fire inside ``fn``.

    Neutral home: lives here with the sibling ``reject_async_in_sync_context``
    primitive (cycle-safe utils substrate) rather than under ``mutations/``, so
    read-side modules (``filters/``, ``orders/``, root ``permissions.py``) can
    reuse it without a root-into-subpackage import.
    """
    return await sync_to_async(fn, thread_sensitive=True)(*args, **kwargs)


def _combined_query_table_defect(query: Any, model: type[models.Model]) -> str | None:
    """Return the name of the first branch model reading a table other than ``model``'s.

    Validating only ``QuerySet.model`` is not sufficient to prove which model
    tables can contribute result rows. Django lets a combined queryset
    (``.union()`` / ``.intersection()`` / ``.difference()``) report the outer
    model on ``QuerySet.model`` while a branch ``Query`` reads another model's
    table; with compatible projections (``.only(...)``/``.values(...)``) the
    branch rows materialize as the outer model, so another table's rows would
    cross the boundary. The public ``QuerySet.model`` is also mutable and can
    disagree with the SQL-bearing ``QuerySet.query.model``. Validate the
    ``Query.model`` and recurse through every ``query.combined_queries`` branch
    that can contribute result rows; returns the first offending model name (or
    ``None`` when every contributing table is ``model``'s concrete table).
    """
    concrete = model._meta.concrete_model
    query_model = getattr(query, "model", None)
    if query_model is not None and query_model._meta.concrete_model is not concrete:
        return query_model.__name__
    for branch in getattr(query, "combined_queries", ()) or ():
        defect = _combined_query_table_defect(branch, model)
        if defect is not None:
            return defect
    return None


def _visibility_defect(
    value: Any,
    model: type[models.Model],
    required_alias: str | None,
    *,
    strict: bool = False,
) -> tuple[str, str] | None:
    """Return the first visibility-boundary defect in ``value``, or ``None``.

    The shared shape check behind both boundary validation sites (the source
    preparation and the hook-result normalization): a real ``QuerySet`` whose
    every contributing table is the registered type's concrete table (proxy
    siblings share the table and are compatible; unrelated models, MTI
    children, and cross-model combined-query branches are not), routed
    consistently with the resolution's required alias. The table check spans
    the public ``QuerySet.model``, the SQL-bearing ``QuerySet.query.model``,
    and every ``combined_queries`` branch, so a union that reads another
    model's table (or a queryset whose public model disagrees with its query
    model) cannot slip rows past the boundary.

    Non-strict mode is the pre-normalization check: an UNROUTED value
    (``_db is None``) is not a defect - normalization repins it, and with no
    concrete required alias the hook may route itself. Strict mode is the
    post-clone revalidation (a consumer-overridable ``.all()`` / ``.using()``
    just ran, so a hostile ``QuerySet`` subclass may have lied): ``value._db``
    must equal ``required_alias`` EXACTLY - a plain ``None`` here means "the
    effective alias captured before the clone was unrouted, so the clone must
    stay unrouted", distinct from the non-strict "no requirement yet" - and
    the value must be unevaluated (cached rows surviving the boundary would
    serve rows no hook filtered). Returns ``(code, detail)`` with ``code`` in
    ``{"type", "table", "alias", "evaluated"}``.
    """
    if not isinstance(value, models.QuerySet):
        return ("type", type(value).__name__)
    if value.model._meta.concrete_model is not model._meta.concrete_model:
        return ("table", value.model.__name__)
    branch_defect = _combined_query_table_defect(value.query, model)
    if branch_defect is not None:
        return ("table", branch_defect)
    if strict:
        if value._db != required_alias:
            return ("alias", str(value._db))
    elif required_alias is not None and value._db is not None and value._db != required_alias:
        return ("alias", str(value._db))
    if strict and value._result_cache is not None:
        return ("evaluated", type(value).__name__)
    return None


def _visibility_result_error(
    type_cls: type,
    model: type[models.Model],
    required_alias: str | None,
    defect: tuple[str, str],
    render_error: Any,
) -> ConfigurationError:
    """Build the fail-closed error for a defective ``get_queryset`` result.

    ``render_error`` is the caller-supplied error-rendering seam: a
    ``(code, detail) -> str`` callable whose message replaces the default
    wording wholesale. The cascade passes one so its path-rich per-edge
    prose (``"... for the cascade subquery on Model.field ..."``) survives
    the checks moving into this shared boundary; surfaces without bespoke
    prose take the defaults below.
    """
    code, detail = defect
    if render_error is not None:
        return ConfigurationError(render_error(code, detail))
    if code == "type":
        return ConfigurationError(
            f"{type_cls.__name__}.get_queryset must return a QuerySet or Manager of "
            f"{model.__name__} rows; got {detail}. A list / generator / iterable has no "
            f"lazy query for the surface to compose into, and None discards the "
            f"visibility contract entirely.",
        )
    if code == "table":
        return ConfigurationError(
            f"{type_cls.__name__}.get_queryset returned a {detail} queryset; the "
            f"visibility contract composes over {model.__name__}'s concrete table "
            f"(proxy siblings are compatible, MTI children and unrelated models are not).",
        )
    if code == "alias":
        return ConfigurationError(
            f"{type_cls.__name__}.get_queryset returned a queryset routed to alias "
            f"{detail!r}, but this resolution is pinned to alias {required_alias!r}; "
            f"a visibility hook cannot re-route a pinned resolution. Remove the "
            f".using(...) call.",
        )
    # ``code == "evaluated"`` -- the only remaining defect the shared checker
    # emits; an unhandled future code would fall through silently, so this
    # last branch is unconditional.
    return ConfigurationError(
        f"{type_cls.__name__}.get_queryset normalization required a fresh clone, but "
        f"{detail}.all() preserved cached rows instead of returning an unevaluated "
        f"queryset; rows cached before the visibility boundary must never survive it.",
    )


def _revalidated_visibility_clone(
    value: Any,
    type_cls: type,
    model: type[models.Model],
    required_alias: str | None,
    render_error: Any,
) -> models.QuerySet:
    """Fail closed unless a just-cloned value still satisfies the boundary invariants.

    Runs after every consumer-overridable clone operation (``Manager.all()``,
    ``QuerySet.all()``, ``QuerySet.using()``): a hostile ``QuerySet`` subclass
    that returns itself, returns a non-queryset, changes model or alias, or
    preserves cached rows must not slip normalized-looking state past the
    boundary. Strict mode: the clone must be routed to the required alias
    exactly and must be unevaluated.
    """
    defect = _visibility_defect(value, model, required_alias, strict=True)
    if defect is not None:
        raise _visibility_result_error(type_cls, model, required_alias, defect, render_error)
    return value


def _prepared_visibility_source(
    type_cls: type,
    queryset: Any,
) -> tuple[models.QuerySet, str | None]:
    """Validate and prepare the source queryset before the visibility hook runs.

    Returns ``(queryset, required_alias)``. The source must already be a real
    ``QuerySet`` over the registered type's concrete table (resolver-source
    ``Manager`` coercion stays in ``normalize_query_source``; framework-created
    seeds are querysets by construction) - anything else fails closed before
    consumer code runs. The required alias is resolved in priority order:

    1. An active write pipeline's alias - the source is pre-pinned through
       ``pin_write_queryset``, which fail-closes an explicitly divergent
       source alias rather than silently overwriting it.
    2. The source's own explicit ``queryset._db`` (a caller that routed with
       ``.using(...)`` keeps that routing through the hook).
    3. ``None`` - no required alias; an unpinned read hook keeps its
       documented ability to choose ``.using(alias)`` itself.

    An already-evaluated source is refreshed with ``.all()`` so cached rows
    never reach (or bypass) the hook, then strictly revalidated - the refresh
    calls a consumer-overridable clone method. Preparation composes lazy
    query state only; it executes zero SQL.
    """
    model = model_for(type_cls)
    defect = _visibility_defect(queryset, model, None)
    if defect is not None:
        code, detail = defect
        if code == "type":
            raise ConfigurationError(
                f"apply_type_visibility requires a QuerySet of {model.__name__} rows "
                f"for {type_cls.__name__}; got {detail}. Coerce a Manager with .all(); "
                f"a list has no lazy query for the hook to narrow.",
            )
        # ``code == "table"`` -- the only other defect reachable with no
        # required alias on an unevaluated non-strict check.
        raise ConfigurationError(
            f"apply_type_visibility for {type_cls.__name__} requires a QuerySet over "
            f"{model.__name__}'s concrete table; got a {detail} queryset (proxy "
            f"siblings are compatible, MTI children and unrelated models are not).",
        )
    pipeline = current_write_pipeline()
    if pipeline is not None:
        queryset = pin_write_queryset(
            queryset,
            pipeline.alias,
            owner=f"The {type_cls.__name__} visibility source",
        )
        required_alias = pipeline.alias
    else:
        required_alias = queryset._db
    if queryset._result_cache is not None:
        queryset = queryset.all()
    return (
        _revalidated_visibility_clone(queryset, type_cls, model, required_alias, None),
        required_alias,
    )


def _normalized_visibility_result(
    type_cls: type,
    result: Any,
    required_alias: str | None,
    render_error: Any = None,
) -> models.QuerySet:
    """Normalize a ``get_queryset`` hook result into a composable, correctly-routed queryset.

    The shared result contract both colored visibility runners apply (the
    hardened boundary): a ``Manager`` is coerced exactly once through
    ``.all()``; anything that is not then a ``QuerySet`` whose every
    contributing table is the registered type's concrete table (``None``,
    lists, generators, async generators, custom iterables, unrelated /
    MTI-child models, cross-model unions) fails closed. Alias handling honors
    the prepared requirement: an unpinned result is normalized onto the
    required alias with ``.using(required_alias)``, an explicitly matching
    result is accepted, an explicitly divergent one is rejected; with no
    required alias the hook keeps its documented ability to route reads
    itself.

    The alias the result must ultimately carry - the ``effective_alias`` - is
    captured HERE, after coercion and repin but before any refresh clone: the
    required alias when one was pinned, else the hook's own explicit
    ``_db`` choice (a concrete alias it selected, or ``None`` for an
    unrouted read). An evaluated result is then re-cloned with ``.all()`` so
    cached rows never survive the boundary, and every consumer-overridable
    clone is strictly revalidated against ``effective_alias`` (hostile-subclass
    containment) - so a hostile ``.all()`` cannot silently move the read to a
    different database after the hook chose its alias. Normalization composes
    lazy query state only - filters, annotations, projections, ordering, and
    queryset subclasses pass through - and executes zero SQL.
    """
    model = model_for(type_cls)
    if isinstance(result, models.Manager):
        result = result.all()
    defect = _visibility_defect(result, model, required_alias)
    if defect is not None:
        raise _visibility_result_error(type_cls, model, required_alias, defect, render_error)
    if required_alias is not None and result._db is None:
        result = result.using(required_alias)
    # ``result._db`` is only read for the no-required-alias branch, where the
    # defect check above proved ``result`` is a QuerySet; the ``.using(...)``
    # repin (required alias present) is a consumer-overridable clone that a
    # hostile subclass could turn into a non-queryset, so the evaluated-refresh
    # guard stays ``isinstance``-gated and the final revalidation fails it closed.
    effective_alias = required_alias if required_alias is not None else result._db
    if isinstance(result, models.QuerySet) and result._result_cache is not None:
        result = result.all()
    return _revalidated_visibility_clone(result, type_cls, model, effective_alias, render_error)


def apply_type_visibility_sync(
    type_cls: type,
    queryset: models.QuerySet,
    info: Any,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
    *,
    render_error: Any = None,
) -> models.QuerySet:
    """Run ``type_cls.get_queryset`` in a sync context; reject async hooks loudly.

    Decision 9 makes a consumer's ``DjangoType.get_queryset`` allowed to
    be sync or async, but a sync resolver context cannot await an async
    hook safely (event-loop edge cases dominate the bridge). On the sync
    path we therefore close the unawaited coroutine to silence the
    "coroutine was never awaited" warning and raise a named
    ``SyncMisuseError`` (a ``ConfigurationError`` subclass that also
    inherits ``RuntimeError``) that points the consumer at the correct
    recourse for the surface that called in.

    The source is prepared and the result normalized through the shared
    hardened boundary (``_prepared_visibility_source`` /
    ``_normalized_visibility_result``): source shape validation, required-
    alias resolution (write pipeline > explicit source ``.using`` > none),
    evaluated-cache refresh on both sides, Manager coercion, fail-closed
    rejection of every other result shape, and hostile-clone revalidation.
    ``SyncMisuseError`` stays reserved for this sync boundary; every other
    defect is a plain ``ConfigurationError``.

    ``async_recourse`` is the surface-specific guidance appended to the
    error. It defaults to the Relay node-defaults wording; callers whose
    recourse differs pass their own (the cascade, for instance, has no
    async-native walk -- its twin wraps this same sync walk -- so it tells
    the consumer to make the target hook sync or scope ``fields=`` rather
    than reach for an async resolver that cannot help, feedback M1).
    ``render_error`` is the result-normalization error seam
    (``_visibility_result_error``): the cascade supplies its path-rich
    per-edge prose; other surfaces take the shared defaults.
    """
    queryset, required_alias = _prepared_visibility_source(type_cls, queryset)
    result = type_cls.get_queryset(queryset, info)
    result = reject_async_in_sync_context(
        result,
        owner=type_cls.__name__,
        method="get_queryset",
        context="resolver",
        recourse=async_recourse,
    )
    return _normalized_visibility_result(type_cls, result, required_alias, render_error)


def visibility_scoped_related_queryset(
    related_type: type,
    info: Any,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
) -> models.QuerySet:
    """Return a related type's base queryset scoped by its ``get_queryset`` visibility hook.

    The one-line composition of the two primitives every relation-visibility check
    shares - ``apply_type_visibility_sync(related_type, initial_queryset(
    related_type), info, recourse)``. Single-sourced so the model relation decode
    (``mutations/resolvers.py``) and the form relation decode
    (``forms/resolvers.py``) provably apply the SAME related-type ``get_queryset``
    (the cross-flavor security invariant spec-038 claims), rather than re-spelling
    the composition at each site. ``async_recourse`` stays a parameter: the model
    and form paths pass their own surface-specific wording.
    """
    return apply_type_visibility_sync(
        related_type,
        initial_queryset(related_type),
        info,
        async_recourse,
    )


def related_visibility_queryset(
    related_model: type,
    info: Any,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
) -> models.QuerySet | None:
    """Return the related model's visibility-scoped queryset, or ``None`` when it has no primary.

    The ``registry.get(related_model)`` resolve + the "scope through the primary
    ``DjangoType.get_queryset`` visibility hook, else no contract" branch that four
    relation surfaces open with (``visible_related_object`` /
    ``visible_related_objects`` here, the model
    ``mutations/resolvers.py::_raw_pk_relation_error``, and the serializer
    ``rest_framework/resolvers.py::_scope_specs_over_serializer``). ``None`` means
    "the related model has no registered primary ``DjangoType``" - a raw-pk relation
    with no visibility contract - and each caller keeps its OWN None-handling
    explicit (default-manager existence, an existence-only check, or skip), because
    that tail genuinely diverges per surface. Single-sites only the resolve + the
    visibility-scoping call, so the ONE place a drift is a data-leak bug class is
    written once (spec-039 Md3). An ``async def get_queryset`` met here raises
    ``SyncMisuseError`` (inherited from ``apply_type_visibility_sync``).
    """
    from ..registry import registry

    related_type = registry.get(related_model)
    if related_type is None:
        return None
    return visibility_scoped_related_queryset(related_type, info, async_recourse)


def related_visibility_queryset_or_default(
    related_model: type,
    info: Any,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
) -> models.QuerySet:
    """The visibility-scoped queryset, falling back to the default manager (DRY review C4).

    The "no primary ``DjangoType`` => default-manager, no visibility contract"
    fallback ``visible_related_object`` and ``visible_related_objects`` both
    opened with - a security-adjacent rule, now single-bodied: a related model
    with a registered primary is scoped through its ``get_queryset`` visibility
    hook; one without gets its plain ``_default_manager.all()`` (existence
    semantics only). Each caller keeps its own tail (``.filter(pk=pk).first()``
    vs the batched ``pk__in`` present-set).
    """
    queryset = related_visibility_queryset(related_model, info, async_recourse)
    if queryset is None:
        return related_model._default_manager.all()
    return queryset


def _stringified(pks: Any) -> set[str]:
    """Stringify a pk collection into the type-agnostic comparison basis (DRY review C5).

    The ``{str(pk) for pk in ...}`` coercion both membership helpers share, so
    the comparison basis (an int pk and its ``"3"`` string form compare equal -
    the GlobalID-in-filter string-explosion class) has exactly one body.
    """
    return {str(pk) for pk in pks}


def stringified_pks_present(queryset: models.QuerySet, query_pks: Any) -> set[str]:
    """Return the stringified pks among ``query_pks`` actually present in ``queryset`` (one query).

    The ``{str(pk) for pk in queryset.filter(pk__in=...).values_list("pk", flat=True)}``
    lookup the relation membership checks share (spec-039 Md4): the model
    ``mutations/resolvers.py::_relation_membership_error`` and the serializer
    ``visible_related_objects`` both build this present-set in one query, stringifying
    each pk for a type-agnostic membership compare (an int pk and its ``"3"`` string
    form compare equal). Single-sites the query + the str-coercion so the
    no-existence-leak comparison basis cannot drift.

    Inside an active write pipeline (``utils/write_transaction.py``) the query is
    pinned to the operation's write alias - a hook-re-routed queryset fails
    closed - and, when the operation locks (``Meta.select_for_update``), the
    membership read doubles as the relation-target row lock: a base-manager
    ``SELECT ... FOR UPDATE`` constrained by the (pinned) queryset's pk subquery,
    so an FK / M2M target confirmed visible here cannot be deleted out from under
    the write before the transaction commits. Read surfaces run with no pipeline
    context and are byte-unchanged.
    """
    pipeline = current_write_pipeline()
    if pipeline is not None:
        queryset = pin_write_queryset(queryset, pipeline.alias)
        if pipeline.lock:
            queryset = base_locked_queryset(queryset.model, pipeline.alias, queryset)
    return _stringified(queryset.filter(pk__in=list(query_pks)).values_list("pk", flat=True))


def pks_all_present(declared_pks: Any, present: set[str]) -> bool:
    """Return whether every ``declared_pks`` member (stringified) is in ``present`` (spec-039 Md4).

    The subset-membership test the model relation guard
    (``mutations/resolvers.py::_relation_membership_error``) and the serializer M2M
    decoder (``rest_framework/resolvers.py::_decode_relation_multi``) share: a
    ``declared`` set is fully present iff its stringified members are a subset of the
    ``present`` set (typically from ``stringified_pks_present``). A missing / hidden
    member fails the subset check, which each caller maps to the uniform field-keyed
    relation error - the same no-existence-leak outcome.
    """
    return _stringified(declared_pks) <= present


def visible_related_object(
    related_model: type,
    pk: Any,
    info: Any,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
) -> Any | None:
    """Resolve the VISIBLE related object by pk through the related primary's ``get_queryset``.

    The object-returning visibility-on-every-branch query, promoted from
    ``forms/resolvers.py::_visible_related_object`` (spec-039 P1.1) so the form AND
    serializer relation decoders share ONE implementation rather than forking a
    second object-returning decoder. Resolves the related model's primary
    ``DjangoType`` via the registry and runs the SAME visibility hook every read
    surface applies (``visibility_scoped_related_queryset`` =
    ``apply_type_visibility_sync(initial_queryset(...))``), so a writer cannot
    attach a row they could not *see*. Returns the visible object or ``None``
    (hidden / missing - the caller maps ``None`` to the field-keyed ``FieldError``,
    indistinguishable). The decoder needs the OBJECT (the form converts it to its
    ``to_field_name`` key; the serializer reduces it to the pk), which the ``036``
    ``_relation_visibility_error`` does not return, so it cannot call that helper -
    but it reuses the same primitives so the query shape is identical. An ``async
    def get_queryset`` met here raises ``SyncMisuseError``.

    The related model has a primary type only when a typed relation input was
    generated for it; a raw-pk relation's primary is resolved the same way
    (``registry.get``), and a model with no primary still resolves via the default
    manager (no visibility contract to apply). ``async_recourse`` stays a parameter:
    the form and serializer paths pass their own surface-specific wording, matching
    ``visibility_scoped_related_queryset``.

    The helper accepts a raw pk AFTER a flavor-specific decoder has chosen that
    branch; it does NOT imply every generated GraphQL relation input accepts both a
    raw pk and a GlobalID (the input exposes one strategy-dependent shape).
    """
    # The visibility-or-default-manager base is single-sited in
    # ``related_visibility_queryset_or_default`` (DRY review C4). Inside an
    # active write pipeline the read is pinned to the write alias (fail-closed on
    # a hook alias switch) and - when the operation locks - acquired as a
    # base-manager ``FOR UPDATE`` constrained by the visibility pk subquery, the
    # same relation-target lock the batched membership check applies.
    queryset = related_visibility_queryset_or_default(related_model, info, async_recourse)
    pipeline = current_write_pipeline()
    if pipeline is not None:
        queryset = pin_write_queryset(queryset, pipeline.alias)
        if pipeline.lock:
            queryset = base_locked_queryset(related_model, pipeline.alias, queryset)
    return queryset.filter(pk=pk).first()


def visible_related_objects(
    related_model: type,
    pks: Any,
    info: Any,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
) -> set:
    """Return the VISIBLE pks among ``pks`` in ONE visibility-scoped ``pk__in`` query (spec-039 rev6 #3).

    The BATCHED counterpart to ``visible_related_object``: instead of one visibility query per
    id (the per-element multi-relation decode), decode/type-check all ids first, then confirm
    the whole set's visibility in ONE ``pk__in`` query through the related primary
    ``DjangoType.get_queryset`` (or the target's default manager when no primary is registered -
    no visibility contract). Returns the set of pks actually visible (stringified for a
    type-agnostic membership compare); the caller asserts the REQUESTED set is a subset, so a
    hidden / missing member collapses to the same field-keyed relation error (no existence
    leak), exactly as the single decoder does. An ``async def get_queryset`` raises
    ``SyncMisuseError``. ``related_model`` has a primary type only when a typed relation input
    was generated for it; a raw-pk relation resolves its primary the same way (``registry.get``).
    """
    # The visibility-or-default-manager base is single-sited in
    # ``related_visibility_queryset_or_default`` (DRY review C4).
    queryset = related_visibility_queryset_or_default(related_model, info, async_recourse)
    return stringified_pks_present(queryset, pks)


async def apply_type_visibility_async(
    type_cls: type,
    queryset: models.QuerySet,
    info: Any,
) -> models.QuerySet:
    """Run ``type_cls.get_queryset`` in an async context, awaiting awaitables.

    Sync ``get_queryset`` returns the queryset directly and is passed
    through. Async ``get_queryset`` returns a coroutine which is awaited
    here before the caller's tail runs - the Decision 9 contract that an
    earlier implementation broke (it called the hook synchronously then
    invoked ``.filter`` on a coroutine).

    The hook is invoked once and AT MOST ONE returned awaitable is awaited;
    a second-level awaitable after that await is malformed (an ``async def``
    returning another coroutine / future) and fails closed - never a
    recursive await over an unbounded chain. The source and result then run
    the same shared hardened boundary as the sync runner
    (``_prepared_visibility_source`` / ``_normalized_visibility_result``),
    so the two colored paths cannot drift. ``SyncMisuseError`` stays
    reserved for sync boundaries: every defect here is a plain
    ``ConfigurationError``.
    """
    queryset, required_alias = _prepared_visibility_source(type_cls, queryset)
    result = type_cls.get_queryset(queryset, info)
    if inspect.isawaitable(result):
        result = await result
        if inspect.isawaitable(result):
            _dispose_sync_awaitable(result)
            raise ConfigurationError(
                f"{type_cls.__name__}.get_queryset resolved to a nested awaitable; an "
                f"async get_queryset must resolve to a QuerySet (or Manager) after ONE "
                f"await, and an unbounded awaitable chain is never consumed.",
            )
    return _normalized_visibility_result(type_cls, result, required_alias)


def reject_awaitable_sync_source(source: Any, type_cls: type) -> None:
    """Reject an awaitable source from a sync list or connection resolver.

    A plain ``def`` that returns an awaitable is committed to the sync field
    path. Passing that value onward would either skip queryset visibility or
    leak a Strawberry pagination error, so both field factories share this
    boundary.
    """
    if not inspect.isawaitable(source):
        return
    _dispose_sync_awaitable(source)
    raise SyncMisuseError(
        f"A sync {type_cls.__name__} consumer resolver returned an awaitable. "
        "Declare the resolver `async def` (or use an async callable) so the "
        "field awaits it and applies the get_queryset visibility hook; a plain "
        "`def` resolver that returns an awaitable is committed to the sync path "
        "and passing it through would silently skip get_queryset.",
    )


def reject_residual_async_source(source: Any, type_cls: type) -> None:
    """Reject a residual awaitable from an already-awaited async consumer resolver.

    Both async consumer pipelines await the consumer ``resolver=`` return
    exactly once before the value reaches source normalization: the list
    field's ``post_process_queryset_result_async`` and the connection field's
    ``connection.py::_pipeline_async``. A value that is STILL awaitable after
    that await is an ``async def`` resolver that resolved to another awaitable;
    it is neither a ``QuerySet`` nor a legitimate plain iterable, so the
    non-queryset branch would pass it through and silently SKIP the
    ``get_queryset`` visibility hook - a data-leak escape. The awaitable is
    disposed (never recursively awaited over an unbounded chain, matching the
    async runner's nested-awaitable handling) and the resolution fails closed.

    Single-sited here, beside ``reject_awaitable_sync_source`` (the sync twin),
    so the list and connection async pipelines cannot drift on the one boundary
    where a miss skips visibility - the connection pipeline previously lacked
    this guard, letting a nested async connection resolver bypass the hook.
    """
    if not inspect.isawaitable(source):
        return
    _dispose_sync_awaitable(source)
    raise ConfigurationError(
        f"An async {type_cls.__name__} consumer resolver resolved to another "
        f"awaitable after being awaited; a nested awaitable is neither a QuerySet "
        f"nor a plain iterable, and passing it through would silently skip the "
        f"get_queryset visibility hook. Return the queryset (or iterable) directly.",
    )


def post_process_queryset_result_sync(type_cls: type, result: Any, info: Any) -> Any:
    """Normalize a consumer-resolver return then apply visibility (sync).

    The list-field consumer-resolver shape: a ``Manager`` is coerced to a
    ``QuerySet`` (the field wrapper owns the coercion), a ``QuerySet`` runs the
    type's ``get_queryset`` visibility hook, and a non-queryset Python
    list / generator passes through unchanged. The default-resolver path bypasses
    this (its source is already ``initial_queryset(...)``, a known ``QuerySet``).

    An awaitable reaching here is rejected loudly through the single-sited
    ``reject_awaitable_sync_source`` guard, which keeps the invariant that a
    consumer ``QuerySet`` return is never resolved without its visibility hook.
    """
    reject_awaitable_sync_source(result, type_cls)
    source, is_queryset = normalize_query_source(result)
    if is_queryset:
        return apply_type_visibility_sync(type_cls, source, info)
    return source


async def post_process_queryset_result_async(type_cls: type, result: Any, info: Any) -> Any:
    """Async sibling of ``post_process_queryset_result_sync``.

    The caller awaits the consumer coroutine BEFORE handing the result here so
    the queryset branch sees the awaited value, not the coroutine itself. A
    RESIDUAL awaitable - an already-awaited async consumer resolver that
    resolved to another awaitable - fails closed through the shared
    ``reject_residual_async_source`` guard (also used by the connection async
    pipeline): it is neither a queryset nor a legitimate plain-iterable return,
    and passing it through the non-queryset branch would skip the
    ``get_queryset`` visibility hook.
    """
    reject_residual_async_source(result, type_cls)
    source, is_queryset = normalize_query_source(result)
    if is_queryset:
        return await apply_type_visibility_async(type_cls, source, info)
    return source
