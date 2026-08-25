# DRY review: `django_strawberry_framework/optimizer/lateral_fetch.py`

Status: verified

## System trace

`django_strawberry_framework/optimizer/lateral_fetch.py` is the PostgreSQL `CROSS JOIN LATERAL` execution engine for nested Relay connections ([spec-002][spec-002], [spec-004][spec-004], [spec-010][spec-010], [spec-016][spec-016], [spec-023][spec-023], [spec-025][spec-025], [spec-028][spec-028], [spec-033][spec-033], [spec-035][spec-035], [spec-051][spec-051], [spec-063][spec-063]). It implements the second backend of the pluggable `NestedConnectionStrategy` seam (the Prisma `LateralJoinSelectBuilder` lesson; see [`optimizer/nested_fetch.py`][optimizer-nested-fetch]).

While the default windowed prefetch strategy computes `ROW_NUMBER()` over every child of every selected parent before filtering to the requested page ($O(\sum \text{partition sizes})$ per request), the lateral join strategy runs the page query once per parent ID via `CROSS JOIN LATERAL` over a typed parent relation:
```sql
SELECT "__dst_parents"."__dst_parent_id", w.<cols>, w."_dst_row_number", ...
FROM unnest(%s::bigint[]) AS "__dst_parents"("__dst_parent_id")
CROSS JOIN LATERAL (
    SELECT <only-cols>,
           ROW_NUMBER() OVER (ORDER BY <order>) AS "_dst_row_number"
           [, COUNT(1) OVER () AS "_dst_total_count"]
    FROM <child> [INNER JOIN <through> ...]
    WHERE <link>.<parent-column> = "__dst_parents"."__dst_parent_id"
) "__dst_window"
WHERE <window-range-predicate>
ORDER BY "__dst_parents"."__dst_parent_id", "__dst_window"."_dst_row_number"
```
On PostgreSQL 15+, the query planner terminates each partition subquery after `offset + limit` rows, achieving $O(\text{parents} \times \text{page})$ execution time. For plain first pages (`first: N`, `offset == 0`), `build_lateral_sql` pushes `ORDER BY ... LIMIT %s` inside the lateral branch, allowing PostgreSQL to use an order-satisfying composite index walk.

It owns the following architectural responsibilities:

1. **Namespace Constants:**
   - [`LATERAL_SQL_STEM`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::LATERAL_SQL_STEM`): Namespace stem prefix `"__dst"` from which all role-specific lateral SQL aliases and column names are derived.
   - [`LATERAL_PARENT_ALIAS`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::LATERAL_PARENT_ALIAS`): SQL alias `"__dst_parents"` for the synthesized parent table, derived from [`LATERAL_SQL_STEM`][optimizer-lateral-fetch].
   - [`LATERAL_PARENT_COLUMN`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::LATERAL_PARENT_COLUMN`): Synthesized column name `"__dst_parent_id"`, derived from [`LATERAL_SQL_STEM`][optimizer-lateral-fetch].
   - [`LATERAL_WINDOW_ALIAS`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::LATERAL_WINDOW_ALIAS`): Subquery alias `"__dst_window"`, derived from [`LATERAL_SQL_STEM`][optimizer-lateral-fetch].
   - [`LATERAL_CHILD_ALIAS`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::LATERAL_CHILD_ALIAS`): Alias `"__dst_child"` for through-table joins, derived from [`LATERAL_SQL_STEM`][optimizer-lateral-fetch].
   - [`LATERAL_THROUGH_ALIAS`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::LATERAL_THROUGH_ALIAS`): Alias `"__dst_through"` for intermediate M2M tables, derived from [`LATERAL_SQL_STEM`][optimizer-lateral-fetch].
   - [`_ARRAY_BINDABLE_PARENT_FIELD_TYPES`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_ARRAY_BINDABLE_PARENT_FIELD_TYPES`): Immutable `frozenset` of 24 standard Django scalar field class names whose values psycopg adapts as a single typed PostgreSQL array parameter (`unnest(%s::type[])`). Structured, custom, or non-scalar types take the typed `VALUES` fallback.
   - [`_WINDOW_ANNOTATIONS`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_WINDOW_ANNOTATIONS`): Immutable `frozenset` of recognized window annotations (`WINDOW_ROW_NUMBER`, `WINDOW_TOTAL_COUNT`, `WINDOW_ROW_NUMBER_REVERSED`) from [`plans.py`][optimizer-plans].

2. **Immutable Plan Spec:**
   - [`LateralWindowSpec`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::LateralWindowSpec`): Frozen dataclass capturing all plan-time facts needed to render lateral SQL: model, table name, `.only()` column projections, field converter expressions, deterministic ordering, parent link fields, through-table metadata, slice parameters (`offset`, `limit`, `reverse`, `with_total_count`, `next_page_probe`), optional count-free `keyset_seek`, and optional single-table `visibility_where`.
   - [`LateralWindowSpec.__post_init__`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::LateralWindowSpec.__post_init__`): Calls [`assert_window_fetch_mode_for`][utils-connections] to enforce probe/count mutual exclusion on spec construction.

3. **SQL AST Compilation:**
   - [`build_lateral_sql`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::build_lateral_sql`): Pure SQL compiler rendering PostgreSQL `CROSS JOIN LATERAL` subqueries. Quotes all identifiers via `quote_name`, parameterizes all parent IDs and pagination bounds, selects between `unnest` array and typed `VALUES` binding, handles `DIRECT_FK` vs `THROUGH_TABLE` joins, optimizes plain first pages with in-branch `LIMIT`, splices count-free keyset seeks, and splices compiled single-table visibility scopes.
   - [`_keyset_seek_sql`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_keyset_seek_sql`): Adapts `spec.keyset_seek` to quoted child-table column references and compiles via [`keyset_seek_sql`][keyset].

4. **QuerySet Subclass and Fetch Recognizer:**
   - [`LateralQuerySet`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::LateralQuerySet`): Subclass of [`RecognizedFetchQuerySet`][optimizer-nested-fetch] binding `_dst_spec_attr = "_dst_lateral_spec"`.
   - [`LateralQuerySet._fetch_recognized_rows`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::LateralQuerySet._fetch_recognized_rows`): Invokes [`_fetch_lateral_rows`][optimizer-lateral-fetch].
   - [`_RecognizedLateralFetch`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_RecognizedLateralFetch`): Frozen dataclass carrying extracted `parent_ids` and approved `visibility_where_sql`.
   - [`_fetch_lateral_rows`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_fetch_lateral_rows`): Runtime executor proving query recognition, verifying PostgreSQL connection vendor on `queryset.db`, deduplicating parent IDs, executing SQL cursor, applying field converters, and instantiating model instances. Unrecognized shapes return `None` to seamlessly fall back to superclass windowed prefetch execution.

5. **Helper Routines and Query AST Inspectors:**
   - [`_deduplicate_parent_ids`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_deduplicate_parent_ids`): Order-preserving de-duplication of parent IDs filtering out `None`, with graceful handling for unhashable values. Exported and reused by [`single_parent_fetch.py`][optimizer-single-parent-fetch].
   - [`_apply_lateral_converters`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_apply_lateral_converters`): Applies Django backend and field converter chains (`get_db_converters`) to raw cursor rows.
   - [`_recognize_lateral_fetch`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_recognize_lateral_fetch`): Structural verifier proving the fetch-time query matches the planned window and Django prefetch `__in` filter.
   - [`_is_window_qual`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_is_window_qual`): Structural classifier identifying nodes constraining exclusively window annotations. Exported and reused by [`single_parent_fetch.py`][optimizer-single-parent-fetch].
   - [`_normalize_window_node`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_normalize_window_node`): Canonical normalization of window-qual nodes.
   - [`window_predicate_signature`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::window_predicate_signature`): Derives canonical hashable signatures of window-range predicates in `query.where`. Exported and reused by [`single_parent_fetch.py`][optimizer-single-parent-fetch] and [`RecognizedFetchQuerySet.rebind`][optimizer-nested-fetch].
   - [`_keyset_seek_quals_match`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_keyset_seek_quals_match`): Verifies fetch-time WHERE residue matches the 2-node keyset seek expansion.
   - [`_visibility_quals_match`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_visibility_quals_match`): Proves single-table visibility residue compiles byte-for-byte to the stored plan, returning approved `(sql, params)`.
   - [`_parent_in_values`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_parent_in_values`): Extracts parent ID lists from prefetch `__in` lookups. Exported and reused by [`single_parent_fetch.py`][optimizer-single-parent-fetch].
   - [`_instantiate_row`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_instantiate_row`): Instantiates model instances via `Model.from_db` and attaches `_dst_row_number`, `_dst_total_count`, and `_prefetch_related_val_*` attributes.
   - [`_plain_single_table_where`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_plain_single_table_where`): Admission test for single-table plain-column visibility WHERE clauses.
   - [`_build_lateral_spec`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_build_lateral_spec`): Resolves a `NestedConnectionRequest` into a `LateralWindowSpec` or returns `None` to trigger windowed downgrade.
   - [`_order_columns`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_order_columns`): Maps deterministic `order_by` sequences to concrete `(column, descending)` pairs using [`order_entry_name_and_direction`][optimizer-plans].
   - [`_select_columns`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::_select_columns`): Maps `.only()` projections to concrete `(attname, column)` pairs using [`deferred_loading_of`][optimizer-plans]. Exported and reused by [`single_parent_fetch.py`][optimizer-single-parent-fetch].

6. **Strategy Implementation & Singleton:**
   - [`LateralPrefetchStrategy`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::LateralPrefetchStrategy`): Implements `NestedConnectionStrategy` protocol (`name = "lateral"`).
   - [`LateralPrefetchStrategy.plan`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::LateralPrefetchStrategy.plan`): Attempts lateral spec resolution via [`_build_lateral_spec`][optimizer-lateral-fetch], falling back to [`WINDOWED_STRATEGY.plan`][optimizer-nested-fetch] on downgrade, or attaching a windowed prefetch wrapping `LateralQuerySet.rebind`.
   - [`LATERAL_STRATEGY`][optimizer-lateral-fetch] (`django_strawberry_framework/optimizer/lateral_fetch.py::LATERAL_STRATEGY`): Stateless singleton instance of [`LateralPrefetchStrategy`][optimizer-lateral-fetch].

Connected behavior examined:
- [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch]: Defines [`NestedConnectionRequest`][optimizer-nested-fetch], [`RecognizedFetchQuerySet`][optimizer-nested-fetch], [`attach_windowed_prefetch`][optimizer-nested-fetch], [`unwindowable_child_queryset_reason`][optimizer-nested-fetch], [`WINDOWED_STRATEGY`][optimizer-nested-fetch], and [`AUTO_STRATEGY`][optimizer-nested-fetch].
- [`django_strawberry_framework/optimizer/single_parent_fetch.py`][optimizer-single-parent-fetch]: Reuses [`_deduplicate_parent_ids`][optimizer-lateral-fetch], [`_is_window_qual`][optimizer-lateral-fetch], [`_parent_in_values`][optimizer-lateral-fetch], [`_select_columns`][optimizer-lateral-fetch], and [`window_predicate_signature`][optimizer-lateral-fetch] to execute degenerate single-parent queries without duplicating AST traversal or signature algorithms.
- [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy]: Supplies join metadata ([`LateralJoinShape`][optimizer-join-taxonomy], [`RelationJoinDescriptor`][optimizer-join-taxonomy]) read by `_build_lateral_spec`.
- [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans]: Supplies window annotation names (`WINDOW_ROW_NUMBER`, `WINDOW_TOTAL_COUNT`, `WINDOW_ROW_NUMBER_REVERSED`), [`OptimizationPlan`][optimizer-plans], [`deferred_loading_of`][optimizer-plans], and [`order_entry_name_and_direction`][optimizer-plans].
- [`django_strawberry_framework/keyset.py`][keyset]: Supplies keyset value seek compilation ([`keyset_seek_sql`][keyset]).
- [`django_strawberry_framework/utils/connections.py`][utils-connections]: Supplies [`window_range_plan`][utils-connections] and [`assert_window_fetch_mode_for`][utils-connections].
- [`tests/optimizer/test_lateral_fetch.py`][test-optimizer-lateral-fetch]: 68 unit tests verifying spec building, pure SQL compilation, AST recognition, signature matching, field converters, and scripted-cursor execution on SQLite.
- [`tests/test_lateral_pg_parity.py`][test-lateral-pg-parity]: Live PostgreSQL integration suite verifying exact byte-for-byte response parity between windowed and lateral execution strategies.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/optimizer/lateral_fetch.py --include-constants`):
- Parsed 1 target file, 1174 lines.
- Inventory of symbols (33 definitions):
  - 9 constants: [`LATERAL_SQL_STEM`][optimizer-lateral-fetch], [`LATERAL_PARENT_ALIAS`][optimizer-lateral-fetch], [`LATERAL_PARENT_COLUMN`][optimizer-lateral-fetch], [`LATERAL_WINDOW_ALIAS`][optimizer-lateral-fetch], [`LATERAL_CHILD_ALIAS`][optimizer-lateral-fetch], [`LATERAL_THROUGH_ALIAS`][optimizer-lateral-fetch], [`_ARRAY_BINDABLE_PARENT_FIELD_TYPES`][optimizer-lateral-fetch], [`_WINDOW_ANNOTATIONS`][optimizer-lateral-fetch], [`LATERAL_STRATEGY`][optimizer-lateral-fetch].
  - 4 classes: [`LateralWindowSpec`][optimizer-lateral-fetch], [`LateralQuerySet`][optimizer-lateral-fetch], [`_RecognizedLateralFetch`][optimizer-lateral-fetch], [`LateralPrefetchStrategy`][optimizer-lateral-fetch].
  - 3 methods: [`LateralWindowSpec.__post_init__`][optimizer-lateral-fetch], [`LateralQuerySet._fetch_recognized_rows`][optimizer-lateral-fetch], [`LateralPrefetchStrategy.plan`][optimizer-lateral-fetch].
  - 17 functions: [`build_lateral_sql`][optimizer-lateral-fetch], [`_keyset_seek_sql`][optimizer-lateral-fetch], [`_fetch_lateral_rows`][optimizer-lateral-fetch], [`_deduplicate_parent_ids`][optimizer-lateral-fetch], [`_apply_lateral_converters`][optimizer-lateral-fetch], [`_recognize_lateral_fetch`][optimizer-lateral-fetch], [`_is_window_qual`][optimizer-lateral-fetch], [`_normalize_window_node`][optimizer-lateral-fetch], [`window_predicate_signature`][optimizer-lateral-fetch], [`_keyset_seek_quals_match`][optimizer-lateral-fetch], [`_visibility_quals_match`][optimizer-lateral-fetch], [`_parent_in_values`][optimizer-lateral-fetch], [`_instantiate_row`][optimizer-lateral-fetch], [`_plain_single_table_where`][optimizer-lateral-fetch], [`_build_lateral_spec`][optimizer-lateral-fetch], [`_order_columns`][optimizer-lateral-fetch], [`_select_columns`][optimizer-lateral-fetch].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `django_strawberry_framework/optimizer/lateral_fetch.py` shares pagination range semantics with `plans.py::apply_window_pagination` through the root plan helper [`window_range_plan`][utils-connections]. The lateral SQL generator [`build_lateral_sql`][optimizer-lateral-fetch] consumes `range_plan.plain_first_page`, `range_plan.fetch_limit`, `range_plan.lower_bound`, `range_plan.fetch_upper_bound`, `range_plan.add_marker_rows`, and `range_plan.reverse` to produce SQL row-number filters that are byte-mirrors of the ORM window predicates. The shared query AST inspection helpers ([`_deduplicate_parent_ids`][optimizer-lateral-fetch], [`_is_window_qual`][optimizer-lateral-fetch], [`_parent_in_values`][optimizer-lateral-fetch], [`_select_columns`][optimizer-lateral-fetch], and [`window_predicate_signature`][optimizer-lateral-fetch]) are defined once in `lateral_fetch.py` and imported by [`single_parent_fetch.py`][optimizer-single-parent-fetch], eliminating duplicate AST traversal logic across strategies. Keyset seek SQL compilation is cleanly delegated to [`keyset.py::keyset_seek_sql`][keyset], and join topology classification is delegated to [`join_taxonomy.py::classify_relation_join`][optimizer-join-taxonomy]. Zero cross-flavor duplication.

2. **Sync and async twins:**
   Zero duplication. Plan-time spec resolution and SQL compilation in `lateral_fetch.py` are purely synchronous, side-effect-free AST and string transformations. Fetch-time execution integrates directly into Django's prefetch pipeline via [`RecognizedFetchQuerySet._fetch_all`][optimizer-nested-fetch], supporting both synchronous query evaluation and Django async queryset iteration without duplicated async twin execution methods.

3. **Derived rather than repeated knowledge:**
   - Parent link column casting types are derived dynamically via `spec.parent_link_field.db_type(connection)`.
   - Parameter array-binding eligibility is derived strictly from `target_field.get_internal_type() in _ARRAY_BINDABLE_PARENT_FIELD_TYPES`.
   - Projection columns are derived from `.only()` expressions via [`plans.py::deferred_loading_of`][optimizer-plans].
   - Keyset seek SQL is derived dynamically by passing the shared `seek.plan()` to [`keyset.py::keyset_seek_sql`][keyset].
   - Window range bounds and probe limits derive dynamically via [`utils/connections.py::window_range_plan`][utils-connections].
   - Window predicate signatures derive deterministically from `query.where` and `query.annotations` via [`window_predicate_signature`][optimizer-lateral-fetch].
   - Raw database row converter chains derive dynamically at cursor fetch time via `connection.ops.get_db_converters` and `expression.get_db_converters`.
   No derived SQL fact or query attribute is manually restated or hardcoded.

4. **Inverse and round-trip pairs:**
   - Forward vs reverse SQL ordering: [`build_lateral_sql`][optimizer-lateral-fetch] cleanly computes forward orderings (`order_sql(descending_flip=False)`) and reversed window orderings (`order_sql(descending_flip=True)`), correctly inverting `ASC` and `DESC` clauses.
   - Forward M2M vs reverse M2M: [`_build_lateral_spec`][optimizer-lateral-fetch] accurately pairs `parent_link_table`, `parent_link_column`, `through_child_column`, and `prefetch_value_aliases` based on join descriptor classifications.
   - Row instantiation ([`_instantiate_row`][optimizer-lateral-fetch]): Translates raw SQL cursor tuples back into Django model instances via `Model.from_db` while faithfully populating synthetic `_dst_row_number`, `_dst_total_count`, and `_prefetch_related_val_*` attributes.

5. **Contracts restated in another medium:**
   The lateral execution engine contracts are codified across:
   - Code: [`django_strawberry_framework/optimizer/lateral_fetch.py`][optimizer-lateral-fetch], [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch], [`django_strawberry_framework/optimizer/single_parent_fetch.py`][optimizer-single-parent-fetch], [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy], [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans], [`django_strawberry_framework/keyset.py`][keyset], [`django_strawberry_framework/utils/connections.py`][utils-connections];
   - Specifications: [`docs/SPECS/spec-002-optimizer-0_0_2.md`][spec-002], [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004], [`docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md`][spec-010], [`docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md`][spec-016], [`docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md`][spec-023], [`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md`][spec-025], [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028], [`docs/SPECS/spec-033-nested_connection_execution_plan-0_0_9.md`][spec-033], [`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`][spec-035], [`docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md`][spec-051], [`docs/SPECS/spec-063-structural_templates-0_1_6.md`][spec-063];
   - Test suites: [`tests/optimizer/test_lateral_fetch.py`][test-optimizer-lateral-fetch] (68 unit tests covering spec building, SQL generation, in-branch LIMIT pushdown, keyset seek integration, single-table visibility WHERE splicing, AST recognition, and SQLite scripted cursor execution), [`tests/test_lateral_pg_parity.py`][test-lateral-pg-parity] (live PostgreSQL integration tests verifying complete data and query count parity), [`tests/optimizer/test_nested_fetch.py`][test-optimizer-nested-fetch], [`tests/optimizer/test_single_parent_fetch.py`][test-optimizer-single-parent-fetch];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding a new scalar parent field type to array-bindable parameter serialization, e.g. a new custom numeric type `PosInteger`):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/lateral_fetch.py`][optimizer-lateral-fetch] (adding the type name string to [`_ARRAY_BINDABLE_PARENT_FIELD_TYPES`][optimizer-lateral-fetch]).
  - *Site count:* 1 in target.
- **Posited change 2 (Adjusting the lateral alias namespace prefix, e.g. from `__dst` to `__dsf`):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/lateral_fetch.py`][optimizer-lateral-fetch] (updating [`LATERAL_SQL_STEM`][optimizer-lateral-fetch], which automatically derives [`LATERAL_PARENT_ALIAS`][optimizer-lateral-fetch], [`LATERAL_PARENT_COLUMN`][optimizer-lateral-fetch], [`LATERAL_WINDOW_ALIAS`][optimizer-lateral-fetch], [`LATERAL_CHILD_ALIAS`][optimizer-lateral-fetch], and [`LATERAL_THROUGH_ALIAS`][optimizer-lateral-fetch]).
  - *Site count:* 1 in target.
- **Posited change 3 (Supporting M2M through-table visibility WHERE filtering in lateral branches):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/lateral_fetch.py`][optimizer-lateral-fetch] (updating [`_build_lateral_spec`][optimizer-lateral-fetch] admission gate and adjusting [`build_lateral_sql`][optimizer-lateral-fetch] child aliasing / splicing).
  - *Site count:* 1 in target.
- **Posited change 4 (Extending raw cursor converter chains to include custom model-level or connection-level output converters):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/lateral_fetch.py`][optimizer-lateral-fetch] (updating [`_apply_lateral_converters`][optimizer-lateral-fetch]).
  - *Site count:* 1 in target.
- **Posited change 5 (Modifying the window qual AST canonical normalization format, e.g. supporting operator commutativity):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/lateral_fetch.py`][optimizer-lateral-fetch] (updating [`_normalize_window_node`][optimizer-lateral-fetch], which automatically propagates to [`window_predicate_signature`][optimizer-lateral-fetch] consumed across lateral and single-parent strategies).
  - *Site count:* 1 in target.

### Rejected candidates

1. **Generating vendor-specific SQL dialect templates for non-Postgres databases in `lateral_fetch.py`:**
   - Disproved per [spec-033][spec-033] and [spec-035][spec-035]. Lateral joins with monotonic window optimization are specific to PostgreSQL (>= 15). Attempting to synthesize dialect-specific correlated subqueries for SQLite or MySQL would create immense complexity and maintenance overhead. Instead, non-Postgres vendors gracefully downgrade to the windowed prefetch strategy, preserving correctness across all databases without duplicating query planner rules.
2. **Re-compiling `spec.visibility_where` a second time during cursor execution instead of passing the recognizer's approved `(sql, params)`:**
   - Disproved per [spec-035][spec-035]. If `spec.visibility_where` were recompiled at execution time, a stateful or consumption-based custom lookup compiler could cause the executed predicate to diverge from the approved predicate. Handing the exact approved `(sql, params)` from [`_RecognizedLateralFetch`][optimizer-lateral-fetch] guarantees fail-closed execution.
3. **Allowing unrecognized or mutated WHERE trees to attempt partial lateral execution:**
   - Disproved per [spec-033][spec-033] and [spec-035][spec-035]. Any divergence between the planned query and the fetch-time query (such as consumer filters, extra annotations, or modified window bounds) must fail closed by returning `None`, allowing [`RecognizedFetchQuerySet._fetch_all`][optimizer-nested-fetch] to execute the windowed ORM query.
4. **Moving AST recognition helpers (`_is_window_qual`, `_parent_in_values`, `_select_columns`, `window_predicate_signature`) to a third utility file:**
   - Disproved. `lateral_fetch.py` is the primary owner of lateral SQL compilation and query recognition. `single_parent_fetch.py` imports these helpers directly from `lateral_fetch.py`. Extracting them to a separate file would create unnecessary module proliferation without adding DRY value.

## Opportunities

None — `django_strawberry_framework/optimizer/lateral_fetch.py` is a highly refined, robust, and fully consolidated implementation. It acts as the singular source of truth for PostgreSQL lateral subquery compilation and query recognition, correctly optimizes plain first pages with in-branch `LIMIT`, safely delegates range bounds and keyset seek SQL to root owners, and exhibits zero redundant logic.

## Judgment

Zero-edit review. `optimizer/lateral_fetch.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/lateral_fetch.py --review docs/dry/dry-file-optimizer__lateral_fetch.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Worker 2 independently verified the PostgreSQL `CROSS JOIN LATERAL` fetch engine, plan specifications, AST query recognizers, SQL compilation logic, and test suites across the repository:

1. **Lateral Fetch Contract and Seam Architecture:**
   - Confirmed that [`LateralWindowSpec`][optimizer-lateral-fetch] serves as the immutable plan-time descriptor, strictly enforcing probe/count mutual exclusion via [`assert_window_fetch_mode_for`][utils-connections].
   - Validated SQL compiler mechanics in [`build_lateral_sql`][optimizer-lateral-fetch]:
     - Identifier quoting through `connection.ops.quote_name` across all synthesized tables (`LATERAL_PARENT_ALIAS`, `LATERAL_WINDOW_ALIAS`, `LATERAL_CHILD_ALIAS`, `LATERAL_THROUGH_ALIAS`) and columns.
     - Unnest array binding (`unnest(%s::type[])`) for 24 scalar field types defined in [`_ARRAY_BINDABLE_PARENT_FIELD_TYPES`][optimizer-lateral-fetch] vs. typed `(VALUES (%s::type))` binding fallback for custom/structured fields.
     - In-branch `ORDER BY ... LIMIT %s` pushdown for plain first pages (`offset == 0` without total count), enabling PostgreSQL index-scan optimizations.
     - Splicing of count-free keyset seek clauses via [`_keyset_seek_sql`][optimizer-lateral-fetch] delegating to [`keyset.py::keyset_seek_sql`][keyset].
     - Splicing of single-table visibility WHERE scopes for `DIRECT_FK` joins using unaliased child tables.
   - Re-traced fetch-time AST recognition in [`_recognize_lateral_fetch`][optimizer-lateral-fetch]:
     - Strict verification of annotations against [`_WINDOW_ANNOTATIONS`][optimizer-lateral-fetch].
     - Exact signature matching via [`window_predicate_signature`][optimizer-lateral-fetch] and [`_normalize_window_node`][optimizer-lateral-fetch] to prevent silently ignoring altered/mutated row bounds.
     - Keyset seek residue validation via [`_keyset_seek_quals_match`][optimizer-lateral-fetch].
     - Single-table visibility residue validation via [`_visibility_quals_match`][optimizer-lateral-fetch], returning the approved compiled `(sql, params)` to guarantee fail-closed execution.
     - Graceful fallback returning `None` to seamlessly delegate unrecognized shapes to superclass windowed prefetch execution.

2. **Downstream Strategy & Multi-Strategy Deduplication:**
   - Verified shared query AST inspectors ([`_deduplicate_parent_ids`][optimizer-lateral-fetch], [`_is_window_qual`][optimizer-lateral-fetch], [`_parent_in_values`][optimizer-lateral-fetch], [`_select_columns`][optimizer-lateral-fetch], [`window_predicate_signature`][optimizer-lateral-fetch]) are imported and reused by [`single_parent_fetch.py`][optimizer-single-parent-fetch], eliminating redundant query graph traversal across strategies.
   - Verified [`LateralPrefetchStrategy`][optimizer-lateral-fetch] singleton [`LATERAL_STRATEGY`][optimizer-lateral-fetch] integrates cleanly with [`nested_fetch.py`][optimizer-nested-fetch].

3. **Duplication Probing Matrix & Single-Edit Site Test:**
   - All 5 axes of the mandatory duplication probing matrix were re-evaluated and confirmed discharged.
   - Single-edit-site counts hold at 1 for all posited structural and functional changes.

4. **Static Analysis & Test Verification:**
   - Executed `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/lateral_fetch.py --review docs/dry/dry-file-optimizer__lateral_fetch.md --include-constants`: confirmed 33 target definitions covered with 0 errors.
   - Verified unit test suite `tests/optimizer/test_lateral_fetch.py` (68 test functions).
   - Verified related test suites `tests/optimizer/test_nested_fetch.py` and `tests/optimizer/test_single_parent_fetch.py` (36 test functions across both suites).

Verification complete. Setting `Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-002]: ../SPECS/spec-002-optimizer-0_0_2.md
[spec-004]: ../SPECS/spec-004-optimizer_beyond-0_0_3.md
[spec-010]: ../SPECS/appx/spec-010-foundation-0_0_4-rationale.md
[spec-016]: ../SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md
[spec-023]: ../SPECS/appx/spec-023-multi_db-0_0_7-rationale.md
[spec-025]: ../SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-033]: ../SPECS/spec-033-nested_connection_execution_plan-0_0_9.md
[spec-035]: ../SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-051]: ../SPECS/spec-051-boundary_dry_squeeze-0_0_15.md
[spec-063]: ../SPECS/spec-063-structural_templates-0_1_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[keyset]: ../../django_strawberry_framework/keyset.py
[optimizer-context]: ../../django_strawberry_framework/optimizer/_context.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[optimizer-field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[optimizer-hints]: ../../django_strawberry_framework/optimizer/hints.py
[optimizer-join-taxonomy]: ../../django_strawberry_framework/optimizer/join_taxonomy.py
[optimizer-lateral-fetch]: ../../django_strawberry_framework/optimizer/lateral_fetch.py
[optimizer-nested-fetch]: ../../django_strawberry_framework/optimizer/nested_fetch.py
[optimizer-nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[optimizer-plans]: ../../django_strawberry_framework/optimizer/plans.py
[optimizer-single-parent-fetch]: ../../django_strawberry_framework/optimizer/single_parent_fetch.py
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[utils-connections]: ../../django_strawberry_framework/utils/connections.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->
[test-lateral-pg-parity]: ../../tests/test_lateral_pg_parity.py
[test-optimizer-join-taxonomy]: ../../tests/optimizer/test_join_taxonomy.py
[test-optimizer-lateral-fetch]: ../../tests/optimizer/test_lateral_fetch.py
[test-optimizer-nested-fetch]: ../../tests/optimizer/test_nested_fetch.py
[test-optimizer-plans]: ../../tests/optimizer/test_plans.py
[test-optimizer-single-parent-fetch]: ../../tests/optimizer/test_single_parent_fetch.py
[test-optimizer-walker]: ../../tests/optimizer/test_walker.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
