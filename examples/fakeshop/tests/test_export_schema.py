"""Project-level export_schema command tests for the fakeshop schema."""

from io import StringIO

from django.core.management import call_command


def test_export_schema_writes_fakeshop_sdl_to_stdout_by_default():
    out = StringIO()
    call_command("export_schema", "config.schema:schema", stdout=out)
    assert "type BranchType" in out.getvalue()


def test_export_schema_writes_fakeshop_sdl_to_path_when_path_set(tmp_path):
    out = StringIO()
    out_path = tmp_path / "schema.graphql"

    call_command(
        "export_schema",
        "config.schema",
        "--path",
        str(out_path),
        stdout=out,
    )

    assert out_path.exists()
    assert "type BranchType" in out_path.read_text(encoding="utf-8")
    assert f"Wrote schema to {out_path}" in out.getvalue()
