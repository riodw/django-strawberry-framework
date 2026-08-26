# Review: `django_strawberry_framework/utils/input_values.py`

Status: verified

## Understanding

`django_strawberry_framework/utils/input_values.py` is the single centralized owner for runtime input value traversal and classification across set families (`FilterSet` and `OrderSet`) and permission walkers (`utils/permissions.py`):

1. **Active Value Decision (`is_inactive_value`)**:
   - Evaluates whether a supplied value represents "not supplied" via strict identity checks: `value is None or value is unset_sentinel`.
   - Distinguishes identity from truthiness so that falsy values (`0`, `""`, `False`, `[]`, `{}`) remain active.
   - Filter sets configure `unset_sentinel=strawberry.UNSET`, while order sets use `unset_sentinel=None`.

2. **Dict vs. Dataclass Introspection (`iter_input_items` and `input_field_value`)**:
   - `iter_input_items` inspects either native/custom `dict` instances (bypassing subclass `items()` overrides with `dict.items`) or Strawberry input dataclasses (`__dataclass_fields__` mapping).
   - `input_field_value` performs single-field lookup safely using `dict.get` or `getattr(..., default=None)`.
   - String key sanitization via `_field_name` uses `str.__str__(value)` to bypass hostile subclass `__str__` overrides and rejects non-string keys with `ConfigurationError`.
   - Malformed or hostile dataclass metadata (unreadable properties, non-mapping `__dataclass_fields__`, unreadable fields) fails closed with typed `ConfigurationError`.

3. **Neutral Traversal and Classification (`iter_active_fields`, `SetInputTraversal`, `ActiveField`)**:
   - Iterates active top-level fields configured via `SetInputTraversal`.
   - Classifies each field mutually exclusively into:
     - `LOGIC` (e.g. `and_`, `or_`, `not_` keys in `config.logic_keys`)
     - `RELATED` (attribute matches `set_cls.<related_attr>` mapping)
     - `LEAF` (standard scalar / operator field)
   - Resolves `FieldSpec` provenance from `config.field_specs`.
   - Handles order-side top-level list inputs (`handle_top_level_list=True`) by flattening elements and failing closed on non-mapping or nested list values.
   - Preserves recursion ceiling constant `DEFAULT_SET_INPUT_TRAVERSAL_DEPTH = 8`.

## Verification

1. **Call-site and Contract Tracing**:
   - Traced all consumers: `filters/sets.py` (`FilterSet._normalize_input`), `orders/inputs.py` (`normalize_input_value`), `filters/inputs.py`, `sets_mixins.py`, and `utils/permissions.py` (`extract_branch_value`, `active_permission_field_paths`, `active_related_branches`).
   - Verified that the classification order, active-input rules, and exception wrappers are strictly respected without drifting between subsystems.
2. **Existing Test Review**:
   - Reviewed `tests/utils/test_input_values.py` (18 initial tests) and related consumer suites in `tests/filters/test_inputs.py`, `tests/orders/test_inputs.py`, and `tests/utils/test_permissions.py`.
3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/utils_input_values/test_scratch.py` probing edge cases: `_field_name` with hostile string subclasses, `_walk_error` formatting, `iter_input_items` on primitives and empty dicts, `input_field_value` on missing fields and non-walkable objects, `is_inactive_value` truthiness matrix, and `iter_active_fields` list rejection. Executed via `uv run pytest docs/review/temp-tests/utils_input_values/test_scratch.py --no-cov` (7 passed).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/utils/input_values.py` provides a unified, robust, and fail-closed traversal substrate for Strawberry input dataclasses and dictionaries. Active value classification, provenance lookup, error containment, and hostile subclass defenses operate correctly without leaks or drift across set families.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/utils/test_input_values.py`: Added permanent unit tests covering single-field extraction on dicts/dataclasses/non-walkable inputs (`test_input_field_value_reads_dict_and_dataclass_fields`), hostile `str` subclass key normalization bypassing `__str__` overrides (`test_field_name_bypasses_hostile_str_subclass_str_override`), and primitive element rejection in order input lists (`test_order_list_elements_reject_primitive_values`).
  - `django_strawberry_framework/utils/input_values.py`: Unmodified (implementation is sound and fully satisfies its contract).
- **Permanent tests and pinned behavior:**
  - `tests/utils/test_input_values.py::test_input_field_value_reads_dict_and_dataclass_fields`: Pins `input_field_value` reading single fields or returning `None` for missing attributes and non-walkable inputs.
  - `tests/utils/test_input_values.py::test_field_name_bypasses_hostile_str_subclass_str_override`: Pins `_field_name` extraction on hostile `str` subclasses without invoking overridden `__str__`.
  - `tests/utils/test_input_values.py::test_order_list_elements_reject_primitive_values`: Pins `iter_active_fields` raising `ConfigurationError` when top-level order lists contain non-mapping primitives (e.g. strings or integers).
- **Scratch or focused verification:**
  - Scratch test suite: `docs/review/temp-tests/utils_input_values/test_scratch.py` (7 passed in 1.46s).
  - Focused test suite: `uv run pytest tests/utils/test_input_values.py --no-cov` (21 passed in 1.53s).
  - Consumer test suites: `uv run pytest tests/filters/test_inputs.py tests/orders/test_inputs.py tests/utils/test_permissions.py --no-cov` (184 passed in 3.62s).
- **Formatter and linter results:**
  - `uv run ruff format .`: formatted 1 file (`tests/utils/test_input_values.py`), 430 files clean.
  - `uv run ruff check --fix .`: all checks passed (0 errors remaining).
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — target implementation is unchanged and internal/external behavior contracts are preserved.

## Independent verification (Worker 2)

- **Baseline and Scoped Diff:**
  - Cycle baseline: `HEAD` (`12779c99`).
  - Verified `git diff 12779c99 -- django_strawberry_framework/utils/input_values.py` is empty (zero-edit).
- **Behavior & Contract Tracing:**
  - `is_inactive_value`: Evaluates inactive status strictly through identity check `value is None or value is unset_sentinel`. Falsy values (`0`, `0.0`, `""`, `False`, `[]`, `{}`, `set()`, `()`) correctly remain active across all callers.
  - `iter_input_items`: Handles both `dict` (bypassing subclass overrides using `dict.items`) and Strawberry input dataclasses (`__dataclass_fields__` mapping). Normalizes string keys using `str.__str__(value)` to bypass hostile `__str__` overrides on string subclasses, and fails closed with `ConfigurationError` for non-string keys or corrupted dataclass metadata.
  - `input_field_value`: Performs single-field extraction using `dict.get` or `getattr(..., default=None)` safely, returning `None` for missing attributes or non-walkable primitives.
  - `iter_active_fields`: Correctly evaluates top-level active fields, resolves provenance via `config.field_specs`, and classifies fields mutually exclusively into `LOGIC`, `RELATED`, and `LEAF`. Handles top-level list flattening for order sets while failing closed with `ConfigurationError` on non-mapping or nested list elements. Recursion ceiling `DEFAULT_SET_INPUT_TRAVERSAL_DEPTH = 8` is aligned across the package.
- **Verification Tests & Experiments:**
  - Focused test suite: `uv run pytest tests/utils/test_input_values.py --no-cov` (21 passed in 1.54s).
  - Consumer test suites: `uv run pytest tests/filters/test_inputs.py tests/orders/test_inputs.py tests/utils/test_permissions.py --no-cov` (184 passed in 3.66s).
  - Worker 1 scratch suite: `uv run pytest docs/review/temp-tests/utils_input_values/test_scratch.py --no-cov` (7 passed in 1.41s).
  - Worker 2 independent scratch suite: `uv run pytest docs/review/temp-tests/utils_input_values/test_worker2_scratch.py --no-cov` (5 passed in 1.66s), testing identity matrix on falsy values, hostile dictionary method overrides, dataclass single field lookups, full leaf/logic/related classification, and depth constant consistency.
- **Findings & Disposition:**
  - Zero open findings. Target implementation is verified, fully tested, and preserves all internal and external contracts.

