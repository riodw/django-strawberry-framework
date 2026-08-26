# Review: django_strawberry_framework/forms/

Status: verified

## Understanding

### Purpose & Architecture
The `django_strawberry_framework/forms/` subpackage implements a robust, secure, and idiomatic bridge between standard Django Form / ModelForm classes and Strawberry GraphQL mutation operations (`spec-038`). It exposes a dual-flavor base architecture supporting both model-backed (`DjangoModelFormMutation`) and model-less (`DjangoFormMutation`) mutations, automatically materializing Strawberry input types, resolving relation fields, executing phased validation and writes, enforcing fine-grained authorization, and returning typed GraphQL payloads with structured error envelopes.

The subpackage comprises 5 tightly cohesive modules organized into a clean 5-layer pipeline:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer 5: Public API & Declarations (__init__.py, sets.py)                   │
│   • Re-exports: DjangoFormMutation, DjangoModelFormMutation                 │
│   • Metaclasses: DjangoFormMutationMetaclass, DjangoMutationMetaclass       │
│   • Registries: _form_mutation_declaration_registry, _mutation_registry     │
│   • Seams: get_form_fields, get_form_kwargs, get_form, perform_mutate       │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 4: Phase 2.5 Schema Finalization & Binding (sets.py)                  │
│   • bind_form_mutations() / bind_mutations() integration                    │
│   • Shape generation & caching: _form_shape_build_cache                     │
│   • Return payload typing: { ok, errors } vs { node/result, errors }        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 3: Finalizer-Free Input Materialization (inputs.py)                   │
│   • Form field discovery: get_form_fields (uninstantiated base_fields)      │
│   • Basis normalization: normalize_form_field_basis                         │
│   • Narrowing guards: guard_create_required_fields, guard_partial_required   │
│   • Global namespace: django_strawberry_framework.forms.inputs             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 2: Resolver Execution Pipeline (resolvers.py)                         │
│   • Sync / Async pipeline: run_write_pipeline_sync / run_write_pipeline_async│
│   • Authorize-before-decode security invariant                              │
│   • Relation decoding: _decode_form_relation_single / multi with visibility  │
│   • Partial reconstruction: _reconstruct_partial_data                       │
│   • Phased write containment: pipeline_write_phase() (read-only validation)  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 1: Form Field Converter & Requiredness Registry (converter.py)        │
│   • Conversion registry: convert_form_field, convert_with_mro               │
│   • Precheck kinds: RELATION_MULTI, RELATION_SINGLE, FILE, SCALAR           │
│   • Requiredness authority: form_field_required (is_explicit_empty_form_val)│
│   • Fail-loud diagnostic: ConfigurationError on unsupported form fields     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dual-Flavor Base Class Symmetry
1. **`DjangoModelFormMutation` (Model-backed)**:
   - Inherits from `DjangoMutation` in `mutations/sets.py`.
   - Requires `Meta.form_class` (must be `forms.ModelForm`) and `Meta.operation` (`"create"` or `"update"`).
   - Resolves target model from `form_class._meta.model` via `resolve_meta_model`.
   - Defaults permissions to `[DjangoModelPermission]` targeting the underlying Django model.
   - Generates typed payloads with `node` (for `relay.Node`) or `result` (for non-Relay) plus `errors: list[FieldError]`.
   - Handled during schema finalization via `mutations/sets.py::bind_mutations()`.
2. **`DjangoFormMutation` (Model-less / Plain Form)**:
   - Inherits directly from `object` with `DjangoFormMutationMetaclass`.
   - Requires `Meta.form_class` (must be `forms.Form`, explicitly rejecting `forms.ModelForm`).
   - Forbids `Meta.operation` (`ConfigurationError`).
   - Defaults permissions to `[DenyAll]` (secure fail-closed default; rejects `DjangoModelPermission`).
   - Generates standardized payloads `{ ok: bool, errors: list[FieldError] }`.
   - Handled during schema finalization via `forms/sets.py::bind_form_mutations()`.

### Cross-Module & External Layer Integration
- **`sets.py` -> `inputs.py`**: `sets.py` invokes `build_form_input_shape()` to generate input shapes, fields, and materialized Strawberry input classes (`*Input` / `*PartialInput`).
- **`inputs.py` -> `converter.py`**: `inputs.py` queries `convert_form_field()` to map Django form fields to Strawberry type annotations, scalar bindings, or enum wrappers, and uses `form_field_required()` to compute GraphQL non-null status.
- **`resolvers.py` -> `inputs.py` & `converter.py`**: `resolvers.py` uses `_decode_form_data()` to inspect input field metadata, split inputs into `provided_data` and `provided_files` (via `Upload` markers), decode relations, and run partial row reconstruction.
- **`types/finalizer.py` (Phase 2.5)**: Coordinates schema-wide binding by invoking `bind_form_mutations()` alongside `bind_mutations()` and `bind_filtersets()`, ensuring all mutation input classes and payload types are materialized and frozen before schema construction.
- **`mutations/fields.py` (`DjangoMutationField`)**: Duck-types mutation targets via `_has_mutation_protocol()` and `_is_registered_mutation_target()`, supporting both `DjangoModelFormMutation` and `DjangoFormMutation` transparently without creating circular imports.
- **`utils/write_transaction.py`**: Provides `pipeline_write_phase()` context manager, guaranteeing that form construction and `is_valid()` clean execution happen in a read-only phase, while database writes (`form.save()` or `perform_mutate()`) execute strictly within an active write phase.

### Security, Phase & Lifecycle Invariants
1. **Authorize-Before-Decode Invariant**: Permission checks (`check_permission` / `permission_classes`) execute *before* any relation decoding (`_decode_form_relation_single`, `_decode_form_relation_multi`) or partial row lookups. This prevents unauthenticated or unauthorized clients from probing entity existence or leaking primary keys via relation resolution errors.
2. **Phased Write Containment Invariant**: Validation (`form.is_valid()`) runs in read-only mode where write SQL triggers `WritePhaseViolationError`. Only `form.save()` (in `DjangoModelFormMutation`) or `perform_mutate()` (in `DjangoFormMutation`) executes inside `pipeline_write_phase()`.
3. **Narrowing Required Guards**: In `inputs.py`, `guard_create_required_fields` prevents `Meta.fields` narrowing from dropping required form fields unless the author explicitly overrides `get_form_kwargs` or `get_form` (detected via `_form_kwargs_overridden`). In partial updates, `guard_partial_required_column_less_fields` ensures required non-model extra fields cannot be omitted from `*PartialInput`.
4. **Visibility-Scoped Relation Resolution**: Relation inputs (`ModelChoiceField`, `ModelMultipleChoiceField`) are verified against the related target's primary `DjangoType.get_queryset(info)` via `visible_related_object` on *every* branch (Relay GlobalID and raw-pk, single and multi), completely eliminating ID enumeration vulnerabilities.
5. **Partial Update Reconstruction Invariant**: Partial updates reconstruct complete form data by combining untouched model instance fields via `_to_form_key_value` (with `serializable_value` and `to_field_name` awareness) with user-provided fields, allowing Django's clean methods and unique constraints to validate accurately against full state without discarding uploaded files.
6. **Namespace & Registry Lifecycle Invariant**: Input classes materialized in `django_strawberry_framework.forms.inputs` and cached shapes in `_form_shape_build_cache` / `_form_mutation_declaration_registry` register teardown hooks with `register_subsystem_clear()`, guaranteeing deterministic, isolated clearing upon `registry.clear()`.

---

## Verification

### Mapping of Callers & Consumers
- **Schema Authors & Public API**: Import `DjangoFormMutation` and `DjangoModelFormMutation` directly from `django_strawberry_framework`.
- **`types/finalizer.py`**: Invokes `bind_form_mutations()` during Phase 2.5 type finalization.
- **`mutations/fields.py`**: Wraps both form mutation flavors into Strawberry mutation fields via `DjangoMutationField`.
- **`examples/fakeshop` & Integration Suite**: Live test coverage exercising multipart upload (`Upload`), ModelForm creates/updates, relation resolution, partial update preservation, and plain form submission over HTTP transport.

### Prior Per-File Review Findings Reconciliation
All 4 component file review passes have been completed and independently verified:
- `docs/review/rev-forms__converter.md`: Verified conversion registry, MRO walk, precheck kinds, requiredness rules, and fail-loud `ConfigurationError` handling.
- `docs/review/rev-forms__inputs.md`: Verified finalizer-free input generation, basis normalization, narrowing required guards, attribute collision guards, and module global namespace lifecycle.
- `docs/review/rev-forms__resolvers.md`: Verified sync/async resolver pipelines, authorize-before-decode invariant, relation visibility decoding, partial reconstruction, and phased write containment.
- `docs/review/rev-forms__sets.md`: Verified dual-flavor base classes, disjoint `Meta` validation matrices, registry hooks, shape build caching, and phase-2.5 binding coordination.

### Scratch Experiments & Suite Results
- **Scratch Integration Testing** (`docs/review/temp-tests/forms/test_scratch_integration.py`):
  - Created end-to-end test schema with `DjangoModelFormMutation` (create, partial update) and `DjangoFormMutation` (plain form execution and validation failure envelope).
  - Verified `Meta` validation matrices (rejection of `ModelForm` in plain `DjangoFormMutation`, rejection of `operation` in plain `DjangoFormMutation`, rejection of `operation="delete"` in `DjangoModelFormMutation`).
  - Verified subsystem registry clearing and shape build cache lifecycle.
  - Executed under `uv run pytest docs/review/temp-tests/forms/test_scratch_integration.py --no-cov`: **3 passed in 5.19s**. Scratch files cleanly cleaned up.
- **Subpackage Test Suite**:
  - `uv run pytest tests/forms/ --no-cov`: **237 passed in 5.95s**.
- **Integration Test Suite (Fakeshop API)**:
  - `uv run pytest examples/fakeshop/test_query/ -k "form or Form" --no-cov`: **51 passed, 1 skipped in 29.40s**.

---

## Improvements

### High
- None.

### Medium
- None.

### Low
- None.

---

## Summary
The `django_strawberry_framework/forms/` subpackage is an exceptionally engineered, secure, and clean component. The dual-flavor mutation architecture (`DjangoModelFormMutation` and `DjangoFormMutation`) provides symmetric, well-typed mutation semantics with strict compile-time `Meta` validation matrices. The resolver pipeline enforces critical security invariants including authorize-before-decode, phased write containment, and visibility-scoped relation decoding across all branches. The input generation substrate accurately captures uninstantiated form definitions and guards against unsafe required-field narrowing. All 237 subsystem tests and 51 end-to-end integration tests pass cleanly. Zero production edits are required for this folder pass.

---

## Implementation (Worker 1)

### Changed Files
- `None — zero-edit cycle` (target subpackage files in `django_strawberry_framework/forms/` are in pristine condition against baseline `12779c99`).

### Permanent Tests and Pinned Behavior
- Pinned behavior is comprehensively tested across `tests/forms/`:
  - `tests/forms/test_converter.py`: Form field conversion, MRO resolution, requiredness rules, unsupported field diagnostics.
  - `tests/forms/test_inputs.py`: Form input shape generation, uninstantiated field discovery, narrowing guards, collision guards, namespace lifecycle.
  - `tests/forms/test_resolvers.py`: Sync/async write pipelines, authorize-before-decode, relation visibility checks, multipart file split, partial update reconstruction, read-only validation enforcement.
  - `tests/forms/test_sets.py`: Dual-flavor mutation declarations, disjoint Meta matrices, hook overrides, shape cache isolation, phase 2.5 binding.
  - `examples/fakeshop/test_query/test_products_api.py` & `test_uploads_api.py`: Live HTTP multipart uploads, partial updates, and plain form mutations.
- Total test count: 237 passing tests in `tests/forms/` and 51 passing tests in `examples/fakeshop/test_query/`.

### Scoped Diff
```
0 files changed, 0 insertions(+), 0 deletions(-)
```

### Linter & Formatter
- Subpackage files are clean under `ruff check` and `ruff format`.

### Release Note Merit
- No release note required for zero-edit folder pass.

---

## Independent verification (Worker 2)

- **System behavior re-traced:**
  - Audited full dual-flavor base architecture (`DjangoModelFormMutation` model-backed and `DjangoFormMutation` model-less / plain form).
  - Verified cross-module contracts across `converter.py`, `inputs.py`, `resolvers.py`, and `sets.py`:
    - `converter.py`: Form field MRO dispatch, precheck kinds (`RELATION_MULTI`, `RELATION_SINGLE`, `FILE`, `SCALAR`), and requiredness authority via `form_field_required`.
    - `inputs.py`: Form input shape materialization (`*Input` / `*PartialInput`), uninstantiated field discovery, basis normalization, and narrowing guards (`guard_create_required_fields`, `guard_partial_required_column_less_fields`).
    - `resolvers.py`: Sync/async resolver pipelines, authorize-before-decode security invariant, visibility-scoped relation decoding across all branches, partial update data reconstruction, and phased write containment via `pipeline_write_phase()`.
    - `sets.py`: Compile-time `Meta` validation matrices, registry hooks, shape build caching (`_form_shape_build_cache`), and phase 2.5 type finalization / schema binding coordination (`bind_form_mutations()`).
  - Confirmed subpackage lifecycle invariants: `registry.clear()` co-clears `_form_mutation_declaration_registry`, `_form_shape_build_cache`, and `django_strawberry_framework.forms.inputs` materialization ledgers cleanly and deterministically.

- **Zero-edit confirmation:**
  - Scoped diff against baseline `HEAD` (`12779c99`):
    `git diff 12779c99 -- django_strawberry_framework/forms/` is empty (0 insertions, 0 deletions across 0 files). Zero-edit confirmed.

- **Independent scratch experiments:**
  - Executed independent scratch tests in `docs/review/temp-tests/forms/` challenging cross-module integration:
    - Verified `DjangoModelFormMutation` and `DjangoFormMutation` subclass creation and `Meta` validation.
    - Verified `DeclarationRegistry` store and registration ordering via `iter_form_mutations()`.
    - Verified Phase 2.5 schema finalization binding inputs (`ContactFormInput`, `ItemFormInput`) and payload types (`SubmitContactMutationPayload` with `{ ok, errors }` vs `CreateItemMutationPayload` with `{ node, errors }`).
    - Verified full subsystem registry clearing and cache teardown isolation.
    - All scratch tests passed; temporary scratch files removed.

- **Permanent test suite execution:**
  - `uv run pytest tests/forms/ --no-cov`: **237 passed in 7.30s**.
  - `uv run pytest examples/fakeshop/test_query/ -k "form or Form" --no-cov`: **51 passed, 1 skipped in 44.42s**.

- **Findings disposition:**
  - No defects or regressions found. The subpackage implementation is solid, complete, and verified.

