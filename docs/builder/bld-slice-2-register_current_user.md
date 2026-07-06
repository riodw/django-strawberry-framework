# Build: Slice 2 — `register_mutation` + `current_user`, earned live

Spec reference: `docs/spec-040-auth_mutations-0_0_13.md` (Slice checklist lines 631-674; Decisions 6/7/8/9/10 at 1419-2065; Helper-reuse obligations 2162-2251; Edge cases 2253-2389; Test plan 2390-2521; DoD items 4/5 at 2706-2760)
Status: final-accepted

## Plan (Worker 1)

Register is a **rider, not a fourth flavor** (Decision 6): `register_mutation()` synthesizes (once, cached) a concrete `DjangoMutation` subclass whose `__name__` is pinned to `Register`, over `get_user_model()` with `operation="create"`, `Meta.fields = derive_register_fields(user_model)`, `RegisterInput` via the input-name seam, and **both** `resolve_sync` / `resolve_async` overridden to ride the shared `run_write_pipeline_sync` skeleton with a password-aware `decode_step` / `write_step` pair — because the `036` create pipeline exposes no per-instance write hook and its default `_model_decode_step` / `_model_write_step` would persist the raw password. `current_user()` is a **query** field factory (not a mutation) sharing the Slice-1 fixed-field builder, returning the nullable session actor with no `get_queryset` re-run. Both land in the same commit as the fakeshop `accounts` `register` + `me` surface and the live `test_auth_api.py` round-trip coverage, with the internals residue mirrored into `tests/auth/`.

### DRY analysis

- **Utils inventory checked.** Refreshed `docs/shadow/utils-inventory.md` this pass (no `django_strawberry_framework/utils/` diff was made — regenerated fresh). Relevant candidates confirmed and reused **by call**, not re-spelled:
  - `utils/inputs.py::iter_provided_input_fields` — the single UNSET-strip provided-field walk `_decode_relations` already opens with; the register decode extends this call site through the new exclusion-seam param, never a second walk (D6).
  - `utils/inputs.py::make_input_namespace` — already used by `auth/queries.py` at HEAD to own the `CurrentUserAlias` namespace trio (`_current_user_alias_names`, `materialize_current_user_alias`, `clear_current_user_alias_namespace`); the bind calls `materialize_current_user_alias(...)` rather than hand-`setattr` (D13).
  - `utils/typing.py::is_async_callable` — the partial-aware async-callable predicate for any `async def has_permission` detection distinct from catching a coroutine result (D18); not `inspect.iscoroutinefunction`.
  - `utils/querysets.py::SyncMisuseError` + `reject_async_in_sync_context` — imported from their public path, reused by call through the bound `check_permission`; no new recourse string (D2 / D19).
  - `utils/permissions.py::request_from_info` — the request extraction with the single `_AUTH_FAMILY_LABEL` constant (already defined in `auth/mutations.py` at HEAD), reused by `current_user` (D1).
  - No new utility is justified; nothing under `utils/` needs a new symbol for this slice.
- **Existing patterns reused (write-stack + auth-substrate, all by call).**
  - `mutations/resolvers.py::run_write_pipeline_sync` (resolvers.py:114-222) — the shared create/update skeleton (the `transaction.atomic()` boundary, authorize-before-decode ordering, envelope short-circuits with rollback, `refetch_optimized`→`build_payload` tail). Register supplies ONLY a `decode_step` / `write_step` pair, exactly as the serializer flavor does at `rest_framework/resolvers.py::resolve_serializer_sync` (resolvers.py:921-950) — the canonical mirror for this slice.
  - `mutations/resolvers.py::_model_decode_step` (resolvers.py:1133-1181) — extended (NOT forked) with a new `excluded_input_fields` seam threaded into `_decode_relations` (resolvers.py:225-293); the register decode reuses the construct + AR-H2 `_provided_attr_names`→`_unprovided_exclude` calculation (resolvers.py:836-895), and returns the 4-tuple `(user, m2m_assignments, exclude, raw_password)` (D6).
  - `mutations/resolvers.py::_model_write_step` (resolvers.py:1184-1211) — the shared `full_clean`→`save`→M2M tail (`_full_clean_or_field_errors` resolvers.py:1294-1314, `save_or_field_errors` resolvers.py:1317-1333). Register's write step delegates these; only `validate_password` + `set_password` are auth-specific (D7).
  - `mutations/resolvers.py::field_error` (resolvers.py:921-951) — the leaf ctor. Register's password error is `field_error("password", exc.messages, codes=[...])` DIRECTLY, deliberately NOT `validation_error_to_field_errors` (resolvers.py:971-996), whose non-dict branch keys a list-style `ValidationError` to `"__all__"` (D8 / D-N2).
  - `mutations/resolvers.py::refetch_optimized` (resolvers.py:1034+) — the by-pk-without-visibility own-write re-fetch; register rides it via the skeleton tail (D9).
  - `mutations/sets.py::DjangoMutation` (sets.py:739-1015) — the base the rider subclasses: inherits `_validate_meta`, `build_input`, `check_permission`, and the `resolver_seams` seam pattern (sets.py:317-389). Register overrides `input_type_name` (sets.py:921-951) to pin `RegisterInput`, `_resolve_model` to return the user model, and both resolver seams to the register sync/async entries (the serializer flavor's `rest_framework/sets.py:782` `resolver_seams(...)` assignment is the exact idiom).
  - `mutations/sets.py::make_declaration_registry` / `_validate_permission_classes(..., unset_default=())` — already used by `auth/mutations.py` at HEAD; register re-uses `_declare_surface`-style conflict/cache logic keyed on `permission_classes` only. The auth-ledger `register` (`register_auth_mutation`) + the mutation-ledger `register` (`mutations.sets.register_mutation`) are the two ledgers every register call re-records into (D14).
  - `mutations/inputs.py::build_payload_type` + `payload_object_slot` + `materialize_mutation_input_class` (inputs.py:563-620) — register's `RegisterPayload` is minted by the UNCHANGED `_bind_mutation` (sets.py:1304-1335) because the rider is an ordinary `DjangoMutation`; `bind_auth_mutations()` materializes NO payload for register — it only resolves+validates the user primary (Decision 9 register arm). `RegisterPayload` is never named explicitly (D5).
  - `mutations/fields.py::DjangoMutationField` (fields.py:222-269) — register is exposed through the UNCHANGED factory internally (`return DjangoMutationField(Register, ...)`); `_synthesized_mutation_signature` (fields.py:168-219) builds `RegisterInput` + `RegisterPayload` refs from `input_type_name` + `__name__` for free (D10/D11).
  - `mutations/fields.py::_lazy_ref` + `attach_synthesized_signature` (fields.py:121-165) — already the shared machinery Slice 1 promoted; `current_user()` reuses them for its `CurrentUserAlias | None` return ref through the Slice-1 `_build_auth_field` helper (D12/P1/P2).
  - `auth/mutations.py::_build_auth_field` / `_make_permission_holder` / `_declare_surface` / `_run_in_one_boundary` / `_resolve_user_primary` / `bind_auth_mutations` (Slice 1, mutations.py:111-311) — `current_user()` is a NEW fixed-field surface that reuses ALL of these; the register arm extends `bind_auth_mutations()` and `_resolve_user_primary` reuse.
  - Fakeshop live-test harness: `examples/fakeshop/test_query/test_auth_api.py` (Slice 1) — `_post` / `_data` helpers, the `reload_all_project_app_schemas` fixture, and `create_users` / `TEST_USER_PASSWORD` first-line seed. Slice 2 appends register/me tests to this file, reusing the harness.
  - Package-test harness: `tests/auth/test_mutations.py` (Slice 1) — `_isolate_registry`, `_declare_user_primary`, `_request_with_session`, `_info_for`, `_field_resolver`, `_DenyAll`, the throwaway-schema + isolated-`registry.clear()` pattern. Slice 2 appends register/current_user internals here and to `tests/auth/test_queries.py`.
- **New helpers justified (single responsibility each).**
  - `auth/mutations.py::derive_register_fields(user_model) -> tuple[str, ...]` — the ONE directly-testable field-tuple derivation: `USERNAME_FIELD` first, each distinct `REQUIRED_FIELDS` entry in declaration order, then `password` exactly once, deduplicated. Takes the model as an argument (never `get_user_model()` inline) so the default AND a custom-`USERNAME_FIELD`/`REQUIRED_FIELDS` test-scoped model are testable with no `AUTH_USER_MODEL` swap. Unknown/non-editable/reverse names are rejected by DELEGATING to `editable_input_fields` (inputs.py:182-254) at bind — never a re-implemented check. Single responsibility: derive the register `Meta.fields` tuple.
  - `mutations/resolvers.py` exclusion seam: a small reusable `excluded_input_fields` parameter (default an empty frozenset) threaded through `_model_decode_step` → `_decode_relations`. Its single responsibility: capture an excluded provided input value out of the constructed model attrs **while preserving its provided-marker** (the value is recorded in an `excluded_values` map and `continue`d before scalar/relation/null validation, but STILL counts as provided for the AR-H2 `_unprovided_exclude` calculation, so `full_clean` still validates the `password` column against the hash). Discharges the `resolvers.py:1158` staged anchor's own pseudocode: "add a small reusable exclusion seam here and in `_decode_relations`". Serves register today; returns for free if a future flavor needs the same "protected input value" pattern.
  - `auth/mutations.py::register_mutation()` body: synthesizes+caches the `Register` rider, its register sync/async resolver entries, and the register `decode_step`/`write_step` pair. The write step's ONLY auth-specific logic is `validate_password(raw, user)` → `field_error("password", ...)` on failure → `set_password(raw)` before `full_clean`.
  - `auth/queries.py::current_user()` body: the query field factory (fixed-field, sharing the Slice-1 auth helper) + the `bind_auth_mutations()` call to `materialize_current_user_alias("CurrentUserAlias", primary_type)` in the current_user arm.
- **Duplication risk avoided.**
  - The classic drift trap is **forking the decode walk** to strip `password`. The plan forbids a second `iter_provided_input_fields` copy: the exclusion is a parameter on the existing `_model_decode_step`/`_decode_relations` path (D6). A forked walk is exactly where the UNSET/raw-`None`-vs-omitted rule drifts.
  - The second trap is **re-keying the password error through the generic mapper**. `validate_password` raises a list-style `ValidationError` (no `error_dict`); routing it through `validation_error_to_field_errors` keys it to `"__all__"`. The plan pins the DIRECT `field_error("password", ...)` at the `validate_password` call site (D8 / D-N2). A helper-level test asserts the key is `password`, not `"__all__"`.
  - The third trap is **adding a payload-name or per-instance-write-hook seam to the `036` base** for register. The plan pins `__name__="Register"` so the unchanged machinery emits `RegisterPayload` (no payload-name seam), and rides the existing per-flavor `resolve_sync`/`resolve_async` seam (no new base hook). The `036`/`038`/`039` surfaces must stay byte-unchanged — `tests/mutations/` green untouched.
  - The fourth trap is **register wiring relation-visibility helpers** (`relation_kind` / `is_forward_many_to_many` / `visible_related_object(s)`) preemptively — the narrowed `Meta.fields` has no relation inputs, so they must NOT be added; a source comment marks this deliberate non-reuse (D-N3).
  - The fifth trap is **`current_user`/`login` scoping through `get_queryset`** — they return the actor, not a lookup, so the visibility helpers must NOT be wired; a source comment marks this (D-N1).
  - The sixth trap is a **stale conflict raise surviving a reload**: the holder/rider cache + conflict state ARE the declaration ledger (drained by the `TypeRegistry.clear()` hand row), so a post-clear re-declaration with a different `permission_classes` mints fresh — the reload-idempotence test pins this.

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against current source before editing (Slice 1's diff is in the working tree, so line numbers already reflect it).

1. **Exclusion seam in `mutations/resolvers.py`** (discharges the `resolvers.py:1158` `TODO(spec-040 Slice 2)` anchor — replace it with `spec-040`/`DONE-040` provenance, do not leave a TODO):
   - `_decode_relations(model, data, info, *, excluded_input_fields=frozenset())` — inside the existing `iter_provided_input_fields` loop, when `python_name in excluded_input_fields`, record `excluded_values[python_name] = value` and `continue` BEFORE the m2m/fk/scalar/null branches. Return `(scalar_and_fk_attrs, m2m_assignments, excluded_values, error)` (add the map to the return tuple). The excluded field's value never enters `scalar_and_fk_attrs`, so `model(**scalar_and_fk_attrs)` never receives it.
   - `_model_decode_step(model, data, info, *, instance, excluded_input_fields=frozenset())` — thread the param down; compute `provided = _provided_attr_names(...)` from `scalar_and_fk_attrs`/`m2m_assignments` AS TODAY, then **add back** the excluded names so the AR-H2 `_unprovided_exclude` still counts them provided (the marker-preservation requirement — the excluded field must NOT be dropped from `full_clean` validation). The default model path (`excluded_input_fields=frozenset()`, `excluded_values={}`) is byte-behavior-identical to today; a **relocation/no-regression check** must prove the model flavor's decode is unchanged (verify against `git show HEAD:.../resolvers.py` per Worker-1 final-verification discipline).
   - Provide a way for `_model_decode_step` to return the excluded values to a caller that asks (the register decode step needs `excluded_values["password"]`). Worker-2 discretion on the exact return shape when `excluded_input_fields` is non-empty (see discretion items).
2. **`derive_register_fields` in `auth/mutations.py`.** `derive_register_fields(user_model) -> tuple[str, ...]`: `(user_model.USERNAME_FIELD, *unique(user_model.REQUIRED_FIELDS), "password")`, deduped preserving order (a `REQUIRED_FIELDS` entry repeating `USERNAME_FIELD` or `password` appears once). Do NOT validate here — the bind's `editable_input_fields` (via the standard `Meta.fields` path) rejects unknown/non-editable/reverse names naming field+model. Default user model → `("username", "email", "password")`.
3. **`register_mutation()` in `auth/mutations.py`** (replaces the `mutations.py:425` `NotImplementedError` stub + its `TODO(spec-040 Slice 2)` block — discharge the anchor):
   - Normalize `permission_classes` via `_validate_permission_classes(_REGISTER, permission_classes, unset_default=())`; look up the `register` surface in the auth ledger. A same-`permission_classes` repeat returns the cached record (→ the cached `Register` rider); a different-`permission_classes` repeat raises `ConfigurationError` (the conflict, keyed on `permission_classes` ONLY — presentation kwargs excluded). Reuse the Slice-1 `_declare_surface` conflict/cache shape (extend it for the `register` surface, which additionally caches a synthesized rider class, not just a holder).
   - On first declaration, synthesize the cached `Register` rider: `type("Register", (DjangoMutation,), {...})` with a nested `Meta` (`model = get_user_model()`, `operation = "create"`, `fields = derive_register_fields(get_user_model())`, `permission_classes = <normalized>`), `input_type_name` overridden to return `"RegisterInput"`, and `resolve_sync`/`resolve_async` overridden to the register sync/async entries. Pin `__name__ = "Register"` so `_bind_mutation` emits `RegisterPayload` with no name seam. (The `DjangoRegisterMutation` name is reserved for the follow-on subclassable base — do NOT use it for the concrete class.)
   - Register sync entry: call `run_write_pipeline_sync(Register, info, data, id, decode_step=<register decode>, write_step=<register write>)` — the serializer flavor's `resolve_serializer_sync` (resolvers.py:921-950) is the exact mirror. Register async entry: `make_resolver_entries(<positional sync body>)` async half (the serializer `_run_serializer_pipeline_sync` + `make_resolver_entries` pattern, resolvers.py:974-998) so the ONE shared `run_pipeline_async` boundary is reused. These entries live wherever Worker 2 finds cleanest (auth-local module-level functions, or an auth resolvers seam) — discretion item.
   - Register decode step: `_model_decode_step(model, data, info, instance=None, excluded_input_fields=frozenset({"password"}))`, then append the captured raw password → return `(user, m2m_assignments, exclude, raw_password)` (the 4-tuple mirroring the model 3-tuple with the password appended fourth).
   - Register write step: unpack the 4-tuple; run `django.contrib.auth.password_validation.validate_password(raw_password, user)` — on `ValidationError`, `return [field_error("password", exc.messages, codes=[leaf.code for leaf in exc.error_list if leaf.code])]` (DIRECT, not the generic mapper); then `user.set_password(raw_password)` BEFORE delegating `full_clean`/`save`/M2M to the shared `_model_write_step` tail (via the `(user, m2m_assignments, exclude)` 3-tuple). Add the D-N2 source comment ("NOT `validation_error_to_field_errors` — it keys list-style errors to `__all__`") and the D-N3 source comment ("no relation-visibility helpers — the narrowed `Meta.fields` has no relation inputs").
   - Every call (cached or not) re-records into BOTH ledgers: the mutation ledger (`register_mutation` from `mutations.sets`, so `bind_mutations()` re-binds the rider) AND the auth ledger (`register_auth_mutation`, so `bind_auth_mutations()`'s Decision-8 validation still covers register). Both are identity-deduped, so live ledgers no-op and a post-`registry.clear()` re-declare re-appends to both. Do NOT write the auth-ledger record once behind the cache guard — that regresses the reload path.
   - Return `DjangoMutationField(Register, description=..., deprecation_reason=..., directives=...)`.
   - A call after `finalize_django_types()` raises the standing declare-after-finalize `ConfigurationError` (owned by the ledger `register`, not re-implemented).
4. **`current_user()` in `auth/queries.py`** (replaces the `queries.py:33` `NotImplementedError` stub + the `queries.py:17` bind-materializer `TODO(spec-040 Slice 2)` comment — discharge both anchors):
   - Share the Slice-1 fixed-field machinery: normalize `permission_classes` (AllowAny unset default), declare/dedupe/conflict-check a `current_user` surface in the auth ledger, synthesize a permission holder via `_make_permission_holder` (holder `operation="current_user"`; `_primary_type` set at bind), inject a `Optional[Annotated["CurrentUserAlias", strawberry.lazy(AUTH_QUERIES_MODULE_PATH)]]` return ref built by `_lazy_ref("CurrentUserAlias", AUTH_QUERIES_MODULE_PATH)` through `_build_auth_field` / `attach_synthesized_signature`, and return `strawberry.field(...)`. `current_user` takes NO GraphQL args (`params=[]`).
   - Resolver body: `request = request_from_info(info, family_label=_AUTH_FAMILY_LABEL)`; `user = request.user`; `instance = user if user.is_authenticated else None` (the `is_authenticated` access forces the lazy user); `authorize_or_raise(holder, info, "current_user", data=None, instance=instance)` FIRST — a denial is a top-level `GraphQLError`; then return `instance` (the authenticated actor, or `None`). NO `get_queryset` re-run, NO optimizer re-fetch — add the D-N1 source comment.
   - Async path: reuse `_run_in_one_boundary` so the gate (whose `instance=request.user` argument forces the lazy object) AND the lazy-user forcing run inside ONE `sync_to_async(thread_sensitive=True)` worker — no `SynchronousOnlyOperation` leak (Decision 10).
   - Because `current_user` is user-typed, extend `bind_auth_mutations()` in `auth/mutations.py`: add the `current_user` arm — resolve+validate the user primary (the current_user-arm message, pinned distinct from login's), set the holder's `_primary_type`, and call `materialize_current_user_alias("CurrentUserAlias", primary)` (through the D13 trio, NOT hand-`setattr`). Also add the `register` arm — resolve+validate the user primary (the register-arm message), then leave `RegisterInput`/`RegisterPayload` to `bind_mutations()`. Both arms reuse `_resolve_user_primary()` (the D16 `registry.get` getter), so only the raise MESSAGE differs per surface. Keep the surface-keyed structure (a logout-only schema still resolves no primary).
5. **`auth/__init__.py`** already re-exports `register_mutation` / `current_user` (present at HEAD) — no change needed; confirm they now resolve to real implementations (the placeholders are replaced in-place). No package-root re-export (Decision 3).
6. **Fakeshop `accounts` live surface** (`examples/fakeshop/apps/accounts/schema.py`) — discharge the `schema.py:21` `TODO(spec-040 Slice 2)` anchor: add `me = current_user()` to a `Query` block (new `@strawberry.type class Query`) and `register = register_mutation()` to the existing `Mutation` block; import `current_user` / `register_mutation` from `django_strawberry_framework.auth`. The `Query` block must be composed into `config/schema.py`'s aggregate Query (verify `config/schema.py` wires the accounts Query — Slice 1 wired Mutation + the accounts module into `_PROJECT_APP_SCHEMA_MODULES`; confirm the Query side is present or add it). The `UserType` selection stays `("id", "username", "email")` (Decision 8 caution — password/privilege columns off the read surface).
7. **Live tests** — append to `examples/fakeshop/test_query/test_auth_api.py`: the register→login→`me`→logout round trip on a fresh username (assert the stored password is hashed: `check_password(raw)` true, raw string NOT in the DB column); duplicate-username envelope keyed to `username`; weak-password envelope keyed to `password` (assert the key is `password`, NOT `"__all__"`, with fakeshop's four validators' messages); anonymous `me: null`. First line of every test is `create_users(N)`.
8. **Package tests** — append the internals residue to `tests/auth/test_mutations.py` (register rider) and `tests/auth/test_queries.py` (`current_user`); discharge the `tests/auth/test_queries.py:3` and `tests/auth/__init__.py:3` anchors (fill the Slice-2 residue, remove the `TODO(spec-040 …)` provenance TODOs). See Test additions.
9. **Anchor sweep.** After the above, `grep -rEn 'TODO\(spec-040 Slice 2' .` must be clean. The only surviving spec-040 anchor allowed at Slice-2 close is `resolvers.py::run_pipeline_async`'s `TODO(spec-040 Slice 1)` (the optional generic-boundary factoring, spec-authorized deferral routed to the integration pass per Slice-1's memory). Do NOT discharge or touch that Slice-1 anchor here.

### Test additions / updates

Live (`examples/fakeshop/test_query/test_auth_api.py`, primary — append; each test's first line is `create_users(N)`):
- `test_register_login_me_logout_round_trip` — register a fresh username via `register(data:)`, assert the created user in the payload slot + empty errors; login as that user; `me` sees the user; logout; `me` → null. Then assert `User.objects.get(username=...).check_password(raw)` is True AND the raw password string is not the stored `.password` column value (hashed-storage).
- `test_register_duplicate_username_envelope` — register an already-seeded username; assert `errors` keyed to `username` (the model `full_clean` unique check), payload slot null.
- `test_register_weak_password_envelope` — register with a weak password (e.g. `"12345"`); assert `errors` keyed to `password` with MULTIPLE messages (fakeshop's `MinimumLengthValidator` / `CommonPasswordValidator` / `NumericPasswordValidator`), explicitly asserting the key is `password` and NOT `"__all__"`.
- `test_anonymous_me_returns_null` — no login; `me` → null (never an error).
- SDL assertion: `RegisterInput { username: String! email: String password: String! }` (email optional per `input_field_required`) and `RegisterPayload` shape as pinned in User-facing API; do NOT encode the Relay-only `node` slot name as the generic contract.

Package-internal (`tests/auth/test_mutations.py`, append — the register-rider residue):
- `derive_register_fields` called DIRECTLY: the default user model → `("username", "email", "password")`; a test-scoped model with a custom `USERNAME_FIELD` (e.g. `email`) + custom `REQUIRED_FIELDS` → the derived tuple (dedup + order); and the unknown/non-editable rejection delegating to `editable_input_fields` (asserted at bind, message names field+model). Use a test-scoped model passed as the argument — NO second Django project, NO `AUTH_USER_MODEL` swap.
- The exclusion-seam helper test (at the `_model_decode_step` / `_decode_relations` seam level): `password`'s value is captured out of the constructed attrs, its provided-marker is PRESERVED (the AR-H2 `_unprovided_exclude` still counts `password` as provided — so it is NOT in the `full_clean` exclude), and `password` is absent from `model(**scalar_and_fk_attrs)`. Three assertions: value captured, marker preserved, attr absent.
- Factory cache identity: two same-`permission_classes` `register_mutation()` calls return fields whose synthesized `Register` rider is the SAME class object; a different-`permission_classes` second call raises `ConfigurationError`; a repeat differing only in `description`/`deprecation_reason`/`directives` returns the cached rider (never raises — key is `permission_classes` only).
- Plaintext-never-persisted on BOTH sync AND async register resolver paths (separate overrides, independently regressable): drive the register sync resolver + the register async resolver; assert the created user's `check_password(raw)` is True, the stored `.password` != raw, and (unit) the model decode never receives `password` in `scalar_and_fk_attrs`. Assert hash-before-`full_clean` ordering (the `password` column validates against the hash, not the raw input).
- `validate_password(password, user)` receives the CONSTRUCTED instance (so `UserAttributeSimilarityValidator` can reject `password == username`); the validator→envelope mapping shape is a `password`-keyed leaf, NOT `"__all__"`.
- Reload-idempotence cycle: finalize → `registry.clear()` → re-declare → finalize; assert `register` (and `login`/`logout`/`me`) present in the second schema (the every-call re-register on both ledgers), AND — for a no-`UserType` schema — the second finalize STILL fires the register-arm auth-specific error (not the generic `_resolve_primary_type` one), AND a prior conflicting-`permission_classes` raise does NOT survive the clear (a post-clear re-declare with a different gate succeeds with a fresh rider).
- Register-arm no-`UserType` error message pinned EXACTLY and distinct from login's (`bind_auth_mutations()` fires it ahead of `bind_mutations()`); register-only surface-keyed bind (register declared, no login/logout — assert its payloads are not orphaned by the login/logout arms).
- Register gate variant on an isolated throwaway schema: a `register_mutation(permission_classes=[DenyAll])` denies with the top-level `GraphQLError` and the pinned denial string (register's holder resolves the user type name; `authorize_or_raise` runs BEFORE decode/write).

Package-internal (`tests/auth/test_queries.py`, fill — the `current_user` residue):
- The `CurrentUserAlias` namespace materializes through `make_input_namespace` (its `materialize_fn`/`clear_fn` trio); its clear is a pre-bind `register_subsystem_clear` row (drained by the pre-bind reset, NOT `TypeRegistry.clear()`).
- The injected resolver return annotation resolves to `UserType | None` (SDL `me: UserType`) after bind.
- Sync `current_user`: authenticated → the actor; anonymous → null (AllowAny default); NO `get_queryset` re-run / no optimizer re-fetch (assert the returned object IS `request.user`, no extra query).
- Async `current_user` forces `request.user` inside ONE sync boundary — including an async `me` under a permission gate whose `instance=request.user` argument forces the lazy object inside the boundary: assert NO `SynchronousOnlyOperation` leaks.
- Current-user-arm no-`UserType` error pinned distinct from login's and register's; current-user-only surface-keyed bind (only the `CurrentUserAlias` materializes, no login/logout payloads).
- Gated `me`: an `IsAuthenticated`-style gate denies an anonymous caller with the `GraphQLError` (distinct from the AllowAny default's anonymous `null`); on an isolated throwaway schema with an explicit `registry.clear()` between the default and gated declarations.

Cross-cutting (Worker 2 must run before setting `built`, per Worker-1 "Example-model field changes / no-regression" guidance):
- A full `uv run pytest tests/ --no-cov` sweep (not just the focused scope) is prudent given the resolvers.py seam edit touches the shared model decode path — the `036`/`038`/`039` surfaces must stay green untouched. `tests/mutations/` MUST stay green (the register rider must not perturb the model flavor's seam defaults). Worker 3 confirms via reading the diff against the spec; the final gate runs the full sweep.
- Temp/scratch tests: none required beyond the above; Worker 3 may use `docs/builder/temp-tests/slice-2/` to spot-check the exclusion seam's marker-preservation if it wants a focused reproduction, and should note disposition.

### Implementation discretion items

Assessed and delegated to Worker 2 (equivalent-shape / naming / independent-order choices; NOT architectural):
- The exact placement of the register sync/async resolver entries and the decode/write step pair: auth-local module-level functions in `auth/mutations.py`, or a small `auth/` resolvers seam. Both are valid; pick the one that keeps `register_mutation()` readable and mirrors the serializer flavor's split cleanly. (The seam CHOICE — riding `run_write_pipeline_sync` with a decode/write pair — is fixed by the spec; only the file/function layout is discretionary.)
- The return shape of `_model_decode_step` / `_decode_relations` when `excluded_input_fields` is non-empty (whether the excluded-values map is always in the return tuple, or only threaded when the param is non-empty). Keep the default (empty) path byte-behavior-identical to today for the model flavor; the register caller must be able to read `excluded_values["password"]`. Worker 2 picks the cleanest reuse-preserving shape.
- The private constant name for the register surface token (`_REGISTER = "register"`) and the current_user token (`_CURRENT_USER = "current_user"`), named once beside the Slice-1 `_LOGIN` / `_LOGOUT`.
- Whether the `register` arm and `current_user` arm in `bind_auth_mutations()` share a small local "resolve+validate+set-holder-primary" closure or inline each — as long as `_resolve_user_primary()` stays the single getter and the per-surface raise MESSAGE is distinct (login / register / current_user), and the surface-keyed structure (logout resolves no primary) is preserved.
- The exact weak-password value in the live test (any string tripping ≥2 of fakeshop's four validators, so the "multiple messages" assertion is genuine).

If any of these turns out to require an architectural decision (e.g. the exclusion seam cannot preserve the provided-marker without changing the model flavor's behavior), STOP and escalate — do not resolve it as discretion.

### Spec slice checklist (verbatim)

- [x] **Slice 2 — `register_mutation` + `current_user`, earned live**
  - [x] `auth/mutations.py` grows `register_mutation()` — synthesizing (and caching)
        a [`DjangoMutation`][glossary-djangomutation] subclass whose `__name__` is
        pinned to `Register` (so the unchanged machinery emits `RegisterPayload` —
        no payload-name seam) over `get_user_model()`,
        `operation = "create"`, `Meta.fields` narrowed to
        `(USERNAME_FIELD, *REQUIRED_FIELDS, "password")` via the directly-testable
        `derive_register_fields(user_model)` helper (`email` optional per
        `input_field_required`), **overriding `resolve_sync` / `resolve_async`** to
        ride `run_write_pipeline_sync` with the password-aware step pair (the
        `decode_step` captures `password` through the provided-marker-preserving
        exclusion seam and returns
        `(user, m2m_assignments, exclude, raw_password)`; the write step runs
        `django.contrib.auth.password_validation.validate_password(raw_password, user)`
        — failures → `password`-keyed [`FieldError`][glossary-fielderror-envelope]s
        — then `set_password(raw_password)` **before** `full_clean()` / `save()`; the
        `036` pipeline has no per-instance write hook to reuse), with **every**
        same-`permission_classes` factory call re-registering the cached rider into the mutation
        ledger (identity-deduped; reload-safe) and a conflicting-`permission_classes`
        second call raising [`ConfigurationError`][glossary-configurationerror]
        ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
  - [x] `auth/queries.py` — the `current_user()` field factory: nullable
        session-actor return typed via a bind-materialized lazy alias, **no**
        [`get_queryset`][glossary-get_queryset-visibility-hook] re-run
        ([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)).
  - [x] **In the same commit:** the fakeshop live surface grows `register` + `me`
        fields and [`test_auth_api.py`][test-query-readme] covers the full
        register → login → `me` → logout round trip, the duplicate-username
        envelope, the weak-password envelope (fakeshop's
        `AUTH_PASSWORD_VALIDATORS`), and the anonymous `me → null` case.
  - [x] Mirrored package tests under `tests/auth/` for the internals (the
        password-hash write step with the **plaintext-never-persisted assertion on
        both the sync and async paths**, the validator → envelope mapping shapes
        (a `password`-keyed leaf, **not** the `"__all__"` sentinel the generic
        `validation_error_to_field_errors` mapper produces for a list-style error),
        the exclusion-seam provided-marker test, the factory cache identity, the
        **reload-idempotence cycle** (finalize → `registry.clear()` → re-declare →
        finalize, `register` present in the second schema; a prior
        conflicting-`permission_classes` raise does not survive the clear), the
        register-arm / current-user-arm no-`UserType` error messages (pinned
        distinct from login's — the coverage moved here from Slice 1, where these
        factories do not yet exist) plus the register-only / current-user-only
        surface-keyed binds, and `derive_register_fields` for the default AND a
        custom-`USERNAME_FIELD` / custom-`REQUIRED_FIELDS` test-scoped model).

---

## Build report (Worker 2)

### Files touched

Slice-intended source (grew Slice-1's landed files further, as the plan expected):
- `django_strawberry_framework/mutations/resolvers.py` — added the reusable exclusion seam: `_decode_relations(..., excluded_input_fields=frozenset())` now captures a protected provided field into an `excluded_values` map (returns a 4-tuple `(scalar_and_fk_attrs, m2m_assignments, excluded_values, error)`); `_model_decode_step(..., excluded_input_fields=frozenset())` threads it, adds the excluded names back to the AR-H2 `provided` set (marker preservation), and appends the `excluded_values` map to a 4-tuple ONLY when the seam is used (the default empty path stays a byte-identical 3-tuple). Discharged the `resolvers.py:1158` `TODO(spec-040 Slice 2)` anchor.
- `django_strawberry_framework/auth/mutations.py` — `derive_register_fields(user_model)`, the register decode/write steps (`_register_decode_step` / `_register_write_step`), the register sync body + `make_resolver_entries` pair (`_run_register_pipeline_sync`, `_resolve_register_sync` / `_resolve_register_async`), the `Register` rider synthesizer (`_synthesize_register_rider`, with a `build_input` override pinning `RegisterInput`), the register surface declaration (`_declare_register_surface`, caching the rider on `_AuthDeclaration.rider`), and the real `register_mutation()`. Extended `bind_auth_mutations()` with the `current_user` + `register` arms (a shared `_complete_user_typed_surface` closure) and `_resolve_user_primary(surface_label=...)` for the per-surface distinct message. Added `_REGISTER` / `_CURRENT_USER` / `_PASSWORD` constants. Discharged the `mutations.py:425` stub anchor.
- `django_strawberry_framework/auth/queries.py` — the real `current_user()` fixed query field factory (shares the Slice-1 auth machinery via a function-local import; nullable `CurrentUserAlias | None` return; no `get_queryset` re-run; async one-boundary). Discharged the `queries.py:17` + `queries.py:33` anchors.

Slice-intended fakeshop + tests:
- `examples/fakeshop/apps/accounts/schema.py` — added `Query.me = current_user()` and `Mutation.register = register_mutation()`; imports grown. Discharged the `schema.py:21` anchor.
- `examples/fakeshop/config/schema.py` — composed `AccountsQuery` into the aggregate `Query`.
- `examples/fakeshop/test_query/test_auth_api.py` — 5 live tests (register→login→me→logout round trip, duplicate-username envelope, weak-password envelope keyed to `password` not `__all__`, anonymous `me → null`, register/me SDL shapes).
- `tests/auth/test_mutations.py` — the register-rider residue (see Tests added).
- `tests/auth/test_queries.py` — the `current_user` residue (rewrote the stub file). Discharged the `test_queries.py:3` anchor.
- `tests/auth/__init__.py` — updated from the "Slice 1-2" note to the final Slice-2-complete form. Discharged the `__init__.py:3` anchor.

### Tests added or updated

Live (`examples/fakeshop/test_query/test_auth_api.py`, appended, first line `create_users(N)`): `test_register_login_me_logout_round_trip` (asserts `check_password(raw)` True + raw not stored), `test_register_duplicate_username_envelope`, `test_register_weak_password_envelope` (≥2 messages, key `password` ≠ `__all__`), `test_anonymous_me_returns_null`, `test_register_me_sdl_shapes`.

Package-internal `tests/auth/test_mutations.py` (register-rider residue): `derive_register_fields` default + custom-`USERNAME_FIELD`/`REQUIRED_FIELDS` (dedup/order); exclusion-seam three-assertion test (value captured / marker preserved / attr absent) + the default-path no-regression 3-tuple test; factory cache identity + presentation-kwargs-don't-conflict + conflicting-`permission_classes` raise + records-into-both-ledgers; plaintext-never-persisted on BOTH the sync AND async register resolver paths (independent tests); weak-password `password`-keyed leaf; `validate_password` sees the constructed instance (similarity validator); register-arm distinct no-`UserType` error; reload-idempotence + conflict-doesn't-survive-clear; register-only bind doesn't orphan login/logout payloads; declare-after-finalize raise; gated register denies before any write.

Package-internal `tests/auth/test_queries.py` (`current_user` residue): `CurrentUserAlias` clear is a pre-bind `register_subsystem_clear` row; alias materializes through `make_input_namespace`; return annotation resolves to `me: UserType`; sync actor (IS `request.user`, no re-query) / anonymous null; async forces the lazy user in one boundary + async gated `me`; current-user-arm distinct no-`UserType` error; current-user-only surface-keyed bind; gated anonymous `me` raises `GraphQLError`.

### Validation run

- `uv run ruff format .` → 1 file reformatted, 307 unchanged (then clean). `uv run ruff check --fix .` → all checks pass (auto-fixed 1 trailing comma; the two initial ARG001/UP045 hits fixed by hand — `noqa: ARG001` on the rider's `build_input`/`input_type_name` classmethods, `Annotated[...] | None` in place of `Optional[...]`). `uv run python scripts/check_trailing_commas.py --fix` → reformatted 3 files (5+-arg signatures ruff misses).
- `git status --short` classification: **slice-intended (stay):** `auth/mutations.py`, `auth/queries.py`, `mutations/resolvers.py`, `examples/fakeshop/apps/accounts/schema.py`, `examples/fakeshop/config/schema.py`, `examples/fakeshop/test_query/test_auth_api.py`, `tests/auth/{__init__,test_mutations,test_queries}.py`, and this artifact. **NOT my churn (untouched by me):** the 6 Slice-1 working-tree files (`mutations/fields.py`, `registry.py`, `types/finalizer.py`, `examples/fakeshop/config/settings.py`, `examples/fakeshop/schema_reload.py`, `docs/spec-040-…md`) — verified their diffs are Slice-1 content (e.g. `fields.py` is the `attach_synthesized_signature` promotion / `fields.py:64` anchor); the 8 `D` prior-cycle (039) artifact deletions; the 3 `??` untracked plan/artifact `.md` files. No tool churn to revert.
- Focused tests (no `--cov*`): `uv run pytest tests/auth/ --no-cov` → **46 passed**. `uv run pytest tests/ --no-cov` (full sweep — resolvers seam touches the shared model decode path) → **2368 passed, 3 skipped** (`036`/`038`/`039` green untouched). `cd examples/fakeshop && uv run pytest test_query/test_auth_api.py --no-cov -n0` → **12 passed**. Full `test_query/` sweep (cross-pollution guard for the added accounts `Query`) → **323 passed, 1 skipped, 4 xfailed**.

### Implementation notes

- **Exclusion-seam return shape (plan discretion item):** `_model_decode_step` returns a 4-tuple `(target, m2m, exclude, excluded_values)` ONLY when `excluded_input_fields` is non-empty; the default path returns the SAME 3-tuple as before. Rationale: keeps the model flavor byte-behavior-identical (verified by a dedicated `len(decoded) == 3` no-regression test) while giving the register caller `excluded_values["password"]`. Marker preservation is `provided |= excluded_values.keys()` before `_unprovided_exclude`.
- **`RegisterInput` name pinning:** the rider overrides `build_input` (not just `input_type_name`) to build the generated create input via `build_mutation_input`, then subclass-rename it to `RegisterInput` using the SAME `strawberry.input(type("RegisterInput", (generated,), {}))` idiom the consumer-input merge uses, and materialize under `RegisterInput`. `input_type_name` alone only fixes the lazy-ref name; the materialized class must ALSO be named `RegisterInput` for the ref to resolve (the initial smoke build failed with a `LazyType KeyError: 'RegisterInput'` until this was added). This is a small mechanically-obvious extension of the plan's "pin `input_type_name`" step — recorded in spec-reconciliation below.
- **Resolver seams as classmethods:** the rider's `resolve_sync` / `resolve_async` are `classmethod(<make_resolver_entries output>)` so `cls` binds `mutation_cls` when `DjangoMutationField._resolve` calls `mutation_cls.resolve_sync(info, ...)` (a `staticmethod` would misbind `info` to `mutation_cls`). Mirrors `resolver_seams`.
- **Register sync entry passes `get_user_model()` to the decode step** rather than reading `mutation_cls._mutation_meta.model` — equivalent (the rider's `Meta.model` IS `get_user_model()`), chosen for readability and to keep the decode step model-explicit.
- **Both-ledger registration is unconditional per call:** `_declare_register_surface` appends the auth-ledger record (dedup no-op on a cached repeat) and `register_mutation` then calls `register_model_mutation(record.rider)` (also identity-deduped — the rider was already registered by the metaclass at synthesis). Registering unconditionally, not behind the cache guard, keeps the post-`registry.clear()` reload path re-appending to both ledgers.
- **`_resolve_user_primary(surface_label)` prefix:** login keeps the byte-identical `"Auth mutations …"` message (Slice-1 test matches `"require a registered DjangoType"`); register uses `"Auth register mutations …"`, current_user `"Auth current_user query …"` — the shared "require a registered DjangoType" fragment stays, only the leading phrase varies, so the ONE getter + message body serves all three with distinct raises.

### Notes for Worker 3

- No shadow files / `review_inspect.py` used this pass.
- The register denial reads `"Not authorized to create UserType."` (the rider's `operation="create"` + `_primary_type` set to the resolved user type by `_bind_mutation`), NOT a register-specific verb — the gate runs through the standard `authorize_or_raise` with `operation="create"`. The gated-register test asserts this exact string.
- The `me` denial reads `"Not authorized to current_user UserType."` (the current_user holder's `_primary_type` set to the user type at bind; operation token `"current_user"`).
- The Slice-1 anchor `resolvers.py:1465` (`run_pipeline_async` `TODO(spec-040 Slice 1)` generic-boundary "may") is left undischarged, per the task's carry-forward instruction (integration-pass-owned). No `TODO(spec-040 Slice 2)` anchors survive in source/tests (verified by grep).

### Notes for Worker 1 (spec reconciliation)

- **`build_input` override on the rider (small, mechanically-obvious drift):** the plan's step 3 says the rider "pins `input_type_name` to `RegisterInput`". That alone is insufficient — the MATERIALIZED input class name must also be `RegisterInput` or the field's `data:` lazy ref cannot resolve (`LazyType KeyError`). I added a `build_input` classmethod override that reuses `build_mutation_input` and renames+materializes as `RegisterInput` via the existing consumer-merge subclass idiom. This stays within the slice's contract (reuses the generator by call, adds no new input generator) and is evaluable from the diff. If Worker 1 prefers, the spec's Decision 6 wording could add "and `build_input` to materialize the generated input under the pinned name" to make the input-name seam explicit; the implementation is faithful to the intent either way.

---

## Review (Worker 3)

Static inspection: ran `scripts/review_inspect.py --output-dir docs/shadow` on `auth/mutations.py`, `auth/queries.py`, and `mutations/resolvers.py` (Slice 2 adds ≥30 lines of logic to the first two, touches the resolvers seam). Shadow overviews at `docs/shadow/django_strawberry_framework__auth__mutations.overview.md` etc. Repeated-literal + hotspot signals fed the DRY findings below. `queries.py` shows zero ORM markers and zero `setattr`/`delattr` calls-of-interest (corroborating D13: the alias rides the `make_input_namespace` trio, not a hand `setattr`).

### High:

None.

### Medium:

#### M1 — Missing test: no-`UserType` register-arm error on the SECOND finalize (post-reload)

The spec pins this as a distinct requirement in two places — Decision 6 (`docs/spec-040-…md` #"asserting both that `register` is present in the second schema AND — for a no-`UserType` schema — that the second finalize still fires the register-arm auth-specific error") and the Test plan (#"for a no-`UserType` schema, that the second finalize still raises the register-arm auth-specific error — not merely that `register` is present when the type exists"). It is the exact regression the every-call-both-ledger re-record design exists to prevent (were the auth-ledger record written once behind the cache guard, a `registry.clear()` would drain it with no re-add and the register arm would silently regress to `_resolve_primary_type`'s generic message).

The suite covers the two halves separately but not the combination:
- `tests/auth/test_mutations.py::test_register_without_user_type_raises_distinct_error` — FIRST finalize, no user type → register-arm message.
- `tests/auth/test_mutations.py::test_register_reload_idempotence_and_conflict_does_not_survive_clear` — reload cycle, but WITH a user primary declared (`_register_schema()` calls `_declare_user_primary()`), so it asserts `register` present in schema2, never the no-`UserType` second-finalize raise.

The implementation IS correct: `register_mutation` re-records into both ledgers unconditionally per call (`auth/mutations.py::register_mutation` #"register_model_mutation(record.rider)" + `_declare_register_surface`'s auth-ledger append). Verified by a temp probe (see Temp test verification) that finalizes a register-only, no-`UserType` schema, clears, re-declares, and finalizes again — the register-arm `ConfigurationError` fires on BOTH finalizes (1 passed). So this is a missing-test finding, not a behavior bug: promote the probe to `tests/auth/test_mutations.py` (a `test_register_reload_no_usertype_still_raises_register_arm` alongside the existing reload test).

Recommended change: add the permanent test pinning `match="Auth register mutations require"` on the second finalize of a cleared-and-re-declared register-only schema with no user primary.

### Low:

#### L1 — `current_user` return ref hand-spells `Annotated[…, strawberry.lazy(…)]` instead of `_lazy_ref(…) | None`

Decision 7 / D12 pin the return ref as "built by the shared `_lazy_ref(type_name, module_path)` helper … not a hand-spelled `Annotated[...]`". `login`/`logout` comply (`_lazy_ref(_LOGIN_PAYLOAD, INPUTS_MODULE_PATH)`), but `current_user` hand-spells the equivalent at `auth/queries.py` #"Annotated[_CURRENT_USER_ALIAS, strawberry.lazy(AUTH_QUERIES_MODULE_PATH)] | None". Since `_lazy_ref` returns exactly `Annotated[type_name, strawberry.lazy(module_path)]`, `_lazy_ref(_CURRENT_USER_ALIAS, AUTH_QUERIES_MODULE_PATH) | None` produces the byte-identical annotation and satisfies the directive. Non-blocking (the annotation is correct and `me: UserType` resolves — pinned by `test_me_return_annotation_resolves_to_user_type_or_null`), but it is a literal D12 deviation the integration pass would otherwise flag.

Recommended change: import `_lazy_ref` (already at `auth/mutations.py:44`, or from `..mutations.fields`) and write `_lazy_ref(_CURRENT_USER_ALIAS, AUTH_QUERIES_MODULE_PATH) | None`.

#### L2 — `"RegisterInput"` is a 3x-repeated bare literal (module names every other such name once)

The inspector flags `RegisterInput` 3x: `_input_type_name` returns it, `_build_input` uses it in `type("RegisterInput", …)` and `materialize_mutation_input_class("RegisterInput", …)`. The module names every other load-bearing generated name once as a constant (`_LOGIN_PAYLOAD`, `_LOGOUT_PAYLOAD`, `_PASSWORD`; `queries.py::_CURRENT_USER_ALIAS`) precisely so the seam and the materialize call cannot drift on the name — the `input_type_name` seam and the `build_input` materialized name MUST match or the `data:` lazy ref fails to resolve (the `LazyType KeyError` Worker 2's notes record). A bare 3x literal is the drift risk those constants exist to remove.

Recommended change: name it once (`_REGISTER_INPUT = "RegisterInput"`) beside the payload constants and reference it in all three sites.

### DRY findings

- **`_declare_register_surface` duplicates `_declare_surface`'s normalize + dedupe + conflict-raise branch (Medium-tier DRY).** `auth/mutations.py::_declare_register_surface` and `::_declare_surface` share a byte-identical body except the final record construction: both call `_validate_permission_classes(<surface>, permission_classes, unset_default=())`, both loop `iter_auth_mutations()` and — on a surface match — raise the SAME `ConfigurationError` (`f"AuthMutation {surface} was already declared with different permission_classes (…); one auth surface may be declared once per process (call registry.clear() first)."`, only `{surface}` vs the `_REGISTER` literal differs) or return the cached record; the sole divergence is `_AuthDeclaration(surface, normalized, holder)` vs `_AuthDeclaration(_REGISTER, normalized, holder=rider, rider=rider)`. The inspector confirms the duplication independently (2x `"…was already declared with different permission_classes ("` and 2x the tail sentence). This is a live duplication (both callers reachable) and inconsistent with the module's own single-siting posture (`_make_permission_holder`, `_build_auth_field`, `_resolve_user_primary` are each ONE helper). `_declare_register_surface`'s own docstring even says it "Mirrors `_declare_surface`". Recommended shape: factor the normalize + lookup + conflict-check into one helper returning the cached record or `None` ("first declaration"), and let each caller supply the record it constructs — e.g. `_declare_surface(surface, operation, primary_type, permission_classes, *, make_record=…)` or a small `_lookup_or_conflict(surface, normalized) -> _AuthDeclaration | None` primitive both call. Routed to Worker 1 for the integration-pass DRY decision if not consolidated in a re-pass (recorded under Notes for Worker 1).
- **Non-reuse comments present (D-N1/D-N2/D-N3).** All three deliberate-non-reuse points carry their source comment: D-N1 at `auth/queries.py` #"NO get_queryset re-run, NO optimizer re-fetch (D-N1)"; D-N2 at `auth/mutations.py::_register_write_step` #"NOT ``validation_error_to_field_errors``"; D-N3 at `_register_write_step` #"No relation-visibility helpers wired". Correct.
- **Reuse-by-call verified (D6/D7/D8/D9/D10/D12/D13/D14/D16).** The exclusion seam threads `excluded_input_fields` through the existing `_model_decode_step`/`_decode_relations` (D6, no forked walk); `_register_write_step` delegates `full_clean`/`save`/M2M to `_model_write_step` and only adds `validate_password` + `set_password` (D7); the password error is `field_error("password", …)` DIRECT, not the generic mapper (D8/D-N2); register rides `run_write_pipeline_sync` + `make_resolver_entries` (`_run_register_pipeline_sync` is the serializer-flavor mirror) so the async path shares the one `run_pipeline_async` boundary (D9/D10/D17); `current_user` rides the shared `_build_auth_field`/`attach_synthesized_signature`/`_run_in_one_boundary` (D12/D17); the alias rides the `make_input_namespace` trio (D13); the ledger is a `make_declaration_registry("AuthMutation")` (D14); `bind_auth_mutations` resolves the primary via `_resolve_user_primary` → `registry.get(get_user_model())` (D16). No re-spelled glue found beyond the DRY finding above.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is empty — `__all__` and the re-export list are unchanged. Authorized by Decision 3 (`docs/spec-040-…md` Decision 3: "four field factories at the `auth` submodule path … no root re-export"); auth symbols are submodule-only re-exports in `auth/__init__.py`, which was already present at HEAD (Slice 2 needs no change there, per plan step 5). Pass.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The `docs/spec-040-…md` diff in the working tree is Worker 1's custodial Status line + the Slice-1 P3 build note — explicitly out of this review's scope per the task framing; the Slice-3 doc/version/KANBAN work is a separate slice.)

### What looks solid

- **Password safety (the highest-stakes contract) — SOLID.** The write step runs `validate_password` → `field_error("password", exc.messages, codes=[…])` DIRECTLY (NOT `validation_error_to_field_errors`, which would key the list-style error to `"__all__"`) → `set_password` BEFORE the shared `_model_write_step` (`full_clean`/`save`). The decode never hands `password` to `model(**scalar_and_fk_attrs)` (the exclusion seam captures it into `excluded_values` and `continue`s before the scalar branch). Plaintext-never-persisted is asserted INDEPENDENTLY on both the sync (`execute_sync`) and async (`await execute`) resolver paths (`test_register_sync/async_hashes_password_never_persists_plaintext`), both pinning `check_password(raw) is True` AND `user.password != raw`. The seam-level unit test pins value-captured + marker-preserved (`"password" not in exclude`) + attr-absent (`target.password == ""`, the field default not the raw input). Live weak-password envelope pins `field == "password"` and `!= "__all__"` with ≥2 messages. Verdict: **safe**.
- **Exclusion seam correctness — SOLID.** The seam preserves the provided-marker via `provided |= excluded_values.keys()` before `_unprovided_exclude` (so `full_clean` still validates the `password` column against the hash — never "pop before decode"). The default (no-exclusion) path is byte-behavior-identical: `excluded_values` stays `{}`, the guard is never true, `provided |= {}` is a no-op, and `_model_decode_step` returns the 3-tuple when `excluded_input_fields` is falsy. Verified mechanically from the diff and corroborated by `tests/mutations/` (176 passed) + `test_model_decode_step_default_path_returns_three_tuple` (`len(decoded) == 3`). The only production caller of `_decode_relations` is `_model_decode_step` (grep-confirmed), so the 3-tuple→4-tuple internal widening has one updated caller.
- **Rider lifecycle — SOLID.** `Register.__name__ == "Register"` → `RegisterPayload` via unchanged `_bind_mutation` (no payload-name seam); `input_type_name` + `build_input` overrides match the base classmethod signatures (`(cls, meta)` / `(cls, meta, primary_type)`); resolve seams are `classmethod(...)` so `cls` binds `mutation_cls` (Worker 2's note is correct — a staticmethod would misbind). Every call re-records into BOTH ledgers unconditionally (auth via `_declare_register_surface`, mutation via `register_model_mutation(record.rider)`); conflicting `permission_classes` → `ConfigurationError`; the reload cycle re-mints post-clear (the cache/conflict state IS the ledger).
- **`current_user` — SOLID.** Nullable session actor, returns `request.user` directly with NO `get_queryset`/re-fetch (`test_sync_current_user_returns_the_session_actor_without_a_requery` pins `result is request.user`). The gate runs FIRST inside the async boundary with `instance=request.user`, forcing the lazy object in-boundary (`test_async_gated_me_forces_lazy_user_inside_the_boundary`). The `CurrentUserAlias` namespace is the one new `register_subsystem_clear` row (`auth/queries.py:41`), materialized through the D13 trio.
- **Worker 2's `build_input`/`RegisterInput` decision — CLEAN reuse.** `_build_input` rides `build_mutation_input` (no new generator) and renames via the SAME `strawberry.input(type("RegisterInput", (generated,), {}))` consumer-merge subclass idiom, then materializes through the shared ledger. `input_type_name` alone was insufficient (it only pins the lazy-ref name; the materialized class must also be named `RegisterInput`) — the override is the mechanically-obvious extension the plan's "pin the input name" step implies, not a near-copy of an existing generator. Faithful to Decision 6's input-name seam (D10/D11). Assessed and accepted; the only residue is L2 (the bare 3x literal).
- **Spec slice checklist walk — all four boxes land.** Box 1 (register rider) — landed in `register_mutation`/`_synthesize_register_rider`. Box 2 (`current_user` nullable, no `get_queryset`) — landed in `auth/queries.py`. Box 3 (live surface + round-trip/duplicate/weak-password/anonymous-me) — landed in `test_auth_api.py`. Box 4 (mirrored package tests) — landed in `tests/auth/`, with the one gap called out as M1 (the no-`UserType` second-finalge assertion that box 4 enumerates). No over-ticked box (every `- [x]` has matching implementation in the diff).

### Temp test verification

- `tests/auth/test_slice2_temp_probe.py` (temporary, written under `tests/` to inherit the `pytest.ini` Django/config bootstrap the isolated `docs/builder/temp-tests/` dir cannot provide; **deleted after the run**). It finalized a register-only, no-`UserType` schema, cleared the registry, re-declared, and finalized again — asserting the register-arm `ConfigurationError` (`match="Auth register mutations require"`) on BOTH finalizes. Result: **1 passed** — confirming the implementation is correct and M1 is a missing-test gap, not a behavior bug.
- Disposition: deleted. Recorded as finding M1 for Worker 2 to promote a permanent equivalent into `tests/auth/test_mutations.py`.

### Notes for Worker 1 (spec reconciliation)

- **`build_input` seam (Worker 2's spec-reconciliation note):** Worker 2 flags that the plan's step 3 ("pin `input_type_name`") is insufficient — the MATERIALIZED input class must also be named `RegisterInput` or the `data:` lazy ref cannot resolve. I confirm the `build_input` override is faithful to Decision 6's intent (Decision 6 already names "the `input_type_name` / `build_input` name seams" as the input-name mechanism, `docs/spec-040-…md` #"pinned to `RegisterInput` via the `input_type_name` / `build_input` name seams"), so no spec edit is required — the wording already anticipates the `build_input` seam. Recorded for Worker 1's awareness only.
- **DRY consolidation of `_declare_surface` / `_declare_register_surface`** (DRY findings above) — if not consolidated in a Worker 2 re-pass, this is a clean candidate for the cross-slice integration pass (the two functions share a byte-identical dedupe/conflict branch). Flagging so it is not lost.

### Review outcome

`revision-needed` — M1 (a spec-enumerated test the diff does not pin) is a Medium finding with no recorded deferral, and the `_declare_register_surface`/`_declare_surface` duplication is a Medium-tier DRY finding. The implementation is behaviorally correct and password-safe; the revision is: (1) promote the M1 temp-probe assertion into `tests/auth/test_mutations.py`; (2) consolidate the duplicated declare-surface conflict/dedup branch (or Worker 1 defers it to the integration pass with a recorded reason). L1 / L2 are non-blocking polish that fold cleanly into the same re-pass.

---

## Build report (Worker 2, pass 2)

Apply-changes pass addressing Worker 3's four `revision-needed` findings (M1, M2, L1, L2). Fixed ONLY these four; no scope expansion. Did NOT touch the `resolvers.py:1465` `TODO(spec-040 Slice 1)` anchor, the unused `_build_auth_field(permission_holder=...)` param, or any Slice-1-only code. Public surface (`__init__.py` `__all__`) unchanged.

### Files touched

Grounded in `git status --short`; only these three source/test files carry pass-2 edits (all other `M` files are prior-pass Slice-1/Slice-2 build content already in the artifact, not pass-2 churn):

- `django_strawberry_framework/auth/mutations.py` — **M2** (DRY): factored the shared `_lookup_or_conflict(surface, permission_classes) -> tuple[normalized, _AuthDeclaration | None]` primitive; both `_declare_surface` and `_declare_register_surface` now ride it, minting only their divergent record (holder vs rider) on a first declaration (`record is None`). The normalize + dedupe + conflict-raise `ConfigurationError` is now single-sited (was byte-duplicated). **L2**: named `_REGISTER_INPUT = "RegisterInput"` beside the payload constants; the `input_type_name` seam, the `type(...)` rename, and the `materialize_mutation_input_class(...)` call all reference it (was a bare 3× literal).
- `django_strawberry_framework/auth/queries.py` — **L1**: `current_user`'s return ref now uses the mandated `_lazy_ref(_CURRENT_USER_ALIAS, AUTH_QUERIES_MODULE_PATH) | None` idiom (D12) instead of the hand-spelled `Annotated[…, strawberry.lazy(…)] | None`. `_lazy_ref` is imported top-level from `..mutations.fields` (cycle-safe — smoke-verified it resolves to the same object `mutations/fields.py` exposes); the resolved annotation is byte-identical (`_lazy_ref` returns exactly `Annotated[type_name, strawberry.lazy(module_path)]`). Dropped the now-unused `Annotated` / `strawberry` imports.
- `tests/auth/test_mutations.py` — **M1**: added `test_register_reload_no_user_type_still_raises_register_arm_error` — a register-only, no-`UserType` schema that finalizes (register-arm raise), `registry.clear()`s, re-declares, and finalizes AGAIN, pinning `match="Auth register mutations require"` on BOTH finalizes. Distinct from `test_register_without_user_type_raises_distinct_error` (first finalize only) and from `test_register_reload_idempotence_and_conflict_does_not_survive_clear` (declares a user primary, so it never exercises the no-`UserType` second-finalge raise).

### Tests added or updated

- Added (M1): `tests/auth/test_mutations.py::test_register_reload_no_user_type_still_raises_register_arm_error`. Pins the register-arm auth-specific error on the post-reload second finalize — the exact regression the every-call-both-ledger re-record design prevents. The `match="Auth register mutations require"` is distinct from the generic `_resolve_primary_type` message (`"DjangoMutation Register targets ... which has no registered DjangoType"`), so a silent regression to the generic path would fail the match.
- No test was removed or weakened. `tests/auth/` grew 46 → 47.

### Validation run

- `uv run ruff format .` → 308 files left unchanged (no reformat). `uv run ruff check --fix .` → All checks passed (no auto-fixes needed). `uv run python scripts/check_trailing_commas.py --fix` → Fixed 0 files. No tool churn to revert.
- Focused tests (no `--cov*`): `uv run pytest tests/auth/ --no-cov` → **47 passed**. `uv run pytest tests/mutations/ --no-cov` → **176 passed** (the seam default 3-tuple path unchanged). `cd examples/fakeshop && uv run pytest test_query/test_auth_api.py --no-cov -n0` → **12 passed** (live register/login/me/logout + envelopes). Full package sweep (the DRY refactor + L1 import touch shared/adjacent code) `uv run pytest tests/ --no-cov` → **2369 passed, 3 skipped** (was 2368 + my new test; `036`/`038`/`039` green untouched).
- Cycle-safety smoke: `_lazy_ref` imported top-level in `queries.py` resolves to the same object as `mutations/fields.py::_lazy_ref` (no import cycle).
- `git status --short` classification: **pass-2 slice-intended (my edits):** `auth/mutations.py`, `auth/queries.py`, `tests/auth/test_mutations.py`, and this artifact. **Prior-pass slice content (in artifact, not pass-2 churn):** `mutations/{fields,resolvers}.py`, `registry.py`, `types/finalizer.py`, `examples/fakeshop/{apps/accounts/schema,config/schema,config/settings,schema_reload,test_query/test_auth_api}.py`, `tests/auth/{__init__,test_queries}.py`. **Baseline (not my churn):** the 8 `D` prior-cycle (039) artifact deletions, the 3 `??` untracked plan/bld `.md`, and the `M docs/spec-040-…md` (Worker-1 custodial). No tool churn.

### Implementation notes

- **`_lookup_or_conflict` shape (M2):** a module-level primitive returning `(normalized, record_or_none)`. It owns the full normalize (`_validate_permission_classes(surface, permission_classes, unset_default=())`) + surface-keyed dedupe + conflict-raise; each caller supplies only its divergent record on a first declaration (`record is None` → mint holder in `_declare_surface`, mint+cache rider in `_declare_register_surface`). Why this shape over `make_record=…` callback injection: returning `(normalized, record | None)` keeps both callers' record-construction inline and readable (the holder path needs `operation`/`primary_type`, the rider path needs `_synthesize_register_rider` + the `rider=` kwarg — a callback would obscure those). The conflict `ConfigurationError` (`f"AuthMutation {surface} was already declared with different permission_classes (…)…"`) is now emitted at ONE site; for register `{surface}` interpolates `_REGISTER` (`"register"`), byte-identical to the pre-refactor message.
- **L2 constant scope:** placed `_REGISTER_INPUT` beside `_LOGIN_PAYLOAD`/`_LOGOUT_PAYLOAD` (the generated-name constant cluster) rather than beside `_PASSWORD`, since it is a generated GraphQL type name like the payloads, not a model column.
- **L1 import placement:** top-level `from ..mutations.fields import _lazy_ref` in `queries.py` (mirrors `auth/mutations.py`'s top-level `_lazy_ref` import). `queries.py` already imported the auth substrate function-locally for cycle reasons, but `mutations.fields` is a lower-level module (it does not import `auth.queries`), so the top-level import is safe — verified by smoke import.

### Notes for Worker 3

- No shadow files / `review_inspect.py` used this pass (targeted four-finding apply-changes).
- M2 verification: the conflict message is now grep-confirmed single-sited (`grep "was already declared with different"` → one hit, in `_lookup_or_conflict`). Both `_declare_surface` and `_declare_register_surface` reduced to `normalized, record = _lookup_or_conflict(...)` + a `record is not None` early return + the divergent mint. Behavior is unchanged: the register conflict test (`test_register_conflicting_permission_classes_raises`), the login/logout conflict tests, the presentation-kwargs-don't-conflict test, and the reload-conflict-doesn't-survive-clear test all still pass.
- M1: the new test is the permanent equivalent of Worker 3's deleted temp probe (`test_slice2_temp_probe.py`), placed in `tests/auth/test_mutations.py` alongside the existing reload test.

### Notes for Worker 1 (spec reconciliation)

- None. All four findings were mechanical fixes within the slice's contract; no plan-level or spec-level deviation. The `build_input` spec-reconciliation note from pass 1 (Worker 3 confirmed it faithful to Decision 6's already-worded input-name seam) is unchanged and still stands.

---

## Review (Worker 3, pass 2)

Targeted re-review of the four pass-1 `revision-needed` findings (M1, M2, L1, L2) against the working-tree diff, plus a no-regression scan of the pass-2 changes. Pass-2 churn is confined to three files (`auth/mutations.py`, `auth/queries.py`, `tests/auth/test_mutations.py`) per Worker 2's pass-2 report; `mutations/resolvers.py` and the register decode/write logic carry NO pass-2 edits (the exclusion seam is unchanged from pass 1). No shadow files / `review_inspect.py` this pass (targeted four-finding confirmation).

### Pass-1 finding resolution

- **M1 (missing test) — RESOLVED.** `tests/auth/test_mutations.py::test_register_reload_no_user_type_still_raises_register_arm_error` (L762-795) exists. It declares a register-only, no-`UserType` schema, finalizes (asserting `match="Auth register mutations require"`), `registry.clear()`s, re-declares, and finalizes AGAIN — asserting the register-arm message on the SECOND (post-clear) finalize too, distinct from the generic `_resolve_primary_type` message. It exercises the post-clear second-finalize path (the `registry.clear()` at L792 drains BOTH the auth ledger — `registry.py:594-598` co-clears `clear_auth_mutation_registry` — and the mutation ledger, so the re-declare re-appends to both). Ran without `--cov`: passes (3 passed with its two neighbors). **Non-vacuousness confirmed** via a temp probe (`tests/auth/test_slice2_m1_nonvacuous_probe.py`, deleted): monkeypatching `auth.mutations.register_auth_mutation` to a no-op during the post-clear re-declare (simulating removal of the every-call auth-ledger re-record) makes the second finalize fire the GENERIC error, which does NOT contain `"Auth register mutations require"` — so the M1 `match=` assertion FAILS under the regression (2 passed: the regression-simulation probe + the unmodified control). The test genuinely pins the every-call re-record, not a tautology.
- **M2 (DRY) — RESOLVED.** `_lookup_or_conflict(surface, permission_classes) -> (normalized, _AuthDeclaration | None)` (mutations.py:243-274) is the shared primitive; both `_declare_surface` (L291) and `_declare_register_surface` (L727) ride it, minting only their divergent record (holder vs rider) on `record is None`. The conflict-raise `ConfigurationError` is now single-sited — `grep "was already declared with different"` returns ONE hit (mutations.py:268). Register's conflict message is byte-unchanged from pass 1: the `f"AuthMutation {surface} was already declared with different permission_classes ({record.permission_classes!r} vs {normalized!r}); one auth surface may be declared once per process (call registry.clear() first)."` form now interpolates `{surface}` = `_REGISTER` = `"register"` at the single site. Behavior verified: the 7 conflict/idempotent/cache/presentation/records-into-both tests pass, and the full auth suite is green (47 passed). The refactor did not perturb Slice-1 login/logout ledger behavior (login/logout conflict + same-args-cache-returns-cached-holder tests pass; the cached-record early return preserves holder identity).
- **L1 — RESOLVED.** `current_user`'s return ref now uses `_lazy_ref(_CURRENT_USER_ALIAS, AUTH_QUERIES_MODULE_PATH) | None` (queries.py:104) — the mandated D12 idiom. `_lazy_ref` (fields.py:121-134) returns exactly `Annotated[type_name, strawberry.lazy(module_path)]`, so the resolved annotation is byte-identical to the pass-1 hand-spelled `Annotated[…, strawberry.lazy(…)] | None`; `me: UserType` (nullable) still resolves (`test_me_return_annotation_resolves_to_user_type_or_null` passes). `_lazy_ref` is imported top-level from `..mutations.fields` (cycle-safe — smoke-verified `auth.queries._lazy_ref is mutations.fields._lazy_ref` → True, and `from ..auth import queries, mutations` imports clean); the now-unused `Annotated` / `strawberry` imports are dropped (ruff clean, the only surviving `Annotated`/`strawberry` tokens are in a comment at L101-103).
- **L2 — RESOLVED.** `_REGISTER_INPUT = "RegisterInput"` (mutations.py:101) is a single module-level constant referenced at all three sites: the `input_type_name` seam return (L678), the `type(_REGISTER_INPUT, (generated,), {})` rename (L698), and the `materialize_mutation_input_class(_REGISTER_INPUT, …)` call (L699). No bare `"RegisterInput"` string literal survives in code (the remaining occurrences are docstrings/comments).

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **The pass-1 Medium-tier DRY finding is discharged in source.** `_declare_surface` / `_declare_register_surface` no longer byte-duplicate the normalize + dedupe + conflict-raise branch — it is single-sited in `_lookup_or_conflict`. The chosen shape (return `(normalized, record | None)`; each caller mints its divergent record inline) is the more readable option over a `make_record=` callback (the holder path needs `operation`/`primary_type`, the rider path needs `_synthesize_register_rider` + the `rider=` kwarg — a callback would obscure those). No new duplication introduced by the refactor.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is empty — `__all__` and the re-export list are unchanged (authorized by Decision 3: auth symbols are `auth`-submodule re-exports, no root re-export). Pass 2 added no public exports. Pass.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### What looks solid

- **No regression from the pass-2 diff.** Password safety is untouched (`_register_write_step` / the exclusion seam carry no pass-2 edits — the `validate_password → field_error("password", …) DIRECT → set_password before full_clean` path and the marker-preserving `excluded_input_fields` seam are pass-1 content, still asserted by the sync + async plaintext-never-persisted tests). The exclusion-seam default 3-tuple path is byte-behavior-identical (`resolvers.py:286` guards on `python_name in excluded_input_fields`, empty by default; `tests/mutations/` 176 green + the dedicated `len(decoded) == 3` no-regression test). The `_lookup_or_conflict` refactor did not perturb the Slice-1 login/logout ledger (login/logout conflict + cached-holder-identity tests green).
- **Full-sweep green.** `uv run pytest tests/auth/ --no-cov` → 47 passed; `tests/mutations/ --no-cov` → 176 passed; `tests/ --no-cov` → 2369 passed, 3 skipped (the `036`/`038`/`039` surfaces untouched); fakeshop `test_query/test_auth_api.py --no-cov -n0` → 12 passed. Consistent with Worker 2's pass-2 report.
- **Anchor sweep clean.** `grep -rEn 'TODO\(spec-040 Slice 2' --include="*.py"` → no hits. The only surviving spec-040 anchor is `resolvers.py:1465` `TODO(spec-040 Slice 1)` (integration-pass-owned, out of scope).

### Temp test verification

- `tests/auth/test_slice2_m1_nonvacuous_probe.py` (temporary, under `tests/auth/` to inherit the `pytest.ini` Django/config bootstrap the isolated `docs/builder/temp-tests/` dir cannot provide; **deleted after the run**). Two cases: (1) a control confirming the unmodified code fires the register-arm error on BOTH finalizes; (2) a regression simulation monkeypatching `register_auth_mutation` to a no-op during the post-clear re-declare, asserting the second finalize then fires the GENERIC error (no `"Auth register mutations require"`) — proving the M1 `match=` assertion is load-bearing. Result: **2 passed**.
- Disposition: deleted. The permanent M1 test (`test_register_reload_no_user_type_still_raises_register_arm_error`) already covers the positive path; the probe existed only to prove non-vacuousness for this review and is not needed as a permanent test.

### Notes for Worker 1 (spec reconciliation)

- None. All four pass-1 findings were resolved with mechanical, in-contract fixes. The pass-1 `build_input`/`RegisterInput` seam note (Worker 3 confirmed faithful to Decision 6's already-worded input-name seam) stands unchanged; no spec edit required.

### Review outcome

`review-accepted`. All four pass-1 findings (M1, M2, L1, L2) are genuinely resolved in the working-tree diff, verified behaviorally and (for M1) proven non-vacuous. No new High / Medium / Low findings; the pass-2 diff introduced no regression (password safety, the exclusion-seam default path, the public surface, and Slice-1 login/logout ledger behavior all confirmed unchanged). Full test sweep green (2369 passed, 3 skipped). Slice 2 is ready for Worker 1 final verification.

---

## Final verification (Worker 1)

### Spec slice checklist audit (all four boxes truly landed)

Walked each `- [x]` in the Plan's `### Spec slice checklist (verbatim)` against the working-tree diff; every box's contract landed (no over-tick, no silently-un-ticked box):

- **Box 1 (register rider) — landed.** `auth/mutations.py::register_mutation` → `_declare_register_surface` → `_synthesize_register_rider`: an ordinary `DjangoMutation` subclass with `__name__ = "Register"` (so unchanged `_bind_mutation` emits `RegisterPayload` — no payload-name seam), over `get_user_model()`, `operation = "create"`, `Meta.fields = derive_register_fields(user_model)` (the model-arg helper), `build_input`/`input_type_name` pinning `RegisterInput`, and both `resolve_sync`/`resolve_async` overridden to `make_resolver_entries(_run_register_pipeline_sync)` riding `run_write_pipeline_sync` with the password-aware `_register_decode_step`/`_register_write_step` pair. Password step: `validate_password(raw, user)` → `field_error("password", exc.messages, codes=[...])` **DIRECT** (D8/D-N2 comment present) → `set_password(raw)` **before** the delegated `_model_write_step` (`full_clean`/`save`). Every call re-records into BOTH ledgers unconditionally (`_declare_register_surface` auth-ledger append + `register_model_mutation(record.rider)`); conflicting-`permission_classes` → `ConfigurationError`; presentation kwargs excluded from the key. ✓
- **Box 2 (`current_user`) — landed.** `auth/queries.py::current_user` — nullable session-actor return via the bind-materialized `_lazy_ref(_CURRENT_USER_ALIAS, AUTH_QUERIES_MODULE_PATH) | None` alias (L1 fix landed — the mandated D12 idiom, not a hand-spelled `Annotated`), gate-first, returns `request.user` directly with **no** `get_queryset` re-run / no optimizer re-fetch (D-N1 comment present). ✓
- **Box 3 (live surface, same commit) — landed.** `examples/fakeshop/apps/accounts/schema.py` grows `Query.me = current_user()` + `Mutation.register = register_mutation()`; `config/schema.py` composes `AccountsQuery` into the aggregate `Query`. `test_auth_api.py` covers the register→login→`me`→logout round trip (with `check_password(raw)` True + raw not stored), duplicate-username → `username` key, weak-password → `password` key ≠ `__all__` with ≥2 messages, anonymous `me → null`, and the `RegisterInput`/`RegisterPayload`/`me: UserType` SDL shapes. **12 live tests pass.** ✓
- **Box 4 (mirrored package tests) — landed.** `tests/auth/test_mutations.py` + `test_queries.py`: plaintext-never-persisted on **both** sync (`test_register_sync_hashes_password_never_persists_plaintext`) AND async (`test_register_async_...`) paths; validator→envelope `password`-keyed-not-`__all__`; exclusion-seam provided-marker test (+ the default-path `len==3` no-regression test); factory cache identity + presentation-kwargs-don't-conflict + conflict raise + both-ledger re-record; the **reload-idempotence cycle** including the pass-2 M1 addition `test_register_reload_no_user_type_still_raises_register_arm_error` (the no-`UserType` second-finalize register-arm raise, proven non-vacuous by Worker 3's deleted probe); register-arm/current-user-arm distinct no-`UserType` errors; register-only/current-user-only surface-keyed binds; `derive_register_fields` default + custom-`USERNAME_FIELD`/`REQUIRED_FIELDS`. **47 auth tests pass.** ✓

No box un-ticked or over-ticked; nothing deferred.

### Register/current_user contract spot-checks (Decision 6/7)

- **Cached `Register` rider → `RegisterPayload`:** `__name__ = "Register"` pinned; `RegisterPayload` minted by the unchanged `_bind_mutation`; live SDL asserts `register(data: RegisterInput!): RegisterPayload!`. Confirmed.
- **Both `resolve_sync` / `resolve_async` overrides:** classmethod seams (`cls` binds `mutation_cls`), async half rides the one shared `run_pipeline_async` boundary via `make_resolver_entries`; plaintext-never-persisted asserted independently on each path. Confirmed.
- **Plaintext-never-persisted on both paths:** decode captures `password` into `excluded_values` and `continue`s before `model(**scalar_and_fk_attrs)`; `set_password` hashes before `full_clean`; both live + unit + async assertions pin `check_password(raw)` True and `.password != raw`. Confirmed.
- **Direct `password`-keyed error:** `field_error(_PASSWORD, exc.messages, codes=...)` at the `validate_password` call site, NOT `validation_error_to_field_errors` (which would key list-style errors to `__all__`); D-N2 comment present; live + unit tests assert `field == "password"` and `!= "__all__"`. Confirmed.
- **Exclusion seam provided-marker preservation:** `_model_decode_step` does `provided |= excluded_values.keys()` before `_unprovided_exclude`, so `full_clean` still validates the `password` column against the hash. The **no-regression / relocation claim** (my carry-forward from the planning pass) is proven mechanically: `_decode_relations` has exactly ONE production caller (`_model_decode_step`), the default model decode (`resolvers.py:1155`) passes no `excluded_input_fields` so `excluded_values == {}`, `provided |= {}` is a no-op, and the function returns the SAME 3-tuple as HEAD; `tests/mutations/` (176) green untouched confirms the model flavor's decode is byte-behavior-identical.
- **`current_user` nullable + no `get_queryset` re-run + bind-materialized alias:** returns `instance` (the actor or `None`) directly; `CurrentUserAlias` rides the `make_input_namespace` trio (pre-bind `register_subsystem_clear` row), materialized by `bind_auth_mutations()`'s `current_user` arm. Confirmed.
- **Register-arm / current-user-arm bind validation distinct from login's:** the shared `_resolve_user_primary(surface_label=...)` getter varies only the leading phrase — login `"Auth mutations …"`, register `"Auth register mutations …"`, current_user `"Auth current_user query …"`, all sharing `"require a registered DjangoType"`. Distinct-message tests pass for all three arms. Confirmed.

### DRY check (this slice AND Slice 1)

- **`_lookup_or_conflict` consolidation is sound and does not perturb Slice-1 login/logout.** Worker 2's pass-2 primitive `_lookup_or_conflict(surface, permission_classes) -> (normalized, record | None)` single-sites the normalize + surface-keyed dedupe + conflict-raise. Both `_declare_surface` (login/logout) and `_declare_register_surface` (register) ride it, minting only their divergent record (holder vs rider) on a first declaration. Verified: exactly two callers; the conflict `ConfigurationError` message is single-sited (one grep hit); the login/logout conflict + cached-holder-identity behavior is functionally identical to the pass-1 inlined shape and its tests pass inside the 223-passed focused run. The `TypeRegistry.clear()`-drained-ledger semantics (a post-clear re-declare with a different gate mints fresh) are preserved for all surfaces. No Slice-1 ledger regression.
- **L2 (`_REGISTER_INPUT`) resolved:** `"RegisterInput"` is a single module constant; no bare 3× literal survives in code.
- No new cross-slice duplication. The register rider reuses the write-stack (`run_write_pipeline_sync`, `_model_decode_step`, `_model_write_step`, `build_mutation_input`, `build_payload_type`, `DjangoMutationField`, `make_resolver_entries`, `field_error`) and the Slice-1 auth substrate (`_build_auth_field`, `_make_permission_holder`, `_lookup_or_conflict`, `_run_in_one_boundary`, `_resolve_user_primary`, `bind_auth_mutations`) all **by call**; the three deliberate non-reuse points (D-N1/D-N2/D-N3) each carry a source comment.

### Focused test run (no `--cov*`)

- `uv run pytest tests/auth/ tests/mutations/ --no-cov` → **223 passed** (47 auth + 176 mutations; the exclusion-seam default path did NOT regress the 036/serializer/form flavors).
- `cd examples/fakeshop && uv run pytest test_query/test_auth_api.py --no-cov -n0` → **12 passed** (live register/login/me/logout round trip + envelopes + SDL).

### Carry-forward anchors (confirmed cleanly deferred — NOT resolved here)

- `resolvers.py::run_pipeline_async` `TODO(spec-040 Slice 1)` (line ~1465) — the optional generic one-boundary factoring; spec Decision 10 P3 "may", integration-pass-owned. Still present and unchanged. Cleanly deferred; does not block Slice 2.
- The unused `_build_auth_field(permission_holder=...)` param — carries an explanatory `del permission_holder` (captured by the resolver closures, not read here). Cleanly deferred to the integration-pass consolidation loop. Does not block Slice 2.
- Anchor sweep: `grep -rEn 'TODO\(spec-040 Slice 2'` across source/tests is clean; the only source `TODO(spec-040 …)` anchor is the Slice-1 one above. The `TODO-ALPHA-040-0.0.13` hits are legitimate KANBAN card-id refs in archived specs (Slice-3 card-wrap concern), not staged-work anchors.

### Final status

`final-accepted`.

### Summary

Slice 2 ships `register_mutation()` and `current_user()` on the opt-in `auth` submodule path, earned live. `register_mutation()` synthesizes a cached `Register` rider — an ordinary `DjangoMutation` (so the unchanged machinery emits `RegisterInput`/`RegisterPayload`) that rides the shared `run_write_pipeline_sync` skeleton through a password-aware decode/write step pair: a reusable, provided-marker-preserving `excluded_input_fields` exclusion seam captures `password` out of model construction, and the write step validates + `set_password`-hashes before `full_clean`, keying any `validate_password` failure DIRECTLY to `password` (never the `__all__` sentinel). `current_user()` is a fixed query field returning the nullable session actor with no `get_queryset` re-run, typed via a bind-materialized lazy alias. Both share the Slice-1 auth substrate by call, and Worker 2's pass-2 `_lookup_or_conflict` primitive consolidated the two declare-surface helpers without perturbing Slice-1 login/logout ledger behavior. The fakeshop `accounts` app grows `register` + `me` with a full live round trip and the envelope/SDL/anonymous-null cases; the internals residue (plaintext-never-persisted on both sync+async, the direct-`password`-keying, the exclusion-seam marker preservation, factory cache identity, the reload-idempotence cycle including the M1 no-`UserType` second-finalize raise, the three distinct bind-arm messages, and `derive_register_fields`) is mirrored under `tests/auth/`. Focused suites green (223 package + 12 live). The two integration-pass carry-forward anchors are confirmed cleanly deferred.

### Spec changes made (Worker 1 only)

- `docs/spec-040-auth_mutations-0_0_13.md:72` (Status header) — updated "Slice 2 … in planning" → "Slice 1 and Slice 2 … final-accepted" to reflect that this pass finally accepts Slice 2 (the standing per-spawn status re-verification duty; stale-status prevention). No contract change.
- **Worker 2's `build_input` build-note — no spec edit required.** Worker 2 flagged that pinning `input_type_name` alone is insufficient (the materialized input class must also be named `RegisterInput` or the `data:` lazy ref raises `LazyType KeyError`), and added a `build_input` override. The spec already names both seams: Decision 6, line 1557 — "The **input** name is pinned to `RegisterInput` via the `input_type_name` / `build_input` name seams". The implementation is faithful to the already-worded contract; this is a pure implementation detail, not a spec gap. No edit.
