# Spec: Auth mutations — `login_mutation` / `logout_mutation` / `register_mutation` + the `current_user` query helper in an opt-in `auth/` module, riding the frozen `FieldError` envelope and the `DjangoMutation` foundation, and closing the joint `0.0.13` cut

Shipped in `0.0.13` (card [`DONE-040-0.0.13`][kanban]). This card adds the
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
a fourth write-flavor plumbing kit** (the standing DRY
review of the three-flavor stack): it is a thin
[`DjangoMutation`][glossary-djangomutation] rider — a `create` over
`get_user_model()` with a password-hashing write step — that adds **no** new field
converter, **no** new input generator, and **no** new pipeline *orchestration*. It
does carry its own decode / write **step pair**: the synthesized `Register` rider
(`__name__ = "Register"`, [Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor))
overrides the per-flavor resolver seam (`resolve_sync` / `resolve_async` — the same
seam the form and serializer flavors override) and rides the shared
`run_write_pipeline_sync` skeleton with a password-aware `decode_step` /
`write_step`, because the `036` create pipeline exposes **no** per-instance write
hook and its default steps would persist the raw password
([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
The only genuinely new machinery is the small session-auth resolver pair
(`django.contrib.auth.authenticate` / `login` / `logout` behind the envelope) and the
auth declaration ledger + `bind_auth_mutations()` phase-2.5 bind that materializes —
**surface-keyed, each artifact only when its surface was declared**
([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)) —
the `LoginPayload` / `LogoutPayload` classes and the `current_user` return alias before
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
requests it — [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told"; this spec describes the edit but cannot grant the permission).

Status: **SHIPPED (`0.0.13`) — all slices final-accepted; cross-slice integration pass + final test-run gate green.**
Three slices: Slice 1 (**the auth substrate + `login` / `logout`, earned live** — the
declaration ledger, the phase-2.5 bind, the payload materialization, the session
resolver pair, and the fakeshop `accounts` live surface land in one commit per the
[`examples/fakeshop/test_query/README.md`][test-query-readme] #"Coverage rule." /
[`docs/TREE.md`][tree] #"Coverage priority." live-first mandate), Slice 2
(**`register_mutation` + `current_user`, earned live** — the synthesized `Register`
rider with password validation/hashing, the `current_user`
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
`shipped (0.0.13)` with the implemented contract.

This spec's deliberative layer — the authoring revision history that produced the
contract across seven revisions, every Decision's justification, every alternative
each Decision rejected, and the risk / open-question deliberation that settled the
card's design questions — lives in the rationale companion
[`docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`][spec-040-rationale].

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the
vocabulary used throughout the spec:

- [Auth mutations][glossary-auth-mutations] — the subject. The glossary carries the
  entry as `shipped (0.0.13)` with the implemented contract: `login` / `logout` /
  `register` mutations plus a `current_user` query helper, **opt-in via explicit
  import** (not bundled into the default schema), composing with
  [`DjangoMutation`][glossary-djangomutation] and `django.contrib.auth`.
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
  ([`DONE-039-0.0.13`][kanban]), whose release-status wording was deferred **to this
  card's cut**; its GLOSSARY status reads `shipped (0.0.13)`, flipped by this card's
  Slice 3
  ([Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)).
- [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] /
  [`TestClient`][glossary-testclient] — the `0.0.14` cards this one does not ship: the
  Channels transport itself belongs to the router card, and multipart / session
  test-client ergonomics to the test-client card. Which transports the auth surface
  accepts once one exists, and how each refusal is stated, is
  [Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)'s.
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
  [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" —
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
- [`docs/TREE.md`][tree] — the target layout carries
  `django_strawberry_framework/auth/`, the `tests/auth/` tree, the fakeshop
  `accounts` app and the live `examples/fakeshop/test_query/test_auth_api.py`, added
  by this card's Slice 3 (the layout reserved no `auth/` row when the card opened — a
  gap recorded in [Risks and open questions][rationale-risks]).
- [`GOAL.md`][goal] — the fakeshop target-example paragraph names "auth mutations
  exercised by the existing test users" as a growth direction; this card ships it,
  and Slice 3 updates the wording from future to present.

## Slice checklist

> **Historical planning text (post-ship note):** the `- [ ]` boxes below are
> preserved as-authored and are intentionally not toggled here. The per-slice
> completion record — every sub-check ticked at build time and audited at final
> verification — was **retired** with the `0.0.13` cycle: the build plan and its
> three slice artifacts were deleted at the next cycle's pre-flight artifact
> reset and survive only in git history, at the release commit
> `3a294082` (`git show 3a294082:docs/builder/build-040-auth_mutations-0_0_13.md`
> and its `bld-slice-1-auth_substrate_login_logout.md` /
> `bld-slice-2-register_current_user.md` /
> `bld-slice-3-docs_version_cut_wrap.md` / `bld-integration.md` /
> `bld-final.md` siblings). Do **not** read the unprefixed `bld-*.md` files in
> the working tree as this card's record — `docs/builder/` is reused by whichever
> cycle is active, so those paths belong to another card. All slices are
> `final-accepted` per the status line at the top of this document.

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
        re-exports (`login_mutation` / `logout_mutation` in Slice 1;
        `register_mutation` / `current_user` added to the re-exports in Slice 2 as
        they land); **no package-root re-export**
        ([Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export)).
  - [ ] `django_strawberry_framework/auth/mutations.py` — the `login_mutation()` /
        `logout_mutation()` field factories (declaration-ledger recording +
        `strawberry.lazy` payload forward-refs + the sync/async resolver pair over
        `django.contrib.auth.authenticate` / `login` / `logout`), the
        `permission_classes=` seam with the explicit AllowAny default
        ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
  - [ ] The auth declaration ledger + `bind_auth_mutations()` wired into
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
  - [ ] Bind validation, Slice-1 scope: a declared `login` with no registered
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
  - [ ] **In the same commit:** the fakeshop `apps/accounts/` live surface (a
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
  - [ ] Mirrored package tests under `tests/auth/` for the residue a live query
        cannot drive (ledger idempotence / clear, bind validation — the login arm +
        the logout-only exemption, the post-finalize-declaration raise, async
        paths, the sessionless-request edge, and the permission-gate variants on
        isolated throwaway schemas — genuinely unreachable live under the
        one-declaration-per-process rule, [Test plan](#test-plan)).
- [ ] **Slice 2 — `register_mutation` + `current_user`, earned live**
  - [ ] `auth/mutations.py` grows `register_mutation()` — synthesizing (and caching)
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
        [Risks and open questions][rationale-risks]); [`TODAY.md`][today] notes the shipped
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
that module (the [`KANBAN.md`][kanban] #"Decision: Alpha cards must claim upstream parity"
rule; `graphene-django` ships **no** auth module, so this is single-upstream
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
  earlier DRY review of that three-flavor stack is the
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
- **Two distinct clear lifecycles already exist, and they matter here.**
  [`registry.py`][registry] ships one registration seam,
  `register_subsystem_clear(clear, *, owner, before_bind=False)`, and the
  `before_bind` flag is what splits the two lifecycles
  ([`registry.py::register_subsystem_clear`][registry] #"marks generated-state resets that the finalizer also").
  `TypeRegistry.clear()` replays **every** registered row through
  `iter_subsystem_clears()`; the [`types/finalizer.py`][types-finalizer] pre-bind
  reset block replays only the `before_bind=True` subset
  ([`types/finalizer.py::finalize_django_types`][types-finalizer] #"phase filter selects emitted namespaces and per-pass caches").
  So the **pre-bind INPUT-namespace / emit ledgers** are exactly the
  `before_bind=True` rows, and the declaration registries are **full-clear-only**
  rows ([`mutations/sets.py`][mutations-sets] #"register_subsystem_clear(clear_mutation_registry",
  [`forms/sets.py`][forms-sets] #"register_subsystem_clear(clear_form_mutation_registry").
  The auth **declaration** ledger follows that latter path; only the auth **emit**
  artifacts carry `before_bind=True`
  ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
- **No `auth/` module exists, and [`docs/TREE.md`][tree] does not reserve one.** The
  target package layout annotates every WIP/TODO-card path (`routers.py` for `041`,
  `middleware/` for `042`, `testing/client.py` for `043`, `extensions/` for `044`)
  but carries **no** `auth/` row for this card — a doc gap recorded in
  [Risks and open questions][rationale-risks] and fixed in Slice 3.
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
4. **Register safely.** The generated registration input is narrowed to
   `(USERNAME_FIELD, *REQUIRED_FIELDS, "password")`, and account-control state
   (`is_active` / `is_staff` / `is_superuser` / `groups` / `user_permissions`) is kept
   off it by **two** layers: the stock user model's narrowed set never names one of
   them, and a custom model that does place one in `USERNAME_FIELD` /
   `REQUIRED_FIELDS` is refused at declaration with a
   [`ConfigurationError`][glossary-configurationerror]; the password is validated
   against `AUTH_PASSWORD_VALIDATORS` (with the constructed user instance, so
   similarity validators bite) and stored only through `set_password`
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

- **An ASGI transport of this card's own.** The package's Channels story is the
  `0.0.14` [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]
  card's, not this one's; this card ships no router, no consumer, and no scope
  handling. What the auth surface does with the transports that card provides —
  which it accepts, and which it refuses rather than answer untruthfully — is
  [Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)'s,
  and upstream's *fallback* shape (a `channels_auth` path attempted after the Django
  path fails) is not borrowed on any transport.
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
  ([Decision 2](#decision-2--card-scope-boundary-session-auth-ships-token-auth-stays-out-no-new-meta--settings-key)).
- **Changing the frozen contracts.** No field is added to
  [`FieldError`][glossary-fielderror-envelope]; the payload builder, the
  [`DjangoMutationField`][glossary-djangomutationfield] factory, and the
  `036` / `038` / `039` surfaces are reused unchanged.

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it?" test this card is
**single-upstream parity**: `strawberry-graphql-django` ships
[`strawberry_django/auth/`][upstream-auth-mutations]; `graphene-django` ships no auth
module at all. The [`KANBAN.md`][kanban] #"Decision: Alpha cards must claim upstream parity"
rule is satisfied honestly with the 🍓 Required link alone — the card's
`Verified in upstream` section grounds it in the three upstream files, all read for
this spec. The borrowing splits along the package's standing line — *behaviorally*
copy the upstream's good ideas, *surface-wise* stay DRF-shaped and envelope-first.

One scope note the [`GOAL.md`][goal] north-star invites:
the pinned cookbook working reference carries **no** auth surface at all — it is pure
read-side nodes + filter / order / aggregate / fieldset sidecars +
[`get_queryset`][glossary-get_queryset-visibility-hook] visibility — so this card does
**not** advance the six-file cookbook/astronomy north-star *shape* ([`GOAL.md`][goal]
"What success looks like"); it advances the adjacent [`GOAL.md`][goal] fakeshop
target-example direction ("auth mutations exercised by the existing test users"). That
is exactly why the single-upstream-parity framing is honest: auth is a
`strawberry-graphql-django` parity item, adjacent to the north star, not a cookbook
parity one.

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
- **`get_current_user(info)`'s core** — the actor off the resolved request. Upstream's
  ASGI-scope **fallback** is not borrowed (below): the shared
  [`request_from_info`][utils-permissions] contract already resolves either request
  shape, so `me` needs no scope-sniffing branch of its own
  ([Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)).

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
- **The fallback *shape* — a `channels_auth` path attempted after the Django path
  fails, and a scope-sniffing user extraction.** The package classifies the transport
  explicitly before any credential or session work instead, so no path is entered
  speculatively and no transport is diagnosed from the failure it caused. The Channels
  **capability** (`channels.auth`'s `login` / `logout`) is used, on an already-classified
  Channels scope
  ([Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)).
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
  email: String
  password: String!
}
```

`username` and `password` are non-null (`AbstractUser.username` has no
`blank` / `default`; `AbstractBaseUser.password` is a plain `CharField(max_length=128)`);
`email` is **optional** (`AbstractUser.email` is `EmailField(blank=True)`) — each
`REQUIRED_FIELDS` entry follows the standard `input_field_required` rule
([`mutations/inputs.py`][mutations-inputs] #"return not field.blank"), which is
semantically right: Django's own model validation accepts a blank email, and
`REQUIRED_FIELDS` governs `createsuperuser`'s **interactive** prompts, not model-level
required-ness. Forcing a `REQUIRED_FIELDS` entry to non-null would need a generator
knob (contradicting "generator unchanged") or a per-entry input-class merge override
(hairy for FK-typed entries), so this card does neither
([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).

The `node` slot in the SDL above is the **fakeshop-specific rendering**, not the
generic contract: the example `UserType`
implements `relay.Node`, and `payload_object_slot(primary)`
([`mutations/inputs.py`][mutations-inputs]) names the object slot `node` for a
Relay-backed primary and `result` otherwise. The generic `login` / `register`
payload contract is "the uniform object slot per `payload_object_slot`" — and `me`
returns the user type **directly**, with no slot at all. Tests must not encode the
Relay-only `node` name as the generic contract ([Test plan](#test-plan)).

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
| Unstorable (non-UTF-8-encodable) `username` or `password` on `login` | same `"__all__"` envelope, short-circuited by the storability preflight before `authenticate` — byte-identical, never a top-level error |
| Password fails a configured validator on `register` | payload `errors` keyed to `password`, one message per failing validator |
| Unstorable (non-UTF-8-encodable) `password` on `register` | payload `errors` keyed to `password`, from the write step's storability preflight before `validate_password` / `set_password` — never a top-level error (the `username` half is rejected earlier, by the shared decode) |
| Duplicate username on `register` | payload `errors` keyed to the `USERNAME_FIELD` (the model `full_clean()` unique check) |
| `logout` with no authenticated session | `ok: false`, empty `errors` (not an error — idempotent logout) |
| `login` over a Channels WebSocket, any session engine | top-level `GraphQLError` ([`ConfigurationError`][glossary-configurationerror]) refusing before authentication — never the failed-login envelope ([Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)) |
| `logout` over a Channels WebSocket on the signed-cookie session engine | top-level `GraphQLError` ([`ConfigurationError`][glossary-configurationerror]) refusing before any session mutation ([Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)) |
| `login` or `logout` with no session on the path (no `SessionMiddleware` / `AuthMiddlewareStack`) | top-level `GraphQLError` ([`ConfigurationError`][glossary-configurationerror]) naming the missing middleware, raised by the prologue's session pre-check before any credential or session work ([Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully) / [Edge cases](#edge-cases-and-constraints)). `register` / `me` are unaffected — the actor is simply anonymous |
| Anonymous `me` | `null` (never an error — the nullable-by-contract read posture) |
| A `permission_classes` denial on any auth field | top-level `GraphQLError` (the standing write-auth contract — authorization failures are not envelope entries) |
| Malformed input (missing argument, wrong type) | standard GraphQL validation error (never reaches the resolver) |

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

This spec was authored at `docs/spec-040-auth_mutations-0_0_13.md` with companion
`docs/spec-040-auth_mutations-0_0_13-terms.csv` (both archived post-ship to
`docs/SPECS/`, where this document now lives), per the
[`docs/SPECS/NEXT.md`][next] convention (`spec-<NNN>-<topic>-<X_Y_Z>.md`; NNN `040`
from the card [`DONE-040-0.0.13`][kanban], topic slug `auth_mutations`, version
segment `0_0_13`).

Rationale companion — this Decision's rejected alternative:
[Decision 1][rationale-d1].

### Decision 2 — Card-scope boundary: session auth ships; token auth stays out; no new `Meta` / settings key

This card ships exactly the four-symbol session-auth surface over
`django.contrib.auth`. The ASGI-transport story itself belongs to the `0.0.14`
router card [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter];
which transports the four auth fields accept, and how each is rejected when it
cannot honour the surface truthfully, is
[Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)'s
single statement. The surface does **not** ship token/JWT auth (no upstream analog; backlog
material), password-change/reset flows (no upstream analog), or any new
[`DjangoType`][glossary-djangotype] `Meta` key or [`conf.py`][conf] settings key —
the auth surface composes purely from factories and the existing seams, so
`DEFERRED_META_KEYS` and the settings reader are untouched (the [`START.md`][start]
"add a settings key only when the feature that needs it lands" rule: nothing here
needs one).

Rationale companion — this Decision's justification and its two rejected
alternatives: [Decision 2][rationale-d2].

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

Rationale companion — this Decision's justification and its three rejected
alternatives: [Decision 3][rationale-d3].

### Decision 4 — Module and test locations: `auth/` mirroring the upstream trio; `tests/auth/` mirroring source

New subpackage `django_strawberry_framework/auth/`:

- `auth/__init__.py` — re-exports the four public factories (the one import line
  consumers write).
- `auth/mutations.py` — `login_mutation()` / `logout_mutation()` /
  `register_mutation()`, the synthesized `Register` rider class (`__name__ =
  "Register"`, [Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)),
  the login / logout permission-holder classes, the sync/async session resolvers,
  the declaration ledger, and `bind_auth_mutations()`.
- `auth/queries.py` — `current_user()` and its resolver pair.
- [`auth/sessions.py`][auth-sessions] — the module-private transport-classification and
  session-capability layer the `login` / `logout` state machines open on. It is
  deliberately not re-exported (neither `auth/__init__.py` nor the package root
  names it) and importing it stays `channels`-free; its contract is
  [Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)'s.

Tests mirror source per the [`AGENTS.md`][agents] placement rule:
`tests/auth/test_mutations.py`, `tests/auth/test_queries.py`,
`tests/auth/test_sessions.py` for package-only
internals; the live consumer surface lands in
`examples/fakeshop/test_query/test_auth_api.py` (the primary harness — Slices 1–2
land resolver code and its live coverage in the same commit).

Rationale companion — this Decision's justification and its two rejected
alternatives: [Decision 4][rationale-d4].

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

**Resolver semantics** (the upstream borrow, envelope-transported). The steps below
are the credential and session semantics; the transport prologue both resolvers open
with — transport classification, the per-surface capability check, and the
missing-session-middleware guard, all of which run before the gate and before any
credential or session work — is
[Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)'s:

1. `request = request_from_info(info, family_label="AuthMutation")` — the shared
   request resolver every permission seam uses ([`utils/permissions.py`][utils-permissions]);
   the `family_label` is a single module-level `_AUTH_FAMILY_LABEL` constant reused by
   every auth surface, never a per-field string literal, so the resolution wording cannot
   drift between fields (the helper-reuse review's D1 reuse directive).
2. Authorization: run the field's `permission_classes` through the shared
   `authorize_or_raise` gate via the permission carrier (named below). A denial is a
   top-level `GraphQLError` — identical to every write flavor.
3. `login`, credential storability preflight: a credential that is not UTF-8
   encodable (a lone surrogate) would crash `authenticate` into a raw
   `UnicodeEncodeError` from the `USERNAME_FIELD` lookup or the password hasher's
   `.encode()`, so each of `username` / `password` is preflighted through the ONE
   shared write-side `unencodable_text_error` primitive
   ([`utils/write_values.py`][utils-write-values]) and an unstorable credential
   short-circuits to the SAME undifferentiated failed-login envelope as step 4 —
   never a top-level error, and byte-identical so the preflight is not an
   enumeration oracle of its own.
4. `login`: `user = auth.authenticate(request, username=username,
   password=password)` — exactly one call, with no local user-model query (the
   actor-not-lookup rule). `None` → the payload with `node: null` and ONE
   `"__all__"`-keyed [`FieldError`][glossary-fielderror-envelope]
   (`"Incorrect username/password"`) — built via the `field_error("", …)` empty-path
   leaf ctor ([`mutations/resolvers.py`][mutations-resolvers]), which normalizes the
   empty path to `NON_FIELD_ERROR_KEY`, **never** a hard-coded `"__all__"` string (the
   helper-reuse review's D8 reuse directive — the leaf ctor owns the sentinel).
   Success → the session is established, then
   the payload with the user in the slot. The message is deliberately
   undifferentiated (no "unknown user" vs "wrong password" split — no
   account-enumeration oracle), the exact upstream wording.
5. `logout`: `ok` is whether an **authenticated actor existed before teardown**,
   answered by the ONE shared anonymity definition
   ([`auth/mutations.py::_authenticated_actor_or_none`][auth-mutations]) `current_user`'s
   nullable return also derives from — so a request with no actor the middleware could
   load (`SessionMiddleware` without `AuthenticationMiddleware`, or a transport adapter
   whose scope carries no middleware-loaded user) and a request whose `user` is
   unauthenticated both read `ok: false`, and the classification cannot drift between
   the two fields or between transports. The payload is constructed **before** any session
   mutation (so `ok` describes the state being transitioned and a
   payload-construction failure cannot follow a completed teardown), then the
   session teardown runs unconditionally (flushing the session whether or not
   authenticated — idempotent), returning `{ ok, errors: [] }`. A teardown failure
   propagates; it is never reported as `{ok: true}`.

**The anonymous-allowed default — the deliberate inversion.** The write family's
posture is deny-by-default ([`DjangoModelPermission`][glossary-djangomodelpermission]
for model-backed writes; [`DenyAll`][mutations-permissions] for the model-less plain
form). Auth mutations are the **front door**: requiring authentication to
authenticate is a contradiction, so each auth factory's *unset*
`permission_classes` resolves to the explicit empty list — the `036` AllowAny
semantics (an empty class list authorizes every request). **There is no `AllowAny`
class anywhere in the package, and this card adds none**: "AllowAny" is this spec's
shorthand for the *semantics* of the empty
permission-class list, produced by `_validate_permission_classes(...,
unset_default=())` — the implementation must not mint a new public `AllowAny`
primitive, and every "AllowAny" in this document reads as "empty list /
allow-all". This is not a weakening of
the family rule but its documented, single-sited exception: the factories pass the
explicit default into the same `_validate_permission_classes` normalization
([`mutations/sets.py`][mutations-sets]) every flavor uses, so a consumer who
supplies `permission_classes=[...]` (rate-limit gate on `login`, invite gate on
`register`, a locked-down `logout` if they insist) gets the standard
`has_permission(info, mutation, operation, data, instance)` contract, including the
sync-only rule (an `async def` hook is a
[`SyncMisuseError`][glossary-syncmisuseerror], never a silent allow).

**The permission carrier — named, reused by call, not re-spelled**. `register`
inherits the write-auth machinery for free (it IS a
[`DjangoMutation`][glossary-djangomutation]), but `login` / `logout` /
`current_user` are fixed field factories, not mutation subclasses — and
[`authorize_or_raise`][mutations-resolvers] assumes a zero-arg-constructible class
exposing `check_permission` + `_mutation_meta` + `_primary_type`
([`mutations/resolvers.py`][mutations-resolvers] `::authorize_or_raise` #"mutation_cls().check_permission").
So each auth factory synthesizes a tiny **module-internal permission holder class**
carrying exactly that duck-typed shape: a `_mutation_meta`-shaped snapshot exposing
the normalized `permission_classes` (produced by the shared
`_validate_permission_classes(..., unset_default=())` — the AllowAny default) plus
the operation string, a `_primary_type` (the resolved user primary for `login` /
`current_user`; `None` for the model-less `logout`), and
`check_permission = DjangoMutation.check_permission` bound directly (its body reads
only `type(self)._mutation_meta.permission_classes`, so the duck-typed snapshot
suffices — it is **not** a `_ValidatedMutationMeta`, which would require `model` /
`operation` constructor kwargs). **That holder synthesis is single-sited in ONE
`_make_permission_holder(operation, holder_name, permission_classes)` helper** —
`login` / `logout` / `current_user` all call it rather than each spelling a
near-identical class body, so the duck-typed `_mutation_meta` shape lives in one place;
the only per-field inputs are the pinned `operation` string and the pinned holder
`__name__` (the helper-reuse review's D3 / P4 reuse directive). The `_primary_type`
slot is minted `None` and assigned at bind — the user primary is unresolved at
class-body time
([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)) —
and the model-less `logout` holder keeps it `None`. **Both halves of the holder's
authorization state are sealed at synthesis**: the snapshot refuses attribute
rebinding and deletion, and the holder class refuses rebinding or deleting its
`_mutation_meta` head, each with a [`ConfigurationError`][glossary-configurationerror].
A custom `has_permission` runs inside the permission walk holding the holder class,
so an unsealed slot would let one request's hook replace the validated permission
set for every later `login` / `logout` / `me` request. The factory's resolver then calls
`authorize_or_raise(holder_cls, info, operation, data, instance=instance)` before the
session work, so the iteration, the `GraphQLError` denial, and the async-hook
[`SyncMisuseError`][glossary-syncmisuseerror] guard (`reject_async_in_sync_context`
with `_PERMISSION_ASYNC_RECOURSE`) are all reused **by call**, not re-implemented.
**The gate payload is pinned per field** so a custom
`has_permission` knows exactly what it receives — `authorize_or_raise` threads `data` /
`instance` straight into `check_permission` → `has_permission`
([`mutations/resolvers.py`][mutations-resolvers] `::authorize_or_raise`): `login`
passes `data = {"username": username}` (the attempted credential — **never** the
password) and `instance=None` (there is no pre-auth object), so an account-scoped
rate-limit / lockout gate can key on the attempted username while an IP-only gate
ignores `data` and reads `request_from_info(info)`; `logout` passes `data=None`,
`instance=None`; `current_user` passes `data=None`, `instance=<request user | None>`
([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)).
The pinned operation strings are `"login"` / `"logout"` / `"current_user"`; the
denial message is `authorize_or_raise`'s standard
`f"Not authorized to {operation} {target}."`, where `target` is the resolved user
type for `login` (e.g. `"Not authorized to login UserType."`) and the holder class
`__name__` for the model-less `logout` (the same `_primary_type is None` fallback the
plain form's `"Not authorized to form <FormClass>."` uses). **The holder `__name__`s
are pinned, not left to implementation taste** — the denial strings are
test-asserted contracts: the login holder is `Login`
and the `current_user` holder is `CurrentUser` (their denial strings read the
resolved user type, so those names never surface in a denial), and the logout
holder — whose `__name__` IS the denial target under the `_primary_type is None`
fallback — is **`Session`**, so its string reads cleanly. The four expected denial
strings, exactly: `"Not authorized to login <UserType>."`,
`"Not authorized to logout Session."`,
`"Not authorized to current_user <UserType>."`, and — for `register`, a real
[`DjangoMutation`][glossary-djangomutation] with `operation = "create"` —
the standard `"Not authorized to create <UserType>."` (where `<UserType>` is the
consumer primary's `__name__`). The `tests/auth/` gate tests assert these exact
strings on isolated throwaway schemas — the gated variants cannot coexist with the
aggregate fakeshop default surface under the one-declaration-per-process rule
([Test plan](#test-plan)).

**`DjangoModelPermission` is incompatible with the model-less auth fields — by
documentation, not a factory-time guard.** Passing
`login_mutation(permission_classes=[DjangoModelPermission])` (the *write* family's
default class) raises at **request time**, not deny: its `has_permission` reads
`mutation._resolve_model(mutation.Meta)` and `_OPERATION_PERMISSION_ACTION[operation]`
([`mutations/permissions.py`][mutations-permissions]), and the holder has no `Meta`
model and no `"login"` / `"logout"` action mapping. This is the exact hazard the
package already documents for the model-less plain form
([`DenyAll`][mutations-permissions] #"it would raise at request time, not deny"), so
this card follows the same posture: document the incompatibility (model-permission
classes need a model + a create/update/delete operation; auth fields want a custom
`has_permission` such as a rate-limit or invite gate), rather than adding a
factory-time `issubclass` reject that would also refuse legitimate consumer
subclasses of `DjangoModelPermission` that override `has_permission` for session
verbs. (`register`, a real `DjangoMutation` with `operation = "create"` → the
`add_<user>` perm, is unaffected — `DjangoModelPermission` works there.)

**This generalizes beyond `DjangoModelPermission`**.
The incompatibility is not that one class's quirk — it is structural: `check_permission`
passes the holder **itself** as the `mutation` positional to any custom `has_permission`
(`permission_class().has_permission(info, type(self), operation, data, instance)`,
[`mutations/sets.py`][mutations-sets]), and for `login` / `logout` / `current_user` that
object is the internal permission holder, **not** a
[`DjangoMutation`][glossary-djangomutation]: it carries the duck-typed `_mutation_meta`
+ `_primary_type` the gate machinery reads, but **no `Meta.model`, no `_resolve_model`**,
none of the create/update/delete shape a real mutation exposes. So [Goal 3](#goals)'s
"gate any auth field without new machinery" holds for gates keyed on `info` /
`operation` / `data` (a rate-limit, invite, IP allow-list, or `IsAuthenticated`-style
check — the intended cases), but a gate that **introspects the `mutation` argument**
(reads `mutation.Meta.model`, branches on the concrete class) raises at request time on
the three model-less fields. The rule for those three, stated plainly: **key on `info` /
`operation` / `data`, never on the mutation object.** This is documented, not
factory-time guarded (the `DenyAll` request-time-raise precedent applied to the general
case). `register`, a real `DjangoMutation`, carries the full shape and is unaffected.

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

Rationale companion — this Decision's justification and its five rejected
alternatives: [Decision 5][rationale-d5].

### Decision 6 — `register_mutation()` rides `DjangoMutation`: a narrow `create` over `get_user_model()` with password hashing — NOT a fourth flavor

`register_mutation()` synthesizes (once, cached) a concrete package-declared
subclass of [`DjangoMutation`][glossary-djangomutation] whose **`__name__` is pinned
to `Register`** with:

- `Meta.model = get_user_model()`, `Meta.operation = "create"`.
- [`Meta.fields`][glossary-metafields] narrowed to
  `(USERNAME_FIELD, *REQUIRED_FIELDS, "password")` — the
  Django-blessed minimal account shape (`createsuperuser`'s own prompt set).
  **The derivation is a directly-testable helper,
  `derive_register_fields(user_model) -> tuple[str, ...]`**: it takes the model as
  an argument — never reading
  `get_user_model()` inline — and the rule is exact: `USERNAME_FIELD` first, then
  each distinct `REQUIRED_FIELDS` entry in declaration order, then `password`
  exactly once, deduplicated (an entry repeating `USERNAME_FIELD` or `password`
  appears once). Unknown / non-editable / reverse names are rejected as the
  bind-time [`ConfigurationError`][glossary-configurationerror] naming field +
  model by **delegating to the standard `editable_input_fields` validation**
  ([`mutations/inputs.py`][mutations-inputs] — which already raises naming field +
  model, maps a forward FK to `<field>_id`, and includes forward M2M), never
  re-implemented. The model argument is what lets both the default and a
  custom-`USERNAME_FIELD` / custom-`REQUIRED_FIELDS` model be tested directly with
  a test-scoped model — no second Django project and no `AUTH_USER_MODEL` swap
  ([Test plan](#test-plan)). Account-control state is kept off the public
  registration surface by **two** layers, because the derivation reads the model:
  for the stock user model the narrowed set simply never names `is_staff` /
  `is_superuser` / `is_active` / `groups` / `user_permissions`, so privilege
  escalation is structurally unreachable
  ([Input type generation][glossary-input-type-generation] narrows via the standard
  `Meta.fields` path, reusing the model-column converter unchanged); and because a
  **custom** user model may place one of those five in `USERNAME_FIELD` /
  `REQUIRED_FIELDS` — which would turn a model declaration into a privilege or
  activation-control input — `derive_register_fields` rejects the derived tuple with
  a [`ConfigurationError`][glossary-configurationerror] naming the offending field(s)
  and the model, directing the consumer to initialize privileges and activation state
  in server-owned registration logic. The protected set is a single module-level
  frozenset, so the five names are stated once. Because the **stock** user model's
  narrowed set has **no relation inputs** (`groups` / `user_permissions` are excluded),
  register wires **none** of the relation-visibility helpers (`relation_kind` /
  `is_forward_many_to_many` / `visible_related_object(s)`); whatever relation handling a
  narrowed set does need — a custom model's `REQUIRED_FIELDS` forward FK taking the
  standard `<field>_id` input, or a consumer widening `Meta.fields` — comes for free via
  the inherited decode, so the rider adds nothing and auth-local helpers must not be
  added preemptively (the helper-reuse review's D-N3 deliberate-non-reuse note).
- `Meta.permission_classes` defaulted to the explicit AllowAny (Decision 5's
  inversion), overridable through the factory's `permission_classes=` kwarg.
  **`permission_classes` is class-local, so `register` is one declaration per
  process**: the permission classes live on the
  synthesized class's `Meta` snapshot ([`mutations/sets.py`][mutations-sets]
  `::_validate_permission_classes` /
  [`DjangoMutation`][glossary-djangomutation]`.check_permission`), and the class's
  fixed `RegisterInput` / `RegisterPayload` names cannot serve two distinct
  permission-specialized classes (`build_payload_type` mints a fresh payload per
  class, and `materialize_generated_input_class` raises on a second distinct class
  under an existing name). So a same-`permission_classes` `register_mutation()`
  call returns the identity-deduped cached class, but a second call with a **different**
  `permission_classes` raises a [`ConfigurationError`][glossary-configurationerror]
  naming the conflict (there is one `register` field per schema in practice; the
  raise makes a conflicting second declaration loud rather than a silent ledger
  collision). The same one-declaration-per-process rule holds for the fixed-payload
  `login` / `logout` / `current_user` holders
  ([Edge cases](#edge-cases-and-constraints)). **The conflict / cache key is the
  schema-affecting declaration args only — today exactly the normalized
  `permission_classes`**: `description` /
  `deprecation_reason` / `directives` are per-field `strawberry.field`
  presentation kwargs, applied to each returned field and never part of the
  generated types. Each factory's own keyword-only signature is what partitions its
  kwargs into three classes — resolver GraphQL args | declaration args
  (`permission_classes`, plus any future payload-/type-affecting arg) | Strawberry
  field kwargs — and each class reaches exactly one consumer: the GraphQL args go to
  the shared signature builder, the declaration args to the ONE declaration path, and
  the field kwargs straight to `strawberry.field`. **Only the declaration args enter
  the key**, because only the declaration path sees them.
  `login_mutation(description="A")` after `login_mutation(description="B")` is the
  cached-idempotent path with the new field metadata, never a
  false-`ConfigurationError`. **And the key's state is the surface-keyed
  declaration ledger itself, drained by its full-clear-only row**: the cached holder
  / rider lookup and the conflict
  check both read the ledger, so after a `registry.clear()` a re-declaration with a
  *different* `permission_classes` mints a fresh holder / rider rather than
  tripping a stale conflict raise that survives the clear
  ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)
  / [Edge cases](#edge-cases-and-constraints)).
- The **password step, carried on the per-flavor resolver seam**:
[`DjangoMutation`][glossary-djangomutation] exposes **no
  per-instance write hook** — `_run_pipeline_sync` hard-wires the model
  `decode_step` / `write_step` as module-level lambdas
  ([`mutations/resolvers.py`][mutations-resolvers] `::_run_pipeline_sync`), and the
  defaults are unsafe for this model: `_model_decode_step` would construct
  `model(password=<raw>)` and `_model_write_step` would `full_clean()` (which only
  checks the 128-char `max_length`) and `save()` the **plaintext**. So
  the synthesized `Register` class overrides **both `resolve_sync` and
  `resolve_async`** — the same per-flavor seam the form and serializer flavors
  override — and rides the shared `run_write_pipeline_sync` skeleton with its own
  step pair. **The raw password is carried in an explicit decoded tuple, not an
  implicit closure**: `run_write_pipeline_sync` passes only the
  `decode_step`'s return into `write_step` ([`mutations/resolvers.py`][mutations-resolvers]
  `::run_write_pipeline_sync` #"write_step(instance, decoded) -> saved"), so the
  `decode_step` pops `password` out of the model attrs and returns the extended
  tuple `(user, m2m_assignments, exclude, raw_password)` — mirroring
  `_model_decode_step`'s `(target, m2m_assignments, exclude)` shape
  ([`mutations/resolvers.py`][mutations-resolvers] `::_model_decode_step`) with the
  raw password appended as a fourth element that never touches
  `model(**scalar_and_fk_attrs)`. **The decode reuses the shared UNSET-strip walk, not
  a second copy** (the helper-reuse review's D6 reuse directive): the
  provided-field iteration goes through the ONE shared decode spine every write
  flavor rides — [`decode_provided_fields`][utils-write-values] over
  [`iter_provided_input_fields`][utils-inputs] — and the auth-specific delta, capturing
  `password` out of the constructed model attrs, is a small reusable **exclusion
  seam declared at bind, honoured by the shared walk**, **not** a fork of the decoder
  (a forked walk is the classic place the UNSET / raw-`None`-vs-omitted rule drifts).
  The seam is a **field kind**, not a per-request parameter: the rider's `build_input`
  stashes `password` as kind `EXCLUDED` through
  [`mutation_input_field_specs`][mutations-inputs]`(…, excluded_attrs=…)`, and
  `_decode_relations` routes every `EXCLUDED` spec to its own `excluded_values` dest
  beside the scalar / FK / M2M dests, so the raw value never reaches
  `model(**scalar_and_fk_attrs)`. `_model_decode_step` then returns the extended
  four-tuple for any mutation whose specs carry that kind and the historical
  three-tuple otherwise, and the generic `_model_write_step` unpacks the three-tuple
  **strictly** — so a bind that introduces an `EXCLUDED` spec without pairing it to a
  flavor write step that knows what the value MEANS raises there instead of silently
  discarding it. **The seam must preserve the provided-marker**: `_model_decode_step`
  computes the create-path `full_clean` exclude from the
  *provided* attrs (`_provided_attr_names` → `_unprovided_exclude` — the AR-H2
  calculation), so naively popping `password` before the walk would mark it
  **unprovided** and silently drop the `password` column from `full_clean`
  validation. The seam therefore extracts the excluded value while the AR-H2
  calculation still counts `password` as provided — the register seam is "extract
  the protected input value *with its provided-marker preserved*," never merely
  "pop `password` from the model attrs" — and a focused helper-level test pins
  exactly that (value captured, marker preserved, attr absent from
  `model(**scalar_and_fk_attrs)`). The `write_step` unpacks that tuple and
  **preflights the captured value before touching it**, because riding the exclusion
  seam is exactly what routes `password` around the shared decode's own scalar checks
  (`decode_scalar_leaf`), which every other input scalar — this register's own
  `username` included — still runs through. Three guards, each returning the
  `password`-keyed envelope rather than a top-level error: an absent captured value
  is the standard null-field leaf; a non-`str` value is an `invalid`-coded
  `password` leaf; and a non-UTF-8-encodable value is rejected through the SAME
  shared [`unencodable_text_error`][utils-write-values] primitive the model decode
  uses, byte-identically to how that decode already rejects a surrogate `username`
  (a lone surrogate passes every configured validator — none of them encodes the
  text — and would then crash the hasher's `.encode()`). Only then does it run
  `django.contrib.auth.password_validation.validate_password(raw_password, user)`,
  and — on failure — maps the raised error to a `password`-keyed
  [`FieldError`][glossary-fielderror-envelope] **directly, not through the generic
  `validation_error_to_field_errors` mapper**. This is
  load-bearing: `validate_password` raises a **list-style** `ValidationError` (a bare
  message list, no `error_dict`), and the shared mapper's non-dict branch keys such an
  error to the `"__all__"` sentinel, not `password`
  ([`mutations/resolvers.py`][mutations-resolvers] `::validation_error_to_field_errors`
  #"return [field_error(\"\", list(exc.messages)...)]" → `field_error`'s empty-path →
  `NON_FIELD_ERROR_KEY`). So the write step catches the `ValidationError` at the
  `validate_password` call site and builds the leaf itself —
  `field_error("password", exc.messages, codes=[leaf.code for leaf in exc.error_list if leaf.code])`
  (the same [`spec-036`][spec-036] leaf ctor, keyed explicitly) — so every failing
  validator's messages land under the single `password` key, not `"__all__"`. It then
  runs `user.set_password(raw_password)`
  **before** `full_clean()` / `save()`. **The password preflight, `validate_password`
  and `set_password` are the ONLY auth-specific steps, and the preflight itself
  re-uses the shared primitives rather than spelling its own checks** (the
  helper-reuse review's D7 reuse directive): the
  `full_clean()` + `save()` + `IntegrityError` mapping are delegated to the shared
  write path (`_full_clean_or_field_errors` / [`save_or_field_errors`][mutations-resolvers]),
  so the duplicate-`USERNAME_FIELD` unique error and the concurrent-race `IntegrityError`
  come back through the standing envelope with no auth-specific error handling. The
  plaintext exists only in memory and
  never reaches a model column (a unit assertion pins that the model decode never
  receives `password` in `scalar_and_fk_attrs`); hashing before `full_clean()` means
  the `password` column validates against the hash rather than the raw input; and the
  **plaintext-never-persisted test is required on both the sync and the async path** —
  the async twin is a separate override and can regress independently.
- **The public names come from two different mechanisms**. The
  **input** name is pinned to `RegisterInput` via the `input_type_name` /
  `build_input` name seams (the [`spec-038`][spec-038]-established override point),
  because the input name otherwise derives from the *model* (`User`) plus the
  narrowed shape — the deterministic `UserEmailPasswordUsernameInput`. The
  **payload** name has **no seam**: the phase-2.5 bind's payload half
  ([`mutations/sets.py`][mutations-sets] `::bind_mutation_outputs`, which both
  write-declaration ledgers ride) calls
  `build_payload_type(mutation_cls.__name__, …)` and
  [`DjangoMutationField`][glossary-djangomutationfield]'s synthesized signature
  builds `f"{mutation_cls.__name__}Payload"` ([`mutations/fields.py`][mutations-fields]),
  both deriving **only** from the class `__name__`. This is exactly why the
  synthesized rider's `__name__` is pinned to `Register` (not `DjangoRegisterMutation`,
  which would emit `DjangoRegisterMutationPayload`): with `__name__ = "Register"` the
  unchanged machinery emits `RegisterPayload` for free — no payload-name seam is added
  (adding one would be a foundation change the "standard machinery" framing forbids).
  The `DjangoRegisterMutation` name is reserved for the possible consumer-facing
  subclassable-base follow-on ([Risks and open questions][rationale-risks]); it is not the
  concrete registered class.

**The genuine reuse, stated precisely**: the register
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
`DjangoMutationField(Register)` internally), the envelope from
`full_clean()` (duplicate `USERNAME_FIELD` → field-keyed error via the model's
unique constraint), and the post-save
[`refetch_optimized`][mutations-resolvers] by pk without visibility (the `036`
own-write exception — load-bearing here, since the brand-new anonymous-created user
is exactly the row a staff-only `UserType.get_queryset` would hide).

The synthesized class is created **lazily on first factory call** (not at module
import): creating it registers a mutation declaration, and a consumer who imports
`auth` only for `login_mutation` must not get a phantom user-input/payload
materialized at bind. **Every factory call — cached or not — re-records into BOTH
declaration ledgers: the mutation ledger (so `bind_mutations()` re-binds the rider)
AND the auth ledger (so `bind_auth_mutations()`'s
[Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)
validation still covers `register`)**. Both re-records are
identity-deduped ([`mutations/sets.py`][mutations-sets] `::make_declaration_registry`
#"if declaration_cls not in store"), so on a live ledger each is a no-op, and after a
`registry.clear()` drains both, a consumer re-declaration **re-appends to both**.
Critically, the auth-ledger record is **not** written once alongside the cached-class
synthesis and then left stale behind the cache guard: were it, a `registry.clear()`
(which the suite's complete-reload fixtures run every test) would drain it with no
re-add, `bind_auth_mutations()` would no longer see `register` on the second finalize,
and its
[Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)
arm would silently regress to `_resolve_primary_type`'s generic message — the exact
failure that Decision pre-empts. The every-call re-record on both ledgers closes that
path, so the rider survives the reload fixtures with its auth-specific error intact,
alongside `login` / `logout` (auth ledger, explicitly cleared and re-declared). A
reload-idempotence test pins the cycle: finalize → `registry.clear()` → re-declare →
finalize, asserting both that `register` is present in the second schema AND — for a
no-`UserType` schema — that the second finalize still fires the register-arm
auth-specific error (not the generic `_resolve_primary_type` one). Calls after
[`finalize_django_types`][glossary-finalize_django_types] raise the standing
declare-after-finalize [`ConfigurationError`][glossary-configurationerror].

Rationale companion — this Decision's justification and its five rejected
alternatives: [Decision 6][rationale-d6].

### Decision 7 — `current_user()` returns the session actor, nullable, and does not re-run `get_queryset`

`current_user()` returns a query **field** (not a mutation) whose resolver reads the
request user via the same `request_from_info` extraction and classifies it through
the ONE shared anonymity definition `logout`'s `ok` also derives from
([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)),
so the two fields cannot drift. It returns:

- the user object, typed as the user model's primary
  [`DjangoType`][glossary-djangotype], when the request carries an authenticated
  actor;
- `null` otherwise. "Otherwise" is every non-authenticated shape, not just the
  anonymous session: a request with **no `user` attribute at all** (a session
  without `AuthenticationMiddleware`, or a transport adapter whose scope carries no
  middleware-loaded user) reads `null` rather than raising, and a **hostile** actor —
  a `user` descriptor, an `is_authenticated` read, a legacy `is_authenticated()`
  callable, or an `is_authenticated` value whose truthiness raises `TypeError` /
  `ValueError` / `AttributeError` / `KeyError` / `IndexError` — collapses to `null`
  as well. The classification is **fail-closed in one direction only**: a hostile
  state is anonymous, never authenticated. Any other exception (a `DatabaseError`
  from forcing the lazy user) still propagates, so a real store outage is never
  disguised as an anonymous read.

**`current_user` is permission-gated like the other three, but its enforcement site
is the query resolver, not `run_write_pipeline_sync`**. It accepts
`permission_classes=` through the same
module-internal permission holder
([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)),
and its resolver runs `authorize_or_raise(holder_cls, info, "current_user", data=None,
instance=<the request user, or None when anonymous>)` **first** — a denial is a
top-level `GraphQLError` (authorization is not the same axis as the anonymous read).
Only after the gate passes does the nullable-return rule apply: an authenticated
actor is returned, an anonymous request resolves to `null`. So the two axes are
distinct — `permission_classes` denial → `GraphQLError`; allowed-but-anonymous →
`null`. The AllowAny default (Decision 5's inversion) means the unset case gates
nothing and every request reaches the null-or-user return; a consumer who wants
`me` to require authentication supplies a `permission_classes=[IsAuthenticated]`-style
class, which denies the anonymous caller with the `GraphQLError` instead of `null`.
This keeps the "every auth factory accepts `permission_classes=`" contract
([Goals](#goals) item 3) honest across all four surfaces.

The return annotation is `<UserPrimaryType> | None` via a bind-materialized
`strawberry.lazy` alias, attached through the **same signature-injection idiom the
field family already uses**. At class-body time the
user's primary type is not resolved, so — exactly as
[`DjangoMutationField`][glossary-djangomutationfield] builds a per-resolver
`inspect.Signature` + `__annotations__` whose return is a `strawberry.lazy` forward-ref
and assigns them onto its dispatcher (`_resolve.__signature__` / `_resolve.__annotations__`,
[`mutations/fields.py`][mutations-fields]) — the `current_user()` factory injects a
return annotation of
`Optional[Annotated["CurrentUserAlias", strawberry.lazy("django_strawberry_framework.auth.queries")]]`
onto its dispatcher resolver. **That `Annotated[…, strawberry.lazy(…)]` return ref is
built by the shared [`_lazy_ref`][mutations-fields]`(type_name, module_path)` helper** —
the same builder [`DjangoMutationField`][glossary-djangomutationfield] uses for its
`<Name>Payload` refs — not a hand-spelled `Annotated[...]`. What is **single-sited in
ONE auth field-construction helper** the three fixed factories share is the
sync-vs-async **dispatch seam** plus the signature / annotation injection, never
copied per field (the helper-reuse review's D12 / P1 / P2 reuse directive); the
per-surface request resolution, permission gate and session work live in the sync and
async resolver **bodies** that helper is handed, which is what makes them the
per-transport specialization point without the dispatch seam changing
([Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary)).
To keep that single copy
honest across `mutations/` and `auth/`, [`_lazy_ref`][mutations-fields] and the
`_resolve.__signature__` / `_resolve.__annotations__` injection assignment are promoted to
shared machinery rather than re-spelled in `auth/`. **The `"CurrentUserAlias"` slot is owned by a
[`make_input_namespace`][utils-inputs]`("django_strawberry_framework.auth.queries",
"AuthMutation")` trio, not a hand-rolled `setattr` / `delattr` pair** (the
helper-reuse review's D13 reuse directive): `bind_auth_mutations()` pins the
alias by calling that trio's `materialize_fn("CurrentUserAlias", primary_type)` — which
sets the module global through the blessed [`materialize_generated_input_class`][utils-inputs]
parked-global path — and the trio's `clear_fn` empties the ledger. Because that `clear_fn`
is the alias namespace's pre-bind [`register_subsystem_clear`][registry] row, the ledger is
empty before each re-materialize, so a *different* `UserType` class object on a reload's
second finalize does not trip the distinct-class collision guard. Strawberry resolves the
lazy ref to the concrete `UserType` at schema build and the SDL reads `me: UserType`.
`login` / `logout` attach their `LoginPayload` / `LogoutPayload` return refs the same way,
into the `mutations.inputs` namespace
([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
The resolver performs **no queryset work**: no
[`get_queryset`][glossary-get_queryset-visibility-hook] re-run, no re-fetch — the
returned object is the actor the transport's own middleware already loaded
(`request.user` under `AuthenticationMiddleware`, the scope's user under
`AuthMiddlewareStack`, reached through the one shared request resolver), lazily; the
resolver's `is_authenticated` access forces it, the upstream trick.
Nested relation selections under `me { ... }` resolve through the type's generated
resolvers as usual (an unplanned deep selection is visible to
[Strictness mode][glossary-strictness-mode] like any non-root object — the same
posture as the mutation payload slot).

Rationale companion — this Decision's two justifications and its three
rejected alternatives: [Decision 7][rationale-d7].

### Decision 8 — The user model's primary `DjangoType` is required, validated at bind

`login_mutation()`, `register_mutation()`, and `current_user()` all type their user
surface as the **primary** [`DjangoType`][glossary-djangotype] registered for
`get_user_model()` (the [`Meta.primary`][glossary-metaprimary] registry lookup every
payload resolution uses). The consumer declares it — their field selection, their
[`Meta.interfaces`][glossary-metainterfaces], their visibility hook for directory
reads. `bind_auth_mutations()` validates at phase 2.5, **and only when the surface-keyed
ledger carries a user-typed surface** — a logout-only ledger never performs the
lookup at all, so the exemption below is structural, not a message branch
([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)'s
surface-keyed bind): it resolves the user primary via
[`registry.get`][registry]`(get_user_model())` — **the same getter
`_resolve_primary_type` uses**, so "what counts as a registered primary" stays
single-sited and only the raise *message* differs between the auth check and the generic
mutation bind (the helper-reuse review's D16 reuse directive). It consults
[`registry.types_for`][registry] only to split the no-registered-type message from the
multiple-types-without-primary ambiguity message. If any of the three user-typed fields
was declared while that lookup returns `None`,
finalization fails with a [`ConfigurationError`][glossary-configurationerror] naming
the missing registration and the fix ("declare a `DjangoType` with
`Meta.model = get_user_model()`; mark it `Meta.primary = True` if the model has
several"). `logout_mutation()` is exempt — its `{ ok, errors }` payload references
no user type, so a logout-only schema (however unlikely) needs no user type and
resolves no primary.

**The validation must run BEFORE `bind_mutations()` to be reachable for
`register`**. The register rider is itself a
[`DjangoMutation`][glossary-djangomutation], and `bind_mutations()` resolves its
payload's primary type through `_resolve_primary_type` — whose no-registered-type
raise is a **generic** message naming the internal `Register` class (which the
consumer never wrote) and the raw concrete user-model class, with no
`get_user_model()` / [`Meta.primary`][glossary-metaprimary] recourse
([`mutations/sets.py`][mutations-sets] `::_resolve_primary_type` #"the mutation has no type to return").
Were the auth bind ordered after it, the generic error would always pre-empt the
auth-specific one for `register` and the register arm of this Decision would be
dead. So
[Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)
orders `bind_auth_mutations()` **before** `bind_mutations()`: the auth ledger
knows every declared surface (`register_mutation()` re-records there on **every**
call, identity-deduped —
[Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)
— so the coverage re-appears after a `registry.clear()` + re-declare and does not
regress to the generic message on a second finalize), the
primary-type lookup needs only registration-time state, and all three user-typed
surfaces fail with the same actionable auth message. Tests pin the **exact** error
a no-`UserType` schema produces for `register` specifically, distinct from
`login`'s — **on both the first finalize and a post-reload second finalize.**

**The user type's field selection IS the authenticated read surface**. The register
input side is guarded on the way in (account-control columns kept off the generated
input by Decision 6's two layers) — but the *output* side is whatever
the consumer's `UserType` selects: a `fields = "__all__"` over the user model
surfaces the password **hash**, `is_superuser` / `is_staff`, and `last_login`
through `LoginPayload.node`, `RegisterPayload.node`, and `me`. Select explicitly
and exclude `password` and privilege columns (the spec's example uses
`("id", "username", "email")`); the Slice 3 GLOSSARY entry carries the same
caution. This is doc-only guidance — the package does not police the consumer's
selection (a deliberately privileged `UserType` behind a staff-only schema is
legitimate), it makes the trade visible. One further asymmetry belongs in the same
caution: because `me` and `login.node`
deliberately skip [`get_queryset`][glossary-get_queryset-visibility-hook]
([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)
/ [Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)),
a `UserType.get_queryset` written to **row-redact** (mask rows, drop the actor under a
directory rule) gives **no** protection on those two surfaces — only the field
selection governs what a logged-in actor sees of *themselves* there. This is sound
(viewing your own row is not a directory lookup — Decision 7's actor-not-lookup
reasoning), but it is a deliberate carve-out from [`GOAL.md`][goal] success-criterion 4
("the same hook covers reads and writes"), called out so a consumer relying on
`get_queryset` for row-level redaction knows it does not reach `me` / `login.node`
(the register payload's re-fetch is likewise by-pk-without-visibility, but that is the
`036` own-write exception, not a general read-gate bypass).

Rationale companion — this Decision's justification and its four rejected
alternatives: [Decision 8][rationale-d8].

### Decision 9 — Bind lifecycle: a declaration ledger + `bind_auth_mutations()` at phase 2.5 + registered clear rows

The factories run at consumer class-body time — **before**
[`finalize_django_types`][glossary-finalize_django_types], when the user's primary
type may not even be registered yet
([Definition-order independence][glossary-definition-order-independence]). So the
factories cannot resolve types eagerly; they follow the exact
[`DjangoMutationField`][glossary-djangomutationfield] discipline:

- Each factory call records a declaration in a module-level auth ledger — **a
  [`make_declaration_registry`][mutations-sets]`("AuthMutation")` instance, not a
  hand-rolled list** (the helper-reuse review's D14 reuse directive), so the
  every-call identity-deduped `.register` and the `TypeRegistry.clear()` drain are the
  same ones the model / form / serializer flavors use — (**surface-keyed**: which of
  `login` / `logout` / `register` / `current_user` was declared, with which
  `permission_classes`) and returns a field whose
  dispatcher resolver carries an **injected `__signature__` / `__annotations__`** — the
  same mechanism [`DjangoMutationField`][glossary-djangomutationfield] uses
  ([`mutations/fields.py`][mutations-fields] `_resolve.__signature__` /
  `_resolve.__annotations__`) — with the return annotation a `strawberry.lazy`
  forward-ref into the package namespaces: `"LoginPayload"` / `"LogoutPayload"` in the
  `mutations.inputs` module path (where `build_payload_type` materializes), and the
  `current_user` `"CurrentUserAlias"` in `auth.queries` (set to the resolved primary
  type at bind — [Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)).
  Injecting the signature (rather than a static annotation) is required precisely
  because the user primary type is unresolved at class-body time.
**The exact phase-2.5 order**: the finalizer's pre-bind
reset loop runs first, then `bind_auth_mutations()`, then `bind_mutations()`, then
`bind_form_mutations()`:

1. **The pre-bind reset loop** (`iter_subsystem_clears(before_bind=True)` in
   [`types/finalizer.py`][types-finalizer], immediately before `bind_mutations()`)
   drains the `before_bind=True` [`register_subsystem_clear`][registry] rows — which
   are, by that flag's own contract, the **emit / input-namespace ledgers and
   per-pass caches only, never the declaration registries**
   ([`types/finalizer.py::finalize_django_types`][types-finalizer] #"phase filter selects emitted namespaces and per-pass caches").
   This is why the auth **declaration** ledger must NOT carry `before_bind=True`
   (below) — draining it here would erase the consumer's class-body-time
   declarations before the auth bind on the very next line could read them.
2. **`bind_auth_mutations()`** runs next — **before** `bind_mutations()`. The
   finalizer reaches it through the **already-loaded-only** lookup
   ([`utils/imports.py::loaded_attr`][utils-imports]), never a plain function-local
   import: a plain import would load `auth/mutations.py` — and through it
   `django.contrib.auth` — in every process that finalizes, silently converting
   [Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export)'s
   structural opt-in into an unconditional import. A declared auth surface implies
   the module is already in `sys.modules`, so the lookup can only skip a genuinely
   auth-free process, where the bind would have been a no-op anyway. Its
   [Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)
   user-type validation must fire with the auth-specific message before the register
   rider's own bind could raise `_resolve_primary_type`'s generic no-DjangoType
   error. Nothing in the auth bind depends on `bind_mutations()` having run — the
   primary-type lookup and the payload materialization consume only
   registration-time state. **The bind is surface-keyed**: it reads which of the
   four surfaces the ledger carries and
   performs only the work those surfaces need — the user primary type is resolved
   at most once, and only when a user-typed surface (`login` / `register` /
   `current_user`) was declared:

   - `login` → resolve the user primary + validate
     ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind),
     the login-arm message), materialize `LoginPayload` (object slot per
     `payload_object_slot(primary)`);
   - `logout` → materialize `LogoutPayload` (`object_type=None`) **only** — the
     user primary is neither resolved nor required (Decision 8's logout exemption,
     made structural);
   - `register` → resolve the user primary + validate (the register-arm message,
     pre-empting `_resolve_primary_type`'s generic raise), then leave
     `RegisterInput` / `RegisterPayload` to `bind_mutations()` (the rider is an
     ordinary [`DjangoMutation`][glossary-djangomutation]) — the auth bind
     materializes **no** login / logout payload for it;
   - `current_user` → resolve the user primary + validate (the current_user-arm
     message), materialize the `CurrentUserAlias` return alias — no login / logout
     payloads.

   Both payload materializations ride the ONE `build_payload_type` builder + the
   existing `mutations.inputs` emit ledger, all before `strawberry.Schema(...)`
   resolves the lazy refs. A partial schema therefore emits **no orphan
   payloads**: a register-only schema materializes no `LoginPayload` (so it cannot
   collide with a consumer's own distinct-shape `LoginPayload`), and a logout-only
   schema binds with no user type registered at all
   ([Edge cases](#edge-cases-and-constraints) / [Test plan](#test-plan)).
3. **`bind_mutations()`** then binds the register rider as an ordinary
   [`DjangoMutation`][glossary-djangomutation] (its `RegisterInput` /
   `RegisterPayload` materialize there), followed by **`bind_form_mutations()`** —
   both unchanged.

**Two distinct clear paths, split the way the mutation / form flavors already split
them**:

- The auth **declaration** ledger (the `login` / `logout` / `register` /
  `current_user` records) is cleared by `TypeRegistry.clear()` **only** — a
  full-clear-only [`register_subsystem_clear`][registry] row (owner
  `auth.declarations`, no `before_bind`) beside the existing
  `clear_mutation_registry` / `clear_form_mutation_registry` declaration-clear rows
  ([`auth/mutations.py`][auth-mutations] #"register_subsystem_clear(clear_auth_mutation_registry"),
  **never** `before_bind=True`. Declarations must survive the
  pre-bind reset so a recover-in-place re-finalize (and the register rider's
  every-call re-register) still sees them. **The ledger is also the holders' /
  rider's same-args cache and conflict state** — the cached permission holders and
  the cached `Register` rider are
  looked up through the declaration records, never a separate module dict a
  `registry.clear()` would miss — so draining the ledger drains the cache: after a
  clear, a re-declaration with a *different* `permission_classes` mints a fresh
  holder / rider rather than tripping a stale conflicting-declaration raise
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)
  / [Edge cases](#edge-cases-and-constraints)).
- The **emit** artifacts follow the pre-bind phase: `LoginPayload` / `LogoutPayload`
  ride the **existing** `mutations.inputs` `before_bind=True` row (no new
  row — importing `auth/mutations.py` transitively imports `mutations/inputs.py`,
  whose row self-registers at import per the [`spec-039`][spec-039]
  owning-module invariant). The **only** net-new `before_bind=True` row is
  the `current_user` generated-alias namespace in `auth/queries.py` — a genuine
  emit ledger whose `clear_fn` is the one the
  [`make_input_namespace`][utils-inputs] trio returns (Decision 7's D13 reuse of the
  parked-global lifecycle), self-registered when `auth/__init__.py` imports `queries`.
- A factory call **after** finalization raises
  [`ConfigurationError`][glossary-configurationerror] (the standing
  declare-after-finalize rule).

Rationale companion — this Decision's justification and its four rejected
alternatives: [Decision 9][rationale-d9].

### Decision 10 — Sync + async: session work through one `sync_to_async(thread_sensitive=True)` boundary

Every auth field ships the sync/async resolver pair, dispatched by the same
construction-time/runtime detection the field family uses. The async paths wrap the
session work — `authenticate` / `auth.login` / `auth.logout` are session- and
DB-touching sync APIs — in a single `sync_to_async(thread_sensitive=True)` call per
resolution, the exact boundary discipline the `036` async pipeline pinned (one
boundary, not per-step hops). `current_user`'s async path forces the lazy
`request.user` inside the boundary (upstream's "access an attribute to force
loading in async contexts" note — the `SynchronousOnlyOperation` guard).
**The permission gate runs inside the same boundary on the async path**, not before
it: `authorize_or_raise` → `check_permission` is synchronous,
a consumer `has_permission` may touch `request.user` (a `SimpleLazyObject` whose
attribute access triggers a sync ORM query), and — decisively for `current_user` —
the gate's own `instance=request.user` argument forces that lazy object as it is
*computed*, so evaluating the gate outside the boundary would raise
`SynchronousOnlyOperation`. The async dispatcher therefore wraps the whole
gate-then-session-work block in one sync helper run via
`await sync_to_async(helper, thread_sensitive=True)()`. **No auth module ever spells
`sync_to_async` itself** (the helper-reuse review's D17 reuse directive): every auth
async body reaches the boundary through the ONE generic
`run_in_one_sync_boundary(fn, *args, **kwargs)` primitive
([`utils/querysets.py`][utils-querysets] — the neutral utils home, beside its sibling
`reject_async_in_sync_context`, so read-side modules can reuse it without a
root-into-subpackage import; it stays importable from
[`mutations/resolvers.py`][mutations-resolvers] for historical importers). The `036`
wrapper is mutation-shaped (it takes `mutation_cls` / `data` / `id`), so its
`await sync_to_async(fn, thread_sensitive=True)(...)` core is factored out and
`run_pipeline_async` rides the primitive as its boundary core, leaving the pinned
`036` AR-M4 wording undisturbed. Each fixed auth field carries a real sync resolver
body and a real *async* resolver body as separate seams — so a native async path can
be specialized per field without touching the dispatch seam — and the invariant the
D17 directive pins is the **count, not the call site**: whichever body runs, one
resolution enters the thread-sensitive boundary exactly once, and the register
rider's `resolve_async` rides the same primitive. The
[`SyncMisuseError`][glossary-syncmisuseerror] discipline is unaffected: a
`sync_to_async(thread_sensitive=True)` worker is itself a sync context, so
`reject_async_in_sync_context` still rejects an `async def` `has_permission` (never a
silent allow) exactly as on the sync path — and `auth/` never defines or re-defines
[`SyncMisuseError`][glossary-syncmisuseerror]: the guards that raise it are reused by
call, so the surface neither imports nor re-spells it (the D19 prohibition; it holds
vacuously today and constrains what the surface may do, rather than asserting an import
that exists). Any place auth must detect whether a
consumer callable is itself `async def` (as distinct from catching a coroutine *result*,
which `reject_async_in_sync_context` owns) uses the partial-aware
[`is_async_callable`][utils-typing] predicate, never a bare `inspect.iscoroutinefunction`
(the D18 prohibition, likewise vacuous today).

Rationale companion — this Decision's rejected alternative:
[Decision 10][rationale-d10].

### Decision 11 — Transport contract: classify first, refuse a transport that cannot honour the surface truthfully

The auth surface requires Django's session stack: `django.contrib.sessions` and
`SessionMiddleware` on the GraphQL request path, `django.contrib.auth` in
`INSTALLED_APPS`, and the actor loader for the transport in use —
`AuthenticationMiddleware` on a Django request, `AuthMiddlewareStack` on a Channels
scope. CSRF stays the transport's concern exactly as for every other mutation
(the fakeshop example and the Django test client already handle it); nothing
auth-specific changes it.

**Every `login` / `logout` resolution opens with the same transport prologue**
([`auth/mutations.py::_transport_prologue`][auth-mutations]), whose three steps run
in a fixed order — classify, capability, session — **before the permission gate and
before any credential or session work**:

1. **Classify.** [`auth/sessions.py::classify_transport`][auth-sessions] resolves the
   request to exactly one of three explicit modes: `DJANGO_HTTP`, `CHANNELS_HTTP`,
   `CHANNELS_WEBSOCKET`. It opens with an `isinstance` check against the
   [Channels request adapter][glossary-channels-request-adapter] — attribute-presence
   sniffing is unreliable under that adapter's `__getattr__` delegation — and only a
   recognized adapter reads `scope["type"]` to split HTTP from WebSocket; a Django
   `HttpRequest` takes the native path. Every other object, and every missing or
   unrecognized scope type, is an actionable
   [`ConfigurationError`][glossary-configurationerror] naming the two supported mounts.
   **The transport is never detected by catching `AttributeError` from Django's auth
   functions.** Importing the module stays `channels`-free: the soft dependency is
   forced through the shared install-hint family ([`utils/imports.py`][utils-imports])
   only *after* a Channels scope has been recognized, so a Channels-shaped context that
   arrives without it raises a loud, actionable `ImportError` instead of failing later
   as an `AttributeError`.
2. **Capability.** The per-surface predicate — `auth/sessions.py::login_supported` /
   `::logout_supported` — answers whether this transport can honour *this* field
   truthfully. Where it cannot, the refusal is raised here — before authentication and
   before any session mutation — carrying that surface's own pinned message
   (`auth/mutations.py::_WEBSOCKET_LOGIN_UNSUPPORTED` /
   `::_WEBSOCKET_LOGOUT_UNSUPPORTED` — the table and its reasons below).
3. **Session.** [`auth/sessions.py::require_session`][auth-sessions] collapses the two
   missing-middleware shapes — a Django request carrying no `session` attribute, and an
   adapter whose scope exposes `session` as `None` — into one actionable error naming
   the transport, rather than a downstream `AttributeError` off a `None` session. Its
   message contract is in [Edge cases](#edge-cases-and-constraints).

`register` and `current_user` run **no prologue at all** and are transport-neutral by
construction: `register` writes a row and never a session, and `current_user` is
read-only — [`request_from_info`][utils-permissions] resolves either request shape and
the ONE shared anonymity definition answers, so `me` works over a Channels scope with
no branch of its own
([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)).

**Per-surface support.** One table, and the only place this is stated:

| Transport | `login` | `logout` | `register` / `current_user` |
| --- | --- | --- | --- |
| Django `HttpRequest`, sync or async | supported | supported | supported |
| Channels HTTP scope | supported | supported | supported |
| Channels WebSocket, server-side session engine | refused before authentication | supported | supported |
| Channels WebSocket, signed-cookie session engine | refused before authentication | refused before any session mutation | supported |
| No session middleware on the path | refused | refused | supported — the actor is simply anonymous |

**Each refusal is a refusal, not a gap.** The surface declines where it cannot tell the
truth, and the reason is what makes the rejection the correct behavior rather than
missing work:

- **`login` over any WebSocket, whatever the session engine.** Login rotates the
  session key, and an established socket cannot return the replacement cookie — so a
  "success" would establish a server-side session the browser could never claim. The
  refusal fires in the prologue, before `authenticate` is called.
- **`logout` over a signed-cookie-engine WebSocket.** A server-side engine invalidates
  by deleting the record, which needs no new cookie, so WebSocket logout is honest
  there and is supported. The signed-cookie engine keeps **no server-side record to
  revoke**, and an established socket can neither delete nor replace the browser
  cookie — so a "success" would claim a durable invalidation that did not happen. The
  capability answer (`auth/sessions.py::uses_signed_cookie_sessions`) is a settings
  read, never adapter metadata: it resolves the configured engine's `SessionStore`
  through [`utils/sessions.py::session_store_class`][utils-sessions] — single-sited *outside*
  `auth/` so the WebSocket revalidation can share the `SESSION_ENGINE` expression
  without importing the opt-in subsystem
  ([Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export)) —
  and refuses only when that store **subclasses** Django's signed-cookie store, so a
  subclassed deployment is recognized while a custom client-side engine that does not
  subclass it is treated as server-side and must not be used with WebSocket logout.

Both refusals are top-level GraphQL execution errors
([`ConfigurationError`][glossary-configurationerror]) and are deliberately **outside**
the byte-compatible failed-login envelope, so their wording is free; and because both
fire before any credential check, neither is an enumeration oracle.

**Per-transport establishment and teardown.** Django's own `login` / `logout` on
`DJANGO_HTTP`; `channels.auth`'s `login` / `logout` against the scope on either
Channels mode, awaited natively. The asymmetry between them is a persistence contract,
not a style choice: Django HTTP adds an explicit `request.session.save()` so a store
failure is an execution error **before** the success payload, leaving `modified` set so
`SessionMiddleware` still emits the rotated cookie; Channels' `login` does not persist
the keys it writes, so an explicit `await session.asave()` is the durability step there;
and Channels' `logout` flushes durably on its own, so no save is added to it. Every
post-authentication failure is fail-closed on both paths — the actor is made anonymous,
partially established durable state is flushed, and the original error is re-raised with
any cleanup failure chained through `__context__` — never a success payload, and never a
clean-state claim the teardown did not reach.

**One lock, and it is scope-owned.** Same-scope Channels session mutation, persistence
and compensation are serialized under a single per-scope `asyncio.Lock` stored on the
ASGI scope ([`auth/sessions.py::scope_session_lock`][auth-sessions]) — never a
process-global registry and never a `ContextVar`. Independent requests, connections and
processes are not globally serialized; they follow the configured session backend's own
contract.

**Sync and async.** Under sync execution a classified Channels HTTP scope takes a single
`async_to_sync` bridge at the private transport boundary — the one permitted sync→async
hop, and what makes a directly-invoked synchronous Channels HTTP consumer work. Under
async execution a Django `HttpRequest` rides the existing thread-sensitive boundary and
a Channels scope is awaited natively, with no nested `async_to_sync`. Classification
itself is pure (no ORM), so it never trips `SynchronousOnlyOperation`. The
boundary-**count** invariant is
[Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary)'s
and is unchanged on either path.

**Where this surface meets the WebSocket transport.** [`spec-046`][spec-046] owns the
Channels transport and this spec does not restate it; what belongs here is its effect on
the auth surface. The package's router serves no GraphQL `http` scope at all — the
GraphQL HTTP endpoint is the package's own Django view in the consumer's URLconf
([`spec-046` Decision 2][spec-046-d2]) — so a `CHANNELS_HTTP` scope reaches this
boundary only from an HTTP consumer the project mounted itself. On a WebSocket the
supported teardown additionally runs inside the connection's actor lease
([`spec-046` Decision 16][spec-046-d16]), which makes it mutually exclusive with that
card's outbound-frame revalidation in both directions and fixes the lock order — the
scope session lock OUTER, the actor lease INNER, with
`auth/mutations.py::_channels_logout` the only site holding both. The consumer-visible
consequence: a same-connection `logout` is a **connection-scoped revocation event**, so
the socket closes at its next protected checkpoint and the `logout` payload itself does
not reach the client.

Upstream's **fallback shape** is still not borrowed. `strawberry_django` attempts a
`channels_auth` path after the Django path fails and sniffs the consumer scope for a
user ([`mutations.py`][upstream-auth-mutations] / [`utils.py`][upstream-auth-utils]);
this package classifies the transport explicitly up front instead, so no path is ever
entered speculatively and no transport is diagnosed from the failure it caused. The
Channels **capability** — `channels.auth`'s `login` / `logout` — is used, on a scope
already classified as Channels.

Rationale companion — this Decision's two rejected alternatives and the record of how
its contract widened: [Decision 11][rationale-d11].

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
cards. Per [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told", the `CHANGELOG.md` edit must be explicitly named in the Slice 3
maintainer prompt — this spec describes it but cannot authorize it. `0.0.13` is a
routine patch cut, not a milestone (`X.Y.0`) rollover, so no `alpha constraint`
lifts or milestone-prose flips apply. The bump moves only in Slice 3 — after the
auth surface, tests, and docs are complete — never in Slice 1.

Rationale companion — this Decision's three rejected alternatives:
[Decision 12][rationale-d12].

## Implementation plan

Three slices. Slices 1 and 2 each land package code **and its live fakeshop
surface in one commit** (the live-first mandate); Slice 3 is docs + the version cut.
Line deltas are planning estimates.

| Slice | Files touched | New / changed tests | Approx. delta |
| --- | --- | --- | --- |
| 1 — auth substrate + `login` / `logout`, earned live | `auth/__init__.py` (new; the four re-exports — `register_mutation` / `current_user` land in Slice 2), `auth/mutations.py` (new; `login_mutation` / `logout_mutation` factories, the login / logout permission-holder classes reusing `check_permission` / `authorize_or_raise` by call, declaration ledger, `bind_auth_mutations()`, sync/async session resolvers, the AllowAny default through `_validate_permission_classes`, the ledger's own full-clear-only [`register_subsystem_clear`][registry] row beside `clear_mutation_registry` / `clear_form_mutation_registry` — no `before_bind`; `LoginPayload` / `LogoutPayload` ride the existing `mutations.inputs` pre-bind row, so no new pre-bind row lands here), [`types/finalizer.py`][types-finalizer] (the `bind_auth_mutations()` call in the pinned phase-2.5 slot — after the pre-bind reset loop, before `bind_mutations()`), `examples/fakeshop/apps/accounts/` (new; schema-only app: `UserType` over `auth.User`, `Query.me`-less for now, `Mutation.login` / `logout`), [`config/schema.py`][config-schema] + [`config/settings.py`][config-settings] (compose + install the app), [`schema_reload.py`][schema-reload] (the `"apps.accounts.schema"` `_PROJECT_APP_SCHEMA_MODULES` row — same commit as the compose) | **Primary: `test_query/test_auth_api.py`** (new; ~7 live — login happy path + session cookie, wrong-password `"__all__"` envelope, inactive-user envelope, logout round trip, anonymous logout `ok: false`, the complete-reload fixture preserving the auth surface — the canonical AllowAny default surface only; the gate variants are package tests). **Internals: `tests/auth/test_mutations.py`** (~14 — ledger record/dedupe, declarations-survive-pre-bind-reset, reload-idempotence incl. the post-clear conflict reset, conflicting-declaration raise keyed on `permission_classes` only (a `description`-only delta never raises), bind validation — the login-arm no-primary-type raise + the logout-only surface-keyed exemption, post-finalize factory raise, async paths, sessionless edge, async-permission `SyncMisuseError`, the permission-gate variants on isolated throwaway schemas — exact denial strings, gate-payload contract, mutation-introspection raise) | `+430 / 0` |
| 2 — `register` + `current_user`, earned live | `auth/mutations.py` (`register_mutation` + the cached `Register` rider synthesis — `__name__ = "Register"` (→ `RegisterPayload`), `Meta.fields` narrowing (`email` optional per `input_field_required`), the `resolve_sync` / `resolve_async` overrides riding `run_write_pipeline_sync` with the password-aware decode / write step pair (`decode_step` → `(user, m2m, exclude, raw_password)`; `write_step` → `validate_password(raw_password, user)` → `set_password` → `full_clean` → `save`), the every-call ledger re-register + conflicting-perms `ConfigurationError`, the `RegisterInput` input-name-seam override), `auth/queries.py` (new; `current_user` factory + resolver pair + its permission holder + the bind-materialized return alias + the alias-namespace `register_subsystem_clear` row), `examples/fakeshop/apps/accounts/schema.py` (grow `register` + `me`), | **Primary: `test_query/test_auth_api.py`** (+~5 live — register → login → `me` → logout round trip, hashed-password assertion, duplicate-username envelope, weak-password validator envelope, anonymous `me: null` — the AllowAny default surface only; the `me` / `register` gate variants are package tests). **Internals: `tests/auth/test_mutations.py` + `tests/auth/test_queries.py`** (+~14 — factory cache identity, the reload-idempotence cycle incl. the post-clear conflict reset, the register-arm / current-user-arm no-`UserType` errors (moved from Slice 1) + the register-only / current-user-only surface-keyed binds, `derive_register_fields` for the default and a custom-`USERNAME_FIELD` / custom-`REQUIRED_FIELDS` test-scoped model, the exclusion-seam provided-marker test, validator → envelope mapping shapes, model-decode-never-sees-`password` + plaintext-never-persisted on BOTH sync and async paths, `current_user` lazy-load forcing, alias materialization, the `me`-gate / `register`-gate variants on isolated throwaway schemas) | `+360 / 0` |
| 3 — docs + `0.0.13` version cut + card wrap | [`docs/GLOSSARY.md`][glossary] ([Auth mutations][glossary-auth-mutations] → `shipped (0.0.13)` full contract; [`SerializerMutation`][glossary-serializermutation] → `shipped (0.0.13)`; package-version line; Index rows; submodule-exports note), [`docs/README.md`][docs-readme] + [`README.md`][readme] ("Coming next" → "Shipped today" for both `0.0.13` features; Status → `0.0.13`), [`TODAY.md`][today] (serializer wording → shipped; auth noted under capabilities-not-exercised-by-products), [`GOAL.md`][goal] (fakeshop auth wording future → shipped), [`docs/TREE.md`][tree] (`auth/`, `tests/auth/`, `accounts`, `test_auth_api.py` rows — closes the target-layout gap), [`CHANGELOG.md`][changelog] (**explicit-permission caveat**), version quintet, [`KANBAN.md`][kanban] card wrap (DB + re-render) | `test_version` → `0.0.13` | `+150 / -60` |

Total expected delta: ~`+940 / -60` — an M cut, matching the card's relative size.
The small footprint is the dividend of riding the frozen foundation: no new
converter, no new input generator, no new pipeline orchestration (register supplies
only its password-aware decode / write step pair over the shared skeleton), both
payload shapes from the existing builder. Staged-but-not-implemented seams follow the
[`AGENTS.md`][agents] design-doc anchor discipline (a source-site
`TODO(spec-040 Slice N)` comment naming this spec, removed in the slice that ships
it).

## Helper-reuse obligations (DRY)

The auth surface is a thin layer over the frozen foundation, so its correctness leans on
**reusing** the write-stack / [`utils/`][utils-inputs] helpers rather than re-spelling
them. This checklist consolidates the helper-reuse review
(a deep pass over all ten [`utils/`][utils-inputs] modules against the planned surface);
each item is single-sited in the decision it cross-references, and the implementation is
verified against it slice by slice. The three `D-N*` items are deliberate **non**-reuse —
sharing the named helper there would be a *bug*, so they carry a source comment.

- [ ] **D1** — every auth resolver reads the request via
  `request_from_info(info, family_label=_AUTH_FAMILY_LABEL)` ([`utils/permissions.py`][utils-permissions]),
  one shared label constant, never a re-spelled `info.context.request` walk
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
- [ ] **D2** — the async-permission-hook guard (`reject_async_in_sync_context` +
  `_PERMISSION_ASYNC_RECOURSE`) is reused **by call** through the bound
  `check_permission`; no new recourse string
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design) / [Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary)).
- [ ] **D3 / P4** — the permission holder binds `DjangoMutation.check_permission`, builds
  `_mutation_meta` via `_validate_permission_classes(..., unset_default=())`, and is
  synthesized by ONE `_make_permission_holder(...)` helper, not three class bodies
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
- [ ] **D4** — all four surfaces gate through `authorize_or_raise`; the denial message
  rides the existing `_primary_type` / holder-`__name__` fallback, no auth-specific
  formatter ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
- [ ] **D5** — `LoginPayload` / `LogoutPayload` via `build_payload_type` +
  `payload_object_slot` on the existing `mutations.inputs` emit ledger; no new clear row;
  `RegisterPayload` never named explicitly
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design) / [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
- [ ] **D6** — register declares `password` as an `EXCLUDED` field kind at bind (the
  rider's `build_input` seam stashes the specs) and reuses the ONE shared
  UNSET-strip decode spine — [`iter_provided_input_fields`][utils-inputs] under
  `_model_decode_step` — to capture the value out of the constructed model attrs
  **with the provided-marker preserved** (the AR-H2 `_unprovided_exclude` calculation
  still counts `password` as provided), rather than forking a second decoder or
  threading a per-call exclusion parameter through the decode signature
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
- [ ] **D7** — register's `write_step` delegates `full_clean()` / `save()` /
  `IntegrityError` / M2M to the shared model write tail (`_model_write_step`, which
  is what calls `_full_clean_or_field_errors` /
  [`save_or_field_errors`][mutations-resolvers]); the auth-specific steps are exactly
  the password preflight (`unencodable_text_error`, itself the shared write-side
  primitive), `validate_password` and `set_password`
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
- [ ] **D8** — register's password error uses `field_error("password", …)` directly;
  `login`'s failure error uses `field_error("", …)` (empty path → `NON_FIELD_ERROR_KEY`);
  neither hard-codes `"__all__"`
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design) / [Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
- [ ] **D9** — register's re-fetch rides the inherited `refetch_optimized`; `login` /
  `current_user` do no queryset work
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor) / [Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)).
- [ ] **D10 / D11** — `RegisterInput` is named via the `input_type_name` / `build_input`
  seams and materialized via the inherited `materialize_mutation_input_class`; no new input
  namespace for register
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
- [ ] **D12 / P1 / P2** — the lazy return refs are built by [`_lazy_ref`][mutations-fields];
  the field-dispatcher construction is single-sited in ONE auth helper; `_lazy_ref` + the
  `__signature__` / `__annotations__` injection are promoted to shared machinery
  ([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset) / [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
- [ ] **D13** — the `CurrentUserAlias` namespace is owned by a
  [`make_input_namespace`][utils-inputs] trio (its `materialize_fn` pins the alias, its
  `clear_fn` is the `register_subsystem_clear` row); no hand-rolled `setattr` / `delattr`
  ([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset) / [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
- [ ] **D14** — the auth declaration ledger is a
  [`make_declaration_registry`][mutations-sets]`("AuthMutation")` instance; every-call
  re-record on both ledgers via `.register`
  ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
- [ ] **D15** — the current_user alias's `register_subsystem_clear` row carries
  `before_bind=True`; the auth declaration ledger's row carries no `before_bind`,
  beside the mutation / form declaration clears
  ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
- [ ] **D16** — `bind_auth_mutations()` resolves the primary via
  [`registry.get`][registry]`(get_user_model())`, the same getter
  `_resolve_primary_type` uses; `registry.types_for` is consulted only to split
  no-type vs ambiguous-type messages
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)).
- [ ] **D17 / P3** — **no auth module spells `sync_to_async` itself.** Every auth async
  path reaches the thread-sensitive worker through the generic
  [`run_in_one_sync_boundary`][utils-querysets] primitive (its home is
  [`utils/querysets.py`][utils-querysets], beside `reject_async_in_sync_context`, and
  it is shared with the `036` wrapper and the read-side async seams), never an
  auth-local copy. The invariant is the **count, not the call site**: one resolution
  enters that boundary exactly once, with the permission gate inside it. The primitive
  is called from each surface's own async body — there is no auth-local wrapper around
  it, and re-introducing one would be a second definition of the boundary discipline,
  not a reuse of it
  ([Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary)).
- [ ] **D18 / D19** (prohibitions) — the auth surface never spells a bare
  `inspect.iscoroutinefunction`: any async-callable detection it needs goes through the
  partial-aware [`is_async_callable`][utils-typing]. It never defines or re-defines
  [`SyncMisuseError`][glossary-syncmisuseerror]; the guards that raise it are reused by
  call, so `auth/` neither imports nor re-spells it. Both hold **vacuously today** —
  there is no such call site in `auth/` — and are stated as standing constraints on the
  surface rather than as claims that a call site exists
  ([Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary)).
- [ ] **D-N1** (non-reuse) — `current_user` / `login` must NOT scope through
  [`get_queryset`][glossary-get_queryset-visibility-hook] / the visibility helpers (they
  return the actor, not a lookup)
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design) / [Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)).
- [ ] **D-N2** (non-reuse) — register's password error must NOT route through
  `validation_error_to_field_errors` (it keys a list-style error to `"__all__"`)
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
- [ ] **D-N3** (non-reuse) — register wires **no** relation-visibility helper of its own.
  The stock user model's narrowed `Meta.fields` carries no relation input at all, and a
  custom model whose `REQUIRED_FIELDS` names a forward FK gets the standard `<field>_id`
  input through the shared decode's own relation handling — so the rider inherits
  whatever the shared path does and adds nothing, which is what keeps registration from
  acquiring a second, auth-local visibility rule
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).

## Edge cases and constraints

- **Wrong credentials / unknown user / inactive user / unstorable credential.** All
  **four** failure classes collapse into the ONE `"__all__"`-keyed envelope entry
  (Django's `authenticate` returns `None` for the first three under `ModelBackend`,
  `is_active=False` included; the fourth short-circuits to the same `None` at the
  storability preflight,
  [Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
  No enumeration oracle; the live suite pins the identical shape for wrong-password
  and unknown-username, and a package row asserts all four payloads are
  byte-identical.
- **Login while already authenticated.** Allowed; `auth.login`'s session handling
  is three-branch (Django's `django/contrib/auth/__init__.py::login`): an
  **anonymous→authenticated** login cycles the session key
  (`request.session.cycle_key()`, the fixation defense); a login as a **different**
  user — or the **same** user whose stored `SESSION_KEY_SALT` auth hash no longer
  matches (e.g. a password change elsewhere) — **flushes** the old session; a
  **same-user re-login with a matching auth hash** leaves the session key intact.
  `rotate_token(request)` always runs but rotates the **CSRF** token, not the
  session key. The payload carries the authenticated user in every branch.
- **Anonymous logout.** `ok: false`, empty errors; the transport's native teardown
  still runs, flushing any residual anonymous session data — idempotent by
  construction. Which teardown runs is
  [Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)'s;
  the observational `ok` and the empty `errors` are the same on every transport.
- **Duplicate username on register.** The model `full_clean()` unique check surfaces
  as a `USERNAME_FIELD`-keyed [`FieldError`][glossary-fielderror-envelope]; the
  concurrent-race `IntegrityError` fallback maps through the standing
  `save_or_field_errors` path — both the `036` contract, no auth-specific code.
- **Password validator failures.** Every failing validator contributes a message
  under the single `password` key (Django's `validate_password` aggregates into one
  **list-style** `ValidationError`). Because that error has no `error_dict`, the write
  step keys it to `password` **directly** (`field_error("password", exc.messages, …)`),
  **not** via the generic `validation_error_to_field_errors` mapper — whose non-dict
  branch would key it to the `"__all__"` sentinel
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
  The live weak-password test asserts multiple messages under the `password`
  key (not `"__all__"`) against fakeshop's four configured validators.
- **Custom user models.** `USERNAME_FIELD` / `REQUIRED_FIELDS` drive the register
  field set, so an email-login model registers with `email` + password; a
  `REQUIRED_FIELDS` entry that is a forward FK becomes the standard `<field>_id`
  input (the model-column converter's relation rule); `authenticate`'s `username`
  kwarg maps onto `USERNAME_FIELD` via `ModelBackend`. A custom auth **backend**
  whose `authenticate` signature does not accept `username=` / `password=` kwargs is
  out of scope ([Risks and open questions][rationale-risks]).
- **`REQUIRED_FIELDS` naming `password`-adjacent, privileged, or unusable columns.**
  The `derive_register_fields(user_model)` tuple deduplicates (`USERNAME_FIELD`
  appearing in `REQUIRED_FIELDS` is a consumer error Django itself rejects); a name in
  the module-level protected set (`is_active` / `is_staff` / `is_superuser` / `groups`
  / `user_permissions`) raises [`ConfigurationError`][glossary-configurationerror]
  naming the offending field(s) and the model, because auto-exposing one would turn an
  unusual model declaration into a public privilege or activation input; and unknown /
  non-editable names are rejected loudly by **delegating to the standard
  `editable_input_fields` validation**, never a re-implemented check — no silent drops
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
- **Payload-name collisions.** `LoginPayload` / `LogoutPayload` / `RegisterPayload` /
  `RegisterInput` materialize through the standard emit ledger, so a consumer's own
  mutation class named `Login` (emitting a distinct-shape `LoginPayload`) hits the
  established distinct-shape collision
  [`ConfigurationError`][glossary-configurationerror] at finalization — documented,
  with the consumer rename as the recourse. Conversely, the surface-keyed bind
  materializes only the **declared** surfaces' payloads
  ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)),
  so a register-only schema emits no `LoginPayload` at all — the collision can only
  fire when the `login` surface is actually declared, never from an orphan payload.
- **One auth surface of each kind per process** (the fixed-payload-name
  consequence). Because the payload names are fixed (`LoginPayload`,
  `RegisterPayload`, …), a second call to the *same* factory with a **different**
  `permission_classes` cannot mint a distinct permission-specialized class under the
  same payload name — it raises a [`ConfigurationError`][glossary-configurationerror]
  naming the conflict. A schema declares one `login` / `logout` / `register` / `me`
  each in practice, so this bites only a genuinely contradictory double-declaration
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
- **Factory called after finalization.** The standing declare-after-finalize
  [`ConfigurationError`][glossary-configurationerror]; tests pin it for both the
  ledger factories and the lazy `Register` synthesis.
- **Two calls to the same factory.** The conflict / cache key is the
  **schema-affecting declaration args only** — today exactly the normalized
  `permission_classes`. `description` / `deprecation_reason` / `directives` are
  per-field `strawberry.field` presentation kwargs, applied to each returned field
  and **excluded** from the key: `login_mutation(description="A")` after
  `login_mutation(description="B")` returns the cached class / holder with the new
  field metadata, never a raise. A same-key call is idempotent — the
  identity-deduped cached class / holder (two schemas, or a Query plus a re-export,
  get the same materialized payloads); a same-`permission_classes`
  `register_mutation()` re-registers the one cached `Register` rider (the reload
  re-register, below). A different-`permission_classes` call is the
  conflicting-declaration raise above — and that conflict state lives in the
  surface-keyed declaration ledger drained by its full-clear-only row,
  so it does **not** survive a `registry.clear()`: a post-clear re-declaration with
  different gates mints a fresh holder / rider
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)
  / [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
- **Password never on the model instance.** A unit assertion pins that the register
  `decode_step` removes `password` before `model(**scalar_and_fk_attrs)` — the raw
  value travels only as the fourth element of the
  `(user, m2m_assignments, exclude, raw_password)` decoded tuple to the `write_step`,
  never as a constructed model attribute
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
- **No registered user `DjangoType`.** Bind-time
  [`ConfigurationError`][glossary-configurationerror] naming the missing primary
  registration and the fix
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind));
  a logout-only schema is exempt.
- **Sessionless / middleware-less deployments.** `login` and `logout` pre-check for a
  session **before** any credential or session work and raise an actionable
  [`ConfigurationError`][glossary-configurationerror] naming `SessionMiddleware` (and,
  for a Channels scope, `AuthMiddlewareStack`), rather than letting the absence surface
  downstream as a raw `AttributeError` off a `None` session. The message keeps the
  substring `"session"`; it is a transport-capability configuration error, deliberately
  outside the byte-compatible failed-login envelope, so its wording is otherwise free.
  The pre-check is single-sited in the shared transport prologue and its per-transport
  behaviour is
  [Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)'s.
  `current_user` needs no such probe: a request with no `user` attribute is simply
  anonymous under the shared classification
  ([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)).
  The `tests/auth/` sessionless edge must pin **this** error — its exact class and its
  actionable text — not merely that some error mentioning `"session"` escaped, which is
  an assertion Django's own downstream failure would also satisfy.
- **Async contexts.** One resolution enters the
  `sync_to_async(thread_sensitive=True)` boundary **exactly once**, and the permission
  gate is always inside it — never before it, and never in a second hop. Whether the
  session work itself rides that same boundary or is awaited natively afterwards is the
  transport's business
  ([Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary)
  for the count invariant,
  [Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)
  for the per-transport split); the invariant this edge case pins is the count and the
  gate's placement, not the call site. `current_user` forces the lazy user inside the
  boundary — including computing the gate's `instance=request.user` argument (no
  `SynchronousOnlyOperation` leaks); an `async def` `has_permission` raises
  [`SyncMisuseError`][glossary-syncmisuseerror] even inside that sync worker — never a
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
- **Reload / re-finalize cycles.** `registry.clear()` drains the auth **declaration**
  ledger (its full-clear-only row, beside the mutation / form declaration
  clears — no `before_bind`,
  [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows))
  AND the mutation declaration ledger; the pre-bind reset separately drains the emit
  ledgers (`mutations.inputs` + the `current_user` alias). The consumer's
  re-declaration re-records the declarations — `login` / `logout` / `me` through
  their factories, `register` through the every-call re-register of the cached rider
  — and phase 2.5 rebuilds the emit artifacts, so a second finalize reconstructs the
  full auth surface (the suite's complete-reload fixtures exercise exactly this path).
  Because the holder / rider cache and the conflict state ARE the declaration ledger
  ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)),
  the clear also resets a prior conflicting-`permission_classes` raise — a
  post-clear re-declaration with different gates starts clean.
  A recover-in-place re-finalize after a fixable later-phase failure still sees the
  declarations because the pre-bind reset never touched them.

## Test plan

Placement per [`AGENTS.md`][agents] / [`docs/TREE.md`][tree] #"Coverage priority.":
every consumer-reachable behavior is earned in
`examples/fakeshop/test_query/test_auth_api.py` over live `/graphql/` (the primary
harness, landing in the same commits as the resolvers — Slices 1–2); `tests/auth/`
holds only what a realistic request cannot drive. **The package-test boundary is
explicit**: `tests/auth/` must not accrete live-reachable acceptance coverage.

**First-line seed-helper rule** ([`AGENTS.md`][agents] catalog/auth test contract).
Every `examples/fakeshop/test_query/test_auth_api.py` test opens with
`create_users(N)` from [`apps.products.services`][create-users] — **including** the
`register` and anonymous-`me` cases that create or expect no account through the
GraphQL surface (they still seed first, then exercise the fresh-account path). No
auth test hand-rolls a `User` outside the seed helper. This keeps the new auth suite
aligned with the standing test-placement contract without weakening live coverage.

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
  `password` (explicitly asserting the key is `password`, **not** the `"__all__"`
  sentinel the generic mapper would produce for `validate_password`'s list-style
  error) with the fakeshop validators' messages;
- the login / re-login session-handling branches of
  [Edge cases](#edge-cases-and-constraints) — anonymous→authenticated cycling the key
  while preserving anonymous session data and pinning the backend, a login as a
  different user flushing the old session and its data, a same-user re-login with a
  matching auth hash retaining the key, and one with a mismatched hash flushing and
  replacing it;
- the unstorable-credential rows for both `username` and `password` on `login` and for
  `password` on `register`, each proving the documented envelope rather than a raw
  `UnicodeEncodeError`; the password-similar-to-username rejection (the validator sees
  the constructed instance); the `register` decode-failure field-keyed envelope; and
  the dict-form validator error still keying to `password`;
- the CSRF row: `login` and `logout` face Django's real CSRF check over the live
  transport;
- anonymous `me: null`;
- **the live suite covers only the canonical default surface** — `login` /
  `logout` / `register` / `me` at the AllowAny default: the
  one-declaration-per-process rule
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)
  / [Edge cases](#edge-cases-and-constraints)) makes a second, permission-gated
  variant of the same fixed-payload field impossible in the single aggregated
  [`config/schema.py`][config-schema], so the gate variants are **genuinely
  unreachable from a real query** against the fakeshop schema — the documented
  [`AGENTS.md`][agents] placement exception for unreachable-live behavior, not a
  weakening of live-first. ALL permission-gate coverage (the exact denial strings,
  the gate-payload contract, the `IsAuthenticated`-style `me` gate, the
  mutation-introspection raise) lives in `tests/auth/` on isolated throwaway
  schemas (below);
- the complete-reload fixture path preserves the auth surface:
  [`reload_all_project_schemas`][schema-reload] (with `"apps.accounts.schema"` in
  `_PROJECT_APP_SCHEMA_MODULES`) rebuilds `login` / `logout` / `me` after a
  `registry.clear()` — pinning against the `LazyType` `KeyError` /
  silently-dropped-surface failure modes the helper's own docstring documents;
- SDL assertions: `LoginPayload` / `LogoutPayload` / `RegisterPayload` /
  `RegisterInput` shapes as pinned in
  [User-facing API](#user-facing-api) (`email: String` optional, below) — noting
  `node` is the fakeshop-specific slot name (the example `UserType` implements
  `relay.Node`; `payload_object_slot(primary)` yields `result` for a non-Relay
  primary), so no test encodes the Relay-only `node` name as the generic contract.

**Package-internal (`tests/auth/`, mirrored, internals only):**

- ledger mechanics: record / dedupe; the **declaration** ledger clears via its
  full-clear-only row (no `before_bind`) while the **emit** ledgers
  (`mutations.inputs` + the `current_user` alias) clear via the pre-bind reset — a
  test pins that declarations **survive** the pre-bind reset (the retry contract) and
  a re-finalize rebuilds the emit artifacts; the **reload-idempotence cycle** —
  finalize → `registry.clear()` → re-declare → finalize, asserting `register` (and
  `login` / `logout` / `me`) are present in the second schema (the every-call
  re-register rule) **and, for a no-`UserType` schema, that the second finalize still
  raises the register-arm auth-specific error — not merely that `register` is present
  when the type exists** (the auth-ledger every-call re-record is what keeps that arm
  alive across a reload) — **and that a prior conflicting-`permission_classes`
  raise does not survive the clear**: after `registry.clear()`, a re-declaration
  with a *different* `permission_classes` succeeds with a fresh holder / rider,
  because the cache / conflict state IS the ledger; the
  **conflicting-declaration raise** — a second
  `register_mutation(permission_classes=[Other])` (or `login_mutation`) with a
  different permission set raises `ConfigurationError`, **keyed on
  `permission_classes` only** — a repeat call differing solely in `description` /
  `deprecation_reason` / `directives` returns the cached class / holder, never
  raises ([Edge cases](#edge-cases-and-constraints));
- bind validation (surface-keyed, [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)):
  the no-primary-user-type
  [`ConfigurationError`][glossary-configurationerror] (message names the fix),
  **fired from `bind_auth_mutations()` ahead of `bind_mutations()`** — a
  **logout-only** schema with no `UserType` **binds successfully**, materializing
  only `LogoutPayload` and never resolving the user primary, while login-only /
  register-only / current-user-only schemas with no `UserType` each raise their
  auth-specific arm (the login arm lands in Slice 1; the register / `current_user`
  arms in Slice 2 when those factories exist, **with the register-arm error pinned
  exactly and distinct from login's** — never the generic `_resolve_primary_type`
  message); post-finalize factory raise;
- permission-gate coverage (moved off the live plan — the gated variants cannot
  coexist with the aggregate default surface in one process): each on an isolated
  throwaway schema with an explicit `registry.clear()` between the default and
  gated declarations — a gated auth field denying with the top-level `GraphQLError`
  and the **exact** pinned denial strings
  (`"Not authorized to login <UserType>."`; `"Not authorized to logout Session."` —
  the pinned holder `__name__`,
  [Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design));
  an `IsAuthenticated`-style gate on `me` denying an anonymous caller with the
  `GraphQLError` (distinct from the AllowAny default's anonymous `null`); a custom
  `login` gate keyed on `data["username"]` seeing the **attempted username** in
  `data` (and asserting the password is **not** in `data`); a gate reading only
  `info` / `operation` authorizing correctly while a gate that introspects the
  `mutation` argument (`mutation.Meta.model`) raises at request time on the
  model-less fields;
- the register rider: factory cache identity; `derive_register_fields(user_model)`
  called **directly** for the default AND a custom-`USERNAME_FIELD` /
  custom-`REQUIRED_FIELDS` model (a test-scoped model passed as the argument — no
  second Django project, no `AUTH_USER_MODEL` swap; fakeshop pins the default
  `auth.User`), including the unknown / non-editable rejection delegating to
  `editable_input_fields`; the exclusion-seam helper test — `password`'s value
  captured out of the constructed attrs **while its provided-marker is preserved**
  (the AR-H2 `_unprovided_exclude` still counts `password` as provided);
  `validate_password(password, user)` receives the constructed instance; the
  plaintext-never-persisted assertion at the write-step seam **on both the sync
  and the async resolver paths** (separate overrides, independently regressable);
  hash-before-`full_clean` ordering;
- sync/async: both resolver paths; the one-boundary discipline; the async
  `has_permission` → [`SyncMisuseError`][glossary-syncmisuseerror] (rejected even
  inside the sync worker); the `current_user` lazy-user forcing — **including an async
  `me` under a permission gate whose `instance=request.user` argument forces the lazy
  object inside the boundary, asserting no `SynchronousOnlyOperation` leaks**; the
  injected-signature return typing (the dispatcher's
  `__annotations__` return ref resolves to the concrete `UserType` — SDL `me: UserType`);
- **the transport contract**
  ([Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)),
  in `tests/auth/test_sessions.py` for the classification / capability layer and in
  `tests/auth/test_mutations.py` for the resolvers driving it: each of the three
  classified modes resolved from its own request shape and every unrecognized object /
  scope type rejected; the `channels`-free import of the `auth` submodule, and the
  install-hint `ImportError` when a Channels scope arrives without the soft dependency;
  the capability answers per engine, including that a **subclassed** signed-cookie
  engine is still recognized as signed-cookie; the per-scope lock created lazily,
  reused per scope, independent across scopes, released on cancellation, and stored
  nowhere process-global; and, at the resolver level, that the WebSocket `login` and
  signed-cookie WebSocket `logout` refusals fire **before** `authenticate` / any
  session mutation respectively, plus the Channels HTTP round trips for both fields on
  the sync bridge and the native async path, their compensation on a failing signal or
  store, and a server-side-engine WebSocket `logout` that invalidates durably and
  survives a reconnect. These are `tests/auth/` work rather than live: fakeshop is
  WSGI-only and mounts no `asgi.py`, so no Channels scope is reachable from a real
  query against it;
- the sessionless-request edge: the session pre-check's own
  [`ConfigurationError`][glossary-configurationerror] — asserted by **class and by the
  actionable middleware text**, not merely by the substring `"session"` appearing
  somewhere in the message, which the un-guarded downstream failure would satisfy too
  ([Edge cases](#edge-cases-and-constraints));
- **the finalizer's opt-in-preserving reach.** A subprocess that sets Django up,
  declares a non-auth [`DjangoType`][glossary-djangotype], **finalizes** (or builds a
  schema), and then asserts `"django_strawberry_framework.auth.mutations" not in
  sys.modules`. The existing clear-path row exercises only `registry.clear()`, so
  replacing the phase-2.5 `loaded_attr` lookup with a plain function-local import keeps
  every auth row green while
  [Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export)'s
  structural opt-in is silently void. The finalize call is what makes the row
  distinguishing; without it the assertion passes either way
  ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows));
- **the privilege rejection at the consumer's declaration site.** `derive_register_fields`
  is called directly for the protected-field raise, which pins the helper only; a second
  row must drive `register_mutation()` itself against a user model whose
  `REQUIRED_FIELDS` names a protected column, so the raise is proved to reach the
  consumer at declaration time rather than only from the helper
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor));
- **deep selections under `me { … }` and `login { node { … } }` are
  [Strictness mode][glossary-strictness-mode]-visible.** Both actors are raw,
  non-optimizer-planned instances
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)
  / [Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)),
  so a relation selected beneath either resolves per-field and strictness must see it.
  This belongs in `tests/auth/` rather than live: strictness is a
  `DjangoOptimizerExtension(strictness=...)` construction choice and the aggregated
  [`config/schema.py`][config-schema] takes the `"off"` default, while the fakeshop
  `UserType` deliberately selects no relation at all — so the behavior is genuinely
  unreachable from a real query without weakening the example's authenticated read
  surface. The row builds a throwaway schema with strictness on and a
  relation-carrying user type, selects the relation under `me` (and under
  `login { node { … } }`), and asserts the strictness diagnostic fires.

**Cross-cutting:** the full suite green at `fail_under = 100`; `ruff format` +
`ruff check` clean; the `036` / `038` / `039` surfaces and the read side unchanged
(the register rider must not perturb the model flavor's seam defaults —
`tests/mutations/` stays green untouched).

## Doc updates

Each slice owns its doc edits. [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" requires the `CHANGELOG.md` edit to be explicitly
named in the Slice 3 maintainer prompt — this spec describes the edit but cannot
itself grant the permission.

- **Slice 1–2 (inline with code):** docstrings only — including the `accounts` app's
  own module docstrings, which carry the breadcrumbs (what the app is for, that it is
  schema-only, that live behavior is earned in
  `examples/fakeshop/test_query/test_auth_api.py`, and why `UserType`'s field selection
  is the authenticated read surface). No app-level README: no fakeshop app has one, so
  the breadcrumbs belong in the docstrings that `docs/TREE.md` is rendered from. No
  repo-level doc flips yet (the surface is unreleased mid-card).
- **Slice 3 — the release cut** (see
  [Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)):
  - [`docs/GLOSSARY.md`][glossary]: [Auth mutations][glossary-auth-mutations] →
    `shipped (0.0.13)` with the implemented contract (the four factories, the
    submodule-only import, the AllowAny inversion + rationale, the envelope
    semantics, the session-transport constraint
    ([Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)),
    and the **`UserType`-selection caution** — the user type's field selection is the authenticated read
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

Every question this card opened is answered by a Decision above. The deliberation
that answered them — each question's preferred answer for the `0.0.13` cut, its
fallback if implementation proved the preferred answer wrong, and the two
card-citation tensions the cut chose to record rather than silently reconcile — is
recorded in the rationale companion under
[Risks and open questions][rationale-risks].

## Out of scope (explicitly tracked elsewhere)

- **The Channels ASGI router itself** —
  [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]
  (`DONE-041-0.0.14`), a separate card this one does not ship. Which transports the
  four auth fields accept, and how an unsupported one is rejected, is stated once in
  [Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)
  and nowhere else, this list included.
- **The ergonomic `TestClient` / `GraphQLTestCase` helpers** —
  [`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase]
  (`DONE-043-0.0.14`, shipped after this card); the live auth tests use the raw Django
  test client's session support.
- **Token / JWT authentication and password-change / password-reset mutations** —
  no upstream analog in either reference package; [`BACKLOG.md`][backlog] material
  if ever ([Decision 2](#decision-2--card-scope-boundary-session-auth-ships-token-auth-stays-out-no-new-meta--settings-key)).
- **A package-provided `UserType` default** — the consumer declares their own;
  a documented helper is a possible follow-on
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)).
- **A register customization surface** (subclassable base / extra-fields seam) —
  recorded follow-on ([Risks and open questions][rationale-risks]).
- **Field-level read gates** ([`FieldSet`][glossary-fieldset] /
  [Per-field permission hooks][glossary-per-field-permission-hooks]) — `0.1.1`;
  they will compose on top of the auth surface's returned user objects — for
  `register`'s G2-planned re-fetched node as for any other type. `login.node` / `me`
  (the raw, non-optimizer-planned actor instances,
  [Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)
  / [Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset))
  will be **re-examined** when field gates land, since whether a per-field
  `check_<field>_permission` fires identically on a raw unplanned instance versus a
  planned node is not yet proven.
- **A new `DjangoType` `Meta` key or settings key** —
  ([Decision 2](#decision-2--card-scope-boundary-session-auth-ships-token-auth-stays-out-no-new-meta--settings-key)).

## Definition of done

The completion contract the card is built against. Items map onto the card's own
DoD bullets: item 2 (the `auth/` module with the four symbols, composable with the
permissions surface), item 3 (mirrored tests under `tests/auth/`), item 4 (the
opt-in documentation) — plus the spec/CSV and the version-cut items the
[`docs/SPECS/NEXT.md`][next] flow and the joint-cut handoff add.

**Spec + companion CSV**

1. `docs/spec-040-auth_mutations-0_0_13.md` (this document; archived post-ship to
   `docs/SPECS/spec-040-auth_mutations-0_0_13.md`) and its companion
   `spec-040-auth_mutations-0_0_13-terms.csv` exist — the companion archived to
   `docs/SPECS/appx/` per [`AGENTS.md`][agents] rule 26, alongside the rationale
   companion [`…-rationale.md`][spec-040-rationale];
   `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md`
   reports `OK: <N> terms`.

**Slice 1 — auth substrate + `login` / `logout`, earned live**

2. `django_strawberry_framework/auth/` ships `login_mutation()` /
   `logout_mutation()` as field factories with the declaration ledger,
   `bind_auth_mutations()` wired into [`types/finalizer.py`][types-finalizer] phase
   2.5 in the pinned slot (pre-bind reset loop → `bind_auth_mutations()` →
   `bind_mutations()` → `bind_form_mutations()`), `LoginPayload` / `LogoutPayload`
   materialized through the ONE `build_payload_type` builder onto the existing
   `mutations.inputs` emit ledger — **surface-keyed: each payload only when its
   surface was declared** ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows))
   — (no new pre-bind `register_subsystem_clear` row in Slice 1),
   the auth **declaration** ledger cleared by a full-clear-only
   [`register_subsystem_clear`][registry] row beside `clear_mutation_registry` /
   `clear_form_mutation_registry` (no `before_bind` — [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)),
   the login / logout permission holders (pinned `__name__`s `Login` / `Session`)
   reusing `authorize_or_raise` / `check_permission` by call, the **surface-keyed**
   user-model primary-type bind validation for the Slice-1-declarable surfaces (the
   login arm's auth-specific message; the logout-only exemption binding with no
   user type and resolving no primary) — with the bind ordering wired so the
   Slice-2 register / `current_user` arms are reachable when those factories land
   (their coverage is DoD items 4–5, **not** this one: `register_mutation()` /
   `current_user()` do not exist in Slice 1)
   ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)),
   the AllowAny default (the empty permission-class list via `unset_default=()` —
   no `AllowAny` class exists or is added) + `permission_classes=` seam through the
   standard `check_permission` machinery (the conflict / cache key being
   `permission_classes` alone — presentation kwargs excluded), and sync + async
   resolver pairs over `django.contrib.auth` — failed authentication returning the
   ONE `"__all__"`-keyed [`FieldError`][glossary-fielderror-envelope]
   ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
   **In the same commit**, the fakeshop `accounts` surface exposes `login` /
   `logout`, `"apps.accounts.schema"` joins [`schema_reload.py`][schema-reload]'s
   `_PROJECT_APP_SCHEMA_MODULES` (so the complete-reload fixtures preserve the auth
   surface after a `registry.clear()`), and `test_query/test_auth_api.py` earns
   every reachable branch live (the canonical AllowAny default surface — the gate
   variants are `tests/auth/` package tests, [Test plan](#test-plan)).
3. `tests/auth/test_mutations.py` mirrors the module for the package-only residue
   (ledger, bind validation, post-finalize raise, async, sessionless,
   [`SyncMisuseError`][glossary-syncmisuseerror]).

**Slice 2 — `register` + `current_user`, earned live**

4. `register_mutation()` synthesizes the cached `Register` rider (`__name__ =
   "Register"`, so the unchanged machinery emits `RegisterPayload` — there is no
   payload-name seam; [`DjangoMutation`][glossary-djangomutation] rider: `create`
   over `get_user_model()`, `Meta.fields = (USERNAME_FIELD, *REQUIRED_FIELDS,
   "password")` via the directly-testable `derive_register_fields(user_model)`
   helper (delegating unknown-field rejection to `editable_input_fields`) with
   `email` optional per `input_field_required`, `RegisterInput`
   via the input-name seam, account-control columns kept off the generated input by
   Decision 6's two layers) — **overriding
   `resolve_sync` AND `resolve_async`** to ride `run_write_pipeline_sync` with the
   password-aware step pair (the `decode_step` returns
   `(user, m2m_assignments, exclude, raw_password)` with `password` captured
   through the provided-marker-preserving exclusion seam — the AR-H2 exclude
   calculation still counts it as provided; the `write_step` runs
   `validate_password(raw_password, user)` →
   `set_password(raw_password)` → `full_clean()` → `save()`; the `036` pipeline
   exposes no per-instance write hook), plaintext never persisted **on either path**
   (asserted: model decode never receives `password`), a **conflicting second call
   with a different `permission_classes` raising
   [`ConfigurationError`][glossary-configurationerror]**, and **every
   same-`permission_classes` factory call re-registering the cached rider into the
   mutation ledger**
   (identity-deduped, reload-safe) — exposed through the unchanged
   [`DjangoMutationField`][glossary-djangomutationfield], with the `036` payload
   re-fetch (by pk, no visibility filter, G2-gated)
   ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
   `current_user()` returns the nullable session actor without a
   [`get_queryset`][glossary-get_queryset-visibility-hook] re-run
   ([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)).
   **In the same commit**, the live suite covers the register → login → `me` →
   logout round trip, the duplicate-username and weak-password envelopes, the
   hashed-storage assertion, and anonymous `me: null`.
5. `tests/auth/` covers the internals residue (factory cache, the
   reload-idempotence cycle with `register` present in the second schema and a
   prior conflicting-`permission_classes` raise not surviving the clear, the
   register-arm / current-user-arm no-`UserType` error messages — pinned distinct
   from login's, the coverage moved here from Slice 1 — plus the register-only /
   current-user-only surface-keyed binds, `derive_register_fields` custom
   user-model field-set derivation (a test-scoped model, no `AUTH_USER_MODEL`
   swap), the exclusion-seam provided-marker test, validator-mapping shapes,
   hash-ordering, the sync + async plaintext-never-persisted pair, lazy-user
   forcing, and the `me` / `register` gate variants on isolated throwaway
   schemas).

**Cross-cutting — no regression**

6. The full suite is green at the 100% coverage gate (`fail_under = 100`);
   `ruff format` + `ruff check` are clean; the `036` / `038` / `039` mutation
   surfaces and the read side are unchanged. Every
   [Helper-reuse obligation](#helper-reuse-obligations-dry) (the
   helper-reuse review's D1–D19 / P1–P4 / D-N1–D-N3 directives) is satisfied —
   the auth code routes through the named write-stack / [`utils/`][utils-inputs] helpers
   and does not re-spell them, and the three deliberate non-reuse points carry their
   source comment.

**Slice 3 — docs + the `0.0.13` version cut + card wrap**

7. The version quintet **moved to `0.0.13` at this card's cut** — all five members
   ([`pyproject.toml`][pyproject], `__version__`,
   [`tests/base/test_init.py::test_version`][test-base-init], the GLOSSARY version
   line, the `uv.lock` package entry) read `0.0.13` at the release commit; later cards
   move them on, so this item is a claim about the cut, never about `HEAD`. The
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
[agents]: ../../AGENTS.md
[backlog]: ../../BACKLOG.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[pyproject]: ../../pyproject.toml
[readme]: ../../README.md
[start]: ../../START.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[glossary-apply_cascade_permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-auth-mutations]: ../GLOSSARY.md#auth-mutations
[glossary-channels-request-adapter]: ../GLOSSARY.md#channels-request-adapter
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-cross-subsystem-invariants]: ../GLOSSARY.md#cross-subsystem-invariants
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-djangoformmutation]: ../GLOSSARY.md#djangoformmutation
[glossary-djangographqlprotocolrouter]: ../GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-djangomodelpermission]: ../GLOSSARY.md#djangomodelpermission
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: ../GLOSSARY.md#djangomutationfield
[glossary-djangonodefield]: ../GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-fielderror-envelope]: ../GLOSSARY.md#fielderror-envelope
[glossary-fieldset]: ../GLOSSARY.md#fieldset
[glossary-finalize_django_types]: ../GLOSSARY.md#finalize_django_types
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-graphqltestcase]: ../GLOSSARY.md#graphqltestcase
[glossary-input-type-generation]: ../GLOSSARY.md#input-type-generation
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metainterfaces]: ../GLOSSARY.md#metainterfaces
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-per-field-permission-hooks]: ../GLOSSARY.md#per-field-permission-hooks
[glossary-serializermutation]: ../GLOSSARY.md#serializermutation
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode
[glossary-syncmisuseerror]: ../GLOSSARY.md#syncmisuseerror
[glossary-testclient]: ../GLOSSARY.md#testclient
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[next]: NEXT.md
[rationale-d10]: appx/spec-040-auth_mutations-0_0_13-rationale.md#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary
[rationale-d11]: appx/spec-040-auth_mutations-0_0_13-rationale.md#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully
[rationale-d12]: appx/spec-040-auth_mutations-0_0_13-rationale.md#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut
[rationale-d1]: appx/spec-040-auth_mutations-0_0_13-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d2]: appx/spec-040-auth_mutations-0_0_13-rationale.md#decision-2--card-scope-boundary-session-auth-ships-token-auth-stays-out-no-new-meta--settings-key
[rationale-d3]: appx/spec-040-auth_mutations-0_0_13-rationale.md#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export
[rationale-d4]: appx/spec-040-auth_mutations-0_0_13-rationale.md#decision-4--module-and-test-locations-auth-mirroring-the-upstream-trio-testsauth-mirroring-source
[rationale-d5]: appx/spec-040-auth_mutations-0_0_13-rationale.md#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design
[rationale-d6]: appx/spec-040-auth_mutations-0_0_13-rationale.md#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor
[rationale-d7]: appx/spec-040-auth_mutations-0_0_13-rationale.md#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset
[rationale-d8]: appx/spec-040-auth_mutations-0_0_13-rationale.md#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind
[rationale-d9]: appx/spec-040-auth_mutations-0_0_13-rationale.md#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows
[rationale-risks]: appx/spec-040-auth_mutations-0_0_13-rationale.md#risks-and-open-questions
[spec-034]: spec-034-permissions-0_0_10.md
[spec-035]: spec-035-optimizer_hardening-0_0_10.md
[spec-036]: spec-036-mutations-0_0_11.md
[spec-038]: spec-038-form_mutations-0_0_12.md
[spec-039]: spec-039-serializer_mutations-0_0_13.md
[spec-040-rationale]: appx/spec-040-auth_mutations-0_0_13-rationale.md
[spec-046-d16]: spec-046-transport_security-0_0_14.md#decision-16--revocation-is-connection-scoped-and-gated-at-the-websocket-adapters-outbound-frame-seam
[spec-046-d2]: spec-046-transport_security-0_0_14.md#decision-2--http-dispatches-directly-to-a-required-consumer-supplied-django-asgi-application
[spec-046]: spec-046-transport_security-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[auth-sessions]: ../../django_strawberry_framework/auth/sessions.py
[conf]: ../../django_strawberry_framework/conf.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[init]: ../../django_strawberry_framework/__init__.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-sessions]: ../../django_strawberry_framework/utils/sessions.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py
[utils-write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py

<!-- examples/ -->
[config-schema]: ../../examples/fakeshop/config/schema.py
[config-settings]: ../../examples/fakeshop/config/settings.py
[config-urls]: ../../examples/fakeshop/config/urls.py
[create-users]: ../../examples/fakeshop/apps/products/management/commands/create_users.py
[schema-reload]: ../../examples/fakeshop/schema_reload.py
[test-query-readme]: ../../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-auth-mutations]: ../../../strawberry-django-main/strawberry_django/auth/mutations.py
[upstream-auth-queries]: ../../../strawberry-django-main/strawberry_django/auth/queries.py
[upstream-auth-utils]: ../../../strawberry-django-main/strawberry_django/auth/utils.py
