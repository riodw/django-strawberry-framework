# DRY review: `django_strawberry_framework/management/commands/inspect_django_type.py`

Status: verified

## System trace

`django_strawberry_framework/management/commands/inspect_django_type.py` is the management command module responsible for introspecting a finalized `DjangoTypeDefinition` and printing its per-field GraphQL resolution table to standard output ([spec-029][spec-029], [spec-031][spec-031], [spec-032][spec-032]). It serves as the framework's primary type-level diagnostic CLI tool, enabling developers to inspect exactly how Django model fields, scalar types, nullability overrides, relations, choice enums, file outputs, and consumer-authored overrides resolve into GraphQL types.

The module owns the following core responsibilities:

1. **Constants & Diagnostic Metadata Mapping:**
   - [`_GLOBAL_ID_GRAPHQL_TYPE`][commands-inspect-django-type] (`"GlobalID!"`): The canonical GraphQL type string rendered for Relay-Node-suppressed primary key fields.
   - [`_RELAY_PK_CONVERTER`][commands-inspect-django-type] (`"relay.Node id"`): The converter column label assigned to Relay-Node primary keys.
   - [`_DEFAULT_NAME_CONVERTER`][commands-inspect-django-type] (`NameConverter()`): The baseline schema name converter fallback when `--schema` is omitted or does not define a custom converter.
   - [`_RELATION_KIND_LABELS`][commands-inspect-django-type]: Canonical dictionary mapping internal `FieldMeta.relation_kind` tokens (`"many"`, `"forward_single"`, `"reverse_many_to_one"`, `"reverse_one_to_one"`, `"generic"`) to human-readable diagnostic labels (`"M2M"`, `"forward FK"`, `"reverse FK"`, `"reverse O2O"`, `"generic relation"`).
   - [`_UNFINALIZED_HINT`][commands-inspect-django-type]: Diagnostic hint string guiding the user to pass `--schema <path>` when a target `DjangoType` has not been finalized.
   - [`_GRAPHQL_SCALAR_NAMES`][commands-inspect-django-type]: Mapping from Python/Strawberry scalar types (`int`, `str`, `bool`, `float`, `decimal.Decimal`, `uuid.UUID`, `datetime.date`, `datetime.datetime`, `datetime.time`, `strawberry.scalars.JSON`) to their GraphQL SDL names, dynamically merged with package-defined scalars from [`django_strawberry_framework.scalars._PACKAGE_SCALAR_MAP`][scalars] (e.g. `BigInt`) to prevent hardcoded scalar name drift.

2. **Django Command Class Registration & CLI Arguments ([`Command`][commands-inspect-django-type]):**
   - Declares [`Command`][commands-inspect-django-type] subclassing `django.core.management.base.BaseCommand` with `help = "Inspect a DjangoType's resolved per-field GraphQL types"`.
   - In [`Command.add_arguments`][commands-inspect-django-type], registers the positional `type` argument (`type=str, help="DjangoType name or fully-dotted object path"`) and the optional `--schema` argument (`type=str, help="Import the project schema first to register and finalize types and use its naming configuration; required for bare names in a cold process"`).

3. **Command Orchestration & Execution Flow ([`Command.handle`][commands-inspect-django-type]):**
   - When `--schema` is provided, loads the project schema symbol via [`import_module_symbol_or_command_error`][commands-imports] (defaulting to symbol `"schema"`), triggering module-level type registration, schema-level configuration loading, and `finalize_django_types()`.
   - Extracts schema configuration, obtaining the active `name_converter` and `scalar_map`.
   - Constructs a parameterized `scalar_namer` callable using `functools.partial` over [`_scalar_name`][commands-inspect-django-type].
   - Resolves the target type via [`Command._resolve_type`][commands-inspect-django-type].
   - Validates that the target is a class subclassing [`DjangoType`][types-base], raising `CommandError(f"{options['type']} is not a DjangoType subclass")` if not.
   - Validates that the target has an attached `__django_strawberry_definition__` (rejecting abstract/no-`Meta` base classes with `CommandError`).
   - Validates that `definition.finalized` is `True`, raising `CommandError` with [`_UNFINALIZED_HINT`][commands-inspect-django-type] if finalization has not occurred.
   - Invokes [`Command._print_table`][commands-inspect-django-type] to render the diagnostic output.

4. **Type Resolution & Ambiguity Disambiguation:**
   - [`Command._resolve_type`][commands-inspect-django-type]: Dispatches by argument shape. If the argument contains a dot (`"." in arg`), delegates directly to [`import_string_or_command_error`][commands-imports]. Otherwise, delegates to [`Command._resolve_bare_name`][commands-inspect-django-type].
   - [`Command._resolve_bare_name`][commands-inspect-django-type]: Iterates over all registered type definitions in [`django_strawberry_framework.registry.registry.iter_definitions`][registry]. Matches against either the converter-applied SDL name ([`_sdl_type_name`][commands-inspect-django-type]) or the Python class name (`type_cls.__name__`).
   - If no matches are found, raises `CommandError` advising the user to pass `--schema` or use a fully-dotted path.
   - If multiple types collide on either surface, raises an ambiguity `CommandError` listing all candidate fully-dotted object paths and their underlying models to allow the operator to disambiguate immediately.

5. **Diagnostic Table Formatting & Field Resolution Hierarchy:**
   - [`Command._print_table`][commands-inspect-django-type]: Computes the authoritative SDL name via [`_sdl_type_name`][commands-inspect-django-type], prints the title line containing the SDL name and Django model qualified name, prints column headers (`field`, `django field type`, `graphql type`, `nullable`, `converter`), and prints one formatted row per field in `definition.selected_fields`.
   - [`Command._resolve_row`][commands-inspect-django-type]: Implements strict, most-specific-first resolution dispatch:
     1. Relay-Node-suppressed primary key ([`Command._is_suppressed_relay_pk`][commands-inspect-django-type]): returns `(_GLOBAL_ID_GRAPHQL_TYPE, "no", _RELAY_PK_CONVERTER)`.
     2. Consumer-authored field (`field.name in definition.consumer_authored_fields`): delegates to [`Command._consumer_authored_row`][commands-inspect-django-type].
     3. Relation field (`field_meta.is_relation`): delegates to [`Command._relation_row`][commands-inspect-django-type].
     4. Scalar field: delegates to [`Command._scalar_row`][commands-inspect-django-type].
   - [`Command._is_suppressed_relay_pk`][commands-inspect-django-type]: Reuses the central predicate [`django_strawberry_framework.types.base._is_relay_shaped`][types-base] to check if the type is Relay-shaped, verifying whether `field.name == definition.model._meta.pk.name`.
   - [`Command._relation_row`][commands-inspect-django-type]: Checks if the list form was suppressed via [`Command._suppressed_connection_name`][commands-inspect-django-type]. If so, delegates to [`Command._connection_only_relation_row`][commands-inspect-django-type]. Otherwise, reads the resolved annotation from `definition.origin.__annotations__[field.name]`, renders it via [`_render_annotation`][commands-inspect-django-type], maps the relation kind label, and computes nullability (`"no (list)"` for many-side, or [`_yes_no`][commands-inspect-django-type] for single-side).
   - [`Command._suppressed_connection_name`][commands-inspect-django-type]: Detects relations configured with `relation_shapes = {<rel>: "connection"}` whose list annotation was dropped by [`django_strawberry_framework.types.finalizer`][types-finalizer], locating the synthesized sibling name in `definition.relation_connections`.
   - [`Command._connection_only_relation_row`][commands-inspect-django-type]: Reads the synthesized connection sibling type from `origin.__strawberry_definition__.fields`, rendering it via [`_render_strawberry_type`][commands-inspect-django-type] with converter label `f"relation: {label} (connection-only)"`.
   - [`Command._scalar_row`][commands-inspect-django-type]: Reads the post-override annotation from `origin.__annotations__[field.name]`, checks if the field is a file/image output type via [`django_strawberry_framework.types.converters._field_output_type_for`][types-converters] (reporting `f"convert_field_output -> {output_type.__name__}"`), checks `field.choices` (reporting `"choice enum"`), or reports the matched MRO ancestor in [`SCALAR_MAP`][types-converters] via [`_matched_scalar_key`][commands-inspect-django-type].
   - [`Command._consumer_authored_row`][commands-inspect-django-type]: Reads finalized Strawberry field metadata from `origin.__strawberry_definition__.fields`. Intercepts Strawberry's `UNRESOLVED` sentinel (unresolved forward reference) to raise an actionable `CommandError` with recovery hints, renders the type via [`_render_strawberry_type`][commands-inspect-django-type], derives nullability via [`_consumer_nullable`][commands-inspect-django-type], and formats the converter source via [`_consumer_converter_label`][commands-inspect-django-type].

6. **Rendering Helpers & Type Analysis Functions:**
   - [`_yes_no`][commands-inspect-django-type]: Converts boolean nullability into `"yes"` or `"no"`.
   - [`_annotation_is_optional`][commands-inspect-django-type]: Inspects `typing.Union` / `types.UnionType` arguments for `type(None)`.
   - [`_matched_scalar_key`][commands-inspect-django-type]: Walks `type(field).__mro__` to find the nearest ancestor class registered in [`SCALAR_MAP`][types-converters].
   - [`_render_strawberry_type`][commands-inspect-django-type]: Recursively renders Strawberry wrapper types (`StrawberryOptional`, `StrawberryList`, concrete leaf definitions) into formatted GraphQL strings.
   - [`_consumer_nullable`][commands-inspect-django-type]: Determines nullability string (`"yes"`, `"no (list)"`, or `"no"`) from Strawberry field types.
   - [`_consumer_converter_label`][commands-inspect-django-type]: Combines authoring style (`"annotation"`, `"strawberry.field"`, or `"annotation + strawberry.field"`) and target kind (`"(scalar)"` or `"(relation)"`) from definition override sets.
   - [`_sdl_type_name`][commands-inspect-django-type]: Extracts authoritative SDL name by applying `name_converter.from_type` to class-owned `__strawberry_definition__`, falling back to `definition.graphql_type_name` for unfinalized definitions.
   - [`_scalar_name`][commands-inspect-django-type]: Resolves scalar names against active schema `scalar_map`, fixed `_GRAPHQL_SCALAR_NAMES`, `__strawberry_definition__`, `_scalar_definition`, definition instances, or `__name__`.
   - [`_render_annotation`][commands-inspect-django-type]: Formats standard typing annotations into GraphQL syntax (`Name!`, `Name`, `[Inner!]!`, `UnionA | UnionB`).

Connected behavior examined:
- [`django_strawberry_framework/management/commands/_imports.py`][commands-imports]: Provides shared import validation and error translation ([`import_module_symbol_or_command_error`][commands-imports], [`import_string_or_command_error`][commands-imports]).
- [`django_strawberry_framework/management/commands/export_schema.py`][commands-export-schema]: Sibling command also utilizing [`_imports.py`][commands-imports].
- [`django_strawberry_framework/registry.py`][registry]: Central registry holding `DjangoTypeDefinition` instances, queried by `iter_definitions` and `model_for_type`.
- [`django_strawberry_framework/scalars.py`][scalars]: Provides `_PACKAGE_SCALAR_MAP` containing package-defined scalars (e.g. `BigInt`), directly merged into `_GRAPHQL_SCALAR_NAMES`.
- [`django_strawberry_framework/types/base.py`][types-base]: Defines `DjangoType`, `DjangoTypeDefinition`, `FieldMeta`, consumer override sets, and `_is_relay_shaped`.
- [`django_strawberry_framework/types/converters.py`][types-converters]: Defines `SCALAR_MAP`, `_field_output_type_for`, `DjangoFileType`, `DjangoImageType`.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Implements type finalization, populating `__strawberry_definition__`, `relation_connections`, and resolving forward references.
- [`django_strawberry_framework/utils/strings.py`][utils-strings]: Supplies `snake_case` for field map indexing.
- [`tests/management/test_inspect_django_type.py`][test-management-inspect-django-type]: Unit test suite exercising `CommandError` failure modes, registry ambiguity diagnostics, cold `--schema` options, custom name converters, MRO scalar resolution, multi-member unions, Relay pk suppression, connection-only relations, and unresolved forward references.
- [`examples/fakeshop/tests/test_inspect_django_type.py`][example-test-inspect-django-type]: Integration test suite verifying live terminal output formatting against real fakeshop models, choice enums, relation rows, consumer overrides, `BigInt` scalars, and nullability overrides.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/management/commands/inspect_django_type.py --include-constants`):
- Target file contains 622 lines, 6 constant definitions ([`_GLOBAL_ID_GRAPHQL_TYPE`][commands-inspect-django-type], [`_RELAY_PK_CONVERTER`][commands-inspect-django-type], [`_DEFAULT_NAME_CONVERTER`][commands-inspect-django-type], [`_RELATION_KIND_LABELS`][commands-inspect-django-type], [`_UNFINALIZED_HINT`][commands-inspect-django-type], [`_GRAPHQL_SCALAR_NAMES`][commands-inspect-django-type]), 1 class definition ([`Command`][commands-inspect-django-type]), 12 method definitions ([`Command.add_arguments`][commands-inspect-django-type], [`Command.handle`][commands-inspect-django-type], [`Command._resolve_type`][commands-inspect-django-type], [`Command._resolve_bare_name`][commands-inspect-django-type], [`Command._print_table`][commands-inspect-django-type], [`Command._resolve_row`][commands-inspect-django-type], [`Command._is_suppressed_relay_pk`][commands-inspect-django-type], [`Command._relation_row`][commands-inspect-django-type], [`Command._suppressed_connection_name`][commands-inspect-django-type], [`Command._connection_only_relation_row`][commands-inspect-django-type], [`Command._scalar_row`][commands-inspect-django-type], [`Command._consumer_authored_row`][commands-inspect-django-type]), and 9 module-level function definitions ([`_yes_no`][commands-inspect-django-type], [`_annotation_is_optional`][commands-inspect-django-type], [`_matched_scalar_key`][commands-inspect-django-type], [`_render_strawberry_type`][commands-inspect-django-type], [`_consumer_nullable`][commands-inspect-django-type], [`_consumer_converter_label`][commands-inspect-django-type], [`_sdl_type_name`][commands-inspect-django-type], [`_scalar_name`][commands-inspect-django-type], [`_render_annotation`][commands-inspect-django-type]).
- Verified exact single-ownership of type introspection diagnostic rendering and error handling.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `inspect_django_type.py` is the single centralized diagnostic CLI command for inspecting `DjangoType` definitions across the framework.
   - It does not replicate or mirror type construction, filter generation, form parsing, or mutation logic from declarative subpackages (`filters`, `forms`, `mutations`, `orders`, `types`, `rest_framework`). Instead, it consumes the finalized metadata already generated by the core type system.
   - For shared predicates and mappings, it reuses existing single-source authorities:
     - Relay shape detection reuses [`django_strawberry_framework.types.base._is_relay_shaped`][types-base].
     - Field output mapping reuses [`django_strawberry_framework.types.converters._field_output_type_for`][types-converters].
     - Scalar conversions reference [`django_strawberry_framework.types.converters.SCALAR_MAP`][types-converters].
     - Package scalar names derive directly from [`django_strawberry_framework.scalars._PACKAGE_SCALAR_MAP`][scalars].
     - Management command import resolution reuses [`django_strawberry_framework.management.commands._imports.py`][commands-imports].
   - There is zero duplicate policy mirroring across flavors or commands.
2. **Sync and async twins:**
   Zero duplication. Django management commands execute synchronously via `manage.py` or `django.core.management.call_command`. Type inspection, metadata querying, and stdout formatting are synchronous operations. No async variants or parallel execution branches exist.
3. **Derived rather than repeated knowledge:**
   The command strictly reads derived, authoritative metadata records rather than re-evaluating or duplicating conversion logic:
   - Auto-synthesized fields read post-override annotations from `origin.__annotations__` (which already reflect `Meta.nullable_overrides` and `Meta.required_overrides`), rather than re-running `convert_scalar`.
   - Consumer-authored fields read finalized Strawberry definitions from `origin.__strawberry_definition__.fields` (which already reflect resolved forward references and assigned resolvers).
   - Package scalar names derive dynamically from `_PACKAGE_SCALAR_MAP` rather than hardcoding duplicate string literals.
   - Connection-only relation fields derive from `definition.relation_connections` to render synthesized siblings when list annotations were popped.
   - Scalar converter rows determine the firing rule by walking the field's `__mro__` against `SCALAR_MAP` via [`_matched_scalar_key`][commands-inspect-django-type].
4. **Inverse and round-trip pairs:**
   `inspect_django_type` is a unidirectional diagnostic projection from in-memory `DjangoTypeDefinition` metadata to formatted terminal text. No reverse text-to-DjangoType parser exists.
   Round-trip naming consistency is maintained: bare SDL type names passed on the CLI are resolved via `name_converter.from_type` and rendered identically in the table title line.
5. **Contracts restated in another medium:**
   The introspection command contracts are codified across:
   - Code: [`django_strawberry_framework/management/commands/inspect_django_type.py`][commands-inspect-django-type];
   - Shared import helpers: [`django_strawberry_framework/management/commands/_imports.py`][commands-imports];
   - Specifications: [`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (Slice 2, Decisions 4 & 7), [`docs/SPECS/spec-031-globalid_encoding-0_0_9.md`][spec-031], [`docs/SPECS/spec-032-full_relay-0_0_9.md`][spec-032];
   - Tests: [`tests/management/test_inspect_django_type.py`][test-management-inspect-django-type] (28 unit tests covering all `CommandError` branches, naming converters, MRO scalar resolution, unions, unresolved forward refs, connection-only shapes, Relay suppression) and [`examples/fakeshop/tests/test_inspect_django_type.py`][example-test-inspect-django-type] (12 live integration tests on fakeshop schema, choice enums, relations, overrides, BigInt, cold `--schema`);
   - Standing documentation: [`docs/GLOSSARY.md`][glossary] (`Schema introspection management command`), [`docs/TREE.md`][tree], [`docs/review/rev-management__commands__inspect_django_type.md`][review-commands-inspect-django-type].

### The single-edit-site test

- **Posited change 1 (Adding a new package-level custom scalar in `django_strawberry_framework/scalars.py`):**
  - Register the scalar in `_PACKAGE_SCALAR_MAP` in `scalars.py`.
  - [`_GRAPHQL_SCALAR_NAMES`][commands-inspect-django-type] automatically inherits the new scalar name via `{scalar: definition.name for scalar, definition in _PACKAGE_SCALAR_MAP.items()}`.
  - *Sites that must move in `inspect_django_type.py`:* Exactly 0 sites.
  - *Site count in `inspect_django_type.py`:* 0.
- **Posited change 2 (Adjusting table column formatting or widths in diagnostic terminal output):**
  - Update format strings in [`Command._print_table`][commands-inspect-django-type].
  - *Sites that must move in `inspect_django_type.py`:* Exactly 1 site.
  - *Site count:* 1.
- **Posited change 3 (Modifying selector syntax validation or import error handling):**
  - Update [`django_strawberry_framework/management/commands/_imports.py`][commands-imports].
  - *Sites that must move in `inspect_django_type.py`:* Exactly 0 sites.
  - *Site count in `inspect_django_type.py`:* 0.
- **Posited change 4 (Adding a new relation cardinality label token mapping):**
  - Update [`_RELATION_KIND_LABELS`][commands-inspect-django-type] in `inspect_django_type.py`.
  - *Sites that must move in `inspect_django_type.py`:* Exactly 1 site.
  - *Site count:* 1.

### Rejected candidates

1. **Re-running `convert_scalar` or relation resolution during table rendering:**
   - Disproved per [spec-029][spec-029] Decision 4. Re-running `convert_scalar` during CLI execution ignores `Meta.nullable_overrides`, `Meta.required_overrides`, and consumer-authored annotations, reporting inaccurate column-native types. Reading directly from `origin.__annotations__` and `origin.__strawberry_definition__` guarantees inspection matches true GraphQL schema behavior.
2. **Hardcoding package scalars (e.g. `"BigInt"`) in `_GRAPHQL_SCALAR_NAMES`:**
   - Disproved. Hardcoding scalar names creates a drift risk if the scalar's public name changes in `scalars.py`. Dynamically unpacking `_PACKAGE_SCALAR_MAP` ensures the CLI fallback stays synchronized with the runtime registry.
3. **Duplicating Relay-Node detection logic via ad-hoc `interfaces` tuple inspection:**
   - Disproved. Reusing [`_is_relay_shaped`][types-base] ensures that direct `relay.Node` inheritance, custom node interfaces, and `Meta.interfaces` declarations are handled uniformly across type synthesis and CLI inspection.
4. **Inlining selector parsing and `CommandError` handling:**
   - Disproved. Delegating import handling to `_imports.py` centralizes CLI exception boundaries across all management commands.

## Opportunities

None — `django_strawberry_framework/management/commands/inspect_django_type.py` is a clean, robust, 622-line diagnostic management command. It correctly reads finalized metadata from `origin.__annotations__` and `origin.__strawberry_definition__`, delegates import resolution to `_imports.py`, shares predicates with `types/base.py`, merges package scalars dynamically from `scalars.py`, handles all failure modes via `CommandError`, and contains zero duplicate logic, zero unowned state, and zero excess surface.

## Judgment

Zero-edit review. `django_strawberry_framework/management/commands/inspect_django_type.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across target-owned formatting changes and 0 for derived/delegated changes.

## Implementation (Worker 1)

No tracked code changes needed. Target file is clean, robust, and fully consolidated at root owners. Verified completeness via `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/management/commands/inspect_django_type.py --review docs/dry/dry-file-management__commands__inspect_django_type.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Worker 2 performed an independent analysis and verification of `django_strawberry_framework/management/commands/inspect_django_type.py` and Worker 1's DRY review.

1. **System Trace and Contract Verification:**
   - Re-traced the module's 28 target definitions (6 constants, 1 class, 12 methods, 9 functions).
   - Re-verified argument parsing in [`Command.add_arguments`][commands-inspect-django-type] (`type` positional, optional `--schema`).
   - Re-verified execution flow in [`Command.handle`][commands-inspect-django-type]: cold-process schema loading via [`import_module_symbol_or_command_error`][commands-imports], extraction of `name_converter` and `scalar_map`, type resolution via [`Command._resolve_type`][commands-inspect-django-type], `DjangoType` subclass check, `__django_strawberry_definition__` check, and `finalized` check raising [`_UNFINALIZED_HINT`][commands-inspect-django-type].
   - Re-verified bare name resolution in [`Command._resolve_bare_name`][commands-inspect-django-type]: queries [`django_strawberry_framework.registry.registry.iter_definitions`][registry], matching against either converter-applied SDL name ([`_sdl_type_name`][commands-inspect-django-type]) or class name `__name__`, raising detailed ambiguity `CommandError` listing all candidates if collisions occur.
   - Re-verified field row dispatch hierarchy in [`Command._resolve_row`][commands-inspect-django-type]:
     1. Relay-Node-suppressed primary key check via [`Command._is_suppressed_relay_pk`][commands-inspect-django-type] (reusing [`django_strawberry_framework.types.base._is_relay_shaped`][types-base]);
     2. Consumer-authored field check via [`Command._consumer_authored_row`][commands-inspect-django-type] (reading `origin.__strawberry_definition__.fields`, detecting `UNRESOLVED` forward references);
     3. Relation field check via [`Command._relation_row`][commands-inspect-django-type] (detecting connection-only shapes via `definition.relation_connections` and falling back cleanly);
     4. Scalar field check via [`Command._scalar_row`][commands-inspect-django-type] (detecting file outputs via [`django_strawberry_framework.types.converters._field_output_type_for`][types-converters], choice enums, or matched ancestor in [`SCALAR_MAP`][types-converters] via [`_matched_scalar_key`][commands-inspect-django-type]).

2. **Mandatory 5-Axis Duplication Probing Matrix Verification:**
   - **Cross-flavor policy mirroring:** Fully discharged. `inspect_django_type.py` acts strictly as an inspector of finalized metadata. It reuses central predicates and mappings ([`_is_relay_shaped`][types-base], [`_field_output_type_for`][types-converters], [`SCALAR_MAP`][types-converters], [`_PACKAGE_SCALAR_MAP`][scalars], [`import_module_symbol_or_command_error`][commands-imports], [`snake_case`][utils-strings]). No cross-flavor mirroring exists.
   - **Sync and async twins:** Fully discharged. Django management commands and terminal formatting execute synchronously with zero async twin duplication.
   - **Derived rather than repeated knowledge:** Fully discharged. All type information is derived from post-finalization runtime records (`origin.__annotations__`, `origin.__strawberry_definition__.fields`, `definition.relation_connections`) rather than re-running synthesis or re-evaluating overrides.
   - **Inverse and round-trip pairs:** Fully discharged. Pure unidirectional diagnostic formatter. SDL type names match CLI resolution inputs.
   - **Contracts restated in another medium:** Fully discharged. Codified across code, tests, specs ([spec-029][spec-029], [spec-031][spec-031], [spec-032][spec-032]), and documentation ([glossary][glossary], [tree][tree], [review-commands-inspect-django-type][review-commands-inspect-django-type]).

3. **Single-Edit-Site Test Verification:**
   - Posited change 1 (Adding a new package scalar in `scalars.py`): 0 sites in `inspect_django_type.py` (inherited dynamically from `_PACKAGE_SCALAR_MAP`).
   - Posited change 2 (Adjusting table column formatting or widths): 1 site in `Command._print_table`.
   - Posited change 3 (Modifying schema selector syntax / error handling): 0 sites in `inspect_django_type.py` (owned by `_imports.py`).
   - Posited change 4 (Adding a relation cardinality label token mapping): 1 site in `_RELATION_KIND_LABELS`.
   - All counts independently verified.

4. **Coverage Tooling and Test Suite Execution:**
   - Executed `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/management/commands/inspect_django_type.py --review docs/dry/dry-file-management__commands__inspect_django_type.md --include-constants` — 28 target definitions and 0 required topics covered.
   - Executed `uv run pytest tests/management/test_inspect_django_type.py examples/fakeshop/tests/test_inspect_django_type.py --no-cov` — all 40 unit and integration tests passing.

Conclusion: Verified. Worker 1's DRY review is thorough, accurate, and complete. Zero code changes required. Updating status to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-015]: ../SPECS/spec-015-relay_interfaces-0_0_5.md
[spec-019]: ../SPECS/spec-019-consumer_overrides_scalar-0_0_6.md
[spec-022]: ../SPECS/spec-022-export_schema-0_0_7.md
[spec-022-rationale]: ../SPECS/appx/spec-022-export_schema-0_0_7-rationale.md
[spec-027]: ../SPECS/spec-027-filters-0_0_8.md
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-029]: ../SPECS/spec-029-consumer_dx_cleanup-0_0_9.md
[spec-031]: ../SPECS/spec-031-globalid_encoding-0_0_9.md
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md
[spec-044]: ../SPECS/spec-044-debug_extension-0_0_14.md
[spec-050]: ../SPECS/spec-050-debug_extraction-0_0_15.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[commands-export-schema]: ../../django_strawberry_framework/management/commands/export_schema.py
[commands-imports]: ../../django_strawberry_framework/management/commands/_imports.py
[commands-inspect-django-type]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[conf]: ../../django_strawberry_framework/conf.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[management-commands-init]: ../../django_strawberry_framework/management/commands/__init__.py
[management-init]: ../../django_strawberry_framework/management/__init__.py
[registry]: ../../django_strawberry_framework/registry.py
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
[example-kanban-test-commands]: ../../examples/fakeshop/apps/kanban/tests/test_commands.py
[example-products-test-commands]: ../../examples/fakeshop/apps/products/tests/test_commands.py
[example-test-export-schema]: ../../examples/fakeshop/tests/test_export_schema.py
[example-test-inspect-django-type]: ../../examples/fakeshop/tests/test_inspect_django_type.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[review-commands-inspect-django-type]: ../review/rev-management__commands__inspect_django_type.md
