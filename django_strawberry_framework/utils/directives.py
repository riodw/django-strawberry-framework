"""Construction-time containment for the consumer-supplied ``directives=`` forward.

Every field factory in the package (``DjangoListField``, ``DjangoMutationField``
and ``register_mutation()``'s passthrough, the ``auth`` fixed-field factories,
and the Relay root ``DjangoNodeField`` / ``DjangoNodesField``) hands a consumer
``directives`` value straight to ``strawberry.field()``. Strawberry consumes
that iterable LAZILY -- at class decoration or SDL render -- so an unvalidated
value fails THERE with an unrelated error, or not at all, far from the
assignment line that supplied it:

- a bare ``str`` / ``bytes`` / ``bytearray`` / ``memoryview`` satisfies
  ``Iterable`` but iterates CHARACTER-wise (into ``str`` chars, or into ``int``
  bytes), so Strawberry builds a field whose "directives" are chars or ints
  without ``__strawberry_directive__``: a raw ``AttributeError`` at schema build
  for ``str``, and a silent build that crashes SDL render for the byte flavors;
- an iterator that raises midway escapes as whatever it raised;
- a non-iterable detonates as a raw ``TypeError`` inside ``strawberry.field``.

This module owns the ONE containment behind all of them. It was three
near-identical inline copies before, and they had already drifted (different
safe renderer in the reject message, different ``except`` tuple), which is
exactly how a containment stops containing.

Why the ``except`` is ``Exception``-wide rather than an enumerated tuple: the
value being materialized is deployment-supplied and arbitrary, so its
``__iter__`` / ``__next__`` can raise ANY exception type. An enumerated tuple
(the previous copies listed ``TypeError``/``ValueError``/``AttributeError``/
``KeyError``/``IndexError``) is a guess about hostile code, and a
``RuntimeError``-raising iterator walked straight through it and escaped raw --
the failure this containment exists to prevent. ``BaseException`` is
deliberately NOT caught: ``KeyboardInterrupt`` / ``SystemExit`` must keep
propagating.
"""

from typing import Any

from ..exceptions import ConfigurationError, _safe_type_name

__all__ = ("validated_field_directives",)

# The types that are ``Iterable`` but whose elements are never directives.
# ``bytearray`` and ``memoryview`` iterate into ``int`` exactly as ``bytes``
# does, so they belong in the same reject arm rather than silently building a
# field whose directives are integers.
_CHAR_WISE_TYPES = (
    str,
    bytes,
    bytearray,
    memoryview,
)


def validated_field_directives(label: str, directives: Any) -> tuple[Any, ...]:
    """Return ``directives`` as a tuple, or raise the typed construction-time reject.

    ``label`` names the consuming factory (``"DjangoListField"``,
    ``"DjangoMutationField"``, ``"auth field"``, ...) so the ``ConfigurationError``
    points at the assignment line the consumer actually wrote.

    The message wording is fixed across every caller on purpose: it is the one
    string a consumer greps for, and the callers' tests match on it.
    """
    if isinstance(directives, _CHAR_WISE_TYPES):
        raise ConfigurationError(
            f"{label} directives must be a sequence of directive instances; "
            f"got {_safe_type_name(directives)}.",
        )
    try:
        return tuple(directives)
    except Exception as exc:
        # Naming the escaping exception's TYPE (never its message, which a
        # hostile ``__str__`` owns) keeps the diagnostic useful without
        # letting deployment-supplied text into the envelope; ``__cause__``
        # carries the original for anyone reading the traceback.
        raise ConfigurationError(
            f"{label} directives could not be read ({_safe_type_name(exc)}).",
        ) from exc
