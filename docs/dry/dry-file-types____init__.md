# DRY review: `django_strawberry_framework/types/__init__.py`

Status: verified

## System trace

`django_strawberry_framework/types/__init__.py` defines the public export facade for the type-system subsystem, providing canonical access to `DjangoType`, `finalize_django_types`, and `SyncMisuseError` ([spec-032][spec-032], [spec-034][spec-034]).

It re-exports the following public symbols:

1. **Core Type Foundation:**
   - [`DjangoType`][types-init] (`django_strawberry_framework/types/__init__.py::DjangoType`): Base class for Django-backed GraphQL type definitions.

2. **Schema Finalization Engine:**
   - [`finalize_django_types`][types-init] (`django_strawberry_framework/types/__init__.py::finalize_django_types`): Top-level schema compiler executing phase 2.5 and phase 3 type binding.

3. **Relay Asynchronous Execution Guard:**
   - [`SyncMisuseError`][types-init] (`django_strawberry_framework/types/__init__.py::SyncMisuseError`): Error raised when synchronous Node resolution is attempted in async contexts without async fallback.

Connected behavior examined:
- [`django_strawberry_framework/types/base.py`][types-base]: `DjangoType` base class implementation.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Multi-phase schema compiler and finalizer.
- [`django_strawberry_framework/types/relay.py`][types-relay]: Relay integration and `SyncMisuseError` definition.
- [`tests/types/`][tests-types]: Comprehensive test suite for type definition, conversion, and finalization.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/types/__init__.py --include-constants`):
- Parsed 1 target file, 36 lines.
- Complete inventory across all 3 exported definitions.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `types/__init__.py` serves as a clean re-export interface without introducing duplicate classes or functions. Internal conversion and resolution helpers remain isolated within submodule boundaries.

2. **Sync and async twins:**
   Zero duplication. Re-exports `SyncMisuseError` from `types/relay.py`.

3. **Derived rather than repeated knowledge:**
   All exported symbols are imported directly from their respective source modules.

4. **Inverse and round-trip pairs:**
   `finalize_django_types` serves as the primary compile-time entrypoint.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/types/__init__.py`][types-init], [`django_strawberry_framework/types/base.py`][types-base], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/types/relay.py`][types-relay];
   - Specifications: [`docs/SPECS/spec-032-full_relay-0_0_9.md`][spec-032], [`docs/SPECS/spec-034-schema_finalization_refactor-0_0_10.md`][spec-034];
   - Test suites: [`tests/types/`][tests-types];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new public type system export):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/__init__.py`][types-init] (`__all__`).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying `DjangoType` metaclass processing):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/base.py`][types-base] ([`DjangoType`][types-base]).
  - *Propagation count:* 0 in `types/__init__.py`.

### Rejected candidates

1. **Re-exporting all internal converters in `types/__init__.py`:**
   - Disproved per [spec-034][spec-034]. Encapsulating internal conversion and relation helpers within submodule paths keeps the public import surface clean and prevents namespace pollution.

## Opportunities

None — `django_strawberry_framework/types/__init__.py` is a clean re-export facade.

## Judgment

Verified. `types/__init__.py` exhibits zero duplicate code. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/types/__init__.py --review docs/dry/dry-file-types____init__.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/types/__init__.py`][types-init] and Worker 1's DRY review.

1. **Public Exports & Encapsulation:**
   - Confirmed public symbols match canonical package export expectations.
   - Confirmed internal submodule boundaries are preserved.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/types/__init__.py --review docs/dry/dry-file-types____init__.md --include-constants`. 100% coverage across all 3 definitions.

Confirmed: `django_strawberry_framework/types/__init__.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md
[spec-034]: ../SPECS/spec-034-schema_finalization_refactor-0_0_10.md

<!-- package source -->
[types-base]: ../../django_strawberry_framework/types/base.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-init]: ../../django_strawberry_framework/types/__init__.py
[types-relay]: ../../django_strawberry_framework/types/relay.py

<!-- tests -->
[tests-types]: ../../tests/types/
