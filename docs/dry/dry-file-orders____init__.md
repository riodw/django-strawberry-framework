# DRY review: `django_strawberry_framework/orders/__init__.py`

Status: verified

## System trace

`django_strawberry_framework/orders/__init__.py` is the public export facade and consumer-helper entry point for the framework's declarative ordering subsystem ([spec-028][spec-028]). It defines the subpackage's public API surface via `__all__`, re-exports the foundational relational order primitive, exposes the declarative `OrderSet` and `OrderSetMetaclass` classes, re-exports the `Ordering` direction enum, manages the consumer-helper reference ledger with decentralized registry clearing, and provides the `order_input_type` lazy forward-reference helper. It owns the following responsibilities:

1. **Subpackage Public Facade & Re-export Surface:**
   - Foundational relational primitive (from [`orders/base.py`][orders-base]): [`RelatedOrder`][orders-base] (the nested-path ordering primitive for cross-relation order traversal).
   - OrderSet classes (from [`orders/sets.py`][orders-sets]): [`OrderSet`][orders-sets] (declarative ordering class with `apply_sync` and `apply_async` pipeline) and [`OrderSetMetaclass`][orders-sets] (metaclass performing declaration collection and owner binding).
   - Direction enum (from [`orders/inputs.py`][orders-inputs]): [`Ordering`][orders-inputs] (Strawberry enum mapping `ASC`, `DESC`, and `NULLS_FIRST`/`NULLS_LAST` variants to Django `OrderBy` expressions).
   - Consumer helper: [`order_input_type`][orders-init] (lazy forward-reference annotation builder for custom resolvers).
   - Bound public surface: [`__all__`][orders-init] defines a static 5-tuple of public symbol names (`"OrderSet"`, `"OrderSetMetaclass"`, `"Ordering"`, `"RelatedOrder"`, `"order_input_type"`).
2. **Consumer Helper `order_input_type`:**
   - [`order_input_type`][orders-init] returns the canonical Strawberry forward-reference type annotation `Annotated["<Name>OrderInputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]` for custom resolvers declaring an `orderBy:` argument ([spec-028][spec-028] Decision 11).
   - Resolvers wrap the return value as `list[order_input_type(MyOrder)] | None` to yield the GraphQL schema shape `orderBy: [MyOrderInputType!]` (list-of-non-null per [spec-028][spec-028] Decision 5).
   - Validates eagerly that `orderset_class` is an `OrderSet` subclass, raising `TypeError` on invalid arguments at resolver declaration time rather than deferring failures to schema build time.
   - Delegates eager validation, ledger recording, and `Annotated[..., strawberry.lazy(...)]` construction to the centralized helper [`django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`][utils-inputs].
3. **Helper-Referenced Ledger & Subsystem Clear Hook:**
   - Maintains [`_helper_referenced_ordersets`][orders-init] (`set[type[OrderSet]]`), recording every `OrderSet` passed to `order_input_type`.
   - Defines [`_clear_helper_referenced_ordersets`][orders-init] to flush the ledger during global registry resets.
   - Registers [`_clear_helper_referenced_ordersets`][orders-init] via [`django_strawberry_framework/registry.py::register_subsystem_clear`][registry] under owner `"orders.helper_references"`.
   - Feeds schema finalizer phase 2.5 orphan validation ([`django_strawberry_framework/types/finalizer.py`][types-finalizer]), which cross-checks `_helper_referenced_ordersets` against the set of `Meta.orderset_class`-wired `DjangoType` definitions and raises `ConfigurationError` for any orphaned references.
4. **Deliberate Module Encapsulation (Non-Exported Internals):**
   - [`OrderArgumentsFactory`][orders-factories] (from `orders/factories.py`) is intentionally **not** re-exported in `orders/__init__.py` per [spec-028][spec-028] Decision 2 (mirroring the filter twin's exclusion of `FilterArgumentsFactory` per [spec-027][spec-027] Decision 2). Advanced consumers import it directly from `django_strawberry_framework.orders.factories`.
   - `INPUTS_MODULE_PATH` and `_input_type_name_for` (from `orders/inputs.py`) are imported at module scope for `order_input_type` construction but omitted from `__all__`.

Connected behavior examined:
- [`django_strawberry_framework/orders/base.py`][orders-base]: Canonical definition of `RelatedOrder` inheriting from `RelatedSetTargetMixin` ([`django_strawberry_framework/sets_mixins.py`][sets-mixins]).
- [`django_strawberry_framework/orders/sets.py`][orders-sets]: Declarative `OrderSet` and `OrderSetMetaclass` implementations, field promotion, and ordering execution pipeline (`apply_sync`, `apply_async`).
- [`django_strawberry_framework/orders/inputs.py`][orders-inputs]: `Ordering` enum, module path `INPUTS_MODULE_PATH`, input type name resolver `_input_type_name_for`, and module-global input class materialization.
- [`django_strawberry_framework/orders/factories.py`][orders-factories]: BFS factory `OrderArgumentsFactory` and dynamic-OrderSet cache.
- [`django_strawberry_framework/filters/__init__.py`][filters-init]: Sibling filtering subsystem facade mirroring `orders/__init__.py` (providing `filter_input_type`, `_helper_referenced_filtersets`, `_clear_helper_referenced_filtersets`).
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Centralized `build_lazy_input_annotation` implementing the shared forward-reference validation and construction mechanics across set families.
- [`django_strawberry_framework/registry.py`][registry]: Decentralized `register_subsystem_clear` hook mechanism.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Phase 2.5 schema finalizer executing orphan checks against `_helper_referenced_ordersets`.
- [`django_strawberry_framework/connection.py`][connection]: Connection field integration wiring `orderset_class` and ordering arguments into GraphQL schema.
- [`tests/orders/test_base.py`][test-orders-base], [`tests/orders/test_inputs.py`][test-orders-inputs], [`tests/orders/test_sets.py`][test-orders-sets], [`tests/orders/test_finalizer.py`][test-orders-finalizer], [`tests/orders/test_composition.py`][test-orders-composition], [`tests/orders/test_factories.py`][test-orders-factories], [`tests/test_connection.py`][test-connection], [`tests/test_registry.py`][test-registry]: Comprehensive test suite verifying orders public API, helper annotations, orphan detection, and clearing lifecycle.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/orders/__init__.py --include-constants`):
- Parsed 1 target file, 102 lines, 2 definitions ([`_clear_helper_referenced_ordersets`][orders-init], [`order_input_type`][orders-init]), 2 constants/module-level variables ([`_helper_referenced_ordersets`][orders-init], [`__all__`][orders-init]), and 5 imports.
- Verified reverse references across production code, finalizer orphan checks, and test suites.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `orders/__init__.py` and `filters/__init__.py` are parallel set-family subsystem facades ([spec-027][spec-027], [spec-028][spec-028]). Both maintain a `_helper_referenced_*sets` ledger, register a `_clear_helper_referenced_*sets` callback with [`register_subsystem_clear`][registry], and export a `*_input_type` consumer helper. All shared mechanics (eager base validation, ledger insertion, `ForwardRef` string annotation construction) are single-sited in [`django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`][utils-inputs]. Both keep their respective BFS factory classes (`OrderArgumentsFactory`, `FilterArgumentsFactory`) out of `__all__` to keep the public surface minimal and declarative. Write flavors (`forms`, `mutations`, `rest_framework`) construct inputs directly without lazy forward-ref helpers, but reuse the shared namespace management functions in [`utils/inputs.py`][utils-inputs].
2. **Sync and async twins:**
   Zero duplication. `orders/__init__.py` contains declarative classes, module ledgers, and type annotation helpers that are completely agnostic to the sync/async boundary. Strawberry resolvers (both synchronous `def` and asynchronous `async def`) receive the identical `Annotated[..., strawberry.lazy(...)]` type annotations. Execution-side QuerySet ordering is handled via `OrderSet.apply_sync` / `OrderSet.apply_async` in [`orders/sets.py`][orders-sets] without duplicating export definitions.
3. **Derived rather than repeated knowledge:**
   `order_input_type` derives the lazy input type name via `_input_type_name_for` (which delegates to `orderset_class.type_name_for()`) and the module path from `INPUTS_MODULE_PATH`, passing them into `build_lazy_input_annotation`. `_helper_referenced_ordersets` records only the referenced `OrderSet` class identity. `__all__` statically derives 1:1 from the subpackage public symbol inventory.
4. **Inverse and round-trip pairs:**
   Lifecycle pairing: `order_input_type` populates `_helper_referenced_ordersets`, while `_clear_helper_referenced_ordersets` clears the ledger during `registry.clear()` to guarantee test isolation.
   Schema finalization pairing: `order_input_type` records a forward reference; finalizer phase 2.5 ([`types/finalizer.py`][types-finalizer]) verifies that every referenced `OrderSet` is wired to a `DjangoType`, raising `ConfigurationError` for orphans, while `OrderArgumentsFactory` materializes the matching input classes into `orders.inputs`.
5. **Contracts restated in another medium:**
   The ordering subsystem exports and `order_input_type` contract are codified across:
   - Code: [`django_strawberry_framework/orders/__init__.py`][orders-init], [`django_strawberry_framework/orders/base.py`][orders-base], [`django_strawberry_framework/orders/inputs.py`][orders-inputs], [`django_strawberry_framework/orders/sets.py`][orders-sets], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/utils/inputs.py`][utils-inputs], [`django_strawberry_framework/registry.py`][registry];
   - Specifications: [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028] (Decisions 2, 5, 9, 11, 12), [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027];
   - Test suites: [`tests/orders/test_base.py`][test-orders-base], [`tests/orders/test_inputs.py`][test-orders-inputs], [`tests/orders/test_sets.py`][test-orders-sets], [`tests/orders/test_finalizer.py`][test-orders-finalizer], [`tests/orders/test_composition.py`][test-orders-composition], [`tests/orders/test_factories.py`][test-orders-factories], [`tests/test_connection.py`][test-connection], [`tests/test_registry.py`][test-registry];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding a new order primitive):** Introduce a new ordering primitive class in `orders/base.py` and surface it on the public subpackage API.
  - *Sites that must move:* Exactly 1 site in this facade: [`django_strawberry_framework/orders/__init__.py`][orders-init] (import from `.base` and append to `__all__`).
  - *Site count:* 1.
- **Posited change 2 (Renaming or deprecating an export):** Rename an existing export in the facade.
  - *Sites that must move:* Exactly 1 site in this facade: [`django_strawberry_framework/orders/__init__.py`][orders-init] (import statement and `__all__`).
  - *Site count:* 1.
- **Posited change 3 (Modifying lazy forward-reference format):** Update the `Annotated[..., strawberry.lazy(...)]` structure or type validation across set families.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`][utils-inputs] (zero edits to `orders/__init__.py` or `filters/__init__.py`).
  - *Site count:* 1.
- **Posited change 4 (Subsystem clear lifecycle registration):** Change how subsystem clearing callbacks are registered with the central registry.
  - *Sites that must move:* Exactly 1 site in this facade: [`django_strawberry_framework/orders/__init__.py`][orders-init] (`register_subsystem_clear`).
  - *Site count:* 1.

### Rejected candidates

1. **Re-exporting `OrderArgumentsFactory` from `django_strawberry_framework/orders/__init__.py`:**
   - Disproved per [spec-028][spec-028] Decision 2 (and sibling [spec-027][spec-027] Decision 2). `OrderArgumentsFactory` is an internal BFS input-class generation mechanism. It is canonically imported from `django_strawberry_framework.orders.factories`. Excluding it from `orders/__init__.py::__all__` keeps the consumer facade uncluttered and focused on declarative primitives.
2. **Inlining `build_lazy_input_annotation` logic into `order_input_type`:**
   - Disproved. The eager validation (`issubclass(..., expected_base)`), ledger tracking, and `Annotated[..., strawberry.lazy(...)]` return shape are identical between `order_input_type` and `filter_input_type` in [`filters/__init__.py`][filters-init]. Centralizing this logic in [`django_strawberry_framework/utils/inputs.py`][utils-inputs] prevents duplication and policy drift across set subsystems.
3. **Moving `_helper_referenced_ordersets` directly inside `registry.py`:**
   - Disproved. The decentralized registration hook (`register_subsystem_clear`) decouples `registry.py` from knowing about specific subsystem internals, preventing circular import dependencies and central registry bloat.

## Opportunities

None — `django_strawberry_framework/orders/__init__.py` is a clean, 102-line export facade and consumer-helper module. It exposes the ordering public API with high precision, routes forward-reference construction to the shared `build_lazy_input_annotation` utility, registers its clear lifecycle callback via `register_subsystem_clear`, and adheres strictly to architectural boundaries.

## Judgment

Zero-edit review. `orders/__init__.py` contains zero duplicate policy or unowned invariants. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/orders/__init__.py --review docs/dry/dry-file-orders____init__.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

I have independently reviewed `django_strawberry_framework/orders/__init__.py` and verified Worker 1's DRY analysis across all system boundaries, contracts, and duplication axes:

1. **Subpackage Facade & Public Export Parity:**
   - Evaluated the public export tuple `__all__ = ("OrderSet", "OrderSetMetaclass", "Ordering", "RelatedOrder", "order_input_type")`.
   - Verified 1:1 structural symmetry with `django_strawberry_framework/filters/__init__.py`: both facades re-export core relational primitives (`RelatedOrder` / `RelatedFilter`), declarative set classes and metaclasses (`OrderSet`, `OrderSetMetaclass` / `FilterSet`, `FilterSetMetaclass`), direction/type enums (`Ordering`), and lazy consumer annotation helpers (`order_input_type` / `filter_input_type`).
   - Verified intentional exclusion of the BFS generation factory (`OrderArgumentsFactory`) from `__init__.py` per [spec-028][spec-028] Decision 2 (mirroring the exclusion of `FilterArgumentsFactory` per [spec-027][spec-027] Decision 2).
   - Confirmed module-scope availability of `INPUTS_MODULE_PATH` and `_input_type_name_for` while excluding them from `__all__` per framework encapsulation conventions.

2. **Consumer Helper Consolidation:**
   - Inspected `order_input_type` implementation and confirmed full DRY consolidation: eager validation against `OrderSet`, ledger recording, and `Annotated[..., strawberry.lazy(...)]` construction are single-sited in [`django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`][utils-inputs].
   - Verified that the resolver consumer contract (`list[order_input_type(MyOrder)] | None` yielding GraphQL argument shape `orderBy: [MyOrderInputType!]`) is strictly preserved.

3. **Ledger Lifecycle & Registry Seam:**
   - Confirmed `_helper_referenced_ordersets` registration with [`register_subsystem_clear`][registry] under owner `"orders.helper_references"`.
   - Verified that `_clear_helper_referenced_ordersets` resets the module ledger during global `TypeRegistry.clear()` calls, preventing cross-test pollution.
   - Verified phase 2.5 schema finalizer orphan validation ([`types/finalizer.py`][types-finalizer]), ensuring that references to un-wired ordersets trigger `ConfigurationError`.

4. **Duplication Probing Matrix & Single-Edit-Site Invariants:**
   - Confirmed all 5 probing matrix axes are thoroughly discharged with valid architectural rationales.
   - Verified posited changes 1–4 each require exactly 1 edit site.

5. **Tooling and Automated Test Verification:**
   - Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/orders/__init__.py --review docs/dry/dry-file-orders____init__.md --include-constants` — passed (2 target definitions, 0 uncovered topics).
   - Executed full test suite `pytest tests/orders/ tests/test_registry.py --no-cov` — all 238 tests passed cleanly.

Conclusion: Zero-edit DRY review confirmed. Marked as `Status: verified`.

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
[connection]: ../../django_strawberry_framework/connection.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[orders-base]: ../../django_strawberry_framework/orders/base.py
[orders-factories]: ../../django_strawberry_framework/orders/factories.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->
[test-connection]: ../../tests/test_connection.py
[test-orders-base]: ../../tests/orders/test_base.py
[test-orders-composition]: ../../tests/orders/test_composition.py
[test-orders-factories]: ../../tests/orders/test_factories.py
[test-orders-finalizer]: ../../tests/orders/test_finalizer.py
[test-orders-inputs]: ../../tests/orders/test_inputs.py
[test-orders-sets]: ../../tests/orders/test_sets.py
[test-registry]: ../../tests/test_registry.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
