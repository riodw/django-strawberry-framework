# DRY review: `django_strawberry_framework/management/commands/export_schema.py`

Status: verified

## System trace

`django_strawberry_framework/management/commands/export_schema.py` is the management command module responsible for generating and exporting the GraphQL Schema Definition Language (SDL) for a Strawberry schema symbol ([spec-022][spec-022]). It provides the framework's CLI entry point for client code generators, CI schema-diffing pipelines, and developer tooling.

The module owns the following core responsibilities:

1. **Django Command Class Registration & CLI Arguments ([`Command`][commands-export-schema], [`Command.add_arguments`][commands-export-schema]):**
   - Declares [`Command`][commands-export-schema] subclassing `django.core.management.base.BaseCommand` with `help = "Export the GraphQL schema"`.
   - In [`Command.add_arguments`][commands-export-schema], registers the positional `schema` argument (`type=str, help="The schema location"`) without `nargs`, returning a scalar dotted path string directly in `options["schema"]`.
   - Registers the optional `--path` argument (`type=str, help="Write UTF-8 SDL to this file, overwriting it without prompting"`) without `nargs`, ensuring a bare `--path` without a following value is rejected early at the `argparse` layer before execution.

2. **Schema Resolution & Type Verification ([`Command.handle`][commands-export-schema]):**
   - Resolves the schema selector string via [`import_module_symbol_or_command_error`][commands-imports] with `default_symbol_name="schema"`. This supports both bare module paths (`"config.schema"`) and explicit symbol selectors (`"config.module:my_schema"`).
   - Validates that the resolved symbol is an instance of `strawberry.Schema` via `isinstance(schema_symbol, Schema)`, raising `django.core.management.base.CommandError("The `schema` must be an instance of strawberry.Schema")` when given any non-Schema symbol.

3. **SDL Rendering & Byte-Exact Output Routing ([`Command.handle`][commands-export-schema]):**
   - Renders the SDL string directly from the schema instance via `strawberry.printer.print_schema(schema_symbol)`.
   - Routes across three distinct execution branches based on `path = options.get("path")`:
     - **Default stdout branch (`path is None`):** Writes the generated SDL to `self.stdout.write(schema_output, ending="")`. Suppressing Django's default `ending="\n"` ensures that stdout emission is byte-identical to `print_schema()` output and `--path` file bytes, preventing spurious single-byte differences in CI schema comparisons.
     - **Empty/whitespace `--path` rejection:** Checks `if not isinstance(path, str) or not path.strip(): raise CommandError("--path requires a non-empty value")`, rejecting blank strings or whitespace-only paths.
     - **File output branch:** Writes UTF-8 SDL to the destination file using `pathlib.Path(path).write_text(schema_output, encoding="utf-8", newline="")`. Passing `newline=""` disables host platform newline translation (e.g. CRLF on Windows), guaranteeing consistent LF line endings across all platforms. Catches `(OSError, ValueError)` and re-raises them as `CommandError(str(e)) from e` while preserving root causes. On success, reports `self.stdout.write(self.style.SUCCESS(f"Wrote schema to {path}"))`.

Connected behavior examined:
- [`django_strawberry_framework/management/commands/_imports.py`][commands-imports]: Provides shared import validation and error translation ([`import_module_symbol_or_command_error`][commands-imports]) for `export_schema` and `inspect_django_type`.
- [`django_strawberry_framework/management/commands/inspect_django_type.py`][commands-inspect-django-type]: Sibling command also utilizing [`import_module_symbol_or_command_error`][commands-imports] for schema loading and type finalization.
- [`django_strawberry_framework/management/commands/__init__.py`][management-commands-init] and [`django_strawberry_framework/management/__init__.py`][management-init]: Subpackage packaging markers required for Django management command discovery.
- [`django_strawberry_framework/conf.py`][conf]: Configuration management singleton; deliberately not used for fallback schema resolution to keep CLI invocation explicit and predictable.
- [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: Framework root exports; deliberately excludes `Command` from public API exports since commands are discovered via `INSTALLED_APPS` and invoked via `manage.py` or `call_command`.
- [`tests/management/test_export_schema.py`][test-management-export-schema]: Package-tier unit test suite covering unimportable modules, missing attributes, non-Schema symbols, argument validation, selector errors, byte equivalence, newline translation disablement, and whitespace `--path` rejection.
- [`examples/fakeshop/tests/test_export_schema.py`][example-test-export-schema]: Live-tier integration test suite validating end-to-end execution against fakeshop's real `config.schema`, file overwrite behavior, missing parent directories, and embedded null bytes.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/management/commands/export_schema.py --include-constants`):
- Target file contains 63 lines, 1 class definition ([`Command`][commands-export-schema]), 2 method definitions ([`Command.add_arguments`][commands-export-schema], [`Command.handle`][commands-export-schema]), 0 constant definitions, and 0 mutable module state.
- Verified exact single-ownership of schema export SDL generation and command output routing.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `export_schema.py` is the single centralized CLI command for exporting GraphQL SDL from a Strawberry schema.
   - Declarative feature subpackages (`filters`, `forms`, `mutations`, `orders`, `types`, `rest_framework`) construct GraphQL types, resolvers, and mutations. They do not handle CLI invocation, string selector parsing, or file emission.
   - Dynamic selector resolution and `CommandError` exception mapping are delegated to [`django_strawberry_framework/management/commands/_imports.py`][commands-imports], which is shared with [`inspect_django_type.py`][commands-inspect-django-type].
   - There is zero duplicate argument parsing, selector resolution, or error translation across commands or flavors.
2. **Sync and async twins:**
   Zero duplication. Django management commands execute synchronously via `manage.py` or `django.core.management.call_command`. Schema printing via `strawberry.printer.print_schema` and filesystem operations via `pathlib.Path.write_text` are synchronous operations. No async variants or parallel execution paths exist.
3. **Derived rather than repeated knowledge:**
   - Schema printing is derived directly from Strawberry's official printer `strawberry.printer.print_schema(schema_symbol)`.
   - Symbol importing and selector parsing derive from `strawberry.utils.importer.import_module_symbol` via [`import_module_symbol_or_command_error`][commands-imports].
   - Argument parsing derives from Django's `CommandParser` (argparse).
   - Byte-exact output is derived by suppressing Django's default ending (`ending=""`) on stdout and disabling platform newline conversion (`newline=""`) on file writes, ensuring byte-for-byte consistency across output destinations without duplicating formatting logic.
4. **Inverse and round-trip pairs:**
   Schema export is a unidirectional projection from an in-memory `strawberry.Schema` object to an SDL string or file on disk. The framework is code-first (Python models/types to GraphQL schema), so no reverse SDL-to-Python import command exists.
   The output parity between `self.stdout` and `--path` file output is verified to be byte-identical to `print_schema()` return value.
5. **Contracts restated in another medium:**
   The schema export CLI contracts are codified across:
   - Code: [`django_strawberry_framework/management/commands/export_schema.py`][commands-export-schema];
   - Specifications: [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] (Slice 1-3, Decisions 1-10) and [`docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md`][spec-022-rationale];
   - Tests: [`tests/management/test_export_schema.py`][test-management-export-schema] (unit tests for argument errors, type errors, byte equivalence, newline translation) and [`examples/fakeshop/tests/test_export_schema.py`][example-test-export-schema] (live fakeshop tests for real schema exports and filesystem error modes);
   - Standing documentation: [`docs/GLOSSARY.md`][glossary] (`Schema export management command`), [`docs/TREE.md`][tree], [`docs/review/rev-management__commands__export_schema.md`][review-commands-export-schema].

### The single-edit-site test

- **Posited change 1 (Customizing SDL generation options or printer formatting, e.g. adding schema directives or sorting types):**
  - Update the `print_schema(schema_symbol)` invocation in [`Command.handle`][commands-export-schema].
  - Both stdout and `--path` file output paths automatically inherit the updated SDL formatting.
  - *Sites that must move in `django_strawberry_framework/management/commands/export_schema.py`:* Exactly 1 site.
  - *Site count:* 1.
- **Posited change 2 (Adjusting output encoding or file write parameters, e.g. supporting alternative encodings or atomic writes):**
  - Update `pathlib.Path(path).write_text(...)` in [`Command.handle`][commands-export-schema].
  - *Sites that must move in `django_strawberry_framework/management/commands/export_schema.py`:* Exactly 1 site.
  - *Site count:* 1.
- **Posited change 3 (Modifying schema selector syntax validation or import error handling):**
  - Update [`django_strawberry_framework/management/commands/_imports.py`][commands-imports].
  - *Sites that must move in `django_strawberry_framework/management/commands/export_schema.py`:* Exactly 0 sites.
  - *Site count in `export_schema.py`:* 0.

### Rejected candidates

1. **Inlining selector parsing and `CommandError` exception handling in `export_schema.py`:**
   - Disproved. The import validation and `CommandError` translation logic is factored into `_imports.py` and shared with `inspect_django_type.py`. Inlining would duplicate path parsing and exception handling across commands.
2. **Adding settings-backed schema defaults or `--watch` / `--indent` / `--json` options:**
   - Disproved per [spec-022][spec-022] Decision 6. Settings-backed defaults add implicit state and unnecessary complexity; SDL formatting belongs in downstream tools (`prettier`, `graphql-cli`); JSON introspection is out of scope for a clean SDL exporter.
3. **Omitting `ending=""` on stdout or `newline=""` on file writes:**
   - Disproved per [spec-022][spec-022] Decision 4 and review fix. Omitting `ending=""` adds a trailing newline to stdout that diverges from `--path` file writes; omitting `newline=""` allows platform newline conversion on Windows (converting LF to CRLF), breaking cross-platform byte-exact diffs.

## Opportunities

None — `django_strawberry_framework/management/commands/export_schema.py` is a clean, 63-line, single-purpose management command. It correctly delegates import handling to `_imports.py` and SDL printing to Strawberry's `print_schema`. It maintains byte-exact parity across output destinations, handles all failure modes via `CommandError`, and contains zero duplicate logic, zero unowned state, and zero excess surface.

## Judgment

Zero-edit review. `django_strawberry_framework/management/commands/export_schema.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across target-owned changes and 0 for delegated import changes.

## Implementation (Worker 1)

No tracked code changes needed. Target file is clean, robust, and fully consolidated at root owners. Verified completeness via `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/management/commands/export_schema.py --review docs/dry/dry-file-management__commands__export_schema.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification conducted by Worker 2 for `django_strawberry_framework/management/commands/export_schema.py`.

### Independent behavioral trace and boundary challenge

1. **Command Class Structure & Argument Specification:**
   - Re-traced [`Command`][commands-export-schema] subclassing `django.core.management.base.BaseCommand` with `help = "Export the GraphQL schema"`.
   - In [`Command.add_arguments`][commands-export-schema], positional `schema` argument and optional `--path` argument are registered as scalar strings (`type=str`) without `nargs`.
   - Confirmed that omitting the positional argument or passing bare `--path` without a value is caught and rejected by `argparse` prior to `handle` execution.

2. **Schema Resolution & Type Enforcement:**
   - In [`Command.handle`][commands-export-schema], schema resolution delegates to [`import_module_symbol_or_command_error`][commands-imports] with `default_symbol_name="schema"`, validating absolute module paths and catching `(ImportError, AttributeError)` to raise `CommandError` with `__cause__` chained.
   - Non-`strawberry.Schema` instances are rejected via `isinstance(schema_symbol, Schema)` check, raising `CommandError("The `schema` must be an instance of strawberry.Schema")`.

3. **SDL Rendering & Byte-Exact Parity:**
   - SDL rendering delegates directly to `strawberry.printer.print_schema(schema_symbol)`.
   - Default stdout branch (`path is None`) writes via `self.stdout.write(schema_output, ending="")`. Suppressing Django's default newline ending guarantees that stdout output is byte-identical to `print_schema()` return bytes.
   - Blank / whitespace-only `--path` values are rejected early with `CommandError("--path requires a non-empty value")`.
   - File output branch writes UTF-8 text via `pathlib.Path(path).write_text(schema_output, encoding="utf-8", newline="")`. The explicit `newline=""` parameter disables host-platform newline translation (e.g., CRLF conversion on Windows), ensuring identical LF byte sequences across platforms and matching stdout redirects.
   - Filesystem and path errors are caught via `(OSError, ValueError)` and converted to `CommandError(str(e)) from e`, preserving underlying causes.
   - Success output writes styled message `self.stdout.write(self.style.SUCCESS(f"Wrote schema to {path}"))`.

4. **Mandatory 5-Axis Duplication Matrix & Single-Edit-Site Verification:**
   - Re-evaluated all 5 axes: cross-flavor policy mirroring, sync/async twins, derived knowledge, inverse pairs, and contract representations across mediums. All axes are fully discharged with valid justifications.
   - Re-verified single-edit-site counts across all 3 posited changes (counts: 1, 1, 0).

5. **Verification Tooling & Test Suite Run:**
   - Executed `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/management/commands/export_schema.py --review docs/dry/dry-file-management__commands__export_schema.md --include-constants` — coverage verified (3 target definitions, 0 required topics).
   - Executed `uv run pytest tests/management/test_export_schema.py examples/fakeshop/tests/test_export_schema.py --no-cov` — all 17 tests passing across package unit tests and live fakeshop integration tests.
   - Executed `uv run pytest tests/management/ --no-cov` — all 59 tests in the management test suite passing.

Conclusion: Verified. Worker 1's DRY review is accurate, comprehensive, and complete. Zero code edits required.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-022]: ../SPECS/spec-022-export_schema-0_0_7.md
[spec-022-rationale]: ../SPECS/appx/spec-022-export_schema-0_0_7-rationale.md
[spec-029]: ../SPECS/spec-029-consumer_dx_cleanup-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[commands-export-schema]: ../../django_strawberry_framework/management/commands/export_schema.py
[commands-imports]: ../../django_strawberry_framework/management/commands/_imports.py
[commands-inspect-django-type]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[conf]: ../../django_strawberry_framework/conf.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[management-commands-init]: ../../django_strawberry_framework/management/commands/__init__.py
[management-init]: ../../django_strawberry_framework/management/__init__.py

<!-- tests/ -->
[test-management-export-schema]: ../../tests/management/test_export_schema.py
[test-management-imports]: ../../tests/management/test_imports.py
[test-management-init]: ../../tests/management/__init__.py
[test-management-inspect-django-type]: ../../tests/management/test_inspect_django_type.py

<!-- examples/ -->
[example-test-export-schema]: ../../examples/fakeshop/tests/test_export_schema.py
[example-test-inspect-django-type]: ../../examples/fakeshop/tests/test_inspect_django_type.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[review-commands-export-schema]: ../review/rev-management__commands__export_schema.md
