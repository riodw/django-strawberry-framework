# DRY review: `django_strawberry_framework/testing/_wrap.py`

Status: verified

## System trace

`django_strawberry_framework/testing/_wrap.py` provides cooperative connection-method wrapping for consumer test instrumentation, forming the wrap-time half of the defense-in-depth against Django Trac #37064 ([spec-043][spec-043]).

It owns the following architectural responsibility:

1. **Cooperative Connection Wrapping:**
   - [`safe_wrap_connection_method`][testing-wrap] (`django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method`): Wraps database connection methods (e.g. `cursor`, `create_cursor`) only if Django's `_DatabaseFailure` wrapper is not already present, utilizing [`_is_database_failure`][django-patches].

Connected behavior examined:
- [`django_strawberry_framework/_django_patches.py`][django-patches]: Central unwrap-time teardown patch and `_is_database_failure` predicate definition.
- [`django_strawberry_framework/testing/__init__.py`][testing-init]: Public re-export.
- [`tests/testing/test_wrap.py`][tests-testing-wrap]: Comprehensive test coverage for connection wrapping, failure detection, and non-callable rejection.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/testing/_wrap.py --include-constants`):
- Parsed 1 target file, 148 lines.
- Complete inventory across all target definitions.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `testing/_wrap.py` reuses [`_is_database_failure`][django-patches] directly from `_django_patches.py` rather than maintaining an independent copy of the `_DatabaseFailure` reflection check.

2. **Sync and async twins:**
   Zero duplication. Connection wrapping executes synchronously at test setup time.

3. **Derived rather than repeated knowledge:**
   Failure type resolution delegates entirely to `_django_patches._is_database_failure`.

4. **Inverse and round-trip pairs:**
   `safe_wrap_connection_method` (wrap time) and `_django_patches` (unwrap teardown time) form a symmetrical defense-in-depth pair.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/testing/_wrap.py`][testing-wrap], [`django_strawberry_framework/_django_patches.py`][django-patches];
   - Specifications: [`docs/SPECS/spec-043-test_client-0_0_12.md`][spec-043];
   - Test suites: [`tests/testing/test_wrap.py`][tests-testing-wrap];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Modifying the wrap-time installation logic or error validation):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/testing/_wrap.py`][testing-wrap] ([`safe_wrap_connection_method`][testing-wrap]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Adjusting the `_DatabaseFailure` detection predicate):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/_django_patches.py`][django-patches] ([`_is_database_failure`][django-patches]).
  - *Propagation count:* 0 in `testing/_wrap.py`.

### Rejected candidates

1. **Duplicating `_is_database_failure` in `testing/_wrap.py`:**
   - Disproved per [spec-043][spec-043]. Sharing `_is_database_failure` between `_django_patches.py` and `testing/_wrap.py` prevents desynchronization if Django internals change.

## Opportunities

None — `django_strawberry_framework/testing/_wrap.py` is fully consolidated with `django_strawberry_framework/_django_patches.py`.

## Judgment

Verified. `testing/_wrap.py` exhibits zero duplicate code and complete policy consolidation. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/testing/_wrap.py --review docs/dry/dry-file-testing___wrap.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/testing/_wrap.py`][testing-wrap] and Worker 1's DRY review.

1. **Wrap Architecture & Defense-in-Depth:**
   - Confirmed `safe_wrap_connection_method` delegates type inspection to `_django_patches._is_database_failure`.
   - Confirmed error checking and return values adhere strictly to `spec-043`.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/testing/_wrap.py --review docs/dry/dry-file-testing___wrap.md --include-constants`. 100% coverage across all target definitions.

Confirmed: `django_strawberry_framework/testing/_wrap.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-043]: ../SPECS/spec-043-test_client-0_0_12.md

<!-- package source -->
[django-patches]: ../../django_strawberry_framework/_django_patches.py
[testing-init]: ../../django_strawberry_framework/testing/__init__.py
[testing-wrap]: ../../django_strawberry_framework/testing/_wrap.py

<!-- tests -->
[tests-testing-wrap]: ../../tests/testing/test_wrap.py
