"""Type-unwrapping helpers for Strawberry / Python / GraphQL types.

Strawberry exposes list-shaped return types in two distinct forms across
versions: native ``typing.list[T]`` (the modern path) and an internal
wrapper object that carries an ``of_type`` attribute. graphql-core also
uses ``of_type`` wrapper stacks for ``GraphQLNonNull`` and ``GraphQLList``.
Both contracts live here so optimizer and schema factories do not grow
parallel unwrap loops.
"""

from typing import Any, get_args, get_origin

# A GraphQL type-wrapper stack (``GraphQLNonNull`` / ``GraphQLList`` / a
# Strawberry ``of_type`` object) nests only as deep as the declared type —
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
