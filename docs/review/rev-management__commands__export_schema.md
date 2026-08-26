# Review: `django_strawberry_framework/management/commands/export_schema.py`

Status: verified

## Understanding

`django_strawberry_framework/management/commands/export_schema.py` implements the `export_schema` Django management command (`manage.py export_schema`). It resolves a Strawberry schema symbol from a dotted module selector path and exports its GraphQL SDL to standard output or a destination file.

It owns:
1. **Command argument definition (`add_arguments`)**:
   - Positional `schema` argument (`str`, no `nargs`) specifying the dotted module selector for the schema object (e.g. `config.schema` or `config.module:schema_name`).
   - Optional `--path` option (`str`, no `nargs`) specifying a destination file path where UTF-8 SDL will be written destructively without prompting.
2. **Schema symbol resolution & type validation (`handle`)**:
   - Resolves `options["schema"]` via `_imports.import_module_symbol_or_command_error(..., default_symbol_name="schema")`.
   - Validates that the resolved object is an instance of `strawberry.Schema`. If not (e.g., resolving a class, module, or unrelated object), raises `CommandError("The `schema` must be an instance of strawberry.Schema")`.
3. **SDL emission & byte-exact output routing (`handle`)**:
   - Renders GraphQL SDL using `strawberry.printer.print_schema(schema_symbol)`.
   - **Stdout branch (`path is None`)**: Writes `schema_output` directly to `self.stdout` with `ending=""` to suppress Django's default trailing newline, guaranteeing byte-exact equivalence with `print_schema` output and file writes.
   - **Validation branch (`not isinstance(path, str) or not path.strip()`)**: Rejects empty or whitespace-only `--path` values with `CommandError("--path requires a non-empty value")`.
   - **File write branch**: Writes UTF-8 encoded SDL via `pathlib.Path(path).write_text(schema_output, encoding="utf-8", newline="")`, setting `newline=""` to prevent platform-specific newline translation. Catches filesystem/path errors `(OSError, ValueError)` and translates them to `CommandError(str(e)) from e`. Upon success, prints a confirmation message via `self.stdout.write(self.style.SUCCESS(f"Wrote schema to {path}"))`.

Callers & consumers:
- Operators executing `python manage.py export_schema <schema> [--path <path>]`.
- CI / build automation calling `django.core.management.call_command("export_schema", ...)`.

## Verification

1. Examined test suites:
   - `tests/management/test_export_schema.py` (12 tests): covers unimportable module resolution, missing module attribute, non-schema symbol rejection, missing required positional argument, bare `--path` flag rejection by argparse, malformed selector rejection (empty or relative paths), `--path` help string documentation verification, byte-exact equality across stdout / `--path` / `print_schema`, newline translation suppression (`newline=""`), and whitespace-only `--path` rejection.
   - `examples/fakeshop/tests/test_export_schema.py` (5 tests): live integration tests against real fakeshop `config.schema` verifying default stdout emission with expected schema types, destructive file overwriting with UTF-8 SDL, `CommandError` on missing parent directories, empty-string `--path` rejection, and embedded null byte error translation.
2. Focused test executions:
   - `uv run pytest tests/management/test_export_schema.py examples/fakeshop/tests/test_export_schema.py --no-cov` (17 passed).
   - `uv run pytest tests/management/test_export_schema.py examples/fakeshop/tests/test_export_schema.py -o addopts="" --cov=django_strawberry_framework.management.commands.export_schema --cov-report=term-missing` (17 passed, 100% statement coverage, 26/26 statements).
   - `uv run pytest tests/management/ --no-cov` (59 passed).
3. Scratch experiments:
   - `docs/review/temp-tests/management/test_export_schema_scratch.py` (3 passed): verified behavior when `--path` points to an existing directory (raises `CommandError`), when `schema` resolves to the `strawberry.Schema` class itself instead of an instance (raises `CommandError`), and when `schema` resolves to a `DjangoSchema` subclass instance (exports successfully).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/management/commands/export_schema.py` is a robust, well-structured, and completely tested management command. It enforces strict argument validation, byte-exact SDL output consistency across stdout and file targets, and clean operator error translation.

## Implementation (Worker 1)

- **Changed files:** None — zero-edit cycle.
- **Scoped diff against baseline (`12779c99`):** empty (`git diff 12779c99 -- django_strawberry_framework/management/commands/export_schema.py`).
- **Justification:** The command is completely covered at 100% statement coverage across package and live tiers, correctly adheres to the byte-exact SDL output contract, and handles all error branches cleanly via `CommandError`.
- **Permanent tests and pinned behavior:**
  - `tests/management/test_export_schema.py` (12 tests) pins CLI argument parsing, selector validation, non-schema error handling, stdout trailing newline suppression, and platform newline suppression during file writes.
  - `examples/fakeshop/tests/test_export_schema.py` (5 tests) pins live integration with the real application schema, destructive overwrites, missing directory errors, and embedded null byte path rejections.
- **Scratch verification:** `docs/review/temp-tests/management/test_export_schema_scratch.py` (3 passed); `tests/management/test_export_schema.py` and `examples/fakeshop/tests/test_export_schema.py` (17 passed).
- **Formatter and linter results:** Zero-edit cycle (no tracked changes).
- **Evidence for rejected findings:** None.
- **Changelog entry:** No.

## Independent verification (Worker 2)

- **Scoped diff confirmation**: Confirmed target production file `django_strawberry_framework/management/commands/export_schema.py` has zero diff against baseline `HEAD` (`12779c99`).
- **Behavioral re-trace**:
  1. Traced `add_arguments` command parameter definitions (`schema` positional and `--path` optional option).
  2. Verified schema symbol resolution delegation to `import_module_symbol_or_command_error` with `default_symbol_name="schema"`.
  3. Verified schema type guard requiring `isinstance(schema_symbol, strawberry.Schema)` and raising `CommandError` on non-instances or non-schema symbols.
  4. Verified byte-exact SDL rendering and destination routing:
     - Stdout branch suppresses Django's `OutputWrapper` trailing newline (`ending=""`) to ensure exact match with `printer.print_schema`.
     - File write branch enforces non-empty `--path` strings, uses UTF-8 encoding with disabled newline translation (`newline=""`), and maps all `(OSError, ValueError)` filesystem exceptions to `CommandError`.
- **Test execution**:
  - Executed package and live suites: `uv run pytest tests/management/test_export_schema.py examples/fakeshop/tests/test_export_schema.py --no-cov` (17 passed).
  - Executed scratch suite: `uv run pytest docs/review/temp-tests/management/test_export_schema_scratch.py --no-cov` (3 passed: existing directory path error translation, schema class vs instance rejection, `DjangoSchema` subclass instance compatibility).
- **Outcome**: Verified. All findings disposed of cleanly; no further production or test changes needed.
