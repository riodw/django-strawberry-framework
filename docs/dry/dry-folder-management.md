# DRY review: `django_strawberry_framework/management/`

Status: verified

## System trace

`django_strawberry_framework/management/` is the Django management command subsystem for the framework ([spec-021][spec-021], [spec-022][spec-022], [spec-029][spec-029], [spec-031][spec-031], [spec-032][spec-032]). It encapsulates the framework's command-line interface tooling for generating and exporting GraphQL Schema Definition Language (SDL) schemas, introspecting finalized `DjangoType` definitions into per-field resolution diagnostic tables, and safely translating command-line import paths and selectors into clean, actionable `CommandError` messages.

The subpackage comprises five Python modules structured across two directory tiers whose responsibilities and inter-module boundaries are strictly partitioned:

1. [`management/__init__.py`][management-init]: The top-level package marker and namespace initializer:
   - **Django Management Package Convention:** Satisfies Django's `django.core.management.find_commands` / `load_command_class` discovery conventions by marking `django_strawberry_framework.management` as an importable Python package within `INSTALLED_APPS` (registered via [`DjangoStrawberryFrameworkConfig`][apps] in `django_strawberry_framework/apps.py`).
   - **Public Surface Encapsulation:** Intentionally defines zero runtime logic, zero classes, zero functions, and zero re-exports (`__all__`). Management commands are invoked via `manage.py` CLI or `django.core.management.call_command`. Omission of re-exports in `management/__init__.py` and the root package [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] avoids API surface pollution ([spec-022][spec-022] Decision 1, [spec-029][spec-029] Decision 4).

2. [`management/commands/__init__.py`][management-commands-init]: The child commands subpackage marker and namespace initializer:
   - **Django Command Discovery Directory:** Marks `django_strawberry_framework.management.commands` as the command implementation package. Sibling command modules ([`export_schema.py`][commands-export-schema], [`inspect_django_type.py`][commands-inspect-django-type]) are discovered dynamically by filename by Django core; private helper modules prefixed with an underscore ([`_imports.py`][commands-imports]) are ignored during discovery.
   - **Public Surface Encapsulation:** Contains zero runtime execution logic and zero re-exports. Both command modules define an entrypoint class named `Command`; omitting re-exports in `commands/__init__.py` prevents naming collisions.

3. [`management/commands/_imports.py`][commands-imports]: Centralized CLI import and path resolution helper module:
   - **CLI Exception Boundary & Cause Chaining ([`import_or_command_error`][commands-imports]):** Runs an arbitrary dynamic importer callable (`Callable[[], T] -> T`, parameterizing [`T`][commands-imports]), catching `(ImportError, AttributeError)` and re-raising as `django.core.management.base.CommandError(str(e))` chained via `from e` (`__cause__` preservation). Application-level exceptions, syntax errors, and consumer errors (`ValueError`, `TypeError`, `ConfigurationError`) propagate unmasked, preventing CLI wrappers from disguising runtime bugs as import failures.
   - **Pre-Import Module Path Syntax Validation ([`_validate_absolute_module_path`][commands-imports]):** Statically validates module path strings before passing them to `importlib` or Strawberry's importer, rejecting empty strings (`""`, `":symbol"`) and relative paths (`".relative"`, `".a.b"`) with structured `CommandError` messages before upstream raises uninformative `ValueError` or `TypeError`.
   - **Strawberry Selector Resolution ([`import_module_symbol_or_command_error`][commands-imports]):** Resolves Strawberry `module[:symbol]` selectors (e.g. `"config.schema"`, `"config.schema:schema"`), validating module path shape and delegating symbol resolution to `strawberry.utils.importer.import_module_symbol` inside [`import_or_command_error`][commands-imports].
   - **Django Dotted Object Path Resolution ([`import_string_or_command_error`][commands-imports]):** Resolves standard Django dotted object paths (e.g. `"apps.library.schema.BookType"`), validating dotted structure and module path before delegating to `django.utils.module_loading.import_string` inside [`import_or_command_error`][commands-imports].

4. [`management/commands/export_schema.py`][commands-export-schema]: The GraphQL SDL schema export management command:
   - **Command Registration & Arguments ([`django_strawberry_framework/management/commands/export_schema.py::Command`][commands-export-schema], [`django_strawberry_framework/management/commands/export_schema.py::Command.add_arguments`][commands-export-schema]):** Subclasses `BaseCommand` (`help = "Export the GraphQL schema"`), registering positional `schema` (type `str`) and optional `--path` (type `str`). Bare `--path` without a following value is rejected early by `argparse`.
   - **Schema Resolution & Type Enforcement ([`django_strawberry_framework/management/commands/export_schema.py::Command.handle`][commands-export-schema]):** Resolves the schema selector via [`import_module_symbol_or_command_error`][commands-imports] (defaulting to `"schema"`), enforcing `isinstance(schema_symbol, Schema)` with `CommandError("The `schema` must be an instance of strawberry.Schema")`.
   - **SDL Rendering & Byte-Exact Output Routing ([`django_strawberry_framework/management/commands/export_schema.py::Command.handle`][commands-export-schema]):** Renders SDL via `strawberry.printer.print_schema(schema_symbol)`. Default stdout branch (`path is None`) writes via `self.stdout.write(schema_output, ending="")`, suppressing Django's default `ending="\n"` to ensure byte-exact identity with `print_schema()` and `--path` file bytes. Blank/whitespace paths raise `CommandError("--path requires a non-empty value")`. File output branch writes UTF-8 text via `pathlib.Path(path).write_text(schema_output, encoding="utf-8", newline="")`, disabling host platform newline translation (`newline=""`) to prevent CRLF divergence on Windows, catching `(OSError, ValueError)` and re-raising as `CommandError(str(e)) from e`.

5. [`management/commands/inspect_django_type.py`][commands-inspect-django-type]: The `DjangoType` field resolution diagnostic introspection command:
   - **Constants & Diagnostic Metadata:** Canonical GlobalID type label [`_GLOBAL_ID_GRAPHQL_TYPE`][commands-inspect-django-type] (`"GlobalID!"`), Relay pk converter label [`_RELAY_PK_CONVERTER`][commands-inspect-django-type] (`"relay.Node id"`), default name converter fallback [`_DEFAULT_NAME_CONVERTER`][commands-inspect-django-type] (`NameConverter()`), relation kind label mapping [`_RELATION_KIND_LABELS`][commands-inspect-django-type] (`"many"` -> `"M2M"`, `"forward_single"` -> `"forward FK"`, `"reverse_many_to_one"` -> `"reverse FK"`, `"reverse_one_to_one"` -> `"reverse O2O"`, `"generic"` -> `"generic relation"`), unfinalized diagnostic hint [`_UNFINALIZED_HINT`][commands-inspect-django-type], and GraphQL scalar mapping [`_GRAPHQL_SCALAR_NAMES`][commands-inspect-django-type] (dynamically merging package-defined scalars from [`django_strawberry_framework.scalars._PACKAGE_SCALAR_MAP`][scalars] to prevent hardcoded scalar name drift).
   - **Command Registration & Arguments ([`django_strawberry_framework/management/commands/inspect_django_type.py::Command`][commands-inspect-django-type], [`django_strawberry_framework/management/commands/inspect_django_type.py::Command.add_arguments`][commands-inspect-django-type]):** Subclasses `BaseCommand` (`help = "Inspect a DjangoType's resolved per-field GraphQL types"`), registering positional `type` and optional `--schema`.
   - **Execution Orchestration ([`django_strawberry_framework/management/commands/inspect_django_type.py::Command.handle`][commands-inspect-django-type]):** Imports project schema when `--schema` is provided via [`import_module_symbol_or_command_error`][commands-imports], triggering type registration and finalization. Extracts active `name_converter` and `scalar_map`. Parameterizes scalar namer via `functools.partial` over [`_scalar_name`][commands-inspect-django-type]. Resolves target type via [`Command._resolve_type`][commands-inspect-django-type], verifies `DjangoType` subclass, verifies definition attachment, enforces `definition.finalized is True` (raising [`_UNFINALIZED_HINT`][commands-inspect-django-type]), and invokes [`Command._print_table`][commands-inspect-django-type].
   - **Type Resolution & Ambiguity Disambiguation:** [`Command._resolve_type`][commands-inspect-django-type] dispatches by argument shape: dotted path delegates to [`import_string_or_command_error`][commands-imports]; bare name delegates to [`Command._resolve_bare_name`][commands-inspect-django-type], which iterates [`django_strawberry_framework.registry.registry.iter_definitions`][registry] matching against SDL type name ([`_sdl_type_name`][commands-inspect-django-type]) and Python class name (`type_cls.__name__`), raising clear ambiguity `CommandError` listing candidates if collisions occur.
   - **Diagnostic Table Formatting & Most-Specific-First Row Resolution:** [`Command._print_table`][commands-inspect-django-type] prints table header with authoritative SDL name and Django model qualified name. [`Command._resolve_row`][commands-inspect-django-type] dispatches field rows:
     1. Relay-Node-suppressed pk ([`Command._is_suppressed_relay_pk`][commands-inspect-django-type] using [`django_strawberry_framework.types.base._is_relay_shaped`][types-base]) returns `(_GLOBAL_ID_GRAPHQL_TYPE, "no", _RELAY_PK_CONVERTER)`.
     2. Consumer-authored field (`field.name in definition.consumer_authored_fields`) delegates to [`Command._consumer_authored_row`][commands-inspect-django-type], reading `origin.__strawberry_definition__.fields`, detecting `UNRESOLVED` forward references and formatting override origins via [`_consumer_converter_label`][commands-inspect-django-type] and [`_consumer_nullable`][commands-inspect-django-type].
     3. Relation field (`field_meta.is_relation`) delegates to [`Command._relation_row`][commands-inspect-django-type], detecting connection-only shapes via [`Command._suppressed_connection_name`][commands-inspect-django-type] and rendering via [`Command._connection_only_relation_row`][commands-inspect-django-type] from synthesized siblings in `definition.relation_connections`, or reading `origin.__annotations__` formatted via [`_render_annotation`][commands-inspect-django-type].
     4. Scalar field delegates to [`Command._scalar_row`][commands-inspect-django-type], reading `origin.__annotations__`, checking file output types via [`django_strawberry_framework.types.converters._field_output_type_for`][types-converters], choice enums, or matched ancestor in [`SCALAR_MAP`][types-converters] via [`_matched_scalar_key`][commands-inspect-django-type].
   - **Rendering Helpers:** Nullability token formatter [`_yes_no`][commands-inspect-django-type], union optionality detector [`_annotation_is_optional`][commands-inspect-django-type], MRO scalar ancestor locator [`_matched_scalar_key`][commands-inspect-django-type], Strawberry type renderer [`_render_strawberry_type`][commands-inspect-django-type], consumer nullability classifier [`_consumer_nullable`][commands-inspect-django-type], consumer converter label formatter [`_consumer_converter_label`][commands-inspect-django-type], authoritative SDL type name extractor [`_sdl_type_name`][commands-inspect-django-type], GraphQL scalar name resolver [`_scalar_name`][commands-inspect-django-type], and typing annotation renderer [`_render_annotation`][commands-inspect-django-type].

Connected subsystem integration examined:
- [`django_strawberry_framework/apps.py`][apps]: `DjangoStrawberryFrameworkConfig` AppConfig registering the application in `INSTALLED_APPS` for management command discovery.
- [`django_strawberry_framework/conf.py`][conf]: Configuration management singleton; CLI explicitly requires schema arguments rather than implicit fallback settings.
- [`django_strawberry_framework/registry.py`][registry]: Global registry maintaining type definitions queried by `inspect_django_type` (`iter_definitions`, `model_for_type`).
- [`django_strawberry_framework/scalars.py`][scalars]: Package-defined scalars (`_PACKAGE_SCALAR_MAP`) dynamically merged into `_GRAPHQL_SCALAR_NAMES`.
- [`django_strawberry_framework/relay.py`][relay]: Relay specification constants and node interfaces integrated into `inspect_django_type` pk suppression.
- [`django_strawberry_framework/types/base.py`][types-base]: `DjangoType`, `_is_relay_shaped`, `FieldMeta`.
- [`django_strawberry_framework/types/converters.py`][types-converters]: `SCALAR_MAP`, `_field_output_type_for`, `FIELD_OUTPUT_TYPE_MAP`, `DjangoFileType`, `DjangoImageType`.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Phase 2.5 schema finalizer executing `finalize_django_types()`.
- [`django_strawberry_framework/utils/imports.py`][utils-imports]: Runtime application import helpers (`import_attr_if_importable`, `loaded_attr`, `import_attr`, `require_optional_module`) strictly partitioned from CLI error translators.
- [`django_strawberry_framework/utils/strings.py`][utils-strings]: Supplies `snake_case` for field map lookups.
- Test suites: [`tests/management/__init__.py`][test-management-init], [`tests/management/test_imports.py`][test-management-imports], [`tests/management/test_export_schema.py`][test-management-export-schema], [`tests/management/test_inspect_django_type.py`][test-management-inspect-django-type], [`examples/fakeshop/tests/test_export_schema.py`][example-test-export-schema], [`examples/fakeshop/tests/test_inspect_django_type.py`][example-test-inspect-django-type].

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/management/ --review docs/dry/dry-folder-management.md --include-constants`):
- Parsed 5 target files (`__init__.py`, `commands/__init__.py`, `commands/_imports.py`, `commands/export_schema.py`, `commands/inspect_django_type.py`), 744 total lines.
- Inventoried 36 definitions and module constants across the entire subpackage:
  - `management/__init__.py`: 0 definitions/constants;
  - `management/commands/__init__.py`: 0 definitions/constants;
  - `management/commands/_imports.py`: 5 definitions/constants ([`T`][commands-imports], [`import_or_command_error`][commands-imports], [`_validate_absolute_module_path`][commands-imports], [`import_module_symbol_or_command_error`][commands-imports], [`import_string_or_command_error`][commands-imports]);
  - `management/commands/export_schema.py`: 3 definitions/constants ([`django_strawberry_framework/management/commands/export_schema.py::Command`][commands-export-schema], [`django_strawberry_framework/management/commands/export_schema.py::Command.add_arguments`][commands-export-schema], [`django_strawberry_framework/management/commands/export_schema.py::Command.handle`][commands-export-schema]);
  - `management/commands/inspect_django_type.py`: 28 definitions/constants ([`_GLOBAL_ID_GRAPHQL_TYPE`][commands-inspect-django-type], [`_RELAY_PK_CONVERTER`][commands-inspect-django-type], [`_DEFAULT_NAME_CONVERTER`][commands-inspect-django-type], [`_RELATION_KIND_LABELS`][commands-inspect-django-type], [`_UNFINALIZED_HINT`][commands-inspect-django-type], [`_GRAPHQL_SCALAR_NAMES`][commands-inspect-django-type], [`django_strawberry_framework/management/commands/inspect_django_type.py::Command`][commands-inspect-django-type], [`django_strawberry_framework/management/commands/inspect_django_type.py::Command.add_arguments`][commands-inspect-django-type], [`django_strawberry_framework/management/commands/inspect_django_type.py::Command.handle`][commands-inspect-django-type], [`Command._resolve_type`][commands-inspect-django-type], [`Command._resolve_bare_name`][commands-inspect-django-type], [`Command._print_table`][commands-inspect-django-type], [`Command._resolve_row`][commands-inspect-django-type], [`Command._is_suppressed_relay_pk`][commands-inspect-django-type], [`Command._relation_row`][commands-inspect-django-type], [`Command._suppressed_connection_name`][commands-inspect-django-type], [`Command._connection_only_relation_row`][commands-inspect-django-type], [`Command._scalar_row`][commands-inspect-django-type], [`Command._consumer_authored_row`][commands-inspect-django-type], [`_yes_no`][commands-inspect-django-type], [`_annotation_is_optional`][commands-inspect-django-type], [`_matched_scalar_key`][commands-inspect-django-type], [`_render_strawberry_type`][commands-inspect-django-type], [`_consumer_nullable`][commands-inspect-django-type], [`_consumer_converter_label`][commands-inspect-django-type], [`_sdl_type_name`][commands-inspect-django-type], [`_scalar_name`][commands-inspect-django-type], [`_render_annotation`][commands-inspect-django-type]).
- Confirmed zero missing definitions across all five files.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   - **Developer Tooling & Diagnostic Inspection:** Management commands provide command-line tooling for schema generation (`export_schema`) and diagnostic introspection (`inspect_django_type`). Unlike declarative feature subpackages (`filters`, `forms`, `mutations`, `orders`, `types`, `rest_framework`) that construct GraphQL types, resolvers, and mutation pipelines, management commands accept CLI strings and format output.
   - **Unified CLI Exception Translation:** Both management commands delegate dynamic module and object resolution to [`django_strawberry_framework/management/commands/_imports.py`][commands-imports] ([`import_module_symbol_or_command_error`][commands-imports], [`import_string_or_command_error`][commands-imports]). There is zero duplicate path validation or exception translation logic across commands.
   - **Single-Source Authorities:** `inspect_django_type.py` reuses existing framework predicates and metadata registries rather than re-implementing them:
     - Relay shape detection delegates to [`django_strawberry_framework.types.base._is_relay_shaped`][types-base];
     - File output type resolution delegates to [`django_strawberry_framework.types.converters._field_output_type_for`][types-converters];
     - Scalar conversions reference [`django_strawberry_framework.types.converters.SCALAR_MAP`][types-converters];
     - Package scalar names derive dynamically from [`django_strawberry_framework.scalars._PACKAGE_SCALAR_MAP`][scalars];
     - Type definitions query [`django_strawberry_framework.registry.registry`][registry].
   - **Packaging Convention Symmetry:** Sibling package markers [`management/__init__.py`][management-init] and [`management/commands/__init__.py`][management-commands-init] mirror each other as clean namespace markers complying with Django discovery conventions without exposing conflicting `Command` symbols.
2. **Sync and async twins:**
   - **Zero Logic Duplication:** Django management commands execute synchronously within the `manage.py` CLI dispatcher or `django.core.management.call_command`.
   - **Inherently Synchronous Pipeline:** Module importing (`importlib`, `import_string`), schema printing (`strawberry.printer.print_schema`), file I/O (`pathlib.Path.write_text`), type registry introspection, and terminal output formatting are synchronous operations. No async variants, parallel execution branches, or twin duplication exist.
3. **Derived rather than repeated knowledge:**
   - **Dynamic Command Discovery:** Command discovery is dynamically derived by Django core scanning `management/commands/*.py` on disk, eliminating static registration tables in `commands/__init__.py` or `management/__init__.py`.
   - **Upstream Parser & Printer Reuse:** Selector parsing derives from Strawberry's `strawberry.utils.importer.import_module_symbol`; dotted path resolution derives from Django's `django.utils.module_loading.import_string`; SDL generation derives from Strawberry's canonical `strawberry.printer.print_schema`.
   - **Dynamic Scalar Registry Synchronization:** [`_GRAPHQL_SCALAR_NAMES`][commands-inspect-django-type] merges `_PACKAGE_SCALAR_MAP` dynamically rather than hardcoding duplicate scalar name literals, preventing silent drift if scalar names change.
   - **Introspection of Finalized Records:** `inspect_django_type` derives per-field resolution from post-finalization runtime records (`origin.__annotations__`, `origin.__strawberry_definition__.fields`, `definition.relation_connections`) rather than re-running synthesis or re-evaluating overrides.
   - **Output Byte Parity:** Byte-for-byte consistency between stdout and `--path` file output is derived by suppressing Django's default ending (`ending=""`) on stdout and disabling platform newline conversion (`newline=""`) on file writes.
4. **Inverse and round-trip pairs:**
   - **SDL Schema Emission:** Unidirectional code-first projection from `strawberry.Schema` to SDL strings or disk files; byte-for-byte consistency between stdout and `--path` file output is guaranteed.
   - **Type Resolution Table:** Unidirectional diagnostic projection from in-memory `DjangoTypeDefinition` metadata to formatted terminal text; SDL type names match CLI resolution inputs.
   - **Exception Cause Preservation:** Dynamic import translation wraps `(ImportError, AttributeError)` in `CommandError` while preserving `__cause__` (`from e`), allowing interactive debuggers and test runners to inspect original tracebacks.
5. **Contracts restated in another medium:**
   - Management command contracts are consistently codified across:
     - Specifications: [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021], [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] (Slice 1-3, Decisions 1-10), [`docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md`][spec-022-rationale], [`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (Slice 2, Decisions 3, 4, 7), [`docs/SPECS/spec-031-globalid_encoding-0_0_9.md`][spec-031], [`docs/SPECS/spec-032-full_relay-0_0_9.md`][spec-032];
     - Production code: [`django_strawberry_framework/management/`][management-init], [`django_strawberry_framework/management/commands/`][management-commands-init], [`django_strawberry_framework/apps.py`][apps], [`django_strawberry_framework/registry.py`][registry], [`django_strawberry_framework/scalars.py`][scalars], [`django_strawberry_framework/relay.py`][relay], [`django_strawberry_framework/types/`][types-base];
     - Comprehensive test suites: [`tests/management/__init__.py`][test-management-init], [`tests/management/test_imports.py`][test-management-imports], [`tests/management/test_export_schema.py`][test-management-export-schema], [`tests/management/test_inspect_django_type.py`][test-management-inspect-django-type], [`examples/fakeshop/tests/test_export_schema.py`][example-test-export-schema], [`examples/fakeshop/tests/test_inspect_django_type.py`][example-test-inspect-django-type];
     - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new package-level custom scalar in `django_strawberry_framework/scalars.py`, e.g. `CustomScalar`):**
  - Register the scalar in `_PACKAGE_SCALAR_MAP` in `scalars.py`.
  - [`_GRAPHQL_SCALAR_NAMES`][commands-inspect-django-type] automatically inherits the new scalar name dynamically via `_PACKAGE_SCALAR_MAP`.
  - *Sites that must move in `management/`:* Exactly 0 sites.
  - *Site count in `management/`:* 0.
- **Posited change 2 (Modifying CLI dynamic import exception translation or cause chaining across all management commands):**
  - Update [`import_or_command_error`][commands-imports] in `_imports.py`.
  - Both `export_schema` and `inspect_django_type` automatically inherit the updated behavior.
  - *Sites that must move in `management/`:* Exactly 1 site: [`django_strawberry_framework/management/commands/_imports.py`][commands-imports].
  - *Site count:* 1.
- **Posited change 3 (Modifying module path syntax validation rules, e.g. supporting or disallowing specific prefix/suffix formats):**
  - Update [`_validate_absolute_module_path`][commands-imports] in `_imports.py`.
  - Both Strawberry selector validation and Django dotted-path validation stay in lockstep.
  - *Sites that must move in `management/`:* Exactly 1 site: [`django_strawberry_framework/management/commands/_imports.py`][commands-imports].
  - *Site count:* 1.
- **Posited change 4 (Customizing SDL formatting or printer options in schema export):**
  - Update the `print_schema(schema_symbol)` invocation in [`django_strawberry_framework/management/commands/export_schema.py::Command.handle`][commands-export-schema].
  - *Sites that must move in `management/`:* Exactly 1 site: [`django_strawberry_framework/management/commands/export_schema.py`][commands-export-schema].
  - *Site count:* 1.
- **Posited change 5 (Adjusting diagnostic table column formatting or widths in `inspect_django_type`):**
  - Update format strings in [`Command._print_table`][commands-inspect-django-type] in `inspect_django_type.py`.
  - *Sites that must move in `management/`:* Exactly 1 site: [`django_strawberry_framework/management/commands/inspect_django_type.py`][commands-inspect-django-type].
  - *Site count:* 1.
- **Posited change 6 (Adding a new Django management command to the framework, e.g. `validate_schema`):**
  - Add `django_strawberry_framework/management/commands/validate_schema.py`, reusing [`_imports.py`][commands-imports].
  - Django's `manage.py` dynamic discovery walks `management/commands/` directly on disk.
  - *Sites that must move in existing `management/` files:* 0 code sites (optionally 1 docstring site in [`commands/__init__.py`][management-commands-init]).
  - *Site count in existing files:* 0 (code) / 1 (docstring).
- **Posited change 7 (Renaming or moving the framework's management namespace or app packaging layout):**
  - Rename or update the docstrings in the namespace markers [`management/__init__.py`][management-init] or [`management/commands/__init__.py`][management-commands-init].
  - *Sites that must move in `management/`:* Exactly 1 site per modified namespace docstring.
  - *Site count:* 1.

### Rejected candidates

1. **Merging `management/commands/_imports.py` into `utils/imports.py`:**
   - Disproved. `utils/imports.py` owns runtime application-level imports, cycle-breaking, and soft dependencies (returning `None` or raising `ImportError` with install hints). `management/commands/_imports.py` specifically manages CLI string validation and `CommandError` transformation for management commands. Importing `django.core.management.base.CommandError` in `utils/imports.py` would leak CLI-specific exception dependencies into runtime utility code.
2. **Inlining import path parsing and `CommandError` exception handling in `export_schema.py` and `inspect_django_type.py`:**
   - Disproved. Both commands share identical requirements for validating absolute paths, translating `ImportError`/`AttributeError` to `CommandError`, preserving `__cause__`, and preventing broad masking of consumer `ValueError`. Inlining would create duplicate `try...except` blocks and redundant string-partitioning logic across command files.
3. **Re-exporting `Command` classes in `management/commands/__init__.py`, `management/__init__.py`, or root `__init__.py`:**
   - Disproved per [spec-022][spec-022] Decision 1 and [spec-029][spec-029] Decision 4. Both commands name their entrypoint class `Command`, causing immediate naming collisions. Furthermore, management commands are discovered dynamically via `INSTALLED_APPS` and invoked via `manage.py` CLI or `call_command`, not imported by consumer application code.
4. **Re-running `convert_scalar` or relation resolution during table rendering in `inspect_django_type.py`:**
   - Disproved per [spec-029][spec-029] Decision 4. Re-running `convert_scalar` during CLI execution ignores `Meta.nullable_overrides`, `Meta.required_overrides`, and consumer-authored annotations, reporting inaccurate column-native types. Reading directly from `origin.__annotations__` and `origin.__strawberry_definition__` guarantees inspection matches true GraphQL schema behavior.
5. **Hardcoding package scalars (e.g. `"BigInt"`) in `_GRAPHQL_SCALAR_NAMES` in `inspect_django_type.py`:**
   - Disproved. Hardcoding scalar names creates a drift risk if the scalar's public name changes in `scalars.py`. Dynamically merging `_PACKAGE_SCALAR_MAP` ensures the CLI fallback stays synchronized with the runtime registry.
6. **Eliminating `management/__init__.py` or `management/commands/__init__.py`:**
   - Disproved per [spec-021][spec-021] and [spec-022][spec-022] Decision 1. Django's command discovery is directory-based, requiring both `management` and `management.commands` to be importable packages on `sys.path`. Omitting either `__init__.py` breaks Django's `find_commands` mechanism.

## Opportunities

None — The folder integration of `django_strawberry_framework/management/` is architecturally clean, comprehensively tested, and fully consolidated at root owners. Cross-file boundaries across `__init__.py`, `commands/__init__.py`, `commands/_imports.py`, `commands/export_schema.py`, and `commands/inspect_django_type.py`, as well as external boundaries with `apps.py`, `conf.py`, `registry.py`, `scalars.py`, `relay.py`, `types/`, `utils/imports.py`, and `utils/strings.py`, are strictly defined and honor all repository and design invariants.

## Judgment

Zero-edit folder integration review. All 5 files in `django_strawberry_framework/management/` operate in total structural alignment. All 5 axes of the mandatory duplication matrix are verified and discharged across the subpackage boundary. Single-edit-site counts are 0 or 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. Subpackage folder integration verified clean and complete across all 5 files and 36 definitions/constants. Completeness verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/management/ --review docs/dry/dry-folder-management.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification confirms that Worker 1's folder review of `django_strawberry_framework/management/` is thorough, exhaustive, and architecturally sound across both directory tiers (`management/` and `management/commands/`).

Key findings and architectural confirmations:
1. **Tiered Packaging & Discovery Architecture:**
   - [`management/__init__.py`][management-init] and [`management/commands/__init__.py`][management-commands-init] form a clean two-tier packaging hierarchy satisfying Django core's `django.core.management.find_commands` discovery convention when registered via [`DjangoStrawberryFrameworkConfig`][apps] in `INSTALLED_APPS`.
   - Both package markers deliberately contain zero runtime logic and zero re-exports (`__all__`), eliminating namespace pollution and avoiding name collisions between sibling commands defining entrypoint classes named `Command` ([spec-022][spec-022] Decision 1, [spec-029][spec-029] Decision 4).
2. **CLI Import & Path Resolution Isolation:**
   - [`management/commands/_imports.py`][commands-imports] establishes a strict boundary for management commands, isolating pre-import module path validation ([`_validate_absolute_module_path`][commands-imports]) and `CommandError` exception wrapping ([`import_or_command_error`][commands-imports], [`import_module_symbol_or_command_error`][commands-imports], [`import_string_or_command_error`][commands-imports]) from runtime application import utilities in [`django_strawberry_framework/utils/imports.py`][utils-imports].
   - Exception cause chaining (`from e`) is preserved for debugging while ensuring non-import consumer exceptions (`ValueError`, `TypeError`, `ConfigurationError`) propagate unmasked.
3. **Command Implementations & Diagnostic Introspection:**
   - [`management/commands/export_schema.py`][commands-export-schema] correctly delegates schema resolution to `_imports.py`, enforces `strawberry.Schema` instance typing, renders SDL using `strawberry.printer.print_schema`, and guarantees byte-for-byte output identity between stdout (`ending=""`) and file writes (`newline=""`).
   - [`management/commands/inspect_django_type.py`][commands-inspect-django-type] queries post-finalization runtime records in priority order (Relay-Node pk suppression -> consumer overrides -> relations / connection siblings -> scalars / file output converters), reusing existing predicates ([`_is_relay_shaped`][types-base]) and scalar registries ([`SCALAR_MAP`][types-converters], [`_PACKAGE_SCALAR_MAP`][scalars]) without duplicating synthesis logic.
4. **5-Axis Probing Matrix Discharged:**
   - *Cross-flavor policy mirroring:* Verified clear separation between CLI tooling/diagnostic inspection and type-generating subsystems. Dynamic module/object resolution is unified in `_imports.py` with zero duplication across commands. Sibling namespace markers mirror each other cleanly.
   - *Sync and async twins:* Verified inherently synchronous CLI execution under Django's management command dispatcher. Zero async twin duplication.
   - *Derived rather than repeated knowledge:* Verified dynamic discovery by Django core, dynamic scalar mapping synchronization via `_PACKAGE_SCALAR_MAP`, and non-duplicative post-finalization metadata introspection.
   - *Inverse and round-trip pairs:* Verified unidirectional SDL schema emission and diagnostic text projections with preserved `__cause__` chains.
   - *Contracts restated in another medium:* Verified alignment across specs ([spec-021][spec-021], [spec-022][spec-022], [spec-029][spec-029], [spec-031][spec-031], [spec-032][spec-032]), production modules, test suites, and standing docs.
5. **Single-Edit-Site Counts:**
   - Verified 7 posited modifications across the folder hierarchy; all require 0 or 1 edit sites within `management/`.
6. **Tool & Test Gate Validations:**
   - Executed `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/management/ --review docs/dry/dry-folder-management.md --include-constants` (36 target definitions, 0 missing).
   - Executed full management test suites across `tests/management/` and `examples/fakeshop/tests/` (76 passed).

Subpackage folder integration is verified complete and clean. Setting `Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-021]: ../SPECS/spec-021-apps-0_0_7.md
[spec-022]: ../SPECS/spec-022-export_schema-0_0_7.md
[spec-022-rationale]: ../SPECS/appx/spec-022-export_schema-0_0_7-rationale.md
[spec-029]: ../SPECS/spec-029-consumer_dx_cleanup-0_0_9.md
[spec-031]: ../SPECS/spec-031-globalid_encoding-0_0_9.md
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[apps]: ../../django_strawberry_framework/apps.py
[commands-export-schema]: ../../django_strawberry_framework/management/commands/export_schema.py
[commands-imports]: ../../django_strawberry_framework/management/commands/_imports.py
[commands-inspect-django-type]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[conf]: ../../django_strawberry_framework/conf.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[management-commands-init]: ../../django_strawberry_framework/management/commands/__init__.py
[management-init]: ../../django_strawberry_framework/management/__init__.py
[registry]: ../../django_strawberry_framework/registry.py
[relay]: ../../django_strawberry_framework/relay.py
[scalars]: ../../django_strawberry_framework/scalars.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py

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
