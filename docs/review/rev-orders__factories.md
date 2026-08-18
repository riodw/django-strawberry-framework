# Review: `django_strawberry_framework/orders/factories.py`

Status: verified

## Understanding

`OrderArgumentsFactory` owns the Layer-5 breadth-first build of every reachable order input class. It consumes `OrderSet.get_fields()` rather than a second metadata map, emits leaf `Ordering | None` fields and lazy related references, detects generated-name collisions, and shares family-local caches with finalizer materialization. `get_orderset_class` and `_dynamic_orderset_cache` are deliberately build-only plumbing; connection consumers use an explicit `Meta.orderset_class`.

The factory depends on `orders/inputs.py` for field triples and module-global materialization, `orders/sets.py` for declaration expansion, `utils/inputs.py::GeneratedInputArgumentsFactory` for BFS/collision mechanics, and `registry.clear()` through the order namespace lifecycle. Finalizer phase 2.5 binds all owners and expands all related targets before this factory is materialized.

## Verification

- Traced factory construction through `utils/inputs.py::GeneratedInputArgumentsFactory`, `orders/inputs.py::_build_input_fields`, `types/finalizer.py::_bind_ordersets`, `registry.clear()`, and Strawberry lazy resolution.
- Reviewed existing package tests for BFS reachability, cycles, duplicate queue entries, generated-name collisions, empty inputs, idempotency, dynamic cache normalization, reserved kwargs, and subclass rejection.
- `uv run pytest --no-cov tests/orders/ -q` — 146 passed after implementation.
- No factory-specific correctness defect was reproduced; the only direct-input issue was owned by `orders/inputs.py::normalize_input_value`, where provenance was not guaranteed for callers bypassing the factory.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The factory BFS and lifecycle caches are coherent with finalizer materialization and the sibling filter factory. The dynamic getter remains an intentional non-consumer surface.

## Implementation (Worker 1)

- No production change was needed in `orders/factories.py`.
- Existing permanent factory tests remain green.
- No changelog entry is warranted.
- Scoped review baseline: `b74172856e2b9b92f2d60446267a10a1d0ffccb9`; unrelated dirty files were preserved.

## Independent verification (Worker 2)

- Re-traced the BFS queue, seen/collision ledgers, empty-input guard, dynamic getter, materialization, finalizer four-subpass ordering, and registry-clear lifecycle. Challenged duplicate enqueues, cycles, same-name classes, distinct metadata, parked globals, partial rebuilds, and helper orphan tracking.
- No factory-owned defect was reproduced. Direct mappings correctly bypass the factory after the input-layer provenance initializer runs; permission timing was fixed at `OrderSet._run_permission_checks`, not in the factory.
- `uv run pytest --no-cov tests/orders/ -q` — 148 passed; live library/products GraphQL tests — 315 passed. Status is verified.

## Final independent verification (Worker 2)

- Rechecked the current factory/materialization lifecycle against the provenance revision; factory BFS, collision handling, parked globals, and registry-clear state remain unchanged and coherent.
- The targeted and complete orders regressions passed (3 direct probes; 148 package tests), with 315 live library/products GraphQL tests passing. `orders/factories.py` remains verified.
