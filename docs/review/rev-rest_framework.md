# Subsystem: rest_framework/

Status: verified

## Understanding

The `django_strawberry_framework/rest_framework/` subpackage provides native integration between Django REST framework (`ModelSerializer`) and Strawberry GraphQL mutations (`SerializerMutation`). It allows existing or newly declared DRF model serializers to back GraphQL mutations with automatic `@strawberry.input` generation, Relay GlobalID relation resolution, file upload handling, full validation error propagation, savepoint isolation, and post-save database attestation—without tight coupling or eager DRF dependencies.

### Architectural Structure & Modules

1. **`__init__.py` (Soft Dependency Boundary & Lazy Root Exports)**
   - Gates DRF access behind `require_drf()`, which invokes `django_strawberry_framework.utils.imports.require_optional_module("rest_framework", install_hint=...)` with the explicit install requirement `djangorestframework>=3.17.0`.
   - Protects the framework root from eager DRF imports: `import django_strawberry_framework` succeeds even if DRF is uninstalled. Accessing serializer surfaces (`SerializerMutation`, `SerializerHookContext`, `UploadMetadata`, `register_serializer_field_converter`, `SerializerFieldConversion`, `describe_serializer_input`, `NestedSerializerConfig`) through root `__getattr__` lazily triggers `require_drf()`.
   - `from django_strawberry_framework import *` excludes serializer symbols from `__all__`, preventing unintended import-time triggers.

2. **`hook_context.py` (Immutable Hook Dataclasses)**
   - `SerializerHookContext`: A frozen, slotted dataclass encapsulating `operation` (`"create"` | `"update"`), `write_alias` (`str`), and `instance_pk` (`Any | None`). Passed to consumer hook methods (`get_serializer_kwargs`, `get_serializer_injected_data`, `get_serializer_save_kwargs`) instead of live model instances, enforcing immutability and preventing premature database reads.
   - `UploadMetadata`: A frozen, slotted dataclass carrying metadata for uploaded files (`name`, `size`, `content_type`, `charset`).

3. **`serializer_converter.py` (Field Conversion & Custom Extensibility)**
   - Implements MRO-based field conversion (`convert_with_mro`) mapping DRF serializer fields to Strawberry types/scalars/enums.
   - Handles built-in DRF field conversions (numbers, booleans, strings, dates, UUIDs, IP addresses, JSON, decimal, choice enums, nested serializers, and file fields).
   - Generates and deduplicates GraphQL choice enum types across mutations via `_SERIALIZER_CHOICE_ENUMS` and registers lifecycle reset with `register_subsystem_clear(owner="rest_framework.choice_enums")`.
   - Protects against hostile metadata (stripping dangerous characters from docstrings/help_text).
   - Exposes public converter extensibility via `register_serializer_field_converter` and `SerializerFieldConversion`.

4. **`inputs.py` (Input Class Materialization & Shape Substrate)**
   - Builds pure, finalizer-free `@strawberry.input` classes corresponding to DRF serializer field shapes.
   - Implements `get_serializer_for_schema()` default discovery, catching lazy `.fields` evaluation errors and raising clear `ConfigurationError` diagnostics advising on the override contract.
   - Computes deterministic SHA-1 shape tokens (`SerializerInputShape`) to ensure identical shapes share materialized input types while divergent shapes (such as differing nullability, requiredness, or field sets) receive distinct, collision-free types.
   - Parks generated input classes in `django_strawberry_framework.rest_framework.inputs` and registers namespace cleanup via `register_subsystem_clear(owner="rest_framework.input_namespace", before_bind=True)`.
   - Enforces nested serializer configuration rules, depth caps (`_NESTED_MAX_DEPTH = 5`), and recursive cycle detection.

5. **`sets.py` (Mutation Base & Metaclass Contracts)**
   - Provides `SerializerMutation`, inheriting from `DjangoMutation` and registered in the unified `_mutation_registry`.
   - Enforces class-creation validation via `_validate_meta` against `_ALLOWED_SERIALIZER_META_KEYS`, requiring a valid `ModelSerializer` subclass, supported `operation` (`"create"` or `"update"`), and consistent model/field definitions.
   - Implements determinism checks (`schema_fingerprint`, `_checked_schema_field_map`) and validates schema-time source ownership and nested serializer configurations.
   - Participates in Phase-2.5 schema finalization (`bind_mutations()`), materializing inputs and payload types (`<Name>Payload`).

6. **`resolvers.py` (Execution Pipeline & Security Invariants)**
   - Implements both synchronous (`_run_serializer_pipeline_sync`) and asynchronous (`_run_serializer_pipeline_async`) write pipelines.
   - Adheres strictly to the **authorize-before-decode** security invariant: authentication and permission checks run prior to decoding Relay IDs, preventing information leaks via visibility side-channels.
   - Enforces runtime write-source ownership (`_assert_runtime_write_source_ownership`) and relation-intent tracking (`_RelationIntentLedger`, `_assert_relation_intent`).
   - Isolates DRF unique/unique-together validator queries by pinning them to the target write database alias (`_pin_validator_querysets`).
   - Wraps database execution in transactional savepoints (`managed_write_transaction`), captures ORM write witnessing (`_write_witness`), and performs post-save relation attestation (`_attest_saved_relations`).
   - Formats validation errors into standard GraphQL `FieldError` structures with depth/budget-limited flattening (`serializer_errors_to_field_errors`).

### Cross-Subsystem Interfaces

- **`django_strawberry_framework.mutations`**: `SerializerMutation` subclasses `DjangoMutation` in `mutations/sets.py`, rides the central mutation registry, shares `DjangoMutationField`, and uses `run_write_pipeline_sync` / `run_write_pipeline_async` execution primitives.
- **`django_strawberry_framework.types` / `finalizer`**: Schema finalizer `bind_mutations()` coordinates phase-2.5 binding of `SerializerMutation` classes, resolving primary `DjangoType` nodes for relation targets and binding input/payload types.
- **`django_strawberry_framework.registry`**: Subsystem lifecycle hooks register pre-bind and post-bind cleanups via `register_subsystem_clear` for `rest_framework.input_namespace`, `rest_framework.choice_enums`, and `rest_framework.shape_cache`.
- **`django_strawberry_framework.utils`**: Reuses core utilities for Relay GlobalID encoding/decoding (`utils/relay.py`), input field specs (`utils/inputs.py`), dynamic imports (`utils/imports.py`), permission extraction (`utils/permissions.py`), and transactional write pipelines (`utils/write_transaction.py`).

## Verification

The subsystem was verified across all layers using targeted automated test suites and cross-subsystem scratch integration testing:

1. **Dedicated Subsystem Test Suite**:
   ```bash
   uv run pytest tests/rest_framework/ --no-cov
   ```
   - **451 passed** in 4.47s across all 5 test modules (`test_converter.py`, `test_inputs.py`, `test_resolvers.py`, `test_sets.py`, `test_soft_dependency.py`).

2. **Soft Dependency Guard Verification**:
   ```bash
   uv run pytest tests/rest_framework/test_soft_dependency.py --no-cov
   ```
   - **19 passed** in 1.80s, verifying that `import django_strawberry_framework` and star imports succeed without DRF, all 7 public exports raise informative `ImportError` hints on access, and attribute resolution is non-memoizing.

3. **Live Example Integration Tests**:
   ```bash
   uv run pytest examples/fakeshop/test_query/test_library_api.py -k "Serializer or serializer" --no-cov
   ```
   - **27 passed** in 8.95s, validating live HTTP execution of serializer mutations, relation visibility scoping, file uploads, nested configs, error envelopes, and golden SDL consistency.

4. **Scratch Subsystem Integration Test**:
   - Executed `docs/review/temp-tests/rest_framework/test_subsystem_scratch.py` validating full-pipeline lifecycle: DRF soft check -> primary `DjangoType` registration -> `SerializerMutation` declaration & validation -> Phase-2.5 `finalize_django_types()` binding -> `DjangoSchema` GraphQL mutation execution -> GlobalID relation resolution -> instance persistence -> payload return -> `registry.clear()` lifecycle cleanup.

## Improvements

### High
None.

### Medium
None.

### Low
None.

## Summary

The `rest_framework` subpackage is fully compliant with all architectural, security, and soft-dependency invariants. Its modular division of responsibilities cleanly separates field conversion, input materialization, mutation class declaration, and resolver execution pipeline while integrating seamlessly with the core schema finalizer, registry lifecycle, and Relay type system.

## Implementation (Worker 1)

- **Status**: fix-implemented
- **Changes**: None — zero-edit cycle. All component modules and subsystem-level contracts are fully verified with 100% test coverage and 0 defects.
- **Verification**: 451 unit/integration tests in `tests/rest_framework/`, 27 live example tests in `examples/fakeshop/`, 19 soft-dependency isolation tests, and scratch integration test all passed.
- **Linter Status**: Clean (`uv run ruff check .` and `uv run ruff format --check .` passing).
- **Changelog Entry**: None required (folder review pass with no code modifications).

## Independent verification (Worker 2)

- **Verification Status**:
  - `Status: verified`
- **Subsystem Architecture & Cohesion Re-tracing**:
  - **Soft dependency boundary & lazy exports (`__init__.py`)**:
    - Confirmed `require_drf()` delegates to `require_optional_module("rest_framework", install_hint=...)` naming `djangorestframework>=3.17.0`.
    - Confirmed root `__getattr__` routes access to `_DRF_SOFT_EXPORTS` lazily and non-memoizingly through `require_drf()`.
    - Confirmed all DRF-related symbols are excluded from root `__all__`, preserving DRF-free `from django_strawberry_framework import *`.
    - Verified with `tests/rest_framework/test_soft_dependency.py` (19 passed).
  - **Immutable hook data structures (`hook_context.py`)**:
    - Confirmed `SerializerHookContext` and `UploadMetadata` are slotted, frozen dataclasses without `__dict__`.
    - Confirmed `SerializerHookContext` encapsulates `operation`, `write_alias`, and `instance_pk` for consumer hooks, protecting against instance mutation attacks before save.
    - Confirmed `UploadMetadata` safely descriptors upload files in hook views without stream consumption.
  - **MRO field conversion & extensibility (`serializer_converter.py`)**:
    - Confirmed `convert_with_mro` dispatch sequence: prechecks -> MRO walk over `_SERIALIZER_FIELD_CONVERTERS` -> fail-loud `ConfigurationError` on unmapped field types.
    - Confirmed public extension registry `register_serializer_field_converter` enforcing `Field` subclassing, callable conversions, and `override=True` duplicate guard.
    - Confirmed choice enum generation, deduplication, and subsystem clear hook (`register_subsystem_clear(owner="rest_framework.choice_enums")`).
    - Confirmed hostile metadata repr sanitization.
  - **Pure input materialization & shape identity (`inputs.py`)**:
    - Confirmed schema discovery via `get_serializer_for_schema()` with lazy `.fields` error wrapping into actionable `ConfigurationError`.
    - Confirmed deterministic SHA-1 shape token hashing (`SerializerInputShape`) reserving canonical naming for full shapes while hashing divergent shapes.
    - Confirmed recursive nested input generation (`NestedSerializerConfig`), depth cap (_NESTED_MAX_DEPTH = 5), and cycle detection.
    - Confirmed pre-bind clear registration (`register_subsystem_clear(owner="rest_framework.input_namespace", before_bind=True)`).
  - **Mutation declaration & metaclass contracts (`sets.py`)**:
    - Confirmed `SerializerMutation` subclassing `DjangoMutation`, inheriting registration and phase-2.5 bind hooks.
    - Confirmed `Meta` validation matrix (`_ALLOWED_SERIALIZER_META_KEYS`, `ModelSerializer` model resolution, `create`/`update` operation filter, `select_for_update` concurrency default).
    - Confirmed schema fingerprinting and source ownership audit across root and nested serializers.
  - **Write pipeline execution & security invariants (`resolvers.py`)**:
    - Confirmed strict pipeline execution ordering and authorize-before-decode invariant.
    - Confirmed Relay GlobalID relation decoding against primary `DjangoType.get_queryset` visibility filters.
    - Confirmed constructor-only hook kwargs merging (`_merged_serializer_kwargs`) and deeply frozen hook views (`_frozen_hook_view`).
    - Confirmed write-alias query pinning for DRF validators (`_pin_validator_querysets`).
    - Confirmed savepoint isolation (`managed_write_transaction`), relation-intent ledger tracking (`_RelationIntentLedger`), ORM write witnessing (`_write_witness`), and post-save database attestation (`_attest_saved_relations`).
    - Confirmed depth- and budget-limited error flattening to GraphQL `FieldError` structures.
- **Challenge Testing & Test Suite Execution**:
  - Executed scratch integration tests challenging soft dependency boundary, root export resolution, hook immutability, custom converter MRO inheritance, choice enum deduplication, and full GraphQL create/update mutation lifecycle with Relay GlobalID relation resolution and savepoint isolation (`4 passed`).
  - Executed dedicated subsystem unit test suite: `uv run pytest tests/rest_framework/ --no-cov` (`451 passed` in 4.37s).
  - Executed soft dependency test suite: `uv run pytest tests/rest_framework/test_soft_dependency.py --no-cov` (`19 passed` in 1.61s).
  - Executed live example HTTP test suite: `uv run pytest examples/fakeshop/test_query/test_library_api.py -k "Serializer or serializer" --no-cov` (`27 passed` in 9.25s).
- **Hygiene & Linting**:
  - `uv run ruff check .` passed with 0 errors.
  - `uv run ruff format --check .` passed with 0 errors.
- **Outcome**:
  - All requirements and invariants are verified. No defects or regressions found.

