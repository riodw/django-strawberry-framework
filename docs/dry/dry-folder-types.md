# DRY review: `django_strawberry_framework/types/` (folder integration)

Status: verified

## System trace

The `django_strawberry_framework/types/` subpackage implements the type-system subsystem, providing Django model introspection, `DjangoType` class declaration, GraphQL schema conversion, Relay Node interface integration, resolver synthesis, and multi-phase schema finalization ([spec-010][spec-010], [spec-011][spec-011], [spec-015][spec-015], [spec-018][spec-018], [spec-027][spec-027], [spec-028][spec-028], [spec-030][spec-030], [spec-031][spec-031], [spec-032][spec-032], [spec-033][spec-033], [spec-034][spec-034], [spec-035][spec-035], [spec-036][spec-036], [spec-037][spec-037], [spec-038][spec-038], [spec-040][spec-040], [spec-047][spec-047], [spec-051][spec-051]).

Folder components:
1. [`django_strawberry_framework/types/__init__.py`][types-init]:
   - Subpackage re-exports: [`DjangoType`][types-base], [`SyncMisuseError`][types-relay], and [`finalize_django_types`][types-finalizer].

2. [`django_strawberry_framework/types/base.py`][types-base]:
   - [`DjangoType`][types-base]: Metaclass driver and base class ([`DjangoType.__init_subclass__`][types-base], [`DjangoType.get_queryset`][types-base], [`DjangoType.has_custom_get_queryset`][types-base]).
   - Core validators & builders: [`_validate_meta`][types-base], [`_select_fields`][types-base], [`_validate_optimizer_hints`][types-base], [`_extract_optimizer_hints`][types-base], [`_validate_filesystem_path_targets`][types-base], [`_validate_relation_shapes`][types-base], [`_check_relay_node_id_override`][types-base], [`_build_annotations`][types-base], [`_validate_nullability_overrides`][types-base], [`_is_custom_get_queryset`][types-base], [`_detect_custom_get_queryset`][types-base], [`_validate_primary_setting`][types-base], [`_validate_globalid_strategy`][types-base], [`_validate_mutation_classes`][types-base], [`_validate_set_sidecar`][types-base], [`_validate_filterset_class`][types-base], [`_validate_orderset_class`][types-base], [`_validate_connection`][types-base], [`_validate_cursor_field`][types-base], [`_validate_globalid_callable`][types-base], [`_has_node_id_marker`][types-base], [`_id_annotation_is_relay_node_id`][types-base], [`_is_relay_shaped`][types-base], [`_normalize_fields_spec`][types-base], [`_normalize_sequence_spec`][types-base], [`_consumer_assigned_fields`][types-base], [`_meta_optimizer_hints`][types-base], [`_format_unknown_fields_error`][types-base], [`_interfaces_shape_error`][types-base], [`_validate_interfaces`][types-base], [`_ValidatedMeta`][types-base], [`_selected_meta_targets`][types-base], [`_validate_nullability_override_targets`][types-base], and [`_validate_relation_shape_targets`][types-base].
   - Constants & sentinels: [`DEFERRED_META_KEYS`][types-base], [`ALLOWED_META_KEYS`][types-base], [`RELATION_SHAPE_VALUES`][types-base], [`DEFAULT_RELATION_SHAPE`][types-base], [`_RELAY_NODE_GATE_LEAD`][types-base], [`_RELAY_NODE_GATE_INHERIT_TAIL`][types-base], [`_GLOBALID_CALLABLE_PARAMS`][types-base], [`_NODEID_STRING_RE`][types-base], [`_INTERFACES_SHAPE_ERROR_LEAD_IN`][types-base], [`_RELAY_NON_INTERFACE_REMEDIATION`][types-base], [`_RELAY_CONNECTION_HELPER_DESCRIPTION`][types-base], [`_RELAY_NON_INTERFACE_HELPERS`][types-base], [`DEFAULT_PRIMARY_SETTING`][types-base], [`DEFAULT_GLOBALID_STRATEGY`][types-base], [`STRING_GLOBALID_STRATEGIES`][types-base], [`ALL_GLOBALID_STRATEGIES`][types-base], [`MUTATION_BINDING_ATTRIBUTES`][types-base], and [`_UNSET`][types-base].

3. [`django_strawberry_framework/types/converters.py`][types-converters]:
   - Mappings & constants: [`SCALAR_MAP`][types-converters], [`FIELD_OUTPUT_TYPE_MAP`][types-converters], [`FILESYSTEM_PATH_OUTPUT_TYPE_MAP`][types-converters], [`_NON_IDENT`][types-converters], [`_GRAPHQL_RESERVED_ENUM_VALUES`][types-converters], [`_ARRAY_FIELD_CLS`][types-converters], and [`_HSTORE_FIELD_CLS`][types-converters].
   - Helpers: [`_sanitize_member_name`][types-converters], [`_safe_file_attr`][types-converters], [`_file_storage_error`][types-converters], [`_safe_text`][types-converters], [`_field_has_choices`][types-converters], [`scalar_for_field`][types-converters], and [`_is_enum_reserved_member`][types-converters].
   - File & Image types: [`_FileSystemPathFields`][types-converters] ([`_FileSystemPathFields.path`][types-converters]), [`DjangoFileType`][types-converters] ([`DjangoFileType.name`][types-converters], [`DjangoFileType.size`][types-converters], [`DjangoFileType.url`][types-converters], [`DjangoFileType.path`][types-converters]), [`DjangoImageType`][types-converters] ([`DjangoImageType.width`][types-converters], [`DjangoImageType.height`][types-converters]), [`DjangoFilePathType`][types-converters] ([`DjangoFilePathType.name`][types-converters], [`DjangoFilePathType.path`][types-converters]), and [`DjangoImagePathType`][types-converters] ([`DjangoImagePathType.name`][types-converters], [`DjangoImagePathType.path`][types-converters]).
   - Conversion entry points: [`build_enum_from_choices`][types-converters], [`convert_choices_to_enum`][types-converters], [`convert_scalar`][types-converters], [`_field_output_type_for`][types-converters], [`convert_field_output`][types-converters], and [`resolved_relation_annotation`][types-converters].

4. [`django_strawberry_framework/types/definition.py`][types-definition]:
   - Constants & helpers: [`_GRAPHQL_NAME_RE`][types-definition], [`_normalize_pk_name`][types-definition], [`_resolves_id_off_pk`][types-definition], and [`_class_has_custom_id_resolver`][types-definition].
   - Dataclass: [`DjangoTypeDefinition`][types-definition] ([`DjangoTypeDefinition.graphql_type_name`][types-definition], [`DjangoTypeDefinition.related_target_for`][types-definition], [`DjangoTypeDefinition.has_custom_id_resolver_for`][types-definition], [`DjangoTypeDefinition.clear_resolver_target_cache`][types-definition]).
   - ID resolver helpers: [`origin_has_custom_id_resolver`][types-definition] and [`_is_framework_relay_id_resolver`][types-definition].

5. [`django_strawberry_framework/types/finalizer.py`][types-finalizer]:
   - Diagnostic formatters: [`_safe_qualified_class_name`][types-finalizer], [`_safe_field_label`][types-finalizer], [`_safe_str`][types-finalizer], and [`_annotation_names`][types-finalizer].
   - Ambiguity & field surface audits: [`_format_unresolved_targets_error`][types-finalizer], [`_format_ambiguity_error`][types-finalizer], [`_audit_primary_ambiguity`][types-finalizer], [`_field_surface_names`][types-finalizer], and [`_audit_field_surface`][types-finalizer].
   - Model label routing audits: [`_format_model_label_routing_error`][types-finalizer], [`_audit_model_label_routing`][types-finalizer], [`_first_model_label_emitter`][types-finalizer], and [`_warn_model_label_secondary_collapse`][types-finalizer].
   - Connection synthesis: [`_SYNTHESIZED_RELATION_CONNECTION_MARKER`][types-finalizer], [`_MISSING_CLASS_MEMBER`][types-finalizer], [`_suppress_relation_list_form`][types-finalizer], [`_record_relation_connection`][types-finalizer], [`_register_relation_connection_teardown`][types-finalizer], and [`_synthesize_relation_connections`][types-finalizer].
   - Orchestrator: [`finalize_django_types`][types-finalizer].
   - Sidecar binding: [`_bind_set_owner_common`][types-finalizer], [`_bind_filterset_owner`][types-finalizer], [`_check_filterset_owner_axes`][types-finalizer], [`_check_filterset_owner_get_queryset_safety`][types-finalizer], [`_check_filterset_owner_pk_identity`][types-finalizer], [`_format_owner_target_mismatch_error`][types-finalizer], [`_format_owner_pk_mismatch_error`][types-finalizer], [`_format_owner_get_queryset_mismatch_error`][types-finalizer], [`_format_owner_set_model_mismatch_error`][types-finalizer], [`_format_owner_model_mismatch_error`][types-finalizer], [`_format_orphan_sets_error`][types-finalizer], [`_format_unregistered_related_target_error`][types-finalizer], [`_bind_orderset_owner`][types-finalizer], and [`_format_owner_orderset_model_mismatch_error`][types-finalizer].
   - Dataclass spec: [`_SidecarBindingSpec`][types-finalizer] ([`_SidecarBindingSpec.definition_attr`][types-finalizer], [`_SidecarBindingSpec.expand_label_noun`][types-finalizer], [`_SidecarBindingSpec.related_noun`][types-finalizer], [`_SidecarBindingSpec.bind_owner`][types-finalizer], [`_SidecarBindingSpec.helper_ledger`][types-finalizer], [`_SidecarBindingSpec.factory_cls`][types-finalizer], [`_SidecarBindingSpec.materialize`][types-finalizer], [`_SidecarBindingSpec.format_orphans`][types-finalizer], [`_SidecarBindingSpec.expand`][types-finalizer], [`_SidecarBindingSpec.post_expand_audit`][types-finalizer]).
   - Expansion and subpass audits: [`_expand_filterset`][types-finalizer], [`_expand_orderset`][types-finalizer], [`_audit_unregistered_related_filter_targets`][types-finalizer], [`_bind_sidecar_sets`][types-finalizer], [`_bind_ordersets`][types-finalizer], [`_audit_globalid_filter_strategies`][types-finalizer], [`_format_globalid_encode_only_filter_error`][types-finalizer], [`_audit_filterset_subpass_2_5`][types-finalizer], and [`_bind_filtersets`][types-finalizer].

6. [`django_strawberry_framework/types/relations.py`][types-relations]:
   - Scaffolding: [`_hash_component`][types-relations], [`PendingRelation`][types-relations] ([`PendingRelation.source_type`][types-relations], [`PendingRelation.source_model`][types-relations], [`PendingRelation.field_name`][types-relations], [`PendingRelation.django_field`][types-relations], [`PendingRelation.related_model`][types-relations], [`PendingRelation.relation_kind`][types-relations], [`PendingRelation.nullable`][types-relations], [`PendingRelation.__hash__`][types-relations]), [`_PendingRelationAnnotationMeta`][types-relations] ([`_PendingRelationAnnotationMeta.__repr__`][types-relations]), and [`PendingRelationAnnotation`][types-relations].

7. [`django_strawberry_framework/types/relay.py`][types-relay]:
   - Exception & identification: [`SyncMisuseError`][types-relay], [`implements_relay_node`][types-relay], [`_NODE_TYPE_HINT_ATTR`][types-relay], [`install_is_type_of`][types-relay], [`apply_interfaces`][types-relay], and [`_check_composite_pk_for_relay_node`][types-relay].
   - ID resolution & default resolvers: [`_RELAY_ID_ATTR_SLOT`][types-relay], [`_stamp_relay_id_attr`][types-relay], [`_resolve_id_attr_default`][types-relay], [`_resolve_id_default`][types-relay], [`_coerce_node_id`][types-relay], [`_coerce_node_ids`][types-relay], [`_apply_node_filter`][types-relay], [`_order_nodes`][types-relay], [`_resolve_node_default`][types-relay], [`_resolve_node_async`][types-relay], [`_resolve_nodes_default`][types-relay], [`_resolve_nodes_async`][types-relay], [`_RELAY_RESOLVER_DEFAULTS`][types-relay], and [`install_relay_node_resolvers`][types-relay].
   - GlobalID strategy codecs: [`_validated_globalid_setting`][types-relay], [`_resolve_globalid_strategy`][types-relay], [`MODEL_LABEL_STRATEGIES`][types-relay], [`TYPE_NAME_STRATEGIES`][types-relay], [`_emits_model_label`][types-relay], [`_accepts_model_label_decode`][types-relay], [`_accepts_type_name_decode`][types-relay], [`encode_typename`][types-relay], [`_FRAMEWORK_CLOSURE_MARKER`][types-relay], [`_inherits_framework_closure`][types-relay], [`_consumer_overrode_resolve_typename`][types-relay], [`install_globalid_typename_resolver`][types-relay], [`_install_typename_closure`][types-relay], and [`decode_global_id`][types-relay].

8. [`django_strawberry_framework/types/resolvers.py`][types-resolvers]:
   - Optimization & strictness probes: [`_resolver_logger`][types-resolvers], [`_EMPTY_ELISIONS`][types-resolvers], [`_PLAN_UNREAD`][types-resolvers], [`_FK_ELISION_UNSAFE`][types-resolvers], [`_fk_attname_is_deferred`][types-resolvers], [`_build_fk_id_stub`][types-resolvers], [`_will_lazy_load_single`][types-resolvers], [`_will_lazy_load_many`][types-resolvers], [`_strictness_for`][types-resolvers], [`_relation_is_planned`][types-resolvers], and [`_check_n1`][types-resolvers].
   - Resolver factories & attachment: [`_name_resolver`][types-resolvers], [`_field_meta_for_resolver`][types-resolvers], [`_custom_visibility_type`][types-resolvers], [`_visible_related_object`][types-resolvers], [`_visible_many_rows`][types-resolvers], [`_optimizer_scoped_relation`][types-resolvers], [`_make_relation_resolver`][types-resolvers], [`_attach_relation_resolvers`][types-resolvers], [`_make_file_resolver`][types-resolvers], and [`_attach_file_resolvers`][types-resolvers].

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/types/ --include-constants`):
- Parsed 8 target files, 6227 lines.
- Complete inventory across all definitions / constants across the subpackage.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   The `types/` subpackage organizes responsibilities into strict one-way layers:
   - Base type collection (`types/base.py`) -> Definition encapsulation (`types/definition.py`) -> Conversion & Codecs (`types/converters.py`, `types/relay.py`) -> Scaffolding (`types/relations.py`) -> Resolver generation (`types/resolvers.py`) -> Finalization orchestrator (`types/finalizer.py`).
   - Sidecar binding unification (`types/finalizer.py`) unifies `FilterSet` and `OrderSet` multi-subpass drivers.
   - GlobalID strategy sets in `types/relay.py` serve codec, filter, and finalization audits without duplicate definitions.

2. **Sync and async twins:**
   Class collection and schema finalization operate synchronously at startup; runtime node and relation resolvers provide unified query-shaping logic with dynamic async branching via `in_async_context()`.

3. **Derived rather than repeated knowledge:**
   Model introspection is executed once per field/relation and stored on `DjangoTypeDefinition`. Resolver accessor names and output types are derived dynamically.

4. **Inverse and round-trip pairs:**
   `PendingRelationAnnotation` is rewritten by `resolved_relation_annotation`; `_register_relation_connection_teardown` restores pre-synthesis attributes on registry clear; `encode_typename` and `decode_global_id` form an exact GlobalID codec pair.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: `django_strawberry_framework/types/`, `django_strawberry_framework/filters/`, `django_strawberry_framework/orders/`, `django_strawberry_framework/mutations/`, `django_strawberry_framework/optimizer/`, `django_strawberry_framework/registry.py`;
   - Specifications: [spec-010][spec-010], [spec-011][spec-011], [spec-015][spec-015], [spec-018][spec-018], [spec-027][spec-027], [spec-028][spec-028], [spec-030][spec-030], [spec-031][spec-031], [spec-032][spec-032], [spec-033][spec-033], [spec-034][spec-034], [spec-035][spec-035], [spec-036][spec-036], [spec-037][spec-037], [spec-038][spec-038], [spec-040][spec-040], [spec-047][spec-047], [spec-051][spec-051];
   - Test suites: `tests/types/`;
   - Documentation: [README][readme], [GLOSSARY][glossary], [TREE][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new public re-export to `types/__init__.py`):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/__init__.py`][types-init].
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying the Phase-2.5 sidecar binding order across the subpackage):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/finalizer.py`][types-finalizer].
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Circular imports between `types/base.py` and sibling modules:**
   - Disproved. Dependencies flow cleanly through `definition.py`, `converters.py`, and `resolvers.py` without circular top-level imports.
2. **Scattering schema finalization logic across individual modules:**
   - Disproved per [spec-034][spec-034]. Centralized in `types/finalizer.py` ensuring single-sited orchestration of the 4-phase build gate.

## Opportunities

None — `django_strawberry_framework/types/` subpackage is fully consolidated at root owners.

## Judgment

Verified. `types/` folder integration exhibits zero duplicate code and complete architectural alignment across type declaration, field conversion, Relay integration, resolver generation, and schema finalization. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/types/ --review docs/dry/dry-folder-types.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of the `django_strawberry_framework/types/` subpackage and Worker 1's DRY review.

1. **Subsystem Boundaries & Integration:**
   - Confirmed module boundaries between base type collection, conversion, definition, finalization, relations, relay, and resolvers are strictly maintained without circular imports or duplicated contracts.
   - Confirmed sidecar integration and optimizer context variables interface cleanly with sibling subpackages.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/types/ --review docs/dry/dry-folder-types.md --include-constants`. 100% coverage across all 8 files and all definitions / constants.

Confirmed: `django_strawberry_framework/types/` subpackage integration satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-010]: ../SPECS/spec-010-relational_fields-0_0_4.md
[spec-011]: ../SPECS/spec-011-optimizer_core-0_0_4.md
[spec-015]: ../SPECS/spec-015-interfaces_relay-0_0_5.md
[spec-018]: ../SPECS/spec-018-primary_ambiguity-0_0_6.md
[spec-027]: ../SPECS/spec-027-filters_first_class-0_0_8.md
[spec-028]: ../SPECS/spec-028-orders_first_class-0_0_8.md
[spec-030]: ../SPECS/spec-030-connection_sidecar-0_0_9.md
[spec-031]: ../SPECS/spec-031-globalid_strategies-0_0_9.md
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md
[spec-033]: ../SPECS/spec-033-relation_connections-0_0_10.md
[spec-034]: ../SPECS/spec-034-schema_finalization_refactor-0_0_10.md
[spec-035]: ../SPECS/spec-035-optimizer_hardened_diffing-0_0_10.md
[spec-036]: ../SPECS/spec-036-mutations-0_0_11.md
[spec-037]: ../SPECS/spec-037-file_and_image_fields-0_0_11.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_11.md
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_12.md
[spec-047]: ../SPECS/spec-047-connection_by_default-0_0_14.md
[spec-051]: ../SPECS/spec-051-finalizer_sidecar_dry-0_0_14.md

<!-- package source -->
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-init]: ../../django_strawberry_framework/types/__init__.py
[types-relations]: ../../django_strawberry_framework/types/relations.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py
