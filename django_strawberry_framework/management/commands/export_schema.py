"""manage.py export_schema — print or write the GraphQL SDL for a Strawberry schema symbol."""

# TODO spec-018 Slice 1: implement `Command(BaseCommand)` per Decision 2 of
# `docs/spec-018-export_schema-0_0_7.md`. Pseudo code below; replace this whole
# comment block with the real class. Every line of the pseudo code is gate-pinned
# (ruff `D100` / `D101` / `D102` / `ANN001` / `ANN201`) — do NOT drop docstrings
# or annotations and do NOT add `# noqa` (per AGENTS.md line 4).
#
# ─── Imports (Decision 2 Method signatures, lines 305-309 of the spec) ──────────
#
#     import pathlib
#
#     from django.core.management.base import BaseCommand, CommandError, CommandParser
#     from strawberry import Schema
#     from strawberry.printer import print_schema
#     from strawberry.utils.importer import import_module_symbol
#
# ─── Class shape (Decision 2) ───────────────────────────────────────────────────
#
#     class Command(BaseCommand):
#         """Export the GraphQL SDL for a strawberry.Schema symbol."""   # D101
#
#         help = "Export the GraphQL schema"                              # Title Case
#
#         def add_arguments(self, parser: CommandParser) -> None:         # ANN001 / ANN201
#             """Register the positional schema argument and the optional --path flag."""  # D102
#             parser.add_argument("schema", nargs=1, type=str,
#                                 help="The schema location")
#             parser.add_argument("--path", nargs="?", type=str,
#                                 help="Optional path to export")
#
#         def handle(self, *args: object, **options: object) -> None:    # ANN201
#             """Resolve the dotted-path schema symbol, print SDL to stdout or write it to --path."""  # D102
#             # Decision 3 — symbol resolution via Strawberry's importer.
#             try:
#                 schema_symbol = import_module_symbol(
#                     options["schema"][0],
#                     default_symbol_name="schema",
#                 )
#             except (ImportError, AttributeError) as e:                  # Decision 5 failure mode 1
#                 raise CommandError(str(e)) from e
#
#             # Decision 5 failure mode 2 — isinstance check (exact upstream wording).
#             if not isinstance(schema_symbol, Schema):
#                 raise CommandError("The `schema` must be an instance of strawberry.Schema")
#
#             # Decision 4 — SDL output via Strawberry's printer.
#             schema_output = print_schema(schema_symbol)
#             path = options.get("path")
#             if path:
#                 pathlib.Path(path).write_text(schema_output, encoding="utf-8")
#             else:
#                 self.stdout.write(schema_output)
#
# ─── Deliberately NOT declared (Decision 6) ─────────────────────────────────────
#  - `--watch` / `--indent` / `--json` flags
#  - settings-backed defaults (forbidden by AGENTS.md line 20)
#  - `dump_schema` / `print_schema` aliases
#  - `requires_system_checks` / `requires_migrations_checks` / `stealth_options` overrides
#
# ─── Failure mode 3 (Decision 5) is raised pre-handle by Django's CommandParser.error()
# when `called_from_command_line=False`; no code is needed in handle() for it.
