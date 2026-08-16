# DRY review: folder `django_strawberry_framework/auth/`

Status: verified

## System trace

`auth/` is the opt-in session-auth component (spec-040 / transport hardening):
four modules that together own the four consumer factories, the private
transport/session boundary, the declaration ledger + phase-2.5 surface-keyed
bind, and the `CurrentUserAlias` emit namespace.

Present-day folder shape (fresh pass; `sessions.py` is first-class here and had
no plan file item):

- `__init__.py` — structural opt-in re-export of the four public factories only;
  package root never imports it; `sessions` is deliberately not re-exported.
- `sessions.py` (~253 lines, private) — transport classification
  (`Transport` / `classify_transport` / `require_channels`), missing-session
  pre-check (`require_session`), per-scope `asyncio.Lock`
  (`scope_session_lock`), and capability predicates (`login_supported` /
  `logout_supported` / `uses_signed_cookie_sessions`). Soft-`channels` import
  stays lazy. Engine resolution delegates to
  `utils/sessions.py::session_store_class` so `consumers` never imports `auth`.
- `mutations.py` (~1248 lines) — declaration ledger
  (`make_declaration_registry`), shared fixed-field hub
  (`_declare_*` / `_make_permission_holder` / `_make_auth_field` /
  `_sync_bridged_async_body` / `_authenticated_actor_or_none` /
  `_AUTH_FAMILY_LABEL`), login/logout state machines (prologue → native
  Django/Channels critical sections under the scope lock; Channels logout also
  takes `utils/sessions.py::actor_transition`), register rider
  (`derive_register_fields` + password decode/write step pair over
  `run_write_pipeline_sync`), and `bind_auth_mutations()` (finalizer phase 2.5
  via `loaded_attr(..., "bind_auth_mutations")`).
- `queries.py` — `current_user()` + `_current_user_resolve_body` + the
  `make_input_namespace` alias trio (`before_bind=True` clear). Imports the
  shared fixed-field helpers from `mutations.py`; bind reaches back with a
  function-local import to break the cycle. No session mutation / no
  `sessions` import (read-only actor field).

Connected behavior re-traced for this folder pass (not inherited as proven):
`types/finalizer.py` phase-2.5 slot; `utils/permissions.py::request_from_info`
+ `ChannelsRequestAdapter`; `utils/sessions.py` (engine + actor lease);
`mutations.resolvers` authorize/payload/write skeleton; `consumers.py`
comments that reference capability/lock without reimplementing them;
`examples/fakeshop/apps/accounts/schema.py` (four public factories);
`tests/auth/` (`test_mutations` / `test_queries` / `test_sessions`) and live
`examples/fakeshop/test_query/test_auth_api.py` as contract evidence.

Folder-level axes: duplicated policy across modules, state ownership
(declaration vs emit vs scope lock vs actor lease), competing helper layers,
public factory flavor consistency, lifecycle work repeated at several phases.

## Verification

- Item-scoped baseline `ac2aebd8579f2a584f5d63ebaba553febd9f5238`:
  `git diff ac2aebd… -- django_strawberry_framework/auth/` is empty (folder
  already contains `__init__.py` / `mutations.py` / `queries.py` /
  `sessions.py` at baseline). This pass edits only this artifact. Concurrent
  dirty paths outside the item left untouched. Plan checkbox not edited
  (Worker 2).
- Re-read all four auth sources end-to-end. Grepped package for
  `classify_transport` / `login_supported` / `logout_supported` /
  `scope_session_lock` / `uses_signed_cookie` / `_authenticated_actor_or_none`
  / `getattr(request, "user"` + `is_authenticated`. Transport/capability/
  lock bodies live only in `auth/sessions.py`; anonymity classification body
  lives only in `mutations.py::_authenticated_actor_or_none` (logout +
  `current_user` call it). `consumers.py` cites the auth symbols in comments
  and uses `utils/sessions` for engine/lease — no parallel auth policy.
- Confirmed the cross-boundary engine split: `session_store_class` stays in
  `utils/sessions.py` because importing `auth.sessions` would execute
  `auth/__init__.py` and register the whole opt-in subsystem on the first
  authenticated WebSocket revalidation (documented in both module docstrings).
- Confirmed lock order at the one dual-hold site
  (`_channels_logout`): scope session lock OUTER, actor lease INNER; no
  lease holder re-enters the auth layer.
- Public flavors: all four factories share
  `permission_classes` / `description` / `deprecation_reason` / `directives`;
  fixed fields share `_declare_fixed_auth_surface` + `_make_auth_field`;
  register alone rides `DjangoMutationField` (model write). Alias emit clears
  `before_bind=True`; declaration ledger clears full-`TypeRegistry.clear()`
  only.
- Tried hard to find a consolidation whose true owner is inside `auth/`;
  every candidate either already has a single owner, crosses the opt-in /
  transport boundary on purpose, or would need mode flags to reconcile
  distinct contracts (see Rejected).

## Opportunities

None — present-day folder ownership is already single-sited per
responsibility. `sessions.py` owns transport/session capability; `mutations.py`
owns declaration + fixed-field hub + session state machines + register rider +
bind; `queries.py` owns the read field + emit alias; `__init__.py` owns the
structural public surface. Prior cross-module anonymity duplication remains
consolidated at `_authenticated_actor_or_none`. No competing helper layer and
no unclear state ownership remain inside the folder.

### Rejected / kept separate (fresh pass)

- **Move `_authenticated_actor_or_none` into `sessions.py`.** Sessions owns
  transport classification and mutation capability, not GraphQL actor
  anonymity (spec-040 Decisions 5/7). `queries.py` already imports the
  fixed-field hub from `mutations.py`; moving the helper would expand the
  private transport module into field-contract policy.
- **Fold `_transport_prologue` into `sessions.py`.** Prologue is the
  login/logout state-machine opening (`request_from_info` under
  `_AUTH_FAMILY_LABEL` + capability messages owned by mutations). Sessions
  correctly answers classify / require_session / supported predicates only.
- **Unify Django vs Channels login-establish / logout compensate twins.**
  Parallel try/fail-closed shapes, different APIs (`auth.login` vs
  `channels.auth.login`, `session.save` vs `asave`, `request.user` vs
  `scope["user"]`) and different extra duties (Channels logout also takes
  `actor_transition`). Consolidation would need mode flags.
- **Abstract async login/logout transport routers.** Outer
  `classify_transport` is a pure event-loop routing predicate; prologue
  re-classifies inside the shared sync state machine. Asymmetric transport
  sets (login: WebSocket rejected → non-`CHANNELS_HTTP` ≡ Django; logout:
  server-side-engine WebSocket still reaches Channels teardown). Cheap
  re-classify is safer than threading a pre-classified transport through.
- **Unify `_CHANNELS_INSTALL_HINT` with `routers.py`.** Feature-keyed
  install hints by design (`utils/imports.py` owner pattern); router hint
  names the router, auth hint names the session boundary. Project-pass
  hygiene note at most, not an `auth/` ownership finding.
- **Share scope-lock get-or-create with `utils/sessions` actor-lease
  pattern.** Intentionally mirrored across the opt-in boundary; consumers
  must not import `auth`. Owner of the lease stays in `utils/sessions`.
- **Declaration ledger vs alias emit clear phases; fixed-field path vs
  register rider; auth vs mutations primary-resolution messages; public
  factory kwargs.** Distinct lifecycle roles / contracts; already
  single-sited per role. `MODULE_PATH` string literals remain a project-pass
  hygiene note.

## Judgment

The folder is a deliberately layered opt-in component: private
`sessions.py` for transport/session capability, `mutations.py` as the
declaration + state-machine hub, `queries.py` as the read/emit arm, and a
minimal public `__init__`. After the sessions extraction and the earlier
authenticated-actor helper, no folder-visible duplicated policy remains.
Zero production edit. Ready for Worker 2.

## Implementation (Worker 1)

- **Zero-edit.** No production paths changed.
- **Artifact only:** this file rewritten for present-day four-module source;
  prior verified pass preserved under Iterations.
- **Validation:** no `.py` edit → ruff not required. No pytest (not the gate;
  no new behavior).
- **Item-scoped diff statement:** against
  `ac2aebd8579f2a584f5d63ebaba553febd9f5238`, only
  `docs/dry/dry-folder-auth.md` changes for this item.
- **Changelog:** N/A (no code change).
- **Deferred pytest:** none owed (no production edit). Existing
  `tests/auth/` + live `test_auth_api.py` remain the standing proof of the
  folder contracts.

## Iterations

### Iteration 2026-07-16 (prior folder pass — three-module source; verified)

Status at close: verified. Source then: `__init__.py` / `mutations.py` /
`queries.py` only (`sessions.py` did not exist in that review's framing).

Accepted consolidation: `_authenticated_actor_or_none` extracted in
`mutations.py`; `_logout_resolve_body` and `_current_user_resolve_body`
migrated. Rejected: moving the helper to `utils/permissions.py`; unifying
with `DjangoModelPermission`; collapsing declaration vs emit clear phases;
fixed-field vs register; auth vs mutations primary resolution; public kwargs;
`MODULE_PATH` hygiene.

Worker 2 re-traced the three-module folder, confirmed the shared anonymity
contract and owner, corrected a live-test citation
(`test_anonymous_me_is_null_not_an_error`), and marked verified. Plan
checkbox was reported marked then; present plan still shows the folder item
open — this 2026-08-15 pass re-opens the integration against four-module
present-day source without seeding findings from that pass as truth.

### Iteration 2026-08-15 (Worker 1 — fresh four-module folder integration)

Re-traced present-day `auth/` including `sessions.py` (~253 lines) and the
grown `mutations.py` (~1248 lines). Confirmed transport/capability/lock
ownership in `sessions.py`, state machines + declaration + bind in
`mutations.py`, read/emit in `queries.py`, structural public surface in
`__init__.py`. Item-scoped auth/ diff vs baseline empty; artifact-only
update. Strongest rejected candidates listed above. Status →
`fix-implemented` for Worker 2; plan checkbox left for Worker 2.

## Independent verification (Worker 2)

Fresh four-module folder integration (2026-08-15). Outcome: **verified**.

### Scoped production diff

`git diff ac2aebd8579f2a584f5d63ebaba553febd9f5238 -- django_strawberry_framework/auth/`
is empty. Working tree: only `docs/dry/dry-folder-auth.md` dirty for this
item (plus this verification + plan checkbox). Line counts match the claim
(`sessions.py` 253, `mutations.py` 1248, `queries.py` 121, `__init__.py` 20).

### Independent re-trace

Re-read all four modules and the bind / consumer / utils edges end-to-end.

- **`__init__.py`**: re-exports only the four factories; `sessions` not public;
  package root does not import `auth` (structural opt-in).
- **`sessions.py`**: sole owner of `Transport` / `classify_transport` /
  `require_channels` / `require_session` / `scope_session_lock` /
  `login_supported` / `logout_supported` / `uses_signed_cookie_sessions`.
  Soft-`channels` import stays lazy; engine resolution delegates to
  `utils/sessions.py::session_store_class`.
- **`mutations.py`**: declaration ledger, fixed-field hub, login/logout state
  machines (prologue → Django/Channels critical sections), register rider,
  `bind_auth_mutations()` at finalizer phase 2.5. Imports `.sessions`;
  function-local import back into `.queries` only inside bind.
- **`queries.py`**: `current_user` + emit-alias trio (`before_bind=True`);
  imports fixed-field / anonymity helpers from `mutations`; no `sessions`
  import.

Import direction is one-way capability → state machines → read/emit, with
the single documented bind-time reverse edge. Lock order at the only
dual-hold site (`_channels_logout`) is scope session lock OUTER, actor lease
INNER.

### Challenged rejected candidates (source evidence)

- **Move `_authenticated_actor_or_none` into `sessions.py`.** Helper is
  GraphQL actor anonymity for logout `ok` + `current_user` nullable return
  (`mutations.py::_authenticated_actor_or_none`). Sessions answers transport /
  capability / lock only. Moving it would expand the private transport module
  into field-contract policy; `queries` already depends on the mutations hub.
  Keep separate. (Outside the folder, `consumers.py` deliberately re-spells the
  authenticated predicate rather than importing `auth` — opt-in boundary /
  project-pass hygiene, not an `auth/` consolidation.)
- **Fold `_transport_prologue` into `sessions.py`.** Prologue owns
  `request_from_info(..., family_label=_AUTH_FAMILY_LABEL)` plus the
  mutation-owned unsupported messages; sessions correctly exposes classify /
  require_session / supported predicates only. Keep separate.
- **Unify Django vs Channels login-establish / logout compensate twins.**
  Parallel try/fail-closed shapes, different APIs (`auth.login` /
  `channels.auth.login`, `session.save` / `asave`, `request.user` /
  `scope["user"]`); Channels logout alone wraps `actor_transition`. Mode
  flags would obscure ownership. Keep separate.
- **Abstract async login/logout transport routers.** Login async routes on
  `is not CHANNELS_HTTP` (Django + rejected WebSocket fall through to sync
  body); logout async routes on `is DJANGO_HTTP` else Channels (HTTP +
  server-side-engine WebSocket). Asymmetric by capability contract; cheap
  re-classify inside shared sync prologues is safer. Keep separate.
- **Unify `_CHANNELS_INSTALL_HINT` with `routers.py`.** Auth hint names the
  session boundary; router hint names `DjangoGraphQLProtocolRouter`; both use
  `require_optional_module` with feature-keyed strings. Project-pass hygiene
  at most. Keep separate.
- **Share scope-lock get-or-create with `utils/sessions` actor-lease pattern.**
  Mirrored lazy get-or-create is intentional across the opt-in boundary
  (`consumers` must not import `auth`). Lease owner stays in `utils/sessions`.
  Keep separate / defer.

### Deferred items

`MODULE_PATH` string literals (`AUTH_QUERIES_MODULE_PATH`,
`INPUTS_MODULE_PATH` lazy refs) and the mirrored lock / Channels-hint pairs
are correctly NOT this folder's remit — they cross package / feature owners
and belong on the project pass.

### Missed folder-level consolidations?

Independently searched for duplicated policy across the four modules,
competing helper layers, and lifecycle repeated at several phases. Within
`auth/`: anonymity is single-sited; transport/capability/lock is single-sited;
declaration clear (full-`TypeRegistry.clear` only) vs emit clear
(`before_bind=True`) remain distinct roles; fixed-field path vs register rider
remain distinct contracts; all four factories share the same public kwargs.
No folder-owned consolidation remains.

Plan checkbox for Folder integration `auth/` marked `[x]`. No production
edit. No commit.
