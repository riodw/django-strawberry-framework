# Review: `django_strawberry_framework/orders/factories.py`

Status: verified

## Understanding

`django_strawberry_framework/orders/factories.py` implements Layer 5 (the `OrderArgumentsFactory` BFS input generation pipeline) and Layer 6 (the module-level dynamic-`OrderSet` cache and `get_orderset_class` factory) of the spec-028 ordering subsystem.

### Key Responsibilities and Symbols:
1. **`OrderArgumentsFactory`**:
   - Direct subclass of `GeneratedInputArgumentsFactory` (`utils/inputs.py`).
   - Owns the order-family class-level type cache `input_object_types` and duplicate-name collision registry `_type_orderset_registry`.
   - Traverses reachable `RelatedOrder` relations using deterministic FIFO BFS walk with cycle detection and diamond-graph deduplication.
   - Specializes `_build_input_triples` by delegating directly to `_build_input_fields(set_cls, owner_definition)` without operator bags (spec-028 Decision 8; no `and_` / `or_` / `not_` logic fields).
   - Rejects subclassing via `__init_subclass__` on the base to prevent shared mutable cache cross-contamination.
   - Invoked during `types/finalizer.py` phase 2.5 sidecar set binding.
2. **`_dynamic_orderset_cache` & `_RESERVED_FACTORY_KEYS`**:
   - Module-level dictionary cache keyed by canonical metadata tuples produced by `make_set_meta_cache_key`.
   - Strips reserved keyword arguments (`orderset_base_class`) to prevent collision with synthetic class generation.
3. **`get_orderset_class`**:
   - Thin wrapper around `_get_orderset_class` created via `make_dynamic_set_getter` (`utils/inputs.py`).
   - Returns pre-declared `orderset_class` unchanged when supplied; otherwise normalizes metadata (unhashable meta structures, sorted sequences) and mints / caches a synthetic `OrderSet` subclass (`<Model>AutoOrder`).

## Verification

1. **Dependency and Caller Mapping**:
   - `django_strawberry_framework/types/finalizer.py`: verified consumption of `OrderArgumentsFactory(orderset_cls).arguments` during phase 2.5 sidecar binding subpass 4.
   - `django_strawberry_framework/orders/inputs.py`: verified integration of `_build_input_fields`, `_materialized_names`, `_field_specs`, and `make_set_input_namespace`.
   - `django_strawberry_framework/orders/sets.py`: verified metaclass `related_orders` collection and metadata expansion.
   - `django_strawberry_framework/utils/inputs.py`: verified shared substrate contracts in `GeneratedInputArgumentsFactory`, `make_dynamic_set_getter`, `normalize_set_meta_for_factory`, and `make_set_meta_cache_key`.
2. **Existing Test Suite Audit**:
   - `tests/orders/test_factories.py`: read all 530+ lines and verified assertions across BFS traversal, cycles, leaf/related type annotations, class collision diagnostics, idempotency, shared cache instances, subclass rejection, empty set rejection, and dynamic class caching.
   - `tests/orders/test_composition.py`: verified filter/order cache isolation.
   - `tests/orders/test_finalizer.py`: verified phase 2.5 materialization and cache clear interactions.
3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/orders__factories/test_scratch_factories.py` testing dynamic `OrderSet` BFS input generation, diamond dependency graph deduplication (`A -> B -> D` and `A -> C -> D`), 4-tier deep BFS chains, and `RelatedOrder` callable target factory resolution.
   - Ran `uv run pytest docs/review/temp-tests/orders__factories/test_scratch_factories.py --no-cov`: 4 passed.
4. **Focused Test Runs**:
   - `uv run pytest tests/orders/test_factories.py --no-cov`: 28 passed.
   - `uv run pytest tests/orders/ --no-cov`: 165 passed across the entire ordering subsystem.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/orders/factories.py` is clean, robust, and correctly integrates with the shared `utils/inputs.py` substrate. The target file requires no modifications. Edge-case test coverage in `tests/orders/test_factories.py` was permanently expanded to pin dynamic `OrderSet` BFS input creation, diamond DAG deduplication, 4-tier deep BFS chains, and callable factory `RelatedOrder` target resolution.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/orders/test_factories.py`: added permanent edge-case tests covering dynamic `OrderSet` BFS input creation, diamond dependency graph deduplication, 4-tier deep BFS traversal, and callable factory `RelatedOrder` targets.
  - Scoped diff against baseline `12779c99` for `django_strawberry_framework/orders/factories.py` is zero-edit (0 diff).
- **Permanent tests and pinned behavior:**
  - `tests/orders/test_factories.py` (28 tests total):
    - `test_factory_visits_every_reachable_relatedorder_target_via_bfs`: pins BFS traversal across reachable `RelatedOrder` targets.
    - `test_factory_handles_cycles_via_seen_set`: pins cycle detection avoiding infinite recursion.
    - `test_factory_builds_leaf_fields_with_ordering_or_none_annotation`: pins `Ordering | None` leaf annotation shape.
    - `test_factory_builds_relatedorder_fields_with_annotated_strawberry_lazy_forward_reference`: pins `LazyType` forward references.
    - `test_factory_raises_on_two_distinct_ordersets_sharing_classname`: pins duplicate name collision detection.
    - `test_factory_arguments_is_idempotent`: pins `.arguments` read idempotency.
    - `test_factory_input_object_types_shared_across_factory_instances`: pins class-level cache convergence.
    - `test_factory_subclass_rejected_at_class_creation_time`: pins subclassing prevention on factory.
    - `test_factory_skips_related_order_with_none_target`: pins skipping placeholder `RelatedOrder(None, ...)`.
    - `test_factory_rejects_related_orders_with_colliding_graphql_names`: pins camel-case GraphQL name collision rejection.
    - `test_factory_raises_on_orderset_with_no_orderable_fields`: pins empty `OrderSet` rejection.
    - `test_factory_raises_on_orderset_with_empty_fields_list`: pins `Meta.fields = []` rejection.
    - `test_factory_raises_when_reachable_related_orderset_is_empty`: pins empty related `OrderSet` rejection in BFS.
    - `test_factory_dedupes_double_enqueued_target_via_seen_check`: pins pop-time seen deduplication.
    - `test_get_orderset_class_returns_explicit_class_unchanged`: pins pass-through of explicit `OrderSet`.
    - `test_get_orderset_class_caches_dynamic_orderset_by_meta`: pins dynamic class caching and naming.
    - `test_get_orderset_class_distinct_meta_produces_distinct_classes`: pins distinct cache slots for distinct metadata.
    - `test_get_orderset_class_strips_reserved_kwargs`: pins stripping reserved factory kwargs.
    - `test_get_orderset_class_collapses_set_and_frozenset_fields`: pins canonical cache slot for set/frozenset fields.
    - `test_get_orderset_class_collapses_exclude_order`: pins exclusion order canonicalization.
    - `test_normalize_meta_strips_reserved_and_canonicalizes_sets`: pins metadata normalization helper.
    - `test_orderset_class_meta_and_factory_kwargs_share_set_fields_order`: pins deterministic field ordering.
    - `test_get_orderset_class_requires_model_when_dynamic`: pins missing model error.
    - `test_get_orderset_class_rejects_non_model_when_dynamic`: pins non-model validation.
    - `test_factory_builds_dynamic_orderset`: pins BFS input generation for dynamic `OrderSet`s.
    - `test_factory_handles_diamond_dependency_graph`: pins diamond DAG deduplication.
    - `test_factory_handles_4_tier_deep_chain`: pins multi-tier deep BFS resolution.
    - `test_factory_handles_related_order_targeting_callable_factory`: pins callable factory target resolution.
- **Scratch verification:**
  - `docs/review/temp-tests/orders__factories/test_scratch_factories.py` passed (4/4 tests).
  - `uv run pytest tests/orders/test_factories.py --no-cov` passed (28/28 tests).
  - `uv run pytest tests/orders/ --no-cov` passed (165/165 tests).
- **Formatter and linter results:**
  - `uv run ruff format .` passed with 0 errors.
  - `uv run ruff check --fix .` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No.

## Independent verification (Worker 2)

- **Target diff check:** Confirmed `git diff 12779c99 -- django_strawberry_framework/orders/factories.py` is zero-edit (0 diff against baseline).
- **Behavior re-trace and contracts:**
  - `OrderArgumentsFactory` correctly subclasses `GeneratedInputArgumentsFactory`, initializing order family registries (`input_object_types`, `_type_orderset_registry`) and hooking `_build_input_triples` to `_build_input_fields(set_cls, owner_definition)` without operator bags (spec-028 Decision 8).
  - Traversal correctly walks reachable `RelatedOrder` targets using deterministic FIFO BFS with cycle detection and diamond graph deduplication.
  - Subclassing prevention guard via `__init_subclass__` rejects deep inheritance to preserve cache isolation.
  - Layer-6 dynamic `OrderSet` getter `get_orderset_class` and module cache `_dynamic_orderset_cache` properly strip reserved keywords (`orderset_base_class`) and collapse metadata shapes.
- **Independent scratch testing:**
  - Authored and ran `docs/review/temp-tests/orders__factories/test_independent_scratch_factories.py` testing:
    1. Self-referencing recursive tree structures (`CategoryOrder` with `parent = RelatedOrder(lambda: CategoryOrder, ...)`).
    2. 3-node cycles (`A -> B -> C -> A`).
    3. Dynamic `OrderSet` generation with `fields="__all__"` and `exclude=[...]`.
  - All 3 tests passed cleanly.
- **Focused test execution:**
  - `uv run pytest tests/orders/test_factories.py --no-cov`: 28 passed.
  - `uv run pytest tests/orders/ --no-cov`: 165 passed.
- **Format and lint hygiene:**
  - `uv run ruff format --check .`: all files formatted.
  - `uv run ruff check .`: all checks passed.
  - `uv run python scripts/check_trailing_commas.py`: 0 files changed.
- **Conclusion:** Verification complete. Status set to `verified`.

