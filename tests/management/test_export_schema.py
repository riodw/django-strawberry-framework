"""Tests for django_strawberry_framework.management.commands.export_schema."""

import sys
import types
from io import StringIO

import pytest
import strawberry
from django.core.management import CommandError, call_command

# ---------------------------------------------------------------------------
# Shared fixture pattern (use inline per test, not a session fixture)
# ---------------------------------------------------------------------------
#
# Every test that synthesizes ``test_module`` does so via
# ``monkeypatch.setitem(sys.modules, "test_module", module)`` so pytest's
# ``monkeypatch`` teardown clears the entry from ``sys.modules`` at end of
# test (rev3 L4 cleanup contract). The seven tests are order-independent
# under any pytest collection ordering.


def _make_test_module(monkeypatch, **attrs):
    module = types.ModuleType("test_module")
    for key, value in attrs.items():
        setattr(module, key, value)
    monkeypatch.setitem(sys.modules, "test_module", module)
    return module


def _make_schema():
    @strawberry.type
    class Query:
        hello: str = "world"

    return strawberry.Schema(query=Query)


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


def test_export_schema_writes_sdl_to_stdout_by_default(monkeypatch):
    _make_test_module(monkeypatch, schema=_make_schema())
    out = StringIO()
    call_command("export_schema", "test_module:schema", stdout=out)
    assert "type Query" in out.getvalue()


def test_export_schema_writes_sdl_to_path_when_path_set(monkeypatch, tmp_path):
    _make_test_module(monkeypatch, schema=_make_schema())
    out_path = tmp_path / "schema.graphql"
    call_command("export_schema", "test_module:schema", "--path", str(out_path))
    assert out_path.exists()
    assert "type Query" in out_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


def test_export_schema_raises_command_error_for_unimportable_module():
    with pytest.raises(CommandError, match="No module named"):
        call_command("export_schema", "does.not.exist:schema")


def test_export_schema_raises_command_error_for_missing_attribute_on_module(monkeypatch):
    _make_test_module(monkeypatch)
    with pytest.raises(CommandError, match="does_not_exist"):
        call_command("export_schema", "test_module:does_not_exist")


def test_export_schema_raises_command_error_for_non_schema_symbol(monkeypatch):
    _make_test_module(monkeypatch, not_a_schema=1)
    with pytest.raises(CommandError, match=r"must be an instance of strawberry\.Schema"):
        call_command("export_schema", "test_module:not_a_schema")


def test_export_schema_raises_command_error_for_missing_positional_argument():
    with pytest.raises(CommandError):
        call_command("export_schema")


# ---------------------------------------------------------------------------
# Default-symbol-name fallback (Decision 3)
# ---------------------------------------------------------------------------


def test_export_schema_falls_back_to_default_symbol_name_schema(monkeypatch):
    _make_test_module(monkeypatch, schema=_make_schema())
    out = StringIO()
    call_command("export_schema", "test_module", stdout=out)
    assert "type Query" in out.getvalue()
