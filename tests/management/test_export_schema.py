"""Tests for django_strawberry_framework.management.commands.export_schema."""

import sys
import types

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
# test (rev3 L4 cleanup contract). The tests are order-independent under
# any pytest collection ordering.


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


def test_export_schema_raises_command_error_when_path_directory_missing(monkeypatch, tmp_path):
    _make_test_module(monkeypatch, schema=_make_schema())
    missing_dir_path = tmp_path / "nonexistent_dir" / "schema.graphql"
    with pytest.raises(CommandError, match="No such file or directory"):
        call_command(
            "export_schema",
            "test_module:schema",
            "--path",
            str(missing_dir_path),
        )


def test_export_schema_raises_command_error_when_path_flag_has_no_value(monkeypatch):
    _make_test_module(monkeypatch, schema=_make_schema())
    with pytest.raises(CommandError):
        call_command("export_schema", "test_module:schema", "--path")


def test_export_schema_raises_command_error_when_path_flag_is_empty_string(monkeypatch):
    _make_test_module(monkeypatch, schema=_make_schema())
    with pytest.raises(CommandError, match="--path requires a non-empty value"):
        call_command("export_schema", "test_module:schema", "--path", "")
