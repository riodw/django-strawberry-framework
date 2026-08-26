# Review: `django_strawberry_framework/filters/factories.py`

Status: verified

## Understanding

`django_strawberry_framework/filters/factories.py` implements Layer 5 (the `FilterArgumentsFactory` BFS input generation pipeline) and Layer 6 (the module-level dynamic-`FilterSet` cache and `get_filterset_class` factory) of the spec-027 filtering subsystem.

### Key Responsibilities and Symbols:
1. **`FilterArgumentsFactory`**:
   - Direct subclass of `GeneratedInputArgumentsFactory` (`utils/inputs.py`).
   - Owns the filter-family class-level type cache `input_object_types` and duplicate-name collision registry `_type_filterset_registry`.
   - Traverses reachable `RelatedFilter` relations using deterministic FIFO BFS walk with cycle detection and diamond-graph deduplication.
   - Specializes `_build_input_triples` by combining field triples from `_build_input_fields` with the filter operator bag `_build_logic_fields` (`and_`, `or_`, `not_`).
   - Rejects subclassing via `__init_subclass__` on the base to prevent shared mutable cache contamination.
   - Invoked during `types/finalizer.py` phase 2.5 sidecar set binding.
2. **`_dynamic_filterset_cache` & `_RESERVED_FACTORY_KEYS`**:
   - Module-level dictionary cache keyed by canonical metadata tuples produced by `make_set_meta_cache_key`.
   - Strips reserved keyword arguments (`filterset_base_class`) to prevent collision with synthetic class generation.
3. **`get_filterset_class`**:
   - Thin wrapper around `_get_filterset_class` created via `make_dynamic_set_getter` (`utils/inputs.py`).
   - Returns pre-declared `filterset_class` unchanged when supplied; otherwise normalizes metadata (including `filter_fields` alias, unhashable meta structures, and sorted sequences) and mints / caches a synthetic `FilterSet` subclass (`<Model>AutoFilter`).

## Verification

1. **Dependency and Caller Mapping**:
   - `django_strawberry_framework/types/finalizer.py`: verified consumption of `FilterArgumentsFactory(filterset_cls).arguments` during phase 2.5 subpass 4.
   - `django_strawberry_framework/filters/inputs.py`: verified integration of `_build_input_fields` and `_build_logic_fields`.
   - `django_strawberry_framework/orders/factories.py`: verified architectural parity with `OrderArgumentsFactory` and `get_orderset_class`.
   - `django_strawberry_framework/utils/inputs.py`: verified shared substrate contracts in `GeneratedInputArgumentsFactory`, `make_dynamic_set_getter`, `normalize_set_meta_for_factory`, and `make_set_meta_cache_key`.
2. **Existing Test Suite Audit**:
   - `tests/filters/test_factories.py`: read all 750+ lines and verified test assertions across BFS traversal, cycles, diamonds, collisions, idempotency, Relay annotations, cache keying, alias normalization, unhashable metadata, and subclass rejection.
   - `tests/filters/test_finalizer.py`: verified phase 2.5 materialization and cache clear interactions.
   - `tests/orders/test_composition.py`: verified filter/order cache isolation.
3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/filters__factories/test_scratch_factories.py` testing empty `FilterSet` logic field generation, `RelatedFilter(None, ...)` placeholder traversal skipping, and dynamic `FilterSet` BFS input creation.
   - Ran `uv run pytest docs/review/temp-tests/filters__factories/test_scratch_factories.py --no-cov`: 3 passed.
4. **Focused Test Runs**:
   - `uv run pytest tests/filters/test_factories.py --no-cov`: 38 passed.
   - `uv run pytest tests/filters/ --no-cov`: 546 passed across the entire filter subsystem.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/filters/factories.py` is clean, robust, and correctly integrates with the shared `utils/inputs.py` substrate. The target file requires no modifications. Edge-case test coverage in `tests/filters/test_factories.py` was permanently expanded to pin empty `FilterSet` logic field emission, placeholder `RelatedFilter` skipping, and dynamic `FilterSet` BFS input creation.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/filters/test_factories.py`: added edge case tests covering empty `FilterSet` logic fields emission, placeholder `RelatedFilter(None, ...)` target skipping during BFS traversal, and dynamic `FilterSet` BFS input creation.
  - Scoped diff against baseline `12779c99` for `django_strawberry_framework/filters/factories.py` is zero-edit (0 diff).
- **Permanent tests and pinned behavior:**
  - `tests/filters/test_factories.py` (38 tests total):
    - Pins BFS walk visiting every reachable FilterSet across `RelatedFilter` chains.
    - Pins self-referential cycle and diamond DAG deduplication.
    - Pins duplicate class name collision raises with actionable diagnostics.
    - Pins flattened field name and camel-case GraphQL name collision rejections.
    - Pins idempotent repeated `.arguments` accesses.
    - Pins Relay lazy reference annotations vs scalar/numeric annotations.
    - Pins `get_filterset_class` explicit pass-through, metadata normalization, `filter_fields` alias collapsing, and unhashable metadata handling.
    - Pins subclassing rejection on `FilterArgumentsFactory`.
    - Pins empty `FilterSet` logic fields emission (`and_`, `or_`, `not_`).
    - Pins `RelatedFilter(None, ...)` placeholder target skipping.
    - Pins BFS input class generation for dynamic `get_filterset_class` FilterSets.
- **Scratch verification:**
  - `docs/review/temp-tests/filters__factories/test_scratch_factories.py` passed (3/3 tests).
  - `uv run pytest tests/filters/test_factories.py --no-cov` passed (38/38 tests).
  - `uv run pytest tests/filters/ --no-cov` passed (546/546 tests).
- **Formatter and linter results:**
  - `uv run ruff format .` passed with 0 errors (1 file reformatted).
  - `uv run ruff check --fix .` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No.

## Independent verification (Worker 2)

- **Target production file diff check:** Confirmed `django_strawberry_framework/filters/factories.py` is zero-edit against baseline `12779c99` (`git diff 12779c99 -- django_strawberry_framework/filters/factories.py` returned 0 diff).
- **System and Behavior Re-tracing:**
  - Traced `FilterArgumentsFactory` subclassing `GeneratedInputArgumentsFactory` in `django_strawberry_framework/utils/inputs.py`, verifying class-level type cache `input_object_types` and duplicate name collision registry `_type_filterset_registry`.
  - Traced `_build_input_triples` integration combining `_build_input_fields` (from `django_strawberry_framework/filters/inputs.py`) and `_build_logic_fields` (`and_`, `or_`, `not_`).
  - Traced `get_filterset_class` dynamic factory created via `make_dynamic_set_getter`, verifying cache key normalization via `make_set_meta_cache_key`, `filter_fields` alias normalization, and `filterset_base_class` reserved keyword argument stripping.
  - Verified architectural parity with `django_strawberry_framework/orders/factories.py`.
- **Independent Scratch Tests:**
  - Created `docs/review/temp-tests/filters__factories/test_independent_scratch_factories.py` covering:
    - 4-tier deep BFS `RelatedFilter` chain resolution (`Branch -> Loan -> Book -> Shelf`).
    - Dynamic `FilterSet` coexistence across different Django models (`CategoryAutoFilter` and `ItemAutoFilter`).
    - Static `FilterSet` targeting dynamic `FilterSet` via `RelatedFilter`.
    - Dynamic factory validation errors on missing `model` or non-Django model.
    - Subclassing prevention guard raising `TypeError`.
  - Executed `uv run pytest docs/review/temp-tests/filters__factories/ --no-cov`: 8/8 passed.
- **Permanent and Focused Test Runs:**
  - `uv run pytest tests/filters/test_factories.py --no-cov`: 38/38 passed.
  - `uv run pytest tests/filters/ --no-cov`: 546/546 passed across the entire filters subsystem.
- **Linter and Governance Checks:**
  - `uv run ruff check .`: passed (all checks passed).
  - `uv run python scripts/check_trailing_commas.py`: passed (0 files modified).
- **Conclusion:** `django_strawberry_framework/filters/factories.py` is complete, robust, and correctly verified. Status updated to `verified`.

