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

_MISSING: Any = object()
"""Sentinel for ``get_context_value`` to distinguish a missing attribute
from an attribute that was explicitly stashed as ``None``."""


def get_context_value(context: Any, key: str, default: Any = None) -> Any:
    """Return ``key`` from an object-or-dict context, or ``default``.

    Dispatch mirrors ``stash_on_context`` so the read and write paths stay
    symmetric:

    - ``None`` short-circuits to ``default`` so callers can pass
      ``getattr(info, "context", None)`` without an extra guard.
    - ``dict`` instances (and subclasses) take the mapping branch via
      ``context.get(key, default)``; this matches Strawberry's normal
      usage and lets ``Box``-style dict subclasses that *also* expose
      attribute access still resolve through ``__getitem__`` first.
      Values stashed by code outside this module via ``setattr`` on a
      dict subclass are intentionally invisible to this branch — the
      read helper preserves write/read symmetry with
      ``stash_on_context``, which routes ``dict`` writes through
      ``__setitem__``.
    - Non-``dict`` contexts try attribute access first via ``getattr``;
      if the attribute is genuinely absent (sentinel ``_MISSING``) the
      helper falls through to ``context[key]``. The fallback is
      load-bearing for non-``dict`` mappings whose values were stashed
      via ``__setitem__`` because their object disallowed ``setattr``
      (e.g. ``__slots__`` classes, or consumer contexts like
      ``strawberry-graphql-django``'s ``StrawberryDjangoContext`` whose
      ``__getitem__`` is bridged to ``__getattribute__``). Pinned by
      ``tests/optimizer/test_extension.py::test_stash_on_non_dict_mapping_reads_correctly``
      (``__slots__`` mapping shape) and
      ``tests/optimizer/test_extension.py::test_get_context_value_swallows_attribute_error_from_getitem``
      (bridged-``AttributeError`` shape) — a future refactor that
      removes this fallback must trip those pins.
    - ``__getitem__`` on a missing key may raise ``KeyError``,
      ``TypeError``, or ``AttributeError`` (the last one for bridged
      attribute-access contexts); all three are caught and return
      ``default``. Read-only / frozen contexts are safe for the same
      reason.
    """
    if context is None:
        return default
    if not isinstance(context, dict):
        val = getattr(context, key, _MISSING)
        if val is not _MISSING:
            return val
    try:
        if isinstance(context, dict):
            return context.get(key, default)
        return context[key]
    except (TypeError, KeyError, AttributeError):
        return default


def stash_on_context(context: Any, key: str, value: Any) -> None:
    """Stash ``value`` on ``context`` under ``key``; silently skip if impossible.

    Dispatch order mirrors ``get_context_value``: ``dict`` instances are
    treated as mappings first so a ``dict`` subclass with separate
    attribute storage round-trips through the same branch the resolver
    reads from. Non-``dict`` contexts use ``setattr`` first and fall
    back to ``__setitem__`` for mapping-like objects (Strawberry's
    default context is an object; some consumers pass a plain dict).
    Frozen contexts raise on assignment; those stashes are silently
    skipped — the optimizer's introspection surface is a nice-to-have,
    not a correctness invariant, so a read-only context must not abort
    the resolver chain. The two frozen-shape error modes the dict path
    must absorb are ``TypeError`` (``MappingProxyType``, frozen
    dataclasses, ``pydantic`` models with ``frozen=True``) and
    ``AttributeError`` (Django's ``QueryDict`` when locked raises
    ``AttributeError("This QueryDict instance is immutable")`` from
    ``__setitem__``; ``QueryDict`` is a ``dict`` subclass so the
    dict-first dispatch routes it through the mapping write path).

    When ``context`` is ``None`` (Strawberry's default when no
    ``context_value`` is provided), the stash is silently skipped.

    Implementation note: the dict-first decision is expressed as a
    guard *around* the ``setattr`` block (skip ``setattr`` entirely for
    ``dict`` instances) rather than as a parallel ``try`` / ``except``
    path. Both shapes have the same observable behavior, but the
    guard-and-shared-tail form keeps one mapping-write exception
    handler instead of duplicating the catch in two branches.
    """
    if context is None:
        return
    if not isinstance(context, dict):
        try:
            setattr(context, key, value)
            return
        except (AttributeError, TypeError):
            # Chain into the dict-write path; covers the ``__slots__`` /
            # bridged-context case where ``setattr`` fails but
            # ``__setitem__`` succeeds (e.g., ``StrawberryDjangoContext``
            # whose attribute writes are blocked while item assignment
            # routes through ``__setitem__``). Catch-and-chain is the
            # write-side counterpart to the read-side ``__getitem__``
            # fallback in ``get_context_value`` (the ``try`` /
            # ``except (TypeError, KeyError, AttributeError)`` block that
            # routes through ``context[key]`` when ``getattr`` returns
            # the ``_MISSING`` sentinel) — both paths exist so the
            # helper round-trips through whichever access mode the
            # context supports. The trailing dict-write ``except`` below
            # is the catch-and-return pattern; this one is the
            # catch-and-chain pattern, intentionally distinct.
            pass
    try:
        context[key] = value
    except (TypeError, AttributeError):
        # ``MappingProxyType`` and other frozen mappings raise ``TypeError``
        # on ``__setitem__``; Django's locked ``QueryDict`` (a ``dict``
        # subclass) raises ``AttributeError`` instead. Both are read-only
        # contexts whose stash failures must be silently skipped per the
        # docstring contract; neither indicates a programming bug in the
        # optimizer. Other exception classes (``KeyError`` from a guarded
        # mapping, custom ``RuntimeError`` from a TypedDict-like wrapper)
        # are NOT swallowed — a real ``dict`` never raises ``KeyError``
        # on assignment, and a custom mapping signalling a guarded write
        # should surface rather than silently lose the stash.
        return
