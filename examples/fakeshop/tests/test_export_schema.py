"""Fakeshop project command tests for export_schema against the configured schema."""

from io import StringIO

import pytest
from django.core.management import CommandError, call_command


def test_export_schema_writes_fakeshop_sdl_to_stdout_by_default():
    out = StringIO()
    call_command("export_schema", "config.schema:schema", stdout=out)
    assert "type BranchType" in out.getvalue()


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
    rendered to SDL, so this carries stronger contract pressure than the prior
    synthetic ``test_module:schema`` package test.
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
