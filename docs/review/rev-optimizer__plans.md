# Review: `django_strawberry_framework/optimizer/plans.py`

Status: verified

## Understanding

`django_strawberry_framework/optimizer/plans.py` defines the core intermediate representation (`OptimizationPlan`), plan lifecycle (accumulation, merging, finalization, queryset application, reconciliation), ordering and cursor parity logic, and window-based pagination construction for GraphQL query optimization.

Key responsibilities and traced behaviors:
- **`OptimizationPlan` & `_IndexedList`**: Directives accumulator mutated during schema/AST walker traversal (`select_related`, `prefetch_related`, `only_fields`, `fk_id_elisions`, `planned_resolver_keys`). Uses `_IndexedList` with hashable index sidecar `_seen` for `O(1)` amortized uniqueness checks. `finalize()` freezes mutable sequences into immutable tuples and frozenset indices (`finalized_fk_id_elisions`, `finalized_planned_resolver_keys`, `finalized_lookup_paths`). Field merge classification is validated at import time and construction by `_assert_merge_field_inventory()`.
- **Runtime Paths and Resolver Keys**: `resolver_key` generates canonical identifier strings (`ParentType.field@path.to.field`) for strictness tracking. `runtime_path_from_info` and `runtime_path_from_path` safely walk Strawberry AST execution paths, skipping integer list indices and guarding against cyclic or excessively deep paths (`_MAX_PATH_DEPTH = 1024`).
- **Ordering and Total-Order Enforcement**: `order_entry_name_and_direction`, `order_entry_has_explicit_nulls`, `ends_in_unique_column`, `deterministic_order`, and `effective_connection_order`. Ensures cursor parity between plan-time window row numbering and resolve-time fallback offset pagination by appending the model primary key as a tiebreaker unless the terminal column is a non-nullable unique column or primary key.
- **Window Pagination**: `window_partition_for_prefetch` resolves SQL window partition expressions using relation taxonomy. `apply_window_pagination` orchestrates forward, backward, and keyset-seek windowed queries using `window_range_plan(...)`, generating SQL window functions (`ROW_NUMBER()`, `COUNT(*)`) and filters, with count-free next-page probe overfetching (`fetch_upper_bound = upper + 1`) and boundary marker rows (`rn == 1` / `rn_abs == 1`) when needed.
- **QuerySet Reconciliation and Diffing**: `prune_unsupportable_select_related` drops `select_related` paths that cannot be traversed under consumer `.only()` or `.defer()` projections. `diff_plan_for_queryset` detects consumer pre-applied `.only()` and `.prefetch_related()`, pruning redundant optimizer directives, absorbing string prefetches into optimizer `Prefetch` querysets when lossless, and synchronizing planned resolver keys.

## Verification

- Ran test suite `tests/optimizer/test_plans.py` (123 tests passing).
- Ran all optimizer test suites under `tests/optimizer/` (822 tests passing).
- Discovered and resolved test defect in `TestEffectiveConnectionOrder.test_falls_back_to_meta_ordering_through_deterministic_order` where `Category` (which lacks `Meta.ordering`) was referenced instead of `Card` (which defines `ordering = ["number"]` with unique `number`).
- Verified defensive behavior of `ends_in_unique_column` when passed non-model objects or mock classes lacking `_meta`.
- Verified `_reverse_order_by` nulls placement inversion when explicit nulls positioning carries boolean values.

## Improvements

### High

None.

### Medium

None.

### Low

- **Observation 1:** `TestEffectiveConnectionOrder.test_falls_back_to_meta_ordering_through_deterministic_order` asserted that `effective_connection_order(None, (), Category) == ("name",)` under the assumption that `Category` had `Meta.ordering = ("name",)`. In reality, `Category` defines `name = TextField(unique=True)` but no `Meta.ordering`, causing the test to fail.
  - **Remedy:** Updated the test to use `Card`, which defines `Meta.ordering = ["number"]` with `number` unique.
- **Observation 2:** `ends_in_unique_column` directly accessed `model._meta.pk` and `field_obj.null` without defensive attribute retrieval, which could raise `AttributeError` if invoked with mock objects or non-model types.
  - **Remedy:** Added defensive `getattr` lookups on `model._meta` and `field_obj.null`.
- **Observation 3:** `_reverse_order_by` checked `if nulls_first or nulls_last:` when swapping nulls positioning flags. If either flag was boolean `False`, the condition could evaluate to `False` rather than swapping.
  - **Remedy:** Changed check to `if nulls_first is not None or nulls_last is not None:`, consistent with `order_entry_has_explicit_nulls`.

## Summary

`django_strawberry_framework/optimizer/plans.py` is robust, well-specified, and central to the query optimization architecture. The improvements ensure clean test execution, defensive model meta access, and consistent nulls-positioning reversal.

## Implementation (Worker 1)

- Changed files:
  - `django_strawberry_framework/optimizer/plans.py`: Defensive `getattr` checks on `model._meta` in `ends_in_unique_column`; updated `_reverse_order_by` nulls swapping check to `nulls_first is not None or nulls_last is not None`.
  - `tests/optimizer/test_plans.py`: Fixed `test_falls_back_to_meta_ordering_through_deterministic_order` to use `Card`; added `test_ends_in_unique_column_defensive_for_non_model` and `test_swaps_explicit_nulls_positioning_with_boolean_flags`.
- Permanent tests:
  - `tests/optimizer/test_plans.py::TestEffectiveConnectionOrder::test_falls_back_to_meta_ordering_through_deterministic_order`
  - `tests/optimizer/test_plans.py::TestDeterministicOrderHoistParity::test_ends_in_unique_column_defensive_for_non_model`
  - `tests/optimizer/test_plans.py::TestReverseOrderBy::test_swaps_explicit_nulls_positioning_with_boolean_flags`
- Focused verification:
  - `uv run pytest tests/optimizer/test_plans.py --no-cov` (123 passed in 1.76s)
  - `uv run pytest tests/optimizer/ --no-cov` (822 passed in 14.0s)
- Formatter and linter results:
  - `uv run ruff format .` (429 files left unchanged)
  - `uv run ruff check --fix .` (All checks passed)
- Rejected findings: None.
- Changelog: Does not merit a separate changelog entry (internal defensive refinement).

## Independent verification (Worker 2)

- Re-traced core behaviors across all operational areas:
  - `OptimizationPlan` accumulation and hashable indexing via `_IndexedList` (`append`, `extend`, `append_unique`).
  - Plan merging (`merge_from`, `merge_metadata_from`) with `_assert_under_construction` lifecycle guarding and `_assert_merge_field_inventory` completeness validation.
  - `finalize()` immutability freeze converting mutable directives to tuples and metadata to frozensets.
  - Runtime path extraction (`runtime_path_from_info`, `runtime_path_from_path`) with `_MAX_PATH_DEPTH = 1024` cycle protection and list index omission.
  - Total-order and cursor-parity enforcement (`order_entry_name_and_direction`, `order_entry_has_explicit_nulls`, `ends_in_unique_column`, `deterministic_order`, `effective_connection_order`).
  - Window pagination filtering, annotations, probe sentinel overfetching, and marker rows (`apply_window_pagination`, `_apply_keyset_counted_window`, `_reverse_order_by`).
  - Queryset reconciliation and traversal pruning (`diff_plan_for_queryset`, `prune_unsupportable_select_related`, `_optimizer_can_absorb`).
- Verified Worker 1's code changes:
  - `ends_in_unique_column` defensive model `_meta` and `null` attribute lookups.
  - `_reverse_order_by` nulls positioning swap condition (`nulls_first is not None or nulls_last is not None`).
  - Correction in `test_falls_back_to_meta_ordering_through_deterministic_order` to use `Card`.
  - Added test coverage for non-model objects and boolean nulls flags.
- Executed verification test suites:
  - `uv run pytest tests/optimizer/test_plans.py --no-cov` (123 passed in 1.84s).
  - `uv run pytest tests/optimizer/ --no-cov` (824 passed in 12.25s).
- Verified that target is sound, contracts are intact, and all tests pass cleanly.

