# DRY review: `django_strawberry_framework/utils/context.py`

Status: verified

## System trace

`django_strawberry_framework/utils/context.py` implements shape-agnostic read, write, and delete helpers for Strawberry's `info.context` ([spec-047][spec-047]).

It owns the following architectural responsibilities:

1. **Context Sentinels & Access Helpers:**
   - Missing sentinel: [`_MISSING`][utils-context] (`django_strawberry_framework/utils/context.py::_MISSING`).
   - Context reader: [`get_context_value`][utils-context] (`django_strawberry_framework/utils/context.py::get_context_value`).
   - Context writer: [`stash_on_context`][utils-context] (`django_strawberry_framework/utils/context.py::stash_on_context`).
   - Context deleter: [`clear_context_key`][utils-context] (`django_strawberry_framework/utils/context.py::clear_context_key`).

Connected behavior examined:
- [`django_strawberry_framework/optimizer/_context.py`][optimizer-context]: Stashes optimizer plan, elision sets, and strictness configuration on the execution context.
- [`django_strawberry_framework/resource_policy.py`][resource-policy]: Stashes request-scoped resource policy configuration on `info.context`.
- [`tests/utils/`][tests-utils]: Test coverage for shape-agnostic context helpers.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/context.py --include-constants`):
- Parsed 1 target file, 207 lines.
- Complete inventory across all 4 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/context.py` centralizes context dispatch across `None`, plain dictionaries, custom objects, frozen dataclasses, and immutable mapping proxies (`MappingProxyType`, locked `QueryDict`). Symmetrical handling across read, write, and delete operations guarantees that optimizer and resource policy stashes behave identically.

2. **Sync and async twins:**
   Context read/write algorithms are pure Python operations executed symmetrically in sync and async contexts.

3. **Derived rather than repeated knowledge:**
   Dict-vs-object dispatch precedence is unified: `dict` instances use mapping protocols first; non-dict objects use attribute access first with mapping fallbacks.

4. **Inverse and round-trip pairs:**
   `stash_on_context` and `get_context_value` form an exact round-trip pair; `clear_context_key` provides the corresponding teardown operation.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/context.py`][utils-context], [`django_strawberry_framework/optimizer/_context.py`][optimizer-context], [`django_strawberry_framework/resource_policy.py`][resource-policy];
   - Specifications: [`docs/SPECS/spec-047-connection_by_default-0_0_14.md`][spec-047];
   - Test suites: [`tests/utils/`][tests-utils], [`tests/optimizer/`][tests-optimizer];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Supporting a new immutable context container error type in writes):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/context.py`][utils-context] ([`stash_on_context`][utils-context]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying read precedence or missing key sentinel in context lookup):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/context.py`][utils-context] ([`get_context_value`][utils-context] / [`_MISSING`][utils-context]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Inlining context reads/writes within `optimizer/_context.py` and `resource_policy.py`:**
   - Disproved per [spec-047][spec-047]. Centralizing in `utils/context.py` ensures consistent handling of edge cases (e.g., locked `QueryDict`, `__slots__` wrappers) across all framework extensions.

## Opportunities

None — `django_strawberry_framework/utils/context.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/context.py` exhibits zero duplicate code and complete policy consolidation across shape-agnostic context accessors. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/context.py --review docs/dry/dry-file-utils__context.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/context.py`][utils-context] and Worker 1's DRY review.

1. **Context Access Symmetry & Robustness:**
   - Confirmed `get_context_value`, `stash_on_context`, and `clear_context_key` maintain symmetrical precedence and handle frozen mappings and locked `QueryDict` safely.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/context.py --review docs/dry/dry-file-utils__context.md --include-constants`. 100% coverage across all 4 definitions / constants.

Confirmed: `django_strawberry_framework/utils/context.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-047]: ../SPECS/spec-047-connection_by_default-0_0_14.md

<!-- package source -->
[optimizer-context]: ../../django_strawberry_framework/optimizer/_context.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[utils-context]: ../../django_strawberry_framework/utils/context.py

<!-- tests -->
[tests-optimizer]: ../../tests/optimizer/
[tests-utils]: ../../tests/utils/
