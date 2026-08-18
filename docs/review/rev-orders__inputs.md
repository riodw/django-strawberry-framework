# Review: `django_strawberry_framework/orders/inputs.py`

Status: verified

## Understanding

`orders/inputs.py` defines the public six-member `Ordering` enum, expands `Meta.fields="__all__"`, emits generated input field specs, normalizes Strawberry dataclasses or mappings into flat Django paths, and owns the module-global materialization/clear ledger. `FieldSpec` provenance maps flattened Python/GraphQL attributes back to ORM source paths, including `shelf_code` → `shelf__code`; related branches recurse into child ordersets.

The module is consumed by `OrderArgumentsFactory`, `OrderSet.apply_sync`/`apply_async`, the finalizer, `connection.py::_synthesized_signature`, and `orders/__init__.py::order_input_type`. The sibling filter input module uses the same shared input traversal substrate, while `registry.clear()` resets order ledgers and caches but intentionally parks already-materialized module globals.

## Verification

- Probed real Django metadata for `Branch.tags` (`GenericRelation`) and `TaggedItem.content_object` (`GenericForeignKey`): both expose `column = None`, so the previous `hasattr(field, "column")` test incorrectly included them in `__all__`.
- Probed direct public usage with `OrderSet.apply_sync({"title": Ordering.ASC}, queryset, info)` before factory construction: `_field_specs` was empty, `normalize_input_value` skipped the active leaf, and the original queryset was returned unchanged.
- Read the generated input factory, shared `iter_active_fields`, permission traversal, finalizer materialization, connection resolver signature, fakeshop schemas, and existing order tests.
- `uv run pytest --no-cov tests/orders/ -q` — 146 passed after implementation.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_library_api.py examples/fakeshop/test_query/test_products_api.py -q` — 315 passed after implementation.

## Improvements

### High

None.

### Medium

#### Virtual Django descriptors were exposed by `Meta.fields="__all__"`

- **Observation:** `_get_concrete_field_names_for_order` accepted any field with a `column` attribute. Django virtual `GenericRelation` and `GenericForeignKey` descriptors expose `column = None`, so generated order inputs advertised paths that are not database columns.
- **Evidence:** Real fakeshop metadata showed `Branch.tags` and `TaggedItem.content_object` in the old helper output. Ordering by either would fail or have undefined ORM semantics.
- **Impact:** A consumer using the documented `__all__` shorthand could receive invalid GraphQL order fields and late query-time errors; the generated surface contradicted the “column-backed fields” contract.
- **Recommendation:** Require a non-`None` database column and continue excluding many-to-many fields.
- **Proof:** `tests/orders/test_sets.py::test_orderset_all_excludes_virtual_generic_fields` asserts both virtual descriptors are absent.

#### Direct mapping inputs silently discarded active order fields

- **Observation:** `normalize_input_value` skipped every active field whose factory-generated `FieldSpec` was absent. The code's shared traversal accepted mappings, but direct `OrderSet.apply_*` callers could therefore receive an unchanged queryset without an error.
- **Evidence:** A real `Book` probe with `{"title": Ordering.ASC}` returned the same queryset with no `order_by` clauses until `OrderArgumentsFactory` was called first.
- **Impact:** The public resolver-facing apply API silently ignored valid-looking mapping input, making a caller's ordering request ineffective.
- **Recommendation:** Lazily build order field specs for model-backed ordersets at normalization time when the factory has not already populated them; preserve the existing model-less defensive skip.
- **Proof:** `tests/orders/test_inputs.py::test_normalize_input_value_builds_field_specs_for_direct_mapping_input` pins mapping normalization without factory setup.

### Low

None.

## Summary

The enum, generated input shape, lazy namespace, and recursive normalizer are sound after two boundary fixes: virtual fields no longer enter `__all__`, and direct mapping callers now receive the same flat paths as factory-generated dataclasses.

## Implementation (Worker 1)

- `django_strawberry_framework/orders/inputs.py::_get_concrete_field_names_for_order` now requires `column is not None`, excluding virtual GenericRelation/GenericForeignKey descriptors.
- `django_strawberry_framework/orders/inputs.py::normalize_input_value` now lazily populates `_field_specs` for model-backed direct callers before traversing input.
- Added permanent package tests in `tests/orders/test_sets.py` and `tests/orders/test_inputs.py`.
- No changelog entry is warranted for this correctness hardening.
- Scoped review baseline: `b74172856e2b9b92f2d60446267a10a1d0ffccb9`; unrelated dirty files were preserved.
- Formatting/lint: `uv run ruff format .` reformatted 3 files; `uv run ruff check --fix .` fixed 2 lint issues and left 0 remaining.

## Independent verification (Worker 2)

- Re-traced `Ordering.resolve`, `__all__` metadata discovery, generated field-spec provenance, mapping/dataclass traversal, nested recursion, materialized globals, helper annotations, and registry clearing. Real metadata probes confirmed virtual descriptors remain excluded.
- The direct-mapping fix was challenged through a flat shorthand plus nested target permission gate. That found a timing gap: normalization lazily built specs too late for permission traversal. `_ensure_field_specs` is now the shared initializer used by normalization and the order permission entry point; permanent coverage is in `tests/orders/test_sets.py::test_orderset_direct_mapping_initializes_specs_before_permissions`.
- Challenged empty/None/malformed inputs, null directions, repeated calls, parked globals, and direct mapping shorthand attributes. `_ensure_field_specs` now skips inactive/non-walkable values, preserving no-op behavior without forcing unresolved lazy targets. No remaining input-owned defect was reproduced.
- `uv run pytest --no-cov tests/orders/ -q` — 148 passed; live library/products GraphQL tests — 315 passed. Status is verified.

## Iterations

Worker 2's adversarial direct-mapping probe found that provenance was initialized too late: `normalize_input_value` built `_field_specs` only after `OrderSet.apply_sync` had already run `_run_permission_checks`. A flat `shelf_code` mapping therefore ordered correctly but bypassed the child `check_code_permission` gate.

Worker 1 accepted the finding. The root fix is now owned by `orders/inputs.py::_ensure_field_specs`, which is called both by normalization and before the shared permission traversal; it initializes the root and recursively initialized child provenance for active direct mappings while preserving inactive no-op inputs. Permanent proof is `tests/orders/test_sets.py::test_orderset_direct_mapping_initializes_specs_before_permissions`, with `test_orderset_inactive_input_does_not_resolve_lazy_related_target` guarding the no-op boundary.

Focused validation after the revision: `uv run pytest --no-cov tests/orders/ -q` — 148 passed. The existing live library/products order suites remain green at 315 passed. Worker 2 should independently re-verify this revision.

## Final independent verification (Worker 2)

- Re-ran the revised provenance initializer through direct mapping normalization and confirmed inactive/non-walkable values short-circuit before `_build_input_fields`, preserving lazy-target no-op behavior.
- The targeted 3-test regression probe passed; the complete orders package suite passed 148 tests and live library/products GraphQL suites passed 315 tests.
- Final formatting/lint and `git --no-pager diff --check` passed. `orders/inputs.py` is verified with no remaining input-owned concern.
