# DRY review: `django_strawberry_framework/utils/write_values.py`

Status: verified

## System trace

`django_strawberry_framework/utils/write_values.py` implements the centralized write-value decode primitives, Unicode encoding preflights, choice-enum unwrap mechanics, relation ID type-checking and batch visibility decoding, and kind-routed write input field traversal ([spec-036][spec-036], [spec-040][spec-040], [spec-046][spec-046]).

It owns the following architectural responsibilities:

1. **Scalar Leaf & Choice Decoding:**
   - Unencodable text validation: [`unencodable_text_error`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::unencodable_text_error`).
   - Choice unwrapping: [`raw_choice_value`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::raw_choice_value`).
   - Scalar compose: [`decode_scalar_leaf`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::decode_scalar_leaf`).

2. **Relation ID Coercion & Visibility Decoding:**
   - Relation PK coercion: [`coerce_relation_pk_or_none`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::coerce_relation_pk_or_none`).
   - Structural relation ID check: [`type_check_relation_id`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::type_check_relation_id`).
   - Single relation decode spine: [`decode_visible_relation`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::decode_visible_relation`).
   - Batched relation ID decoder: [`decode_visible_relation_ids`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::decode_visible_relation_ids`).

3. **Field Handlers & Kind-Routed Traversal:**
   - Path and extra helpers: [`_spec_field_name`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::_spec_field_name`) and [`_no_relation_extra`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::_no_relation_extra`).
   - Storage primitives: [`store_decoded`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::store_decoded`) and [`decoded_into`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::decoded_into`).
   - Kind handlers: [`scalar_into`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::scalar_into`), [`file_into`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::file_into`), and [`relation_into`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::relation_into`).
   - Handler map builder: [`decode_field_handlers`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::decode_field_handlers`).
   - Kind-routed dispatcher: [`decode_provided_fields`][utils-write-values] (`django_strawberry_framework/utils/write_values.py::decode_provided_fields`).

Connected behavior examined:
- [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]: Model mutation input decoding.
- [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers]: Form mutation input decoding and file split.
- [`django_strawberry_framework/rest_framework/resolvers.py`][rest-framework-resolvers]: Serializer input decoding and nested data traversal.
- [`django_strawberry_framework/utils/querysets.py`][utils-querysets]: Batch existence and visibility queries via `visible_related_objects`.
- [`tests/utils/`][tests-utils]: Test suite validating scalar decoding, Unicode preflight, and relation batching.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/write_values.py --include-constants`):
- Parsed 1 target file, 475 lines.
- Complete inventory across all 16 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/write_values.py` consolidates write input decoding across Model, Form, and DRF Serializer mutations:
   - `unencodable_text_error` intercepts invalid surrogate pairs before any database validation or INSERT execution.
   - `raw_choice_value` unwraps Strawberry Enum instances to raw Django choice values uniformly.
   - `decode_visible_relation` and `decode_visible_relation_ids` enforce consistent visibility filtering without existence leaks.
   - `decode_provided_fields` provides the single kind-routed dispatch algorithm for all write inputs.

2. **Sync and async twins:**
   Decode operations and validation are synchronous Python operations; no async twins exist.

3. **Derived rather than repeated knowledge:**
   - `decode_scalar_leaf` composes `raw_choice_value` and `unencodable_text_error` in strict sequential order.
   - `decode_visible_relation_ids` batches all valid PKs into a single `pk__in` visibility query.

4. **Inverse and round-trip pairs:**
   `decode_provided_fields` pairs input field specification lists with bound input data dictionaries, projecting decoded values into flavor-specific destinations.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/write_values.py`][utils-write-values], [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers], [`django_strawberry_framework/rest_framework/resolvers.py`][rest-framework-resolvers];
   - Specifications: [`docs/SPECS/spec-036-mutation_visibility_contracts-0_0_10.md`][spec-036], [`docs/SPECS/spec-040-bulk_mutations-0_0_12.md`][spec-040], [`docs/SPECS/spec-046-composite_pk_support-0_0_14.md`][spec-046];
   - Test suites: [`tests/utils/`][tests-utils], [`tests/mutations/`][tests-mutations], [`tests/forms/`][tests-forms], [`tests/rest_framework/`][tests-rest-framework];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new text encoding preflight check for write fields):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/write_values.py`][utils-write-values] ([`unencodable_text_error`][utils-write-values]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Adjusting the batched relation visibility query generation):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/write_values.py`][utils-write-values] ([`decode_visible_relation_ids`][utils-write-values]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Modifying the field dispatch iteration loop or UNSET handling):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/write_values.py`][utils-write-values] ([`decode_provided_fields`][utils-write-values]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Decoding relation visibility separately inside each mutation flavor resolver:**
   - Disproved per [spec-036][spec-036]. Inconsistent relation resolution led to existence leaks and disparate error envelopes.

## Opportunities

None — `django_strawberry_framework/utils/write_values.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/write_values.py` exhibits zero duplicate code and complete policy consolidation across write value decoding, validation, and relation batching. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/write_values.py --review docs/dry/dry-file-utils__write_values.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/write_values.py`][utils-write-values] and Worker 1's DRY review.

1. **Write Value Primitives & Visibility:**
   - Confirmed `unencodable_text_error` catches invalid UTF-8 surrogate code points before database operations.
   - Confirmed `decode_visible_relation` and `decode_visible_relation_ids` prevent existence leaks by mapping missing and hidden relation targets to identical error envelopes.
   - Confirmed `decode_provided_fields` coordinates kind dispatch cleanly across scalar, relation, and file destinations.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/write_values.py --review docs/dry/dry-file-utils__write_values.md --include-constants`. 100% coverage across all 16 definitions / constants.

Confirmed: `django_strawberry_framework/utils/write_values.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-mutation_visibility_contracts-0_0_10.md
[spec-040]: ../SPECS/spec-040-bulk_mutations-0_0_12.md
[spec-046]: ../SPECS/spec-046-composite_pk_support-0_0_14.md

<!-- package source -->
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[rest-framework-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests -->
[tests-forms]: ../../tests/forms/
[tests-mutations]: ../../tests/mutations/
[tests-rest-framework]: ../../tests/rest_framework/
[tests-utils]: ../../tests/utils/
