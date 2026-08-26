# Review: `django_strawberry_framework/optimizer/nested_planner.py`

Status: verified

## Understanding

`nested_planner.py` is the transactional planner for nested Relay connection selections. The general walker (`walker.py`) normalizes GraphQL field selections and delegates recognized nested connection fields to `plan_connection_relation`.

Key responsibilities and traced paths:
1. **Pagination Normalization and Keyset Integration:** Extracts pagination arguments (`first`, `last`, `after`, `before`), coerces GraphQL AST integer literal strings via `_coerce_pagination_int`, and derives window slices. When `cursor_field` is declared on the target definition (`_keyset_cursor_context`), decodes value cursors with `decode_keyset_cursor` and resolves forward-only bounds via `derive_keyset_window_bounds`. Otherwise, delegates to `derive_connection_window_bounds`.
2. **Fallback Classification & Strictness Bookkeeping:** Identifies and classifies unsupported shapes (sidecars like `filter`/`orderBy`, conflicting arguments on merged alias subtrees, backward/inverted keyset/offset intervals `UnwindowableConnection`, `last: 0` reversed quirks, unwindowable child querysets, unwindowable relation joins). Accurately records resolver identities in `planned_resolver_keys` for valid planned windows and malformed pagination (ensuring GraphQL validation errors raise at field locality without being masked by strictness), while leaving unwindowable fallback shapes unrecorded so per-parent fallback execution remains strictness-visible.
3. **Child Queryset Construction & Throwaway Sub-Plan:** Builds child querysets using the list prefetch helpers against an isolated throwaway `OptimizationPlan`. Defers absorbing child metadata (resolver keys, fk-id elisions, cacheable flags) into the parent plan until a strategy actually accepts the window, preventing partial directives from leaking on refusal.
4. **Ordering & Minimal Window Projections:** Derives deterministic total order via `effective_connection_order`. For scalar-only selections (`pageInfo`/`totalCount` without `edges { node }`), applies `_project_scalar_only_window` to load only pk, prefetch attach columns, and local ordering columns. For keyset connections with node selections, extends `.only()`/`.defer()` projections via `_extend_only_projection` so cursor columns survive column masking without N+1 lazy loads.
5. **Strategy Dispatch & Composite-Index Advisory:** Dispatches `NestedConnectionRequest` to the resolved strategy (`WindowedFetchStrategy`, `LateralJoinFetchStrategy`, or custom). Upon the first accepted window, runs `_advise_composite_index` to verify whether represented physical indexes (`Meta.indexes`, `UniqueConstraint`, `unique_together`, `db_index`/`pk`/`unique`) cover the window partition and ordering columns, respecting fail-soft tri-state rules for non-B-tree indexes, partial/expression indexes, and multi-backend index ordering capabilities.

## Verification

Examined test suites:
- `tests/optimizer/test_nested_index_advisory.py`: Comprehensive coverage of index coverage classification (`_INDEX_COVERED`, `_INDEX_ABSENT`, `_INDEX_UNKNOWN`), multi-backend column ordering checks, B-tree type filtering, expression/partial constraint handling, and LRU cache dedup (`clear_index_advisory_dedup`).
- `tests/optimizer/test_walker.py`: Tests `_plan_nested_connection_relation`, divergent key window generation (`_divergent_key_windows`), scalar-only projections, async generic relation execution without early sync `ContentType` queries, strategy refusal/acceptance throwaway plan isolation, and fallback behavior.
- `tests/optimizer/test_nested_fetch.py`: Verifies `NestedConnectionPlanResult` handling, strategy dispatch, and windowed/lateral fetch execution.
- `tests/test_keyset_connection.py`: Verifies cursor-based pagination integration with `nested_planner.py`.

Focused test runs:
- `uv run pytest tests/optimizer/test_nested_index_advisory.py tests/optimizer/test_nested_fetch.py tests/optimizer/test_walker.py tests/test_keyset_connection.py --no-cov` passed 295 tests.

## Improvements

### High

None.

### Medium

None.

### Low

- **Observation:** Stuttering duplicate word `"composite-index composite-index"` in the comment above the strategy dispatch loop in `plan_connection_relation`.
- **Evidence:** `nested_planner.py:1370-1371` contained `"The composite-index composite-index advisory is likewise field-static"`.
- **Impact:** Minor code comment readability imperfection.
- **Recommendation:** Clean up the duplicate word in the comment.
- **Proof:** Comment updated; linter and test suite pass.

## Summary

`nested_planner.py` provides clean, robust, and transactional planning for nested Relay connections. It encapsulates pagination normalization, fail-soft index advisory checks, throwaway sub-plan isolation, and keyset cursor-column management with extensive test coverage across unit and integration layers.

## Implementation (Worker 1)

- Changed files:
  - `django_strawberry_framework/optimizer/nested_planner.py`: Fixed duplicated word `"composite-index"` in doc comment.
- Permanent tests and pinned behavior: Existing test matrix in `tests/optimizer/test_nested_index_advisory.py`, `tests/optimizer/test_walker.py`, and `tests/optimizer/test_nested_fetch.py` fully pins all behavior including pagination slicing, keyset cursor context, scalar-only window projection, fail-soft index advisories, and transactional plan isolation.
- Verification: Ran `uv run pytest tests/optimizer/test_nested_index_advisory.py tests/optimizer/test_nested_fetch.py tests/optimizer/test_walker.py tests/test_keyset_connection.py --no-cov` (295 passed).
- Formatter and linter results: `uv run ruff format .` and `uv run ruff check --fix .` passed cleanly with 0 errors.
- Changelog: Does not merit a changelog entry (comment-only change).

## Independent verification (Worker 2)

- Re-traced core pathways through `plan_connection_relation`:
  - **Pagination argument extraction & keyset integration:** Verified `_coerce_pagination_int`, `_connection_window_slice_from_arguments`, `_keyset_cursor_context`, and `_keyset_window_slice_from_arguments`. Keyset cursor context properly decodes value cursors and derives bounds through `derive_keyset_window_bounds`.
  - **Fallback classification & strictness recording:** Verified sidecar checking (`has_connection_sidecar_kwargs`), `UnwindowableConnection` detection, `last: 0` reverse quirk handling, conflicting argument handling, and join windowability checks. Planned windows and malformed pagination record identities in `planned_resolver_keys` so GraphQL validation errors raise at field locality without being masked by strictness, whereas unwindowable fallbacks omit them so per-parent execution is strictness-visible.
  - **Throwaway sub-plan isolation:** Verified that child querysets are built against an isolated throwaway `sub_plan = OptimizationPlan()` and child metadata is merged into the parent plan only upon strategy acceptance (`plan.merge_metadata_from(sub_plan)`).
  - **Ordering derivation & projection handling:** Confirmed `effective_connection_order(...)` integration. Verified that scalar-only selections unwrap to empty node children and receive `_project_scalar_only_window(...)` (loading only pk, prefetch attach columns, and local ordering columns while respecting the `enable_only` gate). Confirmed that keyset selections run `_extend_only_projection(...)` to ensure cursor columns survive `.only()`/`.defer()` projections without N+1 lazy loads.
  - **Strategy dispatch & composite-index advisory:** Confirmed `NestedConnectionRequest` construction and dispatch to `_select_nested_strategy(...)`. Verified `_advise_composite_index` fail-soft tri-state logic (`_INDEX_COVERED`, `_INDEX_ABSENT`, `_INDEX_UNKNOWN`), multi-backend column ordering checks, B-tree type filtering, expression/partial constraint handling, and bounded LRU dedup (`_index_advisory_already_emitted`).
- Checked findings and changes against implementation and evidence:
  - Confirmed the comment cleanup at line 1370 removes the duplicate word `"composite-index"` cleanly.
  - Scoped diff contains no unintended changes.
- Tested behavior:
  - Focused test run: `uv run pytest tests/optimizer/test_nested_index_advisory.py tests/optimizer/test_nested_fetch.py tests/optimizer/test_walker.py tests/test_keyset_connection.py --no-cov` (295 passed).
  - Executed disposable scratch test in `docs/review/temp-tests/nested_planner/test_nested_planner_verifier.py` validating `_project_scalar_only_window` with `enable_only=True/False`, `_extend_only_projection` with `.only()`/`.defer()`, and `_index_coverage` tri-state classifications. Cleaned up scratch files.
- Status: verified.
