# DRY review: `django_strawberry_framework/optimizer/predicates.py`

Status: verified

## System trace

`django_strawberry_framework/optimizer/predicates.py` is the pure ORM utility module providing row-preserving relational predicate primitives ([spec-053][spec-053], [spec-055][spec-055]). It compiles to-many relational predicates as correlated `EXISTS` subqueries rather than the row-multiplying `JOIN` + `DISTINCT` idiom, maintaining SQL multiset semantics and preserving the caller queryset's row multiplicity.

It deliberately isolates SQL `EXISTS` correlation and alias management from Strawberry selection trees, GraphQL AST traversal, and filterset business logic:
- It knows nothing about `django-filter` or Strawberry selections.
- It builds no predicate bodies and does no `OR` / `AND` grouping.
- It never calls `.filter()`, `.exclude()`, or `.distinct()` on the outer queryset — `.alias()` is its only outer mutation.
- Request values remain outside the selection optimizer's cross-request `OptimizationPlan` cache.
- Selection AST predicates and fragment traversal are decoupled and owned by [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections] and [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker].
- Field metadata reflection and relation classification are decoupled and owned by [`django_strawberry_framework/optimizer/field_meta.py`][optimizer-field-meta] and [`django_strawberry_framework/utils/relations.py`][utils-relations].

It owns the following architectural components and primitives:

1. **Reserved Alias Management & Collision Avoidance:**
   - [`_RESERVED_ALIAS_PREFIX`][optimizer-predicates] (`django_strawberry_framework/optimizer/predicates.py::_RESERVED_ALIAS_PREFIX`): Module-level string constant `"_dst_predicate_"` defining the deterministic namespace prefix for framework-attached subquery aliases.
   - [`_effective_alias_names`][optimizer-predicates] (`django_strawberry_framework/optimizer/predicates.py::_effective_alias_names`): Inspects the outer QuerySet to construct the comprehensive set of occupied names a reserved alias must avoid:
     - Model field names and concrete column names (`attname`, e.g. `shelf` and `shelf_id`);
     - The literal `"pk"`;
     - Query annotations (`query.annotations`, covering both `.annotate()` and `.alias()`);
     - Query extra selects (`query.extra`);
     - Query values/only projections (`query.values_select`).
   - [`_next_reserved_alias`][optimizer-predicates] (`django_strawberry_framework/optimizer/predicates.py::_next_reserved_alias`): Deterministically increments an integer counter past every occupied name in `_effective_alias_names(queryset)` (`_dst_predicate_0`, `_dst_predicate_1`, ...), allowing multiple chained existence predicates, window annotations, and consumer aliases to coexist without name collisions.

2. **Correlated Inner Root Construction:**
   - [`correlated_inner_root`][optimizer-predicates] (`django_strawberry_framework/optimizer/predicates.py::correlated_inner_root`): Returns an unevaluated inner QuerySet correlated to the outer row's primary key:
     `model._base_manager.using(queryset.db).filter(pk=OuterRef("pk"))`.
     - `_base_manager`: Starts from the model's base manager because the outer QuerySet already applied consumer visibility and manager filters. The inner row exists solely to test relational existence for an already-qualified outer primary key; re-applying filtered managers internally would introduce false negatives.
     - `queryset.db`: Pins the resolved database alias of the outer QuerySet to the inner QuerySet so database routing remains consistent without executing separate routing passes.
     - `pk=OuterRef("pk")`: The canonical correlation predicate. On composite primary keys, Django compiles this expression to a tuple comparison over the composite primary key columns.
     - Invariant: The inner QuerySet compiles inside the outer statement with `OuterRef` and must never be evaluated independently.

3. **Row-Preserving Subquery Attachment & Runtime Guards:**
   - [`attach_exists`][optimizer-predicates] (`django_strawberry_framework/optimizer/predicates.py::attach_exists`): Attaches `Exists(inner_queryset)` under an allocated reserved alias via `queryset.alias(**{alias: Exists(inner_queryset)})` and returns the 2-tuple `(new_queryset, Q(**{alias: True}))`. The caller retains full ownership of boolean composition and applies the positive condition as appropriate.
   - Runtime caller-contract guards (raising typed [`OptimizerError`][exceptions]):
     - *Same-model guard:* Asserts `inner_queryset.model is queryset.model`, preventing correlation mismatches across differing model types.
     - *Same-database alias guard:* Asserts `inner_queryset.db == queryset.db`, preventing cross-database query execution errors.
     - *Combinator guard:* Asserts `not queryset.query.combinator`, rejecting alias attachments to combined QuerySets (e.g. `union()`, `intersection()`, `difference()`).

Connected behavior examined:
- [`django_strawberry_framework/filters/sets.py`][filters-sets]: [`FilterSet._apply_flat_leaves`][filters-sets] consumes [`correlated_inner_root`][optimizer-predicates] and [`attach_exists`][optimizer-predicates] to execute to-many relational filter clauses via correlated `EXISTS` subqueries, eliminating duplicate outer rows and avoiding injected `DISTINCT`.
- [`django_strawberry_framework/filters/sets.py`][filters-sets]: [`FilterSet._apply_related_constraints`][filters-sets] uses the semantically equivalent sibling idiom (`pk__in` parent-pk subquery) for nested relational constraints.
- [`django_strawberry_framework/exceptions.py`][exceptions]: Defines [`OptimizerError`][exceptions] raised by runtime contract guards.
- [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections] & [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker]: Own selection-level predicates (`is_fragment`, `should_include`, `connection_node_children`, etc.) and AST traversal.
- [`django_strawberry_framework/optimizer/field_meta.py`][optimizer-field-meta] & [`django_strawberry_framework/utils/relations.py`][utils-relations]: Own field metadata and relation topology classification.
- [`tests/optimizer/test_predicates.py`][test-optimizer-predicates]: Comprehensive test suite covering row preservation on M2M relations, same-table inner aliasing, alias non-selection, absence of injected `DISTINCT` in SQL/counts, deterministic alias allocation across namespaces, runtime guards (same model, same DB, combinator), evaluated outer QuerySet parity, composite primary key correlation execution on live DB tables, and base manager filter isolation.
- [`tests/filters/test_sets.py`][test-filters-sets]: Verifies end-to-end relational filter application through `FilterSet` consuming `correlated_inner_root` and `attach_exists`.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/optimizer/predicates.py --include-constants`):
- Parsed 1 target file, 167 lines.
- Inventory of symbols:
  - 1 constant: [`_RESERVED_ALIAS_PREFIX`][optimizer-predicates].
  - 4 functions: [`correlated_inner_root`][optimizer-predicates], [`_effective_alias_names`][optimizer-predicates], [`_next_reserved_alias`][optimizer-predicates], [`attach_exists`][optimizer-predicates].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   [`optimizer/predicates.py`][optimizer-predicates] is the single centralized engine for compiling row-preserving correlated `EXISTS` subqueries in the framework.
   - FilterSets ([`django_strawberry_framework/filters/sets.py`][filters-sets]) route to-many filter leaves directly through [`correlated_inner_root`][optimizer-predicates] and [`attach_exists`][optimizer-predicates].
   - Sibling subsystems (`orders/`, `mutations/`, `forms/`, `rest_framework/`) do not duplicate subquery existence correlation or alias generation logic. Where relational operations occur, they operate through their respective domain abstractions or centralized utility modules ([`utils/relations.py`][utils-relations], [`utils/querysets.py`][utils-querysets]).
   - AST selection predicates and directives are cleanly separated and owned by [`optimizer/selections.py`][optimizer-selections]. Model descriptor classification is owned by [`optimizer/field_meta.py`][optimizer-field-meta] and [`utils/relations.py`][utils-relations].
   There is zero duplicate existence predicate logic across flavors.

2. **Sync and async twins:**
   Zero duplication. [`optimizer/predicates.py`][optimizer-predicates] operates entirely at the level of unevaluated Django `QuerySet` query expressions (`Exists`, `OuterRef`, `.alias()`, and `Q` nodes) without performing I/O or evaluating queries. Both synchronous (`apply_sync`) and asynchronous (`apply_async`) execution pipelines in [`filters/sets.py`][filters-sets] share the identical `correlated_inner_root` and `attach_exists` functions without branching or duplication.

3. **Derived rather than repeated knowledge:**
   - [`correlated_inner_root`][optimizer-predicates] dynamically derives the inner root from `queryset.model._base_manager.using(queryset.db).filter(pk=OuterRef("pk"))`.
   - [`_effective_alias_names`][optimizer-predicates] dynamically derives occupied names by inspecting `model._meta.get_fields()`, `attname`, `"pk"`, `query.annotations`, `query.extra`, and `query.values_select` directly from the live QuerySet instance.
   - [`_next_reserved_alias`][optimizer-predicates] dynamically derives the lowest non-colliding alias index from `_effective_alias_names(queryset)`.
   - [`attach_exists`][optimizer-predicates] derives the positive condition `Q(**{alias: True})` directly from the newly attached alias.
   No alias names or model shapes are hardcoded or statically repeated.

4. **Inverse and round-trip pairs:**
   - [`attach_exists`][optimizer-predicates] returns `(new_queryset, Q(**{alias: True}))`, allowing callers to compose either positive conditions or negated conditions (`~cond`) while preserving boolean operator semantics.
   - Chained subquery attachments advance monotonically (`_dst_predicate_0`, `_dst_predicate_1`, ...), coexisting safely with existing annotations and extra selections without name collisions or state clobbering.
   - Evaluated outer QuerySets maintain exact parity with unevaluated QuerySets because `.alias()` clones the query structure without altering cached results.

5. **Contracts restated in another medium:**
   The row-preserving existence predicate contract and multiset semantics are codified across:
   - Code: [`django_strawberry_framework/optimizer/predicates.py`][optimizer-predicates], [`django_strawberry_framework/filters/sets.py`][filters-sets], [`django_strawberry_framework/exceptions.py`][exceptions];
   - Specifications: [`docs/SPECS/spec-053-graph_substrate-0_1_1.md`][spec-053], [`docs/SPECS/spec-055-search_fields-0_1_2.md`][spec-055], [`docs/row-preserving-predicates-part1-plan.md`][predicates-plan], [`docs/row-preserving-predicates-part1-pg-explain.md`][predicates-explain];
   - Test suites: [`tests/optimizer/test_predicates.py`][test-optimizer-predicates] (275 lines verifying M2M row preservation, loan root inner aliasing, alias non-selection, count query optimization without DISTINCT, deterministic alias allocation, runtime guards, evaluated outer parity, composite primary key execution, and base manager isolation), [`tests/filters/test_sets.py`][test-filters-sets], [`tests/test_predicate_pg_explain.py`][test-predicate-pg-explain], [`tests/test_pg_explain_artifact_footer.py`][test-pg-explain-footer];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Changing the reserved alias prefix token):** Change the reserved alias prefix from `"_dst_predicate_"` to `"_dsf_exists_"`.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/predicates.py`][optimizer-predicates] (updating [`_RESERVED_ALIAS_PREFIX`][optimizer-predicates]).
  - *Site count:* 1.
- **Posited change 2 (Expanding the alias collision detection namespace):** Add inspection of query CTE aliases or window function aliases to `_effective_alias_names`.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/predicates.py`][optimizer-predicates] (updating [`_effective_alias_names`][optimizer-predicates]).
  - *Site count:* 1.
- **Posited change 3 (Adding an outer QuerySet slicing guard):** Reject sliced QuerySets (where `query.is_sliced` is `True`) in `attach_exists`.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/predicates.py`][optimizer-predicates] (adding the guard in [`attach_exists`][optimizer-predicates]).
  - *Site count:* 1.
- **Posited change 4 (Adjusting the inner correlation base manager or database routing):** Modify manager selection or routing behavior on inner roots.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/predicates.py`][optimizer-predicates] (updating [`correlated_inner_root`][optimizer-predicates]).
  - *Site count:* 1.
- **Posited change 5 (Modifying relational filter applicability or candidate routing in FilterSets):** Change the criteria for routing to-many filter fields through `attach_exists`.
  - *Sites that must move:* Exactly 1 site at caller owner: [`django_strawberry_framework/filters/sets.py`][filters-sets] (`_apply_flat_leaves`). Exactly 0 sites in `predicates.py`.
  - *Site count:* 1 (0 in target).

### Rejected candidates

1. **Injecting `DISTINCT` on the outer QuerySet inside `attach_exists`:**
   - Disproved per [spec-053][spec-053] and [spec-055][spec-055]. Attaching an `EXISTS` subquery is inherently row-preserving and does not multiply outer rows. Injected `DISTINCT` causes severe PostgreSQL query plan degradation (forcing sort/hash aggregate passes) and corrupts consumer multiset semantics.
2. **Adding a `negated: bool` parameter to `attach_exists`:**
   - Disproved per [spec-053][spec-053]. Negation placement is a boolean composition concern belonging to the caller. `attach_exists` remains minimal and orthogonal by returning `Q(**{alias: True})`, which callers can invert via `~cond` when building logical trees.
3. **Rewriting `pk__in` subqueries automatically to `EXISTS`:**
   - Disproved. `pk__in` and `EXISTS` are semantically equivalent sibling idioms serving different caller composition needs (e.g. `_apply_related_constraints` vs `_apply_flat_leaves`). Maintaining both as explicit siblings avoids fragile query AST rewriting.
4. **Embedding GraphQL selection traversal or field metadata inspection into `predicates.py`:**
   - Disproved. `predicates.py` is strictly a pure ORM primitive module. Coupling it to GraphQL AST nodes or descriptor converters would violate modular separation and impede reuse.

## Opportunities

None — `django_strawberry_framework/optimizer/predicates.py` is a clean, minimal, robust, and mathematically sound implementation. It acts as the singular source of truth for row-preserving ORM existence subquery primitives, exhibits zero duplicate logic, and maintains strict separation of concerns.

## Judgment

Zero-edit review. `optimizer/predicates.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/predicates.py --review docs/dry/dry-file-optimizer__predicates.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification conducted on `django_strawberry_framework/optimizer/predicates.py` covering all 5 inventory symbols (1 constant, 4 functions), connected runtime callers in `filters/sets.py`, error hierarchy in `exceptions.py`, and executable test coverage in `tests/optimizer/test_predicates.py`.

### Analysis & Boundary Challenges

1. **Existence Subquery & Multiset Preservation:**
   - Evaluated whether `attach_exists` or `correlated_inner_root` could leak `DISTINCT` or mutate the outer QuerySet beyond `.alias()`. Verified: `attach_exists` performs exactly one `.alias(**{alias: Exists(inner_queryset)})` mutation and returns `(new_queryset, Q(**{alias: True}))`. No `filter()`, `exclude()`, or `distinct()` calls are made on the outer QuerySet.
   - Verified that row multiplicity is preserved in full accordance with SQL multiset semantics and [spec-053][spec-053] / [spec-055][spec-055].

2. **Base Manager Start & Filter Isolation:**
   - Evaluated the rationale for `model._base_manager.using(queryset.db).filter(pk=OuterRef("pk"))`. Challenged whether consumer manager filters should be re-applied on the inner root. Confirmed: the outer QuerySet already applies consumer visibility and manager constraints. Replaying a filtered default manager inside the inner existence probe would introduce false negatives for existing outer records. Starting from `_base_manager` guarantees clean relational existence semantics without filter leakage.

3. **Composite Primary Key Correlation:**
   - Evaluated correlation expression `pk=OuterRef("pk")`. Confirmed via `tests/optimizer/test_predicates.py::test_composite_pk_correlation_executes_on_composite_fixture` that Django compiles this single expression to a `ColPairs` tuple comparison over composite primary key columns on live database tables without needing custom branching.

4. **Alias Namespace Collision Avoidance:**
   - Evaluated `_effective_alias_names` and `_next_reserved_alias`. Verified that the namespace inspects model field names, column attnames, `"pk"`, annotations (`annotate` and `alias`), `extra(select=...)` names, and `values_select` projected names. The deterministic counter (`_dst_predicate_0`, `_dst_predicate_1`, ...) safely avoids collisions with existing annotations (e.g. `_dst_order_*` window aliases or consumer aliases).

5. **Runtime Guard Family Coherence:**
   - Verified that all three caller-contract guards (same model, same db alias, no combinator) raise [`OptimizerError`][exceptions], maintaining exception hierarchy coherence across the optimizer subsystem.

6. **Coverage & Single-Edit-Site Verification:**
   - Verified that `export_dry_review.py check` passes with 100% coverage across all 5 definitions and constants.
   - Confirmed single-edit-site counts are 1 across all posited architectural changes.
   - All 13 unit tests in `tests/optimizer/test_predicates.py` pass.

### Conclusion

Worker 1's analysis is verified accurate and complete. The module is fully consolidated, orthogonal, and exhibits zero DRY violations. Status updated to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[predicates-explain]: ../row-preserving-predicates-part1-pg-explain.md
[predicates-plan]: ../row-preserving-predicates-part1-plan.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-053]: ../SPECS/spec-053-graph_substrate-0_1_1.md
[spec-055]: ../SPECS/spec-055-search_fields-0_1_2.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[optimizer-field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[optimizer-predicates]: ../../django_strawberry_framework/optimizer/predicates.py
[optimizer-selections]: ../../django_strawberry_framework/optimizer/selections.py
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->
[test-filters-sets]: ../../tests/filters/test_sets.py
[test-optimizer-predicates]: ../../tests/optimizer/test_predicates.py
[test-pg-explain-footer]: ../../tests/test_pg_explain_artifact_footer.py
[test-predicate-pg-explain]: ../../tests/test_predicate_pg_explain.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
