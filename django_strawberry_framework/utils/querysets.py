"""Query-source + ``DjangoType.get_queryset`` visibility contract, single-sited.

The neutral query-source mechanics every resolver surface shares: coerce a
``Manager`` to a ``QuerySet`` exactly once, decide whether a value is a
queryset, run the ``DjangoType.get_queryset`` visibility hook through the sync
or async path, and combine those into the list-field consumer-resolver shape.
Extracted here (the 0.0.9 DRY pass, ``docs/feedback.md`` Major 1) so list
fields, connection fields, the optimizer middleware, the Relay node defaults,
and the filter related-visibility derive all reach ONE implementation of the
contract -- ``get_queryset`` is the visibility hook, and a visibility-hook
mistake is a data-leak bug, so the routing must not be re-decided per surface.

Caller-specific tails stay with their caller: the connection field keeps its
GraphQL non-queryset error (it calls ``normalize_query_source`` then guards),
the Relay node defaults keep their id filter, the optimizer keeps plan
building, and the filter related derive keeps its per-branch recursion. This
module owns only the source normalization + the colored visibility calls.

Cycle-safe by construction: it depends on nothing but ``django`` and
``..exceptions``, so ``types/relay.py`` (imported at module top by
``types/base.py``) can import from here without closing a load cycle, and it
never imports back into the package.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any

from django.db import models

from ..exceptions import ConfigurationError


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
    """Guard a synchronous hook result against an ``async def`` override.

    Three sync pipeline seams invoke a consumer-overridable hook that
    Decision 9 / Decision 15 allow to be sync OR async: the ``get_queryset``
    visibility hook (``apply_type_visibility_sync``) and the two write
    authorization hooks (``check_permission`` / a ``permission_classes``
    entry's ``has_permission``). None can await - the whole ORM pipeline runs
    synchronously (under one ``sync_to_async`` worker on the async surface),
    so an ``async def`` override returns an orphaned coroutine. Treating that
    truthy coroutine as success would be a silent bug - an authorization
    BYPASS for the permission hooks - so it is rejected loudly.

    When ``value`` is a coroutine it is ``close()``d (silencing the "coroutine
    was never awaited" warning that ``filterwarnings = error`` would otherwise
    turn into a test failure) and a ``SyncMisuseError`` is raised naming the
    offending ``owner.method`` and the ``context`` it ran in, with the
    surface-specific ``recourse`` appended. The message template lives here so
    the three seams cannot drift. Otherwise ``value`` is returned unchanged, so
    callers read ``x = reject_async_in_sync_context(x, ...)``.
    """
    if inspect.iscoroutine(value):
        value.close()
        raise SyncMisuseError(
            f"{owner}.{method} returned a coroutine in a sync {context} context. {recourse}",
        )
    return value


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
    """
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
    # ``related_visibility_queryset_or_default`` (DRY review C4).
    queryset = related_visibility_queryset_or_default(related_model, info, async_recourse)
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


def post_process_queryset_result_sync(type_cls: type, result: Any, info: Any) -> Any:
    """Normalize a consumer-resolver return then apply visibility (sync).

    The list-field consumer-resolver shape: a ``Manager`` is coerced to a
    ``QuerySet`` (the field wrapper owns the coercion), a ``QuerySet`` runs the
    type's ``get_queryset`` visibility hook, and a non-queryset Python
    list / generator passes through unchanged. The default-resolver path bypasses
    this (its source is already ``initial_queryset(...)``, a known ``QuerySet``).

    An awaitable reaching here is rejected loudly. The sync branch is chosen
    at construction from ``is_async_callable(user_resolver)``, which only sees an
    ``async def`` / async-callable resolver (or a ``functools.partial`` of one);
    a plain ``def`` resolver that *returns* an awaitable (e.g. ``return
    some_async()`` without ``async def``) is classified sync but its awaitable
    return is not a ``Manager`` / ``QuerySet``. Passing it through unchanged would
    let graphql-core await it downstream (under async execution) to a ``QuerySet``
    that never ran the ``get_queryset`` visibility hook -- a silent data-isolation
    bypass. Native coroutines are ``close()``d first to silence the "coroutine
    was never awaited" warning that ``filterwarnings = error`` would fail on;
    asyncio Future-like values are cancelled. A custom ``__await__`` object has
    no standard disposal contract and has not begun execution, so it is simply
    rejected. This mirrors the sync
    ``get_queryset`` coroutine guard (``reject_async_in_sync_context``) and keeps
    the invariant that a consumer ``QuerySet`` return is never resolved without
    its visibility hook. The recourse: declare the resolver ``async def`` (the
    field then awaits it and applies ``get_queryset`` via the async post-process
    path), or return an already-evaluated ``list`` to opt out of the hook.
    """
    source, is_queryset = normalize_query_source(result)
    if is_queryset:
        return apply_type_visibility_sync(type_cls, source, info)
    if inspect.isawaitable(source):
        if inspect.iscoroutine(source):
            source.close()
        elif asyncio.isfuture(source):
            source.cancel()
        raise SyncMisuseError(
            f"A sync {type_cls.__name__} consumer resolver returned an awaitable. "
            "Declare the resolver `async def` (or use an async callable) so the "
            "field awaits it and applies the get_queryset visibility hook; a plain "
            "`def` resolver that returns an awaitable is committed to the sync path "
            "and passing it through would silently skip get_queryset.",
        )
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
