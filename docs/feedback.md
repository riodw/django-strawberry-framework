# Review feedback - `spec-040-auth_mutations-0_0_13.md`

Reviewed Revision 2 against the current mutation/finalizer source, the fakeshop
settings/schema, and the local upstream `strawberry_django/auth/` module. The prior
`feedback2` findings have mostly been incorporated correctly. The remaining issues are
lifecycle and implementation-seam problems: places where the spec's desired public shape is
right, but the named existing machinery will not produce it as written. I re-checked each
finding against source while editing this file; the cited paths below use symbol-qualified
references or unique source substrings rather than line numbers.

## Findings

### [P1] `register_subsystem_clear` is the wrong lifecycle for auth declarations, and the proposed bind order can clear auth state before or after it is needed

Decision 9 says the auth declaration ledger's clear is registered through
`registry.py::register_subsystem_clear`, so both `registry.clear()` and the finalizer's
pre-bind reset drain it. That conflicts with what the source says that seam is for.

Source grounding:

- `django_strawberry_framework/registry.py #"The canonical pre-bind input-namespace clear list"` says the `_subsystem_clears` rows are exactly the **pre-bind input-namespace clears**, and explicitly excludes declaration registries: `"The declaration-registry resets and the per-pass shape-cache resets are NOT pre-bind input clears"`.
- `django_strawberry_framework/registry.py::register_subsystem_clear` says it records a `"pre-bind input-namespace clear"`, not a declaration-ledger clear.
- `django_strawberry_framework/types/finalizer.py::finalize_django_types #"registry is NOT cleared here - this resets only the emit ledgers, not declarations"` runs `iter_subsystem_clears()` immediately before `bind_mutations()`. The comment says this reset is for emit/materialization ledgers and deliberately not for declarations.
- `django_strawberry_framework/registry.py::TypeRegistry.clear #"The DECLARATION-registry resets"` clears the mutation/form declaration registries separately from the pre-bind namespace loop. That is the existing lifecycle split.

If `clear_auth_declarations` is put into `register_subsystem_clear` and the pre-bind reset
runs before `bind_auth_mutations()`, the auth declarations are gone before they bind. If
`bind_auth_mutations()` is moved before the reset to dodge that, the reset can clear the
`mutations.inputs` materialization ledger after `LoginPayload` / `LogoutPayload` have already
been emitted, weakening the distinct-name collision guard and breaking retry semantics. It
also drains the auth declarations after a failed finalize, so the documented recover-in-place
rerun no longer sees the auth fields.

Fix the lifecycle split in the spec: auth declarations need a registry-clear-only clear path,
not the pre-bind input-namespace seam. Either add a distinct registry-clear hook for
declaration ledgers or wire an auth declaration clear beside the mutation/form declaration
clears in `TypeRegistry.clear()`. Then order phase 2.5 as: run the existing pre-bind
materialization reset first, run `bind_auth_mutations()` next, then `bind_mutations()`, then
`bind_form_mutations()`. Auth payloads can use the existing `mutations.inputs` materialization
ledger; auth declarations should not be part of that reset list.

### [P1] `RegisterPayload` cannot come from a concrete class named `DjangoRegisterMutation` under the existing field machinery

Decision 6 repeatedly names the synthesized concrete rider `DjangoRegisterMutation`, while
the user-facing API and DoD require `RegisterInput` / `RegisterPayload`. The input half is
covered: `DjangoMutation.input_type_name()` is an overridable seam. The payload half is not.

Today `django_strawberry_framework/mutations/sets.py::_bind_mutation` calls
`build_payload_type(mutation_cls.__name__, ...)`, and
`django_strawberry_framework/mutations/fields.py::_synthesized_mutation_signature` returns a
lazy ref to `f"{mutation_cls.__name__}Payload"`. There is no payload-name seam. A concrete
class whose `__name__` is `DjangoRegisterMutation` will therefore expose
`DjangoRegisterMutationPayload`, not `RegisterPayload`.

Source grounding:

- `django_strawberry_framework/mutations/sets.py::_bind_mutation #"build_payload_type("` passes `mutation_cls.__name__` as the payload base name.
- `django_strawberry_framework/mutations/fields.py::_synthesized_mutation_signature #"return_annotation = _lazy_ref"` builds the return annotation as `f"{mutation_cls.__name__}Payload"`.
- `django_strawberry_framework/mutations/fields.py::_synthesized_mutation_signature #"data_ann = _lazy_ref"` reads `mutation_cls.input_type_name(meta)` for the input name, so `RegisterInput` has an existing seam; the payload name does not.

Pick one root fix and make the spec explicit. The smallest is to make the internal safe base
private, then synthesize the concrete registered class with `__name__ == "Register"` so the
unchanged machinery emits `RegisterPayload`. If the concrete class really must be named
`DjangoRegisterMutation`, the card must add a payload-name seam to both `_bind_mutation()` and
`DjangoMutationField`; that is broader and should be named as a foundation change, not
implied by "standard machinery."

### [P2] `register_mutation(permission_classes=...)` is per-field API, but the design stores permissions on a cached class with fixed payload names

The spec promises `permission_classes=` on every auth factory and says
`register_mutation()` caches the rider per normalized argument set. For `register`, those
permissions live in `Meta.permission_classes`, so different factory calls with different
permission classes imply different concrete mutation classes. With fixed `RegisterInput` /
`RegisterPayload` names, two such classes collide in the existing materialization ledger:
input generation may reuse a cached shape, but `build_payload_type()` creates a fresh payload
class for each mutation class and `materialize_generated_input_class()` rejects a different
class under an existing name.

Source grounding:

- `django_strawberry_framework/mutations/sets.py::_validate_permission_classes` normalizes `Meta.permission_classes` into the mutation meta snapshot.
- `django_strawberry_framework/mutations/sets.py::DjangoMutation.check_permission #"for permission_class in meta.permission_classes"` reads permissions from that class-level meta snapshot, so permissions are class-local in the existing mutation family.
- `django_strawberry_framework/mutations/fields.py::DjangoMutationField` exposes no field-level permission override; it accepts only `description`, `deprecation_reason`, and `directives`.
- `django_strawberry_framework/utils/inputs.py::materialize_generated_input_class #"A collision against a different class under the same ``name`` raises"` rejects a second distinct payload/input class under the same GraphQL type name. This is the collision that two permission-specialized `Register` classes would hit.

This is not just an edge-case nicety. The factory API invites field-local customization, while
the current `DjangoMutationField` protocol is class-local. State the contract. Options:

- Support one `register_mutation()` declaration per schema/process and raise a
  `ConfigurationError` if a second call uses different permissions.
- Add a field-level permission override to the auth register field rather than encoding the
  permission classes into the mutation class, so one concrete `Register` class and one
  `RegisterPayload` serve every field.
- Add a payload reuse/name seam that intentionally allows same-shape payload reuse across
  permission-specialized classes.

The second option is the cleanest API-wise, but it means `register_mutation()` is no longer a
plain `DjangoMutationField(DjangoRegisterMutation)` wrapper; the spec should own that if it
chooses it.

### [P2] The permission seam for `login`, `logout`, and `current_user` is promised but not actually named

The spec says every auth factory accepts `permission_classes=` and routes it through the same
`check_permission` machinery. `register` can inherit that from `DjangoMutation`. `login`,
`logout`, and `current_user` cannot: they are fixed field factories, not mutation subclasses,
and `django_strawberry_framework/mutations/resolvers.py::authorize_or_raise` assumes a
mutation class with `_mutation_meta`, `_primary_type`, and `check_permission()`.

Source grounding:

- `django_strawberry_framework/mutations/resolvers.py::authorize_or_raise #"mutation_cls().check_permission"` delegates to a mutation-class instance method and later reads `mutation_cls._primary_type` for the authorization error target.
- `django_strawberry_framework/mutations/sets.py::DjangoMutation.check_permission` is the method that loops over `Meta.permission_classes`; fixed auth fields do not inherit it unless the spec adds a small auth permission target.
- `django_strawberry_framework/mutations/sets.py::_validate_permission_classes #"unset_default"` is reusable for the AllowAny default, but it only validates/normalizes the class list. It does not by itself provide a resolver-time runner for non-mutation fields.
- `django_strawberry_framework/utils/permissions.py::request_from_info` is a request extractor only; it does not run `permission_classes`.

Decision 7 also never says how `current_user(permission_classes=...)` behaves, even though
the glossary references and user-facing section say "every auth factory" / "any auth field."
For a query helper, the operation name, `data`, and `instance` values passed to
`has_permission(info, mutation, operation, data, instance)` are load-bearing API: is
`instance` the authenticated user, `None` for anonymous, or never supplied? Does a denied
anonymous `me` return `null` or raise the top-level auth `GraphQLError`?

Pin a concrete helper instead of leaving each resolver to re-spell the loop. A good shape is a
small shared auth permission target/runner that uses `_validate_permission_classes(...,
unset_default=())`, rejects async hooks with the same `SyncMisuseError` recourse, and passes a
documented operation string (`"login"`, `"logout"`, `"current_user"`, `"register"`) plus
`data` / `instance` values. If `current_user` is not meant to be permission-gated, remove it
from the "every factory" language and the "any auth field" error-shape row.

### [P3] The register password handoff between `decode_step` and `write_step` is underspecified

Decision 6 says the decode step pops `password` before delegating to the model decode, and the
write step later runs `validate_password(password, user)` then `set_password(password)`.
`django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync` only passes the
decoded value returned by `decode_step` into `write_step`; it does not pass the original input.

Source grounding:

- `django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync #"decode_step(instance) -> decoded"` documents the seam as `decode_step(instance) -> decoded | list[FieldError]`.
- `django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync #"write_step(instance, decoded) -> saved"` documents the next seam as receiving only `instance` and that decoded value.
- `django_strawberry_framework/mutations/resolvers.py::_model_decode_step #"target = model(**scalar_and_fk_attrs)"` shows why `password` must be removed before delegating to the default model construction path.
- `django_strawberry_framework/mutations/resolvers.py::_model_write_step #"target, m2m_assignments, exclude = decoded"` shows the existing decoded tuple shape that a register-specific tuple can extend explicitly.

So the raw password must be carried deliberately after it is removed from the model attrs. The
spec should say how. Prefer an explicit decoded tuple, e.g. `(user, m2m_assignments, exclude,
raw_password)`, over an implicit closure: it is easier to test, mirrors the existing
`_model_decode_step` contract, and makes "raw password exists only in memory, never on the
model instance" auditable. Keep the sync and async plaintext-never-persisted tests, but add a
unit assertion that the model decode never receives `password` in `scalar_and_fk_attrs`.

### [P3] The auth test plan should restate the repo's first-line seed-helper rule

The repo instructions require the first line of every catalog/auth test to be
`seed_data(N)` or `create_users(N)` from `apps.products.services`, with no hand-rolled
`User` setup outside seed-helper tests. The spec's live auth plan uses `create_users()` for
login cases, but the register / anonymous-`me` cases are written as if they can start from an
empty database.

Source grounding:

- The thread-level `AGENTS.md` instructions say: "First line of every catalog/auth test: seed_data(N) or create_users(N) from apps.products.services; never hand-roll Category/Item/Property/Entry/User".
- `examples/fakeshop/apps/products/services.py::create_users` is the existing seed helper for auth users and is already used across `examples/fakeshop/test_query/test_products_api.py`.
- `docs/spec-040-auth_mutations-0_0_13.md #"register → login → `me` → logout round trip"` describes live auth tests but does not restate the first-line seed-helper rule for the new auth test module.

Add a short test-plan rule: every `examples/fakeshop/test_query/test_auth_api.py` test starts
with `create_users(N)` even when the behavior under test creates a fresh account through the
GraphQL `register` mutation. That keeps the new auth tests aligned with the standing test
placement contract without weakening the live coverage.

## Verification

- Ran `uv run python scripts/check_spec_glossary.py --spec docs/spec-040-auth_mutations-0_0_13.md`: `OK: 53 terms`.
- Confirmed Django's default fakeshop user model has `USERNAME_FIELD == "username"` and
  `REQUIRED_FIELDS == ["email"]`, so the `RegisterInput { username email password }` example
  is consistent.
- Re-read the cited source symbols while editing this feedback pass; the findings above now
  carry the grounding claims inline.
- No pytest run; this was a design/spec review.
