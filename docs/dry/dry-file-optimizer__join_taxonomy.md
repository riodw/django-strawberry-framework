# DRY review: `django_strawberry_framework/optimizer/join_taxonomy.py`

Status: verified

## System trace

`django_strawberry_framework/optimizer/join_taxonomy.py` is the canonical single source of truth for parent/child join-condition classification across the query optimization pipeline ([spec-002][spec-002], [spec-004][spec-004], [spec-016][spec-016], [spec-033][spec-033], [spec-035][spec-035], [spec-051][spec-051]). It extracts, normalizes, and packages all join-derived relational facts required by nested-connection fetch planning (both the windowed-prefetch and Postgres LATERAL execution strategies) into a single immutable descriptor, eliminating ad-hoc descriptor inspection and repeated relation string/flag checking across query planning and execution consumers.

It owns the following architectural responsibilities:

1. **Lateral Join Shape Taxonomy (`LateralJoinShape`):**
   - [`LateralJoinShape`][optimizer-join-taxonomy] (`django_strawberry_framework/optimizer/join_taxonomy.py::LateralJoinShape`): Enumeration defining how a lateral or correlated child subquery joins back to its parent:
     - `DIRECT_FK`: Child table directly carries the parent ID column (reverse `ForeignKey`, reverse `OneToOneField`, and `GenericRelation`).
     - `THROUGH_TABLE`: Many-to-many join table owns the parent/child attachment (forward and reverse `ManyToManyField`).
     - `UNSUPPORTED`: Single-valued forward relations (`ForeignKey`, forward `OneToOneField`) that have no windowable or partitionable child collection.

2. **Windowable Relation Kinds (`WINDOWABLE_RELATION_KINDS`):**
   - [`WINDOWABLE_RELATION_KINDS`][optimizer-join-taxonomy] (`django_strawberry_framework/optimizer/join_taxonomy.py::WINDOWABLE_RELATION_KINDS`): Immutable `frozenset` defining the exact subset of [`RelationKind`][utils-relations] shapes that can be partitioned across parents in a windowed prefetch query (`"many"`, `"reverse_many_to_one"`, `"reverse_one_to_one"`, `"generic"`). Single-valued forward relations (`"forward_single"`) are excluded. Publicly exported so callers such as [`window_partition_for_prefetch`][optimizer-plans] can differentiate unsupported relation kinds from unresolved partition expressions without repeating the set.

3. **Defensive Metadata Containment Helpers:**
   - [`_safe_getattr`][optimizer-join-taxonomy] (`django_strawberry_framework/optimizer/join_taxonomy.py::_safe_getattr`): Reads attributes from descriptors or synthetic test doubles while catching all `BaseException` occurrences to guarantee planner safety.
   - [`_safe_truthy`][optimizer-join-taxonomy] (`django_strawberry_framework/optimizer/join_taxonomy.py::_safe_truthy`): Evaluates the truth value (`bool(value)`) of an object, safely catching hostile test doubles whose `__bool__` method raises an exception.
   - [`_safe_flag`][optimizer-join-taxonomy] (`django_strawberry_framework/optimizer/join_taxonomy.py::_safe_flag`): Combines [`_safe_getattr`][optimizer-join-taxonomy] and [`_safe_truthy`][optimizer-join-taxonomy] to read boolean descriptor flags safely.
   - [`_first_truthy`][optimizer-join-taxonomy] (`django_strawberry_framework/optimizer/join_taxonomy.py::_first_truthy`): Returns the first truthy argument from a sequence of candidate values, treating any raising truth test as false.

4. **Immutable Join Descriptor (`RelationJoinDescriptor`):**
   - [`RelationJoinDescriptor`][optimizer-join-taxonomy] (`django_strawberry_framework/optimizer/join_taxonomy.py::RelationJoinDescriptor`): Frozen dataclass carrying complete join metadata for a relation:
     - `kind`: Semantic [`RelationKind`][utils-relations] from [`relation_kind`][utils-relations].
     - `windowable`: Boolean flag indicating whether the relation is partitionable and resolved a valid partition expression.
     - `partition_expr`: Parent-side partition attribute name for SQL `PARTITION BY` (e.g. `"category_id"` for reverse FK, `"books"` for forward M2M, `"genres"` for reverse M2M, `"object_id"` for GenericRelation; `None` when unresolvable or unsupported).
     - `parent_join_column`: Child-side connector column name required by Django to attach prefetched child rows to parents.
     - `through_model`: Django M2M intermediate join table model (`type | None`) when `lateral_shape` is `THROUGH_TABLE`.
     - `lateral_shape`: [`LateralJoinShape`][optimizer-join-taxonomy] selector for lateral SQL generation.
     - `parent_link_field`: Resolved child-side or through-table FK field object pointing to the parent model for lateral joins.
     - `through_child_field`: Resolved through-table FK field object pointing to the child model for M2M lateral joins.
     - `content_type_column`: Resolved `content_type_id` attname for `GenericRelation` descriptors (`None` for standard relations).
     - [`RelationJoinDescriptor.prefetch_attach_columns`][optimizer-join-taxonomy] (`django_strawberry_framework/optimizer/join_taxonomy.py::RelationJoinDescriptor.prefetch_attach_columns`): Derived property returning the complete tuple of child columns needed for Django prefetch attachment (combining `parent_join_column` and `content_type_column` for generic relations to prevent N+1 deferred column loads).

5. **Internal Derivation Helpers:**
   - [`_partition_expr`][optimizer-join-taxonomy] (`django_strawberry_framework/optimizer/join_taxonomy.py::_partition_expr`): Derives the parent-side partition expression from `field.remote_field.attname` or `field.remote_field.name`.
   - [`_parent_join_column`][optimizer-join-taxonomy] (`django_strawberry_framework/optimizer/join_taxonomy.py::_parent_join_column`): Resolves the child connector column across reverse relations (`field.field.attname` or `reverse_connector_attname`), forward single relations (`field.target_field.attname` or `target_field_attname`), and M2M relations (`related_model._meta.pk.attname`).
   - [`_through_model`][optimizer-join-taxonomy] (`django_strawberry_framework/optimizer/join_taxonomy.py::_through_model`): Resolves intermediate through model from `field.through` or `remote_field.through`.
   - [`_through_link_fields`][optimizer-join-taxonomy] (`django_strawberry_framework/optimizer/join_taxonomy.py::_through_link_fields`): Resolves the through model's parent-side and child-side FK field objects via `forward_field.m2m_field_name()` and `forward_field.m2m_reverse_field_name()`, correctly orienting forward and reverse M2M links (including self-referential relations).
   - [`_generic_child_attname`][optimizer-join-taxonomy] (`django_strawberry_framework/optimizer/join_taxonomy.py::_generic_child_attname`): Resolves `GenericRelation` field attributes (`object_id_field_name` / `content_type_field_name`) to child model column attnames via `related_model._meta.get_field()`.

6. **Unified Classifier Entry Point (`classify_relation_join`):**
   - [`classify_relation_join`][optimizer-join-taxonomy] (`django_strawberry_framework/optimizer/join_taxonomy.py::classify_relation_join`): Pure, side-effect-free classifier building a [`RelationJoinDescriptor`][optimizer-join-taxonomy] from a raw Django model relation field or reverse relation descriptor. Operates under a strict never-raises contract: unresolvable or malformed test doubles gracefully fall back to `windowable=False`, `partition_expr=None`, and `lateral_shape=LateralJoinShape.UNSUPPORTED`.

Connected behavior examined:
- [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner]: Calls [`classify_relation_join`][optimizer-join-taxonomy] in `plan_connection_relation` to gate windowed prefetch planning, resolves connector columns via [`_connector_only_field`][optimizer-nested-planner] (a shim over `classify_relation_join`), and projects attach-complete columns in `_project_scalar_only_window` via [`RelationJoinDescriptor.prefetch_attach_columns`][optimizer-join-taxonomy].
- [`django_strawberry_framework/optimizer/lateral_fetch.py`][optimizer-lateral-fetch]: Reads `request.join` ([`RelationJoinDescriptor`][optimizer-join-taxonomy]) in `_build_lateral_spec` to extract `parent_link_field`, `lateral_shape`, and `through_child_field` for SQL AST subquery compilation.
- [`django_strawberry_framework/optimizer/single_parent_fetch.py`][optimizer-single-parent-fetch]: Reads `request.join` to verify `lateral_shape is LateralJoinShape.DIRECT_FK` and extract `parent_link_field`.
- [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch]: Carries `join: RelationJoinDescriptor` on [`NestedConnectionRequest`][optimizer-nested-fetch] constructed during planning.
- [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans]: Shims [`window_partition_for_prefetch`][optimizer-plans] over [`classify_relation_join`][optimizer-join-taxonomy], consuming [`WINDOWABLE_RELATION_KINDS`][optimizer-join-taxonomy] to enforce historical raise semantics.
- [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker]: Injects connector columns in `_ensure_connector_only_fields` using [`classify_relation_join(parent_field).prefetch_attach_columns`][optimizer-join-taxonomy].
- [`django_strawberry_framework/optimizer/field_meta.py`][optimizer-field-meta]: Provides static relation metadata snapshots; `join_taxonomy.py` consumes raw descriptors for attributes that only exist on raw fields (e.g., `remote_field.through`, `m2m_field_name`).
- [`django_strawberry_framework/utils/relations.py`][utils-relations]: Centralizes semantic relation topology classification ([`relation_kind`][utils-relations], [`RelationKind`][utils-relations]).
- [`tests/optimizer/test_join_taxonomy.py`][test-optimizer-join-taxonomy]: Comprehensive test suite verifying join classification across reverse FK, forward M2M, reverse M2M, forward single, reverse OneToOne, GenericRelation, missing related models, broken `_meta`, and hostile attribute/truthiness test doubles.
- [`tests/optimizer/test_lateral_fetch.py`][test-optimizer-lateral-fetch] & [`tests/test_lateral_pg_parity.py`][test-lateral-pg-parity]: Verify lateral query planning and SQL execution across all classified join shapes against real PostgreSQL databases.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/optimizer/join_taxonomy.py --include-constants`):
- Parsed 1 target file, 352 lines.
- Inventory of symbols:
  - 1 enumeration class: [`LateralJoinShape`][optimizer-join-taxonomy].
  - 1 constant: [`WINDOWABLE_RELATION_KINDS`][optimizer-join-taxonomy].
  - 4 defensive helper functions: [`_safe_getattr`][optimizer-join-taxonomy], [`_safe_truthy`][optimizer-join-taxonomy], [`_safe_flag`][optimizer-join-taxonomy], [`_first_truthy`][optimizer-join-taxonomy].
  - 1 dataclass: [`RelationJoinDescriptor`][optimizer-join-taxonomy].
  - 1 property method: [`RelationJoinDescriptor.prefetch_attach_columns`][optimizer-join-taxonomy].
  - 5 internal derivation functions: [`_partition_expr`][optimizer-join-taxonomy], [`_parent_join_column`][optimizer-join-taxonomy], [`_through_model`][optimizer-join-taxonomy], [`_through_link_fields`][optimizer-join-taxonomy], [`_generic_child_attname`][optimizer-join-taxonomy].
  - 1 public classification function: [`classify_relation_join`][optimizer-join-taxonomy].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   [`classify_relation_join`][optimizer-join-taxonomy] is the singular canonical classification engine for parent/child join condition mechanics across the entire query optimization subsystem. Neither sibling optimizer modules ([`nested_planner.py`][optimizer-nested-planner], [`lateral_fetch.py`][optimizer-lateral-fetch], [`walker.py`][optimizer-walker], [`plans.py`][optimizer-plans]) nor relation resolvers re-implement join shape classification or descriptor inspection:
   - Nested connection planner ([`nested_planner.py`][optimizer-nested-planner]) classifies raw relation fields via [`classify_relation_join`][optimizer-join-taxonomy] once per relation.
   - Historical shims ([`window_partition_for_prefetch`][optimizer-plans] and [`_connector_only_field`][optimizer-nested-planner]) are thin 1-line delegations to `classify_relation_join`.
   - Projection helpers ([`nested_planner.py::_project_scalar_only_window`][optimizer-nested-planner] and [`walker.py::_ensure_connector_only_fields`][optimizer-walker]) consume the single derived property [`RelationJoinDescriptor.prefetch_attach_columns`][optimizer-join-taxonomy] to safely append required connector columns without duplicating the GenericRelation morph column rule.
   - Postgres lateral fetch strategy ([`lateral_fetch.py`][optimizer-lateral-fetch]) reads precomputed link fields (`parent_link_field`, `through_child_field`) directly from `request.join`, avoiding duplicate descriptor inspection during SQL generation.
   - Semantic relation classification is cleanly decoupled and delegated to root in [`django_strawberry_framework/utils/relations.py`][utils-relations].
   There is zero duplicate join classification logic across flavors or modules.

2. **Sync and async twins:**
   Zero duplication. Join condition classification and descriptor derivation in `join_taxonomy.py` are purely synchronous, side-effect-free, deterministic in-memory operations. Both synchronous and asynchronous GraphQL execution paths share identical query plans and `RelationJoinDescriptor` instances generated during planning.

3. **Derived rather than repeated knowledge:**
   - [`RelationJoinDescriptor.prefetch_attach_columns`][optimizer-join-taxonomy] dynamically derives the required child columns (`parent_join_column` + `content_type_column`) on access.
   - `windowable` derives strictly from `kind in WINDOWABLE_RELATION_KINDS and partition is not None`.
   - `partition_expr` derives from `remote_field.attname or remote_field.name` (or `_generic_child_attname` for generic relations).
   - `parent_join_column` derives from `field.attname`, `target_field.attname`, or `related_model._meta.pk.attname`.
   - `through_model` derives from `field.through` or `remote_field.through`.
   - `parent_link_field` and `through_child_field` derive dynamically by querying the through table's `_meta.get_field` using `forward_field.m2m_field_name()` and `forward_field.m2m_reverse_field_name()`.
   No derived join property is manually restated or maintained separately.

4. **Inverse and round-trip pairs:**
   - For forward vs. reverse `ManyToManyField` relations, [`_through_link_fields`][optimizer-join-taxonomy] accurately inverts the source/target FK pairing: for forward M2M, parent is source FK and child is target FK; for reverse M2M, parent is target FK and child is source FK.
   - `RelationJoinDescriptor` is a frozen dataclass with value equality semantics, allowing safe caching, hashing, and comparison across planning passes.

5. **Contracts restated in another medium:**
   The join taxonomy and descriptor contracts are codified across:
   - Code: [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy], [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner], [`django_strawberry_framework/optimizer/lateral_fetch.py`][optimizer-lateral-fetch], [`django_strawberry_framework/optimizer/single_parent_fetch.py`][optimizer-single-parent-fetch], [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch], [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans], [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker], [`django_strawberry_framework/utils/relations.py`][utils-relations];
   - Specifications: [`docs/SPECS/spec-002-optimizer-0_0_2.md`][spec-002], [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004], [`docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md`][spec-016], [`docs/SPECS/spec-033-nested_connection_execution_plan-0_0_9.md`][spec-033], [`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`][spec-035], [`docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md`][spec-051];
   - Test suites: [`tests/optimizer/test_join_taxonomy.py`][test-optimizer-join-taxonomy] (15 dedicated tests covering reverse FK, forward/reverse M2M, forward single, reverse O2O, GenericRelation, missing related models, broken `_meta`, and hostile attribute/truthiness test doubles), [`tests/optimizer/test_plans.py`][test-optimizer-plans], [`tests/optimizer/test_walker.py`][test-optimizer-walker], [`tests/optimizer/test_lateral_fetch.py`][test-optimizer-lateral-fetch], [`tests/test_lateral_pg_parity.py`][test-lateral-pg-parity];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding a new lateral join shape, e.g. `ARRAY_JOIN` for PostgreSQL array-backed relations):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy] (adding the enum member to [`LateralJoinShape`][optimizer-join-taxonomy] and mapping it in [`classify_relation_join`][optimizer-join-taxonomy]).
  - *Site count:* 1 in target.
- **Posited change 2 (Expanding windowable relation kinds, e.g. supporting foreign object partitions):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy] (updating [`WINDOWABLE_RELATION_KINDS`][optimizer-join-taxonomy]).
  - *Site count:* 1 in target.
- **Posited change 3 (Modifying partition expression resolution for reverse relations):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy] (updating [`_partition_expr`][optimizer-join-taxonomy]).
  - *Site count:* 1 in target.
- **Posited change 4 (Updating child connector column resolution for M2M or generic relations):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy] (updating [`_parent_join_column`][optimizer-join-taxonomy] or [`_generic_child_attname`][optimizer-join-taxonomy]).
  - *Site count:* 1 in target.
- **Posited change 5 (Enhancing attach-complete column assembly, e.g. adding tenant partitioning keys):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy] (updating [`RelationJoinDescriptor.prefetch_attach_columns`][optimizer-join-taxonomy]).
  - *Site count:* 1 in target.

### Rejected candidates

1. **Re-deriving partition expressions and connector columns ad-hoc in each fetch strategy:**
   - Disproved per [spec-033][spec-033] (Decision 4) and [spec-035][spec-035]. Prior to consolidation, `plans.py::window_partition_for_prefetch` and `nested_planner.py::_connector_only_field` derived join facts independently, leading to subtle divergences in reverse M2M query naming and GenericRelation partition handling. Centralizing all join derivations into [`classify_relation_join`][optimizer-join-taxonomy] guarantees that windowed prefetch and lateral execution strategies share identical join-condition semantics.
2. **Passing `FieldMeta` instead of raw Django relation descriptors to `classify_relation_join`:**
   - Disproved per [spec-016][spec-016] and [spec-033][spec-033]. `FieldMeta` is a lightweight, precomputed model snapshot designed for schema converters and AST walking; it deliberately omits deep descriptor metadata such as `remote_field.through`, `m2m_field_name()`, and `m2m_reverse_field_name()`. Join planning requires direct access to these raw descriptor attributes to resolve through tables and link fields.
3. **Adding a `LateralJoinShape.GENERIC` arm to `LateralJoinShape`:**
   - Disproved per [spec-033][spec-033] and [spec-035][spec-035]. Generic relations require a constant content-type WHERE clause that Django injects late during prefetch execution; for lateral joins, leaving `parent_link_field=None` allows `_build_lateral_spec` to gracefully degrade generic relations to the windowed prefetch strategy rather than generating invalid correlated SQL joins.
4. **Allowing `classify_relation_join` to raise exceptions on unresolvable synthetic test doubles:**
   - Disproved per [spec-035][spec-035] and [spec-051][spec-051]. The query planner must never crash when encountering unmanaged models, mock objects, or malformed descriptors. Instead, `classify_relation_join` catches exceptions internally and marks the descriptor as `windowable=False` with `lateral_shape=LateralJoinShape.UNSUPPORTED`, leaving fallback decisions to the caller.

## Opportunities

None — `django_strawberry_framework/optimizer/join_taxonomy.py` is a clean, minimal, robust, and fully consolidated implementation. It acts as the singular source of truth for parent/child join condition classification across the entire framework, cleanly handles all Django relation shapes (reverse FK, forward M2M, reverse M2M, forward single, reverse OneToOne, GenericRelation), safely guards against malformed descriptors at the planner boundary, and exhibits zero redundant logic.

## Judgment

Zero-edit review. `optimizer/join_taxonomy.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/join_taxonomy.py --review docs/dry/dry-file-optimizer__join_taxonomy.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Worker 2 independently verified the join taxonomy contracts, boundaries, downstream callers, and test suites across the repository:

1. **Taxonomy and Strategy Contract Equivalence:**
   - Confirmed that [`classify_relation_join`][optimizer-join-taxonomy] serves as the sole authoritative classifier for all join mechanics.
   - Traced all downstream consumers:
     - [`nested_planner.py::plan_connection_relation`][optimizer-nested-planner] uses `classify_relation_join` to extract join descriptors for nested connection plans.
     - [`nested_planner.py::_connector_only_field`][optimizer-nested-planner] and [`plans.py::window_partition_for_prefetch`][optimizer-plans] are thin shims over `classify_relation_join` preserving legacy caller contracts.
     - [`nested_planner.py::_project_scalar_only_window`][optimizer-nested-planner] and [`walker.py::_ensure_connector_only_fields`][optimizer-walker] consume `join.prefetch_attach_columns` to ensure Django's prefetch attach never issues deferred N+1 queries.
     - [`lateral_fetch.py::_build_lateral_spec`][optimizer-lateral-fetch] and [`single_parent_fetch.py`][optimizer-single-parent-fetch] consume `parent_link_field`, `lateral_shape`, and `through_child_field` directly from `request.join`.
   - Verified that no competing or parallel join classification routines exist anywhere in `django_strawberry_framework`.

2. **Probing Matrix & Single-Edit Site Verification:**
   - All 5 axes of the duplication matrix were re-evaluated and confirmed discharged.
   - Single-edit-site counts hold at 1 for all posited structural and functional changes.

3. **Tool and Test Verification:**
   - Executed `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/join_taxonomy.py --review docs/dry/dry-file-optimizer__join_taxonomy.md --include-constants`: confirmed 14 target definitions covered with 0 errors.
   - Executed full test suite on `tests/optimizer/test_join_taxonomy.py` (15/15 tests passing).
   - Executed full optimizer test suite (`tests/optimizer/`, 813/813 tests passing).

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
[spec-016]: ../SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md
[spec-033]: ../SPECS/spec-033-nested_connection_execution_plan-0_0_9.md
[spec-035]: ../SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-051]: ../SPECS/spec-051-boundary_dry_squeeze-0_0_15.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[optimizer-field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[optimizer-join-taxonomy]: ../../django_strawberry_framework/optimizer/join_taxonomy.py
[optimizer-lateral-fetch]: ../../django_strawberry_framework/optimizer/lateral_fetch.py
[optimizer-nested-fetch]: ../../django_strawberry_framework/optimizer/nested_fetch.py
[optimizer-nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[optimizer-plans]: ../../django_strawberry_framework/optimizer/plans.py
[optimizer-single-parent-fetch]: ../../django_strawberry_framework/optimizer/single_parent_fetch.py
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->
[test-lateral-pg-parity]: ../../tests/test_lateral_pg_parity.py
[test-optimizer-join-taxonomy]: ../../tests/optimizer/test_join_taxonomy.py
[test-optimizer-lateral-fetch]: ../../tests/optimizer/test_lateral_fetch.py
[test-optimizer-plans]: ../../tests/optimizer/test_plans.py
[test-optimizer-walker]: ../../tests/optimizer/test_walker.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

