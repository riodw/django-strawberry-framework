"""Tests for management-command import error translation and path validation."""

import sys
import types

import pytest
from django.core.management import CommandError

from django_strawberry_framework.management.commands._imports import (
    import_module_symbol_or_command_error,
    import_or_command_error,
    import_string_or_command_error,
)


def test_import_or_command_error_passes_through_return_value():
    sentinel = object()
    assert import_or_command_error(lambda: sentinel) is sentinel


def test_import_or_command_error_wraps_import_error():
    original = ImportError("No module named 'nope'")

    def importer():
        raise original

    with pytest.raises(CommandError, match="No module named 'nope'") as exc_info:
        import_or_command_error(importer)
    assert exc_info.value.__cause__ is original


def test_import_or_command_error_wraps_attribute_error():
    original = AttributeError("module 'm' has no attribute 'x'")

    def importer():
        raise original

    with pytest.raises(CommandError, match="has no attribute 'x'") as exc_info:
        import_or_command_error(importer)
    assert str(exc_info.value) == str(original)
    assert exc_info.value.__cause__ is original


def test_import_or_command_error_does_not_swallow_other_exceptions():
    def importer():
        raise ValueError("unrelated")

    with pytest.raises(ValueError, match="unrelated"):
        import_or_command_error(importer)


# ---------------------------------------------------------------------------
# import_module_symbol_or_command_error
# ---------------------------------------------------------------------------


def _make_module(monkeypatch, name="imports_probe_module"):
    module = types.ModuleType(name)
    module.schema = object()
    monkeypatch.setitem(sys.modules, name, module)
    return module


@pytest.mark.parametrize("selector", ["", ":schema"])
def test_import_module_symbol_or_command_error_rejects_empty_module_path(selector):
    # ``import_module_symbol`` reports an empty module path as ``ValueError``
    # ("Empty module name"), which the (ImportError, AttributeError) catch would
    # miss; the selector guard raises a clean CommandError before any import.
    with pytest.raises(CommandError, match="the module path is empty"):
        import_module_symbol_or_command_error(selector, default_symbol_name="schema")


@pytest.mark.parametrize("selector", [".relative", ".relative:schema", ".a.b"])
def test_import_module_symbol_or_command_error_rejects_relative_module_path(selector):
    # ``import_module_symbol`` reports a relative module path as ``TypeError``
    # (relative import without a package), also missed by the narrow catch.
    with pytest.raises(CommandError, match="relative module paths"):
        import_module_symbol_or_command_error(selector, default_symbol_name="schema")


def test_import_module_symbol_or_command_error_resolves_valid_selector(monkeypatch):
    module = _make_module(monkeypatch)
    resolved = import_module_symbol_or_command_error(
        "imports_probe_module:schema",
        default_symbol_name="schema",
    )
    assert resolved is module.schema


def test_import_module_symbol_or_command_error_applies_default_symbol_name(monkeypatch):
    module = _make_module(monkeypatch)
    resolved = import_module_symbol_or_command_error(
        "imports_probe_module",
        default_symbol_name="schema",
    )
    assert resolved is module.schema


def test_import_module_symbol_or_command_error_wraps_import_error():
    # A genuinely unimportable (but well-formed) module path still routes through
    # the ImportError -> CommandError wrapper, not the selector guard.
    with pytest.raises(CommandError, match="No module named") as exc_info:
        import_module_symbol_or_command_error(
            "definitely.not.a.real.module",
            default_symbol_name="schema",
        )
    assert isinstance(exc_info.value.__cause__, ImportError)


def test_import_module_symbol_or_command_error_does_not_mask_module_body_valueerror(monkeypatch):
    # A ValueError raised while importing a *valid* module must surface unchanged:
    # the guard only validates the selector string, it never broadens the catch.
    name = "imports_valueerror_module"

    class _Raiser:
        def __getattr__(self, item):
            raise ValueError("consumer schema construction blew up")

    monkeypatch.setitem(sys.modules, name, _Raiser())
    with pytest.raises(ValueError, match="consumer schema construction blew up"):
        import_module_symbol_or_command_error(f"{name}:schema", default_symbol_name="schema")


# ---------------------------------------------------------------------------
# import_string_or_command_error
# ---------------------------------------------------------------------------


def test_import_string_or_command_error_resolves_valid_path(monkeypatch):
    module = _make_module(monkeypatch)
    assert import_string_or_command_error("imports_probe_module.schema") is module.schema


@pytest.mark.parametrize("dotted_path", [".schema", ".relative.schema"])
def test_import_string_or_command_error_rejects_malformed_module_path(dotted_path):
    with pytest.raises(CommandError, match="module path is empty|relative module paths"):
        import_string_or_command_error(dotted_path)


def test_import_string_or_command_error_wraps_import_error():
    with pytest.raises(CommandError, match="No module named") as exc_info:
        import_string_or_command_error("definitely.not.a.real.module.schema")
    assert isinstance(exc_info.value.__cause__, ImportError)


def test_import_string_or_command_error_does_not_mask_consumer_valueerror(monkeypatch):
    class _Raiser:
        def __getattr__(self, item):
            raise ValueError("consumer module blew up")

    monkeypatch.setitem(sys.modules, "imports_valueerror_module", _Raiser())
    with pytest.raises(ValueError, match="consumer module blew up"):
        import_string_or_command_error("imports_valueerror_module.schema")
