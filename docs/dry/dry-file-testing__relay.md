# DRY review: `django_strawberry_framework/testing/relay.py`

Status: verified

## System trace

`django_strawberry_framework/testing/relay.py` provides consumer test helpers for minting and asserting durable Relay `GlobalID` strings ([spec-032][spec-032], [spec-043][spec-043]).

It owns the following architectural responsibilities:

1. **Relay GlobalID Test Helpers:**
   - [`global_id_for`][testing-relay] (`django_strawberry_framework/testing/relay.py::global_id_for`): Mints the encoded `GlobalID` string a finalized `Relay.Node`-shaped `DjangoType` emits for a given primary key, verifying registration in [`registry`][registry], finalization status, and string strategy membership via [`STRING_GLOBALID_STRATEGIES`][types-base], before delegating to [`encode_typename`][types-relay].
   - [`decode_global_id`][testing-relay] (`django_strawberry_framework/testing/relay.py::decode_global_id`): Direct public re-export of [`types/relay.py::decode_global_id`][types-relay].

Connected behavior examined:
- [`django_strawberry_framework/types/relay.py`][types-relay]: Internal Relay encoding and decoding primitives (`encode_typename`, `decode_global_id`).
- [`django_strawberry_framework/types/base.py`][types-base]: `DjangoType` base class, strategy constants (`STRING_GLOBALID_STRATEGIES`), and error templates (`_RELAY_NODE_GATE_LEAD`, `_RELAY_NODE_GATE_INHERIT_TAIL`).
- [`django_strawberry_framework/registry.py`][registry]: Central definition and model registry.
- [`tests/testing/test_relay.py`][tests-testing-relay]: Unit tests for Relay test helpers.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/testing/relay.py --include-constants`):
- Parsed 1 target file, 111 lines.
- Complete inventory across all target definitions.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `testing/relay.py` reuses core Relay typename encoding (`encode_typename`) and decoding (`decode_global_id`) directly from [`django_strawberry_framework/types/relay.py`][types-relay]. It imports type constants and error messages directly from [`django_strawberry_framework/types/base.py`][types-base] rather than defining duplicates.

2. **Sync and async twins:**
   Zero duplication. GlobalID minting and decoding are pure synchronous AST operations.

3. **Derived rather than repeated knowledge:**
   `global_id_for` derives the emitted payload from `definition.effective_globalid_strategy`, ensuring strict consistency with live GraphQL field resolution.

4. **Inverse and round-trip pairs:**
   `global_id_for` and `decode_global_id` form an encode/decode test pair reflecting the underlying Relay specification.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/testing/relay.py`][testing-relay], [`django_strawberry_framework/types/relay.py`][types-relay], [`django_strawberry_framework/types/base.py`][types-base];
   - Specifications: [`docs/SPECS/spec-032-full_relay-0_0_9.md`][spec-032], [`docs/SPECS/spec-043-test_client-0_0_12.md`][spec-043];
   - Test suites: [`tests/testing/test_relay.py`][tests-testing-relay];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Modifying the GlobalID encoding implementation):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/relay.py`][types-relay] ([`encode_typename`][types-relay]).
  - *Propagation count:* 0 in `testing/relay.py`.
- **Posited change 2 (Adjusting the Relay Node gate error wording):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/base.py`][types-base] ([`_RELAY_NODE_GATE_LEAD`][types-base]).
  - *Propagation count:* 0 in `testing/relay.py`.
- **Posited change 3 (Modifying unfinalized type validation in `global_id_for`):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/testing/relay.py`][testing-relay] ([`global_id_for`][testing-relay]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Re-implementing GlobalID decoding in `testing/relay.py`:**
   - Disproved per [spec-043][spec-043]. Re-exporting `types/relay.py::decode_global_id` ensures uniform parsing behavior.
2. **Duplicating typename encoding logic for test minting:**
   - Disproved per [spec-043][spec-043]. Calling `encode_typename` guarantees that test-minted IDs match schema-emitted IDs.

## Opportunities

None — `django_strawberry_framework/testing/relay.py` is fully consolidated with `django_strawberry_framework/types/relay.py`.

## Judgment

Verified. `testing/relay.py` exhibits zero duplicate code and complete policy consolidation through shared Relay encoding/decoding infrastructure. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/testing/relay.py --review docs/dry/dry-file-testing__relay.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/testing/relay.py`][testing-relay] and Worker 1's DRY review.

1. **Relay Helpers Architecture & Type Integration:**
   - Confirmed `global_id_for` enforces registration, finalization, and string-strategy constraints before delegating to `encode_typename`.
   - Confirmed `decode_global_id` is a direct re-export of `types/relay.py::decode_global_id`.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/testing/relay.py --review docs/dry/dry-file-testing__relay.md --include-constants`. 100% coverage across all target definitions.

Confirmed: `django_strawberry_framework/testing/relay.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md
[spec-043]: ../SPECS/spec-043-test_client-0_0_12.md

<!-- package source -->
[registry]: ../../django_strawberry_framework/registry.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-relay]: ../../django_strawberry_framework/types/relay.py

<!-- tests -->
[tests-testing-relay]: ../../tests/testing/test_relay.py
