# DRY review: `django_strawberry_framework/orders/base.py`

Status: verified

## System trace

`django_strawberry_framework/orders/base.py` defines the nested-path ordering primitive [`RelatedOrder`][orders-base] ([spec-028][spec-028]). It enables ordering over relational paths by targeting another [`OrderSet`][orders-sets] either by class reference, fully-qualified module import string, or same-module unqualified class name.

It owns the following architectural responsibilities:

1. **Relational Ordering Primitive:**
   - [`RelatedOrder`][orders-base] (`django_strawberry_framework/orders/base.py::RelatedOrder`): Subclasses [`RelatedSetTargetMixin`][sets-mixins] to participate in metaclass collection, owner binding, and lazy class resolution.
   - Slot Parameterization: Configures [`RelatedOrder._target_attr`][orders-base] (`"_orderset"`) and [`RelatedOrder._owner_attr`][orders-base] (`"bound_orderset"`).
   - Initialization: [`RelatedOrder.__init__`][orders-base] stores the target `orderset` (class, string path, or unqualified name) and optional `field_name`.
   - Idempotent Binding: [`RelatedOrder.bind_orderset`][orders-base] delegates to [`RelatedSetTargetMixin._bind_owner`][sets-mixins] to idempotently record the owning `OrderSet`.
   - Lazy Resolution: [`RelatedOrder.orderset`][orders-base] (`django_strawberry_framework/orders/base.py::RelatedOrder.orderset`) property resolves target class references on first access via [`RelatedSetTargetMixin._resolved_target`][sets-mixins] (delegating to [`LazyRelatedClassMixin.resolve_lazy_class`][sets-mixins]) and supports reassignment via [`RelatedSetTargetMixin._set_target`][sets-mixins].

Connected behavior examined:
- [`django_strawberry_framework/sets_mixins.py`][sets-mixins]: Houses neutral base mixins [`RelatedSetTargetMixin`][sets-mixins] and [`LazyRelatedClassMixin`][sets-mixins], preventing coupling between `orders` and `filters`.
- [`django_strawberry_framework/orders/sets.py`][orders-sets]: [`OrderSetMetaclass`][orders-sets] collects [`RelatedOrder`][orders-base] declarations, binds them via `bind_orderset`, and expands them into nested ordering fields.
- [`django_strawberry_framework/orders/factories.py`][orders-factories]: Converts resolved related orders into GraphQL ordering input fields.
- [`django_strawberry_framework/filters/base.py`][filters-base]: Houses the sibling primitive [`RelatedFilter`][filters-base], which consumes the identical [`RelatedSetTargetMixin`][sets-mixins] substrate.
- [`tests/orders/test_base.py`][test-orders-base]: Unit test suite verifying class resolution, absolute string imports, unqualified module-relative resolution, `ImportError` propagation, idempotency, and MRO neutrality.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/orders/base.py --include-constants`):
- Parsed 1 target file, 86 lines.
- Inventory of symbols (6 definitions):
  - 1 class: [`RelatedOrder`][orders-base].
  - 2 class attributes: [`RelatedOrder._target_attr`][orders-base], [`RelatedOrder._owner_attr`][orders-base].
  - 2 methods: [`RelatedOrder.__init__`][orders-base], [`RelatedOrder.bind_orderset`][orders-base].
  - 1 property: [`RelatedOrder.orderset`][orders-base] (getter and setter in `django_strawberry_framework/orders/base.py::RelatedOrder.orderset`).

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `RelatedOrder` mirrors the public API style of [`RelatedFilter`][filters-base], but both delegate their core binding, lazy target resolution, and owner association to the neutral [`RelatedSetTargetMixin`][sets-mixins] in `django_strawberry_framework/sets_mixins.py`. `RelatedOrder` specifies its own parameterization `_target_attr = "_orderset"` and `_owner_attr = "bound_orderset"`, maintaining identical semantics without duplicating resolution or binding logic.

2. **Sync and async twins:**
   Zero duplication. `RelatedOrder` operates entirely at schema definition and metaclass expansion time; it does not perform asynchronous runtime operations. Resolving order set classes and binding parent sets is synchronous and in-memory.

3. **Derived rather than repeated knowledge:**
   Target class resolution derives dynamically from [`LazyRelatedClassMixin.resolve_lazy_class`][sets-mixins]. String resolution dynamically inspects the caller/owner's `__module__` rather than requiring hardcoded module registries.

4. **Inverse and round-trip pairs:**
   [`RelatedOrder.orderset`][orders-base] property getter and setter form a symmetric pair delegating to `_resolved_target()` and `_set_target()`. [`RelatedOrder.bind_orderset`][orders-base] provides idempotent binding via `_bind_owner`.

5. **Contracts restated in another medium:**
   The `RelatedOrder` contracts are codified across:
   - Code: [`django_strawberry_framework/orders/base.py`][orders-base], [`django_strawberry_framework/sets_mixins.py`][sets-mixins], [`django_strawberry_framework/orders/sets.py`][orders-sets], [`django_strawberry_framework/orders/factories.py`][orders-factories];
   - Specifications: [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028];
   - Test suites: [`tests/orders/test_base.py`][test-orders-base];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Modifying the lazy target resolution fallback mechanism):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/sets_mixins.py`][sets-mixins] ([`LazyRelatedClassMixin.resolve_lazy_class`][sets-mixins]).
  - *Propagation count:* 0 in `orders/base.py`.
- **Posited change 2 (Altering the owner binding idempotency rule or sentinel semantics):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/sets_mixins.py`][sets-mixins] ([`RelatedSetTargetMixin._bind_owner`][sets-mixins]).
  - *Propagation count:* 0 in `orders/base.py`.
- **Posited change 3 (Renaming the internal attribute slot used to store the unbound orderset string or type):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/orders/base.py`][orders-base] ([`RelatedOrder._target_attr`][orders-base]).
  - *Propagation count:* 0 in production code.

### Rejected candidates

1. **Re-implementing lazy class resolution directly in `RelatedOrder` instead of inheriting `RelatedSetTargetMixin`:**
   - Disproved per [spec-028][spec-028]. Extracting `RelatedSetTargetMixin` into neutral `sets_mixins.py` ensures that `FilterSet`, `OrderSet`, and future set families share one tested resolution engine without importing from each other.
2. **Coupling `RelatedOrder` to `django_strawberry_framework/filters/base.py`:**
   - Disproved per [spec-028][spec-028]. Importing through `filters.base` would load the entire filter subsystem just to build orders, re-coupling sibling Layer-3 packages.

## Opportunities

None — `django_strawberry_framework/orders/base.py` is a compact (86 lines), focused, and single-purpose module that cleanly delegates shared set-target mechanics to `django_strawberry_framework/sets_mixins.py`.

## Judgment

Verified. `orders/base.py` exhibits zero duplicate code and complete policy consolidation through `sets_mixins.py`. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/orders/base.py --review docs/dry/dry-file-orders__base.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/orders/base.py`][orders-base] and Worker 1's DRY review.

1. **Neutral Inheritance & Import Architecture:**
   - Audited imports: confirmed `orders/base.py` imports only from neutral `..sets_mixins`, maintaining total decoupling from `django_strawberry_framework/filters/`.
   - Verified that `RelatedOrder` subclasses `RelatedSetTargetMixin` and supplies `_target_attr = "_orderset"` and `_owner_attr = "bound_orderset"`.
2. **Single-Edit-Site & Matrix Verification:**
   - Confirmed all 5 probing matrix axes are discharged with valid architectural rationales.
   - Verified that lazy string resolution and binding idempotency have single authoritative ownership in `sets_mixins.py`.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/orders/base.py --review docs/dry/dry-file-orders__base.md --include-constants`. 100% coverage across all 6 definitions.

Confirmed: `django_strawberry_framework/orders/base.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md

<!-- package source -->
[filters-base]: ../../django_strawberry_framework/filters/base.py
[orders-base]: ../../django_strawberry_framework/orders/base.py
[orders-factories]: ../../django_strawberry_framework/orders/factories.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py

<!-- tests -->
[test-orders-base]: ../../tests/orders/test_base.py
