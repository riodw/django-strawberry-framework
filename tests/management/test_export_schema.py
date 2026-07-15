"""Management command tests for export_schema selector errors, schema validation, and CLI contracts."""

import sys
import types
from io import StringIO

import pytest
import strawberry
from django.core.management import CommandError, call_command
from strawberry.printer import print_schema

from django_strawberry_framework.management.commands.export_schema import Command

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


def test_export_schema_raises_command_error_when_path_flag_has_no_value(monkeypatch):
    _make_test_module(monkeypatch, schema=_make_schema())
    with pytest.raises(CommandError):
        call_command("export_schema", "test_module:schema", "--path")


@pytest.mark.parametrize(
    ("selector", "message"),
    [
        ("", "module path is empty"),
        (":schema", "module path is empty"),
        (".config.schema", "relative module paths"),
    ],
)
def test_export_schema_raises_command_error_for_malformed_selector(selector, message):
    with pytest.raises(CommandError, match=message):
        call_command("export_schema", selector)


def test_export_schema_path_help_documents_destructive_utf8_write():
    parser = Command().create_parser("manage.py", "export_schema")
    path_action = next(action for action in parser._actions if "--path" in action.option_strings)

    assert path_action.help == "Write UTF-8 SDL to this file, overwriting it without prompting"


def test_export_schema_stdout_matches_path_file_and_print_schema(monkeypatch, tmp_path):
    """Stdout, ``--path``, and ``print_schema`` must emit identical SDL bytes."""
    schema = _make_schema()
    _make_test_module(monkeypatch, schema=schema)
    out = StringIO()
    call_command("export_schema", "test_module:schema", stdout=out)
    path = tmp_path / "schema.graphql"
    call_command(
        "export_schema",
        "test_module:schema",
        "--path",
        str(path),
        stdout=StringIO(),
    )
    expected = print_schema(schema)
    assert out.getvalue() == expected
    assert path.read_text(encoding="utf-8") == expected


def test_export_schema_raises_command_error_when_path_flag_is_whitespace_only(monkeypatch):
    _make_test_module(monkeypatch, schema=_make_schema())
    with pytest.raises(CommandError, match="--path requires a non-empty value"):
        call_command("export_schema", "test_module:schema", "--path", "   ")


# The ``--path`` directory-missing and empty-string failure branches moved to
# the fakeshop project suite (examples/fakeshop/tests/test_export_schema.py),
# where they run against the real ``config.schema`` per feedback4.md. The
# parser-only ``--path`` no-value contract above stays package-side (it short-
# circuits in argparse, before any project schema matters).
