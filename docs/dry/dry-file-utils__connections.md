# DRY review: `django_strawberry_framework/utils/connections.py`

Status: verified

## System trace

`django_strawberry_framework/utils/connections.py` implements the centralized connection contracts shared between the optimizer planner (`optimizer/walker.py`, `optimizer/nested_planner.py`, `optimizer/lateral_fetch.py`) and the Relay connection resolvers (`connection.py`) ([spec-032][spec-032], [spec-033][spec-033], [spec-035][spec-035]).

It owns the following architectural responsibilities:

1. **Connection Sidecar Kwargs & Predicates:**
   - Kwarg constants: [`CONNECTION_FILTER_KWARG`][utils-connections], [`CONNECTION_ORDER_KWARG`][utils-connections], [`CONNECTION_ORDER_KWARG_GRAPHQL`][utils-connections], and [`CONNECTION_SIDECAR_KWARGS`][utils-connections].
   - Sidecar detectors: [`connection_sidecar_inputs_from_kwargs`][utils-connections], [`has_connection_sidecar_input`][utils-connections], and [`has_connection_sidecar_kwargs`][utils-connections].

2. **Window Planning, Fetch Modes & Sentinel Rows:**
   - Exception sentinel: [`UnwindowableConnection`][utils-connections] (`django_strawberry_framework/utils/connections.py::UnwindowableConnection`).
   - Fetch mode policy: [`FetchMode`][utils-connections] (`django_strawberry_framework/utils/connections.py::FetchMode` with members `FetchMode.COUNTED`, `FetchMode.PROBED`, `FetchMode.CONSTANT_FALSE`, `FetchMode.NONE`).
   - Shape & ambiguity predicates: [`_is_probe_shape`][utils-connections] and [`is_ambiguous_empty_window`][utils-connections].
   - Range plan dataclass: [`WindowRangePlan`][utils-connections] (`django_strawberry_framework/utils/connections.py::WindowRangePlan` with attributes `offset`, `limit`, `reverse`, `lower_bound`, `upper_bound`, `add_marker_rows`, `plain_first_page`, `next_page_probe`, `_probe_increment`, [`WindowRangePlan.fetch_upper_bound`][utils-connections], [`WindowRangePlan.fetch_limit`][utils-connections], [`WindowRangePlan.probe_shape`][utils-connections], [`WindowRangePlan.constant_false_shape`][utils-connections], and method [`WindowRangePlan.fetch_mode`][utils-connections]).
   - Range plan resolver & validation: [`window_range_plan`][utils-connections] (`django_strawberry_framework/utils/connections.py::window_range_plan`), [`assert_window_fetch_mode`][utils-connections] (`django_strawberry_framework/utils/connections.py::assert_window_fetch_mode`), and [`assert_window_fetch_mode_for`][utils-connections] (`django_strawberry_framework/utils/connections.py::assert_window_fetch_mode_for`).
   - Row splitter: [`split_window_rows`][utils-connections] (`django_strawberry_framework/utils/connections.py::split_window_rows`).

3. **Bounds Derivation & Keyset Windows:**
   - Bounds dataclass: [`ConnectionWindowBounds`][utils-connections] (`django_strawberry_framework/utils/connections.py::ConnectionWindowBounds` with attributes `offset`, `limit`, `reverse`).
   - Offset bounds derivation: [`derive_connection_window_bounds`][utils-connections] (`django_strawberry_framework/utils/connections.py::derive_connection_window_bounds`).
   - Keyset bounds & caps: [`_RELAY_MAX_RESULTS_DEFAULT`][utils-connections], [`assert_relay_pagination_bound`][utils-connections], [`resolve_relay_max_results`][utils-connections], and [`derive_keyset_window_bounds`][utils-connections].

Connected behavior examined:
- [`django_strawberry_framework/connection.py`][connection]: Runtime Relay connection resolution and sentinel row consumption.
- [`django_strawberry_framework/optimizer/`][optimizer]: Window prefetch planning, lateral SQL compilation, and fallback management.
- [`django_strawberry_framework/resource_policy.py`][resource-policy]: Request page size ceilings.
- [`tests/utils/`][tests-utils]: Test coverage for connection utilities.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/connections.py --include-constants`):
- Parsed 1 target file, 745 lines.
- Complete inventory across all 23 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/connections.py` unifies connection window planning and resolution rules so plan-time and resolve-time contracts never drift:
   - Sidecar arguments are extracted from both Python kwargs (`order_by`) and GraphQL arguments (`orderBy`).
   - Fetch modes (`COUNTED`, `PROBED`, `CONSTANT_FALSE`, `NONE`) and range plans enforce probe-vs-count mutual exclusion (`assert_window_fetch_mode`).
   - Offset and keyset window derivations enforce identical error text and fallback sentinels (`UnwindowableConnection`).

2. **Sync and async twins:**
   Window arithmetic and row splitting are pure CPU algorithms shared across sync and async executors.

3. **Derived rather than repeated knowledge:**
   Resource policy ceilings and Relay max results are combined via `resolve_relay_max_results` and `effective_bound`.

4. **Inverse and round-trip pairs:**
   `window_range_plan` configures marker and probe rows; `split_window_rows` strips them from query results and derives `hasNextPage`.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/connections.py`][utils-connections], [`django_strawberry_framework/connection.py`][connection], [`django_strawberry_framework/optimizer/`][optimizer], [`django_strawberry_framework/resource_policy.py`][resource-policy];
   - Specifications: [`docs/SPECS/spec-032-full_relay-0_0_9.md`][spec-032], [`docs/SPECS/spec-033-relation_connections-0_0_10.md`][spec-033], [`docs/SPECS/spec-035-optimizer_hardened_diffing-0_0_10.md`][spec-035];
   - Test suites: [`tests/utils/`][tests-utils], [`tests/optimizer/`][tests-optimizer], [`tests/relay/`][tests-relay];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new connection sidecar argument like `search`):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/connections.py`][utils-connections] ([`CONNECTION_SIDECAR_KWARGS`][utils-connections] / [`connection_sidecar_inputs_from_kwargs`][utils-connections]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Altering the n+1 probe overfetch increment or shape classification):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/connections.py`][utils-connections] ([`WindowRangePlan._probe_increment`][utils-connections] / [`_is_probe_shape`][utils-connections]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Modifying the fallback signal on inverted or unwindowable cursor intervals):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/connections.py`][utils-connections] ([`derive_connection_window_bounds`][utils-connections] / [`UnwindowableConnection`][utils-connections]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Separating connection window derivation between planner and resolver:**
   - Disproved per [spec-033][spec-033]. A single shared derivation in `utils/connections.py` guarantees the cursor-parity invariant holds across all query shapes.
2. **Duplicating keyset Relay bound assertions:**
   - Disproved. Centralized in `assert_relay_pagination_bound` so keyset and offset pagination errors share identical validation text.

## Opportunities

None — `django_strawberry_framework/utils/connections.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/connections.py` exhibits zero duplicate code and complete policy consolidation across connection pagination bounds, sidecars, fetch modes, and window row splitting. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/connections.py --review docs/dry/dry-file-utils__connections.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/connections.py`][utils-connections] and Worker 1's DRY review.

1. **Window Arithmetic & Mutual Exclusion Contracts:**
   - Confirmed `WindowRangePlan`, `window_range_plan`, and `assert_window_fetch_mode` strictly enforce probe-vs-count mutual exclusion without redundant derivations.
   - Confirmed `split_window_rows` handles the composed offset page (markers + probes) cleanly and correctly.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/connections.py --review docs/dry/dry-file-utils__connections.md --include-constants`. 100% coverage across all 23 definitions / constants.

Confirmed: `django_strawberry_framework/utils/connections.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md
[spec-033]: ../SPECS/spec-033-relation_connections-0_0_10.md
[spec-035]: ../SPECS/spec-035-optimizer_hardened_diffing-0_0_10.md

<!-- package source -->
[connection]: ../../django_strawberry_framework/connection.py
[optimizer]: ../../django_strawberry_framework/optimizer/
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[utils-connections]: ../../django_strawberry_framework/utils/connections.py

<!-- tests -->
[tests-optimizer]: ../../tests/optimizer/
[tests-relay]: ../../tests/relay/
[tests-utils]: ../../tests/utils/
