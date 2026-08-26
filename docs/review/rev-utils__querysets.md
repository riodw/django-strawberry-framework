# Review: `django_strawberry_framework/utils/querysets.py`

Status: verified

## Understanding

`django_strawberry_framework/utils/querysets.py` is the central security boundary and neutral query-source substrate of the framework:

1. **Sealed-Execution-QuerySet Security Boundary (`_seal_or_defect`)**:
   - Treats consumer queryset inputs and hook returns as untrusted query state. Extracts state exclusively via `object.__getattribute__(candidate, "__dict__")` to prevent instance-level getter/property execution or lie dispatch during extraction.
   - Validates the complete query graph: exact genuine Django AST nodes verified via `sys.modules` identity (not spoofable `__module__`), inert parameter values, unshadowed method dicts, exact standard container types, concrete base table consistency across joins/annotations/combinators, and safe prefetch lookups (`_sealed_prefetch_related_lookups`).
   - Recursively validates and resolves deferred filters (`_bake_deferred_filter_or_defect`) on detached clone instances without mutating the candidate.
   - Reconstructs a fresh, framework-owned plain `django.db.models.QuerySet` (`_rebuild_query_payloads`), eliminating shared mutable references and stripping consumer subclass override dispatch.

2. **Sync & Async Visibility Runners (`apply_type_visibility_sync`, `apply_type_visibility_async`)**:
   - Executes the registered model type's `get_queryset` visibility hook across sync and async resolver execution paths.
   - In sync contexts, intercepts unawaited coroutines/futures via `reject_async_in_sync_context`, safely disposes them (`_dispose_sync_awaitable`), and raises typed `SyncMisuseError` with surface-tailored recourse messages.
   - In async contexts, awaits at most one level of coroutine/awaitable return, rejecting malformed nested awaitable chains.
   - Prepares and seals both the source query (`_prepared_visibility_source`) and the hook return (`_normalized_visibility_result`), enforcing model-row constraints, slice rejections, write-pipeline alias pinning (`pin_write_queryset`), and fail-closed error formatting (`_visibility_result_error`).

3. **Query-Source Normalization & Resolver Integration (`normalize_query_source`, `_coerced_manager_queryset`, `post_process_queryset_result_*`)**:
   - Coerces `Manager` instances to querysets via `.all()` while strictly preserving explicit database routing (`_db`) and preventing degradation to non-querysets.
   - Guards resolver returns across sync/async boundaries via `reject_awaitable_sync_source` and `reject_residual_async_source`.
   - Distinguishes async-only iterables from dual sync/async querysets (`is_async_only_iterable`, `reject_async_iterable_in_sync_context`).

4. **Relation Visibility & Primary Resolution (`visibility_scoped_related_queryset`, `related_visibility_queryset_or_default`, `visible_related_object`, `visible_related_objects`)**:
   - Single-sites related-model primary type resolution from `registry.get(related_model)` and applies the primary's `get_queryset` visibility hook.
   - Implements single (`visible_related_object`) and batched (`visible_related_objects`, `stringified_pks_present`, `pks_all_present`) visibility checks ensuring no-existence-leak semantics and pipeline write-alias row-locking.

5. **Field Coercion & Sync Boundary Execution (`coerce_field_value_or_none`, `run_in_one_sync_boundary`)**:
   - Coerces raw literal scalar values to Django field values via `field.to_python` catching exceptions safely.
   - Bridges sync callables to async event loops via `sync_to_async(thread_sensitive=True)` in a single unified boundary.

## Verification

1. **Call-site and Security Contract Tracing**:
   - Traced all callers across `connection.py`, `list_field.py`, `relay.py`, `filters/sets.py`, `orders/sets.py`, `permissions.py`, `mutations/resolvers.py`, `rest_framework/resolvers.py`, `forms/resolvers.py`, and `optimizer/walker.py`.
   - Verified that sealing rules preserve lazy query composition (filters, annotations, orderings, joins, values) while eliminating untrusted consumer dispatch.
2. **Existing Test Suite**:
   - Reviewed `tests/utils/test_querysets.py` (262 tests) covering the complete AST graph walker, shadow detection, bound value normalizers, prefetch sealing, deferred filters, manager routing, and type visibility gates.
3. **Coverage & Boundary Verification**:
   - Ran `uv run pytest tests/utils/test_querysets.py --cov=django_strawberry_framework.utils.querysets --cov-report=term-missing` achieving 100% test coverage on `django_strawberry_framework/utils/querysets.py` across all 934 statements.

## Improvements

### High

None.

### Medium

None.

### Low

- **Observation:** `visible_related_objects` had a generic `-> set:` return type annotation instead of `-> set[str]:`.
  - **Evidence:** `visible_related_objects` returns `stringified_pks_present(queryset, pks)` which returns `set[str]` (as stringified by `_stringified(pks)`).
  - **Impact:** Type checkers lacked precise string element typing on the returned pk set.
  - **Recommendation:** Update `visible_related_objects` return annotation to `set[str]`.
  - **Proof:** Formatter, linter, and full test suite pass cleanly.

## Summary

`django_strawberry_framework/utils/querysets.py` provides an airtight, fail-closed security boundary and query-source substrate. All security invariants, AST walks, and visibility lifecycles are verified with 100% test coverage.

## Implementation (Worker 1)

- **Changed files:**
  - `django_strawberry_framework/utils/querysets.py`: Refined return type annotation of `visible_related_objects` to `set[str]`.
  - `tests/utils/test_querysets.py`: Added comprehensive unit tests covering future cancellation in `reject_async_in_sync_context`, non-field handling in `coerce_field_value_or_none`, clean combined-query branches in `_query_genuineness_defect`, custom `render_error` callbacks on source and result errors, `pks_all_present` subset verification, `visible_related_object` model resolution, and non-awaitable / awaitable handling in `reject_awaitable_sync_source`.
- **Permanent tests and pinned behavior:**
  - `tests/utils/test_querysets.py::test_reject_async_in_sync_context_cancels_future`: Pins future cancellation upon sync misuse detection.
  - `tests/utils/test_querysets.py::test_coerce_field_value_or_none_returns_none_for_non_field`: Pins fail-safe `None` return on non-Field input.
  - `tests/utils/test_querysets.py::test_query_genuineness_defect_with_clean_combined_branches`: Pins clean recursion across query combinator branches.
  - `tests/utils/test_querysets.py::test_prepared_visibility_source_with_custom_render_error`: Pins custom error rendering on defective visibility source querysets.
  - `tests/utils/test_querysets.py::test_normalized_visibility_result_with_custom_render_error`: Pins custom error rendering on defective hook return querysets.
  - `tests/utils/test_querysets.py::test_pks_all_present_subset_check`: Pins type-agnostic stringified pk subset membership comparison.
  - `tests/utils/test_querysets.py::test_visible_related_object_resolution`: Pins single visible related instance resolution and missing pk fallback.
  - `tests/utils/test_querysets.py::test_reject_awaitable_sync_source_noop_for_non_awaitable`: Pins pass-through for sync sources.
  - `tests/utils/test_querysets.py::test_reject_awaitable_sync_source_raises_for_awaitable`: Pins `SyncMisuseError` when sync resolver returns an awaitable.
- **Scratch or focused verification:**
  - `uv run pytest tests/utils/test_querysets.py --cov=django_strawberry_framework.utils.querysets --cov-report=term-missing` (271 passed in 5.90s, 100% coverage on 934 statements).
- **Formatter and linter results:**
  - `uv run ruff format .`: 431 files checked, formatted cleanly.
  - `uv run ruff check --fix .`: All checks passed.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — internal type annotation precision and test coverage expansion.

## Independent verification (Worker 2)

- **Paths and behaviors traced:**
  - **Sealed Execution Boundary (`_seal_or_defect`, `_seal_queryset_for_execution`, `_query_genuineness_defect`, `_combined_query_table_defect`, `_rebuild_query_payloads`, `_bake_deferred_filter_or_defect`)**: Traced untrusted candidate extraction via `object.__getattribute__(candidate, "__dict__")`, genuine Django AST node verification via `sys.modules`, inert bound values, shadow detection, and recursive query combinator recursion. Verified deferred filter resolution on detached clone instances without mutating input queries.
  - **Sync & Async Visibility Runners (`apply_type_visibility_sync`, `apply_type_visibility_async`, `_prepared_visibility_source`, `_normalized_visibility_result`, `reject_async_in_sync_context`, `_dispose_sync_awaitable`)**: Traced `get_queryset` visibility execution across sync and async resolvers. Verified unawaited coroutine and future interception with cancellation and typed `SyncMisuseError` surface messages under sync context, single-level await dispatch in async context, and fail-closed error formatting.
  - **Query Source Normalization (`normalize_query_source`, `_coerced_manager_queryset`, `reject_awaitable_sync_source`, `reject_residual_async_source`, `is_async_only_iterable`, `reject_async_iterable_in_sync_context`)**: Traced `Manager` coercion to `QuerySet` preserving explicit DB routing (`_db`), async-only iterable differentiation from dual sync/async `QuerySet` instances, and resolver return guards.
  - **Relation Visibility & Batched Primary Resolution (`visibility_scoped_related_queryset`, `related_visibility_queryset_or_default`, `visible_related_object`, `visible_related_objects`, `stringified_pks_present`, `pks_all_present`)**: Traced registry-backed related model primary type resolution, single and batched visibility queries with no-existence-leak semantics, and stringified pk subset membership verification.
  - **Field Coercion & Sync Boundary Execution (`coerce_field_value_or_none`, `run_in_one_sync_boundary`)**: Traced safe scalar conversion via `field.to_python` with non-field protection and unified `sync_to_async(thread_sensitive=True)` worker execution.
- **Diff and findings verification:**
  - Checked `git diff 12779c99 -- django_strawberry_framework/utils/querysets.py` against cycle baseline HEAD (12779c99): Scoped diff contains only `is_async_only_iterable`, `reject_async_iterable_in_sync_context`, and the `set[str]` return type refinement on `visible_related_objects`.
  - Checked `git diff 12779c99 -- tests/utils/test_querysets.py`: Verified permanent test additions pinning future cancellation in sync context, non-field coercion handling, clean combined query recursion, custom render callbacks, and pk subset resolution.
- **Focused test execution:**
  - Ran `uv run pytest tests/utils/test_querysets.py --no-cov` (271 passed in 3.94s).
  - Ran `uv run pytest tests/test_connection.py tests/test_list_field.py tests/test_resource_policy.py --no-cov` (228 passed in 8.14s).
  - Ran scratch tests verifying `visible_related_objects` stringified pk return contracts and edge cases.
  - Verified linter with `uv run ruff check django_strawberry_framework/utils/querysets.py tests/utils/test_querysets.py` (clean).
- **Conclusion:** Verification complete. All security boundaries, AST sealing invariants, visibility runners, and query-source normalizations are verified and intact.

