"""Tests for the shared optional-import raising guard (``utils/imports.py``, spec-041 Slice 1).

``require_optional_module`` is the generic raising primitive soft-dependency
guards wrap (``routers.py::require_channels()``). These tests stay generic:
router-specific hint wording and channels-absence behavior live in
``tests/test_routers.py`` so the utility owner remains portable for future
soft dependencies.
"""

import importlib
import sys

import pytest

from django_strawberry_framework.utils import imports as imports_module
from django_strawberry_framework.utils.imports import require_optional_module

_HINT = "TestFeature requires somepackage. Install it with `pip install somepackage`."


def test_require_optional_module_returns_the_real_module_on_success():
    """A present module is imported and returned unchanged."""
    assert require_optional_module("sys", install_hint=_HINT) is sys


def test_require_optional_module_raises_the_hint_and_chains_the_original():
    """An absent module raises ``ImportError`` carrying the hint, chaining the real error."""
    with pytest.raises(ImportError, match="pip install somepackage") as exc_info:
        require_optional_module(
            "definitely_not_an_installed_module_dsf",
            install_hint=_HINT,
        )
    assert str(exc_info.value) == _HINT
    assert isinstance(exc_info.value.__cause__, ImportError)
    assert "definitely_not_an_installed_module_dsf" in str(exc_info.value.__cause__)


def test_require_optional_module_does_not_memoize(monkeypatch):
    """Each call re-runs the import so eviction-based absence tests can re-hit the guard."""
    calls: list[str] = []
    real_import_module = importlib.import_module

    def recording_import_module(name, package=None):
        calls.append(name)
        return real_import_module(name, package)

    monkeypatch.setattr(imports_module.importlib, "import_module", recording_import_module)
    require_optional_module("sys", install_hint=_HINT)
    require_optional_module("sys", install_hint=_HINT)
    assert calls == ["sys", "sys"]
