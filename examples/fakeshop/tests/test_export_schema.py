"""Fakeshop project command tests for export_schema against the configured schema."""

from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from strawberry.printer import print_schema


def test_export_schema_writes_fakeshop_sdl_to_stdout_by_default():
    out = StringIO()
    call_command("export_schema", "config.schema:schema", stdout=out)
    assert "type BranchType" in out.getvalue()


@pytest.mark.parametrize(
    "selector",
    ["config.schema:schema", "config.schema"],
    ids=["colon-symbol", "default-symbol"],
)
def test_export_schema_stdout_matches_print_schema(selector):
    """Stdout SDL bytes match ``print_schema`` for both selector spellings."""
    from config.schema import schema

    out = StringIO()
    call_command("export_schema", selector, stdout=out)
    assert out.getvalue() == print_schema(schema)


def test_export_schema_path_file_matches_print_schema(tmp_path):
    """``--path`` writes the same UTF-8 SDL bytes ``print_schema`` returns."""
    from config.schema import schema

    path = tmp_path / "schema.graphql"
    call_command(
        "export_schema",
        "config.schema",
        "--path",
        str(path),
        stdout=StringIO(),
    )
    assert path.read_text(encoding="utf-8") == print_schema(schema)


def test_export_schema_raises_command_error_for_unimportable_module():
    with pytest.raises(CommandError, match="No module named"):
        call_command("export_schema", "does.not.exist:schema")


def test_export_schema_raises_command_error_for_missing_attribute_on_module():
    with pytest.raises(CommandError, match="does_not_exist"):
        call_command("export_schema", "config.schema:does_not_exist")


@pytest.mark.parametrize(
    "symbol",
    ["apps.library.schema:BookType", "apps.products.models:Item", "config.settings:DEBUG"],
    ids=["djangotype-class", "model-class", "settings-value"],
)
def test_export_schema_raises_command_error_for_non_schema_symbol(symbol):
    with pytest.raises(CommandError, match=r"must be an instance of strawberry\.Schema"):
        call_command("export_schema", symbol)


@pytest.mark.parametrize(
    ("selector", "message"),
    [
        ("", "module path is empty"),
        (":schema", "module path is empty"),
        (".config.schema", "relative module paths"),
    ],
    ids=["empty", "colon-only", "relative"],
)
def test_export_schema_raises_command_error_for_malformed_selector(selector, message):
    with pytest.raises(CommandError, match=message):
        call_command("export_schema", selector)


@pytest.mark.parametrize(
    "path",
    ["   ", "\t", "\n"],
    ids=["spaces", "tab", "newline"],
)
def test_export_schema_raises_command_error_when_path_flag_is_whitespace_only(path):
    with pytest.raises(CommandError, match="--path requires a non-empty value"):
        call_command("export_schema", "config.schema", "--path", path)


def test_export_schema_overwrites_existing_path_with_utf8_fakeshop_sdl(tmp_path):
    out = StringIO()
    out_path = tmp_path / "schema.graphql"
    out_path.write_text("stale schema sentinel", encoding="utf-8")

    call_command(
        "export_schema",
        "config.schema",
        "--path",
        str(out_path),
        stdout=out,
    )

    assert out_path.exists()
    written = out_path.read_text(encoding="utf-8")
    assert "type BranchType" in written
    assert "stale schema sentinel" not in written
    assert f"Wrote schema to {out_path}" in out.getvalue()


def test_export_schema_raises_command_error_when_path_directory_missing(tmp_path):
    """A ``--path`` whose parent directory is missing surfaces a ``CommandError``.

    The ``--path`` failure branch (``write_text`` ``OSError`` -> ``CommandError``)
    is reached only after the real ``config.schema`` is imported, finalized, and
    rendered to SDL.
    """
    missing_dir_path = tmp_path / "nonexistent_dir" / "schema.graphql"
    with pytest.raises(CommandError, match="No such file or directory"):
        call_command(
            "export_schema",
            "config.schema",
            "--path",
            str(missing_dir_path),
        )


def test_export_schema_raises_command_error_when_path_flag_is_empty_string():
    """An explicit empty ``--path ""`` is rejected against the configured schema."""
    with pytest.raises(CommandError, match="--path requires a non-empty value"):
        call_command("export_schema", "config.schema", "--path", "")


def test_export_schema_raises_command_error_when_path_contains_embedded_null():
    """A path rejected by ``pathlib`` is reported as a normal command failure."""
    with pytest.raises(CommandError, match="embedded null byte"):
        call_command("export_schema", "config.schema", "--path", "schema\x00.graphql")
