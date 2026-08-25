# DRY review: `django_strawberry_framework/orders/factories.py`

Status: verified

## System trace

`django_strawberry_framework/orders/factories.py` implements Layer 5 (the BFS input arguments factory) and Layer 6 (the dynamic `OrderSet` generator and cache) of the order subsystem ([spec-028][spec-028]).

It owns the following architectural responsibilities:

1. **BFS Input Arguments Factory:**
   - [`OrderArgumentsFactory`][orders-factories] (`django_strawberry_framework/orders/factories.py::OrderArgumentsFactory`): Subclasses [`GeneratedInputArgumentsFactory`][utils-inputs] to traverse reachable [`OrderSet`][orders-sets] graphs in deterministic breadth-first order and construct corresponding Strawberry input types.
   - Class-Level Caches:
     - [`OrderArgumentsFactory.input_object_types`][orders-factories]: Maps generated type names to built Strawberry input classes.
     - [`OrderArgumentsFactory._type_orderset_registry`][orders-factories]: Tracks source `OrderSet` classes to detect duplicate-name collisions.
   - Family Attributes: Configures [`_collision_registry_attr`][orders-factories], [`_factory_label`][orders-factories], [`_family_label`][orders-factories], [`_rename_noun`][orders-factories], [`_related_attr`][orders-factories], and [`_related_target_attr`][orders-factories].
   - Triples Builder: [`OrderArgumentsFactory._build_input_triples`][orders-factories] delegates to [`_build_input_fields`][orders-inputs] without synthesizing operator bags (since orders have no `and_`/`or_`/`not_` operators).

2. **Dynamic OrderSet Cache & Construction (Layer 6):**
   - [`_dynamic_orderset_cache`][orders-factories] (`django_strawberry_framework/orders/factories.py::_dynamic_orderset_cache`): Module-level dictionary caching dynamically synthesized `OrderSet` classes keyed by canonical meta tuples.
   - [`_RESERVED_FACTORY_KEYS`][orders-factories] (`django_strawberry_framework/orders/factories.py::_RESERVED_FACTORY_KEYS`): Frozenset of reserved kwargs (`{"orderset_base_class"}`).
   - Factory Construction: [`_get_orderset_class`][orders-factories] created via [`make_dynamic_set_getter`][utils-inputs].
   - Public Dynamic Setter: [`get_orderset_class`][orders-factories] exposes the dynamic class resolver.

Connected behavior examined:
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Houses the single-sited [`GeneratedInputArgumentsFactory`][utils-inputs] and [`make_dynamic_set_getter`][utils-inputs] engines shared with [`filters/factories.py`][filters-factories].
- [`django_strawberry_framework/orders/inputs.py`][orders-inputs]: Implements field conversion and field triple construction ([`_build_input_fields`][orders-inputs]).
- [`django_strawberry_framework/orders/sets.py`][orders-sets]: Defines [`OrderSet`][orders-sets] and metaclass expansion.
- [`django_strawberry_framework/filters/factories.py`][filters-factories]: Sibling filter input factory sharing the same base infrastructure.
- [`tests/orders/test_factories.py`][test-orders-factories]: Comprehensive test suite covering BFS generation, cycle handling, collisions, idempotency, and dynamic class synthesis.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/orders/factories.py --include-constants`):
- Parsed 1 target file, 156 lines.
- Inventory of symbols (14 definitions):
  - 3 constants: [`_dynamic_orderset_cache`][orders-factories], [`_RESERVED_FACTORY_KEYS`][orders-factories], [`_get_orderset_class`][orders-factories].
  - 1 class: [`OrderArgumentsFactory`][orders-factories].
  - 8 class attributes: [`OrderArgumentsFactory.input_object_types`][orders-factories], [`OrderArgumentsFactory._type_orderset_registry`][orders-factories], [`OrderArgumentsFactory._collision_registry_attr`][orders-factories], [`OrderArgumentsFactory._factory_label`][orders-factories], [`OrderArgumentsFactory._family_label`][orders-factories], [`OrderArgumentsFactory._rename_noun`][orders-factories], [`OrderArgumentsFactory._related_attr`][orders-factories], [`OrderArgumentsFactory._related_target_attr`][orders-factories].
  - 1 method: [`OrderArgumentsFactory._build_input_triples`][orders-factories].
  - 1 function: [`get_orderset_class`][orders-factories].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `OrderArgumentsFactory` mirrors `FilterArgumentsFactory` in [`filters/factories.py`][filters-factories], but all BFS queue mechanics, collision checks, caching, and recursion safeguards are single-sited in [`GeneratedInputArgumentsFactory`][utils-inputs] in `django_strawberry_framework/utils/inputs.py`. `OrderArgumentsFactory` configures the order family labels, related attribute slots, and implements `_build_input_triples` (which omits filter logic bags like `and_`/`or_`/`not_`). Similarly, dynamic class creation is delegated to [`make_dynamic_set_getter`][utils-inputs] from `utils/inputs.py`.

2. **Sync and async twins:**
   Zero duplication. Class building, metaclass inspection, and BFS AST traversal are purely synchronous and in-memory.

3. **Derived rather than repeated knowledge:**
   Field triples are derived directly from `OrderSet.get_fields()` via [`_build_input_fields`][orders-inputs] in `orders/inputs.py`, ensuring GraphQL input annotations stay strictly downstream of runtime order field declarations.

4. **Inverse and round-trip pairs:**
   [`OrderArgumentsFactory.input_object_types`][orders-factories] and [`OrderArgumentsFactory._type_orderset_registry`][orders-factories] maintain paired mappings from class name to built type and source orderset class.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/orders/factories.py`][orders-factories], [`django_strawberry_framework/utils/inputs.py`][utils-inputs], [`django_strawberry_framework/orders/inputs.py`][orders-inputs], [`django_strawberry_framework/orders/sets.py`][orders-sets];
   - Specifications: [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028];
   - Test suites: [`tests/orders/test_factories.py`][test-orders-factories];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adjusting the BFS queue traversal order or cycle-detection logic):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/inputs.py`][utils-inputs] ([`GeneratedInputArgumentsFactory`][utils-inputs]).
  - *Propagation count:* 0 in `orders/factories.py`.
- **Posited change 2 (Altering the synthetic dynamic OrderSet class naming convention or cache key hashing):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/inputs.py`][utils-inputs] ([`make_dynamic_set_getter`][utils-inputs]).
  - *Propagation count:* 0 in `orders/factories.py`.
- **Posited change 3 (Modifying the order family collision registry attribute name or factory label):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/orders/factories.py`][orders-factories] ([`OrderArgumentsFactory._collision_registry_attr`][orders-factories]).
  - *Propagation count:* 0 in production code.

### Rejected candidates

1. **Duplicating BFS traversal and type generation in `OrderArgumentsFactory`:**
   - Disproved per [spec-028][spec-028]. Extracting `GeneratedInputArgumentsFactory` into `utils/inputs.py` eliminates parallel BFS traversal implementations across filters and orders.
2. **Sharing a single dynamic set cache dict between filters and orders:**
   - Disproved per [spec-028][spec-028]. FilterSet and OrderSet maintain isolated family caches so an order cache clear cannot inadvertently evict filter classes or cross-pollinate generated types.

## Opportunities

None — `django_strawberry_framework/orders/factories.py` is a clean, 156-line subclass and layer configuration module delegating all mechanics to `django_strawberry_framework/utils/inputs.py`.

## Judgment

Verified. `orders/factories.py` exhibits zero duplicate code and complete policy consolidation through `utils/inputs.py`. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/orders/factories.py --review docs/dry/dry-file-orders__factories.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/orders/factories.py`][orders-factories] and Worker 1's DRY review.

1. **Subclass & Template Specialization:**
   - Verified that `OrderArgumentsFactory` cleanly subclasses `GeneratedInputArgumentsFactory` without duplicating BFS traversal, cycle detection, or collision checking.
   - Verified that `_get_orderset_class` is instantiated using `make_dynamic_set_getter` from `utils/inputs.py`.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/orders/factories.py --review docs/dry/dry-file-orders__factories.md --include-constants`. 100% coverage across all 14 definitions.

Confirmed: `django_strawberry_framework/orders/factories.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md

<!-- package source -->
[filters-factories]: ../../django_strawberry_framework/filters/factories.py
[orders-factories]: ../../django_strawberry_framework/orders/factories.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests -->
[test-orders-factories]: ../../tests/orders/test_factories.py
