"""Shared soft-dependency absence simulation for the optional-import guards.

One home for the ``sys.modules`` eviction + two-sided restore + ``None``-sentinel
discipline that the DRF, channels, and debug-toolbar soft-dependency suites each
hand-rolled. All three guards reach their optional dependency through
``django_strawberry_framework/utils/imports.py::require_optional_module`` (an
``importlib.import_module`` call), so a ``sys.modules[name] = None`` entry raises
``ImportError`` for each, which the guard re-raises as its install hint.

The sentinel is keyed on the top-level third-party name, a different ``sys.modules`` key
from the framework's own ``django_strawberry_framework.*`` subpackages, so it never shadows
the relative import that reaches the guard - which is why it replaces the older
``builtins.__import__`` block and its ``level == 0`` discrimination.

Pure absence uses ``simulated_absence``. Broken-install cases (top-level present, one
submodule unimportable) compose inline on ``evicted_modules`` with a submodule sentinel -
see ``tests/test_routers.py`` (Test 17) and ``tests/middleware/test_debug_toolbar.py``
(Test 11a). Third-party absence only: framework-own-module eviction (registry co-clear
tolerance) is a different concern and stays in its own tests.
"""

from __future__ import annotations

import contextlib
import sys
from collections.abc import Iterator
from types import ModuleType


def _matches(name: str, prefixes: tuple[str, ...]) -> bool:
    """True when ``name`` equals one of ``prefixes`` or is a dotted child of one."""
    return any(name == prefix or name.startswith(f"{prefix}.") for prefix in prefixes)


@contextlib.contextmanager
def evicted_modules(
    *prefixes: str,
    parent: ModuleType,
    attr: str,
) -> Iterator[dict[str, ModuleType]]:
    """Evict ``sys.modules`` entries under ``prefixes``; restore both sides on exit.

    Pops every entry whose name equals a prefix or starts with ``prefix + "."``, yielding
    the saved ``{name: module}`` mapping so a caller can reinstate individual real modules
    for a broken-install simulation. ``parent``/``attr`` name the framework attribute a
    blocked-then-retried import would rebind to a fresh module object; presence is
    tracked with a ``missing`` sentinel via ``vars(parent).get(attr, missing)`` and
    restored on exit through ``vars(parent).pop`` / ``setattr`` - every read and write
    goes through ``__dict__`` directly so a package ``__getattr__`` never fires, not even
    on teardown (a ``hasattr(parent, attr)`` probe there would). This two-sided restore
    (spec-041 D3) keeps the attribute path and the import path pointing at one module
    object under ``pytest-xdist``.
    """
    missing = object()
    saved_attr = vars(parent).get(attr, missing)
    saved = {name: sys.modules.pop(name) for name in list(sys.modules) if _matches(name, prefixes)}
    try:
        yield saved
    finally:
        for name in list(sys.modules):
            if _matches(name, prefixes):
                del sys.modules[name]
        sys.modules.update(saved)
        if saved_attr is missing:
            vars(parent).pop(attr, None)
        else:
            setattr(parent, attr, saved_attr)


@contextlib.contextmanager
def simulated_absence(
    sentinel_name: str,
    *prefixes: str,
    parent: ModuleType,
    attr: str,
) -> Iterator[dict[str, ModuleType]]:
    """Simulate ``sentinel_name`` uninstalled, via a ``sys.modules[...] = None`` sentinel.

    The ``None`` entry makes both a statement ``import`` and ``importlib.import_module``
    raise ``ImportError``, which each guard re-raises as its install hint. ``sentinel_name``
    is the top-level third-party package; it heads the ``evicted_modules`` prefix list, so
    the helper evicts AND restores it and owns the ``None`` teardown itself - the sentinel is
    never stranded (which under ``--dist loadscope`` would poison every later import of that
    name in the worker), and a caller need not repeat ``sentinel_name`` in ``prefixes`` to
    have it cleaned up. ``prefixes`` additionally evict the framework's own guard-owning
    module so its cache / module body re-runs the guard.
    """
    with evicted_modules(sentinel_name, *prefixes, parent=parent, attr=attr) as saved:
        sys.modules[sentinel_name] = None
        yield saved
