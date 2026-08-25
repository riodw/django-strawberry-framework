# DRY review: `django_strawberry_framework/utils/permissions.py`

Status: verified

## System trace

`django_strawberry_framework/utils/permissions.py` implements the centralized permission traversal and Django/Channels request-context decoding engine ([spec-027][spec-027], [spec-028][spec-028], [spec-041][spec-041], [spec-051][spec-051]).

It owns the following architectural responsibilities:

1. **Context & Channels Request Resolution:**
   - Constants: [`_GATE_ASYNC_RECOURSE`][utils-permissions].
   - Permission method name formatter: [`_check_method_name`][utils-permissions] (`django_strawberry_framework/utils/permissions.py::_check_method_name`).
   - Channels adapter: [`ChannelsRequestAdapter`][utils-permissions] (`django_strawberry_framework/utils/permissions.py::ChannelsRequestAdapter` with `django_strawberry_framework/utils/permissions.py::ChannelsRequestAdapter.__init__`, `django_strawberry_framework/utils/permissions.py::ChannelsRequestAdapter.scope`, `django_strawberry_framework/utils/permissions.py::ChannelsRequestAdapter._scope_value`, `django_strawberry_framework/utils/permissions.py::ChannelsRequestAdapter.user`, `django_strawberry_framework/utils/permissions.py::ChannelsRequestAdapter.session`, `django_strawberry_framework/utils/permissions.py::ChannelsRequestAdapter.__getattr__`).
   - Scope & context resolvers: [`_channels_scope`][utils-permissions], [`_channels_request_adapter`][utils-permissions], [`_request_from_context`][utils-permissions], and [`request_from_info`][utils-permissions].

2. **Database Auth Routing & Safe Model Lookups:**
   - Model resolution: [`_safe_get_model`][utils-permissions] (`django_strawberry_framework/utils/permissions.py::_safe_get_model`).
   - Database auth alias resolution: [`resolve_auth_aliases`][utils-permissions] (`django_strawberry_framework/utils/permissions.py::resolve_auth_aliases`) and [`auth_aliases_for_permission_classes`][utils-permissions] (`django_strawberry_framework/utils/permissions.py::auth_aliases_for_permission_classes`).

3. **Active Target Walkers & Branch Extraction:**
   - Branch value extraction: [`extract_branch_value`][utils-permissions] (`django_strawberry_framework/utils/permissions.py::extract_branch_value`).
   - Permission method invoker: [`invoke_permission_method`][utils-permissions] (`django_strawberry_framework/utils/permissions.py::invoke_permission_method`).
   - Identity path mapper: [`verbatim_path`][utils-permissions] (`django_strawberry_framework/utils/permissions.py::verbatim_path`).
   - Target partitioner & walkers: [`active_permission_targets`][utils-permissions] (`django_strawberry_framework/utils/permissions.py::active_permission_targets`), [`active_related_branches`][utils-permissions] (`django_strawberry_framework/utils/permissions.py::active_related_branches`), and [`active_permission_field_paths`][utils-permissions] (`django_strawberry_framework/utils/permissions.py::active_permission_field_paths`).

4. **Gate Execution & Flat-Path Traversal:**
   - Gate invokers: [`_fire_gate_on_class`][utils-permissions] and [`_fire_flat_relation_path_gates`][utils-permissions].
   - Related declaration reader: [`_related_declarations`][utils-permissions] (`django_strawberry_framework/utils/permissions.py::_related_declarations`).
   - Active input permission runner: [`run_active_input_permission_checks`][utils-permissions] (`django_strawberry_framework/utils/permissions.py::run_active_input_permission_checks`).

Connected behavior examined:
- [`django_strawberry_framework/filters/sets.py`][filters-sets]: FilterSet permission execution via `run_active_input_permission_checks`.
- [`django_strawberry_framework/orders/sets.py`][orders-sets]: OrderSet permission execution via `run_active_input_permission_checks`.
- [`django_strawberry_framework/mutations/permissions.py`][mutations-permissions]: Mutation permission resolution and auth alias routing.
- [`tests/utils/`][tests-utils]: Test coverage for permission and context utilities.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/permissions.py --include-constants`):
- Parsed 1 target file, 778 lines.
- Complete inventory across all 24 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/permissions.py` unifies active-input permission traversal across FilterSets and OrderSets:
   - `run_active_input_permission_checks` enforces identical per-class firing dedup, parent-branch authorization, and child-set recursion.
   - `_fire_flat_relation_path_gates` eliminates authorization bypasses between nested syntax and flat ORM path syntax (`category__name`).
   - `request_from_info` provides a single authoritative entry point for unwrapping Django HTTP requests and Channels ASGI scope contexts across queries, subscriptions, and mutations.
   - `auth_aliases_for_permission_classes` ensures multi-db auth queries are consistently routed without leaking write-alias locks.

2. **Sync and async twins:**
   Permission checking is synchronous; `reject_async_in_sync_context` guards against accidental async method declaration.

3. **Derived rather than repeated knowledge:**
   `active_permission_targets` extracts active leaf paths and related branches in a single pass over `iter_active_fields`.

4. **Inverse and round-trip pairs:**
   `ChannelsRequestAdapter` adapts ASGI connection scopes; `request_from_info` resolves standard request handles.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/permissions.py`][utils-permissions], [`django_strawberry_framework/filters/sets.py`][filters-sets], [`django_strawberry_framework/orders/sets.py`][orders-sets], [`django_strawberry_framework/mutations/permissions.py`][mutations-permissions];
   - Specifications: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027], [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028], [`docs/SPECS/spec-041-channels_subscriptions-0_0_13.md`][spec-041], [`docs/SPECS/spec-051-finalizer_sidecar_dry-0_0_14.md`][spec-051];
   - Test suites: [`tests/utils/`][tests-utils], [`tests/filters/`][tests-filters], [`tests/orders/`][tests-orders];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Altering request extraction from GraphQL context across HTTP and Channels):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/permissions.py`][utils-permissions] ([`request_from_info`][utils-permissions] / [`_request_from_context`][utils-permissions]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying the flat relation traversal gate resolution or longest-match hop consumption):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/permissions.py`][utils-permissions] ([`_fire_flat_relation_path_gates`][utils-permissions]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Updating the recursion depth limit or error message for self-referential relations):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/input_values.py`][utils-input-values] ([`DEFAULT_SET_INPUT_TRAVERSAL_DEPTH`][utils-input-values]) and [`django_strawberry_framework/utils/permissions.py`][utils-permissions] ([`run_active_input_permission_checks`][utils-permissions]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Inlining permission recursion loops in `FilterSet` and `OrderSet`:**
   - Disproved per [spec-051][spec-051]. Inlined loops allow flat relation path bypasses or async gate swallow bugs to creep into one side.

## Opportunities

None — `django_strawberry_framework/utils/permissions.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/permissions.py` exhibits zero duplicate code and complete policy consolidation across permission traversal, gate execution, and context decoding. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/permissions.py --review docs/dry/dry-file-utils__permissions.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/permissions.py`][utils-permissions] and Worker 1's DRY review.

1. **Permission Execution & Authorization Parity:**
   - Confirmed `run_active_input_permission_checks` correctly dedupes method firing per class using the shared `fired` dictionary.
   - Confirmed `_fire_flat_relation_path_gates` prevents unauthorized access via flattened lookup paths.
   - Confirmed `request_from_info` and `ChannelsRequestAdapter` safely resolve request and ASGI contexts.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/permissions.py --review docs/dry/dry-file-utils__permissions.md --include-constants`. 100% coverage across all 24 definitions / constants.

Confirmed: `django_strawberry_framework/utils/permissions.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-027]: ../SPECS/spec-027-filters-0_0_8.md
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-041]: ../SPECS/spec-041-channels_subscriptions-0_0_13.md
[spec-051]: ../SPECS/spec-051-finalizer_sidecar_dry-0_0_14.md

<!-- package source -->
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[utils-input-values]: ../../django_strawberry_framework/utils/input_values.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py

<!-- tests -->
[tests-filters]: ../../tests/filters/
[tests-orders]: ../../tests/orders/
[tests-utils]: ../../tests/utils/

