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
submodule unimportable) compose ``evicted_modules`` with ``blocked_modules`` for the submodule
sentinel - see the degraded-partial-install row in ``tests/test_routers.py`` and the
broken-install row in ``tests/middleware/test_debug_toolbar.py``.
``blocked_modules`` is the one writer of the ``None`` sentinel, so it also serves the
framework-own-module tolerance tests (an unimportable ``django_strawberry_framework.*``
submodule during a registry or input-namespace clear), which block a name without evicting
anything around it.
"""

from __future__ import annotations

import contextlib
import sys
from collections.abc import Generator
from types import ModuleType


def _matches(name: str, prefixes: tuple[str, ...]) -> bool:
    """True when ``name`` equals one of ``prefixes`` or is a dotted child of one."""
    return any(name == prefix or name.startswith(f"{prefix}.") for prefix in prefixes)


@contextlib.contextmanager
def evicted_modules(
    *prefixes: str,
    parent: ModuleType,
    attr: str,
) -> Generator[dict[str, ModuleType], None, None]:
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
def blocked_modules(*names: str) -> Generator[None, None, None]:
    """Install the ``None`` blocked-import sentinel under each of ``names``; restore on exit.

    A ``None`` entry in ``sys.modules`` makes both a statement ``import`` and
    ``importlib.import_module`` raise ``ImportError`` for that name. On exit, normal or by
    exception, each name that held a module before the block gets that module back and every
    other name is removed, so no sentinel outlives the block (under ``--dist loadscope`` a
    stranded one poisons every later import of that name in the worker).
    """
    saved = {name: sys.modules.get(name) for name in names}
    try:
        for name in names:
            # basedpyright: typeshed types sys.modules values as ModuleType, but the import
            # system reads a None value as "blocked" and raises ImportError for that name
            sys.modules[name] = None  # pyright: ignore[reportArgumentType]
        yield
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


@contextlib.contextmanager
def simulated_absence(
    sentinel_name: str,
    *prefixes: str,
    parent: ModuleType,
    attr: str,
) -> Generator[dict[str, ModuleType], None, None]:
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
    with (
        evicted_modules(sentinel_name, *prefixes, parent=parent, attr=attr) as saved,
        blocked_modules(sentinel_name),
    ):
        yield saved
