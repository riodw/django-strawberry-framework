# Review: `django_strawberry_framework/management/commands/`

Status: verified

## Understanding

The `django_strawberry_framework/management/commands/` subpackage owns the framework's Django CLI management commands (`manage.py export_schema`, `manage.py inspect_django_type`) and shared CLI import resolution mechanics (`_imports.py`).

1. **Subpackage architecture and layout**:
   - `__init__.py`: Package docstring identifying exported management commands.
   - `_imports.py`: Shared import and selector resolution engine. Translates `ImportError` and `AttributeError` from symbol resolution into `django.core.management.base.CommandError(str(e)) from e` while preserving `__cause__` and leaving unexpected application exceptions (`TypeError`, `ValueError`, syntax errors) unmasked. Pre-validates absolute module paths to catch empty or relative selectors (`.`, `..`, `.config.schema`) before downstream libraries fail with cryptic errors.
   - `export_schema.py` (`manage.py export_schema`): Resolves a Strawberry schema symbol from a dotted module selector path (e.g. `config.schema` or `config.schema:schema`), validates that the target is an instance of `strawberry.Schema`, renders GraphQL SDL via `strawberry.printer.print_schema`, and routes output to stdout (with Django `OutputWrapper` trailing newline suppression via `ending=""`) or to a UTF-8 encoded destination file via `Path.write_text(..., newline="")`.
   - `inspect_django_type.py` (`manage.py inspect_django_type`): Diagnostic tool that inspects a finalized `DjangoTypeDefinition` and prints a 5-column table (`field`, `django field type`, `graphql type`, `nullable`, `converter`). Resolves targets via dotted Python paths or bare names (matching converter-applied SDL type names or Python class names across `registry.iter_definitions()`), pre-loads `--schema` selectors for cold processes to register and finalize all types with active `NameConverter` and `scalar_map` settings, and accurately dispatches row formatting across Relay PK suppression, consumer-authored overrides, auto-synthesized relations (including connection-only shapes), file/image output type converters, choice enums, and MRO ancestor `SCALAR_MAP` rows.

2. **Integration with framework and Django runtime**:
   - Discovered automatically by Django's `management.get_commands()` via standard `management/commands/` conventions.
   - Integrates cleanly with `django_strawberry_framework.registry.registry` and `django_strawberry_framework.types.finalizer.finalize_django_types` (triggered when schemas load).
   - Provides clear diagnostics when types are unfinalized, abstract, or missing from the registry, guiding CLI operators to provide the `--schema` selector.

## Verification

1. **Test suites examined**:
   - `tests/management/test_imports.py` (19 tests): import wrapping, cause preservation, non-import exception pass-through, relative/empty path validation, symbol loading.
   - `tests/management/test_export_schema.py` (12 tests): schema argument parsing, non-schema rejection, byte-exact stdout/file parity, `--path` validation.
   - `tests/management/test_inspect_django_type.py` (28 tests): dotted and bare name resolution, ambiguous name handling with copyable candidates, unfinalized/abstract error paths, relation shapes, custom scalar mapping, Relay PK suppression.
   - `examples/fakeshop/tests/test_export_schema.py` (5 tests): live integration with real fakeshop schema, stdout rendering, destructive file overwrites, missing directory handling.
   - `examples/fakeshop/tests/test_inspect_django_type.py` (12 tests): live integration across example types, cold-path `--schema` loading, consumer override combinations, choice enums, relation rows.
2. **Focused test execution**:
   - `uv run pytest tests/management/ examples/fakeshop/tests/test_export_schema.py examples/fakeshop/tests/test_inspect_django_type.py --no-cov` (76 passed).
3. **Scratch verification**:
   - `docs/review/temp-tests/management/test_imports_scratch.py` (2 passed): selector syntax edge cases.
   - `docs/review/temp-tests/management/test_export_schema_scratch.py` (3 passed): directory targets, schema class vs instance, DjangoSchema subclasses.
   - `docs/review/temp-tests/management/test_inspect_django_type_scratch.py` (5 passed): helper utilities and filesystem path fields.
   - `docs/review/temp-tests/management/test_commands_folder_scratch.py` (4 passed): subpackage command hierarchy, cross-command error consistency on unimportable modules, relative paths, and empty selectors.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The `django_strawberry_framework/management/commands/` subpackage is cohesive, robust, and completely verified. Shared import resolution in `_imports.py` ensures uniform CLI error behavior across commands, `export_schema.py` guarantees byte-exact SDL output contracts, and `inspect_django_type.py` provides high-fidelity schema diagnostics across all field origins.

## Implementation (Worker 1)

- **Changed files:** None — zero-edit cycle.
- **Scoped diff against baseline (`12779c99`):** empty (`git diff 12779c99 -- django_strawberry_framework/management/commands/`).
- **Justification:** The subpackage architecture is modular and consistent. All commands and helpers are covered at 100% statement coverage across unit and live tiers, handle errors without masking underlying application bugs, and provide actionable CLI feedback.
- **Permanent tests and pinned behavior:**
  - `tests/management/` (59 tests across `test_imports.py`, `test_export_schema.py`, `test_inspect_django_type.py`) pins error translation, validation guards, symbol resolution, SDL formatting, table row generation, and CLI argument parsing.
  - `examples/fakeshop/tests/` (17 tests across `test_export_schema.py` and `test_inspect_django_type.py`) pins live application schema integration, file export behaviors, and real DjangoType inspection.
- **Scratch verification:** `docs/review/temp-tests/management/` (14 passed across 4 scratch modules).
- **Formatter and linter results:** Zero-edit cycle (no tracked changes).
- **Evidence for rejected findings:** None.
- **Changelog entry:** No.

## Independent verification (Worker 2)

1. **Subpackage architecture & behavior verification**:
   - Re-traced all subpackage modules (`__init__.py`, `_imports.py`, `export_schema.py`, `inspect_django_type.py`) against runtime and caller expectations.
   - Verified that `_imports.py` centralizes import and selector resolution for CLI commands, systematically transforming `ImportError` and `AttributeError` into `CommandError(str(e)) from e` while leaving unexpected application exceptions (`TypeError`, `ValueError`, `SyntaxError`) unmasked. Pre-validations guard against empty or relative selectors.
   - Verified `export_schema.py` (`manage.py export_schema`) resolves Strawberry schema symbols, verifies instance types, prints byte-exact GraphQL SDL with Django's `OutputWrapper` trailing newline suppressed (`ending=""`), and handles UTF-8 file emission with overwrite-without-prompt semantics.
   - Verified `inspect_django_type.py` (`manage.py inspect_django_type`) walks `DjangoTypeDefinition`s and renders precise 5-column diagnostic tables across Relay PK suppression, consumer-authored overrides, auto-synthesized relations (including connection-only shapes), file/image output converters, choice enums, and MRO ancestor `SCALAR_MAP` rows.
2. **Zero-diff confirmation**:
   - Evaluated `git diff 12779c99 -- django_strawberry_framework/management/commands/` and confirmed zero modifications against baseline HEAD.
3. **Focused test execution**:
   - Ran `uv run pytest tests/management/ examples/fakeshop/tests/test_export_schema.py examples/fakeshop/tests/test_inspect_django_type.py docs/review/temp-tests/management/ --no-cov` (90 passed across unit, live example, and scratch test suites).
4. **Findings disposition**:
   - No open findings, defects, or gaps identified. Zero-edit subpackage pass verified.
