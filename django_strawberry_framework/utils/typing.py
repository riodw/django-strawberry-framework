"""Async-callable detection and type-unwrapping helpers for Strawberry, Python, and GraphQL types.

Strawberry exposes list-shaped return types in two distinct forms across
versions: native ``typing.list[T]`` (the modern path) and an internal
wrapper object that carries an ``of_type`` attribute. graphql-core also
uses ``of_type`` wrapper stacks for ``GraphQLNonNull`` and ``GraphQLList``.
Both contracts live here so optimizer and schema factories do not grow
parallel unwrap loops.

Also home to the partial-aware async predicate the public field factories
and the GlobalID-callable validator share:

- ``is_async_callable`` -- coroutine-callable (``async def`` / async ``__call__``).
  An ``async def`` that ``yield``s is intentionally False here; the field
  wrappers classify that shape by VALUE at resolve time (the shared
  async-only-iterable route), not by declared shape.

And to the brittle Strawberry-private ``_strawberry_schema`` / ``.config``
accessors (``strawberry_schema_from_*`` / ``schema_config_from_info``): the
optimizer middleware, nested planner, and connection window helpers all need
the same dig from plan-time graphql-core ``info`` and resolve-time Strawberry
``Info``, so the private attribute name lives in exactly one place.
"""

import functools
import inspect
from typing import Any, get_args, get_origin

__all__ = (
    "MAX_TYPE_WRAPPER_DEPTH",
    "is_async_callable",
    "schema_config_from_info",
    "strawberry_schema_from_info",
    "strawberry_schema_from_schema",
    "unwrap_container_type",
    "unwrap_graphql_type",
    "unwrap_non_null",
    "unwrap_return_type",
)


def strawberry_schema_from_schema(schema: Any) -> Any:
    """Unwrap a Strawberry Schema to its inner schema; return ``schema`` if already unwrapped.

    Centralizes the brittle Strawberry-private ``_strawberry_schema`` contract.
    Test fixtures sometimes pass the inner schema directly, so the fallback is
    the input itself.
    """
    unwrapped = getattr(schema, "_strawberry_schema", None)
    return schema if unwrapped is None else unwrapped


def strawberry_schema_from_info(info: Any) -> Any | None:
    """Walk ``info.schema._strawberry_schema``; return ``None`` if any step is missing.

    Centralizes the brittle Strawberry-private ``_strawberry_schema`` contract for
    the resolver-info path. Caller treats ``None`` as "no schema available,
    nothing to look up."
    """
    return getattr(getattr(info, "schema", None), "_strawberry_schema", None)


def schema_config_from_info(info: Any) -> Any | None:
    """Return StrawberryConfig from plan-time graphql-core or resolve-time Info.

    Prefers ``info.schema._strawberry_schema.config`` (optimizer middleware /
    nested planner shape, where ``info.schema`` is a bare ``GraphQLSchema``) and
    falls back to ``info.schema.config`` (Strawberry ``Info`` and test stubs).
    Returns ``None`` when neither shape carries a config; callers decide whether
    that means "engine default" (``None`` into ``SliceMetadata``) or a terminal
    numeric default (``resolve_relay_max_results``).
    """
    schema = getattr(info, "schema", None)
    if schema is None:
        return None
    config = getattr(strawberry_schema_from_info(info), "config", None)
    if config is None:
        config = getattr(schema, "config", None)
    return config


# A type- or callable-wrapper stack (``GraphQLNonNull`` / ``GraphQLList`` / a
# Strawberry ``of_type`` object / nested ``partial`` or ``staticmethod`` wrappers)
# nests only as deep as the declared shape - realistically a handful of layers.
# This ceiling sits far above any real construct, so the only way to exceed it is a
# cyclic or corrupt chain. Capping the peel gives the loops a fixed, statically-checkable
# upper bound (NASA Power-of-Ten Rule 2) and turns a would-be hang into a loud failure.
MAX_TYPE_WRAPPER_DEPTH = 64


def _callable_inspection_target(value: Any) -> Any:
    """Unwrap ``partial`` / ``staticmethod`` layers for the async predicates.

    Lets ``is_async_callable`` see every supported wrapper shape without
    drift between them. ``partial`` flattens nested partials at
    construction (``partial(partial(f)).func is f``), but a staticmethod descriptor
    can contain a partial, so peel both wrapper kinds until the callable target is
    reached. This handles both ``partial(staticmethod_obj)`` and
    ``staticmethod(partial(callable_instance))``.

    The peel is bounded by ``MAX_TYPE_WRAPPER_DEPTH`` rather than looping
    unconditionally: a chain longer than that ceiling can only be cyclic or
    corrupt, so it raises ``RuntimeError`` instead of spinning forever.
    """
    target = value
    for _ in range(MAX_TYPE_WRAPPER_DEPTH + 1):
        if not isinstance(target, (functools.partial, staticmethod)):
            return target
        target = target.func if isinstance(target, functools.partial) else target.__func__
    raise RuntimeError(
        f"_callable_inspection_target: callable wrapper stack exceeded "
        f"{MAX_TYPE_WRAPPER_DEPTH} layers; the wrapper chain is likely cyclic or corrupt.",
    )


def is_async_callable(value: Any) -> bool:
    """Return whether calling ``value`` yields a coroutine.

    ``inspect.iscoroutinefunction`` only reports on the value handed to it
    directly; it misses three realistic wrapper shapes the field factories and the
    GlobalID-callable validator both must see through:

    1. a callable *instance* whose ``__call__`` is ``async def`` -- the instance
       itself is not a coroutine function, so its ``__call__`` is checked too;
    2. a ``functools.partial`` around either of the above -- ``iscoroutinefunction``
       only unwraps a partial whose ``.func`` is itself an ``async def`` function,
       not a partial around an async callable instance;
    3. a raw ``staticmethod`` descriptor -- a ``@staticmethod async def`` referenced
       by name inside its own class body is the descriptor object, not the function.
       Since Python 3.10 that descriptor is directly callable, but
       ``iscoroutinefunction`` still reads it as sync; ``.__func__`` recovers the
       underlying coroutine function. A raw ``classmethod`` is not callable and is
       therefore outside this predicate's contract.
    4. a class whose *metaclass* carries ``async def __call__`` -- calling the class
       dispatches through ``type(target).__call__``, so the metaclass path is what
       is inspected (a plain class's ``type.__call__`` keeps the pinned
       "instantiation is sync" answer, and a class body's own ``__call__`` is
       instance-call semantics that never answers for the class itself).

    Resolvers whose sync entry point returns an awaitable from elsewhere remain
    undetected -- the contract is to signal async-ness through the standard
    coroutine-function flag, not an opaque awaitable return. An ``async def`` that
    ``yield``s is an async *generator* function and is intentionally False here:
    the field wrappers classify an async-generator resolver's return by VALUE at
    resolve time, so no declared-shape predicate is needed for it.
    """
    target = _callable_inspection_target(value)
    if inspect.iscoroutinefunction(target):
        return True
    if isinstance(target, type):
        # Calling a class runs ``type(target).__call__`` (the metaclass), not the
        # class body's ``__call__`` -- that one belongs to instances. A plain
        # class resolves to the sync ``type.__call__`` slot wrapper, and a
        # metaclass carrying ``async def __call__`` is genuinely async to call.
        return inspect.iscoroutinefunction(
            getattr(type(target), "__call__", None),  # noqa: B004
        )
    # Inspecting ``__call__``'s async-ness, not testing callability -- so
    # ``callable()`` (what B004 suggests) is the wrong tool here.
    return inspect.iscoroutinefunction(
        getattr(target, "__call__", None),  # noqa: B004
    )


def unwrap_graphql_type(gql_type: Any) -> Any:
    """Peel all graphql-core / Strawberry ``of_type`` wrapper layers.

    Returns the innermost type when ``gql_type`` is a
    ``GraphQLNonNull``/``GraphQLList`` (or Strawberry ``of_type``)
    wrapper stack, or returns ``gql_type`` itself when there is no
    wrapper to peel (including ``None`` and any object that does not
    expose ``of_type``).

    The peel is bounded by ``MAX_TYPE_WRAPPER_DEPTH`` rather than looping
    unconditionally: a chain longer than that ceiling can only be cyclic or
    corrupt, so it raises ``RuntimeError`` instead of spinning forever.

    Examples:
        ``NonNull(List(NonNull(Inner)))`` -> ``Inner``;
        ``Inner`` -> ``Inner`` (no wrapper to peel);
        ``None`` -> ``None`` (no ``of_type`` attribute).
    """
    for _ in range(MAX_TYPE_WRAPPER_DEPTH + 1):
        if not hasattr(gql_type, "of_type"):
            return gql_type
        gql_type = gql_type.of_type
    raise RuntimeError(
        f"unwrap_graphql_type: `of_type` wrapper stack exceeded "
        f"{MAX_TYPE_WRAPPER_DEPTH} layers; the type chain is likely cyclic or corrupt.",
    )


def unwrap_non_null(gql_type: Any) -> Any:
    """Peel ONLY ``GraphQLNonNull`` layers, bounded; leave list wrappers in place.

    The narrow sibling of :func:`unwrap_graphql_type`, for the callers that must
    still SEE the ``GraphQLList`` underneath - the resource policy's list-vs-
    connection classification would answer wrong if the list layer were peeled
    too, which is why those sites could not simply call the full peel and each
    grew its own raw ``while isinstance(..., GraphQLNonNull)`` loop instead.

    Bounded like every other peel in this module (Power-of-Ten Rule 2): a
    genuine graphql-core ``GraphQLNonNull`` cannot wrap another, so a chain past
    the ceiling can only be a hand-built or corrupt type, and an unbounded
    ``while`` on one hangs the request thread rather than failing.
    """
    from graphql import GraphQLNonNull

    for _ in range(MAX_TYPE_WRAPPER_DEPTH + 1):
        if not isinstance(gql_type, GraphQLNonNull):
            return gql_type
        gql_type = gql_type.of_type
    raise RuntimeError(
        f"unwrap_non_null: GraphQLNonNull wrapper stack exceeded "
        f"{MAX_TYPE_WRAPPER_DEPTH} layers; the type chain is likely cyclic or corrupt.",
    )


def unwrap_container_type(strawberry_type: Any) -> Any:
    """Peel Strawberry ``StrawberryContainer`` layers only, bounded.

    The container-scoped sibling of ``unwrap_graphql_type`` for resolved
    Strawberry field types (``list[Edge[Node]]`` -> ``Edge``): the
    ``isinstance(StrawberryContainer)`` gate is load-bearing - a concrete leaf
    class that happens to expose an ``of_type`` attribute must NOT be peeled
    (the bare-``hasattr`` contract would descend into it) - so the shared
    unbounded ``while isinstance`` loop lands here with the same
    ``MAX_TYPE_WRAPPER_DEPTH`` Power-of-Ten cap and loud cyclic-chain failure,
    instead of living raw at a call site.

    The ``StrawberryContainer`` import is function-local so this module stays
    importable without pulling Strawberry's type machinery at import time
    (matching the module's stdlib-only header).
    """
    from strawberry.types.base import StrawberryContainer

    for _ in range(MAX_TYPE_WRAPPER_DEPTH + 1):
        if not isinstance(strawberry_type, StrawberryContainer):
            return strawberry_type
        strawberry_type = strawberry_type.of_type
    raise RuntimeError(
        f"unwrap_container_type: `of_type` container stack exceeded "
        f"{MAX_TYPE_WRAPPER_DEPTH} layers; the type chain is likely cyclic or corrupt.",
    )


def unwrap_return_type(rt: Any) -> Any:
    """Unwrap **one layer** of list / Strawberry-list-wrapper around the inner type.

    Returns the inner type when ``rt`` is ``list[T]``, a Strawberry-style
    wrapper exposing ``of_type``, or returns ``rt`` itself when there is
    no wrapper to peel.

    Strawberry exposes lists either as native ``typing.list[T]`` or wraps
    them in an internal ``StrawberryList``-style object that carries an
    ``of_type`` attribute. Handling both styles keeps callers portable
    across Strawberry versions.

    The Strawberry-wrapper check (``of_type``) runs first so a wrapper
    that *also* presents a list-like origin (a hypothetical
    ``StrawberryList[list[T]]``) yields its declared inner type rather
    than the generic-args inner type.

    Examples:
        ``list[int]`` -> ``int``;
        ``list[list[int]]`` -> ``list[int]`` (this helper peels one
        layer; chain calls if you need full unwrapping);
        ``StrawberryList(of_type=int)`` -> ``int``;
        ``int`` -> ``int`` (no wrapper to peel).
    """
    missing = object()
    inner = getattr(rt, "of_type", missing)
    if inner is not missing:
        return inner
    if get_origin(rt) is list:
        args = get_args(rt)
        return args[0] if args else Any
    if rt is list:
        return Any
    return rt
