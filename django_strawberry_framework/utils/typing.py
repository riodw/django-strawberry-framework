"""Async-callable detection and type-unwrapping helpers for Strawberry, Python, and GraphQL types.

Strawberry exposes list-shaped return types in two distinct forms across
versions: native ``typing.list[T]`` (the modern path) and an internal
wrapper object that carries an ``of_type`` attribute. graphql-core also
uses ``of_type`` wrapper stacks for ``GraphQLNonNull`` and ``GraphQLList``.
Both contracts live here so optimizer and schema factories do not grow
parallel unwrap loops.

Also home to ``is_async_callable`` -- the partial-aware coroutine-callable
predicate the public field factories and the GlobalID-callable validator share
(the 0.0.9 DRY pass, ``docs/feedback.md`` Major 4).
"""

import functools
import inspect
from typing import Any, get_args, get_origin


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

    A single ``.func`` hop reaches the partial target with no loop to bound:
    ``partial`` flattens nested partials at construction
    (``partial(partial(f)).func is f``), so ``.func`` is never itself a ``partial``
    and the traversal is depth-1; the descriptor unwrap then runs on that target so
    ``partial(staticmethod_obj)`` is handled too. Resolvers whose sync entry point
    returns an awaitable from elsewhere remain undetected -- the contract is to
    signal async-ness through the standard coroutine-function flag, not an opaque
    awaitable return.
    """
    target = value.func if isinstance(value, functools.partial) else value
    if isinstance(target, staticmethod):
        target = target.__func__
    # Inspecting ``__call__``'s async-ness, not testing callability -- so
    # ``callable()`` (what B004 suggests) is the wrong tool here.
    return inspect.iscoroutinefunction(target) or inspect.iscoroutinefunction(
        getattr(target, "__call__", None),  # noqa: B004
    )


# A GraphQL type-wrapper stack (``GraphQLNonNull`` / ``GraphQLList`` / a
# Strawberry ``of_type`` object) nests only as deep as the declared type -
# realistically a handful of layers. This ceiling sits far above any real type,
# so the only way to exceed it is a cyclic or corrupt ``of_type`` chain. Capping
# the peel gives the loop a fixed, statically-checkable upper bound (NASA
# Power-of-Ten Rule 2) and turns a would-be hang into a loud failure.
_MAX_TYPE_WRAPPER_DEPTH = 64


def unwrap_graphql_type(gql_type: Any) -> Any:
    """Peel all graphql-core / Strawberry ``of_type`` wrapper layers.

    Returns the innermost type when ``gql_type`` is a
    ``GraphQLNonNull``/``GraphQLList`` (or Strawberry ``of_type``)
    wrapper stack, or returns ``gql_type`` itself when there is no
    wrapper to peel (including ``None`` and any object that does not
    expose ``of_type``).

    The peel is bounded by ``_MAX_TYPE_WRAPPER_DEPTH`` rather than looping
    unconditionally: a chain longer than that ceiling can only be cyclic or
    corrupt, so it raises ``RuntimeError`` instead of spinning forever.

    Examples:
        ``NonNull(List(NonNull(Inner)))`` -> ``Inner``;
        ``Inner`` -> ``Inner`` (no wrapper to peel);
        ``None`` -> ``None`` (no ``of_type`` attribute).
    """
    for _ in range(_MAX_TYPE_WRAPPER_DEPTH):
        if not hasattr(gql_type, "of_type"):
            return gql_type
        gql_type = gql_type.of_type
    raise RuntimeError(
        f"unwrap_graphql_type: `of_type` wrapper stack exceeded "
        f"{_MAX_TYPE_WRAPPER_DEPTH} layers; the type chain is likely cyclic or corrupt.",
    )


def unwrap_container_type(strawberry_type: Any) -> Any:
    """Peel Strawberry ``StrawberryContainer`` layers only, bounded (DRY review B3).

    The container-scoped sibling of ``unwrap_graphql_type`` for resolved
    Strawberry field types (``list[Edge[Node]]`` -> ``Edge``): the
    ``isinstance(StrawberryContainer)`` gate is load-bearing - a concrete leaf
    class that happens to expose an ``of_type`` attribute must NOT be peeled
    (the bare-``hasattr`` contract would descend into it) - so the shared
    unbounded ``while isinstance`` loop lands here with the same
    ``_MAX_TYPE_WRAPPER_DEPTH`` Power-of-Ten cap and loud cyclic-chain failure,
    instead of living raw at a call site.

    The ``StrawberryContainer`` import is function-local so this module stays
    importable without pulling Strawberry's type machinery at import time
    (matching the module's stdlib-only header).
    """
    from strawberry.types.base import StrawberryContainer

    for _ in range(_MAX_TYPE_WRAPPER_DEPTH):
        if not isinstance(strawberry_type, StrawberryContainer):
            return strawberry_type
        strawberry_type = strawberry_type.of_type
    raise RuntimeError(
        f"unwrap_container_type: `of_type` container stack exceeded "
        f"{_MAX_TYPE_WRAPPER_DEPTH} layers; the type chain is likely cyclic or corrupt.",
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
    inner = getattr(rt, "of_type", None)
    if inner is not None:
        return inner
    if get_origin(rt) is list:
        args = get_args(rt)
        return args[0] if args else Any
    if rt is list:
        return Any
    return rt
