"""Tests for the shared optional-import helpers (``utils/imports.py``, spec-041 Slice 1).

``require_optional_module`` is the generic raising primitive soft-dependency
guards wrap (``routers.py::require_channels()`` / ``rest_framework::require_drf()``);
``import_attr_if_importable`` is the best-effort variant callers use when a missing
optional module should degrade to ``None`` rather than raise (``types/converters.py``'s
postgres fields, ``registry.py``'s subsystem co-clears). These tests stay generic:
router-specific hint wording and channels-absence behavior live in
``tests/test_routers.py`` so the utility owner remains portable for future
soft dependencies.
"""

import importlib
import sys
import types

import pytest

from django_strawberry_framework.utils import imports as imports_module
from django_strawberry_framework.utils.imports import (
    import_attr_if_importable,
    require_optional_module,
)

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


def test_import_attr_if_importable_returns_the_attribute_on_an_importable_module(monkeypatch):
    """A reachable module returns its named attribute unchanged."""
    fake = types.ModuleType("dsf_fake_importable_module")
    marker = object()
    fake.Marker = marker
    monkeypatch.setitem(sys.modules, "dsf_fake_importable_module", fake)
    assert import_attr_if_importable("dsf_fake_importable_module", "Marker") is marker


def test_import_attr_if_importable_returns_none_when_the_module_is_unimportable(monkeypatch):
    """A ``None`` entry in ``sys.modules`` makes ``import_module`` raise ``ImportError``;
    the helper swallows it and returns ``None`` so callers skip an absent optional module.
    """
    monkeypatch.setitem(sys.modules, "dsf_absent_optional_module", None)
    assert import_attr_if_importable("dsf_absent_optional_module", "Anything") is None


def test_import_attr_if_importable_raises_when_importable_module_lacks_the_attr(monkeypatch):
    """An importable module missing the expected attribute fails loud (``AttributeError``)
    rather than silently degrading - a broken environment, not an absent optional dependency.
    """
    fake = types.ModuleType("dsf_fake_module_without_attr")
    monkeypatch.setitem(sys.modules, "dsf_fake_module_without_attr", fake)
    with pytest.raises(AttributeError):
        import_attr_if_importable("dsf_fake_module_without_attr", "Missing")
