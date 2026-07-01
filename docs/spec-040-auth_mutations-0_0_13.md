# Spec: Auth mutations — `login_mutation` / `logout_mutation` / `register_mutation` + the `current_user` query helper in an opt-in `auth/` module, riding the frozen `FieldError` envelope and the `DjangoMutation` foundation, and closing the joint `0.0.13` cut

Planned for `0.0.13` (card [`WIP-ALPHA-040-0.0.13`][kanban]). This card adds the
package's **session-auth surface**: a new opt-in `django_strawberry_framework/auth/`
module shipping the three most common Django auth flows as mutations —
`login_mutation()`, `logout_mutation()`, `register_mutation()` — plus the
`current_user()` query helper, each declared through the package's existing field-factory
idiom and composable with the shipped write-authorization seam
(`Meta.permission_classes` / `check_permission`,
[`DjangoModelPermission`][glossary-djangomodelpermission]). It is a Required
🍓 `strawberry-graphql-django` parity item (the card's own tag):
[`strawberry_django/auth/`][upstream-auth-mutations] ships a small auth-mutations
module (`login` / `logout` / `register` + `current_user`) so consumers don't have to
hand-wire `django.contrib.auth` into every schema, and without an equivalent every
migrant re-spells `authenticate()` / `auth.login()` / password hashing by hand — the
exact boilerplate class the package exists to absorb. It is the natural follow-on to
the mutation foundation [`DONE-036-0.0.11`][kanban] ([`spec-036`][spec-036]), which the
card's own body names as its hard dependency ("builds on DONE-036-0.0.11's mutation
infra").

The surface reuses, **byte-identical**, the contracts [`spec-036`][spec-036] froze and
[`spec-038`][spec-038] / [`spec-039`][spec-039] proved reusable across flavors: the
shared [`errors: list[FieldError]`][glossary-fielderror-envelope] envelope (populated
here from failed authentication, password-validator failures, and user-model
`full_clean()` errors), the generated `<Name>Payload` wrapper in both of its shapes
(the uniform `node` / `result` object slot for `login` / `register`, the model-less
`{ ok, errors }` shape for `logout` — both emitted by the ONE
`mutations/inputs.py::build_payload_type` builder [`spec-038`][spec-038] Decision 6
single-sited), the [`DjangoMutationField`][glossary-djangomutationfield] exposure
factory for the register flavor, the write-authorization seam
(`Meta.permission_classes` / `check_permission`), and the phase-2.5
materialize-before-`Schema` bind discipline. **The register flavor is deliberately NOT
a fourth write-flavor plumbing kit** ([`docs/feedback.md`][feedback]'s standing DRY
review of the three-flavor stack): it is a thin
[`DjangoMutation`][glossary-djangomutation] rider — a `create` over
`get_user_model()` with a password-hashing write step — that adds **no** new field
converter, **no** new input generator, and **no** new pipeline *orchestration*. It
does carry its own decode / write **step pair**: `DjangoRegisterMutation` overrides
the per-flavor resolver seam (`resolve_sync` / `resolve_async` — the same seam the
form and serializer flavors override) and rides the shared
`run_write_pipeline_sync` skeleton with a password-aware `decode_step` /
`write_step`, because the `036` create pipeline exposes **no** per-instance write
hook and its default steps would persist the raw password
([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
The only genuinely new machinery is the small session-auth resolver pair
(`django.contrib.auth.authenticate` / `login` / `logout` behind the envelope) and the
auth declaration ledger + `bind_auth_mutations()` phase-2.5 bind that materializes the
`LoginPayload` / `LogoutPayload` classes and the `current_user` return alias before
`strawberry.Schema(...)` runs.

**Version boundary** (see
[Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)):
unlike [`spec-039`][spec-039] (which shared the `0.0.13` patch line and deferred its
bump), `040` is now the **only non-Done card at `0.0.13`** — `039` is Done
([`DONE-039-0.0.13`][kanban], implemented on main with its release wording explicitly
deferred "to the joint `0.0.13` cut shared with `WIP-ALPHA-040-0.0.13`, which still
owns the version bump", [`spec-039`][spec-039] Decision 14 / F8). So this card's final
slice owns the `pyproject.toml` / `__version__` /
[`tests/base/test_init.py::test_version`][test-base-init] bump from `0.0.12` to
`0.0.13` (the lone-card posture of [`spec-038`][spec-038] Decision 14) **and** the
joint-cut release flips `039` deferred: the [`docs/GLOSSARY.md`][glossary]
[`SerializerMutation`][glossary-serializermutation] `shipped (0.0.13)` status, the
[`README.md`][readme] / [`docs/README.md`][docs-readme] "Coming next" → "Shipped
today" moves, and the `CHANGELOG.md` release bullets for **both** `0.0.13` cards
(the `CHANGELOG.md` edit lands only when the slice's maintainer prompt explicitly
requests it — [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly
instructed"; this spec describes the edit but cannot grant the permission).

Status: **PLANNED — no slice built yet.**
Three slices: Slice 1 (**the auth substrate + `login` / `logout`, earned live** — the
declaration ledger, the phase-2.5 bind, the payload materialization, the session
resolver pair, and the fakeshop `accounts` live surface land in one commit per the
[`examples/fakeshop/test_query/README.md`][test-query-readme] #"Coverage rule." /
[`docs/TREE.md`][tree] #"Coverage priority." live-first mandate), Slice 2
(**`register_mutation` + `current_user`, earned live** — the
`DjangoRegisterMutation` rider with password validation/hashing, the `current_user`
field, and their live tests in the same commit), and Slice 3 (**docs + the `0.0.13`
version cut + card wrap** — including the `039`-deferred joint-cut release flips).

Owner: package maintainer.

Predecessors: [`spec-039-serializer_mutations-0_0_13.md`][spec-039] (the
most-recently-shipped spec and the canonical voice / depth / section-layout reference;
also the sibling `0.0.13` card whose Decision 14 / F8 explicitly hands this card the
joint-cut version bump and release flips);
[`spec-038-form_mutations-0_0_12.md`][spec-038] (the lone-card version-bump Decision
this spec mirrors — its Decision 14 — and the source of the model-less
`{ ok, errors }` payload shape `logout` reuses and the
[`DenyAll`][mutations-permissions] deny-by-default posture the auth factories
deliberately invert);
[`spec-036-mutations-0_0_11.md`][spec-036] (the foundation `register` rides — the
[`FieldError` envelope][glossary-fielderror-envelope], the `<Name>Payload` uniform
slot, the [`DjangoMutationField`][glossary-djangomutationfield] factory, the
write-auth seam, and the by-pk-without-visibility payload re-fetch
[`mutations/resolvers.py::refetch_optimized`][mutations-resolvers] whose "the actor
just wrote the row" exception is exactly what a fresh registration needs);
[`spec-034-permissions-0_0_10.md`][spec-034] (the
[`get_queryset`][glossary-get_queryset-visibility-hook] visibility contract this card
must compose with — and, for `current_user`, deliberately NOT re-run,
[Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)).
[`docs/GLOSSARY.md`][glossary] carries [Auth mutations][glossary-auth-mutations] as
`planned for 0.0.13`; Slice 3 flips it to `shipped (0.0.13)` with the implemented
contract.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the [`WIP-ALPHA-040-0.0.13`][kanban]
  card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-07-01). Pinned: the
  canonical structured filename
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the card-scope
  boundary — session auth only, Channels / websocket auth deferred to the `0.0.14`
  router card, no token / JWT surface, no new `DjangoType` `Meta` key or settings key
  ([Decision 2](#decision-2--card-scope-boundary-session-auth-ships-channels--token-auth-stay-out-no-new-meta--settings-key));
  the four card-named factories at the `django_strawberry_framework.auth` submodule
  path with **no package-root re-export** (opt-in by import, the card's own DoD)
  ([Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export));
  the `auth/` module + `tests/auth/` mirror
  ([Decision 4](#decision-4--module-and-test-locations-auth-mirroring-the-upstream-trio-tests-auth-mirroring-source));
  the login / logout shapes on the frozen envelope with the **anonymous-allowed
  default** as the deliberate, documented inversion of the family's deny-by-default
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design));
  `register_mutation` riding [`DjangoMutation`][glossary-djangomutation] as a narrow
  `create` over `get_user_model()` with `validate_password` + `set_password` — not a
  fourth flavor
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor));
  `current_user` returning the session actor, nullable, without a
  [`get_queryset`][glossary-get_queryset-visibility-hook] re-run
  ([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset));
  the user-model primary-[`DjangoType`][glossary-djangotype] requirement validated
  loudly at bind
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind));
  the declaration ledger + `bind_auth_mutations()` phase-2.5 bind + the
  [`register_subsystem_clear`][registry] rows
  ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows));
  sync + async twin paths
  ([Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary));
  the session-transport constraints and the deliberate non-borrow of upstream's
  Channels fallback
  ([Decision 11](#decision-11--session-transport-constraints-sessionmiddleware--authenticationmiddleware-the-channels-fallback-is-not-borrowed));
  and **this card owning the `0.0.13` version bump + the joint-cut completion**
  ([Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)).
  Two card-body tensions are carried into
  [Risks and open questions](#risks-and-open-questions) rather than silently
  reconciled (the card's bare symbol list vs the factory-call consumer shape; the
  [`docs/TREE.md`][tree] target layout carrying no `auth/` row for this card), each
  with a preferred reading.
- **Revision 2** — applied a code-review pass ([`docs/feedback2.md`][feedback2];
  every finding re-verified against the package source before editing —
  `run_write_pipeline_sync`'s `decode_step` / `write_step` parameters, the
  hard-wired `_model_decode_step` / `_model_write_step` lambdas in
  `_run_pipeline_sync`, `_resolve_primary_type`'s generic no-DjangoType message,
  and `make_declaration_registry`'s identity dedupe were all confirmed).
  **Foundational (security / shape-setting) fixes:** **(P1)** the register
  password step now has a **named seam** — [`DjangoMutation`][glossary-djangomutation]
  exposes no per-instance write hook and its default create steps would persist
  the **plaintext** password, so `DjangoRegisterMutation` overrides
  `resolve_sync` **and** `resolve_async` and rides the shared
  `run_write_pipeline_sync` skeleton with a password-aware `decode_step` /
  `write_step` pair; the "no new pipeline / foundation unchanged" framing is
  corrected to "reuses the skeleton via a custom step pair," and the
  plaintext-never-persisted test is required on **both** the sync and async paths
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor));
  **(P2)** the user-type bind validation is made **reachable for `register`** —
  `bind_auth_mutations()` now runs **before** `bind_mutations()` in phase 2.5 and
  validates all three user-typed surfaces from the auth ledger with the
  auth-specific message, so the generic `_resolve_primary_type` error (naming
  `DjangoRegisterMutation` and the raw model class) can no longer pre-empt it,
  with a test pinning register's exact error distinct from login's
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)
  / [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows));
  **(P2)** the cached rider's reload story is pinned — **every**
  `register_mutation()` call re-registers the cached class into the mutation
  ledger (identity-deduped, so a live ledger is a no-op and a cleared one
  re-appends), closing the second-finalize path where `register` would silently
  drop out of the schema, with a finalize → `registry.clear()` → re-declare →
  finalize reload-idempotence test
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
  Plus: **(P3)** the consumer `UserType` field selection is cautioned as **the
  authenticated read surface** (exclude `password` and privilege columns; the
  GLOSSARY entry carries the caution)
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind));
  and **(P3)** Decision 5 now states plainly that `login` skips **both**
  visibility **and** the optimizer re-fetch (its node is the raw `authenticate()`
  instance, not optimizer-planned — asymmetric with `register`'s G2-planned
  re-fetch, deliberately)
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the
vocabulary used throughout the spec:

- [Auth mutations][glossary-auth-mutations] — the subject. The glossary already pins
  the planned contract: `login` / `logout` / `register` mutations plus a
  `current_user` query helper, **opt-in via explicit import** (not bundled into the
  default schema), composing with [`DjangoMutation`][glossary-djangomutation] and
  `django.contrib.auth`. Slice 3 flips the entry to `shipped (0.0.13)` with the
  implemented contract.
- [`DjangoMutation`][glossary-djangomutation] /
  [Input type generation][glossary-input-type-generation] /
  [`DjangoMutationField`][glossary-djangomutationfield] — the shipped
  [`spec-036`][spec-036] foundation the register flavor rides: `register_mutation()`
  synthesizes a `create`-operation [`DjangoMutation`][glossary-djangomutation]
  subclass over `get_user_model()`, its input generated by the **model-column
  generator unchanged** (narrowed to the safe registration field set,
  [Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)),
  exposed through the standard
  [`DjangoMutationField`][glossary-djangomutationfield] factory.
- [`FieldError` envelope][glossary-fielderror-envelope] — the shared error contract
  every mutation flavor returns, [`spec-036`][spec-036]-frozen. A failed
  authentication is one `"__all__"`-keyed entry (never a credential-enumerating
  split), a password-validator failure keys to `password`, and a user-model
  `full_clean()` / unique-username failure keys to its field — all through the same
  envelope, never a raised `GraphQLError`
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
- [`DjangoFormMutation`][glossary-djangoformmutation] — the `0.0.12` model-less
  sibling whose pinned `{ ok: Boolean!, errors: [FieldError!]! }` payload shape
  `logout` reuses (emitted by the same
  `mutations/inputs.py::build_payload_type(object_type=None)` builder), and whose
  [`DenyAll`][mutations-permissions] unset-default is the posture the auth factories
  deliberately invert
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
- [`DjangoModelPermission`][glossary-djangomodelpermission] — the family's
  write-authorization default and the seam the card's "composable with the existing
  permissions surface" DoD names. Every auth factory accepts `permission_classes=`
  and routes it through the same `check_permission` machinery; the auth **default**
  is the explicit empty list (AllowAny) because an auth surface that requires
  authentication is a contradiction — the deliberate, documented exception to the
  family's deny-by-default
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] /
  [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — the visibility
  seam this card composes with **and** deliberately steps around in two pinned
  places: `current_user` returns the session actor directly (running visibility
  against yourself is not a lookup,
  [Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)),
  and the register payload re-fetch rides
  [`refetch_optimized`][mutations-resolvers]'s existing by-pk-without-visibility
  contract (the `036` "the actor just wrote the row" exception — a visibility hook
  that hides non-staff users must not 404 the account it just created).
- [`Meta.primary`][glossary-metaprimary] / [`Meta.model`][glossary-metamodel] /
  [`DjangoType`][glossary-djangotype] — the payload / return type for `login`,
  `register`, and `current_user` resolves the user model's **primary**
  [`DjangoType`][glossary-djangotype] through the registry primary lookup, exactly as
  the write flavors do; a schema that declares an auth field without registering one
  is a bind-time [`ConfigurationError`][glossary-configurationerror]
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)).
- [`ConfigurationError`][glossary-configurationerror] /
  [`SyncMisuseError`][glossary-syncmisuseerror] — the validation / misuse exceptions
  this card raises: `ConfigurationError` at bind (no registered primary
  [`DjangoType`][glossary-djangotype] for the user model; an auth factory called
  after [`finalize_django_types`][glossary-finalize_django_types]) and the standing
  [`SyncMisuseError`][glossary-syncmisuseerror] discipline wherever the reused write
  pipeline meets an `async def` hook.
- [`finalize_django_types`][glossary-finalize_django_types] /
  [Definition-order independence][glossary-definition-order-independence] — the
  materialize-before-`Schema` discipline the auth bind rides: the factories record
  declarations at class-body time (when the user's primary type may not exist yet),
  and `bind_auth_mutations()` at phase 2.5 validates and materializes the payload /
  return-alias classes the factories' `strawberry.lazy` forward-refs resolve at
  schema build
  ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] /
  [`only()` projection][glossary-only-projection] — the register payload's post-save
  re-fetch rides the same `036` optimizer path, so the [`spec-035`][spec-035] G2
  mutation gate (keep `select_related` / `prefetch_related`, suppress `.only(...)`)
  comes for free.
- [`SerializerMutation`][glossary-serializermutation] — the sibling `0.0.13` card
  ([`DONE-039-0.0.13`][kanban]), implemented on main with its release-status wording
  deferred **to this card's cut**; Slice 3 flips its GLOSSARY status to
  `shipped (0.0.13)`
  ([Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)).
- [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] /
  [`TestClient`][glossary-testclient] — the `0.0.14` cards this one deliberately does
  not reach into: Channels / websocket login (upstream's `channels_auth` fallback)
  waits for the router card, and multipart / session test-client ergonomics wait for
  the test-client card
  ([Decision 11](#decision-11--session-transport-constraints-sessionmiddleware--authenticationmiddleware-the-channels-fallback-is-not-borrowed)).
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] — the `1.0.0`
  invariants this card must hold: the
  [`FieldError` envelope][glossary-fielderror-envelope] is shared across every
  mutation flavor (auth included), and no `DjangoType` `Meta` key is promoted (this
  card adds none).

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package-internal ledger / bind /
  validation mechanics under `tests/auth/` mirroring source; live consumer behavior
  over `/graphql/` when a realistic request reaches it — both Slice 1 and Slice 2
  land their live tests in the same commit as their resolvers); the
  settings-keys-only-when-needed rule (this card adds **no** settings key); the
  no-pytest-after-edits rule; the CHANGELOG-edit-permission rule at
  [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" —
  Slice 3's release-note edit must be named in its maintainer prompt.
- [`START.md`][start] — "Meta classes everywhere on consumer surfaces"; the auth
  factories keep the consumer surface decorator-free (one class-attribute assignment
  per field, the same shape as [`DjangoListField`][glossary-djangolistfield] /
  [`DjangoMutationField`][glossary-djangomutationfield]); also the "behaviorally we
  copy `strawberry-graphql-django`'s good ideas" rule — this card is the clearest
  case yet: the *capability set* is borrowed from
  [`strawberry_django/auth/`][upstream-auth-mutations] verbatim, the *shape* is the
  package's own envelope-first, factory-based, Meta-composable surface.
- [`CONTRIBUTING.md`][contributing] — the 100% coverage target (`fail_under = 100`);
  every resolver branch (failed auth, the anonymous logout, the password-validator
  envelope, the bind validation) earns coverage in `tests/auth/` plus the live
  fakeshop suite.
- [`docs/TREE.md`][tree] — the target layout does **not** yet reserve
  `django_strawberry_framework/auth/` for this card (a gap this spec records in
  [Risks](#risks-and-open-questions) and Slice 3 fixes); the test trees gain
  `tests/auth/` and the live `examples/fakeshop/test_query/test_auth_api.py`.
- [`GOAL.md`][goal] — the fakeshop target-example paragraph names "auth mutations
  exercised by the existing test users" as a growth direction; this card ships it,
  and Slice 3 updates the wording from future to present.

## Slice checklist

Each top-level item maps to one commit / PR. **Three slices: the auth substrate +
`login` / `logout` earned live (Slice 1), `register` + `current_user` earned live
(Slice 2), and docs + the `0.0.13` version cut + card wrap (Slice 3).** Slices 1 and 2
each land their resolvers **together with** their fakeshop live surface — required by
the [`examples/fakeshop/test_query/README.md`][test-query-readme] #"Coverage rule."
live-first mandate, so every consumer-reachable resolver line is earned by a real
`/graphql/` request at the commit it appears. Slice 3 is doc + version-cut only and
completes the joint `0.0.13` cut
([Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)).

- [ ] **Slice 1 — auth substrate + `login_mutation` / `logout_mutation`, earned live**
  - [ ] `django_strawberry_framework/auth/__init__.py` — the public factory
        re-exports (`login_mutation`, `logout_mutation`, `register_mutation`,
        `current_user`); **no package-root re-export**
        ([Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export)).
  - [ ] `django_strawberry_framework/auth/mutations.py` — the `login_mutation()` /
        `logout_mutation()` field factories (declaration-ledger recording +
        `strawberry.lazy` payload forward-refs + the sync/async resolver pair over
        `django.contrib.auth.authenticate` / `login` / `logout`), the
        `permission_classes=` seam with the explicit AllowAny default
        ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
  - [ ] The auth declaration ledger + `bind_auth_mutations()` wired into
        [`types/finalizer.py`][types-finalizer] phase 2.5 **before**
        `bind_mutations()` (the ordering that keeps the register-arm validation
        reachable), payload materialization through
        `mutations/inputs.py::build_payload_type` (the `LoginPayload` object
        slot resolved from the user model's primary
        [`DjangoType`][glossary-djangotype]; the `LogoutPayload` from
        `object_type=None`), and the ledger clear registered through
        [`registry.py::register_subsystem_clear`][registry]
        ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
  - [ ] Bind validation: a declared `login` (or `current_user` / `register`) with no
        registered primary [`DjangoType`][glossary-djangotype] for
        `get_user_model()` raises
        [`ConfigurationError`][glossary-configurationerror] naming the fix — fired
        from `bind_auth_mutations()` before `bind_mutations()` can raise the
        generic `_resolve_primary_type` message, with the register-arm error
        pinned distinct from login's
        ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)).
  - [ ] **In the same commit:** the fakeshop `apps/accounts/` live surface (a
        schema-only app declaring `UserType(DjangoType)` over `auth.User` + the auth
        `Query` / `Mutation` blocks, composed into
        [`config/schema.py`][config-schema]) and the live
        `examples/fakeshop/test_query/test_auth_api.py` login / logout coverage
        (happy path, wrong-credential envelope, anonymous logout, session-cookie
        round trip).
  - [ ] Mirrored package tests under `tests/auth/` for the residue a live query
        cannot drive (ledger idempotence / clear, bind validation, the
        post-finalize-declaration raise, async paths, the sessionless-request edge).
- [ ] **Slice 2 — `register_mutation` + `current_user`, earned live**
  - [ ] `auth/mutations.py` grows `register_mutation()` — synthesizing (and caching)
        a `DjangoRegisterMutation` subclass of
        [`DjangoMutation`][glossary-djangomutation] over `get_user_model()`,
        `operation = "create"`, `Meta.fields` narrowed to
        `(USERNAME_FIELD, *REQUIRED_FIELDS, "password")`, **overriding
        `resolve_sync` / `resolve_async`** to ride `run_write_pipeline_sync` with
        the password-aware step pair (pop `password` in the decode step; the write
        step runs
        `django.contrib.auth.password_validation.validate_password(password, user)`
        — failures → `password`-keyed [`FieldError`][glossary-fielderror-envelope]s
        — then `set_password` **before** `full_clean()` / `save()`; the `036`
        pipeline has no per-instance write hook to reuse), with **every** factory
        call re-registering the cached rider into the mutation ledger
        (identity-deduped; reload-safe)
        ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
  - [ ] `auth/queries.py` — the `current_user()` field factory: nullable
        session-actor return typed via a bind-materialized lazy alias, **no**
        [`get_queryset`][glossary-get_queryset-visibility-hook] re-run
        ([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)).
  - [ ] **In the same commit:** the fakeshop live surface grows `register` + `me`
        fields and [`test_auth_api.py`][test-query-readme] covers the full
        register → login → `me` → logout round trip, the duplicate-username
        envelope, the weak-password envelope (fakeshop's
        `AUTH_PASSWORD_VALIDATORS`), and the anonymous `me → null` case.
  - [ ] Mirrored package tests under `tests/auth/` for the internals (the
        password-hash write step with the **plaintext-never-persisted assertion on
        both the sync and async paths**, the validator → envelope mapping shapes,
        the factory cache identity, the **reload-idempotence cycle** (finalize →
        `registry.clear()` → re-declare → finalize, `register` present in the
        second schema), the register-arm no-`UserType` error message,
        custom-`USERNAME_FIELD` mapping).
- [ ] **Slice 3 — docs + the `0.0.13` version cut + card wrap**
  - [ ] The version quintet moves `0.0.12` → `0.0.13`: [`pyproject.toml`][pyproject],
        `__version__` in [`__init__.py`][init],
        [`tests/base/test_init.py::test_version`][test-base-init], the
        [`docs/GLOSSARY.md`][glossary] package-version line, and the
        `django-strawberry-framework` `version` entry inside `uv.lock`
        ([Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)).
  - [ ] The `039`-deferred joint-cut release flips land: the GLOSSARY
        [`SerializerMutation`][glossary-serializermutation] status →
        `shipped (0.0.13)`; [`docs/README.md`][docs-readme] / [`README.md`][readme]
        move the serializer flavor **and** the auth surface from "Coming next
        (`0.0.13`)" to "Shipped today" (README **Status** → `0.0.13`);
        [`CHANGELOG.md`][changelog] carries the `0.0.13` release bullets for both
        cards — **only when the maintainer prompt explicitly requests the
        `CHANGELOG.md` edit**.
  - [ ] [Auth mutations][glossary-auth-mutations] GLOSSARY entry flips to
        `shipped (0.0.13)` with the implemented contract (the four factories, the
        submodule-only import path, the AllowAny default and its rationale, the
        envelope semantics); the Index row updates; a submodule-exports note is
        added beside the `testing` note (auth symbols are **not** root exports,
        [Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export)).
  - [ ] [`docs/TREE.md`][tree] gains the `auth/` package rows, the `tests/auth/`
        tree, the fakeshop `accounts` app, and the live `test_auth_api.py` row
        (closing the target-layout gap recorded in
        [Risks](#risks-and-open-questions)); [`TODAY.md`][today] notes the shipped
        auth surface under its capabilities-not-exercised-by-products section (the
        `accounts` app owns the live demonstration); [`GOAL.md`][goal]'s fakeshop
        paragraph flips "auth mutations exercised by the existing test users" from
        future to shipped.
  - [ ] [`KANBAN.md`][kanban] card wrap: `WIP-ALPHA-040-0.0.13` → Done with the next
        `DONE-040-0.0.13` id and its `SpecDoc` pointing at this spec (kanban DB edit
        + `scripts/build_kanban_md.py` / `build_kanban_html.py` re-render, never a
        hand-edit).

## Problem statement

The package shipped its write side across three cards — the model-driven
[`DjangoMutation`][glossary-djangomutation] foundation ([`DONE-036-0.0.11`][kanban]),
the form flavor ([`DONE-038-0.0.12`][kanban]), and the serializer flavor
([`DONE-039-0.0.13`][kanban], implemented on main) — all returning the one frozen
[`FieldError` envelope][glossary-fielderror-envelope]. But the most common write a
Django app performs before any of those is **authentication**: log a user in, log
them out, create an account. Today a consumer of this package must hand-wire those
flows — a `@strawberry.mutation` resolver spelling
`django.contrib.auth.authenticate(...)` / `auth.login(...)`, a hand-built payload
type, hand-rolled password validation and hashing for registration, and a hand-typed
`me` query — re-deriving exactly the session semantics, error shapes, and
password-safety rules `django.contrib.auth` already defines. That is the boilerplate
class this package exists to absorb.

`strawberry-graphql-django` serves its consumers with a small
[`auth/` module][upstream-auth-mutations]: `login` / `logout` mutation fields over
`django.contrib.auth`, a `register` mutation subclassing its create-mutation base
with `validate_password` + `set_password`, and a [`current_user`
query][upstream-auth-queries] over a [`get_current_user(info)`
helper][upstream-auth-utils]. The card carries the Required 🍓 parity tag for exactly
that module (the [`KANBAN.md`][kanban] #"Decision: Alpha cards must claim upstream
parity" rule; `graphene-django` ships **no** auth module, so this is single-upstream
parity — honest, not fabricated). Without an equivalent, the package's migration
story leaks: a `strawberry-graphql-django` migrant loses a shipped surface, and every
consumer re-spells session auth by hand next to a package whose pitch is "the
boilerplate becomes `class Meta` and factories."

The work is **small in new machinery** because the mutation foundation froze the
reusable contracts for exactly this kind of rider: the envelope, both payload shapes
(the `node` / `result` object slot and the model-less `{ ok, errors }` pair), the
[`DjangoMutationField`][glossary-djangomutationfield] exposure factory, the
write-authorization seam, and the by-pk payload re-fetch. The genuinely new parts are
the session resolver pair (authenticate / login / logout behind the envelope), the
register rider's password step, the `current_user` field, and the small phase-2.5
bind that materializes the auth payloads — plus the release mechanics: this card
closes the joint `0.0.13` cut [`spec-039`][spec-039] explicitly deferred to it.

## Current state

A true description of the repo as this spec is authored:

- **The mutation foundation and both sibling flavors are on main.**
  [`mutations/sets.py`][mutations-sets] ships
  [`DjangoMutation`][glossary-djangomutation] with the overridable seam set
  (`_resolve_model` / `_validate_meta` / `build_input` / `input_type_name` /
  `input_module_path` / `resolve_sync` / `resolve_async`);
  [`forms/sets.py`][forms-sets] proves the rider pattern twice (the `ModelForm`
  rider and the model-less plain-form sibling with its pinned `{ ok, errors }`
  payload and [`DenyAll`][mutations-permissions] default); `rest_framework/`
  ([`spec-039`][spec-039], implemented on main) proves it a third time. The
  [`docs/feedback.md`][feedback] DRY review of that three-flavor stack is the
  standing warning this card heeds by **not** becoming a fourth flavor
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
- **The payload builder already emits both shapes this card needs.**
  `mutations/inputs.py::build_payload_type(mutation_name, *, object_type, object_slot)`
  emits the `node` / `result` object-slot payload (for `login` / `register`) and the
  model-less `{ ok, errors }` payload (for `logout`) from one builder + one
  materialize ledger ([`spec-038`][spec-038] Decision 6).
- **The re-fetch contract already carries the registration case.**
  [`mutations/resolvers.py::refetch_optimized`][mutations-resolvers] re-fetches the
  written row **by pk, without the visibility `get_queryset` filter** — the
  deliberate `036` "the actor just wrote the row" exception — so a freshly-registered
  anonymous user's payload cannot be hidden by a staff-only `UserType.get_queryset`.
- **The subsystem-clear seam exists.** [`registry.py`][registry] ships
  `register_subsystem_clear(module_path, attr)` with static string rows iterated via
  `_clear_if_importable` from both `TypeRegistry.clear()` and the
  [`types/finalizer.py`][types-finalizer] pre-bind reset block — the auth ledger
  registers its clear row there rather than adding a third hand-edited list
  ([`spec-039`][spec-039] P1.6 / M4).
- **No `auth/` module exists, and [`docs/TREE.md`][tree] does not reserve one.** The
  target package layout annotates every WIP/TODO-card path (`routers.py` for `041`,
  `middleware/` for `042`, `testing/client.py` for `043`, `extensions/` for `044`)
  but carries **no** `auth/` row for this card — a doc gap recorded in
  [Risks](#risks-and-open-questions) and fixed in Slice 3.
- **The version line reads `0.0.12`, and `039` explicitly handed this card the cut.**
  [`spec-039`][spec-039]'s status block: "Release deferred to the joint `0.0.13` cut
  shared with `WIP-ALPHA-040-0.0.13`, which still owns the version bump (`0.0.12` →
  `0.0.13`) and the public release-status flip (the GLOSSARY `shipped (0.0.13)`
  status, the `README.md` / `docs/README.md` 'Shipped today' move, the
  `CHANGELOG.md` bullets)." `040` is now the **only** non-Done card at `0.0.13`
  (verified against the re-rendered board), so the lone-card bump rule applies
  ([Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)).
- **The fakeshop example is auth-ready but has no auth surface.**
  [`config/settings.py`][config-settings] installs `django.contrib.auth` /
  `sessions` and the `AUTH_PASSWORD_VALIDATORS` set;
  [`create_users`][create-users] seeds permission-shaped test users (password
  `admin`); [`config/urls.py`][config-urls] wires Django's HTML login views — but no
  fakeshop app declares a `DjangoType` over `auth.User` and `/graphql/` exposes no
  auth field. [`config/schema.py`][config-schema] composes five app schemas and is
  the seam the new `accounts` surface plugs into.

## Goals

1. **Ship the four card-named symbols in an opt-in `auth/` module.**
   `login_mutation()`, `logout_mutation()`, `register_mutation()`, and
   `current_user()` — field factories at the `django_strawberry_framework.auth`
   submodule path, imported explicitly, never injected into a schema by default
   ([Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export)).
2. **Return the frozen envelope from every auth mutation.** Failed authentication,
   password-validator failures, and user-model validation failures are
   [`FieldError`][glossary-fielderror-envelope]s in the standard payloads — the
   uniform `node` / `result` slot for `login` / `register`, the pinned
   `{ ok, errors }` shape for `logout` — never top-level `GraphQLError`s
   ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
3. **Compose with the existing permissions surface.** Every factory accepts
   `permission_classes=` routed through the standard `check_permission` machinery;
   the auth default is the explicit AllowAny (the documented inversion of
   deny-by-default), and a consumer can gate any auth field (an invite-only
   deployment gates `register`) without new machinery
   ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
4. **Register safely by construction.** The generated registration input is narrowed
   to `(USERNAME_FIELD, *REQUIRED_FIELDS, "password")` — privilege-bearing columns
   (`is_staff`, `is_superuser`, `groups`, `user_permissions`) are structurally
   unreachable; the password is validated against `AUTH_PASSWORD_VALIDATORS` (with
   the constructed user instance, so similarity validators bite) and stored only
   through `set_password`
   ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
5. **Resolve the user type through the registry.** `login` / `register` /
   `current_user` type their user payload as the consumer's own primary
   [`DjangoType`][glossary-djangotype] over `get_user_model()` — validated loudly at
   bind
   ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)).
6. **Sync + async.** Both resolver paths ship for every field, with the session work
   behind one `sync_to_async(thread_sensitive=True)` boundary
   ([Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary)).
7. **Mirrored tests + live-first coverage.** `tests/auth/` mirrors the module for
   package-only internals; every consumer-reachable resolver line is earned by the
   live `test_auth_api.py` over `/graphql/` in the same commit it lands (the card's
   "Mirrored tests under `tests/auth/`" DoD plus the standing live-first mandate).
8. **Close the `0.0.13` cut.** The final slice bumps the version quintet and lands
   the `039`-deferred release flips
   ([Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)).

## Non-goals

- **Channels / websocket authentication.** Upstream's `channels_auth` fallback
  (login/logout against `request.consumer.scope`) is deliberately not borrowed until
  the `0.0.14` [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]
  card gives the package a Channels story
  ([Decision 11](#decision-11--session-transport-constraints-sessionmiddleware--authenticationmiddleware-the-channels-fallback-is-not-borrowed)).
- **Token / JWT auth.** The card and its upstream analog are session-auth only; a
  token surface has no upstream analog in either reference package and belongs to
  [`BACKLOG.md`][backlog] if ever.
- **Password-change / password-reset mutations.** No upstream analog in
  `strawberry_django/auth/` (or graphene-django); not carded; a consumer composes
  them from [`DjangoMutation`][glossary-djangomutation] today.
- **A package-provided `UserType`.** The consumer declares their own
  [`DjangoType`][glossary-djangotype] over `get_user_model()` (their field
  selection, their visibility hook); the package resolves it through the registry
  rather than shipping an opinionated default
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)).
- **A new `DjangoType` `Meta` key or settings key.** The auth surface is factories +
  the existing seams; `DEFERRED_META_KEYS` and [`conf.py`][conf] are untouched
  ([Decision 2](#decision-2--card-scope-boundary-session-auth-ships-channels--token-auth-stay-out-no-new-meta--settings-key)).
- **Changing the frozen contracts.** No field is added to
  [`FieldError`][glossary-fielderror-envelope]; the payload builder, the
  [`DjangoMutationField`][glossary-djangomutationfield] factory, and the
  `036` / `038` / `039` surfaces are reused unchanged.

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it?" test this card is
**single-upstream parity**: `strawberry-graphql-django` ships
[`strawberry_django/auth/`][upstream-auth-mutations]; `graphene-django` ships no auth
module at all. The [`KANBAN.md`][kanban] #"Decision: Alpha cards must claim upstream
parity" rule is satisfied honestly with the 🍓 Required link alone — the card's
`Verified in upstream` section grounds it in the three upstream files, all read for
this spec. The borrowing splits along the package's standing line — *behaviorally*
copy the upstream's good ideas, *surface-wise* stay DRF-shaped and envelope-first.

### From `strawberry-graphql-django` — borrow the capability set and the session semantics

- **The four-symbol surface** — `login`, `logout`, `register`, `current_user`
  ([`upstream mutations.py`][upstream-auth-mutations] /
  [`queries.py`][upstream-auth-queries]) → the card's `login_mutation` /
  `logout_mutation` / `register_mutation` / `current_user`.
- **`resolve_login`'s semantics** — `auth.authenticate(request, username=...,
  password=...)`, `None` → failure, else `auth.login(request, user)` and return the
  user. Borrowed as-is, including the single undifferentiated failure message
  ("Incorrect username/password" — no credential enumeration); only the failure
  *transport* changes (envelope, not raised error).
- **`resolve_logout`'s semantics** — capture `user.is_authenticated` as the result,
  then `auth.logout(request)` unconditionally. Borrowed as the `ok` value of the
  `{ ok, errors }` payload.
- **The register recipe** — a create-mutation subclass that pops `password`,
  runs `validate_password`, and writes it via a `set_password` pre-save hook
  (`DjangoRegisterMutation.create` upstream). Borrowed onto the
  [`DjangoMutation`][glossary-djangomutation] base — with one deliberate
  improvement: the package passes the constructed (unsaved) user instance as
  `validate_password(password, user)`'s second argument so
  `UserAttributeSimilarityValidator` actually compares against the submitted
  username/email (upstream calls `validate_password(password)` with no user).
- **`get_current_user(info)`'s core** — `request.user` off the resolved request.
  The ASGI-scope fallbacks are **not** borrowed (below).

### From the package's own write family — borrow the shape

- The [`FieldError` envelope][glossary-fielderror-envelope] + both generated payload
  shapes, the [`DjangoMutationField`][glossary-djangomutationfield] exposure for
  `register`, the `permission_classes` / `check_permission` seam, the phase-2.5
  bind + `strawberry.lazy` forward-ref discipline, and the by-pk payload re-fetch.
  The consumer-facing result is one uniform write contract across model / form /
  serializer / auth mutations — the
  [Cross-subsystem invariants][glossary-cross-subsystem-invariants] requirement.

### Explicitly do not borrow

- **The raised-`ValidationError` failure shape.** Upstream's `resolve_login` and
  `resolve_current_user` raise; this package's cross-flavor contract is the
  envelope for expected failures
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design) /
  [Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)).
- **The bare-`bool` logout return.** The `{ ok, errors }` payload keeps the client
  contract uniform with every other mutation.
- **The `channels_auth` fallback and the consumer-scope user extraction.** Both are
  Channels-transport concerns deferred to the `0.0.14` router card
  ([Decision 11](#decision-11--session-transport-constraints-sessionmiddleware--authenticationmiddleware-the-channels-fallback-is-not-borrowed)).
- **`strawberry_django.field` / decorator wiring.** The consumer surface is the
  package's factory idiom, not upstream's field/decorator composition.

## User-facing API

The consumer declares their own user type, then assigns the four factories — no
decorators on any consumer class, no hand-written resolvers:

```python
import strawberry
from django.contrib.auth import get_user_model
from strawberry import relay

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.auth import (
    current_user,
    login_mutation,
    logout_mutation,
    register_mutation,
)


class UserType(DjangoType):
    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email")
        interfaces = (relay.Node,)


@strawberry.type
class Query:
    me = current_user()


@strawberry.type
class Mutation:
    login = login_mutation()
    logout = logout_mutation()
    register = register_mutation()


finalize_django_types()
```

The generated schema surface (with the `UserType` above):

```graphql
type Mutation {
  login(username: String!, password: String!): LoginPayload!
  logout: LogoutPayload!
  register(data: RegisterInput!): RegisterPayload!
}

type Query {
  me: UserType
}

type LoginPayload {
  node: UserType
  errors: [FieldError!]!
}

type LogoutPayload {
  ok: Boolean!
  errors: [FieldError!]!
}

input RegisterInput {
  username: String!
  email: String!
  password: String!
}
```

Consumer-visible behavior:

- `login(username:, password:)` authenticates against the configured backends and
  establishes the Django session. Success → the user in the uniform slot, empty
  `errors`; failure → `node: null` plus one `"__all__"`-keyed
  [`FieldError`][glossary-fielderror-envelope] (`"Incorrect username/password"` —
  deliberately not saying which).
- `logout` ends the session; `ok` is whether an authenticated session existed
  (upstream's return-value semantics), `errors` is empty today.
- `register(data:)` creates the account: password validated against
  `AUTH_PASSWORD_VALIDATORS` (failures keyed to `password`), the user-model
  `full_clean()` envelope for everything else (a duplicate username keys to
  `username`), the password stored hashed, and the created user returned in the
  uniform slot — re-fetched optimizer-planned like every other create.
- `me` returns the session user typed as the consumer's `UserType`, or `null` for an
  anonymous request.
- Each factory accepts `permission_classes=` (default: allow-any — the documented
  auth exception): `register_mutation(permission_classes=[InviteOnly])` gates
  registration through the same `has_permission` seam every write flavor uses.
- **The `UserType` field selection is the authenticated read surface.** Whatever
  the consumer's user type selects is what `login` / `register` / `me` return —
  select explicitly (the example's `("id", "username", "email")`), never
  `fields = "__all__"` over the user model, and exclude `password` and privilege
  columns
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)).
- **The `login` node is the raw `authenticate()` instance** — no visibility re-run
  and no optimizer re-fetch, so a deep `login { node { <relations> } }` selection
  resolves per-field; `register`'s node, by contrast, is optimizer-planned through
  the standard post-write re-fetch. Issue deep post-login reads as a follow-up
  query
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).

### Error shapes

| Case | Where it lands |
| --- | --- |
| Wrong username **or** password on `login` | payload `errors: [{field: "__all__", messages: ["Incorrect username/password"]}]`, `node: null` |
| Inactive user under `ModelBackend` on `login` | same `"__all__"` envelope (Django's `authenticate` returns `None` for `is_active=False`) |
| Password fails a configured validator on `register` | payload `errors` keyed to `password`, one message per failing validator |
| Duplicate username on `register` | payload `errors` keyed to the `USERNAME_FIELD` (the model `full_clean()` unique check) |
| `logout` with no authenticated session | `ok: false`, empty `errors` (not an error — idempotent logout) |
| Anonymous `me` | `null` (never an error — the nullable-by-contract read posture) |
| A `permission_classes` denial on any auth field | top-level `GraphQLError` (the standing write-auth contract — authorization failures are not envelope entries) |
| Malformed input (missing argument, wrong type) | standard GraphQL validation error (never reaches the resolver) |

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

This spec lives at `docs/spec-040-auth_mutations-0_0_13.md` with companion
`docs/spec-040-auth_mutations-0_0_13-terms.csv`, per the
[`docs/SPECS/NEXT.md`][next] convention (`spec-<NNN>-<topic>-<X_Y_Z>.md`; NNN `040`
from [`WIP-ALPHA-040-0.0.13`][kanban], topic slug `auth_mutations`, version segment
`0_0_13`).

Alternatives considered (and rejected):

- **An unstructured `docs/spec-auth_mutations.md`.** Rejected: the structured name
  sorts with its card and version on disk and matches every spec since `spec-020`.

### Decision 2 — Card-scope boundary: session auth ships; Channels / token auth stay out; no new `Meta` / settings key

This card ships exactly the four-symbol session-auth surface over
`django.contrib.auth`. It does **not** ship Channels/websocket auth (the `0.0.14`
router card [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]
owns the ASGI-transport story), token/JWT auth (no upstream analog; backlog
material), password-change/reset flows (no upstream analog), or any new
[`DjangoType`][glossary-djangotype] `Meta` key or [`conf.py`][conf] settings key —
the auth surface composes purely from factories and the existing seams, so
`DEFERRED_META_KEYS` and the settings reader are untouched (the [`START.md`][start]
"add a settings key only when the feature that needs it lands" rule: nothing here
needs one).

Justification: the card's DoD names exactly the four symbols + tests + the opt-in
doc line; every candidate extension either belongs to an already-scheduled card
(`041` for Channels, `043` for the test client) or has no upstream analog to claim
parity against (token auth, password reset) — and [`START.md`][start]'s
resist-scope-creep rule applies squarely.

Alternatives considered (and rejected):

- **Fold in the Channels fallback now** (upstream carries it inline). Rejected: the
  package has no Channels surface until `041`; an untestable fallback (no ASGI
  router to exercise it) would ship dead lines against a 100% coverage gate.
- **Ship a `password_change` mutation while here.** Rejected: no upstream analog in
  either reference package (the Alpha parity rule would be satisfied by fabrication),
  and the consumer composes it from [`DjangoMutation`][glossary-djangomutation]
  today.

### Decision 3 — Consumer surface: four field factories at the `auth` submodule path, opt-in by import, no root re-export

The public surface is exactly the card's four symbols, importable **only** from the
submodule:

```python
from django_strawberry_framework.auth import (
    current_user, login_mutation, logout_mutation, register_mutation,
)
```

Nothing is added to the package root's `__all__` or its module namespace
([`__init__.py`][init]); the auth module is never imported by the package root, so a
consumer who doesn't use auth never pays its import. Each symbol is a **field
factory** (a callable returning a Strawberry field the `@strawberry.type` class-body
walk picks up), the exact consumer idiom
[`DjangoListField`][glossary-djangolistfield] /
[`DjangoNodeField`][glossary-djangonodefield] /
[`DjangoMutationField`][glossary-djangomutationfield] established — one
class-attribute assignment per field, no decorators, no hand-written resolvers.

Justification: the card's DoD is explicit — "Documented as opt-in: consumers must
import explicitly; auth mutations are not injected into every schema." A
submodule-only path makes the opt-in **structural** rather than merely documented,
and the package already has the precedent: the `testing.relay` helpers are
deliberately not re-exported from their parent either ([`docs/GLOSSARY.md`][glossary]
"NOT re-exported from the `testing` root, by design"). The snake_case factory names
are the card's own symbol names, and the factory-call shape mirrors upstream's
consumer surface (`login = auth.login()` upstream ↔ `login = login_mutation()`
here), keeping the migration diff one import line.

Alternatives considered (and rejected):

- **Root exports (`from django_strawberry_framework import login_mutation`).**
  Rejected: the root `__all__` is the pinned always-available surface; auth is
  opt-in by card mandate, and the root would also eagerly import `auth/` (and
  `django.contrib.auth`) for every consumer, used or not.
- **PascalCase mutation classes the consumer wires through
  [`DjangoMutationField`][glossary-djangomutationfield]
  (`login = DjangoMutationField(LoginMutation)`).** Rejected for `login` / `logout`:
  their argument signatures (`username:` / `password:`; no arguments) do not fit the
  factory's synthesized `data:` / `id:` signatures, so they would need signature
  special-cases inside the shared factory — a worse trade than two self-contained
  field factories. `register` **does** ride
  [`DjangoMutationField`][glossary-djangomutationfield] internally
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
- **A `strawberry_django`-style module of loose resolvers the consumer wraps
  themselves.** Rejected: hands the payload/envelope work back to the consumer —
  the exact boilerplate the card exists to absorb.

### Decision 4 — Module and test locations: `auth/` mirroring the upstream trio; `tests/auth/` mirroring source

New subpackage `django_strawberry_framework/auth/`:

- `auth/__init__.py` — re-exports the four public factories (the one import line
  consumers write).
- `auth/mutations.py` — `login_mutation()` / `logout_mutation()` /
  `register_mutation()`, the `DjangoRegisterMutation` rider class, the sync/async
  session resolvers, the declaration ledger, and `bind_auth_mutations()`.
- `auth/queries.py` — `current_user()` and its resolver pair.

Tests mirror source per the [`AGENTS.md`][agents] placement rule:
`tests/auth/test_mutations.py`, `tests/auth/test_queries.py` for package-only
internals; the live consumer surface lands in
`examples/fakeshop/test_query/test_auth_api.py` (the primary harness — Slices 1–2
land resolver code and its live coverage in the same commit).

Justification: the module split mirrors the upstream trio the card's `Verified in
upstream` section names (`mutations.py` / `queries.py`; upstream's `utils.py`
content — request/user extraction — already exists in this package as
[`utils/permissions.py::request_from_info`][utils-permissions], which the resolvers
reuse rather than re-spelling). The card's DoD names both `django_strawberry_framework/auth/`
and `tests/auth/` verbatim.

Alternatives considered (and rejected):

- **A single flat `auth.py`.** Rejected: the module carries two distinct surfaces
  (mutations + a query helper) plus a bind; the trio keeps each file one-purpose and
  mirrors the upstream layout a migrant greps for.
- **A set-family layout (`auth/sets.py` / `auth/resolvers.py` / `auth/inputs.py`).**
  Rejected: auth is not a declarative set family — there is no consumer-declared
  class to collect, validate, and expand; forcing the family layout onto four fixed
  factories manufactures indirection.

### Decision 5 — `login` / `logout`: session mutations on the frozen envelope, anonymous-allowed by design

**Shape.** `login_mutation()` returns a mutation field with two flat arguments —
`username: String!`, `password: String!` — resolving to the generated
`LoginPayload` (the uniform `node` / `result` slot typed as the user model's primary
[`DjangoType`][glossary-djangotype], plus
`errors: [FieldError!]!`). `logout_mutation()` takes no arguments and resolves to the
generated `LogoutPayload` — the pinned model-less `{ ok: Boolean!, errors:
[FieldError!]! }` shape [`spec-038`][spec-038] froze for the plain form, emitted by
the same `build_payload_type(object_type=None)` builder. The `username` argument
name is fixed: Django's `authenticate(request, username=..., password=...)` maps the
`username` kwarg onto the user model's `USERNAME_FIELD` inside `ModelBackend`, so an
email-login custom user model works unchanged (documented; the argument is the
credential slot, not a claim the column is called "username").

**Resolver semantics** (the upstream borrow, envelope-transported):

1. `request = request_from_info(info, family_label="AuthMutation")` — the shared
   request resolver every permission seam uses ([`utils/permissions.py`][utils-permissions]).
2. Authorization: run the field's `permission_classes` through the standard
   `check_permission` iteration (see below). A denial is a top-level `GraphQLError`
   — identical to every write flavor.
3. `login`: `user = auth.authenticate(request, username=username,
   password=password)`. `None` → the payload with `node: null` and ONE
   `"__all__"`-keyed [`FieldError`][glossary-fielderror-envelope]
   (`"Incorrect username/password"`). Success → `auth.login(request, user)`, then
   the payload with the user in the slot. The message is deliberately
   undifferentiated (no "unknown user" vs "wrong password" split — no
   account-enumeration oracle), the exact upstream wording.
4. `logout`: `ok = user.is_authenticated` (the session actor before teardown), then
   `auth.logout(request)` unconditionally (flushes the session whether or not
   authenticated — idempotent), returning `{ ok, errors: [] }`.

**The anonymous-allowed default — the deliberate inversion.** The write family's
posture is deny-by-default ([`DjangoModelPermission`][glossary-djangomodelpermission]
for model-backed writes; [`DenyAll`][mutations-permissions] for the model-less plain
form). Auth mutations are the **front door**: requiring authentication to
authenticate is a contradiction, so each auth factory's *unset*
`permission_classes` resolves to the explicit empty list — the `036` AllowAny
semantics (an empty class list authorizes every request). This is not a weakening of
the family rule but its documented, single-sited exception: the factories pass the
explicit default into the same `_validate_permission_classes` normalization
([`mutations/sets.py`][mutations-sets]) every flavor uses, so a consumer who
supplies `permission_classes=[...]` (rate-limit gate on `login`, invite gate on
`register`, a locked-down `logout` if they insist) gets the standard
`has_permission(info, mutation, operation, data, instance)` contract, including the
sync-only rule (an `async def` hook is a
[`SyncMisuseError`][glossary-syncmisuseerror], never a silent allow).

**Login skips both visibility AND the optimizer re-fetch — two distinct choices,
each deliberate.** The payload's user is the raw object `authenticate()` returned —
the session actor — with **no** [`get_queryset`][glossary-get_queryset-visibility-hook]
re-run and **no** `refetch_optimized` call. The visibility skip shares
`current_user`'s actor-not-lookup reasoning
([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)):
running the consumer's `UserType.get_queryset` (a hook commonly shaped "staff see
everyone, others see themselves") would let a visibility rule written for
*directory reads* hide the caller from their own successful login. The re-fetch
skip is a separate call: `authenticate()` already loaded the row, and re-fetching
costs a query to optimize a payload that is almost always `{ node { id username } }`.
The consequence, stated plainly: **the login node is NOT optimizer-planned** —
unlike `register`, whose node comes back through the G2-planned
[`refetch_optimized`][mutations-resolvers] — so a deep
`login { node { <relations> } }` selection resolves per-field (visible to
[Strictness mode][glossary-strictness-mode], like any non-root object). The two
payloads are deliberately asymmetric on this axis; a client wanting a planned
post-login graph issues a follow-up query. If implementation experience demands a
planned login node, the by-pk-no-visibility `refetch_optimized` call `register`
uses is the drop-in — a contained resolver change, not a contract change.

Justification: the envelope transport (rather than upstream's raised
`ValidationError`) is the [Cross-subsystem
invariants][glossary-cross-subsystem-invariants] requirement — "the `FieldError`
envelope is shared across every mutation flavor for a consistent client contract";
a client already handling `{ node, errors }` from every write handles a failed
login with zero new code paths.

Alternatives considered (and rejected):

- **Raise `GraphQLError` on bad credentials (upstream's shape).** Rejected: a wrong
  password is an *expected* outcome, and the package's contract routes expected
  write outcomes through the envelope; top-level errors are reserved for
  authorization denials and malformed requests.
- **A `data: LoginInput!` argument for family consistency.** Rejected: the
  generated-input machinery exists to derive shapes from models/forms/serializers;
  a fixed two-credential signature derives from nothing, and flat arguments match
  both upstream and the plain GraphQL ergonomics of the most-called mutation in any
  schema.
- **Distinguish "no such user" from "wrong password".** Rejected: an
  account-enumeration oracle; upstream, Django's own `AuthenticationForm`, and this
  spec all deliberately refuse.
- **Return the user from `logout` (symmetry with `login`).** Rejected: upstream
  returns a bool; the session is gone and the only useful fact is whether one
  existed. `{ ok, errors }` carries exactly that.
- **Default `permission_classes` to the family's deny.** Rejected as a
  contradiction: nobody could ever log in. The inversion is explicit, single-sited
  in the factories, and documented in the GLOSSARY entry.

### Decision 6 — `register_mutation()` rides `DjangoMutation`: a narrow `create` over `get_user_model()` with password hashing — NOT a fourth flavor

`register_mutation()` synthesizes (once, cached per normalized argument set) a
concrete `DjangoRegisterMutation` — a package-declared subclass of
[`DjangoMutation`][glossary-djangomutation] with:

- `Meta.model = get_user_model()`, `Meta.operation = "create"`.
- [`Meta.fields`][glossary-metafields] narrowed to
  `(USERNAME_FIELD, *REQUIRED_FIELDS, "password")` — the
  Django-blessed minimal account shape (`createsuperuser`'s own prompt set). The
  generated input therefore **cannot** carry `is_staff` / `is_superuser` /
  `is_active` / `groups` / `user_permissions` — privilege escalation is structurally
  unreachable, not policy-checked
  ([Input type generation][glossary-input-type-generation] narrows via the standard
  `Meta.fields` path, reusing the model-column converter unchanged).
- `Meta.permission_classes` defaulted to the explicit AllowAny (Decision 5's
  inversion), overridable through the factory's `permission_classes=` kwarg.
- The **password step, carried on the per-flavor resolver seam** (the P1 review
  finding, folded in): [`DjangoMutation`][glossary-djangomutation] exposes **no
  per-instance write hook** — `_run_pipeline_sync` hard-wires the model
  `decode_step` / `write_step` as module-level lambdas
  ([`mutations/resolvers.py`][mutations-resolvers] `::_run_pipeline_sync`), and the
  defaults are unsafe for this model: `_model_decode_step` would construct
  `model(password=<raw>)` and `_model_write_step` would `full_clean()` (which only
  checks the 128-char `max_length`) and `save()` the **plaintext**. So
  `DjangoRegisterMutation` overrides **both `resolve_sync` and `resolve_async`** —
  the same per-flavor seam the form and serializer flavors override — and rides
  the shared `run_write_pipeline_sync` skeleton with its own step pair: a
  `decode_step` that pops `password` from the input before delegating the
  remaining fields to the model decode, and a `write_step` that builds the unsaved
  user, runs
  `django.contrib.auth.password_validation.validate_password(password, user)`
  (each `ValidationError` message a `password`-keyed
  [`FieldError`][glossary-fielderror-envelope]), then `user.set_password(password)`
  **before** `full_clean()` / `save()`. The plaintext never reaches a model
  column, hashing before `full_clean()` means the `password` column validates
  against the hash rather than the raw input, and the **plaintext-never-persisted
  test is required on both the sync and the async path** — the async twin is a
  separate override and can regress independently.
- The input type name pinned to `RegisterInput` via the `input_type_name` /
  `build_input` name seams (the [`spec-038`][spec-038]-established override point),
  so the public SDL reads `RegisterInput` rather than the narrowed-shape
  deterministic name (`UserEmailPasswordUsernameInput`) the model default would
  derive. The payload is `RegisterPayload` from the class name, standard machinery.

**The genuine reuse, stated precisely** (the P1 framing correction): the register
rider reuses the model-column converter, the [Input type
generation][glossary-input-type-generation] narrowing, and the
`run_write_pipeline_sync` **skeleton** — the `transaction.atomic()` boundary, the
authorize-before-decode security ordering, the envelope short-circuits with
rollback, and the closing `refetch_optimized` → `build_payload` steps — while the
pipeline **body** (the decode / write step pair) is register's own, exactly as it
is the form's and the serializer's. Structurally, `register` is a fourth
decode/write **step pair**, not a fourth plumbing *kit*. Everything else rides the
foundation as-is: registration + phase-2.5 bind via `bind_mutations()` (the class
IS a `DjangoMutation`), exposure via
[`DjangoMutationField`][glossary-djangomutationfield] (the factory returns
`DjangoMutationField(DjangoRegisterMutation)` internally), the envelope from
`full_clean()` (duplicate `USERNAME_FIELD` → field-keyed error via the model's
unique constraint), and the post-save
[`refetch_optimized`][mutations-resolvers] by pk without visibility (the `036`
own-write exception — load-bearing here, since the brand-new anonymous-created user
is exactly the row a staff-only `UserType.get_queryset` would hide).

The synthesized class is created **lazily on first factory call** (not at module
import): creating it registers a mutation declaration, and a consumer who imports
`auth` only for `login_mutation` must not get a phantom user-input/payload
materialized at bind. **Every factory call — cached or not — re-registers the
class into the mutation declaration ledger** (the P2 reload finding):
`register_mutation`'s registry dedupes by identity
([`mutations/sets.py`][mutations-sets] `::make_declaration_registry` #"if
declaration_cls not in store"), so on a live ledger the re-register is a no-op,
and after a `registry.clear()` + consumer re-declaration it **re-appends** — the
rider survives the suite's complete-reload fixtures instead of silently dropping
out of the second schema while `login` / `logout` (auth ledger, explicitly cleared
and re-declared) survive. A reload-idempotence test pins the cycle: finalize →
`registry.clear()` → re-declare → finalize, with `register` present in the second
schema. Calls after
[`finalize_django_types`][glossary-finalize_django_types] raise the standing
declare-after-finalize [`ConfigurationError`][glossary-configurationerror].

Justification: [`docs/feedback.md`][feedback]'s three-flavor DRY review is the
standing warning — "every new write flavor re-spells the same ~8 pieces of glue."
The register flavor dodges the *kit* by being a rider: no new converter (the
model-column converter covers `AbstractBaseUser` columns), no new input generator
(standard `Meta.fields` narrowing), no new orchestration (the shared skeleton) —
only the one step pair the password work genuinely requires. This is also the
upstream shape verbatim — `DjangoRegisterMutation(DjangoCreateMutation)` overriding
the create step with `validate_password` + a `set_password` pre-save hook — adapted
to the package's seams, plus the validator-gets-the-user improvement noted in
[Borrowing posture](#borrowing-posture).

Alternatives considered (and rejected):

- **A consumer-facing subclassable base instead of a factory** (`class Register(
  DjangoRegisterMutation): class Meta: ...`). Rejected for `0.0.13`: the card names
  the factory symbol, the no-argument default covers the parity case, and a naive
  consumer-declared `DjangoMutation` over the user model is a *plaintext-password
  foot-gun* (the generated create would store `password` verbatim — the exact
  default-pipeline behavior the rider's step pair exists to prevent) — the factory
  keeps the safe path the obvious path. A customization surface is a recorded
  follow-on ([Risks](#risks-and-open-questions)).
- **A `pre_save` / per-instance write hook added to the `036` base instead of the
  resolver-seam override.** Rejected: widening the frozen
  [`DjangoMutation`][glossary-djangomutation] base for one internal consumer
  re-opens a shipped contract; the per-flavor `resolve_sync` / `resolve_async`
  seam plus `run_write_pipeline_sync`'s `decode_step` / `write_step` parameters
  exist for exactly this, and the form / serializer flavors already prove the
  shape. (A public write hook, if consumer demand materializes, is its own card.)
- **Include `email` unconditionally.** Rejected: `REQUIRED_FIELDS` already includes
  it for the default user model; hardcoding it would break custom user models that
  deliberately omit it. The `(USERNAME_FIELD, *REQUIRED_FIELDS, "password")` set is
  model-derived, not assumed.
- **The narrowed-shape deterministic input name.** Rejected: `RegisterInput` is the
  consumer-facing SDL contract a migrant expects; the deterministic
  `UserEmailPasswordUsernameInput` name is collision-proof but reads like generated
  debris. The name seams exist precisely for flavors to pin friendlier names
  ([`spec-038`][spec-038]'s `<FormClass>Input` precedent); the materialize ledger's
  distinct-shape collision raise still guards a consumer's own `RegisterInput`.
- **Validate the password with no user context (upstream's call).** Rejected:
  `validate_password(password, user)` with the constructed instance lets
  `UserAttributeSimilarityValidator` reject `password == username` — strictly better
  validation for one argument.

### Decision 7 — `current_user()` returns the session actor, nullable, and does not re-run `get_queryset`

`current_user()` returns a query **field** (not a mutation) whose resolver reads the
request user via the same `request_from_info` extraction and returns:

- the user object, typed as the user model's primary
  [`DjangoType`][glossary-djangotype], when `user.is_authenticated`;
- `null` otherwise (anonymous / no session).

The return annotation is `<UserPrimaryType> | None` via a bind-materialized
`strawberry.lazy` alias
([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
The resolver performs **no queryset work**: no
[`get_queryset`][glossary-get_queryset-visibility-hook] re-run, no re-fetch — the
returned object is `request.user`, already loaded by `AuthenticationMiddleware`
(lazily; the resolver's `is_authenticated` access forces it, the upstream trick).
Nested relation selections under `me { ... }` resolve through the type's generated
resolvers as usual (an unplanned deep selection is visible to
[Strictness mode][glossary-strictness-mode] like any non-root object — the same
posture as the mutation payload slot).

Justification for nullable-not-raising: upstream raises `ValidationError("User is
not logged in.")`; this package's read posture is nullable-by-contract
(`node(id:)` returns `null` for hidden/missing; the file/image output object is
null-by-default) — an anonymous session is an expected state, not an error, and a
nullable `me` is the shape every GraphQL client library expects to branch on.
Justification for skipping visibility: `get_queryset` scopes *lookups of other
rows*; `me` is the actor themselves. A directory-shaped hook ("non-staff see only
public profiles") must not make `me` return `null` for a logged-in user — that
breaks the one query every authenticated SPA fires first. The same
actor-not-lookup reasoning already governs the `036` re-fetch exception and
Decision 5's login payload; this spec makes it uniform across the three
actor-returning surfaces.

Alternatives considered (and rejected):

- **Raise on anonymous (upstream's shape).** Rejected: expected state ≠ error; the
  nullable contract is the package's standing read posture.
- **Run the type's `get_queryset` over a `pk=user.pk` queryset.** Rejected: hides
  the actor from themselves under directory-shaped visibility hooks, and costs a
  query to re-fetch a row the middleware already loaded.
- **A `viewer`-style wrapper type.** Rejected: nothing to carry beyond the user;
  the consumer can compose their own wrapper trivially.

### Decision 8 — The user model's primary `DjangoType` is required, validated at bind

`login_mutation()`, `register_mutation()`, and `current_user()` all type their user
surface as the **primary** [`DjangoType`][glossary-djangotype] registered for
`get_user_model()` (the [`Meta.primary`][glossary-metaprimary] registry lookup every
payload resolution uses). The consumer declares it — their field selection, their
[`Meta.interfaces`][glossary-metainterfaces], their visibility hook for directory
reads. `bind_auth_mutations()` validates at phase 2.5: if any of the three
user-typed fields was declared and no primary type for the user model is registered,
finalization fails with a [`ConfigurationError`][glossary-configurationerror] naming
the missing registration and the fix ("declare a `DjangoType` with
`Meta.model = get_user_model()`; mark it `Meta.primary = True` if the model has
several"). `logout_mutation()` is exempt — its `{ ok, errors }` payload references
no user type, so a logout-only schema (however unlikely) needs no user type.

**The validation must run BEFORE `bind_mutations()` to be reachable for
`register`** (the P2 review finding). The register rider is itself a
[`DjangoMutation`][glossary-djangomutation], and `bind_mutations()` resolves its
payload's primary type through `_resolve_primary_type` — whose no-registered-type
raise is a **generic** message naming `DjangoRegisterMutation` (a class the
consumer never wrote) and the raw concrete user-model class, with no
`get_user_model()` / [`Meta.primary`][glossary-metaprimary] recourse
([`mutations/sets.py`][mutations-sets] `::_resolve_primary_type` #"which has no
registered DjangoType"). Were the auth bind ordered after it (as an earlier draft
had it), the generic error would always pre-empt the auth-specific one for
`register` and the register arm of this Decision would be dead. So
[Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)
orders `bind_auth_mutations()` **before** `bind_mutations()`: the auth ledger
knows every declared surface (`register_mutation()` records there too), the
primary-type lookup needs only registration-time state, and all three user-typed
surfaces fail with the same actionable auth message. Tests pin the **exact** error
a no-`UserType` schema produces for `register` specifically, distinct from
`login`'s.

**The user type's field selection IS the authenticated read surface** (the P3
review caution). The register input side is safe by construction (privilege
columns structurally unreachable, Decision 6) — but the *output* side is whatever
the consumer's `UserType` selects: a `fields = "__all__"` over the user model
surfaces the password **hash**, `is_superuser` / `is_staff`, and `last_login`
through `LoginPayload.node`, `RegisterPayload.node`, and `me`. Select explicitly
and exclude `password` and privilege columns (the spec's example uses
`("id", "username", "email")`); the Slice 3 GLOSSARY entry carries the same
caution. This is doc-only guidance — the package does not police the consumer's
selection (a deliberately privileged `UserType` behind a staff-only schema is
legitimate), it makes the trade visible.

Justification: resolving through the registry is what every flavor does with its
payload type; a package-provided fallback `UserType` would pick a field selection
(privacy surface!) on the consumer's behalf — the wrong side of the "no silent
schema decisions" line. Failing at bind (not at first query) is the
materialize-before-`Schema` discipline: a missing type is a configuration error,
and configuration errors surface at finalization, loudly, with a named fix.

Alternatives considered (and rejected):

- **Ship a minimal package `UserType` fallback.** Rejected: the package would be
  choosing which user columns a schema exposes — a security-adjacent default no
  library should pick silently. (A documented optional helper could be a follow-on
  if consumers ask.)
- **Type the user surface as an opaque `JSON` / generic object when no type is
  registered.** Rejected outright: "a system that silently weakens rich relations
  into generic placeholders" is a named [`GOAL.md`][goal] non-goal.
- **Scope the auth-specific validation to `login` / `current_user` and let
  `register` surface the generic `bind_mutations()` error.** Rejected: the three
  user-typed surfaces should fail uniformly, and the generic message names the
  internal rider class and the raw model class without the
  `get_user_model()` / `Meta.primary` recourse — worse exactly for the consumer
  most likely to hit it (one who wired auth first, types second).
- **Police the consumer's `UserType` selection (reject `password` in
  `Meta.fields` when auth is bound).** Rejected: the type may serve non-auth,
  legitimately privileged surfaces; a hard reject would make the auth import
  change the validity of an unrelated declaration. The caution is documentation,
  like the `038` file-clearing scope note.

### Decision 9 — Bind lifecycle: a declaration ledger + `bind_auth_mutations()` at phase 2.5 + registered clear rows

The factories run at consumer class-body time — **before**
[`finalize_django_types`][glossary-finalize_django_types], when the user's primary
type may not even be registered yet
([Definition-order independence][glossary-definition-order-independence]). So the
factories cannot resolve types eagerly; they follow the exact
[`DjangoMutationField`][glossary-djangomutationfield] discipline:

- Each factory call records a declaration in a module-level auth ledger (which
  surfaces were declared, with which `permission_classes`) and returns a field
  typed via `strawberry.lazy` forward-refs into the package namespaces —
  `"LoginPayload"` / `"LogoutPayload"` in the `mutations.inputs` module path (where
  `build_payload_type` materializes), and the `current_user` return alias in
  `auth.queries`.
- `bind_auth_mutations()` runs inside [`types/finalizer.py`][types-finalizer] phase
  2.5, **before** `bind_mutations()` (the P2 review ordering fix): its
  [Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)
  user-type validation must fire with the auth-specific message before the
  register rider's own bind could raise `_resolve_primary_type`'s generic
  no-DjangoType error. Nothing in the auth bind depends on `bind_mutations()`
  having run — the primary-type lookup and the payload materialization consume
  only registration-time state. It validates Decision 8 for **every** declared
  user-typed surface (`register` included, via its auth-ledger record), resolves
  the user primary type, materializes `LoginPayload` (object slot per
  `payload_object_slot(primary)`) and `LogoutPayload` (`object_type=None`) through
  the ONE `build_payload_type` builder + ledger, and materializes the
  `current_user` alias — all before `strawberry.Schema(...)` resolves the lazy
  refs. The register rider itself is then bound by `bind_mutations()` as an
  ordinary [`DjangoMutation`][glossary-djangomutation] (its `RegisterInput` /
  `RegisterPayload` materialize there).
- The ledger's clear is registered once through
  [`registry.py::register_subsystem_clear`][registry] (a static
  `("django_strawberry_framework.auth.mutations", "clear_auth_declarations")` row),
  so both `TypeRegistry.clear()` and the finalizer's pre-bind reset block drain it
  via `_clear_if_importable` — the [`spec-039`][spec-039] P1.6/M4 seam, not a third
  hand-edited list. Auth has no soft dependency (`django.contrib.auth` ships with
  Django), but the static-row mechanism is used anyway for uniformity and retry
  idempotence.
- A factory call **after** finalization raises
  [`ConfigurationError`][glossary-configurationerror] (the standing
  declare-after-finalize rule).

Justification: this is the established lifecycle for every generated-at-bind
surface (mutation inputs, payloads, filter/order inputs, relation connections);
inventing a second lifecycle for auth would be gratuitous divergence. Payload
materialization reuses the single builder + ledger so name collisions (a consumer's
own `Login` mutation class also emitting `LoginPayload`) hit the standard
distinct-shape collision raise rather than a silent overwrite
([Edge cases](#edge-cases-and-constraints)).

Alternatives considered (and rejected):

- **Resolve types eagerly at factory-call time.** Rejected: breaks definition-order
  independence — the factory would demand the user type be declared first, the
  exact constraint `finalize_django_types()` exists to remove.
- **A dedicated auth payload namespace.** Rejected: `build_payload_type` already
  owns payload materialization + collision policy in one ledger; a second namespace
  forks the collision story.

### Decision 10 — Sync + async: session work through one `sync_to_async(thread_sensitive=True)` boundary

Every auth field ships the sync/async resolver pair, dispatched by the same
construction-time/runtime detection the field family uses. The async paths wrap the
session work — `authenticate` / `auth.login` / `auth.logout` are session- and
DB-touching sync APIs — in a single `sync_to_async(thread_sensitive=True)` call per
resolution, the exact boundary discipline the `036` async pipeline pinned (one
boundary, not per-step hops). `current_user`'s async path forces the lazy
`request.user` inside the boundary (upstream's "access an attribute to force
loading in async contexts" note — the `SynchronousOnlyOperation` guard).
Where the reused write pipeline meets consumer hooks the standing
[`SyncMisuseError`][glossary-syncmisuseerror] discipline applies unchanged (an
`async def` `has_permission` is rejected, never treated as allow).

Alternatives considered (and rejected):

- **Native-async auth via Django's `aauthenticate` / `alogin`** (Django ≥ 5.0).
  Rejected for `0.0.13`: the package's write family standardized on the one
  `sync_to_async` boundary; adopting the native-async auth APIs is a
  family-wide decision (it would apply equally to `036`'s pipeline) and belongs to
  a dedicated async card, not a divergence smuggled in here. Recorded in
  [Risks](#risks-and-open-questions).

### Decision 11 — Session-transport constraints: `SessionMiddleware` + `AuthenticationMiddleware`; the Channels fallback is NOT borrowed

The auth surface requires Django's session stack — `django.contrib.sessions` +
`SessionMiddleware` + `AuthenticationMiddleware` on the `/graphql/` request path
(and `django.contrib.auth` in `INSTALLED_APPS`). This is documented, not probed:
a sessionless deployment hitting `auth.login` gets Django's own error, and the
package does not add a bespoke pre-flight check (the same posture as every Django
API the package composes — the framework's error is the correct error). CSRF is the
consumer's transport concern exactly as for every existing mutation (the fakeshop
example and Django test client already handle it); nothing auth-specific changes it.

Upstream's two Channels fallbacks — `channels_auth.login/logout` against
`request.consumer.scope` in [`mutations.py`][upstream-auth-mutations], and the
consumer-scope user extraction in [`utils.py`][upstream-auth-utils] — are
**deliberately not borrowed**. The package has no Channels surface until the
`0.0.14` [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] card;
shipping a fallback no supported transport can reach would be dead, untestable code
under the 100% gate. The router card inherits the question ("does `041` extend auth
to consumer-scope sessions?") — recorded in
[Out of scope](#out-of-scope-explicitly-tracked-elsewhere) and
[Risks](#risks-and-open-questions).

Alternatives considered (and rejected):

- **Borrow the `try: channels import` fallback now.** Rejected: unreachable until
  `041`; a soft-dep guard defending a path nothing exercises.
- **A bespoke "sessions not configured" `ConfigurationError` probe.** Rejected:
  duplicates Django's own error surface and adds a false-confidence check
  (middleware order, custom session backends, and subpath configs make a reliable
  probe larger than the feature).

### Decision 12 — This card owns the `0.0.13` version bump AND completes the joint cut

`040` is now the **lone non-Done `0.0.13` card**: `039` is Done
([`DONE-039-0.0.13`][kanban]), and the [`docs/SPECS/NEXT.md`][next] Step 3 scan
confirms no other WIP / To-Do card carries the `0.0.13` patch version. Both the
lone-card rule ([`spec-038`][spec-038] Decision 14's posture) and the sibling's
explicit deferral ([`spec-039`][spec-039] Decision 14 / F8: the joint cut "shared
with `WIP-ALPHA-040-0.0.13`, which still owns the version bump … and the public
release-status flip") point at the same owner: **this card's Slice 3.** Leaving the
version at `0.0.12` after `040` ships would strand *two* implemented cards behind a
stale identity, and nobody else would bump it. Slice 3 therefore aligns the version
quintet:

- [`pyproject.toml`][pyproject] `[project].version`
- `__version__` in [`__init__.py`][init]
- [`tests/base/test_init.py::test_version`][test-base-init]
- the [`docs/GLOSSARY.md`][glossary] package-version line
- the `django-strawberry-framework` `version` entry inside `uv.lock`

**and** lands the `039`-deferred release wording in the same slice: the GLOSSARY
[`SerializerMutation`][glossary-serializermutation] status flips from "implemented on
main, releasing in `0.0.13`" to `shipped (0.0.13)`; [`docs/README.md`][docs-readme] /
[`README.md`][readme] move the serializer flavor **and** the new auth surface from
"Coming next" to "Shipped today" (README **Status** version line → `0.0.13`); and
[`CHANGELOG.md`][changelog] carries the `0.0.13` release bullets covering **both**
cards. Per [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly
instructed", the `CHANGELOG.md` edit must be explicitly named in the Slice 3
maintainer prompt — this spec describes it but cannot authorize it. `0.0.13` is a
routine patch cut, not a milestone (`X.Y.0`) rollover, so no `alpha constraint`
lifts or milestone-prose flips apply. The bump moves only in Slice 3 — after the
auth surface, tests, and docs are complete — never in Slice 1.

Alternatives considered (and rejected):

- **Defer the bump to a separate release-alignment card.** Rejected: no such card
  exists; `039` already deferred *to this card by name* — a second deferral orphans
  the cut.
- **Bump in Slice 1.** Rejected: the version moves after the feature it describes,
  the same reason every prior cut-owning spec staged it last.
- **Split the `039` flips into their own commit ahead of this card.** Rejected: the
  flips advertise a released `0.0.13` and are only truthful in the same cut that
  moves the version — landing them early recreates the mismatch F8 existed to
  prevent.

## Implementation plan

Three slices. Slices 1 and 2 each land package code **and its live fakeshop
surface in one commit** (the live-first mandate); Slice 3 is docs + the version cut.
Line deltas are planning estimates.

| Slice | Files touched | New / changed tests | Approx. delta |
| --- | --- | --- | --- |
| 1 — auth substrate + `login` / `logout`, earned live | `auth/__init__.py` (new; the four re-exports — `register_mutation` / `current_user` stubs raise until Slice 2 only if unavoidable, else land in Slice 2), `auth/mutations.py` (new; `login_mutation` / `logout_mutation` factories, declaration ledger, `bind_auth_mutations()`, sync/async session resolvers, the AllowAny default through `_validate_permission_classes`), [`types/finalizer.py`][types-finalizer] (one `bind_auth_mutations()` call in phase 2.5), [`registry.py`][registry] (one `register_subsystem_clear` row — via the seam, no list edit), `examples/fakeshop/apps/accounts/` (new; schema-only app: `UserType` over `auth.User`, `Query.me`-less for now, `Mutation.login` / `logout`), [`config/schema.py`][config-schema] + [`config/settings.py`][config-settings] (compose + install the app) | **Primary: `test_query/test_auth_api.py`** (new; ~8 live — login happy path + session cookie, wrong-password `"__all__"` envelope, inactive-user envelope, logout round trip, anonymous logout `ok: false`, a `permission_classes` gate). **Internals: `tests/auth/test_mutations.py`** (~10 — ledger record/clear/idempotence, bind validation incl. the no-primary-type raise, post-finalize factory raise, async paths, sessionless edge, async-permission `SyncMisuseError`) | `+420 / 0` |
| 2 — `register` + `current_user`, earned live | `auth/mutations.py` (`register_mutation` + the cached `DjangoRegisterMutation` synthesis: `Meta.fields` narrowing, the `resolve_sync` / `resolve_async` overrides riding `run_write_pipeline_sync` with the password-aware decode / write step pair (pop → `validate_password(password, user)` → `set_password` → `full_clean` → `save`), the every-call ledger re-register, the `RegisterInput` name-seam override), `auth/queries.py` (new; `current_user` factory + resolver pair + the bind-materialized return alias), `examples/fakeshop/apps/accounts/schema.py` (grow `register` + `me`), | **Primary: `test_query/test_auth_api.py`** (+~7 live — register → login → `me` → logout round trip, hashed-password assertion, duplicate-username envelope, weak-password validator envelope, anonymous `me: null`, register under an explicit permission gate). **Internals: `tests/auth/test_mutations.py` + `tests/auth/test_queries.py`** (+~11 — factory cache identity, the reload-idempotence cycle, the register-arm no-`UserType` error, custom-`USERNAME_FIELD` field-set derivation, validator → envelope mapping shapes, plaintext-never-persisted on BOTH sync and async paths, `current_user` lazy-load forcing, alias materialization) | `+350 / 0` |
| 3 — docs + `0.0.13` version cut + card wrap | [`docs/GLOSSARY.md`][glossary] ([Auth mutations][glossary-auth-mutations] → `shipped (0.0.13)` full contract; [`SerializerMutation`][glossary-serializermutation] → `shipped (0.0.13)`; package-version line; Index rows; submodule-exports note), [`docs/README.md`][docs-readme] + [`README.md`][readme] ("Coming next" → "Shipped today" for both `0.0.13` features; Status → `0.0.13`), [`TODAY.md`][today] (serializer wording → shipped; auth noted under capabilities-not-exercised-by-products), [`GOAL.md`][goal] (fakeshop auth wording future → shipped), [`docs/TREE.md`][tree] (`auth/`, `tests/auth/`, `accounts`, `test_auth_api.py` rows — closes the target-layout gap), [`CHANGELOG.md`][changelog] (**explicit-permission caveat**), version quintet, [`KANBAN.md`][kanban] card wrap (DB + re-render) | `test_version` → `0.0.13` | `+150 / -60` |

Total expected delta: ~`+920 / -60` — an M cut, matching the card's relative size.
The small footprint is the dividend of riding the frozen foundation: no new
converter, no new input generator, no new pipeline orchestration (register supplies
only its password-aware decode / write step pair over the shared skeleton), both
payload shapes from the existing builder. Staged-but-not-implemented seams follow the
[`AGENTS.md`][agents] design-doc anchor discipline (a source-site
`TODO(spec-040 Slice N)` comment naming this spec, removed in the slice that ships
it).

## Edge cases and constraints

- **Wrong credentials / unknown user / inactive user.** All three collapse into the
  ONE `"__all__"`-keyed envelope entry (Django's `authenticate` returns `None` for
  each under `ModelBackend`, including `is_active=False`). No enumeration oracle;
  the live suite pins the identical shape for wrong-password and unknown-username.
- **Login while already authenticated.** Allowed; `auth.login` establishes the new
  session (Django rotates the session key and, for a *different* user, flushes the
  old session — its standard fixation defense). The payload carries the newly
  authenticated user.
- **Anonymous logout.** `ok: false`, empty errors; `auth.logout` still runs (a
  session flush on an anonymous session is a no-op) — idempotent by construction.
- **Duplicate username on register.** The model `full_clean()` unique check surfaces
  as a `USERNAME_FIELD`-keyed [`FieldError`][glossary-fielderror-envelope]; the
  concurrent-race `IntegrityError` fallback maps through the standing
  `save_or_field_errors` path — both the `036` contract, no auth-specific code.
- **Password validator failures.** Every failing validator contributes a message
  under the single `password` key (Django's `validate_password` aggregates into one
  `ValidationError`); the live weak-password test asserts multiple messages under
  one key against fakeshop's four configured validators.
- **Custom user models.** `USERNAME_FIELD` / `REQUIRED_FIELDS` drive the register
  field set, so an email-login model registers with `email` + password; a
  `REQUIRED_FIELDS` entry that is a forward FK becomes the standard `<field>_id`
  input (the model-column converter's relation rule); `authenticate`'s `username`
  kwarg maps onto `USERNAME_FIELD` via `ModelBackend`. A custom auth **backend**
  whose `authenticate` signature does not accept `username=` / `password=` kwargs is
  out of scope ([Risks](#risks-and-open-questions)).
- **`REQUIRED_FIELDS` naming `password`-adjacent or unusable columns.** The
  synthesized `Meta.fields` tuple deduplicates (`USERNAME_FIELD` appearing in
  `REQUIRED_FIELDS` is a consumer error Django itself rejects) and the standard
  `Meta.fields` validation rejects unknown names loudly — no silent drops.
- **Payload-name collisions.** `LoginPayload` / `LogoutPayload` / `RegisterPayload` /
  `RegisterInput` materialize through the standard ledgers, so a consumer's own
  mutation class named `Login` (emitting a distinct-shape `LoginPayload`) hits the
  established distinct-shape collision
  [`ConfigurationError`][glossary-configurationerror] at finalization — documented,
  with the consumer rename as the recourse.
- **Factory called after finalization.** The standing declare-after-finalize
  [`ConfigurationError`][glossary-configurationerror]; tests pin it for both the
  ledger factories and the lazy `DjangoRegisterMutation` synthesis.
- **Two calls to the same factory.** The ledger dedupes per normalized argument set
  (two schemas or a Query + a re-export both get the same materialized payloads);
  two `register_mutation()` calls share the one cached rider class.
- **No registered user `DjangoType`.** Bind-time
  [`ConfigurationError`][glossary-configurationerror] naming the missing primary
  registration and the fix
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind));
  a logout-only schema is exempt.
- **Sessionless / middleware-less deployments.** Django's own error surfaces
  (documented constraint,
  [Decision 11](#decision-11--session-transport-constraints-sessionmiddleware--authenticationmiddleware-the-channels-fallback-is-not-borrowed));
  the package adds no probe. The `tests/auth/` sessionless edge pins that the error
  is Django's, not a swallowed pass.
- **Async contexts.** The session work runs inside one
  `sync_to_async(thread_sensitive=True)` boundary; `current_user` forces the lazy
  user inside it (no `SynchronousOnlyOperation` leaks); an `async def`
  `has_permission` raises [`SyncMisuseError`][glossary-syncmisuseerror] — never a
  silent allow.
- **The register payload under visibility.** The post-save re-fetch is by pk
  without [`get_queryset`][glossary-get_queryset-visibility-hook] (the `036`
  own-write exception), so a staff-only `UserType.get_queryset` cannot null the
  just-created account's payload; the live round trip pins it with the fakeshop
  hook in place.
- **`login` under a consumer permission gate.** `permission_classes=[...]` on
  `login_mutation()` runs **before** `authenticate` — a gated login denies with the
  top-level `GraphQLError` and never touches credential checking (no
  timing/enumeration side channel through the gate).
- **Deep selections under `login { node { … } }`.** The login node is the raw
  `authenticate()` instance — not optimizer-planned (unlike `register`'s G2-planned
  re-fetch) — so nested relations resolve per-field and are
  [Strictness mode][glossary-strictness-mode]-visible; deep post-login reads
  belong in a follow-up query
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
- **Reload / re-finalize cycles.** `registry.clear()` drains the auth ledger (the
  registered clear row) AND the mutation ledger; the consumer's re-declaration
  re-records both — `login` / `logout` / `me` through their factories, `register`
  through the every-call re-register of the cached rider — so a second finalize
  rebuilds the full auth surface (the suite's complete-reload fixtures exercise
  exactly this path).

## Test plan

Placement per [`AGENTS.md`][agents] / [`docs/TREE.md`][tree] #"Coverage priority.":
every consumer-reachable behavior is earned in
`examples/fakeshop/test_query/test_auth_api.py` over live `/graphql/` (the primary
harness, landing in the same commits as the resolvers — Slices 1–2); `tests/auth/`
holds only what a realistic request cannot drive. **The package-test boundary is
explicit**: `tests/auth/` must not accrete live-reachable acceptance coverage.

**Live (`test_query/test_auth_api.py`, primary):**

- login happy path (seeded `create_users` fixture users, password `admin`): payload
  user in the slot, session cookie established, a follow-up `me` sees the user;
- wrong-password AND unknown-username: byte-identical `"__all__"` envelope
  (enumeration guard pinned as a shape equality);
- inactive user: same envelope;
- logout: `ok: true` then session gone (`me: null` after); anonymous logout
  `ok: false`;
- register → login → `me` → logout round trip on a fresh username; the stored
  password is hashed (`check_password` true, raw string not in the column);
- duplicate-username envelope keyed to `username`; weak-password envelope keyed to
  `password` with the fakeshop validators' messages;
- anonymous `me: null`;
- a `permission_classes`-gated auth field denying with a top-level `GraphQLError`
  (the composability DoD, exercised live);
- SDL assertions: `LoginPayload` / `LogoutPayload` / `RegisterPayload` /
  `RegisterInput` shapes as pinned in
  [User-facing API](#user-facing-api).

**Package-internal (`tests/auth/`, mirrored, internals only):**

- ledger mechanics: record / dedupe / clear via the `register_subsystem_clear` row;
  retry-idempotence through the finalizer pre-bind reset; the **reload-idempotence
  cycle** — finalize → `registry.clear()` → re-declare → finalize, asserting
  `register` is present in the second schema (the every-call re-register rule);
- bind validation: the no-primary-user-type
  [`ConfigurationError`][glossary-configurationerror] (message names the fix),
  **fired from `bind_auth_mutations()` ahead of `bind_mutations()` — with the
  register-arm error pinned exactly and distinct from login's** (never the generic
  `_resolve_primary_type` message); logout-only exemption; post-finalize factory
  raise;
- the register rider: factory cache identity; the synthesized `Meta.fields` set for
  the default AND a custom-`USERNAME_FIELD` / custom-`REQUIRED_FIELDS` user model
  (a test-scoped model, since fakeshop pins the default `auth.User`);
  `validate_password(password, user)` receives the constructed instance; the
  plaintext-never-persisted assertion at the write-step seam **on both the sync
  and the async resolver paths** (separate overrides, independently regressable);
  hash-before-`full_clean` ordering;
- sync/async: both resolver paths; the one-boundary discipline; the async
  `has_permission` → [`SyncMisuseError`][glossary-syncmisuseerror]; the
  `current_user` lazy-user forcing;
- the sessionless-request edge (Django's error propagates, not swallowed).

**Cross-cutting:** the full suite green at `fail_under = 100`; `ruff format` +
`ruff check` clean; the `036` / `038` / `039` surfaces and the read side unchanged
(the register rider must not perturb the model flavor's seam defaults —
`tests/mutations/` stays green untouched).

## Doc updates

Each slice owns its doc edits. [`AGENTS.md`][agents] #"Do not update CHANGELOG.md
unless explicitly instructed" requires the `CHANGELOG.md` edit to be explicitly
named in the Slice 3 maintainer prompt — this spec describes the edit but cannot
itself grant the permission.

- **Slice 1–2 (inline with code):** docstrings + the fakeshop `accounts` app README
  breadcrumbs; no repo-level doc flips yet (the surface is unreleased mid-card).
- **Slice 3 — the release cut** (see
  [Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)):
  - [`docs/GLOSSARY.md`][glossary]: [Auth mutations][glossary-auth-mutations] →
    `shipped (0.0.13)` with the implemented contract (the four factories, the
    submodule-only import, the AllowAny inversion + rationale, the envelope
    semantics, the no-Channels constraint, and the **`UserType`-selection
    caution** — the user type's field selection is the authenticated read
    surface; exclude `password` and privilege columns); the
    [`SerializerMutation`][glossary-serializermutation] status →
    `shipped (0.0.13)` (the `039`-deferred flip); the package-version line →
    `0.0.13`; Index rows; a submodule-exports note beside the `testing` note.
  - [`docs/README.md`][docs-readme] / [`README.md`][readme]: the `0.0.13` "Coming
    next" row (serializer + auth) moves into "Shipped today"; README **Status** →
    `0.0.13` with the newest-shipped-surface prose.
  - [`TODAY.md`][today]: the serializer paragraphs drop "releasing in `0.0.13`"
    for shipped wording; auth is noted under "Shipped package capabilities not
    exercised by products" pointing at the `accounts` app (products stays the
    canonical vehicle — the file's own scope rule).
  - [`GOAL.md`][goal]: the fakeshop target-example "auth mutations exercised by the
    existing test users" flips from growth-direction to shipped.
  - [`docs/TREE.md`][tree]: `auth/` package rows, `tests/auth/`, the `accounts`
    app, `test_auth_api.py` — closing the missing-`auth/`-row gap.
  - [`CHANGELOG.md`][changelog]: the `0.0.13` release bullets for both cards —
    **only when explicitly requested in the maintainer prompt**.
  - [`KANBAN.md`][kanban]: card wrap to `DONE-040-0.0.13` with the `SpecDoc`
    pointing at this spec (kanban DB edit + `scripts/build_kanban_md.py` /
    `build_kanban_html.py` re-render; never a hand-edit of the generated exports).

## Risks and open questions

Each item names a preferred answer for the `0.0.13` cut and a fallback if
implementation reveals it is wrong.

- **The card's symbol list vs the factory-call shape.** The card DoD names
  `login_mutation`, `logout_mutation`, `register_mutation`, `current_user` as the
  deliverables without pinning whether they are fields or factories. Preferred
  reading
  ([Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export)):
  zero-argument-callable **factories** (`login = login_mutation()`), matching both
  the package's field-factory idiom and upstream's `login = auth.login()` call
  shape, and giving every symbol the `permission_classes=` seam the card's
  composability DoD requires. Fallback: pre-built field *instances* — rejected
  unless the maintainer prefers them, because instances cannot carry per-schema
  `permission_classes`. Recorded per the [`docs/SPECS/NEXT.md`][next] "prefer the
  card, surface the conflict" rule.
- **[`docs/TREE.md`][tree] carries no `auth/` row for this card.** The target
  layout annotates every other WIP/TODO card's planned paths but reserves nothing
  for `TODO-ALPHA-040`; the card body, by contrast, names
  `django_strawberry_framework/auth/` explicitly. Preferred reading: the card is
  authoritative (the TREE row is an omission from the `0.0.14`-era annotation
  sweep); Slice 3 adds the rows. No fallback needed — the two sources do not
  actually conflict on substance.
- **Custom authentication backends with non-`username` credential kwargs.**
  `authenticate(request, username=, password=)` covers `ModelBackend` and every
  backend honoring the conventional kwargs (including email-login models via
  `USERNAME_FIELD`). A backend wanting different credential *names* (a
  `token=`-shaped backend) cannot ride `login_mutation()`. Preferred answer: out of
  scope — that consumer hand-writes their login mutation today exactly as before
  this card. Fallback: a `credential_fields=` factory kwarg mapping GraphQL
  arguments onto `authenticate` kwargs — a contained, additive follow-on if
  demanded.
- **A register customization surface.** The no-arg factory covers the parity case;
  a consumer wanting extra profile fields at registration has no seam short of
  hand-writing a mutation (with the plaintext-password foot-gun named in
  [Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
  Preferred answer for `0.0.13`: ship the factory as specced; record the demand.
  Fallback / follow-on: expose `DjangoRegisterMutation` as a documented
  subclassable base (its password write step inherited), the upstream shape — a
  small additive card, sequenced on real consumer need.
- **Native-async auth APIs** (`aauthenticate` / `alogin` / `alogout`, Django ≥
  5.0, in-support on the package's `Django>=5.2` floor). Preferred answer
  ([Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary)):
  keep the family's single `sync_to_async` boundary for `0.0.13`; adopting
  native-async session APIs is a family-wide decision for a dedicated card.
  Fallback: none needed — the boundary is correct, just not maximally concurrent.
- **Channels / websocket sessions.** Deferred to the `0.0.14` router card
  ([Decision 11](#decision-11--session-transport-constraints-sessionmiddleware--authenticationmiddleware-the-channels-fallback-is-not-borrowed));
  the risk is a consumer on ASGI websockets expecting upstream's fallback.
  Preferred answer: document the constraint in the GLOSSARY entry now; `041`
  decides whether to extend auth to consumer-scope sessions. Fallback: a fast
  follow-on porting upstream's `channels_auth` fallback once `041` gives it a
  reachable transport.
- **Where the live surface lives.** Preferred answer: a new schema-only fakeshop
  `apps/accounts/` (clean domain split; products stays the catalog vehicle per
  [`TODAY.md`][today]'s scope rule). Fallback: fold the auth fields into
  [`config/schema.py`][config-schema] directly if a models-less app proves awkward
  under fakeshop's app conventions — a mechanical relocation, settled in Slice 1.

## Out of scope (explicitly tracked elsewhere)

- **Channels ASGI router + websocket/consumer-scope auth** —
  [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]
  (`TODO-ALPHA-041-0.0.14`); upstream's `channels_auth` fallback ports there if at
  all
  ([Decision 11](#decision-11--session-transport-constraints-sessionmiddleware--authenticationmiddleware-the-channels-fallback-is-not-borrowed)).
- **The ergonomic `TestClient` / `GraphQLTestCase` helpers** —
  [`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase]
  (`TODO-ALPHA-043-0.0.14`); the live auth tests use the raw Django test client's
  session support today.
- **Token / JWT authentication and password-change / password-reset mutations** —
  no upstream analog in either reference package; [`BACKLOG.md`][backlog] material
  if ever ([Decision 2](#decision-2--card-scope-boundary-session-auth-ships-channels--token-auth-stay-out-no-new-meta--settings-key)).
- **A package-provided `UserType` default** — the consumer declares their own;
  a documented helper is a possible follow-on
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)).
- **A register customization surface** (subclassable base / extra-fields seam) —
  recorded follow-on ([Risks](#risks-and-open-questions)).
- **Field-level read gates** ([`FieldSet`][glossary-fieldset] /
  [Per-field permission hooks][glossary-per-field-permission-hooks]) — `0.1.1`;
  they will compose on top of the auth surface's returned user objects like any
  other type.
- **A new `DjangoType` `Meta` key or settings key** —
  ([Decision 2](#decision-2--card-scope-boundary-session-auth-ships-channels--token-auth-stay-out-no-new-meta--settings-key)).

## Definition of done

The completion contract the card is built against. Items map onto the card's own
DoD bullets: item 2 (the `auth/` module with the four symbols, composable with the
permissions surface), item 3 (mirrored tests under `tests/auth/`), item 4 (the
opt-in documentation) — plus the spec/CSV and the version-cut items the
[`docs/SPECS/NEXT.md`][next] flow and the joint-cut handoff add.

**Spec + companion CSV**

1. `docs/spec-040-auth_mutations-0_0_13.md` (this document) and its companion
   `spec-040-auth_mutations-0_0_13-terms.csv` exist;
   `uv run python scripts/check_spec_glossary.py --spec docs/spec-040-auth_mutations-0_0_13.md`
   reports `OK: <N> terms`.

**Slice 1 — auth substrate + `login` / `logout`, earned live**

2. `django_strawberry_framework/auth/` ships `login_mutation()` /
   `logout_mutation()` as field factories with the declaration ledger,
   `bind_auth_mutations()` wired into [`types/finalizer.py`][types-finalizer] phase
   2.5 **before** `bind_mutations()`, `LoginPayload` / `LogoutPayload` materialized
   through the ONE `build_payload_type` builder, the ledger clear registered through
   [`register_subsystem_clear`][registry], the user-model primary-type bind
   validation covering all three user-typed surfaces with the auth-specific
   message (the register arm pinned distinct from the generic
   `_resolve_primary_type` error)
   ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)),
   the AllowAny default + `permission_classes=` seam through the standard
   `check_permission` machinery, and sync + async resolver pairs over
   `django.contrib.auth` — failed authentication returning the ONE
   `"__all__"`-keyed [`FieldError`][glossary-fielderror-envelope]
   ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
   **In the same commit**, the fakeshop `accounts` surface exposes `login` /
   `logout` and `test_query/test_auth_api.py` earns every reachable branch live.
3. `tests/auth/test_mutations.py` mirrors the module for the package-only residue
   (ledger, bind validation, post-finalize raise, async, sessionless,
   [`SyncMisuseError`][glossary-syncmisuseerror]).

**Slice 2 — `register` + `current_user`, earned live**

4. `register_mutation()` synthesizes the cached `DjangoRegisterMutation`
   ([`DjangoMutation`][glossary-djangomutation] rider: `create` over
   `get_user_model()`, `Meta.fields = (USERNAME_FIELD, *REQUIRED_FIELDS,
   "password")`, `RegisterInput` via the name seams, privilege columns
   structurally absent) — **overriding `resolve_sync` AND `resolve_async`** to
   ride `run_write_pipeline_sync` with the password-aware step pair (the password
   pop in the decode step; `validate_password(password, user)` →
   `set_password` → `full_clean()` → `save()` in the write step; the `036`
   pipeline exposes no per-instance write hook), plaintext never persisted **on
   either path**, and **every factory call re-registering the cached rider into
   the mutation ledger** (identity-deduped, reload-safe) — exposed through the
   unchanged [`DjangoMutationField`][glossary-djangomutationfield], with the `036`
   payload re-fetch (by pk, no visibility filter, G2-gated)
   ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
   `current_user()` returns the nullable session actor without a
   [`get_queryset`][glossary-get_queryset-visibility-hook] re-run
   ([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)).
   **In the same commit**, the live suite covers the register → login → `me` →
   logout round trip, the duplicate-username and weak-password envelopes, the
   hashed-storage assertion, and anonymous `me: null`.
5. `tests/auth/` covers the internals residue (factory cache, the
   reload-idempotence cycle with `register` present in the second schema, the
   register-arm no-`UserType` error message, custom user-model field-set
   derivation, validator-mapping shapes, hash-ordering, the sync + async
   plaintext-never-persisted pair, lazy-user forcing).

**Cross-cutting — no regression**

6. The full suite is green at the 100% coverage gate (`fail_under = 100`);
   `ruff format` + `ruff check` are clean; the `036` / `038` / `039` mutation
   surfaces and the read side are unchanged.

**Slice 3 — docs + the `0.0.13` version cut + card wrap**

7. The version quintet reads `0.0.13` ([`pyproject.toml`][pyproject],
   `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], the
   GLOSSARY version line, the `uv.lock` package entry); the
   [Auth mutations][glossary-auth-mutations] GLOSSARY entry is `shipped (0.0.13)`
   with the implemented contract; the `039`-deferred flips land
   ([`SerializerMutation`][glossary-serializermutation] → `shipped (0.0.13)`,
   [`docs/README.md`][docs-readme] / [`README.md`][readme] "Shipped today" +
   Status → `0.0.13`); [`TODAY.md`][today] / [`GOAL.md`][goal] /
   [`docs/TREE.md`][tree] updated as pinned in [Doc updates](#doc-updates);
   [`CHANGELOG.md`][changelog] carries the `0.0.13` bullets **only under an
   explicit maintainer instruction**; [`KANBAN.md`][kanban] records
   `DONE-040-0.0.13` with this spec as its `SpecDoc` (DB edit + re-render)
   ([Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[backlog]: ../BACKLOG.md
[changelog]: ../CHANGELOG.md
[contributing]: ../CONTRIBUTING.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[pyproject]: ../pyproject.toml
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[feedback]: feedback.md
[feedback2]: feedback2.md
[glossary]: GLOSSARY.md
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-auth-mutations]: GLOSSARY.md#auth-mutations
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-cross-subsystem-invariants]: GLOSSARY.md#cross-subsystem-invariants
[glossary-definition-order-independence]: GLOSSARY.md#definition-order-independence
[glossary-djangoformmutation]: GLOSSARY.md#djangoformmutation
[glossary-djangographqlprotocolrouter]: GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangomodelpermission]: GLOSSARY.md#djangomodelpermission
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: GLOSSARY.md#djangomutationfield
[glossary-djangonodefield]: GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-fielderror-envelope]: GLOSSARY.md#fielderror-envelope
[glossary-fieldset]: GLOSSARY.md#fieldset
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-graphqltestcase]: GLOSSARY.md#graphqltestcase
[glossary-input-type-generation]: GLOSSARY.md#input-type-generation
[glossary-metafields]: GLOSSARY.md#metafields
[glossary-metainterfaces]: GLOSSARY.md#metainterfaces
[glossary-metamodel]: GLOSSARY.md#metamodel
[glossary-metaprimary]: GLOSSARY.md#metaprimary
[glossary-only-projection]: GLOSSARY.md#only-projection
[glossary-per-field-permission-hooks]: GLOSSARY.md#per-field-permission-hooks
[glossary-serializermutation]: GLOSSARY.md#serializermutation
[glossary-strictness-mode]: GLOSSARY.md#strictness-mode
[glossary-syncmisuseerror]: GLOSSARY.md#syncmisuseerror
[glossary-testclient]: GLOSSARY.md#testclient
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-034]: SPECS/spec-034-permissions-0_0_10.md
[spec-035]: SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-036]: SPECS/spec-036-mutations-0_0_11.md
[spec-038]: SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: SPECS/spec-039-serializer_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../django_strawberry_framework/conf.py
[forms-sets]: ../django_strawberry_framework/forms/sets.py
[init]: ../django_strawberry_framework/__init__.py
[mutations-permissions]: ../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../django_strawberry_framework/mutations/sets.py
[registry]: ../django_strawberry_framework/registry.py
[types-finalizer]: ../django_strawberry_framework/types/finalizer.py
[utils-permissions]: ../django_strawberry_framework/utils/permissions.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py

<!-- examples/ -->
[config-schema]: ../examples/fakeshop/config/schema.py
[config-settings]: ../examples/fakeshop/config/settings.py
[config-urls]: ../examples/fakeshop/config/urls.py
[create-users]: ../examples/fakeshop/apps/products/management/commands/create_users.py
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-auth-mutations]: ../../strawberry-django-main/strawberry_django/auth/mutations.py
[upstream-auth-queries]: ../../strawberry-django-main/strawberry_django/auth/queries.py
[upstream-auth-utils]: ../../strawberry-django-main/strawberry_django/auth/utils.py
