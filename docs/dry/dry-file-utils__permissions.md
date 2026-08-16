# DRY review: `django_strawberry_framework/utils/permissions.py`

Status: verified

## System trace

This module owns two neutral contracts that both FilterSet and OrderSet (and
several write/auth surfaces) must share without importing each other:

1. **Active-input permission traversal** — resolve request → walk only supplied
   fields → dedupe `check_<field>_permission` by class → recurse active related
   branches → fire child gates and parent branch gates → fire the flat
   relation-traversal twin chain (`_fire_flat_relation_path_gates`) so a flat
   leaf cannot bypass a nested target gate.
2. **Django / Channels request-context decoding** — `request_from_info` +
   `ChannelsRequestAdapter` (HTTP `consumer.scope` and WebSocket `scope`
   shapes) so every authorization seam reads one actor source.
3. **Write-pipeline auth-alias allowlist** — `resolve_auth_aliases` /
   `auth_aliases_for_permission_classes` (router `db_for_read` for the auth
   models, gated on non-empty `permission_classes`).

Family-specific shape stays at the call sites as configuration:
`unset_sentinel` (filter `UNSET` vs order `None`), `handle_top_level_list`
(order), `related_attr` / `target_attr`, and FilterSet-only logical
`and` / `or` / `not` recursion wrapping `run_active_input_permission_checks`.

Connected surfaces examined:

- `filters/sets.py` / `orders/sets.py` — thin family wrappers
  (`_request_from_info`, `_active_permission_targets`,
  `_invoke_permission_method`, `_run_permission_checks`) pinning family config
  then calling this module.
- `utils/input_values.py` — traversal substrate
  (`iter_active_fields` / `is_inactive_value` / `input_field_value`); this
  module partitions `LEAF`/`RELATED` and re-exports `iter_input_items` for
  import compatibility.
- `mutations/permissions.py` — write-auth `has_permission` /
  `DjangoModelPermission`; reuses `request_from_info`, owns its own async-bool
  recourse (`_PERMISSION_ASYNC_RECOURSE`).
- Root `permissions.py` — cascade visibility (`apply_cascade_permissions`);
  different question ("may see") from input gates / write auth.
- `auth/mutations.py` / `auth/queries.py` / `auth/sessions.py` —
  `request_from_info` consumers; `_authenticated_actor_or_none`; sessions
  classifies via `isinstance(..., ChannelsRequestAdapter)`.
- `consumers.py` — WebSocket revalidation; deliberately re-spells the
  authenticated predicate to avoid importing `auth`.
- `forms/resolvers.py` / `mutations/resolvers.py` /
  `rest_framework/resolvers.py` — `auth_aliases_for_permission_classes` /
  `request_from_info`.
- `tests/utils/test_permissions.py` — direct pins for decoding, fire/dedup,
  flat-path gates, recursion cap, auth-alias gating.

Item-scoped baseline
`350fcbd9a59b4ea8d55a329419745b5557c7147d` vs working tree for
`django_strawberry_framework/utils/permissions.py`: empty (661 lines,
unchanged).

## Verification

Searches:

- Callers of `request_from_info`, `run_active_input_permission_checks`,
  `active_permission_*`, `invoke_permission_method`, `ChannelsRequestAdapter`,
  `resolve_auth_aliases` — every production site routes through this module
  (or a one-line family/auth wrapper that only pins `family_label` / config).
- Leftover inline permission walks (`check_*_permission` dispatch,
  `object.__new__` gate fire, related-branch permission recursion) — only
  FilterSet / OrderSet prologues + this module's core remain; no second walk
  body.
- Request decoding (`info.context.request`, Channels scope sniff) — sole
  production decoder is here; `rest_framework/resolvers.py` only compares a
  consumer override against the already-resolved request; `auth/sessions.py`
  consumes the adapter type, does not re-decode.
- Authenticated-actor predicates — two sites only (see rejected candidates).
- Auth-model alias discovery — sole-sited in `resolve_auth_aliases`.

No scratch experiment required: ownership is readable from the call graph and
the thin-wrapper bodies.

### Strongest rejected candidates

1. **Promote consumers' authenticated predicate into this module** (beside
   `ChannelsRequestAdapter`), consolidating with
   `auth/mutations.py::_authenticated_actor_or_none`.
   - Sites differ in input shape (`scope["user"]` vs `request.user`) and
     package boundary: consumers intentionally avoids importing `auth` (would
     pull the Strawberry type stack into the transport layer). The predicate
     itself is a trivial `is_authenticated` check; a shared helper would
     couple transport to auth without collapsing a second non-trivial body.
   - Still only two sites; the consumers comment correctly defers promotion
     until a third consumer appears. Leave as-is.

2. **Unify `_GATE_ASYNC_RECOURSE` with
   `mutations/permissions.py::_PERMISSION_ASYNC_RECOURSE`.**
   - Same *class* of bug (async auth hook → truthy coroutine → silent allow),
     but different contracts: filter/order gates are fire-and-forget through
     `reject_async_in_sync_context`; write auth additionally requires a
     sync `bool` via `_require_sync_bool_auth_result`. Recourse text names
     different methods (`check_<field>_permission` vs
     `has_permission` / `check_permission` / `has_perm`). Sharing a string
     would couple unrelated surfaces for no second implementation.

3. **Collapse FilterSet / OrderSet thin permission wrappers** into direct
   calls at every apply site.
   - Wrappers pin family config (`related_filters` vs `related_orders`,
     `UNSET` vs list aggregation, logic recursion only on filter) and are the
     names family tests and docs address. Removing them churns call sites
     without deleting a second walk body — the body already lives here.

4. **Move `resolve_auth_aliases` into `mutations/permissions.py`** (or
   `write_transaction.py`) as "more write-flavored."
   - Already single-sited. Forms, model mutations, and serializer mutations
     all import the neutral utils helper without a cycle. Relocating is
     ownership aesthetics, not DRY.

5. **Absorb `extract_branch_value` / permission walkers into
   `utils/input_values.py`.**
   - Traversal classification is already owned by `input_values`; this module
     owns permission *dispatch* (dedup, double-dispatch, flat-path twin,
     depth cap). `extract_branch_value` is a one-line composition used by
     permission and nested-visibility scoping — moving it does not eliminate
     a duplicate.

6. **Share FilterSet logical-branch permission recursion with OrderSet.**
   - OrderSet has no operator-bag (spec-028). Correctly stays filter-only
     around the shared related/leaf core.

## Opportunities

None — the historical FilterSet / OrderSet permission-walk fork is already
collapsed here; request decoding and auth-alias resolution have one production
owner each. Remaining near-misses are intentional boundary copies or thin
family/config delegates, not second implementations of the same rule.

## Judgment

Proved zero-edit. `utils/permissions.py` is the single source of truth for
active-input permission mechanics and Django/Channels request decoding.
Family wrappers, write-auth (`mutations/permissions.py`), cascade visibility
(root `permissions.py`), and the consumers/auth authenticated-actor split
correctly keep distinct contracts. Ready for Worker 2.

Deferred findings (not blocking; not production consolidations):

- `FilterSet._iter_input_items` docstring still attributes ownership to
  `utils/permissions.py::iter_input_items`; true owner is
  `utils/input_values.py` (this module only re-exports for import
  compatibility). Same stale-doc class noted on the input_values item.
- Authenticated-actor predicate: revisit promotion into this module only if a
  third production site appears.
- Pytest for this item: deferred until maintainer authorizes the cycle gate
  (`tests/utils/test_permissions.py` already covers the shared surface;
  family suites cover deep dedup / logic / list behavior).

Item-scoped diff vs `350fcbd9a59b4ea8d55a329419745b5557c7147d`: empty for
`django_strawberry_framework/utils/permissions.py`; this artifact only
(`docs/dry/dry-file-utils__permissions.md`).

## Independent verification (Worker 2)

Re-traced present-day `utils/permissions.py` plus FilterSet / OrderSet wrappers,
`mutations/permissions.py`, `auth/mutations.py::_authenticated_actor_or_none`,
`consumers.py` WebSocket revalidation, `auth/sessions.py` adapter classification,
write-resolver `auth_aliases_for_permission_classes` sites, root
`permissions.py` cascade visibility, and `rest_framework/resolvers.py` request
override check. Item-scoped diff vs
`350fcbd9a59b4ea8d55a329419745b5557c7147d` is empty (661 lines unchanged).

Challenges to rejected candidates (source evidence):

1. **Authenticated predicate promotion** — Confirmed only two production sites:
   `auth/mutations.py::_authenticated_actor_or_none` (`request.user` +
   `is_authenticated`) and `consumers.py` revalidation (`scope["user"]` +
   `is_authenticated`, with an explicit comment that importing `auth` would pull
   the Strawberry type stack into transport). Post-refresh
   `refreshed.is_authenticated` in the same consumer path is not a third ownership
   site. Trivial predicate + intentional package boundary — reject stands.

2. **`_GATE_ASYNC_RECOURSE` vs `_PERMISSION_ASYNC_RECOURSE`** — Same bypass
   class (truthy orphaned coroutine), different contracts: filter/order gates
   fire-and-forget through `reject_async_in_sync_context` alone; write auth adds
   `_require_sync_bool_auth_result` and names `has_permission` /
   `check_permission` / `has_perm`. Sharing the string would couple unrelated
   surfaces — reject stands.

3. **Collapse FilterSet / OrderSet thin wrappers** — Both
   `_run_permission_checks` bodies are prologues + one call into
   `run_active_input_permission_checks`; family config
   (`related_filters`/`related_orders`, `UNSET` vs list aggregation, filter-only
   `and`/`or`/`not`) stays at the wrappers. No second walk body — reject stands.

Independent leftover-walk search (`object.__new__` gate fire, `_fired` maps,
`check_*_permission` dispatch, Channels scope sniff, `resolve_auth_aliases`):
walk/dispatch/dedup/flat-path twin live only here; family sites are thin
delegates; request decoding sole-sited here; auth-alias sole-sited here;
cascade visibility is a different question ("may see").

Deferred items confirmed non-blocking: stale
`FilterSet._iter_input_items` ownership docstring (true owner
`utils/input_values.py`; this module re-exports); authenticated-predicate
promotion only if a third site appears.

**Verdict: verified** — zero-edit claim holds; no consolidation opportunity
found; plan checkbox may close.
