"""Shared context read/write helpers for optimizer ↔ resolver hand-off.

Both the optimizer (write side) and the relation resolvers (read side)
need to interact with Strawberry's ``info.context``, which can be one
of three shapes:

- ``None`` — Strawberry's default when no ``context_value`` is provided.
- An object — the typical Strawberry context (attribute access).
- A dict — consumers sometimes pass a plain dict.
- A frozen object — ``MappingProxyType``, frozen dataclass,
  ``pydantic`` model with ``frozen=True`` (write side only — the read
  helper is read-only and does not need to handle TypeError).

Centralizing the dispatch here means a future broadening (a new
context shape, a new exception class to swallow on write) only has to
land in one place rather than across ``optimizer/extension.py`` and
``types/resolvers.py``.
"""

from __future__ import annotations

from typing import Any


def get_context_value(context: Any, key: str, default: Any = None) -> Any:
    """Return ``key`` from an object-or-dict context, or ``default``.

    Read-only; safe on frozen contexts.  ``None`` short-circuits to
    ``default`` so callers can pass ``getattr(info, "context", None)``
    directly without an extra guard.
    """
    if context is None:
        return default
    if isinstance(context, dict):
        return context.get(key, default)
    return getattr(context, key, default)


def stash_on_context(context: Any, key: str, value: Any) -> None:
    """Stash ``value`` on ``context`` under ``key``; silently skip if impossible.

    Strawberry's default context is an object, so ``setattr`` is the
    primary path.  Consumers sometimes pass a plain ``dict`` as context,
    so we fall back to ``__setitem__`` when ``setattr`` raises.  Frozen
    objects (``MappingProxyType``, frozen dataclasses, ``pydantic``
    models with ``frozen=True``) raise ``TypeError`` on assignment;
    those stashes are silently skipped — the optimizer's introspection
    surface is a nice-to-have, not a correctness invariant, so a
    read-only context must not abort the resolver chain.

    When ``context`` is ``None`` (Strawberry's default when no
    ``context_value`` is provided), the stash is silently skipped.
    """
    if context is None:
        return
    try:
        setattr(context, key, value)
        return
    except (AttributeError, TypeError):
        pass
    try:
        context[key] = value
    except (TypeError, KeyError):
        return
