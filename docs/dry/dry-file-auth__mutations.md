# DRY review: `django_strawberry_framework/auth/mutations.py`

Status: fix-implemented

Iteration 2026-07-16: internal sync-boundary imports now target the canonical
`utils/querysets.py` owner directly. Independent verification is pending.

## System trace

`auth/mutations.py` is the spec-040 session-auth surface owner. It ships the opt-in
factories `login_mutation()` / `logout_mutation()` / `register_mutation()`, the folder-shared
field-construction and declaration helpers `queries.py` imports (`_make_auth_field`,
`_declare_fixed_auth_surface`, `_AUTH_FAMILY_LABEL`), and the phase-2.5 `bind_auth_mutations()`
that `types/finalizer.py` runs before `bind_mutations()`. What it *owns* is genuinely narrow:

- **The auth declaration ledger + its cache/conflict state** — an instance of the shared
  `mutations/sets.py::make_declaration_registry` over its own disjoint store, cleared full-only
  (registered via `registry.py::register_subsystem_clear` without the `before_bind` flag). The
  per-surface `_declared_auth_surface` / `_reject_conflicting_permission_classes` /
  `_declare_auth_surface` layer adds the one-declaration-per-process permission-conflict rule the
  fixed payload names require.
- **The fixed-field permission holder** — `_AuthMutationMetaSnapshot` + `_make_permission_holder`
  synthesize a zero-arg class whose duck-typed `_mutation_meta` carries only
  `permission_classes` + `operation`, with `DjangoMutation.check_permission` bound by reference.
- **The session resolver bodies** — `_login_resolve_body` / `_logout_resolve_body` (and
  `queries.py::_current_user_resolve_body`) wrap `django.contrib.auth.authenticate/login/logout`
  behind the `FieldError` envelope.
- **The register rider** — `_synthesize_register_rider` mints a concrete `DjangoMutation`
  subclass; `derive_register_fields`, `_register_decode_step`, `_register_write_step`, and
  `_run_register_pipeline_sync` add only the password-aware decode/write step pair.
- **The surface-keyed bind** — `_resolve_user_primary_or_raise` + `bind_auth_mutations()`.

Connected owners traced: `mutations/sets.py` (`make_declaration_registry`,
`_validate_permission_classes`, `DjangoMutation.check_permission`, `_resolve_primary_type`,
`_bind_mutation`); `mutations/resolvers.py` (`run_write_pipeline_sync`, `_model_decode_step` with
the D6 `excluded_input_fields` seam, `_model_write_step`, `authorize_or_raise`, `build_payload`,
`field_error`, `payload_cls_for`, `run_in_one_sync_boundary`); `mutations/fields.py`
(`DjangoMutationField`, `_lazy_ref`, `build_lazy_field_signature` — promoted to shared machinery
by spec-040); `mutations/inputs.py` (`build_payload_type`, `payload_object_slot`,
`materialize_mutation_input_class`, `editable_input_fields`, `mutation_input_shape`,
`build_mutation_input`); `utils/permissions.py::request_from_info`;
`utils/write_values.py::unencodable_text_error`; `utils/inputs.py::make_input_namespace`;
`mutations/permissions.py` (`run_permission_classes`, `DjangoModelPermission`); `registry.py`;
`types/finalizer.py` (the `loaded_attr`-guarded pre-`bind_mutations()` call); `tests/auth/`;
`examples/fakeshop/apps/accounts/schema.py`.

## Verification

- **Item-scoped diff is empty.** `git diff <ITEM_BASELINE> -- django_strawberry_framework/auth/`
  returns nothing; this review changed nothing and no prior in-flight edit exists on the target.
- **The file is already a thin layer over the frozen write foundation.** spec-040's Helper-reuse
  directives (D1–D17) were designed to prevent duplication, and every reuse obligation is
  discharged by call: the declaration mechanics via `make_declaration_registry`; the async
  boundary via `run_in_one_sync_boundary`; the field signature/lazy-ref via
  `build_lazy_field_signature` / `_lazy_ref`; the register write pipeline via
  `run_write_pipeline_sync` + `_model_decode_step` (D6 exclusion seam) + `_model_write_step`;
  payload emit via `build_payload_type` + `materialize_mutation_input_class`; the unstorable-text
  preflight via `unencodable_text_error`; the register field narrowing via
  `editable_input_fields`. Confirmed by reading each owner, not by name similarity.

Rejected candidates (searched by concept, tried to prove a shared change-axis):

1. **`_resolve_user_primary_or_raise` vs `mutations/sets.py::_resolve_primary_type`.** Both are
   "resolve model's primary `DjangoType` or raise", both use `registry.get` then
   `registry.types_for` to split the no-type vs multiple-no-primary arms. The *getter* is already
   single-sited in `registry.py` (the target's docstring calls this out as D16). What remains
   distinct is the two error messages (auth names the offending factories + gives
   `get_user_model()` recourse) and the *lifecycle placement* — the auth raise fires before
   `bind_mutations()` precisely so its actionable message pre-empts the generic mutation one
   (Decision 8; pinned by `tests/auth/test_mutations.py::test_register_only_schema_without_user_type_raises_the_register_arm_error`
   asserting the generic wording never appears). Consolidating the three-line branch would demand
   a message-builder-callback helper whose only content is the divergent messages — obscuring
   ownership for no shared substance. Kept separate.

2. **`_AuthMutationMetaSnapshot` vs `_ValidatedMutationMeta`.** Deliberate non-reuse: the holder
   needs only `permission_classes` + `operation` and must be constructible without the
   `model`/`operation` kwargs a model-less session field cannot supply. Documented at the class;
   `check_permission` reads only `permission_classes`. Kept separate.

3. **The register rider's `resolve_sync` / `resolve_async` twins vs `resolver_seams` /
   `make_resolver_entries`.** The shared owners produce module-level entries (or classmethods) that
   thread `data` **and** `id` through to a named resolver module. The rider is create-only: it
   drops `id`, is a classmethod on the synthesized class, and calls the local
   `_run_register_pipeline_sync(cls, info, data)` directly (it IS the bespoke sync body, not a
   dispatcher consumer). The async boundary itself already rides the shared
   `run_in_one_sync_boundary`. Forcing the rider through the seam factories would need an adapter
   re-adding `id` and re-wrapping as classmethods — more code, less clarity. Kept separate.

4. **The permission-conflict raise (`_reject_conflicting_permission_classes`) vs the emit-ledger
   AR-M6 collision (`materialize_generated_input_class`).** Both raise on "two distinct things
   claim one fixed name", but at different layers (declaration-time permission specialization vs
   materialize-time distinct-class identity) with different keys. Not one contract. Kept separate.

5. **The authenticated-actor idiom** `user = getattr(request, "user", None)` + `is_authenticated`
   in `_logout_resolve_body` (bool form) and `queries.py::_current_user_resolve_body`
   (actor form). Grep confirms exactly these two live sites; `DjangoModelPermission` only mentions
   `is_authenticated` in prose and instead relies on a None-guard + `has_perm` (a different
   responsibility). This is a genuine 2-line, 2-site idiom whose anonymity definition would change
   in lockstep, but the two sites return different shapes and both live in the auth folder. It is a
   cross-file (mutations.py + queries.py) folder-scope concern best weighed in the separate
   `auth/` folder-integration pass; extracting a helper for a 2-line idiom here risks
   over-abstraction against the DRY charter's "do not optimize for fewer lines". Deferred to the
   folder pass, not consolidated in this file review.

## Opportunities

None — the file is a deliberately thin composition over already-single-sited owners
(`make_declaration_registry`, `run_write_pipeline_sync`, `_model_decode_step`/`_model_write_step`,
`build_lazy_field_signature`/`_lazy_ref`, `run_in_one_sync_boundary`, `build_payload_type` +
`materialize_mutation_input_class`, `unencodable_text_error`, `editable_input_fields`,
`registry.get`). Every apparent parallel is either already reused by call or an intentional,
documented, and test-pinned divergence (the auth-specific primary-resolution message and
lifecycle placement; the minimal holder snapshot; the create-only rider seams). The strongest
remaining candidate (the authenticated-actor idiom) is a folder-scope 2-line pattern deferred to
the `auth/` integration pass.

## Judgment

Well-proved zero-edit review. `auth/mutations.py` introduces no duplicated responsibility that a
truer owner should hold; its spec-040 Helper-reuse obligations are all discharged against existing
single-sited owners, and the few structural parallels are intentional, documented divergences with
distinct change axes. Item-scoped diff empty. Ready for Worker 2.

## Independent verification (Worker 2)

**Scoped diff.** `git diff 6783d0a8fd7b6500600a93952cd36f836123c329 -- django_strawberry_framework/auth/mutations.py`
returns empty, and so does the same diff widened to the whole `auth/` package plus `tests/auth/`
(`ITEM_BASELINE` per the assignment, not the older cycle baseline `bdf3f44b...` recorded in
`dry-0_0_13.md`, which predates several already-verified items in this cycle and does show
unrelated prior-item changes — e.g. the `unencodable_text_error` login guard and the logout
docstring rewording landed by the `auth/queries.py`-adjacent earlier work — none of which are new
edits from this item). `git status --short` on the same paths shows only `tests/auth/test_mutations.py`
and `tests/auth/test_queries.py` as `M` against `HEAD`, and those same two files are already `M`
relative to `ITEM_BASELINE` at zero delta (identical content, pre-existing in the baseline commit) —
consistent with the sibling `auth/__init__.py` verification's finding that these are baked-into-baseline,
not concurrent or in-flight work. Confirmed zero-edit.

**Re-traced the responsibility.** Read the complete target plus every connected owner named in the
artifact, not just the names:

- `mutations/sets.py`: confirmed `make_declaration_registry` (`mutations/sets.py::make_declaration_registry`), `DjangoMutation.check_permission`
  (`mutations/sets.py::DjangoMutation.check_permission`, delegates to `mutations/permissions.py::run_permission_classes`), `_resolve_primary_type`
  (`mutations/sets.py::_resolve_primary_type`), `_validate_permission_classes` (`mutations/sets.py::_validate_permission_classes`), and that `mutations.sets.register_mutation`
  (aliased `_mutation_declaration_registry.register`, `mutations/sets.py #"register_mutation = "`) is the exact object `auth/mutations.py`
  imports as `record_mutation_declaration` — the register rider's dual-ledger re-record calls the real
  shared method, not a re-spelled copy.
- `mutations/resolvers.py`: confirmed `run_write_pipeline_sync` (`mutations/resolvers.py::run_write_pipeline_sync`), `_model_decode_step`
  (`mutations/resolvers.py::_model_decode_step`) with the real `excluded_input_fields` seam (default `frozenset()`, extends the
  return tuple only when non-empty — read the full body, not just the signature), `_model_write_step`
  (`mutations/resolvers.py::_model_write_step`), `authorize_or_raise` (`mutations/resolvers.py::authorize_or_raise`), `payload_cls_for` (`mutations/resolvers.py::payload_cls_for`),
  `run_in_one_sync_boundary` (`mutations/resolvers.py::run_in_one_sync_boundary`), and `build_payload` (`mutations/resolvers.py::build_payload`). `field_error`
  is not defined in `resolvers.py` itself but imported there from `utils/errors.py::field_error` and re-exposed as a
  module attribute, so `resolvers.field_error(...)` in the target resolves to the single real owner — the
  artifact's phrasing ("mutations/resolvers.py (... field_error ...)") is a location shorthand for an
  attribute access, not a wrong claim.
- `mutations/fields.py` / `mutations/inputs.py`: confirmed `_lazy_ref` (`mutations/fields.py::_lazy_ref`),
  `build_lazy_field_signature` (`mutations/fields.py::build_lazy_field_signature`), `editable_input_fields` (`mutations/inputs.py::editable_input_fields`),
  `build_payload_type`, `payload_object_slot`, `materialize_mutation_input_class`,
  `mutation_input_shape`, `build_mutation_input` all exist with the call shapes the target uses.
- `utils/permissions.py::request_from_info` (`utils/permissions.py::request_from_info`) and
  `utils/write_values.py::unencodable_text_error` (`utils/write_values.py::unencodable_text_error`) confirmed as the single owners
  the target calls by reference, not by re-implementation.

**Challenged each rejected/deferred candidate independently** rather than trusting the write-up:

1. `_resolve_user_primary_or_raise` vs `_resolve_primary_type` — confirmed both route through
   `registry.get` / `registry.types_for`; confirmed the two error messages and the phase-2.5-vs-bind
   lifecycle placement are real and test-pinned (`tests/auth/test_mutations.py::test_register_only_schema_without_user_type_raises_the_register_arm_error`,
   read in full at `tests/auth/test_mutations.py::test_register_only_schema_without_user_type_raises_the_register_arm_error`: it explicitly asserts the generic mutation-bind wording is absent).
   Holds.
2. `_AuthMutationMetaSnapshot` vs `_ValidatedMutationMeta` — confirmed `check_permission` (`mutations/sets.py::DjangoMutation.check_permission`)
   reads only `permission_classes` off `_mutation_meta`, and the holder's `__slots__` carry exactly
   `operation` + `permission_classes`; a model-less session field genuinely cannot supply
   `_ValidatedMutationMeta`'s `model` kwarg. Holds.
3. Register rider's `resolve_sync`/`resolve_async` vs `resolver_seams`/`make_resolver_entries` — confirmed
   by reading the rider body (`auth/mutations.py::_synthesize_register_rider`): it is a classmethod pair calling the local
   `_run_register_pipeline_sync` directly, drops `id`, and rides `run_in_one_sync_boundary` for the async
   half exactly like the fixed-field dispatcher does. Forcing it through the seam factories would need an
   `id`-reintroducing adapter for no shared behavior. Holds.
4. Permission-conflict raise vs the AR-M6 emit-ledger collision — confirmed these are different layers
   (declaration-time permission specialization vs materialize-time class-identity collision) with
   different keys; not the same contract. Holds.
5. **The authenticated-actor idiom, deferred to the folder pass** — independently grepped
   `getattr(request, "user", None)` and `is_authenticated` across the whole package. Confirmed exactly
   two live sites carry the `getattr(...) then is_authenticated` shape: `auth/mutations.py::_logout_resolve_body`
   (`_logout_resolve_body`, boolean `ok`) and `auth/queries.py::_current_user_resolve_body` (`_current_user_resolve_body`, actor
   value). A third site, `mutations/permissions.py::DjangoModelPermission.has_permission` (`mutations/permissions.py::DjangoModelPermission.has_permission`),
   also does `getattr(request, "user", None)` but branches on `user is None` only (a None-guard before
   `has_perm`), never reads `is_authenticated` — read the body directly to confirm this rather than trusting
   the artifact's characterization, and it is correct: `is_authenticated` appears in that file only in a
   docstring sentence, not in a code branch. This is a genuinely different responsibility (permission
   check vs anonymity classification), so the "exactly two live sites" claim and the "kept separate from
   `DjangoModelPermission`" claim both hold. The 2-line, 2-site idiom is real, cross-file
   (`mutations.py` + `queries.py`), and the `auth/` folder-integration plan item
   (`dry-folder-auth.md`) is still open in `dry-0_0_13.md`, so the deferral has a real landing site and
   will not be silently dropped. Deferring a 2-line idiom out of a single-file review rather than minting
   a premature helper is consistent with `DRY.md`'s "do not optimize for fewer lines" ground rule. Holds.

**Searched independently for missed consolidation** beyond the artifact's own candidate list:

- **Password handling.** Grepped the whole package for `password`, `validate_password`,
  `password_validation`, and `set_password`: `auth/mutations.py` is the only production module that
  imports or calls any of them (`rest_framework/`, `forms/` have zero matches). There is no second,
  parallel password-hashing or password-validation implementation anywhere in
  `django_strawberry_framework/` to consolidate against. None found.
- **`django.contrib.auth` usage.** Grepped for `django.contrib.auth` / `authenticate(`: only
  `auth/mutations.py` calls `authenticate` / `auth.login` / `auth.logout`; `testing/client.py` imports
  `AbstractBaseUser` for an unrelated type-check, not session auth. No duplicate session-auth surface
  exists elsewhere. None found.
- **Coverage of the claimed test-pinned behaviors, at the correct tier.** The enumeration-guard and
  surrogate-credential claims are NOT covered in `tests/auth/test_mutations.py` (which covers only
  declaration/ledger/bind internals) — correctly, per `AGENTS.md`'s test-placement rule that real-query-reachable
  behavior belongs in `examples/fakeshop/test_query/`. Found and read
  `examples/fakeshop/test_query/test_auth_api.py`: `test_wrong_password_and_unknown_username_return_identical_envelope`
  and `test_inactive_user_gets_the_same_envelope` pin the byte-identical `"Incorrect username/password"`
  envelope; `test_login_surrogate_username_is_the_undifferentiated_envelope_not_a_crash` and
  `test_login_surrogate_password_is_the_undifferentiated_envelope_not_a_crash` pin the
  `unencodable_text_error` short-circuit the artifact describes; `test_register_surrogate_password_keys_to_password_not_a_crash`
  pins the D6 exclusion seam's bypass of the scalar preflight for `password`. All exist and assert the
  exact shapes the artifact claims. No coverage gap.
- **The register dual-ledger re-record.** Confirmed independently (see above) that
  `record_mutation_declaration` is a direct alias for the real `mutations.sets` registry method, so the
  "every call re-records on BOTH ledgers" behavior is not a second hand-rolled ledger — it is two calls
  into the one shared `register` method on two disjoint `DeclarationRegistry` instances. Not duplication.

Tried to break the zero-edit conclusion with a fresh angle: does any fixed auth field (`login` /
`logout` / `current_user`) duplicate the register rider's password/validation concerns, or vice versa?
No — `_login_resolve_body` never touches `set_password`/`validate_password` (it calls `authenticate`,
which hashes internally via the configured backend), and the register rider never calls
`authenticate`/`auth.login`. The two password-adjacent code paths (`authenticate`'s internal hash
comparison vs `set_password`'s hash-on-create) are different Django-owned operations with no shared
policy this package should own once. No missed opportunity.

No challenge to any rejected or deferred candidate survives re-inspection, no missed consolidation
was found against `mutations/` package helpers, the `queries.py` actor idiom, or password handling,
and the item-scoped diff is independently confirmed empty.

Status: fix-implemented. The Worker-2 pass above verified the zero-edit responsibility analysis
against a baseline where `run_in_one_sync_boundary` was still defined in `mutations/resolvers.py`
(its trace names that location). The 2026-07-16 sync-boundary iteration centralized the primitive
into `utils/querysets.py::run_in_one_sync_boundary` and repointed this file's import to it directly;
that iteration reopens the artifact for independent re-verification.
