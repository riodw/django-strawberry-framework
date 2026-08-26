# Review: `django_strawberry_framework/forms/inputs.py`

Status: verified

## Understanding

`django_strawberry_framework/forms/inputs.py` is the pure, finalizer-free input generation substrate for `DjangoFormMutation` and `DjangoModelFormMutation` (spec-038 Decision 7).

### Key Responsibilities and Architecture:

1. **Uninstantiated Field Discovery (`get_form_fields`, `_form_field_basis`, `normalize_form_field_basis`)**:
   - Reads `form_class.base_fields` directly without calling `form_class()` so forms requiring `__init__` kwargs (e.g. `user`, `request`, tenant) have discoverable, request-independent input shapes.
   - Normalizes mutation hook-returned field mappings (`form_fields`) with typed diagnostics and fail-loud checks on non-mapping types, non-string keys, and non-`Field` values.

2. **Field Resolution and Narrowing (`resolve_effective_form_fields`)**:
   - Thin wrapper over `utils/inputs.py::resolve_effective_fields`, enforcing mutual exclusion between `fields` and `exclude`, rejecting bare strings and duplicate names, and failing loud on unknown field names or empty effective sets.

3. **Backing Column vs Model-Less Field Resolution (`_model_column_for`, `_field_triple_and_spec`)**:
   - For `ModelForm` subclasses, `_model_column_for` introspects `form_class._meta.model`.
   - Distinguishes forward concrete relations (`is_forward_concrete_relation`), forward concrete `ManyToManyField`s (`is_forward_many_to_many`), scalar/file columns, and column-less/virtual relations (`ForeignObjectRel`, `GenericForeignKey`, `GenericRelation`, non-concrete fields).
   - Column-backed fields route through `model_column_input_annotation` / `model_column_write_kind` from `mutations/inputs.py`, ensuring write-side/read-side type symmetry.
   - Column-less fields route through `forms/converter.py::convert_form_field` and `_model_less_relation_annotation` (delegating to `annotate_queryset_relation` with fail-loud diagnostics if `queryset is None` at class definition).
   - Generates `InputFieldSpec` records capturing `input_attr`, `graphql_name`, `target_name`, `kind` (`SCALAR`, `FILE`, `RELATION_SINGLE`, `RELATION_MULTI`), and `related_model`.

4. **Requiredness and Input Shaping (`build_form_input_class`, `build_form_inputs`)**:
   - Determines field requiredness via single-sited `forms/converter.py::form_field_required(field, column=column)`.
   - In create inputs (`CREATE`, `FORM`), required fields remain non-optional in GraphQL, while optional fields widen to `T | None` with `UNSET` default.
   - In partial inputs (`PARTIAL`), model-backed fields widen to `T | None` with `UNSET` default (reconstructed from row), while column-less extra fields preserve their declared `field.required` status (since they cannot be reconstructed from the database row).

5. **Narrowing and Collision Guards (`guard_create_required_fields`, `guard_partial_required_column_less_fields`, `_guard_input_attr_collisions`)**:
   - `guard_create_required_fields`: rejects dropping any required form field via `Meta.fields` / `Meta.exclude` unless waived via `guard_required=False`.
   - `guard_partial_required_column_less_fields`: rejects dropping required column-less form fields on partial/update inputs.
   - `_guard_input_attr_collisions`: delegates to `utils/inputs.py::iter_input_field_collisions` to fail loud on clashing input attributes (e.g. `target` -> `target_id` vs literal `target_id`) or collapsed camelCase GraphQL names (e.g. `foo_bar` vs `fooBar`).

6. **Namespace Lifecycle and Materialization (`make_input_namespace`, `materialize_form_input_class`, `clear_form_input_namespace`)**:
   - Maintains module global namespace under `django_strawberry_framework.forms.inputs` for lazy GraphQL type references.
   - Reuses identical input shapes idempotently and rejects colliding class names.
   - Registers `clear_form_input_namespace` with `register_subsystem_clear(owner="forms.input_namespace", before_bind=True)`.

## Verification

1. **Caller and Trace Audit**:
   - Traced callers across `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/forms/resolvers.py`, `django_strawberry_framework/forms/converter.py`, and `django_strawberry_framework/utils/inputs.py`.
   - Verified that `_cached_build_form_input` in `forms/sets.py` correctly coordinates `guard_create_required_fields`, `guard_partial_required_column_less_fields`, and `build_form_inputs`.
   - Verified that `InputFieldSpec` reverse-map attributes (`input_attr`, `target_name`, `kind`, `related_model`) align with `forms/resolvers.py` relation decoding and partial data reconstruction.

2. **Existing Test Suite Audit**:
   - Audited existing tests in `tests/forms/test_inputs.py` and `tests/forms/test_sets.py`.
   - Identified test coverage gaps on `normalize_form_field_basis` (`form_fields=None` and non-mapping basis types) and explicit `form_fields` parameter propagation.

3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/forms_inputs/test_scratch_basics.py`: verified basic field discovery, input generation, and materialization deduplication/collision.
   - Created `docs/review/temp-tests/forms_inputs/test_scratch_advanced.py`: verified advanced ModelForm column resolution (`ForeignKey`, `ManyToManyField`, `FileField`, `TextField`), column-less extra fields, requiredness differences in create vs partial inputs, and partial column-less narrowing guard.
   - All scratch tests passed (100%).

4. **Focused Test Execution**:
   - `uv run pytest tests/forms/test_inputs.py --no-cov`: 57 passed (51 baseline + 6 added tests).
   - `uv run pytest tests/forms/ --no-cov`: 234 passed.
   - `uv run pytest tests/forms/test_inputs.py -o "addopts=" --cov=django_strawberry_framework.forms.inputs --cov-report=term-missing`: 100% statement coverage (121/121 stmts).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/forms/inputs.py` is robust, well-factored, and strictly compliant with spec-038 Decision 7. It cleanly separates schema-time input generation from form instantiation, correctly dispatches model-backed versus model-less fields, enforces precise requiredness and narrowing guards, and maintains module-level materialization idempotency.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/forms/test_inputs.py`:
    - Added `test_inputs_module_path_and_kind_constants` testing `INPUTS_MODULE_PATH` and `CREATE_SHAPED_KINDS` exports.
    - Added `test_normalize_form_field_basis_rejects_none` testing fail-loud `ConfigurationError` when hook returns `None`.
    - Added `test_form_field_basis_rejects_non_mapping_source` testing fail-loud `ConfigurationError` on non-mapping basis values.
    - Added `test_normalize_form_field_basis_valid_mapping` testing valid hook basis normalization.
    - Added `test_build_form_inputs_with_custom_form_fields_basis` testing `build_form_inputs` with explicit `form_fields` argument.
    - Added `test_guard_create_required_fields_with_custom_form_fields` and `test_guard_partial_required_column_less_fields_with_custom_form_fields` testing requiredness guards with explicit `form_fields` basis.
- **Scoped diff against HEAD (`12779c99`):**
  - `django_strawberry_framework/forms/inputs.py`: empty (zero-edit cycle).
- **Permanent tests and pinned behavior:**
  - `tests/forms/test_inputs.py` (57 tests total):
    - Pins module constants (`INPUTS_MODULE_PATH`, `CREATE_SHAPED_KINDS`, `CREATE`, `FORM`, `PARTIAL`).
    - Pins uninstantiated `base_fields` discovery and `__init__` kwarg independence.
    - Pins basis normalization diagnostics and custom `form_fields` basis handling.
    - Pins create and partial input requiredness rules (model-backed fields widened in partial; column-less extra fields retain requiredness).
    - Pins `NullBooleanField` optionality across model-backed and model-less forms.
    - Pins relation ID generation (`GlobalID` for Relay targets, raw PK for non-Relay targets, `list[ID]` for multi-relations).
    - Pins `FileField` mapping to `Upload` with `FILE` kind.
    - Pins `ModelForm` choice fields reusing read-side enum types.
    - Pins `Meta.fields` and `Meta.exclude` narrowing, one-shot iterable freezing, and mutual exclusion.
    - Pins create-required and partial column-less required narrowing guards and waivers.
    - Pins input naming, deduplication ledger, and collision detection.
    - Pins attribute and camelCase collision guards.
    - Pins model column filtering against reverse relations, generic foreign keys, and generic relations.
    - Pins fail-loud error when `ModelChoiceField` queryset is `None` at class definition.
- **Scratch and focused verification:**
  - Scratch tests: `docs/review/temp-tests/forms_inputs/test_scratch_basics.py` and `test_scratch_advanced.py`.
  - Focused test suite: `uv run pytest tests/forms/test_inputs.py --no-cov` (57 passed), `tests/forms/` (234 passed).
  - Target coverage: 100% line coverage (121/121 statements).
- **Formatter and linter results:**
  - `uv run ruff format .` and `uv run ruff check --fix .`: passed cleanly.
- **Evidence for rejected findings:**
  - No findings were rejected; target implementation is fully sound and complete.
- **Changelog:**
  - Does not merit a changelog entry (zero-edit cycle with test suite additions).

## Independent verification (Worker 2)

1. **Production zero-edit confirmation**:
   - `git diff 12779c99 -- django_strawberry_framework/forms/inputs.py` is empty (zero changes to production source).

2. **System Behavior & Architecture Verification**:
   - **Discovery without Instantiation**: Verified `get_form_fields` reads `form_class.base_fields` directly without calling `form_class()`, allowing kwarg-requiring forms (`user`, `request`, etc.) to generate deterministic schema input types.
   - **Basis Normalization**: Verified `normalize_form_field_basis` fail-loud diagnostics on `None`, non-mappings, non-string keys, and non-`forms.Field` values.
   - **Column Identification & Filtering**: Verified `_model_column_for` correctly identifies forward concrete fields and M2Ms while cleanly discarding reverse relations (`ForeignObjectRel`), `GenericForeignKey`, and `GenericRelation`, falling back to the column-less scalar/relation conversion path.
   - **Input Attribute and Reverse Map Separation**: Verified `InputFieldSpec.target_name` consistently preserves the form's declared field name (required for bound form dict keys) while `input_attr` appropriately uses `_id` for relation fields.
   - **Requiredness Split**: Verified create inputs honor `form_field_required`, partial inputs force model-backed fields to optional (`| None` + `UNSET`), and column-less extra fields retain their declared `field.required` status on update.
   - **Narrowing & Requiredness Guards**: Verified `guard_create_required_fields` rejects dropped required fields unless waived via `guard_required=False`, and `guard_partial_required_column_less_fields` rejects dropped required column-less fields while allowing dropped model-backed fields.
   - **Collision Guards**: Verified `_guard_input_attr_collisions` detects both Python input attribute collisions (e.g. `foo` -> `foo_id` vs `foo_id`) and GraphQL camelCase collisions (e.g. `foo_bar` vs `fooBar`).
   - **Namespace Lifecycle & Clear**: Verified module-level materialization idempotency, collision detection on distinct class definitions, parked globals preservation on reset, and registration with `register_subsystem_clear(owner="forms.input_namespace", before_bind=True)`.

3. **Independent Scratch & Test Verification**:
   - Authored additional independent scratch test `docs/review/temp-tests/forms_inputs/test_independent_scratch_forms_inputs.py` covering column resolution branches, target name vs input attr separation, Relay vs non-Relay ID resolution, registry clear execution, and effective fields narrowing order.
   - Ran `uv run pytest docs/review/temp-tests/forms_inputs/ --no-cov`: 7 passed in 2.21s.
   - Ran `uv run pytest tests/forms/test_inputs.py --no-cov`: 57 passed in 1.81s.
   - Ran `uv run pytest tests/forms/ --no-cov`: 234 passed in 4.03s.
   - Verified 100% statement coverage (121/121 statements) on `django_strawberry_framework.forms.inputs`.

4. **Disposition of Findings**:
   - No findings or discrepancies were identified; implementation is verified complete, correct, and robust.

