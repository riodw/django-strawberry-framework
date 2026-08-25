# DRY folder integration: `django_strawberry_framework/orders/`

Status: verified

## System trace

The `django_strawberry_framework/orders/` subsystem provides declarative ordering over root models and nested relational paths ([spec-028][spec-028], [spec-030][spec-030]).

It consists of 5 modular components:

1. **Public Package Surface & Helper Reference Ledger ([`django_strawberry_framework/orders/__init__.py`][orders-init]):**
   - Public re-exports: [`OrderSet`][orders-init], [`RelatedOrder`][orders-init], [`Ordering`][orders-init], [`OrderArgumentsFactory`][orders-init], [`get_orderset_class`][orders-init], [`materialize_input_class`][orders-init], [`clear_order_input_namespace`][orders-init], [`LazyRelatedClassMixin`][orders-init].
   - Standalone helper decorator: [`order_input_type`][orders-init] (`django_strawberry_framework/orders/__init__.py::order_input_type`) attaching standalone input types to classes and registering into [`_helper_referenced_ordersets`][orders-init] (`django_strawberry_framework/orders/__init__.py::_helper_referenced_ordersets`).
   - Orphan validation & Subsystem clear: [`_clear_helper_referenced_ordersets`][orders-init] registered into `registry.clear()` via [`register_subsystem_clear`][registry].

2. **Relational Ordering Primitive ([`django_strawberry_framework/orders/base.py`][orders-base]):**
   - [`RelatedOrder`][orders-base] (`django_strawberry_framework/orders/base.py::RelatedOrder`): Targets related `OrderSet` classes with slot parameterization ([`_target_attr`][orders-base], [`_owner_attr`][orders-base]), initialization ([`RelatedOrder.__init__`][orders-base]), idempotent binding ([`RelatedOrder.bind_orderset`][orders-base]), and lazy resolution ([`RelatedOrder.orderset`][orders-base] property getter and setter: `django_strawberry_framework/orders/base.py::RelatedOrder.orderset`) delegating to [`RelatedSetTargetMixin`][sets-mixins].

3. **Input Generation & Dynamic Synthesis ([`django_strawberry_framework/orders/factories.py`][orders-factories]):**
   - [`OrderArgumentsFactory`][orders-factories] (`django_strawberry_framework/orders/factories.py::OrderArgumentsFactory`): Breadth-first input AST builder subclassing [`GeneratedInputArgumentsFactory`][utils-inputs], maintaining [`input_object_types`][orders-factories] and collision check [`_type_orderset_registry`][orders-factories], configuring [`_collision_registry_attr`][orders-factories], [`_factory_label`][orders-factories], [`_family_label`][orders-factories], [`_rename_noun`][orders-factories], [`_related_attr`][orders-factories], [`_related_target_attr`][orders-factories], and implementing [`OrderArgumentsFactory._build_input_triples`][orders-factories].
   - Dynamic class cache & builder: [`_dynamic_orderset_cache`][orders-factories], [`_RESERVED_FACTORY_KEYS`][orders-factories], [`_get_orderset_class`][orders-factories], [`get_orderset_class`][orders-factories] utilizing [`make_dynamic_set_getter`][utils-inputs].

4. **Input Namespace, Direction Enum & Normalization ([`django_strawberry_framework/orders/inputs.py`][orders-inputs]):**
   - Module path & Aliases: [`INPUTS_MODULE_PATH`][orders-inputs], [`FieldSpec`][orders-inputs], [`build_input_class`][orders-inputs], [`_camel_case`][orders-inputs], [`_iter_orderset_subclasses`][orders-inputs], [`_input_type_name_for`][orders-inputs].
   - Direction Enum: [`Ordering`][orders-inputs] (`django_strawberry_framework/orders/inputs.py::Ordering`) with members [`Ordering.ASC`][orders-inputs], [`Ordering.DESC`][orders-inputs], [`Ordering.ASC_NULLS_FIRST`][orders-inputs], [`Ordering.ASC_NULLS_LAST`][orders-inputs], [`Ordering.DESC_NULLS_FIRST`][orders-inputs], [`Ordering.DESC_NULLS_LAST`][orders-inputs], prefix-based classifier [`Ordering.is_ascending`][orders-inputs], and Django `OrderBy` translator [`Ordering.resolve`][orders-inputs].
   - Namespace lifecycle: [`_materialized_names`][orders-inputs], [`_field_specs`][orders-inputs], [`materialize_input_class`][orders-inputs], and [`clear_order_input_namespace`][orders-inputs] via [`make_set_input_namespace`][utils-inputs].
   - Field converters & normalization: [`_get_concrete_field_names_for_order`][orders-inputs], [`convert_order_field_to_input_annotation`][orders-inputs], [`_build_input_fields`][orders-inputs], [`_ensure_field_specs`][orders-inputs], and [`normalize_input_value`][orders-inputs] leveraging [`iter_active_fields`][utils-input-values] and [`SetInputTraversal`][utils-input-values].

5. **OrderSet Declaration, Metaclass & Execution Pipeline ([`django_strawberry_framework/orders/sets.py`][orders-sets]):**
   - Metaclass: [`OrderSetMetaclass`][orders-sets] (`django_strawberry_framework/orders/sets.py::OrderSetMetaclass`) running [`promote_set_meta_fields`][utils-inputs] and [`collect_related_declarations`][sets-mixins] in [`OrderSetMetaclass.__new__`][orders-sets].
   - Foundation class: [`OrderSet`][orders-sets] (`django_strawberry_framework/orders/sets.py::OrderSet`) inheriting from [`ClassBasedTypeNameMixin`][sets-mixins] and [`ActiveInputPermissionMixin`][sets-mixins], housing slots [`_owner_definition`][orders-sets], [`_expanded_fields`][orders-sets], [`_is_expanding_fields`][orders-sets], descriptors [`_lifecycle`][orders-sets] and [`_permission`][orders-sets].
   - Expansion & Normalization: [`OrderSet.get_fields`][orders-sets] (via [`expanded_once`][sets-mixins] and [`should_cache_expansion`][sets-mixins]), [`OrderSet._expand_meta_fields`][orders-sets] (via [`read_set_meta_fields`][utils-inputs] and [`classify_path`][utils-relations]), [`OrderSet._normalize_input`][orders-sets], [`OrderSet._prepare_permission_input`][orders-sets], [`OrderSet.get_flat_orders`][orders-sets].
   - Queryset Ordering & Resolution: [`OrderSet._resolve_order_expressions`][orders-sets] handling row-preserving `Min`/`Max` aggregate annotations for to-many paths via [`path_traverses_to_many`][utils-relations], un-colored core pipeline [`OrderSet._apply_orderings`][orders-sets], sync entrypoint [`OrderSet.apply_sync`][orders-sets], and async entrypoint [`OrderSet.apply_async`][orders-sets] wrapped in [`run_in_one_sync_boundary`][utils-querysets].

Connected behavior examined:
- [`django_strawberry_framework/sets_mixins.py`][sets-mixins]: Neutral mixins and declaration lifecycle machinery shared across `filters` and `orders`.
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Neutral input namespace generation, BFS factory, and meta fields handling.
- [`django_strawberry_framework/utils/input_values.py`][utils-input-values]: Active input traversal and value normalization.
- [`django_strawberry_framework/utils/relations.py`][utils-relations]: Path classification and to-many relation detection.
- [`django_strawberry_framework/utils/querysets.py`][utils-querysets]: Sync boundary management for async resolver permission execution.
- [`django_strawberry_framework/registry.py`][registry]: Subsystem clear registration hooks.
- [`tests/orders/`][tests-orders]: Comprehensive unit and integration test suite covering the full order subsystem.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/orders/ --include-constants`):
- Parsed 5 target files across `django_strawberry_framework/orders/`.
- Total symbols covered across all 5 files.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   The `orders/` subsystem mirrors the structure of `filters/`, but all shared declaration collection, lifecycle resetting, BFS AST traversal, active input walking, and meta fields normalization are single-sited in neutral substrates (`django_strawberry_framework/sets_mixins.py`, `django_strawberry_framework/utils/inputs.py`, `django_strawberry_framework/utils/input_values.py`). `orders/` retains only its order-specific domain rules (`Ordering` enum, `OrderBy` resolution, and `Min`/`Max` aggregation for to-many paths).

2. **Sync and async twins:**
   [`OrderSet.apply_sync`][orders-sets] and [`OrderSet.apply_async`][orders-sets] share the uncolored [`OrderSet._apply_orderings`][orders-sets] pipeline. The sync/async distinction is isolated solely to the permission-evaluation boundary ([`run_in_one_sync_boundary`][utils-querysets]). Zero duplication in query building or expression resolution.

3. **Derived rather than repeated knowledge:**
   `Meta.fields = "__all__"` derives columns dynamically via [`_get_concrete_field_names_for_order`][orders-inputs]. To-many relation paths derive dynamically via [`path_traverses_to_many`][utils-relations]. Direction classification derives from `self.name.startswith("ASC")`.

4. **Inverse and round-trip pairs:**
   `materialize_input_class` and `clear_order_input_namespace` form a clean write/clear pair. `_build_input_fields` and `normalize_input_value` form an encode/decode pair over `_field_specs`.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: `django_strawberry_framework/orders/`, `django_strawberry_framework/sets_mixins.py`, `django_strawberry_framework/utils/`;
   - Specs: [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028], [`docs/SPECS/spec-030-connection_field-0_0_9.md`][spec-030];
   - Tests: [`tests/orders/`][tests-orders];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Modifying the shared set-family declaration collector or MRO inheritance):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/sets_mixins.py`][sets-mixins] ([`collect_related_declarations`][sets-mixins]).
  - *Propagation count:* 0 in `orders/`.
- **Posited change 2 (Adjusting the generated input BFS queue traversal or class-name collision rule):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/inputs.py`][utils-inputs] ([`GeneratedInputArgumentsFactory`][utils-inputs]).
  - *Propagation count:* 0 in `orders/`.
- **Posited change 3 (Modifying the to-many relation aggregate ordering logic or alias structure):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/orders/sets.py`][orders-sets] ([`OrderSet._resolve_order_expressions`][orders-sets]).
  - *Propagation count:* 0 in other modules.

### Rejected candidates

1. **Re-implementing filter-family infrastructure locally in `orders/`:**
   - Disproved per [spec-028][spec-028]. Extracting neutral machinery into `sets_mixins.py` and `utils/` eliminates duplicated lifecycle and AST logic between `filters` and `orders`.
2. **Merging filter and order registries into a single shared mutable dict:**
   - Disproved per [spec-028][spec-028]. Isolating family registries prevents cross-subsystem leakage and ensures clean subsystem-level lifecycle boundaries.

## Opportunities

None — the `django_strawberry_framework/orders/` subsystem is completely integrated and consolidated at root owners.

## Judgment

Verified. `orders/` exhibits zero duplicate code and complete policy consolidation through `sets_mixins.py` and `utils/`. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/orders/ --review docs/dry/dry-folder-orders.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of the `django_strawberry_framework/orders/` subsystem and Worker 1's DRY review.

1. **Subsystem Architecture & Neutral Substrate Integration:**
   - Verified that all 5 files in `django_strawberry_framework/orders/` cleanly separate domain semantics from shared set machinery.
   - Verified that `sets_mixins.py`, `utils/inputs.py`, `utils/input_values.py`, and `utils/relations.py` own all shared lifecycle, BFS, traversal, and relation logic.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes across the subsystem and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/orders/ --review docs/dry/dry-folder-orders.md --include-constants`. 100% coverage across all target definitions in the folder.

Confirmed: `django_strawberry_framework/orders/` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-030]: ../SPECS/spec-030-connection_field-0_0_9.md

<!-- package source -->
[orders-base]: ../../django_strawberry_framework/orders/base.py
[orders-factories]: ../../django_strawberry_framework/orders/factories.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[utils-input-values]: ../../django_strawberry_framework/utils/input_values.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests -->
[tests-orders]: ../../tests/orders/
