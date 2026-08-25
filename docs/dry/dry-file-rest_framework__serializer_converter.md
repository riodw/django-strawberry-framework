# DRY review: `django_strawberry_framework/rest_framework/serializer_converter.py`

Status: verified

## System trace

`django_strawberry_framework/rest_framework/serializer_converter.py` provides conversion from Django REST Framework `serializers.Field` instances into Strawberry GraphQL input annotations and reverse-map specs ([spec-039][spec-039]).

It owns the following architectural responsibilities:

1. **Kind Identifiers & Value Conversion Structure:**
   - Kind constants: [`FILE`][rf-converter], [`RELATION_MULTI`][rf-converter], [`RELATION_SINGLE`][rf-converter], and [`SCALAR`][rf-converter] (re-exported from [`utils/inputs.py`][utils-inputs]), alongside serializer-specific [`NESTED_SINGLE`][rf-converter] and [`NESTED_MULTI`][rf-converter].
   - [`SerializerFieldConversion`][rf-converter] (`django_strawberry_framework/rest_framework/serializer_converter.py::SerializerFieldConversion`): Subclasses [`FieldConversionBase`][utils-inputs] to package annotation, kind, and requiredness.
   - [`SerializerFieldConverter`][rf-converter] (`django_strawberry_framework/rest_framework/serializer_converter.py::SerializerFieldConverter`): Callable conversion protocol type.
   - Factories: [`_scalar_converter`][rf-converter] (wrapping [`make_scalar_converter`][utils-converters]) and [`_model_field_converter`][rf-converter].

2. **Registry Infrastructure & Extension Point:**
   - Built-ins and live map: [`_BUILTIN_SCALAR_CONVERTERS`][rf-converter] and [`_SERIALIZER_FIELD_CONVERTERS`][rf-converter].
   - Kind converters: [`_CONVERT_RELATION_MULTI`][rf-converter], [`_CONVERT_RELATION_SINGLE`][rf-converter], [`_CONVERT_FILE`][rf-converter], and [`_CONVERT_MULTIPLE_CHOICE`][rf-converter] via [`make_kind_converter`][utils-converters].
   - [`register_serializer_field_converter`][rf-converter] (`django_strawberry_framework/rest_framework/serializer_converter.py::register_serializer_field_converter`): Public API for registering custom DRF field converters.
   - Serializer choice cache: [`_SERIALIZER_CHOICE_ENUMS`][rf-converter] and [`clear_serializer_choice_enums`][rf-converter] wired to [`register_subsystem_clear`][registry].

3. **Field Dispatch, Validation & Error Handling:**
   - Nested detection: [`is_nested_serializer_field`][rf-converter], [`nested_serializer_child`][rf-converter], and [`_reject_nested_serializer`][rf-converter].
   - Restriction guards: [`_reject_unsupported_relation_field`][rf-converter] and [`_reject_relation_cardinality_mismatch`][rf-converter] (using [`_relation_cardinality`][rf-converter] and [`_model_relation_cardinality`][rf-converter]).
   - List and post-processing: [`_list_child_conversion`][rf-converter] and [`_finish_serializer_conversion`][rf-converter] (wrapping [`finish_field_conversion`][utils-converters]).
   - Core dispatch: [`convert_serializer_field`][rf-converter] executing via [`convert_with_mro`][utils-converters] and falling through to [`_unsupported_serializer_field`][rf-converter].

4. **Field Introspection, Source Rules & Metadata:**
   - Naming and docs: [`serializer_field_graphql_name`][rf-converter] and [`serializer_field_description`][rf-converter].
   - Source mapping: [`require_one_segment_source`][rf-converter] and [`backing_model_field`][rf-converter].
   - Relation typing: [`_require_relation_primary`][rf-converter] and [`serializer_only_relation_annotation`][rf-converter] (using [`annotate_queryset_relation`][mutations-inputs]).

5. **Model-Backed and Choice Enum Resolution:**
   - Classification & diagnostics: [`_is_consumer_declared`][rf-converter] and [`_scalar_name`][rf-converter].
   - Conflict resolution: [`_model_backed_scalar_annotation`][rf-converter].
   - Choice enum synthesis: [`_is_enumerable_serializer_choice`][rf-converter], [`_enum_member_map`][rf-converter], [`_serializer_choice_enum`][rf-converter], [`_serializer_choice_annotation`][rf-converter], and [`_serializer_only_scalar_annotation`][rf-converter].
   - Top-level resolver: [`resolve_serializer_field`][rf-converter] (`django_strawberry_framework/rest_framework/serializer_converter.py::resolve_serializer_field`).

Connected behavior examined:
- [`django_strawberry_framework/rest_framework/inputs.py`][rf-inputs]: Consumes `resolve_serializer_field`, `serializer_field_description`, and `require_one_segment_source`.
- [`django_strawberry_framework/rest_framework/resolvers.py`][rf-resolvers]: Consumes kind constants and `nested_serializer_child`.
- [`django_strawberry_framework/types/converters.py`][types-converters]: Read-side scalar and choice-enum conversion engine (`build_enum_from_choices`, `convert_scalar`, `scalar_for_field`).
- [`django_strawberry_framework/utils/converters.py`][utils-converters]: Shared `convert_with_mro` skeleton and converter builder helpers.
- [`tests/rest_framework/test_serializer_converter.py`][tests-rf-converter]: Comprehensive tests for DRF field mappings, choice enums, source semantics, and validation.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/rest_framework/serializer_converter.py --include-constants`):
- Parsed 1 target file, 1,052 lines.
- Complete inventory across all 37 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `rest_framework/serializer_converter.py` shares its MRO conversion skeleton and builder helpers directly with [`django_strawberry_framework/utils/converters.py`][utils-converters]. Read-side enum and scalar conversion primitives are reused from [`types/converters.py`][types-converters] (`build_enum_from_choices`, `convert_scalar`, `scalar_for_field`). Conversion rules unique to DRF serializers (such as `_model_backed_scalar_annotation`, `is_nested_serializer_field`, `_reject_relation_cardinality_mismatch`, and `serializer_field_description`) are single-sited in this file.

2. **Sync and async twins:**
   Zero duplication. Field conversion runs synchronously at schema compilation time.

3. **Derived rather than repeated knowledge:**
   Model-backed field conversions inspect Django `models.Field` attributes to ensure type alignment, and serializer-only choice enums derive their structures directly from `field.choices.items()`.

4. **Inverse and round-trip pairs:**
   `_SERIALIZER_CHOICE_ENUMS` is cleared via `clear_serializer_choice_enums` registered in the central subsystem clear lifecycle.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/rest_framework/serializer_converter.py`][rf-converter], [`django_strawberry_framework/rest_framework/inputs.py`][rf-inputs], [`django_strawberry_framework/forms/converter.py`][forms-converter], [`django_strawberry_framework/utils/converters.py`][utils-converters];
   - Specifications: [`docs/SPECS/spec-039-serializer_mutation-0_0_11.md`][spec-039];
   - Test suites: [`tests/rest_framework/test_serializer_converter.py`][tests-rf-converter];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new built-in DRF serializer field conversion):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/rest_framework/serializer_converter.py`][rf-converter] ([`_BUILTIN_SCALAR_CONVERTERS`][rf-converter]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Adjusting the shared converter MRO resolution algorithm):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/converters.py`][utils-converters] ([`convert_with_mro`][utils-converters]).
  - *Propagation count:* 0 in `rest_framework/serializer_converter.py`.
- **Posited change 3 (Modifying DRF field description rendering format):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/rest_framework/serializer_converter.py`][rf-converter] ([`serializer_field_description`][rf-converter]).
  - *Propagation count:* 0 in other files.

### Rejected candidates

1. **Re-implementing the MRO search algorithm independently:**
   - Disproved per [spec-039][spec-039]. Using `convert_with_mro` guarantees consistent fallback and inheritance handling across forms and serializers.
2. **Re-implementing choice enum generation independently:**
   - Disproved per [spec-039][spec-039]. Using `build_enum_from_choices` guarantees identical sanitization and casing rules across model and serializer choice enums.

## Opportunities

None — `django_strawberry_framework/rest_framework/serializer_converter.py` is fully consolidated with shared infrastructure in `django_strawberry_framework/utils/converters.py` and `django_strawberry_framework/types/converters.py`.

## Judgment

Verified. `rest_framework/serializer_converter.py` exhibits zero duplicate code and complete policy consolidation through shared converter and typing infrastructure. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/rest_framework/serializer_converter.py --review docs/dry/dry-file-rest_framework__serializer_converter.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/rest_framework/serializer_converter.py`][rf-converter] and Worker 1's DRY review.

1. **DRF Field Conversion & Enum Infrastructure:**
   - Confirmed `convert_serializer_field` utilizes `convert_with_mro` and shares conversion conventions with `forms/converter.py`.
   - Confirmed choice-enum generation reuses `build_enum_from_choices` from `types/converters.py` while maintaining a distinct name-keyed cache.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/rest_framework/serializer_converter.py --review docs/dry/dry-file-rest_framework__serializer_converter.md --include-constants`. 100% coverage across all 37 definitions.

Confirmed: `django_strawberry_framework/rest_framework/serializer_converter.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-039]: ../SPECS/spec-039-serializer_mutation-0_0_11.md

<!-- package source -->
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[registry]: ../../django_strawberry_framework/registry.py
[rf-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rf-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[utils-converters]: ../../django_strawberry_framework/utils/converters.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests -->
[tests-rf-converter]: ../../tests/rest_framework/test_serializer_converter.py
