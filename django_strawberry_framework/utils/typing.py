"""Type-unwrapping helpers for Strawberry / Python annotations.

Strawberry exposes list-shaped return types in two distinct forms across
versions: native ``typing.list[T]`` (the modern path) and an internal
wrapper object that carries an ``of_type`` attribute. Subsystems that
need to introspect a resolver's return type — the optimizer today, and
the connection-field / filter argument factories tomorrow — all need
the same one-layer unwrap, so it lives here rather than re-implemented
per consumer.
"""

from typing import Any, get_args, get_origin


def unwrap_return_type(rt: Any) -> Any:
    """Unwrap one layer of list / Strawberry-list-wrapper around the inner type.

    Returns the inner type when ``rt`` is ``list[T]``, a Strawberry-style
    wrapper exposing ``of_type``, or returns ``rt`` itself when there is
    no wrapper to peel.

    Strawberry exposes lists either as native ``typing.list[T]`` or wraps
    them in an internal ``StrawberryList``-style object that carries an
    ``of_type`` attribute. Handling both styles keeps callers portable
    across Strawberry versions.
    """
    inner = getattr(rt, "of_type", None)
    if inner is not None:
        return inner
    if get_origin(rt) is list:
        return get_args(rt)[0]
    return rt
