# DRY review: `django_strawberry_framework/filters/factories.py`

Status: verified

## System trace

`django_strawberry_framework/filters/factories.py` defines the Filter input-class BFS factory (Layer 5 of the [spec-027][spec-027] six-layer pipeline) and the dynamic-`FilterSet` cache and getter helper (Layer 6). It owns the following responsibilities:

1. **Layer 5: Filter Input-Class BFS Factory ([`FilterArgumentsFactory`][filters-factories]):**
   - Subclasses [`django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory`][utils-inputs], supplying filter-family caches and configuration hooks.
   - Class-level caches:
     - `FilterArgumentsFactory.input_object_types`: Shared mutable dict mapping generated input class names to built Strawberry `@strawberry.input` dataclasses, ensuring repeated builds converge on the same input class.
     - `FilterArgumentsFactory._type_filterset_registry`: Collision registry mapping generated class names to owning `FilterSet` source classes, enabling fast collision detection when two distinct filtersets claim the same class-derived name.
   - Configuration hooks:
     - `_collision_registry_attr = "_type_filterset_registry"`
     - `_factory_label = "FilterArgumentsFactory"`
     - `_family_label = "FilterSet"`
     - `_rename_noun = "filterset"`
     - `_related_attr = "related_filters"`
     - `_related_target_attr = "filterset"`
   - Triple generation:
     - [`FilterArgumentsFactory._build_input_triples`][filters-factories] calls [`_build_input_fields`][filters-inputs] (per-field input triples from Layer-4 `filterset_cls.get_filters()`) and appends [`_build_logic_fields`][filters-inputs] (the self-referential `and_`, `or_`, `not_` boolean logic operator bag per [spec-027][spec-027] Decision 8).
   - Inherited BFS mechanics from [`GeneratedInputArgumentsFactory`][utils-inputs]:
     - FIFO queue traversal (`pending.pop(0)`) yielding deterministic breadth-first input generation.
     - Cycle (`A -> B -> A`) and diamond (`A -> {B, C} -> D`) graph deduplication via `seen` set tracking.
     - Subclass rejection guard: `__init_subclass__` rejects deeper inheritance of concrete family factories to prevent cross-contamination of mutable class-level caches.
     - Zero-field guard: `_build_class_type` rejects empty input classes at schema construction with an actionable `ConfigurationError` before Strawberry compilation.
     - `FilterArgumentsFactory.arguments` property: returns the built input class for the root `FilterSet`.

2. **Layer 6: Dynamic-FilterSet Cache & Factory Helper ([`get_filterset_class`][filters-factories]):**
   - Module-level cache [`_dynamic_filterset_cache`][filters-factories]: `dict[tuple, type[FilterSet]]` keyed by normalized `(model, fields_key, extra)` tuples produced by [`django_strawberry_framework/utils/inputs.py::make_set_meta_cache_key`][utils-inputs].
   - Constant [`_RESERVED_FACTORY_KEYS`][filters-factories]: `frozenset({"filterset_base_class"})`, stripped from kwargs to avoid keyword collisions during dynamic class construction.
   - Dynamic class constructor delegate: `_get_filterset_class`, constructed via [`django_strawberry_framework/utils/inputs.py::make_dynamic_set_getter`][utils-inputs] with `cache=_dynamic_filterset_cache`, `set_base_class=FilterSet`, `auto_name_suffix="AutoFilter"`, `getter_name="get_filterset_class"`, `reserved_keys=_RESERVED_FACTORY_KEYS`, `explicit_param="filterset_class"`, and `fields_alias=FILTERSET_FIELDS_ALIAS` (`"filter_fields"`).
   - Public factory function [`get_filterset_class`][filters-factories]:
     - If `filterset_class` is provided explicitly, returns it unchanged.
     - Otherwise, normalizes `meta` kwargs via [`normalize_set_meta_for_factory`][utils-inputs] (promoting `filter_fields` to `fields`, canonicalizing sets/frozensets/lists/tuples/dicts, sorting `exclude`), hashes the key via [`make_set_meta_cache_key`][utils-inputs], checks `_dynamic_filterset_cache`, or generates a synthetic `FilterSet` subclass (`<Model>AutoFilter`) via [`create_dynamic_set_class`][utils-inputs].
   - Lifecycle & Consumer Context: Layer 6 has no source consumer in the current release (`DjangoConnectionField` per [spec-030][spec-030] reads `Meta.filterset_class` sidecars directly; auto-generation of `FilterSet` from model/fields is a standing deferred Non-goal per [spec-027][spec-027]). The cache carries no `registry.clear()` hook because keys embed model identity (rebuilt models get fresh keys).

Connected behavior examined:
- [`django_strawberry_framework/orders/factories.py`][orders-factories]: Sibling ordering subsystem factory ([`OrderArgumentsFactory`][orders-factories], `get_orderset_class`, `_dynamic_orderset_cache`).
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Canonical owner of [`GeneratedInputArgumentsFactory`][utils-inputs], [`make_dynamic_set_getter`][utils-inputs], [`make_set_meta_cache_key`][utils-inputs], [`normalize_set_meta_for_factory`][utils-inputs], [`create_dynamic_set_class`][utils-inputs], [`build_strawberry_input_class`][utils-inputs], [`set_input_type_name`][utils-inputs], and [`FILTERSET_FIELDS_ALIAS`][utils-inputs].
- [`django_strawberry_framework/filters/inputs.py`][filters-inputs]: Canonical owner of [`_build_input_fields`][filters-inputs], [`_build_logic_fields`][filters-inputs], [`convert_filter_to_input_annotation`][filters-inputs], [`_field_specs`][filters-inputs], and [`_materialized_names`][filters-inputs].
- [`django_strawberry_framework/filters/sets.py`][filters-sets]: [`FilterSet`][filters-sets] class definition and Layer-4 filter expansion.
- [`django_strawberry_framework/filters/base.py`][filters-base]: Filter primitives, `RelatedFilter` traversal, and GlobalID validation.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Phase 2.5 finalizer orchestrating `FilterArgumentsFactory` builds and module-global input class materialization.
- [`django_strawberry_framework/registry.py`][registry]: Central registry and subsystem lifecycle manager.
- [`tests/filters/test_factories.py`][test-filters-factories]: Test suite verifying BFS input generation, cycle handling, diamond deduplication, name collisions, and dynamic cache keying.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/filters/factories.py --review docs/dry/dry-file-filters__factories.md --include-constants`):
- Parsed 1 target file, 172 lines, 1 class ([`FilterArgumentsFactory`][filters-factories]), 1 method ([`FilterArgumentsFactory._build_input_triples`][filters-factories]), 1 function ([`get_filterset_class`][filters-factories]), 1 module-level constant ([`_RESERVED_FACTORY_KEYS`][filters-factories]), and 1 module-level cache dict ([`_dynamic_filterset_cache`][filters-factories]).
- Verified symbol coverage, reverse imports across production code (`django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/filters/inputs.py`) and test suites (`tests/filters/test_factories.py`).

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `filters/factories.py` and [`orders/factories.py`][orders-factories] are parallel Layer 5 and Layer 6 modules ([spec-027][spec-027], [spec-028][spec-028]). Both [`FilterArgumentsFactory`][filters-factories] and [`OrderArgumentsFactory`][orders-factories] subclass [`django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory`][utils-inputs], which single-sites the FIFO BFS walk, cycle detection, diamond deduplication, source collision checks, idempotent caching, zero-field rejection, and subclassing guards. The only structural divergence between them is `_build_input_triples`: the filter side composes `_build_input_fields` with `_build_logic_fields` (`and_` / `or_` / `not_` boolean operator bag), whereas the order side omits logic fields because SQL ordering cannot be boolean-composed ([spec-028][spec-028] Decision 8). On Layer 6, both modules use [`make_dynamic_set_getter`][utils-inputs], keeping separate family caches (`_dynamic_filterset_cache` vs `_dynamic_orderset_cache`) and passing `fields_alias=FILTERSET_FIELDS_ALIAS` (`"filter_fields"`) on filters vs `None` on orders. Write flavors (`mutations`, `forms`, `rest_framework`) do not require relational BFS factories, building single-declaration inputs directly via shared utilities in [`utils/inputs.py`][utils-inputs].
2. **Sync and async twins:**
   Zero duplication. [`FilterArgumentsFactory`][filters-factories] and [`get_filterset_class`][filters-factories] execute exclusively during schema construction / type finalization. They build static Strawberry GraphQL input dataclasses (`@strawberry.input`) and synthetic `FilterSet` classes. They are completely decoupled from runtime query execution and QuerySet evaluation, whether synchronous (`apply_type_visibility_sync`) or asynchronous (`apply_type_visibility_async`).
3. **Derived rather than repeated knowledge:**
   - Input class names are derived strictly through [`django_strawberry_framework/utils/inputs.py::set_input_type_name`][utils-inputs] (which delegates to `ClassBasedTypeNameMixin.type_name_for()`), ensuring `FooFilter` always produces `FooFilterInputType`.
   - Input field shapes are derived directly from resolved `FilterSet.get_filters()` filter instances via [`_build_input_fields`][filters-inputs] and [`convert_filter_to_input_annotation`][filters-inputs], rather than consulting a parallel `FILTER_DEFAULTS` map ([spec-027][spec-027] Decision 4).
   - Boolean logic fields are derived via [`_build_logic_fields`][filters-inputs] from [`LOGIC_OPERATORS`][filters-inputs].
   - Dynamic `FilterSet` names and cache keys are derived deterministically by [`create_dynamic_set_class`][utils-inputs] (`<Model>AutoFilter`) and [`make_set_meta_cache_key`][utils-inputs].
4. **Inverse and round-trip pairs:**
   - Name mapping and runtime normalization round-trip: Field names derived during BFS by [`emit_set_input_field_triples`][utils-inputs] (`flatten_lookup_path` and `graphql_camel_name`) are recorded in `_field_specs` ([`GeneratedInputFieldSpec`][utils-inputs]). At runtime, `FilterSet._normalize_input` and `normalize_input_value` use `_field_specs` and `LOOKUP_NAME_MAP` to translate wire GraphQL input arguments back to Django ORM query parameters and form-data keys.
   - Dynamic factory kwargs round-trip: Keyword normalization via [`normalize_set_meta_for_factory`][utils-inputs] strips [`_RESERVED_FACTORY_KEYS`][filters-factories] and promotes `filter_fields`, ensuring identical logical declarations collapse onto the same cache slot and round-trip into synthetic `Meta` classes without keyword errors.
5. **Contracts restated in another medium:**
   The BFS factory and dynamic set caching contracts are codified across:
   - Code: [`django_strawberry_framework/filters/factories.py`][filters-factories], [`django_strawberry_framework/orders/factories.py`][orders-factories], [`django_strawberry_framework/utils/inputs.py`][utils-inputs], [`django_strawberry_framework/filters/inputs.py`][filters-inputs], [`django_strawberry_framework/filters/sets.py`][filters-sets], [`django_strawberry_framework/types/finalizer.py`][types-finalizer];
   - Specifications: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] (Decisions 3, 4, 6, 8, 9), [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028] (Decisions 8, 9, 12), [`docs/SPECS/spec-030-django_connection_field-0_0_9.md`][spec-030], [`docs/SPECS/spec-051-converters-0_0_14.md`][spec-051];
   - Test suites: [`tests/filters/test_factories.py`][test-filters-factories], [`tests/orders/test_factories.py`][test-orders-factories], [`tests/filters/test_inputs.py`][test-filters-inputs], [`tests/filters/test_sets.py`][test-filters-sets], [`tests/types/test_finalizer.py`][test-types-finalizer];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Altering BFS queue traversal or cycle-detection logic across set families):** Switch BFS queue ordering or cycle detection semantics for generated input argument factories across filters and orders.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built`][utils-inputs].
  - *Site count:* 1.
- **Posited change 2 (Modifying generated input duplicate name collision error formatting):** Change the wording or formatting of the duplicate type name collision error message across set argument factories.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/inputs.py::duplicate_name_message`][utils-inputs].
  - *Site count:* 1.
- **Posited change 3 (Modifying dynamic FilterSet naming suffix, e.g. `AutoFilter` to `DynamicFilter`):** Change the synthetic class name suffix for dynamically created filtersets.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/filters/factories.py`][filters-factories] (`auto_name_suffix` argument passed to `make_dynamic_set_getter`).
  - *Site count:* 1.
- **Posited change 4 (Adding a reserved factory keyword to strip from dynamic FilterSet kwargs):** Add a new internal reserved parameter to strip before constructing synthetic `Meta` classes.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/filters/factories.py::_RESERVED_FACTORY_KEYS`][filters-factories].
  - *Site count:* 1.
- **Posited change 5 (Altering the logical operator field structure for filters):** Add or adjust a boolean operator in the filter input operator bag (e.g. adding `xor_`).
  - *Sites that must move:* Exactly 2 sites: [`django_strawberry_framework/filters/inputs.py::LOGIC_OPERATORS`][filters-inputs] (which feeds `_build_logic_fields` called by [`FilterArgumentsFactory._build_input_triples`][filters-factories]) and [`tests/filters/test_inputs.py`][test-filters-inputs].
  - *Site count:* 2.

### Rejected candidates

1. **Merging `_dynamic_filterset_cache` and `_dynamic_orderset_cache` into a single shared cache in `utils/inputs.py`:**
   - Disproved. FilterSet and OrderSet subclasses inhabit separate class hierarchies with different base classes (`FilterSet` vs `OrderSet`), different naming suffixes (`AutoFilter` vs `AutoOrder`), and different synonym rules (`FILTERSET_FIELDS_ALIAS` on filters vs `None` on orders). Keeping disjoint family cache dictionaries prevents cross-subsystem cache poisoning and ensures lifecycle autonomy.
2. **Inlining `GeneratedInputArgumentsFactory` BFS walk directly inside `FilterArgumentsFactory`:**
   - Disproved. Sibling subsystem `orders/factories.py::OrderArgumentsFactory` shares the exact same BFS queue traversal, cycle handling, diamond deduplication, and collision detection algorithm. Centralizing the shared algorithm in `utils/inputs.py` eliminates code duplication across subsystems.
3. **Adding a `registry.clear()` hook for `_dynamic_filterset_cache`:**
   - Disproved. The cache keys embed the model class identity via `make_set_meta_cache_key`. In reloaded or dynamically rebuilt model environments, rebuilt model classes produce fresh keys, ensuring zero cross-test collision without requiring global clear hooks.

## Opportunities

None — `django_strawberry_framework/filters/factories.py` is a clean, 172-line factory and caching module. All shared BFS algorithms, dynamic class factories, cache key normalization, and error reporting mechanics are consolidated at their root owner in [`django_strawberry_framework/utils/inputs.py`][utils-inputs]. All filter-specific field and logic conversions are owned by [`django_strawberry_framework/filters/inputs.py`][filters-inputs].

## Judgment

Zero-edit review. `django_strawberry_framework/filters/factories.py` contains zero duplicate policy or unowned invariants. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 or 2 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/filters/factories.py --review docs/dry/dry-file-filters__factories.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Worker 2 independently verified `django_strawberry_framework/filters/factories.py` against its sister factory [`orders/factories.py`][orders-factories], the shared input generation substrate [`django_strawberry_framework/utils/inputs.py`][utils-inputs], and the filter input converter [`django_strawberry_framework/filters/inputs.py`][filters-inputs].

### Independent findings & boundary analysis

1. **Layer 5 BFS Factory Architecture ([`FilterArgumentsFactory`][filters-factories]):**
   - [`FilterArgumentsFactory`][filters-factories] cleanly subclasses [`GeneratedInputArgumentsFactory`][utils-inputs], which single-sites the FIFO queue traversal (`pending.pop(0)`), graph cycle prevention (`seen` set tracking), diamond deduplication, empty input guard (`ConfigurationError` for zero-field inputs), duplicate type name collision detection, and class-creation subclassing rejection (`__init_subclass__`).
   - The family-specific specialization in `FilterArgumentsFactory` is strictly limited to declaring its isolated class-level caches (`input_object_types` and `_type_filterset_registry`), its hook attributes (`_collision_registry_attr`, `_factory_label`, `_family_label`, `_rename_noun`, `_related_attr`, `_related_target_attr`), and its triple builder [`_build_input_triples`][filters-factories].
   - `_build_input_triples` delegates field construction to [`_build_input_fields`][filters-inputs] and appends boolean combinators via [`_build_logic_fields`][filters-inputs] (`and_` / `or_` / `not_` per [spec-027][spec-027] Decision 8). Sibling [`OrderArgumentsFactory`][orders-factories] appropriately omits logic fields because SQL ordering clauses do not support boolean logic composition ([spec-028][spec-028] Decision 8).

2. **Layer 6 Dynamic FilterSet Caching & Factory Helper ([`get_filterset_class`][filters-factories]):**
   - Dynamic FilterSet generation delegates to `_get_filterset_class`, constructed via [`make_dynamic_set_getter`][utils-inputs] in `utils/inputs.py`.
   - Hashing, keyword normalization, and dynamic `type(...)` synthesis are completely centralized in `utils/inputs.py` ([`normalize_set_meta_for_factory`][utils-inputs], [`make_set_meta_cache_key`][utils-inputs], [`create_dynamic_set_class`][utils-inputs]).
   - `filters/factories.py` owns its family-scoped cache dictionary [`_dynamic_filterset_cache`][filters-factories], its reserved kwarg set [`_RESERVED_FACTORY_KEYS`][filters-factories] (`frozenset({"filterset_base_class"})`), and passes `fields_alias=FILTERSET_FIELDS_ALIAS` (`"filter_fields"`).
   - Separate family cache dictionaries between filters and orders prevent cross-subsystem cache collisions or unintended cache evictions.

3. **Duplication Probing Matrix & Single-Edit-Site Counts:**
   - All 5 axes of the mandatory probing matrix were re-evaluated and verified:
     - Axis 1 (Cross-flavor policy mirroring): Shared BFS logic in `GeneratedInputArgumentsFactory`; shared dynamic set constructor in `make_dynamic_set_getter`; flavor-specific divergence strictly confined to domain requirements (`_build_logic_fields` and `FILTERSET_FIELDS_ALIAS`).
     - Axis 2 (Sync and async twins): Schema construction only; zero runtime QuerySet execution paths.
     - Axis 3 (Derived knowledge): Deterministic name derivation (`set_input_type_name`, `create_dynamic_set_class`), direct resolution from filter instances (`_build_input_fields`, `convert_filter_to_input_annotation`), and key hashing (`make_set_meta_cache_key`).
     - Axis 4 (Inverse pairs): Name and lookup mapping round-trips via `_field_specs` and `LOOKUP_NAME_MAP`; factory kwargs round-trip via `normalize_set_meta_for_factory`.
     - Axis 5 (Contracts in another medium): Fully aligned across specifications, unit tests (`tests/filters/test_factories.py`), and documentation.
   - All posited change single-edit-site counts hold (1 or 2 sites).

4. **Coverage & Test Gate:**
   - Static analysis check passed: `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/filters/factories.py --review docs/dry/dry-file-filters__factories.md --include-constants` (4 target definitions covered).
   - Test suite passed: 35 tests in `tests/filters/test_factories.py` executed cleanly.

Review verified with zero outstanding edits needed. Status updated to `verified`.

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
[spec-030]: ../SPECS/spec-030-django_connection_field-0_0_9.md
[spec-051]: ../SPECS/spec-051-converters-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
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
[test-orders-factories]: ../../tests/orders/test_factories.py
[test-registry]: ../../tests/test_registry.py
[test-relay-connection]: ../../tests/test_relay_connection.py
[test-types-finalizer]: ../../tests/types/test_finalizer.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
