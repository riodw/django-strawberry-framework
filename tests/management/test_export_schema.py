"""Package tests for export_schema argparse contracts and newline-preserving file writes.

Handle-level selector errors, the non-schema symbol check, whitespace ``--path``,
and stdout/``--path``/``print_schema`` byte identity run against ``config.schema``
in ``examples/fakeshop/tests/test_export_schema.py``. What stays here has no
project-schema shape: argparse rejects a missing positional and a bare ``--path``
before ``handle`` runs; ``Command.create_parser`` is the only place the
destructive-write help string is asserted; ``Path.write_text(..., newline="")``
is a kwargs pin that Unix SDL text cannot distinguish from the platform default.
"""

import sys
import types
from io import StringIO

import pytest
import strawberry
from django.core.management import CommandError, call_command

from django_strawberry_framework.management.commands.export_schema import Command


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


def test_export_schema_raises_command_error_for_missing_positional_argument():
    with pytest.raises(CommandError):
        call_command("export_schema")


def test_export_schema_raises_command_error_when_path_flag_has_no_value():
    with pytest.raises(CommandError):
        call_command("export_schema", "x", "--path")


def test_export_schema_path_help_documents_destructive_utf8_write():
    parser = Command().create_parser("manage.py", "export_schema")
    path_action = next(action for action in parser._actions if "--path" in action.option_strings)

    assert path_action.help == "Write UTF-8 SDL to this file, overwriting it without prompting"


def test_export_schema_file_write_disables_newline_translation(monkeypatch):
    """File output preserves SDL LF bytes on platforms with different native newlines."""
    schema = _make_schema()
    _make_test_module(monkeypatch, schema=schema)
    captured: dict[str, object] = {}

    def write_text(
        self,
        data,
        *,
        encoding=None,
        errors=None,
        newline=None,
    ):
        captured.update(data=data, encoding=encoding, errors=errors, newline=newline)
        return len(data)

    monkeypatch.setattr("pathlib.Path.write_text", write_text)
    call_command(
        "export_schema",
        "test_module:schema",
        "--path",
        "schema.graphql",
        stdout=StringIO(),
    )

    assert captured["encoding"] == "utf-8"
    assert captured["newline"] == ""
