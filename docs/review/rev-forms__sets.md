# Review: `django_strawberry_framework/forms/sets.py`

Status: verified

## Understanding

`django_strawberry_framework/forms/sets.py` defines the base classes, `Meta` validation, declaration registries, and phase-2.5 bind hooks for form-backed GraphQL mutations (spec-038 Decision 6 / Decision 10 / Decision 13).

### Architectural Responsibilities and Invariants:

1. **Dual-Flavor Base Class Architecture**:
   - `DjangoModelFormMutation`: Subclasses `DjangoMutation` for `forms.ModelForm`-backed operations (`create` / `update`). Inherits the `DjangoMutation` metaclass, declaration registry (`_mutation_registry`), and primary `DjangoType` payload binding (`bind_mutations()`). Overrides model resolution (`form_class._meta.model`), input generation (`forms/inputs.py`), input namespace (`forms.inputs`), and delegates to `forms/resolvers.py` for sync/async execution.
   - `DjangoFormMutation`: Dedicated model-less base for plain `forms.Form` mutations with no backing model or `DjangoType` object slot. Carries its own metaclass (`DjangoFormMutationMetaclass`), disjoint declaration registry (`_form_mutation_declaration_registry`), and separate finalizer entrypoint (`bind_form_mutations()`) that materializes a pinned `{ ok, errors }` payload.

2. **Strict Class-Creation `Meta` Validation Matrices**:
   - **`DjangoModelFormMutation` Matrix**: Requires `form_class` (must subclass `forms.ModelForm`), resolvable model (must subclass `django.db.models.Model`), and `operation in {"create", "update"}` (`"delete"` rejected - no form delete pipeline). Validates `fields` / `exclude` via `resolve_effective_form_fields` and configures `permission_classes` (defaulting to `[DjangoModelPermission]`) and `select_for_update`.
   - **`DjangoFormMutation` Matrix**: Rejects any `Meta.operation` (own or inherited, including `None`), rejects `forms.ModelForm` subclasses with a targeted error directing consumers to `DjangoModelFormMutation`, requires `form_class` subclassing `forms.Form`, and rejects `DjangoModelPermission` (which requires a model). Unset `permission_classes` defaults to `[DenyAll]` (deny-by-default; explicit `permission_classes = []` for public access).

3. **Field Discovery and Customization Seams**:
   - `get_form_fields`: Classmethod hook resolving the stable field mapping at schema build time. Defaults to `get_form_fields(form_class)` reading frozen `_mutation_meta.form_class` (or live `Meta.form_class` during initial validation), with validation and normalization via `normalize_form_field_basis`.
   - `_form_kwargs_overridden` & Construction Waiver: Detects whether concrete subclasses override `get_form_kwargs` or `get_form`. When overridden, the create-required narrowing guard is waived because the consumer's hook is presumed to supply required omitted parameters.
   - `_default_get_form_kwargs` & `_default_get_form`: Shared module-level defaults utilizing `mutations/sets.py::construction_kwargs`, injecting `instance` only on updates with a non-`None` instance.
   - `perform_mutate`: Plain-form write hook executing `form.save()` if callable, or serving as an overridable customization point for arbitrary model-less side effects.

4. **Per-Pass Shape Build Caching & Deduping**:
   - `_form_shape_build_cache`: Per-pass shape cache keyed by `(form_class, operation_kind, frozenset(effective), hook_identity)`.
   - Ensures distinct mutation classes sharing identical form shapes reuse the same `@strawberry.input` class object, avoiding duplicate class collisions during materialization.
   - Runs narrowing required guards (`guard_create_required_fields` / `guard_partial_required_column_less_fields`) per declaration prior to cache lookup to prevent cache poisoning across waiving and non-waiving declarations.

5. **Phase-2.5 Finalizer Bind Integration**:
   - `bind_form_mutations`: Drains `iter_form_mutations()` through `bind_write_declarations`, clearing `_form_shape_build_cache`, building form inputs via `build_input`, and binding model-less payloads with `resolve_object_type = lambda _cls, _meta: None`.
   - Co-clears `clear_form_mutation_registry` and `clear_form_shape_build_cache` with `registry.clear()` via `register_subsystem_clear`.

## Verification

1. **Static and Structural Audit**:
   - Audited the complete implementation in `django_strawberry_framework/forms/sets.py` (1008 lines).
   - Traced integration with `mutations/sets.py`, `forms/inputs.py`, `forms/resolvers.py`, and `types/finalizer.py`.

2. **Existing Test Suite Audit**:
   - `tests/forms/test_sets.py`: 81 baseline tests covering class validation matrices, operation rules, allowed Meta keys, permission defaults, disjoint registry registration, phase-2.5 binding, retry idempotency, and form input dedupe.
   - `tests/forms/test_resolvers.py`: 60 tests covering sync/async execution and resolver pipeline integration.
   - `tests/forms/`: 234 total baseline tests passing.

3. **Scratch Experiments**:
   - Authored `docs/review/temp-tests/forms_sets/test_scratch_sets.py` probing:
     - `_ALLOWED_MODELFORM_META_KEYS` and `_ALLOWED_PLAIN_FORM_META_KEYS` sets.
     - `_default_mutation_get_form_fields` error handling with missing/None `Meta`.
     - `_form_kwargs_overridden` detection across base and overridden subclasses.
     - `_default_get_form` and `_default_get_form_kwargs` behavior with/without instance.
     - `input_type_name` derivation for `CREATE`, `PARTIAL`, and `FORM` sentinel operations.
     - `DjangoFormMutation.check_permission` and `perform_mutate` execution.
     - `_cached_build_form_input` for `PARTIAL` operations.
     - `bind_form_mutations` execution flow and output slot population.
   - All 8 scratch tests passed (100%).

4. **Focused Test Execution & Coverage**:
   - `uv run pytest tests/forms/test_sets.py --no-cov`: 84 passed (after adding permanent tests).
   - `uv run pytest tests/forms/ --no-cov`: 237 passed.
   - Statement coverage on `django_strawberry_framework.forms.sets`: 100% (152/152 statements).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/forms/sets.py` provides a clean, robust, and well-isolated foundation for Django Form and ModelForm mutations. It rigorously validates `Meta` configurations at class creation, maintains distinct registries for model-backed vs model-less mutations, correctly implements per-shape build deduplication with per-declaration required field guarding, and seamlessly integrates with the finalizer phase-2.5 bind.

## Implementation (Worker 1)

- **changed files and why each was necessary:**
  - `tests/forms/test_sets.py`: Added permanent tests pinning `input_type_name` derivation for both form mutation bases (`CREATE`, `PARTIAL`, `FORM`), `DjangoFormMutation.check_permission` write-auth walk, and `PARTIAL` `_cached_build_form_input` column-less required field guarding.
- **permanent tests and the behavior they pin:**
  - `test_input_type_name_seams`: Pins `input_type_name` returning canonical names (`<FormClass>Input`, `<FormClass>PartialInput`) across `DjangoModelFormMutation` and `DjangoFormMutation`.
  - `test_plain_form_check_permission_seam`: Pins `DjangoFormMutation.check_permission` executing the permission walk against `permission_classes`.
  - `test_cached_build_form_input_partial_column_less_guard`: Pins `_cached_build_form_input` executing `guard_partial_required_column_less_fields` on `PARTIAL` operations and building the partial input class.
- **scratch or focused verification and its result:**
  - Authored `docs/review/temp-tests/forms_sets/test_scratch_sets.py` (8 passed).
  - Executed `uv run pytest tests/forms/test_sets.py --no-cov` (84 passed).
  - Executed `uv run pytest tests/forms/ --no-cov` (237 passed).
  - Verified 100% statement coverage (152/152 statements) on `django_strawberry_framework.forms.sets`.
- **formatter and linter results:**
  - `uv run ruff format .`: Formatted, 0 errors.
  - `uv run ruff check --fix .`: All checks passed.
  - `uv run python scripts/check_trailing_commas.py --check tests/forms/test_sets.py`: Passed.
- **evidence for any rejected finding:** No findings were rejected; the production target is bug-free and conforms to all repository design specifications.
- **whether the completed behavior merits a changelog entry:** No (test suite strengthening; zero production code diff).

## Independent verification (Worker 2)

1. **Production zero-edit confirmation**:
   - `git diff 12779c99 -- django_strawberry_framework/forms/sets.py` is empty (zero edits against baseline `HEAD`).

2. **System Behavior & Architecture Verification**:
   - **Dual-Flavor Base Class Architecture**: Re-traced class creation and lifecycle across `DjangoModelFormMutation` and `DjangoFormMutation`. Confirmed model-backed mutations ride `DjangoMutation`, `_mutation_registry`, and phase-2.5 `bind_mutations()`, while plain form mutations ride `DjangoFormMutationMetaclass`, disjoint `_form_mutation_declaration_registry`, and phase-2.5 `bind_form_mutations()`.
   - **Disjoint Class-Creation Meta Validation Matrices**:
     - Confirmed `DjangoModelFormMutation` strictly validates `_ALLOWED_MODELFORM_META_KEYS`, requires `form_class` subclassing `forms.ModelForm`, resolves backed model from `form_class._meta.model`, enforces `operation in {"create", "update"}` (rejecting `"delete"`), validates field narrowing via `resolve_effective_form_fields`, and applies `DjangoModelPermission` and `select_for_update` defaults.
     - Confirmed `DjangoFormMutation` rejects `Meta.operation` presence outright, rejects `forms.ModelForm` with a targeted error directing consumers to `DjangoModelFormMutation`, requires `forms.Form`, rejects `DjangoModelPermission` subclasses, and defaults unset `permission_classes` to `[DenyAll]`.
   - **Per-Pass Shape Caching & Deduping**:
     - Verified `_cached_build_form_input` caching behavior keyed by `(form_class, operation_kind, frozenset(effective), hook_identity)`.
     - Confirmed the create-required-narrowing guard runs per declaration *before* cache lookup, preventing a waiving mutation from suppressing the guard on a subsequent non-waiving mutation reusing the same shape.
     - Confirmed `PARTIAL` operations execute `guard_partial_required_column_less_fields` while create/form operations execute `guard_create_required_fields`.
   - **Waiver Mechanics & Seams**:
     - Verified `_form_kwargs_overridden` correctly detects overrides of `get_form_kwargs` or `get_form` on subclasses relative to framework bases, waiving the create-required narrowing guard as specified in spec-038 Decision 7.
     - Confirmed `_default_get_form_kwargs` and `_default_get_form` pass `instance` only on updates with non-`None` instances.
     - Confirmed `perform_mutate` defaults to `form.save()` if callable or no-op.
     - Confirmed `check_permission` on `DjangoFormMutation` delegates to `run_permission_classes`.
   - **Phase-2.5 Finalizer Bind Integration**:
     - Verified `bind_form_mutations` drains `iter_form_mutations()`, stashes `_input_field_specs` and `_payload_type_name` (`<Name>Payload`), leaves `_primary_type = None`, and binds model-less output payloads.
     - Confirmed `clear_form_mutation_registry` and `clear_form_shape_build_cache` are registered for subsystem co-clearing with `registry.clear()`.

3. **Independent Challenge & Scratch Test Verification**:
   - Authored scratch tests probing:
     - ModelForm reject when passing a plain `forms.Form` (targeted message).
     - Plain Form reject when passing `forms.ModelForm` (targeted message).
     - Plain Form reject when `Meta.operation` is present (including `operation = None`).
     - Plain Form reject when `permission_classes` includes `DjangoModelPermission`.
     - ModelForm reject when `operation = "delete"`.
     - Shape cache guard isolation across waiving and non-waiving declarations.
     - Custom `get_form_fields` hook identity discriminator and Strawberry type name collision detection.
   - Executed `uv run pytest tests/forms/test_sets.py -W default --no-cov` (84 passed).
   - Executed `uv run pytest tests/forms/ -W default --no-cov` (237 passed).
   - Confirmed 100% statement coverage (152/152 statements) on `django_strawberry_framework.forms.sets`.

4. **Disposition of Findings**:
   - Zero findings or gaps remain. Target is sound, correct, well-tested, and verified complete.

