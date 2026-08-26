# Review: `django_strawberry_framework/rest_framework/sets.py`

Status: verified

## Understanding

`django_strawberry_framework/rest_framework/sets.py` defines `SerializerMutation`, the DRF `ModelSerializer`-backed GraphQL mutation base class, its class-creation `Meta` validation matrix, schema-time field discovery and determinism guards, nested serializer validation and recursion controls, and the phase-2.5 bind hooks (spec-039 Decision 6 / Decision 10 / Decision 11 / Decision 12).

### Architectural Responsibilities and Invariants:

1. **Subclass Architecture & Metaclass Reuse (Decision 6)**:
   - `SerializerMutation` subclasses `DjangoMutation` and overrides specific seams (`_resolve_model`, `_validate_meta`, `build_input`, `input_type_name`, `input_module_path = SERIALIZER_INPUTS_MODULE_PATH`).
   - Rides `DjangoMutation`'s metaclass, declaration registry (`_mutation_registry`), and `bind_mutations()` phase-2.5 bind unchanged. Binds model-backed `<Name>Payload` (`node` / `result` slot) through the shared primary `DjangoType` path.
   - Guarded by the DRF soft-import boundary: importing `django_strawberry_framework.rest_framework.sets` or accessing `django_strawberry_framework.SerializerMutation` resolves via root `__getattr__` with DRF present.

2. **Strict Class-Creation `Meta` Validation Matrix**:
   - `_ALLOWED_SERIALIZER_META_KEYS`: Composed from `MODEL_BACKED_WRITE_META_KEYS` (`fields`, `exclude`, `permission_classes`, `operation`, `select_for_update`) plus serializer-specific keys (`serializer_class`, `optional_fields`, `injected_fields`, `nested_fields`). Rejects `model`, `input_class`, `partial_input_class`, or unknown keys via `reject_unknown_meta_keys`.
   - Requires `serializer_class` subclassing `serializers.Serializer` and specifically `serializers.ModelSerializer`.
   - Resolves model from `Meta.serializer_class.Meta.model` via `resolve_meta_model` / `resolve_backed_model_or_raise`, type-gated with `require_model_class`.
   - Restricts `operation` to `create` and `update` via `require_non_delete_operation` (`"delete"` rejected - DRF serializers do not delete).
   - Validates field narrowing (`fields` / `exclude` mutual exclusion, normalization via `normalize_meta_field_selection`, and effective field resolution via `resolve_effective_serializer_fields`).
   - Normalizes mutation-level `optional_fields` and validates names against effective fields.
   - Validates `injected_fields` ensuring declared fields are writable at schema time, not read-only or hidden, and narrowed *out* of the client GraphQL input.
   - Enforces default `select_for_update = True` (or explicit bool) for concurrency-hardened row locks.
   - Normalizes `permission_classes` (defaulting to `[DjangoModelPermission]`).

3. **Schema Field Map Discovery & Determinism Fingerprint**:
   - `get_serializer_for_schema`: Overridable classmethod hook returning the schema-time field map. Default discovers fields by constructing `serializer_class()` with no arguments; serializers requiring context override this method to provide a stable, request-independent field map.
   - `_validate_schema_field_map`: Validates that hook returns a valid mapping of bound field names to DRF `Field` instances.
   - `_checked_schema_field_map`: Single guarded read during bind and naming that verifies the effective field shape has not drifted from the `schema_fingerprint` captured during class creation.

4. **Nested Serializer Writes & Recursion Guarding (`Meta.nested_fields`)**:
   - `_validate_serializer_nested_fields`: Validates mapping of `field_name -> NestedSerializerConfig`, ensures fields exist in the schema field map and are nested serializers (`Serializer` / `ListSerializer`), and requires the serializer class to explicitly override `create()` (for create operations) or `update()` (for update operations) to prevent DRF's default nested write `AssertionError`.
   - `_assert_schema_source_ownership`: Recursively traverses root and nested serializer fields to reject `source="*"` fields or colliding writable sources across client input, injected fields, and defaults (`runtime_validated_data_fields`). Guarded against circular recursion via `guard_nested_recursion`.

5. **Phase-2.5 Finalizer Bind & Per-Declaration Required Guarding**:
   - `build_input`: Resolves operation kind (`CREATE` -> `<Serializer>Input`, `PARTIAL` -> `<Serializer>PartialInput`), stashes `_injected_field_specs` for runtime validation, runs `guard_create_required_serializer_fields` per declaration before shape deduplication, builds the input class via `build_serializer_input_class`, dedupes via `dedupe_serializer_input_shape`, and stashes reverse-map `_input_field_specs` on the mutation class.
   - `input_type_name`: Resolves canonical input type name through `_checked_schema_field_map` and the descriptor shape cache.

6. **Constructor & Save Hook Seams**:
   - `get_serializer_kwargs`: Constructor-only kwargs hook (default returns `construction_kwargs(data=data)`). Framework-owned keys (`data`, `instance`, `partial`, `context["request"]`, `context["write_alias"]`) are strictly enforced by the resolver.
   - `get_serializer_injected_data`: Sanctioned injection hook returning values for `Meta.injected_fields` (default returns `{}`).
   - `get_serializer_save_kwargs`: DRF-native save kwargs hook for `serializer.save(**kwargs)` (default returns `{}`).
   - `resolve_sync` / `resolve_async`: Generated via `resolver_seams` delegating lazily to `django_strawberry_framework.rest_framework.resolvers`.

## Verification

1. **Static and Structural Audit**:
   - Audited all 975 lines of `django_strawberry_framework/rest_framework/sets.py`.
   - Traced connections to `django_strawberry_framework/mutations/sets.py`, `rest_framework/inputs.py`, `rest_framework/resolvers.py`, `rest_framework/serializer_converter.py`, and `types/finalizer.py`.

2. **Existing Test Suite Audit**:
   - `tests/rest_framework/test_sets.py`: 84 existing tests covering the `Meta` validation matrix, `serializer_class` type gates, `ModelSerializer` model resolution, operation restrictions, field narrowing, `optional_fields`, `injected_fields`, `select_for_update`, determinism fingerprints, nested serializer validation and cycles, retry-idempotence, and per-declaration required field guarding.
   - `tests/rest_framework/test_resolvers.py`: 163 tests covering sync/async execution, hook kwargs merging, validator queryset pinning, relation-intent tracking, ORM write witnessing, and error mapping.

3. **Scratch Experiments**:
   - Authored `docs/review/temp-tests/sets/test_scratch.py` probing:
     - Direct execution of default instance hook methods (`get_serializer_kwargs`, `get_serializer_injected_data`, `get_serializer_save_kwargs`) on instantiated `SerializerMutation` objects.
   - Scratch test passed cleanly.

4. **Focused Test Execution & Coverage**:
   - Added permanent unit test `test_default_serializer_mutation_instance_hook_methods` to `tests/rest_framework/test_sets.py`.
   - `uv run pytest tests/rest_framework/test_sets.py --no-cov`: 85 passed.
   - `uv run pytest tests/rest_framework/ --no-cov`: 451 passed.
   - Verified 100% statement coverage on `sets.py`: `uv run pytest tests/rest_framework/test_sets.py -o "addopts=" --cov=django_strawberry_framework.rest_framework.sets --cov-report=term-missing` (173/173 statements).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/rest_framework/sets.py` provides an exceptionally well-engineered, robust, and secure mutation base for DRF `ModelSerializer` models. It rigorously enforces class-creation `Meta` validation, verifies schema-time field map determinism, guards nested serializer recursion and source ownership, and ensures per-declaration create-required field integrity. The target has zero production code defects and achieves 100% statement coverage.

## Implementation (Worker 1)

- **changed files and why each was necessary:**
  - `tests/rest_framework/test_sets.py`: Added permanent test `test_default_serializer_mutation_instance_hook_methods` verifying the default behavior of `SerializerMutation` instance hook methods (`get_serializer_kwargs`, `get_serializer_injected_data`, `get_serializer_save_kwargs`) in isolation.
- **permanent tests and the behavior they pin:**
  - `test_default_serializer_mutation_instance_hook_methods`: Pins default `get_serializer_kwargs` returning `{"data": data}`, and default `get_serializer_injected_data` and `get_serializer_save_kwargs` returning `{}`.
- **scratch or focused verification and its result:**
  - Authored and ran `docs/review/temp-tests/sets/test_scratch.py` (1 passed).
  - Executed `uv run pytest tests/rest_framework/test_sets.py --no-cov` (85 passed).
  - Executed `uv run pytest tests/rest_framework/ --no-cov` (451 passed).
  - Verified 100% statement coverage (173/173 statements) on `sets.py`.
- **formatter and linter results:**
  - Executed `uv run ruff format .` and `uv run ruff check --fix .` (clean, 0 errors).
- **evidence for any rejected finding:**
  - No findings were rejected; target is robust, secure, and fully verified.
- **whether the completed behavior merits a changelog entry:**
  - No (test additions only; zero production code diff).

## Independent verification (Worker 2)

- **verification status:**
  - Complete and verified (`Status: verified`).
- **zero-edit status:**
  - Confirmed target production file `django_strawberry_framework/rest_framework/sets.py` is zero-edit against baseline `HEAD` (`12779c99`).
- **paths, behaviors, and seams traced & verified:**
  - `SerializerMutation` class creation & `_validate_meta` validation matrix (`_ALLOWED_SERIALIZER_META_KEYS`, `serializer_class` `ModelSerializer` type-gate and model resolution via `_resolve_model`, `operation in {"create", "update"}` rejection of delete, `fields` / `exclude` mutual exclusion and normalization via `normalize_meta_field_selection`, `optional_fields`, `injected_fields` writability and exposure checks, `select_for_update` default `True`, `permission_classes`).
  - Schema-time field discovery (`get_serializer_for_schema`) with own-dict `_mutation_meta` isolation during subclass inheritance, and runtime/bind determinism checking via `_checked_schema_field_map` and `serializer_schema_fingerprint`.
  - Nested serializer validation and recursion guards (`_validate_serializer_nested_fields` ensuring `create()` / `update()` override on the serializer class, and `_assert_schema_source_ownership` catching star sources and duplicate runtime write targets across root and nested levels).
  - Phase-2.5 bind hooks (`build_input` and `input_type_name` executing `guard_create_required_serializer_fields` per declaration before descriptor deduplication, stashing `_injected_field_specs` and `_input_field_specs`).
  - Constructor & save hook seams (`get_serializer_kwargs`, `get_serializer_injected_data`, `get_serializer_save_kwargs`, and `resolve_sync` / `resolve_async`).
- **test & coverage results:**
  - Executed `uv run pytest tests/rest_framework/test_sets.py --no-cov` (85 passed).
  - Executed `uv run pytest tests/rest_framework/ --no-cov` (451 passed).
  - Verified 100% statement coverage on `django_strawberry_framework/rest_framework/sets.py` (173/173 statements).
  - Linter: `uv run ruff check .` passed with 0 errors.
- **disposition of findings:**
  - No defects found; implementation is secure, resilient, and adheres strictly to specification.

