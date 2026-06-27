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


# TODO(spec-039 Slice 3): Promote the object-returning related-visibility helper
# currently local to `forms/resolvers.py` into this module before serializer
# relation decoding lands.
# Pseudo flow:
#   - Resolve the related model's registered Django type.
#   - If no primary type exists, fall back to the model default manager and pk.
#   - Otherwise apply `visibility_scoped_related_queryset(...)`, then filter that
#     visible queryset by pk and return the first matching object.
#
# The serializer decoder and form decoder should both call this helper so raw-pk
# relation visibility cannot drift between write flavors. The helper accepts raw
# pks after a flavor-specific decoder chooses that branch; it does not imply every
# generated GraphQL relation input accepts both raw pk and GlobalID.
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
    """
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
