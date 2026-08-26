# Review: `django_strawberry_framework/mutations/operations.py`

Status: verified

## Understanding

`django_strawberry_framework/mutations/operations.py` serves as the single authoritative source of truth for write-side mutation operation vocabulary and descriptors (spec-036, spec-038, spec-039):

1. **Operation Descriptors**: Defines the frozen, slotted dataclass `MutationOperationDescriptor` capturing per-operation invariants (`name`, `input_kind`, `input_override_attr`, `has_id_arg`, `has_data_arg`, `permission_action`, `supports_model_mutation`, `supports_form_mutation`).
2. **Canonical Operation Instances**: Singletons `OPERATION_CREATE`, `OPERATION_UPDATE`, `OPERATION_DELETE`, and `OPERATION_FORM` define the exact properties of standard mutation types and plain form operations.
3. **Lookup Registry & Argument Predicates**: Maintains `_OPERATIONS_BY_NAME` and provides `get_operation_descriptor(name)`, `operation_takes_id(name)`, and `operation_takes_data(name)` for schema generation and execution checks.
4. **Derived Constants**: Single-sources derived lookup structures:
   - `NON_DELETE_OPERATION_INPUT_KIND`: Maps `"create"` -> `CREATE` and `"update"` -> `PARTIAL`.
   - `_OPERATION_INPUT_OVERRIDE_ATTR`: Maps `"create"` -> `"input_class"` and `"update"` -> `"partial_input_class"`.
   - `NON_DELETE_WRITE_OPERATIONS`: `frozenset({"create", "update"})` representing the operations supported across model, form, and serializer mutation flavors.
   - `_VALID_OPERATIONS`: `frozenset({"create", "update", "delete"})` representing supported model-flavor operations.
   - `_OPERATION_PERMISSION_ACTION`: Maps operations to Django permission codenames (`"add"`, `"change"`, `"delete"`).
5. **Shared Diagnostic Builder**: `non_delete_operation_error(base_label, name, got)` standardizes error reporting across `DjangoModelFormMutation` and `SerializerMutation` when `delete` or an invalid operation is configured on a flavor that lacks delete pipeline support.
6. **Integration & Callers**:
   - `django_strawberry_framework/mutations/fields.py`: Uses `operation_takes_id` and `operation_takes_data` to synthesize GraphQL field argument signatures.
   - `django_strawberry_framework/mutations/permissions.py`: Uses `_OPERATION_PERMISSION_ACTION` to look up the required model permission action codename.
   - `django_strawberry_framework/mutations/resolvers.py`: Uses `operation_takes_id` to determine whether instance location (`needs_locate`) is required prior to authorization and execution.
   - `django_strawberry_framework/mutations/sets.py`: Uses `_VALID_OPERATIONS`, `_OPERATION_INPUT_OVERRIDE_ATTR`, `NON_DELETE_OPERATION_INPUT_KIND`, `NON_DELETE_WRITE_OPERATIONS`, and `non_delete_operation_error` for `Meta` validation and input dispatch.
   - `django_strawberry_framework/forms/sets.py` & `django_strawberry_framework/rest_framework/sets.py`: Import `NON_DELETE_OPERATION_INPUT_KIND` and share `require_non_delete_operation`.

## Verification

1. **Test Suite Analysis**: Examined `tests/mutations/test_operations.py` (7 tests) covering:
   - Immutability of `MutationOperationDescriptor` (frozen dataclass validation).
   - Invariants of `OPERATION_CREATE`, `OPERATION_UPDATE`, `OPERATION_DELETE`, `OPERATION_FORM`.
   - Resolution via `get_operation_descriptor` for valid, invalid, and empty strings.
   - Argument presence predicates `operation_takes_id` and `operation_takes_data`.
   - Derived mappings and frozensets (`NON_DELETE_OPERATION_INPUT_KIND`, `_OPERATION_INPUT_OVERRIDE_ATTR`, `NON_DELETE_WRITE_OPERATIONS`, `_VALID_OPERATIONS`, `_OPERATION_PERMISSION_ACTION`).
   - Formatting and hostile `__repr__` resilience in `non_delete_operation_error`.
2. **Focused & Coverage Runs**:
   - `uv run pytest tests/mutations/test_operations.py --cov=django_strawberry_framework.mutations.operations`: 7 passed, 100% line coverage (35/35 lines covered, 0 missed).
   - `uv run pytest tests/mutations/ --no-cov`: 336 passed across all mutation subsystem tests.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/mutations/operations.py` provides a clean, well-factored, immutable single source of truth for mutation operations across all write flavors. All invariants are rigorously tested with 100% coverage, and no defects or design improvements were identified.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Scoped diff against cycle baseline HEAD (12779c99)**: Empty (no source or test modifications needed).
- **Justification**: Target is completely sound, fully covered (100% line coverage across 7 dedicated tests in `tests/mutations/test_operations.py`), and correctly integrated with all callers across `mutations`, `forms`, and `rest_framework`.
- **Permanent tests**: Existing suite in `tests/mutations/test_operations.py` pins all descriptors, lookups, predicates, and error handling.
- **Verification**: Focused pytest run passed 7/7 tests with 100% coverage on `operations.py`. Full `tests/mutations/` suite passed 336/336 tests.
- **Formatter & linter**: Unchanged files; no formatting or linting changes required.
- **Rejected findings**: None.
- **Changelog**: Does not merit a changelog entry (zero-edit cycle).

## Independent verification (Worker 2)

- **Scoped diff verification**: Checked `git diff 12779c99 -- django_strawberry_framework/mutations/operations.py`; diff is completely empty (zero-edit cycle confirmed).
- **Behavior re-tracing**:
  - Validated `MutationOperationDescriptor` dataclass invariants across `OPERATION_CREATE`, `OPERATION_UPDATE`, `OPERATION_DELETE`, and `OPERATION_FORM` descriptors.
  - Validated argument predicate dispatch (`operation_takes_id`, `operation_takes_data`) used by `mutations/fields.py` and `mutations/resolvers.py`.
  - Validated permission action mappings (`_OPERATION_PERMISSION_ACTION`) used by `mutations/permissions.py`.
  - Validated input kind and override mappings (`NON_DELETE_OPERATION_INPUT_KIND`, `_OPERATION_INPUT_OVERRIDE_ATTR`, `NON_DELETE_WRITE_OPERATIONS`, `_VALID_OPERATIONS`) referenced by `mutations/sets.py`, `forms/sets.py`, and `rest_framework/sets.py`.
  - Validated `non_delete_operation_error` diagnostic formatting including unprintable repr handling.
- **Test execution**: Executed `uv run pytest tests/mutations/test_operations.py --no-cov` (7 passed in 3.55s).
- **Conclusion**: Implementation is robust, correctly single-sources mutation descriptor invariants, and satisfies all architectural constraints. Status set to `verified`.
