"""Type-unwrapping helpers for Strawberry / Python / GraphQL types.

Strawberry exposes list-shaped return types in two distinct forms across
versions: native ``typing.list[T]`` (the modern path) and an internal
wrapper object that carries an ``of_type`` attribute. graphql-core also
uses ``of_type`` wrapper stacks for ``GraphQLNonNull`` and ``GraphQLList``.
Both contracts live here so optimizer and schema factories do not grow
parallel unwrap loops.
"""

from typing import Any, get_args, get_origin


def unwrap_graphql_type(gql_type: Any) -> Any:
    """Peel all graphql-core / Strawberry ``of_type`` wrapper layers."""
    while hasattr(gql_type, "of_type"):
        gql_type = gql_type.of_type
    return gql_type


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
        return get_args(rt)[0]
    return rt
