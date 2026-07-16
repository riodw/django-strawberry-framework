# DRY review: folder `django_strawberry_framework/auth/`

Status: verified

Iteration 2026-07-16: reopened after the canonical sync-boundary import
migration; the authenticated-actor helper extraction was re-verified against the
final source and the independent folder verification below is complete.

## System trace

`auth/` is the opt-in session-auth component (spec-040): three modules that
together own the four consumer factories (`login_mutation` / `logout_mutation` /
`register_mutation` / `current_user`), the declaration ledger + phase-2.5
surface-keyed bind, the fixed-field resolver bodies, the register rider's
password-aware decode/write pair, and the `CurrentUserAlias` emit namespace.

Folder shape after the three verified file reviews:

- `__init__.py` — structural opt-in re-export only; package root never imports it.
- `mutations.py` — declaration ledger (`make_declaration_registry`), shared fixed-
  field helpers (`_declare_fixed_auth_surface`, `_make_permission_holder`,
  `_make_auth_field`, `_resolve_auth_async`), session mutation bodies, register
  rider, `bind_auth_mutations()` (finalizer phase 2.5 via
  `loaded_attr(..., "bind_auth_mutations")`).
- `queries.py` — `current_user()` factory + `_current_user_resolve_body` + the
  `make_input_namespace` alias trio (`before_bind=True` clear). Imports the
  shared fixed-field helpers from `mutations.py` (sibling private import; the
  bind reaches back with a function-local import to break the cycle).

Connected behavior re-traced for this folder pass (not inherited as proven):
`types/finalizer.py` phase-2.5 slot; `utils/permissions.py::request_from_info`
(all four resolvers); `mutations.resolvers` authorize/payload/write skeleton;
`mutations/permissions.py::DjangoModelPermission` (near-miss `getattr(request,
"user", None)`); `examples/fakeshop/apps/accounts/schema.py` (the four public
factories); live `examples/fakeshop/test_query/test_auth_api.py`; package
`tests/auth/` residue (absent-`user`, gated-`me`, logout-without-auth-
middleware, surface-keyed bind arms).

Folder-level axes examined: duplicated policy across modules, state ownership
(declaration ledger vs alias emit ledger), competing helper layers, public
factory flavor consistency, lifecycle work repeated at several phases.

## Verification

- Item-scoped baseline `2d8baebe703feb86ac5d0940d4eb619bc38b6297`: auth/ was
  empty before this pass's edit; concurrent dirty paths
  (`docs/GLOSSARY.md`, `docs/dry/dry-0_0_13.md`, `docs/dry/dry-file-exceptions.md`,
  `examples/fakeshop/db.sqlite3`, untracked `docs/dry/dry-file-auth__queries.md`)
  left untouched. Plan checkbox not edited.
- Re-read all three auth sources end-to-end. Grepped the package for
  `getattr(request, "user", None)` and `is_authenticated`: exactly two
  production sites carried the full `getattr` + `is_authenticated` anonymity
  classification (`_logout_resolve_body`, `_current_user_resolve_body`).
  `DjangoModelPermission.has_permission` shares only the `getattr` None-guard
  before `has_perm` — a write-permission contract, not session-actor
  classification (different change axis; kept separate).
- Read the file-pass deferrals in `dry-file-auth__mutations.md` /
  `dry-file-auth__queries.md` as *flags only*; re-proved the 2-site idiom from
  source. Both sites encode the same anonymity rule (missing `.user` attr OR
  not `is_authenticated` → anonymous) and must change together under Channels
  adapter / middleware-absence / AnonymousUser edges; they only differ in
  return shape (`ok: bool` vs nullable actor).
- Rejected placing the helper in `utils/permissions.py`: that module owns
  request *resolution* and active-input permission walks for FilterSet /
  OrderSet / mutations; folding auth-session actor classification there would
  couple an opt-in auth policy into a always-loaded utility and tempt wrongly
  unifying `DjangoModelPermission`'s None-guard. Owner stays inside `auth/`, on
  the already-shared helper hub (`mutations.py`) that `queries.py` already
  imports.
- Other folder candidates examined and rejected (see below).

## Opportunities

### 1. Authenticated-actor anonymity classification (accepted)

- **Repeated responsibility:** classify a resolved request as "authenticated
  session actor or anonymous" under the auth surfaces' middleware-tolerant
  contract (`getattr(request, "user", None)` then `is_authenticated`).
- **Sites:** `auth/mutations.py::_logout_resolve_body` (`ok =
  actor is not None`); `auth/queries.py::_current_user_resolve_body` (return /
  gate `instance=actor`).
- **Evidence:** identical anonymity predicate; same Channels-adapter /
  bare-HttpRequest edges pinned by
  `tests/auth/test_mutations.py::test_logout_without_auth_middleware_is_anonymous_and_flushes_the_session`
  and
  `tests/auth/test_queries.py::test_me_is_null_not_a_crash_when_the_request_user_is_absent`;
  live round-trip coverage in
  `examples/fakeshop/test_query/test_auth_api.py::test_logout_round_trip_and_anonymous_logout`
  and `test_anonymous_me_is_null_not_an_error`. Drift between the two sites would
  make `logout.ok` disagree with `me` for the same request shape.
- **Owner:** `auth/mutations.py::_authenticated_actor_or_none` — the folder's
  shared private-helper module (already exports `_AUTH_FAMILY_LABEL`,
  `_declare_fixed_auth_surface`, `_make_auth_field` to `queries.py`).
- **Consolidation:** one helper returning the actor or `None`; logout reduces
  to `ok = helper(request) is not None`; `current_user` uses the actor
  directly. Implemented in this pass.
- **Proof:** existing permanent tests at both tiers already pin both call
  sites' public contracts (live `/graphql` anonymous logout + anonymous `me`;
  package tests for absent-`user` / no-auth-middleware). No new behavior; no
  new test required beyond those owners.
- **Risks / non-goals:** do not unify with `DjangoModelPermission`'s
  None-guard + `has_perm`; do not move into `utils/permissions.py`; do not
  change login (which never classifies a pre-existing actor for its return —
  it authenticates credentials).

### Rejected / kept separate

- **Declaration ledger vs alias emit ledger clear phases.** Declaration clears
  on full `TypeRegistry.clear()` only; alias clears `before_bind=True`. Distinct
  lifecycle roles (reload-surviving declarations vs emit artifacts drained
  before re-materialize). Intentional; already single-sited per ledger.
- **Fixed-field path (`_make_auth_field`) vs register rider (`DjangoMutationField`).**
  Register is a narrow create over `get_user_model()` that must ride the write
  skeleton; fixed fields are session/envelope work without a model write.
  Different contracts; already share declaration/conflict via
  `_declare_auth_surface`.
- **Auth-specific `_resolve_user_primary_or_raise` vs mutations'
  `_resolve_primary_type`.** Same `registry.get` lookup, deliberately different
  actionable messages and phase-2.5 placement so register's generic message
  cannot pre-empt (Decision 8). Kept separate.
- **Public factory kwargs** (`permission_classes` / `description` /
  `deprecation_reason` / `directives`) — already consistent across all four
  factories; no competing flavors.
- **Per-module `MODULE_PATH` string literals** — package-wide hygiene note for
  the project pass, not an `auth/` ownership finding.

## Judgment

Folder is a thin, deliberately layered composition over write-foundation owners.
The one cross-module policy that was still spelled twice — authenticated-actor
anonymity — now has a single owner in `mutations.py`. No competing helper layers
or unclear state ownership remain inside the folder. Ready for Worker 2.

## Implementation (Worker 1)

- **Owner chosen:** `auth/mutations.py::_authenticated_actor_or_none`.
- **Migrated sites:** `_logout_resolve_body` (`ok = … is not None`);
  `_current_user_resolve_body` (import + call; gate `instance` / return unchanged).
- **Behavior kept separate:** `DjangoModelPermission` None-guard; login
  credential path; declaration vs emit clear phases; register rider vs fixed
  fields.
- **Validation:** `uv run ruff format .` and `uv run ruff check --fix .` — clean.
  No full pytest (not the gate). Permanent proof remains the existing live +
  package auth tests named above.
- **Changelog:** not warranted without maintainer authorization (internal
  private-helper extraction; no public contract change).
- **Concurrent paths preserved:** no edits outside `auth/mutations.py`,
  `auth/queries.py`, and this artifact.

## Independent verification (Worker 2)

Re-traced `auth/` as one component (`__init__.py` structural re-export;
`mutations.py` declaration ledger + fixed-field hub + session/register bodies +
phase-2.5 bind; `queries.py` `current_user` + emit-alias trio). Item-scoped
diff against `2d8baebe703feb86ac5d0940d4eb619bc38b6297` is only the helper
extraction + the two call-site migrations (plus this artifact).

**Shared contract (accepted).** Both former sites encoded the same anonymity
predicate — `getattr(request, "user", None)` then `user is not None and
user.is_authenticated` — and must move together under Channels-adapter /
no-AuthenticationMiddleware / AnonymousUser edges. They differ only in how the
boolean/actor result is consumed (`ok = actor is not None` vs return/gate
`instance=actor`). That is one responsibility with two return shapes, not two
policies. Drift would make `logout.ok` disagree with `me` for the same request.

**Owner.** `_authenticated_actor_or_none` in `mutations.py` is the right hub:
`queries.py` already imports the folder's shared private helpers from there
(`_AUTH_FAMILY_LABEL`, `_declare_fixed_auth_surface`, `_make_auth_field`); the
bind reaches back with a function-local import to break the cycle. Placing the
helper in `queries.py` would reverse that direction for no gain; a new
`auth/_helpers.py` would be a module for one predicate.

**Call sites migrated.** Grep of `auth/`: the full
`getattr` + `is_authenticated` body exists only inside the helper; logout and
`current_user` both call it. No leftover duplicate classification bodies.

**Rejected candidates (disposed).**

- **`utils/permissions.py`:** owns request *resolution* (`request_from_info`,
  Channels adapter) and active-input permission walks — always-loaded. Session-
  actor anonymity is opt-in auth policy (spec-040 Decisions 5/7). Folding it
  there would couple opt-in auth into a core utility and invite wrongly unifying
  the next item.
- **`DjangoModelPermission.has_permission`:** shares only the `getattr` None-
  guard, then `has_perm` for write authorization. Different return shape
  (bool vs actor), different change axis (model codenames vs session anonymity).
  `AnonymousUser` is handled by `has_perm`, not by this classifier. Kept
  separate — correct.
- **Declaration ledger vs alias emit clear phases:** confirmed in source —
  declarations register full-clear-only; `CurrentUserAlias` clears
  `before_bind=True`. Distinct lifecycle roles; not consolidation candidates.
- **Fixed-field path vs register rider; auth vs mutations primary resolution;
  public factory kwargs; MODULE_PATH hygiene:** re-examined; intentional
  separations / project-pass notes stand. No additional folder opportunity.

**Proof.** No new tests (no new behavior). Existing owners pin both edges:
`tests/auth/test_mutations.py::test_logout_without_auth_middleware_is_anonymous_and_flushes_the_session`,
`tests/auth/test_queries.py::test_me_is_null_not_a_crash_when_the_request_user_is_absent`,
live `examples/fakeshop/test_query/test_auth_api.py::test_logout_round_trip_and_anonymous_logout`
and `test_anonymous_me_is_null_not_an_error` (Worker 1 cited the latter as
`test_anonymous_me_returns_null` — citation corrected above; placement N/A, no
new tests). Package-tier middleware-absence / Channels-null-user arms remain the
correct home for shapes unreachable on the aggregated live schema.

**Missed opportunities.** None material inside `auth/`.

**Outcome.** verified. Plan checkbox marked.
