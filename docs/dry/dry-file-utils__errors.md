# DRY review: `django_strawberry_framework/utils/errors.py`

Status: verified

## System trace

`django_strawberry_framework/utils/errors.py` implements the centralized, flavor-neutral `FieldError` and mutation write-error envelope constructors ([spec-036][spec-036], [spec-038][spec-038], [spec-039][spec-039]).

It owns the following architectural responsibilities:

1. **Leaf `FieldError` Construction & Path Normalization:**
   - Single leaf constructor: [`field_error`][utils-errors] (`django_strawberry_framework/utils/errors.py::field_error`).
   - String & list coercions: [`_str_list`][utils-errors], [`_safe_text`][utils-errors], and [`_unprintable`][utils-errors].
   - Path joiner: [`join_error_path`][utils-errors] (`django_strawberry_framework/utils/errors.py::join_error_path`).

2. **Validation Error & Relation Error Mappers:**
   - Django `ValidationError` leaf helpers: [`_validation_messages`][utils-errors], [`_validation_code`][utils-errors], [`_validation_codes`][utils-errors], [`_empty_validation_error`][utils-errors], and [`_error_dict_entry`][utils-errors].
   - Relation decode error constructor: [`relation_field_error`][utils-errors] (`django_strawberry_framework/utils/errors.py::relation_field_error`).
   - Django validation error flattener: [`validation_error_to_field_errors`][utils-errors] (`django_strawberry_framework/utils/errors.py::validation_error_to_field_errors`).
   - Database constraint error flattener: [`integrity_error_field_errors`][utils-errors] (`django_strawberry_framework/utils/errors.py::integrity_error_field_errors`).

Connected behavior examined:
- [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs]: Declares `FieldError` and `NON_FIELD_ERROR_KEY`.
- [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]: Model mutation execution and error normalization.
- [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers]: Form mutation execution and error normalization.
- [`django_strawberry_framework/rest_framework/resolvers.py`][serializer-resolvers]: Serializer mutation execution and error normalization.
- [`tests/utils/`][tests-utils]: Test coverage for error mapping utilities.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/errors.py --include-constants`):
- Parsed 1 target file, 377 lines.
- Complete inventory across all 13 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/errors.py` unifies error envelope generation across Model mutations, Django Form mutations, and DRF Serializer mutations:
   - Root non-field errors consistently route to `NON_FIELD_ERROR_KEY` (`"__all__"`) with empty `path` segments (`[]`).
   - Relation decode errors across all flavors emit uniform `relation_field_error` envelopes without leaking existence details.
   - `ValidationError` and `IntegrityError` mappings produce consistent, structured error envelopes.

2. **Sync and async twins:**
   Error formatting and translation routines are pure synchronous functions executed on mutation error pathways.

3. **Derived rather than repeated knowledge:**
   `field_error` derives structured `path` segments from dotted string paths and coerces messages and error codes uniformly via `_str_list`.

4. **Inverse and round-trip pairs:**
   `join_error_path` joins nested path segments into dotted strings; `field_error` splits dotted path strings into path segment lists.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/errors.py`][utils-errors], [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs], [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers], [`django_strawberry_framework/rest_framework/resolvers.py`][serializer-resolvers];
   - Specifications: [`docs/SPECS/spec-036-model_mutations-0_0_11.md`][spec-036], [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038], [`docs/SPECS/spec-039-rest_framework_mutations-0_0_12.md`][spec-039];
   - Test suites: [`tests/utils/`][tests-utils], [`tests/mutations/`][tests-mutations], [`tests/forms/`][tests-forms], [`tests/rest_framework/`][tests-rest_framework];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Altering non-field error path segmentation or code normalization):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/errors.py`][utils-errors] ([`field_error`][utils-errors]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Updating the standard relation error message text):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/errors.py`][utils-errors] ([`relation_field_error`][utils-errors]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Modifying the database constraint violation message or code):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/errors.py`][utils-errors] ([`integrity_error_field_errors`][utils-errors]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Retaining separate error construction functions per write flavor:**
   - Disproved per [spec-039][spec-039]. Consolidating in `utils/errors.py` ensures identical error responses across all mutation styles.
2. **Importing `mutations.inputs` at module level in `utils/errors.py`:**
   - Disproved. Deferred function-local import prevents circular dependencies between `utils` and `mutations`.

## Opportunities

None — `django_strawberry_framework/utils/errors.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/errors.py` exhibits zero duplicate code and complete policy consolidation across write error envelope construction. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/errors.py --review docs/dry/dry-file-utils__errors.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/errors.py`][utils-errors] and Worker 1's DRY review.

1. **Error Formatting & Hostile Object Protection:**
   - Confirmed `_safe_text`, `_str_list`, and `_validation_messages` guard against hostile string dunders or unprintable exceptions during error normalization.
   - Confirmed `validation_error_to_field_errors` and `integrity_error_field_errors` correctly map Django exceptions to `FieldError` envelopes.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/errors.py --review docs/dry/dry-file-utils__errors.md --include-constants`. 100% coverage across all 13 definitions / constants.

Confirmed: `django_strawberry_framework/utils/errors.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-model_mutations-0_0_11.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-rest_framework_mutations-0_0_12.md

<!-- package source -->
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[serializer-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[utils-errors]: ../../django_strawberry_framework/utils/errors.py

<!-- tests -->
[tests-forms]: ../../tests/forms/
[tests-mutations]: ../../tests/mutations/
[tests-rest_framework]: ../../tests/rest_framework/
[tests-utils]: ../../tests/utils/
