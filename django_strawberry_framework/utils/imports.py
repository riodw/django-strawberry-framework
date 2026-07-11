"""Optional-import handling for best-effort subsystem lookups (feedback P1.5 owner).

The single owner for the package's "reach into a module that may not be
importable / may not be loaded" patterns. Three call sites shared this
shape before it was single-sited here:

- ``registry.py::_clear_if_importable`` (best-effort subsystem co-clears);
- ``registry.py::_clear_if_loaded`` (the opt-in-preserving auth co-clear);
- ``utils/inputs.py::_safe_import`` (generated-input namespace clearing).

New optional-import handling (a partially-installed extra, a sidecar
package absent from a build) belongs here, not inline at a fourth call
site. ``import_attr`` (DRY review B2) is the STRICT sibling for internal
deferred-import seams where a failure must propagate.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any


def import_attr_if_importable(module_path: str, attr_name: str) -> Any | None:
    """Import ``module_path`` best-effort and return its ``attr_name``; ``None`` on ImportError.

    The cycle-safe best-effort import owner: a partial-load environment (one
    submodule reachable, another not) returns ``None`` for the unreachable
    module so the caller can skip it and continue. A ``None`` entry in
    ``sys.modules`` (the test-isolation shape for simulating an unimportable
    submodule) raises ``ImportError`` inside ``import_module``, same as the
    previous inline guards, and so also returns ``None``. The ``getattr`` has
    NO default - a missing attribute on an importable module is a real bug
    and fails loud (``AttributeError``), matching the registry co-clear
    semantics.
    """
    try:
        module = importlib.import_module(module_path)
    except ImportError:
        return None
    return getattr(module, attr_name)


def loaded_attr(module_path: str, attr_name: str) -> Any | None:
    """Return ``module_path``'s ``attr_name`` only when the module is ALREADY loaded.

    The opt-in-preserving variant: it never imports on behalf of a consumer
    who skipped the module. A module absent from ``sys.modules`` returns
    ``None`` (nothing loaded means nothing to reach); a loaded module's
    ``getattr`` has NO default and fails loud on a missing attribute, same
    as ``import_attr_if_importable``.
    """
    module = sys.modules.get(module_path)
    if module is None:
        return None
    return getattr(module, attr_name)


def import_attr(module_path: str, attr_name: str) -> Any:
    """Import ``module_path`` (STRICT) and return its ``attr_name`` (DRY review B2).

    The strict member of the family: a broken import propagates (unlike the
    best-effort ``import_attr_if_importable``, which would MASK a broken
    internal module as ``None``), an unloaded module IS imported (unlike the
    opt-in-preserving ``loaded_attr``), and no install hint is reframed (unlike
    ``require_optional_module``). For internal deferred-import seams - e.g. the
    generated ``resolve_sync`` / ``resolve_async`` bodies' function-local
    resolver-module import (the cycle guard) - where both the module and the
    attribute are the package's own and any failure is a real bug that must
    fail loud. The ``getattr`` has NO default for the same reason.
    """
    return getattr(importlib.import_module(module_path), attr_name)


def require_optional_module(module_name: str, *, install_hint: str) -> Any:
    """Import + return an optional module, or raise ``ImportError`` carrying ``install_hint``.

    The RAISING optional-dependency primitive (spec-041 Decision 5): soft-dependency
    guards (``routers.py::require_channels()``) wrap this instead of hand-rolling a
    fourth import-handling pattern beside the best-effort helpers above. On success
    the imported module object is returned unchanged; on ``ImportError`` a new
    ``ImportError`` carrying the caller's ``install_hint`` is raised with the
    original chained (``from exc``), so the consumer sees an actionable install
    message with the real failure preserved underneath.

    No memoization - each call re-runs the import so eviction-simulated absence
    tests can evict ``sys.modules`` entries and re-hit the guard in one process.
    There is deliberately NO ``feature_label`` parameter: the feature-specific
    text lives entirely in the caller's ``install_hint`` (the ``require_drf()``
    shape), and hint strings stay single-sited at the feature owner.
    """
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise ImportError(install_hint) from exc
