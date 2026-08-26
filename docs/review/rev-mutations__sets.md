# Review: `django_strawberry_framework/mutations/sets.py`

Status: verified

## Understanding

`django_strawberry_framework/mutations/sets.py` defines the write-side declarative base, metaclass, `Meta` validation, declaration registry, and phase-2.5 bind substrate for GraphQL mutations (spec-036, spec-037, spec-038, spec-039, spec-040, spec-051):

1. **Declarative Surface & Metaclass**: Provides `DjangoMutation` and `DjangoMutationMetaclass` (constructed via `make_meta_validating_metaclass`). Concrete subclasses declare a nested `class Meta` (`model`, `operation`, `fields`, `exclude`, `input_class`, `partial_input_class`, `permission_classes`, `select_for_update`), which is validated at class creation time.
2. **Meta Validation Pipeline**: `DjangoMutation._validate_meta` audits declared keys against `_ALLOWED_MUTATION_META_KEYS` via `reject_unknown_meta_keys`, verifies model validity (`require_model_class`), operation semantics (`require_non_delete_operation` / valid operations set), mutual exclusion of `fields` and `exclude`, non-empty editable column sets (`editable_input_fields`), input class typing and naming scheme conformity (`_validate_input_class`), and permission/lock configuration (`model_backed_permission_and_lock`).
3. **Declaration Registry**: Provides `make_declaration_registry` managing identity-deduplicated mutation class registration (`_mutation_declaration_registry`, `register_mutation`, `clear_mutation_registry`, `iter_mutations`), rejecting post-finalization mutations and registering clearing hooks with `register_subsystem_clear`.
4. **Phase-2.5 Finalization Bind**: `bind_mutations` delegates to `bind_write_declarations`, which clears the per-pass shape build cache (`_shape_build_cache`), resolves primary `DjangoType`s for each model (`_resolve_primary_type`), generates and materializes input types (`_materialize_input_for` / `_materialize_merged_input`), shape-locks relation overrides (`_validate_relation_override_types`), and creates/materializes payload types (`bind_mutation_outputs`).
5. **Shared Write Foundations**: Exports foundational helpers reused by `forms/sets.py`, `rest_framework/sets.py`, and `auth/mutations.py`, including `COMMON_WRITE_META_KEYS`, `MODEL_BACKED_WRITE_META_KEYS`, `cached_build_input`, `build_and_stash_input`, `construction_kwargs`, `require_backing_class`, `require_subclass`, `resolve_meta_model`, `resolve_backed_model_or_raise`, and `resolver_seams`.

## Verification

1. **Existing Test Suite**: Ran `tests/mutations/test_sets.py` (102 tests) covering the full validation matrix (missing model, bad operations, typo keys, field collisions, empty fields, bare strings, hostile object representations, registration idempotency, deduplicated shape caches, and relation override type locks).
2. **Cross-Subsystem Tests**: Ran 374 tests across `tests/mutations/test_sets.py`, `tests/forms/test_sets.py`, `tests/rest_framework/test_sets.py`, and `tests/auth/test_mutations.py` to confirm interoperability across all write flavor subclasses and registries.
3. **Scratch Experiments**: Authored `docs/review/temp-tests/mutations_sets/test_scratch.py` validating union/optional relation override definitions (e.g. `list[relay.GlobalID] | None`, `relay.GlobalID | None`) and verifying flavor parameterization in permission validation diagnostics.

## Improvements

### High

None.

### Medium

None.

### Low

#### 1. Parameterize `_validate_permission_classes` with `base_label`

- **Observation:** `_validate_permission_classes` hardcoded `"DjangoMutation "` in its error messages when rejecting non-sequence inputs, un-iterable values, or classes lacking a callable `has_permission`, even when invoked by sibling write flavors like `DjangoModelFormMutation` or `DjangoFormMutation`.
- **Evidence:** `model_backed_permission_and_lock` takes a `flavor: str` parameter and passes it to `validate_select_for_update`, but did not forward it to `_validate_permission_classes`.
- **Impact:** Misleading diagnostic error prefix naming `DjangoMutation` for errors originating on other mutation flavors.
- **Recommendation:** Add optional `base_label: str = "DjangoMutation"` parameter to `_validate_permission_classes` and forward `base_label=flavor` from `model_backed_permission_and_lock`.
- **Proof:** Permanent test `test_validate_permission_classes_custom_base_label_and_flavor_forwarding` in `tests/mutations/test_sets.py`.

#### 2. Simplify payload construction in `bind_mutation_outputs`

- **Observation:** `bind_mutation_outputs` redundantly passed `object_slot=None if object_type is None else payload_object_slot(object_type)` to `build_payload_type`, which already defaults and derives `object_slot` automatically.
- **Evidence:** `mutations/inputs.py::build_payload_type` cleanly derives `payload_object_slot(object_type)` when `object_type` is provided.
- **Impact:** Redundant boilerplate at the bind call site.
- **Recommendation:** Omit the redundant `object_slot` ternary argument when calling `build_payload_type`.
- **Proof:** All bind unit and integration tests across `tests/mutations/test_sets.py` and `tests/forms/test_sets.py` pass cleanly.

## Summary

`django_strawberry_framework/mutations/sets.py` provides a robust, highly-factored write-side declarative and bind infrastructure with rigorous class-creation validation, deterministic deduplication, and secure relation override shape locking. Diagnostics were polished to respect caller flavor labels and payload construction was simplified.

## Implementation (Worker 1)

- **Changed files**:
  - `django_strawberry_framework/mutations/sets.py`: Added `base_label: str = "DjangoMutation"` parameter to `_validate_permission_classes`; forwarded `base_label=flavor` in `model_backed_permission_and_lock`; simplified `bind_mutation_outputs` by removing redundant explicit `object_slot` derivation when calling `build_payload_type`.
  - `tests/mutations/test_sets.py`: Added permanent unit test `test_validate_permission_classes_custom_base_label_and_flavor_forwarding`.
- **Permanent tests**:
  - `tests/mutations/test_sets.py::test_validate_permission_classes_custom_base_label_and_flavor_forwarding`: Pins `base_label` error prefix formatting for `_validate_permission_classes` and flavor forwarding in `model_backed_permission_and_lock`.
- **Verification**: Focused test runs across `tests/mutations/test_sets.py`, `tests/forms/test_sets.py`, `tests/rest_framework/test_sets.py`, and `tests/auth/test_mutations.py` (374 tests passed). Scratch test executed under `docs/review/temp-tests/mutations_sets/test_scratch.py`.
- **Formatter and linter**: `uv run ruff format .` and `uv run ruff check --fix .` passed cleanly with 0 errors.
- **Rejected findings**: None.
- **Changelog**: Does not merit a separate changelog entry (internal diagnostics and ergonomics refinement within unreleased cycle).

## Independent verification (Worker 2)

- **Trace paths and contracts verified**:
  - `DjangoMutationMetaclass` lifecycle and `make_meta_validating_metaclass`: verified concrete subclass validation, abstract base bypass when `Meta` is omitted, and idempotent registration into `_mutation_declaration_registry`.
  - `_validate_meta` validation pipeline: confirmed class-creation rejection of unknown `Meta` keys, non-model objects/strings, invalid operations, `fields` and `exclude` collisions, empty editable field projections, inapplicable input overrides for operation kinds, and non-conformant input shapes.
  - Permission classes and lock configuration: verified `_validate_permission_classes` correctly validates sequences of classes exposing `has_permission`, formats diagnostic messages using `base_label`, and respects flavor forwarding from `model_backed_permission_and_lock`.
  - Phase-2.5 bind substrate (`bind_mutations`, `bind_write_declarations`, `bind_mutation_outputs`): verified primary type resolution, shape cache clearing, materialized input class stashing, and payload synthesis with automatic object slot derivation (`build_payload_type`).
  - Relation override type/shape locking (`_validate_relation_override_types`): verified Relay Node primary relation overrides enforce `relay.GlobalID` core type and exact list depth matching (scalar for FK/OneToOne, 1-level list for M2M).
- **Checks against implementation & evidence**:
  - Inspected diff in `django_strawberry_framework/mutations/sets.py` and `tests/mutations/test_sets.py`.
  - Confirmed `base_label` parameter defaults cleanly to `"DjangoMutation"` while allowing sibling write flavors to pass custom labels.
  - Confirmed `build_payload_type` automatically resolves `payload_object_slot(object_type)` when `object_slot` is not passed.
- **Test execution**:
  - `tests/mutations/test_sets.py`: 103 passed.
  - Cross-subsystem test suites (`tests/forms/test_sets.py`, `tests/rest_framework/test_sets.py`, `tests/auth/test_mutations.py`): 271 passed (374 total across write flavor subsystems).
  - Scratch test `docs/review/temp-tests/mutations_sets/test_scratch.py`: 1 passed.
- **Outcome**: Verified. All behaviors, validation invariants, and bind lifecycle contracts are sound and well-tested.
