# Review: `django_strawberry_framework/orders/sets.py`

Status: verified

## Understanding

`OrderSetMetaclass` collects related declarations and promotes normalized `Meta.fields`; `OrderSet.get_fields` expands leaves plus `RelatedOrder` branches under a guarded cache. `apply_sync` and `apply_async` extract the request, run active-input permission checks, flatten input, classify to-many paths, use `Min`/`Max` annotations to avoid parent-row fan-out, and apply `OrderBy` expressions.

The class is called by `connection.py` after visibility and filtering, by fakeshop root resolvers, and by the finalizer before Strawberry schema construction. `types/finalizer.py::_bind_ordersets` validates owner-model compatibility and related target agreement, but the order set itself owns field/path declaration semantics.

## Verification

- Read the full source, `sets_mixins.py` permission/lifecycle machinery, relation classifier, filter twin, connection pipeline, finalizer binding, fakeshop order declarations, and package/live tests.
- Reproduced an invalid explicit `Meta.fields` path: `BookOrder.get_fields()` previously returned `["does_not_exist"]`, deferring failure until a query attempted Django ORM ordering.
- Confirmed valid forward/reverse FK, M2M, nullable ordering, to-many aggregation, permission gates, async permission boundary, and connection composition through existing tests.
- `uv run pytest --no-cov tests/orders/ -q` — 146 passed after implementation.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_library_api.py examples/fakeshop/test_query/test_products_api.py -q` — 315 passed after implementation.

## Improvements

### High

None.

### Medium

#### Invalid declared order paths reached query-time ORM errors

- **Observation:** `_expand_meta_fields` accepted arbitrary strings, so an explicit unknown field/property became a generated GraphQL input field and only failed later as a Django `FieldError`.
- **Evidence:** A real `OrderSet` with `Meta.model=Book` and `Meta.fields=["does_not_exist"]` successfully expanded before the fix. The package contract and spec require model-field-only ordering and typed `ConfigurationError` handling.
- **Impact:** Schema/finalization could succeed with an invalid public order surface; clients encountered a late backend exception rather than an actionable configuration error.
- **Recommendation:** Strictly classify explicit paths with `utils/relations.py::classify_path` during expansion and again at runtime for model-less/direct applications, wrapping `PathResolutionError` with orderset/path/model context.
- **Proof:** `tests/orders/test_sets.py::test_orderset_meta_fields_rejects_unknown_order_path` asserts the declaration boundary now fails with `ConfigurationError`; runtime classification is exercised by existing to-many and path tests.

### Low

None.

## Summary

`OrderSet` now owns the invalid-path invariant at the declaration/runtime boundaries while retaining row-preserving aggregate ordering, active-input permission dispatch, and sync/async behavior.

## Implementation (Worker 1)

- `django_strawberry_framework/orders/sets.py::_expand_meta_fields` now classifies explicit paths against `Meta.model` and raises typed `ConfigurationError` for unresolved/property paths.
- `django_strawberry_framework/orders/sets.py::_resolve_order_expressions` now classifies active runtime paths against the concrete queryset model before to-many detection/order expression construction.
- Added `tests/orders/test_sets.py::test_orderset_meta_fields_rejects_unknown_order_path`.
- No changelog entry is warranted.
- Scoped review baseline: `b74172856e2b9b92f2d60446267a10a1d0ffccb9`; unrelated dirty files were preserved.

## Independent verification (Worker 2)

- Re-traced declaration collection/cache writes, explicit and runtime path classification, permission dispatch, sync/async boundaries, queryset model selection, to-many `Min`/`Max` aggregation, and connection ordering/pagination cooperation.
- An adversarial direct-mapping probe found `OrderSet.apply_sync` ran permission checks before `normalize_input_value` initialized provenance; a flat `shelf_code` mapping could therefore bypass the nested `check_code_permission` gate. Root cause is fixed by `OrderSet._run_permission_checks` calling `orders/inputs.py::_ensure_field_specs` before the shared traversal, including recursive child sets.
- Added permanent proof in `tests/orders/test_sets.py::test_orderset_direct_mapping_initializes_specs_before_permissions` and `tests/orders/test_sets.py::test_orderset_inactive_input_does_not_resolve_lazy_related_target`. Invalid explicit `Meta.fields` and invalid runtime paths remain typed `ConfigurationError`; no unresolved sets defect remains.
- `uv run pytest --no-cov tests/orders/ -q` — 148 passed; live library/products GraphQL tests — 315 passed. Status is verified.

## Iterations

Worker 2 found a permission-boundary defect in direct mapping usage: `OrderSet.apply_sync` called `_run_permission_checks` before normalization's lazy provenance setup, so a flat `shelf_code` mapping could bypass the nested target's `check_code_permission` gate.

Worker 1 accepted the finding and retained the root fix at the orders layer. `OrderSet._run_permission_checks` now calls `orders/inputs.py::_ensure_field_specs` before `ActiveInputPermissionMixin` traverses fields; child ordersets re-enter the same initializer. Active `None`/empty inputs still return without resolving lazy targets. Permanent proof is `tests/orders/test_sets.py::test_orderset_direct_mapping_initializes_specs_before_permissions`, plus the inactive-input regression.

Focused validation after the revision: `uv run pytest --no-cov tests/orders/ -q` — 148 passed. Existing live library/products order suites remain green at 315 passed. Worker 2 should independently re-verify this revision.

## Final independent verification (Worker 2)

- Re-ran the exact direct flat-mapping permission regression and inactive lazy-target tests; all passed. The permission initializer runs before shared dispatch and recurses through child ordersets, while inactive `None`/`[]`/`{}` inputs remain unchanged.
- The complete orders suite passed 148 tests; live library/products HTTP GraphQL suites passed 315 tests. Runtime invalid-path checks, sync/async behavior, aggregate ordering, and connection composition remain green.
- Final formatting/lint and `git --no-pager diff --check` passed. `orders/sets.py` is verified with no remaining sets-owned concern.
