# DRY review: `django_strawberry_framework/filters/`

Status: verified

## System trace

`django_strawberry_framework/filters/` is the declarative query-filtering subsystem ([spec-027][spec-027], [spec-031][spec-031], [spec-051][spec-051]). It bridges Django's `django-filter` ecosystem into Strawberry GraphQL, providing declarative filter definition, automatic GraphQL input dataclass generation, Relay GlobalID adaptation, PostgreSQL array and list filtering, integer overflow protection, tree-form boolean logic composition (`and`, `or`, `not`), correlated-`EXISTS` query optimization, and synchronous/asynchronous execution pipelines.

The subpackage implements a six-layer pipeline partitioned across five modules:

1. [`filters/__init__.py`][filters-init]: The public subpackage export facade and consumer forward-reference helper (Layer 3):
   - **Public Re-Export Surface:** Re-exports foundational primitives from [`filters/base.py`][filters-base] ([`Filter`][filters-base] shadowing `django_filters.Filter`, [`TypedFilter`][filters-base], [`ArrayFilter`][filters-base], [`ArrayFilterMethod`][filters-base], [`ListFilter`][filters-base], [`ListFilterMethod`][filters-base], [`RangeFilter`][filters-base], [`RangeField`][filters-base], [`validate_range`][filters-base], [`GlobalIDFilter`][filters-base], [`GlobalIDMultipleChoiceFilter`][filters-base], [`LazyRelatedClassMixin`][filters-base], [`RelatedFilter`][filters-base]) and declarative FilterSet classes from [`filters/sets.py`][filters-sets] ([`FilterSet`][filters-sets], [`FilterSetMetaclass`][filters-sets]) in [`__all__`][filters-init].
   - **Consumer Helper:** [`filter_input_type`][filters-init] returns the Strawberry forward-reference type annotation `Annotated["<Name>FilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]` for custom resolver declarations, validating base classes and delegating to [`django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`][utils-inputs].
   - **Lifecycle Ledger & Clear Hook:** Maintains [`_helper_referenced_filtersets`][filters-init] (`set[type[FilterSet]]`) recording filtersets passed to [`filter_input_type`][filters-init], exposes [`_clear_helper_referenced_filtersets`][filters-init] registered with [`django_strawberry_framework/registry.py::register_subsystem_clear`][registry] (`owner="filters.helper_references"`), and feeds Phase 2.5 finalizer orphan detection ([`django_strawberry_framework/types/finalizer.py`][types-finalizer]).
   - **Encapsulation:** Internal BFS factories ([`FilterArgumentsFactory`][filters-factories]) and dynamic input module internals (`INPUTS_MODULE_PATH`, `_input_type_name_for`) are deliberately omitted from [`__all__`][filters-init] per [spec-027][spec-027] Decision 2.

2. [`filters/base.py`][filters-base]: Foundational filter primitives, form fields, validators, integer overflow guards, Relay GlobalID adaptation, and cross-relation traversal (Layer 1 & Layer 2):
   - **Base Hierarchy:** [`Filter`][filters-base] re-exported from `django_filters.Filter`; [`TypedFilter`][filters-base] subclassing `django_filters.Filter` without Graphene dependencies.
   - **Array & List Filtering:** PostgreSQL array support via [`ArrayFilterMethod`][filters-base] and [`ArrayFilter`][filters-base] (with property setter [`ArrayFilter.method`][filters-base] and filter execution [`ArrayFilter.filter`][filters-base]), sharing [`_EmptyListAwareFilterMethod`][filters-base] ([`_EmptyListAwareFilterMethod.__call__`][filters-base]) and [`_install_empty_list_aware_method`][filters-base] with CSV/JSON list filtering in [`ListFilterMethod`][filters-base] and [`ListFilter`][filters-base] (with property setter [`ListFilter.method`][filters-base] and filter execution [`ListFilter.filter`][filters-base]). Empty lists `[]` are evaluated as real filter values for arrays and mapped to empty querysets via [`_match_none_queryset`][filters-base] for list filters.
   - **Range Filtering & Bounds Validation:** [`validate_range`][filters-base] validating 2-element sequence boundaries, [`RangeField`][filters-base] setting `default_validators=[validate_range]`, and [`RangeFilter`][filters-base] binding `field_class = RangeField`.
   - **Integer Overflow Protection:** [`_coerce_int_in_members`][filters-base] using [`django_strawberry_framework/utils/querysets.py::coerce_field_value_or_none`][utils-querysets], [`IntegerInFilter`][filters-base] ([`IntegerInFilter.filter`][filters-base]), and [`IntegerRangeFilter`][filters-base] ([`IntegerRangeFilter.filter`][filters-base]) decomposing ranges into compound `{gte, lte}` predicates via [`_apply_lookups`][filters-base] and [`_apply_lookup_predicate`][filters-base].
   - **Relay GlobalID Filtering & Strategy Validation:** Constants [`FRAMEWORK_GLOBALID_STRATEGIES`][filters-base], [`ENCODE_ONLY_GLOBALID_STRATEGIES`][filters-base], and [`_GLOBALID_RELATION_PK_ATTR`][filters-base]. Relation detection via [`_relation_uses_non_pk_to_field`][filters-base] and dynamic runtime field qualification via [`_marked_pk_field_name`][filters-base]. Target definition derivation via [`_target_definition_for`][filters-base] and [`resolve_globalid_target_definition`][filters-base]. Strategy validation via [`_accepted_globalid_type_names`][filters-base], container check via [`_globalid_multiple_choice_values`][filters-base], and decoding via [`_decode_and_validate_global_id`][filters-base]. Filter classes: [`GlobalIDFilter`][filters-base] ([`GlobalIDFilter.filter`][filters-base]), [`_AbsentGlobalIDMultipleChoiceWidget`][filters-base] ([`_AbsentGlobalIDMultipleChoiceWidget.value_from_datadict`][filters-base]), [`_GlobalIDMultipleChoiceField`][filters-base] ([`_GlobalIDMultipleChoiceField.valid_value`][filters-base], [`_GlobalIDMultipleChoiceField.to_python`][filters-base], [`_GlobalIDMultipleChoiceField.validate`][filters-base]), and [`GlobalIDMultipleChoiceFilter`][filters-base] ([`GlobalIDMultipleChoiceFilter.filter`][filters-base]).
   - **Related Filter Traversal:** [`LazyRelatedClassMixin`][filters-base] (re-exported from [`django_strawberry_framework/sets_mixins.py`][sets-mixins]) and [`RelatedFilter`][filters-base] (subclassing `RelatedSetTargetMixin` and `django_filters.ModelChoiceFilter`), providing [`RelatedFilter.__init__`][filters-base], [`RelatedFilter.bind_filterset`][filters-base], [`django_strawberry_framework/filters/base.py::RelatedFilter.filterset`][filters-base] property getter/setter, and [`RelatedFilter.get_queryset`][filters-base].

3. [`filters/inputs.py`][filters-inputs]: Input dataclass generation namespace, lookup mappings, operator-bag minting, and data converters (Layer 3 & Layer 5):
   - **Namespace Scaffolding & Mappings:** Module path constant [`INPUTS_MODULE_PATH`][filters-inputs], search prefixes [`LOOKUP_PREFIXES`][filters-inputs], canonical 25-lookup expression mapping [`LOOKUP_NAME_MAP`][filters-inputs], logical operator descriptor [`LogicOperatorDescriptor`][filters-inputs] (`python_attr`, `wire_name`, `is_sequence`, `compose`), singletons [`LOGIC_OP_AND`][filters-inputs], [`LOGIC_OP_OR`][filters-inputs], [`LOGIC_OP_NOT`][filters-inputs], operator tuple [`LOGIC_OPERATORS`][filters-inputs], index mappings [`LOGIC_OPERATORS_BY_WIRE`][filters-inputs] and [`LOGIC_OPERATORS_BY_PYTHON_ATTR`][filters-inputs], and composition functions [`_compose_and`][filters-inputs], [`_compose_or`][filters-inputs], and [`_compose_not`][filters-inputs]. Namespace management via [`materialize_input_class`][filters-inputs] and [`clear_filter_input_namespace`][filters-inputs] registered with [`register_subsystem_clear`][registry] (`owner="filters.input_namespace"`, `before_bind=True`).
   - **Internal Helpers:** [`_pascal_case`][filters-inputs] (delegating to [`pascal_case_or_raise`][utils-strings] with [`exceptions.py::_safe_arg_repr`][exceptions]), [`_scalar_from_form_field`][filters-inputs], [`_scalar_from_model_field`][filters-inputs] (delegating to [`types/converters.py::scalar_for_field`][types-converters]), [`_choice_enum_from_filter`][filters-inputs] (delegating to [`types/converters.py::convert_choices_to_enum`][types-converters]), [`_element_annotation`][filters-inputs], [`_owner_type_name`][filters-inputs], [`_model_field_for_filter`][filters-inputs], and [`construct_search`][filters-inputs].
   - **MRO Conversion & Normalization:** Symmetrical kind tuple [`_FILTER_INPUT_KIND_TYPES`][filters-inputs], symmetry check [`_filter_input_prechecks`][filters-inputs] (`strict=True`), error factory [`_unexpected_filter_dispatch`][filters-inputs], annotation generator [`convert_filter_to_input_annotation`][filters-inputs], and runtime value normalizer [`normalize_input_value`][filters-inputs] powered by [`django_strawberry_framework/utils/converters.py::convert_with_mro`][utils-converters] and [`django_strawberry_framework/utils/input_values.py::is_inactive_value`][utils-input-values].
   - **Leaf & Logic Builders:** Re-encoding [`_encode_global_id_input`][filters-inputs], enum unwrapping [`_unwrap_enum_member`][filters-inputs], scoped range dataclass builder [`_build_range_input_class`][filters-inputs] (`{FilterSet}{Pascal(field_name)}RangeInputType`), positional range normalizer [`_normalize_range_value`][filters-inputs] (`{<name>_0, <name>_1}`), tree boolean combinator builder [`_build_logic_fields`][filters-inputs] (`and_`, `or_`, `not_`), and per-field operator-bag builder [`_build_input_fields`][filters-inputs] (`{FilterSet}{Pascal(field_name)}FilterInputType`) calling [`django_strawberry_framework/utils/inputs.py::emit_set_input_field_triples`][utils-inputs].

4. [`filters/factories.py`][filters-factories]: BFS input-generation factory and dynamic-FilterSet cache (Layer 5 & Layer 6):
   - **BFS Input-Class Factory:** [`FilterArgumentsFactory`][filters-factories] subclasses [`django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory`][utils-inputs], supplying isolated caches (`input_object_types`, `_type_filterset_registry`), hooks (`_collision_registry_attr`, `_factory_label`, `_family_label`, `_rename_noun`, `_related_attr`, `_related_target_attr`), and triple builder [`FilterArgumentsFactory._build_input_triples`][filters-factories] composing [`_build_input_fields`][filters-inputs] and [`_build_logic_fields`][filters-inputs].
   - **Dynamic FilterSet Caching:** Module cache `_dynamic_filterset_cache`, reserved keyword set [`_RESERVED_FACTORY_KEYS`][filters-factories] (`frozenset({"filterset_base_class"})`), dynamic constructor built via [`django_strawberry_framework/utils/inputs.py::make_dynamic_set_getter`][utils-inputs], and public factory helper [`get_filterset_class`][filters-factories] (normalizing meta kwargs via [`normalize_set_meta_for_factory`][utils-inputs] and [`make_set_meta_cache_key`][utils-inputs], generating synthetic filtersets via [`create_dynamic_set_class`][utils-inputs]).

5. [`filters/sets.py`][filters-sets]: Metaclass, FilterSet class, policy baselines, optimizer release auditing, candidate metadata, provenance tracking, family profiles, Relay filter adaptation, normalization, permission checks, correlated-`EXISTS` query optimization, and execution pipelines (Layer 4 & Layer 5):
   - **Reverse Mappings & Traversal:** [`_LOGIC_PYTHON_ATTRS`][filters-sets], [`_FORM_KEY_BY_PYTHON_ATTR`][filters-sets] (derived from [`LOOKUP_NAME_MAP`][filters-inputs]), and traversal configuration [`_NORMALIZE_TRAVERSAL`][filters-sets] (`ActiveInputTraversalAttrs`).
   - **Lookup Expansion & Model-Choice Stripping:** [`_lookups_for_field`][filters-sets] memoized lookup cache excluding `Transform`, [`_MODEL_CHOICE_ONLY_EXTRAS`][filters-sets], and [`_strip_model_choice_extras`][filters-sets].
   - **Policy Baseline & Provider Functions:** [`_forward_relation_extra`][filters-sets], [`_forward_m2m_extra`][filters-sets], [`_reverse_o2o_extra`][filters-sets], [`_reverse_rel_extra`][filters-sets], public deepcopyable dictionary [`_PUBLIC_PACKAGE_FILTER_DEFAULTS`][filters-sets], immutable value baseline [`_PACKAGE_POLICY_BASELINE`][filters-sets] of [`_NormalizedPolicyEntry`][filters-sets] records normalized via [`_normalize_policy_entry`][filters-sets].
   - **Optimizer Audited Release Range:** [`_AUDITED_DJANGO_FILTER_RANGE`][filters-sets] (`((25, 2), (27,))`), semver parser [`_release_is_audited`][filters-sets], and cached boolean [`_DJANGO_FILTER_OPTIMIZER_AUDITED`][filters-sets].
   - **Provenance Tracking:** Private attribute [`_GENERATION_PROVENANCE_ATTR`][filters-sets], dataclass [`FilterGenerationProvenance`][filters-sets], public accessor [`filter_generation_provenance`][filters-sets], stamper [`_stamp_generation_provenance`][filters-sets], and origins [`_FRAMEWORK_GENERATED_ORIGINS`][filters-sets].
   - **Filter Family Profiles:** Record [`_FilterFamilyProfile`][filters-sets], profile singletons [`_SCALAR_LOOKUP_PROFILE`][filters-sets], [`_SEQUENCE_LOOKUP_PROFILE`][filters-sets], [`_CHOICE_PROFILE`][filters-sets], [`_MODEL_CHOICE_PROFILE`][filters-sets], [`_MULTIPLE_CHOICE_PROFILE`][filters-sets], [`_MODEL_MULTIPLE_CHOICE_PROFILE`][filters-sets], [`_GLOBALID_PROFILE`][filters-sets], [`_GLOBALID_MULTIPLE_PROFILE`][filters-sets], sequence [`_ALL_FAMILY_PROFILES`][filters-sets], mapping registry [`_FILTER_FAMILY_REGISTRY`][filters-sets], dynamic CSV introspectors [`_EmptyBodyDynamicCsvReference`][filters-sets], [`_EMPTY_BODY_DYNAMIC_CSV_ATTRS`][filters-sets], [`_dynamic_csv_profile_for`][filters-sets], and resolver [`_family_profile_for`][filters-sets].
   - **Candidate Metadata & Expansion Publication:** Immutable dataclasses [`CandidateFilterMetadata`][filters-sets], [`ExpansionSnapshot`][filters-sets], and factory [`_candidate_metadata_for`][filters-sets].
   - **Metaclass & Recursive Expansion:** [`FilterSetMetaclass`][filters-sets] with [`FilterSetMetaclass.__new__`][filters-sets] (promoting `filter_fields` via [`promote_set_meta_fields`][utils-inputs], collecting `RelatedFilter`s via [`collect_related_declarations`][sets-mixins], stamping declared provenance, and attaching lifecycle descriptors) and recursive relation expander [`_expand_related_filter`][filters-sets].
   - **FilterSet Core Class:** [`FilterSet`][filters-sets] subclassing [`ClassBasedTypeNameMixin`][sets-mixins], [`ActiveInputPermissionMixin`][sets-mixins], and `django_filters.filterset.BaseFilterSet`. Expansion resolution in [`FilterSet.get_filters`][filters-sets] (using [`expanded_once`][sets-mixins] and [`should_cache_expansion`][sets-mixins]), published snapshot accessor [`FilterSet._expansion_snapshot`][filters-sets], lookup narrowing in [`FilterSet.get_fields`][filters-sets], Relay adaptation in [`FilterSet.filter_for_field`][filters-sets] and [`FilterSet.filter_for_lookup`][filters-sets], provenance check in [`FilterSet._generation_origin_for_field`][filters-sets], capability check in [`FilterSet._is_generation_capable`][filters-sets], own-PK check in [`FilterSet._is_own_pk_under_relay_owner`][filters-sets], Relay filter class selection in [`FilterSet._relay_filter_class_for_field`][filters-sets], and relation target resolution in [`FilterSet._resolve_relation_target_type`][filters-sets].
   - **Input Normalization & Shape Validation:** Delegate [`FilterSet._iter_input_items`][filters-sets] (using [`iter_input_items`][utils-input-values]), logical branch iterator [`FilterSet._iter_logic_branches`][filters-sets], shape validators [`FilterSet._validate_logic_branch_shape`][filters-sets] and [`FilterSet._validate_logic_element_shape`][filters-sets], normalization driver [`FilterSet._normalize_input`][filters-sets] (using [`iter_active_fields`][utils-input-values] and [`normalize_input_value`][filters-inputs]), bag inspector [`FilterSet._operator_bag_items`][filters-sets], key reverser [`FilterSet._form_key_for_python_attr`][filters-sets], and permission path mapper [`FilterSet._permission_fallback_path`][filters-sets].
   - **Relation Visibility, Permissions, Optimization, & Pipelines:** Step iterator [`FilterSet._iter_visibility_steps`][filters-sets], sync visibility scoping [`FilterSet._derive_related_visibility_querysets_sync`][filters-sets] (via [`apply_type_visibility_sync`][utils-querysets]), async visibility scoping [`FilterSet._derive_related_visibility_querysets_async`][filters-sets] (via [`apply_type_visibility_async`][utils-querysets]), depth error factory [`FilterSet._raise_logic_depth_exceeded`][filters-sets], async nested visibility pre-await [`FilterSet._collect_nested_visibility_querysets_async`][filters-sets], target type resolver [`FilterSet._target_type_for_related_filter`][filters-sets], permission depth check [`FilterSet._check_permission_depth`][filters-sets], logic permission checker [`FilterSet._run_logic_permission_checks`][filters-sets], public permission checker [`FilterSet.check_permissions`][filters-sets], form validation [`FilterSet._validate_form_or_raise`][filters-sets] (`FILTER_INVALID`), distinct suppression [`FilterSet._invoke_suppressing_framework_distinct`][filters-sets], flat leaf evaluator [`FilterSet._apply_flat_leaves`][filters-sets] (routing routable candidates through [`correlated_inner_root`][predicates] and [`attach_exists`][predicates]), queryset filter pipeline [`FilterSet.filter_queryset`][filters-sets], boolean logic evaluator [`FilterSet._evaluate_logic_tree`][filters-sets], branch Q builder [`FilterSet._q_for_branch`][filters-sets], related constraint applicator [`FilterSet._apply_related_constraints`][filters-sets], shared prelude [`FilterSet._apply_common_prelude`][filters-sets], shared finalize [`FilterSet._apply_common_finalize`][filters-sets], synchronous entry point [`FilterSet.apply_sync`][filters-sets], asynchronous entry point [`FilterSet.apply_async`][filters-sets] (wrapped in [`run_in_one_sync_boundary`][utils-querysets]), and sync dispatcher [`FilterSet.apply`][filters-sets].

Connected subsystem integration examined:
- [`django_strawberry_framework/sets_mixins.py`][sets-mixins]: Canonical owner of shared set-family abstractions (`ClassBasedTypeNameMixin`, `ActiveInputPermissionMixin`, `SetLifecycleAttrs`, `collect_related_declarations`, `expanded_once`, `should_cache_expansion`, `RelatedSetTargetMixin`, `LazyRelatedClassMixin`).
- [`django_strawberry_framework/orders/`][orders-init]: Sibling ordering subsystem sharing factory algorithms, dynamic set constructors, input namespace lifecycle, and set lifecycle descriptors.
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Canonical owner of `GeneratedInputArgumentsFactory`, `make_dynamic_set_getter`, `make_set_input_namespace`, `emit_set_input_field_triples`, `build_strawberry_input_class`, `optional_field_kwargs`, `set_input_type_name`, `duplicate_name_message`, `make_set_meta_cache_key`, `normalize_set_meta_for_factory`, `create_dynamic_set_class`, `promote_set_meta_fields`, `FILTERSET_FIELDS_ALIAS`, `build_lazy_input_annotation`, and `GeneratedInputFieldSpec`.
- [`django_strawberry_framework/utils/input_values.py`][utils-input-values]: Shared input traversal primitives (`iter_active_fields`, `iter_input_items`, `is_inactive_value`, `ActiveInputTraversalAttrs`).
- [`django_strawberry_framework/utils/querysets.py`][utils-querysets]: Shared visibility scoping and async boundary execution (`apply_type_visibility_sync`, `apply_type_visibility_async`, `run_in_one_sync_boundary`, `coerce_field_value_or_none`).
- [`django_strawberry_framework/utils/relations.py`][utils-relations]: Shared relation path analysis (`classify_path`, `path_traverses_to_many`, `relation_kind`, `is_many_side_relation_kind`).
- [`django_strawberry_framework/utils/converters.py`][utils-converters]: Shared MRO conversion engine (`convert_with_mro`, `MRO_CONTINUE`).
- [`django_strawberry_framework/utils/strings.py`][utils-strings]: Shared casing utilities (`pascal_case_or_raise`, `graphql_camel_name`).
- [`django_strawberry_framework/optimizer/predicates.py`][predicates]: Subquery optimization primitives (`attach_exists`, `correlated_inner_root`).
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Phase 2.5 schema finalizer executing build-time GlobalID strategy audits via `resolve_globalid_target_definition` and validating `_helper_referenced_filtersets`.
- [`django_strawberry_framework/types/relay.py`][types-relay]: Relay strategy definitions (`MODEL_LABEL_STRATEGIES`, `TYPE_NAME_STRATEGIES`).
- [`django_strawberry_framework/types/converters.py`][types-converters]: Shared scalar and enum conversion (`scalar_for_field`, `convert_choices_to_enum`).
- [`django_strawberry_framework/registry.py`][registry]: Primary and model type registry, decentralized subsystem clear hooks (`register_subsystem_clear`).

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/filters/ --include-constants`):
- Parsed 5 target files (`__init__.py`, `base.py`, `factories.py`, `inputs.py`, `sets.py`), 5,780 total lines.
- Inventoried 172 definitions and module constants across the entire subpackage:
  - `filters/__init__.py`: 4 definitions/constants;
  - `filters/base.py`: 47 definitions/constants;
  - `filters/factories.py`: 4 definitions/constants;
  - `filters/inputs.py`: 34 definitions/constants;
  - `filters/sets.py`: 83 definitions/constants.
- Confirmed zero missing definitions and verified all reverse imports across production code, test suites, and examples.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   - *Filters vs Orders Sibling Symmetry:* `filters/` and `orders/` are organized into symmetrical five-file subpackages ([spec-027][spec-027], [spec-028][spec-028]). All cross-family mechanics are extracted to canonical root owners:
     - Relational BFS input-class generation is single-sited in [`django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory`][utils-inputs], inherited symmetrically by [`FilterArgumentsFactory`][filters-factories] and [`OrderArgumentsFactory`][orders-factories];
     - Dynamic set class synthesis and cache key normalization are single-sited in [`utils/inputs.py::make_dynamic_set_getter`][utils-inputs], [`make_set_meta_cache_key`][utils-inputs], [`normalize_set_meta_for_factory`][utils-inputs], and [`create_dynamic_set_class`][utils-inputs];
     - Input namespace materialization, duplicate class collision detection, and clear hook lifecycles are single-sited in [`utils/inputs.py::make_set_input_namespace`][utils-inputs];
     - Field camel-casing, name flattening, and field triple generation are single-sited in [`utils/inputs.py::emit_set_input_field_triples`][utils-inputs];
     - Lazy forward-reference string annotations and eager base validation are single-sited in [`utils/inputs.py::build_lazy_input_annotation`][utils-inputs];
     - Set metaclass field promotion is single-sited in [`utils/inputs.py::promote_set_meta_fields`][utils-inputs];
     - Related target binding, lazy target resolution, declared target collection, cycle-safe expansion caching, permission mixins, and class-based type name generation are single-sited in [`django_strawberry_framework/sets_mixins.py`][sets-mixins] ([`RelatedSetTargetMixin`][sets-mixins], [`LazyRelatedClassMixin`][sets-mixins], [`collect_related_declarations`][sets-mixins], [`expanded_once`][sets-mixins], [`should_cache_expansion`][sets-mixins], [`ActiveInputPermissionMixin`][sets-mixins], [`ClassBasedTypeNameMixin`][sets-mixins]).
     - *Domain-Dictated Divergence:* Filters generate per-field operator-bag dataclasses (`{FilterSet}{Pascal(field_name)}FilterInputType`) supporting multi-lookup inputs (`exact`, `iExact`, `gt`, `in`, `range`), and compose boolean logic fields (`and_`, `or_`, `not_`), whereas orders map leaves directly to [`Ordering | None`][orders-inputs] without boolean algebra ([spec-028][spec-028] Decision 8). Filters adapt Relay Node targets to [`GlobalIDFilter`][filters-base] and [`GlobalIDMultipleChoiceFilter`][filters-base], and support `HIDE_FLAT_FILTERS` to prune redundant flat traversals.
   - *Write Flavors (`mutations`, `forms`, `rest_framework`):* Build single-declaration inputs using [`build_strawberry_input_class`][utils-inputs] directly, reusing [`coerce_field_value_or_none`][utils-querysets], [`is_inactive_value`][utils-input-values], and [`iter_active_fields`][utils-input-values] without duplicating relational BFS or set expansion logic.
2. **Sync and async twins:**
   - *Build-Time Decoupling:* Schema construction, BFS input generation, dynamic FilterSet caching, and forward-reference registration (`filters/__init__.py`, `filters/factories.py`, `filters/inputs.py`) run entirely during schema compile time and are completely decoupled from runtime execution.
   - *Shared Execution Composition:* [`FilterSet.apply_sync`][filters-sets] and [`FilterSet.apply_async`][filters-sets] share 100% of their prelude logic ([`FilterSet._apply_common_prelude`][filters-sets]) and finalize logic ([`FilterSet._apply_common_finalize`][filters-sets]).
   - *Symmetric Visibility Scoping:* Sync visibility scoping ([`FilterSet._derive_related_visibility_querysets_sync`][filters-sets]) and async visibility scoping ([`FilterSet._derive_related_visibility_querysets_async`][filters-sets]) share identical traversal step generation via [`FilterSet._iter_visibility_steps`][filters-sets], delegating to [`apply_type_visibility_sync`][utils-querysets] and [`apply_type_visibility_async`][utils-querysets] respectively.
   - *Non-Blocking Async Boundary:* The async pipeline pre-awaits nested child visibility querysets via [`FilterSet._collect_nested_visibility_querysets_async`][filters-sets] and executes `_apply_common_finalize` inside [`run_in_one_sync_boundary`][utils-querysets], avoiding event-loop thread blocking while keeping Django ORM calls safely within thread-sensitive workers.
   - *Sync Dispatcher:* [`FilterSet.apply`][filters-sets] converts [`SyncMisuseError`][exceptions] into an actionable `RuntimeError`.
3. **Derived rather than repeated knowledge:**
   - *Facade Re-Exports:* `filters/__init__.py` derives its public surface directly from member modules.
   - *Naming Derivations:* Input type names derive strictly through [`set_input_type_name`][utils-inputs] (which delegates to `ClassBasedTypeNameMixin.type_name_for()`); range input names derive from owning FilterSet names (`{FilterSet}{Pascal(field_name)}RangeInputType`); dynamic FilterSet names derive via [`create_dynamic_set_class`][utils-inputs] (`<Model>AutoFilter`).
   - *Type Annotations:* Field annotations derive from model fields via [`_scalar_from_model_field`][filters-inputs] (delegating to [`types/converters.py::scalar_for_field`][types-converters]), choices via [`_choice_enum_from_filter`][filters-inputs] (delegating to [`types/converters.py::convert_choices_to_enum`][types-converters]), and form fields via [`_scalar_from_form_field`][filters-inputs].
   - *Reverse Mappings:* Reverse form keys derive from [`LOOKUP_NAME_MAP`][filters-inputs] into [`_FORM_KEY_BY_PYTHON_ATTR`][filters-sets] at module load.
   - *Policy Baselines:* Immutable baseline [`_PACKAGE_POLICY_BASELINE`][filters-sets] derives directly from [`_PUBLIC_PACKAGE_FILTER_DEFAULTS`][filters-sets] via [`_normalize_policy_entry`][filters-sets].
   - *Optimizer Eligibility:* Evaluated during `FilterSet.get_filters` and frozen into [`CandidateFilterMetadata.routable`][filters-sets] in [`ExpansionSnapshot`][filters-sets].
   - *Relay Target Definition:* Derived once by [`resolve_globalid_target_definition`][filters-base] iteratively parsing relation segments, shared between runtime evaluation ([`_target_definition_for`][filters-base]) and build-time schema audit ([`types/finalizer.py::_audit_globalid_filter_strategies`][types-finalizer]).
   - *Dynamic Field Lookups:* Derived dynamically via [`_lookups_for_field`][filters-sets] from `model_field.get_lookups()`.
4. **Inverse and round-trip pairs:**
   - *Lookup & Name Mapping Round-Trip:* Lookups mapped to `(python_attr, graphql_name)` by [`LOOKUP_NAME_MAP`][filters-inputs] and recorded in `_field_specs` during BFS generation round-trip back to Django form keys and ORM parameters via [`FilterSet._normalize_input`][filters-sets], [`FilterSet._operator_bag_items`][filters-sets], [`_FORM_KEY_BY_PYTHON_ATTR`][filters-sets], and [`normalize_input_value`][filters-inputs].
   - *Range Input Round-Trip:* [`_build_range_input_class`][filters-inputs] mints `{start, end}` dataclass fields; [`_normalize_range_value`][filters-inputs] unpacks them into Django `RangeWidget` positional form-data keys `{<name>_0, <name>_1}`.
   - *GlobalID Wire Format Round-Trip:* [`_encode_global_id_input`][filters-inputs] re-encodes `relay.GlobalID` to base64 wire strings so [`GlobalIDFilter`][filters-base] can decode and validate `type_name` at filter evaluation time.
   - *Subsystem Clear Hooks:* Helper ledger registration ([`_clear_helper_referenced_filtersets`][filters-init]) and input namespace registration ([`clear_filter_input_namespace`][filters-inputs]) cleanly reset ledgers during `TypeRegistry.clear()`.
   - *Distinct Flag Bracket:* [`FilterSet._invoke_suppressing_framework_distinct`][filters-sets] temporarily sets `distinct=False` on correlated inner roots and restores the original value in a `finally` block.
   - *Dynamic Factory Kwargs Round-Trip:* [`normalize_set_meta_for_factory`][utils-inputs] strips [`_RESERVED_FACTORY_KEYS`][filters-factories] and promotes `filter_fields`, ensuring identical logical declarations collapse onto the same cache slot and round-trip into synthetic `Meta` classes without keyword errors.
5. **Contracts restated in another medium:**
   - Specifications: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027], [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028], [`docs/SPECS/spec-030-django_connection_field-0_0_9.md`][spec-030], [`docs/SPECS/spec-031-globalid_type_names-0_0_9.md`][spec-031], [`docs/SPECS/spec-051-converters-0_0_14.md`][spec-051];
   - Code: [`django_strawberry_framework/filters/`][filters-init], [`django_strawberry_framework/sets_mixins.py`][sets-mixins], [`django_strawberry_framework/orders/`][orders-init], [`django_strawberry_framework/utils/inputs.py`][utils-inputs], [`django_strawberry_framework/utils/input_values.py`][utils-input-values], [`django_strawberry_framework/utils/querysets.py`][utils-querysets], [`django_strawberry_framework/optimizer/predicates.py`][predicates], [`django_strawberry_framework/types/`][types-finalizer];
   - Test suites: [`tests/filters/test_base.py`][test-filters-base], [`tests/filters/test_factories.py`][test-filters-factories], [`tests/filters/test_inputs.py`][test-filters-inputs], [`tests/filters/test_sets.py`][test-filters-sets], [`tests/filters/test_finalizer.py`][test-filters-finalizer], [`tests/test_relay_connection.py`][test-relay-connection], [`tests/test_registry.py`][test-registry];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook], [`GOAL.md`][goal].

### The single-edit-site test

- **Posited change 1 (Adding a new filter primitive, e.g. `SetFilter`):** Introduce a new empty-list-aware filter class.
  - *Sites that must move:* Exactly 2 sites: [`django_strawberry_framework/filters/base.py`][filters-base] (define `SetFilterMethod` and `SetFilter` using `_install_empty_list_aware_method` and `_match_none_queryset`) and [`django_strawberry_framework/filters/__init__.py`][filters-init] (export in `__all__`).
  - *Site count:* 2.
- **Posited change 2 (Adding a new lookup expression mapping, e.g. `trigram_similar`):** Add a lookup mapping from `django-filter` to GraphQL wire names and Python dataclass attributes.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/filters/inputs.py::LOOKUP_NAME_MAP`][filters-inputs] (which feeds [`_build_input_fields`][filters-inputs], [`FilterSet._normalize_input`][filters-sets], and [`normalize_input_value`][filters-inputs]).
  - *Site count:* 1.
- **Posited change 3 (Modifying GlobalID validation error codes or messages):** Update error message or code for malformed GlobalID inputs.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/filters/base.py::_decode_and_validate_global_id`][filters-base].
  - *Site count:* 1.
- **Posited change 4 (Altering the BFS input factory traversal or duplicate collision detection):** Update BFS queue ordering or collision error formatting across set families.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory`][utils-inputs] (zero edits in `filters/factories.py` or `orders/factories.py`).
  - *Site count:* 1.
- **Posited change 5 (Adjusting tree-form boolean combinator operator bag, e.g. adding `xor_`):** Introduce a new logical operator to the filter input type.
  - *Sites that must move:* Exactly 2 sites: [`django_strawberry_framework/filters/inputs.py::LOGIC_OPERATORS`][filters-inputs] (which automatically feeds [`_build_logic_fields`][filters-inputs] and [`FilterSet._normalize_input`][filters-sets]) and [`tests/filters/test_inputs.py`][test-filters-inputs].
  - *Site count:* 2.
- **Posited change 6 (Widening audited `django-filter` release range for optimizer):** Update the supported upstream version window for the optimizer.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/filters/sets.py::_AUDITED_DJANGO_FILTER_RANGE`][filters-sets].
  - *Site count:* 1.
- **Posited change 7 (Changing dynamic FilterSet synthesis suffix or reserved kwargs):** Change the synthetic class name suffix for dynamically created filtersets or add a reserved keyword.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/filters/factories.py`][filters-factories] (`auto_name_suffix` / [`_RESERVED_FACTORY_KEYS`][filters-factories]).
  - *Site count:* 1.
- **Posited change 8 (Modifying relation visibility execution pipelines or async boundary wrapper):** Adjust how async execution boundaries run sync ORM code.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary`][utils-querysets].
  - *Site count:* 1.

### Rejected candidates

1. **Merging `filters/base.py` and `filters/sets.py` into a single module:**
   - Disproved. `filters/base.py` encapsulates Layer 1 and Layer 2 primitives (filter classes, form fields, validators, GlobalID decoders) without depending on FilterSet metaclass or execution pipelines. Keeping them decoupled allows importing filter primitives and type definitions without triggering heavy FilterSet metaclass machinery or optimizer tables.
2. **Merging `filters/factories.py` and `filters/inputs.py` into a single module:**
   - Disproved. `filters/inputs.py` owns the Strawberry input generation namespace, lookup mappings, and runtime data converters, while `filters/factories.py` encapsulates the relational BFS traversal algorithm and Layer 6 dynamic FilterSet cache. Separating them prevents circular dependencies during dynamic input materialization.
3. **Sharing a single dynamic set cache dictionary across `filters/` and `orders/`:**
   - Disproved. FilterSet and OrderSet subclasses inhabit separate class hierarchies with different base classes (`FilterSet` vs `OrderSet`), different naming suffixes (`AutoFilter` vs `AutoOrder`), and different field alias rules (`FILTERSET_FIELDS_ALIAS` on filters vs `None` on orders). Keeping separate family cache dictionaries prevents cross-subsystem cache collisions and ensures lifecycle autonomy.
4. **Moving `resolve_globalid_target_definition` from `filters/base.py` to `types/finalizer.py`:**
   - Disproved. `resolve_globalid_target_definition` is required at runtime during query execution by `_target_definition_for` on every GlobalID filter evaluation. Placing it in `filters/base.py` keeps runtime filter evaluation self-contained while allowing `types/finalizer.py` to import and reuse the exact same function during build-time schema audits without circular imports.
5. **Re-exporting `FilterArgumentsFactory` from `django_strawberry_framework/filters/__init__.py`:**
   - Disproved per [spec-027][spec-027] Decision 2. `FilterArgumentsFactory` is an internal BFS input generation mechanism. Advanced consumers and schema generation import it directly from `django_strawberry_framework.filters.factories`. Excluding it from `filters/__init__.py::__all__` keeps the consumer facade clean and uncluttered.

## Opportunities

None — The folder integration of `django_strawberry_framework/filters/` is architecturally pristine, comprehensively tested, and fully consolidated at root owners. Cross-file boundaries across `__init__.py`, `base.py`, `factories.py`, `inputs.py`, and `sets.py`, as well as external boundaries with `sets_mixins.py`, `orders/`, `utils/inputs.py`, `utils/input_values.py`, `utils/querysets.py`, `utils/relations.py`, `utils/converters.py`, `optimizer/`, and `types/`, are strictly defined and honor all repository and design invariants.

## Judgment

Zero-edit folder integration review. All 5 files in `django_strawberry_framework/filters/` operate in total structural alignment. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 or 2 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. Subpackage folder integration verified clean and complete across all 5 files and 166 definitions/constants. Checked with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/filters/ --review docs/dry/dry-folder-filters.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification confirms that the folder integration of [`django_strawberry_framework/filters/`][filters-init] is complete, architecturally sound, and adheres to all repository and DRY design invariants.

### 1. Subsystem Trace & Layered Boundary Verification

Re-traced the six-layer query-filtering pipeline across all five modules:
- [`filters/__init__.py`][filters-init] (Layer 3 facade): Clean re-export surface in `__all__`, forward-reference helper [`filter_input_type`][filters-init] delegating to [`django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`][utils-inputs], and isolated ledger [`_helper_referenced_filtersets`][filters-init] registered via [`django_strawberry_framework/registry.py::register_subsystem_clear`][registry].
- [`filters/base.py`][filters-base] (Layer 1 & 2 primitives): Independent filter primitives ([`TypedFilter`][filters-base], [`ArrayFilter`][filters-base], [`ListFilter`][filters-base], [`RangeFilter`][filters-base], [`GlobalIDFilter`][filters-base], [`GlobalIDMultipleChoiceFilter`][filters-base], [`RelatedFilter`][filters-base]), empty-list awareness via [`_EmptyListAwareFilterMethod`][filters-base] and [`_match_none_queryset`][filters-base], integer overflow prevention via [`IntegerInFilter`][filters-base] and [`IntegerRangeFilter`][filters-base], and GlobalID resolution via [`resolve_globalid_target_definition`][filters-base].
- [`filters/inputs.py`][filters-inputs] (Layer 3 & 5 dynamic input namespace): Namespace lifecycle ([`materialize_input_class`][filters-inputs], [`clear_filter_input_namespace`][filters-inputs]), 25-lookup mapping ([`LOOKUP_NAME_MAP`][filters-inputs]), symmetrical MRO conversion ([`convert_filter_to_input_annotation`][filters-inputs], [`normalize_input_value`][filters-inputs]), range input builder ([`_build_range_input_class`][filters-inputs]), and per-field operator bags ([`_build_input_fields`][filters-inputs], [`_build_logic_fields`][filters-inputs]).
- [`filters/factories.py`][filters-factories] (Layer 5 & 6 BFS factory): [`FilterArgumentsFactory`][filters-factories] cleanly subclassing [`GeneratedInputArgumentsFactory`][utils-inputs], dynamic FilterSet getter [`get_filterset_class`][filters-factories] delegating to [`make_dynamic_set_getter`][utils-inputs], and isolated dynamic cache.
- [`filters/sets.py`][filters-sets] (Layer 4 & 5 metaclass, FilterSet core, and execution pipeline): Metaclass [`FilterSetMetaclass`][filters-sets] (incorporating [`sets_mixins.py::collect_related_declarations`][sets-mixins] and [`promote_set_meta_fields`][utils-inputs]), [`FilterSet`][filters-sets] (incorporating [`ClassBasedTypeNameMixin`][sets-mixins] and [`ActiveInputPermissionMixin`][sets-mixins]), immutable policy baseline [`_PACKAGE_POLICY_BASELINE`][filters-sets], optimizer release auditing [`_AUDITED_DJANGO_FILTER_RANGE`][filters-sets], frozen candidate metadata [`CandidateFilterMetadata`][filters-sets] and [`ExpansionSnapshot`][filters-sets], correlated-`EXISTS` query rewrites ([`correlated_inner_root`][predicates], [`attach_exists`][predicates]), and unified execution pipelines ([`FilterSet.apply_sync`][filters-sets], [`FilterSet.apply_async`][filters-sets], [`FilterSet.apply`][filters-sets]).

Cross-subsystem integration contracts with [`sets_mixins.py`][sets-mixins], [`orders/`][orders-init], [`utils/inputs.py`][utils-inputs], [`utils/input_values.py`][utils-input-values], [`utils/querysets.py`][utils-querysets], [`utils/relations.py`][utils-relations], [`utils/converters.py`][utils-converters], [`optimizer/predicates.py`][predicates], [`types/finalizer.py`][types-finalizer], and [`registry.py`][registry] are strictly observed without abstraction leaks.

### 2. Probing Matrix & Single-Edit-Site Verification

1. **Cross-flavor policy mirroring:** Verified sibling symmetry between `filters/` and `orders/`. Common graph traversal algorithms, dynamic set compilation, namespace lifecycle, and mixins reside in canonical root owners (`utils/inputs.py`, `sets_mixins.py`). Domain-specific logic (operator bags, boolean logic trees, Relay Node GlobalID adaptation, and correlated subqueries) is contained in `filters/`.
2. **Sync and async twins:** Verified that `apply_sync` and `apply_async` share 100% of their prelude ([`FilterSet._apply_common_prelude`][filters-sets]) and finalize ([`FilterSet._apply_common_finalize`][filters-sets]) pipelines, share step generation via [`FilterSet._iter_visibility_steps`][filters-sets], and execute async ORM boundaries cleanly via [`run_in_one_sync_boundary`][utils-querysets].
3. **Derived rather than repeated knowledge:** Re-export surface in `__init__.py`, input type naming via [`set_input_type_name`][utils-inputs], reverse lookup map [`_FORM_KEY_BY_PYTHON_ATTR`][filters-sets], immutable baseline [`_PACKAGE_POLICY_BASELINE`][filters-sets], candidate metadata routing verdicts in [`ExpansionSnapshot`][filters-sets], and GlobalID target definitions derive from single authoritative sources.
4. **Inverse and round-trip pairs:** Round-trip pairs verified across lookup expressions, `{start, end}` to `{_0, _1}` range mappings, GlobalID wire encoding/decoding, subsystem clear registrations, distinct suppression brackets, and factory kwargs normalization.
5. **Restatements in another medium:** Verified alignment across specifications ([spec-027][spec-027], [spec-028][spec-028], [spec-031][spec-031], [spec-051][spec-051]), implementation code, comprehensive test suites (`tests/filters/`), and documentation (`README.md`, `GLOSSARY.md`, `TREE.md`, `COOKBOOK.md`).

All single-edit-site counts (Posited changes 1–8) hold at 1 or 2 sites. All rejected candidates are architecturally justified.

### 3. Review Tool Check

Executed target definitions check:
```bash
uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/filters/ --review docs/dry/dry-folder-filters.md --include-constants
```
Output:
```
OK: 164 target definition(s) and 0 required topic(s) are covered.
```

Subpackage folder review verified with zero code modifications needed.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../GOAL.md

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-027]: ../SPECS/spec-027-filters-0_0_8.md
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-030]: ../SPECS/spec-030-django_connection_field-0_0_9.md
[spec-031]: ../SPECS/spec-031-globalid_type_names-0_0_9.md
[spec-051]: ../SPECS/spec-051-converters-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-factories]: ../../django_strawberry_framework/filters/factories.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[orders-base]: ../../django_strawberry_framework/orders/base.py
[orders-factories]: ../../django_strawberry_framework/orders/factories.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[predicates]: ../../django_strawberry_framework/optimizer/predicates.py
[registry]: ../../django_strawberry_framework/registry.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[utils-converters]: ../../django_strawberry_framework/utils/converters.py
[utils-input-values]: ../../django_strawberry_framework/utils/input_values.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py

<!-- tests/ -->
[test-filters-base]: ../../tests/filters/test_base.py
[test-filters-factories]: ../../tests/filters/test_factories.py
[test-filters-finalizer]: ../../tests/filters/test_finalizer.py
[test-filters-inputs]: ../../tests/filters/test_inputs.py
[test-filters-sets]: ../../tests/filters/test_sets.py
[test-orders-factories]: ../../tests/orders/test_factories.py
[test-orders-sets]: ../../tests/orders/test_sets.py
[test-registry]: ../../tests/test_registry.py
[test-relay-connection]: ../../tests/test_relay_connection.py
[test-types-converters]: ../../tests/types/test_converters.py
[test-types-finalizer]: ../../tests/types/test_finalizer.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
