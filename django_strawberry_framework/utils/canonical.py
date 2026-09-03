"""Hostile-safe primitives for canonically reading consumer-controlled containers.

Two subsystems reduce arbitrary consumer data to a comparable token: the
generated-input metadata cache key (``utils/inputs.py::make_hashable_meta_value``,
whose output is a Layer-6 cache key) and the write pipeline's pre-save drift
fingerprint (``utils/write_transaction.py::_field_fingerprint``, which is
request-scoped). Their OUTPUT encodings are deliberately different and stay with
each owner - one produces a hashable structure, the other a flat digest string.

What must NOT differ is how either one READS the data on the way there, because
both read values a consumer controls, and the two halves of that read are where
a walk stops being trustworthy:

* **Iteration.** ``for x in value`` on a ``dict`` / ``list`` / ``set`` SUBCLASS
  dispatches the subclass's own ``__iter__`` / ``items`` / ``keys``. A value that
  reports different contents on different calls makes a fingerprint compare
  itself to a lie, which on the drift path means an unauthorized in-memory change
  passes the check. The five built-in containers are read through their base
  slots; a value outside that set has no base slot to read, so it is refused with
  a typed ``ConfigurationError`` rather than iterated on the consumer's terms.
* **Ordering.** Unordered containers must be sorted to fingerprint
  deterministically, and a bare ``repr`` sort key runs a consumer ``__repr__``:
  one that raises breaks the walk with an untyped exception, and one that returns
  a CONSTANT collapses distinct values onto one sort key - and, for the drift
  path, onto one fingerprint.

Both defects are fail-OPEN on a security check, which is why the reads live here
rather than being spelled per walk.
"""

from __future__ import annotations

from typing import Any

from ..exceptions import ConfigurationError, _safe_arg_repr, _safe_type_name

__all__ = ["base_container_values", "canonical_sort_key"]


def base_container_values(value: Any) -> tuple[Any, ...]:
    """Read a built-in container through its BASE iterator, never an override.

    A ``dict`` yields its ``(key, value)`` pairs; every other built-in container
    yields its members. The unbound slot (``dict.items``, ``list.__iter__``, ...)
    is called explicitly so a subclass that overrides iteration cannot decide
    what the walk sees.

    Anything that is not one of the five built-in containers is REFUSED rather
    than iterated. ``tuple(value)`` on such a value would dispatch the consumer's
    own ``__iter__``, which is the exact escape this module exists to close:
    containing the exception it raises would not help, because the worse failure
    is the silent one - an ``__iter__`` that returns DIFFERENT members per call
    fingerprints a lie without raising anything. There is no base slot to read
    for a type the interpreter does not define, so the honest answer is a typed
    refusal. Both callers gate on the five built-in types before arriving here
    (``utils/inputs.py::_hashable_meta_value``,
    ``utils/write_transaction.py`` #"members = base_container_values(item)"), so
    the refusal fires only for a future caller that widened its gate without
    deciding how an arbitrary iterable should be read.
    """
    if isinstance(value, dict):
        return tuple(dict.items(value))
    if isinstance(value, set):
        return tuple(set.__iter__(value))
    if isinstance(value, frozenset):
        return tuple(frozenset.__iter__(value))
    if isinstance(value, list):
        return tuple(list.__iter__(value))
    if isinstance(value, tuple):
        return tuple(tuple.__iter__(value))
    raise ConfigurationError(
        f"Cannot canonically read a {_safe_type_name(value)} value: only the built-in "
        "dict / set / frozenset / list / tuple containers (and their subclasses) have a "
        "base iterator that consumer code cannot override.",
    )


def canonical_sort_key(value: Any) -> tuple[str, int, int]:
    """Return a TOTAL, hostile-repr-safe ordering key for a consumer value.

    Three parts, in order of decreasing usefulness and increasing reliability:
    a guarded ``repr`` (``_safe_arg_repr`` never raises and never dispatches a
    lying ``__str__`` on the result), then the type's identity, then the value's
    identity. The last two make the key total - two values whose guarded reprs
    collide still order deterministically - which is what a bare ``repr`` key
    cannot promise: a ``__repr__`` returning a constant would otherwise let
    structurally different values sort as equal, and a fingerprint built on that
    ordering would collide.
    """
    return (_safe_arg_repr(value), id(type(value)), id(value))
