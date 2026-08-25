# DRY review: `django_strawberry_framework/filters/base.py`

Status: verified

## System trace

`django_strawberry_framework/filters/base.py` defines the foundational filter primitives, custom field/widget classes, range/list/array normalization helpers, integer overflow protection filters, Relay GlobalID decoding/validation machinery, and the cross-relation traversal filter [`RelatedFilter`][filters-base] ([spec-027][spec-027], [spec-031][spec-031]). It comprises Layer 1 and Layer 2 of the filtering subsystem pipeline. It owns the following responsibilities:

1. **Subsystem Base Filter Hierarchy & Re-export:**
   - [`Filter`][filters-base]: Re-exported directly from `django_filters.Filter` to provide a unified import surface for consumers.
   - [`TypedFilter`][filters-base]: Subclasses `django_filters.Filter`. Serves as the base marker class for [`ArrayFilter`][filters-base], [`RangeFilter`][filters-base], and [`ListFilter`][filters-base]. Ports `graphene_django/filter/filters/typed_filter.py` with Graphene-specific `_input_type` constructor argument dropped (Strawberry input annotations are derived downstream by `convert_filter_to_input_annotation` in [`filters/inputs.py`][filters-inputs]).

2. **Array Filtering (PostgreSQL `ArrayField` Support):**
   - [`_EmptyListAwareFilterMethod`][filters-base]: Subclasses `django_filters.filters.FilterMethod`. Custom filter method wrapper whose `_EmptyListAwareFilterMethod.__call__` treats an empty list `[]` as a real filter value rather than short-circuiting to `EMPTY_VALUES` (only `None` short-circuits to the unfiltered queryset).
   - [`_install_empty_list_aware_method`][filters-base]: Single-sited helper to install empty-list-aware method classes on [`TypedFilter`][filters-base] instances when consumer-supplied `method=` callables are provided.
   - [`ArrayFilterMethod`][filters-base]: Subclasses [`_EmptyListAwareFilterMethod`][filters-base] specifically for [`ArrayFilter`][filters-base].
   - [`ArrayFilter`][filters-base]: Subclasses [`TypedFilter`][filters-base]. Handles PostgreSQL `ArrayField` filtering. The `ArrayFilter.method` property setter installs [`ArrayFilterMethod`][filters-base]. The `ArrayFilter.filter` method treats `[]` as a real value (evaluating against `lookup_expr` such as `__contains`, `__overlap`, `__contained_by`) and delegates to [`_apply_lookup_predicate`][filters-base].

3. **Range Filtering & Bounds Validation:**
   - [`validate_range`][filters-base]: Form validator function enforcing that input sequences are `list` or `tuple` instances with length exactly equal to 2, raising `ValidationError(code="invalid")` on length mismatch.
   - [`RangeField`][filters-base]: Subclasses `django.forms.Field` with `default_validators = [validate_range]` and `empty_values = [None]`.
   - [`RangeFilter`][filters-base]: Subclasses [`TypedFilter`][filters-base], binding `field_class = RangeField`.

4. **List Filtering & Empty-Set Semantics:**
   - [`_match_none_queryset`][filters-base]: Shared restrictive-empty helper returning `qs.none()` (or `qs` when `filter_instance.exclude` is `True`) to prevent restrictive empty-list filters from silently widening into unconstrained passes.
   - [`ListFilterMethod`][filters-base]: Subclasses [`_EmptyListAwareFilterMethod`][filters-base] specifically for [`ListFilter`][filters-base].
   - [`ListFilter`][filters-base]: Subclasses [`TypedFilter`][filters-base]. The `ListFilter.method` property setter installs [`ListFilterMethod`][filters-base]. The `ListFilter.filter` method intercepts empty-list inputs (`len(value) == 0`) and returns [`_match_none_queryset`][filters-base].

5. **Integer Overflow Protection (`__in` and `__range`):**
   - [`_coerce_int_in_members`][filters-base]: Coerces each candidate member using [`django_strawberry_framework/utils/querysets.py::coerce_field_value_or_none`][utils-querysets], dropping uncoercible/out-of-range elements so backend integer overflow errors (e.g. SQLite `OverflowError`) are avoided.
   - [`IntegerInFilter`][filters-base]: Subclasses `(django_filters.filters.BaseInFilter, django_filters.NumberFilter)`. The `IntegerInFilter.filter` method applies [`_coerce_int_in_members`][filters-base], returning [`_match_none_queryset`][filters-base] if a non-empty list has all elements dropped by coercion.
   - [`IntegerRangeFilter`][filters-base]: Subclasses `(django_filters.filters.BaseRangeFilter, django_filters.NumberFilter)`. The `IntegerRangeFilter.filter` method decomposes the two-bound range into a single compound predicate `{field__gte: start, field__lte: end}` via [`_apply_lookups`][filters-base] instead of a raw SQL `BETWEEN` parameter binding, delegating range evaluation to Django's range-aware integer lookup backend.

6. **Lookup & Predicate Application Primitives:**
   - [`_apply_lookups`][filters-base]: Applies `qs.distinct()` if `filter_instance.distinct` is truthy and applies lookups via `filter_instance.get_method(qs)(**lookups)`.
   - [`_apply_lookup_predicate`][filters-base]: Builds `{f"{field}__{filter_instance.lookup_expr}": value}` (with optional `field_name` override) and invokes [`_apply_lookups`][filters-base] in a single predicate.

7. **GlobalID Filtering & Strategy Validation:**
   - Constants: [`FRAMEWORK_GLOBALID_STRATEGIES`][filters-base] (`MODEL_LABEL_STRATEGIES | TYPE_NAME_STRATEGIES`), [`ENCODE_ONLY_GLOBALID_STRATEGIES`][filters-base] (`frozenset({"callable", "custom"})`), and [`_GLOBALID_RELATION_PK_ATTR`][filters-base] (`"_dst_globalid_relation_pk"`).
   - Relation Non-PK Detection & Marking: [`_relation_uses_non_pk_to_field`][filters-base] detects concrete forward FK/O2O relations joined on non-pk `to_field` columns. [`_marked_pk_field_name`][filters-base] checks `_GLOBALID_RELATION_PK_ATTR` on a filter instance and dynamically derives `f"{field_name}__pk"` at filter time from the live `field_name`.
   - Target Definition Resolution: [`_target_definition_for`][filters-base] retrieves the parent FilterSet's `_owner_definition` and delegates to [`resolve_globalid_target_definition`][filters-base]. [`resolve_globalid_target_definition`][filters-base] iteratively parses `__`-separated relation segments to resolve terminal target `DjangoTypeDefinition` instances for own-PK and multi-hop relation paths.
   - Strategy Validation & Error Handling: [`_accepted_globalid_type_names`][filters-base] computes valid wire `type_name` payloads based on `definition.effective_globalid_strategy`. [`_globalid_multiple_choice_values`][filters-base] validates list/tuple containers. [`_decode_and_validate_global_id`][filters-base] decodes `strawberry.relay.GlobalID`, validates strategy compatibility (rejecting encode-only or unfinalized targets with code `"GLOBALID_UNVALIDATABLE"`), validates type names, rejects empty `node_id` strings, and coerces node IDs against the target model PK field via [`coerce_field_value_or_none`][utils-querysets].
   - Scalar & Multi-Choice GlobalID Filters:
     - [`GlobalIDFilter`][filters-base]: Subclasses `django_filters.Filter`. The `GlobalIDFilter.filter` method decodes and validates the GlobalID scalar, qualifies non-pk `to_field` relations via [`_marked_pk_field_name`][filters-base], and applies the predicate.
     - [`_AbsentGlobalIDMultipleChoiceWidget`][filters-base]: Subclasses `django.forms.SelectMultiple`. The `_AbsentGlobalIDMultipleChoiceWidget.value_from_datadict` method preserves omitted form keys as `None` rather than `[]`.
     - [`_GlobalIDMultipleChoiceField`][filters-base]: Subclasses `django.forms.MultipleChoiceField`. Overrides `_GlobalIDMultipleChoiceField.valid_value` to skip static choice checks, and `_GlobalIDMultipleChoiceField.to_python` / `_GlobalIDMultipleChoiceField.validate` to preserve omission `None`.
     - [`GlobalIDMultipleChoiceFilter`][filters-base]: Subclasses `django_filters.MultipleChoiceFilter`. Uses `field_class = _GlobalIDMultipleChoiceField`. The `GlobalIDMultipleChoiceFilter.filter` method validates the container, matches none on `[]`, validates each item with index, and for `lookup_expr == "in"` applies the entire list in one predicate via [`_apply_lookup_predicate`][filters-base].

8. **Related Filter Traversal & Lifecycle:**
   - [`LazyRelatedClassMixin`][filters-base]: Re-exported from [`django_strawberry_framework/sets_mixins.py`][sets-mixins].
   - [`RelatedFilter`][filters-base]: Subclasses `(RelatedSetTargetMixin, django_filters.ModelChoiceFilter)`. Rejects legacy `lookups=` kwargs in `RelatedFilter.__init__`. Exposes `RelatedFilter.bind_filterset` (calling `_bind_owner`), the lazy `django_strawberry_framework/filters/base.py::RelatedFilter.filterset` property getter and setter (delegating to `_resolved_target` / `_set_target`), and `RelatedFilter.get_queryset` (deriving `target._meta.model._default_manager.all()` when no explicit queryset was provided).

Connected behavior examined:
- [`django_strawberry_framework/sets_mixins.py`][sets-mixins]: Canonical owner of `RelatedSetTargetMixin`, `LazyRelatedClassMixin`, `ClassBasedTypeNameMixin`, and set lifecycle descriptors.
- [`django_strawberry_framework/filters/sets.py`][filters-sets]: Metaclass collection, `_relation_uses_non_pk_to_field` stamping of `_GLOBALID_RELATION_PK_ATTR`, and `FilterSet` expansion.
- [`django_strawberry_framework/filters/inputs.py`][filters-inputs]: Input dataclass generation and runtime filter argument normalizers.
- [`django_strawberry_framework/filters/factories.py`][filters-factories]: BFS factory `FilterArgumentsFactory`.
- [`django_strawberry_framework/orders/base.py`][orders-base]: Sibling ordering subsystem primitive `RelatedOrder`.
- [`django_strawberry_framework/types/relay.py`][types-relay]: Relay strategy memberships (`MODEL_LABEL_STRATEGIES`, `TYPE_NAME_STRATEGIES`) and GlobalID encoding/decoding.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Phase 2.5 finalizer executing `_audit_globalid_filter_strategies` via [`resolve_globalid_target_definition`][filters-base].
- [`django_strawberry_framework/utils/querysets.py`][utils-querysets]: Shared `coerce_field_value_or_none` coercion primitive.
- [`tests/filters/test_base.py`][test-filters-base]: Test suite covering all filter primitives, validators, GlobalID decode edge cases, and multi-hop relation traversal.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/filters/base.py --review docs/dry/dry-file-filters__base.md --include-constants`):
- Parsed 1 target file, 1009 lines, 13 classes, 19 functions/methods, 3 module-level constants ([`FRAMEWORK_GLOBALID_STRATEGIES`][filters-base], [`ENCODE_ONLY_GLOBALID_STRATEGIES`][filters-base], [`_GLOBALID_RELATION_PK_ATTR`][filters-base]).
- Verified symbol coverage and reverse imports across production code (`filters/sets.py`, `filters/inputs.py`, `types/finalizer.py`, `types/relay.py`) and test suites (`tests/filters/test_base.py`, `tests/filters/test_sets.py`, `tests/filters/test_inputs.py`, `tests/filters/test_finalizer.py`).

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `filters/base.py` and `orders/base.py` are parallel Layer 1 primitive modules ([spec-027][spec-027], [spec-028][spec-028]). Both `RelatedFilter` and `RelatedOrder` derive from [`django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin`][sets-mixins], parameterizing `_target_attr` and `_owner_attr` while delegating `_bind_owner`, `_resolved_target`, and `_set_target` to the shared base. `orders/base.py` does not duplicate range, array, or GlobalID filtering primitives because SQL ordering operates on column expressions rather than multi-operator input bags. Form and mutation flavors construct inputs directly while sharing `coerce_field_value_or_none` from [`django_strawberry_framework/utils/querysets.py`][utils-querysets].
2. **Sync and async twins:**
   Zero duplication. `filters/base.py` primitives define declarative filter specifications, form fields, validation functions, and QuerySet predicate construction (`.filter(**lookups)`). They are completely agnostic to whether the downstream QuerySet evaluation is executed synchronously via `apply_type_visibility_sync` or asynchronously via `apply_type_visibility_async`.
3. **Derived rather than repeated knowledge:**
   - `resolve_globalid_target_definition` derives the target `DjangoTypeDefinition` for a filter instance by iteratively walking relation segments. Both runtime filter execution (`_target_definition_for`) and build-time schema validation (`types/finalizer.py::_audit_globalid_filter_strategies`) share this single derivation function.
   - `_accepted_globalid_type_names` derives accepted wire payloads directly from `definition.effective_globalid_strategy` using `MODEL_LABEL_STRATEGIES` and `TYPE_NAME_STRATEGIES` imported from [`types/relay.py`][types-relay].
   - `_marked_pk_field_name` derives `f"{self.field_name}__pk"` dynamically from the live `field_name` at filter evaluation time, ensuring immunity to relation prefix rebasing during `_expand_related_filter`.
   - `RelatedFilter.get_queryset` derives fallback querysets dynamically from `target._meta.model._default_manager.all()`.
4. **Inverse and round-trip pairs:**
   - GlobalID wire format round-trip: GlobalIDs emitted by `types/relay.py` under framework strategies round-trip through `_decode_and_validate_global_id`, while encode-only strategies (`callable`, `custom`) are rejected with `GLOBALID_UNVALIDATABLE`.
   - Form data / query dict round-trip: `_AbsentGlobalIDMultipleChoiceWidget` and `_GlobalIDMultipleChoiceField` preserve key omission (`None`) vs explicit empty list (`[]`) through `value_from_datadict` and `to_python`.
   - QuerySet predicate complement: `_match_none_queryset` handles both positive filtering (`qs.none()`) and complement filtering under `exclude=True` (`qs`). Integer range decomposition maintains inclusive bounds semantics across filter (`__gte` + `__lte`) and exclude (`NOT (__gte AND __lte)`).
5. **Contracts restated in another medium:**
   The filter primitive and GlobalID validation contracts are codified across:
   - Code: [`django_strawberry_framework/filters/base.py`][filters-base], [`django_strawberry_framework/filters/sets.py`][filters-sets], [`django_strawberry_framework/filters/inputs.py`][filters-inputs], [`django_strawberry_framework/sets_mixins.py`][sets-mixins], [`django_strawberry_framework/types/relay.py`][types-relay], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/utils/querysets.py`][utils-querysets];
   - Specifications: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] (Decisions 2, 3, 4), [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028], [`docs/SPECS/spec-031-globalid_type_names-0_0_9.md`][spec-031] (Decision 13);
   - Test suites: [`tests/filters/test_base.py`][test-filters-base], [`tests/filters/test_sets.py`][test-filters-sets], [`tests/filters/test_inputs.py`][test-filters-inputs], [`tests/filters/test_finalizer.py`][test-filters-finalizer], [`tests/test_relay_connection.py`][test-relay-connection];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding a new empty-list-aware filter primitive, e.g. `SetFilter`):** Introduce a new empty-list-aware filter class.
  - *Sites that must move:* Exactly 2 sites: [`django_strawberry_framework/filters/base.py`][filters-base] (define `SetFilterMethod` and `SetFilter` using `_install_empty_list_aware_method` and `_match_none_queryset`) and [`django_strawberry_framework/filters/__init__.py`][filters-init] (export in `__all__`).
  - *Site count:* 2.
- **Posited change 2 (Altering GlobalID validation error codes or messages):** Update the error message or code for malformed GlobalID inputs.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/filters/base.py::_decode_and_validate_global_id`][filters-base].
  - *Site count:* 1.
- **Posited change 3 (Modifying multi-hop relation target definition resolution):** Adjust how relation paths resolve target `DjangoTypeDefinition` instances for GlobalID filtering.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/filters/base.py::resolve_globalid_target_definition`][filters-base] (automatically updating both runtime evaluation and finalizer build-time audit).
  - *Site count:* 1.
- **Posited change 4 (Updating integer field range coercion boundaries):** Change how integer column values are coerced and bounds-checked.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/querysets.py::coerce_field_value_or_none`][utils-querysets] (automatically updating `_coerce_int_in_members`, `GlobalIDFilter`, `relay.py`, and write values).
  - *Site count:* 1.

### Rejected candidates

1. **Moving `resolve_globalid_target_definition` into `types/finalizer.py`:**
   - Disproved. `resolve_globalid_target_definition` is required at runtime during query execution by `_target_definition_for` on every GlobalID filter evaluation. Placing it in `filters/base.py` keeps runtime filter evaluation self-contained while allowing `types/finalizer.py` to import and reuse the exact same function during build-time schema audits without circular imports (`filters -> types` is the safe import direction).
2. **Duplicating owner-bind and lazy resolution between `RelatedFilter` and `RelatedOrder`:**
   - Disproved. Both classes inherit from [`django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin`][sets-mixins], parameterizing `_target_attr` and `_owner_attr`. Centralizing this lifecycle in `sets_mixins.py` prevents policy drift across set families.
3. **Inlining `coerce_field_value_or_none` in `_coerce_int_in_members`:**
   - Disproved. Field coercion logic is shared across integer in-filters, GlobalID validation, Relay node refetching, and mutation write values. Centralizing coercion in [`django_strawberry_framework/utils/querysets.py`][utils-querysets] guarantees identical boundary and overflow protections across all subsystems.

## Opportunities

None — `django_strawberry_framework/filters/base.py` is a fully consolidated, 1009-line foundational module. All shared filter behaviors (`_EmptyListAwareFilterMethod`, `_install_empty_list_aware_method`, `_apply_lookups`, `_apply_lookup_predicate`, `_match_none_queryset`, `_marked_pk_field_name`, `resolve_globalid_target_definition`) are single-sited at their root owners, set-family lifecycle is delegated to `sets_mixins.py`, and data coercion delegates to `utils/querysets.py`.

## Judgment

Zero-edit review. `django_strawberry_framework/filters/base.py` contains zero duplicate policy or unowned invariants. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 or 2 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/filters/base.py --review docs/dry/dry-file-filters__base.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification conducted by Worker 2 for `django_strawberry_framework/filters/base.py`.

### Independent behavioral trace and boundary challenge

1. **Foundational Filter Hierarchy & Parity Primitives:**
   - Verified that [`Filter`][filters-base] is cleanly re-exported from `django_filters.Filter`, and [`TypedFilter`][filters-base] correctly drops Graphene `_input_type` dependencies in favor of Strawberry dynamic annotation conversion.
   - Verified that [`ArrayFilter`][filters-base] and [`ListFilter`][filters-base] share [`_EmptyListAwareFilterMethod`][filters-base] and [`_install_empty_list_aware_method`][filters-base] to ensure empty lists `[]` are treated as valid filter values without duplicating setter boilerplate.
   - Verified that [`validate_range`][filters-base] and [`RangeField`][filters-base] enforce 2-element sequence boundaries cleanly for [`RangeFilter`][filters-base].

2. **Integer Overflow & Restrictive-Empty Protections:**
   - Verified that [`IntegerInFilter`][filters-base] and [`IntegerRangeFilter`][filters-base] protect against backend parameter binding overflows by reusing [`django_strawberry_framework/utils/querysets.py::coerce_field_value_or_none`][utils-querysets] and decomposing range lookups into compound `{gte, lte}` predicates via [`_apply_lookups`][filters-base].
   - Verified that [`_match_none_queryset`][filters-base] provides consistent empty-set semantics (`qs.none()` or `qs` on `exclude`) across [`ListFilter`][filters-base], [`IntegerInFilter`][filters-base], and [`GlobalIDMultipleChoiceFilter`][filters-base].

3. **GlobalID Strategy Validation & Non-PK Relation Traversal:**
   - Verified that [`resolve_globalid_target_definition`][filters-base] is single-sited in `filters/base.py` and shared between runtime [`_target_definition_for`][filters-base] and build-time `types/finalizer.py::_audit_globalid_filter_strategies`.
   - Verified that [`_relation_uses_non_pk_to_field`][filters-base], [`_GLOBALID_RELATION_PK_ATTR`][filters-base], and [`_marked_pk_field_name`][filters-base] correctly derive `f"{field_name}__pk"` at runtime from live field names, surviving relation rebasing during filterset expansion.
   - Verified that [`_decode_and_validate_global_id`][filters-base] handles malformed inputs, strategy mismatches, empty node IDs, and field coercion with uniform coded GraphQL errors (`GLOBALID_INVALID`, `GLOBALID_UNVALIDATABLE`).

4. **Cross-Package Symmetry & RelatedFilter:**
   - Verified cross-package symmetry between [`RelatedFilter`][filters-base] and [`orders/base.py::RelatedOrder`][orders-base] via [`django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin`][sets-mixins].

5. **Tooling and Completeness Checks:**
   - Executed `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/filters/base.py --review docs/dry/dry-file-filters__base.md --include-constants` — all definitions covered.
   - Ran `uv run ruff check` and `uv run ruff format` across the codebase.

Conclusion: Verified. The review is complete, accurate, and zero edits are required on the target file.

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

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-factories]: ../../django_strawberry_framework/filters/factories.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[orders-base]: ../../django_strawberry_framework/orders/base.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[registry]: ../../django_strawberry_framework/registry.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py

<!-- tests/ -->
[test-filters-base]: ../../tests/filters/test_base.py
[test-filters-factories]: ../../tests/filters/test_factories.py
[test-filters-finalizer]: ../../tests/filters/test_finalizer.py
[test-filters-inputs]: ../../tests/filters/test_inputs.py
[test-filters-sets]: ../../tests/filters/test_sets.py
[test-registry]: ../../tests/test_registry.py
[test-relay-connection]: ../../tests/test_relay_connection.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
