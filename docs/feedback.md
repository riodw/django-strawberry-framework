# Spec Review (DRY / helper-reuse pass): Auth Mutations spec-040-auth_mutations-0_0_13

Deep review of `django_strawberry_framework/utils/` (all 10 modules) plus the sibling
write-stack / envelope helpers a `DjangoMutation` rider inherits, mapped against the
**planned** `django_strawberry_framework/auth/` surface in
`docs/spec-040-auth_mutations-0_0_13.md`. The auth module does not exist yet, so this
is forward-looking: the goal is that the eventual Slice-1..3 code **routes through the
existing single-sited helpers and never re-spells them**.

The spec is already unusually DRY-conscious and names most reuse points inline. This
review (a) hardens those into an enforceable directive list so the implementation
cannot drift, (b) flags the handful of places the prose describes logic **without**
naming a helper (the real drift hazards), (c) records the deliberate **non**-reuse
points where over-sharing would be a *bug*, and (d) lists the small promote-to-shared
opportunities the auth work motivates.

Scope note: `login` / `logout` / `current_user` are **fixed field factories, not
`DjangoMutation` subclasses**, so they get *nothing* for free -- every reuse below is a
call they must make explicitly. `register` is a `DjangoMutation` rider, so it inherits
the write stack and must only override the two step lambdas.

---

## 1. Reuse map -- the canonical helper each concern MUST route through

| Concern | Canonical helper | Defined in | Who calls it today |
|---|---|---|---|
| Resolve request from `info` | `request_from_info(info, family_label=...)` | `utils/permissions.py:74` | `DjangoModelPermission.has_permission` (`mutations/permissions.py:94`) |
| Reject async hook in a sync context | `reject_async_in_sync_context(...)` -> `SyncMisuseError` | `utils/querysets.py:58` / `:35` | `authorize_or_raise` (`resolvers.py:1263`), `DjangoMutation.check_permission` (`sets.py:1000`) |
| Detect an async callable (partial-aware) | `is_async_callable(value)` | `utils/typing.py:20` | read-side field factories, GlobalID validator |
| Walk provided input fields (UNSET-strip) | `iter_provided_input_fields(data)` | `utils/inputs.py:386` | `_decode_relations` (`resolvers.py:262`) |
| Build the `@strawberry.input` class | `build_strawberry_input_class(name, triples)` | `utils/inputs.py:409` | `build_mutation_input` (`mutations/inputs.py`) |
| Derive an input type name | `generated_input_type_name(...)` + `pascalize_token` / `graphql_camel_name` | `utils/inputs.py:228/201/188` | `mutation_input_type_name` (`mutations/inputs.py:344`) |
| Pin a generated class as a module global | `materialize_generated_input_class(...)` | `utils/inputs.py:470` | `materialize_mutation_input_class` (`mutations/inputs.py:133`) |
| Own a `(ledger, materialize, clear)` namespace trio | `make_input_namespace(module_path, family_label)` | `utils/inputs.py:106` | `mutations/inputs.py` |
| Validate a `Meta.fields`/`exclude` sequence | `normalize_field_name_sequence(...)` | `utils/inputs.py:255` | `_validate_meta` (`sets.py:835`) |
| Resolve a `DjangoType`'s model / seed a queryset | `model_for` / `initial_queryset` | `utils/querysets.py:94/108` | `locate_instance`, `refetch_optimized` |
| FieldError leaf ctor | `field_error(path, messages, codes=)` | `mutations/resolvers.py:921` | every Django/DRF mapper |
| Django `ValidationError` -> envelope | `validation_error_to_field_errors(exc)` | `mutations/resolvers.py:971` | `_full_clean_or_field_errors` |
| `IntegrityError` -> envelope | `save_or_field_errors(callable)` | `mutations/resolvers.py:1303` | `_model_write_step` (`:1193`) |
| `"__all__"` sentinel | `NON_FIELD_ERROR_KEY` | `mutations/inputs.py:71` | `field_error` empty-path branch |
| Write-authorization gate | `authorize_or_raise(...)` | `mutations/resolvers.py:1238` | `run_write_pipeline_sync`, `_run_delete` |
| Normalize `permission_classes` (with default) | `_validate_permission_classes(..., unset_default=...)` | `mutations/sets.py:653` | Slice-2 Meta validation |
| One-boundary async wrapper (`thread_sensitive=True`) | the `sync_to_async(sync_body, ...)` wrapper | `mutations/resolvers.py:~1402` | `resolve_mutation_async`, `resolve_form_async` |
| Payload slot rule / payload builder | `payload_object_slot` / `build_payload_type` | `mutations/inputs.py:563/573` | `bind_mutations` |
| Lazy return ref for a resolver | `_lazy_ref(type_name, module_path)` | `mutations/fields.py:121` | `DjangoMutationField` signature build |
| Signature injection idiom | `_resolve.__signature__` / `__annotations__` | `mutations/fields.py:236-237` | `DjangoMutationField` |
| Named declaration ledger | `make_declaration_registry(label)` | `mutations/sets.py:426` | model / form / serializer flavors |
| Subsystem-clear registration + pre-bind drain | `register_subsystem_clear` / `iter_subsystem_clears` | `registry.py` / `types/finalizer.py` | every generated-input namespace |
| Resolve primary `DjangoType` for a model | `registry.primary_for(model)` | `registry.py:314` | `_resolve_primary_type` |

---

## 2. DRY directives (the "ways") -- enforce each at implementation time

### D1 -- Request resolution: one seam, one label
Every auth resolver (`login`, `logout`, `current_user`) and the register permission
path must read the request via `request_from_info(info, family_label="AuthMutation")`
(`utils/permissions.py:74`). **Never** re-spell `getattr(info.context, "request", ...)`
or the bare-`HttpRequest` fallback -- that branch is precisely why the helper exists and
is family-neutral (no `.apply` suffix, per its CR-5 note). Use one label string constant
for all auth surfaces so the error wording cannot drift between fields.

### D2 -- Async permission-hook rejection: reuse by call, reuse the recourse string
The permission holder binds `check_permission = DjangoMutation.check_permission`
directly, so the async-hook guard (`reject_async_in_sync_context` +
`_PERMISSION_ASYNC_RECOURSE`, `mutations/permissions.py:52`) is reused **by call**. Do
**not** author a new recourse sentence for auth and do **not** re-spell the
close-the-coroutine-and-raise logic. The same guard must still fire inside the
`sync_to_async(thread_sensitive=True)` worker (a sync context) -- verified reachable
because `check_permission` runs there.

### D3 -- Permission holder: bind the real method, normalize through the real validator, single-site the synthesis
The module-internal holder is correct to (a) bind `DjangoMutation.check_permission`
rather than re-implement the iterate-classes-and-call loop, and (b) build its
`_mutation_meta` snapshot via `_validate_permission_classes(..., unset_default=())`
(`mutations/sets.py:653`) so the AllowAny default rides the same normalization every
mutation uses. **Additional DRY obligation not spelled in the spec:** the holder is
synthesized for all three of `login` / `logout` / `current_user`; single-site that
synthesis in ONE `_make_permission_holder(operation, primary_type, permission_classes)`
helper inside `auth/`, not three near-identical class bodies. The only per-field inputs
are the operation string and the `_primary_type` (user primary, or `None` for `logout`).

### D4 -- Gate + denial message: reuse `authorize_or_raise` and the existing fallback
All four surfaces gate through `authorize_or_raise(holder_or_mutation, info, operation,
data, instance=...)`. The denial message must ride `authorize_or_raise`'s existing
`f"Not authorized to {operation} {target}."` formula with the **existing**
`_primary_type is None` -> class `__name__` fallback (the same path the plain-form
`"Not authorized to form <FormClass>."` uses). Do **not** add an auth-specific message
formatter -- pick holder `__name__`s so the fallback reads sensibly instead.

### D5 -- Payloads: one builder, the existing emit ledger, no new row
`LoginPayload` and `LogoutPayload` must be built by `build_payload_type(...)` with the
slot from `payload_object_slot(primary)` (`mutations/inputs.py:563/573`) and materialized
onto the **existing** `mutations.inputs` emit ledger. Do **not** hand-construct payload
classes and do **not** add a `register_subsystem_clear` row for them -- importing
`auth/mutations.py` transitively imports `mutations/inputs.py`, whose row self-registers
(spec-039 F10). `RegisterPayload` is emitted automatically by the unchanged machinery off
the rider's `__name__ = "Register"`; do not name it explicitly anywhere.

### D6 -- register decode: reuse the UNSET-strip walk + the model decode; only the password is auth-specific
The rider's `decode_step` must reuse `iter_provided_input_fields(data)`
(`utils/inputs.py:386`) for the provided-field walk and the existing relation-decode
path -- it must **mirror** `_model_decode_step`'s `(target, m2m_assignments, exclude)`
result, appending `raw_password` as the 4th tuple element. The ONLY auth-specific delta
is keeping `password` out of the `model(**scalar_and_fk_attrs)` construction. **Prefer
parameterizing `_model_decode_step` with an extra-`exclude` (e.g. `{"password"}`) over
forking a second decoder** -- a forked walk is the classic place the UNSET-strip / raw
`None`-vs-omitted rule drifts. Do not re-spell the field iteration or the relation decode.

### D7 -- register write: reuse the full_clean/save/IntegrityError path; only validate+hash is auth-specific
`write_step` must delegate the `full_clean()` + `save()` + IntegrityError mapping to the
shared path (`save_or_field_errors` at `resolvers.py:1303` and the
`_full_clean_or_field_errors` body). The only auth-specific steps are `validate_password`
and `user.set_password(raw_password)` **before** `full_clean()`. The duplicate-username
race is already covered by the inherited `save_or_field_errors` -- add no auth-specific
IntegrityError handling.

### D8 -- Error keying: reuse the leaf ctor; the mapper bypass is a *correct* non-reuse
- register's password failure must call `field_error("password", exc.messages,
  codes=[...])` (`resolvers.py:921`) directly. It must **deliberately bypass**
  `validation_error_to_field_errors`, because `validate_password` raises a list-style
  `ValidationError` that the generic mapper keys to `NON_FIELD_ERROR_KEY` ("__all__"),
  not `password`. This is a documented, load-bearing non-reuse -- keep the comment.
- `login`'s undifferentiated failure must build its one error via `field_error` with an
  empty path (which normalizes to `NON_FIELD_ERROR_KEY`) -- **never** hard-code the
  `"__all__"` string.

### D9 -- register re-fetch: ride the inherited path, add nothing
The payload re-fetch is `refetch_optimized` (by-pk, G2 gate, no visibility) inherited via
`run_write_pipeline_sync`. Do **not** add a bespoke re-fetch, and do **not** re-run
`get_queryset` -- the "actor just wrote the row" exception is exactly why the inherited
path skips visibility. `login` and `current_user` must not re-fetch at all (see D-N1).

### D10 / D11 -- register input: name via the Meta seams, materialize via the inherited helper
Pin `RegisterInput` through the existing `input_type_name` / `build_input` Meta seams
(not a bespoke name string), let `mutation_input_type_name` -> `generated_input_type_name`
(`utils/inputs.py:228`) + `pascalize_token` / `graphql_camel_name` derive field names, and
materialize through the inherited `materialize_mutation_input_class`
(`mutations/inputs.py:133`). Do **not** create a new input namespace for register -- its
input lives in `mutations.inputs` like every other mutation input.

### D12 -- current_user (and login/logout) return typing: reuse the field-family idiom, single-site auth field construction
`current_user`'s nullable lazy return annotation must be attached with the **same**
signature-injection idiom `DjangoMutationField` uses (`mutations/fields.py:236-237`), and
the `Annotated[<name>, strawberry.lazy(<module>)]` ref must be built by
`_lazy_ref(type_name, module_path)` (`mutations/fields.py:121`), **not** hand-spelled.
The same is true of `login`/`logout` payload return refs. Single-site auth's
field-dispatcher construction in ONE helper so all three fields share the
resolve-request -> gate -> work -> annotate skeleton. (See P1/P2 for promoting `_lazy_ref`
and the injection assignment so they are not copied across `mutations/` and `auth/`.)

### D13 -- CurrentUserAlias namespace: reuse `make_input_namespace`, do not hand-roll setattr/delattr
The spec describes `bind_auth_mutations()` doing `setattr(auth.queries,
"CurrentUserAlias", primary_type)` plus a hand-written clear. That is exactly the
`(ledger, materialize_fn, clear_fn)` trio `make_input_namespace(
"django_strawberry_framework.auth.queries", "AuthMutation")` (`utils/inputs.py:106`)
returns -- `materialize_fn` does the `setattr` (via `materialize_generated_input_class`),
`clear_fn` empties the ledger. Build the alias namespace through it and register
`clear_fn` via `register_subsystem_clear`. Because the clear is a pre-bind row, the
ledger is empty before each re-materialize, so the reload case (a *different* `UserType`
class object on the second finalize) will not trip the distinct-class collision guard.
This replaces bespoke lifecycle code with the blessed parked-global path.

### D14 -- Auth declaration ledger: `make_declaration_registry`, not a hand-rolled list
The module-level auth ledger must be a `make_declaration_registry("AuthMutation")`
instance (`mutations/sets.py:426`), so the every-call, identity-deduped re-record clause
(and the `TypeRegistry.clear()` drain) is the same one the model / form / serializer
flavors use. The register rider records into BOTH the mutation ledger (via its
`DjangoMutation` declaration) and this auth ledger on every call -- both through
`make_declaration_registry.register`, never a bespoke dedup.

### D15 -- Clear wiring: reuse the two existing seams, do not invent a third
- The current_user alias emit ledger: `register_subsystem_clear` (pre-bind drain via
  `iter_subsystem_clears`), per D13.
- The auth *declaration* ledger: a hand-written `_clear_if_importable`-style row inside
  `TypeRegistry.clear()`, sitting beside `clear_mutation_registry` /
  `clear_form_mutation_registry`. Declarations must survive the pre-bind reset, so this
  is a declaration-clear row, NOT a `register_subsystem_clear` row -- match the existing
  split exactly.

### D16 -- Primary-type lookup: route bind_auth_mutations through `registry.primary_for`
`bind_auth_mutations()`'s Decision-8 check must resolve the user primary via
`registry.primary_for(get_user_model())` (`registry.py:314`) -- the same getter
`_resolve_primary_type` uses -- so "what counts as a registered primary" is single-sited.
Only the *raise message* differs (auth-specific vs the generic `_resolve_primary_type`
wording); do not re-derive the lookup.

### D17 -- Async boundary: match spec-036 AR-M4, single-site auth's boundary
Auth's async fields must wrap the whole gate-then-work block in exactly ONE
`sync_to_async(thread_sensitive=True)` call per resolution (matching the contract at
`mutations/resolvers.py:~1402`), never a per-step boundary. Single-site that boundary in
one auth helper shared by the three async resolvers. The mutation wrapper itself is
mutation-shaped (takes `mutation_cls, data, id`), so auth cannot call it directly -- see
P3 for optionally promoting a truly generic "run this sync callable in one
thread-sensitive boundary" primitive both can share.

### D18 -- Async-callable detection: only `is_async_callable`
If any auth code needs to test whether a consumer-supplied callable is async (e.g. a
custom permission class), it must use `is_async_callable` (`utils/typing.py:20`, which is
`functools.partial`- and `__call__`-aware), never a bare `inspect.iscoroutinefunction`.
(Runtime coroutine *results* are still handled by `reject_async_in_sync_context` per D2 --
these are two different checks; use each where the write stack already does.)

### D19 -- SyncMisuseError: import the public export, never redefine
Auth must import `SyncMisuseError` from its public path
(`django_strawberry_framework.SyncMisuseError`, re-exported from `.types`) rather than
declaring a new exception -- it is raised only via the reused guard in D2 anyway.

---

## 3. Deliberate NON-reuse -- over-DRYing these is a *bug*

These are places where a well-meaning "share the helper" refactor would introduce a
defect. Call them out in code comments so a later reviewer does not "fix" them.

### D-N1 -- current_user / login must NOT scope through the visibility helpers
`current_user` and `login` return the **actor themselves** (`request.user` / the
freshly-authenticated user), not a lookup of other rows. They must **not** call
`apply_type_visibility_sync` / `initial_queryset` / any `*_related_queryset` helper. A
directory-shaped `UserType.get_queryset` ("non-staff see only public profiles") would
otherwise make `me` return `null` for the logged-in user -- breaking the first query every
authenticated SPA fires. This "actor-not-lookup" exception is the same reasoning behind
register's no-visibility re-fetch. (Same class of judgment as the recorded
`initial_queryset-not-for-filterset-visibility-seed` finding: a helper that *looks*
reusable here is semantically wrong.)

### D-N2 -- register password error must NOT use `validation_error_to_field_errors`
Covered in D8; restated here because it is the single most likely "helpful" DRY mistake:
the generic mapper keys the list-style `validate_password` error to `"__all__"`, so
routing through it silently mis-keys every password-policy error.

### D-N3 -- register must NOT reuse the relation-visibility helpers
Because `Meta.fields` is narrowed to `(USERNAME_FIELD, *REQUIRED_FIELDS, "password")`,
register has **no** relation inputs, so `relation_kind` / `is_forward_many_to_many` /
`visible_related_object(s)` / `stringified_pks_present` / `pks_all_present` do not apply.
They come back for free via the inherited decode only if a consumer ever widens the Meta;
do not wire them in preemptively.

---

## 4. utils methods reviewed with NO auth touchpoint (completeness)

Confirmed not applicable to the auth surface as specified -- listed so the review is
exhaustive and so nobody "reuses" them where they do not belong:

- `utils/input_values.py` -- `iter_active_fields` / `is_inactive_value` /
  `iter_input_items`: FilterSet/OrderSet set-input traversal. Auth has no set inputs.
  (register's decode uses the *different* `iter_provided_input_fields` walk.)
- `utils/permissions.py` -- `active_permission_targets` / `active_permission_field_paths`
  / `active_related_branches` / `run_active_input_permission_checks` /
  `extract_branch_value` / `verbatim_path` / `invoke_permission_method`: the set-input
  permission walk. Auth authorizes at a single seam (`authorize_or_raise`), no walk.
- `utils/connections.py` -- all of it: no auth connections. (register's re-fetch rides
  `refetch_optimized`, not connection windowing.)
- `utils/converters.py` -- `convert_with_mro`: form/serializer field-conversion dispatch.
  register uses model-column input generation.
- `utils/relations.py` -- see D-N3 (narrowed Meta, no relations).
- `utils/strings.py` -- `snake_case` / `pascal_case`: payload names are literals
  (`LoginPayload` / `LogoutPayload`) or already-Pascal (`Register` -> `RegisterPayload`).
- `utils/querysets.py` -- `normalize_query_source` / `post_process_queryset_result_*`:
  consumer-supplied queryset-source normalization. Auth fields return a single object or
  a payload, never a consumer queryset.
- `utils/typing.py` -- `unwrap_return_type` / `unwrap_graphql_type`: consumed by the
  optimizer at plan time (inherited), not by auth authoring.
- `utils/inputs.py` -- `GeneratedInputArgumentsFactory` / `clear_generated_input_namespace`
  / `iter_set_subclasses` / `_safe_import` / `build_lazy_input_annotation` /
  `make_shape_build_cache` / `resolve_effective_fields` / `guard_dropped_required`: the
  set-family BFS graph and the form/serializer effective-field narrowing. register uses
  the model flavor's light path (inherited); the set-family machinery does not apply.

---

## 5. Promote-to-shared candidates the auth work motivates

Small single-siting moves so `auth/` becomes the *second* consumer instead of a copy.
Each is low-risk and keeps the pinned wording byte-identical.

- **P1 -- promote `_lazy_ref`.** `mutations/fields.py::_lazy_ref` (build
  `Annotated[name, strawberry.lazy(module)]`) is exactly what auth's field factories need
  for their payload / alias return refs. Lift it to shared machinery (`utils/typing.py`
  or a new `utils/fields.py`) and have `mutations/fields.py` import it, so the ForwardRef
  form is defined once. (`utils/inputs.py::build_lazy_input_annotation` is the *set*
  variant with a subclass check + ledger -- keep that separate; the auth need is the
  bare field-return ref.)
- **P2 -- promote the signature-injection assignment.** A tiny
  `inject_resolver_signature(fn, signature, annotations)` wrapping the
  `fn.__signature__ = ...; fn.__annotations__ = ...` pair (`mutations/fields.py:236-237`)
  so auth does not copy the 2-line idiom. The *signature builder* stays mutation-shaped;
  only the assignment is generic.
- **P3 (optional) -- a generic one-boundary async primitive.** Factor the
  `await sync_to_async(fn, thread_sensitive=True)(...)` core out of the mutation-shaped
  wrapper (`resolvers.py:~1402`) into `run_in_one_sync_boundary(fn, *args)` so both the
  mutation async entry and auth's async fields share the boundary contract rather than
  each spelling `sync_to_async(..., thread_sensitive=True)`. Only do this if it does not
  disturb the pinned spec-036 AR-M4 wording.
- **P4 (intra-auth) -- `_make_permission_holder`.** Per D3, one holder factory rather
  than three; keeps the duck-typed `_mutation_meta` shape single-sited within `auth/`.

---

## 6. Implementation DoD checklist

- [ ] `request_from_info(info, family_label="AuthMutation")` at every auth resolver; no re-spelled `info.context.request` access. (D1)
- [ ] Permission holder binds `DjangoMutation.check_permission`; `_mutation_meta` built via `_validate_permission_classes(..., unset_default=())`; synthesis single-sited in `_make_permission_holder`. (D3/P4)
- [ ] No new async-permission recourse string; `_PERMISSION_ASYNC_RECOURSE` reused via the bound `check_permission`. (D2)
- [ ] `authorize_or_raise` for all four surfaces; denial message rides the existing `_primary_type`/`__name__` fallback. (D4)
- [ ] `LoginPayload`/`LogoutPayload` via `build_payload_type` + `payload_object_slot` on the existing `mutations.inputs` emit ledger; no new clear row; `RegisterPayload` never named explicitly. (D5)
- [ ] register `decode_step` reuses `iter_provided_input_fields` + mirrors `_model_decode_step` (prefer extra-`exclude` for `password` over a forked decoder). (D6)
- [ ] register `write_step` delegates full_clean/save/IntegrityError to `save_or_field_errors` + `_full_clean_or_field_errors`; only `validate_password` + `set_password` are auth-specific. (D7)
- [ ] register password error uses `field_error("password", ...)` and deliberately bypasses `validation_error_to_field_errors`; `login` `"__all__"` error uses `field_error` empty-path -> `NON_FIELD_ERROR_KEY`. (D8)
- [ ] register re-fetch rides inherited `refetch_optimized`; `login`/`current_user` do no queryset work. (D9/D-N1)
- [ ] `RegisterInput` named via the `input_type_name`/`build_input` Meta seams; materialized via inherited `materialize_mutation_input_class`; no new input namespace. (D10/D11)
- [ ] current_user/login/logout return refs via `_lazy_ref` + the signature-injection idiom; auth field construction single-sited. (D12/P1/P2)
- [ ] `CurrentUserAlias` namespace built via `make_input_namespace`; `clear_fn` registered via `register_subsystem_clear`; no hand-rolled setattr/delattr. (D13)
- [ ] Auth declaration ledger is a `make_declaration_registry("AuthMutation")`; every-call re-record on both ledgers via `.register`. (D14)
- [ ] current_user alias uses the pre-bind `register_subsystem_clear` seam; the auth declaration ledger uses a `TypeRegistry.clear()` hand-row beside the mutation/form declaration clears. (D15)
- [ ] `bind_auth_mutations()` resolves the primary via `registry.primary_for(get_user_model())`; only the message differs from `_resolve_primary_type`. (D16)
- [ ] Async fields wrap gate-then-work in ONE `sync_to_async(thread_sensitive=True)` call, single-sited across the three. (D17/P3)
- [ ] `is_async_callable` for any async-callable detection; `SyncMisuseError` imported from the public path, never redefined. (D18/D19)
- [ ] Comments pin the deliberate non-reuse points (D-N1/D-N2/D-N3) so they are not "fixed" later.
