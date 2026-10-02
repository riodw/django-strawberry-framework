# Rationale companion: spec-039 (DRF serializer mutations — `SerializerMutation`)

Companion to [`docs/SPECS/spec-039-serializer_mutations-0_0_13.md`][spec-039]. It
carries the reasons behind that spec's contract: each Decision's justification, the
alternatives it rejected and why, the reasoning behind the graphene-django keys the
flavor does not adopt, and the reasons behind the shipped improvement contracts. The
spec carries the contract; this file carries why the code is shaped that way.

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-039-d1].

### Justification

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in
  [`docs/SPECS/NEXT.md`][next] bakes the card's NNN (`039`) and target patch
  (`0_0_13`) into the filename.
- The topic slug is `serializer_mutations` — short, snake-case, and naming the
  subsystem capability.

### Alternatives considered (and rejected)

- **An unstructured `docs/spec-serializer_mutations.md`.** Rejected: the structured
  filename is the convention every spec follows.
- **Topic slug `serializers` / `drf` / `rest_framework`.** Rejected: `serializers`
  collides conceptually with the DRF `serializers` module name; `drf` / `rest_framework`
  name the dependency, not the subsystem capability (the mutation flavor).

## Decision 2 — Card-scope boundary: the serializer flavor ships; auth stays out; the frozen `036` contracts and the `038` factory are reused unchanged

Spec: [Decision 2 — Card-scope boundary: the serializer flavor ships; auth stays out; the frozen `036` contracts and the `038` factory are reused unchanged][spec-039-d2].

### Justification

Auth is a separate subsystem with its own spec ([`spec-040`][spec-040]); folding it into
the serializer flavor would bloat it exactly as [`START.md`][start]'s scope-creep rule
warns. The foundation ([`spec-036`][spec-036]) and the form-flavor precedent
([`spec-038`][spec-038]) carry the shared machinery; the serializer flavor's job is the
serializer-specific generation + pipeline on top of them.

### Alternatives considered (and rejected)

- **Ship auth mutations in the same subsystem** (they also reuse the envelope).
  Rejected: auth has a distinct surface (`login` / `logout` / `register` +
  `current_user`, composing with `django.contrib.auth`) under
  `django_strawberry_framework.auth`, not a serializer-flavor concern.
- **A serializer-specific fork of `FieldError`.** Rejected: one envelope across every
  flavor is the client contract. The envelope grows only additively, in the shared
  [`mutations/inputs.py`][mutations-inputs] type, so all three write flavors gain a
  member together (the `codes` and `path` members are that case).

## Decision 3 — `class Meta` surface, not graphene's `MutationOptions`

Spec: [Decision 3 — `class Meta` surface, not graphene's `MutationOptions`][spec-039-d3].

### Justification

This is the package's defining surface contract ([`START.md`][start] "Meta classes on
every consumer surface"). The [`spec-036`][spec-036]
[`DjangoMutation`][glossary-djangomutation] base and the [`spec-038`][spec-038] form
bases established the nested-`Meta` mutation shape; the serializer flavor is uniform
with them. The *capabilities* of graphene-django's `SerializerMutation` are borrowed at
the outcome level; the `MutationOptions` / `ClientIDMutation` mechanism is not.
[`GOAL.md`][goal]'s DRF-migration example declares the flavor on the
`SerializerMutation` base with a nested `class Meta`.

### Alternatives considered (and rejected)

- **graphene's `__init_subclass_with_meta__` keyword options.** Rejected: it is the
  metaclass-options surface the nested `class Meta` replaces; it also fragments the
  declaration shape away from [`DjangoMutation`][glossary-djangomutation].
- **A `@serializer_mutation(serializer_class=…)` decorator.** Rejected: a decorator on
  a consumer class is exactly the shape [`START.md`][start] forbids.

## Decision 4 — Module and test locations: `rest_framework/` subpackage mirroring `forms/`

Spec: [Decision 4 — Module and test locations: `rest_framework/` subpackage mirroring `forms/`][spec-039-d4].

### Justification

The [`forms/`][forms-sets] subpackage ([`spec-038`][spec-038] Decision 4) is the proven
shape for a flavor reusing the mutation base, and `rest_framework/` is its structural
twin (a converter + an input generator + a `DjangoMutation` subclass + a resolver
pipeline). A separate subpackage keeps the serializer-specific generation + pipeline
distinct and behind one DRF soft-import boundary
([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
The directory name matches graphene-django's own `rest_framework/` subpackage.

The name has one cost: `django_strawberry_framework.rest_framework` shares its leaf name
with DRF's top-level `rest_framework` package, so the DRF-absent test evicts **both**
`rest_framework*` **and** `django_strawberry_framework.rest_framework*` from
`sys.modules` ([`tests/rest_framework/test_soft_dependency.py`][test-soft-dependency-rf]).
The double eviction traces to this naming choice, not to an accident of the guard.

### Alternatives considered (and rejected)

- **Fold the serializer base into [`mutations/`][mutations-sets] or
  [`forms/`][forms-sets].** Rejected: the serializer-field converter is a distinct
  concern, and the DRF soft-import boundary wants its own module wall — one subpackage
  per flavor keeps each extension point separable.
- **A flat `rest_framework.py` module.** Rejected: the surface is a converter + an
  input generator + a base + a resolver pipeline (plus the frozen hook context) — a
  subpackage matches it.
- **Name it `serializers/` instead of `rest_framework/`.** Rejected: `rest_framework/`
  matches graphene-django's layout and names the dependency boundary the soft-import
  guard wraps.

## Decision 5 — Public surface: `SerializerMutation` exported from the root, the `038`-generalized factory reused

Spec: [Decision 5 — Public surface: `SerializerMutation` exported from the root, the `038`-generalized factory reused][spec-039-d5].

### Justification

Reusing the field factory + error type rather than a parallel factory keeps one
exposure idiom and one error contract across the write family. `SerializerMutation` is
the one name a consumer must import to declare a mutation; the other six lazy exports are
the surfaces the improvement contracts and the hook contract expose. All seven stay out
of `__all__` because a star import binds every `__all__` name through the root
`__getattr__`, so a DRF-guarded name there would make a star import raise for a
DRF-absent consumer who never writes a serializer mutation.

### Alternatives considered (and rejected)

- **A net-new `DjangoSerializerMutationField` factory.** Rejected: the generic
  [`DjangoMutationField`][glossary-djangomutationfield] already exposes any
  mutation-family member through its duck-typed target check and `resolve_sync` /
  `resolve_async` / `input_type_name` dispatch; a parallel factory would duplicate the
  dispatch + input-ref logic for no gain.
- **Exporting from a `django_strawberry_framework.rest_framework` namespace only.**
  Rejected: the symbol is used inside schema modules alongside root-exported
  [`DjangoMutation`][glossary-djangomutation] / [`DjangoModelFormMutation`][glossary-djangomodelformmutation],
  so it belongs at the root next to its sibling flavor bases — guarded so the root
  import survives DRF's absence
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).

## Decision 6 — Base-class strategy: `SerializerMutation` rides the `DjangoMutation` base, `ModelSerializer`-driven

Spec: [Decision 6 — Base-class strategy: `SerializerMutation` rides the `DjangoMutation` base, `ModelSerializer`-driven][spec-039-d6].

### Justification

This is the shape [`DjangoModelFormMutation`][glossary-djangomodelformmutation] uses:
overriding the [`_resolve_model`][spec-036] seam to return
`Meta.serializer_class.Meta.model` reuses permission, locate, re-fetch, payload and bind,
and keeps the serializer flavor uniform with the form flavor. A **dedicated
[`SerializerMutation`][glossary-serializermutation] base** (rather than teaching
[`DjangoMutation`][glossary-djangomutation] itself to detect `serializer_class`) also
buys the strongest migration ergonomics ([`GOAL.md`][goal]'s graphene-django migration
criterion): a graphene-django consumer already subclasses `SerializerMutation`, so
that declaration carries over **by name**.

The input-namespace clear registers through `register_subsystem_clear` as a zero-argument
callable with a stable `owner`, not as a string reference resolved later: importing the
owner to register makes a rename fail loudly at import, where a string row would leave
state silently uncleared. The soft-dependency property follows from the same shape — only
an imported owner can register, so a DRF-absent build registers nothing and needs no
import-guarded clear.

### Alternatives considered (and rejected)

- **`DjangoMutation` itself detects `Meta.serializer_class`** (no dedicated
  `SerializerMutation` base). Rejected: it forfeits the by-name graphene-django
  carry-over (a migrant's `class FooMutation(SerializerMutation)` would have to become
  `(DjangoMutation)`), and folds serializer-specific `Meta` validation / `build_input`
  branching into the model-driven base instead of isolating it in a subclass. The base
  is reused **by subclassing**, not by overloading one class with both flavors.
- **A standalone `SerializerMutation` not subclassing `DjangoMutation`** (its own
  metaclass + registry + bind, the model-less [`DjangoFormMutation`][glossary-djangoformmutation]
  shape). Rejected for the `ModelSerializer`-driven contract: it would re-implement the
  permission / locate / re-fetch / payload the base already provides; the model-less
  sibling shape is the one a plain-`Serializer` flavor would take.
- **Supporting both `ModelSerializer` and plain `Serializer`** (graphene's single
  `SerializerMutation` handles both via `model_class=None`). Rejected: it doubles the
  surface (two payload shapes, two bind paths) for a rare case; the form flavor likewise
  splits the model-backed and model-less cases into two bases.

## Decision 7 — Serializer-field → Strawberry input mapping: the serializer is the input source of truth

Spec: [Decision 7 — Serializer-field → Strawberry input mapping: the serializer is the input source of truth][spec-039-d7].

### Justification

Deriving the input from the serializer's fields is the only way a serializer's declared /
renamed / extra fields reach the write surface; reusing the read-side converters keeps
the symmetric wire contract; the fail-loud converter matches the package's own
[`forms/converter.py`][forms-converter] posture and is mandated by [`GOAL.md`][goal]'s
non-goal against silently weakening rich relations into generic placeholders; the
shape-identity + materialize-before-`Schema` discipline is the set-family lifecycle.

The finer rules each serve one invariant — the generated input describes exactly the shape
the runtime serializer validates:

- **Nullability.** A field is nullable when it is `allow_null=True` **or** optional, with a
  `strawberry.UNSET` default. A GraphQL input field that is neither nullable nor defaulted
  is required, so an omittable non-null field would be unsatisfiable; the framework never
  fabricates a GraphQL default instead.
- **Relations.** Only `PrimaryKeyRelatedField` (and `ManyRelatedField` over one) is
  accepted, because the relation input decodes to a primary key; a `SlugRelatedField` /
  `HyperlinkedRelatedField` / custom `RelatedField` expects another representation, so
  mapping it would accept ids the serializer then misreads. A serializer relation whose
  cardinality disagrees with its model relation (`many=True` over a foreign key, or the
  inverse) is rejected, since the schema would emit one id where DRF validates a list.
- **Descriptor identity.** `rest_framework/inputs.py::SerializerInputShape` keys the cache
  on every value that shapes the emitted type (field specs, post-widening annotations,
  descriptions, effective requiredness, `optional_fields`). The `036` / `038` name-only
  key is insufficient here: `optional_fields` changes requiredness without changing the
  name set, and the schema-time hook can return same-named fields with different classes,
  `source` or kind.
- **Canonical naming.** The canonical `<Serializer>Input` is granted only to the shape the
  default no-arg discovery produces (`_default_full_shape_identity`); a hook-returned
  "full" shape that differs takes a descriptor-derived name, so two distinct descriptors
  never collide on the canonical name at materialize.
- **Writable `source` uniqueness** spans the whole write surface (inputs **and**
  `Meta.injected_fields`), because DRF resolves a source collision last-write-wins and an
  injected value could otherwise silently replace the client's.

### Alternatives considered (and rejected)

- **Reuse the `036` model-column generator** (derive the input from `Meta.model`, not
  the serializer). Rejected: a serializer may declare fields a model lacks, rename
  fields, mark columns read-only, or narrow — the input must be the serializer's
  contract, exactly the `038` form-derived precedent.
- **graphene's `singledispatch` + `Field → String` catch-all.** Rejected: the
  catch-all shadows the raise so an unmapped field silently becomes `String`; the
  fail-loud MRO walk is the package's settled discipline.
- **Build a serializer-derived output type** (`is_input=False`). Rejected: the uniform
  `node` / `result` slot is the one cross-flavor output contract; a serializer-derived
  output would fork it.

## Decision 8 — Resolver pipeline: instantiate → `is_valid()` → `serializer.errors` → `save()` → optimizer re-fetch → payload

Spec: [Decision 8 — Resolver pipeline: instantiate → `is_valid()` → `serializer.errors` → `save()` → optimizer re-fetch → payload][spec-039-d8].

### Justification

`serializer.is_valid()` / `serializer.save()` is the DRF-native validation + write
entry; routing `serializer.errors` into the envelope (rather than raising) is the
graphene-django / cross-flavor contract; the relation-visibility decode is the package
security invariant the `036` / `038` mutations enforce; the single `atomic()` / single
`sync_to_async` boundary is the settled async-safety contract.

The shared skeleton `mutations/resolvers.py::run_write_pipeline_sync` serves every write
flavor through per-variation callback seams (`decode_step`, `write_step`, delete's
`tail_step`) rather than a per-flavor copy, so the **locate → authorize → decode** security
ordering is single-sited for all of them.

Hooks never own `data` or `instance`. A hook holding the live located row could mutate
the row that had just been authorized, and DRF's `update()` saves the whole instance, so
hooks receive the frozen `SerializerHookContext` / `UploadMetadata` view instead. Three
choices inside that contract each reject a plausible weaker alternative:

- **Reserved returns are checked by omission sentinel + object identity, never deep
  equality.** A deep `!=` recurses on deep valid payloads, and a `pop(..., None)` default
  conflates an explicit `None` with omission. A returned `data` must be omitted or the
  exact frozen object; any returned `instance` key is refused.
- **The alias guard performs no read/write classification.** A lexical test is bypassable
  (leading SQL comments, `EXPLAIN ANALYZE`, write-capable functions called through
  `SELECT`), so `utils/write_transaction.py::pipeline_alias_guard` rejects every statement
  on a non-pinned connection before it executes, and the authorization phase's exception
  is contained by a **database-enforced** read-only transaction rather than by inspecting
  SQL. Post-hoc detection cannot roll back a write that already escaped.
- **The freeze fails closed on an opaque leaf.** Aliasing a possibly-mutable value a hook
  could reach back through reopens the bypass the frozen view closes.

The save runs in its own savepoint and maps `DRFValidationError`, Django
`ValidationError` and `IntegrityError` to the envelope outside that atomic block, through
the shared `utils/errors.py::integrity_error_field_errors` leaf rather than the `036`
`save_or_field_errors` wrapper: the savepoint rolls back a custom `save()` that wrote rows
and then raised before the error is converted, and catching outside the block is what
clears the connection's `needs_rollback` flag. `_pin_validator_querysets` shallow-copies
each queryset-backed validator per serializer instance before pinning it to the write
alias, because DRF shares validator objects across serializer instances and concurrent
requests would otherwise reroute one another's validators.
`_assert_runtime_write_source_ownership` runs on the instantiated serializer because
schema discovery cannot see a context-dependent `get_fields()`.

### Alternatives considered (and rejected)

- **Skip `is_valid()` and rely on the model's `full_clean()`.** Rejected: it loses the
  serializer's `validate_<field>` / `validate()` logic — the whole point of the
  flavor.
- **Reconstruct the full payload for `update` (the `038` shape).** Rejected: DRF's
  `partial=True` is the native partial-update mechanism and is cleaner than a
  `model_to_dict` overlay; reconstruction is a form-flavor necessity, not a serializer
  one.
- **Pass relation ids straight to the serializer without the visibility decode.**
  Rejected: a `PrimaryKeyRelatedField`'s default queryset is `Model.objects.all()`
  (not request-scoped), so a hidden target would be writable — the package's
  relation-visibility invariant requires the decode-time `get_queryset` check.

## Decision 9 — Optimizer composition: the `ModelSerializer` payload re-fetch rides the `spec-036` G2 path

Spec: [Decision 9 — Optimizer composition: the `ModelSerializer` payload re-fetch rides the `spec-036` G2 path][spec-039-d9].

### Justification

The `036` re-fetch path (`mutations/resolvers.py::refetch_optimized`) and the
[`spec-035`][spec-035] G2 gate (keep `select_related` / `prefetch_related`, no
`.only(...)` under a mutation) exist for exactly this; reusing them gives the serializer
flavor optimizer-composed returns for free, identical to the form flavor.

### Alternatives considered (and rejected)

- **Return `serializer.data` / `serializer.instance` without re-fetching.** Rejected:
  `serializer.instance` after `save()` has no response-selection relations loaded, so a
  relation in the response selection N+1s; the re-fetch is what makes the response
  planable, and `serializer.data` is the serializer's representation, not the
  `DjangoType` the uniform slot returns.

## Decision 10 — Operations: `create` / `update`, no serializer `delete`

Spec: [Decision 10 — Operations: `create` / `update`, no serializer `delete`][spec-039-d10].

### Justification

`create` / `update` are the operations a serializer expresses; `delete` has no serializer
step; one mutation per operation is the package's settled shape (the `036` / `038`
precedent). `Meta.operation` is mandatory because the model-driven and `ModelForm` bases
already require it; defaulting it for the serializer flavor alone would make it the only
write flavor that infers the operation.

### Alternatives considered (and rejected)

- **Adopt graphene's `model_operations` runtime dispatch.** Rejected: it fragments the
  declaration shape away from [`DjangoMutation`][glossary-djangomutation] /
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation] (one mutation per
  operation), and the single-string `Meta.operation` is the more `class Meta`-idiomatic
  selector.
- **Add a serializer `delete`.** Rejected: DRF serializers have no delete pipeline;
  the model-driven `DjangoMutation` `delete` already covers it.

## Decision 11 — Write authorization: reuse the `036` seam (`DjangoModelPermission` for the `ModelSerializer`)

Spec: [Decision 11 — Write authorization: reuse the `036` seam (`DjangoModelPermission` for the `ModelSerializer`)][spec-039-d11].

### Justification

The `036` seam is shared by every write flavor; the `ModelSerializer`'s model resolves
the default [`DjangoModelPermission`][glossary-djangomodelpermission] through the
`_resolve_model` override, so the serializer flavor is safe-by-default with no new
permission machinery, and `check_permission` stays the escape hatch.

### Alternatives considered (and rejected)

- **Use DRF's own `permission_classes` / `DEFAULT_PERMISSION_CLASSES`.** Rejected: the
  package's write-auth is a first-class, `class Meta`-driven contract shared across
  flavors; threading DRF's request-level permissions through a GraphQL mutation would
  fork the contract and couple write-auth to DRF's view machinery (which is absent — a
  serializer is used here without a DRF view).

## Decision 12 — Soft `djangorestframework` dependency and the 100%-coverage strategy

Spec: [Decision 12 — Soft `djangorestframework` dependency and the 100%-coverage strategy][spec-039-d12].

### Justification

This is the package's pattern for a soft dependency under a 100%-coverage gate, shared
with `channels` and `debug_toolbar`: out of runtime deps, in the dev group, a raising
guard over `utils/imports.py::require_optional_module`, and the absent path simulated. It
also matches graphene-django's own optional `rest_framework` dependency.

The absent path is simulated with the `sys.modules[name] = None` sentinel
(`tests/_soft_dependency.py::simulated_absence`), not a `builtins.__import__` patch: the
guards call `importlib.import_module`, which consults `sys.modules` directly and never
calls `__import__`, so the patch would leave the guard unreached and the test would pass
without exercising anything. The root-import half runs in a fresh subprocess, which can
catch a newly introduced eager DRF import at the package root that a warm process cannot.
The root `__getattr__` does not memoize, so an earlier DRF-present access cannot leave the
symbol bound and mask the missing-dependency path.

### Alternatives considered (and rejected)

- **Add DRF to `[project].dependencies`.** Rejected: it forces every consumer to
  install DRF even if they never write a serializer mutation; package import must
  succeed without DRF installed.
- **`# pragma: no cover` the whole `rest_framework/` subpackage.** Rejected: it would
  ship untested write-side code; the dev-group dependency lets the suite cover it for
  real, which is the point of the 100% gate.
- **Skip the absent-path test.** Rejected: the guard's raise is a reachable line under
  the 100% gate; simulated absence covers it.

## Decision 13 — Live coverage: products grows a `ModelSerializer` mutation

Spec: [Decision 13 — Live coverage: products grows a `ModelSerializer` mutation][spec-039-d13].

### Justification

The live-first rule
([`test_query/README.md`][test-query-readme] #"Live-first, both verdicts, and the must-not.")
makes live the **first** home for any reachable line, so the serializer resolver is
covered by real `/graphql/` requests. Products is the canonical write-surface example
(the `036` / `038` precedent) and already carries the `unique_item_per_category`
constraint, the seeded fixtures, and the [`Item.attachment`][products-models] `FileField`
the `Upload` path needs. DRF being a dev-group dependency
([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy))
keeps it present in the test context.

### Alternatives considered (and rejected)

- **Cover the resolver's reachable branches in `tests/rest_framework/`.** Rejected: it
  violates the live-first rule;
  [`tests/rest_framework/test_resolvers.py`][test-rest-framework] keeps only the residue a
  live query cannot drive.
- **A dedicated `test_serializer_api.py` against a fresh app.** Rejected: products
  already carries the constraint and the seeded fixtures; extending
  [`test_products_api.py`][test-products-api] matches the `036` / `038` precedent.
- **Host the headline surface in the `library` app.** Rejected: products is the canonical
  write-surface example and already hosts the model-driven and form mutations. The
  library app carries only the shapes products cannot (a non-Relay target, a raw-pk M2M,
  a nested write, a schema-hook serializer), so those rows sit in
  `test_query/test_library_api.py`.

## Decision 14 — Version bumps are owned by the joint `0.0.13` cut

Spec: [Decision 14 — Version bumps are owned by the joint `0.0.13` cut][spec-039-d14].

### Justification

Per [`docs/SPECS/NEXT.md`][next], when several cards target one patch version the bump
belongs to the joint cut, not to any one card's spec. `039` and `040` both shipped in
`0.0.13`.

## Risks and open questions

- **Model-less plain `Serializer`.** Not supported: a model-less serializer has no object
  for the `node` / `result` slot, and `DjangoMutation`'s base requires a resolvable model
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).
  A serializer-validated non-model write would take the
  [`DjangoFormMutation`][glossary-djangoformmutation] shape (its own metaclass +
  `{ ok, errors }` payload + bind) rather than weakening the `ModelSerializer` contract.
- **graphene's `Meta.model_operations`.** Not adopted
  ([Decision 10](#decision-10--operations-create--update-no-serializer-delete)). This is
  where a graphene-django serializer-mutation migrant feels the most friction: one
  auto-dispatching `model_operations = ["create", "update"]` mutation becomes **two**
  package mutations, each with an `operation` key their old code never had — a
  declaration-shape change, where the base-class swap
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven))
  carries over by name. An alias that expands `Meta.model_operations` into the
  per-operation mutations at class creation would soften it while keeping one mutation
  per operation internally; it is not built.
- **graphene's `Meta.lookup_field`.** Not adopted. An `update` row is located by its
  `id:` (a `GlobalID` for a Relay primary, a raw pk otherwise), decoded server-side and
  run through the target `get_queryset`
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)),
  so a hidden row is not-found rather than an existence leak, uniform with the model and
  form flavors; graphene's `get_object_or_404` on an arbitrary column has no visibility
  step.
- **graphene's "dual-purposed for inputs and outputs" converter.** The converter is
  **input-directed**; the mutation output is the primary [`DjangoType`][glossary-djangotype]
  in the uniform `node` / `result` slot
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)),
  the same way `038` declines `Meta.return_field_name`. The `is_input` parameter is
  accepted and ignored with no `if not is_input:` branch, so it adds no uncovered line
  under `fail_under = 100`. A serializer-shaped output type would be a separate surface.
- **DRF version floor.** The binding constraint is not serializer-API availability but
  that the dev-group DRF imports and runs **warning-free across the CI matrix**:
  [`django.yml`][django-workflow] runs the newest Python + Django cell under
  [`pytest.ini`][pytest-ini]'s `filterwarnings = error`, so any deprecation DRF emits there
  is a hard failure, and DRF's Django support lags Django releases.
  [`pytest.ini`][pytest-ini] sanctions only a targeted `ignore::` for a third-party
  warning, never a blanket one. The floor value itself is recorded in
  [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy).
- **`serializer.save()` create-vs-update + M2M.** `serializer.save()` runs `create()` (no
  instance) / `update()` (with instance) and assigns M2M within that call, all inside the
  one `transaction.atomic()` — no separate M2M step (the DRF idiom). A consumer serializer
  that needs the saved instance before its M2M rows overrides `create()` / `update()`.
- **`rest_framework` in the example's `INSTALLED_APPS`.** Not installed: the products
  `ItemSerializer` is a flat `ModelSerializer`, and DRF serializers validate and save
  without the app registry. A serializer reaching app-registry-only DRF machinery would
  need it.

## Improvements over graphene-django's DRF integration

The spec states each improvement's contract. The reasons that are not visible from the
contract alone:

- **Row locking defaults on.** `Meta.select_for_update` defaults to `True` for every
  model-backed flavor through one shared validator
  (`mutations/sets.py::validate_select_for_update`): locked writes are the safe posture,
  so an opt-*out* is the shape that fails safe when a consumer says nothing. A per-flavor
  default was rejected because it would make one `Meta` key mean different things on
  three bases.
- **Save kwargs never name a model field.** DRF merges `serializer.save(**kwargs)` into
  the write with no validation and no visibility check, so a save kwarg naming a model
  column or relation would be an unaudited model-field injection.
  `_assert_save_kwargs_not_model_fields` refuses it, leaving the audited
  `Meta.injected_fields` + `get_serializer_injected_data` channel as the one way to inject
  a model field; save kwargs carry only non-model arguments a custom `create()` /
  `update()` consumes.
- **Injected fields ride the input fields' walk.** Every top-level per-field discipline
  (schema/runtime agreement, write-source ownership, queryset scoping, the relation-intent
  ledger, the post-save attestation) walks the one `_write_surface_specs` list of input
  fields plus `Meta.injected_fields`, so an injected field gets the same checks as an
  input field by construction rather than through a parallel guard kept in step.
- **The schema/runtime agreement guard fails closed.** A field carrying a requiredness or
  annotation contract with no validated `Meta` snapshot raises rather than returning: a
  guard that skips when its input is missing reports agreement it never checked.
- **Nested writes require the serializer's own `create()` / `update()`.** DRF's
  `ModelSerializer.create` / `.update` assert that no nested writable data is present
  unless overridden, a raw `AssertionError` that would escape the envelope, so
  `Meta.nested_fields` requires the override at class creation.

## Non-Decision deliberation

- **The import manifest is per-module.** The `### Import manifest` in the spec names which
  shared modules each `rest_framework/` module imports from, not which symbols. Module
  granularity is the level at which the contract is stable: a per-symbol manifest goes
  stale at the next legitimate move *inside* a permitted module. The per-symbol obligation
  that needs a ratchet has an executable one,
  `tests/rest_framework/test_dry_import_ratchet.py`, which checks object identity rather
  than grepping source: a grep is satisfied by a same-named local carrying a copied body
  and breaks on a legitimate import-style change, while identity catches both the
  redefinition and the deletion.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[django-workflow]: ../../../.github/workflows/django.yml
[goal]: ../../../GOAL.md
[pytest-ini]: ../../../pytest.ini
[start]: ../../../START.md

<!-- docs/ -->
[glossary-djangoformmutation]: ../../GLOSSARY.md#djangoformmutation
[glossary-djangomodelformmutation]: ../../GLOSSARY.md#djangomodelformmutation
[glossary-djangomodelpermission]: ../../GLOSSARY.md#djangomodelpermission
[glossary-djangomutation]: ../../GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: ../../GLOSSARY.md#djangomutationfield
[glossary-djangotype]: ../../GLOSSARY.md#djangotype
[glossary-serializermutation]: ../../GLOSSARY.md#serializermutation

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-035]: ../spec-035-optimizer_hardening-0_0_10.md
[spec-036]: ../spec-036-mutations-0_0_11.md
[spec-038]: ../spec-038-form_mutations-0_0_12.md
[spec-039-d10]: ../spec-039-serializer_mutations-0_0_13.md#decision-10--operations-create--update-no-serializer-delete
[spec-039-d11]: ../spec-039-serializer_mutations-0_0_13.md#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelserializer
[spec-039-d12]: ../spec-039-serializer_mutations-0_0_13.md#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy
[spec-039-d13]: ../spec-039-serializer_mutations-0_0_13.md#decision-13--live-coverage-products-grows-a-modelserializer-mutation
[spec-039-d14]: ../spec-039-serializer_mutations-0_0_13.md#decision-14--version-bumps-are-owned-by-the-joint-0013-cut
[spec-039-d1]: ../spec-039-serializer_mutations-0_0_13.md#decision-1--spec-filename-and-canonical-naming
[spec-039-d2]: ../spec-039-serializer_mutations-0_0_13.md#decision-2--card-scope-boundary-the-serializer-flavor-ships-auth-stays-out-the-frozen-036-contracts-and-the-038-factory-are-reused-unchanged
[spec-039-d3]: ../spec-039-serializer_mutations-0_0_13.md#decision-3--class-meta-surface-not-graphenes-mutationoptions
[spec-039-d4]: ../spec-039-serializer_mutations-0_0_13.md#decision-4--module-and-test-locations-rest_framework-subpackage-mirroring-forms
[spec-039-d5]: ../spec-039-serializer_mutations-0_0_13.md#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused
[spec-039-d6]: ../spec-039-serializer_mutations-0_0_13.md#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven
[spec-039-d7]: ../spec-039-serializer_mutations-0_0_13.md#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth
[spec-039-d8]: ../spec-039-serializer_mutations-0_0_13.md#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload
[spec-039-d9]: ../spec-039-serializer_mutations-0_0_13.md#decision-9--optimizer-composition-the-modelserializer-payload-re-fetch-rides-the-spec-036-g2-path
[spec-039]: ../spec-039-serializer_mutations-0_0_13.md
[spec-040]: ../spec-040-auth_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[forms-converter]: ../../../django_strawberry_framework/forms/converter.py
[forms-sets]: ../../../django_strawberry_framework/forms/sets.py
[mutations-inputs]: ../../../django_strawberry_framework/mutations/inputs.py
[mutations-sets]: ../../../django_strawberry_framework/mutations/sets.py

<!-- tests/ -->
[test-rest-framework]: ../../../tests/rest_framework/
[test-soft-dependency-rf]: ../../../tests/rest_framework/test_soft_dependency.py

<!-- examples/ -->
[products-models]: ../../../examples/fakeshop/apps/products/models.py
[test-products-api]: ../../../examples/fakeshop/test_query/test_products_api.py
[test-query-readme]: ../../../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
