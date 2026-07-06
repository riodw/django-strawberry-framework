"""Optional-import handling for best-effort subsystem lookups (feedback P1.5 owner).

The single owner for the package's "reach into a module that may not be
importable / may not be loaded" patterns. Three call sites shared this
shape before it was single-sited here:

- ``registry.py::_clear_if_importable`` (best-effort subsystem co-clears);
- ``registry.py::_clear_if_loaded`` (the opt-in-preserving auth co-clear);
- ``utils/inputs.py::_safe_import`` (generated-input namespace clearing).

New optional-import handling (a partially-installed extra, a sidecar
package absent from a build) belongs here, not inline at a fourth call
site.
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


# TODO(spec-041 Slice 1): add the raising optional-dependency primitive here:
# ``require_optional_module(module_name, *, install_hint, feature_label)``.
#
# TODO(spec-041 Slice 1) pseudo-steps:
# - accept a module name plus keyword-only ``install_hint`` and ``feature_label``;
# - import the module through ``importlib.import_module``;
# - return the imported module object unchanged on success;
# - on ``ImportError``, raise a new ``ImportError`` carrying ``install_hint`` and
#   chain the original exception.
#
# Contract details:
# - no memoization; absence tests must evict ``sys.modules`` and re-hit imports;
# - ``feature_label`` exists for docstrings / future diagnostics, not branching;
# - do not swallow ``AttributeError``; this imports modules, not module attrs;
# - keep this primitive generic, and keep feature-specific hint strings at the
#   feature owner (``routers.py::_CHANNELS_INSTALL_HINT`` for spec-041).
