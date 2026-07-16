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
    """Release an awaitable rejected at a synchronous boundary when possible."""
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


def apply_type_visibility_sync(
    type_cls: type,
    queryset: models.QuerySet,
    info: Any,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
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

    ``async_recourse`` is the surface-specific guidance appended to the
    error. It defaults to the Relay node-defaults wording; callers whose
    recourse differs pass their own (the cascade, for instance, has no
    async-native walk -- its twin wraps this same sync walk -- so it tells
    the consumer to make the target hook sync or scope ``fields=`` rather
    than reach for an async resolver that cannot help, feedback M1).
    """
    result = type_cls.get_queryset(queryset, info)
    return reject_async_in_sync_context(
        result,
        owner=type_cls.__name__,
        method="get_queryset",
        context="resolver",
        recourse=async_recourse,
    )


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
    """
    result = type_cls.get_queryset(queryset, info)
    if inspect.isawaitable(result):
        result = await result
    return result


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
    the queryset branch sees the awaited value, not the coroutine itself.
    """
    source, is_queryset = normalize_query_source(result)
    if is_queryset:
        return await apply_type_visibility_async(type_cls, source, info)
    return source
