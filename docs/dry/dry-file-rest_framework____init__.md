# DRY review: `django_strawberry_framework/rest_framework/__init__.py`

Status: verified

## System trace

`django_strawberry_framework/rest_framework/__init__.py` is the entry point and soft-dependency import guard for the DRF serializer mutation subsystem ([spec-039][spec-039]).

It owns the following architectural responsibilities:

1. **DRF Soft-Dependency Guard & Install Hint:**
   - [`_DRF_INSTALL_HINT`][rf-init] (`django_strawberry_framework/rest_framework/__init__.py::_DRF_INSTALL_HINT`): Single authoritative install-hint string specifying `djangorestframework>=3.17.0`.
   - [`require_drf`][rf-init] (`django_strawberry_framework/rest_framework/__init__.py::require_drf`): Guard function calling [`require_optional_module`][utils-imports] with `"rest_framework"` and `_DRF_INSTALL_HINT`.
   - Eager Package Guard: Module body executes `require_drf()` so importing `django_strawberry_framework.rest_framework` immediately raises an informative `ImportError` when DRF is absent.

Connected behavior examined:
- [`django_strawberry_framework/utils/imports.py`][utils-imports]: Houses the single-sited [`require_optional_module`][utils-imports] primitive shared with Channels and Django Debug Toolbar guards.
- [`django_strawberry_framework/__init__.py`][root-init]: Routes root `SerializerMutation` lazy access through `require_drf()` via `__getattr__` and `_DRF_SOFT_EXPORTS`.
- [`django_strawberry_framework/rest_framework/sets.py`][rf-sets]: Submodule housing `SerializerMutation` and `SerializerMutationMetaclass`.
- [`tests/rest_framework/test_soft_dependency.py`][test-rf-soft-dependency]: Test suite verifying root import cleanliness, `*`-import safety, lazy `__getattr__` dispatch, and absence simulation.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/rest_framework/__init__.py --include-constants`):
- Parsed 1 target file, 62 lines.
- Inventory of symbols (2 definitions):
  - 1 constant: [`_DRF_INSTALL_HINT`][rf-init].
  - 1 function: [`require_drf`][rf-init].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `require_drf()` mirrors soft-dependency guards across the package (`routers.py::require_channels`, `middleware/debug_toolbar.py::require_debug_toolbar`), but all optional module import resolution and exception handling mechanics are single-sited in [`require_optional_module`][utils-imports] in `django_strawberry_framework/utils/imports.py`. `rest_framework/__init__.py` owns only the DRF-specific package target and verified floor hint string ([`_DRF_INSTALL_HINT`][rf-init]).

2. **Sync and async twins:**
   Zero duplication. Python import mechanics are purely synchronous.

3. **Derived rather than repeated knowledge:**
   The install hint [`_DRF_INSTALL_HINT`][rf-init] is the authoritative single source for the DRF installation prompt across all `rest_framework/` submodules and the root `django_strawberry_framework.__getattr__`.

4. **Inverse and round-trip pairs:**
   [`require_drf`][rf-init] provides an idempotent import check that works cleanly with simulated absence eviction and restore cycles.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/rest_framework/__init__.py`][rf-init], [`django_strawberry_framework/utils/imports.py`][utils-imports], [`django_strawberry_framework/__init__.py`][root-init];
   - Specifications: [`docs/SPECS/spec-039-serializer_mutation-0_0_11.md`][spec-039];
   - Test suites: [`tests/rest_framework/test_soft_dependency.py`][test-rf-soft-dependency];
   - Configuration: `pyproject.toml` (`[dependency-groups].dev` pin);
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Modifying the optional module import or error handling logic):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/imports.py`][utils-imports] ([`require_optional_module`][utils-imports]).
  - *Propagation count:* 0 in `rest_framework/__init__.py`.
- **Posited change 2 (Updating the minimum required DRF version string / install hint message):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/rest_framework/__init__.py`][rf-init] ([`_DRF_INSTALL_HINT`][rf-init]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Changing the root package lazy export lookup dispatch for DRF symbols):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/__init__.py`][root-init] (`__getattr__` / `_DRF_SOFT_EXPORTS`).
  - *Propagation count:* 0 in `rest_framework/__init__.py`.

### Rejected candidates

1. **Re-implementing `importlib.import_module` try/except blocks locally in `rest_framework/__init__.py`:**
   - Disproved per [spec-039][spec-039]. Using `require_optional_module` centralizes soft-dependency handling across the codebase.
2. **Duplicating `_DRF_INSTALL_HINT` across `sets.py` and `inputs.py`:**
   - Disproved per [spec-039][spec-039]. Housing `require_drf()` in `rest_framework/__init__.py` ensures all submodules share one hint.

## Opportunities

None — `django_strawberry_framework/rest_framework/__init__.py` is a clean, 62-line guard module delegating mechanics to `django_strawberry_framework/utils/imports.py`.

## Judgment

Verified. `rest_framework/__init__.py` exhibits zero duplicate code and complete policy consolidation through `utils/imports.py`. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/rest_framework/__init__.py --review docs/dry/dry-file-rest_framework____init__.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/rest_framework/__init__.py`][rf-init] and Worker 1's DRY review.

1. **Soft-Dependency Guard & Single Siting:**
   - Confirmed `require_drf` delegates directly to `require_optional_module`.
   - Confirmed `_DRF_INSTALL_HINT` is the sole definition of the DRF install hint string.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/rest_framework/__init__.py --review docs/dry/dry-file-rest_framework____init__.md --include-constants`. 100% coverage across all definitions.

Confirmed: `django_strawberry_framework/rest_framework/__init__.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-039]: ../SPECS/spec-039-serializer_mutation-0_0_11.md

<!-- package source -->
[rf-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[rf-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[root-init]: ../../django_strawberry_framework/__init__.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py

<!-- tests -->
[test-rf-soft-dependency]: ../../tests/rest_framework/test_soft_dependency.py
