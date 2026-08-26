# Review: `django_strawberry_framework/management/commands/inspect_django_type.py`

Status: verified

## Understanding

`django_strawberry_framework/management/commands/inspect_django_type.py` implements the `inspect_django_type` Django diagnostic management command (`manage.py inspect_django_type <type> [--schema <selector>]`). It walks a finalized `DjangoTypeDefinition` and prints a per-field table detailing the Django field name, Django field type, resolved GraphQL type, nullability, and which converter row fired.

It owns:
1. **Command argument definition & options (`add_arguments`)**:
   - Positional `type` argument (`str`): Accepts either a fully-qualified dotted Python path (`apps.library.schema.BookType`) or a bare registered name (`BookType`, `PublicPatron`, `ApiBookType`).
   - Optional `--schema` argument (`str`): Schema module/symbol selector imported first to register and finalize types on a cold CLI process, and to supply custom schema configuration (`name_converter`, `scalar_map`).
2. **Schema and type resolution (`handle`, `_resolve_type`, `_resolve_bare_name`)**:
   - Imports `--schema` via `_imports.import_module_symbol_or_command_error(schema, default_symbol_name="schema")` if specified.
   - Dotted paths resolve via `_imports.import_string_or_command_error`.
   - Bare names resolve across all registered types via `registry.iter_definitions()`, matching against either the converter-applied SDL type name (`_sdl_type_name`, honoring custom `NameConverter` and `Meta.name`) or the Python class `__name__`.
   - Raises informative `CommandError` diagnostics for unregistered bare names, ambiguous multi-matches (listing disambiguating dotted paths with model names), non-`DjangoType` symbols, abstract/unregistered classes lacking definitions, and unfinalized types.
3. **Table building and row dispatch (`_print_table`, `_resolve_row`)**:
   - Titles the table with the authoritative SDL type name and the underlying Django model's fully-qualified path.
   - Formats a 5-column table (`field`, `django field type`, `graphql type`, `nullable`, `converter`).
   - Dispatches per selected field in strict priority order:
     1. *Relay-Node suppressed PK* (`_is_suppressed_relay_pk`): Returns `GlobalID!`, `no`, `relay.Node id` (bypassing annotation inspection since the interface supplies the id).
     2. *Consumer-authored fields* (`_consumer_authored_row`): Reads Strawberry field metadata from `origin.__strawberry_definition__.fields`. Raises `CommandError` if Strawberry left a forward reference as `UNRESOLVED`; otherwise renders the type via `_render_strawberry_type` and reports the consumer override style (`annotation`, `strawberry.field`, or `annotation + strawberry.field`).
     3. *Auto-synthesized relations* (`_relation_row`): Detects connection-only relations (`relation_shapes = {<rel>: "connection"}`) whose list annotation was suppressed (`_suppressed_connection_name`) and renders from the synthesized `<rel>_connection` Strawberry field metadata (`_connection_only_relation_row`); otherwise renders from `origin.__annotations__[field.name]` and names the relation cardinality (`M2M`, `forward FK`, `reverse FK`, `reverse O2O`, `generic relation`).
     4. *Auto-synthesized scalars* (`_scalar_row`): Reads resolved annotation; routes file/image output objects to `convert_field_output -> <output_type>` via `_field_output_type_for`; reports `choice enum` for choices; otherwise reports the nearest supported MRO ancestor row in `SCALAR_MAP[<Ancestor>]`.
4. **GraphQL type & scalar rendering helpers**:
   - `_render_strawberry_type` / `_consumer_nullable`: Translates Strawberry wrappers (`StrawberryOptional`, `StrawberryList`, definitions) into SDL representations and nullability tokens.
   - `_render_annotation` / `_annotation_is_optional`: Translates Python typing annotations (unions, lists, leaf scalars) into SDL representations and nullability tokens.
   - `_scalar_name`: Resolves scalar/object/enum/union names using schema `scalar_map`, built-in GraphQL scalars, `_PACKAGE_SCALAR_MAP`, or `__strawberry_definition__`/`_scalar_definition` metadata.

## Verification

1. Examined existing test suites:
   - `tests/management/test_inspect_django_type.py` (28 tests): covers bad/malformed dotted paths, ambiguous bare name resolution with copyable dotted paths, `--schema` help documentation and naming configuration, bare name SDL resolution/titling with custom `NameConverter`, bad/malformed `--schema` selectors, unregistered bare names, non-`DjangoType` symbols, unfinalized types, abstract bases, MRO ancestor `SCALAR_MAP` row naming, multi-member union rendering, unresolved forward references, direct `relay.Node` inheritance pk suppression, connection-only relation shapes, `Meta.name` resolution/titling, `Meta.name` collisions, and custom scalar/union definitions.
   - `examples/fakeshop/tests/test_inspect_django_type.py` (12 tests): live integration tests against real fakeshop schema verifying resolution by `Meta.name`, registered name, and dotted path; cold-path `--schema` invocation; choice enum rows; relation rows (forward FK, M2M, reverse FK); consumer-authored relation field overrides; consumer-authored scalar override matrix (`annotation`, `strawberry.field`, overlap, unsupported field); `BigInt` scalar naming fallback; Relay Node PK row; and post-override nullability reading.
2. Focused test executions:
   - `uv run pytest tests/management/test_inspect_django_type.py examples/fakeshop/tests/test_inspect_django_type.py --no-cov` (40 passed).
   - `uv run pytest tests/management/test_inspect_django_type.py examples/fakeshop/tests/test_inspect_django_type.py -o addopts="" --cov=django_strawberry_framework.management.commands.inspect_django_type --cov-report=term-missing` (40 passed, 100% statement coverage, 206/206 statements).
3. Scratch experiments:
   - `docs/review/temp-tests/management/test_inspect_django_type_scratch.py` (5 passed): verified `_yes_no`, `_annotation_is_optional`, `_consumer_nullable`, nested Strawberry type rendering, and `Meta.filesystem_path_fields` rendering.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/management/commands/inspect_django_type.py` is a comprehensive, well-architected diagnostic command. It correctly handles all field origins (Relay PKs, consumer overrides, connection-only relations, standard relations, file/image output objects, choices, and scalar types) and provides clear, actionable `CommandError` messages on invalid inputs.

## Implementation (Worker 1)

- **Changed files:** None — zero-edit cycle.
- **Scoped diff against baseline (`12779c99`):** empty (`git diff 12779c99 -- django_strawberry_framework/management/commands/inspect_django_type.py`).
- **Justification:** The command is thoroughly tested with 100% statement coverage (206/206 statements) across 40 unit and live integration tests. It handles all edge cases cleanly without defect.
- **Permanent tests and pinned behavior:**
   - `tests/management/test_inspect_django_type.py` (28 tests) pins argument parsing, disambiguation error formatting, custom name converter and scalar map threading, abstract and unfinalized type errors, unresolved forward references, and direct relay inheritance.
   - `examples/fakeshop/tests/test_inspect_django_type.py` (12 tests) pins live integration against example models/types, cold-path `--schema` loading, consumer override combinations, choice fields, and relation rendering.
- **Scratch verification:** `docs/review/temp-tests/management/test_inspect_django_type_scratch.py` (5 passed).
- **Formatter and linter results:** Zero-edit cycle (no tracked edits).
- **Evidence for rejected findings:** None.
- **Changelog entry:** No.

## Independent verification (Worker 2)

- **Scoped baseline check:** Target file `django_strawberry_framework/management/commands/inspect_django_type.py` is zero-edit against baseline `12779c99` (`git diff 12779c99 -- django_strawberry_framework/management/commands/inspect_django_type.py` confirmed empty).
- **Behavioral re-trace and analysis:**
  - Positional argument resolution handles dotted module paths (`import_string_or_command_error`) and bare registered names (`_resolve_bare_name`), matching against both converter-applied SDL type names (honoring custom schema `NameConverter` and `Meta.name`) and Python class `__name__`.
  - Collision diagnostics report disambiguating dotted paths and underlying model names when bare names match multiple registered types.
  - Clear error paths for non-DjangoType symbols, abstract base classes without definitions, and unfinalized types.
  - Robust row dispatch order:
    1. Relay-Node suppressed PKs bypass `origin.__annotations__` indexing and output `GlobalID!`, `no`, `relay.Node id`.
    2. Consumer-authored fields (annotation, `strawberry.field`, or both) resolve from `origin.__strawberry_definition__.fields` and catch `UNRESOLVED` forward references.
    3. Auto-synthesized relations (including connection-only shapes that popped list annotations) resolve via annotations or synthesized `<rel>_connection` Strawberry fields.
    4. Auto-synthesized scalars accurately identify file/image output type routing (`_field_output_type_for`), choice enums, or matched MRO ancestor entries in `SCALAR_MAP`.
- **Focused test execution:**
  - `uv run pytest tests/management/test_inspect_django_type.py examples/fakeshop/tests/test_inspect_django_type.py --no-cov` passed (40 passed).
  - `uv run pytest docs/review/temp-tests/management/test_inspect_django_type_scratch.py --no-cov` passed (5 passed).
- **Disposition:** All findings and edge cases verified complete. No open defects or behavior gaps.

