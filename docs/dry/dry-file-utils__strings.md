# DRY review: `django_strawberry_framework/utils/strings.py`

Status: verified

## System trace

`django_strawberry_framework/utils/strings.py` implements the centralized GraphQL/Django identifier naming, case conversions, injective casing pairs, and lookup path flattening ([spec-027][spec-027], [spec-028][spec-028], [spec-030][spec-030], [spec-051][spec-051]).

It owns the following architectural responsibilities:

1. **String Normalization & Snake-Case Caching:**
   - Normalizer: [`_plain_text`][utils-strings] (`django_strawberry_framework/utils/strings.py::_plain_text`).
   - Cached snake_case converter: [`_snake_case_cached`][utils-strings] (`django_strawberry_framework/utils/strings.py::_snake_case_cached`) and [`snake_case`][utils-strings] (`django_strawberry_framework/utils/strings.py::snake_case`).

2. **Pascal Case & Token Validation:**
   - Pascal case converter: [`pascal_case`][utils-strings] (`django_strawberry_framework/utils/strings.py::pascal_case`).
   - Token validation wrapper: [`pascal_case_or_raise`][utils-strings] (`django_strawberry_framework/utils/strings.py::pascal_case_or_raise`).

3. **Injective Camel Casing & Lookup Flattening:**
   - GraphQL camelCase converter: [`graphql_camel_name`][utils-strings] (`django_strawberry_framework/utils/strings.py::graphql_camel_name`).
   - Path separator flattening: [`flatten_lookup_path`][utils-strings] (`django_strawberry_framework/utils/strings.py::flatten_lookup_path`).

Connected behavior examined:
- [`django_strawberry_framework/filters/inputs.py`][filters-inputs]: Generated filter input field naming and type PascalCase naming.
- [`django_strawberry_framework/orders/inputs.py`][orders-inputs]: Order input field naming and aggregate alias mangling via `flatten_lookup_path`.
- [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker]: Field selection resolution via `snake_case`.
- [`django_strawberry_framework/utils/permissions.py`][utils-permissions]: Method name formatting for permission gates.
- [`tests/utils/`][tests-utils]: Test suite validating casing invariants and round-trip properties.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/strings.py --include-constants`):
- Parsed 1 target file, 220 lines.
- Complete inventory across all 7 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/strings.py` provides uniform naming algorithms across queries, filters, orders, and optimizer walkers:
   - `snake_case` safely inverts GraphQL field camelCasing back to Django model attributes.
   - `pascal_case` and `pascal_case_or_raise` guarantee stable generated enum and type naming.
   - `flatten_lookup_path` ensures `LOOKUP_SEP` (`__`) is systematically stripped from Python field attributes, permission hook names, and aggregate aliases.

2. **Sync and async twins:**
   String manipulation is synchronous and stateless; no async twins exist.

3. **Derived rather than repeated knowledge:**
   `graphql_camel_name` and `snake_case` preserve digit separators and one-letter segment markers (`__x`) to remain strictly injective.

4. **Inverse and round-trip pairs:**
   - `graphql_camel_name` and `snake_case` form an injective round-trip pair over valid snake_case identifiers.
   - `pascal_case` and `pascal_case_or_raise` form the base/guarded pair for type name derivation.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/strings.py`][utils-strings], [`django_strawberry_framework/filters/inputs.py`][filters-inputs], [`django_strawberry_framework/orders/inputs.py`][orders-inputs], [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker];
   - Specifications: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027], [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028], [`docs/SPECS/spec-030-optimizer-0_0_9.md`][spec-030], [`docs/SPECS/spec-051-finalizer_sidecar_dry-0_0_14.md`][spec-051];
   - Test suites: [`tests/utils/`][tests-utils], [`tests/filters/`][tests-filters];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adjusting acronym splitting rules during camel-to-snake conversion):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/strings.py`][utils-strings] ([`_snake_case_cached`][utils-strings]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying the digit-separation delimiter in PascalCase generation):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/strings.py`][utils-strings] ([`pascal_case`][utils-strings]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Changing the lookup path flattening delimiter reduction algorithm):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/strings.py`][utils-strings] ([`flatten_lookup_path`][utils-strings]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Inlining `.replace("__", "_")` in filter/order input generators:**
   - Disproved per [spec-051][spec-051]. Inlined replacements risked leaking double underscores into prefetch `to_attr` paths and method mangles.

## Opportunities

None — `django_strawberry_framework/utils/strings.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/strings.py` exhibits zero duplicate code and complete policy consolidation across casing transformations and lookup path flattening. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/strings.py --review docs/dry/dry-file-utils__strings.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/strings.py`][utils-strings] and Worker 1's DRY review.

1. **Casing Invariants & Injectivity:**
   - Confirmed `snake_case` and `graphql_camel_name` maintain injectivity over complex tokens and adjacent single-character segments.
   - Confirmed `pascal_case_or_raise` provides unified validation for non-empty word token inputs.
   - Confirmed `flatten_lookup_path` safely collapses all instances of `__`.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/strings.py --review docs/dry/dry-file-utils__strings.md --include-constants`. 100% coverage across all 7 definitions / constants.

Confirmed: `django_strawberry_framework/utils/strings.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-027]: ../SPECS/spec-027-filters-0_0_8.md
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-030]: ../SPECS/spec-030-optimizer-0_0_9.md
[spec-051]: ../SPECS/spec-051-finalizer_sidecar_dry-0_0_14.md

<!-- package source -->
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py

<!-- tests -->
[tests-filters]: ../../tests/filters/
[tests-utils]: ../../tests/utils/
