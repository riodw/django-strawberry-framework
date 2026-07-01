# Review feedback - `spec-040-auth_mutations-0_0_13.md`

Reviewed against the shipped `036` mutation foundation the spec says `register`
rides "unchanged" — every load-bearing reuse claim was checked against the actual
source (`mutations/resolvers.py`, `mutations/sets.py`, `utils/permissions.py`), not
taken on the spec's word. The spec is strong: the envelope reuse, the AllowAny
inversion, the `get_queryset`-skip reasoning, and the bind lifecycle all hold up.
The findings below are the places where a reuse claim does not match the code it
names, or where a stated DoD item cannot be implemented as written.

## Findings

### [P1] The `register` password write-step has no seam in the `036` pipeline, and the default create pipeline persists the raw password

Decision 6 describes `register` as a thin `DjangoMutation` rider: "the `036`
foundation unchanged" with "no new pipeline"
(`docs/spec-040-auth_mutations-0_0_13.md #"foundation unchanged"`;
`docs/spec-040-auth_mutations-0_0_13.md #"one write-step wrapper on the 036 skeleton"`).
The password step is described as happening inside "the resolver" — pop `password`
"before instance construction", `validate_password(password, user)`, then
`set_password` before `full_clean()` / `save()`
(`docs/spec-040-auth_mutations-0_0_13.md #"before instance construction"`;
`docs/spec-040-auth_mutations-0_0_13.md #"set_password"`). But the spec never names
which seam carries that step, and the actual `036` create pipeline has none.

`_run_pipeline_sync` hard-wires the create/update steps as **module-level
functions**, not subclass-overridable hooks:
`django_strawberry_framework/mutations/resolvers.py::_run_pipeline_sync #"write_step=lambda instance, decoded: _model_write_step"`.
`_model_decode_step` constructs `model(**scalar_and_fk_attrs)` with `password` as a
plain attribute
(`django_strawberry_framework/mutations/resolvers.py::_model_decode_step #"target = model(**scalar_and_fk_attrs)"`),
and `_model_write_step` runs `full_clean` → `save` with no `set_password`
(`django_strawberry_framework/mutations/resolvers.py::_model_write_step #"write_error = save_or_field_errors(target.save)"`).
`DjangoMutation` exposes no `perform_create` / write hook — the only per-subclass
resolver seam is `resolve_sync` / `resolve_async`
(`django_strawberry_framework/mutations/sets.py::DjangoMutation #"def resolve_sync"`),
which is exactly what the form and serializer *flavors* override to supply their own
decode/write steps.

So the literal "rides `DjangoMutation` unchanged" reading is a security defect: with
the default pipeline, `RegisterInput.password` is set via `model(password=<raw>)`,
`full_clean` only checks the 128-char `max_length`, and `save()` stores the
**plaintext password**. Making `register` safe *requires* overriding
`resolve_sync` **and** `resolve_async` and re-supplying a custom decode step (pop
`password`) plus a custom write step (`validate_password` → `set_password` →
`full_clean` → `save`) over the shared `run_write_pipeline_sync` skeleton — i.e.
`register` is structurally a fourth decode/write-step pair; the genuine reuse is the
column converter + input generator + skeleton, not the pipeline body.

Pin the seam in Decision 6: state that `DjangoRegisterMutation` overrides
`resolve_sync` / `resolve_async`, reuses `run_write_pipeline_sync` with a custom
`write_step` (and decode step) for the password work, and that `036` provides no
per-instance write hook to reuse. Correct the "no new pipeline / foundation
unchanged" framing to "reuses the skeleton via a custom write step." Keep the
`plaintext-never-persisted` test, and require it on **both** the sync and async
paths (the async twin is a separate override and can regress independently).

### [P2] Decision 8's bind-validation is unreachable for `register`; its no-user-type error is a different, generic message raised earlier by `bind_mutations()`

Decision 8 and the Slice 1 checklist promise that a declared `login` **or
`current_user` / `register`** with no registered primary `DjangoType` for the user
model raises a `ConfigurationError` naming the auth-specific fix — "declare a
`DjangoType` with `Meta.model = get_user_model()`; mark it `Meta.primary = True`…"
(`docs/spec-040-auth_mutations-0_0_13.md #"or current_user / register"`;
`docs/spec-040-auth_mutations-0_0_13.md #"mark it"`).

But `register` is a `DjangoMutation`, bound by `bind_mutations()`, and Decision 9
places `bind_auth_mutations()` **after** it
(`docs/spec-040-auth_mutations-0_0_13.md #"after bind_mutations"`). `bind_mutations()`
resolves the payload's primary type first, and a missing user type raises the
**generic** message there, before `bind_auth_mutations()` runs:
`django_strawberry_framework/mutations/sets.py::_resolve_primary_type #"which has no registered DjangoType"`
— "DjangoMutation `DjangoRegisterMutation` targets `User`, which has no registered
DjangoType; … Declare a DjangoType for `User`." That names the raw model class (a
swapped `AUTH_USER_MODEL` yields whatever the concrete class is called), not
`get_user_model()` / `Meta.primary`, and never reaches the auth-specific check.

So the `register` arm of the Decision 8 / Slice 1 DoD item cannot be implemented as
written — either it is dead (the generic error wins) or it would have to duplicate a
check `bind_mutations()` already performs. Reconcile: either (a) scope Decision 8's
auth-specific validation to `login` / `current_user` only and document that
`register` surfaces the generic `bind_mutations()` no-primary error, or (b) have
`bind_auth_mutations()` (or a pre-`bind_mutations` hook) validate the user primary
type for all three with the auth message before `bind_mutations()` can raise. Add a
test pinning the *exact* error and message a no-`UserType` schema produces for
`register` specifically, distinct from `login`.

### [P2] The cached `DjangoRegisterMutation` rider can silently drop out of the schema on a second finalize (reload idempotence)

Decision 6 says the rider is "created lazily on first factory call"
(`docs/spec-040-auth_mutations-0_0_13.md #"lazily on first factory call"`) and
"synthesizes (once, cached per normalized argument set)"
(`docs/spec-040-auth_mutations-0_0_13.md #"cached per normalized argument set"`).
Decision 9 wires a `register_subsystem_clear` row for the **auth** declaration
ledger — but the rider rides the **mutation** ledger
(`register_mutation`), which `registry.clear()` empties via
`clear_mutation_registry`
(`django_strawberry_framework/mutations/sets.py::make_declaration_registry #"def clear"`).

The spec does not say how the per-args class cache interacts with a
`registry.clear()` + re-finalize. If the factory registers the rider into the
mutation ledger only at first *synthesis* and later returns the cached class without
re-calling `register_mutation`, then on the second finalize (ledger cleared, the
consumer re-runs `register = register_mutation()`) the rider is never re-appended and
`register` **silently disappears from the schema** — while `login` / `logout` (auth
ledger, explicitly cleared + re-declared) survive. This is precisely the reload path
the suite's autouse complete-reload fixtures exercise, so it would surface as an
order-dependent "register missing" flake, not a clean failure.

Specify that every `register_mutation()` call re-registers the (cached) rider into
the mutation ledger — `register_mutation` already dedups by identity
(`#"if declaration_cls not in store"`), so a live ledger is a no-op and a cleared one
re-appends — or that the per-args cache is reset on `registry.clear()`. Add a
reload-idempotence test: finalize → `registry.clear()` → re-declare → finalize again,
asserting `register` is still present in the second schema.

### [P3] A user-typed payload makes the consumer's `UserType` field selection the auth read surface, but the spec never cautions against exposing `password` / privilege columns

`login`, `register`, and `me` all type their user in the consumer's own primary
`DjangoType` (Decision 8). The register safety story is entirely about the *input*
side — narrowing `Meta.fields` so privilege columns are structurally unreachable
(`docs/spec-040-auth_mutations-0_0_13.md #"privilege escalation is structurally"`).
But the *output* side is whatever the consumer put in `UserType.fields`. A consumer
who writes `fields = "__all__"` (or lists `password`, `is_superuser`, `last_login`)
gets the password **hash** and privilege flags surfaced through `LoginPayload.node`,
`RegisterPayload.node`, and `me` — on the auth surface specifically.

The example UserType is safe (`fields = ("id", "username", "email")`), but nothing
warns the reader. Add a caution to Decision 8 and the `Auth mutations` GLOSSARY entry:
the user primary type's field selection *is* the authenticated read surface; exclude
`password` and privilege columns. (Doc-only, like the `038` file-clearing scope note
— no code.)

### [P3] `login` returns `authenticate()`'s user directly (no optimizer re-fetch), which is asymmetric with `register`, and Decision 5 conflates "skip visibility" with "skip re-fetch"

Decision 5 says the login payload's user is "the object `authenticate()` returned …
not a visibility-scoped lookup," and calls this the "Same posture as `current_user`
… and the register re-fetch"
(`docs/spec-040-auth_mutations-0_0_13.md #"not a visibility-scoped lookup"`;
`docs/spec-040-auth_mutations-0_0_13.md #"and the register re-fetch"`). But those are
two different things. `register` re-fetches by pk through
`refetch_optimized` (Decision 6, `#"refetch_optimized"`), which is what applies the
spec-035 G2 optimizer plan
(`django_strawberry_framework/mutations/resolvers.py::refetch_optimized #"apply_connection_optimization"`).
`login` returns the raw `authenticate()` instance with **no** such re-fetch — so the
two payload nodes are not the same posture: `login { node { <relations> } }` is
unplanned (N+1, and a different Strictness-mode footprint) while `register`'s node is
optimizer-planned.

This is defensible (the login actor is themselves, and a re-fetch costs a query), but
the spec should say it plainly rather than lumping `login` in with "the register
re-fetch." Clarify Decision 5: `login` skips **both** visibility and the re-fetch and
returns the `authenticate()` instance directly, so its node is not optimizer-planned;
if a planned login node is wanted, note the by-pk-no-visibility `refetch_optimized`
call is available (the same one register uses). No test change required if the raw
instance is intended; add an SDL/behavior note either way.

## Verification

This is a design review of an unimplemented spec; no code changed, so `ruff` /
`git diff --check` do not apply. I grounded the reuse claims against the named source
rather than running the test suite:

- **Confirmed accurate:** `refetch_optimized` is by-pk **without** the visibility
  filter (`mutations/resolvers.py::refetch_optimized`); `_validate_permission_classes`
  preserves an explicit `[]` as AllowAny and only applies `unset_default` for `None`
  (`mutations/sets.py::_validate_permission_classes #"An explicit"`), so the
  AllowAny-default design is feasible; `request_from_info(info, *, family_label=...)`
  exists with that signature (`utils/permissions.py`); `build_payload_type(...,
  object_type=None)` and `payload_object_slot(primary)` exist as cited.
- **Contradicted / underspecified (the findings above):** no per-subclass write hook
  in the create pipeline (P1); `_resolve_primary_type`'s generic no-DjangoType error
  pre-empts the auth-specific one for `register` (P2); mutation-ledger reload
  interaction with the rider cache (P2).

Recommended before finalizing: run
`uv run python scripts/check_spec_glossary.py --spec docs/spec-040-auth_mutations-0_0_13.md`
(I could not run it here — local tooling outage — so the `OK: <N> terms` gate in DoD
item 1 is unverified).
