# DRY review: `django_strawberry_framework/utils/imports.py`

Status: verified

## System trace

`django_strawberry_framework/utils/imports.py` implements the centralized import helpers for best-effort, loaded-only, strict, and guarded optional-dependency lookups ([spec-041][spec-041]).

It owns the following architectural responsibilities:

1. **Import String Normalization:**
   - String normalization helper: [`_plain_text`][utils-imports] (`django_strawberry_framework/utils/imports.py::_plain_text`).

2. **Dynamic Import Family:**
   - Best-effort attribute import: [`import_attr_if_importable`][utils-imports] (`django_strawberry_framework/utils/imports.py::import_attr_if_importable`).
   - Opt-in preserving loaded attribute lookup: [`loaded_attr`][utils-imports] (`django_strawberry_framework/utils/imports.py::loaded_attr`).
   - Strict attribute import: [`import_attr`][utils-imports] (`django_strawberry_framework/utils/imports.py::import_attr`).
   - Optional dependency guard: [`require_optional_module`][utils-imports] (`django_strawberry_framework/utils/imports.py::require_optional_module`).

Connected behavior examined:
- [`django_strawberry_framework/registry.py`][registry]: Uses `import_attr_if_importable` for cross-subsystem registry co-clearing.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Uses `loaded_attr` to detect auth extensions without forcing imports.
- [`django_strawberry_framework/routers.py`][routers]: Uses `require_optional_module` to guard optional Channels router dependencies.
- [`tests/utils/`][tests-utils]: Test coverage for import utilities.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/imports.py --include-constants`):
- Parsed 1 target file, 114 lines.
- Complete inventory across all 5 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/imports.py` provides distinct, single-sited primitives for the four standard dynamic import patterns across the codebase:
   - Best-effort import (`import_attr_if_importable`) for optional PostgreSQL/contrib integrations.
   - Loaded-only lookup (`loaded_attr`) for preserving consumer opt-ins without side-effects.
   - Strict import (`import_attr`) for internal cycle-breaking seams.
   - Soft-dependency enforcement (`require_optional_module`) for clear error messages when optional packages (Channels, DRF) are missing.

2. **Sync and async twins:**
   Dynamic import helpers are synchronous primitives invoked at module load or schema finalization.

3. **Derived rather than repeated knowledge:**
   Module names and attribute strings are normalized centrally through `_plain_text` before reaching standard import machinery.

4. **Inverse and round-trip pairs:**
   `loaded_attr` (non-importing) vs `import_attr` (strictly importing) establish precise semantic boundaries for optional versus required module traversal.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/imports.py`][utils-imports], [`django_strawberry_framework/registry.py`][registry], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/routers.py`][routers];
   - Specifications: [`docs/SPECS/spec-041-channels_subscriptions-0_0_13.md`][spec-041];
   - Test suites: [`tests/utils/`][tests-utils];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Altering string normalization or subclass defense before import machinery):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/imports.py`][utils-imports] ([`_plain_text`][utils-imports]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying the exception chaining or structure in `require_optional_module`):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/imports.py`][utils-imports] ([`require_optional_module`][utils-imports]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Inlining `try...importlib.import_module` across subsystems:**
   - Disproved per [spec-041][spec-041]. Inlined imports lead to inconsistent exception swallowing (e.g., masking real `AttributeError`s) and divergent error message formatting.

## Opportunities

None — `django_strawberry_framework/utils/imports.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/imports.py` exhibits zero duplicate code and complete policy consolidation across dynamic import operations. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/imports.py --review docs/dry/dry-file-utils__imports.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/imports.py`][utils-imports] and Worker 1's DRY review.

1. **Dynamic Import Semantics & Error Boundaries:**
   - Confirmed `import_attr_if_importable` swallows `ImportError` while letting `AttributeError` propagate.
   - Confirmed `require_optional_module` wraps `ImportError` with actionable user hints while preserving exception causes.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/imports.py --review docs/dry/dry-file-utils__imports.md --include-constants`. 100% coverage across all 5 definitions / constants.

Confirmed: `django_strawberry_framework/utils/imports.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-041]: ../SPECS/spec-041-channels_subscriptions-0_0_13.md

<!-- package source -->
[registry]: ../../django_strawberry_framework/registry.py
[routers]: ../../django_strawberry_framework/routers.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py

<!-- tests -->
[tests-utils]: ../../tests/utils/
