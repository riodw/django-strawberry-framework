# DRY review: `django_strawberry_framework/utils/inputs.py`

Status: verified

## System trace

`django_strawberry_framework/utils/inputs.py` implements the centralized generated-input construction, caching, naming, collision auditing, and lifecycle clearing substrate shared across FilterSets, OrderSets, Model Mutations, Form Mutations, and Serializer Mutations ([spec-027][spec-027], [spec-028][spec-028], [spec-036][spec-036], [spec-038][spec-038], [spec-039][spec-039], [spec-051][spec-051]).

It owns the following architectural responsibilities:

1. **Input Specs & Decode Kinds:**
   - Set-input field spec: [`GeneratedInputFieldSpec`][utils-inputs] (`django_strawberry_framework/utils/inputs.py::GeneratedInputFieldSpec` with attributes `python_attr`, `graphql_name`, `django_source_path`).
   - Canonical input type naming: [`set_input_type_name`][utils-inputs] (`django_strawberry_framework/utils/inputs.py::set_input_type_name`).
   - Field kwargs & widening helpers: [`optional_field_kwargs`][utils-inputs], [`optional_input_field`][utils-inputs], and [`emit_set_input_field_triples`][utils-inputs].
   - Shared decode kinds: [`SCALAR`][utils-inputs], [`RELATION_SINGLE`][utils-inputs], [`RELATION_MULTI`][utils-inputs], and [`FILE`][utils-inputs].
   - Shared conversion value object: [`FieldConversionBase`][utils-inputs] (`django_strawberry_framework/utils/inputs.py::FieldConversionBase` with `django_strawberry_framework/utils/inputs.py::FieldConversionBase.__init__`, `annotation`, `kind`, `required`).
   - Unified reverse-map spec: [`InputFieldSpec`][utils-inputs] (`django_strawberry_framework/utils/inputs.py::InputFieldSpec` with attributes `input_attr`, `graphql_name`, `target_name`, `kind`, `source`, `related_model`, `nested_specs`, `annotation_repr`, `required`).

2. **Namespace Management & Meta Cache Hashing:**
   - Namespace generators: [`make_input_namespace`][utils-inputs] and [`make_set_input_namespace`][utils-inputs].
   - Hashable metadata conversion: [`_opaque_meta_value`][utils-inputs], [`_meta_sort_key`][utils-inputs], [`_base_meta_values`][utils-inputs], [`_sorted_meta_values`][utils-inputs], [`_MAX_META_VALUE_DEPTH`][utils-inputs], [`_hashable_meta_value`][utils-inputs], and [`make_hashable_meta_value`][utils-inputs].
   - Set Meta resolution & promotion: [`FILTERSET_FIELDS_ALIAS`][utils-inputs], [`_set_meta_has`][utils-inputs], [`_set_meta_get`][utils-inputs], [`resolve_set_meta_fields`][utils-inputs], [`canonicalize_set_meta_fields`][utils-inputs], [`promote_set_meta_fields`][utils-inputs], and [`read_set_meta_fields`][utils-inputs].
   - Set cache keys & factory normalization: [`make_set_meta_cache_key`][utils-inputs], [`normalize_set_meta_for_factory`][utils-inputs], [`create_dynamic_set_class`][utils-inputs], and [`make_dynamic_set_getter`][utils-inputs].
   - Build cache helpers: [`make_shape_build_cache`][utils-inputs] and [`get_or_store_shape_build`][utils-inputs].

3. **Injective Naming, Field Narrowing & Collision Auditing:**
   - Injective token encoder: [`pascalize_token`][utils-inputs] (`django_strawberry_framework/utils/inputs.py::pascalize_token`).
   - Type name formatters: [`generated_input_type_name`][utils-inputs] and [`name_set_input_type_name`][utils-inputs].
   - Field sequence & narrowing validators: [`normalize_field_name_sequence`][utils-inputs], [`resolve_effective_fields`][utils-inputs], and [`guard_dropped_required`][utils-inputs].
   - Provided field iterator: [`iter_provided_input_fields`][utils-inputs] (`django_strawberry_framework/utils/inputs.py::iter_provided_input_fields`).
   - Strawberry class builder: [`build_strawberry_input_class`][utils-inputs] (`django_strawberry_framework/utils/inputs.py::build_strawberry_input_class`).
   - Class materializer & collision messages: [`materialize_generated_input_class`][utils-inputs], [`duplicate_name_message`][utils-inputs], and [`iter_input_field_collisions`][utils-inputs].

4. **Lifecycle Clearing & Arguments Factory:**
   - Lazy forward-ref builder: [`build_lazy_input_annotation`][utils-inputs].
   - Subclass iterator & safe import: [`iter_set_subclasses`][utils-inputs] and [`_safe_import`][utils-inputs].
   - Namespace resetter: [`clear_generated_input_namespace`][utils-inputs].
   - BFS Arguments Factory: [`GeneratedInputArgumentsFactory`][utils-inputs] (`django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory` with `django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory.__init_subclass__`, `django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory.__init__`, `django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory._collision_registry`, `django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory.arguments`, `django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built`, `django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory._build_class_type`, `django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory._build_input_triples`, plus class attributes `input_object_types`, `_collision_registry_attr`, `_factory_label`, `_family_label`, `_rename_noun`, `_related_attr`, `_related_target_attr`).

Connected behavior examined:
- [`django_strawberry_framework/filters/`][filters-inputs]: Uses `GeneratedInputFieldSpec`, `GeneratedInputArgumentsFactory`, `make_set_input_namespace`.
- [`django_strawberry_framework/orders/`][orders-inputs]: Uses `GeneratedInputFieldSpec`, `GeneratedInputArgumentsFactory`, `make_set_input_namespace`.
- [`django_strawberry_framework/mutations/`][mutations-inputs]: Uses `InputFieldSpec`, `build_strawberry_input_class`, `make_input_namespace`.
- [`django_strawberry_framework/forms/`][forms-inputs]: Uses `InputFieldSpec`, `FieldConversionBase`, `build_strawberry_input_class`, `make_input_namespace`.
- [`django_strawberry_framework/rest_framework/`][serializer-inputs]: Uses `InputFieldSpec`, `FieldConversionBase`, `build_strawberry_input_class`, `make_input_namespace`.
- [`tests/utils/`][tests-utils]: Test coverage for input generation, caching, and lifecycle clearing.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/inputs.py --include-constants`):
- Parsed 1 target file, 1744 lines.
- Complete inventory across all 59 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/inputs.py` acts as the root owner for input dataclass compilation across all five framework subsystems:
   - Wire name pinning in `build_strawberry_input_class` prevents divergence across casing rules.
   - `GeneratedInputArgumentsFactory` enforces identical BFS graph resolution, cycle handling, and collision detection across FilterSets and OrderSets.
   - `resolve_effective_fields` and `normalize_field_name_sequence` unify field sequence normalization across Form, Model, and Serializer mutations.
   - `clear_generated_input_namespace` guarantees uniform clearing behavior across test isolation fixtures.

2. **Sync and async twins:**
   Input generation, validation, and metadata hashing are synchronous CPU operations executed identically across sync and async contexts.

3. **Derived rather than repeated knowledge:**
   Injective naming (`pascalize_token`, `generated_input_type_name`) and cache key generation (`make_set_meta_cache_key`, `make_hashable_meta_value`) are derived from source field collections rather than hand-mirrored.

4. **Inverse and round-trip pairs:**
   `build_strawberry_input_class` compiles GraphQL input classes; `iter_provided_input_fields` deconstructs incoming input dataclasses at runtime.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/inputs.py`][utils-inputs], [`django_strawberry_framework/filters/inputs.py`][filters-inputs], [`django_strawberry_framework/orders/inputs.py`][orders-inputs], [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs], [`django_strawberry_framework/forms/inputs.py`][forms-inputs], [`django_strawberry_framework/rest_framework/inputs.py`][serializer-inputs];
   - Specifications: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027], [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028], [`docs/SPECS/spec-036-model_mutations-0_0_11.md`][spec-036], [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038], [`docs/SPECS/spec-039-rest_framework_mutations-0_0_12.md`][spec-039], [`docs/SPECS/spec-051-finalizer_sidecar_dry-0_0_14.md`][spec-051];
   - Test suites: [`tests/utils/`][tests-utils], [`tests/filters/`][tests-filters], [`tests/orders/`][tests-orders], [`tests/mutations/`][tests-mutations], [`tests/forms/`][tests-forms], [`tests/rest_framework/`][tests-rest_framework];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Altering Strawberry input class required-vs-optional detection or wire name pinning):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/inputs.py`][utils-inputs] ([`build_strawberry_input_class`][utils-inputs]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Changing the injective token escaping rules for generated input class names):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/inputs.py`][utils-inputs] ([`pascalize_token`][utils-inputs]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Modifying the BFS related-set enqueue or cycle prevention logic):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/inputs.py`][utils-inputs] ([`GeneratedInputArgumentsFactory._ensure_built`][utils-inputs]).
  - *Propagation count:* 0 in other source files.
- **Posited change 4 (Updating the field sequence normalization or duplicate rejection):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/inputs.py`][utils-inputs] ([`normalize_field_name_sequence`][utils-inputs]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Allowing individual subsystems to hand-roll Strawberry input dataclasses:**
   - Disproved per [spec-027][spec-027] and [spec-051][spec-051]. Centralizing construction in `build_strawberry_input_class` prevents casing discrepancies, missing field defaults, and silent schema clobbering.

## Opportunities

None — `django_strawberry_framework/utils/inputs.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/inputs.py` exhibits zero duplicate code and complete policy consolidation across generated input construction, hashing, validation, and lifecycle management. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/inputs.py --review docs/dry/dry-file-utils__inputs.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/inputs.py`][utils-inputs] and Worker 1's DRY review.

1. **Input Generation & Collision Infrastructure:**
   - Confirmed `build_strawberry_input_class` correctly binds names and defaults while preventing accidental field overwrite.
   - Confirmed `GeneratedInputArgumentsFactory` executes robust BFS graph traversals and detects name collisions across set hierarchies.
   - Confirmed metadata caching and hashable conversion securely handle nested and unhashable structures up to `_MAX_META_VALUE_DEPTH`.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/inputs.py --review docs/dry/dry-file-utils__inputs.md --include-constants`. 100% coverage across all 59 definitions / constants.

Confirmed: `django_strawberry_framework/utils/inputs.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-027]: ../SPECS/spec-027-filters-0_0_8.md
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-036]: ../SPECS/spec-036-model_mutations-0_0_11.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-rest_framework_mutations-0_0_12.md
[spec-051]: ../SPECS/spec-051-finalizer_sidecar_dry-0_0_14.md

<!-- package source -->
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[serializer-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests -->
[tests-filters]: ../../tests/filters/
[tests-forms]: ../../tests/forms/
[tests-mutations]: ../../tests/mutations/
[tests-orders]: ../../tests/orders/
[tests-rest_framework]: ../../tests/rest_framework/
[tests-utils]: ../../tests/utils/
