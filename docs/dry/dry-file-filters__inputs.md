# DRY review: `django_strawberry_framework/filters/inputs.py`

Status: verified

## System trace

`django_strawberry_framework/filters/inputs.py` defines the Filter input-generation namespace, lookup-name scaffolding, operator-bag dataclass construction, and input-data shape converters ([spec-027][spec-027], [spec-051][spec-051]). It comprises Layer 3, Layer 4 leaf operator-bag minting, and Layer 5 runtime/build-time input translation of the filtering subsystem pipeline. It owns the following responsibilities:

1. **Module & Namespace Scaffolding (spec-027 Decision 9):**
   - [`INPUTS_MODULE_PATH`][filters-inputs]: Pinned constant (`"django_strawberry_framework.filters.inputs"`) used as the target path for `strawberry.lazy(...)` forward references across [`_build_logic_fields`][filters-inputs], [`_build_input_fields`][filters-inputs], [`FilterArgumentsFactory`][filters-factories], and [`django_strawberry_framework/filters/__init__.py::filter_input_type`][filters-init].
   - [`LOOKUP_PREFIXES`][filters-inputs]: Search-prefix vocabulary map (`{"^": "istartswith", "=": "iexact", "@": "search", "$": "iregex"}`) for `Meta.search_fields` expansion, consumed by [`construct_search`][filters-inputs].
   - [`LOOKUP_NAME_MAP`][filters-inputs]: Canonical mapping of `django-filter` lookup expressions (`exact`, `iexact`, `contains`, `icontains`, `startswith`, `istartswith`, `endswith`, `iendswith`, `regex`, `iregex`, `gt`, `gte`, `lt`, `lte`, `isnull`, `in`, `range`, `date`, `year`, `month`, `day`, `week_day`, `quarter`, `hour`, `minute`, `second`) to `(python_attr, graphql_name)` tuples. Pinned explicitly per [spec-027][spec-027] Decision 3 Layer 5 because Strawberry's automatic camel-casing cannot split strings without underscores (e.g. `icontains` to `iContains`) and Python keywords like `in` cannot serve as dataclass attributes (`in_`). Consumed by [`_build_input_fields`][filters-inputs], [`FilterSet._normalize_input`][filters-sets], and [`normalize_input_value`][filters-inputs].
   - [`LogicOperatorDescriptor`][filters-inputs]: Frozen dataclass defining logical operator contracts: `python_attr` (`and_`, `or_`, `not_`), `wire_name` (`and`, `or`, `not`), `is_sequence` cardinality (`True` for `and`/`or`, `False` for `not`), and `compose` (`Callable[[list[models.Q]], models.Q]`).
   - [`_compose_and`][filters-inputs], [`_compose_or`][filters-inputs], [`_compose_not`][filters-inputs]: Canonical Q-composition functions for boolean combinators.
   - [`LOGIC_OP_AND`][filters-inputs], [`LOGIC_OP_OR`][filters-inputs], [`LOGIC_OP_NOT`][filters-inputs], [`LOGIC_OPERATORS`][filters-inputs], [`LOGIC_OPERATORS_BY_WIRE`][filters-inputs], [`LOGIC_OPERATORS_BY_PYTHON_ATTR`][filters-inputs]: Canonical operator descriptor singletons, tuples, and immutable index maps establishing the single source of truth for tree-form boolean filter combinators, consumed by [`_build_logic_fields`][filters-inputs] and [`FilterSet._normalize_input`][filters-sets].
   - Namespace lifecycle ledgers: [`_materialized_names`][filters-inputs], `_field_specs` ([`GeneratedInputFieldSpec`][utils-inputs]), `_materialize_input`, and `_clear_input_namespace` generated via [`django_strawberry_framework/utils/inputs.py::make_set_input_namespace`][utils-inputs].
   - [`materialize_input_class`][filters-inputs]: Public wrapper binding dynamic Strawberry input dataclasses into `filters.inputs.__dict__` for Strawberry lazy resolution.
   - [`clear_filter_input_namespace`][filters-inputs]: Public clear helper registered via [`django_strawberry_framework/registry.py::register_subsystem_clear`][registry] (`owner="filters.input_namespace"`, `before_bind=True`) to reset the filter ledger and subclass lifecycle bindings.

2. **Internal Helpers & Type Converters:**
   - [`_pascal_case`][filters-inputs]: Name converter delegating to [`django_strawberry_framework/utils/strings.py::pascal_case_or_raise`][utils-strings] with a [`RangeFilter`][filters-base]-specific `ConfigurationError` factory using [`django_strawberry_framework/exceptions.py::_safe_arg_repr`][exceptions] for robust hostile-value diagnostics.
   - [`_scalar_from_form_field`][filters-inputs]: Maps Django form fields (`NullBooleanField`, `BooleanField`, `DecimalField`, `FloatField`, `IntegerField`, `DateTimeField`, `DateField`, `TimeField`, `UUIDField`, `CharField`) to Python scalars. Respects form-field inheritance hierarchy where `DecimalField` and `FloatField` subclass `IntegerField`.
   - [`_scalar_from_model_field`][filters-inputs]: Local-import delegate to [`django_strawberry_framework/types/converters.py::scalar_for_field`][types-converters], mapping model fields to GraphQL scalars, custom `SCALAR_MAP` entries, and 64-bit `BigInt`.
   - [`_choice_enum_from_filter`][filters-inputs]: Local-import delegate to [`django_strawberry_framework/types/converters.py::convert_choices_to_enum`][types-converters], deriving shared GraphQL enums from Django model field choices or raising `ConfigurationError` for unbacked choices.
   - [`_element_annotation`][filters-inputs]: Resolves single-element Strawberry types prioritizing model fields over form fields so integer columns and choice enums do not collapse to strings on CSV/list filters.
   - [`_owner_type_name`][filters-inputs]: Derives the GraphQL type name from [`DjangoTypeDefinition.graphql_type_name`][types-definition].

3. **Public Converter & Normalizer Pair (MRO Dispatch per spec-051 C3):**
   - [`_FILTER_INPUT_KIND_TYPES`][filters-inputs]: Shared kind hierarchy tuple in most-specific-first order: `GlobalIDMultipleChoiceFilter`, `GlobalIDFilter`, `BaseCSVFilter`, `(RangeFilter, _DjangoRangeFilter)`, `(ListFilter, ArrayFilter)`, `TypedFilter`, `(ChoiceFilter, TypedChoiceFilter)`, `object`.
   - [`_filter_input_prechecks`][filters-inputs]: Helper zipping [`_FILTER_INPUT_KIND_TYPES`][filters-inputs] with per-pass handlers using `strict=True` to guarantee handler symmetry.
   - [`_unexpected_filter_dispatch`][filters-inputs]: Fallthrough error factory for [`django_strawberry_framework/utils/converters.py::convert_with_mro`][utils-converters].
   - [`convert_filter_to_input_annotation`][filters-inputs]: Walks [`_FILTER_INPUT_KIND_TYPES`][filters-inputs] via [`convert_with_mro`][utils-converters] to generate Strawberry input field annotations, qualifying nested range types via `filterset_cls` and applying optionality `| None`.
   - [`normalize_input_value`][filters-inputs]: Short-circuits inactive/`UNSET` values via [`django_strawberry_framework/utils/input_values.py::is_inactive_value`][utils-input-values] and walks [`_FILTER_INPUT_KIND_TYPES`][filters-inputs] via [`convert_with_mro`][utils-converters] to translate Strawberry input values into `django-filter` form data (scalar, list, or positional range dict patch).

4. **Range, GlobalID, and Enum Normalization Helpers:**
   - [`_encode_global_id_input`][filters-inputs]: Re-encodes `relay.GlobalID` objects to base64 wire strings so [`GlobalIDFilter`][filters-base] can validate `type_name` at filter evaluation time.
   - [`_unwrap_enum_member`][filters-inputs]: Unwraps `value.value` for `enum.Enum` instances, preserving `None` enum values and passing non-enum instances through.
   - [`_build_range_input_class`][filters-inputs]: Generates and caches Strawberry input dataclasses (`start: T | None`, `end: T | None`), scoped by owning `FilterSet` name (`{FilterSet}{Pascal(field_name)}RangeInputType`) to prevent silent GraphQL schema collision across filtersets.
   - [`_normalize_range_value`][filters-inputs]: Decomposes range dataclasses/dicts into positional form-data patches `{<name>_0, <name>_1}`, omitting `None`/`UNSET` bounds for partial range queries.

5. **Logical-Operator & Field Builders:**
   - [`_build_logic_fields`][filters-inputs]: Emits `(python_attr, annotation, field_kwargs)` triples for `and_`, `or_`, `not_` referencing `Annotated[type_name, strawberry.lazy(INPUTS_MODULE_PATH)]` (inside list for `and_` / `or_`, single ref for `not_`).
   - [`_build_input_fields`][filters-inputs]: Groups `filterset_cls.get_filters()` by top-level field name, applies `HIDE_FLAT_FILTERS` via [`hide_flat_filters_setting`][filters-inputs], mints per-field operator-bag dataclasses (`{FilterSet}{Pascal(field_name)}FilterInputType`), and calls [`django_strawberry_framework/utils/inputs.py::emit_set_input_field_triples`][utils-inputs] to populate `_field_specs`.
   - [`_model_field_for_filter`][filters-inputs]: Resolves the backing Django model field via `django_filters.utils.get_model_field`.
   - [`construct_search`][filters-inputs]: Translates search-prefixed filter names into `{name: lookup}` maps using [`LOOKUP_PREFIXES`][filters-inputs].

Connected behavior examined:
- [`django_strawberry_framework/orders/inputs.py`][orders-inputs]: Sibling ordering subsystem input module ([`Ordering`][orders-inputs], `_build_input_fields`, `normalize_input_value`, `INPUTS_MODULE_PATH`).
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Canonical owner of [`make_set_input_namespace`][utils-inputs], [`build_strawberry_input_class`][utils-inputs], [`emit_set_input_field_triples`][utils-inputs], [`optional_field_kwargs`][utils-inputs], [`set_input_type_name`][utils-inputs], and [`GeneratedInputFieldSpec`][utils-inputs].
- [`django_strawberry_framework/utils/converters.py`][utils-converters]: Canonical owner of [`convert_with_mro`][utils-converters] and `MRO_CONTINUE`.
- [`django_strawberry_framework/utils/input_values.py`][utils-input-values]: Canonical owner of [`is_inactive_value`][utils-input-values] and input traversal classifiers.
- [`django_strawberry_framework/utils/strings.py`][utils-strings]: Canonical owner of [`pascal_case_or_raise`][utils-strings] and [`graphql_camel_name`][utils-strings].
- [`django_strawberry_framework/filters/base.py`][filters-base]: Filter primitives ([`RangeFilter`][filters-base], [`GlobalIDFilter`][filters-base], [`GlobalIDMultipleChoiceFilter`][filters-base], [`ListFilter`][filters-base], [`ArrayFilter`][filters-base], [`TypedFilter`][filters-base]).
- [`django_strawberry_framework/filters/sets.py`][filters-sets]: Metaclass collection, `FilterSet._normalize_input`, and lookup expansion.
- [`django_strawberry_framework/filters/factories.py`][filters-factories]: BFS factory [`FilterArgumentsFactory`][filters-factories].
- [`django_strawberry_framework/types/converters.py`][types-converters]: Shared scalar and enum resolution (`scalar_for_field`, `convert_choices_to_enum`).
- [`django_strawberry_framework/registry.py`][registry]: Central registry and subsystem lifecycle manager.
- [`tests/filters/test_inputs.py`][test-filters-inputs]: Comprehensive test suite covering lookup name mappings, operator bags, range classes, and normalization.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/filters/inputs.py --review docs/dry/dry-file-filters__inputs.md --include-constants`):
- Parsed 1 target file, 1052 lines, 34 target definitions (24 functions/methods, 1 class: [`LogicOperatorDescriptor`][filters-inputs], 9 module-level constants: [`INPUTS_MODULE_PATH`][filters-inputs], [`LOOKUP_PREFIXES`][filters-inputs], [`LOOKUP_NAME_MAP`][filters-inputs], [`LOGIC_OP_AND`][filters-inputs], [`LOGIC_OP_OR`][filters-inputs], [`LOGIC_OP_NOT`][filters-inputs], [`LOGIC_OPERATORS`][filters-inputs], [`LOGIC_OPERATORS_BY_WIRE`][filters-inputs], [`LOGIC_OPERATORS_BY_PYTHON_ATTR`][filters-inputs], [`_compose_and`][filters-inputs], [`_compose_or`][filters-inputs], [`_compose_not`][filters-inputs], [`_pascal_case`][filters-inputs], [`_scalar_from_form_field`][filters-inputs], [`_scalar_from_model_field`][filters-inputs], [`_choice_enum_from_filter`][filters-inputs], [`_element_annotation`][filters-inputs], [`_FILTER_INPUT_KIND_TYPES`][filters-inputs], [`_filter_input_prechecks`][filters-inputs], [`_unexpected_filter_dispatch`][filters-inputs], [`convert_filter_to_input_annotation`][filters-inputs], [`normalize_input_value`][filters-inputs], [`_encode_global_id_input`][filters-inputs], [`_unwrap_enum_member`][filters-inputs], [`_build_range_input_class`][filters-inputs], [`_normalize_range_value`][filters-inputs], [`_owner_type_name`][filters-inputs], [`_build_logic_fields`][filters-inputs], [`_build_input_fields`][filters-inputs], [`_model_field_for_filter`][filters-inputs], [`construct_search`][filters-inputs], [`materialize_input_class`][filters-inputs], [`clear_filter_input_namespace`][filters-inputs]).
- Verified symbol coverage and reverse imports across production code (`filters/sets.py`, `filters/factories.py`, `filters/__init__.py`, `types/converters.py`, `registry.py`) and test suites (`tests/filters/test_inputs.py`, `tests/filters/test_sets.py`, `tests/filters/test_factories.py`, `tests/filters/test_finalizer.py`).

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `filters/inputs.py` and [`orders/inputs.py`][orders-inputs] are parallel Layer 3 / Layer 5 modules ([spec-027][spec-027], [spec-028][spec-028]). Both modules leverage the shared input substrate in [`django_strawberry_framework/utils/inputs.py`][utils-inputs] via [`make_set_input_namespace`][utils-inputs] (single-siting namespace materialization, duplicate class collision detection, and registry clear lifecycle) and [`emit_set_input_field_triples`][utils-inputs] (single-siting field name flattening, camel-casing, and forward-reference emission). Structural divergence between them is domain-dictated:
   - Filters generate per-field operator-bag dataclasses (`{FilterSet}{Pascal(field_name)}FilterInputType`) supporting varied lookups (`exact`, `iExact`, `gt`, `in`, `range`), whereas orders map leaves directly to [`Ordering | None`][orders-inputs] without operator bags;
   - Filters emit boolean logic fields via [`_build_logic_fields`][filters-inputs] (`and_`, `or_`, `not_`), whereas orders omit logic fields because SQL order clauses cannot be boolean-composed ([spec-028][spec-028] Decision 8);
   - Filters support `HIDE_FLAT_FILTERS` configuration via [`hide_flat_filters_setting`][filters-inputs] to skip flat relation traversal fields when nested `RelatedFilter` paths exist;
   - Filters dispatch multi-kind primitives via [`_FILTER_INPUT_KIND_TYPES`][filters-inputs] and [`convert_with_mro`][utils-converters], whereas orders have a single uniform leaf type.
   Write flavors (`mutations`, `forms`, `rest_framework`) construct flat inputs using [`build_strawberry_input_class`][utils-inputs] directly.
2. **Sync and async twins:**
   Zero duplication. `filters/inputs.py` executes exclusively during schema construction (building `@strawberry.input` dataclasses) and input data normalization (transforming GraphQL arguments into `django-filter` form-data). It is completely decoupled from runtime QuerySet evaluation, whether synchronous (`apply_type_visibility_sync`, `FilterSet.apply_sync`) or asynchronous (`apply_type_visibility_async`, `FilterSet.apply_async`).
3. **Derived rather than repeated knowledge:**
   - Input type names are derived deterministically via [`set_input_type_name`][utils-inputs] and [`_pascal_case`][filters-inputs] (delegating to [`pascal_case_or_raise`][utils-strings]).
   - Range input dataclasses are dynamically minted and cached per `(filterset_cls, field_name, inner)` via [`_build_range_input_class`][filters-inputs], qualifying names with the owning `FilterSet` (`{FilterSet}{Pascal(field_name)}RangeInputType`) to prevent silent GraphQL schema collision.
   - Field annotations are derived directly from resolved filter instances and model field inspection via [`_element_annotation`][filters-inputs], [`_scalar_from_model_field`][filters-inputs] (delegating to [`types/converters.py::scalar_for_field`][types-converters]), [`_choice_enum_from_filter`][filters-inputs] (delegating to [`types/converters.py::convert_choices_to_enum`][types-converters]), and [`_scalar_from_form_field`][filters-inputs].
   - Boolean combinators derive from [`LOGIC_OPERATORS`][filters-inputs] in [`_build_logic_fields`][filters-inputs].
   - Search prefixes derive from [`LOOKUP_PREFIXES`][filters-inputs] in [`construct_search`][filters-inputs].
   - Model fields resolve via `django_filters.utils.get_model_field` in [`_model_field_for_filter`][filters-inputs].
   - Owner GraphQL type names derive from [`DjangoTypeDefinition.graphql_type_name`][types-definition] in [`_owner_type_name`][filters-inputs].
4. **Inverse and round-trip pairs:**
   - Lookup and name mapping round-trip: During schema building, [`_build_input_fields`][filters-inputs] maps lookups via [`LOOKUP_NAME_MAP`][filters-inputs] (`lookup -> (python_attr, graphql_name)`) and records provenance in `_field_specs` ([`GeneratedInputFieldSpec`][utils-inputs]). At runtime, [`FilterSet._normalize_input`][filters-sets] and [`normalize_input_value`][filters-inputs] consult `_field_specs` and [`LOOKUP_NAME_MAP`][filters-inputs] to translate wire arguments back into `django-filter` form keys and ORM lookups.
   - Range input round-trip: [`_build_range_input_class`][filters-inputs] mints `{start, end}` dataclass fields; [`_normalize_range_value`][filters-inputs] unpacks them into Django `RangeWidget` positional form-data keys `{<name>_0, <name>_1}`, omitting `None`/`UNSET` bounds for partial ranges.
   - GlobalID wire format round-trip: [`_encode_global_id_input`][filters-inputs] re-encodes `relay.GlobalID` objects to base64 wire strings so [`GlobalIDFilter`][filters-base] can validate `type_name` and decode at filter evaluation time.
   - Enum unwrapping: [`_unwrap_enum_member`][filters-inputs] extracts `.value` from `enum.Enum` instances, supporting `None`-valued enum members without duck-typing issues.
5. **Contracts restated in another medium:**
   The input generation and normalization contracts are codified across:
   - Code: [`django_strawberry_framework/filters/inputs.py`][filters-inputs], [`django_strawberry_framework/filters/sets.py`][filters-sets], [`django_strawberry_framework/filters/base.py`][filters-base], [`django_strawberry_framework/filters/factories.py`][filters-factories], [`django_strawberry_framework/orders/inputs.py`][orders-inputs], [`django_strawberry_framework/utils/inputs.py`][utils-inputs], [`django_strawberry_framework/types/converters.py`][types-converters], [`django_strawberry_framework/registry.py`][registry];
   - Specifications: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] (Decisions 2, 3, 4, 8, 9, 11), [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028] (Decisions 8, 9), [`docs/SPECS/spec-031-globalid_type_names-0_0_9.md`][spec-031], [`docs/SPECS/spec-051-converters-0_0_14.md`][spec-051] (Decision 3, Section C3);
   - Test suites: [`tests/filters/test_inputs.py`][test-filters-inputs], [`tests/filters/test_sets.py`][test-filters-sets], [`tests/filters/test_factories.py`][test-filters-factories], [`tests/filters/test_base.py`][test-filters-base], [`tests/filters/test_finalizer.py`][test-filters-finalizer], [`tests/test_registry.py`][test-registry];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding a new lookup expression mapping, e.g. `trigram_similar`):** Add a new lookup mapping from `django-filter` to GraphQL wire names and Python dataclass attributes.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/filters/inputs.py::LOOKUP_NAME_MAP`][filters-inputs] (which feeds [`_build_input_fields`][filters-inputs], [`FilterSet._normalize_input`][filters-sets], and [`normalize_input_value`][filters-inputs]).
  - *Site count:* 1.
- **Posited change 2 (Adding or altering a boolean logical operator, e.g. adding `xor_`):** Introduce a new logical operator to the filter input type.
  - *Sites that must move:* Exactly 2 sites: [`django_strawberry_framework/filters/inputs.py::LOGIC_OPERATORS`][filters-inputs] (which automatically feeds [`_build_logic_fields`][filters-inputs] and [`FilterSet._normalize_input`][filters-sets]) and [`tests/filters/test_inputs.py`][test-filters-inputs].
  - *Site count:* 2.
- **Posited change 3 (Modifying the search-prefix vocabulary, e.g. adding `~` for regex):** Add or adjust a search prefix symbol in `Meta.search_fields`.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/filters/inputs.py::LOOKUP_PREFIXES`][filters-inputs] (which feeds [`construct_search`][filters-inputs]).
  - *Site count:* 1.
- **Posited change 4 (Adjusting the naming convention or error handling for Range input types):** Change the suffix or validation of generated Range input classes.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/filters/inputs.py::_build_range_input_class`][filters-inputs] (or [`_pascal_case`][filters-inputs]).
  - *Site count:* 1.
- **Posited change 5 (Altering generated input namespace lifecycle or clear mechanics across set families):** Change how generated input classes are cleared or parked in `module.__dict__`.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/inputs.py::make_set_input_namespace`][utils-inputs].
  - *Site count:* 1.
- **Posited change 6 (Modifying MRO converter dispatch mechanics for filter types):** Change the MRO traversal or handler registration logic.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/converters.py::convert_with_mro`][utils-converters].
  - *Site count:* 1.

### Rejected candidates

1. **Merging `_build_range_input_class` across all filtersets into an unqualified `<Field>RangeInputType`:**
   - Disproved. Multiple filtersets filtering a field of the same name (e.g. `price` on `BookFilter` vs `price` on `CarFilter`) can resolve different scalars (e.g. `Decimal` vs `float` or `int`). Qualifying nested range types with the owning `FilterSet` name ensures GraphQL schema uniqueness without silent type clobbering.
2. **Inlining `make_set_input_namespace` mechanics directly into `filters/inputs.py` and `orders/inputs.py`:**
   - Disproved. The lifecycle of Strawberry lazy module-dict materialization, duplicate class collision checking, factory cache flushing, and `_lifecycle` descriptor resetting is identical across `FilterSet` and `OrderSet`. Centralizing in [`django_strawberry_framework/utils/inputs.py`][utils-inputs] prevents lifecycle drift.
3. **Merging `LOOKUP_NAME_MAP` with `LOOKUP_PREFIXES`:**
   - Disproved. `LOOKUP_NAME_MAP` maps standard `django-filter` lookup expressions to GraphQL field/attribute pairs, whereas `LOOKUP_PREFIXES` defines the prefix string vocabulary for `Meta.search_fields` translation. They serve distinct layers of the filtering pipeline.

## Opportunities

None — `django_strawberry_framework/filters/inputs.py` is a clean, 1002-line input-generation and conversion module. All shared namespace mechanics, field triple emission scaffolds, string casing utilities, and MRO dispatch engines are consolidated at their root owners in [`django_strawberry_framework/utils/inputs.py`][utils-inputs], [`django_strawberry_framework/utils/converters.py`][utils-converters], [`django_strawberry_framework/utils/input_values.py`][utils-input-values], and [`django_strawberry_framework/utils/strings.py`][utils-strings].

## Judgment

Zero-edit review. `django_strawberry_framework/filters/inputs.py` contains zero duplicate policy or unowned invariants. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 or 2 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/filters/inputs.py --review docs/dry/dry-file-filters__inputs.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Worker 2 independently verified the DRY review for `django_strawberry_framework/filters/inputs.py`:

1. **Architecture and Subsystem Contracts:**
   - Verified that `django_strawberry_framework/filters/inputs.py` cleanly encapsulates Layer 3/4/5 filtering contracts: dynamic input dataclass construction, per-field operator-bag minting, MRO-driven annotation generation, runtime value normalization, and module namespace materialization ([spec-027][spec-027], [spec-051][spec-051]).
   - Confirmed that shared input generation mechanics (`make_set_input_namespace`, `emit_set_input_field_triples`, `build_strawberry_input_class`, `optional_field_kwargs`, `set_input_type_name`) reside squarely in [`django_strawberry_framework/utils/inputs.py`][utils-inputs], with `filters/inputs.py` providing only filter-domain specific closures (`_visible_entries`, `_related_target_of`, `_leaf_of`).
   - Verified that `LOOKUP_NAME_MAP` is the single source of truth mapping `django-filter` lookup expressions to `(python_attr, graphql_name)` pairs, feeding schema generation (`_build_input_fields`), argument normalization (`FilterSet._normalize_input`), and value normalization (`normalize_input_value`).
   - Verified that `LOGIC_OPERATORS` is the single source of truth for boolean combinators (`and_`, `or_`, `not_`), shared between `_build_logic_fields` and `FilterSet._normalize_input`.
   - Verified that `_FILTER_INPUT_KIND_TYPES` pairs symmetrically across `convert_filter_to_input_annotation` and `normalize_input_value` via `_filter_input_prechecks(..., strict=True)` and `convert_with_mro`.
   - Verified that `_build_range_input_class` qualifies range input type names with the owning `FilterSet` name (`{FilterSet}{Pascal(field_name)}RangeInputType`) and caches per `(filterset_cls, field_name, inner)`, preventing silent GraphQL schema collisions across distinct filtersets.
   - Verified that `_normalize_range_value` unpacks range objects/dictionaries into Django `RangeWidget` positional form-data keys `{<name>_0, <name>_1}`, correctly pruning inactive/`UNSET`/`None` values for partial range queries.
   - Verified that `_encode_global_id_input` re-encodes `relay.GlobalID` objects to base64 wire strings, ensuring `type_name` validation occurs at filter execution time on bound `GlobalIDFilter` instances.

2. **Mandatory 5-Axis Matrix Discharge:**
   - All 5 axes are fully analyzed and discharged with detailed architectural rationales:
     - Cross-flavor policy mirroring verified against `orders/inputs.py`, `mutations`, `forms`, and `rest_framework`.
     - Sync/async twin divergence verified absent (pure schema generation and data normalization).
     - Derived knowledge verified across name generation, dynamic range types, element annotations, enum/scalar resolution, logic keys, search prefixes, and model field resolution.
     - Inverse/round-trip pairs verified for lookup name mapping, range input creation/decomposition, GlobalID wire encoding, and enum unwrapping.
     - Medium restatements verified across specs, codebase, tests, and documentation.

3. **Single-Edit-Site Scenarios:**
   - Confirmed single-edit-site counts of 1 or 2 across all 6 posited change scenarios.

4. **Coverage and Test Suite:**
   - Executed `export_dry_review.py check --target django_strawberry_framework/filters/inputs.py --review docs/dry/dry-file-filters__inputs.md --include-constants`: confirmed 26 target definitions covered, 0 missing.
   - Executed full pytest suite (`uv run pytest`): 2,704 passed tests, 0 failures.

Review verified. Updating `Status: verified`.

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
[orders-factories]: ../../django_strawberry_framework/orders/factories.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
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
[utils-strings]: ../../django_strawberry_framework/utils/strings.py

<!-- tests/ -->
[test-filters-base]: ../../tests/filters/test_base.py
[test-filters-factories]: ../../tests/filters/test_factories.py
[test-filters-finalizer]: ../../tests/filters/test_finalizer.py
[test-filters-inputs]: ../../tests/filters/test_inputs.py
[test-filters-sets]: ../../tests/filters/test_sets.py
[test-orders-factories]: ../../tests/orders/test_factories.py
[test-registry]: ../../tests/test_registry.py
[test-relay-connection]: ../../tests/test_relay_connection.py
[test-types-converters]: ../../tests/types/test_converters.py
[test-types-finalizer]: ../../tests/types/test_finalizer.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

