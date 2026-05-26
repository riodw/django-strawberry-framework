"""``DjangoListField`` — non-Relay ``list[T]`` field for root Query fields.

Spec: ``docs/spec-016-list_field-0_0_7.md``.
Target release: ``0.0.7``.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from typing import Any

import strawberry
from django.db import models
from strawberry.types import Info
from strawberry.utils.inspect import in_async_context

from .exceptions import ConfigurationError
from .types import DjangoType
from .types.relay import _apply_get_queryset_async, _apply_get_queryset_sync, _initial_queryset

__all__ = ("DjangoListField",)


# Consumer-resolver post-processing helpers (rev6 H2: module-scope placement,
# rev6 H3: ``_consumer`` suffix). The default-resolver path bypasses these
# because ``qs`` is already known to be a ``QuerySet`` from ``Manager.all()`` —
# no Manager-to-QuerySet coercion or isinstance branching is needed there.


def _post_process_consumer_sync(target_type: type, result: Any, info: Info) -> Any:
    if isinstance(result, models.Manager):
        result = result.all()  # field-wrapper Manager → QuerySet coercion (rev4 M1).
    if isinstance(result, models.QuerySet):
        return _apply_get_queryset_sync(target_type, result, info)
    return result  # Python list / generator — pass through (rev2 H1).


async def _post_process_consumer_async(target_type: type, result: Any, info: Info) -> Any:
    if isinstance(result, models.Manager):
        result = result.all()
    if isinstance(result, models.QuerySet):
        return await _apply_get_queryset_async(target_type, result, info)
    return result


def _is_async_callable(fn: Any) -> bool:
    """True if calling ``fn`` returns a coroutine.

    Two checks cover the practical resolver shapes:

    - ``inspect.iscoroutinefunction(fn)`` — catches ``async def`` functions
      AND ``functools.partial`` / ``functools.partialmethod`` wrapping them.
      Python's ``inspect`` module unwraps ``partial.func`` natively since 3.8
      (verified at run time against the installed Python in
      ``tests/test_list_field.py::test_djangolistfield_partial_wrapped_async_resolver_gets_get_queryset_applied``;
      a manual ``.func`` unwrap branch would be dead code on Python 3.10+).
    - ``inspect.iscoroutinefunction(fn.__call__)`` — catches callable
      instances whose ``__call__`` is ``async def``. ``iscoroutinefunction``
      checks the function flag of the immediate argument, so a callable
      instance is False; descending into ``__call__`` recovers the async flag.
      Without this branch an async-callable-object resolver would land in the
      sync wrapper, its coroutine return would bypass
      ``_post_process_consumer_sync``, and the awaited QuerySet would silently
      skip ``target_type.get_queryset(...)`` (``docs/feedback.md`` High #2).

    Resolvers whose sync entry point returns an awaitable (e.g., a plain ``def``
    that produces a coroutine from somewhere else) remain undetected — the
    contract is that resolvers signal sync-vs-async through the standard
    coroutine-function flag, not through opaque awaitable returns.
    """
    if inspect.iscoroutinefunction(fn):
        return True
    call = getattr(fn, "__call__", None)
    return call is not None and inspect.iscoroutinefunction(call)


def DjangoListField(  # noqa: N802  # PascalCase for graphene-django parity — consumer usage is `DjangoListField(BranchType)`
    target_type: type,
    *,
    resolver: Callable | None = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Sequence[object] = (),
) -> Any:
    """Factory for a non-Relay ``list[T]`` root Query field bound to a ``DjangoType``.

    See ``docs/spec-016-list_field-0_0_7.md`` Decision 1 (mechanism) and
    Decision 2 (default-resolver shape) for the design contract.
    """
    # Decision 5 validation guards (spec lines 542-549): four constructor-site
    # checks that fail at the line that wrote ``DjangoListField(...)`` rather
    # than at finalize-time. Order is load-bearing: each target-type check
    # assumes the previous one passed. The own-class registration check
    # (third guard, below) is the strict invariant — see its comment block for
    # the inheritance failure mode that ``hasattr`` would silently accept.
    if not inspect.isclass(target_type):
        raise ConfigurationError(
            f"DjangoListField requires a DjangoType class; got {target_type!r}.",
        )
    if not issubclass(target_type, DjangoType):
        raise ConfigurationError(
            f"DjangoListField requires a DjangoType subclass; got {target_type.__name__}.",
        )
    # Own-class registration check: ``__django_strawberry_definition__`` is
    # assigned by ``DjangoType.__init_subclass__`` (``types/base.py::DjangoType.__init_subclass__``)
    # only for concrete subclasses carrying their own ``Meta`` with a ``model``. The
    # attribute is inherited via MRO, so ``hasattr`` would accept a subclass
    # that omits its own ``Meta`` — binding the field to a target whose
    # definition, ``Meta.primary`` state, and model belong to the parent.
    # ``definition.origin is target_type`` is the strict own-class invariant.
    definition = getattr(target_type, "__django_strawberry_definition__", None)
    if definition is None or getattr(definition, "origin", None) is not target_type:
        raise ConfigurationError(
            f"DjangoListField target {target_type.__name__} is not a registered DjangoType. "
            f"This usually means {target_type.__name__}'s `Meta` is missing a `model` "
            "declaration, or it inherits a definition from a parent without declaring its own `Meta`.",
        )
    if resolver is not None and not callable(resolver):
        raise ConfigurationError("DjangoListField resolver must be callable.")
    # Async-detection asymmetry (rev5 H2; see spec Decision 2,
    # "Async-detection asymmetry — intentional, not a harmonization candidate"):
    # ``_default`` uses runtime ``in_async_context()`` per-call so the same
    # factory output dispatches correctly under both ``schema.execute_sync``
    # and ``await schema.execute``. The consumer-wrapper branch below commits
    # per-construction via ``inspect.iscoroutinefunction(user_resolver)``
    # because Strawberry inspects the resolver signature once at schema
    # construction and freezes the sync-vs-async handling.
    if resolver is None:

        def _default(root: Any, info: Info) -> Any:
            qs = _initial_queryset(target_type)
            if in_async_context():
                # rev6 H1: return the coroutine from ``_apply_get_queryset_async``
                # directly; Strawberry's AwaitableOrValue dispatch awaits it.
                # An inner ``async def`` wrapper would add a redundant coroutine
                # layer with no semantic gain.
                return _apply_get_queryset_async(target_type, qs, info)
            return _apply_get_queryset_sync(target_type, qs, info)

        wrapped = _default
    else:
        user_resolver = resolver
        if _is_async_callable(user_resolver):

            async def _wrap(root: Any, info: Info) -> Any:
                # rev4 H2: ``await`` the consumer coroutine BEFORE handing
                # the result to ``_post_process_consumer_async`` so the
                # isinstance-QuerySet branch sees the awaited value, not the
                # coroutine itself.
                return await _post_process_consumer_async(
                    target_type,
                    await user_resolver(root, info),
                    info,
                )
        else:

            def _wrap(root: Any, info: Info) -> Any:
                return _post_process_consumer_sync(
                    target_type,
                    user_resolver(root, info),
                    info,
                )

        wrapped = _wrap

    return strawberry.field(
        resolver=wrapped,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
