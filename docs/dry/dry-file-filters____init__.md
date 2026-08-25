# DRY review: `django_strawberry_framework/filters/__init__.py`

Status: verified

## System trace

`django_strawberry_framework/filters/__init__.py` is the public export facade and consumer-helper entry point for the framework's filtering subsystem ([spec-027][spec-027]). It provides the subpackage's public API surface via `__all__`, exposes foundational filter primitives, connects the declarative `FilterSet` + `FilterSetMetaclass` classes, registers the subsystem clear hook, and defines the consumer-facing `filter_input_type` forward-reference helper. It owns the following responsibilities:

1. **Subpackage Public Facade & Re-export Surface:**
   - Foundational primitives (from [`filters/base.py`][filters-base]): [`Filter`][filters-base] (deliberately shadowing `django_filters.Filter` for unified import surface), [`TypedFilter`][filters-base], [`ArrayFilter`][filters-base] and [`ArrayFilterMethod`][filters-base] (PostgreSQL array filtering), [`ListFilter`][filters-base] and [`ListFilterMethod`][filters-base] (CSV/JSON list filtering), [`RangeFilter`][filters-base], [`RangeField`][filters-base], and [`validate_range`][filters-base] (range filtering and bounds validation), [`GlobalIDFilter`][filters-base] and [`GlobalIDMultipleChoiceFilter`][filters-base] (Relay GlobalID resolution), [`LazyRelatedClassMixin`][filters-base] (re-exported from [`sets_mixins.py`][sets-mixins]), and [`RelatedFilter`][filters-base] (cross-relation filter traversal).
   - FilterSet classes (from [`filters/sets.py`][filters-sets]): [`FilterSet`][filters-sets] and [`FilterSetMetaclass`][filters-sets].
   - Consumer helper: [`filter_input_type`][filters-init].
   - Bound public surface: [`__all__`][filters-init] defines a static 16-tuple of public symbol names.
2. **Consumer Helper `filter_input_type`:**
   - [`filter_input_type`][filters-init] returns the Strawberry forward-reference type annotation `Annotated["<Name>FilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]` for custom resolvers declaring a `filter:` argument ([spec-027][spec-027] Decision 11).
   - Eagerly validates that `filterset_class` is a `FilterSet` subclass (raising `TypeError` on invalid types at resolver declaration time).
   - Delegates the validation, ledger recording, and `Annotated[..., strawberry.lazy(...)]` construction to [`django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`][utils-inputs].
3. **Helper-Referenced Ledger & Subsystem Clear Hook:**
   - Maintains [`_helper_referenced_filtersets`][filters-init] (`set[type[FilterSet]]`), which records every `FilterSet` passed to `filter_input_type`.
   - Provides [`_clear_helper_referenced_filtersets`][filters-init] to empty the ledger during global registry resets.
   - Registers [`_clear_helper_referenced_filtersets`][filters-init] via [`django_strawberry_framework/registry.py::register_subsystem_clear`][registry] under owner `"filters.helper_references"`.
   - Feeds finalizer phase 2.5 orphan detection ([`django_strawberry_framework/types/finalizer.py`][types-finalizer]), which compares `_helper_referenced_filtersets` against wired `Meta.filterset_class` definitions and raises `ConfigurationError` for orphan references not wired to a `DjangoType`.
4. **Deliberate Module Encapsulation (Non-Exported Internals):**
   - [`FilterArgumentsFactory`][filters-factories] (from `filters/factories.py`) is intentionally **not** re-exported in `filters/__init__.py` per [spec-027][spec-027] Decision 2. Advanced consumers and schema generation import it directly from `django_strawberry_framework.filters.factories`.
   - `INPUTS_MODULE_PATH` and `_input_type_name_for` (from `filters/inputs.py`) are imported for `filter_input_type` construction but omitted from `__all__`.

Connected behavior examined:
- [`django_strawberry_framework/filters/base.py`][filters-base]: Canonical definitions of `Filter` re-export and typed/range/array/list/globalid/related filter classes.
- [`django_strawberry_framework/filters/sets.py`][filters-sets]: `FilterSet` and `FilterSetMetaclass` implementations.
- [`django_strawberry_framework/filters/inputs.py`][filters-inputs]: Generated Strawberry input dataclass namespace and runtime normalizers.
- [`django_strawberry_framework/filters/factories.py`][filters-factories]: BFS factory `FilterArgumentsFactory` and dynamic-FilterSet cache.
- [`django_strawberry_framework/orders/__init__.py`][orders-init]: Sibling ordering subsystem facade mirroring `filters/__init__.py` (providing `order_input_type`, `_helper_referenced_ordersets`, `_clear_helper_referenced_ordersets`).
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Shared `build_lazy_input_annotation` implementing the shared forward-reference mechanics.
- [`django_strawberry_framework/registry.py`][registry]: Decentralized `register_subsystem_clear` registry.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Phase 2.5 schema finalizer executing orphan checks against `_helper_referenced_filtersets`.
- [`tests/filters/test_base.py`][test-filters-base], [`tests/filters/test_inputs.py`][test-filters-inputs], [`tests/filters/test_sets.py`][test-filters-sets], [`tests/filters/test_finalizer.py`][test-filters-finalizer]: Test coverage for filter primitives, inputs, sets, and orphan reference checks.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/filters/__init__.py --include-constants`):
- Parsed 1 target file, 115 lines, 2 definitions ([`_clear_helper_referenced_filtersets`][filters-init], [`filter_input_type`][filters-init]), 2 constants/module-level variables ([`_helper_referenced_filtersets`][filters-init], [`__all__`][filters-init]), and 5 imports.
- Verified reverse references across production code, finalizer orphan checks, and test suites.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `filters/__init__.py` and `orders/__init__.py` are parallel set-family subsystem facades ([spec-027][spec-027], [spec-028][spec-028]). Both maintain a `_helper_referenced_*sets` ledger, register a `_clear_helper_referenced_*sets` callback with [`register_subsystem_clear`][registry], and export a `*_input_type` consumer helper. All shared mechanics (eager base validation, ledger insertion, ForwardRef string annotation construction) are single-sited in [`django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`][utils-inputs]. Write flavors (`forms`, `mutations`, `rest_framework`) construct inputs directly rather than through lazy forward-ref helpers, but reuse the shared namespace management functions in [`utils/inputs.py`][utils-inputs].
2. **Sync and async twins:**
   Zero duplication. `filters/__init__.py` contains declarative classes, module ledgers, and type annotation helpers that are completely agnostic to the sync/async boundary. Strawberry resolvers (both `def` and `async def`) receive the identical `Annotated[..., strawberry.lazy(...)]` type annotations. Execution-side filtering on Django QuerySets is handled during query resolution without duplicating filter definitions.
3. **Derived rather than repeated knowledge:**
   `filter_input_type` derives the lazy input type name via `_input_type_name_for` (which delegates to `set_class.type_name_for()`) and the module path from `INPUTS_MODULE_PATH`, passing them into `build_lazy_input_annotation`. `_helper_referenced_filtersets` records only the referenced `FilterSet` class identity. `__all__` statically derives 1:1 from the public symbol inventory.
4. **Inverse and round-trip pairs:**
   Lifecycle pairing: `filter_input_type` populates `_helper_referenced_filtersets`, while `_clear_helper_referenced_filtersets` clears the ledger during `registry.clear()` to preserve test isolation.
   Schema finalization pairing: `filter_input_type` records a forward reference; finalizer phase 2.5 (`types/finalizer.py`) verifies that every referenced `FilterSet` is wired to a `DjangoType`, raising `ConfigurationError` for orphans, while `FilterArgumentsFactory` materializes the matching input classes into `filters.inputs`.
5. **Contracts restated in another medium:**
   The filter subsystem exports and `filter_input_type` contract are codified across:
   - Code: [`django_strawberry_framework/filters/__init__.py`][filters-init], [`django_strawberry_framework/filters/base.py`][filters-base], [`django_strawberry_framework/filters/sets.py`][filters-sets], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/utils/inputs.py`][utils-inputs];
   - Specifications: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] (Decisions 2, 3, 4, 11), [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028];
   - Test suites: [`tests/filters/test_base.py`][test-filters-base], [`tests/filters/test_inputs.py`][test-filters-inputs], [`tests/filters/test_sets.py`][test-filters-sets], [`tests/filters/test_finalizer.py`][test-filters-finalizer], [`tests/test_relay_connection.py`][test-relay-connection], [`tests/test_registry.py`][test-registry];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding a new filter primitive):** Introduce a new filter class (e.g. `DateRangeFilter` in `filters/base.py`) and surface it on the public subpackage API.
  - *Sites that must move:* Exactly 1 site in this facade: [`django_strawberry_framework/filters/__init__.py`][filters-init] (import from `.base` and append to `__all__`).
  - *Site count:* 1.
- **Posited change 2 (Renaming or deprecating an export):** Rename an existing filter export in the facade.
  - *Sites that must move:* Exactly 1 site in this facade: [`django_strawberry_framework/filters/__init__.py`][filters-init] (import statement and `__all__`).
  - *Site count:* 1.
- **Posited change 3 (Modifying lazy forward-reference format):** Update the `Annotated[..., strawberry.lazy(...)]` structure or type validation across set families.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`][utils-inputs] (zero edits to `filters/__init__.py` or `orders/__init__.py`).
  - *Site count:* 1.
- **Posited change 4 (Subsystem clear lifecycle registration):** Change how subsystem clearing callbacks are registered with the central registry.
  - *Sites that must move:* Exactly 1 site in this facade: [`django_strawberry_framework/filters/__init__.py`][filters-init] (`register_subsystem_clear`).
  - *Site count:* 1.

### Rejected candidates

1. **Re-exporting `FilterArgumentsFactory` from `django_strawberry_framework/filters/__init__.py`:**
   - Disproved per [spec-027][spec-027] Decision 2 (and sibling [spec-028][spec-028] Decision 2). `FilterArgumentsFactory` is an internal/advanced BFS input-class generation mechanism. It is canonically imported from `django_strawberry_framework.filters.factories`. Excluding it from `filters/__init__.py::__all__` keeps the consumer-facing facade uncluttered and focused on declarative primitives.
2. **Inlining `build_lazy_input_annotation` logic into `filter_input_type`:**
   - Disproved. The eager validation (`issubclass(..., expected_base)`), ledger tracking, and `Annotated[..., strawberry.lazy(...)]` return shape are identical between `filter_input_type` and `order_input_type` in [`orders/__init__.py`][orders-init]. Centralizing this logic in [`django_strawberry_framework/utils/inputs.py`][utils-inputs] prevents duplication and policy drift across set subsystems.
3. **Moving `_helper_referenced_filtersets` directly inside `registry.py`:**
   - Disproved. The decentralized registration hook (`register_subsystem_clear`) decouples `registry.py` from knowing about specific subsystem internals, preventing circular import dependencies and central registry bloat.

## Opportunities

None — `django_strawberry_framework/filters/__init__.py` is a clean, 115-line export facade and consumer-helper module. It exposes the filtering public API with high precision, routes forward-reference construction to the shared `build_lazy_input_annotation` utility, registers its clear lifecycle callback via `register_subsystem_clear`, and adheres strictly to architectural boundaries.

## Judgment

Zero-edit review. `filters/__init__.py` contains zero duplicate policy or unowned invariants. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/filters/__init__.py --review docs/dry/dry-file-filters____init__.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification conducted by Worker 2 for `django_strawberry_framework/filters/__init__.py`.

### Independent behavioral trace and boundary challenge

1. **Facade Boundary and Re-export Precision:**
   - Re-exports 14 foundational filter and mixin classes/functions from [`filters/base.py`][filters-base] and 2 classes from [`filters/sets.py`][filters-sets], along with [`filter_input_type`][filters-init], totaling 16 symbols accurately listed in [`__all__`][filters-init].
   - Verified that internal BFS mechanics ([`FilterArgumentsFactory`][filters-factories]) and dynamic input module internals (`INPUTS_MODULE_PATH`, `_input_type_name_for`) are deliberately omitted from `__all__` in accordance with [spec-027][spec-027] Decision 2, keeping the consumer facade clean.

2. **Set-Family Helper Symmetry (`filter_input_type` vs `order_input_type`):**
   - Verified cross-package symmetry with [`orders/__init__.py`][orders-init]. Both set families isolate forward-reference creation to a consumer helper ([`filter_input_type`][filters-init] / [`order_input_type`][orders-init]), delegate validation and annotation wrapping to [`django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`][utils-inputs], and maintain private reference ledgers for finalizer orphan checking.

3. **Decentralized Subsystem Clearing:**
   - [`_clear_helper_referenced_filtersets`][filters-init] is registered with [`register_subsystem_clear`][registry] under owner `"filters.helper_references"`. This decoupled design ensures `TypeRegistry.clear()` can flush all subsystem state without circular dependencies or tight coupling.

4. **Probing Matrix and Single-Edit-Site Counts:**
   - Verified that all 5 axes of the mandatory probing matrix are fully discharged with sound justifications.
   - Posited single-edit-site counts verified: adding/renaming exports, changing lazy forward-ref construction, and modifying clear lifecycle callbacks each move at exactly 1 single site.

5. **Tooling and Test Suite Execution:**
   - Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/filters/__init__.py --review docs/dry/dry-file-filters____init__.md --include-constants` — coverage verified clean.
   - Executed filter test suite (`tests/filters/`) — 538 tests passing.

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

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-factories]: ../../django_strawberry_framework/filters/factories.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[registry]: ../../django_strawberry_framework/registry.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

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
