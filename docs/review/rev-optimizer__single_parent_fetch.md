# Review: `django_strawberry_framework/optimizer/single_parent_fetch.py`

Status: verified

## Understanding

`django_strawberry_framework/optimizer/single_parent_fetch.py` implements a runtime-only degenerate fast path for the windowed nested prefetch strategy:

1. **Core Problem & Responsibility**:
   - The windowed nested-connection strategy (`plans.py::apply_window_pagination`, using `ROW_NUMBER() OVER (PARTITION BY fk)`) executes a single query for N parents, but lacks SQL `LIMIT` pushdown. When the prefetch-injected parent `IN` list contains exactly one parent, the database numbers every child row in the partition before filtering by row number.
   - When a parent has many children (e.g. 50k) and requests `first: 10`, the window query scans all 50k rows; an equivalent plain query `WHERE fk = x ORDER BY ... LIMIT 10` is an efficient bounded index walk.
   - This module provides a safe, fail-closed runtime fast path: when the injected parent list has length 1 and the query matches the planned count-free plain first page (identical order, annotations, projection, and join graph), `_fetch_single_parent_rows` executes the plain filtered `LIMIT` query using the pristine child clone and synthesizes `_dst_row_number` (1..N) in Python.
   - Any unrecognized shape, multi-parent prefetch, or configuration change returns `None`, seamlessly falling back to executing the planned windowed query via `super()._fetch_all()` (strict performance degradation, never a correctness cliff).

2. **Components & Interfaces**:
   - `SingleParentWindowSpec`: Frozen dataclass resolved once at plan time by `single_parent_spec(request)`. Captures `pristine_child_queryset`, `order_by`, `parent_link_attname`, `parent_link_column`, `parent_link_table`, `fetch_limit` (page limit + sentinel if `next_page_probe=True`), `select_related`, and `select_columns`.
   - `single_parent_spec(request)`: Evaluates plan-time eligibility. Rejects keyset seeks (`keyset_seek is not None`), counted queries (`with_total_count`), reverse pagination (`reverse`), non-standard `QuerySet` subclasses, non-`DIRECT_FK` joins or unresolvable parent link fields, and non-first-page ranges.
   - `SingleParentWindowQuerySet`: Subclass of `RecognizedFetchQuerySet` carrying `_dst_single_parent_spec` across query cloning (`_clone`) and dispatching `_fetch_recognized_rows()` to `_fetch_single_parent_rows`.
   - `_single_parent_where_ids(where, spec)`: Inspects the root `WhereNode` to confirm it consists solely of window quals and at most one parent `IN` lookup on the expected column/table, extracting the raw parent IDs.
   - `_fetch_single_parent_rows(queryset)`: Validates runtime query state against the plan-frozen spec (checking `single_parent_fast_path_setting()`, unwindowable reasons, extra selects/tables/group_by, ordering, annotation set `{WINDOW_ROW_NUMBER}`, window predicate signature match, `select_related` and `_select_columns` parity, and single deduplicated parent ID), executes the filtered `LIMIT` query on `pristine_child_queryset.using(queryset.db)`, and stamps `WINDOW_ROW_NUMBER` on each returned row.

3. **Invariants & Safety Guards**:
   - `node(id:)` queries do not reach window prefetch today (`_resolve_node_default` returns `qs.first()`), so the fast path targets general single-parent connection prefetches (such as root filtered connections or connections under a single parent).
   - M2M / `THROUGH_TABLE` relations are excluded in v1 because Django attaches M2M rows via `extra(select={"_prefetch_related_val_*": ...})`, which a plain child clone cannot reproduce.
   - `WINDOW_TOTAL_COUNT` is never set on fast-path rows, preserving connection resolution logic that detects probe rows.

## Verification

1. **Existing Test Coverage**:
   - `tests/optimizer/test_single_parent_fetch.py`: 28 unit tests exercising spec generation, eligibility rejections, fetch-time mutation rejections, forward row number synthesis, probe overfetching, parent ID deduplication, nested prefetch preservation, and windowed fallback.
   - `examples/fakeshop/test_query/test_single_parent_fastpath_api.py`: 10 live GraphQL HTTP integration tests verifying fast-path execution (omission of `OVER (` SQL) for plain first pages, probe sentinel overfetching, keyset cursor round-tripping, and graceful fallback to `OVER (` for `totalCount`, seek offsets, multiple parents, visibility filtering, settings toggle, and M2M relations.

2. **Scratch Test Experiments**:
   - `docs/review/temp-tests/optimizer_single_parent_fetch/test_scratch.py` (5 passed in 2.89s):
     - Verified `single_parent_spec` rejection when `parent_link_field` is `None` on generic relations.
     - Verified `_single_parent_where_ids` handling of empty and non-matching `WhereNode` children.
     - Verified database alias routing (`.using("default")`) propagation into child query execution.
     - Verified single parent with zero child rows returning an empty list without window overhead.
     - Verified `_deduplicate_parent_ids` behavior with unhashable and `None` parent ID lists.

3. **Target Test Execution & Coverage**:
   - `uv run pytest tests/optimizer/test_single_parent_fetch.py examples/fakeshop/test_query/test_single_parent_fastpath_api.py --cov=django_strawberry_framework.optimizer.single_parent_fetch`: 48 passed in 3.56s with 100% statement coverage (90/90 statements).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/optimizer/single_parent_fetch.py` is a robust, well-isolated, and strictly fail-closed optimization. It safely replaces expensive partition window scans with index-bounded single-parent `LIMIT` queries while preserving exact projection, ordering, and nested prefetches, backed by comprehensive unit and live GraphQL HTTP test suites with 100% coverage.

## Implementation (Worker 1)

- **Changed files**:
  - `None — zero-edit cycle` (target `django_strawberry_framework/optimizer/single_parent_fetch.py` is fully verified, bug-free, and adheres to all repository invariants).
- **Permanent tests**:
  - `tests/optimizer/test_single_parent_fetch.py` (28 tests) and `examples/fakeshop/test_query/test_single_parent_fastpath_api.py` (10 tests) pin all plan-time eligibility, runtime validation, fallback semantics, and GraphQL HTTP execution behaviors.
- **Scratch verification**:
  - `docs/review/temp-tests/optimizer_single_parent_fetch/test_scratch.py` (5 passed in 2.89s) probing generic relations, empty WHERE children, multi-DB alias propagation, zero-child queries, and unhashable ID deduplication.
- **Formatter and linter**:
  - No edits made to tracked source files (zero-edit cycle).
- **Evidence for rejected findings**:
  - None.
- **Changelog**:
  - No changelog entry required (zero-edit review cycle).

## Independent verification (Worker 2)

- **Trace & Behavior**:
  - Re-traced `single_parent_spec(request)` eligibility: verified strict gatekeeping requiring count-free plain first pages (`with_total_count=False`, `reverse=False`, `keyset_seek=None`, positive bounded limit, `offset=0`), standard `QuerySet` type, and `DIRECT_FK` join shape with resolved `parent_link_field`.
  - Re-traced `SingleParentWindowQuerySet`: confirmed class rebind and `_dst_spec_attr` propagation across `_clone()`, delegating `_fetch_recognized_rows` to `_fetch_single_parent_rows`.
  - Re-traced `_single_parent_where_ids`: confirmed tree inspection requiring non-negated `AND` root, allowing only window quals and exactly one matching `__in` parent lookup on the target column/table.
  - Re-traced `_fetch_single_parent_rows`: confirmed exhaustive runtime guards (dynamic `single_parent_fast_path_setting()` setting check, unwindowable reasons, query mutation checks, ordering parity, annotation set `{WINDOW_ROW_NUMBER}`, window predicate signature match against `_dst_window_signature`, `select_related` and column projection parity against `spec`, and single parent deduplication via `_deduplicate_parent_ids`).
  - Re-traced row synthesis and database routing: confirmed `.using(queryset.db)` propagation, filtered limit re-query execution, sequential 1-indexed `WINDOW_ROW_NUMBER` stamping (`1..N`), omission of `WINDOW_TOTAL_COUNT` for sentinel probe detection, and seamless fallback to windowed execution when any check returns `None`.
- **Zero-edit confirmation**:
  - `git diff 12779c99 -- django_strawberry_framework/optimizer/single_parent_fetch.py` is completely clean (zero edits).
- **Test execution**:
  - Executed target test suites: `tests/optimizer/test_single_parent_fetch.py` and `examples/fakeshop/test_query/test_single_parent_fastpath_api.py` (48 passed).
  - Executed scratch tests: `docs/review/temp-tests/optimizer_single_parent_fetch/test_scratch.py` (5 passed).
- **Conclusion**:
  - Target module is completely sound, fail-closed, and adheres to all architectural constraints and contracts. Verified without reservations.

