"""Shared context read/write helpers for optimizer ↔ resolver hand-off.

Both the optimizer (write side) and the relation resolvers (read side)
need to interact with Strawberry's ``info.context``, which can take
several shapes:

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

Defensive-coerce stance (package-wide). Reflective shape reads off
Strawberry / graphql-core / Django descriptors throughout the
optimizer subpackage use the pattern ``getattr(obj, name, None) or
{}`` (or ``or ()`` / ``or set()``). This is *correct* here because the
upstream contract genuinely allows the attribute to be absent or
``None`` on legitimate shapes (e.g., ``SelectedField.directives``).
That posture is the opposite of the one taken for consumer-supplied
input — see ``conf.py`` module docstring — and the two should not
be conflated when refactoring.
"""

from __future__ import annotations

from typing import Any

DST_OPTIMIZER_PLAN = "dst_optimizer_plan"
DST_OPTIMIZER_FK_ID_ELISIONS = "dst_optimizer_fk_id_elisions"
DST_OPTIMIZER_PLANNED = "dst_optimizer_planned"
DST_OPTIMIZER_LOOKUP_PATHS = "dst_optimizer_lookup_paths"
DST_OPTIMIZER_STRICTNESS = "dst_optimizer_strictness"


def get_context_value(context: Any, key: str, default: Any = None) -> Any:
    """Return ``key`` from an object-or-dict context, or ``default``.

    Read-only; safe on frozen contexts.  ``None`` short-circuits to
    ``default`` so callers can pass ``getattr(info, "context", None)``
    directly without an extra guard.
    """
    if context is None:
        return default
    # Dispatch order matters: ``dict`` is checked before the ``getattr``
    # fallback so that a ``dict`` subclass that *also* exposes attribute
    # access (e.g., a ``Box``-style mapping) takes the mapping branch,
    # which matches Strawberry's normal usage.  Do not reverse the order.
    if isinstance(context, dict):
        return context.get(key, default)
    return getattr(context, key, default)


def stash_on_context(context: Any, key: str, value: Any) -> None:
    """Stash ``value`` on ``context`` under ``key``; silently skip if impossible.

    Dispatch order mirrors ``get_context_value``: ``dict`` instances are
    treated as mappings first so a ``dict`` subclass with separate
    attribute storage round-trips through the same branch the resolver
    reads from. Non-``dict`` contexts use ``setattr`` first and fall
    back to ``__setitem__`` for mapping-like objects (Strawberry's
    default context is an object; some consumers pass a plain dict).
    Frozen objects (``MappingProxyType``, frozen dataclasses,
    ``pydantic`` models with ``frozen=True``) raise ``TypeError`` on
    assignment; those stashes are silently skipped — the optimizer's
    introspection surface is a nice-to-have, not a correctness
    invariant, so a read-only context must not abort the resolver chain.

    When ``context`` is ``None`` (Strawberry's default when no
    ``context_value`` is provided), the stash is silently skipped.

    Implementation note: the dict-first decision is expressed as a
    guard *around* the ``setattr`` block (skip ``setattr`` entirely for
    ``dict`` instances) rather than as a parallel ``try`` / ``except``
    path. Both shapes have the same observable behavior, but the
    guard-and-shared-tail form keeps one ``except TypeError`` handler
    that ``MappingProxyType``-style fixtures already exercise, so no
    parallel test scaffold for a frozen ``dict`` subclass is required
    to keep the package coverage gate at 100%.
    """
    if context is None:
        return
    if not isinstance(context, dict):
        try:
            setattr(context, key, value)
            return
        except (AttributeError, TypeError):
            pass
    try:
        context[key] = value
    except TypeError:
        # ``MappingProxyType`` and other frozen mappings raise ``TypeError``
        # on ``__setitem__``.  Narrow to ``TypeError`` only — a real ``dict``
        # never raises ``KeyError`` from assignment, and a future mapping
        # subclass that raises a custom error should surface, not be silently
        # swallowed.  The dict-first guard above routes plain ``dict``
        # instances and ``dict`` subclasses through this same handler so
        # frozen subclass shapes share coverage with ``MappingProxyType``.
        return
