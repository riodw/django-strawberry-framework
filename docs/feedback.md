# Spec 040 — verified feedback for the spec update

Every item below was re-grounded against the already-scaffolded code (`django_strawberry_framework/auth/`
and `examples/fakeshop/apps/accounts/` exist as fail-loud TODO stubs) and the current spec text before
being written here. Each carries the confirmed problem, the source evidence, and the exact spec edit to
fold in. This supersedes and verifies the prior review round; the `(was P… #N)` tags preserve traceability.
Priority order — build-critical first, since this is the last pass before build.

Source refs use `path::Symbol` / `path #"substring"` per `AGENTS.md`. Spec anchors are by Decision /
section name, not line number.

## Build-critical — fold in before build

### 1. `bind_auth_mutations()` must be surface-keyed, not "any auth declaration exists" (was P1 #1)

CONFIRMED. `django_strawberry_framework/auth/mutations.py::bind_auth_mutations` (its TODO pseudocode)
resolves the user primary type once and materializes **both** `LoginPayload` **and** `LogoutPayload`
unconditionally whenever any auth declaration exists — only `current_user` is guarded. This:

- breaks the spec's own logout-only exemption (Decision 8): a logout-only schema would resolve
  `get_user_model()`'s primary type and raise when none is registered;
- materializes orphan / colliding payloads for partial schemas (a register-only schema would still emit
  `LoginPayload`, colliding with a consumer's own `Login` mutation of a different shape);
- is an internal spec tension: Decision 9 reads "resolves the user primary type, materializes
  `LoginPayload` and `LogoutPayload`" unconditionally, while Decision 8 exempts logout.

Spec edit: make the auth **declaration ledger surface-keyed** (which of login/logout/register/current_user
was declared) and rewrite Decision 9 so `bind_auth_mutations()` materializes only what the declared
surfaces need:

- `login`: resolve primary user type, materialize `LoginPayload`, validate the login holder;
- `logout`: materialize `LogoutPayload` (`object_type=None`), validate the logout holder, do **not** resolve
  the user primary type;
- `register`: resolve primary user type + validate (auth-specific message), then let `bind_mutations()`
  emit `RegisterPayload`/`RegisterInput`; do **not** materialize `LoginPayload`;
- `current_user`: resolve primary user type + materialize the alias; do **not** materialize login/logout
  payloads.

Add package tests: logout-only without a `UserType` (must succeed), and login-only / register-only /
current-user-only without a `UserType` (each must raise the auth-specific `ConfigurationError`).

### 2. The live permission-gate test plan conflicts with one-surface-per-process (was P1 #2)

CONFIRMED. The conflict rule (`auth/mutations.py::login_mutation` TODO #"reject conflicting second
declarations"; Decision 6 / Edge cases) makes a second `login_mutation(permission_classes=[...])` after the
default `login_mutation()` raise `ConfigurationError`. But the Test plan asks the **live** fakeshop suite to
cover both a default `me` (anonymous -> `null`) **and** a gated `me` (`IsAuthenticated`-style denial), plus a
gated `login` denial — all over the single aggregated `examples/fakeshop/config/schema.py`. Those cannot
coexist in one process/schema.

Spec edit: revise the Test plan so the fakeshop live suite covers only the **canonical default** surface
(`login`/`logout`/`register`/`me` at AllowAny). Move the custom-permission-carrier and exact-denial-string
variants into `tests/auth/` using isolated throwaway schemas with explicit `registry.clear()` between the
default and gated declarations. Note the `AGENTS.md` live-first placement rule explicitly: the gate variants
are genuinely unreachable live in one aggregate schema, so `tests/auth/` is the correct home (a documented
"unreachable from a real query" case, not a weakening of live-first).

### 3. The schema-reload helper must include the accounts schema (was P1 #3)

CONFIRMED, concrete. `examples/fakeshop/schema_reload.py::_PROJECT_APP_SCHEMA_MODULES` lists only
glossary/kanban/library/products/scalars. `examples/fakeshop/config/schema.py` does not yet compose accounts
(it carries a Slice-1 TODO to do so). The `schema_reload.py` module docstring itself documents the failure
mode: `importlib.reload(config.schema)` does not re-execute the cached app-schema modules, so a
post-`registry.clear()` rebuild that omits an app raises a `LazyType` `KeyError` (here on the auth payloads /
`UserType` lazy refs) or silently drops the auth surface.

Spec edit: the Slice-1 checklist must add `"apps.accounts.schema"` to `_PROJECT_APP_SCHEMA_MODULES` in the
**same slice** that composes accounts into `config/schema.py`, in dependency-safe order (accounts references
`auth.User` but no other fakeshop app — place it among the independent apps, before the `config.schema`
reload). Add an acceptance note that `reload_all_project_schemas()` preserves the accounts auth surface after
a `registry.clear()`.

### 4. The conflict/cache key must exclude field-presentation kwargs (was P2 #4)

CONFIRMED — and it is a spec-wording bug. Edge cases #"Two calls to the same factory, same args" states "the
same normalized argument set returns the cached ... A different-args call is the conflicting-declaration
raise." Taken literally that is too broad: the factories accept `description` / `deprecation_reason` /
`directives` (`auth/mutations.py::login_mutation`), so `login(description="A")` vs `login(description="B")`
would false-raise `ConfigurationError`, even though presentation metadata is per-field and does not affect
generated types.

Spec edit: pin the conflict/cache key to the **schema-affecting declaration args only** — `permission_classes`
(and any future payload/type-affecting arg). `description` / `deprecation_reason` / `directives` are
per-field `strawberry.field` kwargs, applied to each field and **not** part of the conflict key. Correct
Decision 6 and the Edge-cases wording from "different args" to "different `permission_classes`". State that
the signature helper partitions three arg classes: resolver GraphQL args | declaration args | Strawberry
field kwargs.

### 5. Slice 1's DoD/test-plan references Slice-2-only surfaces (was P3 #3)

CONFIRMED. `register_mutation()` and `current_user()` raise `NotImplementedError` until Slice 2
(`auth/mutations.py::register_mutation`, `auth/queries.py::current_user`), yet the Slice-1 DoD and Test plan
require "the register-arm error pinned distinct from login's" and validation across "all three user-typed
surfaces." Register cannot be declared in Slice 1, so those tests are unrunnable there.

Spec edit: Slice 1 tests only the login/logout substrate reachable through Slice-1 factories. Move the
register-arm bind-error test and the "all three user-typed surfaces" validation coverage to Slice 2. Keep the
bind **ordering** (`bind_auth_mutations()` before `bind_mutations()`) wired in Slice 1, but exercise the
register-arm branch only in Slice 2 when register exists.

## Also fold in — confirmed, lower severity

### 6. The register password seam must preserve the provided-marker (was P2 #2)

CONFIRMED; already anticipated by the scaffold. `django_strawberry_framework/mutations/resolvers.py::_model_decode_step`
computes the create-path `full_clean` exclude from provided attrs (`::_provided_attr_names` ->
`::_unprovided_exclude`), so naively removing `password` before decode would mark it **unprovided** and drop
it from validation. The scaffold TODO at `resolvers.py::_model_decode_step #"add a small reusable exclusion
seam"` already names this and requires the seam to "preserve ... the AR-H2 exclude calculation." Practical
impact on the default `auth.User` is low (password validation is length-only), but the seam must be right.

Spec edit: Decision 6 should model the register seam as "extract protected input value **with its
provided-marker preserved**," not merely "pop password from the model attrs" — thread
`excluded_input_fields` into `_decode_relations` so the excluded value is captured while the AR-H2 exclude
calculation still treats `password` as provided. Require a focused helper-level test of the seam.

### 7. No `AllowAny` class exists — fix the "AllowAny helper path" wording (was P2 #3)

CONFIRMED. There is no `class AllowAny` anywhere; "AllowAny" is used only as semantics (empty class list). The
`login` TODO correctly names `_validate_permission_classes(..., unset_default=())`
(`django_strawberry_framework/mutations/sets.py::_validate_permission_classes`); the `logout` TODO at
`auth/mutations.py::logout_mutation #"AllowAny helper path"` is the loose wording that could mislead an
implementer into minting a new public `AllowAny` primitive.

Spec edit: define the default as "empty permission-class list / allow-all semantics"; do not add an
`AllowAny` class; align all wording (Decision 5, the factory TODOs) on the `unset_default=()` / empty-list
convention.

### 8. Pin the holder `__name__`s for stable denial-string tests (was P2 #5)

CONFIRMED. `django_strawberry_framework/mutations/resolvers.py::authorize_or_raise` builds
`f"Not authorized to {operation} {target}."` where
`target = getattr(mutation_cls._primary_type, "__name__", mutation_cls.__name__)`. For `logout`
(`_primary_type is None`) the denial string is the **holder** `__name__`, which the spec leaves as "chosen
sensibly" but unpinned.

Spec edit: pin the concrete holder `__name__` for login/logout/register/current_user (logout most of all,
since its denial string IS the holder name), and document the exact expected denial strings — or restrict the
exact-string assertions to the stable segment.

### 9. Register field derivation — factor a directly-testable helper; the rule is not fully explicit (was P2 #1, softened; folds in P3 #2)

CONFIRMED with nuance. The prior framing ("implicit / risks broken input types") overstates it:
`django_strawberry_framework/mutations/inputs.py::editable_input_fields` already raises `ConfigurationError`
naming field + model for unknown/non-editable fields, already maps a forward FK to `<field>_id`, and already
includes forward M2M. The real gap: the derivation reads `get_user_model()` inline
(`auth/mutations.py::register_mutation` TODO), so it cannot be unit-tested with a test-scoped model without a
full `AUTH_USER_MODEL` swap.

Spec edit: factor the derivation as a helper taking a model argument (e.g. `derive_register_fields(user_model)
-> tuple[str, ...]`) so the default AND a custom-`USERNAME_FIELD` / custom-`REQUIRED_FIELDS` model test
directly — the Test plan already says "a test-scoped model." State the exact rule: `USERNAME_FIELD`, then each
distinct `REQUIRED_FIELDS` entry in order, then `password` exactly once; unsupported/non-editable/reverse
fields rejected as a bind-time `ConfigurationError` naming field + model (delegating to
`editable_input_fields`, not re-implementing). Do **not** require a second Django project / `AUTH_USER_MODEL`
swap for coverage.

### 10. `node`/`result` wording — drop `current_user` from this item (was P2 #6, corrected)

CONFIRMED with a correction: `current_user` returns the user type **directly** (`me: UserType`) with no
`node`/`result` slot, so it does not belong in this item. Decision 5 already says "`node` / `result` slot";
only the SDL example and a few prose spots hard-code `node` (correct for the Relay-backed fakeshop
`UserType`).

Spec edit: keep `node`/`result` in generic contract/GLOSSARY text for `login`/`register` payloads; keep
`node` only in fakeshop-specific SDL where `UserType` implements `relay.Node`
(`payload_object_slot(primary)` returns `result` for a non-Relay primary,
`django_strawberry_framework/mutations/inputs.py::payload_object_slot`); ensure tests do not encode the
Relay-only slot name as the generic contract.

## Verified as a non-issue — do not action

### 11. The `types/relay.py` setting anchor is not a spec-040 concern (was P3 #1)

Claims verified TRUE and require no spec-040 edit: auth adds no `DJANGO_STRAWBERRY_FRAMEWORK` settings key
(Decision 2), and `django_strawberry_framework/types/relay.py::_resolve_globalid_strategy` runs at
finalization inside `::install_globalid_typename_resolver` (the installed closure captures an
already-resolved strategy), not per-query. This was a correct rebuttal of an out-of-scope `RELAY_GLOBALID_STRATEGY`
concern; nothing in spec-040 changes.

## Gaps the prior round did not cover — fold in

### 12. Custom permission classes receive the bare holder as the `mutation` argument

`django_strawberry_framework/mutations/sets.py::DjangoMutation.check_permission #"type(self)"` passes the
permission-holder class as the `mutation` positional to `has_permission(info, mutation, operation, data,
instance)`. For the model-less `login`/`logout`/`current_user` holders that object has no `Meta.model` /
`_resolve_model`, so any consumer gate that introspects `mutation` breaks at request time. The spec documents
this only for `DjangoModelPermission`, understating a general hazard against the Goal-3 "compose with the
permissions surface" promise.

Spec edit: broaden the Decision 5 caution to the general rule — gates on the model-less auth fields must key
on `info` / `operation` / `data`, never on introspecting the `mutation` object.

### 13. Confirm `registry.clear()` resets the holder / rider cache (reload idempotence)

The "one declaration per process" design returns a cached permission holder (login/logout/current_user) and
a cached `Register` rider. `registry.clear()` clears the auth **declaration** ledger via its
`TypeRegistry.clear()` hand row, but if the same-args holder cache is a separate module dict it will not be
reset — a second finalize after `registry.clear()` (the complete-reload fixtures' path) could then see a
stale holder or a spurious conflicting-declaration raise that persists across the clear.

Spec edit: pin that the holder / rider cache is drained by `registry.clear()` (or is the declaration ledger
itself), and that the reload-idempotence test asserts a clean re-declaration after a clear — specifically
that a prior conflicting-`permission_classes` raise does not survive the clear.
