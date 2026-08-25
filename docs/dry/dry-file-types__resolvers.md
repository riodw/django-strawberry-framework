# DRY review: `django_strawberry_framework/types/resolvers.py`

Status: verified

## System trace

`django_strawberry_framework/types/resolvers.py` implements generated relation and file-field resolvers attached to `DjangoType` classes during type finalization ([spec-010][spec-010], [spec-011][spec-011], [spec-033][spec-033], [spec-035][spec-035], [spec-037][spec-037]).

It owns the following architectural responsibilities:

1. **Sentinels & Optimization Context Checks:**
   - [`_resolver_logger`][types-resolvers]: Re-export of canonical N+1 logger from optimizer subpackage.
   - Sentinels: [`_EMPTY_ELISIONS`][types-resolvers], [`_PLAN_UNREAD`][types-resolvers], and [`_FK_ELISION_UNSAFE`][types-resolvers].
   - [`_fk_attname_is_deferred`][types-resolvers] (`django_strawberry_framework/types/resolvers.py::_fk_attname_is_deferred`) and [`_build_fk_id_stub`][types-resolvers] (`django_strawberry_framework/types/resolvers.py::_build_fk_id_stub`): FK ID elision stub synthesis and deferred column safety.
   - Cache probes: [`_will_lazy_load_single`][types-resolvers] and [`_will_lazy_load_many`][types-resolvers].
   - Context readers: [`_strictness_for`][types-resolvers] and [`_relation_is_planned`][types-resolvers].
   - Strictness gate: [`_check_n1`][types-resolvers] (`django_strawberry_framework/types/resolvers.py::_check_n1`): Centralized N+1 lazy-load detection across single-valued, many-side, and connection relation shapes.

2. **Resolver Helpers & Target Visibility:**
   - [`_name_resolver`][types-resolvers] (`django_strawberry_framework/types/resolvers.py::_name_resolver`): Stable naming for generated resolver callables.
   - [`_field_meta_for_resolver`][types-resolvers] (`django_strawberry_framework/types/resolvers.py::_field_meta_for_resolver`): Metadata lookup for relation fields.
   - Visibility integration: [`_custom_visibility_type`][types-resolvers], [`_visible_related_object`][types-resolvers], [`_visible_many_rows`][types-resolvers], and [`_optimizer_scoped_relation`][types-resolvers].

3. **Resolver Construction & Attachment Pipelines:**
   - Relation resolvers: [`_make_relation_resolver`][types-resolvers] (`django_strawberry_framework/types/resolvers.py::_make_relation_resolver`) and [`_attach_relation_resolvers`][types-resolvers] (`django_strawberry_framework/types/resolvers.py::_attach_relation_resolvers`).
   - File field resolvers: [`_make_file_resolver`][types-resolvers] (`django_strawberry_framework/types/resolvers.py::_make_file_resolver`) and [`_attach_file_resolvers`][types-resolvers] (`django_strawberry_framework/types/resolvers.py::_attach_file_resolvers`).

Connected behavior examined:
- [`django_strawberry_framework/types/base.py`][types-base]: Pre-selected field lists and consumer-authored override tracking.
- [`django_strawberry_framework/types/converters.py`][types-converters]: `_field_output_type_for` mapping for file fields.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Invokes `_attach_relation_resolvers` and `_attach_file_resolvers` during Phase 2.
- [`django_strawberry_framework/optimizer/`][optimizer]: Plans, strictness context variables, and FK elision sets.
- [`django_strawberry_framework/resource_policy.py`][resource-policy]: Bounded list row slicing.
- [`tests/types/`][tests-types]: Test coverage for relation and file field resolvers.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/types/resolvers.py --include-constants`):
- Parsed 1 target file, 819 lines.
- Complete inventory across all 21 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `types/resolvers.py` centralizes relation and file-field resolver creation:
   - `_check_n1` unifies N+1 lazy-load enforcement for single-valued, many-side, and connection relations (`kind="connection_to_attr"`).
   - `_build_fk_id_stub` and `_FK_ELISION_UNSAFE` safeguard FK elision without duplicate queries.
   - Custom visibility checks (`_visible_related_object`, `_visible_many_rows`) ensure uniform scoping across all relation cardinalities.

2. **Sync and async twins:**
   Resolvers dynamically branch using `in_async_context()` and `_will_lazy_load_single(root, ...)`, offloading synchronous unloaded descriptor reads via `sync_to_async(getattr, thread_sensitive=True)` without thread hop overhead on warm caches.

3. **Derived rather than repeated knowledge:**
   Accessor names are derived via `instance_accessor(field)`. Output types for file fields are derived via `_field_output_type_for(field)`.

4. **Inverse and round-trip pairs:**
   Generated resolvers read Django instance attributes/descriptors and return properly formatted GraphQL structures.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/types/resolvers.py`][types-resolvers], [`django_strawberry_framework/types/base.py`][types-base], [`django_strawberry_framework/types/converters.py`][types-converters], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/optimizer/`][optimizer], [`django_strawberry_framework/resource_policy.py`][resource-policy];
   - Specifications: [`docs/SPECS/spec-010-relational_fields-0_0_4.md`][spec-010], [`docs/SPECS/spec-011-optimizer_core-0_0_4.md`][spec-011], [`docs/SPECS/spec-033-relation_connections-0_0_10.md`][spec-033], [`docs/SPECS/spec-035-optimizer_hardened_diffing-0_0_10.md`][spec-035], [`docs/SPECS/spec-037-file_and_image_fields-0_0_11.md`][spec-037];
   - Test suites: [`tests/types/`][tests-types];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adjusting N+1 lazy load detection for many-side relations):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/resolvers.py`][types-resolvers] ([`_will_lazy_load_many`][types-resolvers]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying FK id elision stub building and safety sentinel logic):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/resolvers.py`][types-resolvers] ([`_build_fk_id_stub`][types-resolvers] / [`_fk_attname_is_deferred`][types-resolvers]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Modifying file field resolver nullability handling):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/resolvers.py`][types-resolvers] ([`_make_file_resolver`][types-resolvers]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Duplicating N+1 checks across separate cardinality modules:**
   - Disproved per [spec-011][spec-011]. Unifying in `_check_n1` provides a single authoritative implementation of N+1 detection.
2. **Duplicating file field resolver logic:**
   - Disproved per [spec-037][spec-037]. Factoring into `_make_file_resolver` and `_attach_file_resolvers` mirrors the relation resolver architecture cleanly.

## Opportunities

None — `django_strawberry_framework/types/resolvers.py` is fully consolidated at root owners.

## Judgment

Verified. `types/resolvers.py` exhibits zero duplicate code and complete policy consolidation across relation resolvers, file resolvers, N+1 detection, and FK-id elisions. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/types/resolvers.py --review docs/dry/dry-file-types__resolvers.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/types/resolvers.py`][types-resolvers] and Worker 1's DRY review.

1. **Resolver Generation & Optimization Contracts:**
   - Confirmed `_check_n1`, `_build_fk_id_stub`, and `_optimizer_scoped_relation` provide robust integration with optimizer context without duplication.
   - Confirmed `_attach_relation_resolvers` and `_attach_file_resolvers` correctly respect consumer-authored field overrides.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/types/resolvers.py --review docs/dry/dry-file-types__resolvers.md --include-constants`. 100% coverage across all 21 definitions / constants.

Confirmed: `django_strawberry_framework/types/resolvers.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-010]: ../SPECS/spec-010-relational_fields-0_0_4.md
[spec-011]: ../SPECS/spec-011-optimizer_core-0_0_4.md
[spec-033]: ../SPECS/spec-033-relation_connections-0_0_10.md
[spec-035]: ../SPECS/spec-035-optimizer_hardened_diffing-0_0_10.md
[spec-037]: ../SPECS/spec-037-file_and_image_fields-0_0_11.md

<!-- package source -->
[optimizer]: ../../django_strawberry_framework/optimizer/
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py

<!-- tests -->
[tests-types]: ../../tests/types/
