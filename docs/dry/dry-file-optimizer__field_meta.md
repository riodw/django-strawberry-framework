# DRY review: `django_strawberry_framework/optimizer/field_meta.py`

Status: verified

## System trace

`django_strawberry_framework/optimizer/field_meta.py` is the canonical single source of truth for Django field and relation metadata across the framework ([spec-002][spec-002], [spec-004][spec-004], [spec-035][spec-035], [spec-051][spec-051]). It captures, classifies, and caches immutable snapshots of Django model field descriptors at class-creation time, insulating the query optimizer walker, type converters, relation resolvers, schema finalizers, and management commands from repetitive and costly Django `_meta` reflection and descriptor attribute inspection.

It owns the following architectural responsibilities:

1. **Immutable Field Metadata Definition (`FieldMeta`):**
   - [`FieldMeta`][optimizer-field-meta] (`django_strawberry_framework/optimizer/field_meta.py::FieldMeta`): Frozen, slotted dataclass storing precomputed relation shape, cardinality flags, column names, target primary keys, and optimization eligibility:
     - `name`: The Django field name (snake_case).
     - `is_relation`: Boolean flag indicating whether the field represents a database relation.
     - `many_to_many`: Boolean flag indicating forward M2M relations (`ManyToManyField`).
     - `one_to_many`: Boolean flag indicating reverse FK relations (`ManyToOneRel`).
     - `one_to_one`: Boolean flag indicating OneToOne relations (forward `OneToOneField` or reverse `OneToOneRel`).
     - `nullable`: Cardinality-gated nullability rule. Reverse FK and M2M relations short-circuit to `False` (GraphQL lists `list[T]` are never `None` at the root/manager level); reverse OneToOne short-circuits to `True` (related row may be absent); other relations follow `field.null`.
     - `related_model`: Target Django model class (`type[models.Model] | None`).
     - `attname`: Database column name on the source model (e.g. `category_id` for forward FK; `None` for reverse relations).
     - `target_field_name`: Target model field name a FK or forward M2M points at (e.g. `"id"`), preserving custom `to_field` mappings.
     - `target_field_attname`: Target model column attname for the target field, preserving non-PK `to_field` connector columns.
     - `target_pk_name`: Related model's concrete primary-key field name (`_target_pk_name`), or `None` for non-relations or unresolvable targets.
     - `fk_id_elision_eligible`: Boolean flag indicating whether a forward single relation can satisfy an ID-only child selection directly from the source row's local FK column without issuing a database join or prefetch query.
     - `reverse_connector_attname`: Reverse FK connector column on the related model that points back to the parent model.
     - `auto_created`: Django auto-created descriptor flag (`True` for reverse relations and concrete multi-table inheritance parent links).
     - `accessor_name`: Attribute name used to access related rows on a model instance (`utils.relations.instance_accessor`), accounting for reverse FKs without `related_name` (e.g. `"book_set"` vs query name `"book"`).
     - `concrete`: Boolean flag indicating whether the field stores a column on the source model (distinguishing concrete MTI parent links from non-concrete reverse `OneToOneRel`).
     - `content_type_field_name`: Content-type FK column name for `GenericRelation` descriptors (`contenttypes`).
     - `object_id_field_name`: Object-id column name for `GenericRelation` descriptors.

2. **Cardinality & Type Properties:**
   - [`FieldMeta.relation_kind`][optimizer-field-meta] (`django_strawberry_framework/optimizer/field_meta.py::FieldMeta.relation_kind`): Property delegating to [`relation_kind(self)`][utils-relations] in `utils/relations.py` to classify the relation into the canonical five-shape taxonomy (`"many"`, `"generic"`, `"reverse_many_to_one"`, `"reverse_one_to_one"`, `"forward_single"`).
   - [`FieldMeta.is_many_side`][optimizer-field-meta] (`django_strawberry_framework/optimizer/field_meta.py::FieldMeta.is_many_side`): Property delegating to [`is_many_side_relation_kind(self.relation_kind)`][utils-relations] to determine whether the relation resolves as a GraphQL list.

3. **Descriptor Ingestion & Defensive Extraction:**
   - [`_DjangoFieldLike`][optimizer-field-meta] (`django_strawberry_framework/optimizer/field_meta.py::_DjangoFieldLike`): Structural Protocol defining the minimal attribute contract (`name: str`, `is_relation: bool`) required from incoming Django descriptors.
   - [`FieldMeta.from_django_field`][optimizer-field-meta] (`django_strawberry_framework/optimizer/field_meta.py::FieldMeta.from_django_field`): Canonical public factory constructor building a [`FieldMeta`][optimizer-field-meta] instance from a Django field descriptor. Validates required attributes and string name types, raising typed [`OptimizerError`][exceptions] at stamp time rather than failing with late `AttributeError` during AST walking.
   - [`FieldMeta._from_field_shape`][optimizer-field-meta] (`django_strawberry_framework/optimizer/field_meta.py::FieldMeta._from_field_shape`): Internal construction helper shared between [`from_django_field`][optimizer-field-meta] and resolver test-double fallbacks ([`types/resolvers.py::_field_meta_for_resolver`][types-resolvers]), centralizing attribute extraction, cardinality-gated nullability, and FK-id elision eligibility logic.
   - [`_target_pk_name`][optimizer-field-meta] (`django_strawberry_framework/optimizer/field_meta.py::_target_pk_name`): Defensive model primary-key inspection helper safely reading `model._meta.pk.name` while guarding against unmanaged test doubles, missing `_meta`, or non-standard primary-key configurations.

Connected behavior examined:
- [`django_strawberry_framework/types/base.py`][types-base]: Populates `field_map` on `DjangoType` class construction using `FieldMeta.from_django_field`.
- [`django_strawberry_framework/types/definition.py`][types-definition]: Stores `field_map: dict[str, FieldMeta]` on [`DjangoTypeDefinition`][types-definition].
- [`django_strawberry_framework/types/converters.py`][types-converters]: Reads `FieldMeta.is_many_side` and `FieldMeta.nullable` in field conversion factories.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Inspects `FieldMeta` during schema relation wiring and pending relation resolution.
- [`django_strawberry_framework/types/resolvers.py`][types-resolvers]: Consumes `FieldMeta` for relation resolvers, visibility filtering, and FK ID elision stubs (`_build_fk_id_stub`, `_field_meta_for_resolver`).
- [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker]: Reads cached `field_map` from `DjangoTypeDefinition` or stamps unregistered fallbacks via `FieldMeta.from_django_field` to drive AST selection optimization and join planning.
- [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension]: Uses `FieldMeta` via `DjangoTypeDefinition.field_map` for schema auditing (`check_schema`).
- [`django_strawberry_framework/management/commands/inspect_django_type.py`][management-inspect]: Reads `FieldMeta.relation_kind` to format field inspection tables.
- [`django_strawberry_framework/utils/relations.py`][utils-relations]: Duck-types `FieldMeta` instances alongside raw Django fields for unified relation classification and accessor resolution.
- [`tests/optimizer/test_field_meta.py`][test-optimizer-field-meta]: Comprehensive test suite verifying `FieldMeta` construction, nullability gates, MTI parent links, GenericRelation morph columns, FK ID elision eligibility, immutability, hashing, pickle serialization, and unregistered fallback stamping.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/optimizer/field_meta.py --include-constants`):
- Parsed 1 target file, 331 lines.
- Inventory of symbols:
  - 1 protocol definition: [`_DjangoFieldLike`][optimizer-field-meta].
  - 1 class definition: [`FieldMeta`][optimizer-field-meta].
  - 4 methods/properties on `FieldMeta`: [`FieldMeta.relation_kind`][optimizer-field-meta], [`FieldMeta.is_many_side`][optimizer-field-meta], [`FieldMeta.from_django_field`][optimizer-field-meta], [`FieldMeta._from_field_shape`][optimizer-field-meta].
  - 1 module-level function: [`_target_pk_name`][optimizer-field-meta].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   [`FieldMeta`][optimizer-field-meta] is the singular canonical source of truth for relation topology, cardinality, nullability, column names, accessors, and optimization flags across the entire codebase. No sibling subsystem (GraphQL schema converters, finalizer, optimizer walker, relation resolvers, or CLI tools) re-implements Django descriptor reflection:
   - Type definition creation ([`django_strawberry_framework/types/base.py`][types-base]) constructs `field_map: dict[str, FieldMeta]` once at class-creation time and attaches it to [`DjangoTypeDefinition`][types-definition].
   - Field conversion ([`django_strawberry_framework/types/converters.py`][types-converters]) and relation finalization ([`django_strawberry_framework/types/finalizer.py`][types-finalizer]) read cardinality and nullability directly from `FieldMeta`.
   - AST optimizer walker ([`django_strawberry_framework/optimizer/walker.py`][optimizer-walker]) reads `field_map` from the registered definition or falls back to `FieldMeta.from_django_field` on unregistered models, avoiding raw `_meta` calls during selection walks.
   - Relation resolvers and FK-id stubs ([`django_strawberry_framework/types/resolvers.py`][types-resolvers]) consume `FieldMeta` attributes (`attname`, `target_field_attname`, `fk_id_elision_eligible`, `accessor_name`) directly.
   - CLI tools ([`django_strawberry_framework/management/commands/inspect_django_type.py`][management-inspect]) query `FieldMeta.relation_kind`.
   - Relation classification and accessor algorithms are centralized at root in [`django_strawberry_framework/utils/relations.py`][utils-relations].
   There is zero duplicate descriptor reflection logic across flavors.

2. **Sync and async twins:**
   Zero duplication. Field metadata inspection, caching, and snapshot generation are purely synchronous, deterministic pure data structures. Synchronous and asynchronous GraphQL execution engines share identical `FieldMeta` snapshots on `DjangoTypeDefinition.field_map` without separate async metadata structures or branched logic.

3. **Derived rather than repeated knowledge:**
   - [`FieldMeta.relation_kind`][optimizer-field-meta] dynamically derives relation classification by delegating to [`relation_kind(self)`][utils-relations].
   - [`FieldMeta.is_many_side`][optimizer-field-meta] dynamically derives GraphQL list status by delegating to [`is_many_side_relation_kind(self.relation_kind)`][utils-relations].
   - `fk_id_elision_eligible` dynamically derives in [`_from_field_shape`][optimizer-field-meta] from `attname`, `related_model`, `target_pk_name`, `target_field_name`, cardinality flags, and [`has_composite_pk(related_model)`][utils-relations].
   - `nullable` derives deterministically: many-side cardinalities (M2M, reverse FK) evaluate to `False` (manager/queryset is never `None`), reverse OneToOne evaluates to `True`, and single relations follow `field.null`.
   - `accessor_name` derives via [`instance_accessor(field)`][utils-relations].
   - `target_pk_name` derives via [`_target_pk_name(related_model)`][optimizer-field-meta].
   No derived data is manually restated or maintained independently.

4. **Inverse and round-trip pairs:**
   - Slotted, frozen dataclass immutability ensures `FieldMeta` instances are hashable, shallow/deep copyable, and round-trippable via Python `pickle.loads(pickle.dumps(fm))` as verified in [`tests/optimizer/test_field_meta.py`][test-optimizer-field-meta].
   - Equality (`__eq__`) and hash (`__hash__`) semantics guarantee stable dictionary keys and set memberships.
   - Internal helper [`FieldMeta._from_field_shape`][optimizer-field-meta] unifies the extraction logic shared by [`from_django_field`][optimizer-field-meta] and resolver test-double fallbacks, preventing metadata skew.

5. **Contracts restated in another medium:**
   The `FieldMeta` architecture and relation contracts are codified across:
   - Code: [`django_strawberry_framework/optimizer/field_meta.py`][optimizer-field-meta], [`django_strawberry_framework/types/definition.py`][types-definition], [`django_strawberry_framework/types/base.py`][types-base], [`django_strawberry_framework/types/resolvers.py`][types-resolvers], [`django_strawberry_framework/types/converters.py`][types-converters], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker], [`django_strawberry_framework/utils/relations.py`][utils-relations];
   - Specifications: [`docs/SPECS/spec-002-optimizer-0_0_2.md`][spec-002] (O1–O6), [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004] (B7: precomputed field metadata), [`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`][spec-035], [`docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md`][spec-051];
   - Test suites: [`tests/optimizer/test_field_meta.py`][test-optimizer-field-meta] (732 lines covering scalar fields, nullable scalars, forward/reverse FK, forward/reverse M2M, GenericRelation morph columns, forward/reverse OneToOne, MTI parent links, FK ID elision edge cases, slot hashing, copy/pickle serialization, unregistered fallbacks, and defensive error containment), [`tests/optimizer/test_walker.py`][test-optimizer-walker], [`tests/types/test_resolvers.py`][test-types-resolvers], [`tests/types/test_base.py`][test-types-base];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding a new metadata attribute to FieldMeta, e.g. `db_column`):** Add a database column attribute to `FieldMeta` for SQL generation optimizations.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/field_meta.py`][optimizer-field-meta] (adding the attribute to [`FieldMeta`][optimizer-field-meta] dataclass and extracting it in [`FieldMeta._from_field_shape`][optimizer-field-meta]).
  - *Site count:* 1.
- **Posited change 2 (Adjusting the cardinality-gated nullability rule for reverse relations):** Update the nullability logic for reverse OneToOne or reverse FK relations.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/field_meta.py`][optimizer-field-meta] (updating the nullability expression in [`FieldMeta._from_field_shape`][optimizer-field-meta]).
  - *Site count:* 1.
- **Posited change 3 (Modifying FK-ID elision eligibility criteria):** Require additional constraints (e.g. source FK column non-nullability) before enabling FK-ID elision.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/field_meta.py`][optimizer-field-meta] (updating the `fk_id_elision_eligible` predicate in [`FieldMeta._from_field_shape`][optimizer-field-meta]).
  - *Site count:* 1.
- **Posited change 4 (Updating relation classification taxonomy or adding a new relation kind):** Add a new relation kind (e.g. partition relations) to the framework taxonomy.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/relations.py`][utils-relations] (`relation_kind`, `RelationKind`). Exactly 0 sites in `field_meta.py`.
  - *Site count:* 1 (0 in target).
- **Posited change 5 (Enhancing defensive primary-key name resolution):** Add support for non-standard primary key descriptors on proxy models.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/field_meta.py`][optimizer-field-meta] (updating [`_target_pk_name`][optimizer-field-meta]).
  - *Site count:* 1.

### Rejected candidates

1. **Making `FieldMeta` a mutable dictionary or dynamic object:**
   - Disproved per [spec-004][spec-004] (B7). An immutable, slotted dataclass prevents runtime mutation bugs, enables safe hashability for caching and set operations, minimizes memory overhead per field, and guarantees high-performance attribute access during query plan walking.
2. **Re-evaluating raw Django descriptors on every selection walk:**
   - Disproved per [spec-004][spec-004] (B7). Re-evaluating `_meta` descriptors repeatedly during AST walking causes substantial CPU overhead. Computing `FieldMeta` once during `DjangoType` class construction in `__init_subclass__` and storing it on `DjangoTypeDefinition.field_map` ensures O(1) attribute lookups during AST traversal.
3. **Allowing `ForeignObjectRel.null=True` default to dictate GraphQL nullability on many-side relations:**
   - Disproved per [spec-004][spec-004] and [spec-035][spec-035]. Django reverse FK and reverse M2M descriptors inherit `null=True` at the class level. In GraphQL, many-side relations always resolve to `list[T]` (never `None`), so `FieldMeta` enforces `nullable=False` for many-side relations to prevent schema corruption (`list[T] | None`).
4. **Permitting FK-ID elision when target model uses composite primary keys or non-PK `to_field`:**
   - Disproved per [spec-035][spec-035]. FK-ID elision replaces a database join with the parent row's scalar FK column. When the target relation points to a non-PK `to_field` or when the target model uses composite primary keys, eliding the join would produce an invalid ID or fail to fulfill the scalar contract.

## Opportunities

None — `django_strawberry_framework/optimizer/field_meta.py` is a clean, minimal, robust, and fully consolidated implementation. It acts as the singular source of truth for relation topology across the entire framework, cleanly delegates classification to `utils/relations.py`, guards against invalid inputs at stamp time, and exhibits zero redundant logic.

## Judgment

Zero-edit review. `optimizer/field_meta.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/field_meta.py --review docs/dry/dry-file-optimizer__field_meta.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independently traced and verified `django_strawberry_framework/optimizer/field_meta.py` across all callers, sibling modules, test suites, and specifications.

1. **Behavioral Trace & Boundary Analysis:**
   - **Immutable Snapshot & Type Definition Wiring:** Re-verified [`FieldMeta`][optimizer-field-meta] as a frozen, slotted dataclass serving as the single source of truth for relation topology, column names, cardinality, and nullability across the package. Confirmed that [`DjangoType.__init_subclass__`][types-base] maps model fields to `FieldMeta` instances once at class-creation time via [`FieldMeta.from_django_field`][optimizer-field-meta], attaching them immutably to [`DjangoTypeDefinition.field_map`][types-definition].
   - **Centralized Classifier Delegation:** Re-verified that [`FieldMeta.relation_kind`][optimizer-field-meta] and [`FieldMeta.is_many_side`][optimizer-field-meta] cleanly delegate to [`relation_kind(self)`][utils-relations] and [`is_many_side_relation_kind(self.relation_kind)`][utils-relations] in `utils/relations.py`, maintaining strict topological classification (`"many"`, `"generic"`, `"reverse_many_to_one"`, `"reverse_one_to_one"`, `"forward_single"`) without duplicating classification heuristics.
   - **Unified Shared Extraction (`_from_field_shape`):** Re-verified [`FieldMeta._from_field_shape`][optimizer-field-meta] as the shared consolidation point for attribute extraction between the canonical [`FieldMeta.from_django_field`][optimizer-field-meta] and [`types/resolvers.py::_field_meta_for_resolver`][types-resolvers] test-double fallback. Re-verified that `from_django_field` enforces strict descriptor contracts ([`_DjangoFieldLike`][optimizer-field-meta]) and raises typed [`OptimizerError`][exceptions] on missing `name`/`is_relation` attributes at stamp time.
   - **Cardinality-Gated Nullability & FK-ID Elision:** Re-verified cardinality gating in `_from_field_shape`: many-side relations (`many_to_many`, `one_to_many`) short-circuit `nullable` to `False` (defending GraphQL `list[T]` from `ForeignObjectRel.null=True` class-level leakage), and reverse OneToOne relations short-circuit to `True`. Re-verified strict eligibility predicates for `fk_id_elision_eligible` (`attname is not None`, `related_model is not None`, `target_pk_name is not None`, `target_field_name == target_pk_name`, non-many, `forward_single`, and `not has_composite_pk(related_model)`).
   - **Defensive Target PK Resolution:** Re-verified [`_target_pk_name`][optimizer-field-meta] defensively inspecting `model._meta.pk.name` and catching missing `_meta` or non-standard configurations cleanly.

2. **Mandatory 5-Axis Matrix Discharge:**
   - *Cross-flavor policy mirroring:* Verified. `FieldMeta` snapshots are universally consumed by AST walkers, type converters, relation resolvers, schema finalizers, and CLI inspection commands without redundant descriptor inspection.
   - *Sync and async twins:* Verified. `FieldMeta` is pure, deterministic frozen data shared uniformly across sync and async execution pipelines.
   - *Derived rather than repeated knowledge:* Verified. `relation_kind`, `is_many_side`, `nullable`, `fk_id_elision_eligible`, `accessor_name`, and `target_pk_name` derive dynamically from primary field attributes and centralized utility helpers.
   - *Inverse and round-trip pairs:* Verified. Frozen slotted dataclass preserves hashability, equality, copyability, and round-trip pickle serialization (`pickle.loads(pickle.dumps(fm))`).
   - *Contracts restated in another medium:* Verified. Codified in specifications ([spec-002][spec-002], [spec-004][spec-004], [spec-035][spec-035], [spec-051][spec-051]), tests ([`tests/optimizer/test_field_meta.py`][test-optimizer-field-meta], [`tests/optimizer/test_walker.py`][test-optimizer-walker], [`tests/types/test_resolvers.py`][test-types-resolvers], [`tests/types/test_base.py`][test-types-base]), and documentation ([`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook]).

3. **Single-Edit-Site Counts:**
   - Posited changes 1–5 verified with single-edit-site counts of 1 at authoritative root owners.

4. **Tooling & Test Gate:**
   - Ran `export_dry_review.py check --target django_strawberry_framework/optimizer/field_meta.py --review docs/dry/dry-file-optimizer__field_meta.md --include-constants` (7 target definitions covered).
   - Test suite in `tests/optimizer/test_field_meta.py` passes cleanly (28 tests passing).

Status verified.

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
[spec-035]: ../SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-051]: ../SPECS/spec-051-boundary_dry_squeeze-0_0_15.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[management-inspect]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[optimizer-field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->
[test-optimizer-field-meta]: ../../tests/optimizer/test_field_meta.py
[test-optimizer-walker]: ../../tests/optimizer/test_walker.py
[test-types-base]: ../../tests/types/test_base.py
[test-types-resolvers]: ../../tests/types/test_resolvers.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
