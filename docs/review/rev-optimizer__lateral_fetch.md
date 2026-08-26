# Review: `django_strawberry_framework/optimizer/lateral_fetch.py`

Status: verified

## Understanding

`django_strawberry_framework/optimizer/lateral_fetch.py` implements the PostgreSQL `CROSS JOIN LATERAL` nested-connection fetch strategy, providing $O(\text{parents} \times \text{page})$ pagination query execution for nested Relay connections:

1. **Architecture & Strategy Role**:
   - Implements `NestedConnectionStrategy` via `LateralPrefetchStrategy` (and its singleton `LATERAL_STRATEGY`).
   - Pairs with `NestedConnectionRequest` and `OptimizationPlan` during query planning to produce a `LateralQuerySet` carrying a `LateralWindowSpec`.
   - Generates raw lateral SQL using Postgres `CROSS JOIN LATERAL` and window functions (`ROW_NUMBER() OVER (...)`, optional `COUNT(1) OVER ()`) executed against parent ID arrays (`unnest(%s::<type>[])`) or typed `(VALUES (...))` lists.
   - Preserves complete correctness by embedding the fully valid windowed ORM queryset inside the `LateralQuerySet`. At fetch time, if any condition fails (non-PostgreSQL database router, unrecognized consumer filter, mutated query, or unsupported internal shape), `_fetch_lateral_rows` returns `None` and execution safely falls back to the windowed query.

2. **Core Components**:
   - `LateralWindowSpec`: Immutable frozen dataclass encapsulating all plan-time facts required for SQL generation (model, db table, projection columns and converter fields, deterministic order columns, parent link fields/table/column, through table specs, offset/limit/reverse/total count/next page probe, keyset seek, and single-table visibility WHERE clause). Enforces probe/count mutual exclusion in `__post_init__` via `assert_window_fetch_mode_for`.
   - `build_lateral_sql`: Pure SQL builder that renders the complete lateral SQL query and bound parameter list. Quotes all identifiers via `quote_name`, parameters for parent IDs, limits, offsets, keyset values, and visibility filters. Optimizes forward plain first pages (`first: N`, `offset == 0`) with in-branch `ORDER BY ... LIMIT %s` to enable index-backed costed scans.
   - `LateralQuerySet`: `RecognizedFetchQuerySet` subclass bound with `_dst_lateral_spec` and `_dst_window_signature`, overriding `_fetch_recognized_rows()` to call `_fetch_lateral_rows()`.
   - `_fetch_lateral_rows`: Fetch-time executor that verifies Postgres vendor, confirms exact plan recognition via `_recognize_lateral_fetch`, deduplicates parent IDs via `_deduplicate_parent_ids`, executes raw SQL, applies field/backend converter chains via `_apply_lateral_converters`, and instantiates deferred model instances via `_instantiate_row`.
   - `_recognize_lateral_fetch`: Defensive runtime recognizer verifying query invariants (no unrecognized `select_related`, annotations, extra tables, group by, ordering drifts, or projection changes), validating window predicate signature matches the plan signature via `window_predicate_signature`, extracting parent IDs from the prefetch `__in` qual via `_parent_in_values`, and verifying keyset seek or single-table visibility where clauses.

3. **Inexpressible Shapes & Fallback Behavior**:
   - `_build_lateral_spec` safely returns `None` (downgrading to standard windowed prefetch) for:
     - Counted keyset seeks (where a full partition scan is already required).
     - Querysets with `select_related`, extra annotations, extra tables, or `group_by`.
     - Multi-table, expression, or relation-traversal ordering.
     - Custom `QuerySet` subclasses that would lose clone/manager state on rebind.
     - Composite (columnless) primary keys.
     - Unsupported join shapes or unresolvable through links.
     - Multi-table inheritance parent projections / orderings or unreadable deferred loading.
     - Complex, multi-table, or empty (`.none()`) visibility WHERE clauses.

4. **Safety and Security Invariants**:
   - Full SQL injection immunity: all table and column identifiers are passed through `connection.ops.quote_name`; all parent IDs, row bounds, keyset values, and filter literals are passed as query parameters.
   - Strict degradation: any recognition mismatch, database routing away from PostgreSQL, or unexpected query mutation seamlessly runs the standard ORM windowed query.

## Verification

1. **Existing Permanent Tests**:
   - `tests/optimizer/test_lateral_fetch.py` (92 tests passed in 3.66s) covering:
     - Spec construction for reverse foreign keys (`DIRECT_FK`), forward M2M (`THROUGH_TABLE`), reverse M2M, and join swapping.
     - Plan-time probe and count mutual-exclusion assertion.
     - Keyset seek and single-table visibility WHERE capture and validation.
     - Safe plan-time downgrade for inexpressible shapes (annotations, extra tables, expression ordering, custom queryset subclasses, composite PKs, multi-table inheritance).
     - Pure SQL building for forward pages, count-free pages, next-page probe overfetching, offset shapes, reverse shapes, M2M through joins, typed `VALUES` for non-scalar parent keys, and spliced visibility clauses.
     - `LateralQuerySet` cloning, spec preservation, window signature preservation, and fallback on non-Postgres vendors or missing specs.
     - Fetch-time parent ID extraction, marker OR recognition, reversed window qual recognition, visibility scope byte-equal matching, and fail-closed handling for unrecognized mutations.
     - Window predicate signature determinism, bound discrimination, unbounded handling, and expression fail-closed handling.
     - Scripted execution over Postgres facade, row instantiation, M2M prefetch values, parent ID deduplication, and converter application.
     - End-to-end auto fallback execution on SQLite.
     - Keyset seek recognition for 1-column, 2-column, and 3-column plans.
     - Lateral SQL namespace derivation consistency.

2. **Scratch Test Verification**:
   - Executed `docs/review/temp-tests/optimizer/scratch_lateral_fetch.py` (5 tests passed in 1.58s):
     - Verified frozen dataclass immutability and post-init probe/count validation on `LateralWindowSpec`.
     - Verified `_deduplicate_parent_ids` handling across empty lists, all-None lists, hashables, and unhashables.
     - Verified `_order_columns` behavior across standard columns, pk aliases, expressions, traversals, random orderings, and invalid columns.
     - Verified `_plain_single_table_where` validation of base table cols and rejection of foreign aliases, joins, and subqueries.
     - Verified `_instantiate_row` model instantiation with deferred attributes and window metadata.

3. **Scoped Diff Verification**:
   - Scoped diff against cycle baseline `12779c99` (`git diff 12779c99 -- django_strawberry_framework/optimizer/lateral_fetch.py`) is empty.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/optimizer/lateral_fetch.py` is a state-of-the-art, robust implementation of PostgreSQL lateral join nested connection prefetching. It combines high-performance $O(\text{parents} \times \text{page})$ SQL execution with fail-closed security and safe degradation to the standard ORM windowed query under any deviation or non-Postgres routing.

## Implementation (Worker 1)

None — zero-edit cycle

- **Changed files**: None.
- **Permanent tests**: Existing test suite in `tests/optimizer/test_lateral_fetch.py` (92 tests) comprehensively verifies spec generation, SQL generation, recognition, parameter binding, converter handling, and runtime execution.
- **Scratch verification**: `docs/review/temp-tests/optimizer/scratch_lateral_fetch.py` (5 tests, 0 failures) verified spec validation, parent ID deduplication, ordering parsing, where clause admission, and instance hydration.
- **Formatter and linter**: Zero-edit cycle (no files modified).
- **Evidence for rejected findings**: No findings raised or rejected; all investigated code paths behave according to specifications and invariants.
- **Changelog**: Does not merit a changelog entry (zero-edit cycle).
 
## Independent verification (Worker 2)

- **Target file diff**: Verified zero-edit (`git diff 12779c99 -- django_strawberry_framework/optimizer/lateral_fetch.py` is empty).
- **Paths & behaviors verified**:
  - `LateralWindowSpec` frozen dataclass contract and post-init probe/count mutual-exclusion check via `assert_window_fetch_mode_for`.
  - Pure SQL construction (`build_lateral_sql`):
    - In-branch `ORDER BY ... LIMIT %s` optimization for plain first pages (`first: N`, `offset == 0`).
    - Standard outer row-number filtering and marker row (`OR rn = 1`) preservation for ambiguous shapes.
    - Deterministic parameter bindings, quoting via `connection.ops.quote_name`, and typed `unnest(%s::<type>[])` or typed `(VALUES (...))` generation for parent IDs.
    - Spliced keyset seeks (`_keyset_seek_sql`) and compiled single-table visibility scopes.
  - Fetch-time recognizer (`_recognize_lateral_fetch`):
    - Integrity checks on queryset attributes (`select_related`, annotations, extra tables, group by, ordering, projections).
    - Window predicate signature verification against plan signature via `window_predicate_signature`.
    - Parent ID extraction and validation via `_parent_in_values`.
    - Exact structural matching for keyset seek quals and byte-equal matching for visibility quals via `_visibility_quals_match`.
  - Fetch executor (`_fetch_lateral_rows`):
    - PostgreSQL vendor enforcement and fail-closed fallback to windowed ORM query when conditions fail.
    - Deduplication of parent IDs across empty, scalar, and unhashable collections via `_deduplicate_parent_ids`.
    - Converter application across parent link fields and select fields via `_apply_lateral_converters`.
    - Deferred model instance hydration with window attributes and prefetch value aliases via `_instantiate_row`.
  - Safe plan-time downgrade in `_build_lateral_spec` for inexpressible shapes (counted keyset seeks, custom QuerySet subclasses, multi-table inheritance, expression orderings, complex WHERE clauses).
- **Test execution**:
  - Full permanent suite `tests/optimizer/test_lateral_fetch.py` (92 passed in 3.26s).
  - Disposable scratch test suite `docs/review/temp-tests/optimizer/scratch_lateral_fetch_w2.py` (5 passed in 1.53s) challenging keyset seek first-page lateral SQL generation, parent-in lookup rejection, window signature determinism, and parent ID deduplication edge cases.
- **Outcome**: Complete and verified without issues.
