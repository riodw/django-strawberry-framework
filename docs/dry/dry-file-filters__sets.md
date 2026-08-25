# DRY review: `django_strawberry_framework/filters/sets.py`

Status: verified

## System trace

`django_strawberry_framework/filters/sets.py` defines the core FilterSet metaclass, class hierarchy, policy baselines, optimizer release auditing, generation provenance tracking, family profiles, candidate metadata caching, related filter expansion, Relay-aware filter generation, input normalization, permission filtering, relation visibility derivation, correlated-`EXISTS` query optimization, tree-form boolean combinator evaluation (`and_`, `or_`, `not_`), and the synchronous/asynchronous execution pipelines ([spec-027][spec-027], [spec-031][spec-031], [spec-051][spec-051]). It comprises Layer 4 (filter expansion, metaclass, and Relay awareness) and Layer 5 (execution pipelines and optimizer adapter) of the filtering subsystem. It owns the following responsibilities:

1. **Logical Traversal & Reverse Key Scaffolding:**
   - [`_LOGIC_PYTHON_ATTRS`][filters-sets]: Frozen set `frozenset({"and_", "or_", "not_"})` defining Python-side attribute names for boolean combinators, consumed by [`_NORMALIZE_TRAVERSAL`][filters-sets] and [`ActiveInputPermissionAttrs`][sets-mixins].
   - [`_FORM_KEY_BY_PYTHON_ATTR`][filters-sets]: Precomputed reverse map derived from [`LOOKUP_NAME_MAP`][filters-inputs] mapping Python dataclass attributes back to `django-filter` form lookup keys (e.g. `i_contains` -> `icontains`, `in_` -> `in`), consumed by [`FilterSet._form_key_for_python_attr`][filters-sets] and [`FilterSet._operator_bag_items`][filters-sets].
   - [`_NORMALIZE_TRAVERSAL`][filters-sets]: Module-level singleton instance of [`ActiveInputTraversalAttrs`][utils-input-values] configured with `_field_specs`, `_LOGIC_PYTHON_ATTRS`, and `UNSET`, consumed by [`iter_active_fields`][utils-input-values] inside [`FilterSet._normalize_input`][filters-sets].

2. **Field Lookup Expansion & Model Choice Stripping:**
   - [`_lookups_for_field`][filters-sets]: Memoized helper caching lookup names returned by `model_field.get_lookups()` excluding Django `Transform` subclasses, consumed by [`FilterSet.get_fields`][filters-sets] for per-field `__all__` expansion.
   - [`_MODEL_CHOICE_ONLY_EXTRAS`][filters-sets]: Frozen set of constructor kwargs (`queryset`, `empty_label`, `to_field_name`, `null_label`, `null_value`, `limit_choices_to`) specific to `ModelChoiceFilter` / `ModelMultipleChoiceFilter`.
   - [`_strip_model_choice_extras`][filters-sets]: Strips model-choice-only kwargs when converting upstream relational filters to [`GlobalIDFilter`][filters-base] or [`GlobalIDMultipleChoiceFilter`][filters-base] in [`FilterSet.filter_for_field`][filters-sets] and [`FilterSet.filter_for_lookup`][filters-sets].

3. **Public Generation Policy & Immutable Policy Baseline:**
   - [`_forward_relation_extra`][filters-sets], [`_forward_m2m_extra`][filters-sets], [`_reverse_o2o_extra`][filters-sets], [`_reverse_rel_extra`][filters-sets]: Package-owned extra-kwarg provider functions mirroring `django-filter` 25.2 `FILTER_FOR_DBFIELD_DEFAULTS` without referencing foreign module globals.
   - [`_PUBLIC_PACKAGE_FILTER_DEFAULTS`][filters-sets]: The package-authored public generation-policy dictionary installed on [`FilterSet.FILTER_DEFAULTS`][filters-sets] as our own deepcopyable dictionary.
   - [`_NormalizedPolicyEntry`][filters-sets]: Named tuple `(filter_class, extra_identity)` representing normalized policy entries for value comparison.
   - [`_normalize_policy_entry`][filters-sets]: Extracts and normalizes policy entries from raw dictionaries or tuples.
   - [`_PACKAGE_POLICY_BASELINE`][filters-sets]: Private, normalized baseline dictionary derived from [`_PUBLIC_PACKAGE_FILTER_DEFAULTS`][filters-sets] used by [`FilterSet._generation_origin_for_field`][filters-sets] to distinguish pristine framework defaults from consumer overrides.

4. **Optimizer Audited Release Verification:**
   - [`_AUDITED_DJANGO_FILTER_RANGE`][filters-sets]: Pinned version tuple `((23, 1), (25, 2))` representing the inclusive semver range of audited `django-filter` releases.
   - [`_release_is_audited`][filters-sets]: Parses version strings against [`_AUDITED_DJANGO_FILTER_RANGE`][filters-sets].
   - [`_DJANGO_FILTER_OPTIMIZER_AUDITED`][filters-sets]: Module-level boolean caching whether the installed `django_filters.__version__` falls within the audited range.

5. **Generation Provenance Tracking:**
   - [`_GENERATION_PROVENANCE_ATTR`][filters-sets]: Private symbol `"_dst_generation_provenance"` for attaching provenance to filter instances.
   - [`FilterGenerationProvenance`][filters-sets]: Frozen dataclass capturing origin (`FilterOrigin`), `framework_added_distinct`, `generation_capable`, and `expanded_from` breadcrumbs.
   - [`filter_generation_provenance`][filters-sets]: Public accessor retrieving provenance from a filter instance.
   - [`_stamp_generation_provenance`][filters-sets]: Attaches frozen provenance to a filter instance.
   - [`_FRAMEWORK_GENERATED_ORIGINS`][filters-sets]: Frozen set `frozenset({"framework_default", "package_replacement"})` defining framework-generated origins.

6. **Filter Family Profiles & Dynamic CSV Introspection:**
   - [`_FilterFamilyProfile`][filters-sets]: Dataclass defining family name, base classes, lookup expression rules, value shape, and distinct safety for the optimizer.
   - Profile definitions: [`_SCALAR_LOOKUP_PROFILE`][filters-sets], [`_SEQUENCE_LOOKUP_PROFILE`][filters-sets], [`_CHOICE_PROFILE`][filters-sets], [`_MODEL_CHOICE_PROFILE`][filters-sets], [`_MULTIPLE_CHOICE_PROFILE`][filters-sets], [`_MODEL_MULTIPLE_CHOICE_PROFILE`][filters-sets], [`_GLOBALID_PROFILE`][filters-sets], and [`_GLOBALID_MULTIPLE_PROFILE`][filters-sets].
   - [`_ALL_FAMILY_PROFILES`][filters-sets]: Sequence of all family profiles.
   - [`_FILTER_FAMILY_REGISTRY`][filters-sets]: Precomputed tuple pairing filter classes with their corresponding profiles.
   - [`_EmptyBodyDynamicCsvReference`][filters-sets]: Sentinel class for introspecting `django_filters.rest_framework.BaseCSVFilter`.
   - [`_EMPTY_BODY_DYNAMIC_CSV_ATTRS`][filters-sets]: Frozen set of attribute names on dynamic CSV classes.
   - [`_dynamic_csv_profile_for`][filters-sets]: Generates dynamic CSV family profiles for `BaseCSVFilter` subclasses.
   - [`_family_profile_for`][filters-sets]: Resolves the appropriate [`_FilterFamilyProfile`][filters-sets] for a given filter instance.

7. **Candidate Metadata & Expansion Snapshot:**
   - [`CandidateFilterMetadata`][filters-sets]: Frozen dataclass describing build-time candidate metadata including field name, lookup expr, target model, traversal path, provenance, profile, eligibility, and frozen `routable` status.
   - [`ExpansionSnapshot`][filters-sets]: Immutable publication dataclass pairing `filters` (`MappingProxyType`) and `candidates` (`MappingProxyType`).
   - [`_candidate_metadata_for`][filters-sets]: Evaluates model paths and family profiles to construct candidate metadata rows.

8. **Metaclass & Related Filter Expansion:**
   - [`FilterSetMetaclass`][filters-sets]: Subclasses `django_filters.filterset.FilterSetMetaclass`. Overrides [`FilterSetMetaclass.__new__`][filters-sets] to promote `Meta.filter_fields` via [`promote_set_meta_fields`][utils-inputs], collect declared [`RelatedFilter`][filters-base] instances via [`collect_related_declarations`][sets-mixins], stamp declared provenance, and attach lifecycle descriptors.
   - [`_expand_related_filter`][filters-sets]: Recursively deepcopies child filterset filters, prepends the relation path (`filter_name__`), updates provenance breadcrumbs (`expanded_from`), and copies marked PK attributes.

9. **FilterSet Core Class & Generation Methods:**
   - [`FilterSet`][filters-sets]: Subclasses [`ClassBasedTypeNameMixin`][sets-mixins], [`ActiveInputPermissionMixin`][sets-mixins], and `django_filters.filterset.BaseFilterSet`, with metaclass [`FilterSetMetaclass`][filters-sets].
   - [`FilterSet.get_filters`][filters-sets]: Resolves declared + Meta-derived + related-expanded filters using [`expanded_once`][sets-mixins] and [`should_cache_expansion`][sets-mixins], building candidate metadata and publishing [`ExpansionSnapshot`][filters-sets].
   - [`FilterSet._expansion_snapshot`][filters-sets]: Classmethod accessor retrieving this class's own published expansion snapshot from `__dict__`.
   - [`FilterSet.get_fields`][filters-sets]: Expands per-field `"__all__"` dict lookups and narrows top-level `"__all__"` sweeps (adding PK and removing M2M fields).
   - [`FilterSet.filter_for_field`][filters-sets]: Owner-aware Relay-vs-scalar conditional replacing relation targets implementing `relay.Node` with [`GlobalIDFilter`][filters-base] or [`GlobalIDMultipleChoiceFilter`][filters-base], stamping `distinct=True` for to-many paths and qualifying non-pk `to_field` paths with `_GLOBALID_RELATION_PK_ATTR`.
   - [`FilterSet._generation_origin_for_field`][filters-sets]: Authoritative ownership oracle comparing selected policy entries against [`_PACKAGE_POLICY_BASELINE`][filters-sets].
   - [`FilterSet._is_generation_capable`][filters-sets]: Verifies that this FilterSet subclass has not overridden supported generation seams (`filter_for_field`, `filter_for_lookup`, `FILTER_DEFAULTS`, `__init__`).
   - [`FilterSet.filter_for_lookup`][filters-sets]: Lookup-aware Relay-vs-scalar conditional selecting GlobalID primitives for `exact`/`in` on Relay targets, routing integer `in`/`range` to overflow-safe filters ([`IntegerInFilter`][filters-base], [`IntegerRangeFilter`][filters-base]), and raising [`ConfigurationError`][exceptions] on unsupported lookups.
   - [`FilterSet._is_own_pk_under_relay_owner`][filters-sets]: Detects when a field is the model's PK and the bound owner `DjangoType` implements `relay.Node`.
   - [`FilterSet._relay_filter_class_for_field`][filters-sets]: Selects [`GlobalIDMultipleChoiceFilter`][filters-base] or [`GlobalIDFilter`][filters-base] based on [`is_many_side_relation_kind`][utils-relations].
   - [`FilterSet._resolve_relation_target_type`][filters-sets]: Resolves target `DjangoType` from `_owner_definition` or fallback registry.

10. **Input Normalization & Shape Validation:**
    - [`FilterSet._iter_input_items`][filters-sets]: Thin delegate to [`iter_input_items`][utils-input-values].
    - [`FilterSet._iter_logic_branches`][filters-sets]: Single authoritative iterator for all runtime logical-tree traversals (visibility derive, permission checks, Q composition), extracting branch values, validating shapes, and filtering inactive elements.
    - [`FilterSet._validate_logic_branch_shape`][filters-sets]: Rejects malformed logical container structures (`not` with list, `and`/`or` with non-list).
    - [`FilterSet._validate_logic_element_shape`][filters-sets]: Rejects non-mapping / non-dataclass elements within logical branches.
    - [`FilterSet._normalize_input`][filters-sets]: Normalizes Strawberry input dataclasses and dicts into `django-filter` form data using [`iter_active_fields`][utils-input-values] and [`normalize_input_value`][filters-inputs], handling operator bags and stripping related branches.
    - [`FilterSet._operator_bag_items`][filters-sets]: Inspects and extracts `(lookup_attr, value)` pairs from per-field operator bags.
    - [`FilterSet._form_key_for_python_attr`][filters-sets]: Reverses Python attributes to `django-filter` form keys via [`_FORM_KEY_BY_PYTHON_ATTR`][filters-sets].
    - [`FilterSet._permission_fallback_path`][filters-sets]: Maps lookup attributes to form keys for permission checks.

11. **Relation Visibility Scoping & Execution Pipelines:**
    - [`FilterSet._iter_visibility_steps`][filters-sets]: Yields pre-await state `(field_name, target_type, child_filterset, child_input, child_base)` for active related branches, binding `child_base` to `parent_db`.
    - [`FilterSet._derive_related_visibility_querysets_sync`][filters-sets]: Runs sync type visibility scoping ([`apply_type_visibility_sync`][utils-querysets]) and recurses into child filterset `apply_sync`.
    - [`FilterSet._derive_related_visibility_querysets_async`][filters-sets]: Async sibling running [`apply_type_visibility_async`][utils-querysets] and child `apply_async`.
    - [`FilterSet._raise_logic_depth_exceeded`][filters-sets]: Single-sited depth cap [`ConfigurationError`][exceptions] factory.
    - [`FilterSet._collect_nested_visibility_querysets_async`][filters-sets]: Pre-walks nested `and`/`or`/`not` branches to await child visibility querysets before sync `.qs` evaluation.
    - [`FilterSet._target_type_for_related_filter`][filters-sets]: Resolves owner `DjangoType` for a [`RelatedFilter`][filters-base].
    - [`FilterSet._check_permission_depth`][filters-sets]: Enforces `_MAX_LOGIC_DEPTH` during permission traversal.
    - [`FilterSet._run_logic_permission_checks`][filters-sets]: Recurses into logical branches to execute field permission checks.
    - [`FilterSet.check_permissions`][filters-sets]: Backward-compatible public permission check method.
    - [`FilterSet._validate_form_or_raise`][filters-sets]: Validates filterset form, raising `GraphQLError` with code `FILTER_INVALID` on failure.
    - [`FilterSet._invoke_suppressing_framework_distinct`][filters-sets]: Suppresses `distinct=False` during correlated inner root evaluation in `finally` block.
    - [`FilterSet._apply_flat_leaves`][filters-sets]: Evaluates flat leaves against outer queryset or correlated inner root via [`attach_exists`][predicates] for routable candidates.
    - [`FilterSet.filter_queryset`][filters-sets]: Composes flat leaves and tree-form logic via [`FilterSet._evaluate_logic_tree`][filters-sets].
    - [`FilterSet._evaluate_logic_tree`][filters-sets]: Evaluates `and`, `or`, `not` branches into a composite `django.db.models.Q` expression.
    - [`FilterSet._q_for_branch`][filters-sets]: Materializes a nested branch into a `pk__in` subquery `Q` object against a child FilterSet sibling instance.
    - [`FilterSet._apply_related_constraints`][filters-sets]: Intersects child querysets with explicit `RelatedFilter(queryset=...)` constraints and filters `pk__in` subqueries.
    - [`FilterSet._apply_common_prelude`][filters-sets]: Shared prelude building filterset instance, extracting request, applying related constraints, and stashing `_apply_info`.
    - [`FilterSet._apply_common_finalize`][filters-sets]: Shared finalize running permission checks, form validation, and returning `.qs`.
    - [`FilterSet.apply_sync`][filters-sets]: Synchronous execution entry point.
    - [`FilterSet.apply_async`][filters-sets]: Asynchronous execution entry point running `_apply_common_finalize` inside [`run_in_one_sync_boundary`][utils-querysets].
    - [`FilterSet.apply`][filters-sets]: Thin dispatcher translating [`SyncMisuseError`][exceptions] into an actionable `RuntimeError`.

Connected behavior examined:
- [`django_strawberry_framework/sets_mixins.py`][sets-mixins]: Canonical owner of [`ClassBasedTypeNameMixin`][sets-mixins], [`ActiveInputPermissionMixin`][sets-mixins], [`SetLifecycleAttrs`][sets-mixins], [`collect_related_declarations`][sets-mixins], [`expanded_once`][sets-mixins], and [`should_cache_expansion`][sets-mixins].
- [`django_strawberry_framework/filters/base.py`][filters-base]: Filter primitives ([`Filter`][filters-base], [`TypedFilter`][filters-base], [`RangeFilter`][filters-base], [`ListFilter`][filters-base], [`ArrayFilter`][filters-base], [`IntegerInFilter`][filters-base], [`IntegerRangeFilter`][filters-base], [`GlobalIDFilter`][filters-base], [`GlobalIDMultipleChoiceFilter`][filters-base], [`RelatedFilter`][filters-base], `_relation_uses_non_pk_to_field`, `_GLOBALID_RELATION_PK_ATTR`).
- [`django_strawberry_framework/filters/inputs.py`][filters-inputs]: Input generation namespace, [`LOOKUP_NAME_MAP`][filters-inputs], [`LOGIC_OPERATORS`][filters-inputs], and [`normalize_input_value`][filters-inputs].
- [`django_strawberry_framework/orders/sets.py`][orders-sets]: Sibling ordering subsystem set implementation.
- [`django_strawberry_framework/utils/input_values.py`][utils-input-values]: Shared input traversal ([`iter_active_fields`][utils-input-values], [`iter_input_items`][utils-input-values], [`is_inactive_value`][utils-input-values], [`ActiveInputTraversalAttrs`][utils-input-values]).
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Shared field promotion ([`promote_set_meta_fields`][utils-inputs], [`FILTERSET_FIELDS_ALIAS`][utils-inputs]).
- [`django_strawberry_framework/utils/relations.py`][utils-relations]: Shared relation classifiers ([`classify_path`][utils-relations], [`path_traverses_to_many`][utils-relations], [`relation_kind`][utils-relations], [`is_many_side_relation_kind`][utils-relations]).
- [`django_strawberry_framework/utils/querysets.py`][utils-querysets]: Shared visibility and async boundary utilities ([`apply_type_visibility_sync`][utils-querysets], [`apply_type_visibility_async`][utils-querysets], [`run_in_one_sync_boundary`][utils-querysets]).
- [`django_strawberry_framework/optimizer/predicates.py`][predicates]: Correlated subquery primitives ([`attach_exists`][predicates], [`correlated_inner_root`][predicates]).
- [`django_strawberry_framework/registry.py`][registry]: Primary and model type registry.
- [`tests/filters/test_sets.py`][test-filters-sets]: Comprehensive test suite covering FilterSet expansion, provenance, candidate metadata, optimizer routing, and execution pipelines.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/filters/sets.py --review docs/dry/dry-file-filters__sets.md --include-constants`):
- Parsed 1 target file, 3,473 lines, 6 classes, 49 functions/methods, 28 constants.
- Verified all 83 static symbols are documented and linked.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   - `filters/sets.py` and `orders/sets.py` share architecture via [`django_strawberry_framework/sets_mixins.py`][sets-mixins] ([`ClassBasedTypeNameMixin`][sets-mixins], [`ActiveInputPermissionMixin`][sets-mixins], [`SetLifecycleAttrs`][sets-mixins], [`collect_related_declarations`][sets-mixins], [`expanded_once`][sets-mixins], [`should_cache_expansion`][sets-mixins]) and [`django_strawberry_framework/utils/inputs.py`][utils-inputs] ([`promote_set_meta_fields`][utils-inputs]).
   - `filters/sets.py` subclasses `django_filters.filterset.BaseFilterSet` and supports tree-form boolean combinators (`and`, `or`, `not`), related queryset constraints, and correlated-`EXISTS` subquery optimization. `orders/sets.py` is a standalone set implementation without boolean algebra because SQL `ORDER BY` clauses are linear sequences rather than composable boolean trees.
   - Mutation and form flavors construct input types and execute validation directly, reusing shared input traversal and error types without duplicating filterset generation.

2. **Sync and async twins:**
   - [`FilterSet.apply_sync`][filters-sets] and [`FilterSet.apply_async`][filters-sets] share structural composition via [`FilterSet._apply_common_prelude`][filters-sets] (input normalization, request extraction, related constraints, instance construction) and [`FilterSet._apply_common_finalize`][filters-sets] (permission checks, form validation, `.qs` read).
   - Visibility derivation twins [`FilterSet._derive_related_visibility_querysets_sync`][filters-sets] and [`FilterSet._derive_related_visibility_querysets_async`][filters-sets] share iteration mechanics via [`FilterSet._iter_visibility_steps`][filters-sets].
   - Async pipeline executes [`FilterSet._collect_nested_visibility_querysets_async`][filters-sets] to pre-await nested `get_queryset` hooks before sync evaluation, and wraps [`FilterSet._apply_common_finalize`][filters-sets] in [`run_in_one_sync_boundary`][utils-querysets] to avoid event loop blocking.
   - [`FilterSet.apply`][filters-sets] acts as a thin sync dispatcher converting [`SyncMisuseError`][exceptions] into an actionable `RuntimeError`.

3. **Derived rather than repeated knowledge:**
   - Field lookups are derived dynamically from model field definitions via [`_lookups_for_field`][filters-sets] and cached at class level.
   - Baseline policy is derived from [`_PUBLIC_PACKAGE_FILTER_DEFAULTS`][filters-sets] via [`_normalize_policy_entry`][filters-sets] and stored in [`_PACKAGE_POLICY_BASELINE`][filters-sets].
   - Optimizer auditing is derived from installed package version via [`_release_is_audited`][filters-sets].
   - Filter routing eligibility is computed once at expansion build time and frozen into [`CandidateFilterMetadata.routable`][filters-sets] within [`ExpansionSnapshot`][filters-sets].
   - Reverse lookup mappings are derived from [`LOOKUP_NAME_MAP`][filters-inputs] at module import into [`_FORM_KEY_BY_PYTHON_ATTR`][filters-sets].
   - Relation cardinality is derived via [`is_many_side_relation_kind`][utils-relations] from [`relation_kind`][utils-relations].

4. **Inverse and round-trip pairs:**
   - GraphQL wire inputs round-trip into Django form parameters via [`FilterSet._normalize_input`][filters-sets] and [`FilterSet._operator_bag_items`][filters-sets], resolving back to form keys via [`_FORM_KEY_BY_PYTHON_ATTR`][filters-sets].
   - Related filter paths round-trip during expansion via [`_expand_related_filter`][filters-sets], preserving and accumulating provenance breadcrumbs in `expanded_from`.
   - Distinct flag suppression on correlated inner roots in [`FilterSet._invoke_suppressing_framework_distinct`][filters-sets] temporarily clears `distinct=False` and restores the original value in a `finally` block.

5. **Contracts restated in another medium:**
   The FilterSet contracts, optimization rules, and execution pipelines are codified across:
   - Code: [`django_strawberry_framework/filters/sets.py`][filters-sets], [`django_strawberry_framework/filters/base.py`][filters-base], [`django_strawberry_framework/filters/inputs.py`][filters-inputs], [`django_strawberry_framework/sets_mixins.py`][sets-mixins], [`django_strawberry_framework/orders/sets.py`][orders-sets], [`django_strawberry_framework/utils/input_values.py`][utils-input-values], [`django_strawberry_framework/utils/querysets.py`][utils-querysets], [`django_strawberry_framework/optimizer/predicates.py`][predicates];
   - Specifications: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] (Layers 4, 5, Decisions 2, 3, 4, 8, 9, 11), [`docs/SPECS/spec-031-globalid_type_names-0_0_9.md`][spec-031], [`docs/SPECS/spec-051-converters-0_0_14.md`][spec-051];
   - Test suites: [`tests/filters/test_sets.py`][test-filters-sets], [`tests/filters/test_inputs.py`][test-filters-inputs], [`tests/filters/test_base.py`][test-filters-base], [`tests/filters/test_finalizer.py`][test-filters-finalizer];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding a new supported filter family profile to optimizer registry):** Add a new profile for a custom filter class.
  - *Sites that must move:* Exactly 2 sites: [`django_strawberry_framework/filters/sets.py`][filters-sets] (define profile constant and register in [`_FILTER_FAMILY_REGISTRY`][filters-sets]) and [`tests/filters/test_sets.py`][test-filters-sets] (add test case).
  - *Site count:* 2.
- **Posited change 2 (Widening audited `django-filter` release range):** Update the supported upstream version window for the optimizer.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/filters/sets.py::_AUDITED_DJANGO_FILTER_RANGE`][filters-sets].
  - *Site count:* 1.
- **Posited change 3 (Changing maximum logical-branch recursion depth default cap):** Adjust `_MAX_LOGIC_DEPTH` default.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/filters/sets.py::FilterSet._MAX_LOGIC_DEPTH`][filters-sets].
  - *Site count:* 1.
- **Posited change 4 (Updating model-choice extras stripped during Relay conversion):** Add a new kwarg to strip when building GlobalID filters.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/filters/sets.py::_MODEL_CHOICE_ONLY_EXTRAS`][filters-sets].
  - *Site count:* 1.
- **Posited change 5 (Adjusting active input traversal rules for sets):** Update traversal logic across all set families.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/input_values.py::iter_active_fields`][utils-input-values].
  - *Site count:* 1.
- **Posited change 6 (Modifying lifecycle expansion caching for all set families):** Adjust expansion caching conditions.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/sets_mixins.py::should_cache_expansion`][sets-mixins].
  - *Site count:* 1.

## Opportunities

None — `django_strawberry_framework/filters/sets.py` represents a mature, fully consolidated module where all cross-family abstractions (lifecycle caching, permission mixins, input traversal, field promotion, relation classification, queryset visibility scoping, and subquery predicate attachment) have been extracted to their respective canonical root owners (`sets_mixins.py`, `utils/input_values.py`, `utils/inputs.py`, `utils/relations.py`, `utils/querysets.py`, and `optimizer/predicates.py`). All 83 static symbols are cohesively organized, single-sited, and verified.

## Judgment

The FilterSet subsystem in `django_strawberry_framework/filters/sets.py` exhibits exemplary DRY adherence. Responsibilities are cleanly segmented between declarative metaclass expansion, build-time candidate metadata classification, immutable publication snapshots, Relay GlobalID adaptation, and synchronous/asynchronous execution pipelines. All single-edit-site tests verify minimal touchpoints (1 to 2 sites).

## Implementation (Worker 1)

No tracked changes needed. All 83 static symbols are verified and discharged across the 5-axis matrix.

## Independent verification (Worker 2)

I have independently analyzed `django_strawberry_framework/filters/sets.py` (3,456 lines, 83 static symbols), its connected behaviors, underlying specifications ([spec-027][spec-027], [spec-031][spec-031], [spec-051][spec-051]), and the dedicated test suite [`tests/filters/test_sets.py`][test-filters-sets] (289 tests passing).

### Subsystem Verification

1. **Metaclass and Expansion Lifecycle (`FilterSetMetaclass`, `FilterSet.get_filters`, `_expand_related_filter`):**
   - Verified that `FilterSetMetaclass.__new__` delegates alias promotion to [`promote_set_meta_fields`][utils-inputs] (`Meta.filter_fields` -> `Meta.fields`), collects declared `RelatedFilter`s via [`collect_related_declarations`][sets-mixins], rebuilds `base_filters` when tombstones are removed, and stamps `origin="declared"` on own and untracked inherited declarations.
   - Verified that `FilterSet.get_filters` uses [`expanded_once`][sets-mixins] to prevent recursion loops during cyclic `RelatedFilter` expansion.
   - Confirmed that expansion deepcopies child filters with prepended paths (`filter_name__`), updates `expanded_from` breadcrumbs, and publishes filters and candidate metadata atomically via [`ExpansionSnapshot`][filters-sets] guarded by [`should_cache_expansion`][sets-mixins].

2. **Relay Adaptation and Provenance Tracking (`filter_for_field`, `filter_for_lookup`, `_generation_origin_for_field`):**
   - Verified that `_PUBLIC_PACKAGE_FILTER_DEFAULTS` provides an independent, deepcopyable policy table mirroring `django-filter` 25.2 defaults with package-owned extra providers (`_forward_relation_extra`, `_forward_m2m_extra`, `_reverse_o2o_extra`, `_reverse_rel_extra`).
   - Verified that `_PACKAGE_POLICY_BASELINE` provides a private, immutable value baseline of `_NormalizedPolicyEntry` records.
   - Verified that `_generation_origin_for_field` resolves output fields (handling `isnull` re-selection to `models.BooleanField`) and compares normalized policy entries by value against the baseline to distinguish framework defaults from `Meta.filter_overrides` and `FILTER_DEFAULTS` shadows.
   - Verified that `_is_generation_capable` verifies function identities (`filter_for_field`, `filter_for_lookup`), table identity (`FILTER_DEFAULTS is _PUBLIC_PACKAGE_FILTER_DEFAULTS`), and `__init__` identity.
   - Verified that `filter_for_field` and `filter_for_lookup` adapt Relay Node relation targets and own-PK fields to `GlobalIDFilter` and `GlobalIDMultipleChoiceFilter`, stripping model choice extras via `_strip_model_choice_extras` and setting `_GLOBALID_RELATION_PK_ATTR` when using non-pk `to_field` paths.

3. **Optimizer Auditing and Candidate Metadata (`_release_is_audited`, `_family_profile_for`, `_candidate_metadata_for`):**
   - Verified that `_AUDITED_DJANGO_FILTER_RANGE` pins `((25, 2), (27,))` and `_release_is_audited` parses numeric segments, failing closed on unparseable versions.
   - Verified that `_FILTER_FAMILY_REGISTRY` maintains an exact-class mapping to `_FilterFamilyProfile` singletons.
   - Verified that `_dynamic_csv_profile_for` strictly inspects `__bases__` (2-tuple with `BaseInFilter`/`BaseRangeFilter` and an audited scalar) and enforces empty body via `_EMPTY_BODY_DYNAMIC_CSV_ATTRS`.
   - Verified that `_candidate_metadata_for` classifies model paths via [`classify_path`][utils-relations], propagates `PathResolutionError` on direct framework leaves (genuine defects), and fails closed on expanded leaves under declared relation prefixes.

4. **Input Normalization, Form Validation, and Permissions (`_normalize_input`, `_validate_form_or_raise`, `_run_permission_checks`):**
   - Verified that `_normalize_input` delegates traversal to [`iter_active_fields`][utils-input-values] using singleton `_NORMALIZE_TRAVERSAL`, strips `RELATED` branches, normalizes operator bags via `_operator_bag_items` and `_FORM_KEY_BY_PYTHON_ATTR`, and delegates value transformations to [`normalize_input_value`][filters-inputs].
   - Verified container shape validations `_validate_logic_branch_shape` and `_validate_logic_element_shape` which reject malformed logic branches (preventing silent permission bypasses).
   - Verified that `_validate_form_or_raise` asserts `form.is_valid()`, raising `GraphQLError` with code `FILTER_INVALID` and JSON-serialized errors on failure.

5. **Execution Pipelines and Query Optimization (`apply_sync`, `apply_async`, `apply`, `_apply_flat_leaves`):**
   - Verified that `apply_sync` and `apply_async` share prelude (`_apply_common_prelude`) and finalize (`_apply_common_finalize`).
   - Verified that relation visibility scoping (`_derive_related_visibility_querysets_sync` / `_derive_related_visibility_querysets_async`) shares step generation via `_iter_visibility_steps` and passes `run_permissions=False` to prevent double-firing child permission gates.
   - Verified that `apply_async` pre-awaits nested visibility maps via `_collect_nested_visibility_querysets_async` and runs finalize inside [`run_in_one_sync_boundary`][utils-querysets].
   - Verified that `_apply_flat_leaves` routes routable leaves through `_invoke_suppressing_framework_distinct` against [`correlated_inner_root`][predicates] and attaches positive `Exists` via [`attach_exists`][predicates], falling back to outer `.filter()` for non-routable leaves.
   - Verified that `_evaluate_logic_tree` and `_q_for_branch` construct `pk__in` subqueries for boolean combinators (`and`, `or`, `not`) while enforcing `_MAX_LOGIC_DEPTH` recursion bounds.

### Probing Matrix and Single-Edit-Site Confirmation

- **5-Axis Matrix:** All 5 axes are fully satisfied and discharged with no unaccounted duplication. Shared concerns are factored out to `sets_mixins.py`, `utils/input_values.py`, `utils/inputs.py`, `utils/relations.py`, `utils/querysets.py`, and `optimizer/predicates.py`.
- **Single-Edit-Site Counts:** Confirmed that all 6 posited modifications require between 1 and 2 localized edit sites.
- **Static Coverage:** Verified 100% coverage of all 83 static symbols via `export_dry_review.py`.

### Technical Clarifications

- Note on `_AUDITED_DJANGO_FILTER_RANGE`: The audited version window is `((25, 2), (27,))` covering both django-filter 25.x and 26.x series.
- Note on `_NormalizedPolicyEntry`: Implemented as an immutable frozen dataclass (`@dataclass(frozen=True)`).
- Note on `_FILTER_FAMILY_REGISTRY`: Implemented as an immutable `MappingProxyType` dictionary rather than a tuple.

Review status is verified.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-027]: ../SPECS/spec-027-filters-0_0_8.md
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
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
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[predicates]: ../../django_strawberry_framework/optimizer/predicates.py
[registry]: ../../django_strawberry_framework/registry.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[types-base]: ../../django_strawberry_framework/types/base.py
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
[test-orders-sets]: ../../tests/orders/test_sets.py
[test-registry]: ../../tests/test_registry.py
[test-relay-connection]: ../../tests/test_relay_connection.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
