# Review: `django_strawberry_framework/types/resolvers.py`

Status: verified

## Understanding

`django_strawberry_framework/types/resolvers.py` generates and attaches cardinality-aware relation resolvers and file/image parent resolvers to `DjangoType` classes during schema finalization (Phase 2):

1. **Relation Resolvers (`_attach_relation_resolvers`, `_make_relation_resolver`)**:
   - **Many-Side (M2M, Reverse FK)**: `many_resolver` directly returns `_prefetched_objects_cache` when populated (skipping QuerySet cloning), bounds rows via `bounded_rows`, and evaluates through `apply_type_visibility_sync`/`apply_type_visibility_async` if the target type declares custom visibility. For unprefetched async access, streams rows asynchronously via `bounded_rows_async`.
   - **Reverse OneToOne**: `reverse_one_to_one_resolver` catches `<RelatedModel>.DoesNotExist` (or `AttributeError` fallback) and maps missing reverse rows to `None`. Handles async event-loop lazy loading with `sync_to_async(getattr, thread_sensitive=True)` and applies target visibility hooks.
   - **Forward FK / Forward OneToOne**: `forward_resolver` supports B2 FK-id elision via `_build_fk_id_stub`, constructing unpersisted target model instances (`related_model(pk=related_id)`) with proper router read DB assignment (`router.db_for_read`) to avoid querying when only the related object's PK is selected. Falls back loudly when consumer `.only(...)` defers the FK column (`_FK_ELISION_UNSAFE`). Dispatches unloaded single-relation reads under async execution via `sync_to_async`.

2. **N+1 Strictness Guard (`_check_n1`)**:
   - Centralizes N+1 query detection across all relation resolution pathways.
   - Evaluates active strictness (`_strictness_for`) from execution-scoped `ContextVar` or context stash (`DST_OPTIMIZER_STRICTNESS`), short-circuiting when `"off"`.
   - Checks if relation is planned (`_relation_is_planned`) via `DST_OPTIMIZER_PLANNED` or scoped relations set (`relation_is_optimizer_scoped`).
   - For unplanned relations, probes Django caches (`_will_lazy_load_many` on `_prefetched_objects_cache`, `_will_lazy_load_single` on `__dict__` and `_state.fields_cache`, or `kind="connection_to_attr"` for windowed-prefetch `to_attr` presence).
   - Raises `OptimizerError` on `"raise"` or logs warning on `"warn"`.

3. **File & Image Resolvers (`_attach_file_resolvers`, `_make_file_resolver`)**:
   - Attaches parent resolvers to `FileField` / `ImageField` columns (Phase 2).
   - Evaluates the `FieldFile` descriptor's truthiness, returning `None` for falsy/unattached files and the bound `FieldFile` instance when present (delegating subfield resolution and storage failure isolation to `DjangoFileType`/`DjangoImageType`).

## Verification

1. **Static & Structural Audit**:
   - Verified that `resolvers.py` avoids importing from `base.py` to prevent circular dependencies at `DjangoType.__init_subclass__` and finalization time.
   - Audited exception resilience: `_build_fk_id_stub` defensively catches exceptions during stub construction, `_fk_attname_is_deferred` handles non-Django doubles and hostile `get_deferred_fields`, and `reverse_one_to_one_resolver` handles missing reverse rows.
   - Checked N+1 strictness and optimizer integration: verified precomputed resolver keys, elision safety flags (`force_unplanned`), and connection-agnostic multi-db routing.

2. **Scratch Experiments**:
   - Created and executed `docs/review/temp-tests/types_resolvers/test_scratch.py` validating sentinels (`_EMPTY_ELISIONS`, `_PLAN_UNREAD`, `_FK_ELISION_UNSAFE`), resolver naming (`_name_resolver`), strictness resolution (`_strictness_for`), lazy-load predicates (`_will_lazy_load_single`, `_will_lazy_load_many`), file resolver nullability, and `_check_n1` raise/warn/silent behavior across standard and connection `to_attr` contracts.

3. **Focused Test Execution**:
   - `uv run pytest tests/types/test_resolvers.py examples/fakeshop/test_query/test_relations_async_api.py --no-cov` (51 passed in 4.37s).
   - Full package coverage for `django_strawberry_framework/types/resolvers.py` confirmed at 100% (288/288 statements).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/types/resolvers.py` provides high-performance, cardinality-aware relation resolution, robust FK-id elision, comprehensive N+1 strictness detection, and secure type visibility enforcement across both synchronous and asynchronous GraphQL operations.

## Implementation (Worker 1)

- **Changed files:**
  - `None — zero-edit cycle` (Scoped diff against `12779c99` for `django_strawberry_framework/types/resolvers.py` is empty).
- **Permanent tests:**
  - `tests/types/test_resolvers.py` (48 tests), `examples/fakeshop/test_query/test_relations_async_api.py` (3 tests), and `tests/optimizer/test_extension.py` thoroughly pin relation resolution, FK-id elision, N+1 strictness checks, multi-database routing, custom visibility scoping, and file/image parent resolvers across sync and async contexts with 100% statement coverage.
- **Verification:**
  - `docs/review/temp-tests/types_resolvers/test_scratch.py` passed (8 tests).
  - Focused suite: `uv run pytest tests/types/test_resolvers.py examples/fakeshop/test_query/test_relations_async_api.py --no-cov` (51 passed in 4.37s).
- **Formatter & Linter:**
  - `None — zero-edit cycle` (no production changes).
- **Changelog:**
  - `None — zero-edit cycle`; no runtime behavior change or public API modification.

## Independent verification (Worker 2)

1. **Scoped Diff & Zero-Edit Confirmation**:
   - Verified that `git diff 12779c99 -- django_strawberry_framework/types/resolvers.py` is empty. The module is fully intact and clean against the review baseline.

2. **System Tracing & Invariant Verification**:
   - **Many-side Resolvers**: Verified that prefetch cache accesses bypass query cloning, apply `bounded_rows`, and enforce custom target visibility hooks when not optimizer-scoped (`_optimizer_scoped_relation`). Unprefetched async relations use `bounded_rows_async` to iterate asynchronously on the event loop.
   - **Reverse OneToOne Resolvers**: Verified that missing reverse relations caught by `DoesNotExist` (or `AttributeError`) safely evaluate to `None`, and unloaded relations under async contexts use `sync_to_async(getattr, thread_sensitive=True)` before checking custom visibility.
   - **Forward FK / OneToOne Resolvers & FK-ID Elision**: Re-checked `_build_fk_id_stub` ensuring database read routing (`router.db_for_read`), state marking (`state.adding = False`), and deferred FK attname fallback detection via `_fk_attname_is_deferred` / `_FK_ELISION_UNSAFE` with `force_unplanned=True` to prevent silent N+1 queries.
   - **N+1 Strictness Guard**: Verified `_check_n1`, supporting both `ContextVar` and stash strictness resolution, multi-channel planned status (`_relation_is_planned`), distinct single vs many cache checks, and windowed prefetch `connection_to_attr` presence probes.
   - **File / Image Resolvers**: Verified `_make_file_resolver` and `_attach_file_resolvers`, ensuring object nullability on falsy `FieldFile` descriptors without clobbering consumer-authored type overrides.

3. **Test Suite Verification**:
   - Executed focused test suite: `uv run pytest tests/types/test_resolvers.py examples/fakeshop/test_query/test_relations_async_api.py --no-cov` (51 passed in 5.12s).
   - Executed scratch suite: `uv run pytest docs/review/temp-tests/types_resolvers/test_scratch.py --no-cov` (8 passed in 1.56s).
   - Zero-edit review cycle verified complete and correct.
