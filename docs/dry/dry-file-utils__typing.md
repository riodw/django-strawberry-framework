# DRY review: `django_strawberry_framework/utils/typing.py`

Status: verified

## System trace

`django_strawberry_framework/utils/typing.py` implements the centralized async-callable inspection, schema/config resolution, type unwrapping, and Strawberry container peeling helpers ([spec-029][spec-029], [spec-030][spec-030], [spec-031][spec-031], [spec-046][spec-046]).

It owns the following architectural responsibilities:

1. **Schema & Configuration Accessors:**
   - Schema unwrappers: [`strawberry_schema_from_schema`][utils-typing] (`django_strawberry_framework/utils/typing.py::strawberry_schema_from_schema`) and [`strawberry_schema_from_info`][utils-typing] (`django_strawberry_framework/utils/typing.py::strawberry_schema_from_info`).
   - Schema config resolver: [`schema_config_from_info`][utils-typing] (`django_strawberry_framework/utils/typing.py::schema_config_from_info`).

2. **Callable Inspection & Async Predicates:**
   - Bounded recursion ceiling: [`_MAX_TYPE_WRAPPER_DEPTH`][utils-typing].
   - Target unwrapper: [`_callable_inspection_target`][utils-typing] (`django_strawberry_framework/utils/typing.py::_callable_inspection_target`).
   - Callable predicates: [`is_async_callable`][utils-typing] (`django_strawberry_framework/utils/typing.py::is_async_callable`) and [`is_async_generator_callable`][utils-typing] (`django_strawberry_framework/utils/typing.py::is_async_generator_callable`).

3. **Type & Container Unwrapping:**
   - GraphQL type unwrap: [`unwrap_graphql_type`][utils-typing] (`django_strawberry_framework/utils/typing.py::unwrap_graphql_type`).
   - Strawberry container unwrap: [`unwrap_container_type`][utils-typing] (`django_strawberry_framework/utils/typing.py::unwrap_container_type`).
   - Return type single-layer unwrap: [`unwrap_return_type`][utils-typing] (`django_strawberry_framework/utils/typing.py::unwrap_return_type`).

Connected behavior examined:
- [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker]: GraphQL type unwrapping via `unwrap_graphql_type`.
- [`django_strawberry_framework/fields/relay.py`][fields-relay]: Relay connection resolution and async callable checks.
- [`django_strawberry_framework/types/relay.py`][types-relay]: Relay GlobalID resolver callable validation.
- [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner]: Schema config extraction via `schema_config_from_info`.
- [`tests/utils/`][tests-utils]: Test suite validating wrapper peeling, async callable detection, and container unwrapping.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/typing.py --include-constants`):
- Parsed 1 target file, 244 lines.
- Complete inventory across all 10 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/typing.py` provides uniform type inspection across GraphQL schema generation, field factories, optimizer walkers, and subscription handlers:
   - `is_async_callable` and `is_async_generator_callable` see through `partial`, `staticmethod`, and instance `__call__` wrappers identically.
   - `unwrap_graphql_type`, `unwrap_container_type`, and `unwrap_return_type` enforce safe type peeling across Strawberry and graphql-core ASTs.
   - `strawberry_schema_from_info` and `schema_config_from_info` unify private Strawberry schema extraction across plan-time and resolve-time Info objects.

2. **Sync and async twins:**
   Async callable inspection correctly differentiates standard coroutines (`is_async_callable`) from asynchronous generators (`is_async_generator_callable`).

3. **Derived rather than repeated knowledge:**
   `_callable_inspection_target` unwraps nested `functools.partial` and `staticmethod` descriptors in a single shared loop bounded by `_MAX_TYPE_WRAPPER_DEPTH`.

4. **Inverse and round-trip pairs:**
   Type unwrapping primitives safely terminate on base leaf types without altering non-wrapper attributes.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/typing.py`][utils-typing], [`django_strawberry_framework/fields/relay.py`][fields-relay], [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker], [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner];
   - Specifications: [`docs/SPECS/spec-029-fields-0_0_8.md`][spec-029], [`docs/SPECS/spec-030-optimizer-0_0_9.md`][spec-030], [`docs/SPECS/spec-031-relay_connections-0_0_9.md`][spec-031], [`docs/SPECS/spec-046-composite_pk_support-0_0_14.md`][spec-046];
   - Test suites: [`tests/utils/`][tests-utils], [`tests/fields/`][tests-fields];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Supporting a new wrapper type in callable inspection):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/typing.py`][utils-typing] ([`_callable_inspection_target`][utils-typing]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Adjusting the maximum type wrapper recursion ceiling):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/typing.py`][utils-typing] ([`_MAX_TYPE_WRAPPER_DEPTH`][utils-typing]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Modifying schema configuration extraction from info objects):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/typing.py`][utils-typing] ([`schema_config_from_info`][utils-typing]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Ad-hoc `inspect.iscoroutinefunction` calls in field wrappers:**
   - Disproved per [spec-029][spec-029]. Direct `iscoroutinefunction` missed `partial` and `staticmethod` descriptors, causing runtime misclassification.

## Opportunities

None — `django_strawberry_framework/utils/typing.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/typing.py` exhibits zero duplicate code and complete policy consolidation across callable detection, schema resolution, and type unwrapping. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/typing.py --review docs/dry/dry-file-utils__typing.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/typing.py`][utils-typing] and Worker 1's DRY review.

1. **Callable Detection & Type Unwrapping:**
   - Confirmed `is_async_callable` and `is_async_generator_callable` unwrap static methods and partials correctly.
   - Confirmed `unwrap_graphql_type` and `unwrap_container_type` enforce `_MAX_TYPE_WRAPPER_DEPTH` to guard against circular references.
   - Confirmed `schema_config_from_info` cleanly extracts configuration from plan-time and resolve-time Info contexts.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/typing.py --review docs/dry/dry-file-utils__typing.md --include-constants`. 100% coverage across all 10 definitions / constants.

Confirmed: `django_strawberry_framework/utils/typing.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-029]: ../SPECS/spec-029-fields-0_0_8.md
[spec-030]: ../SPECS/spec-030-optimizer-0_0_9.md
[spec-031]: ../SPECS/spec-031-relay_connections-0_0_9.md
[spec-046]: ../SPECS/spec-046-composite_pk_support-0_0_14.md

<!-- package source -->
[fields-relay]: ../../django_strawberry_framework/fields/relay.py
[optimizer-nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py

<!-- tests -->
[tests-fields]: ../../tests/fields/
[tests-utils]: ../../tests/utils/
