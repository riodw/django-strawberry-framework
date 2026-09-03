"""Import helpers for best-effort, loaded-only, strict, and guarded optional-dependency lookups.

The single owner for the package's "reach into a module that may not be
importable / may not be loaded" patterns. Call sites that share this
shape route through here:

- ``registry.py::_clear_if_importable`` (best-effort per-type co-clears);
- ``types/finalizer.py`` auth bind (opt-in-preserving ``loaded_attr``);
- ``utils/inputs.py::_safe_import`` (generated-input namespace clearing;
  attr-lenient wrapper over ``import_attr_if_importable``);
- ``types/converters.py`` / ``optimizer/nested_planner.py`` (postgres-only
  soft symbols via ``import_attr_if_importable``);
- soft-dependency ``require_*`` guards (``require_optional_module``).

New optional-import handling (a partially-installed extra, a sidecar
package absent from a build) belongs here, not inline at a new call
site. ``import_attr`` is the STRICT sibling for internal
deferred-import seams where a failure must propagate.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any

__all__ = [
    "CHANNELS_FLOOR",
    "STRAWBERRY_FLOOR",
    "import_attr",
    "import_attr_if_importable",
    "loaded_attr",
    "require_optional_module",
]


# The verified Channels floor, interpolated into every install hint that names
# it. Channels is the one optional dependency whose hint text is written at more
# than one site (the router's three, the auth session boundary's one), so the
# version was being re-typed as a bare literal that nothing compared against the
# ``channels[daphne]`` row in ``pyproject.toml``. That row is still the second
# place and must be bumped with this one; there is no third.
CHANNELS_FLOOR = "4.3.2"

# The verified Strawberry floor, interpolated into the one install hint that
# names it (the router's broken-``strawberry.channels`` message). It lives here
# beside ``CHANNELS_FLOOR`` for the same reason: a hard literal in a hint string
# is compared against nothing, so it drifts silently away from the
# ``strawberry-graphql`` row in ``pyproject.toml``. That row is the only other
# place the floor is written and must be bumped with this one.
STRAWBERRY_FLOOR = "0.316.0"


def _plain_text(value: Any) -> Any:
    """Normalize a string subclass before handing it to import machinery."""
    if not isinstance(value, str) or type(value) is str:
        return value
    return str.__str__(value)


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
    module_path = _plain_text(module_path)
    attr_name = _plain_text(attr_name)
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
    module_path = _plain_text(module_path)
    attr_name = _plain_text(attr_name)
    module = sys.modules.get(module_path)
    if module is None:
        return None
    return getattr(module, attr_name)


def import_attr(module_path: str, attr_name: str) -> Any:
    """Import ``module_path`` (STRICT) and return its ``attr_name``.

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
    module_path = _plain_text(module_path)
    attr_name = _plain_text(attr_name)
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
    module_name = _plain_text(module_name)
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise ImportError(_plain_text(install_hint)) from exc
