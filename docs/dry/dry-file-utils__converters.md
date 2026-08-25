# DRY review: `django_strawberry_framework/utils/converters.py`

Status: verified

## System trace

`django_strawberry_framework/utils/converters.py` implements the centralized converter-dispatch skeleton shared across form field conversion (`forms/converter.py`), serializer field conversion (`rest_framework/serializer_converter.py`), and filter input conversion (`filters/inputs.py`) ([spec-039][spec-039], [spec-051][spec-051]).

It owns the following architectural responsibilities:

1. **Sentinels & MRO Dispatch Engine:**
   - Sentinel class: [`_MroContinue`][utils-converters] (`django_strawberry_framework/utils/converters.py::_MroContinue` with method [`_MroContinue.__repr__`][utils-converters]).
   - Sentinel instance: [`MRO_CONTINUE`][utils-converters] (`django_strawberry_framework/utils/converters.py::MRO_CONTINUE`).
   - MRO dispatcher: [`convert_with_mro`][utils-converters] (`django_strawberry_framework/utils/converters.py::convert_with_mro`).

2. **Converter Factories & Result Normalization:**
   - Kind converter factory: [`make_kind_converter`][utils-converters] (`django_strawberry_framework/utils/converters.py::make_kind_converter`).
   - Scalar converter factory: [`make_scalar_converter`][utils-converters] (`django_strawberry_framework/utils/converters.py::make_scalar_converter`).
   - Result wrapper: [`finish_field_conversion`][utils-converters] (`django_strawberry_framework/utils/converters.py::finish_field_conversion`).

Connected behavior examined:
- [`django_strawberry_framework/forms/converter.py`][forms-converter]: Form field conversion using `convert_with_mro`.
- [`django_strawberry_framework/rest_framework/serializer_converter.py`][serializer-converter]: Serializer field conversion using `convert_with_mro`.
- [`django_strawberry_framework/filters/inputs.py`][filters-inputs]: Filter input normalization using `convert_with_mro`.
- [`tests/utils/`][tests-utils]: Test coverage for converter utilities.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/converters.py --include-constants`):
- Parsed 1 target file, 173 lines.
- Complete inventory across all 6 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/converters.py` centralizes the 3-phase conversion pipeline (ordered `isinstance` prechecks -> scalar registry MRO walk -> fail-loud fallthrough raise) shared by Django Forms, DRF Serializers, and FilterSet inputs without coupling their disparate key spaces or dependencies.

2. **Sync and async twins:**
   Conversion mechanics operate synchronously during schema building and mutation execution.

3. **Derived rather than repeated knowledge:**
   `make_scalar_converter` derives scalar conversions directly from `make_kind_converter(..., SCALAR)`.

4. **Inverse and round-trip pairs:**
   `convert_with_mro` and `finish_field_conversion` map source framework field classes to unified `FieldConversionBase` instances.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/converters.py`][utils-converters], [`django_strawberry_framework/forms/converter.py`][forms-converter], [`django_strawberry_framework/rest_framework/serializer_converter.py`][serializer-converter], [`django_strawberry_framework/filters/inputs.py`][filters-inputs];
   - Specifications: [`docs/SPECS/spec-039-rest_framework_mutations-0_0_12.md`][spec-039], [`docs/SPECS/spec-051-finalizer_sidecar_dry-0_0_14.md`][spec-051];
   - Test suites: [`tests/utils/`][tests-utils], [`tests/forms/`][tests-forms], [`tests/rest_framework/`][tests-rest_framework];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Altering MRO traversal precedence or metaclass-safe inspection in `convert_with_mro`):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/converters.py`][utils-converters] ([`convert_with_mro`][utils-converters]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying the `FieldConversionBase` finalization dispatch):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/converters.py`][utils-converters] ([`finish_field_conversion`][utils-converters]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Merging form and serializer scalar registries into a single dictionary:**
   - Disproved per [spec-039][spec-039]. Keeping key spaces distinct prevents hard dependencies on DRF when only Django Forms are used.
2. **Spelling separate MRO dispatch loops in `forms` and `rest_framework`:**
   - Disproved per [spec-039][spec-039] and [spec-051][spec-051]. Unified in `convert_with_mro` to guarantee consistent fail-loud semantics across all input flavors.

## Opportunities

None — `django_strawberry_framework/utils/converters.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/converters.py` exhibits zero duplicate code and complete policy consolidation across input conversion dispatch. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/converters.py --review docs/dry/dry-file-utils__converters.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/converters.py`][utils-converters] and Worker 1's DRY review.

1. **Converter Pipeline & Safety Contracts:**
   - Confirmed `convert_with_mro` safely inspects MRO attributes using `type.__getattribute__` and matches keys by identity to guard against hostile metaclass overrides.
   - Confirmed `make_scalar_converter`, `make_kind_converter`, and `finish_field_conversion` cleanly bridge converter outputs.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/converters.py --review docs/dry/dry-file-utils__converters.md --include-constants`. 100% coverage across all 6 definitions / constants.

Confirmed: `django_strawberry_framework/utils/converters.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-039]: ../SPECS/spec-039-rest_framework_mutations-0_0_12.md
[spec-051]: ../SPECS/spec-051-finalizer_sidecar_dry-0_0_14.md

<!-- package source -->
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[serializer-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[utils-converters]: ../../django_strawberry_framework/utils/converters.py

<!-- tests -->
[tests-forms]: ../../tests/forms/
[tests-rest_framework]: ../../tests/rest_framework/
[tests-utils]: ../../tests/utils/
