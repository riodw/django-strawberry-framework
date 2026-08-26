# Review: `django_strawberry_framework/permissions.py`

Status: verified

## Understanding

`django_strawberry_framework/permissions.py` implements depth-1 cascade visibility filtering (`apply_cascade_permissions` and `aapply_cascade_permissions`) for consumer `DjangoType.get_queryset` hooks. When called inside a type's `get_queryset`, it narrows the caller's `QuerySet` so that every single-column concrete forward relation of the model respects its target type's visibility policy via SQL subquery composition (`Q(<edge>__in=<subquery>)`). Transitive cascading (e.g. `Entry -> Item -> Category`) naturally emerges when target types recursively invoke the helper in their own `get_queryset`.

It owns:
1. **Immutable Traversal State & Context Isolation:**
   - Carries frozen `_TraversalState` (`alias`, `active`, `path`) in module-level `ContextVar[_TraversalState | None]`.
   - Every root call, nested cascade, and edge traversal installs a new state object and resets it via token in a `finally` block.
   - Prevents state leaks across requests, threads, async tasks, and exceptions. Under ASGI / async contexts, `sync_to_async` worker threads operate on copied contexts, guaranteeing task isolation.
2. **Fail-Closed Cycle Detection & Diagnostics:**
   - Tracks active `DjangoType` classes in `_TraversalState.active`. Re-entry into an in-flight type raises a path-rich `ConfigurationError` (e.g., `AType.b -> BType.a -> AType`), preventing cyclic data leaks.
   - Permits explicit zero-edge scoping (`fields=[]`) as a well-defined cycle-breaking mechanism for self-referential models without recursion.
3. **Relation Classification & Edge Planning:**
   - `_is_cascadable_edge`: Classifies single-column concrete forward `ForeignKey` and `OneToOneField` relations (including multi-table inheritance `<parent>_ptr` parent links). Excludes join tables, reverse relations, and non-concrete fields.
   - `_is_unsupported_forward_edge`: Preflights forward relations lacking single-column cascade semantics (`GenericForeignKey`, composite `ForeignObject`). Full walks fail closed before executing hooks; explicit scoping via `fields=` rejects unsupported relations with clear remediation advice.
   - `_edge_plan`: Bounded LRU cache (`maxsize=1024`) over model relation classifications, ensuring zero redundant metadata scans per request.
4. **Fields Scoping & Input Validation:**
   - `_validate_fields`: Validates `fields` argument loudly against bare strings, non-iterables, non-string items, unsupported relations, and non-cascadable names.
5. **Shared Visibility Boundary & Sealed QuerySet Integration:**
   - Root querysets are prepared and sealed through `_prepared_visibility_source` with cascade-specific error rendering (`_root_error_renderer`), neutralizing hostile query manipulation while supporting `.values()` inputs.
   - `_validate_root_queryset` rejects sliced and combinator (`union`, `intersection`, `difference`) querysets up front.
   - Per-edge target hook results are executed through `apply_type_visibility_sync` with `_edge_error_renderer`, ensuring uniform sync/async hook misuse detection (`SyncMisuseError`) and concrete table validation.
6. **SQL-Composability Validation & Column Normalization:**
   - `_validated_target_subquery`: Re-projects accepted target querysets to `target_field.attname` (binding explicit `to_field` columns or PKs).
   - Enforces fail-closed validation against sliced, combinator, field-specific `distinct()`, aggregate-grouped (`GROUP BY`), and column-shadowing annotation/extra aliases (preventing injected constant bypasses).
   - Preserves nullable FK rows via `| Q(<edge>__isnull=True)` disjuncts only when `field.null` is true.
7. **Cross-Database Alias Pinning:**
   - Pins the root call's database alias (`queryset.db`). Enforces that nested cascade applications and hook returns stay on the same alias, rejecting cross-database subqueries.
8. **Thread-Safe Async Dispatching:**
   - `aapply_cascade_permissions`: Offloads blocking permission logic (e.g. database/permission table reads in target hooks) from the event loop using `run_in_one_sync_boundary`.

## Verification

1. **Traced connections across callers and consumers:**
   - `django_strawberry_framework/__init__.py` (re-exports `apply_cascade_permissions`, `aapply_cascade_permissions`, `SyncMisuseError`).
   - `django_strawberry_framework/permissions.py` (re-exports `SyncMisuseError` from `utils/querysets.py`).
   - `django_strawberry_framework/mutations/permissions.py` (uses cascade visibility for mutation permission resolution).
   - `django_strawberry_framework/utils/querysets.py` (`apply_type_visibility_sync`, `_prepared_visibility_source`, `model_for`, `run_in_one_sync_boundary`).
   - `examples/fakeshop/apps/products/schema.py` (uses `apply_cascade_permissions` in `CategoryType`, `ItemType`, `PropertyType`, `EntryType` `get_queryset` hooks).
2. **Examined existing test suites:**
   - `tests/test_permissions.py` (63 tests): Comprehensive suite covering mutual cycles, self-referential cycles, diamond DAGs, MTI parent links (single and multi-level), nullable FK preservation, hidden-target exclusion, proxy default managers, hook return validation, target column normalization, hostile clone/values neutralization, annotation alias shadowing, DB alias pinning, `fields=` validation, sync misuse, `aapply_cascade_permissions` off-loop execution, and thread/task state isolation.
   - `tests/optimizer/test_extension.py`: Verifies cascade permission subqueries under optimizer prefetch planning.
   - `tests/test_connection.py` & `tests/test_list_field.py`: Verifies cascade permissions within Relay connection fields and root list fields.
   - `examples/fakeshop/test_query/test_products_visibility_api.py`: Live GraphQL HTTP acceptance tests verifying visibility filtering on relations.
3. **Focused test execution:**
   - `uv run pytest tests/test_permissions.py --no-cov` passed (63 passed, 1 skipped).
   - `uv run pytest examples/fakeshop/test_query/test_products_visibility_api.py --no-cov` passed (2 passed).
   - Line coverage on `django_strawberry_framework/permissions.py` is 100% (145/145 statements).
4. **Scratch verification:**
   - `docs/review/temp-tests/permissions/test_permissions_scratch.py` passed (2/2 tests), probing field-type classifications, reverse relation exclusions, GFK unsupported preflights, `fields=` validation errors, contextvar cleanup on hook exception, and async execution.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/permissions.py` provides a fail-closed, context-isolated, and mathematically rigorous cascade visibility implementation. It correctly handles cycle detection, MTI parent inheritance, relation descriptor classification, cross-database alias pinning, and SQL-composability validation without adding query round-trips. Test coverage is 100% with no defects or design improvements identified.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:** None (zero-edit cycle). Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/permissions.py` is empty.
- **Permanent tests and pinned behavior:**
  - `tests/test_permissions.py` (63 tests), `tests/optimizer/test_extension.py`, `tests/test_connection.py`, `tests/test_list_field.py`, and `examples/fakeshop/test_query/test_products_visibility_api.py` pin all cascade permissions behaviors, error paths, and live GraphQL HTTP queries.
- **Scratch verification:**
  - `docs/review/temp-tests/permissions/test_permissions_scratch.py` passed (2/2 tests).
  - Focused pytest suite passed (63 unit tests, 2 live HTTP tests).
- **Formatter and linter results:**
  - `uv run ruff check django_strawberry_framework/permissions.py` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/permissions.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- **Behavior and Path Re-tracing:**
  - Re-traced immutable `_TraversalState` isolation in `ContextVar[_TraversalState | None]` across nested cascades, sync/async boundaries, and exception unwinding.
  - Re-traced cycle detection in `apply_cascade_permissions` and verified that `fields=[]` provides safe cycle breaking for self-referential relations without recursion.
  - Re-traced edge classification (`_is_cascadable_edge`, `_is_unsupported_forward_edge`) and caching (`_edge_plan`), confirming proper inclusion of MTI `<parent>_ptr` links, skipping of reverse/M2M relations, and fail-closed handling of polymorphic `GenericForeignKey` edges.
  - Re-traced root queryset preparation/sealing (`_prepared_visibility_source`, `_validate_root_queryset`), target subquery normalization (`_validated_target_subquery`), and SQL composability checks (blocking slices, combinators, distinct ON, GROUP BY aggregations, and column-shadowing annotation/extra aliases).
  - Re-traced DB alias pinning across nested cascade layers and hook return normalizations.
  - Re-traced async off-loop execution in `aapply_cascade_permissions` via `run_in_one_sync_boundary` and verified `SyncMisuseError` propagation for `async def get_queryset` target hooks.
- **Scoped Diff Verification:**
  - Verified empty diff against baseline `12779c99` (`git diff 12779c99 -- django_strawberry_framework/permissions.py`).
- **Test Executions:**
  - `uv run pytest tests/test_permissions.py --no-cov`: 63 passed, 1 skipped.
  - `uv run pytest docs/review/temp-tests/permissions/test_permissions_scratch.py --no-cov`: 2/2 passed.
  - `uv run pytest examples/fakeshop/test_query/test_products_visibility_api.py --no-cov`: 5/5 passed.
- **Disposition:**
  - Zero findings confirmed. Implementation is robust, well-architected, and fully verified. Status set to `verified`.
