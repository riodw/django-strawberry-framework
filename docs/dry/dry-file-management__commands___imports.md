# DRY review: `django_strawberry_framework/management/commands/_imports.py`

Status: verified

## System trace

`django_strawberry_framework/management/commands/_imports.py` is the centralized CLI import and path resolution helper module for the framework's Django management commands ([spec-022][spec-022], [spec-029][spec-029]). It establishes the command-line boundary where module-loading and symbol-resolution errors are caught, validated, and translated into clean, actionable Django `CommandError` instances while preserving root causes as `__cause__`.

The module owns the following core responsibilities:

1. **CLI Exception Boundary & Root-Cause Preservation ([`import_or_command_error`][commands-imports]):**
   - Executes an arbitrary zero-argument dynamic import callable (`Callable[[], T] -> T`).
   - Catches `(ImportError, AttributeError)` failures emitted during dynamic module importation or symbol lookup, re-raising them as `django.core.management.base.CommandError(str(e))`.
   - Chains the original exception using `raise CommandError(...) from e` (`__cause__` preservation), so developers and debuggers retain access to the full underlying traceback while Django CLI runners display a clean, single-line error message without leaking traceback noise to end users.
   - Strictly limits the catch boundary to `(ImportError, AttributeError)`. Arbitrary runtime exceptions, syntax errors inside user module bodies, or consumer-raised exceptions (e.g., `ValueError`, `TypeError`, `KeyError`, `ConfigurationError`) propagate unmasked, preventing the CLI wrapper from disguising application-level bugs as import path failures.

2. **Pre-Import Module Path Syntax Validation ([`_validate_absolute_module_path`][commands-imports]):**
   - Statically validates module path strings before passing them to Python's `importlib` machinery or Strawberry's importer.
   - Rejects empty module paths (`""` or `":symbol"`) with a clear error: `"<value>" is not a valid <label>: the module path is empty.`
   - Rejects relative module paths (`".relative"`, `".relative:symbol"`, `".a.b"`) with: `"<value>" is not a valid <label>: relative module paths are not supported.`
   - This pre-validation intercepts syntax mistakes that would otherwise cause `strawberry.utils.importer.import_module_symbol` to raise uninformative `ValueError` ("Empty module name") or `TypeError` ("relative import without a package"), which are outside the standard `(ImportError, AttributeError)` catch boundary.

3. **Strawberry Selector Resolution ([`import_module_symbol_or_command_error`][commands-imports]):**
   - Resolves Strawberry-style `module[:symbol]` selector strings (e.g. `"my_app.schema:schema"` or `"my_app.schema"`).
   - Extracts the leading module name via `selector.split(":", 1)[0]` and validates it via [`_validate_absolute_module_path`][commands-imports] with `label="schema selector"`.
   - Delegates symbol resolution to upstream `strawberry.utils.importer.import_module_symbol(selector, default_symbol_name=default_symbol_name)` inside [`import_or_command_error`][commands-imports].
   - Consumed by [`django_strawberry_framework/management/commands/export_schema.py`][commands-export-schema] (`export_schema <schema>`) and [`django_strawberry_framework/management/commands/inspect_django_type.py`][commands-inspect-django-type] (`inspect_django_type --schema <schema>`).

4. **Django Dotted Object Path Resolution ([`import_string_or_command_error`][commands-imports]):**
   - Resolves standard Django dotted object paths (e.g. `"my_app.types.BookType"`).
   - Validates that the input contains at least one dot via `dotted_path.rpartition(".")`. Bare names (e.g. `"BookType"`) are immediately rejected with `"<dotted_path>" is not a valid dotted object path: a module path is required.`
   - Validates the extracted module path via [`_validate_absolute_module_path`][commands-imports] with `label="dotted object path"`.
   - Delegates object resolution to Django's canonical `django.utils.module_loading.import_string(dotted_path)` inside [`import_or_command_error`][commands-imports].
   - Consumed by [`django_strawberry_framework/management/commands/inspect_django_type.py`][commands-inspect-django-type] when resolving positional `type` arguments that contain dots.

5. **Type Parameterization (`T`):**
   - Defines invariant `TypeVar("T")` to ensure [`import_or_command_error`][commands-imports] preserves the exact return type of the passed importer callable for full static type safety.

Connected behavior examined:
- [`django_strawberry_framework/management/commands/export_schema.py`][commands-export-schema]: Invokes [`import_module_symbol_or_command_error`][commands-imports] to import Strawberry schemas for SDL output.
- [`django_strawberry_framework/management/commands/inspect_django_type.py`][commands-inspect-django-type]: Invokes [`import_module_symbol_or_command_error`][commands-imports] to load optional schemas for type registration/finalization, and [`import_string_or_command_error`][commands-imports] to resolve dotted `DjangoType` target classes.
- [`django_strawberry_framework/management/commands/__init__.py`][management-commands-init]: Subpackage marker for management commands; deliberately encapsulates `_imports.py` without leaking it into public API.
- [`django_strawberry_framework/management/__init__.py`][management-init]: Parent management subpackage marker.
- [`django_strawberry_framework/utils/imports.py`][utils-imports]: Runtime import helpers (`import_attr_if_importable`, `loaded_attr`, `import_attr`, `require_optional_module`) serving cycle-breaking, best-effort optional dependency loading, and strict internal attribute imports. Serves different contracts from the CLI error-translation boundary.
- [`django_strawberry_framework/conf.py`][conf]: Configuration management singleton; reads settings dicts without CLI string resolution.
- [`tests/management/test_imports.py`][test-management-imports]: Comprehensive test suite exercising all functions, edge cases, error propagation, and cause chaining.
- [`tests/management/test_export_schema.py`][test-management-export-schema] and [`tests/management/test_inspect_django_type.py`][test-management-inspect-django-type]: Command integration test suites verifying CLI error behavior.
- [`examples/fakeshop/tests/test_export_schema.py`][example-test-export-schema], [`examples/fakeshop/tests/test_inspect_django_type.py`][example-test-inspect-django-type], [`examples/fakeshop/apps/products/tests/test_commands.py`][example-products-test-commands], [`examples/fakeshop/apps/kanban/tests/test_commands.py`][example-kanban-test-commands]: Live-tier integration tests exercising management commands via `call_command`.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/management/commands/_imports.py --include-constants`):
- Target file contains 55 lines, 4 function definitions ([`import_or_command_error`][commands-imports], [`_validate_absolute_module_path`][commands-imports], [`import_module_symbol_or_command_error`][commands-imports], [`import_string_or_command_error`][commands-imports]), and 1 TypeVar definition (`T`).
- Verified zero duplicate definitions, zero unowned state, and exact single-ownership of management CLI import translation.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `_imports.py` is the single centralized CLI import resolution module for all management commands in the framework.
   - Declarative feature subpackages (`filters`, `forms`, `mutations`, `orders`, `types`, `rest_framework`) resolve types, serializers, models, and filtersets through Python class declarations, `Meta` attributes, or the central type registry (`django_strawberry_framework.registry.registry`). They do not accept or parse CLI selector strings.
   - Runtime optional dependency loading and internal cycle-breaking are owned by [`django_strawberry_framework/utils/imports.py`][utils-imports] (`require_optional_module`, `import_attr_if_importable`, `loaded_attr`, `import_attr`). Those helpers return values or `None`, or raise `ImportError` with install hints, which is appropriate for application runtime code.
   - In contrast, `management/commands/_imports.py` specifically owns translating selector/dotted-path syntax and `(ImportError, AttributeError)` into `django.core.management.base.CommandError`. Both management commands ([`export_schema`][commands-export-schema] and [`inspect_django_type`][commands-inspect-django-type]) reuse these exact helpers rather than hand-rolling import logic or exception handling. There is zero duplicate import translation across flavors or commands.
2. **Sync and async twins:**
   Zero duplication. Django management commands execute synchronously via the `manage.py` CLI dispatcher or `django.core.management.call_command`. Python module loading (`importlib`, `import_string`, `import_module_symbol`) is inherently synchronous. There are no async variants or twin execution paths.
3. **Derived rather than repeated knowledge:**
   - [`import_module_symbol_or_command_error`][commands-imports] derives symbol resolution directly from Strawberry's canonical `strawberry.utils.importer.import_module_symbol`, avoiding duplication of Strawberry's `module:symbol` syntax parser.
   - [`import_string_or_command_error`][commands-imports] derives dotted object resolution directly from Django's canonical `django.utils.module_loading.import_string`, avoiding duplication of Django's dotted path lookup algorithm.
   - Module name partitioning uses standard Python string slicing (`split(":", 1)`, `rpartition(".")`) to validate path shapes upfront.
   - Exception translation logic is derived in a single root helper ([`import_or_command_error`][commands-imports]), which both wrapper functions call via zero-arg lambdas.
4. **Inverse and round-trip pairs:**
   Inapplicable to this target. CLI import helpers perform unidirectional string-to-object resolution and exception transformation at the CLI entry point. There is no reverse object-to-selector serialization or lifecycle inversion owned by this module.
5. **Contracts restated in another medium:**
   The CLI import translation and path validation contracts are codified across:
   - Code: [`django_strawberry_framework/management/commands/_imports.py`][commands-imports], [`django_strawberry_framework/management/commands/export_schema.py`][commands-export-schema], [`django_strawberry_framework/management/commands/inspect_django_type.py`][commands-inspect-django-type];
   - Specifications: [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] (Slice 1, dynamic schema loading), [`docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md`][spec-022-rationale] (Decision 1 rationale), [`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (Decision 3 & 4, diagnostic CLI resolution);
   - Tests: [`tests/management/test_imports.py`][test-management-imports] (unit tests for all error translation, validation guards, and exception propagation), [`tests/management/test_export_schema.py`][test-management-export-schema], [`tests/management/test_inspect_django_type.py`][test-management-inspect-django-type];
   - Standing documentation: [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/review/rev-management__commands___imports.md`][review-commands-imports].

### The single-edit-site test

- **Posited change 1 (Modifying the exception boundary for management command imports, e.g. adding a custom exception type or adjusting cause chaining):**
  - Update [`import_or_command_error`][commands-imports] in `django_strawberry_framework/management/commands/_imports.py`.
  - All command callers ([`export_schema`][commands-export-schema], [`inspect_django_type`][commands-inspect-django-type], and future commands) automatically inherit the new behavior.
  - *Sites that must move in `django_strawberry_framework/management/commands/_imports.py`:* Exactly 1 site.
  - *Site count:* 1.
- **Posited change 2 (Altering module path syntax validation rules, e.g. supporting or disallowing specific prefix/suffix formats):**
  - Update [`_validate_absolute_module_path`][commands-imports] in `django_strawberry_framework/management/commands/_imports.py`.
  - Both Strawberry selector validation and Django dotted-path validation automatically stay in lockstep.
  - *Sites that must move in `django_strawberry_framework/management/commands/_imports.py`:* Exactly 1 site.
  - *Site count:* 1.
- **Posited change 3 (Adding a new management command that resolves a dynamic module symbol or object path, e.g. `manage.py validate_schema`):**
  - The new command imports [`import_module_symbol_or_command_error`][commands-imports] or [`import_string_or_command_error`][commands-imports].
  - *Sites that must move in `django_strawberry_framework/management/commands/_imports.py`:* Exactly 0 sites.
  - *Site count in `_imports.py`:* 0.

### Rejected candidates

1. **Merging `management/commands/_imports.py` into `utils/imports.py`:**
   - Disproved. `utils/imports.py` owns application runtime import helpers (`import_attr_if_importable`, `loaded_attr`, `import_attr`, `require_optional_module`) which depend on `importlib` and return `None` or raise `ImportError`. Importing `django.core.management.base.CommandError` in `utils/imports.py` would create an unnecessary coupling between general utility code and Django's management command subsystem. Keeping CLI-specific `CommandError` translation isolated in `management/commands/_imports.py` maintains clear architectural boundaries.
2. **Inlining `import_string` and `import_module_symbol` error handling in each command (`export_schema.py` and `inspect_django_type.py`):**
   - Disproved. Both commands share identical requirements for validating absolute paths, translating `ImportError`/`AttributeError` to `CommandError`, preserving `__cause__`, and preventing broad masking of consumer `ValueError`. Inlining would create redundant `try...except` blocks and duplicate string-partitioning logic across command files.
3. **Catching all exceptions (`except Exception:`) in `import_or_command_error`:**
   - Disproved per [spec-022][spec-022] and [spec-029][spec-029]. Broadly catching `Exception` would mask syntax errors, consumer `ValueError`s, `TypeError`s, or runtime bugs occurring inside imported modules, misleading operators into thinking the import path was wrong when in fact an unhandled error occurred during module execution. Catching strictly `(ImportError, AttributeError)` preserves correct diagnostic fidelity.

## Opportunities

None — `django_strawberry_framework/management/commands/_imports.py` is a clean, 55-line, focused utility module. It provides the single source of truth for management command path validation and `CommandError` exception translation, maintains clean separation of concerns from runtime import helpers, and contains zero duplicate logic, zero unowned state, and zero excess surface.

## Judgment

Zero-edit review. `django_strawberry_framework/management/commands/_imports.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. Target file is clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/management/commands/_imports.py --review docs/dry/dry-file-management__commands___imports.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification conducted by Worker 2 for `django_strawberry_framework/management/commands/_imports.py`.

### Independent behavioral trace and boundary challenge

1. **CLI Exception Boundary & Chained Error Translation:**
   - Re-traced [`import_or_command_error`][commands-imports]. It executes a generic dynamic importer callable `Callable[[], T] -> T` and intercepts `(ImportError, AttributeError)`.
   - Confirmed that errors are re-raised as `django.core.management.base.CommandError(str(e))` with `from e` chaining (`__cause__` preservation). This gives Django's CLI runners a clean single-line error message while keeping full debugging context in the exception hierarchy.
   - Confirmed that non-import exceptions (such as `ValueError`, `TypeError`, `SyntaxError`, or consumer domain exceptions) propagate unmasked, preventing user application errors during schema instantiation from being disguised as CLI path syntax failures.

2. **Pre-Import Syntax Validation & Upstream Exception Normalization:**
   - Re-traced [`_validate_absolute_module_path`][commands-imports]. It validates module path strings before passing them to Python's `importlib` or Strawberry's importer.
   - Rejects empty module paths (`""`, `":symbol"`) with `<value> is not a valid <label>: the module path is empty.`
   - Rejects relative module paths (`".relative"`, `".relative:symbol"`, `".a.b"`) with `<value> is not a valid <label>: relative module paths are not supported.`
   - Validated that this prevents Strawberry's `import_module_symbol` from throwing unhandled `ValueError` ("Empty module name") or `TypeError` ("relative import without a package"), standardizing error messages under `CommandError`.

3. **Selector and Dotted Path Resolution Sibling Symmetry:**
   - [`import_module_symbol_or_command_error`][commands-imports] extracts the leading module path via `selector.split(":", 1)[0]`, validates via [`_validate_absolute_module_path`][commands-imports], and invokes `strawberry.utils.importer.import_module_symbol` inside [`import_or_command_error`][commands-imports].
   - [`import_string_or_command_error`][commands-imports] partitions via `dotted_path.rpartition(".")`, validates module presence, validates module path via [`_validate_absolute_module_path`][commands-imports], and invokes Django's canonical `django.utils.module_loading.import_string` inside [`import_or_command_error`][commands-imports].
   - Confirmed both management commands ([`export_schema`][commands-export-schema] and [`inspect_django_type`][commands-inspect-django-type]) reuse these helpers exclusively.

4. **Architectural Separation from Runtime Import Helpers:**
   - Compared against [`django_strawberry_framework/utils/imports.py`][utils-imports] (`import_attr_if_importable`, `loaded_attr`, `import_attr`, `require_optional_module`).
   - `utils/imports.py` manages runtime application-level imports, cycle-breaking, and soft dependencies (returning `None` or raising `ImportError` with install hints).
   - `management/commands/_imports.py` specifically manages CLI string validation and `CommandError` transformation for management commands.
   - The separation is clean, modular, and prevents coupling general utilities to Django's management command exception classes.

5. **Mandatory 5-Axis Duplication Matrix & Single-Edit-Site Verification:**
   - Re-evaluated all 5 axes: cross-flavor policy mirroring, sync/async twins, derived knowledge, inverse pairs, and contract representations across mediums. All axes are fully discharged with valid justifications.
   - Re-verified single-edit-site counts across all 3 posited changes (counts: 1, 1, 0).

6. **Verification Tooling & Test Suite Run:**
   - Executed `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/management/commands/_imports.py --review docs/dry/dry-file-management__commands___imports.md --include-constants` — coverage verified (5 target definitions, 0 required topics).
   - Executed `uv run pytest tests/management/test_imports.py --no-cov` — all 19 unit tests passing.

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
[spec-041]: ../SPECS/spec-041-graphql_ws_subscription-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[commands-export-schema]: ../../django_strawberry_framework/management/commands/export_schema.py
[commands-imports]: ../../django_strawberry_framework/management/commands/_imports.py
[commands-inspect-django-type]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[conf]: ../../django_strawberry_framework/conf.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[management-commands-init]: ../../django_strawberry_framework/management/commands/__init__.py
[management-init]: ../../django_strawberry_framework/management/__init__.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py

<!-- tests/ -->
[test-management-export-schema]: ../../tests/management/test_export_schema.py
[test-management-imports]: ../../tests/management/test_imports.py
[test-management-inspect-django-type]: ../../tests/management/test_inspect_django_type.py

<!-- examples/ -->
[example-kanban-test-commands]: ../../examples/fakeshop/apps/kanban/tests/test_commands.py
[example-products-test-commands]: ../../examples/fakeshop/apps/products/tests/test_commands.py
[example-test-export-schema]: ../../examples/fakeshop/tests/test_export_schema.py
[example-test-inspect-django-type]: ../../examples/fakeshop/tests/test_inspect_django_type.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[review-commands-imports]: ../review/rev-management__commands___imports.md
