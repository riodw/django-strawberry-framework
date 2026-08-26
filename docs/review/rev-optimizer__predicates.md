# Review: `django_strawberry_framework/optimizer/predicates.py`

Status: verified

## Understanding

`django_strawberry_framework/optimizer/predicates.py` provides pure ORM predicate primitives for compiling to-many relational predicates as correlated `EXISTS` subqueries rather than row-multiplying `JOIN` + `DISTINCT` patterns:

1. **Core Primitives & Responsibilities**:
   - `correlated_inner_root(queryset: QuerySet) -> QuerySet`: Constructs an unevaluated inner queryset correlated with the outer row via `model._base_manager.using(queryset.db).filter(pk=OuterRef("pk"))`. Uses `_base_manager` so custom or filtered default managers do not introduce false negatives; pins the outer queryset's database alias (`queryset.db`) to ensure multi-db routing consistency; relies on `pk=OuterRef("pk")` which natively compiles to tuple comparisons for composite primary keys on supported Django.
   - `_effective_alias_names(queryset: QuerySet) -> set[str]`: Inspects the outer queryset to collect all model field names, `attname`s (e.g. `shelf_id`), literal `"pk"`, annotations (`query.annotations`), extra select names (`query.extra`), and projected fields (`query.values_select`) to form a collision-free namespace.
   - `_next_reserved_alias(queryset: QuerySet, prefix: str = "_dst_predicate_") -> str`: Computes a deterministic alias (`_dst_predicate_0`, `_dst_predicate_1`, ...) advancing past all occupied effective alias names.
   - `attach_exists(queryset: QuerySet, inner_queryset: QuerySet) -> tuple[QuerySet, Q]`: Attaches `Exists(inner_queryset)` under a reserved alias via `.alias(**{alias: Exists(inner_queryset)})` and returns `(new_queryset, Q(**{alias: True}))`.

2. **Invariants & Architectural Boundaries**:
   - **Neutral ORM Layer**: The module has no awareness of Strawberry ASTs, selections, or `django-filter` filter sets. It builds no predicate bodies, performs no `OR`/`AND` composition, and never calls `.filter()`, `.exclude()`, or `.distinct()` on the outer queryset (`.alias()` is its sole outer mutation).
   - **Multiset Row Preservation Contract**: Existence subqueries never multiply outer rows, inject `DISTINCT`, or dedup consumer duplicates.
   - **Runtime Guards**: Raises typed `OptimizerError` if:
     - `inner_queryset.model is not queryset.model` (model mismatch),
     - `inner_queryset.db != queryset.db` (database alias mismatch),
     - `queryset.query.combinator` is set (cannot attach aliases to union/intersection/difference combined queries).
   - **Execution Invariant**: The inner queryset is correlated via `OuterRef` and compiles inside the outer statement; it must never execute independently. Evaluated outer querysets remain valid inputs because `.alias()` clones the query cleanly.

## Verification

1. **Existing Permanent Tests**:
   - Executed `tests/optimizer/test_predicates.py` (13 tests passing in 3.16s):
     - `test_row_preservation_direct_m2m`: Direct M2M relation filter compiles to correlated `EXISTS` with no outer joins and `query.distinct is False`.
     - `test_same_table_inner_aliasing_from_loan_root`: Same-table reverse-FK deep traversal preserves outer row count without `DISTINCT` and supports caller boolean `OR` composition.
     - `test_reserved_alias_not_selected`: Reserved alias `_dst_predicate_0` is attached via `.alias()` and excluded from SQL SELECT / `values_select` / `annotation_select`.
     - `test_count_emits_no_distinct_wrapper` & `test_primitive_injects_no_distinct`: Verified outer `COUNT(*)` and queries emit no `DISTINCT` wrapper.
     - `test_alias_allocation`: Validated alias counter advancement across pre-occupied `.alias()`, `extra(select=)`, field attnames, and chained attachments.
     - `test_same_model_guard`, `test_same_alias_guard`, `test_database_alias_preserved`, `test_combinator_guard_names_combinator`: Validated all `OptimizerError` runtime guards.
     - `test_evaluated_outer_parity`: Verified that evaluating the outer queryset prior to `attach_exists` produces identical SQL and results.
     - `test_composite_pk_correlation_executes_on_composite_fixture`: Verified `pk=OuterRef("pk")` execution on composite primary key models (`RpCompositeParent`).
     - `test_base_manager_start_does_not_leak_outer_filters`: Confirmed `_base_manager` inner roots do not inherit outer query filters.

2. **Scratch Test Experiments**:
   - Executed `docs/review/temp-tests/optimizer_predicates/test_scratch.py`:
     - Verified `attach_exists` with inner combined queries (`inner.union(...)` inside `Exists(...)`) executes properly on SQLite.
     - Verified deterministic counter resolution across multiple alias collisions.

3. **Scoped Diff Verification**:
   - `git diff 12779c99 -- django_strawberry_framework/optimizer/predicates.py` is empty (zero-edit cycle).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/optimizer/predicates.py` is a clean, focused, and robust ORM primitive for row-preserving correlated `EXISTS` subqueries. It cleanly decouples predicate attachment from filter semantics and AST selections, enforces strict runtime guards with typed `OptimizerError` diagnostics, and is fully covered by existing unit, composite PK, and Postgres planner regression suites.

## Implementation (Worker 1)

None — zero-edit cycle

- **Changed files**: None.
- **Permanent tests**: Existing test suite in `tests/optimizer/test_predicates.py` (13 tests) pins all behaviors and contracts (correlation, manager isolation, database pinning, reserved alias allocation, runtime guards, composite primary keys, row preservation).
- **Scratch verification**: `docs/review/temp-tests/optimizer_predicates/test_scratch.py` (3 tests, 0 failures) verified inner combinator and sequential alias allocation behavior.
- **Formatter and linter**: Zero-edit cycle (no files modified).
- **Evidence for rejected findings**: None.
- **Changelog**: Does not merit a changelog entry (zero-edit cycle).

## Independent verification (Worker 2)

- **Behavioral Re-trace**:
  - Re-traced `correlated_inner_root(queryset)` ensuring manager isolation (`_base_manager`), database alias pinning (`queryset.db`), and pk-based correlation (`pk=OuterRef("pk")`).
  - Re-traced `_effective_alias_names(queryset)` and `_next_reserved_alias(queryset)` confirming complete namespace reservation spanning model field names, `attname`s (e.g. `shelf_id`), literal `"pk"`, annotations, `extra(select=)` aliases, and `values_select` projections.
  - Re-traced `attach_exists(queryset, inner_queryset)` confirming zero mutation to filter / distinct on outer queryset, alias attachment using `Exists(inner_queryset)`, and return of `(new_qs, Q(**{alias: True}))`.
  - Re-traced runtime error guards (`OptimizerError` raised on model mismatch, db mismatch, and combinator presence on outer queryset for union, intersection, and difference).
  - Re-traced multiset row preservation invariant and composite PK correlation semantics (`RpCompositeParent` / `RpCompositeChild`).
- **Baseline Diff**:
  - Confirmed `git diff 12779c99 -- django_strawberry_framework/optimizer/predicates.py` is completely empty (zero-edit cycle).
- **Test Executions**:
  - Ran permanent tests: `uv run pytest tests/optimizer/test_predicates.py --no-cov` (13 passed in 2.88s).
  - Ran Worker 1 scratch tests: `uv run pytest docs/review/temp-tests/optimizer_predicates/test_scratch.py --no-cov` (3 passed in 2.95s).
  - Authored and ran independent scratch suite in `docs/review/temp-tests/optimizer_predicates/test_independent_scratch_predicates.py` (6 passed in 3.63s) covering:
    - Namespace collection in `_effective_alias_names` across fields, attnames, pk, annotations, extra select, and values projections.
    - Deterministic skipping in `_next_reserved_alias`.
    - Combinator guards on outer querysets across union, intersection, and difference.
    - Model mismatch and database alias mismatch guards.
    - Multiset row preservation without injected `DISTINCT`.
    - Composite primary key correlation execution.
- **Conclusion**: Target production module is sound, verified, and adheres strictly to architectural contracts.
