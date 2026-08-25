# DRY review: `django_strawberry_framework/mutations/sets.py`

Status: verified

## System trace

`django_strawberry_framework/mutations/sets.py` implements the foundational write-side declarative base class, `Meta` validation, mutation declaration registry, input class materialization, resolver seam synthesis, and phase-2.5 schema binding for GraphQL mutations ([spec-036][spec-036] Decisions 3, 5, 6, 11, 12, 13, 14, 15; [spec-038][spec-038] Decisions 6, 7, 8, 13; [spec-039][spec-039] Decisions 6, 7, 10, 11). It serves as the primary root owner for write-mutation abstractions shared across all write flavors (model mutations, form mutations, and DRF serializer mutations).

1. **Declarative Base Architecture and Metaclass Lifecycle ([spec-036][spec-036] Decisions 3, 5; [spec-038][spec-038] Decision 13):**
   - [`DjangoMutation`][mutations-sets]: Consumer-facing write base class. A concrete subclass declares a nested `class Meta` (`model`, `operation`, and optional `input_class`, `partial_input_class`, `fields`, `exclude`, `permission_classes`, `select_for_update`).
   - [`DjangoMutationMetaclass`][mutations-sets]: Metaclass minted via [`make_meta_validating_metaclass`][mutations-sets] over [`register_mutation`][mutations-sets]. At class creation, it skips abstract bases lacking `Meta`, validates concrete subclass `Meta` via [`DjangoMutation._validate_meta`][mutations-sets], stashes the resulting [`_ValidatedMutationMeta`][mutations-sets] snapshot on `_mutation_meta`, and registers the concrete class into the declaration registry.
   - [`make_meta_validating_metaclass`][mutations-sets]: Factory building validation-and-registration metaclasses with pinned `__name__`, `__qualname__`, and `__module__`, shared with [`DjangoFormMutationMetaclass`][forms-sets].
   - [`DeclarationRegistry`][mutations-sets] & [`make_declaration_registry`][mutations-sets]: Factory producing a named bundle of `(register, clear, iter_, store)` callables over an isolated list. Implements idempotent registration, post-finalization lockout ([spec-036][spec-036] Edge cases), and clear hooks. Instantiated as `_mutation_declaration_registry` (exporting [`register_mutation`][mutations-sets], [`clear_mutation_registry`][mutations-sets], [`iter_mutations`][mutations-sets], and backing list `_mutation_registry`), with `clear_mutation_registry` registered with [`register_subsystem_clear`][registry].
   - [`_ValidatedMutationMeta`][mutations-sets] (and its [`_ValidatedMutationMeta.__init__`][mutations-sets]): Slot-based snapshot record storing validated `Meta` configuration (`model`, `operation`, `input_class`, `partial_input_class`, `fields`, `exclude`, `permission_classes`, `form_class`, `serializer_class`, `optional_fields`, `schema_fingerprint`, `injected_fields`, `select_for_update`, `nested_fields`).

2. **Shared Meta Validation Primitives and Typo Guards ([spec-036][spec-036] Decisions 5, 12; [spec-038][spec-038] Decisions 6, 10; [spec-039][spec-039] Decision 6):**
   - [`COMMON_WRITE_META_KEYS`][mutations-sets]: Frozenset of common Meta keys accepted by every write flavor (`fields`, `exclude`, `permission_classes`).
   - [`MODEL_BACKED_WRITE_META_KEYS`][mutations-sets]: Frozenset of common model-backed write Meta keys (`COMMON_WRITE_META_KEYS` | `{"operation", "select_for_update"}`).
   - [`_ALLOWED_MUTATION_META_KEYS`][mutations-sets]: Allowed keys frozenset for `DjangoMutation.Meta` (`model`, `operation`, `input_class`, `partial_input_class`, `fields`, `exclude`, `permission_classes`, `select_for_update`).
   - [`NON_DELETE_OPERATION_INPUT_KIND`][mutations-sets]: Mapping `{"create": CREATE, "update": PARTIAL}` defining input generator kinds per non-delete operation.
   - [`_OPERATION_INPUT_OVERRIDE_ATTR`][mutations-sets]: Mapping `{"create": "input_class", "update": "partial_input_class"}` for consumer input overrides.
   - [`NON_DELETE_WRITE_OPERATIONS`][mutations-sets]: Frozenset derived from `NON_DELETE_OPERATION_INPUT_KIND.keys()`.
   - [`_VALID_OPERATIONS`][mutations-sets]: Union of `NON_DELETE_WRITE_OPERATIONS` and `frozenset({"delete"})`.
   - [`non_delete_operation_error`][mutations-sets] & [`require_non_delete_operation`][mutations-sets]: Shared operation validation and error formatting for create/update-only write flavors ([`forms/sets.py`][forms-sets] and [`rest_framework/sets.py`][rest-framework-sets]).
   - [`reject_unknown_meta_keys`][mutations-sets]: Shared typo guard scanning own-keys of `Meta` against an allowed set without MRO traversal.
   - [`normalize_meta_field_selection`][mutations-sets]: Normalizes `Meta.fields` and `Meta.exclude` sequences via [`normalize_field_name_sequence`][utils-inputs].
   - [`require_backing_class`][mutations-sets] & [`require_subclass`][mutations-sets]: Shared presence and subclass type gates for form and serializer backing classes.
   - [`require_model_class`][mutations-sets]: Shared type gate verifying that a resolved model is a Django `models.Model` subclass.
   - [`resolve_meta_model`][mutations-sets] & [`resolve_backed_model_or_raise`][mutations-sets]: Shared 3-getattr resolution chain extracting `Meta.model` from backing form/serializer classes.
   - [`validate_select_for_update`][mutations-sets]: Shared validator for boolean `Meta.select_for_update` (default `True`).
   - [`_validate_permission_classes`][mutations-sets] & [`model_backed_permission_and_lock`][mutations-sets]: Validates and normalizes `Meta.permission_classes` (defaulting to [`DjangoModelPermission`][mutations-permissions]) and pairs it with `select_for_update` validation.
   - [`_validate_input_class`][mutations-sets] & [`_expected_input_attr_names`][mutations-sets]: Validates that consumer `input_class` / `partial_input_class` overrides are `@strawberry.input` types and do not diverge from expected python attribute names derived via [`editable_input_fields`][mutations-inputs] and [`relation_input_annotation`][mutations-inputs].
   - [`DjangoMutation._resolve_model`][mutations-sets]: Overridable classmethod hook extracting `getattr(meta, "model", None)`.
   - [`DjangoMutation._validate_meta`][mutations-sets]: Class validation matrix enforcing allowed keys, resolvable Django model, valid operation, mutually exclusive `fields`/`exclude`, non-empty editable column narrowing, valid custom input classes, permissions, and locking.

3. **Input Construction, Shape Caching, and Override Merging ([spec-036][spec-036] Decisions 6, 10, 14; [spec-038][spec-038] Decisions 7, 8):**
   - [`_shape_build_cache`][mutations-sets] & `clear_mutation_shape_build_cache`: Created via [`make_shape_build_cache`][utils-inputs] and registered with [`register_subsystem_clear`][registry] for caching built input types across mutation declarations within a finalization pass.
   - [`_hook_overridden`][mutations-sets]: Shared identity check detecting method overrides on subclasses relative to base classes.
   - [`cached_build_input`][mutations-sets]: Guard-before-cache-lookup helper running per-declaration guards prior to cached shape retrieval.
   - [`build_and_stash_input`][mutations-sets]: Shared input materialization helper stashing reverse-map field specifications on `cls._input_field_specs`.
   - [`_materialize_input_for`][mutations-sets]: Builds and caches `@strawberry.input` classes for create/update operations via [`get_or_store_shape_build`][utils-inputs] and [`build_mutation_input`][mutations-inputs], returning `None` for delete.
   - [`_materialize_merged_input`][mutations-sets]: Merges consumer-provided `input_class` overrides with generated remainder inputs using class inheritance (`strawberry.input(type(name, (consumer, remainder), {}))`), preserving consumer field metadata while filling omitted fields.
   - [`_validate_relation_override_types`][mutations-sets], [`_annotation_core_is_global_id`][mutations-sets], & [`_strawberry_field_shape`][mutations-sets]: Enforces relation override type-locking, verifying that consumer relation overrides targeting Relay-Node primary models maintain `relay.GlobalID` core types and matching list depths (peeling Strawberry wrapper types via [`unwrap_return_type`][utils-typing] and `_strawberry_field_shape`), preventing relation visibility bypasses ([spec-036][spec-036] Decision 10).
   - [`DjangoMutation.build_input`][mutations-sets]: Phase-2.5 input materialization hook delegating to `_materialize_input_for` and stashing reverse-map `_input_field_specs` and `_model_fields_by_attr` via [`mutation_input_field_specs`][mutations-inputs].
   - [`DjangoMutation.input_type_name`][mutations-sets]: Input naming hook returning canonical GraphQL input type names from [`mutation_input_shape`][mutations-inputs].

4. **Construction Kwargs, Resolver Seams, and Permissions ([spec-036][spec-036] Decisions 8, 15; [spec-038][spec-038] Decision 8; [spec-039][spec-039] Decision 8):**
   - [`construction_kwargs`][mutations-sets]: Shared helper packaging constructor kwargs with `instance` included only when non-`None`.
   - [`resolver_seams`][mutations-sets]: Classmethod factory generating `(resolve_sync, resolve_async)` pairs with function-local lazy imports of resolver modules (via [`import_attr`][utils-imports]), eliminating load-time circular dependencies. Configurable with `with_id=False` for model-less flavors.
   - `DjangoMutation.resolve_sync` and `DjangoMutation.resolve_async`: Minted via `resolver_seams("django_strawberry_framework.mutations.resolvers", "resolve_mutation_sync", "resolve_mutation_async")`.
   - [`DjangoMutation.check_permission`][mutations-sets]: Imperative permission check hook delegating to [`run_permission_classes`][mutations-permissions].

5. **Phase-2.5 Finalization and Binding Pipeline ([spec-036][spec-036] Decisions 11, 12, 13; [spec-038][spec-038] Decision 13):**
   - [`_resolve_primary_type`][mutations-sets]: Resolves the model's primary [`DjangoType`][types-base] from [`registry`][registry], raising targeted `ConfigurationError` diagnostics distinguishing between un-registered models and ambiguous multi-type registrations.
   - [`bind_mutation_outputs`][mutations-sets]: Builds the `<Name>Payload` class via [`build_payload_type`][mutations-inputs] (with [`payload_object_slot`][mutations-inputs] for model-backed mutations or pinned `{ ok errors }` for model-less mutations), materializes it via [`materialize_mutation_input_class`][mutations-inputs], and stashes `_primary_type`, `_input_class`, and `_payload_type_name` on the mutation class.
   - [`bind_write_declarations`][mutations-sets]: Unified binding loop draining any write-declaration registry, clearing per-pass build caches, resolving object types, invoking `build_input`, and binding mutation outputs via `bind_mutation_outputs`.
   - [`bind_mutations`][mutations-sets]: Finalizer phase-2.5 entry point called by [`finalize_django_types`][types-finalizer] that invokes `bind_write_declarations` over `iter_mutations` with `_resolve_primary_type`.

Connected behavior examined:
- [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs]: Input and payload building, relation annotations, shape descriptor derivation, and input class materialization.
- [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]: Mutation execution pipeline, relation decoding, object lookup, instance locking, and payload construction.
- [`django_strawberry_framework/mutations/permissions.py`][mutations-permissions]: Permission class hierarchy and sync-safe execution walk `run_permission_classes`.
- [`django_strawberry_framework/mutations/fields.py`][mutations-fields]: Field factory `DjangoMutationField` synthesizing resolver signatures and payload type lazy refs from mutation class state.
- [`django_strawberry_framework/forms/sets.py`][forms-sets]: Form mutation write surface reusing shared validation, registry, and binding helpers.
- [`django_strawberry_framework/rest_framework/sets.py`][rest-framework-sets]: Serializer mutation write surface subclassing `DjangoMutation` and reusing shared validation and binding helpers.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Phase-2.5 finalizer orchestrating `bind_mutations` and `bind_form_mutations`.
- [`django_strawberry_framework/registry.py`][registry]: Declaration registry coordinator managing subsystem clears.
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Shape build cache factory `make_shape_build_cache` and sequence normalizer `normalize_field_name_sequence`.
- [`django_strawberry_framework/utils/typing.py`][utils-typing]: Return type unwrap helper `unwrap_return_type`.
- [`tests/mutations/test_sets.py`][test-mutations-sets]: Test suite verifying mutation validation, registry isolation, input merging, relation override type locks, and binding.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/mutations/sets.py --review docs/dry/dry-file-mutations__sets.md --include-constants`):
- Parsed 1 target file, 1597 lines, 46 target definitions:
  - 7 constants: [`COMMON_WRITE_META_KEYS`][mutations-sets], [`MODEL_BACKED_WRITE_META_KEYS`][mutations-sets], [`_ALLOWED_MUTATION_META_KEYS`][mutations-sets], [`NON_DELETE_OPERATION_INPUT_KIND`][mutations-sets], [`_OPERATION_INPUT_OVERRIDE_ATTR`][mutations-sets], [`NON_DELETE_WRITE_OPERATIONS`][mutations-sets], [`_VALID_OPERATIONS`][mutations-sets]
  - 3 classes: [`DeclarationRegistry`][mutations-sets], [`_ValidatedMutationMeta`][mutations-sets], [`DjangoMutation`][mutations-sets]
  - 6 class methods: [`_ValidatedMutationMeta.__init__`][mutations-sets], [`DjangoMutation._resolve_model`][mutations-sets], [`DjangoMutation._validate_meta`][mutations-sets], [`DjangoMutation.build_input`][mutations-sets], [`DjangoMutation.input_type_name`][mutations-sets], [`DjangoMutation.check_permission`][mutations-sets]
  - 30 functions: [`non_delete_operation_error`][mutations-sets], [`require_non_delete_operation`][mutations-sets], [`reject_unknown_meta_keys`][mutations-sets], [`normalize_meta_field_selection`][mutations-sets], [`_hook_overridden`][mutations-sets], [`cached_build_input`][mutations-sets], [`build_and_stash_input`][mutations-sets], [`construction_kwargs`][mutations-sets], [`require_backing_class`][mutations-sets], [`require_subclass`][mutations-sets], [`require_model_class`][mutations-sets], [`resolve_meta_model`][mutations-sets], [`resolve_backed_model_or_raise`][mutations-sets], [`resolver_seams`][mutations-sets], [`make_declaration_registry`][mutations-sets], [`make_meta_validating_metaclass`][mutations-sets], [`_validate_input_class`][mutations-sets], [`_expected_input_attr_names`][mutations-sets], [`_validate_permission_classes`][mutations-sets], [`validate_select_for_update`][mutations-sets], [`model_backed_permission_and_lock`][mutations-sets], [`_resolve_primary_type`][mutations-sets], [`_materialize_input_for`][mutations-sets], [`_materialize_merged_input`][mutations-sets], [`_validate_relation_override_types`][mutations-sets], [`_annotation_core_is_global_id`][mutations-sets], [`_strawberry_field_shape`][mutations-sets], [`bind_mutation_outputs`][mutations-sets], [`bind_write_declarations`][mutations-sets], [`bind_mutations`][mutations-sets]
- Verified reverse references across `django_strawberry_framework/mutations/__init__.py`, `django_strawberry_framework/mutations/fields.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/types/finalizer.py`, and `tests/mutations/test_sets.py`.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   - **Root Owner of Write Abstractions:** `django_strawberry_framework/mutations/sets.py` is the single source of truth for write mutation infrastructure. All three write flavors (model mutations in `mutations/sets.py`, form mutations in [`forms/sets.py`][forms-sets], serializer mutations in [`rest_framework/sets.py`][rest-framework-sets]) reuse its primitives:
     - Metaclass generation via [`make_meta_validating_metaclass`][mutations-sets];
     - Declaration registry creation via [`make_declaration_registry`][mutations-sets];
     - Typo checking via [`reject_unknown_meta_keys`][mutations-sets];
     - Subclass and model type checks via [`require_backing_class`][mutations-sets], [`require_subclass`][mutations-sets], [`require_model_class`][mutations-sets], and [`resolve_backed_model_or_raise`][mutations-sets];
     - Operation validation via [`NON_DELETE_OPERATION_INPUT_KIND`][mutations-sets], [`NON_DELETE_WRITE_OPERATIONS`][mutations-sets], [`_VALID_OPERATIONS`][mutations-sets], [`require_non_delete_operation`][mutations-sets], and [`non_delete_operation_error`][mutations-sets];
     - Field selection normalization via [`normalize_meta_field_selection`][mutations-sets];
     - Shape cache creation via [`make_shape_build_cache`][utils-inputs], input caching via [`cached_build_input`][mutations-sets], and input materialization/stashing via [`build_and_stash_input`][mutations-sets];
     - Constructor kwargs packaging via [`construction_kwargs`][mutations-sets] and override detection via [`_hook_overridden`][mutations-sets];
     - Resolver seam generation via [`resolver_seams`][mutations-sets];
     - Permission and lock validation via [`_validate_permission_classes`][mutations-sets], [`validate_select_for_update`][mutations-sets], and [`model_backed_permission_and_lock`][mutations-sets];
     - Phase-2.5 finalization loop via [`bind_write_declarations`][mutations-sets] and [`bind_mutation_outputs`][mutations-sets].
   - **Disjoint Subsystems & Namespaces:** Read-side subsystems (`types/base.py`, `filters/sets.py`, `orders/sets.py`) maintain their own disjoint `Meta` namespaces and lifecycles. Mutation `Meta` validation does not mutate or import `types/base.py::ALLOWED_META_KEYS`.
2. **Sync and async twins:**
   - Zero duplication. Both `resolve_sync` and `resolve_async` classmethod seams on [`DjangoMutation`][mutations-sets] are minted simultaneously via [`resolver_seams`][mutations-sets].
   - `resolver_seams` encapsulates function-local lazy imports of the respective resolver module (`django_strawberry_framework.mutations.resolvers.resolve_mutation_sync` and `resolve_mutation_async`), eliminating load-time import cycles.
   - `DjangoMutation.check_permission` delegates to [`run_permission_classes`][mutations-permissions], which intercepts async coroutine return values from permission classes and raises `SyncMisuseError` to prevent silent authorization bypasses in synchronous execution contexts.
3. **Derived rather than repeated knowledge:**
   - **Operation Constants:** `NON_DELETE_WRITE_OPERATIONS` and `_VALID_OPERATIONS` are derived directly from `NON_DELETE_OPERATION_INPUT_KIND.keys()`.
   - **Attribute Names for Custom Inputs:** `_expected_input_attr_names` derives expected python attribute names dynamically from `editable_input_fields` and `relation_input_annotation`.
   - **Shape Identity and Naming:** Shape cache keys and generated GraphQL input type names derive deterministically from [`mutation_input_shape`][mutations-inputs].
   - **Merged Input Inheritance:** `_materialize_merged_input` uses class inheritance (`type(shape.type_name, (consumer_input, remainder), {})`), allowing Strawberry to derive field union and precedence naturally rather than manually reconstructing field specifications.
   - **Relation Override Type Validation:** `_validate_relation_override_types` derives expected id types and list depths dynamically from `relation_input_annotation` and peels Strawberry wrappers using `_strawberry_field_shape` and `_annotation_core_is_global_id`.
4. **Inverse and round-trip pairs:**
   - **Meta Configuration <-> Input Field Narrowing:**
     - Declarations `Meta.fields` / `Meta.exclude` validated in `DjangoMutation._validate_meta` are consumed by `editable_input_fields` during class validation and input generation.
   - **Input Generation & Stashing <-> Resolver Argument Decoding:**
     - `DjangoMutation.build_input` stashes `_input_field_specs` and `_model_fields_by_attr` on the mutation class.
     - [`mutations/resolvers.py`][mutations-resolvers] consumes these stashed specs to decode GraphQL input objects into Django model field values.
   - **Declaration Registration <-> Phase-2.5 Finalization Binding:**
     - Concrete mutation classes register into `_mutation_declaration_registry` during class definition.
     - [`bind_mutations`][mutations-sets] drains the registry during schema finalization, and [`clear_mutation_registry`][mutations-sets] co-clears the registry on test reset.
   - **Shape Cache Population <-> Subsystem Clear:**
     - `_shape_build_cache` caches generated inputs during finalize and is cleared by `clear_mutation_shape_build_cache` upon `registry.clear()`.
5. **Contracts restated in another medium:**
   - The write-mutation declarative contract is codified across:
     - Production code: [`django_strawberry_framework/mutations/sets.py`][mutations-sets], [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs], [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], [`django_strawberry_framework/mutations/permissions.py`][mutations-permissions], [`django_strawberry_framework/mutations/fields.py`][mutations-fields], [`django_strawberry_framework/forms/sets.py`][forms-sets], [`django_strawberry_framework/rest_framework/sets.py`][rest-framework-sets], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/registry.py`][registry];
     - Specifications: [`docs/SPECS/spec-036-mutation_sets-0_0_11.md`][spec-036], [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038], [`docs/SPECS/spec-039-drf_serializer_mutations-0_0_13.md`][spec-039], [`docs/SPECS/spec-040-auth_mutations-0_0_13.md`][spec-040], [`docs/SPECS/spec-046-transport_security-0_0_14.md`][spec-046], [`docs/SPECS/spec-047-resource_policy-0_0_14.md`][spec-047];
     - Test suites: [`tests/mutations/test_sets.py`][test-mutations-sets], [`tests/mutations/test_inputs.py`][test-mutations-inputs], [`tests/mutations/test_resolvers.py`][test-mutations-resolvers], [`tests/mutations/test_fields.py`][test-mutations-fields], [`tests/forms/test_sets.py`][test-forms-sets], [`tests/rest_framework/test_sets.py`][test-rest-framework-sets];
     - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Modifying the declaration registry lifecycle, deduplication, or post-finalization lockout):** Change registration deduplication, post-finalization lockouts, or iteration semantics across mutation declaration registries.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::make_declaration_registry`][mutations-sets].
  - *Site count:* 1.
- **Posited change 2 (Modifying the meta-validating metaclass generation factory):** Change metaclass class construction, `Meta` extraction, or registration invocation across mutation metaclasses.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::make_meta_validating_metaclass`][mutations-sets].
  - *Site count:* 1.
- **Posited change 3 (Modifying Meta typo detection and reporting):** Alter how unknown `Meta` keys are computed and formatted across write mutation flavors.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::reject_unknown_meta_keys`][mutations-sets].
  - *Site count:* 1.
- **Posited change 4 (Modifying non-delete operation validation or diagnostic messages):** Update error text or supported operation checking for create/update-only write flavors.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::require_non_delete_operation`][mutations-sets] or [`django_strawberry_framework/mutations/sets.py::non_delete_operation_error`][mutations-sets].
  - *Site count:* 1.
- **Posited change 5 (Modifying allowed Meta keys for DjangoMutation):** Add or remove a supported configuration option on `DjangoMutation.Meta`.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/mutations/sets.py::_ALLOWED_MUTATION_META_KEYS`][mutations-sets].
  - *Site count:* 1.
- **Posited change 6 (Modifying field selection sequence normalization):** Change sequence conversion or error handling for `Meta.fields` and `Meta.exclude` across write flavors.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::normalize_meta_field_selection`][mutations-sets].
  - *Site count:* 1.
- **Posited change 7 (Modifying default constructor kwargs packaging):** Alter how `data`, `files`, and `instance` kwargs are structured for form or serializer constructors.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::construction_kwargs`][mutations-sets].
  - *Site count:* 1.
- **Posited change 8 (Modifying backing class presence or inheritance type-gates):** Update backing class presence checks or inheritance error formatting for form/serializer mutations.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::require_backing_class`][mutations-sets] or [`django_strawberry_framework/mutations/sets.py::require_subclass`][mutations-sets].
  - *Site count:* 1.
- **Posited change 9 (Modifying Django model type validation):** Change how resolved models are verified to be Django `models.Model` subclasses.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::require_model_class`][mutations-sets].
  - *Site count:* 1.
- **Posited change 10 (Modifying the resolver seam classmethod factory):** Change the lazy import wrapper generation for `resolve_sync` and `resolve_async` seams across mutation bases.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::resolver_seams`][mutations-sets].
  - *Site count:* 1.
- **Posited change 11 (Modifying select_for_update locking validation):** Update validation or default value handling for `Meta.select_for_update` across model-backed write flavors.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::validate_select_for_update`][mutations-sets].
  - *Site count:* 1.
- **Posited change 12 (Modifying permission classes validation and default assignment):** Alter validation rules or default permission class assignments for model-backed mutations.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::_validate_permission_classes`][mutations-sets] or [`django_strawberry_framework/mutations/sets.py::model_backed_permission_and_lock`][mutations-sets].
  - *Site count:* 1.
- **Posited change 13 (Modifying the phase-2.5 write declaration binding loop):** Alter the binding sequence, type resolution, or payload materialization across mutation declaration registries.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::bind_write_declarations`][mutations-sets].
  - *Site count:* 1.
- **Posited change 14 (Modifying payload materialization and attribute stashing):** Alter how payload classes are built and how `_primary_type`, `_input_class`, and `_payload_type_name` are stashed.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::bind_mutation_outputs`][mutations-sets].
  - *Site count:* 1.
- **Posited change 15 (Modifying relation override shape-locking rules):** Change the Relay GlobalID core type or list depth verification for consumer relation overrides.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::_validate_relation_override_types`][mutations-sets].
  - *Site count:* 1.

### Rejected candidates

1. **Merging `DjangoFormMutation` into `DjangoMutation`:**
   - Disproved per [spec-038][spec-038] Decisions 6 & 10. `DjangoFormMutation` represents model-less write mutations (plain `forms.Form`). It has no associated Django model, no `DjangoType` slot, no model-derived permissions default, and no model operation. Forcing plain forms into `DjangoMutation` would require nullable model branches across the mutation subsystem, violating the model-backed mutation contract.
2. **Making `DjangoMutation` a `DjangoType` sidecar:**
   - Disproved per [spec-036][spec-036] Decision 5. `DjangoMutation` specifies its own `Meta.model` directly and does not attach as a sidecar attribute on `DjangoType` (unlike `FilterSet` / `OrderSet`). The phase-2.5 bind iterates the mutation declaration registry, keeping write and read declarations decoupled.
3. **Sharing a single declaration registry between model mutations and plain form mutations:**
   - Disproved per [spec-038][spec-038] Decision 13. While both registries share mechanics via [`make_declaration_registry`][mutations-sets], they operate over disjoint stores drained by different binding routines (`bind_mutations` vs `bind_form_mutations`).
4. **Coalescing form constructor hook waiver with DRF serializer waiver:**
   - Disproved per [spec-038][spec-038] Decision 7 and [spec-039][spec-039] Decision 7. Forms waive create-required narrowing when overriding `get_form_kwargs` / `get_form`, whereas serializer mutations deliberately reject constructor-hook waivers in favor of explicit `Meta.injected_fields`.

## Opportunities

None — `django_strawberry_framework/mutations/sets.py` is a clean, 1661-line module serving as the foundational root owner for all write mutations across the framework. All reusable metaclass generation, declaration registry management, shape caching, validation primitives, resolver seam synthesis, constructor kwarg packaging, relation override type locks, and phase-2.5 binding orchestration are consolidated here and cleanly consumed by `django_strawberry_framework/forms/sets.py` and `django_strawberry_framework/rest_framework/sets.py`.

## Judgment

Zero-edit review. `django_strawberry_framework/mutations/sets.py` contains zero duplicate policy or unowned invariants. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/sets.py --review docs/dry/dry-file-mutations__sets.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification conducted by Worker 2 on 2026-08-24.

### Verification of Core Contracts and Seams

1. **Root Ownership of Write Infrastructure:**
   - Re-traced the contract hierarchy across all three write flavors: model mutations in [`mutations/sets.py`][mutations-sets], form mutations in [`forms/sets.py`][forms-sets], and DRF serializer mutations in [`rest_framework/sets.py`][rest-framework-sets].
   - Verified that all shared write mechanisms reside canonically in [`django_strawberry_framework/mutations/sets.py`][mutations-sets] without duplication or policy leakage:
     - Metaclass generation via [`make_meta_validating_metaclass`][mutations-sets];
     - Isolated declaration registry state via [`make_declaration_registry`][mutations-sets] and [`DeclarationRegistry`][mutations-sets];
     - Typo detection via [`reject_unknown_meta_keys`][mutations-sets];
     - Backing class and model type gates via [`require_backing_class`][mutations-sets], [`require_subclass`][mutations-sets], and [`require_model_class`][mutations-sets];
     - Operation vocabulary and validation via [`NON_DELETE_OPERATION_INPUT_KIND`][mutations-sets], [`_OPERATION_INPUT_OVERRIDE_ATTR`][mutations-sets], [`NON_DELETE_WRITE_OPERATIONS`][mutations-sets], [`_VALID_OPERATIONS`][mutations-sets], [`non_delete_operation_error`][mutations-sets], and [`require_non_delete_operation`][mutations-sets];
     - Sequence normalization via [`normalize_meta_field_selection`][mutations-sets];
     - Shape cache management and input materialization via [`_shape_build_cache`][mutations-sets], [`cached_build_input`][mutations-sets], and [`build_and_stash_input`][mutations-sets];
     - Constructor kwargs assembly and hook waiver detection via [`construction_kwargs`][mutations-sets] and [`_hook_overridden`][mutations-sets];
     - Resolver seam synthesis via [`resolver_seams`][mutations-sets];
     - Concurrency locking and permission validation via [`validate_select_for_update`][mutations-sets], [`_validate_permission_classes`][mutations-sets], and [`model_backed_permission_and_lock`][mutations-sets];
     - Schema finalization and payload binding via [`_resolve_primary_type`][mutations-sets], [`bind_mutation_outputs`][mutations-sets], [`bind_write_declarations`][mutations-sets], and [`bind_mutations`][mutations-sets].

2. **Probing Matrix 5-Axis Discharge:**
   - **Cross-flavor policy mirroring:** Fully verified. `mutations/sets.py` serves as the single source of truth for all write flavors. Read subsystems (`types/base.py`, `filters/sets.py`, `orders/sets.py`) maintain separate, disjoint namespaces and lifecycles.
   - **Sync and async twins:** Fully verified. `resolver_seams` generates symmetric `resolve_sync` and `resolve_async` classmethods wrapping lazy imports to eliminate circular module dependencies. Sync permission checks in `DjangoMutation.check_permission` invoke `run_permission_classes`, raising `SyncMisuseError` on async coroutines to prevent authorization bypasses.
   - **Derived rather than repeated knowledge:** Fully verified. Operation allow-lists derive strictly from generator mapping keys. Expected input attribute names derive from model reflection (`editable_input_fields` and `relation_input_annotation`). Merged inputs utilize Python class inheritance for field union and precedence. Relation override checks peel Strawberry decorators dynamically via `unwrap_return_type` and `_strawberry_field_shape`.
   - **Inverse and round-trip pairs:** Fully verified. Declarative `Meta.fields` / `Meta.exclude` configurations are validated against model fields and converted to input shapes, whose stashed reverse specs (`_input_field_specs`, `_model_fields_by_attr`) are consumed by resolvers to decode GraphQL inputs back into model fields. Declaration registration is balanced by finalization draining and test reset hooks.
   - **Cross-medium codification:** Fully verified across specifications (spec-036, spec-038, spec-039, spec-040, spec-046, spec-047), documentation, and test suites (101 mutation set tests and 984 total write tests passing).

3. **Subsystem Boundaries and Rejected Alternatives:**
   - Confirmed that keeping `DjangoFormMutation` separate from `DjangoMutation` is architecturally correct due to the model-less nature of plain form mutations (no Django model, no DjangoType slot, no `select_for_update` lock).
   - Confirmed that keeping `DjangoMutation` decoupled from `DjangoType` sidecars avoids write/read coupling and preserves clean schema finalization ordering.
   - Confirmed that maintaining separate declaration registries via `make_declaration_registry` preserves distinct binding pipelines and subsystem clear hooks.

4. **Single-Edit-Site Counts:**
   - Re-verified all 15 posited change scenarios. Each posited modification requires editing exactly 1 canonical site at its root owner.

5. **Tooling and Test Verification:**
   - `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/sets.py --review docs/dry/dry-file-mutations__sets.md --include-constants` confirms all 44 target definitions covered (0 missing).
   - Full test suites pass (`tests/mutations/`, `tests/forms/`, `tests/rest_framework/`).

Status updated to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-mutation_sets-0_0_11.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-drf_serializer_mutations-0_0_13.md
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md
[spec-046]: ../SPECS/spec-046-transport_security-0_0_14.md
[spec-047]: ../SPECS/spec-047-resource_policy-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[rest-framework-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py

<!-- tests/ -->
[test-forms-sets]: ../../tests/forms/test_sets.py
[test-mutations-fields]: ../../tests/mutations/test_fields.py
[test-mutations-inputs]: ../../tests/mutations/test_inputs.py
[test-mutations-resolvers]: ../../tests/mutations/test_resolvers.py
[test-mutations-sets]: ../../tests/mutations/test_sets.py
[test-rest-framework-sets]: ../../tests/rest_framework/test_sets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
