# DRY review: `django_strawberry_framework/mutations/permissions.py`

Status: verified

Iteration 2026-07-16: independently re-verified after the strict sync-bool
authorization contract and permission-class/auth-alias gate were centralized.

## System trace

`mutations/permissions.py` owns **write authorization** — a first-class contract
separate from row visibility (`permissions.py::apply_cascade_permissions` /
`get_queryset`):

1. **`_OPERATION_PERMISSION_ACTION`** — the single `create→add` / `update→change` /
   `delete→delete` map (spec-036 Decision 15).
2. **`run_permission_classes`** — the shared `Meta.permission_classes` loop behind
   both write-flavor `check_permission` defaults (`DjangoMutation` and
   model-less `DjangoFormMutation`).
3. **`DjangoModelPermission`** — default model-perm class; resolves the request via
   `utils/permissions.py::request_from_info`, the model via
   `mutation._resolve_model`, then `user.has_perm(<app>.<action>_<model>)`.
4. **`DenyAll`** — model-less plain-form unset default (spec-038 Decision 11);
   internal, not in `__all__`.
5. **`_require_sync_bool_auth_result`** (this pass) — the ONE sync-bool result
   contract for `has_permission` / `check_permission` / `user.has_perm`
   (async reject + BETA-055 non-bool reject).

Connected behavior examined:

- **Resolver gate:** `mutations/resolvers.py::authorize_or_raise` maps a `False`
  to a top-level `GraphQLError`; now consumes `_require_sync_bool_auth_result`
  instead of re-stating the reject-async + bool rule.
- **Defaults / validation:** `mutations/sets.py` and `forms/sets.py` install
  `[DjangoModelPermission]` / `[DenyAll]` and both `check_permission` bodies
  call `run_permission_classes` (already consolidated, DRY A5).
- **Request decode:** `utils/permissions.py::request_from_info` (shared with
  filter/order); `resolve_auth_aliases` is the write-pipeline auth-alias allowlist
  (resolvers), not actor classification.
- **Auth actor helper:** `auth/mutations.py::_authenticated_actor_or_none` answers
  "who is the session actor?" for `current_user` / `logout.ok` — not "may this
  user write?".
- **Root `permissions.py`:** cascade visibility only; no write-auth code path.
- **Tests / live:** `tests/mutations/test_permissions.py` (class + enforcement),
  `tests/mutations/test_write_transaction.py` (strict-bool / async bypass),
  `examples/fakeshop/test_query/test_products_api.py` and siblings (live
  `DjangoModelPermission` / `DenyAll` over `/graphql`).

Baseline `git diff e5b776f6c1f418c0dea8cf01ea182f39605e9e35 --
django_strawberry_framework/mutations/permissions.py` was empty before this pass.

## Verification

- Compared root `permissions.py` vs this module: visibility narrowing vs write
  allow/deny; different inputs, outputs, and change axes. No shared body.
- Compared `_PERMISSION_ASYNC_RECOURSE` vs
  `utils/permissions.py::_GATE_ASYNC_RECOURSE`: both reject async authorization
  hooks, but filter/order gates are side-effect/`PermissionDenied` methods that
  do **not** return a bool to the caller; write hooks must. Merging would force
  mode flags or wrong contracts onto one side.
- Compared `DjangoModelPermission` user extraction
  (`getattr(request, "user", None)` then `has_perm`) to
  `_authenticated_actor_or_none` (`user is not None and user.is_authenticated`).
  Auth classifies session anonymity for actor-returning fields; model permission
  asks Django's perm machinery. An authenticated user without the codename must
  still deny via `has_perm`, not via actor presence. **Rejected** merge.
- Compared the three copy-pasted reject-async + `isinstance(..., bool)` blocks in
  `run_permission_classes`, `DjangoModelPermission.has_permission`, and
  `authorize_or_raise`: same recourse string, same `context="mutation"`, same
  BETA-055 error template, same reason to change (authorization bypass).
  **Confirmed** one invariant.
- Operation-verb map vs Meta allow-list / resolver branch / field arg shape:
  same vocabulary, four responsibilities (fields artifact already rejected a
  shared OPERATIONS module). Map stays here; folder/project may inventory.
- Local test `DenyAll` / `_DenyAll` / `_AllowAll` doubles: intentional isolation,
  not production ownership drift.

No scratch under `docs/dry/temp-tests/`: import graph + contract comparison
sufficed. Permanent proof already lives in
`tests/mutations/test_write_transaction.py`
(`test_permission_class_returning_non_bool_is_a_configuration_error`,
`test_check_permission_override_returning_non_bool_is_a_configuration_error`,
`test_has_perm_returning_non_bool_is_a_configuration_error`) and live products
auth tests.

## Opportunities

### 1. Single sync-bool write-auth result guard

- **Repeated responsibility:** write-authorization hook results must be a sync
  `bool` — reject awaitables and never coerce truthiness (BETA-055).
- **Sites:** `run_permission_classes` (`has_permission`),
  `DjangoModelPermission.has_permission` (`user.has_perm`),
  `mutations/resolvers.py::authorize_or_raise` (`check_permission`).
- **Evidence:** identical recourse, context label, and error wording; a fix to
  one seam without the others reopens the silent-allow bypass class.
- **Owner:** `mutations/permissions.py` (write-auth module); resolvers already
  imported this module's private recourse string.
- **Consolidation:** add `_require_sync_bool_auth_result`; migrate all three
  sites; drop the now-unused `reject_async_in_sync_context` /
  `_PERMISSION_ASYNC_RECOURSE` imports from resolvers.
- **Proof:** existing permanent tests above; live
  `examples/fakeshop/test_query/` paths already exercise allow/deny through
  `authorize_or_raise` (no new earnable line for a pure extract).
- **Risks / non-goals:** do not fold filter/order `_GATE_ASYNC_RECOURSE` or
  visibility `get_queryset` into this helper; those surfaces do not share the
  bool-return contract.

## Judgment

One confirmed consolidation at the true owner. Strongest rejected candidates:
merging with cascade visibility, merging with the auth actor helper, merging
async-recourse text with filter/order gates, and inventing a package-wide
OPERATIONS table from this file alone. Ready for Worker 2.

## Implementation (Worker 1)

- **Owner:** `mutations/permissions.py::_require_sync_bool_auth_result`.
- **Migrated:** `run_permission_classes`, `DjangoModelPermission.has_permission`,
  `resolvers.py::authorize_or_raise` (import switched from
  `_PERMISSION_ASYNC_RECOURSE` + `reject_async_in_sync_context` to the helper).
- **Kept separate:** root cascade permissions; `request_from_info` /
  `resolve_auth_aliases`; auth `_authenticated_actor_or_none`; filter/order
  gate async recourse; `_OPERATION_PERMISSION_ACTION` as this module's private
  map; test-local allow/deny doubles.
- **Validation:** `uv run ruff format .` and `uv run ruff check --fix .` after
  edits. No full pytest (per assignment / AGENTS). Changelog: not warranted
  (internal extract; public contracts unchanged).

## Independent verification (Worker 2)

Re-traced independently from the item-scoped diff
(`e5b776f6c1f418c0dea8cf01ea182f39605e9e35` → working tree on
`mutations/permissions.py` + `mutations/resolvers.py`), the full target, and
connected callers — not from Worker 1's narration alone.

**Shared-contract challenge (three sites).** Confirmed one sync-bool
write-auth result contract across:

1. `run_permission_classes` → each `has_permission(...)` result
2. `DjangoModelPermission.has_permission` → `user.has_perm(...)` result
3. `resolvers.py::authorize_or_raise` → `check_permission(...)` result

All three previously ran the same pair: `reject_async_in_sync_context(...,
context="mutation", recourse=_PERMISSION_ASYNC_RECOURSE)` then
`isinstance(..., bool)` → `ConfigurationError` with the BETA-055 wording.
Same bypass class (truthy coroutine / truthy non-bool reads as allow), same
reason to change. Distinct hook *names* and owners; identical result
invariant. Challenge fails — consolidation warranted.

**Migration.** All three call sites now go through
`_require_sync_bool_auth_result`. Resolvers dropped
`reject_async_in_sync_context` and `_PERMISSION_ASYNC_RECOURSE` imports; sole
production `isinstance(..., bool)` + BETA-055 raise for write-auth lives in
the helper. Package-wide `rg` finds no leftover duplicate of that pair under
`mutations/`. Owner (`mutations/permissions.py`) is the write-auth module
resolvers already depended on — clearer than three copy-pasted guards.

**Rejected candidates (re-challenged; all stand):**

1. **Root `permissions.py` cascade visibility** — queryset narrowing /
   `apply_cascade_permissions`; no sync-bool allow/deny return to a write
   gate. Different inputs, outputs, change axis.
2. **`utils/permissions.py::invoke_permission_method` /
   `_GATE_ASYNC_RECOURSE`** — filter/order gates are side-effect methods
   (`None` return); only async-reject, no bool contract. Merging would force
   a mode flag or invent a bool return those gates do not own. Recourse text
   correctly stays separate (different surface wording).
3. **`auth/mutations.py::_authenticated_actor_or_none`** — session anonymity
   (`user is not None and user.is_authenticated`) for actor-returning fields;
   `DjangoModelPermission` still needs `has_perm` after user presence. An
   authenticated user without the codename must deny via perms, not actor
   presence.
4. **Package-wide OPERATIONS table from this file alone** — verb vocabulary
   shared with Meta/resolver/field shapes, but four responsibilities; map
   stays private here (fields artifact already rejected a shared module).

**Proof.** Permanent tests hit all three seams for both async and non-bool:

- `tests/mutations/test_permissions.py` —
  `test_async_has_permission_is_rejected_not_bypassed`,
  `test_awaitable_has_permission_is_rejected_not_bypassed`,
  `test_async_check_permission_override_is_rejected_not_bypassed`,
  plus awaitable `has_perm` coverage in the same file
- `tests/mutations/test_write_transaction.py` —
  `test_permission_class_returning_non_bool_is_a_configuration_error`,
  `test_check_permission_override_returning_non_bool_is_a_configuration_error`,
  `test_has_perm_returning_non_bool_is_a_configuration_error`

No fourth production implementation found. `DenyAll.has_permission` returns
literal `False` without the helper — correct (constant, not a hook result).
No unrelated work absorbed. No production edits this pass.

**Comment drift corrected:** `_PERMISSION_ASYNC_RECOURSE`'s comment previously
said "both enforcement seams"; it now names the single
`_require_sync_bool_auth_result` guard the three write-auth result seams share
(`has_permission` / `check_permission` / `user.has_perm`), matching the helper.

**Disposition:** verified. Plan item checked.
