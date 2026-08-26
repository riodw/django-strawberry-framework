# Review: `django_strawberry_framework/utils/connections.py`

Status: verified

## Understanding

`django_strawberry_framework/utils/connections.py` is the cycle-safe foundation module defining shared contracts for connection pagination, sidecar argument handling, fetch modes, and windowed prefetch bounds. It is consumed symmetrically by both the plan-time optimizer planner (`optimizer/walker.py`, `optimizer/nested_planner.py`, `optimizer/plans.py`, `optimizer/lateral_fetch.py`, `optimizer/nested_fetch.py`, `optimizer/single_parent_fetch.py`) and the resolve-time Relay connection execution pipeline (`connection.py`, `keyset.py`).

It owns:
1. **Connection Sidecar Keyword Contract**:
   - `CONNECTION_FILTER_KWARG` (`"filter"`), `CONNECTION_ORDER_KWARG` (`"order_by"`), `CONNECTION_ORDER_KWARG_GRAPHQL` (`"orderBy"`), and `CONNECTION_SIDECAR_KWARGS`.
   - `connection_sidecar_inputs_from_kwargs(kwargs)`: normalizes both Python kwarg keys (`order_by`) from resolvers and raw GraphQL AST converted argument keys (`orderBy`) from the walker into `(filter_input, order_by_input)`.
   - `has_connection_sidecar_input(*, filter_input, order_by_input)` and `has_connection_sidecar_kwargs(kwargs)`: single-site predicates determining whether sidecar inputs are present (ignoring `None` and `strawberry.UNSET`), ensuring planner fallback decisions and resolver consumption gates never drift.
2. **Unwindowable Connection Sentinel**:
   - `UnwindowableConnection`: internal control-flow exception raised when a pagination shape cannot be represented by SQL row-number windows without altering results (e.g., `after` + `last` offset-bearing backward windows, inverted intervals with negative `expected`, or backward keyset shapes). Allows the optimizer planner to treat these valid shapes as Decision-6 per-parent fallbacks while remaining visible to strictness checks.
3. **Fetch Modes and Window Range Planning**:
   - `FetchMode` enum (`COUNTED`, `PROBED`, `CONSTANT_FALSE`, `NONE`): single source of truth for count and probe strategy.
   - `_is_probe_shape` and `is_ambiguous_empty_window`: shape classification for `hasNextPage` N+1 probe eligibility and marker row insertion for ambiguous empty pages (such as `first: 0` or overshot `after:` offsets).
   - `WindowRangePlan`: immutable dataclass capturing window boundaries (`lower_bound`, `upper_bound`), sentinel arithmetic (`_probe_increment`, `fetch_upper_bound`, `fetch_limit`), marker flags (`add_marker_rows`), probe flags (`next_page_probe`), and mapping to `FetchMode`.
   - `window_range_plan(...)`: constructor normalizing `limit=sys.maxsize` to `None`, guarding against negative offsets/limits (`OptimizerError`), composing marker rows with probe sentinels, and configuring keyset-counted exclusive bounds.
   - `assert_window_fetch_mode` / `assert_window_fetch_mode_for`: loud invariant assertions enforcing probe XOR count mutual exclusivity on resolved window plans and raw window dataclasses.
   - `split_window_rows(rows, range_plan, *, row_number)`: render-agnostic row partitioner splitting retrieved rows into actual page rows and dropped sentinels/markers, returning `(page_rows, probe_row_seen)` where `probe_row_seen` determines `hasNextPage`.
4. **Window Bounds Derivation**:
   - `ConnectionWindowBounds`: immutable dataclass `(offset, limit, reverse)`.
   - `derive_connection_window_bounds(info, *, before, after, first, last, max_results)`: executes Strawberry's `SliceMetadata.from_arguments` clamped against request-level `ResourcePolicy.max_page_size`, handling `last`-only reverse window bounds, negative cursor detection (`TypeError`), and unwindowable shapes (`UnwindowableConnection`).
   - `_RELAY_MAX_RESULTS_DEFAULT` (100), `resolve_relay_max_results(info, max_results)`, `assert_relay_pagination_bound(argument, value, *, cap)`: shared pagination cap resolution and bounds validation used by keyset pagination to maintain strict parity with `SliceMetadata` error messages.
   - `derive_keyset_window_bounds(info, *, before, after, first, last, max_results)`: keyset twin of offset bounds derivation, enforcing forward-only bounds at offset 0 and delegating backward/before shapes to `UnwindowableConnection`.

## Verification

1. **Traced connections across the codebase**:
   - `connection.py` imports `CONNECTION_FILTER_KWARG`, `CONNECTION_ORDER_KWARG`, `UnwindowableConnection`, `assert_relay_pagination_bound`, `connection_sidecar_inputs_from_kwargs`, `derive_connection_window_bounds`, `derive_keyset_window_bounds`, `has_connection_sidecar_input`, `resolve_relay_max_results`, `split_window_rows`, `window_range_plan`.
   - `optimizer/nested_planner.py` imports `ConnectionWindowBounds`, `FetchMode`, `UnwindowableConnection`, `connection_sidecar_inputs_from_kwargs`, `derive_connection_window_bounds`, `derive_keyset_window_bounds`, `has_connection_sidecar_kwargs`, `window_range_plan`.
   - `optimizer/plans.py`, `optimizer/lateral_fetch.py`, `optimizer/nested_fetch.py`, and `optimizer/single_parent_fetch.py` import `assert_window_fetch_mode`, `assert_window_fetch_mode_for`, `window_range_plan`.
   - `tests/test_keyset.py`, `tests/test_keyset_connection.py`, and `tests/test_relay_connection.py` verify keyset bounds, cursor fallback signals, and window resolution.
2. **Examined existing test suite**:
   - `tests/utils/test_connections.py` (50 tests): covers `last`-only bounds, `first` forward bounds, request policy max page size ceilings, `before` + `last` forward offset, `after` + `last` unwindowable fallback, inverted interval unwindowable fallback, forged negative cursor `TypeError`s, negative direct bounds `OptimizerError`s, sidecar kwarg extraction (Python and camelCase GraphQL vocabularies), `assert_relay_pagination_bound` error parity, probe shapes and fetch modes table, probe/count mutual exclusivity, `split_window_rows` (marker, probe, plain, composed offset probe, generators), `strawberry.UNSET` handling, and keyset bounds derivation.
   - Executed: `uv run pytest tests/utils/test_connections.py --no-cov` (50 passed).
3. **Scratch verification**:
   - Created `docs/review/temp-tests/utils_connections/test_connections_scratch.py` (6 tests) probing sidecar kwarg extraction/precedence, `UnwindowableConnection` type hierarchy, `WindowRangePlan` invariants (`sys.maxsize`, `keyset_counted`), `FetchMode` four-way mapping, `split_window_rows` marker/probe decomposition, and `resolve_relay_max_results` policy clamping.
   - Executed: `uv run pytest docs/review/temp-tests/utils_connections/test_connections_scratch.py --no-cov` (6 passed).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/utils/connections.py` is a clean, robust, and well-tested cycle-safe foundation. It provides unambiguous mathematical contracts for pagination bounds, marker row disambiguation, N+1 probe overfetching, and sidecar keyword synchronization between the optimizer planner and Relay runtime resolvers. All edge cases (such as inverted slices, forged cursors, policy ceilings, and `strawberry.UNSET` sentinels) are comprehensively handled. No defects or design improvements were identified.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:** None (zero-edit cycle). Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/utils/connections.py` is empty.
- **Permanent tests and pinned behavior:**
  - `tests/utils/test_connections.py` (50 tests) thoroughly pins sidecar kwarg extraction, `UnwindowableConnection` fallback signals, window range bounds, probe XOR count mutual exclusivity, `split_window_rows` sentinel and marker row stripping, and `derive_connection_window_bounds` / `derive_keyset_window_bounds` policy enforcement.
- **Scratch verification:**
  - `docs/review/temp-tests/utils_connections/test_connections_scratch.py` passed (6/6 tests), verifying sidecar kwargs handling, unwindowable exceptions, range plan bounds, fetch mode resolution, and row splitting across composed shapes.
- **Formatter and linter results:**
  - Zero-edit cycle; existing code already formatted and clean.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- Verified zero-edit status against baseline `HEAD` (`12779c99`) for `django_strawberry_framework/utils/connections.py` (`git diff 12779c99 -- django_strawberry_framework/utils/connections.py` is clean).
- Re-traced all contracts across plan-time and resolve-time call sites:
  1. `connection_sidecar_inputs_from_kwargs` and `has_connection_sidecar_input` correctly reconcile Python snake_case (`order_by`) and GraphQL camelCase (`orderBy`), handling `None` and `strawberry.UNSET` without leaking dead windows into the planner.
  2. `UnwindowableConnection` acts as an internal control-flow signal (distinct from `OptimizerError` and `ValueError`/`TypeError`), ensuring backward offset shapes (`after` + `last`), inverted slices, and backward keyset shapes drop down to per-parent fallbacks and remain detectable by strictness checks.
  3. `FetchMode` cleanly partitions into `COUNTED`, `PROBED`, `CONSTANT_FALSE`, and `NONE`, with `assert_window_fetch_mode` strictly enforcing probe XOR count mutual exclusivity.
  4. `split_window_rows` accurately decomposes retrieved rows into page content and marker/sentinel rows across all window shapes, including composed offset probe pages.
  5. `derive_connection_window_bounds` and `derive_keyset_window_bounds` reliably clamp against `ResourcePolicy.max_page_size` and maintain exact parity with Strawberry's `SliceMetadata` error messages.
- Ran tests:
  - `uv run pytest tests/utils/test_connections.py --no-cov`: 50 passed.
  - `uv run pytest docs/review/temp-tests/utils_connections/test_connections_scratch.py --no-cov`: 6 passed.
- All findings and tests confirmed accurate. Target verified.
