# DRY review: `django_strawberry_framework/types/relay.py`

Status: verified

## System trace

`django_strawberry_framework/types/relay.py` implements Relay Node interface injection, default node resolvers, and GlobalID encoding/decoding strategies ([spec-015][spec-015], [spec-031][spec-031], [spec-032][spec-032]).

It owns the following architectural responsibilities:

1. **Relay Node Identification & Interface Injection:**
   - [`SyncMisuseError`][types-relay] (`django_strawberry_framework/types/relay.py::SyncMisuseError`): Re-export of sync misuse exception from `utils/querysets.py`.
   - [`implements_relay_node`][types-relay] (`django_strawberry_framework/types/relay.py::implements_relay_node`): MRO-based check for `relay.Node` conformance.
   - [`_NODE_TYPE_HINT_ATTR`][types-relay] and [`install_is_type_of`][types-relay] (`django_strawberry_framework/types/relay.py::install_is_type_of`): Interface concrete-type discriminator.
   - [`apply_interfaces`][types-relay] (`django_strawberry_framework/types/relay.py::apply_interfaces`): Base class injection for `Meta.interfaces`.
   - [`_check_composite_pk_for_relay_node`][types-relay] (`django_strawberry_framework/types/relay.py::_check_composite_pk_for_relay_node`): Rejection of composite primary keys without single-column `NodeID`.

2. **Relay ID Attribute Pinning & Default Resolvers:**
   - [`_RELAY_ID_ATTR_SLOT`][types-relay] and [`_stamp_relay_id_attr`][types-relay] (`django_strawberry_framework/types/relay.py::_stamp_relay_id_attr`): One-time id attribute resolution and class pinning.
   - [`_resolve_id_attr_default`][types-relay] (`django_strawberry_framework/types/relay.py::_resolve_id_attr_default`): Dict-cached `resolve_id_attr` method default.
   - [`_resolve_id_default`][types-relay] (`django_strawberry_framework/types/relay.py::_resolve_id_default`): Primary key resolver reading instance `__dict__`.
   - [`_coerce_node_id`][types-relay], [`_coerce_node_ids`][types-relay], and [`_apply_node_filter`][types-relay] (`django_strawberry_framework/types/relay.py::_apply_node_filter`): Shared query filter constructor for sync and async resolvers.
   - [`_order_nodes`][types-relay] (`django_strawberry_framework/types/relay.py::_order_nodes`): Order-preserving result mapping.
   - Resolvers: [`_resolve_node_default`][types-relay], [`_resolve_node_async`][types-relay], [`_resolve_nodes_default`][types-relay], and [`_resolve_nodes_async`][types-relay].
   - Registry and installer: [`_RELAY_RESOLVER_DEFAULTS`][types-relay] and [`install_relay_node_resolvers`][types-relay] (`django_strawberry_framework/types/relay.py::install_relay_node_resolvers`).

3. **GlobalID Strategies & Codec Pipeline:**
   - Setting validation & precedence: [`_validated_globalid_setting`][types-relay] and [`_resolve_globalid_strategy`][types-relay].
   - Strategy memberships: [`MODEL_LABEL_STRATEGIES`][types-relay] and [`TYPE_NAME_STRATEGIES`][types-relay].
   - Strategy classifiers: [`_emits_model_label`][types-relay], [`_accepts_model_label_decode`][types-relay], and [`_accepts_type_name_decode`][types-relay].
   - Encoder: [`encode_typename`][types-relay] (`django_strawberry_framework/types/relay.py::encode_typename`).
   - Typing closure helpers: [`_FRAMEWORK_CLOSURE_MARKER`][types-relay], [`_inherits_framework_closure`][types-relay], [`_consumer_overrode_resolve_typename`][types-relay], [`install_globalid_typename_resolver`][types-relay], and [`_install_typename_closure`][types-relay].
   - Decoder: [`decode_global_id`][types-relay] (`django_strawberry_framework/types/relay.py::decode_global_id`).

Connected behavior examined:
- [`django_strawberry_framework/types/base.py`][types-base]: `Meta.globalid_strategy` validation and type initialization.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Phase 2.5 interface application and resolver installation.
- [`django_strawberry_framework/filters/base.py`][filters-base]: Strategy-aware GlobalID filtering using `TYPE_NAME_STRATEGIES`.
- [`tests/types/`][tests-types]: Test coverage for Relay node defaults and GlobalID operations.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/types/relay.py --include-constants`):
- Parsed 1 target file, 1017 lines.
- Complete inventory across all 34 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `types/relay.py` centralizes all Relay and GlobalID policies:
   - `MODEL_LABEL_STRATEGIES` and `TYPE_NAME_STRATEGIES` serve as the single sources of truth across encode, decode, filter validation, and finalization audits.
   - `_apply_node_filter` and `_order_nodes` are shared between single-node and multi-node resolver implementations across sync and async modes.
   - `_stamp_relay_id_attr` provides a single id-attribute resolution cache eliminating redundant MRO scans.

2. **Sync and async twins:**
   `_resolve_node_default` / `_resolve_node_async` and `_resolve_nodes_default` / `_resolve_nodes_async` share query filtering logic (`_apply_node_filter`) and result ordering (`_order_nodes`), delegating visibility checks to `apply_type_visibility_sync` / `apply_type_visibility_async`.

3. **Derived rather than repeated knowledge:**
   Relay conformance is derived via `implements_relay_node`. GlobalID type-name values are derived dynamically based on the resolved strategy.

4. **Inverse and round-trip pairs:**
   `encode_typename` and `decode_global_id` form an exact encoder/decoder pair across `model`, `type`, and `type+model` strategy representations.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/types/relay.py`][types-relay], [`django_strawberry_framework/types/base.py`][types-base], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/filters/base.py`][filters-base], [`django_strawberry_framework/registry.py`][registry];
   - Specifications: [`docs/SPECS/spec-015-interfaces_relay-0_0_5.md`][spec-015], [`docs/SPECS/spec-031-globalid_strategies-0_0_9.md`][spec-031], [`docs/SPECS/spec-032-full_relay-0_0_9.md`][spec-032];
   - Test suites: [`tests/types/`][tests-types];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new GlobalID encoding strategy):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/relay.py`][types-relay] ([`encode_typename`][types-relay] / [`MODEL_LABEL_STRATEGIES`][types-relay] / [`TYPE_NAME_STRATEGIES`][types-relay]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Adjusting the default node filtering logic for resolve_node / resolve_nodes):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/relay.py`][types-relay] ([`_apply_node_filter`][types-relay]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Modifying the Relay node resolver method default list):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/relay.py`][types-relay] ([`_RELAY_RESOLVER_DEFAULTS`][types-relay]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Splitting strategy sets across encoder, decoder, and filters:**
   - Disproved per [spec-031][spec-031]. Centralized `MODEL_LABEL_STRATEGIES` and `TYPE_NAME_STRATEGIES` guarantee consistent behavior across all subsystems.
2. **Duplicating query filtering across sync and async resolver twins:**
   - Disproved per [spec-015][spec-015]. Factoring into `_apply_node_filter` and `_order_nodes` eliminates query construction drift.

## Opportunities

None — `django_strawberry_framework/types/relay.py` is fully consolidated at root owners.

## Judgment

Verified. `types/relay.py` exhibits zero duplicate code and complete policy consolidation across Relay node resolver defaults, interface injection, and GlobalID encoding/decoding. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/types/relay.py --review docs/dry/dry-file-types__relay.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/types/relay.py`][types-relay] and Worker 1's DRY review.

1. **Relay Node & GlobalID Pipeline:**
   - Confirmed `MODEL_LABEL_STRATEGIES` and `TYPE_NAME_STRATEGIES` unify codec and filter policies.
   - Confirmed shared `_apply_node_filter` and `_order_nodes` prevent divergence between sync and async execution paths.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/types/relay.py --review docs/dry/dry-file-types__relay.md --include-constants`. 100% coverage across all 34 definitions / constants.

Confirmed: `django_strawberry_framework/types/relay.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-015]: ../SPECS/spec-015-interfaces_relay-0_0_5.md
[spec-031]: ../SPECS/spec-031-globalid_strategies-0_0_9.md
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md

<!-- package source -->
[filters-base]: ../../django_strawberry_framework/filters/base.py
[registry]: ../../django_strawberry_framework/registry.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-relay]: ../../django_strawberry_framework/types/relay.py

<!-- tests -->
[tests-types]: ../../tests/types/
