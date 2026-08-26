# Review: `django_strawberry_framework/rest_framework/resolvers.py`

Status: verified

## Understanding

`django_strawberry_framework/rest_framework/resolvers.py` implements the sync and async serializer-mutation resolver pipeline for `SerializerMutation` (spec-039). It is the DRF-serializer write runtime, the sibling of `mutations/resolvers.py` (model mutations) and `forms/resolvers.py` (form mutations).

### Architectural Responsibilities and Invariants:

1. **Pipeline Execution Lifecycle**:
   - The write pipeline follows the strict ordering:
     `(update) locate -> authorize -> decode -> construct -> validate -> write -> re-fetch -> payload`
   - **Authorize-before-decode security invariant**: Authorization executes before relation decoding, preventing unauthorized callers from probing related-object visibility/existence by id.
   - Leverages the promoted shared skeleton `mutations/resolvers.py::run_write_pipeline_sync` for `transaction.atomic()` boundaries, locate preambles, authorization ordering, locking, and the G2 re-fetch tail (`refetch_optimized`).

2. **Serializer-Field-Keyed Data Decoding (`_decode_serializer_data`, `_decode_input_object`, `_decode_nested`)**:
   - Decodes Strawberry input objects into declared DRF serializer-field-keyed dictionaries (`provided_data`).
   - Routes fields by `kind` (`SCALAR`, `RELATION_SINGLE`, `RELATION_MULTI`, `NESTED_SINGLE`, `NESTED_MULTI`, `FILE`).
   - Routes file uploads directly into `data` (matching DRF conventions, distinct from Django form `files=`).
   - Relation single and multi decoders (`_decode_relation_single`, `_decode_relation_multi`) validate target models against stashed `InputFieldSpec.related_model`, resolve visibility through `DjangoType.get_queryset`, and reduce to expected primary keys in batched queries.
   - Recursively decodes nested single/multi input objects, tracking dotted error paths (e.g. `shelves.0.code`).

3. **Constructor-Only Kwargs & Declared Injections (`_injected_serializer_data`, `_merged_serializer_kwargs`, `_frozen_hook_view`)**:
   - Authoritative data is constructed by the framework (decoded input + `get_serializer_injected_data()` matching `Meta.injected_fields` exactly).
   - Hook extension points (`get_serializer_injected_data`, `get_serializer_kwargs`, `get_serializer_save_kwargs`) receive deep, iteratively frozen views (`_frozen_hook_view` converting mappings to `MappingProxyType`, lists/tuples to `tuple`, sets to `frozenset`, bytearrays to `bytes`, and files to `UploadMetadata`), failing closed on opaque mutable leaf types or cyclic structures.
   - `_merged_serializer_kwargs` strictly guards framework-owned parameters (`data`, `instance`, `partial`, `context["request"]`, `context["write_alias"]`), rejecting modifications, substitutions, or invalid types with `ConfigurationError`.

4. **Schema/Runtime Agreement & Source Ownership Guard (`_assert_schema_runtime_agreement`, `_assert_runtime_write_source_ownership`)**:
   - Compares the runtime serializer instance against schema-time write-surface specs (`_write_surface_specs`) before validation.
   - Enforces field presence, writability (not `read_only`), source attribute matching, relation type and target model agreement, nested serializer structure agreement, file/scalar compatibility, and required/optional consistency.
   - Traverses instantiated serializers (including nested serializers) to reject collisions where context-dependent runtime fields or defaults could silently overwrite input or injected sources in `validated_data`.

5. **Queryset Scoping & Validator Pinning (`_scope_relation_querysets_to_visibility`, `_pin_validator_querysets`)**:
   - Intersects runtime serializer relation field querysets (`PrimaryKeyRelatedField`, `ManyRelatedField`) with the related `DjangoType`'s visibility queryset using a `pk__in` subquery, pinning querysets to the pipeline's write alias and applying base-manager `select_for_update` locks when requested.
   - Recursively clones and pins all queryset-backed DRF validators (`UniqueValidator`, unique-together/date validators) to the write alias, ensuring instance isolation between concurrent requests.

6. **Relation-Intent Ledger & Integrity Attestation (`_instrument_relation_intent`, `_assert_relation_intent`, `_m2m_membership_snapshot`, `_attest_saved_relations`)**:
   - Wraps relation fields' `run_validation` via `_RelationIntentLedger` to capture exact resolved instances, PKs, and database aliases before object-level validators execute.
   - Post-validation (`_assert_relation_intent`) verifies `validated_data` still carries the identical resolved objects, catching hidden-row substitutions, in-place PK mutations, popped relations, or unauthorized injected relations, while compiling the canonical `relation_pks` manifest.
   - Pre-save M2M snapshot (`_m2m_membership_snapshot`) records initial memberships for partial updates.
   - Post-save attestation (`_attest_saved_relations`) directly inspects the database to confirm FK columns and M2M memberships match the validated intent and that untouched partial-update M2Ms remained unaltered.

7. **Phased Write Execution, Witnessing, and Error Mapping (`_write_witness`, `_checked_saved_result`, `_serializer_write_step`, `serializer_errors_to_field_errors`)**:
   - Wraps execution in `_write_witness` with `pre_save` cross-alias blockers and `post_save` ORM write recording on the backing model.
   - Enforces read-only database operations until `pipeline_write_phase()` opens precisely for `serializer.save()`.
   - Runs `serializer.save()` inside a nested atomic savepoint; catches and maps `serializers.ValidationError` (depth-first flattening via `serializer_errors_to_field_errors`), Django `ValidationError`, and `IntegrityError` to `FieldError` envelopes outside the savepoint.
   - Validates saved rows via `_checked_saved_result` (backing model type, `serializer.instance` identity, non-null pk, not adding, pinned alias match, update `authorized_pk` match, and witnessed created/updated write).

8. **Resolver Entry Generation (`_run_serializer_pipeline_sync`, `resolve_serializer_sync`, `resolve_serializer_async`)**:
   - Integrates serializer decode/write steps into `run_write_pipeline_sync`.
   - Generates sync and async entrypoints via `make_resolver_entries`, running async requests under a single `sync_to_async(thread_sensitive=True)` thread boundary.

## Verification

1. **Static and Contract Analysis**:
   - Audited all 2,411 lines of `django_strawberry_framework/rest_framework/resolvers.py`.
   - Traced connections to `mutations/resolvers.py`, `rest_framework/hook_context.py`, `rest_framework/inputs.py`, `rest_framework/serializer_converter.py`, `utils/write_transaction.py`, `utils/write_values.py`, and `utils/querysets.py`.

2. **Existing Test Suite Audit**:
   - `tests/rest_framework/test_resolvers.py`: 160 existing tests covering sync/async execution, Relay and raw-pk relation decodes, hook kwargs merging and context immutability, schema/runtime agreement assertions, validator queryset pinning, relation-intent ledger enforcement, savepoint rollbacks, error flattening with depth and budget limits, and post-save attestations.
   - Identified three narrow internal branches lacking test coverage in `test_resolvers.py`:
     - Multi-nested items decoding (`_decode_nested` with `NESTED_MULTI` elements and child error handling).
     - Direct root leaf errors in `serializer_errors_to_field_errors`.
     - `_serializer_decode_step` returning `[decode_error]` on input decoding failure.

3. **Scratch Experiments**:
   - Authored `docs/review/temp-tests/resolvers/test_scratch.py` probing:
     - Root leaf errors with `serializer_errors_to_field_errors` directly returning `NON_FIELD_ERROR_KEY` (`"__all__"`).
     - `_decode_nested` with `NESTED_MULTI` decoding valid list items and short-circuiting on invalid child input objects.
     - `_serializer_decode_step` returning `[decode_error]` when decoding fails on invalid input.
   - Verified that all 3 scratch tests pass.

4. **Focused Test Execution & Coverage**:
   - Added permanent test cases to `tests/rest_framework/test_resolvers.py`.
   - `uv run pytest tests/rest_framework/test_resolvers.py --no-cov`: 163 passed.
   - `uv run pytest tests/rest_framework/ --no-cov`: 447 passed.
   - Coverage check: `uv run pytest tests/rest_framework/test_resolvers.py -o "addopts=" --cov=django_strawberry_framework.rest_framework.resolvers --cov-report=term-missing`: 100% statement coverage (667/667 statements).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/rest_framework/resolvers.py` is exceptionally well-architected, highly defensive, and rigorously implemented. It adheres strictly to spec-039 invariants (authorize-before-decode, immutable hook views, schema/runtime agreement, runtime write-source ownership, validator queryset isolation, relation-intent tracking, ORM write witnessing, and post-save database attestation). Three previously uncovered internal branches were supplemented with comprehensive permanent unit tests, achieving 100% statement coverage.

## Implementation (Worker 1)

- **changed files and why each was necessary:**
  - `tests/rest_framework/test_resolvers.py`: Added 3 permanent unit tests (`test_decode_nested_multi_decodes_items_and_handles_item_error`, `test_serializer_errors_to_field_errors_direct_leaf`, `test_serializer_decode_step_returns_field_errors_on_decode_failure`) to ensure full coverage over multi-nested item decoding, direct leaf error handling in the error flattener, and decode-step error returns.
- **permanent tests and the behavior they pin:**
  - `test_decode_nested_multi_decodes_items_and_handles_item_error`: Pins recursive decoding of multi-nested items under `NESTED_MULTI` and short-circuit error returns when a child item fails decoding.
  - `test_serializer_errors_to_field_errors_direct_leaf`: Pins handling of direct leaf error objects (e.g. `ErrorDetail`) in `serializer_errors_to_field_errors` without dict wrapping.
  - `test_serializer_decode_step_returns_field_errors_on_decode_failure`: Pins `_serializer_decode_step` returning `[decode_error]` on input decoding failure.
- **scratch or focused verification and its result:**
  - Scratch tests in `docs/review/temp-tests/resolvers/test_scratch.py` passed (3 passed).
  - Executed `uv run pytest tests/rest_framework/test_resolvers.py --no-cov` (163 passed).
  - Executed `uv run pytest tests/rest_framework/ --no-cov` (447 passed).
  - Verified 100% statement coverage on `resolvers.py` (667/667 statements).
- **formatter and linter results:**
  - Executed `uv run ruff format .` and `uv run ruff check --fix .` (clean, 0 errors).
- **evidence for any rejected finding:**
  - No findings were rejected; the target is architecturally sound and free of defects.
- **whether the completed behavior merits a changelog entry:**
  - No (test additions only).

## Independent verification (Worker 2)

- **verification steps taken:**
  - Re-traced the pipeline lifecycle (`(update) locate -> authorize -> decode -> construct -> validate -> write -> re-fetch -> payload`), authorize-before-decode security invariant, input decoding, constructor-only hook kwargs merging and frozen hook views, schema/runtime agreement assertions, runtime write-source ownership enforcement, validator queryset pinning, relation-intent ledger tracking, ORM write witnessing, savepoint rollbacks, and depth/budget error flattening.
  - Verified `git diff 12779c99 -- django_strawberry_framework/rest_framework/resolvers.py` is zero-diff against baseline `HEAD`.
  - Audited new unit tests added in `tests/rest_framework/test_resolvers.py` for multi-nested item decoding, direct leaf error handling in the error flattener, and decode-step failure envelope mapping.
  - Executed inline scratch verification script exercising frozen hook view immutability, `_merged_serializer_kwargs` framework-managed key guards, and nested error path mapping.
  - Executed focused pytest runs (`tests/rest_framework/test_resolvers.py` -> 163 passed; `tests/rest_framework/` -> 447 passed) and verified 100% statement coverage (667/667 statements).
- **evidence confirming implementation matches understanding and findings:**
  - `git diff 12779c99 -- django_strawberry_framework/rest_framework/resolvers.py` is completely empty.
  - `uv run pytest tests/rest_framework/test_resolvers.py --no-cov` exited 0 with 163 passed.
  - `uv run pytest tests/rest_framework/ --no-cov` exited 0 with 447 passed.
  - `uv run pytest tests/rest_framework/test_resolvers.py -o "addopts=" --cov=django_strawberry_framework.rest_framework.resolvers --cov-report=term-missing` confirms 100% statement coverage.
  - `uv run ruff check .` passed with 0 errors.
- **whether all findings are addressed and tests pass:**
  - All findings are addressed, test coverage is 100%, and all tests pass cleanly.
- **final disposition: verified or revision-needed:**
  - `verified`.
