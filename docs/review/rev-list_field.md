# Review: `django_strawberry_framework/list_field.py`

Status: verified

## Understanding

`django_strawberry_framework/list_field.py` implements the `DjangoListField` factory function for non-Relay `list[T]` root Query fields bound to a `DjangoType`, along with shared constructor validation guards reused across field factories (`DjangoConnectionField`, `DjangoNodeField`, `DjangoNodesField`).

It owns:
1. **Target-Type Validation Guards:**
   - `_validate_djangotype_target`: Enforces the four shared constructor guards: class type check, `DjangoType` subclass check, strict own-class definition registration check (`definition.origin is target_type`, preventing unconfigured child types from inheriting parent `Meta` definitions), and `callable` resolver validation when supplied.
   - `_validate_relay_djangotype_target`: Composes `_validate_djangotype_target` with `_is_relay_shaped` to ensure targets declare `relay.Node` in `Meta.interfaces` or inherit `relay.Node` directly. Shared by `connection.py` and `relay.py`.
2. **Field-Level Collection Bound Configuration:**
   - Validates explicit `max_rows` positive integer bounds via `validate_collection_bound` at construction time.
   - Forwards `max_rows` and `trusted_max_rows` to `bounded_rows` / `bounded_rows_async`, ensuring no unbounded raw list query escapes the request's resource policy.
3. **Default-Resolver Lifecycle:**
   - When no resolver is provided, seeds the base `QuerySet` via `initial_queryset(target_type)` (`model._default_manager.all()`).
   - Dispatches dynamically at runtime via `in_async_context()`: in sync contexts, applies `apply_type_visibility_sync` followed by `bounded_rows`; in async contexts, awaits `apply_type_visibility_async` via `_bounded_async` before applying `bounded_rows_async`.
   - Ensures row bounding is applied *after* visibility hooks so querysets are not sliced prematurely before visibility filters are composed.
4. **Consumer-Resolver Wrapping and Async Classification:**
   - Detects async generator callables via `is_async_generator_callable`, ensuring async iterables are rejected in sync contexts via `_require_async_iterable_context()` and bounded/closed asynchronously via `bounded_rows_async`.
   - Detects async coroutine callables via `is_async_callable`, awaiting the user coroutine before post-processing via `_post_process_consumer_async` and applying `bounded_rows_async`.
   - For synchronous resolvers, post-processes returns via `_post_process_consumer_sync` (`normalize_query_source` + `apply_type_visibility_sync`), while routing async-only iterable returns through async bounding under `_require_async_iterable_context()`.
   - Enforces loud failure (via `reject_awaitable_sync_source` / `reject_residual_async_source`) if a sync resolver leaks a coroutine/awaitable or an async resolver returns a residual awaitable.

## Verification

1. **Traced connections across callers and consumers:**
   - `django_strawberry_framework/__init__.py` (exported in `__all__`).
   - `connection.py` (imports and calls `_validate_relay_djangotype_target` for `DjangoConnectionField`).
   - `relay.py` (imports and calls `_validate_relay_djangotype_target` via `_validate_node_target`).
   - `optimizer/extension.py` (root-level list field query optimization, prefetch planning, and FK-id elision).
   - `utils/querysets.py` (`initial_queryset`, `normalize_query_source`, `post_process_queryset_result_sync`, `post_process_queryset_result_async`, `apply_type_visibility_sync`, `apply_type_visibility_async`).
   - `resource_policy.py` (`bounded_rows`, `bounded_rows_async`, `validate_collection_bound`).
2. **Examined existing test suites:**
   - `tests/test_list_field.py` (46 tests): Comprehensive unit, validation, sync/async execution, generator bounding, hostile queryset sealing, manager degradation, and alias drift tests.
   - `tests/test_relay_connection.py` (90 tests): Exercises `_validate_relay_djangotype_target` through connection field declarations.
   - `examples/fakeshop/test_query/test_library_api.py`: Live `/graphql/` HTTP acceptance tests for `DjangoListField` default resolver, manager resolver, nullable outer annotation, and optimized nested selections.
   - `examples/fakeshop/test_query/test_resource_policy_api.py`: Live tests verifying `DjangoListField` row bounds under request resource policies.
3. **Focused test execution:**
   - `uv run pytest tests/test_list_field.py --no-cov` passed (46/46 passed).
   - `uv run pytest examples/fakeshop/test_query/test_library_api.py -k "djangolistfield or list_field" --no-cov` passed (4/4 passed).
   - Line coverage on `django_strawberry_framework/list_field.py` is 100% (68/68 statements covered).
4. **Scratch verification:**
   - `docs/review/temp-tests/list_field/test_list_field_scratch.py` passed (7/7 tests), probing non-class, non-DjangoType, abstract DjangoType, missing own-Meta inheritance, non-callable resolver, Relay Node validation, sync context async iterable rejection, metadata pass-through, and async bounded helper execution.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/list_field.py` is a clean, well-bounded, and robust implementation. It provides strict declaration-time type validation, flawless sync/async resolver dispatching and coroutine/generator classification, airtight visibility hook integration, and mandatory collection row bounds. Test coverage across package unit tests and live HTTP acceptance tests is 100%. No defects or improvements were identified.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:** None (zero-edit cycle). Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/list_field.py` is empty.
- **Permanent tests and pinned behavior:**
  - `tests/test_list_field.py` (46 tests), `tests/test_relay_connection.py` (90 tests), and `examples/fakeshop/test_query/test_library_api.py` comprehensively pin all `DjangoListField` and target validation behaviors.
- **Scratch verification:**
  - `docs/review/temp-tests/list_field/test_list_field_scratch.py` passed (7/7 tests).
  - Focused pytest suite passed (46/46 unit tests, 4/4 live HTTP tests).
- **Formatter and linter results:**
  - `uv run ruff check django_strawberry_framework/list_field.py` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/list_field.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- **Behavior and Path Re-tracing:**
  - Re-traced the four constructor validation guards in `_validate_djangotype_target` and the Relay Node guard in `_validate_relay_djangotype_target`. Confirmed cross-module consumption in `connection.py` (`DjangoConnectionField`) and `relay.py` (`_validate_node_target`).
  - Re-traced `DjangoListField` resolver construction: default resolver dynamic dispatch via `in_async_context()` applying `initial_queryset`, `apply_type_visibility_sync`/`async`, and row bounding after visibility composition (`_bounded_async` / `bounded_rows`).
  - Re-traced consumer resolver wrappers: async generator detection (`is_async_generator_callable`), async callable detection (`is_async_callable`), sync post-processing (`_post_process_consumer_sync`), async post-processing (`_post_process_consumer_async`), sync context async-iterable rejection (`_require_async_iterable_context`), and loud rejection of leaked coroutines/awaitables (`SyncMisuseError`).
  - Verified integration with `DjangoOptimizerExtension` (root list field prefetch planning and FK-id elision) and `ResourcePolicy` (mandatory row bounds).
- **Scoped Diff Verification:**
  - Confirmed empty diff against baseline `12779c99` (`git diff 12779c99 -- django_strawberry_framework/list_field.py`).
- **Test Executions:**
  - `uv run pytest tests/test_list_field.py --no-cov`: 46/46 passed.
  - `uv run pytest docs/review/temp-tests/list_field/test_list_field_scratch.py --no-cov`: 7/7 passed.
  - `uv run pytest examples/fakeshop/test_query/test_library_api.py -k "djangolistfield or list_field" --no-cov`: 4/4 passed.
- **Disposition:**
  - Zero findings confirmed. Implementation is robust, well-tested, and contractually sound. Status marked `verified`.
