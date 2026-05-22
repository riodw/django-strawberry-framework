"""Tests for django_strawberry_framework.management.commands.export_schema."""

# TODO spec-018 Slice 2: author the seven tests below per Test plan of
# `docs/spec-018-export_schema-0_0_7.md`. Replace this comment block with the
# real test functions. Rules:
#  - Every test invokes the command via `django.core.management.call_command(...)`,
#    NEVER `Command().handle(...)` directly (Decision 8).
#  - One pytest item per test, NO `pytest.mark.parametrize` fan-out.
#  - Package-internal selectors use the explicit `:symbol` form
#    (`test_module:schema`), except test (g) which exercises the
#    `default_symbol_name="schema"` fallback (Decision 3, rev2 M2).
#  - Every test that synthesizes `test_module` does so via
#    `monkeypatch.setitem(sys.modules, "test_module", module)` so the entry
#    is cleared at teardown — the seven tests must be order-independent
#    (rev3 L4 cleanup contract).
#
# ─── Imports ────────────────────────────────────────────────────────────────────
#
#     import sys
#     import types
#     from io import StringIO
#
#     import pytest
#     import strawberry
#     from django.core.management import CommandError, call_command
#
# ─── Shared fixture pattern (use inline per test, not a session fixture) ────────
#
#     def _make_test_module(monkeypatch, **attrs):
#         module = types.ModuleType("test_module")
#         for k, v in attrs.items():
#             setattr(module, k, v)
#         monkeypatch.setitem(sys.modules, "test_module", module)
#         return module
#
#     def _make_schema():
#         @strawberry.type
#         class Query:
#             hello: str = "world"
#         return strawberry.Schema(query=Query)
#
# ─── (a) happy stdout ───────────────────────────────────────────────────────────
#
#     def test_export_schema_writes_sdl_to_stdout_by_default(monkeypatch):
#         _make_test_module(monkeypatch, schema=_make_schema())
#         out = StringIO()
#         call_command("export_schema", "test_module:schema", stdout=out)
#         assert "type Query" in out.getvalue()
#
# ─── (b) happy --path ───────────────────────────────────────────────────────────
#
#     def test_export_schema_writes_sdl_to_path_when_path_set(monkeypatch, tmp_path):
#         _make_test_module(monkeypatch, schema=_make_schema())
#         out_path = tmp_path / "schema.graphql"
#         call_command("export_schema", "test_module:schema", "--path", str(out_path))
#         assert out_path.exists()
#         assert "type Query" in out_path.read_text(encoding="utf-8")
#
# ─── (c) CommandError — ImportError branch (Decision 5 failure mode 1, half 1) ──
#
#     def test_export_schema_raises_command_error_for_unimportable_module():
#         with pytest.raises(CommandError, match="No module named"):
#             call_command("export_schema", "does.not.exist:schema")
#
# ─── (d) CommandError — AttributeError branch (Decision 5 failure mode 1, half 2)
#
#     def test_export_schema_raises_command_error_for_missing_attribute_on_module(monkeypatch):
#         _make_test_module(monkeypatch)  # no `schema`, no `does_not_exist`
#         with pytest.raises(CommandError, match="does_not_exist"):
#             call_command("export_schema", "test_module:does_not_exist")
#
# ─── (e) CommandError — non-Schema resolved symbol (Decision 5 failure mode 2) ──
#
#     def test_export_schema_raises_command_error_for_non_schema_symbol(monkeypatch):
#         _make_test_module(monkeypatch, not_a_schema=1)
#         with pytest.raises(CommandError, match=r"must be an instance of strawberry\.Schema"):
#             call_command("export_schema", "test_module:not_a_schema")
#
# ─── (f) CommandError — missing positional argument (Decision 5 failure mode 3) ─
#  Note (rev4 L3): the conversion is NOT a SystemExit-wrap. Django's
#  `CommandParser.error()` (subclass of `argparse.ArgumentParser`) raises
#  `CommandError` directly when `called_from_command_line=False`, which is
#  the default when `call_command(...)` constructs the parser. See
#  `.venv/lib/python3.10/site-packages/django/core/management/base.py:49-78`.
#
#     def test_export_schema_raises_command_error_for_missing_positional_argument():
#         with pytest.raises(CommandError):
#             call_command("export_schema")
#
# ─── (g) default-symbol-name="schema" fallback (Decision 3) ─────────────────────
#  The ONE test that uses the implicit (no `:symbol`) form. All other tests
#  above use explicit `:symbol` selectors per rev2 M2.
#
#     def test_export_schema_falls_back_to_default_symbol_name_schema(monkeypatch):
#         _make_test_module(monkeypatch, schema=_make_schema())
#         out = StringIO()
#         call_command("export_schema", "test_module", stdout=out)  # no `:schema`
#         assert "type Query" in out.getvalue()
#
# ─── Negative-shape test (none in 0.0.7) — rev4 L1 ──────────────────────────────
#  No `test_export_schema_command_does_not_define_forbidden_attributes` ships.
#  The Command class has no forbidden-key list to enforce; future cards that
#  introduce "do not ship X" enforcement add the negative test then.
