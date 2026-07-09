"""The DRF soft-dependency guard shared by every serializer-mutation module (spec-039 Decision 12).

``djangorestframework`` is a SOFT dependency: ``import django_strawberry_framework``
must succeed without it, and ``from django_strawberry_framework import *`` must stay
DRF-free (``SerializerMutation`` is resolved by name through the root
``__getattr__``, never added to ``__all__`` - F1). This package gates the DRF
import behind one guard so every ``rest_framework/`` module + the root
``__getattr__`` route a DRF-absent build through the SAME install-hint
``ImportError``.

The install hint names ``djangorestframework>=3.17.0`` - the Slice-0 verified
floor (place 2 of the three-places-that-must-agree: place 1 is the
``[dependency-groups].dev`` pin in ``pyproject.toml``, place 3 is the spec Risks
note; all three say ``>=3.17.0``). Importing THIS package runs ``require_drf()`` as
its guard, so ``import django_strawberry_framework.rest_framework`` raises the
guarded ``ImportError`` when DRF is absent. Generalizes the
``types/converters.py`` soft-import precedent (return-``None``) to a RAISING guard.
"""

from __future__ import annotations

from typing import Any

from ..utils.imports import require_optional_module

# The single DRF install-hint string (spec-039 Slice 0 carry-forward, Decision 12).
# Every DRF-absent raise routes through ``require_drf()`` so the hint lives in
# exactly one source location and names the verified floor.
_DRF_INSTALL_HINT: str = (
    "SerializerMutation requires djangorestframework, which is not installed. Install it "
    "with `pip install 'djangorestframework>=3.17.0'` (the package's verified DRF floor)."
)


def require_drf() -> Any:
    """Import + return the DRF ``rest_framework`` package, or raise the install hint.

    The shared soft-dependency guard (spec-039 Decision 12): every serializer-mutation
    module + the root ``__getattr__`` call this before importing a DRF class. When DRF
    is present it returns the imported ``rest_framework`` module; when absent it raises
    an ``ImportError`` carrying the single ``_DRF_INSTALL_HINT`` string (the original
    chained), so a DRF-absent consumer sees a clear, actionable install message rather
    than a bare ``ModuleNotFoundError``. No memoization - each call re-runs the import so
    the absent-DRF test can evict ``sys.modules`` and re-hit the guard in one process.

    Delegates to ``utils/imports.py::require_optional_module`` exactly as
    ``routers.py::require_channels`` and
    ``middleware/debug_toolbar.py::require_debug_toolbar`` do - the three soft-dependency
    guards are identical thin wrappers over the one raising primitive. The absence test
    simulates DRF absence with the importlib-native ``sys.modules[...] = None`` sentinel
    (``tests/rest_framework/test_soft_dependency.py``), which raises for the delegated
    ``importlib.import_module`` call.
    """
    return require_optional_module("rest_framework", install_hint=_DRF_INSTALL_HINT)


# Guard on import: ``import django_strawberry_framework.rest_framework`` raises the
# guarded ``ImportError`` when DRF is absent (the root ``__getattr__`` reaches
# ``rest_framework.sets`` through this package, so the guard fires before the
# DRF-importing submodule loads).
require_drf()
