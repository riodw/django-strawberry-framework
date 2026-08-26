# Review: `django_strawberry_framework/utils/inputs.py`

Status: verified

## Understanding

`django_strawberry_framework/utils/inputs.py` is the neutral, framework-wide foundation for GraphQL input type generation, name derivation, cache keying, namespace lifecycle management, and metadata normalization across all five input-generating subsystems (`filters`, `orders`, `mutations`, `forms`, `rest_framework`). It is strictly decoupled from the domain-specific subsystems to prevent circular imports while ensuring complete single-siting of shared generation invariants.

Its responsibilities divide into four core areas:

1. **Common Input Construction, Materialization, and Collision Detection**:
   - `build_strawberry_input_class`: Safely dynamically builds `@strawberry.input` dataclasses from `(python_attr, annotation, field_kwargs)` triples, strictly respecting explicit GraphQL names, descriptions, and default value semantics (required vs optional).
   - `materialize_generated_input_class`: Pins built classes into caller module globals (`sys.modules[module_path]`) and a tracking ledger. Handles idempotent re-materialization while raising fail-loud `ConfigurationError` on duplicate class name collisions.
   - `duplicate_name_message` and `iter_input_field_collisions`: Single-sources actionable collision diagnostic messages across input attributes, GraphQL names, and write sources.
   - `make_input_namespace`: Single-sited factory producing the `(ledger, materialize_fn, clear_fn)` namespace trio used across write families (`mutations`, `forms`, `rest_framework`). Leaves module globals parked in `module.__dict__` during clears to preserve lazy type references across test reloads.

2. **Set Family Lifecycle and BFS Input Factory**:
   - `GeneratedInputFieldSpec`: Immutable dataclass recording python attribute, GraphQL name, and source lookup path for set inputs.
   - `emit_set_input_field_triples`: Translates set filter/order entries into input field triples while validating collisions and recording field specifications.
   - `set_input_type_name`: Delegates to class `type_name_for()` hook.
   - `optional_field_kwargs` and `optional_input_field`: Single-sites optional widening (`annotation | None`, `default=strawberry.UNSET` or `default=None`) and divergent GraphQL camelCase name aliasing.
   - `make_set_input_namespace`: Produces the heavy `(ledger, field_specs, materialize_fn, clear_fn)` namespace tuple for set families (`filters`, `orders`).
   - `clear_generated_input_namespace`: Cleans materialization ledgers, field specification maps, arguments-factory caches, and per-set `_lifecycle` binding attributes across all subclasses.
   - `GeneratedInputArgumentsFactory`: Base BFS walker constructing input classes for a root set and all reachable related targets. Features FIFO deterministic build queue, cycle resilience (`A -> B -> A`), duplicate type name collision detection, and subclassing protection via `__init_subclass__`.
   - `build_lazy_input_annotation`: Eagerly validates set classes and returns `Annotated[<Name>, strawberry.lazy(<module>)]` forward references while recording references in the helper ledger.

3. **Write Family Input Mechanics and Shape Identity**:
   - `InputFieldSpec` and `FieldConversionBase`: Standard specifications and decode kinds (`SCALAR`, `RELATION_SINGLE`, `RELATION_MULTI`, `FILE`).
   - `pascalize_token`: Injective, uniquely-decomposable token encoder for field names with single leading uppercase and underscore-escaped special characters.
   - `generated_input_type_name` and `name_set_input_type_name`: Derives deterministic `<Base>Input` / `<Base>PartialInput` or narrowed `<Base><Tokens>Input` class names.
   - `normalize_field_name_sequence`: Validates and normalizes `Meta.fields` / `Meta.exclude` sequences, rejecting non-sequences, bare strings, non-string items, and duplicates.
   - `resolve_effective_fields`: Narrows a basis dictionary against `fields` or `exclude`, enforcing mutual exclusivity, unknown field detection, and non-empty result requirements.
   - `guard_dropped_required`: Ensures required fields are not silently dropped by exclusions unless explicitly waived.
   - `iter_provided_input_fields`: Inspects Strawberry input instances, yielding active attributes where value is not `strawberry.UNSET`.
   - `make_shape_build_cache` and `get_or_store_shape_build`: Generic memoization cache for shape builds.

4. **Set-Meta Canonicalization, Promotion, and Layer-6 Dynamic Sets**:
   - `make_hashable_meta_value`: Recursively transforms complex metadata (dicts, sets, lists, tuples, models) into stable, hashable primitives resilient to hostile `__repr__`, container recursion cycles, and excessive depth.
   - `resolve_set_meta_fields`, `canonicalize_set_meta_fields`, `promote_set_meta_fields`, `read_set_meta_fields`: Single-sites `filter_fields` alias resolution, sort-canonicalizes set/frozenset field definitions, and ensures class-Meta consistency across Python hash seeds.
   - `make_set_meta_cache_key` and `normalize_set_meta_for_factory`: Canonicalizes factory keyword arguments into deduplication keys.
   - `create_dynamic_set_class` and `make_dynamic_set_getter`: Factory helper for Layer-6 dynamic `FilterSet` and `OrderSet` class generation and caching.

## Verification

1. **Traced Callers Across Subsystems**:
   - `filters/` (`__init__.py`, `base.py`, `inputs.py`, `sets.py`, `factories.py`): Verified usage of `make_set_input_namespace`, `GeneratedInputArgumentsFactory`, `build_lazy_input_annotation`, `resolve_set_meta_fields`, `promote_set_meta_fields`, `read_set_meta_fields`, `make_dynamic_set_getter`.
   - `orders/` (`__init__.py`, `base.py`, `inputs.py`, `sets.py`, `factories.py`): Verified usage of `make_set_input_namespace`, `GeneratedInputArgumentsFactory`, `build_lazy_input_annotation`, `promote_set_meta_fields`, `read_set_meta_fields`, `make_dynamic_set_getter`.
   - `mutations/` (`inputs.py`, `sets.py`, `resolvers.py`): Verified usage of `make_input_namespace`, `build_strawberry_input_class`, `name_set_input_type_name`, `pascalize_token`, `iter_input_field_collisions`, `InputFieldSpec`, `optional_input_field`.
   - `forms/` (`converter.py`, `inputs.py`, `sets.py`, `resolvers.py`): Verified usage of `make_input_namespace`, `resolve_effective_fields`, `guard_dropped_required`, `name_set_input_type_name`, `InputFieldSpec`, `FieldConversionBase`.
   - `rest_framework/` (`serializer_converter.py`, `inputs.py`, `sets.py`, `resolvers.py`): Verified usage of `make_input_namespace`, `resolve_effective_fields`, `guard_dropped_required`, `normalize_field_name_sequence`, `make_shape_build_cache`, `get_or_store_shape_build`, `generated_input_type_name`, `InputFieldSpec`.
   - `auth/` (`queries.py`): Verified usage of `iter_provided_input_fields`.

2. **Existing Test Suite**:
   - Executed focused tests for the target: `uv run pytest tests/utils/test_inputs.py --no-cov` (55 passed in 2.96s).
   - Executed all subsystem input suites: `uv run pytest tests/utils/test_inputs.py tests/filters/test_inputs.py tests/orders/test_inputs.py tests/mutations/test_inputs.py tests/forms/test_inputs.py tests/rest_framework/test_inputs.py --no-cov` (403 passed in 4.72s).

3. **Scratch Verification**:
   - Created `docs/review/temp-tests/utils_inputs/test_inputs_scratch.py` covering:
     - `FieldConversionBase` attributes and kinds.
     - `resolve_effective_fields` behavior: un-narrowed copies, `fields` order preservation, `exclude` filtering, mutual exclusivity rejection, unknown field diagnostics, and empty result checks.
     - `guard_dropped_required` validation on non-waived vs waived fields.
     - `build_lazy_input_annotation` validation and ledger registration.
     - `GeneratedInputArgumentsFactory` BFS traversal, subclassing rejection, and zero-field input rejection.
   - Executed scratch tests: `uv run pytest docs/review/temp-tests/utils_inputs/test_inputs_scratch.py --no-cov` (6 passed in 1.60s).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/utils/inputs.py` is an exceptionally well-engineered, robust substrate for input construction across all framework families. It cleanly isolates shared concerns—including metaclass normalization, name generation, lazy module globals materialization, collision reporting, and BFS input walking—with extensive defensive safeguards against hostile objects, container cycles, and duplicate names. No defects or regressions were found.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:** None (zero-edit cycle). Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/utils/inputs.py` is empty.
- **Permanent tests and pinned behavior:**
  - `tests/utils/test_inputs.py` (55 tests) comprehensively pins all functions and classes across `utils/inputs.py`.
- **Scratch verification:**
  - `docs/review/temp-tests/utils_inputs/test_inputs_scratch.py` passed (6/6 tests), verifying `FieldConversionBase`, `resolve_effective_fields`, `guard_dropped_required`, `build_lazy_input_annotation`, and `GeneratedInputArgumentsFactory` BFS / subclassing guards.
- **Formatter and linter results:**
  - Zero-edit cycle; target file is clean and conforms to all formatting/linting rules.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

Independently verified `django_strawberry_framework/utils/inputs.py` across all four core capability areas and callers:

1. **Behavioral Tracing & Contract Invariants**:
   - **Common input generation and namespace lifecycle**: Checked `build_strawberry_input_class` (handles custom SDL descriptions, required non-null fields when default is omitted vs optional fields when explicit default is provided, duplicate attribute and duplicate GraphQL name rejection), `materialize_generated_input_class` (idempotent module global attachment with duplicate name `ConfigurationError`), `duplicate_name_message` and `iter_input_field_collisions` (consistent diagnostic formatting across collision axes), and `make_input_namespace` (lightweight ledger trio leaving parked globals intact).
   - **Set family lifecycle & BFS input arguments factory**: Checked `GeneratedInputFieldSpec`, `emit_set_input_field_triples`, `set_input_type_name`, `optional_field_kwargs`, `optional_input_field`, `make_set_input_namespace`, `clear_generated_input_namespace` (heavy clear resetting factory caches, field provenance, and lifecycle descriptors), `GeneratedInputArgumentsFactory` (deterministic BFS queue, cycle resilience on related targets, class-level cache isolation, empty-expansion fail-loud guard, subclassing guard on concrete factories), and `build_lazy_input_annotation` (type validation, ledger tracking, and `Annotated[..., strawberry.lazy(...)]` generation).
   - **Write family input mechanics**: Checked `InputFieldSpec`, `FieldConversionBase`, `pascalize_token` (injective leading-capital token encoding across all alphanumeric, underscore, uppercase, and special unicode boundaries), `generated_input_type_name` / `name_set_input_type_name`, `normalize_field_name_sequence` (handles sequence validation, rejection of bare strings, non-strings, and duplicates), `resolve_effective_fields` (mutual exclusivity, unknown field detection, basis order preservation on exclusion, and empty result rejection), `guard_dropped_required` (set-arithmetic required field validation with waiver support), `iter_provided_input_fields` (inspecting active input attributes where value is not `strawberry.UNSET`), and `make_shape_build_cache` / `get_or_store_shape_build`.
   - **Set-meta canonicalization, promotion, and dynamic set cache**: Checked `make_hashable_meta_value` (hostile repr safety, cycle detection, depth bound <= 64, sorting of unordered dicts and sets), `resolve_set_meta_fields` / `promote_set_meta_fields` / `read_set_meta_fields` / `canonicalize_set_meta_fields` (synonym resolution and hash seed stability), `make_set_meta_cache_key` / `normalize_set_meta_for_factory`, and `create_dynamic_set_class` / `make_dynamic_set_getter`.

2. **Scoped Diff Verification**:
   - Confirmed `git diff 12779c99 -- django_strawberry_framework/utils/inputs.py` is empty (zero-edit cycle against baseline).

3. **Test Suite Verification**:
   - Executed `uv run pytest tests/utils/test_inputs.py --no-cov` (55 passed).
   - Executed full input subsystems suite: `uv run pytest tests/utils/test_inputs.py tests/filters/test_inputs.py tests/orders/test_inputs.py tests/mutations/test_inputs.py tests/forms/test_inputs.py tests/rest_framework/test_inputs.py --no-cov` (403 passed).
   - Executed scratch suite: `uv run pytest docs/review/temp-tests/utils_inputs/test_inputs_scratch.py --no-cov` (6 passed).

