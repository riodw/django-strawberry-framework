# Build: Slice 2 — conformance audit A (auth substrate + `login` / `logout`)

Spec reference: `docs/SPECS/spec-040-auth_mutations-0_0_13.md` (Decisions 1-5, 9, 10 at lines 793-1052, 1461-1600; `## User-facing API` / `### Error shapes` at lines 655-780; `## Slice checklist` Slice 1 block at lines 258-340)
Status: final-accepted

## Plan (Worker 1)

This is a **retrospective conformance audit**, not a build. It ships no source change.
Its instrument is the checklist plus the conformance matrix below; its output is spec
edits (`SPEC-STALE` rows), hand-offs to later slices, and — had there been any — code
gaps. There were none.

### DRY analysis

**Helper inventory checked.** Refreshed package-wide against `HEAD` for this pass by
reading the auth surface and its callees directly rather than re-running the AST
dump: the shapes searched were `sync_to_async` / `run_in_one_sync_boundary` (the
Decision 10 boundary count), `register_subsystem_clear` / `iter_subsystem_clears`
(the Decision 9 clear rows), `_make_permission_holder` / `authorize_or_raise` /
`_validate_permission_classes` (the Decision 5 permission carrier), `loaded_attr` /
`import_attr` / `import_attr_if_importable` (the phase-2.5 reach), and
`field_error` / `unencodable_text_error` (the envelope leaf ctors). Relevant
candidates found and all already reused by call — no new helper is proposed by this
pass, and none could be: the slice writes no `.py`.

- **Existing patterns reused.** None to introduce. The audit *verified* reuse:
  `auth/mutations.py:73` imports the boundary primitive from `utils/querysets.py:456`
  rather than spelling `sync_to_async`; `auth/mutations.py:164` builds the ledger via
  `mutations/sets.py::make_declaration_registry`; `auth/mutations.py:632` gates through
  `mutations/resolvers.py::authorize_or_raise`.
- **New helpers justified.** None. A docs-only pass.
- **Duplication risk avoided.** One real risk, and it is a *documentation* duplication:
  Decisions 2, 4, 5 and 11 could each end up stating a transport contract. The audit's
  fence keeps that single-sited — Decisions 2, 4 and 5 now **point at** Decision 11,
  and Slice 5 writes Decision 11 once.

### Implementation steps

1. Re-verify the spec's status/header lines (`docs/SPECS/spec-040-auth_mutations-0_0_13.md:1-110`).
2. Copy the spec's `## Slice checklist` Slice 1 sub-bullets verbatim; tick only what
   `HEAD` proves.
3. Decompose Decisions 1-5, 9, 10 and the `login` / `logout` half of
   `## User-facing API` / `### Error shapes` into individual normative claims; grade each
   against source read directly.
4. Edit the spec for every `SPEC-STALE` row; append the explanation to the rationale
   companion under the owning Decision.
5. Route every transport-dependent finding to Slice 5 without editing Decision 11.

Line numbers in this artifact are pin-at-write-time navigational hints (per-cycle
scratchpad; raw `path:NN` is permitted here and nowhere else).

### Test additions / updates

None — this pass writes no test. Focused read-only run performed as evidence:

- `uv run pytest tests/auth examples/fakeshop/test_query/test_auth_api.py --no-cov -q`
  → **210 passed** in 20.64s (8 workers). No `--cov*` flag.

### Implementation discretion items

None. Every verdict below is decided.

### Spec slice checklist (verbatim)

The spec's `## Slice checklist` **Slice 1** block, copied verbatim. A box is ticked
only where the contract it states is proved present at `HEAD` by the cited
symbol-qualified path.

- [x] **Slice 1 — auth substrate + `login_mutation` / `logout_mutation`, earned live**
  - [x] `django_strawberry_framework/auth/__init__.py` — the public factory
        re-exports (`login_mutation` / `logout_mutation` in Slice 1;
        `register_mutation` / `current_user` added to the re-exports in Slice 2 as
        they land); **no package-root re-export**
        ([Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export)).

        *Proof:* `django_strawberry_framework/auth/__init__.py` #"__all__ = (" carries the
        four names; `django_strawberry_framework/__init__.py::__all__` and
        `django_strawberry_framework/__init__.py::__getattr__`'s `_DRF_SOFT_EXPORTS` map
        carry none of them (`rg -in "login|logout|register_mutation|current_user"` over
        that file returns 0 hits).
  - [x] `django_strawberry_framework/auth/mutations.py` — the `login_mutation()` /
        `logout_mutation()` field factories (declaration-ledger recording +
        `strawberry.lazy` payload forward-refs + the sync/async resolver pair over
        `django.contrib.auth.authenticate` / `login` / `logout`), the
        `permission_classes=` seam with the explicit AllowAny default
        ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).

        *Proof:* `auth/mutations.py::login_mutation`, `::logout_mutation`,
        `::_declare_fixed_auth_surface` (ledger recording),
        `::login_mutation #"return_annotation=_lazy_ref("LoginPayload", INPUTS_MODULE_PATH)"`,
        `::_login_resolve_body` / `::_login_resolve_body_async`,
        `::_declare_auth_surface #"unset_default=()"`.
  - [x] The auth declaration ledger + `bind_auth_mutations()` wired into
        [`types/finalizer.py`][types-finalizer] phase 2.5 in the pinned slot
        (pre-bind reset loop → `bind_auth_mutations()` → `bind_mutations()` →
        `bind_form_mutations()` — the ordering that keeps the register-arm
        validation reachable), payload materialization through
        `mutations/inputs.py::build_payload_type` onto the **existing**
        `mutations.inputs` emit ledger (the `LoginPayload` object slot resolved
        from the user model's primary [`DjangoType`][glossary-djangotype]; the
        `LogoutPayload` from `object_type=None` — **each materialized only when its
        surface was declared**, the surface-keyed bind of
        [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)),
        and the auth **declaration**
        ledger cleared by a full-clear-only [`register_subsystem_clear`][registry]
        row beside `clear_mutation_registry` / `clear_form_mutation_registry` —
        registered **without** `before_bind`, so the pre-bind reset, which must not
        touch declarations, never reaches it
        ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).

        *Proof:* `types/finalizer.py:1077-1110` runs
        `iter_subsystem_clears(before_bind=True)` → `bind_auth()` → `bind_mutations()` →
        `bind_form_mutations()` in that order;
        `auth/mutations.py::bind_auth_mutations` materializes each payload under a
        `by_surface.get(...) is not None` arm;
        `auth/mutations.py #"register_subsystem_clear(clear_auth_mutation_registry, owner="auth.declarations")"`
        passes no `before_bind` (registry.py:91 defaults it `False`).
  - [x] Bind validation, Slice-1 scope: a declared `login` with no registered
        primary [`DjangoType`][glossary-djangotype] for `get_user_model()` raises
        [`ConfigurationError`][glossary-configurationerror] naming the fix — fired
        from `bind_auth_mutations()` before `bind_mutations()` can raise the
        generic `_resolve_primary_type` message — and a **logout-only** schema
        binds with **no** user type registered at all (the surface-keyed
        exemption). The bind **ordering** is wired here so the Slice-2 register /
        `current_user` arms (their auth-specific errors pinned distinct from
        login's) are reachable the commit those factories land — those arms are
        exercised in Slice 2, not here (`register_mutation()` / `current_user()`
        do not exist in Slice 1)
        ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)
        / [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).

        *Proof:* `auth/mutations.py::_resolve_user_primary_or_raise` (both messages,
        naming the factory the consumer wrote); `::bind_auth_mutations` resolves the
        primary only when `user_typed` is non-empty, so a logout-only ledger never
        reaches the lookup. Pinned by `tests/auth/test_mutations.py::test_login_only_schema_without_user_type_raises_the_login_arm_error`
        and `::test_logout_only_schema_binds_with_no_user_type_and_no_orphan_payloads`.
  - [x] **In the same commit:** the fakeshop `apps/accounts/` live surface (a
        schema-only app declaring `UserType(DjangoType)` over `auth.User` + the auth
        `Query` / `Mutation` blocks, composed into
        [`config/schema.py`][config-schema]), **`"apps.accounts.schema"` added to
        [`schema_reload.py`][schema-reload]'s `_PROJECT_APP_SCHEMA_MODULES`** — the
        row lands in the SAME slice that composes
        accounts into the aggregate, placed among the independent apps (accounts
        references only `auth.User`, no other fakeshop app) before the
        `config.schema` reload, because without it a post-`registry.clear()`
        rebuild raises the `LazyType` `KeyError` (here on the auth payload /
        `UserType` lazy refs) or silently drops the auth surface — the helper's own
        documented failure mode — and the live
        `examples/fakeshop/test_query/test_auth_api.py` login / logout coverage
        (happy path, wrong-credential envelope, anonymous logout, session-cookie
        round trip — the canonical AllowAny default surface only,
        [Test plan](#test-plan)).

        *Proof:* `examples/fakeshop/apps/accounts/schema.py::UserType` /
        `::Query` / `::Mutation`; `examples/fakeshop/config/schema.py:14-15` imports
        both; `examples/fakeshop/schema_reload.py:51` carries `"apps.accounts.schema"`
        at index 2, before `"config.schema"`'s reload at `::reload_project_schema_shell`.
        Live rows: `test_auth_api.py::test_login_happy_path_sets_session_and_me_sees_the_user`,
        `::test_wrong_password_and_unknown_username_return_identical_envelope`,
        `::test_logout_round_trip_and_anonymous_logout`,
        `::test_login_anonymous_to_auth_cycles_key_preserves_anon_data_and_pins_backend`.
  - [x] Mirrored package tests under `tests/auth/` for the residue a live query
        cannot drive (ledger idempotence / clear, bind validation — the login arm +
        the logout-only exemption, the post-finalize-declaration raise, async
        paths, the sessionless-request edge, and the permission-gate variants on
        isolated throwaway schemas — genuinely unreachable live under the
        one-declaration-per-process rule, [Test plan](#test-plan)).

        *Proof, one row per named item:* `tests/auth/test_mutations.py::test_same_args_factory_calls_dedupe_to_one_cached_holder`
        and `::test_registry_clear_drains_ledger_and_resets_conflict_state` (ledger
        idempotence / clear); `::test_login_only_schema_without_user_type_raises_the_login_arm_error`
        + `::test_logout_only_schema_binds_with_no_user_type_and_no_orphan_payloads`
        (bind validation, both arms); `::test_factory_after_finalize_raises_the_standing_configuration_error`
        (post-finalize raise); `::test_async_login_and_logout_run_in_one_sync_boundary`
        (async paths); `::test_sessionless_request_surfaces_djangos_own_error`
        (sessionless edge); `::test_gated_login_denies_with_the_exact_pinned_string_before_authenticate`,
        `::test_gated_logout_denies_with_the_session_holder_string`,
        `::test_gate_introspecting_the_mutation_object_raises_on_the_model_less_fields`
        (permission-gate variants on throwaway schemas).

**Tick count: 7 of 7** (the Slice-1 parent box plus its six sub-bullets). No box is
left `- [ ]`; no deferral reason is owed.

Two notes the ticks do not carry, because the boxes as written are still satisfied:

- The `## Slice checklist` blockquote preceding this block points at retired
  `bld-slice-*.md` / `bld-integration.md` / `bld-final.md` artifacts. **Slice 4 owns
  it** (already routed by Slice 1); not re-raised here.
- The sixth box's `tests/auth/` enumeration is now *under*-inclusive — `HEAD` also
  carries `tests/auth/test_sessions.py`, `conftest.py`, `_helpers.py`. That is a
  Decision 4 staleness, fixed there (row **D4.1** below), not a failed box: every item
  the box names exists.

### Conformance matrix

One row per normative claim. Verdicts: `CONFORMS` / `SPEC-STALE` (code right, spec
moves) / `CODE-GAP` (spec right, code moves) / `UNPROVABLE`.

#### Decision 1 — Spec filename and canonical naming

| # | Claim (spec, quoted) | Settling citation | Verdict |
|---|---|---|---|
| D1.1 | "authored at `docs/spec-040-auth_mutations-0_0_13.md` with companion `docs/spec-040-auth_mutations-0_0_13-terms.csv` (both archived post-ship to `docs/SPECS/`, where this document now lives)" | The file is at `docs/SPECS/spec-040-auth_mutations-0_0_13.md`; `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-terms.csv` exists (the `AGENTS.md` rule-26 `appx/` destination) | `CONFORMS` |
| D1.2 | the `spec-<NNN>-<topic>-<X_Y_Z>` segments: NNN `040`, slug `auth_mutations`, version `0_0_13` | filename parses exactly | `CONFORMS` |

#### Decision 2 — Card-scope boundary

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| D2.1 | "ships exactly the four-symbol session-auth surface over `django.contrib.auth`" | `django_strawberry_framework/auth/__init__.py::__all__` — exactly four names | `CONFORMS` |
| D2.2 | "does **not** ship Channels/websocket auth (the `0.0.14` router card … owns the ASGI-transport story)" | `django_strawberry_framework/auth/sessions.py::Transport` ships `CHANNELS_HTTP` / `CHANNELS_WEBSOCKET`; `::login_supported` / `::logout_supported` answer a per-transport capability question; `auth/mutations.py::_channels_http_login_establish` / `::_channels_logout` are native Channels paths | **`SPEC-STALE`** |
| D2.3 | "does not ship … token/JWT auth … password-change/reset flows" | no such symbol anywhere under `django_strawberry_framework/auth/` | `CONFORMS` |
| D2.4 | "[does not ship] any new [`DjangoType`] `Meta` key" | `types/base.py::ALLOWED_META_KEYS` / `::DEFERRED_META_KEYS` — 16 + 3 entries, none auth-related | `CONFORMS` |
| D2.5 | "[or any new] [`conf.py`] settings key — … `DEFERRED_META_KEYS` and the settings reader are untouched" | `rg -n "auth\|session\|AUTH\|SESSION" django_strawberry_framework/conf.py` → 0 hits | `CONFORMS` |

**D2.2 — what the spec should say instead** (and now does, `spec-040:797-803`): the
ASGI-transport story belongs to the `0.0.14` router card, and *which* transports the
four auth fields accept — and how an unsupported one is rejected — is Decision 11's
single statement. The transport contract itself is **not** restated here; Slice 5
writes it once, in Decision 11.

#### Decision 3 — Consumer surface

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| D3.1 | "importable **only** from the submodule" — the four-name import line | `auth/__init__.py:12-20` | `CONFORMS` |
| D3.2 | "Nothing is added to the package root's `__all__` or its module namespace" | `django_strawberry_framework/__init__.py::__all__` (no auth name) and `::__getattr__` (the PEP 562 map holds only the three DRF soft exports; every other miss raises `AttributeError`) | `CONFORMS` |
| D3.3 | "the auth module is never imported by the package root, so a consumer who doesn't use auth never pays its import" | no package module imports `auth` — the only near-matches are a docstring in `utils/sessions.py` and the unrelated `mutations/resolvers.py` `auth_aliases_for_permission_classes` import; the finalizer reaches the bind via `utils/imports.py::loaded_attr`, which reads `sys.modules` and never imports. Pinned by `tests/auth/test_mutations.py::test_registry_clear_does_not_import_the_auth_subsystem` | `CONFORMS` |
| D3.4 | "Each symbol is a **field factory** (a callable returning a Strawberry field …) — one class-attribute assignment per field, no decorators" | `auth/mutations.py::_make_auth_field` returns `strawberry.field(resolver=_resolve, …)`; `::register_mutation` returns a `DjangoMutationField`; consumer usage at `examples/fakeshop/apps/accounts/schema.py::Mutation` | `CONFORMS` |

#### Decision 4 — Module and test locations

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| D4.1 | the `auth/` subpackage is the three modules `__init__.py` / `mutations.py` / `queries.py` | `ls django_strawberry_framework/auth/` → four modules; `auth/sessions.py` (397 lines) is the fourth | **`SPEC-STALE`** |
| D4.2 | `auth/__init__.py` "re-exports the four public factories (the one import line consumers write)" | `auth/__init__.py:12-20` | `CONFORMS` |
| D4.3 | `auth/mutations.py` holds the three factories, the `Register` rider, "the login / logout permission-holder classes, the sync/async session resolvers, the declaration ledger, and `bind_auth_mutations()`" | all present: `::login_mutation`, `::logout_mutation`, `::register_mutation`, `::_synthesize_register_rider`, `::_make_permission_holder`, `::_login_resolve_body`(`_async`), `::_logout_resolve_body`(`_async`), `::_auth_declaration_registry`, `::bind_auth_mutations` | `CONFORMS` |
| D4.4 | `auth/queries.py` — "`current_user()` and its resolver pair" | `auth/queries.py::current_user`, `::_current_user_resolve_body`; the async half is `mutations.py::_sync_bridged_async_body` applied to that body | `CONFORMS` |
| D4.5 | "`tests/auth/test_mutations.py`, `tests/auth/test_queries.py` for package-only internals" | both exist; `tests/auth/` additionally carries `test_sessions.py`, `conftest.py`, `_helpers.py` | **`SPEC-STALE`** |
| D4.6 | "the live consumer surface lands in `examples/fakeshop/test_query/test_auth_api.py`" | file exists, 21 live rows | `CONFORMS` |

**D4.1 / D4.5 — what the spec should say instead** (and now does, `spec-040:850-858`):
`auth/` is four modules, the fourth being the module-private
`auth/sessions.py` transport-classification and session-capability layer, not
re-exported and `channels`-free on import, **whose contract is Decision 11's**; and
`tests/auth/` mirrors it with `test_sessions.py` alongside `test_mutations.py` /
`test_queries.py`. Stating location and privacy only keeps this from becoming a second
home for the transport contract.

#### Decision 5 — `login` / `logout`

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| D5.1 | `login_mutation()` → two flat non-null args `username` / `password`, resolving to `LoginPayload` (uniform slot + `errors`) | `auth/mutations.py::login_mutation #"arguments=[("username", str), ("password", str)]"`; SDL pinned by `test_auth_api.py::test_generated_auth_type_shapes` | `CONFORMS` |
| D5.2 | `logout_mutation()` takes no arguments, resolves to the model-less `{ ok: Boolean!, errors: [FieldError!]! }` from `build_payload_type(object_type=None)` | `::logout_mutation #"arguments=[]"`; `::bind_auth_mutations #"build_payload_type("Logout", object_type=None, object_slot=None)"`; `test_generated_auth_type_shapes` asserts `"node" not in logout_fields` | `CONFORMS` |
| D5.3 | "The `username` argument name is fixed" (maps onto `USERNAME_FIELD` inside `ModelBackend`) | `::_login_authenticate #"auth.authenticate(request, username=username, password=password)"` | `CONFORMS` |
| D5.4 | step 1 — `request_from_info(info, family_label="AuthMutation")`, the label a single module-level constant | `auth/mutations.py::_AUTH_FAMILY_LABEL` (one definition, consumed by `::_transport_prologue`, `::_login_resolve_body_async`, `::_logout_resolve_body_async`, `queries.py::_current_user_resolve_body`) | `CONFORMS` |
| D5.5 | step 2 — authorization through `authorize_or_raise` via the permission carrier; denial is a top-level `GraphQLError` | `::_login_authenticate #"resolvers.authorize_or_raise(holder_cls, info, "login", {"username": username}, instance=None)"`; `mutations/resolvers.py::authorize_or_raise #"raise GraphQLError(f"Not authorized to {operation} {target_name}.")"` | `CONFORMS` |
| D5.6 | the gate is the **first** thing the resolver does after request resolution | `::_login_authenticate` runs `_transport_prologue` (classify → capability → `require_session`) **before** `authorize_or_raise`; `::_logout_prologue` likewise | **`SPEC-STALE`** |
| D5.7 | step 3 — exactly one `auth.authenticate(...)` call; `None` → `node: null` + ONE `"__all__"`-keyed `FieldError` `"Incorrect username/password"` built via the `field_error("", …)` empty-path leaf ctor, never a hard-coded `"__all__"` | `::_login_authenticate` (one call), `::_failed_login_payload #"resolvers.field_error("", _INCORRECT_CREDENTIALS_MESSAGE)"`, `::_INCORRECT_CREDENTIALS_MESSAGE`. Live: `test_auth_api.py::test_wrong_password_and_unknown_username_return_identical_envelope` | `CONFORMS` |
| D5.8 | the message is undifferentiated — no enumeration oracle | same constant for every failure branch incl. inactive user (`test_inactive_user_gets_the_same_envelope`) and unstorable credential (`::test_login_surrogate_username_is_the_undifferentiated_envelope_not_a_crash`) | `CONFORMS` |
| D5.9 | a non-UTF-8-encodable credential is *not mentioned* by the Decision or the `### Error shapes` table | `::_login_authenticate #"unencodable_text_error("username", username) is not None"` short-circuits to `user = None`, i.e. the same envelope | **`SPEC-STALE`** |
| D5.10 | step 4 — `ok = user.is_authenticated`, then `auth.logout(request)` unconditionally, returning `{ ok, errors: [] }` | `::_logout_observation #"ok = _authenticated_actor_or_none(request) is not None"` — a *shared* anonymity definition covering a request with no `user` attribute at all; the payload is built before any mutation; `::_django_http_logout` then runs `auth.logout(request)` unconditionally | **`SPEC-STALE`** (the `ok` spelling and the payload-before-mutation ordering; "unconditional teardown" and `{ ok, errors: [] }` conform) |
| D5.11 | AllowAny default — unset `permission_classes` resolves to the explicit empty list via `_validate_permission_classes(…, unset_default=())`; **no `AllowAny` class is minted** | `::_declare_auth_surface #"_validate_permission_classes(label, permission_classes, unset_default=())"`; `rg "AllowAny" django_strawberry_framework/` → 0 hits in source | `CONFORMS` |
| D5.12 | a supplied `permission_classes` gets the standard `has_permission(...)` contract incl. the sync-only rule (`async def` hook → `SyncMisuseError`, never a silent allow) | `::_make_permission_holder #"check_permission": DjangoMutation.check_permission`; pinned by `tests/auth/test_mutations.py::test_async_has_permission_raises_sync_misuse_never_a_silent_allow` and `::test_async_permission_hook_rejected_inside_the_sync_worker_too` | `CONFORMS` |
| D5.13 | the holder carries a `_mutation_meta`-shaped snapshot (normalized `permission_classes` + operation), a `_primary_type`, and `check_permission` bound directly; it is **not** a `_ValidatedMutationMeta` | `::_AuthMutationMetaSnapshot` (`__slots__ = ("_sealed", "operation", "permission_classes")`), `::_make_permission_holder` | `CONFORMS` |
| D5.14 | "That holder synthesis is single-sited in ONE `_make_permission_holder(operation, primary_type, permission_classes)` helper" | one synthesis site (`::_make_permission_holder`, reached only through `::_declare_fixed_auth_surface`) — but the signature is `(operation, holder_name, permission_classes)`; `_primary_type` is minted `None` and assigned by `::bind_auth_mutations` | **`SPEC-STALE`** (single-siting conforms; the signature does not) |
| D5.15 | the holder's validated permission set is captured once and cannot be rebound | `::_AuthMutationMetaSnapshot.__setattr__` / `.__delattr__` and `::_SealedAuthHolderMeta.__setattr__` / `.__delattr__` raise `ConfigurationError` — a contract the spec states nowhere | **`SPEC-STALE`** |
| D5.16 | pinned gate payloads: `login` → `data = {"username": username}` (never the password), `instance=None`; `logout` → `data=None`, `instance=None`; `current_user` → `data=None`, `instance=<request user \| None>` | `::_login_authenticate`, `::_logout_prologue #"authorize_or_raise(holder_cls, info, "logout", None, instance=None)"`, `queries.py::_current_user_resolve_body #"authorize_or_raise(holder_cls, info, "current_user", None, instance=actor)"`. Pinned by `test_login_gate_sees_the_attempted_username_and_never_the_password` | `CONFORMS` |
| D5.17 | pinned operation strings `"login"` / `"logout"` / `"current_user"` and pinned holder `__name__`s `Login` / `Session` / `CurrentUser`; the four exact denial strings | `::login_mutation #"_declare_fixed_auth_surface("login", "Login", permission_classes)"`, `::logout_mutation #"("logout", "Session", …)"`, `queries.py::current_user #"("current_user", "CurrentUser", …)"`; target resolution at `mutations/resolvers.py::authorize_or_raise #"getattr(mutation_cls._primary_type, "__name__", mutation_cls.__name__)"`. Strings asserted by `test_gated_login_denies_with_the_exact_pinned_string_before_authenticate`, `test_gated_logout_denies_with_the_session_holder_string`, `test_gated_register_denies_with_the_standard_create_string` | `CONFORMS` |
| D5.18 | `DjangoModelPermission` on a model-less auth field raises at **request time**, documented rather than factory-guarded | no `issubclass` reject exists in `::_declare_auth_surface` / `::_make_permission_holder`; `tests/auth/test_mutations.py::test_gate_introspecting_the_mutation_object_raises_on_the_model_less_fields` pins the request-time raise | `CONFORMS` |
| D5.19 | the generalization: a gate that introspects the `mutation` argument raises on the three model-less fields; key on `info` / `operation` / `data` | same test row; `::_make_permission_holder` gives the holder no `Meta` / `_resolve_model` | `CONFORMS` |
| D5.20 | "the login node is the raw `authenticate()` instance" — no `get_queryset` re-run, no `refetch_optimized` | `::_login_result_payload #"return resolvers.build_payload(payload_cls, slot, user, [])"` — the `authenticate` return object, unretouched; no `refetch_optimized` / `get_queryset` call anywhere in `auth/mutations.py` | `CONFORMS` |

**What the spec should say instead:**

- **D5.6** — the numbered steps state the *credential and session* semantics, and the
  transport prologue both resolvers open with (classification, per-surface capability,
  the missing-session guard — all before the gate) is Decision 11's. Written as a
  pointer at `spec-040:881-887`; the prologue's own contract stays unwritten here.
- **D5.9** — a new step 3: each of `username` / `password` is preflighted through the
  shared `unencodable_text_error` primitive, and an unstorable credential
  short-circuits to the same undifferentiated envelope — byte-identical, so the
  preflight is not an enumeration oracle of its own. Plus a matching `### Error shapes`
  row (`spec-040:773`).
- **D5.10** — `ok` is whether an authenticated actor existed before teardown, answered
  by the ONE shared `_authenticated_actor_or_none` definition `current_user`'s nullable
  return also derives from, so a request with no `user` attribute reads `ok: false`
  rather than raising; the payload is constructed before any session mutation; a
  teardown failure propagates and is never reported as `{ok: true}`.
- **D5.14** — `_make_permission_holder(operation, holder_name, permission_classes)`,
  with `_primary_type` minted `None` and assigned at bind (the user primary is
  unresolved at class-body time), `None` forever for the model-less `logout`.
- **D5.15** — both halves of the holder's authorization state are sealed at synthesis
  (the snapshot's attributes and the class's `_mutation_meta` head), each refusing a
  rebind or delete with `ConfigurationError`, because a custom `has_permission` runs
  holding the holder class.

#### Decision 9 — Bind lifecycle

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| D9.1 | each factory call records a declaration in "a `make_declaration_registry("AuthMutation")` instance, not a hand-rolled list" | `auth/mutations.py::_auth_declaration_registry` = `make_declaration_registry(_AUTH_FAMILY_LABEL)`, `_AUTH_FAMILY_LABEL == "AuthMutation"` | `CONFORMS` |
| D9.2 | the declaration is **surface-keyed** (which of the four, with which `permission_classes`) | `::_declared_auth_surface` scans `_auth_surface`; `::_reject_conflicting_permission_classes` keys on the normalized classes only | `CONFORMS` |
| D9.3 | the field's dispatcher resolver carries an injected `__signature__` / `__annotations__`, "the same mechanism `DjangoMutationField` uses (`mutations/fields.py` `_resolve.__signature__` / `_resolve.__annotations__`)" | `::_make_auth_field #"_resolve.__signature__ = signature"` via `mutations/fields.py::build_lazy_field_signature`; the cited substring still exists at `mutations/fields.py:299-300` | `CONFORMS` |
| D9.4 | return annotation is a `strawberry.lazy` forward-ref: `"LoginPayload"` / `"LogoutPayload"` in the `mutations.inputs` path, `"CurrentUserAlias"` in `auth.queries` | `::login_mutation` / `::logout_mutation` use `_lazy_ref(..., INPUTS_MODULE_PATH)`; `queries.py::current_user` uses `_lazy_ref(CURRENT_USER_ALIAS_NAME, AUTH_QUERIES_MODULE_PATH) \| None` | `CONFORMS` |
| D9.5 | the exact phase-2.5 order: pre-bind reset → `bind_auth_mutations()` → `bind_mutations()` → `bind_form_mutations()` | `types/finalizer.py:1077-1110`, in that literal order | `CONFORMS` |
| D9.6 | the pre-bind reset drains `before_bind=True` rows only — "emit / input-namespace ledgers and per-pass caches only, never the declaration registries" | `registry.py::iter_subsystem_clears #"if not before_bind or runs_before_bind"`; the cited finalizer substring #"phase filter selects emitted namespaces and per-pass caches" is present | `CONFORMS` |
| D9.7 | the auth **declaration** ledger's row is full-clear-only, registered **without** `before_bind` | `auth/mutations.py:169` — `register_subsystem_clear(clear_auth_mutation_registry, owner="auth.declarations")`, no `before_bind` argument; `registry.py:72` defaults it `False`. Pinned by `tests/auth/test_mutations.py::test_declarations_survive_the_pre_bind_reset` | `CONFORMS` |
| D9.8 | the only net-new `before_bind=True` row is the `current_user` alias namespace in `auth/queries.py`, its `clear_fn` from the `make_input_namespace` trio | `auth/queries.py:49-64` — the trio's third member registered with `before_bind=True`; no other `register_subsystem_clear` call exists under `auth/` | `CONFORMS` |
| D9.9 | `LoginPayload` / `LogoutPayload` ride the **existing** `mutations.inputs` `before_bind=True` row — no new row | `::bind_auth_mutations` calls `materialize_mutation_input_class(...)` (the `mutations.inputs` ledger); no auth-side emit row for them | `CONFORMS` |
| D9.10 | the bind is surface-keyed: the user primary is resolved **at most once** and only for `login` / `register` / `current_user` | `::bind_auth_mutations` — one `_resolve_user_primary_or_raise` call guarded by a non-empty `user_typed` list | `CONFORMS` |
| D9.11 | four arms: `login` → validate + `LoginPayload`; `logout` → `LogoutPayload` only, primary neither resolved nor required; `register` → validate only, payloads left to `bind_mutations()`; `current_user` → validate + alias | `::bind_auth_mutations`, all four arms present and exactly as described (the register arm's closing comment states the no-emit contract) | `CONFORMS` |
| D9.12 | "A partial schema therefore emits **no orphan payloads**" | `tests/auth/test_mutations.py::test_login_only_bind_emits_no_orphan_logout_payload`, `::test_register_only_surface_keyed_bind_emits_no_login_logout_payloads`, `::test_logout_only_schema_binds_with_no_user_type_and_no_orphan_payloads` | `CONFORMS` |
| D9.13 | the ledger is also the holders'/rider's same-args cache and conflict state; draining it drains the cache | `::_declared_auth_surface` reads the cache *through* `iter_auth_mutations()`; pinned by `::test_registry_clear_drains_ledger_and_resets_conflict_state` | `CONFORMS` |
| D9.14 | "A factory call **after** finalization raises `ConfigurationError`" | the ledger's own `register`; pinned by `::test_factory_after_finalize_raises_the_standing_configuration_error` | `CONFORMS` |
| D9.15 | *how the finalizer reaches the bind* — the spec is silent | `types/finalizer.py #"bind_auth = loaded_attr("django_strawberry_framework.auth.mutations", "bind_auth_mutations")"` — the already-loaded-only lookup, not the function-local import every sibling binder uses. The silence is load-bearing: a plain import would load `django.contrib.auth` in every finalizing process and silently void Decision 3's opt-in | **`SPEC-STALE`** |

**D9.15 — what the spec should say instead** (and now does, `spec-040:1471-1481`): the
bind is reached through `utils/imports.py::loaded_attr`, never a plain function-local
import, because a plain import would convert Decision 3's structural opt-in into an
unconditional one; a declared auth surface implies the module is already in
`sys.modules`, so the lookup can only skip a genuinely auth-free process, where the
bind would have been a no-op.

#### Decision 10 — Sync + async

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| D10.1 | "Every auth field ships the sync/async resolver pair, dispatched by the same construction-time/runtime detection the field family uses" | `::_make_auth_field #"if in_async_context():"` — the `DjangoMutationField` runtime dispatch, with `sync_body` / `async_body` per field | `CONFORMS` |
| D10.2 | the async paths wrap the session work in **a single** `sync_to_async(thread_sensitive=True)` call per resolution — "one boundary, not per-step hops" | **Counted at `HEAD`, per async path.** `current_user`: `::_sync_bridged_async_body` → 1. `login`, Django HTTP: `::_login_resolve_body_async` → one `run_in_one_sync_boundary(_login_resolve_body, …)` → 1. `login`, Channels HTTP: one `run_in_one_sync_boundary(_login_authenticate, …)` + native `await` → 1. `logout`, Django HTTP → 1. `logout`, Channels → one `run_in_one_sync_boundary(_logout_prologue, …)` + native `await` → 1. Register rider `resolve_async` → 1. **No path enters two.** Pinned by `tests/auth/test_mutations.py::test_async_login_and_logout_run_in_one_sync_boundary` and the four `_sync_boundary_spy` dispatch rows | `CONFORMS` |
| D10.3 | "`current_user`'s async path forces the lazy `request.user` inside the boundary" | `queries.py::_current_user_resolve_body` computes `actor` inside the sync body, which the async path only ever reaches through `::_sync_bridged_async_body`'s boundary | `CONFORMS` |
| D10.4 | "The permission gate runs inside the same boundary on the async path, not before it" | `login`: the gate lives in `::_login_authenticate`, which every async path invokes *inside* `run_in_one_sync_boundary`. `logout`: the gate lives in `::_logout_prologue`, same. `current_user`: inside the bridged body | `CONFORMS` |
| D10.5 | "That boundary is single-sited in ONE auth async helper the three async resolvers share … never a per-field copy of the `sync_to_async(…, thread_sensitive=True)` call" | The named helper `_resolve_auth_async` no longer exists (`git log -S` : present at `fa704722`, removed by `c8346750`). Three separate async bodies now each call `run_in_one_sync_boundary` directly | **`SPEC-STALE`** (the *per-field `sync_to_async` copy* half still holds — `rg "sync_to_async" django_strawberry_framework/auth/` → 0 hits; the *one shared auth helper* half does not) |
| D10.6 | "the generic `run_in_one_sync_boundary(fn, *args, **kwargs)` primitive in `mutations/resolvers.py`" | It is defined at `utils/querysets.py::run_in_one_sync_boundary` and imported by `auth/mutations.py:73` from there. `mutations/resolvers.py` re-imports it and keeps it importable for historical importers | **`SPEC-STALE`** |
| D10.7 | "`run_pipeline_async` rides the primitive as its boundary core, leaving the pinned `036` AR-M4 wording undisturbed" | `mutations/resolvers.py::run_pipeline_async #"return await run_in_one_sync_boundary(sync_body, mutation_cls, info, data, id)"` | `CONFORMS` |
| D10.8 | "the register rider's `resolve_async`" shares that same primitive | `::_synthesize_register_rider` → `Register.resolve_async #"await run_in_one_sync_boundary(_run_register_pipeline_sync, cls, info, data)"` | `CONFORMS` |
| D10.9 | a `sync_to_async(thread_sensitive=True)` worker is itself a sync context, so `reject_async_in_sync_context` still rejects an `async def has_permission` | `tests/auth/test_mutations.py::test_async_permission_hook_rejected_inside_the_sync_worker_too` | `CONFORMS` |
| D10.10 | "`SyncMisuseError` is imported from its public path …, never redefined in `auth/`" | `rg "SyncMisuseError" django_strawberry_framework/auth/` → two docstring mentions, zero definitions and zero imports. The "never redefined" half holds; the "imported from its public path" half is **vacuous** — no auth module imports it, because the guards it belongs to are all reused by call | `CONFORMS` (vacuously on the import half; recorded so a later pass does not read the vacuity as a violation) |
| D10.11 | "Any place auth must detect whether a consumer callable is itself `async def` … uses the partial-aware `is_async_callable` predicate, never a bare `inspect.iscoroutinefunction`" | `rg "iscoroutinefunction" django_strawberry_framework/auth/` → 0 hits. Auth has no such place: `::_authenticated_actor_or_none` inspects a *result* with `inspect.isawaitable`, which is the other case the Decision explicitly carves out | `CONFORMS` (vacuously true; the forbidden spelling is absent) |

**What the spec should say instead:**

- **D10.5 / D10.6** — no auth module spells `sync_to_async` itself; every auth async
  body reaches the boundary through the ONE generic `run_in_one_sync_boundary`
  primitive in `utils/querysets.py` (the neutral utils home beside
  `reject_async_in_sync_context`, so read-side modules reuse it without a
  root-into-subpackage import; still importable from `mutations/resolvers.py` for
  historical importers). Each fixed auth field carries a real sync body and a real
  async body as separate seams, and the invariant D17 pins is the **count, not the
  call site**: one resolution enters the thread-sensitive boundary exactly once.
  Written at `spec-040:1574-1590`.

### Verdict tally

Row counts are the `len()` of each decision block above, re-counted as this table was
written: D1 = 2, D2 = 5, D3 = 4, D4 = 6, D5 = 20, D9 = 15, D10 = 11.

| Verdict | Count |
|---|---|
| `CONFORMS` | 52 |
| `SPEC-STALE` | 11 |
| `CODE-GAP` | **0** |
| `UNPROVABLE` | 0 |
| **Total rows** | **63** |

The eleven `SPEC-STALE` rows, listed so the count is re-derivable rather than asserted:
D2.2, D4.1, D4.5, D5.6, D5.9, D5.10, D5.14, D5.15, D9.15, D10.5, D10.6. They are
discharged by **ten** content edits below (D4.1 + D4.5 are one edit; D5.14 + D5.15 are
one; D10.5 + D10.6 are one; D5.9 takes two — a resolver step and an `### Error shapes`
row).

### Boundary-removal reasoning (read-only)

No mutation was applied — this pass may not mutate source. For each boundary a claim
rests on, whether a test would fail if it were removed, by reading:

- **The `before_bind`-less declaration row** (D9.7): `test_declarations_survive_the_pre_bind_reset`
  asserts the ledger is non-empty after the pre-bind drain; adding `before_bind=True`
  empties it, so the row fails. Additionally every login/logout live row would break,
  because the bind would see no declarations. Strongly pinned.
- **The surface-keyed user-primary resolve** (D9.10/D9.11): removing the `if user_typed:`
  guard makes a logout-only schema resolve a primary it has none of →
  `test_logout_only_schema_binds_with_no_user_type_and_no_orphan_payloads` fails.
- **The `_login_authenticate` storability preflight** (D5.9): removing it lets a lone
  surrogate reach `authenticate` → `test_login_surrogate_username_is_the_undifferentiated_envelope_not_a_crash`
  and `::test_login_surrogate_password_…` fail with a raw `UnicodeEncodeError`. Two rows.
- **The holder seals** (D5.15): `test_auth_permission_holder_snapshot_is_sealed` and
  `test_auth_permission_holder_head_is_sealed` each assert the `ConfigurationError`;
  removing either seal drops its row. Two rows, one per seal.
- **`loaded_attr` at the phase-2.5 bind** (D9.15): swapping it for a plain import would
  keep every auth row green — the auth module is loaded in those tests by construction.
  `test_registry_clear_does_not_import_the_auth_subsystem` pins the *registry* clear
  path, not the finalizer's. **The finalizer's opt-in-preserving reach is pinned by no
  test row this audit could find.** Not a code gap (the code is correct); recorded as a
  test-coverage observation for Slice 4, which owns `## Test plan`.

### Notes for Worker 1 (spec reconciliation)

**Hand-offs to Slice 5 (Decision 11 — transport). Decision 11 was not read, edited, or
cited beyond a pointer.**

1. `django_strawberry_framework/auth/sessions.py` is a fourth `auth/` module Decision
   11 still names nowhere. Decision 4 now lists its **location and privacy only**; its
   **contract** — `::Transport`'s three modes, `::classify_transport`,
   `::require_session`, `::login_supported` / `::logout_supported`,
   `::scope_session_lock`, `::uses_signed_cookie_sessions` — is unwritten and is
   Slice 5's.
2. Decision 5's resolver steps now say the transport prologue runs first and point at
   Decision 11. Slice 5 must write what that prologue *does*: classify → capability →
   `require_session`, all before the gate and before any credential or session work
   (`auth/mutations.py::_transport_prologue`).
3. The two WebSocket rejection constants — `::_WEBSOCKET_LOGIN_UNSUPPORTED` and
   `::_WEBSOCKET_LOGOUT_UNSUPPORTED` — are `ConfigurationError`s raised *before* any
   session mutation, deliberately outside the byte-compatible failed-login envelope.
   Neither appears in the spec, in Decision 5's step list or the `### Error shapes`
   table. Slice 5 owns both the Decision 11 text and the two `### Error shapes` rows;
   this pass deliberately added neither, so the rejection contract is written once.
4. Decision 2's Channels clause was rewritten to point at Decision 11 rather than to
   state a transport contract. If Slice 5's Decision 11 rewrite changes what the auth
   surface accepts, Decision 2 needs no second edit — it now carries no transport claim
   of its own. That is the intent.
5. `auth/mutations.py::_login_resolve_body` and `::_logout_resolve_body` take a single
   `async_to_sync` hop at the private transport boundary for a classified Channels HTTP
   scope under sync execution. This is a sync→async hop the spec describes nowhere, and
   Decision 10's "one boundary" claim is about `sync_to_async`, not this. It is a
   transport behavior: **Slice 5's**.
6. `auth/mutations.py::_channels_logout` runs the teardown inside
   `utils/sessions.py::actor_transition` and documents a two-lock order (scope session
   lock OUTER, actor lease INNER) against `spec-046` Decision 11's WebSocket
   revalidation. That cross-spec interaction is stated only in a docstring. Slice 5
   should decide whether `spec-040` states it or defers to `spec-046`.

**Hand-off to Slice 3 (Decisions 6-8, 12).**

7. Decision 5's D5.16 row proves `current_user`'s gate payload; the `current_user`
   *contract* (Decision 7) was not audited here.
8. `auth/mutations.py::_REGISTER_PROTECTED_FIELDS` and the `derive_register_fields`
   privilege rejection it drives are not in Decision 6's text as this pass read it.
   Slice 3 should check.

**Hand-off to Slice 4 (obligations, edge cases, test plan, DoD).**

9. The `## Slice checklist` blockquote cites four retired `bld-*.md` artifacts
   (already routed by Slice 1; restated so Slice 4 does not have to re-derive it).
10. `## Test plan` owes a row pinning the finalizer's `loaded_attr` reach (see
    *Boundary-removal reasoning*). Today nothing fails if the phase-2.5 bind is changed
    to a plain function-local import, and Decision 3's opt-in is what that would void.
11. The D17 / P3 helper-reuse obligation still describes `run_in_one_sync_boundary`'s
    home. Decision 10 now says `utils/querysets.py`; Slice 4 must re-check that the
    `## Helper-reuse obligations (DRY)` D17 item agrees, or the two homes disagree
    inside one spec.
12. The D18 (`is_async_callable`) and D19 (`SyncMisuseError` import path) obligations
    are **vacuously** satisfied in `auth/` — no call site exists for either. Slice 4
    owns whether an obligation with no call site should still be stated.

### Spec changes made (Worker 1 only)

All in `docs/SPECS/spec-040-auth_mutations-0_0_13.md`; line numbers are post-edit.
Every "why" appended to `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`
under the owning Decision's `### Changes this Decision underwent`.

| # | Spec lines | Change | Reason |
|---|---|---|---|
| 1 | 103-104 | Header/predecessors line: `docs/GLOSSARY.md` "carries [Auth mutations] as `planned for 0.0.13`; Slice 3 flips it to `shipped (0.0.13)`" → "carries [Auth mutations] as `shipped (0.0.13)` with the implemented contract" | Status-line re-verification (`worker-1.md` `## Spec status-line re-verification`): `docs/GLOSSARY.md:97` / `:327` read `shipped (0.0.13)`, so the present-tense claim was false on its own date |
| 2 | 797-803 | Decision 2: the "does not ship Channels/websocket auth" clause replaced by a pointer to Decision 11 | Row D2.2 — `auth/sessions.py` falsified it; the transport contract is stated once, in Decision 11 (Slice 5) |
| 3 | 850-858 | Decision 4: `auth/sessions.py` added to the module enumeration (location + privacy only) and `tests/auth/test_sessions.py` to the test enumeration | Rows D4.1 / D4.5 — the trio is now a quartet |
| 4 | 773 | `### Error shapes`: new row for an unstorable `username` / `password` on `login` | Row D5.9 |
| 5 | 881-887 | Decision 5 `**Resolver semantics**`: lead-in saying the steps are the credential/session semantics and the transport prologue is Decision 11's | Row D5.6 — the gate is no longer step 2 of the whole resolver |
| 6 | 896-904 | Decision 5: new numbered step 3, the credential storability preflight | Row D5.9 |
| 7 | 905-916 | Decision 5 step 4 (was 3): "exactly one call, no local user-model query"; "Success → the session is established" (transport-neutral) | Row D5.7 refinement; the old wording named `auth.login(request, user)`, one transport's spelling |
| 8 | 917-928 | Decision 5 step 5 (was 4): `ok` from the shared `_authenticated_actor_or_none` definition, payload-before-mutation ordering, failure never reported as `{ok: true}` | Row D5.10 |
| 9 | 969-983 | Decision 5: `_make_permission_holder` signature corrected; `_primary_type` minted `None` and assigned at bind; both holder seals stated | Rows D5.14, D5.15 |
| 10 | 1471-1481 | Decision 9 step 2: the `loaded_attr` already-loaded-only reach and why a plain import would void Decision 3's opt-in | Row D9.15 |
| 11 | 1574-1590 | Decision 10: no auth module spells `sync_to_async`; the primitive's home is `utils/querysets.py`; per-field sync + async bodies; the invariant is the boundary **count**, not the call site | Rows D10.5, D10.6 |
| 12 | 2294, 2333, 2338 | Link definitions added: `[auth-sessions]`, `[utils-imports]`, `[utils-querysets]`, `[utils-write-values]`, alphabetical within `<!-- django_strawberry_framework/ -->` | Required by edits 3, 6, 10, 11 |

Rationale companion: post-ship bullets appended under Decisions 1, 2, 3, 4, 5, 9 and
10, each naming what the Decision claimed, the commit that changed it (`c8346750`,
`a6f5a6cb`, `a8f31a2d`, `c537b2dc`, `44b33e9f`, `5e0c53b2`, `fa704722`), and what the
Decision may no longer claim. Decisions 1 and 3 earn a *checked-and-still-true* bullet,
per the companion's own rule that a measured no-change and an unexamined one read
identically otherwise. One `[utils-querysets]` link definition added there too.

**No spec edit touched Decision 11, Decisions 6-8, Decision 12, `## Helper-reuse
obligations (DRY)`, `## Edge cases and constraints`, `## Test plan`, `## Definition of
done`, or the `## Slice checklist`.**

---

## Final verification (Worker 1)

No `CODE-GAP` row, so this closes as a Worker-1-only slice (`docs/builder/build-040-auth_mutations-0_0_13.md`
`## Artifact list` / the task's closing rule). No Worker 2 or Worker 3 pass is owed.

- **Spec slice checklist:** 7 of 7 boxes `- [x]`, each with a symbol-qualified proof
  above. No box left `- [ ]`; no deferral reason owed.
- **Conformance matrix:** 63 rows — 52 `CONFORMS`, 11 `SPEC-STALE`, 0 `CODE-GAP`,
  0 `UNPROVABLE`. Every `SPEC-STALE` row was discharged by an edit in this pass; none
  was deferred.
- **DRY check across this slice and Slice 1:** no new duplication. The one live risk —
  a transport contract stated in Decisions 2, 4, 5 *and* 11 — was avoided by making
  Decisions 2, 4 and 5 carry pointers only. Slice 1's rationale bullet under Decision 10
  named `mutations/resolvers.py` as the primitive's home; this pass corrected it in the
  same file rather than leaving two homes recorded.
- **Existing tests still run:**
  `uv run pytest tests/auth examples/fakeshop/test_query/test_auth_api.py --no-cov -q`
  → **210 passed**, 0 failed, 0 errors. No `--cov*` flag (`BUILD.md` `## Coverage is the
  maintainer's gate, not a worker's tool`).
- **Fail-open shapes:** read the audited surface for the catalogued shapes. The one
  candidate is `auth/mutations.py::_authenticated_actor_or_none`, whose four
  `except (TypeError, ValueError, AttributeError, KeyError, IndexError)` arms return
  `None`. It is **not** fail-open: `None` is the *anonymous* answer, i.e. the denied
  side — a hostile `is_authenticated` classifies as anonymous, never authenticated —
  and every other exception (a `DatabaseError` from a `SimpleLazyObject`) propagates
  rather than being coerced. The guard is on the answer, not on one spelling of bad
  input. No finding.
- **Hot-path:** the plan declares none by default, and this slice produced no code gap,
  so nothing lands on the per-request resolver path. **Not applicable; no re-declaration
  is owed.**
- **Floor verification:** the plan declares none by default, same condition. **No floor
  scope owed by this slice.**
- **Gates run:**
  - `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md`
    → `OK: 30 terms - all have glossary entries and at least one spec link.` (exit 0)
  - In-page anchors, both files: every `](#…)` target resolves against a real heading
    (spec: 17 refs / 34 headings, 0 missing; rationale: 0 missing).
  - Reference-style link convention: every `][label]` has a definition and every
    definition a use, in both files; all ten canonical group headers present and
    unchanged; new definitions alphabetical within their group.
  - `uvx pre-commit run --files …` — see below.
  - `git status --short` — only files on the writable list.
- **Spec reconciliation:** done in-pass; 12 edits recorded above.
- **Final status:** `final-accepted`.

### Summary

A read-only conformance audit of `spec-040`'s Decisions 1-5, 9 and 10, the Slice-1
checklist block, and the `login` / `logout` half of `## User-facing API` /
`### Error shapes` against the shipped tree. **Nothing was dropped or forgotten:** all
seven Slice-1 checklist boxes are proved landed. Every divergence found runs the same
direction — the code moved forward after `0.0.13` and the spec did not — so all nine
are `SPEC-STALE` and none is a `CODE-GAP`. The spec now states the shipped contract
directly for the module quartet, the credential storability preflight, the shared
anonymity definition behind `logout`'s `ok`, the permission holder's real signature and
its two seals, the opt-in-preserving `loaded_attr` reach at phase 2.5, and the real
home and real invariant of the one thread-sensitive boundary. Six transport findings
were recorded as Slice-5 hand-offs and Decision 11 was left untouched, so the transport
contract gets written once.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-djangotype]: ../GLOSSARY.md#djangotype

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[registry]: ../../django_strawberry_framework/registry.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py

<!-- tests/ -->

<!-- examples/ -->
[config-schema]: ../../examples/fakeshop/config/schema.py
[schema-reload]: ../../examples/fakeshop/schema_reload.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
