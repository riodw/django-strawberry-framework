# DRY review: `django_strawberry_framework/utils/relations.py`

Status: verified

## System trace

`django_strawberry_framework/utils/relations.py` implements the centralized relation taxonomy, path classification, lookup expression validation, traversal cardinality probes, and relation accessor resolvers ([spec-027][spec-027], [spec-028][spec-028], [spec-036][spec-036], [spec-046][spec-046]).

It owns the following architectural responsibilities:

1. **Relation Classification & Metadata Inspection:**
   - Type aliases & constants: [`RelationKind`][utils-relations], [`MANY_SIDE_RELATION_KINDS`][utils-relations], and [`_MISSING`][utils-relations].
   - Metadata readers: [`_relation_attr`][utils-relations] (`django_strawberry_framework/utils/relations.py::_relation_attr`), [`_relation_bool`][utils-relations] (`django_strawberry_framework/utils/relations.py::_relation_bool`), and [`_relation_name`][utils-relations] (`django_strawberry_framework/utils/relations.py::_relation_name`).
   - Structural protocol: [`_RelationFieldLike`][utils-relations] (`django_strawberry_framework/utils/relations.py::_RelationFieldLike` with `django_strawberry_framework/utils/relations.py::_RelationFieldLike.many_to_many`, `django_strawberry_framework/utils/relations.py::_RelationFieldLike.one_to_many`, `django_strawberry_framework/utils/relations.py::_RelationFieldLike.one_to_one`, `django_strawberry_framework/utils/relations.py::_RelationFieldLike.auto_created`, `django_strawberry_framework/utils/relations.py::_RelationFieldLike.concrete`).
   - Cardinality classifier: [`relation_kind`][utils-relations] (`django_strawberry_framework/utils/relations.py::relation_kind`) and [`is_many_side_relation_kind`][utils-relations] (`django_strawberry_framework/utils/relations.py::is_many_side_relation_kind`).

2. **Immutable Path Planning & Classification:**
   - Classification records: [`RelationPathHop`][utils-relations] (`django_strawberry_framework/utils/relations.py::RelationPathHop` with `django_strawberry_framework/utils/relations.py::RelationPathHop.segment`, `django_strawberry_framework/utils/relations.py::RelationPathHop.kind`, `django_strawberry_framework/utils/relations.py::RelationPathHop.target_model`, `django_strawberry_framework/utils/relations.py::RelationPathHop.many_side`) and [`ClassifiedPath`][utils-relations] (`django_strawberry_framework/utils/relations.py::ClassifiedPath` with `django_strawberry_framework/utils/relations.py::ClassifiedPath.model`, `django_strawberry_framework/utils/relations.py::ClassifiedPath.path`, `django_strawberry_framework/utils/relations.py::ClassifiedPath.hops`, `django_strawberry_framework/utils/relations.py::ClassifiedPath.terminal`, `django_strawberry_framework/utils/relations.py::ClassifiedPath.first_many_index`, `django_strawberry_framework/utils/relations.py::ClassifiedPath.relation_chain`).
   - Segment resolution & traversability: [`_resolve_segment_field`][utils-relations] (`django_strawberry_framework/utils/relations.py::_resolve_segment_field`) and [`_is_traversable_relation`][utils-relations] (`django_strawberry_framework/utils/relations.py::_is_traversable_relation`).
   - Strict path classifier: [`classify_path`][utils-relations] (`django_strawberry_framework/utils/relations.py::classify_path`).

3. **Lookup Expression Validation & Traversal Probing:**
   - Lookup expression validator: [`validate_lookup_expr`][utils-relations] (`django_strawberry_framework/utils/relations.py::validate_lookup_expr`).
   - Lenient fallback & cached probe: [`_lenient_traverses_to_many`][utils-relations] (`django_strawberry_framework/utils/relations.py::_lenient_traverses_to_many`), [`_classify_path_cached`][utils-relations] (`django_strawberry_framework/utils/relations.py::_classify_path_cached`), [`_path_traverses_to_many_cached`][utils-relations] (`django_strawberry_framework/utils/relations.py::_path_traverses_to_many_cached`), and [`path_traverses_to_many`][utils-relations] (`django_strawberry_framework/utils/relations.py::path_traverses_to_many`).

4. **Write-Surface Predicates & Accessor Resolution:**
   - Concrete relation predicates: [`is_forward_many_to_many`][utils-relations] (`django_strawberry_framework/utils/relations.py::is_forward_many_to_many`) and [`is_forward_concrete_relation`][utils-relations] (`django_strawberry_framework/utils/relations.py::is_forward_concrete_relation`).
   - Instance accessor resolution: [`instance_accessor`][utils-relations] (`django_strawberry_framework/utils/relations.py::instance_accessor`).
   - Composite PK detection: [`has_composite_pk`][utils-relations] (`django_strawberry_framework/utils/relations.py::has_composite_pk`).

Connected behavior examined:
- [`django_strawberry_framework/filters/base.py`][filters-base]: Filter field validation and distinct tagging via `path_traverses_to_many`.
- [`django_strawberry_framework/orders/sets.py`][orders-sets]: Order set aggregation planning via `path_traverses_to_many`.
- [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs]: Editable relation indexing via `is_forward_many_to_many` and `is_forward_concrete_relation`.
- [`django_strawberry_framework/optimizer/field_meta.py`][optimizer-field-meta]: Field metadata caching and accessor resolution via `instance_accessor` and `has_composite_pk`.
- [`tests/utils/`][tests-utils]: Test suite validating 32-path matrix classification and lookup expressions.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/relations.py --include-constants`):
- Parsed 1 target file, 679 lines.
- Complete inventory across all 38 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/relations.py` centralizes relation classification and path walking across all query and mutation flavors:
   - `relation_kind` and `is_many_side_relation_kind` provide the single authoritative taxonomy for GraphQL schema generation, filter distinct triggers, and optimizer join taxonomy.
   - `instance_accessor` eliminates splits between `ForeignObjectRel.name` (query vocabulary) and `get_accessor_name()` (instance attribute) across resolvers and prefetch builders.
   - `is_forward_many_to_many` and `is_forward_concrete_relation` unify editable relation detection across ModelForm, Serializer, and Model mutation pipelines.

2. **Sync and async twins:**
   Relation metadata inspection is synchronous and purely metadata-driven; no async twins are required.

3. **Derived rather than repeated knowledge:**
   - `classify_path` derives `first_many_index` and `relation_chain` during a single split-and-resolve walk.
   - `validate_lookup_expr` advances an expression cursor through chained transforms, validating subsequent parts against transform output fields.
   - `has_composite_pk` derives composite pk eligibility directly from `_meta.pk_fields`.

4. **Inverse and round-trip pairs:**
   - `ClassifiedPath` provides complete forward traversal hops while preserving the exact `terminal` field.
   - `path_traverses_to_many` pairs strict classification with `_lenient_traverses_to_many` fallback to maintain compatibility for invalid path queries.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/relations.py`][utils-relations], [`django_strawberry_framework/filters/base.py`][filters-base], [`django_strawberry_framework/orders/sets.py`][orders-sets], [`django_strawberry_framework/optimizer/field_meta.py`][optimizer-field-meta];
   - Specifications: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027], [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028], [`docs/SPECS/spec-036-mutation_visibility_contracts-0_0_10.md`][spec-036], [`docs/SPECS/spec-046-composite_pk_support-0_0_14.md`][spec-046];
   - Test suites: [`tests/utils/`][tests-utils], [`tests/filters/`][tests-filters], [`tests/orders/`][tests-orders];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding support for a new custom Django relation descriptor shape):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/relations.py`][utils-relations] ([`relation_kind`][utils-relations] and [`_is_traversable_relation`][utils-relations]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Adjusting the transform chaining logic in lookup validation):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/relations.py`][utils-relations] ([`validate_lookup_expr`][utils-relations]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Modifying how reverse relation accessor names are resolved):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/relations.py`][utils-relations] ([`instance_accessor`][utils-relations]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Re-implementing relation cardinality checks inside filter generation and order resolution:**
   - Disproved per [spec-027][spec-027] and [spec-028][spec-028]. Ad-hoc cardinality inspection caused regressions on unique reverse foreign keys and custom through models.

## Opportunities

None — `django_strawberry_framework/utils/relations.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/relations.py` exhibits zero duplicate code and complete policy consolidation across relation classification, path planning, and lookup validation. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/relations.py --review docs/dry/dry-file-utils__relations.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/relations.py`][utils-relations] and Worker 1's DRY review.

1. **Relation Taxonomy & Classification:**
   - Confirmed `relation_kind` properly distinguishes forward M2M, GenericRelation, reverse M2O, reverse O2O, and forward single relations.
   - Confirmed `classify_path` and `RelationPathHop` correctly capture relation topology, target models, and many-side cardinality.
   - Confirmed `instance_accessor` correctly resolves precomputed, callable `get_accessor_name()`, and fallback attribute names.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/relations.py --review docs/dry/dry-file-utils__relations.md --include-constants`. 100% coverage across all 38 definitions / constants.

Confirmed: `django_strawberry_framework/utils/relations.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-027]: ../SPECS/spec-027-filters-0_0_8.md
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-036]: ../SPECS/spec-036-mutation_visibility_contracts-0_0_10.md
[spec-046]: ../SPECS/spec-046-composite_pk_support-0_0_14.md

<!-- package source -->
[filters-base]: ../../django_strawberry_framework/filters/base.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[optimizer-field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests -->
[tests-filters]: ../../tests/filters/
[tests-orders]: ../../tests/orders/
[tests-utils]: ../../tests/utils/
