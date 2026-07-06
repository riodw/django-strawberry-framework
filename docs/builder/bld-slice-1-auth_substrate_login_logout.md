# Build: Slice 1 — auth substrate + `login_mutation` / `logout_mutation`, earned live

Spec reference: `docs/spec-040-auth_mutations-0_0_13.md` (Slice-1 checklist lines 567-630; load-bearing Decisions 5 lines 1215-1417, 8 lines 1758-1858, 9 lines 1860-2007, 10 lines 2009-2054; Helper-reuse obligations lines 2152-2241; Edge cases lines 2243-2378; Test plan lines 2380-2510; DoD item 2/3 lines 2656-2694)
Status: review-accepted

## Plan (Worker 1)

Scope: the auth substrate + `login_mutation()` / `logout_mutation()`, earned live. This slice ships **only** login/logout (fixed field factories), the auth declaration ledger + `bind_auth_mutations()` phase-2.5 wiring, surface-keyed `LoginPayload` / `LogoutPayload` materialization, the `TypeRegistry.clear()` declaration-clear hand row, the Slice-1-scope bind validation (login-arm `ConfigurationError` + logout-only exemption + the bind *ordering* that keeps the Slice-2 arms reachable), and — in the same commit — the fakeshop `accounts` live surface + live `test_auth_api.py` login/logout coverage + mirrored `tests/auth/` residue.

**Explicitly NOT in Slice 1** (Slice 2's contract; do not build): `register_mutation()`, `current_user()`, the `Register` rider, the `CurrentUserAlias` materialization call from the bind, and any register-arm / current-user-arm bind-validation *coverage* (the arms' error messages are exercised in Slice 2 when those factories exist). Slice 1 wires the *ordering* only. `auth/queries.py` and `auth/mutations.py::register_mutation` stay fail-loud placeholders after Slice 1.

Line numbers below are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written (per `BUILD.md` Implementation steps note).

### DRY analysis

- **Utils inventory checked.** `docs/shadow/utils-inventory.md` was refreshed this pass (AST index of all ten `django_strawberry_framework/utils/` modules). Relevant candidates the Slice-1 code reuses **by call**, not re-spell: `utils/permissions.py::request_from_info(info, *, family_label)` (D1 — the shared request resolver, called with `family_label=_AUTH_FAMILY_LABEL`, already defined in the scaffold as `"AuthMutation"`); `utils/typing.py::is_async_callable` (D18 — any async-callable detection); `utils/querysets.py::SyncMisuseError` (D19 — imported from its public path, never redefined); `utils/querysets.py::reject_async_in_sync_context` (D2 — reused transitively through the bound `check_permission`). `utils/inputs.py::make_input_namespace` is a Slice-2 concern (the `current_user` alias namespace) — Slice 1 does not wire it. No new `utils/` helper is justified by Slice 1.

- **Existing patterns reused (cite `path/file.py:NN-MM`).**
  - **Payload materialization — D5.** `mutations/inputs.py::build_payload_type` (`inputs.py:573-616`) + `mutations/inputs.py::payload_object_slot` (`inputs.py:563-570`) + `mutations/inputs.py::materialize_mutation_input_class` (`inputs.py:133-147`) build & pin both payloads onto the **existing** `mutations.inputs` emit ledger. `LoginPayload` = `build_payload_type("Login", object_type=<user primary>, object_slot=payload_object_slot(<user primary>))`; `LogoutPayload` = `build_payload_type("Logout", object_type=None, object_slot=None)`. No new `register_subsystem_clear` row in Slice 1 (importing `auth/mutations.py` transitively imports `mutations/inputs.py`, whose row self-registers at import — spec Decision 9 / `mutations/inputs.py:179`). The scaffold pseudocode at `auth/mutations.py::bind_auth_mutations` already names this exact call sequence.
  - **Permission normalization + holder — D3/P4.** `mutations/sets.py::_validate_permission_classes` (`sets.py:653-733`) called with `unset_default=()` produces the AllowAny empty list (an explicit `[]` is preserved; `sets.py:685-686` + docstring "allow-any opt-out"). `DjangoMutation.check_permission` (`sets.py` `::DjangoMutation.check_permission`, body at `sets.py:998-1015`) reads **only** `type(self)._mutation_meta.permission_classes` — so a duck-typed holder exposing a `_mutation_meta` snapshot with `permission_classes` + `_primary_type` + `check_permission = DjangoMutation.check_permission` (bound directly) suffices; it is **not** a `_ValidatedMutationMeta` (which would need `model` / `operation` ctor kwargs, `sets.py:559`). ONE `_make_permission_holder(operation, primary_type, permission_classes)` helper synthesizes all holders (login now; logout now; current_user in Slice 2).
  - **Authorization gate — D4.** `mutations/resolvers.py::authorize_or_raise` (`resolvers.py:1252-1291`) reused by call: it constructs `mutation_cls()`, runs `check_permission(info, operation, data, instance)` through `reject_async_in_sync_context`, and raises `GraphQLError(f"Not authorized to {operation} {target}.")` where `target = getattr(mutation_cls._primary_type, "__name__", mutation_cls.__name__)` (`resolvers.py:1290`). So the login holder's `_primary_type` = resolved user primary (denial reads the user type name); the logout holder's `_primary_type = None` and its `__name__ = "Session"` (denial reads `"Not authorized to logout Session."`). No auth-specific denial formatter.
  - **Empty-path leaf ctor — D8.** `mutations/resolvers.py::field_error` (`resolvers.py:921-951`): `field_error("", "Incorrect username/password")` normalizes the empty path to `NON_FIELD_ERROR_KEY` (`resolvers.py:942`) — the login-failure `"__all__"`-keyed envelope entry. **Never** a hard-coded `"__all__"` literal.
  - **Lazy return ref + signature injection — D12/P1/P2.** `mutations/fields.py::_lazy_ref(type_name, module_path)` (`fields.py:131-144`) builds `Annotated[type_name, strawberry.lazy(module_path)]`; the `_resolve.__signature__` / `_resolve.__annotations__` injection idiom (`fields.py:245-247`, built by `_synthesized_mutation_signature` `fields.py:147-202`) is what lets a fixed field carry a lazy forward-ref return before the user primary is resolved. The auth fixed-field dispatcher reuses `_lazy_ref("LoginPayload", INPUTS_MODULE_PATH)` / `_lazy_ref("LogoutPayload", INPUTS_MODULE_PATH)` and injects a hand-built `inspect.Signature` for the auth arg shapes (`login`: `username: str`, `password: str`; `logout`: none). Note `mutations/fields.py:64` already carries a `TODO(spec-040 Slice 1)` inviting promotion of `_lazy_ref` + the signature-attachment idiom to shared machinery so auth and `DjangoMutationField` share ONE injector rather than a per-field copy (the D12/P1/P2 directive — see Implementation discretion for the promotion-shape latitude).
  - **Declaration ledger — D14.** `mutations/sets.py::make_declaration_registry("AuthMutation")` (`sets.py:426-466`) is already instantiated in the scaffold (`auth/mutations.py:17-21` — `register_auth_mutation` / `clear_auth_mutation_registry` / `iter_auth_mutations` / `_auth_declarations`). `register` is identity-deduped (`sets.py:457-458`) and raises after finalization (`sets.py:452-456`) — the standing declare-after-finalize rule. Slice 1 records login/logout declarations through `register_auth_mutation`.
  - **Declaration-clear hand row — D15.** `registry.py::TypeRegistry.clear` (`registry.py:514-629`) carries the mutation / form declaration-clear rows (`registry.py:581-585`, `599-603`). The pre-placed `TODO(spec-040 Slice 1)` at `registry.py:586-593` names the exact insertion: a `_clear_if_importable("django_strawberry_framework.auth.mutations", "clear_auth_mutation_registry", lambda clear: clear())` row **beside** them — **not** `register_subsystem_clear` (the pre-bind reset would drain it before the auth bind reads it, spec Decision 9 / `registry.py:572-575`).
  - **Primary-type lookup — D16.** `bind_auth_mutations()` resolves the user primary via `registry.get(get_user_model())` — the same getter `mutations/sets.py::_resolve_primary_type` uses (`sets.py:1034`) — and consults `registry.types_for(get_user_model())` (`sets.py:1037`) only to split the no-type message from the multiple-types-without-primary ambiguity message. The auth check's *message* differs; "what counts as a registered primary" stays single-sited.
  - **Bind slot — D9.** `types/finalizer.py::finalize_django_types` (`finalizer.py:574-830`); the pre-bind reset loop is `finalizer.py:786-787` (`for module_path, attr in iter_subsystem_clears(): _clear_if_importable(...)`), and `bind_mutations()` is at `finalizer.py:797`, `bind_form_mutations()` at `finalizer.py:810`. The pre-placed `TODO(spec-040 Slice 1)` at `finalizer.py:788-796` marks the exact slot: a function-local `from ..auth.mutations import bind_auth_mutations` + call, **after** the reset loop and **before** `bind_mutations()`.

- **New helpers justified (single responsibility + call sites).**
  - `auth/mutations.py::_make_permission_holder(operation, primary_type, permission_classes)` — synthesizes the duck-typed permission holder class (D3/P4). Single responsibility: build ONE `_mutation_meta`-shaped snapshot + `_primary_type` + bound `check_permission`, with a pinned `__name__`. Call sites: `login_mutation` (op `"login"`, primary = user primary, `__name__="Login"`), `logout_mutation` (op `"logout"`, primary=`None`, `__name__="Session"`), and in Slice 2 `current_user` (op `"current_user"`, primary=user primary, `__name__="CurrentUser"`). Justified now (two Slice-1 call sites); avoids three near-identical class bodies. The holder `__name__`s are test-asserted contracts (spec lines 1318-1333), so they are pinned here, not left to Worker-2 taste.
  - `auth/mutations.py` shared **auth fixed-field dispatcher builder** — the ONE helper that, given `(operation, permission_holder, payload_lazy_ref, resolver_body)`, returns a `strawberry.field(resolver=...)` with the injected `__signature__` / `__annotations__` (D12/P1/P2). Single responsibility: fixed-field construction with the injected lazy return. Call sites: `login_mutation`, `logout_mutation` (and `current_user` in Slice 2). This is the "shared auth dispatcher/signature helper" the scaffold pseudocode names (`auth/mutations.py:69`, `auth/queries.py:38`). If the D12/P1/P2 promotion of `_lazy_ref` + the injection idiom to shared machinery is done, this helper consumes the promoted primitive rather than a per-field copy.
  - `auth/mutations.py` shared **one-boundary async helper** — the ONE `sync_to_async(thread_sensitive=True)` wrapper the async resolvers share (D17/P3). Single responsibility: run the whole gate-then-session-work block in one sync worker. Call sites: `login`/`logout` async paths now (and `current_user` async in Slice 2). Never a per-field copy of the `sync_to_async(..., thread_sensitive=True)` call.
  - The auth resolver bodies themselves (`login` sync/async, `logout` sync/async) are the only genuinely new machinery this slice adds beyond reuse — small resolvers over `django.contrib.auth.authenticate` / `login` / `logout` behind the envelope.

- **Duplication risk avoided.**
  - **Three near-identical holder class bodies** → collapsed into `_make_permission_holder` (D3/P4). The naive shape spells a class body per field.
  - **Per-field `sync_to_async` boundary copies** → one shared async helper (D17/P3). The naive shape copies the `sync_to_async(..., thread_sensitive=True)` call into each async resolver.
  - **Per-field `info.context.request` walks** → `request_from_info(info, family_label=_AUTH_FAMILY_LABEL)` with one shared label constant (D1). The naive shape re-spells the context walk.
  - **A second payload namespace / a hand-rolled payload builder** → reuse `build_payload_type` + the `mutations.inputs` emit ledger (D5). The naive shape forks a `auth`-local payload builder, forking the distinct-shape collision story.
  - **Hard-coded `"__all__"`** in the login-failure envelope → `field_error("", …)` (D8). The naive shape writes the sentinel string directly.
  - **A new `AllowAny` primitive** → NONE is created (spec lines 1262-1267); "AllowAny" is the semantics of `_validate_permission_classes(..., unset_default=())`. The naive shape mints a public `AllowAny` class.
  - **A hand-rolled declaration list** → reuse the `make_declaration_registry("AuthMutation")` instance already in the scaffold (D14). The naive shape keeps a module-level `list`.
  - **Answer to "any DRY question = none"?** No — every question above has a concrete reuse or a justified single-sited helper. Silence is not acceptance; nothing here is left unaddressed.

### Implementation steps

1. **`django_strawberry_framework/auth/mutations.py` — the login/logout factories, holder helper, dispatcher helper, async-boundary helper, and the real `bind_auth_mutations()`.** Remove the four `TODO(spec-040 Slice 1)` anchors (`mutations.py:23`, `:33`, `:63`, `:89`); leave the `TODO(spec-040 Slice 2)` register anchor (`:111`) and the fail-loud `register_mutation` body untouched.
   - Keep the module-level `_AUTH_FAMILY_LABEL = "AuthMutation"` constant and the `make_declaration_registry("AuthMutation")` instance (`mutations.py:16-21`). Records go through `register_auth_mutation`. The ledger is **surface-keyed**: each record captures which surface (`"login"` / `"logout"`) with which normalized `permission_classes`, and is the holder cache + conflict state (Decision 9 lines 1950-1958) — so a same-`permission_classes` repeat returns the cached holder (idempotent), a different-`permission_classes` repeat raises `ConfigurationError` (Edge cases lines 2297-2304), and the conflict/cache state drains with the ledger on `registry.clear()`. The conflict/cache **key is the normalized `permission_classes` only** — `description` / `deprecation_reason` / `directives` are per-field `strawberry.field` presentation kwargs applied to each returned field and excluded from the key (spec lines 2308-2318). (See Implementation discretion for the ledger record's concrete shape.)
   - Add `_make_permission_holder(operation, primary_type, permission_classes)` (D3/P4) — builds the duck-typed `_mutation_meta` snapshot via `_validate_permission_classes(<name>, permission_classes, unset_default=())`, sets `_primary_type`, binds `check_permission = DjangoMutation.check_permission`, pins `__name__`. Pinned `__name__`s: login holder = `Login`, logout holder = `Session` (spec lines 1318-1333; `Session` is load-bearing — it IS the denial target under the `_primary_type is None` fallback at `resolvers.py:1290`).
   - Add the shared **auth fixed-field dispatcher builder** (D12/P1/P2) — injects `__signature__` / `__annotations__` with the lazy return ref (`_lazy_ref("LoginPayload", INPUTS_MODULE_PATH)` / `_lazy_ref("LogoutPayload", INPUTS_MODULE_PATH)`, `INPUTS_MODULE_PATH` = `mutations/inputs.py:64`) and dispatches sync-vs-async at runtime (the `in_async_context()` idiom `DjangoMutationField` uses, `fields.py:241`). Login args: `username: str`, `password: str` (both non-null — `String!`). Logout: no args.
   - Add the shared **one-boundary async helper** (D17/P3) — `await sync_to_async(fn, thread_sensitive=True)()` wrapping the whole gate-then-work block.
   - `login_mutation(*, permission_classes=None, description=None, deprecation_reason=None, directives=())`: normalize permissions (`unset_default=()`); resolve/reuse cached holder or raise on conflict; record via `register_auth_mutation`; build the field. Resolver (sync): `request = request_from_info(info, family_label=_AUTH_FAMILY_LABEL)` (D1); `authorize_or_raise(holder, info, "login", {"username": username}, instance=None)` (D4 — `data={"username": username}`, **never** the password; spec lines 1306-1312); `user = auth.authenticate(request, username=username, password=password)`; on `None` → payload with object slot `None` + `[field_error("", "Incorrect username/password")]` (D8); on success → `auth.login(request, user)` then payload with the user in the slot (NO `get_queryset`, NO `refetch_optimized` — D-N1 / D9, spec lines 1370-1389). Async path: run gate+authenticate+login inside the one-boundary helper (Decision 10).
   - `logout_mutation(*, ...)`: same normalization/record/build. Holder `_primary_type=None`, `__name__="Session"`. Resolver: `request = request_from_info(...)`; `authorize_or_raise(holder, info, "logout", None, instance=None)`; `ok = request.user.is_authenticated` (captured before teardown); `auth.logout(request)` unconditionally; return `LogoutPayload(ok=ok, errors=[])` (Decision 5 step 4 / Edge cases lines 2258-2259). Async via the shared boundary helper.
   - Replace the placeholder `bind_auth_mutations()` (`mutations.py:31-52`) with the real **surface-keyed** bind (Decision 9 lines 1906-1934): snapshot `iter_auth_mutations()`; read which surfaces the ledger carries; **only if a user-typed surface (login) was declared**, resolve the user primary via `registry.get(get_user_model())` + validate (Decision 8, the login-arm message using `registry.types_for` to split no-type vs ambiguous — D16); materialize `LoginPayload` via `build_payload_type("Login", object_type=primary, object_slot=payload_object_slot(primary))` + `materialize_mutation_input_class` (D5); if `logout` was declared, materialize `LogoutPayload` via `build_payload_type("Logout", object_type=None, object_slot=None)` + `materialize_mutation_input_class` — **and do NOT resolve or require the user primary for a logout-only ledger** (the structural exemption, Decision 8 lines 1780-1782 / Decision 9 lines 1916-1918). Slice 1 must NOT call `materialize_current_user_alias` and must NOT reference `register`/`current_user` arms in the bind body beyond leaving the ordering slot ready (those factories don't exist yet). The post-finalize declare-after-finalize raise is already owned by the ledger `register` (`sets.py:452-456`).

2. **`django_strawberry_framework/types/finalizer.py` — wire `bind_auth_mutations()` into the pinned phase-2.5 slot.** At `finalizer.py:788-796` replace the `TODO(spec-040 Slice 1)` block with a function-local `from ..auth.mutations import bind_auth_mutations` and a `bind_auth_mutations()` call, placed **after** the `iter_subsystem_clears()` pre-bind reset loop (`finalizer.py:786-787`) and **before** `bind_mutations()` (`finalizer.py:797`). Function-local import (cycle-safe, mirroring `bind_mutations` / `bind_form_mutations`). Two-line net addition to the `finalize_django_types` hotspot; no other logic in that function changes. This is the ordering (pre-bind reset → `bind_auth_mutations()` → `bind_mutations()` → `bind_form_mutations()`) that keeps the Slice-2 register arm's auth-specific error reachable ahead of `_resolve_primary_type`'s generic raise (Decision 8 lines 1784-1805 / Decision 9 lines 1899-1905).

3. **`django_strawberry_framework/registry.py` — add the auth declaration-clear hand row.** At `registry.py:586-593` replace the `TODO(spec-040 Slice 1)` block with a `_clear_if_importable("django_strawberry_framework.auth.mutations", "clear_auth_mutation_registry", lambda clear: clear())` row, placed beside the `clear_mutation_registry` (`registry.py:581-585`) / `clear_form_mutation_registry` (`registry.py:599-603`) declaration-clear rows — NOT `register_subsystem_clear` (D15 / Decision 9). This clear drains the ledger (and thus the holder cache + conflict state).

4. **`examples/fakeshop/apps/accounts/schema.py` — the schema-only accounts surface (login/logout).** Remove the `TODO(spec-040 Slice 1)` anchor (`schema.py:8`); leave the `TODO(spec-040 Slice 2)` anchor (`:15`) and add the Slice-2 register/me surface only in Slice 2. Declare `UserType(DjangoType)` over `get_user_model()` with `Meta.fields = ("id", "username", "email")` and `Meta.interfaces = (relay.Node,)` (spec User-facing API lines 967-971; explicit selection is the authenticated read surface — Decision 8 lines 1807-1816, `password`/privilege columns off). Expose an app-local `@strawberry.type class Mutation` with `login = login_mutation()` and `logout = logout_mutation()` (AllowAny default — the canonical live surface, no gated variant). No app-local `Query` in Slice 1 (`me` is Slice 2). Consumer surface stays decorator-free on `UserType` (one class-attribute assignment per field — `START.md` "Meta classes everywhere").

5. **`examples/fakeshop/config/settings.py` — install the accounts app.** Remove the `TODO(spec-040 Slice 1)` anchor (`settings.py:47-52`) and add `"apps.accounts.apps.AccountsConfig"` to the local-app block of `INSTALLED_APPS`. **This anchor is a genuine Slice-1 discharge obligation not explicitly itemized in the spec's Slice-1 checklist bullet, but required** — the accounts app must be installed for `UserType` over `auth.User` to register and for `apps.accounts.schema` to import (see Notes for Worker 1 / spec reconciliation). `AGENTS.md`'s "the staged anchor is removed in the same change that ships the slice" makes this non-waivable even though the checklist bullet omits `settings.py`.

6. **`examples/fakeshop/config/schema.py` — compose accounts into the aggregate.** Remove the `TODO(spec-040 Slice 1)` anchor (`config/schema.py:23-27`). Import `apps.accounts.schema`'s `Mutation` (as `AccountsMutation`) and add it to the top-level `Mutation` multiple-inheritance composition (`config/schema.py:41`), placed among the independent apps (accounts references only `auth.User`). No `Query` composition change in Slice 1 (`me` is Slice 2). `finalize_django_types()` (`config/schema.py:60`) then runs the phase-2.5 auth bind before `strawberry.Schema(...)` resolves the `LoginPayload` / `LogoutPayload` / `UserType` lazy refs.

7. **`examples/fakeshop/schema_reload.py` — add `"apps.accounts.schema"` to `_PROJECT_APP_SCHEMA_MODULES`.** Insert `"apps.accounts.schema"` into the tuple (`schema_reload.py:41-47`), placed among the independent apps (accounts references only `auth.User`, no other fakeshop app), **before** the `config.schema` reload. This is the Revision-7 reload fix (spec Slice-1 bullet lines 609-624): without it a post-`registry.clear()` rebuild raises the documented `LazyType` `KeyError` on the auth payload / `UserType` lazy refs, or silently drops the auth surface (`schema_reload.py:5-25` docstring). The row lands in the SAME slice that composes accounts.

8. **`examples/fakeshop/test_query/test_auth_api.py` — live login/logout coverage (AllowAny default surface).** Remove the `TODO(spec-040 Slice 1)` anchor (`test_auth_api.py:3`); leave the Slice-2 anchor (`:10`). Every test's first executable line is `create_users(N)` from `apps.products.services` (`AGENTS.md` first-line seed rule / spec Test plan lines 2389-2395; seeded users share password `"admin"` = `services.TEST_USER_PASSWORD`, are `is_active=True`). See Test additions.

9. **`tests/auth/test_mutations.py` — mirrored package residue (Slice-1 internals only).** Replace the Slice-1 `TODO` (`test_mutations.py:3-9`) with the real tests; leave the Slice-2 `TODO` block (`:11-17`). See Test additions. Do not touch `tests/auth/test_queries.py` (current_user is Slice 2) or the `tests/auth/__init__.py` `TODO(spec-040 Slice 1-2)` anchor (spans both slices; discharged when Slice 2 lands).

### Test additions / updates

**Live — `examples/fakeshop/test_query/test_auth_api.py` (primary, one commit with the resolvers).** Each test opens with `create_users(N)`; users seeded with password `"admin"`. Pin (spec Test plan lines 2397-2436):
- **login happy path** — `login(username:"staff_1", password:"admin")` returns the payload user in the object slot, empty `errors`; the response sets a session cookie; a follow-up query over the same test client sees the session established. Assert against the fakeshop-specific `node` slot only where the example `UserType` is Relay-backed (do NOT encode `node` as the generic contract — spec lines 1031-1038 / 2431-2436).
- **wrong password AND unknown username** — byte-identical `"__all__"`-keyed envelope, `node: null`, one message `"Incorrect username/password"` (enumeration guard pinned as a shape equality between the two cases — spec lines 2401-2402 / Edge cases lines 2245-2248).
- **inactive user** — same `"__all__"` envelope (Django's `authenticate` returns `None` for `is_active=False` under `ModelBackend`).
- **logout** — `logout` returns `ok: true` when an authenticated session existed; `ok: false` for an anonymous logout, empty `errors` (idempotent — spec Edge cases lines 2258-2259). (A post-logout `me: null` assertion belongs to Slice 2, where `me` exists; Slice 1 asserts the session cookie is cleared/flushed at the transport level.)
- **SDL assertions (Slice-1 subset)** — `LoginPayload` and `LogoutPayload` shapes as pinned in User-facing API (lines 1002-1010): `LoginPayload { <slot>: UserType, errors: [FieldError!]! }`, `LogoutPayload { ok: Boolean!, errors: [FieldError!]! }`. (`RegisterInput` / `RegisterPayload` SDL is Slice 2.)
- **complete-reload path (Slice-1 subset)** — a test that calls `reload_all_project_schemas()` (with `"apps.accounts.schema"` now in `_PROJECT_APP_SCHEMA_MODULES`) and confirms `login` / `logout` survive the `registry.clear()` rebuild — pinning against the `LazyType` `KeyError` / silently-dropped-surface failure modes (`schema_reload.py` docstring / spec lines 2426-2430). (The `me` half of this test is Slice 2.)

**Package-internal — `tests/auth/test_mutations.py` (mirrored, Slice-1 internals only; genuinely unreachable-live).** Pin (spec Test plan lines 2438-2505, filtered to Slice-1 scope):
- **ledger mechanics** — record / identity-dedupe; the **declaration** ledger clears via the `TypeRegistry.clear()` hand row (NOT the pre-bind seam) while the **emit** ledger (`mutations.inputs`) clears via the pre-bind reset; a test pins that auth **declarations survive** the pre-bind reset (the retry contract) and a re-finalize rebuilds `LoginPayload` / `LogoutPayload`.
- **conflicting-declaration raise** — a second `login_mutation(permission_classes=[Other])` after a default `login_mutation()` (same process) raises `ConfigurationError`, **keyed on `permission_classes` only**; a repeat call differing solely in `description` / `deprecation_reason` / `directives` returns the cached holder, never raises (Edge cases lines 2308-2318). A same-`permission_classes` repeat is idempotent.
- **bind validation (surface-keyed, Slice-1 scope)** — a login-declaring schema with no registered `UserType` primary for `get_user_model()` raises the **auth-specific** `ConfigurationError` (message names the fix: "declare a `DjangoType` with `Meta.model = get_user_model()`; mark it `Meta.primary = True` if the model has several") fired from `bind_auth_mutations()`; a **logout-only** schema with no `UserType` **binds successfully**, materializing only `LogoutPayload` and never resolving the user primary (the structural exemption). Register-arm / current-user-arm no-`UserType` coverage is explicitly Slice 2 (those factories don't exist in Slice 1) — do NOT add it here.
- **post-finalize factory raise** — `login_mutation()` / `logout_mutation()` after `finalize_django_types()` raise `ConfigurationError` (the standing declare-after-finalize rule via the ledger `register`).
- **sync/async** — both resolver paths for login and logout; the one-boundary discipline (the async path wraps gate+session-work in one `sync_to_async(thread_sensitive=True)`); an `async def has_permission` on a gated login/logout raises `SyncMisuseError` through `check_permission` even inside the sync worker (never a silent allow).
- **permission-gate variants (isolated throwaway schemas, `registry.clear()` between default and gated declarations)** — a gated `login` / `logout` denying with the top-level `GraphQLError` and the **exact** pinned denial strings: `"Not authorized to login <UserType>."` and `"Not authorized to logout Session."` (the pinned holder `__name__`); a custom `login` gate keyed on `data["username"]` sees the **attempted username** in `data` and asserts the password is **NOT** in `data`. (The `me`-gate / `IsAuthenticated` / mutation-introspection-raise variants are Slice 2.)
- **sessionless-request edge** — Django's own error propagates (not swallowed / not a silent pass); the package adds no probe (Decision 11 / Edge cases lines 2336-2340).

**Temp/scratch tests for Worker 3.** None planned as required; Worker 3 may create throwaway isolated-schema fixtures under `docs/builder/temp-tests/slice-1/` to independently confirm the surface-keyed logout-only exemption and the pinned denial strings if the diff's own tests are ambiguous. Note them there for disposition.

**Focused (non-coverage) test commands Worker 2/3 may run** (never with `--cov*`): `uv run pytest tests/auth/test_mutations.py --no-cov`, `uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov`, and `uv run pytest tests/mutations/ --no-cov` (the register rider is not touched in Slice 1, so `036`/`038`/`039` surfaces must stay green untouched — spec Cross-cutting lines 2507-2510).

### Implementation discretion items

Items I have **assessed and decided** belong to Worker 2 (equivalent shapes / naming / independent ordering) — not architectural escape hatches:

- **The surface-keyed ledger record's concrete shape.** The `make_declaration_registry("AuthMutation")` store is typed `list[type]` (`sets.py:423`), but the auth ledger records *surfaces* (which of login/logout with which `permission_classes`), not `DjangoType` classes. Worker 2 chooses the record object it registers (e.g. a small frozen dataclass / a synthesized marker class carrying `surface` + normalized `permission_classes` + the cached holder) so `register`'s identity-dedupe (`not in store`) and the `TypeRegistry.clear()` drain both operate correctly and the record doubles as the holder cache + conflict state (Decision 9 lines 1950-1958). Any shape satisfying identity-dedupe + carrying the cache/conflict state is acceptable; the spec does not pin it.
- **D12/P1/P2 promotion depth.** Whether to physically move `_lazy_ref` + the `__signature__`/`__annotations__` injection out of `mutations/fields.py` into shared machinery (the `fields.py:64` TODO invites it), versus importing and reusing them in place from `auth/mutations.py`. Either satisfies "single-sited, not a per-field copy." Worker 2 picks the lower-churn shape that keeps ONE injector; if it promotes, it removes the `fields.py:64` `TODO(spec-040 Slice 1)` anchor in this slice.
- **D17/P3 boundary-helper reach.** Whether the shared one-boundary async helper is auth-local or the optional generic `run_in_one_sync_boundary(fn, *args)` primitive shared with the `036` wrapper (spec lines 2027-2035; explicitly optional, "only if it does not disturb the pinned `036` AR-M4 wording"). Worker 2 may keep it auth-local for Slice 1 and defer the generic primitive; `resolvers.py:1428` carries a `TODO(spec-040 Slice 1)` inviting the factoring — if Worker 2 does the generic factoring it removes that anchor, otherwise the anchor stays for a later discharge and Worker 1 records the deferral. (Auth-local is the safe default; the generic primitive is a "may," not a "must.")
- **Ordering of the two independent doc/config edits** (settings-install vs schema-compose) and the internal helper definition order within `auth/mutations.py`.
- **`AccountsMutation` composition position** in `config/schema.py`'s `Mutation` bases (accounts is independent — references only `auth.User` — so any position among the independent apps is valid; mirror the `schema_reload.py` "independent apps" placement).

### Spec slice checklist (verbatim)

- [x] **Slice 1 — auth substrate + `login_mutation` / `logout_mutation`, earned live**
  - [x] `django_strawberry_framework/auth/__init__.py` — the public factory
        re-exports (`login_mutation` / `logout_mutation` in Slice 1;
        `register_mutation` / `current_user` added to the re-exports in Slice 2 as
        they land); **no package-root re-export**
        ([Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export)).
  - [x] `django_strawberry_framework/auth/mutations.py` — the `login_mutation()` /
        `logout_mutation()` field factories (declaration-ledger recording +
        `strawberry.lazy` payload forward-refs + the sync/async resolver pair over
        `django.contrib.auth.authenticate` / `login` / `logout`), the
        `permission_classes=` seam with the explicit AllowAny default
        ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
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
        ledger cleared by a `TypeRegistry.clear()` hand row beside
        `clear_mutation_registry` / `clear_form_mutation_registry` — **not**
        [`register_subsystem_clear`][registry] (that seam is drained by the
        pre-bind reset, which must not touch declarations)
        ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
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
  - [x] **In the same commit:** the fakeshop `apps/accounts/` live surface (a
        schema-only app declaring `UserType(DjangoType)` over `auth.User` + the auth
        `Query` / `Mutation` blocks, composed into
        [`config/schema.py`][config-schema]), **`"apps.accounts.schema"` added to
        [`schema_reload.py`][schema-reload]'s `_PROJECT_APP_SCHEMA_MODULES`** — the
        Revision-7 reload fix: the row lands in the SAME slice that composes
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
  - [x] Mirrored package tests under `tests/auth/` for the residue a live query
        cannot drive (ledger idempotence / clear, bind validation — the login arm +
        the logout-only exemption, the post-finalize-declaration raise, async
        paths, the sessionless-request edge, and the permission-gate variants on
        isolated throwaway schemas — genuinely unreachable live under the
        one-declaration-per-process rule, [Test plan](#test-plan)).

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/auth/mutations.py` — implemented the real
  `login_mutation()` / `logout_mutation()` over the fail-loud scaffold: the
  `_AuthDeclaration` surface-keyed ledger record (holder cache + conflict state),
  `_make_permission_holder` (D3/P4 — one synthesizer, pinned `__name__`s `Login`
  / `Session`), `_build_auth_field` (the one auth dispatcher builder consuming the
  promoted `attach_synthesized_signature`), `_run_in_one_boundary` (D17/P3 — the
  one shared `sync_to_async(thread_sensitive=True)` wrapper), `_declare_surface`
  (normalize/dedupe/conflict), `_resolve_user_primary` (Decision 8 auth-specific
  message via `registry.get` + `registry.types_for`), and the real surface-keyed
  `bind_auth_mutations()`. Discharged the four `TODO(spec-040 Slice 1)` anchors
  (`:23 :33 :63 :89`); left the Slice-2 register placeholder + its
  `TODO(spec-040 Slice 2)` anchor untouched.
- `django_strawberry_framework/mutations/fields.py` — discharged the
  `TODO(spec-040 Slice 1)` promotion anchor (`:64`) by promoting the
  signature-attachment idiom into a shared `attach_synthesized_signature(resolver,
  params, return_annotation)` helper (D12/P1/P2 — ONE injector); `_lazy_ref` was
  already here and stays. `_synthesized_mutation_signature` now returns `(params,
  return_annotation)` and `DjangoMutationField` calls the shared helper — the SDL
  output is byte-unchanged (verified by the 176 `tests/mutations/` passing).
- `django_strawberry_framework/types/finalizer.py` — replaced the phase-2.5
  `TODO(spec-040 Slice 1)` slot (`:788`) with a function-local
  `from ..auth.mutations import bind_auth_mutations` + call, placed AFTER the
  pre-bind reset loop and BEFORE `bind_mutations()` (the load-bearing ordering).
- `django_strawberry_framework/registry.py` — replaced the `TypeRegistry.clear()`
  `TODO(spec-040 Slice 1)` block (`:586`) with the
  `clear_auth_mutation_registry` hand row beside the mutation / form
  declaration-clear rows (D15 — NOT `register_subsystem_clear`).
- `examples/fakeshop/apps/accounts/schema.py` — declared `UserType(DjangoType)`
  over `get_user_model()` with `fields=("id","username","email")` +
  `interfaces=(relay.Node,)` and the app-local `Mutation` (`login`/`logout`,
  AllowAny default). Discharged the Slice-1 anchor; left the Slice-2 anchor.
- `examples/fakeshop/config/settings.py` — installed
  `"apps.accounts.apps.AccountsConfig"`; discharged the `settings.py:47` anchor.
- `examples/fakeshop/config/schema.py` — imported `apps.accounts.schema`'s
  `Mutation as AccountsMutation` and added it to the top-level `Mutation` bases
  (among the independent apps); discharged the compose anchor. No `Query`
  composition change (`me` is Slice 2).
- `examples/fakeshop/schema_reload.py` — added `"apps.accounts.schema"` to
  `_PROJECT_APP_SCHEMA_MODULES` (among the independent apps, before
  `config.schema`) — the Revision-7 reload fix.
- `examples/fakeshop/test_query/test_auth_api.py` — the live login/logout
  coverage (discharged the Slice-1 anchor; left the Slice-2 anchor).
- `tests/auth/test_mutations.py` — the mirrored package residue (replaced the
  Slice-1 TODO; left the Slice-2 TODO block untouched).

### Tests added or updated

Live — `examples/fakeshop/test_query/test_auth_api.py` (7 tests):

- `test_login_happy_path_returns_user_and_establishes_session` — payload user in
  the `node` slot, empty errors, session established on the client.
- `test_wrong_password_and_unknown_username_are_byte_identical_envelopes` — shape
  equality between the two failure cases (the enumeration guard) + the `__all__`
  envelope.
- `test_inactive_user_login_fails_with_same_envelope` — `is_active=False` → same
  `__all__` envelope.
- `test_logout_reports_prior_session_and_is_idempotent` — `ok:true` authenticated
  / `ok:false` anonymous, session flushed both ways.
- `test_login_payload_still_returns_without_node_selection` — errors-only
  selection succeeds.
- `test_auth_payload_sdl_shapes` — `LoginPayload { node: UserType, errors:
  [FieldError!]! }`, `LogoutPayload { ok: Boolean!, errors: [FieldError!]! }`.
- `test_login_logout_survive_a_registry_clear_rebuild` — the complete-reload path
  (accounts now in `_PROJECT_APP_SCHEMA_MODULES`).

Package-internal — `tests/auth/test_mutations.py` (19 tests): ledger
record/dedupe/conflict/clear + declarations-survive-pre-bind-reset; surface-keyed
bind validation (login-arm auth-specific raise + logout-only exemption + the
login holder's `_primary_type` set at bind); post-finalize factory raise;
sync + async login/logout paths (async via the one boundary); the login gate sees
the attempted username and NOT the password; exact denial strings ("Not authorized
to login UserType." / "Not authorized to logout Session."); async `has_permission`
→ `SyncMisuseError`; sessionless-request edge (Django's own `AttributeError`
propagates).

### Validation run

- `uv run ruff format .` — pass (reformatted the two new test files + the two
  trailing-comma-fixed files; all 308 files formatted).
- `uv run ruff check --fix .` — pass (`All checks passed!`); one E501 on a new
  docstring summary fixed by hand.
- `uv run python scripts/check_trailing_commas.py --fix` — fixed 5 `has_permission`
  / ctor-signature layout violations in `auth/mutations.py` +
  `tests/auth/test_mutations.py` (the custom checker enforces trailing-comma
  explosion COM812 cannot). Re-ran ruff format after.
- `git status --short` classification — every modified file is slice-intended and
  appears in `### Files touched`: `auth/mutations.py`, `mutations/fields.py`,
  `registry.py`, `types/finalizer.py`, `apps/accounts/schema.py`,
  `config/schema.py`, `config/settings.py`, `schema_reload.py`, `test_auth_api.py`,
  `tests/auth/test_mutations.py`. NO unrelated tool churn to revert. The 8 `D`
  deletions of prior-cycle (039) `bld-*.md` / `build-039-*.md` artifacts and the
  untracked `build-040-*.md` plan + this `bld-slice-1-*.md` artifact are Worker 0's
  pre-flight baseline (left alone per the task's baseline note).
- Focused tests (no `--cov*`): `uv run pytest tests/auth/ --no-cov -n0` → 19
  passed; `uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov
  -n0` → 7 passed; `uv run pytest tests/mutations/ --no-cov -n0` → 176 passed (the
  `fields.py` refactor is transparent to `036`/`038`/`039`); `uv run pytest
  tests/test_registry.py tests/filters/test_finalizer.py tests/types/ --no-cov
  -n0` → 497 passed, 2 skipped (the finalizer wiring is safe); `uv run pytest
  examples/fakeshop/test_query/ --no-cov -n0` → 318 passed, 1 skipped, 4 xfailed
  (the accounts install + reload-list change caused no live regressions).
- `uv run python examples/fakeshop/manage.py check` → no issues;
  `makemigrations --check --dry-run` → no changes (accounts is schema-only).

### Implementation notes

- **D12/P1/P2 promotion depth — chose to promote in place, not to a new module.**
  `_lazy_ref` already lived in `mutations/fields.py`; the only genuinely shared new
  piece was the `__signature__`/`__annotations__` attachment, so I promoted a
  single `attach_synthesized_signature(resolver, params, return_annotation)` helper
  there and had both `DjangoMutationField` and the auth dispatcher consume it. This
  is the lowest-churn shape that keeps ONE injector (no new module, no cross-folder
  move); `_synthesized_mutation_signature` was narrowed to return `(params,
  return_annotation)` so the attachment is single-sited in the helper. The
  `fields.py:64` anchor is discharged.
- **The surface-keyed ledger record is a small `_AuthDeclaration` instance** (the
  discretion item): it carries `surface` + normalized `permission_classes` + the
  cached `holder`, and exposes `__name__ = surface` so `make_declaration_registry`'s
  post-finalize reject message (which reads `.__name__`, built for class
  declarations) reads cleanly. `_declare_surface` looks the surface up in the ledger
  BEFORE registering, so identity-dedupe holds (a repeat returns the cached record
  rather than appending a second one), and the conflict raise is keyed on
  `permission_classes` only.
- **The login holder's `_primary_type` is set at bind, not at factory time.** The
  factory synthesizes the holder before the user primary is registrable, so
  `_make_permission_holder("login", None, ...)` starts with `_primary_type=None`;
  `bind_auth_mutations()` sets `record.holder._primary_type = primary` after
  resolving it (the closure sees the mutation because the resolver captures the same
  `record.holder`). The login resolver reads `payload_object_slot(holder._primary_type)`
  at request time (post-bind), so the slot resolves correctly and the denial string
  reads the user type name.
- **D17/P3 boundary helper kept auth-local.** `_run_in_one_boundary(fn)` is the
  auth-local one-boundary wrapper; I did NOT factor the generic
  `run_in_one_sync_boundary` primitive out of the `036` `run_pipeline_async` core
  (spec Decision 10 P3 makes it an explicit "may", not "must", and auth-local is the
  safe default). Consequently the `resolvers.py:1428` `TODO(spec-040 Slice 1)`
  anchor inviting that factoring is intentionally left for a later discharge — see
  Notes for Worker 1.
- **Async tests execute the dispatcher directly.** The `tests/auth/` async tests
  reach `_resolve` via `Mutation.__strawberry_definition__.fields[...].base_resolver.wrapped_func`
  and call it under an async test (so `in_async_context()` is True and the async
  path runs), rather than round-tripping through `await schema.execute` — the
  dispatcher IS the production entry, so this exercises the same path.

### Notes for Worker 3

- No shadow file was used for implementation (the plan pinned the seams precisely;
  the changes are small additions to existing files + one new logic module
  `auth/mutations.py`). `auth/mutations.py` is a new `.py` file with review-worthy
  logic (~300 lines), so per BUILD.md Worker 3 must run `scripts/review_inspect.py`
  on it (`--output-dir docs/shadow`).
- The `mutations/fields.py` refactor (`attach_synthesized_signature` promotion) is
  the only change to an existing `types/`-adjacent hot file; it is behavior-preserving
  for `DjangoMutationField` (176 `tests/mutations/` green) — the SDL is byte-identical.
- Focused-test commands to re-confirm: `uv run pytest tests/auth/ --no-cov -n0`,
  `uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov -n0`,
  `uv run pytest tests/mutations/ --no-cov -n0`. Use `-n0` (pytest.ini forces
  `-n auto`; `-p no:xdist` errors because addopts still passes `-n`).
- Temp-test-if-ambiguous latitude the plan granted Worker 3 (logout-only exemption
  + pinned denial strings under `docs/builder/temp-tests/slice-1/`): both are
  already pinned by `test_logout_only_schema_binds_without_any_user_type`,
  `test_gated_login_denial_names_the_user_type`, and
  `test_gated_logout_denial_reads_session`.

### Notes for Worker 1 (spec reconciliation)

- **`resolvers.py:1428` `TODO(spec-040 Slice 1)` deliberately NOT discharged this
  slice.** The plan's Implementation-discretion item on D17/P3 says the generic
  `run_in_one_sync_boundary` factoring is a spec "may" (Decision 10 P3), and that if
  Worker 2 keeps the boundary auth-local "the anchor stays for a later discharge and
  Worker 1 records the deferral." I kept it auth-local (safe default), so this
  Slice-1-labelled anchor survives. It is the ONLY surviving `TODO(spec-040 Slice 1)`
  anchor in the tree. Flagging for the deferral record: either (a) accept it staying
  and re-label it a later-slice / optional anchor, or (b) route the generic factoring
  through a follow-up. This is not a correctness gap — the auth async paths already
  ride one boundary via `_run_in_one_boundary`.
- No spec gap or conflict surfaced during implementation; every pinned seam resolved
  as the plan described. The `settings.py` `INSTALLED_APPS` install (not itemized in
  the spec's Slice-1 checklist bullet but required, per the plan's step 5) landed as
  planned.

---

## Review (Worker 3)

Reviewed Worker 2's diff for the 10 slice-intended files against the Slice-1 contract
(spec `## Slice checklist` Slice 1; Decisions 5 / 8 / 9 / 10; `## Helper-reuse
obligations (DRY)` D1–D19 + D-N1–D-N3; `## Edge cases`; `## Test plan`; DoD 2/3). Ran
the static inspection helper on `auth/mutations.py`; traced the load-bearing behavioral
claims to the source; ran focused (non-coverage) tests; verified the mechanical
transparency claim for `attach_synthesized_signature`.

### High:

None.

### Medium:

None.

### Low:

#### `_build_auth_field(permission_holder=...)` is a genuinely-unused parameter

`_build_auth_field`'s first positional `permission_holder` is passed by both call sites
(`login_mutation` / `logout_mutation`) but immediately `del`'d with the comment "captured
by the resolver closures, not read here." The resolvers close over the outer
`holder = record.holder`, not over this parameter, so it is dead — the `del` acknowledges
it. It reads as a documentation-of-association marker but adds a no-op argument to the
shared dispatcher-builder's contract (and a `del` line).

```django_strawberry_framework/auth/mutations.py:149
def _build_auth_field(
    permission_holder: type,
    ...
):
    ...
    del permission_holder  # captured by the resolver closures, not read here.
```

Recommended change (non-blocking; Worker 1 may weigh at final verification): drop the
parameter and the `del`, since it is not read; the resolver bodies already capture the
holder they need. Low severity — no behavior impact, purely a minor API/readability nit
on a module-internal helper. **Not blocking acceptance.**

### DRY findings

The DRY spine of this rider build is satisfied — every helper-reuse obligation the plan
named is honored by call, not re-spelled. Verified against the spec `## Helper-reuse
obligations (DRY)`:

- **D1** — every auth resolver reads the request via
  `request_from_info(info, family_label=_AUTH_FAMILY_LABEL)` with ONE module-level
  `_AUTH_FAMILY_LABEL = "AuthMutation"` constant; no re-spelled `info.context.request`
  walk. Confirmed (`auth/mutations.py::_login_body` / `::_logout_body`).
- **D2** — the async-hook guard rides `check_permission` → `reject_async_in_sync_context`
  transitively; no new recourse string. Confirmed live: the async `has_permission` →
  `SyncMisuseError` test passes and the control-flow trace shows no earlier
  short-circuit swallows it (the gate runs before `authenticate`).
- **D3 / P4** — ONE `_make_permission_holder` synthesizes both holders; the
  `_mutation_meta` snapshot is built via `_validate_permission_classes(..., unset_default=())`
  and `check_permission = DjangoMutation.check_permission` bound directly (verified the
  method body reads only `type(self)._mutation_meta.permission_classes`, so the duck-typed
  snapshot suffices — it is not a `_ValidatedMutationMeta`). No three class bodies.
- **D4** — both surfaces gate through `authorize_or_raise`; the denial rides the existing
  `getattr(mutation_cls._primary_type, "__name__", mutation_cls.__name__)` fallback
  (`resolvers.py::authorize_or_raise`). Login denial reads the resolved user type;
  logout reads the holder `__name__` = `Session`. No auth-specific formatter. Exact
  strings pinned by `tests/auth/` and verified passing.
- **D5** — `LoginPayload` / `LogoutPayload` via `build_payload_type` +
  `payload_object_slot` on the existing `mutations.inputs` emit ledger
  (`materialize_mutation_input_class`); **no new `register_subsystem_clear` row in Slice
  1** (grep of `auth/mutations.py` confirms none; the only auth `register_subsystem_clear`
  row lives in the untouched Slice-2 `auth/queries.py` scaffold). `RegisterPayload` never
  named.
- **D8** — login failure uses `field_error("", _BAD_CREDENTIALS)` (empty path →
  `NON_FIELD_ERROR_KEY` = `"__all__"`); never a hard-coded sentinel. Confirmed against
  `resolvers.py::field_error`.
- **D12 / P1 / P2** — the signature-injection idiom is promoted to ONE
  `attach_synthesized_signature(resolver, params, return_annotation)` in
  `mutations/fields.py`; `DjangoMutationField` and the auth dispatcher both consume it;
  `_lazy_ref` reused in place. **Transparency verified mechanically** (see Public-surface
  / relocation-claim note below).
- **D14** — the ledger is a `make_declaration_registry("AuthMutation")` instance; records
  go through `register_auth_mutation`. The surface-keyed `_AuthDeclaration` record doubles
  as the holder cache + conflict state; identity-dedupe is handled by `_declare_surface`'s
  surface-lookup-before-register (the fresh-instance-per-call would otherwise defeat
  `not in store`), documented in the record docstring.
- **D15** — the declaration ledger clears via a `TypeRegistry.clear()` hand row beside
  `clear_mutation_registry` / `clear_form_mutation_registry` (registry.py), **NOT**
  `register_subsystem_clear`. Confirmed the row is a `_clear_if_importable(...,
  clear_auth_mutation_registry, lambda clear: clear())` in the same block as the mutation
  / form declaration clears.
- **D16** — `_resolve_user_primary` uses `registry.get(get_user_model())` (the same getter
  `_resolve_primary_type` uses at `sets.py:1034`) and consults `registry.types_for` only
  to split the no-type vs ambiguous message. "What counts as a primary" stays single-sited.
- **D17 / P3** — ONE `_run_in_one_boundary(fn)` wraps gate-then-work in a single
  `sync_to_async(thread_sensitive=True)`; shared by both async resolvers, no per-field
  copy. Auth-local (the generic-primitive factoring is the deliberately-deferred anchor —
  see Notes for Worker 1).
- **D18 / D19** — grep confirms no `SyncMisuseError` redefinition and no bare
  `inspect.iscoroutinefunction` in `auth/`; `SyncMisuseError` is imported from its public
  path in the test.
- **D-N1** (non-reuse) — login does NO `get_queryset` re-run and NO `refetch_optimized`;
  the payload user is the raw `authenticate()` instance, source-commented at the site.
- **No `AllowAny` class minted** — grep confirms "AllowAny" appears only in
  docstring/comment prose describing the empty-list semantics; Decision 5's prohibition is
  honored.

Repeated-literal scan (shadow overview): `"AuthMutation"` (2x) and `"username"` (2x) are
**not** live duplication — the `"AuthMutation"` occurrences are the constant definition vs.
a human-readable error-message prefix; the `"username"` occurrences are the gate `data`
key (spec-pinned) vs. the GraphQL arg parameter name (semantically distinct; coupling them
would over-abstract). No consolidation warranted.

Register-arm DRY (D6 / D7 / D10 / D11 / D-N2 / D-N3) is Slice-2 scope — `register_mutation`
is still the fail-loud placeholder here; correctly out of Slice-1 review scope.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty** — no change to the
package-root `__all__` / re-export list. This matches spec Decision 3 (auth symbols are
submodule-only, no package-root re-export). `django_strawberry_framework/auth/__init__.py`
is **not** in Worker 2's diff (unchanged scaffold at HEAD; already re-exports the four
factory names — `register_mutation` / `current_user` importable as fail-loud placeholders,
callable-time `NotImplementedError`), so no public-surface drift was introduced by this
slice.

**Relocation / transparency claim verification (D12 / P1 / P2).** Worker 2 claims the
`attach_synthesized_signature` promotion is byte-transparent to `DjangoMutationField`.
Verified mechanically against pristine HEAD (`git show HEAD:.../mutations/fields.py`): the
pre-refactor `_synthesized_mutation_signature` built `annotations = {"info": Info}` and
appended `id` / `data` / `return` conditionally; the new shared helper derives annotations
from `params` where `param.annotation is not inspect.Parameter.empty` — `root` carries no
annotation (excluded in both), `info` carries `annotation=Info` (→ `{"info": Info}`), and
`id` / `data` / `return` carry their lazy refs. The produced `__annotations__` dict is
byte-identical to the pre-refactor dict, and the `inspect.Signature(params,
return_annotation=...)` is unchanged. Corroborated by `tests/mutations/` staying green
(176 passed) — the SDL output is unchanged.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The two
example-project docstring edits in `apps/accounts/schema.py` / `config/schema.py` /
`config/settings.py` / `schema_reload.py` are source-comment provenance updates, not
standing-doc / release-metadata changes.)

### What looks solid

- **Surface-keyed bind (Decision 9).** `bind_auth_mutations()` reads `{record.surface ...}`
  and does only each surface's work: login resolves + validates the primary and
  materializes `LoginPayload`; logout materializes only `LogoutPayload` and never resolves
  the primary (the structural exemption). Verified the orphan-payload guard holds both
  directions — a logout-only ledger materializes no `LoginPayload` (package test
  `test_logout_only_schema_binds_without_any_user_type`), and a temp test confirmed a
  login-only ledger materializes no `LogoutPayload` (temp test, deleted after
  corroborating — behavior already pinned by the reverse-direction package test + the
  aggregated live surface).
- **Bind ordering (Decision 8 / 9).** `types/finalizer.py` places the function-local
  `from ..auth.mutations import bind_auth_mutations` + call AFTER the
  `iter_subsystem_clears()` pre-bind reset loop and BEFORE `bind_mutations()` — the
  load-bearing ordering that keeps the Slice-2 register arm reachable ahead of
  `_resolve_primary_type`'s generic raise. Cycle-safe function-local import mirroring
  `bind_mutations` / `bind_form_mutations`.
- **Declaration-clear hand row (Decision 9 / D15).** In `TypeRegistry.clear()` beside the
  mutation / form declaration clears, NOT `register_subsystem_clear` — so declarations
  survive the pre-bind reset (the retry contract), and because the holder cache + conflict
  state ARE the ledger records, the clear also resets a prior conflicting-`permission_classes`
  raise. Pinned by `test_registry_clear_drains_the_declaration_ledger` +
  `test_declarations_survive_pre_bind_reset_and_both_payloads_materialize`.
- **The one `sync_to_async(thread_sensitive=True)` boundary with the gate INSIDE it
  (Decision 10).** `_run_in_one_boundary(fn)` wraps the whole gate-then-session-work block;
  the async resolvers pass `lambda: _login_body(...)` / `lambda: _logout_body(...)` so the
  permission gate runs on the same worker thread as `authenticate` / `auth.login` /
  `auth.logout`. The `SyncMisuseError` discipline survives (a `sync_to_async` worker is
  itself a sync context) — pinned and passing.
- **Enumeration guard.** The live suite pins wrong-password == unknown-username as a shape
  equality (`test_wrong_password_and_unknown_username_are_byte_identical_envelopes`) and
  inactive-user → same `"__all__"` envelope. The `field_error("", ...)` leaf ctor owns the
  sentinel.
- **Test rigor.** The live suite earns every reachable branch over `/graphql/` HTTP
  (happy path, byte-identical failure envelopes, inactive user, idempotent logout,
  errors-only selection, SDL shapes, complete-reload survival); `tests/auth/` holds only
  genuinely-unreachable residue (gate variants on isolated throwaway schemas with exact
  denial strings, ledger mechanics, sync/async internals, sessionless edge). The
  permission-gate-coverage placement in `tests/auth/` is the documented unreachable-live
  exception (one-declaration-per-process), not a live-first weakening.
- **`in_async_context()` dispatch** in `_build_auth_field::_resolve` mirrors the
  `DjangoMutationField` runtime asymmetry; the async tests exercise the real dispatcher
  entry (`base_resolver.wrapped_func`) under an async test so `in_async_context()` is True.

### Temp test verification

- `docs/builder/temp-tests/slice-1/test_orphan_payload.py` — created to independently
  confirm the reverse orphan-payload direction (login-only materializes no `LogoutPayload`),
  since the package suite pins only the logout-only → no-`LoginPayload` direction. It
  passed. **Disposition: deleted** — the property is already adequately pinned by the
  existing package test (logout-only direction) plus the aggregated live surface (both
  declared); the reverse-direction assertion is a nice-to-have, not a coverage gap. No
  promotion needed; not recorded as a finding.
- Focused pass/fail runs (no `--cov*`): `tests/auth/test_mutations.py` → 19 passed;
  `examples/fakeshop/test_query/test_auth_api.py` → 7 passed; `tests/mutations/` → 176
  passed (transparency regression). `manage.py check` → no issues;
  `makemigrations --check --dry-run` → no changes. `ruff format --check` + `ruff check` on
  all 10 files → clean.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Low/procedural — surviving Slice-1-tagged staged anchor):** the tree
  carries exactly ONE surviving `TODO(spec-040 Slice 1)` anchor —
  `django_strawberry_framework/mutations/resolvers.py:1428`, inviting the optional generic
  `run_in_one_sync_boundary` factoring of the `036` boundary core. Worker 2 deliberately
  kept the auth boundary auth-local (`_run_in_one_boundary`), which spec Decision 10 / D17
  P3 explicitly authorizes as a "may," not a "must." **My anchor-discharge read:** this is
  **acceptable as-is for Slice 1's review** — the async one-boundary discipline is fully
  satisfied auth-locally (verified by the passing async tests), so there is no correctness
  gap. But the anchor is now **mis-tagged**: it names Slice-1 work that the spec permits to
  be deferred indefinitely, and per BUILD.md integration-pass step 6 a `TODO(spec-040 Slice
  1)` anchor surviving the build's end is a finding routed to the owning slice. Two clean
  resolutions for Worker 1 to adjudicate (not resolvable by Worker 2 — needs spec context):
  (a) re-tag it as an optional / later-slice provenance anchor (drop the "Slice 1" label,
  e.g. `TODO(spec-040 optional)` or a `spec-040` provenance note) so the integration-pass
  grep stops flagging it; or (b) delete it — the auth async paths already ride one boundary,
  so the generic-primitive factoring is a genuine "nice-to-have" that can live in a future
  async card without a source anchor. Recommend recording the choice in `### Spec changes
  made (Worker 1 only)` / the deferred-work catalog. This does **not** block
  `review-accepted`.
- **`settings.py` INSTALLED_APPS install** (not itemized in the spec's Slice-1 checklist
  bullet, added per the plan's step 5): landed correctly (`apps.accounts.apps.AccountsConfig`
  in the local-app block); the accompanying `TODO(spec-040 Slice 1)` anchor at that site was
  discharged. AGENTS.md's staged-anchor-removed-in-the-shipping-slice rule makes this
  non-waivable even though the checklist bullet omitted `settings.py`; no reconciliation
  needed beyond noting the checklist-vs-implementation gap is a spec-bullet omission, not a
  build defect.
- **Low finding (unused `permission_holder` param)** above is a minor cleanup Worker 1 may
  fold in during final verification or defer; recorded, non-blocking.

### Review outcome

`review-accepted` — no High or Medium findings; the single Low finding (unused
`_build_auth_field(permission_holder=...)` parameter) is recorded as non-blocking, and the
surviving `resolvers.py:1428` Slice-1-tagged anchor is escalated to Worker 1 (a
spec-authorized deferral needing a re-tag/remove decision Worker 2 cannot make) with no
correctness impact. Every Slice-1 spec-checklist sub-check, every applicable helper-reuse
obligation, and every load-bearing Decision (5 / 8 / 9 / 10) is reflected in the diff and
pinned by a passing test.

---

## Final verification (Worker 1)

**Spec status-line re-verification.** Spec header (lines 1-19) still reads "Planned for
`0.0.13` (card `WIP-ALPHA-040-0.0.13`)" — accurate: the build is mid-flight (Slice 1 of 3);
the version cut and card flip are Slice 3's contract. No header edit needed this spawn.

### Spec slice checklist audit (against Worker 2's diff)

Walked every `- [x]` in the Plan's `### Spec slice checklist (verbatim)` and confirmed the
contract landed in the diff (not just that a box was ticked). All six are genuinely landed;
none un-ticked; none left `- [ ]`:

1. **`auth/__init__.py` re-exports** — present at HEAD (the scaffold already re-exported the
   four factory names; Slice 1 makes `login_mutation` / `logout_mutation` real, register /
   current_user stay fail-loud placeholders). `git diff HEAD -- .../__init__.py` is empty —
   no package-root re-export (Decision 3 honored). ✓
2. **`auth/mutations.py` factories** — `login_mutation()` / `logout_mutation()` land the
   ledger recording (`_declare_surface` → `register_auth_mutation`), the `strawberry.lazy`
   payload forward-refs (`_lazy_ref(_LOGIN_PAYLOAD/_LOGOUT_PAYLOAD, INPUTS_MODULE_PATH)`), the
   sync/async resolver pair over `auth.authenticate` / `auth.login` / `auth.logout`, and the
   `permission_classes=` seam with the AllowAny default (`_validate_permission_classes(...,
   unset_default=())`). ✓
3. **Ledger + `bind_auth_mutations()` in finalizer phase-2.5** — `types/finalizer.py`
   places the function-local `from ..auth.mutations import bind_auth_mutations` + call AFTER
   the `iter_subsystem_clears()` pre-bind reset loop and BEFORE `bind_mutations()` (the
   load-bearing ordering, verified in the diff). Surface-keyed materialization: `LoginPayload`
   via `build_payload_type("Login", object_type=primary, object_slot=payload_object_slot(primary))`
   only when `login` declared; `LogoutPayload` via `object_type=None` only when `logout`
   declared. Declaration ledger cleared by a `_clear_if_importable(..., clear_auth_mutation_registry,
   ...)` hand row in `TypeRegistry.clear()` beside `clear_mutation_registry` /
   `clear_form_mutation_registry` — NOT `register_subsystem_clear` (verified by diff + grep). ✓
4. **Bind validation (Slice-1 scope)** — `_resolve_user_primary()` raises the auth-specific
   `ConfigurationError` naming the fix (`get_user_model()` / `Meta.primary`) for a login-declaring
   schema with no registered user primary, fired from `bind_auth_mutations()` before
   `bind_mutations()` (the ordering). A logout-only ledger binds with no user type resolved
   (structural exemption). Pinned by `test_login_without_user_type_raises_auth_specific_error`
   + `test_logout_only_schema_binds_without_any_user_type`. ✓
5. **fakeshop live surface (same commit)** — `apps/accounts/schema.py` declares
   `UserType(DjangoType)` over `get_user_model()` (`fields=("id","username","email")`,
   `interfaces=(relay.Node,)`) + app-local `Mutation` (`login`/`logout`, AllowAny); composed
   into `config/schema.py`'s top-level `Mutation` bases; `"apps.accounts.schema"` added to
   `schema_reload.py::_PROJECT_APP_SCHEMA_MODULES` among the independent apps (the Revision-7
   reload fix); `settings.py` installs `apps.accounts.apps.AccountsConfig`; live
   `test_auth_api.py` covers happy path / wrong-credential+unknown+inactive envelope /
   idempotent logout / errors-only selection / SDL shapes / registry-clear-rebuild survival. ✓
6. **Mirrored `tests/auth/` residue** — 20 package tests cover ledger record/dedupe/conflict/
   clear + survive-pre-bind-reset, surface-keyed bind validation (login arm + logout-only
   exemption + login-holder primary set at bind), post-finalize factory raise, sync/async
   login+logout paths (one-boundary discipline), gated denials with exact pinned strings, the
   gate seeing the attempted username and NOT the password, async-`has_permission` →
   `SyncMisuseError`, and the sessionless-request edge. ✓

**Checklist audit result: all six boxes correctly ticked; no over-tick, no silent un-tick,
no un-deferred `- [ ]`.**

### DRY check (this slice; no prior accepted slices)

No new duplication. Every helper-reuse obligation the plan named is honored by call, not
re-spelled — verified mechanically against source:

- `authorize_or_raise` (`resolvers.py::authorize_or_raise`) reads
  `getattr(mutation_cls._primary_type, "__name__", mutation_cls.__name__)` — so the logout
  holder (`_primary_type=None`, `__name__="Session"`) yields "Not authorized to logout
  Session." and the login holder reads the resolved user type name. No auth-specific denial
  formatter. ✓
- `field_error("", ...)` normalizes the empty path to `NON_FIELD_ERROR_KEY` (`"__all__"`) —
  no hard-coded sentinel. ✓
- `payload_object_slot` returns `"node"` for Relay types / `"result"` otherwise;
  `build_payload_type` emits both payload shapes from ONE builder. No second payload
  namespace. ✓
- `DjangoMutation.check_permission` (`sets.py::DjangoMutation.check_permission`) reads only
  `type(self)._mutation_meta.permission_classes` and rejects an async hook via
  `reject_async_in_sync_context` — confirming the duck-typed holder synthesized by the ONE
  `_make_permission_holder` suffices (no `_ValidatedMutationMeta`, no three class bodies). ✓
- **Relocation/transparency claim proven mechanically (D12/P1/P2).** Diffed the refactored
  `attach_synthesized_signature` derivation against pristine `git show HEAD:.../fields.py`:
  HEAD seeded `annotations={"info": Info}` then conditionally added `id`/`data`/`return`; the
  promoted helper derives annotations from `params` where `annotation is not
  inspect.Parameter.empty` — `root` (no annotation) excluded in both, `info` → `{"info":
  Info}`, `id`/`data`/`return` carry their refs. Produced `__annotations__` dict and
  `inspect.Signature` are byte-identical for `DjangoMutationField`; corroborated by 175
  `tests/mutations/` green. The "I only promoted it" claim holds under the shell diff. ✓
- Repeated-literal scan: `"AuthMutation"` (constant def vs. error-prefix) and `"username"`
  (gate `data` key vs. GraphQL arg name) are semantically distinct, not live duplication.
  No consolidation warranted. ✓

### Existing tests still pass (focused scope, `--no-cov`)

- `uv run pytest tests/auth/ examples/fakeshop/test_query/test_auth_api.py tests/mutations/
  --no-cov -n0` → **202 passed** (20 auth + 7 live auth API + 175 mutations — the `036`/`038`/
  `039` surfaces stay green; the `fields.py` promotion is transparent).
- Regression belt (finalizer/registry wiring + full live suite): `uv run pytest
  tests/test_registry.py tests/types/ tests/filters/test_finalizer.py
  examples/fakeshop/test_query/ --no-cov -n0` → **815 passed, 3 skipped, 4 xfailed**. No
  regression from the phase-2.5 auth bind, the `TypeRegistry.clear()` hand row, or the accounts
  install + reload-list change.

### Escalation adjudications

**1. Low finding — unused `_build_auth_field(permission_holder=...)` parameter.** The first
positional is passed by both call sites, immediately `del`'d, and the resolvers close over
`record.holder` (not the parameter), so it is dead. **Decision: defer to the cross-slice
integration pass** (not `revision-needed`). Rationale: it is a Low, non-blocking, module-internal
readability nit with zero behavior impact; folding it in now requires a source edit (Worker 2
re-loop) for a cosmetic change, and the integration pass already owns a Worker-2 consolidation
loop where this can land cheaply alongside any other cross-slice cleanup. Recorded in the
deferred-work list below; the integration pass (`bld-integration.md`) will route it to Worker 2
(drop the parameter + the `del`; the resolver bodies already capture the holder they need).

**2. `resolvers.py::run_pipeline_async` `TODO(spec-040 Slice 1)` anchor** (was `resolvers.py:1428`
at plan-write; the anchor invites the OPTIONAL generic `run_in_one_sync_boundary` factoring).
Worker 2 kept the auth boundary auth-local (`_run_in_one_boundary`), which spec **Decision 10 P3
explicitly authorizes as a "may... optional, only if it does not disturb the pinned `036` AR-M4
wording"** (spec lines 2032-2035). **Decision: clean spec-permitted deferral — resolution path
(c).** I edited the SPEC (not source — I cannot edit source) to record the deferral explicitly
under Decision 10 P3, and routed the source-side anchor removal / re-tag to the cross-slice
integration pass, which owns anchor discharge per BUILD.md integration-pass step 6. This is NOT
`revision-needed`: the async one-boundary discipline is fully satisfied auth-locally (verified by
the passing `test_async_login_runs_in_one_sync_boundary` / `test_async_logout_runs_in_one_sync_boundary`
+ `test_async_has_permission_hook_raises_sync_misuse_error`), so there is no correctness gap — the
deferral is of an optional DRY refactor, not of any Slice-1 behavior. The anchor is the ONLY
surviving `TODO(spec-040 Slice 1)` anchor in the tree (all other spec-040 anchors are Slice-2 or
the Slice 1-2 span in `tests/auth/__init__.py`, which are legitimately still open). Recorded in the
deferred-work list; the integration pass will either delete the anchor (the auth paths already ride
one boundary) or re-tag it as a non-Slice-1 provenance note so its grep stops flagging it as an
undischarged Slice-1 obligation.

### Final status

`final-accepted` — all six spec-checklist sub-checks landed in the diff (audited, not
prose-accepted); no new DRY duplication (relocation claim proven byte-transparent); the focused
scope (202) and the regression belt (815) both pass; both escalated items are cleanly resolved
(the Low finding deferred to the integration-pass consolidation loop; the `run_pipeline_async`
Slice-1 anchor a spec-authorized deferral recorded in the spec with source-side removal routed to
the integration pass). No spec edit changed the Slice-1 contract Worker 2 implemented against
(the deferral edit records what already shipped — auth-local was the plan's P3 safe default), so
no Worker-2 adjustment pass is required.

### Summary

Slice 1 ships the auth substrate + `login_mutation()` / `logout_mutation()` as **fixed** field
factories (not `DjangoMutation` subclasses), earned live over `/graphql/`. The surface-keyed
`make_declaration_registry("AuthMutation")` ledger (a `_AuthDeclaration` record doubling as holder
cache + conflict state) records each surface with its normalized `permission_classes`; a
same-permissions repeat is idempotent, a different-permissions repeat raises `ConfigurationError`.
`bind_auth_mutations()` wires into `types/finalizer.py` phase-2.5 in the pinned slot (pre-bind
reset → auth bind → `bind_mutations()`), materializing `LoginPayload` / `LogoutPayload` through the
existing `mutations.inputs` emit ledger only for declared surfaces (login resolves + validates the
user primary with an auth-specific `ConfigurationError`; logout is the model-less structural
exemption). The declaration ledger clears via a `TypeRegistry.clear()` hand row (surviving the
pre-bind emit-ledger reset — the retry contract). Reuse is honored by call throughout:
`authorize_or_raise` (denial via the `_primary_type`-`__name__` fallback → "Not authorized to
logout Session."), `field_error("", ...)` (the `"__all__"` enumeration-guard envelope), one
`_make_permission_holder` (duck-typed holder, no three class bodies), one `_run_in_one_boundary`
(the shared `sync_to_async(thread_sensitive=True)` async boundary), and the promoted
`attach_synthesized_signature` (ONE signature injector shared with `DjangoMutationField`,
byte-transparent). The fakeshop `accounts` app (schema-only `UserType` + login/logout, AllowAny)
lands in the same commit with `"apps.accounts.schema"` in `schema_reload.py` (the Revision-7 reload
fix) and live coverage; `tests/auth/` holds only the genuinely-unreachable residue. `register` /
`current_user` stay fail-loud Slice-2 placeholders; Slice 1 wires only the bind ordering that keeps
their arms reachable.

### Spec changes made (Worker 1 only)

- `docs/spec-040-auth_mutations-0_0_13.md` Decision 10 (lines ~2035, inside the P3 sentence) —
  added a "Slice-1 build note (Worker 1)" recording that Slice 1 took the P3 safe default
  (auth-local `_run_in_one_boundary`), that the optional generic `run_in_one_sync_boundary`
  factoring is deferred (a spec "may," not "must"), and that the `TODO(spec-040 Slice 1)`
  provenance anchor at `mutations/resolvers.py::run_pipeline_async` inviting the factoring is a
  spec-authorized deferral whose source-side removal/re-tag is routed to the cross-slice
  integration pass (BUILD.md integration-pass step 6). Triggered by: Slice 1 escalation item 2
  (the surviving Slice-1-tagged anchor). Reason: record the spec-permitted deferral explicitly so
  the integration-pass anchor grep reads it as an authorized-and-tracked deferral rather than an
  un-discharged obligation. **This edit does NOT change the Slice-1 contract Worker 2 implemented
  against** — it documents what already shipped (auth-local was the plan's P3 safe default), so no
  Worker-2 adjustment pass is triggered.
- No other spec edit. The `settings.py` `INSTALLED_APPS` install (not itemized in the spec's
  Slice-1 checklist bullet but required and landed per the plan's step 5) is a spec-bullet
  omission, not a build defect; the staged anchor at that site was discharged, so no reconciliation
  edit is needed beyond noting it here.

### Deferred-work note (carried to `bld-integration.md` / `bld-final.md` deferred-work catalog)

- **Low — unused `_build_auth_field(permission_holder=...)` parameter** (`auth/mutations.py::_build_auth_field`):
  dead parameter + its `del`; the resolvers close over `record.holder`. Deferred to the
  integration-pass consolidation loop (source edit; Worker-2 owned). Non-blocking, no behavior
  impact.
- **Optional — generic `run_in_one_sync_boundary` factoring + the `mutations/resolvers.py::run_pipeline_async`
  `TODO(spec-040 Slice 1)` anchor** (spec Decision 10 P3 "may"): the auth boundary is auth-local; the
  generic-primitive factoring is deferred (spec-authorized). Integration-pass step 6 owns the
  source-side anchor removal or re-tag. Non-blocking, no correctness gap.

---

## Build report (Worker 2, pass 2)

Slice-1 regression re-loop dispatched by `bld-final.md`: the final-gate `uv run pytest --no-cov`
parallel sweep failed with `DuplicatedTypeName: Type UserType is defined multiple times in the
schema` at the aggregate `config.schema` build in
`examples/fakeshop/tests/test_inspect_django_type.py`. Root cause (per `bld-final.md`): an
order-dependent cross-test pollution — this test file's private `_SCHEMA_MODULES` eviction tuple
listed the six pre-Slice-1 project schema modules but **omitted `apps.accounts.schema`** (the app
Slice 1 added). Under the 8-worker distribution, a worker that had already built the aggregate left
`apps.accounts.schema` stranded (cached, still holding its `UserType`) while the cold-path
`--schema config.schema` re-import re-registered `UserType`, colliding at the aggregate build. Slice
1 had correctly synced the shared `schema_reload._PROJECT_APP_SCHEMA_MODULES` but missed this one
test's private parallel list.

### Files touched

- `examples/fakeshop/tests/test_inspect_django_type.py` — the ONE slice-intended change this pass.
  Added `"apps.accounts.schema"` to the module-level `_SCHEMA_MODULES` eviction tuple (now
  seven modules, matching the shared `schema_reload._PROJECT_APP_SCHEMA_MODULES` set) so the
  cold-path `test_inspect_with_schema_option[config.schema]` strands+restores accounts alongside the
  other five apps rather than leaving it cached-and-unrefreshed. The same accounts entry was added
  to the `_reload_inspect_schema()` bare-name reload loop (before `config.schema`) with a docstring
  note, so both the cold-path eviction list AND the bare-name registry-clear reload path know about
  accounts — the two seams in this file that must mirror the shared reload helper's module set. No
  production code touched; the teardown (`reload_all_project_schemas`) already handled accounts.

### Tests added or updated

- **No new test.** This is a fixture module-list sync: the fix makes an existing test's private
  eviction/reload lists match the accounts app Slice 1 introduced. `bld-final.md` correctly framed
  it as a test-list staleness (Worker-1 does not edit tests; this is Slice-1 re-loop work for
  Worker 2), not new coverage.
- **No sibling private list needed the same edit.** Verified `test_inspect_django_type.py` is the
  sole holder of a private hardcoded project-schema-module list: `test_query/conftest.py` and
  `apps/products/tests/conftest.py` both delegate to `schema_reload.reload_all_project_schemas()`
  (single-sited, already carries accounts); a tree grep for the sibling module names
  (`apps.library.schema` etc.) surfaces only single-app imports, docstring prose, and the two lists
  already synced (this test file + `schema_reload.py`). Nothing else omits accounts.

### Validation run

- **`uv run pytest --no-cov` (full parallel xdist sweep — the ONLY run that reproduces the
  order-dependent regression):** **2816 passed, 4 skipped, 4 xfailed, 0 failed, 0 errors** in
  220.24s. This is the confirming sweep — GREEN. The two prior final-gate setup ERRORs
  (`test_inspect_by_registered_name` / `test_inspect_by_dotted_path`) and the failed
  `test_inspect_with_schema_option[config.schema]` now pass; the `DuplicatedTypeName` regression is
  resolved. The 4 xfailed are the pre-existing `test_mutation_atomicity.py` xfails; the 4 skipped
  are the FAKESHOP_SHARDED-gated tests that do not run under the default invocation. One confirming
  sweep only — no redundant re-runs.
- `uv run ruff format .` — no-op (308 files left unchanged). The standing
  `COM812`-conflicts-with-formatter warning is pre-existing config noise, not a failure.
- `uv run ruff check --fix .` — no-op (`All checks passed!`).
- `git status --short` classification: the ONLY slice-intended (this-pass) change is
  `examples/fakeshop/tests/test_inspect_django_type.py` (the `_SCHEMA_MODULES` /
  `_reload_inspect_schema` accounts sync above); its diff is confined to those two lists + the
  docstring. Everything else in the working tree is NOT this pass's churn and is left untouched per
  the recovery contract: the 8 `D` deletions of prior-cycle (039) `bld-*.md` / `build-039-*.md`
  artifacts; the untracked `build-040-*.md` plan + the three `bld-slice-*.md` / `bld-integration.md`
  / `bld-final.md` artifacts; the spec `.md` + terms `.csv`; the concurrent-writable tracked
  generated files (`db.sqlite3`, `KANBAN.md`/`KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md`); and
  all prior Slice 1/2/3 + integration source/test/doc changes. No unrelated tool churn was
  introduced by this pass (ruff was a no-op), so nothing to revert.

### Implementation notes

- **Fix landed slightly broader than `bld-final.md`'s minimal "one-line `_SCHEMA_MODULES`" note, and
  correctly so.** `bld-final.md` diagnosed the cold-path eviction tuple (`_SCHEMA_MODULES`) as the
  stale list. The as-landed fix also adds accounts to the `_reload_inspect_schema()` bare-name reload
  loop (the registry-clear reload path used by the `test_inspect_by_*` tests). Both seams in this
  file must mirror the shared `schema_reload._PROJECT_APP_SCHEMA_MODULES` module set; syncing only
  the eviction tuple would leave the bare-name path able to strand accounts on a registry-clear.
  Placing accounts before `config.schema` in both matches the "independent apps before the aggregate"
  ordering `schema_reload.py` documents (accounts references only `auth.User`).
- The change is test-fixture plumbing only — no production behavior, no public surface, no SDL, no
  new coverage line. `scripts/review_inspect.py` is not applicable (no new/changed `.py` logic under
  `django_strawberry_framework/`; the touched file is an example-project test).

### Notes for Worker 3

- Re-review scope is narrow: confirm the `_SCHEMA_MODULES` / `_reload_inspect_schema` accounts sync
  in `examples/fakeshop/tests/test_inspect_django_type.py` matches the shared
  `schema_reload._PROJECT_APP_SCHEMA_MODULES` set (both now seven modules incl. accounts, accounts
  before `config.schema`), and that the regression is gone. The confirming evidence is the full
  parallel sweep (2816 passed / 0 failed / 0 errors) — the regression is invisible to any single-file
  or single-worker scope, so re-confirmation (if any) MUST be the full `uv run pytest --no-cov`
  parallel sweep, never a focused run.
- No shadow file used (test-fixture-only change). Prior-pass Slice-1 review findings and DRY spine
  are unchanged by this pass — the auth production surface is byte-identical to pass 1.

---

## Review (Worker 3, pass 2)

Focused re-review of the Slice-1-owned order-dependent regression fix that `bld-final.md`
diagnosed (`DuplicatedTypeName: Type UserType` at the aggregate `config.schema` build under
the 8-worker parallel sweep). Scope: the single pass-2 file
`git diff HEAD -- examples/fakeshop/tests/test_inspect_django_type.py`. No production code,
no permanent-test-logic change is in this pass.

### High:

None.

### Medium:

None.

### Low:

None.

### Fix correctness (root-cause resolution)

- **Both seams in the file now account for `apps.accounts.schema`, and both mirror the
  shared helper's module set.** Verified against the current source:
  - The cold-path eviction tuple `test_inspect_django_type.py #"_SCHEMA_MODULES"` now lists
    `config.schema` + all SIX apps incl. `"apps.accounts.schema"` (line 45). This is the tuple
    `test_inspect_with_schema_option` walks in `for name in _SCHEMA_MODULES: sys.modules.pop(...)` —
    so the cold-path eviction now pops `apps.accounts.schema` too, no longer stranding it cached
    with a registered `UserType` while the `--schema config.schema` re-import re-registers `UserType`.
    Root cause resolved exactly as `bld-final.md` diagnosed.
  - The `_reload_inspect_schema()` bare-name reload loop now reloads
    `("apps.library.schema", "apps.scalars.schema", "apps.accounts.schema", "config.schema")` with
    `apps.accounts.schema` placed **before** `config.schema` (lines 65-70). Dependency-safe:
    `apps.accounts.schema` (verified) declares `UserType` over `get_user_model()` (`auth.User`) and
    imports only the `django_strawberry_framework.auth` factories — it references no other fakeshop
    app, so any position ahead of the aggregate `config.schema` is valid. This is the broader-than-
    the-minimal-`bld-final.md`-note fix, and correctly so: the bare-name registry-clear reload path
    (used by `test_inspect_by_registered_name` / `test_inspect_by_dotted_path`) would otherwise be
    able to strand accounts on its own `registry.clear()`; syncing only the eviction tuple would
    leave the second seam stale.
- **Module-set equivalence with the shared source of truth.** `schema_reload.py
  #"_PROJECT_APP_SCHEMA_MODULES"` carries the six apps (glossary, kanban, accounts, library,
  products, scalars); the test file's `_SCHEMA_MODULES` covers the same six apps + `config.schema`.
  The eviction seam is now a complete superset of the aggregate's registered modules. The narrower
  `_reload_inspect_schema` subset (library + scalars + accounts + config) is the pre-existing
  bare-name-inspection reload shape (it reloads only the apps whose types those tests inspect); adding
  accounts to it is the correct extension of that shape, not a regression of it.
- **Docstring provenance is accurate.** The `_reload_inspect_schema` docstring note (lines 57-62)
  correctly names spec-040 Slice 1, the strand-in-`sys.modules` mechanism, and the
  `DuplicatedTypeName` failure mode — factual inline provenance (no `TODO(` prefix), consistent with
  the shared helper's own docstring rationale.

### Behavior-neutral for the passing case

Confirmed a fixture-hygiene fix, not a test-logic change. The file's own assertions are untouched
(the pass-2 diff is confined to the two module lists + the docstring; `git diff --stat`: 13 insertions,
2 deletions). All 10 tests pass in single-worker isolation (`-n0`), identical to their pre-fix
in-isolation behavior — the fix only makes the reload/eviction *complete*, it does not change what
any test asserts.

### No sibling polluter survives

Grep-confirmed `test_inspect_django_type.py` is the **sole** holder of a private hardcoded
project-schema-module list. `grep -rln "reload_all_project_schemas|_PROJECT_APP_SCHEMA_MODULES|
_SCHEMA_MODULES"` surfaces six files; the two that hold a private list are `schema_reload.py`
(the shared source of truth) and this test file (now synced). Every other harness delegates by
call to `schema_reload.reload_all_project_schemas`:
- `test_query/conftest.py` — `reload_all_project_app_schemas` fixture wraps `reload_all_project_schemas`.
- `apps/products/tests/conftest.py` — same delegation.
- `test_query/test_auth_api.py` / `apps/products/tests/test_schema.py` — call the fixture, no private list.
The remaining grep hits on the sibling module-name strings are single-app imports and docstring prose,
not eviction/reload lists. Nothing else omits accounts.

### Independent full-parallel-sweep confirmation

Ran the ONLY run that reproduces the regression (default xdist, NO `--cov*` flags):

- `uv run pytest --no-cov` → **2816 passed, 4 skipped, 4 xfailed, 0 failed, 0 errors** (143.64s).
  Matches Worker 2's reported counts. The 4 xfailed are the pre-existing `test_mutation_atomicity.py`
  xfails; the 4 skipped are the FAKESHOP_SHARDED-gated tests (do not run under the default invocation).
- Targeted re-confirmation of the three previously-failing nodes under default parallel:
  `test_inspect_with_schema_option[config.schema]` / `[config.schema:schema]`,
  `test_inspect_by_registered_name`, `test_inspect_by_dotted_path` → **4 passed**. The
  `DuplicatedTypeName` collision and the two follow-on setup ERRORs are gone.
- `test_inspect_django_type.py` alone, `-n0` → **10 passed** (behavior-neutral in isolation).

This de-risks Worker 1's gate re-run: the full parallel sweep is independently green.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` shows only the whole-build cumulative
`__version__` 0.0.12→0.0.13 bump (Slice 3's contract), **not** a pass-2 change. The pass-2 fix
touches exactly one file (the example-project test); it changes no `__all__`, no re-export list, no
package surface. No public-surface drift introduced by this pass.

### CHANGELOG sanity

Not applicable; the pass-2 fix did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; the pass-2 fix modified only an example-project test file (no docs/release/KANBAN/
archive surfaces).

### DRY findings

None. The fix reuses the file's existing two-list idiom (it does not introduce a third list, and it
does not fork a parallel helper). The two seams intentionally mirror the shared
`_PROJECT_APP_SCHEMA_MODULES` module set; that the test file keeps its own private lists (rather than
importing the shared tuple) is the pre-existing shape — the eviction seam needs `config.schema`
included and the bare-name seam needs a narrower subset, so neither can consume the shared apps-only
tuple verbatim. Not a new DRY defect introduced by this pass.

### What looks solid

- The fix is the root-cause fix `bld-final.md` prescribed (sync the stale private eviction list with
  the accounts app Slice 1 added), extended correctly to the second in-file seam so both reload paths
  know about accounts. No surface patch, no `pragma no cover`, no test-only masking of a production
  bug — the production auth surface was already correct; the sole defect was a stale test-fixture list.
- The confirming evidence is the full parallel sweep (the only scope that reproduces the regression),
  independently reproduced here at 2816/0/0.

### Temp test verification

None created — the fix is a module-list sync verified directly by the full parallel sweep (the
regression is invisible to any narrower scope, so a temp test would not add signal). No disposition needed.

### Notes for Worker 1 (spec reconciliation)

None. The pass-2 fix is a test-fixture module-list sync with no spec implication. The prior-pass
escalations (the unused `_build_auth_field(permission_holder=…)` Low and the `run_pipeline_async`
`TODO(spec-040 Slice 1)` anchor) were already resolved in the integration consolidation pass per the
build's integration/final artifacts and are unaffected by this pass.

### Review outcome

`review-accepted` — the regression fix is complete (both the eviction seam and the reload seam
account for `apps.accounts.schema`, accounts placed before the aggregate `config.schema`, both
mirroring the shared `schema_reload._PROJECT_APP_SCHEMA_MODULES` module set), correct (resolves the
cold-path `sys.modules.pop` eviction that stranded the accounts module while `config.schema`
re-registered `UserType` → `DuplicatedTypeName`), behavior-neutral for the file's own passing tests,
the sole surviving private schema-module list (every other harness delegates to the shared helper),
and independently confirmed green under the full parallel sweep (2816 passed / 0 failed / 0 errors).
No new findings; public surface unaffected. This signals Worker 0 to return to Worker 1 to re-run the
final test-run gate.
