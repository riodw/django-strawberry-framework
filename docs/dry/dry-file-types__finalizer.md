# DRY review: `django_strawberry_framework/types/finalizer.py`

Status: verified

## System trace

`django_strawberry_framework/types/finalizer.py` implements `finalize_django_types()`, the once-only finalization build gate for collected `DjangoType` classes ([spec-018][spec-018], [spec-027][spec-027], [spec-028][spec-028], [spec-030][spec-030], [spec-031][spec-031], [spec-032][spec-032], [spec-033][spec-033], [spec-034][spec-034], [spec-036][spec-036], [spec-037][spec-037], [spec-038][spec-038], [spec-040][spec-040], [spec-047][spec-047], [spec-051][spec-051]).

It owns the following architectural responsibilities:

1. **Diagnostic Formatting & Audits:**
   - Diagnostic formatters: [`_safe_qualified_class_name`][types-finalizer], [`_safe_field_label`][types-finalizer], [`_safe_str`][types-finalizer], and [`_annotation_names`][types-finalizer].
   - Ambiguity & unresolved error formatters: [`_format_unresolved_targets_error`][types-finalizer] and [`_format_ambiguity_error`][types-finalizer].
   - [`_audit_primary_ambiguity`][types-finalizer] (`django_strawberry_framework/types/finalizer.py::_audit_primary_ambiguity`): Rejects multi-type models lacking a declared primary.
   - [`_field_surface_names`][types-finalizer] (`django_strawberry_framework/types/finalizer.py::_field_surface_names`) and [`_audit_field_surface`][types-finalizer] (`django_strawberry_framework/types/finalizer.py::_audit_field_surface`): Settled field surface computation and collision/empty audit.
   - GlobalID routing audit: [`_format_model_label_routing_error`][types-finalizer], [`_audit_model_label_routing`][types-finalizer], [`_first_model_label_emitter`][types-finalizer], and [`_warn_model_label_secondary_collapse`][types-finalizer].

2. **Relation Connection Synthesis & Lifecycle:**
   - Sentinel and helper constants: [`_SYNTHESIZED_RELATION_CONNECTION_MARKER`][types-finalizer] and [`_MISSING_CLASS_MEMBER`][types-finalizer].
   - [`_suppress_relation_list_form`][types-finalizer] (`django_strawberry_framework/types/finalizer.py::_suppress_relation_list_form`): Suppresses list annotation and resolver for connection-only relations.
   - [`_record_relation_connection`][types-finalizer] (`django_strawberry_framework/types/finalizer.py::_record_relation_connection`): Records generated-to-underlying mapping on `DjangoTypeDefinition`.
   - [`_register_relation_connection_teardown`][types-finalizer] (`django_strawberry_framework/types/finalizer.py::_register_relation_connection_teardown`): Registers identity-safe reset callback.
   - [`_synthesize_relation_connections`][types-finalizer] (`django_strawberry_framework/types/finalizer.py::_synthesize_relation_connections`): Synthesizes `<field>_connection` fields on Relay-Node types.

3. **Multi-Phase Finalization Driver:**
   - [`finalize_django_types`][types-finalizer] (`django_strawberry_framework/types/finalizer.py::finalize_django_types`): The 4-phase build gate.

4. **Sidecar Binding (FilterSet & OrderSet Integration per spec-051):**
   - [`_bind_set_owner_common`][types-finalizer] (`django_strawberry_framework/types/finalizer.py::_bind_set_owner_common`): Shared owner binding core.
   - [`_bind_filterset_owner`][types-finalizer] (`django_strawberry_framework/types/finalizer.py::_bind_filterset_owner`): FilterSet owner binding.
   - [`_check_filterset_owner_axes`][types-finalizer], [`_check_filterset_owner_get_queryset_safety`][types-finalizer], and [`_check_filterset_owner_pk_identity`][types-finalizer]: Filter-specific multi-owner safety audits.
   - Shared sidecar error formatters: [`_format_owner_target_mismatch_error`][types-finalizer], [`_format_owner_pk_mismatch_error`][types-finalizer], [`_format_owner_get_queryset_mismatch_error`][types-finalizer], [`_format_owner_set_model_mismatch_error`][types-finalizer], [`_format_owner_model_mismatch_error`][types-finalizer], [`_format_orphan_sets_error`][types-finalizer], and [`_format_unregistered_related_target_error`][types-finalizer].
   - [`_bind_orderset_owner`][types-finalizer] and [`_format_owner_orderset_model_mismatch_error`][types-finalizer]: OrderSet owner binding.
   - Dataclass spec: [`_SidecarBindingSpec`][types-finalizer] (`django_strawberry_framework/types/finalizer.py::_SidecarBindingSpec`):
     - [`_SidecarBindingSpec.definition_attr`][types-finalizer]
     - [`_SidecarBindingSpec.expand_label_noun`][types-finalizer]
     - [`_SidecarBindingSpec.related_noun`][types-finalizer]
     - [`_SidecarBindingSpec.bind_owner`][types-finalizer]
     - [`_SidecarBindingSpec.helper_ledger`][types-finalizer]
     - [`_SidecarBindingSpec.factory_cls`][types-finalizer]
     - [`_SidecarBindingSpec.materialize`][types-finalizer]
     - [`_SidecarBindingSpec.format_orphans`][types-finalizer]
     - [`_SidecarBindingSpec.expand`][types-finalizer]
     - [`_SidecarBindingSpec.post_expand_audit`][types-finalizer]
   - Expansion and subpass audits: [`_expand_filterset`][types-finalizer], [`_expand_orderset`][types-finalizer], [`_audit_unregistered_related_filter_targets`][types-finalizer], [`_audit_globalid_filter_strategies`][types-finalizer], [`_format_globalid_encode_only_filter_error`][types-finalizer], and [`_audit_filterset_subpass_2_5`][types-finalizer].
   - Drivers: [`_bind_sidecar_sets`][types-finalizer], [`_bind_filtersets`][types-finalizer], and [`_bind_ordersets`][types-finalizer].

Connected behavior examined:
- [`django_strawberry_framework/types/base.py`][types-base]: Type registration and metadata initialization.
- [`django_strawberry_framework/types/relay.py`][types-relay]: Relay node validation and resolver installation.
- [`django_strawberry_framework/types/resolvers.py`][types-resolvers]: Resolver attachment during Phase 2.
- [`django_strawberry_framework/filters/`][filters]: FilterSet binding and input class materialization.
- [`django_strawberry_framework/orders/`][orders]: OrderSet binding and input class materialization.
- [`django_strawberry_framework/mutations/`][mutations]: Mutation binding during Phase 2.5.
- [`tests/types/`][tests-types]: Test coverage for type finalization and edge cases.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/types/finalizer.py --include-constants`):
- Parsed 1 target file, 2014 lines.
- Complete inventory across all 54 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `types/finalizer.py` implements unified cross-flavor pipelines:
   - `_SidecarBindingSpec` and `_bind_sidecar_sets` unify the multi-subpass owner binding, expansion, orphan validation, and input materialization loops for `FilterSet` and `OrderSet` (spec-051).
   - `_format_owner_set_model_mismatch_error`, `_format_owner_target_mismatch_error`, and `_format_orphan_sets_error` share unified error formatting logic parameterized by family nouns.
   - Multi-type model list is materialized once per build and shared across Phase-1 and Phase-2.5 audits.

2. **Sync and async twins:**
   All finalization steps, interface modifications, resolver attachments, and materialization runs operate synchronously at schema build time.

3. **Derived rather than repeated knowledge:**
   `_field_surface_names` derives the settled pre-decoration GraphQL surface dynamically from class MRO, annotations, and `StrawberryField` definitions. `_audit_model_label_routing` derives routing validity from primary/secondary strategy classifications.

4. **Inverse and round-trip pairs:**
   `_register_relation_connection_teardown` registers exact inverses for connection synthesis, ensuring test-suite `registry.clear()` restores pre-synthesis class state cleanly.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/types/base.py`][types-base], [`django_strawberry_framework/types/relay.py`][types-relay], [`django_strawberry_framework/types/resolvers.py`][types-resolvers], [`django_strawberry_framework/filters/base.py`][filters-base], [`django_strawberry_framework/orders/base.py`][orders-base], [`django_strawberry_framework/mutations/sets.py`][mutations-sets], [`django_strawberry_framework/registry.py`][registry];
   - Specifications: [`docs/SPECS/spec-018-primary_ambiguity-0_0_6.md`][spec-018], [`docs/SPECS/spec-027-filters_first_class-0_0_8.md`][spec-027], [`docs/SPECS/spec-028-orders_first_class-0_0_8.md`][spec-028], [`docs/SPECS/spec-030-connection_sidecar-0_0_9.md`][spec-030], [`docs/SPECS/spec-031-globalid_strategies-0_0_9.md`][spec-031], [`docs/SPECS/spec-032-full_relay-0_0_9.md`][spec-032], [`docs/SPECS/spec-033-relation_connections-0_0_10.md`][spec-033], [`docs/SPECS/spec-034-schema_finalization_refactor-0_0_10.md`][spec-034], [`docs/SPECS/spec-036-mutations-0_0_11.md`][spec-036], [`docs/SPECS/spec-037-file_and_image_fields-0_0_11.md`][spec-037], [`docs/SPECS/spec-038-form_mutations-0_0_11.md`][spec-038], [`docs/SPECS/spec-040-auth_mutations-0_0_12.md`][spec-040], [`docs/SPECS/spec-047-connection_by_default-0_0_14.md`][spec-047], [`docs/SPECS/spec-051-finalizer_sidecar_dry-0_0_14.md`][spec-051];
   - Test suites: [`tests/types/`][tests-types];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new phase-2.5 sidecar subsystem binding step):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/finalizer.py`][types-finalizer] ([`finalize_django_types`][types-finalizer] / [`_bind_sidecar_sets`][types-finalizer]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Adjusting the multi-owner sidecar model mismatch error format):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/finalizer.py`][types-finalizer] ([`_format_owner_set_model_mismatch_error`][types-finalizer]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Modifying the field surface collision detection algorithm):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/finalizer.py`][types-finalizer] ([`_field_surface_names`][types-finalizer] / [`_audit_field_surface`][types-finalizer]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Duplicating sidecar binding subpass loops between filters and orders:**
   - Disproved per [spec-051][spec-051]. Factored into `_SidecarBindingSpec` and `_bind_sidecar_sets`, eliminating structural duplication while preserving family-specific checks and error messages.
2. **Scattering GraphQL type name and surface derivation:**
   - Disproved per [spec-034][spec-034]. Factored into `_field_surface_names` and `DjangoTypeDefinition.graphql_type_name`.

## Opportunities

None — `django_strawberry_framework/types/finalizer.py` is fully consolidated at root owners.

## Judgment

Verified. `types/finalizer.py` exhibits zero duplicate code and complete policy consolidation across type finalization, sidecar binding, relation connection synthesis, and schema surface validation. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/types/finalizer.py --review docs/dry/dry-file-types__finalizer.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/types/finalizer.py`][types-finalizer] and Worker 1's DRY review.

1. **Unified Sidecar & Finalization Architecture:**
   - Confirmed `_SidecarBindingSpec` and `_bind_sidecar_sets` implement a robust shared binding skeleton for filters and orders without regression.
   - Confirmed diagnostic formatters and multi-phase execution guarantees remain strictly centralized.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/types/finalizer.py --review docs/dry/dry-file-types__finalizer.md --include-constants`. 100% coverage across all 54 definitions / constants.

Confirmed: `django_strawberry_framework/types/finalizer.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-018]: ../SPECS/spec-018-primary_ambiguity-0_0_6.md
[spec-027]: ../SPECS/spec-027-filters_first_class-0_0_8.md
[spec-028]: ../SPECS/spec-028-orders_first_class-0_0_8.md
[spec-030]: ../SPECS/spec-030-connection_sidecar-0_0_9.md
[spec-031]: ../SPECS/spec-031-globalid_strategies-0_0_9.md
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md
[spec-033]: ../SPECS/spec-033-relation_connections-0_0_10.md
[spec-034]: ../SPECS/spec-034-schema_finalization_refactor-0_0_10.md
[spec-036]: ../SPECS/spec-036-mutations-0_0_11.md
[spec-037]: ../SPECS/spec-037-file_and_image_fields-0_0_11.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_11.md
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_12.md
[spec-047]: ../SPECS/spec-047-connection_by_default-0_0_14.md
[spec-051]: ../SPECS/spec-051-finalizer_sidecar_dry-0_0_14.md

<!-- package source -->
[filters]: ../../django_strawberry_framework/filters/
[filters-base]: ../../django_strawberry_framework/filters/base.py
[mutations]: ../../django_strawberry_framework/mutations/
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[orders]: ../../django_strawberry_framework/orders/
[orders-base]: ../../django_strawberry_framework/orders/base.py
[registry]: ../../django_strawberry_framework/registry.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py

<!-- tests -->
[tests-types]: ../../tests/types/
