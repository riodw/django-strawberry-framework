"""``DjangoListField`` - non-Relay ``list[T]`` field for root Query fields.

Spec: ``docs/SPECS/spec-020-list_field-0_0_7.md``.
Target release: ``0.0.7``.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterable, Callable, Iterable, Sequence
from typing import Any

import strawberry
from strawberry.types import Info
from strawberry.utils.inspect import in_async_context

from .exceptions import ConfigurationError
from .resource_policy import bounded_rows, bounded_rows_async, validate_collection_bound
from .types import DjangoType
from .types.base import _is_relay_shaped
from .utils.querysets import (
    SyncMisuseError,
    apply_type_visibility_async,
    apply_type_visibility_sync,
    initial_queryset,
    post_process_queryset_result_async,
    post_process_queryset_result_sync,
)
from .utils.typing import is_async_callable, is_async_generator_callable

__all__ = ("DjangoListField",)


# Consumer-resolver post-processing helpers. The field-wrapper Manager -> QuerySet
# coercion + visibility-hook contract is single-sited in
# ``utils/querysets.py::post_process_queryset_result_sync`` / ``_async``;
# these stay as the named consumer-wrapper entry points the
# ``_wrap`` resolvers call. The default-resolver path bypasses them because
# ``qs`` is already known to be a ``QuerySet`` from ``initial_queryset(...)`` -
# no normalization is needed there.


def _post_process_consumer_sync(target_type: type, result: Any, info: Info) -> Any:
    return post_process_queryset_result_sync(target_type, result, info)


async def _post_process_consumer_async(target_type: type, result: Any, info: Info) -> Any:
    return await post_process_queryset_result_async(target_type, result, info)


async def _bounded_async(
    awaitable: Any,
    info: Info,
    max_rows: int | None,
    *,
    trusted: bool,
) -> Any:
    """Await a visibility-applied result, then apply the field's row bound.

    The bound is applied LAST, never before the visibility hook. A sliced
    queryset cannot be refiltered or reordered, and both the visibility hook and
    the surface compose onto the source - so slicing first would turn the bound
    into a crash on every type that declares a hook. Ordering the two this way is
    a correctness constraint, not a preference.
    """
    return await bounded_rows_async(await awaitable, info, max_rows, trusted=trusted)


def _require_async_iterable_context() -> None:
    """Reject async-only iterable results from synchronous GraphQL execution."""
    if not in_async_context():
        raise SyncMisuseError(
            "A DjangoListField resolver returned an AsyncIterable in a sync execution "
            "context. Use `await schema.execute(...)` for async iterable resolvers.",
        )


def _validate_djangotype_target(
    target_type: type,
    resolver: Callable | None,
    *,
    field: str,
) -> None:
    """Run the four shared DjangoType-target constructor guards for a field factory.

    Shared by ``DjangoListField`` and ``DjangoConnectionField`` (and any future
    node field). ``field`` is the factory's public name
    (e.g. ``"DjangoListField"``) interpolated into the ``ConfigurationError``
    messages so each factory's errors name itself. These four constructor-site
    checks fail at the line that wrote ``<field>(...)`` rather than at
    finalize-time.

    Order is load-bearing - each target-type check assumes the previous one
    passed. The third (own-class registration) check is the strict invariant:
    ``__django_strawberry_definition__`` is assigned by
    ``DjangoType.__init_subclass__`` (``types/base.py::DjangoType.__init_subclass__``)
    only for concrete subclasses carrying their own ``Meta`` with a ``model``.
    The attribute is inherited via MRO, so ``hasattr`` would accept a subclass
    that omits its own ``Meta`` - binding the field to a target whose
    definition, ``Meta.primary`` state, and model belong to the parent.
    ``definition.origin is target_type`` is the strict own-class invariant
    (NOT ``hasattr``).

    Raises ``ConfigurationError`` on failure; returns ``None`` when all four
    pass. The caller runs any factory-specific guards (e.g. the connection
    field's Relay-Node guard) AFTER this returns.
    """
    if not inspect.isclass(target_type):
        raise ConfigurationError(
            f"{field} requires a DjangoType class; got {target_type!r}.",
        )
    if not issubclass(target_type, DjangoType):
        raise ConfigurationError(
            f"{field} requires a DjangoType subclass; got {target_type.__name__}.",
        )
    definition = getattr(target_type, "__django_strawberry_definition__", None)
    if definition is None or getattr(definition, "origin", None) is not target_type:
        raise ConfigurationError(
            f"{field} target {target_type.__name__} is not a registered DjangoType. "
            f"This usually means {target_type.__name__}'s `Meta` is missing a `model` "
            "declaration, or it inherits a definition from a parent without declaring its own `Meta`.",
        )
    if resolver is not None and not callable(resolver):
        raise ConfigurationError(f"{field} resolver must be callable.")


def _validate_relay_djangotype_target(
    target_type: type,
    resolver: Callable | None,
    *,
    field: str,
    relay_error_message: str,
) -> None:
    """Run the four shared DjangoType-target guards plus the Relay-Node-shaped fifth.

    The Relay-shaped target guard shared by ``DjangoConnectionField`` and
    ``relay.py::_validate_node_target`` (which backs ``DjangoNodeField`` /
    ``DjangoNodesField``) -- single-sited. Delegates the
    four base checks to ``_validate_djangotype_target`` (with the call site's
    ``resolver`` seam), then rejects a non-Relay-Node-shaped target.
    ``_is_relay_shaped`` reads the declared ``Meta.interfaces`` (a
    Meta-declared ``relay.Node`` is in ``definition.interfaces`` before Phase
    2.5 injects it into ``__bases__``) OR direct ``relay.Node`` inheritance.
    The caller supplies the full ``relay_error_message`` so each factory keeps
    its own wording.
    """
    _validate_djangotype_target(target_type, resolver, field=field)
    definition = target_type.__django_strawberry_definition__
    if not _is_relay_shaped(target_type, definition.interfaces):
        raise ConfigurationError(relay_error_message)


def DjangoListField(  # noqa: N802  # PascalCase for graphene-django parity - consumer usage is `DjangoListField(BranchType)`
    target_type: type,
    *,
    resolver: Callable | None = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Sequence[object] = (),
    max_rows: int | None = None,
    trusted_max_rows: bool = False,
) -> Any:
    """Factory for a non-Relay ``list[T]`` root Query field bound to a ``DjangoType``.

    See ``docs/SPECS/spec-020-list_field-0_0_7.md`` Decision 1 (mechanism) and
    Decision 2 (default-resolver shape) for the design contract.

    Ordering contract: a ``DjangoListField`` does NOT guarantee row order unless
    the query supplies an ``orderBy`` argument or the model declares
    ``Meta.ordering``. The default resolver returns
    ``model._default_manager.all()`` with no tiebreaker, so the response array
    order is database-dependent. This is intentional and asymmetric with
    ``DjangoConnectionField``, which appends a pk tiebreaker to guarantee a
    deterministic total order (its positional cursors require one); a flat list
    has no cursors, so the unordered sequence is acceptable.

    Row bound (spec-047 Decision 6). Every ``DjangoListField`` is bounded: the
    request's ``ResourcePolicy.max_list_rows`` applies whether or not the field
    says anything, and ``max_rows=`` narrows it further for this field. There is
    no unbounded spelling - ``max_rows=None`` means "the policy governs", not
    "no bound". ``trusted_max_rows=True`` is the explicit widening opt-in: it
    declares that this field's ``max_rows`` is a deliberate declaration that
    outranks the request policy, and it is the only way a field can be wider
    than the policy.
    """
    if max_rows is not None:
        validate_collection_bound(max_rows, field="DjangoListField max_rows")
    # Decision 5 validation guards: the four shared DjangoType-target
    # constructor checks (see ``_validate_djangotype_target`` for the
    # load-bearing ordering and the own-class registration invariant).
    _validate_djangotype_target(target_type, resolver, field="DjangoListField")
    # Async-detection asymmetry (see spec Decision 2,
    # "Async-detection asymmetry - intentional, not a harmonization candidate"):
    # ``_default`` uses runtime ``in_async_context()`` per-call so the same
    # factory output dispatches correctly under both ``schema.execute_sync``
    # and ``await schema.execute``. The consumer-wrapper branch below commits
    # per-construction via ``is_async_callable(user_resolver)`` (the
    # ``__call__``/``functools.partial``-aware superset of
    # ``inspect.iscoroutinefunction``) because Strawberry inspects the resolver
    # signature once at schema
    # construction and freezes the sync-vs-async handling.
    if resolver is None:

        def _default(root: Any, info: Info) -> Any:  # noqa: ARG001
            qs = initial_queryset(target_type)
            if in_async_context():
                # The async branch DOES need its own coroutine wrapper: the row
                # bound has to be applied to the awaited value, after the
                # visibility hook has composed onto the unsliced source.
                return _bounded_async(
                    apply_type_visibility_async(target_type, qs, info),
                    info,
                    max_rows,
                    trusted=trusted_max_rows,
                )
            return bounded_rows(
                apply_type_visibility_sync(target_type, qs, info),
                info,
                max_rows,
                trusted=trusted_max_rows,
            )

        wrapped = _default
    else:
        user_resolver = resolver

        async def _resolve_async_iterable(source: Any, info: Info) -> Any:
            return await bounded_rows_async(
                await _post_process_consumer_async(target_type, source, info),
                info,
                max_rows,
                trusted=trusted_max_rows,
            )

        if is_async_generator_callable(user_resolver):

            def _wrap(root: Any, info: Info) -> Any:
                source = user_resolver(root, info)
                _require_async_iterable_context()
                return _resolve_async_iterable(source, info)

        elif is_async_callable(user_resolver):

            async def _wrap(root: Any, info: Info) -> Any:
                # ``await`` the consumer coroutine BEFORE handing
                # the result to ``_post_process_consumer_async`` so the
                # isinstance-QuerySet branch sees the awaited value, not the
                # coroutine itself. The row bound is applied AFTER
                # post-processing, so a returned ``Manager`` has already been
                # coerced to a ``QuerySet`` and the visibility hook has already
                # composed onto the unsliced source.
                return await bounded_rows_async(
                    await _post_process_consumer_async(
                        target_type,
                        await user_resolver(root, info),
                        info,
                    ),
                    info,
                    max_rows,
                    trusted=trusted_max_rows,
                )
        else:

            def _wrap(root: Any, info: Info) -> Any:
                source = user_resolver(root, info)
                if isinstance(source, AsyncIterable) and not isinstance(source, Iterable):
                    _require_async_iterable_context()
                    return _resolve_async_iterable(source, info)
                return bounded_rows(
                    _post_process_consumer_sync(target_type, source, info),
                    info,
                    max_rows,
                    trusted=trusted_max_rows,
                )

        wrapped = _wrap

    return strawberry.field(
        resolver=wrapped,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
