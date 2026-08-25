# DRY review: `django_strawberry_framework/types/base.py`

Status: verified

## System trace

`django_strawberry_framework/types/base.py` implements `DjangoType`, the metaclass-driven adapter bridging Django models to Strawberry GraphQL types ([spec-011][spec-011], [spec-018][spec-018], [spec-029][spec-029], [spec-030][spec-030], [spec-031][spec-031], [spec-032][spec-032], [spec-034][spec-034], [spec-048][spec-048]).

It owns the following architectural responsibilities:

1. **Meta Vocabulary & Error Constants:**
   - [`DEFERRED_META_KEYS`][types-base] (`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`): Reserved keys for unreleased features.
   - [`ALLOWED_META_KEYS`][types-base] (`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`): Permitted declarative options in nested `Meta`.
   - Relation shapes: [`RELATION_SHAPE_VALUES`][types-base] and [`DEFAULT_RELATION_SHAPE`][types-base].
   - Relay-Node gating strings: [`_RELAY_NODE_GATE_LEAD`][types-base] and [`_RELAY_NODE_GATE_INHERIT_TAIL`][types-base].
   - GlobalID strategies: [`STRING_GLOBALID_STRATEGIES`][types-base] and [`DEFAULT_GLOBALID_STRATEGY`][types-base].
   - Interface error formatting: [`_INTERFACES_SHAPE_ERROR_LEAD_IN`][types-base], [`_interfaces_shape_error`][types-base], [`_RELAY_NON_INTERFACE_REMEDIATION`][types-base], [`_RELAY_CONNECTION_HELPER_DESCRIPTION`][types-base], and [`_RELAY_NON_INTERFACE_HELPERS`][types-base].
   - NodeID detection: [`_NODEID_STRING_RE`][types-base], [`_has_node_id_marker`][types-base], [`_id_annotation_is_relay_node_id`][types-base], and [`_is_relay_shaped`][types-base].

2. **Sidecar & Option Validators:**
   - [`_validate_set_sidecar`][types-base] (`django_strawberry_framework/types/base.py::_validate_set_sidecar`): Shared type check for filter/order set sidecars.
   - [`_validate_filterset_class`][types-base] (`django_strawberry_framework/types/base.py::_validate_filterset_class`) and [`_validate_orderset_class`][types-base] (`django_strawberry_framework/types/base.py::_validate_orderset_class`).
   - [`_validate_connection`][types-base] (`django_strawberry_framework/types/base.py::_validate_connection`): Validates connection pagination configuration.
   - [`_validate_cursor_field`][types-base] (`django_strawberry_framework/types/base.py::_validate_cursor_field`): Stage 1 keyset cursor validation.
   - [`_validate_relation_shapes`][types-base] (`django_strawberry_framework/types/base.py::_validate_relation_shapes`): Stage 1 relation shape dictionary validation.
   - GlobalID validators: [`_GLOBALID_CALLABLE_PARAMS`][types-base], [`_validate_globalid_strategy`][types-base], and [`_validate_globalid_callable`][types-base].
   - [`_validate_interfaces`][types-base] (`django_strawberry_framework/types/base.py::_validate_interfaces`): Validates Strawberry interface classes and rejects non-interface helpers.

3. **DjangoType Base Class & Queryset Hook:**
   - [`DjangoType`][types-base] (`django_strawberry_framework/types/base.py::DjangoType`): Base class managing [`DjangoType._is_default_get_queryset`][types-base], [`DjangoType.__init_subclass__`][types-base], identity hook [`DjangoType.get_queryset`][types-base], and fast introspection [`DjangoType.has_custom_get_queryset`][types-base].
   - [`_detect_custom_get_queryset`][types-base] (`django_strawberry_framework/types/base.py::_detect_custom_get_queryset`): MRO scanner for custom queryset overrides.

4. **Normalization & Field Surface Analysis:**
   - [`_normalize_fields_spec`][types-base] (`django_strawberry_framework/types/base.py::_normalize_fields_spec`): Normalizes `Meta.fields`.
   - [`_normalize_sequence_spec`][types-base] (`django_strawberry_framework/types/base.py::_normalize_sequence_spec`): Shared normalizer for sequence/set Meta keys.
   - [`_consumer_assigned_fields`][types-base] (`django_strawberry_framework/types/base.py::_consumer_assigned_fields`): Partitions consumer-assigned `strawberry.field` attributes.
   - [`_meta_optimizer_hints`][types-base] (`django_strawberry_framework/types/base.py::_meta_optimizer_hints`): Validates `Meta.optimizer_hints` mapping shape.
   - [`_format_unknown_fields_error`][types-base] (`django_strawberry_framework/types/base.py::_format_unknown_fields_error`): Canonical error formatter for unknown field names.
   - [`_ValidatedMeta`][types-base] (`django_strawberry_framework/types/base.py::_ValidatedMeta`): Validated metadata snapshot containing:
     - [`_ValidatedMeta.interfaces`][types-base]
     - [`_ValidatedMeta.name`][types-base]
     - [`_ValidatedMeta.primary`][types-base]
     - [`_ValidatedMeta.optimizer_hints`][types-base]
     - [`_ValidatedMeta.fields_spec`][types-base]
     - [`_ValidatedMeta.exclude_spec`][types-base]
     - [`_ValidatedMeta.filterset_class`][types-base]
     - [`_ValidatedMeta.orderset_class`][types-base]
     - [`_ValidatedMeta.connection`][types-base]
     - [`_ValidatedMeta.cursor_field`][types-base]
     - [`_ValidatedMeta.globalid_strategy`][types-base]
     - [`_ValidatedMeta.relation_shapes`][types-base]
     - [`_ValidatedMeta.nullable_overrides`][types-base]
     - [`_ValidatedMeta.required_overrides`][types-base]
     - [`_ValidatedMeta.filesystem_path_fields`][types-base]
   - [`_validate_meta`][types-base] (`django_strawberry_framework/types/base.py::_validate_meta`): Single-pass Meta validator returning `_ValidatedMeta`.
   - [`_validate_optimizer_hints`][types-base] (`django_strawberry_framework/types/base.py::_validate_optimizer_hints`): Verifies hint targets and types against model fields.
   - [`_selected_meta_targets`][types-base] (`django_strawberry_framework/types/base.py::_selected_meta_targets`): Shared stage-2 validator skeleton for field-targeted Meta keys.
   - [`_validate_nullability_override_targets`][types-base] (`django_strawberry_framework/types/base.py::_validate_nullability_override_targets`): Stage-2 nullability override target validation.
   - [`_validate_filesystem_path_targets`][types-base] (`django_strawberry_framework/types/base.py::_validate_filesystem_path_targets`): Stage-2 filesystem path target validation.
   - [`_validate_relation_shape_targets`][types-base] (`django_strawberry_framework/types/base.py::_validate_relation_shape_targets`): Stage-2 relation shape target validation.
   - [`_select_fields`][types-base] (`django_strawberry_framework/types/base.py::_select_fields`): Filters Django model fields.
   - [`_build_annotations`][types-base] (`django_strawberry_framework/types/base.py::_build_annotations`): Synthesizes scalar annotations via [`convert_field_output`][types-converters] and registers [`PendingRelation`][types-relations] instances.

Connected behavior examined:
- [`django_strawberry_framework/types/converters.py`][types-converters]: Output conversion and scalar conversion.
- [`django_strawberry_framework/types/definition.py`][types-definition]: `DjangoTypeDefinition` dataclass.
- [`django_strawberry_framework/types/relations.py`][types-relations]: `PendingRelation` and `PendingRelationAnnotation`.
- [`django_strawberry_framework/types/relay.py`][types-relay]: Relay node resolution and type installation.
- [`django_strawberry_framework/registry.py`][registry]: Global model and definition registry.
- [`tests/types/`][tests-types]: Comprehensive test suite covering field selection, overrides, Meta validation, and inheritance.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/types/base.py --include-constants`):
- Parsed 1 target file, 1,951 lines.
- Complete inventory across all 53 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `types/base.py` centralizes all model-to-type declarative semantics. Meta option validation shares `_normalize_sequence_spec` and `_selected_meta_targets` across nullability overrides, required overrides, filesystem path fields, and relation shapes. Error formatting is unified via `_format_unknown_fields_error`. Relay-Node gate texts are single-sourced via `_RELAY_NODE_GATE_LEAD` and `_RELAY_NODE_GATE_INHERIT_TAIL`.

2. **Sync and async twins:**
   `_validate_globalid_callable` checks sync-ness using `is_async_callable`, ensuring async coroutine functions cannot be registered as sync GlobalID encoders.

3. **Derived rather than repeated knowledge:**
   Selected fields, consumer overrides, and relation metadata derive from the Django model's `_meta.get_fields()` and `DjangoType` annotations. `has_custom_get_queryset` derives from class MRO inspection and is cached on the class and `DjangoTypeDefinition`.

4. **Inverse and round-trip pairs:**
   `nullable_overrides` and `required_overrides` form a mutually exclusive pair verified disjoint at validation time.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/types/base.py`][types-base], [`django_strawberry_framework/types/converters.py`][types-converters], [`django_strawberry_framework/types/definition.py`][types-definition], [`django_strawberry_framework/types/finalizer.py`][types-finalizer];
   - Specifications: [`docs/SPECS/spec-011-interfaces-0_0_4.md`][spec-011], [`docs/SPECS/spec-018-reverse_relation_order-0_0_5.md`][spec-018], [`docs/SPECS/spec-029-nullability_overrides-0_0_8.md`][spec-029], [`docs/SPECS/spec-030-connection_sidecar-0_0_9.md`][spec-030], [`docs/SPECS/spec-031-globalid_strategies-0_0_9.md`][spec-031], [`docs/SPECS/spec-032-full_relay-0_0_9.md`][spec-032], [`docs/SPECS/spec-034-schema_finalization_refactor-0_0_10.md`][spec-034], [`docs/SPECS/spec-048-filesystem_path_fields-0_0_14.md`][spec-048];
   - Test suites: [`tests/types/`][tests-types];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new recognized `Meta` configuration key):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/base.py`][types-base] ([`ALLOWED_META_KEYS`][types-base]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying error formatting for unknown Meta field targets):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/base.py`][types-base] ([`_format_unknown_fields_error`][types-base]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Modifying GlobalID string strategy vocabulary):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/base.py`][types-base] ([`STRING_GLOBALID_STRATEGIES`][types-base]).
  - *Propagation count:* 0 in other files.

### Rejected candidates

1. **Inlining sequence normalization across each Meta validator:**
   - Disproved per [spec-029][spec-029] / [spec-048][spec-048]. Shared `_normalize_sequence_spec` guarantees uniform rejection messages and types across set-valued Meta keys.
2. **Duplicating model-field target validation logic across override keys:**
   - Disproved per [spec-029][spec-029] / [spec-032][spec-032]. Factoring into `_selected_meta_targets` ensures identical unknown-vs-excluded handling.

## Opportunities

None — `django_strawberry_framework/types/base.py` is fully consolidated at root owners.

## Judgment

Verified. `types/base.py` exhibits zero duplicate code and complete policy consolidation across Meta options, field selection, and type synthesis. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/types/base.py --review docs/dry/dry-file-types__base.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/types/base.py`][types-base] and Worker 1's DRY review.

1. **Declarative Metaclass Pipeline & Shared Validation Skeleton:**
   - Confirmed `_ValidatedMeta` and `_selected_meta_targets` eliminate redundant Meta validation passes.
   - Confirmed error lead constants and Relay Node gating predicates are single-sourced.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/types/base.py --review docs/dry/dry-file-types__base.md --include-constants`. 100% coverage across all 53 definitions / constants.

Confirmed: `django_strawberry_framework/types/base.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-011]: ../SPECS/spec-011-interfaces-0_0_4.md
[spec-018]: ../SPECS/spec-018-reverse_relation_order-0_0_5.md
[spec-029]: ../SPECS/spec-029-nullability_overrides-0_0_8.md
[spec-030]: ../SPECS/spec-030-connection_sidecar-0_0_9.md
[spec-031]: ../SPECS/spec-031-globalid_strategies-0_0_9.md
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md
[spec-034]: ../SPECS/spec-034-schema_finalization_refactor-0_0_10.md
[spec-048]: ../SPECS/spec-048-filesystem_path_fields-0_0_14.md

<!-- package source -->
[registry]: ../../django_strawberry_framework/registry.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-relations]: ../../django_strawberry_framework/types/relations.py
[types-relay]: ../../django_strawberry_framework/types/relay.py

<!-- tests -->
[tests-types]: ../../tests/types/
