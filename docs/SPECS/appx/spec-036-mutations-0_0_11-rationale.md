# Rationale companion: spec-036 (Mutations — the `DjangoMutation` write-side foundation)

Companion to [`docs/SPECS/spec-036-mutations-0_0_11.md`][spec-036]. It carries that spec's deliberative layer: each Decision's justification, the alternatives each Decision rejected and why, and the standing risks with the fallback that applies if a shipped answer proves wrong. The spec carries the contract.

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-036-d1].

### Justification

- The `spec-<NNN>-<topic>-<X_Y_Z>.md` filename convention in [`docs/SPECS/NEXT.md`][next] bakes the card's NNN and target patch into the filename. The card is [`DONE-036-0.0.11`][kanban], so `<NNN>` is `036` and `<X_Y_Z>` is `0_0_11`.
- The topic slug is `mutations`, the subsystem name.

### Alternatives considered (and rejected)

- **Topic slug `mutations_foundation` / `django_mutation`.** Rejected: the subsystem is "mutations"; the foundation framing belongs in the scope boundary ([Decision 2](#decision-2--card-scope-boundary-the-mutation-foundation-ships-the-flavor-cards-and-uploads-are-out-the-fielderror-envelope-is-defined-here)), not the filename.

## Decision 2 — Card-scope boundary: the mutation foundation ships; the flavor cards and uploads are out; the `FieldError` envelope is defined here

Spec: [Decision 2 — Card-scope boundary: the mutation foundation ships; the flavor cards and uploads are out; the `FieldError` envelope is defined here][spec-036-d2].

### Justification

The card is XL and the form / serializer / upload flavors are separately carded with their own `0.0.12` / `0.0.13` / `0.0.11` targets; pulling any forward would bloat the slice exactly as [`START.md`][start]'s scope-creep advice warns. The base + envelope + model-driven operations are the irreducible foundation the flavors all subclass.

### Alternatives considered (and rejected)

- **Ship the form flavor in this card too.** Rejected: `DjangoFormMutation` is its own `0.0.12` card with its own DoD; the form-validation-to-`FieldError` mapping is a distinct slice, and the base must exist first.
- **Defer the `FieldError` envelope to the first flavor card.** Rejected: the card DoD pins it here so the flavors return the same class; deferring it forks the contract.

## Decision 3 — `class Meta` surface, not decorators: borrow the capabilities, reject the decorator surface

Spec: [Decision 3 — `class Meta` surface, not decorators: borrow the capabilities, reject the decorator surface][spec-036-d3].

### Justification

This is the package's defining surface contract: [`START.md`][start] "Meta classes on every consumer surface" — stacked Strawberry decorators on a consumer-facing class are the strawberry-graphql-django API, the reason this package exists. [`GOAL.md`][goal]'s `1.0.0` showcase spells the write surface as `class CreateCelestialBody(DjangoMutation): class Meta: ...`. The *capabilities* of upstream's decorators (operations, input generation, error capture, optimizer return) are borrowed at the outcome level ([Borrowing posture][spec-036-borrowing-posture]); the decorator mechanism is not.

### Alternatives considered (and rejected)

- **strawberry-django's `create(InputType)` field-verb factories.** Rejected: that *is* the decorator-adjacent surface the package replaces; it also requires the consumer to hand-declare the input type (`@strawberry_django.input`), re-introducing the duplicate-field burden.
- **A `@django_mutation` class decorator** (Meta-shaped config, decorator trigger). Rejected: a decorator on a consumer class is exactly the shape [`START.md`][start] forbids; the base-class form is uniform with `DjangoType` / `FilterSet` / `OrderSet`.

## Decision 4 — Module and test locations: `mutations/` subpackage mirroring `filters/` / `orders/`

Spec: [Decision 4 — Module and test locations: `mutations/` subpackage mirroring `filters/` / `orders/`][spec-036-d4].

### Justification

The card names `django_strawberry_framework/mutations/` and `tests/mutations/`; the set-family precedent ([`spec-027`][spec-027] / [`spec-028`][spec-028]) is the proven shape for a declarative `class Meta` subsystem with generated input classes and finalizer binding. The module split keeps generation, declaration, resolution, field exposure, and write authorization separable for the flavor cards to extend.

### Alternatives considered (and rejected)

- **A flat `mutations.py` module** (like [`permissions.py`][permissions]). Rejected: mutations is generation + a metaclass + a resolver pipeline + a field factory + a permission seam + downstream-flavor extension points; a subpackage matches the surface.
- **Folding input generation into the [`filters/`][filters-sets] input substrate.** Rejected: filter inputs are lookup-shaped (`{exact, icontains, ...}`); mutation inputs are model-column-shaped. The [`utils/inputs.py`][utils-inputs] shared substrate is reused where it fits, but the mutation generator is its own concern.

## Decision 5 — Public surface: `DjangoMutation` base + `DjangoMutationField` factory + `FieldError`, exported from the root

Spec: [Decision 5 — Public surface: `DjangoMutation` base + `DjangoMutationField` factory + `FieldError`, exported from the root][spec-036-d5].

### Justification

- **Factory uniformity, with a timing-forced annotation exception.** Every root field the package ships is a factory assigned to a class attribute; `DjangoMutationField` keeps the write side idiomatic with the read side rather than introducing a `.Field()`-style classmethod (graphene-django's shape) or a decorator (strawberry-django's). The one difference is forced by timing, not style: the read-side factories read a consumer annotation that names a type existing at import (`DjangoConnection[CategoryType]`), but the mutation payload is **generated at finalization** ([Decision 12](#decision-12--finalization-seam-register-at-class-creation-bind-at-phase-25-no-deferred_meta_keys-change)) and has no importable name when `@strawberry.type class Mutation` evaluates its annotations — so `DjangoMutationField` carries no class-attribute annotation and types the field itself via a `strawberry.lazy` forward-ref to the generated `<Name>Payload` ([Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)).
- **Root export matches the audience.** `DjangoMutation` and `DjangoMutationField` are used in every schema that writes, `FieldError` is referenced in every payload, and `DjangoModelPermission` is the base a custom permission class subclasses — all belong at the root alongside [`DjangoType`][glossary-djangotype] / [`finalize_django_types`][glossary-finalize_django_types], parallel to how [`apply_cascade_permissions`][glossary-apply_cascade_permissions] ([`spec-034`][spec-034] Decision 4) is root-exported.
- **One `operation` key over three base classes.** A single nested-`Meta` key driving behavior is the most `class Meta`-idiomatic shape (it parallels `filterset_class` / `globalid_strategy` selecting behavior through one key), and keeps the public symbol count at four.

### Alternatives considered (and rejected)

- **Three base classes `DjangoCreateMutation` / `DjangoUpdateMutation` / `DjangoDeleteMutation`.** Rejected: triples the base-class surface for what one `Meta.operation` selector expresses; graphene-django itself routes all operations through one `ClientIDMutation` lineage with `model_operations`.
- **A `.field()` classmethod accessor on the mutation class** (graphene-django's `.Field()`, `create_item = CreateItem.field()`). Rejected: the no-annotation `DjangoMutationField` form resolves the payload-timing hazard ([Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)) with a single factory symbol, so a `.field()` accessor would add a second exposure idiom for no gain.
- **Exporting only from a `django_strawberry_framework.mutations` namespace.** Rejected: the symbols are used inside schema modules alongside root-exported types; subsystem-namespace imports are for *family* surfaces (`from .filters import FilterSet`), as [`spec-034`][spec-034] Decision 4 settled for the cascade helper.

## Decision 6 — Auto-generated `Input` / `PartialInput` types

Spec: [Decision 6 — Auto-generated `Input` / `PartialInput` types][spec-036-d6].

### Justification

Input generation is the card's headline parity item ([`GOAL.md`][goal] success-criterion 6); reusing the read-side converters gives read and write one wire contract; the stable-naming + materialize-before-`Schema` discipline is the proven set-family lifecycle ([Decision 12](#decision-12--finalization-seam-register-at-class-creation-bind-at-phase-25-no-deferred_meta_keys-change)). Type identity is the complete shape rather than the model because GraphQL type names are schema-global: a narrowed input that claimed the bare `<Model>Input` name could leak a field one mutation meant to exclude, or make another mutation too narrow (AR-H1 / AR-M6). A relation override is type-locked because re-declaring a `GlobalID` relation as a raw `int` would route the value down the raw-pk path, past the relation type-check and visibility confirmation.

### Alternatives considered (and rejected)

- **A single `Input` with all-optional fields for both create and update.** Rejected: it loses the create-required contract (a missing required field would only fail at `full_clean()`, not at the GraphQL layer); upstream and graphene-django both keep the required/partial split.
- **A blanket "every editable field required" create rule.** Rejected: it would force `description` / `isPrivate` required on products and on [`GOAL.md`][goal]'s `Galaxy` / `CelestialBody` models (the same `blank=True, default=""` / `default=False` shape), diverging from DRF and strawberry-django.
- **FK input as the nested object (strawberry-django's `ParsedObject` connect/create).** Rejected: nested writes are out of scope ([Out of scope][spec-036-out-of-scope]); `<field>_id` is the minimal, unambiguous shape.
- **Reuse the `DjangoType` output type as the input.** Rejected: GraphQL forbids an output type in input position; the input is a distinct `@strawberry.input` type with id-shaped relations.

## Decision 7 — The shared `FieldError` envelope and the payload wrapper

Spec: [Decision 7 — The shared `FieldError` envelope and the payload wrapper][spec-036-d7].

### Justification

- **The card pins the graphene-django shape.** Its DoD mirrors graphene-django's `ErrorType` (a `field` name + a list of message strings); the payload-with-`errors` surface is graphene-django's `DjangoModelFormMutation` / `SerializerMutation` shape, so the `0.0.12` / `0.0.13` flavors attach the identical `errors` field.
- **Partial-success representability.** A payload that carries both the object and errors can express "no object, here are the errors" and a successful object in one type; a disjoint union cannot.
- **A uniform object slot (AR-H5).** Naming the payload's object field after the model collides with Python / GraphQL constraints (`Property` → `property`) and with future payload-metadata fields; `node` / `result` never does.

### Alternatives considered (and rejected)

- **strawberry-django's disjoint `Type | OperationInfo` union return.** Rejected: `OperationInfo` is a flat `list[OperationMessage]` (each message carries an optional `field`, but it is **not** the field-keyed `errors: list[FieldError]` shape the card pins), and a disjoint union cannot host the shared `errors: list[FieldError]` field the flavor cards reuse.
- **Raising `GraphQLError` for validation failures** (errors in the top-level `errors` array). Rejected: loses the field-keyed structure clients need to attach messages to form fields, and conflates expected validation failures with execution errors.

## Decision 8 — Resolver pipeline: decode → `full_clean()` → write → optimizer re-fetch → payload (sync and async)

Spec: [Decision 8 — Resolver pipeline: decode → `full_clean()` → write → optimizer re-fetch → payload (sync and async)][spec-036-d8].

### Justification

`full_clean()` is the Django-native validation entry strawberry-django uses; routing its errors into the envelope (rather than raising) is the graphene-django contract; the re-fetch step is where optimizer composition lives; the single-`atomic()` / single-`sync_to_async` boundary keeps the write atomic under concurrency. Authorizing before the relation decode keeps an unauthorized caller from probing relation visibility by id. A sync path meeting an `async def get_queryset` raises [`SyncMisuseError`][glossary-syncmisuseerror] (coroutine closed first), the package's standing async-misuse discipline.

### Alternatives considered (and rejected)

- **Skip `full_clean()` and rely on DB constraints.** Rejected: loses field-level validation messages and defers errors to opaque `IntegrityError`s; upstream and DRF both validate before write.
- **A construction-time sync / async resolver split** (the [`DjangoListField`][glossary-djangolistfield] consumer-`resolver=` half). Rejected: the pipeline is package-owned, so there is no consumer resolver to inspect; one resolver dispatching per call via `async_execution()` serves `schema.execute_sync` and `await schema.execute` alike.
- **No transaction / per-call `sync_to_async` hops on the async path (AR-M4).** Rejected: a write, its relation assignments, and the payload snapshot separated by `await`s are not atomic and are hard to reason about under concurrent requests; one `atomic()` inside one `sync_to_async(thread_sensitive=True)` is the defensible foundation.

## Decision 9 — Optimizer composition and the `spec-035` G2 live-test handoff

Spec: [Decision 9 — Optimizer composition and the `spec-035` G2 live-test handoff][spec-036-d9].

### Justification

[`spec-035`][spec-035]'s G2 gate exists for this path, and its test plan names the live mutation rows this card carries. The re-fetch-and-plan return mirrors strawberry-django's optimizer-composed mutation return at the outcome level.

### Alternatives considered (and rejected)

- **Return the written instance without re-fetching.** Rejected: a freshly `save()`d instance has no related rows loaded, so any relation in the response selection N+1s; the re-fetch is what makes the response selection planable.
- **Disable the optimizer for mutation returns entirely.** Rejected: the response selection still needs `select_related` / `prefetch_related`; only `.only(...)` is unsafe under a mutation, which is exactly what G2 gates, so a coarser disable would regress the join / prefetch planning.
- **Re-fetch through the visibility `get_queryset` (Medium-1).** Rejected: write authorization is model permission, not visibility, so an authorized caller can write a row the visibility hook hides, and a filtered re-fetch would return a null object after a successful write.

## Decision 10 — Permission composition: `update` / `delete` lookups run through the target `get_queryset`

Spec: [Decision 10 — Permission composition: `update` / `delete` lookups run through the target `get_queryset`][spec-036-d10].

### Justification

The [`DONE-034-0.0.10`][kanban] dependency exists for this: write mutations compose with `apply_cascade_permissions`. Routing the lookup through `get_queryset` reuses the visibility contract with no new permission machinery, and not-found-equals-hidden matches the package's no-existence-leak posture ([`DjangoNodeField`][glossary-djangonodefield]). The row lock rides the base manager with the visibility queryset reduced to a pk subquery because a `FOR UPDATE` cannot legally carry the joins / unions / annotations a consumer's queryset may hold.

### Alternatives considered (and rejected)

- **Look up by raw `Model.objects.get(pk=...)` and check visibility after.** Rejected: a post-hoc check leaks existence (the timing / error differs for hidden vs missing); routing through `get_queryset` makes them identical by construction.
- **Reusing `get_queryset` as the write-authorization gate.** Rejected (AR-H3): the cascade + `get_queryset` gate row *reachability*, and treating "can see this row" as "can change / delete this row" would let a public read surface silently grant writes. Write authorization is its own seam ([Decision 15](#decision-15--write-authorization-a-drf-shaped-check_permission--metapermission_classes-seam)); the field-level read gates planned for `0.1.1` ([`FieldSet`][glossary-fieldset] / [Per-field permission hooks][glossary-per-field-permission-hooks]) layer on top of both, not in place of either.

## Decision 11 — Primary-type resolution: return type and input target resolve the model's primary `DjangoType`

Spec: [Decision 11 — Primary-type resolution: return type and input target resolve the model's primary `DjangoType`][spec-036-d11].

### Justification

The [`DONE-018-0.0.6`][kanban] dependency exists for this: the explicit primary type drives mutation target resolution. Reusing the primary lookup keeps the mutation return consistent with what relation traversal and node refetch resolve, so a mutated row round-trips through the same type a query would return.

### Alternatives considered (and rejected)

- **An explicit `Meta.return_type` on the mutation.** Rejected: redundant with the registry primary lookup for the common case; it stays the escape hatch if a mutation must return a *secondary* type ([Risks](#risks-and-open-questions)).
- **Resolve the first registered type for the model.** Rejected: violates `Meta.primary` semantics (secondaries never auto-resolve), exactly the ambiguity `Meta.primary` exists to forbid.

## Decision 12 — Finalization seam: register at class creation, bind at phase 2.5, no `DEFERRED_META_KEYS` change

Spec: [Decision 12 — Finalization seam: register at class creation, bind at phase 2.5, no `DEFERRED_META_KEYS` change][spec-036-d12].

### Justification

The materialize-generated-classes-before-`Schema` discipline ([`spec-027`][spec-027] / [`spec-028`][spec-028] Decision 6 / Decision 9) is how Strawberry resolves lazily-referenced generated input classes; reusing phase 2.5 keeps one finalization gate. Leaving `DEFERRED_META_KEYS` untouched honors the [Cross-subsystem invariants][glossary-cross-subsystem-invariants] rule (promote a `DjangoType` `Meta` key only when its subsystem applies it end-to-end); mutations add no such key.

### Alternatives considered (and rejected)

- **Generate input / payload classes lazily at first request.** Rejected: Strawberry resolves schema types at `Schema(...)` construction; lazy generation would miss the schema build, exactly the failure the phase-2.5 materialize step prevents.
- **A separate `finalize_django_mutations()` entry point.** Rejected: a second finalization gate the consumer must remember to call; phase 2.5 of `finalize_django_types()` already runs after all types are registered.

## Decision 13 — Version bumps are owned by the joint `0.0.11` cut

Spec: [Decision 13 — Version bumps are owned by the joint `0.0.11` cut][spec-036-d13].

### Justification

Per [`docs/SPECS/NEXT.md`][next], when several cards target one patch version the bump belongs to the joint cut, not to any one card's spec. `036` and `037` both target `0.0.11`.

### Alternatives considered (and rejected)

- **Bump to `0.0.11` in this card's Slice 5.** Rejected: `037` also ships into `0.0.11`; a per-card bump races the joint cut.

## Decision 14 — Single `data:` argument, no Relay `clientMutationId` in `0.0.11`

Spec: [Decision 14 — Single `data:` argument, no Relay `clientMutationId` in `0.0.11`][spec-036-d14].

### Justification

A single `data:` argument mirrors strawberry-django's `data:` shape, avoids collisions between input field names and reserved argument names, and lets the input type evolve without re-spelling the field signature. The root `id:` renders `ID!` and is decoded server-side, the `node(id: ID!)` contract [`DjangoNodeField`][glossary-djangonodefield] uses. The Relay `clientMutationId` round-trip is a Graphene-runtime convention the package does not adopt ([Borrowing posture][spec-036-borrowing-posture]).

### Alternatives considered (and rejected)

- **Flattened per-field arguments** (`createItem(name: ..., description: ..., categoryId: ...)`). Rejected: collides with reserved names, bloats the field signature, and fragments the input contract the flavor cards reuse.
- **graphene-django's `input:` single-argument + `clientMutationId`.** Rejected: `clientMutationId` is the Relay-mutation-spec round-trip the package's non-Graphene-runtime stance declines; `data:` is the strawberry-native spelling.

## Decision 15 — Write authorization: a DRF-shaped `check_permission` / `Meta.permission_classes` seam

Spec: [Decision 15 — Write authorization: a DRF-shaped `check_permission` / `Meta.permission_classes` seam][spec-036-d15].

### Justification

It matches [`GOAL.md`][goal]'s DRF-shaped, `class Meta`-driven, layered permissions; it keeps visibility and write authorization distinct (so "can view" never silently means "can write"); and the safe-by-default model-permission check means the write side is not unauthenticated the moment a consumer exposes a `Mutation`.

### Alternatives considered (and rejected)

- **Leave create authorization to the consumer or to `0.1.1`.** Rejected (AR-H3): a write foundation whose `create` is unauthenticated unless every schema bolts on an ad-hoc resolver gate, with "anonymous cannot mutate" underivable from the contract.
- **A single coarse `Meta.login_required` boolean.** Rejected: not DRF-shaped, expresses neither model-permission nor object-level checks, and gives the flavor cards nothing reusable.
- **Routing denials into the `FieldError` envelope instead of raising.** Rejected: conflates authorization (a `403`-shaped failure) with field validation; raising is the Strawberry `permission_classes` convention and keeps the two failure modes legible to clients.

## Risks and open questions

Each item names the shipped answer and the fallback if it proves wrong.

- **`Meta.operation` selector vs three base classes.** Shipped ([Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root)): one `DjangoMutation` base with `Meta.operation` ∈ `{"create", "update", "delete"}`. Fallback: if the per-operation pipelines diverge enough that one base accretes operation-conditional branches everywhere, split into `DjangoCreateMutation` / `DjangoUpdateMutation` / `DjangoDeleteMutation` sharing a private base, keeping `DjangoMutation` as the abstract parent.
- **The model-permission default's strictness.** Shipped ([Decision 15](#decision-15--write-authorization-a-drf-shaped-check_permission--metapermission_classes-seam)): the default `DjangoModelPermission` denies a caller with no `request.user` or without the model perm; a public write is the explicit `Meta.permission_classes = []` opt-out, and an object-level rule is a `DjangoModelPermission` subclass or a `check_permission` override. Fallback: if the default proves too strict for common cases, ship an additional permissive built-in class consumers opt into, never a weaker default.
- **Returning a secondary `DjangoType`.** Shipped ([Decision 11](#decision-11--primary-type-resolution-return-type-and-input-target-resolve-the-models-primary-djangotype)): the payload object resolves the model's **primary** type, matching relation traversal and node refetch. Fallback: a `Meta.return_type` escape hatch for a mutation that must return a *secondary* type, defined only when a consumer needs it.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../../GOAL.md
[kanban]: ../../../KANBAN.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary-apply_cascade_permissions]: ../../GLOSSARY.md#apply_cascade_permissions
[glossary-cross-subsystem-invariants]: ../../GLOSSARY.md#cross-subsystem-invariants
[glossary-djangolistfield]: ../../GLOSSARY.md#djangolistfield
[glossary-djangonodefield]: ../../GLOSSARY.md#djangonodefield
[glossary-djangotype]: ../../GLOSSARY.md#djangotype
[glossary-fieldset]: ../../GLOSSARY.md#fieldset
[glossary-finalize_django_types]: ../../GLOSSARY.md#finalize_django_types
[glossary-per-field-permission-hooks]: ../../GLOSSARY.md#per-field-permission-hooks
[glossary-syncmisuseerror]: ../../GLOSSARY.md#syncmisuseerror

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-027]: ../spec-027-filters-0_0_8.md
[spec-028]: ../spec-028-orders-0_0_8.md
[spec-034]: ../spec-034-permissions-0_0_10.md
[spec-035]: ../spec-035-optimizer_hardening-0_0_10.md
[spec-036-borrowing-posture]: ../spec-036-mutations-0_0_11.md#borrowing-posture
[spec-036-d10]: ../spec-036-mutations-0_0_11.md#decision-10--permission-composition-update--delete-lookups-run-through-the-target-get_queryset
[spec-036-d11]: ../spec-036-mutations-0_0_11.md#decision-11--primary-type-resolution-return-type-and-input-target-resolve-the-models-primary-djangotype
[spec-036-d12]: ../spec-036-mutations-0_0_11.md#decision-12--finalization-seam-register-at-class-creation-bind-at-phase-25-no-deferred_meta_keys-change
[spec-036-d13]: ../spec-036-mutations-0_0_11.md#decision-13--version-bumps-are-owned-by-the-joint-0011-cut
[spec-036-d14]: ../spec-036-mutations-0_0_11.md#decision-14--single-data-argument-no-relay-clientmutationid-in-0011
[spec-036-d15]: ../spec-036-mutations-0_0_11.md#decision-15--write-authorization-a-drf-shaped-check_permission--metapermission_classes-seam
[spec-036-d1]: ../spec-036-mutations-0_0_11.md#decision-1--spec-filename-and-canonical-naming
[spec-036-d2]: ../spec-036-mutations-0_0_11.md#decision-2--card-scope-boundary-the-mutation-foundation-ships-the-flavor-cards-and-uploads-are-out-the-fielderror-envelope-is-defined-here
[spec-036-d3]: ../spec-036-mutations-0_0_11.md#decision-3--class-meta-surface-not-decorators-borrow-the-capabilities-reject-the-decorator-surface
[spec-036-d4]: ../spec-036-mutations-0_0_11.md#decision-4--module-and-test-locations-mutations-subpackage-mirroring-filters--orders
[spec-036-d5]: ../spec-036-mutations-0_0_11.md#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root
[spec-036-d6]: ../spec-036-mutations-0_0_11.md#decision-6--auto-generated-input--partialinput-types
[spec-036-d7]: ../spec-036-mutations-0_0_11.md#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper
[spec-036-d8]: ../spec-036-mutations-0_0_11.md#decision-8--resolver-pipeline-decode--full_clean--write--optimizer-re-fetch--payload-sync-and-async
[spec-036-d9]: ../spec-036-mutations-0_0_11.md#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff
[spec-036-out-of-scope]: ../spec-036-mutations-0_0_11.md#out-of-scope-explicitly-tracked-elsewhere
[spec-036]: ../spec-036-mutations-0_0_11.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filters-sets]: ../../../django_strawberry_framework/filters/sets.py
[permissions]: ../../../django_strawberry_framework/permissions.py
[utils-inputs]: ../../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
