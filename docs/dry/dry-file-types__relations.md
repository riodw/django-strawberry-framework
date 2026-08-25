# DRY review: `django_strawberry_framework/types/relations.py`

Status: verified

## System trace

`django_strawberry_framework/types/relations.py` implements the scaffolding objects that carry relation fields from class collection to finalization ([spec-010][spec-010], [spec-018][spec-018]).

It owns the following architectural responsibilities:

1. **Pending Relation Scaffolding:**
   - [`_hash_component`][types-relations] (`django_strawberry_framework/types/relations.py::_hash_component`): Safe hash component extractor for unhashable or malformed metadata.
   - [`PendingRelation`][types-relations] (`django_strawberry_framework/types/relations.py::PendingRelation`): Frozen dataclass capturing unresolved relation metadata:
     - [`PendingRelation.source_type`][types-relations]
     - [`PendingRelation.source_model`][types-relations]
     - [`PendingRelation.field_name`][types-relations]
     - [`PendingRelation.django_field`][types-relations]
     - [`PendingRelation.related_model`][types-relations]
     - [`PendingRelation.relation_kind`][types-relations]
     - [`PendingRelation.nullable`][types-relations]
     - [`PendingRelation.__hash__`][types-relations]

2. **Annotation Sentinel:**
   - [`_PendingRelationAnnotationMeta`][types-relations] (`django_strawberry_framework/types/relations.py::_PendingRelationAnnotationMeta`):
     - [`_PendingRelationAnnotationMeta.__repr__`][types-relations]: Provides diagnostic guidance if an unfinalized class reaches `strawberry.Schema`.
   - [`PendingRelationAnnotation`][types-relations] (`django_strawberry_framework/types/relations.py::PendingRelationAnnotation`): Sentinel type placeholder installed in `cls.__annotations__`.

Connected behavior examined:
- [`django_strawberry_framework/types/base.py`][types-base]: `_build_annotations` records `PendingRelation` and installs `PendingRelationAnnotation`.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: `finalize_django_types` resolves pending relations and rewrites the sentinel via `resolved_relation_annotation`.
- [`django_strawberry_framework/registry.py`][registry]: Pending relation collection and identity-based discarding.
- [`tests/types/`][tests-types]: Test coverage for pending relations and annotation rewriting.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/types/relations.py --include-constants`):
- Parsed 1 target file, 111 lines.
- Complete inventory across all 11 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `types/relations.py` provides the single definition for pending relation representation across all relation kinds (forward FK, reverse FK, M2M).

2. **Sync and async twins:**
   Pending relation registration and annotation rewriting are synchronous class introspection steps.

3. **Derived rather than repeated knowledge:**
   `PendingRelation.__hash__` safely extracts hash components from potentially unhashable Django field references.

4. **Inverse and round-trip pairs:**
   `PendingRelationAnnotation` is installed at class declaration and rewritten during type finalization.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/types/relations.py`][types-relations], [`django_strawberry_framework/types/base.py`][types-base], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/registry.py`][registry];
   - Specifications: [`docs/SPECS/spec-010-relational_fields-0_0_4.md`][spec-010], [`docs/SPECS/spec-018-primary_ambiguity-0_0_6.md`][spec-018];
   - Test suites: [`tests/types/`][tests-types];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a diagnostic field to `PendingRelation`):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/relations.py`][types-relations] ([`PendingRelation`][types-relations]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying unfinalized relation annotation sentinel repr message):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/relations.py`][types-relations] ([`_PendingRelationAnnotationMeta.__repr__`][types-relations]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Scattering raw tuples for pending relations:**
   - Disproved per [spec-010][spec-010]. Structuring into `PendingRelation` dataclass guarantees type safety and uniform introspection across registry and finalizer.

## Opportunities

None — `django_strawberry_framework/types/relations.py` is fully consolidated at root owners.

## Judgment

Verified. `types/relations.py` exhibits zero duplicate code and complete policy consolidation across pending relation tracking and sentinel annotation representation. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/types/relations.py --review docs/dry/dry-file-types__relations.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/types/relations.py`][types-relations] and Worker 1's DRY review.

1. **Pending Relation Lifecycle:**
   - Confirmed `PendingRelation` and `PendingRelationAnnotation` provide clean scaffolding between class declaration and type finalization.
   - Confirmed identity-based discarding in the registry avoids reliance on unhashable Django model fields.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/types/relations.py --review docs/dry/dry-file-types__relations.md --include-constants`. 100% coverage across all 11 definitions / constants.

Confirmed: `django_strawberry_framework/types/relations.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-010]: ../SPECS/spec-010-relational_fields-0_0_4.md
[spec-018]: ../SPECS/spec-018-primary_ambiguity-0_0_6.md

<!-- package source -->
[registry]: ../../django_strawberry_framework/registry.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-relations]: ../../django_strawberry_framework/types/relations.py

<!-- tests -->
[tests-types]: ../../tests/types/
