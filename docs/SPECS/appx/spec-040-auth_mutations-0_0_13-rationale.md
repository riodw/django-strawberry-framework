# Rationale companion: spec-040 (Auth mutations — `login_mutation` / `logout_mutation` / `register_mutation` / `current_user`)

Companion to [`docs/SPECS/spec-040-auth_mutations-0_0_13.md`][spec-040]. It carries
the reasons behind that spec's contract: each Decision's justification, the
alternatives it rejected and why, and the open questions the surface leaves. The spec
carries the contract; this file carries why the code is shaped that way.

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-040-d1].

### Alternatives considered (and rejected)

- **An unstructured `docs/spec-auth_mutations.md`.** Rejected: the structured
  `spec-<NNN>-<topic>-<X_Y_Z>.md` name sorts with its card and release on disk and is
  the convention every spec follows.

## Decision 2 — Card-scope boundary: session auth ships; token auth stays out; no new `Meta` / settings key

Spec: [Decision 2 — Card-scope boundary: session auth ships; token auth stays out; no new `Meta` / settings key][spec-040-d2].

### Justification

Token / JWT auth and password-change / reset flows have no analog in either reference
package to claim parity against, and [`START.md`][start]'s resist-scope-creep rule
applies. The session surface composes from field factories and the existing write
seams, so nothing in it needs a new `Meta` key or settings key. Which transports the
surface accepts is
[Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)'s
answer, not a scope question.

### Alternatives considered (and rejected)

- **Ship a `password_change` mutation.** Rejected: neither reference package has one
  (parity would be fabricated), and a consumer composes it from
  [`DjangoMutation`][glossary-djangomutation].

## Decision 3 — Consumer surface: four field factories at the `auth` submodule path, opt-in by import, no root re-export

Spec: [Decision 3 — Consumer surface: four field factories at the `auth` submodule path, opt-in by import, no root re-export][spec-040-d3].

### Justification

A submodule-only path makes the opt-in **structural** rather than merely documented:
the package root never imports `auth/`, so a schema that does not use auth never loads
it. The `testing.relay` helpers set the precedent (not re-exported from the `testing`
root, by design). The symbols are factories rather than pre-built field instances
because an instance cannot carry a per-schema `permission_classes=`. The factory-call
shape mirrors upstream's consumer surface (`login = auth.login()` upstream ↔
`login = login_mutation()` here), so migrating is an import-line change.

### Alternatives considered (and rejected)

- **Root exports (`from django_strawberry_framework import login_mutation`).**
  Rejected: the root `__all__` is the always-available surface; auth is opt-in, and a
  root export would import `auth/` (and `django.contrib.auth` through it) for every
  consumer, used or not.
- **PascalCase mutation classes the consumer wires through
  [`DjangoMutationField`][glossary-djangomutationfield]
  (`login = DjangoMutationField(LoginMutation)`).** Rejected for `login` / `logout`:
  their argument signatures (`username:` / `password:`; no arguments) do not fit the
  factory's synthesized `data:` / `id:` signatures, so they would need special cases
  inside the shared factory. `register` **does** ride
  [`DjangoMutationField`][glossary-djangomutationfield] internally
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
- **A module of loose resolvers the consumer wraps themselves (the
  `strawberry_django` style).** Rejected: hands the payload / envelope work back to the
  consumer, the boilerplate the surface exists to absorb.

## Decision 4 — Module and test locations: `auth/` mirroring the upstream trio; `tests/auth/` mirroring source

Spec: [Decision 4 — Module and test locations: `auth/` mirroring the upstream trio; `tests/auth/` mirroring source][spec-040-d4].

### Justification

`auth/mutations.py` / `auth/queries.py` mirror upstream's
[`strawberry_django/auth/`][upstream-auth-mutations] layout; upstream's `utils.py`
(request / user extraction) already exists in this package as
[`utils/permissions.py::request_from_info`][utils-permissions], which the resolvers
reuse rather than re-spell. `auth/sessions.py` has no upstream counterpart because it
replaces upstream's inline transport fallback with an explicit classification
([Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)).

### Alternatives considered (and rejected)

- **A single flat `auth.py`.** Rejected: the subpackage carries the mutations, a
  query helper, a bind and a transport layer; one-purpose files keep each small and
  mirror the upstream layout a migrant greps for.
- **A set-family layout (`auth/sets.py` / `auth/resolvers.py` / `auth/inputs.py`).**
  Rejected: auth is not a declarative set family — there is no consumer-declared class
  to collect, validate and expand, so the family layout over four fixed factories is
  indirection with nothing to hold.

## Decision 5 — `login` / `logout`: session mutations on the frozen envelope, anonymous-allowed by design

Spec: [Decision 5 — `login` / `logout`: session mutations on the frozen envelope, anonymous-allowed by design][spec-040-d5].

### Justification

The envelope (rather than upstream's raised `ValidationError`) is the
[Cross-subsystem invariants][glossary-cross-subsystem-invariants] requirement: one
`FieldError` envelope across every mutation flavor, so a client already handling
`{ node, errors }` from every write handles a failed login with no new code path.

### Alternatives considered (and rejected)

- **Raise `GraphQLError` on bad credentials (upstream's shape).** Rejected: a wrong
  password is an *expected* outcome, and the package routes expected write outcomes
  through the envelope; top-level errors are for authorization denials and malformed
  requests.
- **A `data: LoginInput!` argument for family consistency.** Rejected: the
  generated-input machinery derives shapes from models / forms / serializers, and a
  fixed two-credential signature derives from nothing; flat arguments match upstream
  and the plain GraphQL ergonomics of the most-called mutation in a schema.
- **Distinguish "no such user" from "wrong password".** Rejected: an
  account-enumeration oracle, which upstream and Django's own `AuthenticationForm`
  also refuse.
- **Return the user from `logout` (symmetry with `login`).** Rejected: the session is
  gone and the only useful fact is whether an authenticated actor existed, which
  `{ ok, errors }` carries (upstream returns a bool).
- **Default `permission_classes` to the family's deny.** Rejected: nobody could ever
  log in. The inversion is explicit and single-sited: every auth factory normalizes
  through `_validate_permission_classes(..., unset_default=())` in the one shared
  declaration path.

## Decision 6 — `register_mutation()` rides `DjangoMutation`: a narrow `create` over `get_user_model()` with password hashing — NOT a fourth flavor

Spec: [Decision 6 — `register_mutation()` rides `DjangoMutation`: a narrow `create` over `get_user_model()` with password hashing — NOT a fourth flavor][spec-040-d6].

### Justification

A new write flavor re-spells a converter, an input generator and an orchestration
layer. The register rider needs none of them: the model-column converter covers the
`AbstractBaseUser` columns, the standard `Meta.fields` narrowing generates the input,
and the shared write skeleton orchestrates. Only the password work is genuinely new,
so it is the one decode / write step pair the rider supplies. This is also upstream's
shape — `DjangoRegisterMutation(DjangoCreateMutation)` overriding the create step with
`validate_password` + a `set_password` pre-save hook — adapted to the package's seams,
plus the validator-gets-the-user improvement in
[Borrowing posture][spec-040-borrowing].

### Alternatives considered (and rejected)

- **A consumer-facing subclassable base instead of a factory**
  (`class MyRegister(DjangoRegisterMutation): class Meta: ...`). Rejected: the
  no-argument factory covers the parity case and keeps the safe path the obvious one —
  a naive consumer-declared [`DjangoMutation`][glossary-djangomutation] over the user
  model stores `password` verbatim, because the generic pipeline constructs and saves
  the column as submitted. A customization surface is an open question
  ([Risks and open questions](#risks-and-open-questions)).
- **A `pre_save` / per-instance write hook on the shared
  [`DjangoMutation`][glossary-djangomutation] base instead of the resolver-seam
  override.** Rejected: it widens the base every flavor shares for one internal
  consumer, while the per-flavor `resolve_sync` / `resolve_async` seam plus
  `run_write_pipeline_sync`'s `decode_step` / `write_step` parameters already exist for
  exactly this and the form / serializer flavors use them.
- **Include `email` unconditionally.** Rejected: `REQUIRED_FIELDS` already carries it
  for the default user model, and hardcoding it would break a custom user model that
  omits it. The `(USERNAME_FIELD, *REQUIRED_FIELDS, "password")` set is model-derived.
- **The narrowed shape's deterministic input name.** Rejected: `RegisterInput` is the
  SDL name a migrant expects; the deterministic `UserEmailPasswordUsernameInput` is
  collision-proof but reads like generated debris. The name seams exist for flavors to
  pin friendlier names ([`spec-038`][spec-038]'s `<FormClass>Input`), and the
  materialize ledger's distinct-shape collision raise still guards a consumer's own
  `RegisterInput`.
- **Validate the password with no user context (upstream's call).** Rejected:
  `validate_password(password, user)` with the constructed instance lets
  `UserAttributeSimilarityValidator` reject a password similar to the username — better
  validation for one argument.

## Decision 7 — `current_user()` returns the session actor, nullable, and does not re-run `get_queryset`

Spec: [Decision 7 — `current_user()` returns the session actor, nullable, and does not re-run `get_queryset`][spec-040-d7].

### Justification

**Nullable, not raising.** Upstream raises `ValidationError("User is not logged in.")`.
This package's read posture is nullable by contract (`node(id:)` answers `null` for a
hidden or missing row; the file / image output object is nullable by default): an
anonymous session is an expected state, not an error, and a nullable `me` is the shape
GraphQL clients branch on.

**Skipping visibility.** [`get_queryset`][glossary-get_queryset-visibility-hook]
scopes *lookups of other rows*; `me` is the actor. A directory-shaped hook ("non-staff
see only public profiles") must not make `me` return `null` for a logged-in user, the
first query every authenticated client fires. The same actor-not-lookup reasoning
governs the own-write re-fetch exception and `login`'s payload
([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)),
so it is uniform across the three actor-returning surfaces.

### Alternatives considered (and rejected)

- **Raise on anonymous (upstream's shape).** Rejected: an expected state is not an
  error, and the nullable contract is the package's read posture.
- **Run the type's `get_queryset` over a `pk=user.pk` queryset.** Rejected: hides the
  actor from themselves under directory-shaped visibility hooks, and spends a query to
  re-fetch a row the transport's middleware already loaded.
- **A `viewer`-style wrapper type.** Rejected: there is nothing to carry beyond the
  user, and a consumer composes a wrapper trivially.

## Decision 8 — The user model's primary `DjangoType` is required, validated at bind

Spec: [Decision 8 — The user model's primary `DjangoType` is required, validated at bind][spec-040-d8].

### Justification

Resolving through the registry is what every flavor does with its payload type; a
package-provided fallback `UserType` would pick a field selection — a privacy surface —
on the consumer's behalf. Failing at bind rather than at first query is the
materialize-before-`Schema` discipline: a missing type is a configuration error, and
configuration errors surface at finalization, loudly, with a named fix.

### Alternatives considered (and rejected)

- **Ship a minimal package `UserType` fallback.** Rejected: the package would be
  choosing which user columns a schema exposes, a security-adjacent default no library
  should pick silently.
- **Type the user surface as an opaque `JSON` / generic object when no type is
  registered.** Rejected: "a system that silently weakens rich relations into generic
  placeholders" is a [`GOAL.md`][goal] non-goal.
- **Validate only `login` / `current_user` and let `register` surface the generic
  `bind_mutations()` error.** Rejected: the three user-typed surfaces should fail
  uniformly, and the generic message names the internal `Register` class and the raw
  model class with no `get_user_model()` / `Meta.primary` recourse — worst for the
  consumer most likely to hit it (one who wired auth before declaring types).
- **Police the consumer's `UserType` selection (reject `password` in `Meta.fields`
  when auth is bound).** Rejected: the type may serve non-auth, legitimately privileged
  surfaces, and a hard reject would let the auth import change the validity of an
  unrelated declaration. The caution is documentation.

## Decision 9 — Bind lifecycle: a declaration ledger + `bind_auth_mutations()` at phase 2.5 + registered clear rows

Spec: [Decision 9 — Bind lifecycle: a declaration ledger + `bind_auth_mutations()` at phase 2.5 + registered clear rows][spec-040-d9].

### Justification

This is the lifecycle split every generated-at-bind surface already uses (mutation
inputs / payloads, filter / order inputs, relation connections): declaration
registries clear on `TypeRegistry.clear()`, emit ledgers clear pre-bind. A second
lifecycle for auth would be gratuitous divergence. Payload materialization reuses the
one builder and emit ledger, so a name collision (a consumer's own `Login` mutation
class also emitting `LoginPayload`) hits the standard distinct-shape collision raise
rather than a silent overwrite ([Edge cases][spec-040-edges]).

### Alternatives considered (and rejected)

- **Materialize both fixed payloads whenever any auth declaration exists.** Rejected: a
  logout-only schema would then resolve — and raise on — `get_user_model()`'s missing
  primary, defeating Decision 8's logout exemption, and a partial schema would emit
  orphan payloads (a register-only schema would materialize `LoginPayload`, colliding
  with a consumer's own distinct-shape `LoginPayload`). Keying the ledger and the bind
  on the declared surfaces makes the exemption structural.
- **Register the auth declaration ledger with `before_bind=True`.** Rejected: the
  pre-bind reset would drain the declarations before `bind_auth_mutations()` reads
  them, breaking the first finalize; moving the bind ahead of the reset instead would
  let the reset wipe the `mutations.inputs` emit ledger after `LoginPayload`
  materialized, voiding the distinct-shape collision guard and the recover-in-place
  retry. The declaration clear is a full-clear-only row, as for the mutation and form
  flavors.
- **Resolve types eagerly at factory-call time.** Rejected: breaks definition-order
  independence — the factory would demand the user type be declared first, the
  constraint `finalize_django_types()` exists to remove.
- **A dedicated auth payload namespace.** Rejected: `build_payload_type` already owns
  payload materialization and collision policy in one ledger; a second namespace forks
  the collision story.

## Decision 10 — Sync + async: session work through one `sync_to_async(thread_sensitive=True)` boundary

Spec: [Decision 10 — Sync + async: session work through one `sync_to_async(thread_sensitive=True)` boundary][spec-040-d10].

### Alternatives considered (and rejected)

- **Django's native-async auth APIs (`aauthenticate` / `alogin` / `alogout`) on the
  Django request path.** Rejected: the write family keeps one thread-sensitive
  boundary per resolution, and adopting the native-async APIs is a family-wide choice
  that would apply equally to the shared mutation pipeline, not an auth-local
  divergence. The boundary is correct, just not maximally concurrent. (A Channels
  scope already awaits `channels.auth` natively,
  [Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully).)

## Decision 11 — Transport contract: classify first, refuse a transport that cannot honour the surface truthfully

Spec: [Decision 11 — Transport contract: classify first, refuse a transport that cannot honour the surface truthfully][spec-040-d11].

### Justification

Classifying the request into one explicit mode before any credential or session work
means no path is entered speculatively and no transport is diagnosed from the failure
it caused. The per-surface support table carries a `register` / `current_user` column
because the transport neutrality of those two fields is a contract — nothing in
`auth/queries.py` branches on transport — and a column that says so is the cheapest
place for a future branch to contradict. The WebSocket actor lease, the outbound-frame
revalidation and the `4403` close are [`spec-046`][spec-046]'s decisions and are cited,
not restated, so they have one home; what this spec states is the effect an auth
consumer observes, plus the lock order, because
`auth/mutations.py::_channels_logout` is the only site that holds both locks.

### Alternatives considered (and rejected)

- **Upstream's fallback shape: try Django's `login` / `logout`, and on
  `AttributeError` reach for `request.consumer.scope` and `channels.auth`.** Rejected:
  it diagnoses the transport from an exception, swallows the case where Channels is
  absent, and cannot refuse a transport that cannot honour the surface. The Channels
  *capability* is used, on a scope already classified as Channels.
- **Let a sessionless deployment hit Django's own error.** Rejected: the absence
  surfaces downstream as a raw `AttributeError` off a `None` session, so
  `auth/sessions.py::require_session` raises an actionable error naming the
  transport's missing middleware before any credential or session work.

## Decision 12 — This card owns the `0.0.13` version bump AND completes the joint cut

Spec: [Decision 12 — This card owns the `0.0.13` version bump AND completes the joint cut][spec-040-d12].

### Justification

The release is single-sourced in `__version__` (hatchling derives the distribution
version from it through `[tool.hatch.version]`), so the cut is that one literal and its
`tests/base/test_init.py::test_version` pin. The version moves after the feature it
describes, together with the release-status wording for both `0.0.13` cards, so neither
card advertises a release the version does not carry.

### Alternatives considered (and rejected)

- **A separate release-alignment card owning the bump.** Rejected: the bump is one literal
  and its test pin, which the last card of a patch line carries; a dedicated card adds an
  owner without adding work.
- **Bumping before the auth surface lands.** Rejected: the version would name a release
  whose feature is not in the tree.
- **Serializer-flavor release-status wording ahead of the bump.** Rejected: that wording
  advertises a released `0.0.13`, true only in a tree whose `__version__` reads `0.0.13`.

## Risks and open questions

- **Custom authentication backends with non-`username` credential kwargs.**
  `authenticate(request, username=..., password=...)` covers `ModelBackend` and every
  backend honoring the conventional kwargs, including email-login models through
  `USERNAME_FIELD`. A backend wanting different credential *names* (a `token=`-shaped
  backend) cannot ride `login_mutation()`; that consumer hand-writes a login mutation.
  A `credential_fields=` factory kwarg mapping GraphQL arguments onto `authenticate`
  kwargs would be a contained, additive follow-on if demanded.
- **A register customization surface.** The no-argument factory covers the parity case;
  a consumer wanting extra profile fields at registration has no seam short of
  hand-writing a mutation (with the plaintext-password hazard named under
  [Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
  The follow-on is `DjangoRegisterMutation` as a documented subclassable base
  inheriting the password write step — upstream's shape, sequenced on real consumer
  need. The name is reserved for it; the concrete registered class is `Register`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../../GOAL.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary-cross-subsystem-invariants]: ../../GLOSSARY.md#cross-subsystem-invariants
[glossary-djangomutation]: ../../GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: ../../GLOSSARY.md#djangomutationfield
[glossary-get_queryset-visibility-hook]: ../../GLOSSARY.md#get_queryset-visibility-hook

<!-- docs/SPECS/ -->
[spec-038]: ../spec-038-form_mutations-0_0_12.md
[spec-040-borrowing]: ../spec-040-auth_mutations-0_0_13.md#borrowing-posture
[spec-040-d10]: ../spec-040-auth_mutations-0_0_13.md#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary
[spec-040-d11]: ../spec-040-auth_mutations-0_0_13.md#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully
[spec-040-d12]: ../spec-040-auth_mutations-0_0_13.md#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut
[spec-040-d1]: ../spec-040-auth_mutations-0_0_13.md#decision-1--spec-filename-and-canonical-naming
[spec-040-d2]: ../spec-040-auth_mutations-0_0_13.md#decision-2--card-scope-boundary-session-auth-ships-token-auth-stays-out-no-new-meta--settings-key
[spec-040-d3]: ../spec-040-auth_mutations-0_0_13.md#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export
[spec-040-d4]: ../spec-040-auth_mutations-0_0_13.md#decision-4--module-and-test-locations-auth-mirroring-the-upstream-trio-testsauth-mirroring-source
[spec-040-d5]: ../spec-040-auth_mutations-0_0_13.md#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design
[spec-040-d6]: ../spec-040-auth_mutations-0_0_13.md#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor
[spec-040-d7]: ../spec-040-auth_mutations-0_0_13.md#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset
[spec-040-d8]: ../spec-040-auth_mutations-0_0_13.md#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind
[spec-040-d9]: ../spec-040-auth_mutations-0_0_13.md#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows
[spec-040-edges]: ../spec-040-auth_mutations-0_0_13.md#edge-cases-and-constraints
[spec-040]: ../spec-040-auth_mutations-0_0_13.md
[spec-046]: ../spec-046-transport_security-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[utils-permissions]: ../../../django_strawberry_framework/utils/permissions.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-auth-mutations]: ../../../../strawberry-django-main/strawberry_django/auth/mutations.py
