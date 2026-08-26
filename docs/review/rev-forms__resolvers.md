# Review: `django_strawberry_framework/forms/resolvers.py`

Status: verified

## Understanding

`django_strawberry_framework/forms/resolvers.py` implements the sync and async form-mutation resolver pipeline for `DjangoFormMutation` and `DjangoModelFormMutation` (spec-038 Decision 8).

### Architectural Responsibilities and Invariants:

1. **Pipeline Execution Lifecycle**:
   - The write pipeline follows the strict ordering:
     `(update) locate -> authorize -> decode -> construct + validate-once -> write -> (ModelForm) re-fetch -> payload`
   - **Authorize-before-decode security invariant**: Authorization executes prior to relation decoding so unauthorized callers cannot probe related-object existence or visibility via id errors vs auth denials.
   - Delegates the overarching transaction boundary, locate preamble, authorization ordering, and re-fetch tail to the promoted shared skeleton `mutations/resolvers.py::run_write_pipeline_sync`.

2. **Form-Field-Keyed Data & File Splitting (`_decode_form_data`)**:
   - Routes provided input attributes via `mutation_cls._input_field_specs` (`InputFieldSpec`).
   - Translates GraphQL input attributes into declared form field names (`spec.target_name`), separating scalar/relation data into `provided_data` and file uploads into `provided_files`.

3. **Relation Decoding & `to_field_name` Translation (`_decode_form_relation_single`, `_decode_form_relation_multi`, `_to_form_key_value`)**:
   - Drives relation ID decoding (supporting both Relay `GlobalID` and raw PK) through `utils/write_values.py::decode_visible_relation` and `utils/querysets.py::visible_related_object`.
   - Projects resolved relation models through `_to_form_key_value`, converting to `obj.serializable_value(to_field_name)` when `to_field_name` is set on `ModelChoiceField` / `ModelMultipleChoiceField`, or `obj.pk` otherwise.
   - Treats empty values (`None`, `""`, `[]`) safely via `_is_empty_form_value`, bypassing decoding so the form's own validation rules govern required vs optional clearing.
   - Rejects non-collection sequences (e.g. `str`, `bytes`, `Mapping`) in multi-relation inputs and short-circuits on the first invalid ID.

4. **Partial Update Reconstruction (`_reconstruct_partial_data`, `_modelform_decode_step`)**:
   - Because Django `ModelForm` lacks native `partial=True`, untouched declared form fields on partial updates are reconstructed from the located `instance`.
   - Excludes `forms.FileField` so untouched file fields preserve existing storage without corruption.
   - Reads omitted M2M relations via `.all()` and FK relations with `to_field_name` set, projecting them via `_to_form_key_value`.
   - Reads remaining omitted scalar and standard FK fields via `model_to_dict`.
   - Overlays `provided_data` on top so explicit user input takes precedence.

5. **Validation and Error Envelope Mapping (`_bound_form_or_field_errors`, `_form_errors_to_field_errors`)**:
   - Constructs the form via `holder.get_form(info, data=..., files=..., instance=...)` and validates once with `form.is_valid()`.
   - Converts `form.errors.as_data()` via `ValidationError(as_data())` through `utils/errors.py::validation_error_to_field_errors`, standardizing field errors and mapping `NON_FIELD_ERRORS` to `"__all__"`.

6. **Phased Write Execution (`_modelform_write_step`, `_plain_form_write_step`)**:
   - Form construction and validation execute outside the write phase (read-only enforcement under phased alias guard).
   - The write phase opens precisely inside `pipeline_write_phase()` for `form.save()` (in `DjangoModelFormMutation`) or `holder.perform_mutate(form, info)` (in `DjangoFormMutation`).
   - Wrapped in `save_or_field_errors` within nested savepoints to catch `ValidationError` and `IntegrityError` without leaking unhandled database exceptions.

7. **Resolver Entry Generation (`_run_form_pipeline_sync`, `resolve_form_sync`, `resolve_form_async`)**:
   - Dispatches model-backed vs model-less write steps.
   - Exposes sync and async entrypoints via `make_resolver_entries(_run_form_pipeline_sync)`, running async requests under a single `sync_to_async(thread_sensitive=True)` call.

## Verification

1. **Static and Contract Analysis**:
   - Audited the full implementation in `django_strawberry_framework/forms/resolvers.py` (619 lines).
   - Verified integration with `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/utils/write_values.py`, and `django_strawberry_framework/forms/sets.py`.

2. **Existing Test Suite Audit**:
   - `tests/forms/test_resolvers.py`: 60 tests covering sync/async execution, Relay and raw-pk relation decodes, `to_field_name` projections, partial updates, M2M handling, file uploads, write-auth ordering, error mapping, write phase boundaries, and async recourse errors.
   - `examples/fakeshop/test_query/test_products_api.py`: 22 tests validating form mutation endpoints against live GraphQL requests.

3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/forms_resolvers/test_scratch_resolvers.py` probing:
     - `_to_form_key_value` with custom `to_field_name`, `serializable_value` exceptions, and fallback to `pk`.
     - `_is_empty_form_value` boundary and unhashable type handling.
     - `_decode_form_relation_single` empty pass-through vs valid ID projection.
     - `_decode_form_relation_multi` empty collection handling vs non-collection / invalid element short-circuiting.
     - `_reconstruct_partial_data` field reconstruction and `provided_data` overlay.
     - `DjangoFormMutation` execution under `DjangoSchema` with `perform_mutate` and error reporting.
   - All 5 scratch tests passed (100%).

4. **Focused Test Execution**:
   - `uv run pytest tests/forms/test_resolvers.py --no-cov`: 60 passed.
   - `uv run pytest tests/forms/ --no-cov`: 234 passed.
   - `uv run pytest examples/fakeshop/test_query/test_products_api.py -k "form or Form" --no-cov`: 22 passed.
   - Coverage check: `uv run pytest tests/forms/test_resolvers.py -o "addopts=" --cov=django_strawberry_framework.forms.resolvers --cov-report=term-missing`: 100% statement coverage (125/125 statements).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/forms/resolvers.py` is fully sound, robust, and cohesive. It leverages the shared write pipeline skeleton (`run_write_pipeline_sync`), respects the authorize-before-decode invariant, properly handles `to_field_name` projections and empty-value bypass, ensures safe partial update reconstruction without file corruption, and strictly confines database writes to the pinned write phase.

## Implementation (Worker 1)

None — zero-edit cycle.
- **changed files and why each was necessary:** None (zero-edit cycle).
- **permanent tests and the behavior they pin:** Existing 60 tests in `tests/forms/test_resolvers.py` and 22 tests in `examples/fakeshop/test_query/test_products_api.py` fully pin relation decoding, `to_field_name` conversion, partial data reconstruction, auth-before-decode ordering, `_bound_form_or_field_errors` validation, write phase enforcement, error mapping, and sync/async dispatch with 100% statement coverage.
- **scratch or focused verification and its result:**
  - Authored `docs/review/temp-tests/forms_resolvers/test_scratch_resolvers.py` (5 passed).
  - Executed `uv run pytest tests/forms/test_resolvers.py --no-cov` (60 passed).
  - Executed `uv run pytest tests/forms/ --no-cov` (234 passed).
  - Executed `uv run pytest examples/fakeshop/test_query/test_products_api.py -k "form or Form" --no-cov` (22 passed).
  - Verified 100% statement coverage (125/125 statements).
- **formatter and linter results:** Not applicable (zero-edit cycle).
- **evidence for any rejected finding:** No findings were rejected; the target is architecturally sound, thoroughly tested, and bug-free.
- **whether the completed behavior merits a changelog entry:** No (zero-edit cycle).

## Independent verification (Worker 2)

1. **Production zero-edit confirmation**:
   - `git diff 12779c99 -- django_strawberry_framework/forms/resolvers.py` is empty (zero edits against baseline `HEAD`).

2. **System Behavior & Architecture Verification**:
   - **Pipeline Lifecycle & Skeleton Integration**: Re-traced the complete execution lifecycle (`locate` -> `authorize` -> `decode` -> `construct + validate` -> `write` -> `refetch` -> `payload`). Verified clean integration with promoted skeleton `mutations/resolvers.py::run_write_pipeline_sync`.
   - **Authorize-Before-Decode Security Invariant**: Confirmed authorization runs prior to relation decoding so unauthorized callers cannot probe relation existence or visibility.
   - **Relation Decoding & to_field_name Translation**: Verified `_decode_form_relation_single`, `_decode_form_relation_multi`, and `_to_form_key_value`. Confirmed Relay GlobalID and raw PK support, type checking, visibility checking via `DjangoType.get_queryset`, `to_field_name` projection via `serializable_value` (with fallback to `pk` on `FieldDoesNotExist` / `AttributeError`), and safe bypass of empty values (`None`, `""`, `[]`) via `_is_empty_form_value`.
   - **Multi-Relation Decoding**: Verified non-collection sequences (`str`, `bytes`, `Mapping`) are rejected with `FieldError`, empty collections return `[]`, and invalid elements short-circuit on the first error.
   - **Partial Update Reconstruction**: Verified `_reconstruct_partial_data` reconstructs untouched declared form fields from the located instance using `model_to_dict` for scalars and plain FKs, and `_to_form_key_value` for M2M relations and FKs with `to_field_name`. Confirmed `forms.FileField` / `forms.ImageField` are excluded from reconstruction so existing storage remains uncorrupted.
   - **Single-Pass Validation & Envelope Error Mapping**: Verified `_bound_form_or_field_errors` runs `form.is_valid()` once and maps `form.errors.as_data()` via `_form_errors_to_field_errors` (`validation_error_to_field_errors`), mapping `NON_FIELD_ERRORS` to `"__all__"`.
   - **Phased Write Execution**: Verified writes are strictly confined to `pipeline_write_phase()` under `save_or_field_errors`, properly mapping `IntegrityError` to `"A database constraint was violated."` without database error leakage.
   - **Entrypoint Generation**: Verified `resolve_form_sync` and `resolve_form_async` via `make_resolver_entries`, running async executions under a single `sync_to_async(thread_sensitive=True)` thread boundary.

3. **Independent Challenge & Scratch Test Verification**:
   - Authored `docs/review/temp-tests/forms_resolvers/test_worker2_challenge.py` probing:
     - `_is_empty_form_value` exception safety with unhashable objects raising `TypeError` on comparison.
     - `_to_form_key_value` handling of custom `to_field_name`, `serializable_value` exceptions (`FieldDoesNotExist`, `AttributeError`), and objects without `pk`.
     - `_decode_form_relation_single` empty bypass and invalid raw PK handling.
     - `_decode_form_relation_multi` generator input handling and multi-element short-circuiting.
     - `_reconstruct_partial_data` comprehensive test with `FileField`, `ImageField`, and scalar overlay.
     - `_form_errors_to_field_errors` mapping with non-field errors mapped to `"__all__"`.
     - `_modelform_write_step` under `managed_write_transaction` and `open_write_pipeline` with `IntegrityError` sanitized envelope mapping.
   - Ran `uv run pytest docs/review/temp-tests/forms_resolvers/ --no-cov`: 11 passed (5 Worker 1 scratch + 6 Worker 2 challenge).
   - Ran `uv run pytest tests/forms/test_resolvers.py --no-cov`: 60 passed.
   - Ran `uv run pytest tests/forms/ --no-cov`: 234 passed.
   - Ran `uv run pytest examples/fakeshop/test_query/test_products_api.py -k "form or Form" --no-cov`: 22 passed.
   - Confirmed 100% statement coverage (125/125 statements).

4. **Disposition of Findings**:
   - Zero findings or gaps remain. Target is sound, correct, well-tested, and verified complete.

