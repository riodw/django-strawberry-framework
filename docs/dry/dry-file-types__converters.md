# DRY review: `django_strawberry_framework/types/converters.py`

Status: verified

## System trace

`django_strawberry_framework/types/converters.py` implements Django model field to Strawberry GraphQL output type conversion ([spec-011][spec-011], [spec-037][spec-037], [spec-039][spec-039], [spec-048][spec-048]).

It owns the following architectural responsibilities:

1. **File and Image Output Types:**
   - [`_safe_file_attr`][types-converters] (`django_strawberry_framework/types/converters.py::_safe_file_attr`): Shared exception barrier for file/image storage attributes (`ValueError`, `OSError`, `NotImplementedError`).
   - [`DjangoFileType`][types-converters] (`django_strawberry_framework/types/converters.py::DjangoFileType`): Structured output object with subfields:
     - [`DjangoFileType.name`][types-converters]
     - [`DjangoFileType.size`][types-converters]
     - [`DjangoFileType.url`][types-converters]
   - [`DjangoImageType`][types-converters] (`django_strawberry_framework/types/converters.py::DjangoImageType`): Subclass adding:
     - [`DjangoImageType.width`][types-converters]
     - [`DjangoImageType.height`][types-converters]
   - [`_FileSystemPathFields`][types-converters] (`django_strawberry_framework/types/converters.py::_FileSystemPathFields`): Mixin defining:
     - [`_FileSystemPathFields.path`][types-converters]
   - [`DjangoFilePathType`][types-converters] (`django_strawberry_framework/types/converters.py::DjangoFilePathType`) and [`DjangoImagePathType`][types-converters] (`django_strawberry_framework/types/converters.py::DjangoImagePathType`): Opt-in path-bearing file/image types.
   - Output maps: [`FIELD_OUTPUT_TYPE_MAP`][types-converters] and [`FILESYSTEM_PATH_OUTPUT_TYPE_MAP`][types-converters].

2. **Scalar and Choice Mappings:**
   - [`SCALAR_MAP`][types-converters] (`django_strawberry_framework/types/converters.py::SCALAR_MAP`): Shared dictionary mapping Django field classes to Python/Strawberry types.
   - Enums and postgres field sentinels: [`_NON_IDENT`][types-converters], [`_GRAPHQL_RESERVED_ENUM_VALUES`][types-converters], [`_ARRAY_FIELD_CLS`][types-converters], and [`_HSTORE_FIELD_CLS`][types-converters].

3. **Field Diagnostics & Scalar Conversion:**
   - Diagnostic formatters: [`_safe_text`][types-converters], [`_field_label`][types-converters], and [`_field_has_choices`][types-converters].
   - [`scalar_for_field`][types-converters] (`django_strawberry_framework/types/converters.py::scalar_for_field`): Shared MRO scalar lookup for `DjangoType` and `FilterSet` input generation.
   - [`convert_scalar`][types-converters] (`django_strawberry_framework/types/converters.py::convert_scalar`): Scalar conversion with choices and nullability widening.
   - [`_field_output_type_for`][types-converters] (`django_strawberry_framework/types/converters.py::_field_output_type_for`): Shared MRO lookup for file/image output objects.
   - [`convert_field_output`][types-converters] (`django_strawberry_framework/types/converters.py::convert_field_output`): Entry point for field read-output synthesis.

4. **Enum Building & Member Sanitization:**
   - [`_is_enum_reserved_member`][types-converters] (`django_strawberry_framework/types/converters.py::_is_enum_reserved_member`): Python enum keyword and directive guard.
   - [`_sanitize_member_name`][types-converters] (`django_strawberry_framework/types/converters.py::_sanitize_member_name`): Identifier-safe enum member derivation.
   - [`build_enum_from_choices`][types-converters] (`django_strawberry_framework/types/converters.py::build_enum_from_choices`): Shared choices -> enum core used by model fields and DRF serializers.
   - [`convert_choices_to_enum`][types-converters] (`django_strawberry_framework/types/converters.py::convert_choices_to_enum`): Cached model-field enum generator.

5. **Relation Annotation Resolution:**
   - [`resolved_relation_annotation`][types-converters] (`django_strawberry_framework/types/converters.py::resolved_relation_annotation`): Generates concrete relation annotation from target type and `FieldMeta`.

Connected behavior examined:
- [`django_strawberry_framework/types/base.py`][types-base]: `_build_annotations` delegates to `convert_field_output`.
- [`django_strawberry_framework/types/resolvers.py`][types-resolvers]: File and relation resolver attachment.
- [`django_strawberry_framework/rest_framework/serializer_converter.py`][rf-serializer-converter]: Serializer choice field conversion via `build_enum_from_choices`.
- [`django_strawberry_framework/filters/inputs.py`][filters-inputs]: Shared `scalar_for_field` usage.
- [`tests/types/`][tests-types]: Test coverage for converters, choices enums, file fields, and scalars.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/types/converters.py --include-constants`):
- Parsed 1 target file, 817 lines.
- Complete inventory across all 26 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `types/converters.py` provides consolidated single sources of truth across multiple flavors:
   - `scalar_for_field` is shared between GraphQL type annotation synthesis and filter input construction.
   - `build_enum_from_choices` is shared between model-choice enums and serializer choice field enums.
   - `_safe_file_attr` is shared across all file and image subfield resolvers.
   - `_field_output_type_for` is shared between annotation conversion and resolver attachment.

2. **Sync and async twins:**
   Type conversions and resolver delegates are synchronous operations designed for Django model field introspection.

3. **Derived rather than repeated knowledge:**
   Scalar mappings and output objects are derived via field MRO walks. Choice enums derive member names from raw choice values with collision detection. Relation annotations derive from `FieldMeta`.

4. **Inverse and round-trip pairs:**
   `resolved_relation_annotation` converts `FieldMeta` cardinality and nullability to Python type annotations matching resolver unwrap/wrap conventions.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/types/converters.py`][types-converters], [`django_strawberry_framework/types/base.py`][types-base], [`django_strawberry_framework/types/resolvers.py`][types-resolvers], [`django_strawberry_framework/rest_framework/serializer_converter.py`][rf-serializer-converter], [`django_strawberry_framework/filters/inputs.py`][filters-inputs];
   - Specifications: [`docs/SPECS/spec-011-interfaces-0_0_4.md`][spec-011], [`docs/SPECS/spec-037-file_and_image_fields-0_0_11.md`][spec-037], [`docs/SPECS/spec-039-serializer_mutation_choices-0_0_11.md`][spec-039], [`docs/SPECS/spec-048-filesystem_path_fields-0_0_14.md`][spec-048];
   - Test suites: [`tests/types/`][tests-types];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new Django model field to Python scalar mapping):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/converters.py`][types-converters] ([`SCALAR_MAP`][types-converters]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Updating enum member name sanitization logic or reserved keywords):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/converters.py`][types-converters] ([`_sanitize_member_name`][types-converters]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Modifying the safe file attribute exception catch list):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/converters.py`][types-converters] ([`_safe_file_attr`][types-converters]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Merging `SCALAR_MAP` and `FIELD_OUTPUT_TYPE_MAP`:**
   - Disproved per [spec-037][spec-037] Decision 3. `SCALAR_MAP` is shared with filter inputs where file fields must remain `str` inputs; mixing output object types into `SCALAR_MAP` would contaminate filter input schemas.
2. **Duplicating choice-to-enum building in `rest_framework/serializer_converter.py`:**
   - Disproved per [spec-039][spec-039]. Factoring into `build_enum_from_choices` guarantees identical sanitization, grouped-form rejection, and collision handling.

## Opportunities

None — `django_strawberry_framework/types/converters.py` is fully consolidated at root owners.

## Judgment

Verified. `types/converters.py` exhibits zero duplicate code and complete policy consolidation across field conversion, scalar mapping, file types, and enum construction. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/types/converters.py --review docs/dry/dry-file-types__converters.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/types/converters.py`][types-converters] and Worker 1's DRY review.

1. **Shared MRO & Choice Enum Pipeline:**
   - Confirmed `scalar_for_field`, `_field_output_type_for`, and `build_enum_from_choices` serve as clean single sources of truth.
   - Confirmed file/image output objects and safe attribute extraction are strictly centralized.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/types/converters.py --review docs/dry/dry-file-types__converters.md --include-constants`. 100% coverage across all 26 definitions / constants.

Confirmed: `django_strawberry_framework/types/converters.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-011]: ../SPECS/spec-011-interfaces-0_0_4.md
[spec-037]: ../SPECS/spec-037-file_and_image_fields-0_0_11.md
[spec-039]: ../SPECS/spec-039-serializer_mutation_choices-0_0_11.md
[spec-048]: ../SPECS/spec-048-filesystem_path_fields-0_0_14.md

<!-- package source -->
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[rf-serializer-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py

<!-- tests -->
[tests-types]: ../../tests/types/
