# DRY review: `django_strawberry_framework/orders/sets.py`

Status: verified

## System trace

`django_strawberry_framework/orders/sets.py` defines the metaclass [`OrderSetMetaclass`][orders-sets] and consumer-facing class [`OrderSet`][orders-sets] ([spec-028][spec-028]).

It owns the following architectural responsibilities:

1. **Metaclass & Declaration Collection:**
   - [`OrderSetMetaclass`][orders-sets] (`django_strawberry_framework/orders/sets.py::OrderSetMetaclass`): Metaclass discovering and binding [`RelatedOrder`][orders-base] declarations.
   - Metaclass Constructor: [`OrderSetMetaclass.__new__`][orders-sets] promotes `Meta.fields` via [`promote_set_meta_fields`][utils-inputs] and collects declarations via [`collect_related_declarations`][sets-mixins].

2. **OrderSet Declaration Foundation:**
   - [`OrderSet`][orders-sets] (`django_strawberry_framework/orders/sets.py::OrderSet`): Foundation class inheriting from [`ClassBasedTypeNameMixin`][sets-mixins] and [`ActiveInputPermissionMixin`][sets-mixins].
   - Binding & Cache Slots: [`OrderSet._owner_definition`][orders-sets], [`OrderSet._expanded_fields`][orders-sets], [`OrderSet._is_expanding_fields`][orders-sets].
   - Subsystem Descriptors:
     - [`OrderSet._lifecycle`][orders-sets]: [`SetLifecycleAttrs`][sets-mixins] descriptor parameterizing expansion cache and guard slots.
     - [`OrderSet._permission`][orders-sets]: [`ActiveInputPermissionAttrs`][sets-mixins] descriptor parameterizing active input permission checks.

3. **Field Expansion & Normalization:**
   - Field Expansion: [`OrderSet.get_fields`][orders-sets] uses [`expanded_once`][sets-mixins] and [`should_cache_expansion`][sets-mixins] to return expanded fields.
   - Meta Expansion: [`OrderSet._expand_meta_fields`][orders-sets] reads `Meta.fields` via [`read_set_meta_fields`][utils-inputs], validates paths via [`classify_path`][utils-relations], and handles `"__all__"` via [`_get_concrete_field_names_for_order`][orders-inputs].
   - Normalization Delegate: [`OrderSet._normalize_input`][orders-sets] delegates to [`normalize_input_value`][orders-inputs].
   - Permission Preparation: [`OrderSet._prepare_permission_input`][orders-sets] ensures field specs are populated before permission checking.
   - Flat Orders Extraction: [`OrderSet.get_flat_orders`][orders-sets] flattens normalized order structures.

4. **Order Resolution & Apply Pipeline:**
   - Expression Resolution: [`OrderSet._resolve_order_expressions`][orders-sets] translates flat orders into Django `OrderBy` expressions, constructing `Min`/`Max` aggregate annotations for to-many paths ([`_path_traverses_to_many`][utils-relations]) to prevent row duplication ([`spec-030`][spec-030]).
   - Shared Apply Pipeline: [`OrderSet._apply_orderings`][orders-sets] runs normalization, expression resolution, annotation, and `order_by` attachment.
   - Synchronous Entry Point: [`OrderSet.apply_sync`][orders-sets] evaluates permissions and executes `_apply_orderings`.
   - Asynchronous Entry Point: [`OrderSet.apply_async`][orders-sets] executes permissions in [`run_in_one_sync_boundary`][utils-querysets] before calling `_apply_orderings`.

Connected behavior examined:
- [`django_strawberry_framework/sets_mixins.py`][sets-mixins]: Houses neutral mixins ([`ClassBasedTypeNameMixin`][sets-mixins], [`ActiveInputPermissionMixin`][sets-mixins]) and helpers ([`collect_related_declarations`][sets-mixins], [`expanded_once`][sets-mixins], [`should_cache_expansion`][sets-mixins], [`SetLifecycleAttrs`][sets-mixins], [`ActiveInputPermissionAttrs`][sets-mixins]).
- [`django_strawberry_framework/orders/base.py`][orders-base]: Defines [`RelatedOrder`][orders-base].
- [`django_strawberry_framework/orders/inputs.py`][orders-inputs]: Defines [`Ordering`][orders-inputs] and [`normalize_input_value`][orders-inputs].
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Houses [`promote_set_meta_fields`][utils-inputs] and [`read_set_meta_fields`][utils-inputs].
- [`django_strawberry_framework/utils/relations.py`][utils-relations]: Houses path classification and to-many detection ([`classify_path`][utils-relations], [`path_traverses_to_many`][utils-relations]).
- [`django_strawberry_framework/filters/sets.py`][filters-sets]: Sibling filterset foundation consuming identical neutral substrates.
- [`tests/orders/test_sets.py`][test-orders-sets]: Comprehensive test suite covering declaration, inheritance, expansion, sync/async apply, and permission gates.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/orders/sets.py --include-constants`):
- Parsed 1 target file, 508 lines.
- Inventory of symbols (17 definitions):
  - 2 classes: [`OrderSetMetaclass`][orders-sets], [`OrderSet`][orders-sets].
  - 5 class attributes: [`OrderSet._owner_definition`][orders-sets], [`OrderSet._expanded_fields`][orders-sets], [`OrderSet._is_expanding_fields`][orders-sets], [`OrderSet._lifecycle`][orders-sets], [`OrderSet._permission`][orders-sets].
  - 1 metaclass method: [`OrderSetMetaclass.__new__`][orders-sets].
  - 9 classmethods: [`OrderSet.get_fields`][orders-sets], [`OrderSet._expand_meta_fields`][orders-sets], [`OrderSet._normalize_input`][orders-sets], [`OrderSet._prepare_permission_input`][orders-sets], [`OrderSet.get_flat_orders`][orders-sets], [`OrderSet._resolve_order_expressions`][orders-sets], [`OrderSet._apply_orderings`][orders-sets], [`OrderSet.apply_sync`][orders-sets], [`OrderSet.apply_async`][orders-sets].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `OrderSet` mirrors `FilterSet` in [`filters/sets.py`][filters-sets], but all shared metaclass collection ([`collect_related_declarations`][sets-mixins]), expansion caching ([`expanded_once`][sets-mixins], [`should_cache_expansion`][sets-mixins]), permission facade ([`ActiveInputPermissionMixin`][sets-mixins]), and meta promotion/reading ([`promote_set_meta_fields`][utils-inputs], [`read_set_meta_fields`][utils-inputs]) are single-sited in `django_strawberry_framework/sets_mixins.py` and `django_strawberry_framework/utils/inputs.py`. `OrderSet` customizes its own descriptors ([`SetLifecycleAttrs`][sets-mixins], [`ActiveInputPermissionAttrs`][sets-mixins]) and implements order-specific semantics ([`OrderSet._resolve_order_expressions`][orders-sets] with `Min`/`Max` aggregate annotations for to-many paths).

2. **Sync and async twins:**
   [`OrderSet.apply_sync`][orders-sets] and [`OrderSet.apply_async`][orders-sets] share the identical [`OrderSet._apply_orderings`][orders-sets] backend. The only difference is the execution boundary for permission checking: `apply_sync` calls `_run_permission_checks` synchronously, while `apply_async` executes it inside [`run_in_one_sync_boundary`][utils-querysets] to protect the event loop. Zero duplication in queryset ordering or SQL construction.

3. **Derived rather than repeated knowledge:**
   Field expansion derives column names dynamically from [`_get_concrete_field_names_for_order`][orders-inputs]. To-many relation detection derives dynamically from [`path_traverses_to_many`][utils-relations]. Direction resolution derives directly from `direction.resolve` and `direction.is_ascending`.

4. **Inverse and round-trip pairs:**
   [`OrderSet.get_fields`][orders-sets] and [`OrderSet._expand_meta_fields`][orders-sets] form the declaration-to-runtime mapping; [`OrderSet.get_flat_orders`][orders-sets] and [`OrderSet._resolve_order_expressions`][orders-sets] translate parsed inputs back to ORM `OrderBy` expressions.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/orders/sets.py`][orders-sets], [`django_strawberry_framework/sets_mixins.py`][sets-mixins], [`django_strawberry_framework/orders/inputs.py`][orders-inputs], [`django_strawberry_framework/orders/base.py`][orders-base];
   - Specifications: [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028], [`docs/SPECS/spec-030-connection_field-0_0_9.md`][spec-030];
   - Test suites: [`tests/orders/test_sets.py`][test-orders-sets], [`tests/orders/test_composition.py`][test-orders-composition];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Modifying the metaclass declaration inheritance and collection logic):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/sets_mixins.py`][sets-mixins] ([`collect_related_declarations`][sets-mixins]).
  - *Propagation count:* 0 in `orders/sets.py`.
- **Posited change 2 (Altering the expansion cache check and reentry guard):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/sets_mixins.py`][sets-mixins] ([`expanded_once`][sets-mixins] / [`should_cache_expansion`][sets-mixins]).
  - *Propagation count:* 0 in `orders/sets.py`.
- **Posited change 3 (Changing the to-many aggregate alias mangling template):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/orders/sets.py`][orders-sets] ([`OrderSet._resolve_order_expressions`][orders-sets]).
  - *Propagation count:* 0 in production code.

### Rejected candidates

1. **Re-implementing declaration collection and MRO merge in `OrderSetMetaclass`:**
   - Disproved per [spec-028][spec-028]. Extracting `collect_related_declarations` into `sets_mixins.py` guarantees consistent declaration collection and inheritance across FilterSet and OrderSet.
2. **Duplicating the sync and async queryset ordering logic:**
   - Disproved per [spec-028][spec-028]. Extracting `_apply_orderings` ensures that both sync and async resolvers execute the identical normalization, annotation, and order_by pipeline.

## Opportunities

None — `django_strawberry_framework/orders/sets.py` is fully consolidated at root owners, delegating shared metaclass and lifecycle mechanics to `django_strawberry_framework/sets_mixins.py` and `django_strawberry_framework/utils/`.

## Judgment

Verified. `orders/sets.py` exhibits zero duplicate code and complete policy consolidation through `sets_mixins.py` and `utils/`. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/orders/sets.py --review docs/dry/dry-file-orders__sets.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/orders/sets.py`][orders-sets] and Worker 1's DRY review.

1. **Metaclass & Subsystem Descriptors:**
   - Confirmed `OrderSetMetaclass.__new__` delegates to `promote_set_meta_fields` and `collect_related_declarations`.
   - Confirmed `OrderSet` uses `SetLifecycleAttrs` and `ActiveInputPermissionAttrs`.
   - Confirmed `get_fields` uses `expanded_once` and `should_cache_expansion`.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/orders/sets.py --review docs/dry/dry-file-orders__sets.md --include-constants`. 100% coverage across all definitions.

Confirmed: `django_strawberry_framework/orders/sets.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-030]: ../SPECS/spec-030-connection_field-0_0_9.md

<!-- package source -->
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[orders-base]: ../../django_strawberry_framework/orders/base.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests -->
[test-orders-composition]: ../../tests/orders/test_composition.py
[test-orders-sets]: ../../tests/orders/test_sets.py
