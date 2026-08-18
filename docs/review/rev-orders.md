# Review: `django_strawberry_framework/orders/`

Status: verified

## Understanding

The orders folder is a complete sidecar lifecycle. `base.py` declares lazy related targets; `sets.py` collects declarations, expands fields, dispatches permissions, and applies ORM ordering; `inputs.py` defines `Ordering`, provenance, normalization, and the generated-input namespace; `factories.py` builds the reachable Strawberry input graph; `__init__.py` exposes the public classes/helper and tracks helper references for orphan validation.

Integration crosses `sets_mixins.py`, `utils/input_values.py`, `utils/permissions.py`, `utils/relations.py`, `types/base.py`/`definition.py`, `types/finalizer.py`, `registry.py`, `connection.py`, and the fakeshop library/products schemas. The finalizer binds every `Meta.orderset_class`, resolves all related targets, validates orphan helper references, materializes module globals, and only then allows Strawberry schema construction. Connection fields synthesize `orderBy` from the materialized sidecar and run visibility → filter → order → optimizer.

## Verification

- Read all five source modules in order, then re-read the integrated folder and connected finalizer, connection, filters, registry, type definitions, shared mixins/utilities, fakeshop schemas, and all order tests.
- Scoped pre-existing target diff against `b74172856e2b9b92f2d60446267a10a1d0ffccb9`: no prior orders-owned source/test/review diff was present before this pass.
- Confirmed two boundary defects (virtual `__all__` fields and direct mapping no-op) and one declaration defect (invalid explicit paths). An independent permission probe found direct flat mappings could bypass nested target gates before provenance initialization; the root fix now initializes specs before permission traversal. No remaining defect was reproduced in lazy target resolution, BFS/cache lifecycle, finalizer owner binding/orphan checks, permission dedup/double-dispatch, aggregate to-many ordering, connection argument synthesis, or optimizer composition.
- `uv run pytest --no-cov tests/orders/ -q` — 148 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_library_api.py examples/fakeshop/test_query/test_products_api.py -q` — 315 passed.
- Final `uv run ruff format .` — 1 file reformatted, 422 files left unchanged.
- Final `uv run ruff check --fix .` — all checks passed, 0 remaining.
- `git --no-pager diff --check` — clean.


## Improvements

### High

None.

### Medium

- **Virtual field exposure:** `Meta.fields="__all__"` included `GenericRelation`/`GenericForeignKey` descriptors with `column=None`; fixed in `orders/inputs.py`.
- **Direct mapping no-op:** mapping input was accepted by shared traversal but dropped when factory provenance was absent; fixed by lazy provenance build in `orders/inputs.py`.
- **Direct mapping permission bypass:** permission traversal ran before that lazy build, so flat shorthand mappings could skip a related target gate; fixed by initializing provenance in `OrderSet._run_permission_checks`.
- **Late invalid-path failure:** explicit unknown/property paths reached ORM translation; fixed with strict `classify_path` checks in `orders/sets.py`.

Each finding is detailed in the corresponding per-file artifact with evidence and permanent proof.

### Low

None.

## Summary

The integrated orders lifecycle is coherent and live GraphQL ordering remains green. Four meaningful input/configuration boundaries were hardened at their owning layers without changing unrelated files or the documented connection/finalizer architecture.

## Implementation (Worker 1)

- Changed production files: `django_strawberry_framework/orders/inputs.py` and `django_strawberry_framework/orders/sets.py`.
- Changed permanent package tests: `tests/orders/test_inputs.py` and `tests/orders/test_sets.py`.
- Review artifacts added: `docs/review/rev-orders__base.md`, `docs/review/rev-orders__factories.md`, `docs/review/rev-orders__inputs.md`, `docs/review/rev-orders__sets.md`, and this folder artifact.
- No fakeshop schema/query test change was required: the virtual-field and direct-mapping paths are package-level contracts; existing live ordering tests cover the reachable GraphQL path and passed.
- Changelog: no update warranted for internal correctness hardening.
- Unrelated concurrent dirty files, including pre-existing changes in `examples/fakeshop/test_query/test_multi_db.py` and `test_optimizer_auto_api.py`, were preserved.

## Independent verification (Worker 2)

- Re-traced all five orders modules and the integrated finalizer, connection, registry, type-definition, shared-mixin, relation-classifier, permission, factory, fakeshop schema, and live HTTP paths independently of Worker 1's conclusions.
- Disposable probes challenged virtual `__all__` metadata, direct dataclass/mapping normalization, invalid declarations/runtime paths, repeated registry clears, lazy related targets, async permission execution, model/queryset boundaries, to-many aggregate ordering, and connection composition. One concrete direct-mapping permission bypass was fixed in `orders/inputs.py::_ensure_field_specs` and `orders/sets.py::OrderSet._run_permission_checks`, with permanent coverage in `tests/orders/test_sets.py::test_orderset_direct_mapping_initializes_specs_before_permissions`.
- No unresolved orders defect remains. The attempted declaration-time `RelatedOrder.field_name` validation was rejected because direct model/queryset applications intentionally use the concrete queryset model as the runtime authority; `_resolve_order_expressions` already provides typed runtime validation. Inactive `None`/empty mapping/list inputs remain no-ops without resolving lazy targets.
- Focused validation: `uv run pytest --no-cov tests/orders/ -q` — 148 passed; `uv run pytest --no-cov examples/fakeshop/test_query/test_library_api.py examples/fakeshop/test_query/test_products_api.py -q` — 315 passed.
- Final formatting/lint: `uv run ruff format .` reformatted 1 file and left 422 unchanged; `uv run ruff check --fix .` passed with 0 remaining. `git --no-pager diff --check` is clean.

## Iterations

Worker 2's independent pass found one revision-needed integration defect: direct mapping order input could reach `OrderSet.apply_sync` permission traversal without `_field_specs`, so flat relation paths such as `shelf_code` skipped child permission gates even though the later normalization applied the order.

Worker 1 accepted and completed the revision. `orders/inputs.py::_ensure_field_specs` now owns active-input provenance initialization, and `OrderSet._run_permission_checks` invokes it before shared permission dispatch; recursive child ordersets use the same boundary. Empty/`None`/inactive mapping and list inputs remain no-ops without lazy-target resolution.

Post-revision focused validation: `uv run pytest --no-cov tests/orders/ -q` — 148 passed; `uv run pytest --no-cov examples/fakeshop/test_query/test_library_api.py examples/fakeshop/test_query/test_products_api.py -q` — 315 passed. Worker 2 should re-run independent verification before returning the folder to `verified`.

## Final independent verification (Worker 2)

- Re-read the current post-revision `orders/inputs.py` and `orders/sets.py` implementation and challenged the exact flat-mapping permission path plus `None`/`[]`/`{}` inactive-input cases.
- Direct regression probes: 3 passed (`test_orderset_direct_mapping_initializes_specs_before_permissions`, `test_orderset_inactive_input_does_not_resolve_lazy_related_target`, and `test_normalize_input_value_builds_field_specs_for_direct_mapping_input`).
- Current focused validation: `uv run pytest --no-cov tests/orders/ -q` — 148 passed; live fakeshop HTTP GraphQL validation — 315 passed.
- Final `uv run ruff format .` left 423 files unchanged; `uv run ruff check --fix .` passed; `git --no-pager diff --check` passed. No unresolved defect remains; orders folder is verified.
