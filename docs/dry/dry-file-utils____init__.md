# DRY review: `django_strawberry_framework/utils/__init__.py`

Status: verified

## System trace

`django_strawberry_framework/utils/__init__.py` defines the public convenience re-exports for cross-cutting framework utility helpers.

It owns the following architectural responsibilities:

1. **Subpackage Convenience Re-exports:**
   - Relation classification: [`RelationKind`][utils-relations], [`is_many_side_relation_kind`][utils-relations], and [`relation_kind`][utils-relations].
   - Casing helpers: [`pascal_case`][utils-strings] and [`snake_case`][utils-strings].
   - Type unwrapping: [`unwrap_graphql_type`][utils-typing] and [`unwrap_return_type`][utils-typing].

Connected behavior examined:
- [`django_strawberry_framework/utils/relations.py`][utils-relations]: Relation taxonomy and classification functions.
- [`django_strawberry_framework/utils/strings.py`][utils-strings]: Casing conversion helpers.
- [`django_strawberry_framework/utils/typing.py`][utils-typing]: Type introspection and unwrapping utilities.
- [`tests/utils/`][tests-utils]: Test coverage for utility functions.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/__init__.py --include-constants`):
- Parsed 1 target file, 49 lines.
- Complete inventory across all 7 re-exported symbols.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/__init__.py` provides single-sited convenience re-exports of core leaf helpers without creating wrapper layers or shadowing submodule definitions.

2. **Sync and async twins:**
   Module-level re-exports are static at import time.

3. **Derived rather than repeated knowledge:**
   Directly re-exports canonical implementations from sibling utility modules.

4. **Inverse and round-trip pairs:**
   Naming (`snake_case` / `pascal_case`) and type unwrapping (`unwrap_graphql_type` / `unwrap_return_type`) utilities.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/__init__.py`][utils-init], [`django_strawberry_framework/utils/relations.py`][utils-relations], [`django_strawberry_framework/utils/strings.py`][utils-strings], [`django_strawberry_framework/utils/typing.py`][utils-typing];
   - Test suites: [`tests/utils/`][tests-utils];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new utility re-export to `utils/__init__.py`):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/__init__.py`][utils-init].
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Re-exporting internal or heavy utility submodules:**
   - Disproved. `utils/__init__.py` intentionally exposes only lightweight leaf utilities (`relations`, `strings`, `typing`) to prevent circular import cascades across subsystems.

## Opportunities

None — `django_strawberry_framework/utils/__init__.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/__init__.py` exhibits zero duplicate code and complete policy consolidation across cross-cutting utility re-exports. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/__init__.py --review docs/dry/dry-file-utils____init__.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/__init__.py`][utils-init] and Worker 1's DRY review.

1. **Module Re-exports & Subpackage Boundaries:**
   - Confirmed `utils/__init__.py` exposes only pure leaf helpers and avoids eager loading of larger utility modules (`querysets`, `permissions`, `write_transaction`).
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/__init__.py --review docs/dry/dry-file-utils____init__.md --include-constants`. 100% coverage across all 7 definitions.

Confirmed: `django_strawberry_framework/utils/__init__.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- package source -->
[utils-init]: ../../django_strawberry_framework/utils/__init__.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py

<!-- tests -->
[tests-utils]: ../../tests/utils/
