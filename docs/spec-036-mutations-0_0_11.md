# Spec: Mutations + auto-generated Input types — the `DjangoMutation` write-side foundation, the shared `FieldError` envelope, and `create` / `update` / `delete` on the DRF-shaped `class Meta` surface

Planned for `0.0.11` (card [`TODO-ALPHA-036-0.0.11`][kanban]). This card opens the package's **write side** — the single largest unscoped gap against [`strawberry-graphql-django`][upstream-mutations], which ships `create` / `update` / `delete` + auto-generated `Input` / `PartialInput` types and the package has none of. It lands the mutation *foundation*: a [`DjangoMutation`][glossary-djangomutation] base class configured through a nested `class Meta` (the DRF shape, not Strawberry decorators), [auto-generated `Input` / `PartialInput` types][glossary-input-type-generation] derived from `Meta.model` that honor the relation-override contract pinned in [`DONE-010-0.0.4`][kanban] ([`spec-010`][spec-010]), and the shared [`errors: list[FieldError]`][glossary-fielderror-envelope] envelope — defined and frozen here so the form-based (`0.0.12`) and DRF-serializer / auth (`0.0.13`) flavor cards reuse it unchanged. The write resolvers run sync and async, scope `update` / `delete` lookups through the target type's [`get_queryset`][glossary-get_queryset-visibility-hook] + [`apply_cascade_permissions`][glossary-apply_cascade_permissions] ([`DONE-034-0.0.10`][kanban]), re-fetch the mutated row through [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] for the response selection, and resolve the return / input target through the model's **primary** [`DjangoType`][glossary-djangotype] ([`Meta.primary`][glossary-metaprimary], [`DONE-018-0.0.6`][kanban]). **Version boundary** (see [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0011-cut)): this card shares the `0.0.11` patch line with [`TODO-ALPHA-037-0.0.11`][kanban] (the [`Upload` scalar][glossary-upload-scalar] + file / image field mapping, which maps the same model fields to `Upload` on the mutation input side this card generates); the `pyproject.toml` / `__version__` / [`tests/base/test_init.py::test_version`][test-base-init] bump to `0.0.11` is owned by the **joint cut**, not by this card. No slice in this card bumps the version.

Status: **PLANNED** (card `TODO-ALPHA-036-0.0.11`, not yet started). Authored from the card body via the [`docs/SPECS/NEXT.md`][next] flow. Slices: Slice 1 (**input-type generation + the `FieldError` envelope + the payload wrapper** — [`mutations/inputs.py`][mutations-inputs], the public `FieldError` type, the generated `<Name>Payload`; [Decision 6](#decision-6--auto-generated-input--partialinput-types) / [Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)), Slice 2 (**the `DjangoMutation` base + `Meta` validation + finalizer binding** — [`mutations/sets.py`][mutations-sets]; [Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root) / [Decision 12](#decision-12--finalization-seam-register-at-class-creation-bind-at-phase-25-no-deferred_meta_keys-change)), Slice 3 (**the write resolvers + `DjangoMutationField` + optimizer / permission composition** — [`mutations/resolvers.py`][mutations-resolvers] / [`mutations/fields.py`][mutations-fields]; [Decision 8](#decision-8--resolver-pipeline-decode--full_clean--write--optimizer-refetch--payload-sync-and-async) / [Decision 9](#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff) / [Decision 10](#decision-10--permission-composition-update--delete-lookups-run-through-the-target-get_queryset)), Slice 4 (**the products live write surface** — `examples/fakeshop/apps/products/schema.py` gains a `Mutation`, `config/schema.py` wires it, and [`test_products_api.py`][test-products-api] earns the live HTTP coverage that discharges the [`spec-035`][spec-035] G2 handoff), and Slice 5 (**doc updates + card-completion wrap**; the per-card [`CHANGELOG.md`][changelog] edit must be named explicitly in the Slice 5 maintainer prompt — this spec describes the edit but cannot grant the permission [`AGENTS.md`][agents] reserves for an explicit instruction). The card's two hard dependencies are satisfied: [`DONE-018-0.0.6`][kanban] (`Meta.primary`) and [`DONE-034-0.0.10`][kanban] (permissions) have both shipped.

Owner: package maintainer.

Predecessors: [`spec-035-optimizer_hardening-0_0_10.md`][spec-035] (the most-recently-authored spec — the canonical voice / depth / section-layout reference for this document; its **G2** operation-type `.only()` gate was shipped *because of* this card, and its [Test plan][spec-035] records a **mandatory live-test handoff** the first mutation card must discharge — this card does, in Slice 4, [Decision 9](#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff)); [`spec-034-permissions-0_0_10.md`][spec-034] (the permissions subsystem this card composes with — `update` / `delete` lookups run through the target type's `get_queryset` + `apply_cascade_permissions`, and [Decision 2][spec-034]'s "define-the-surface-here, implement-later" pattern is the template for this card's frozen-`FieldError`-envelope boundary, [Decision 2](#decision-2--card-scope-boundary-the-mutation-foundation-ships-the-flavor-cards-and-uploads-are-out-the-fielderror-envelope-is-frozen-here)); [`spec-027-filters-0_0_8.md`][spec-027] / [`spec-028-orders-0_0_8.md`][spec-028] (the two prior *set-family* subsystems — `mutations/` mirrors their subpackage layout, their finalizer phase-2.5 binding seam, their stable class-derived input-class naming, and their materialize-generated-classes-before-`Schema` discipline); [`spec-030-connection_field-0_0_9.md`][spec-030] (the field-factory + Meta-only-derivation precedent — `DjangoMutationField` is the write-side sibling of [`DjangoConnectionField`][glossary-djangoconnectionfield], and its optimizer-cooperation seam is the read-side analogue of this card's post-write re-fetch); [`spec-018-meta_primary-0_0_6.md`][spec-018] (the primary-type resolution this card's return / input target depends on); [`spec-010-foundation-0_0_4.md`][spec-010] (the relation-override contract the generated input types must honor). [`docs/GLOSSARY.md`][glossary] carries [`DjangoMutation`][glossary-djangomutation], [Input type generation][glossary-input-type-generation], and [`FieldError` envelope][glossary-fielderror-envelope] as `planned for 0.0.11`; Slice 5 promotes those three to `shipped (0.0.11)` and adds a `DjangoMutationField` entry (the one net-new symbol the glossary does not yet name — [Doc updates](#doc-updates)).

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the [`TODO-ALPHA-036-0.0.11`][kanban] card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-06-16). Pinned: the canonical structured spec filename ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the card-scope boundary that ships the mutation foundation and parks the flavor cards, with the `FieldError` envelope **frozen here** for downstream reuse ([Decision 2](#decision-2--card-scope-boundary-the-mutation-foundation-ships-the-flavor-cards-and-uploads-are-out-the-fielderror-envelope-is-frozen-here)); the **`class Meta`-not-decorators** surface that is the package's reason to exist ([Decision 3](#decision-3--class-meta-surface-not-decorators-borrow-the-capabilities-reject-the-decorator-surface)); the `mutations/` subpackage layout mirroring `filters/` / `orders/` ([Decision 4](#decision-4--module-and-test-locations-mutations-subpackage-mirroring-filters--orders)); the `DjangoMutation` base + `DjangoMutationField` factory + `FieldError` public surface ([Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root)); the auto-generated `Input` / `PartialInput` derivation and its relation-override-contract obligation ([Decision 6](#decision-6--auto-generated-input--partialinput-types)); the payload-wrapper + `FieldError` envelope shape, with the disjoint-union alternative rejected ([Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)); the sync + async resolver pipeline ([Decision 8](#decision-8--resolver-pipeline-decode--full_clean--write--optimizer-refetch--payload-sync-and-async)); the optimizer-composition resolution that **discharges the [`spec-035`][spec-035] G2 live-test handoff** ([Decision 9](#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff)); the permission-composition contract for `update` / `delete` lookups ([Decision 10](#decision-10--permission-composition-update--delete-lookups-run-through-the-target-get_queryset)); the primary-type resolution dependency ([Decision 11](#decision-11--primary-type-resolution-return-type-and-input-target-resolve-the-models-primary-djangotype)); the finalizer binding seam with no `DEFERRED_META_KEYS` change ([Decision 12](#decision-12--finalization-seam-register-at-class-creation-bind-at-phase-25-no-deferred_meta_keys-change)); the joint-`0.0.11`-cut version boundary ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0011-cut)); and the single-`data:`-argument shape with no Relay `clientMutationId` ([Decision 14](#decision-14--single-data-argument-no-relay-clientmutationid-in-0011)). Two open design questions are carried into [Risks and open questions](#risks-and-open-questions) with a preferred answer for `0.0.11`: the `Meta.operation`-selector-vs-three-base-classes shape and the payload-type annotation ergonomics.
- **Revision 2** — review-feedback fold-in (2026-06-17), applying a rigorous review pass cross-referenced against [`GOAL.md`][goal] and the `django-graphene-filters` cookbook. Foundational changes (applied first, since they reshape the dependent items): **(1)** the input generator derives from the model's **editable fields** narrowed by the mutation's own `Meta.fields` / `Meta.exclude` — **not** the read-side [`DjangoType`][glossary-djangotype] selection (which carries read-only `created_date` / `updated_date` and may omit editable columns the cookbook hides), with create-input required-ness following Django's `default` / `blank` / `null` so `description` / `is_private` are optional rather than blanket-required (Major-1 + Medium-4, [Decision 6](#decision-6--auto-generated-input--partialinput-types)); **(2)** the payload exposure surface is committed to a **no-annotation** `DjangoMutationField` typed via a `strawberry.lazy` forward-ref — an eager `CreateItem.Payload` annotation cannot exist when `@strawberry.type class Mutation` evaluates at import — resolving the former Risks open question into [Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root) / [Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper) (Major-3); **(3)** the base `Meta` validation requires a *resolvable* model via an overridable `_resolve_model` seam (not the literal `Meta.model`), so the `0.0.12` form / `0.0.13` serializer flavors — whose [`GOAL.md`][goal] declaration omits `Meta.model` — supply it without re-opening the base (Medium-5, [Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root)). Dependent changes: the unique-constraint create error is a `full_clean()` / `validate_constraints()` `ValidationError` (Django 4.1+, floor `>=5.2`) with `IntegrityError` demoted to a documented concurrent-race fallback (Major-2); the post-write re-fetch is **by pk without the visibility filter** — a deliberate, documented exception to [`GOAL.md`][goal] success-criterion 4 (Medium-1, [Decision 9](#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff)); `delete` loads its response-selection relations *before* `delete()` since the optimizer plans querysets, not instances (Medium-2); partial update validates with `full_clean(exclude=<unprovided>)` (Medium-3) — all in [Decision 8](#decision-8--resolver-pipeline-decode--full_clean--write--optimizer-refetch--payload-sync-and-async). Minor corrections: the `input_class` criterion (a `@strawberry.input` type, not "registered"), the auth card number (`040`, not `039`), a `README.md` roadmap-drift watch-out for Slice 5, and "module-for-module" softened to "in the spirit of" (the `mutations/` module names differ from `filters/`).

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoMutation`][glossary-djangomutation] — the subject. The glossary already pins its planned contract: a base class with `Meta`-driven configuration, auto-generated `Input` / `PartialInput`, the shared `FieldError` envelope, sync + async resolver paths, and optimizer composition for the post-write return value. This card ships exactly that contract; the entry is promoted from `planned for 0.0.11` to `shipped (0.0.11)` in Slice 5.
- [Input type generation][glossary-input-type-generation] — the surface Slice 1 builds. The entry pins two generated types: `Input` (every field required, matching `Model.objects.create(...)` semantics) and `PartialInput` (every field optional, matching `Model.objects.update(...)` semantics), both preserving the relation-override contract from the foundation slice. [Decision 6](#decision-6--auto-generated-input--partialinput-types) realizes it.
- [`FieldError` envelope][glossary-fielderror-envelope] — the shared error contract. `errors: list[FieldError]` returned by every mutation flavor, each `FieldError` carrying a `field` path and `messages: list[str]`, populated from `form.errors` / `serializer.errors` / a `ValidationError` raised inside the write path. This card **defines and freezes** it ([Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)) so [`DjangoFormMutation`][glossary-djangoformmutation] (`0.0.12`) and [`SerializerMutation`][glossary-serializermutation] (`0.0.13`) reuse the byte-identical type.
- [`DjangoType`][glossary-djangotype] / [`Meta.primary`][glossary-metaprimary] / [`Meta.model`][glossary-metamodel] / [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] — the type system the mutation target rides. The **return type** resolves the model's **primary** `DjangoType` through the registry primary lookup ([Decision 11](#decision-11--primary-type-resolution-return-type-and-input-target-resolve-the-models-primary-djangotype)); the **input-field set**, by contrast, derives from the model's *editable* fields narrowed by the mutation's own `Meta.fields` / `Meta.exclude` — **not** the read `DjangoType` selection ([Decision 6](#decision-6--auto-generated-input--partialinput-types), Medium-4).
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] / [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — the permission seams `update` / `delete` lookups compose with. A `DjangoMutation` cannot mutate a row the target type's `get_queryset` (plus any cascade) hides; the lookup runs through the same visibility queryset every read surface uses, so a hidden row is "not found", never an existence leak ([Decision 10](#decision-10--permission-composition-update--delete-lookups-run-through-the-target-get_queryset)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] / [`only()` projection][glossary-only-projection] / [FK-id elision][glossary-fk-id-elision] / [Queryset diffing][glossary-queryset-diffing] — the post-write re-fetch cooperation. The mutated row is re-fetched as a queryset the optimizer plans for the response selection. Because the operation is a **mutation**, the [`spec-035`][spec-035] **G2** gate keeps `select_related` / `prefetch_related` but suppresses `.only(...)` column deferral — so the re-fetched instance carries no selection-shaped deferred-field set and post-write consumer code touching an unprojected field never triggers a deferred refetch or a deferred-instance partial `save()` ([Decision 9](#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff)).
- [`DjangoConnectionField`][glossary-djangoconnectionfield] / [`DjangoListField`][glossary-djangolistfield] / [`DjangoNodeField`][glossary-djangonodefield] — the existing field-factory family `DjangoMutationField` joins. Each is a factory assigned to a class attribute on an `@strawberry.type`; the write-side factory follows the same idiom rather than inventing a decorator ([Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root)).
- [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] / [`RelatedFilter`][glossary-relatedfilter] — the prior set-family subsystems whose layout, finalizer phase-2.5 binding, stable class-derived input naming, and materialize-before-`Schema` lifecycle this card mirrors ([Decision 4](#decision-4--module-and-test-locations-mutations-subpackage-mirroring-filters--orders) / [Decision 12](#decision-12--finalization-seam-register-at-class-creation-bind-at-phase-25-no-deferred_meta_keys-change)).
- [`finalize_django_types`][glossary-finalize_django_types] / [Definition-order independence][glossary-definition-order-independence] — the once-only finalization gate the mutation binding hangs off; generated input / payload classes must be materialized before `strawberry.Schema(...)` runs, exactly as the filter / order input classes are.
- [`ConfigurationError`][glossary-configurationerror] / [`SyncMisuseError`][glossary-syncmisuseerror] — the two validation / misuse exceptions this card raises: `ConfigurationError` at mutation-class creation (bad `Meta`, unknown operation, model with no registered primary type), and `SyncMisuseError` when a sync write path meets an `async def` target `get_queryset` (the same discipline the Relay node defaults and the cascade helper already follow).
- [Scalar field conversion][glossary-scalar-field-conversion] / [Choice enum generation][glossary-choice-enum-generation] / [Specialized scalar conversions][glossary-specialized-scalar-conversions] / [`auto`-typed annotations][glossary-auto-typed-annotations] — the converters the input generator reuses; a model field becomes an input field of the same scalar / enum the read-side `DjangoType` would synthesize, so the wire contract is symmetric across read and write.
- [`Upload` scalar][glossary-upload-scalar] / [`DjangoFileType`][glossary-djangofiletype] / [`DjangoImageType`][glossary-djangoimagetype] — the sibling `0.0.11` card ([`TODO-ALPHA-037-0.0.11`][kanban]); it maps `FileField` / `ImageField` to `Upload` on the **input** side this card generates, so the two cards share the `0.0.11` cut and a thin input-converter seam ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0011-cut), [Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- [`DjangoFormMutation`][glossary-djangoformmutation] / [`DjangoModelFormMutation`][glossary-djangomodelformmutation] / [`SerializerMutation`][glossary-serializermutation] / [Auth mutations][glossary-auth-mutations] — the downstream flavor cards (`0.0.12` / `0.0.13`) that consume this card's `DjangoMutation` base and `FieldError` envelope unchanged; named here only to fix the reuse contract this card freezes.
- [Per-field permission hooks][glossary-per-field-permission-hooks] / [`FieldSet`][glossary-fieldset] / [Cross-subsystem invariants][glossary-cross-subsystem-invariants] — the `1.0.0` invariant this card must not violate: deferred `Meta` keys are promoted only when their subsystem applies them end-to-end. This card adds no `DjangoType` `Meta` key, so [`DEFERRED_META_KEYS`][types-base] is untouched ([Decision 12](#decision-12--finalization-seam-register-at-class-creation-bind-at-phase-25-no-deferred_meta_keys-change)).

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package-internal mutation mechanics under [`tests/mutations/`][test-mutations] mirroring source; live consumer behavior earned over `/graphql/` in [`examples/fakeshop/test_query/`][test-query-dir]); the live-HTTP-priority coverage rule (the write side **is** live-reachable the moment products exposes a `Mutation`, so Slice 4 is mandatory, not optional — it is also the [`spec-035`][spec-035] G2 handoff); the no-pytest-after-edits rule; the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — Slice 5's release-note edit must be named in its maintainer prompt.
- [`START.md`][start] — "Meta classes everywhere on consumer surfaces. If you find yourself writing stacked Strawberry decorators on a consumer-facing class, stop. That is the strawberry-graphql-django API and the explicit reason this package exists." This is the decisive rule for [Decision 3](#decision-3--class-meta-surface-not-decorators-borrow-the-capabilities-reject-the-decorator-surface). Also: the "behaviorally we copy strawberry-graphql-django's good ideas, surface-wise we copy django-graphene-filters" rule, and the reference-style markdown link convention (defs at the bottom under the 10 canonical group headers).
- [`CONTRIBUTING.md`][contributing] — the 100% coverage target (`fail_under = 100`); every branch of the input generator, the resolver pipeline, and the error path earns coverage in [`tests/mutations/`][test-mutations] plus the live products suite.
- [`docs/TREE.md`][tree] — the target layout already reserves `django_strawberry_framework/mutations/` (planned by this card) and `tests/mutations/`; this card creates those trees and adds no module outside them beyond the products-example wiring.
- [`GOAL.md`][goal] — the `1.0.0` showcase and the DRF-migration shape both spell the mutation surface as `class CreateCategory(DjangoMutation): class Meta: ...` (the serializer flavor lands `0.0.13`); this card ships the model-driven base that shape rests on.

## Slice checklist

Each top-level item maps to one commit / PR. **Five slices: input generation + envelope (Slice 1), the `DjangoMutation` base (Slice 2), the resolvers + field factory (Slice 3), the products live write surface (Slice 4), and the doc + card wrap (Slice 5).** Slices 1–3 are package-internal and mutually staged (each builds on the prior); Slice 4 is the live consumer surface and the [`spec-035`][spec-035] G2 handoff; Slice 5 is doc-only.

- [ ] Slice 1: input-type generation + the `FieldError` envelope + the payload wrapper (per [Decision 6](#decision-6--auto-generated-input--partialinput-types) / [Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper))
  - [ ] [`mutations/inputs.py`][mutations-inputs]: a BFS-free, single-model input factory that, given a model's **editable** fields (narrowed by the mutation's own `Meta.fields` / `Meta.exclude`, **not** the read `DjangoType` selection — Medium-4), generates `<Model>Input` (each field required **only when it has no usable default** — no `default`, `null=False`, `blank=False` — else optional with `strawberry.UNSET`; Major-1) and `<Model>PartialInput` (every field optional, defaulting to `strawberry.UNSET`). Editable-field selection excludes the pk, `auto_now` / `auto_now_add` / `editable=False` columns, and reverse relations; forward FK / OneToOne become a single `<field>_id` input typed as the target's id (`GlobalID` for a Relay-Node target, else the raw pk scalar); M2M becomes `list[<id>]`. Stable class-derived names (`CategoryInput` / `CategoryPartialInput`), materialized as module globals so two mutations over one model resolve to the same input type.
  - [ ] The public `FieldError` `@strawberry.type` (`field: str`, `messages: list[str]`) and the generated `<Name>Payload` wrapper (the mutated object, nullable, plus `errors: list[FieldError]!`).
  - [ ] The relation-override contract from [`spec-010`][spec-010] holds on the input side: a consumer-authored input field is honored, not clobbered by a generated one.
  - [ ] Package coverage: [`tests/mutations/test_inputs.py`][test-mutations] — required/optional field shapes, FK/O2O/M2M id mapping, pk/auto-field exclusion, Relay-vs-non-Relay id type, stable naming, consumer override preserved.
- [ ] Slice 2: the `DjangoMutation` base + `Meta` validation + finalizer binding (per [Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root) / [Decision 12](#decision-12--finalization-seam-register-at-class-creation-bind-at-phase-25-no-deferred_meta_keys-change))
  - [ ] [`mutations/sets.py`][mutations-sets]: `DjangoMutation` + its metaclass — collect `Meta` (`model`, `operation`, optional `input_class` / `partial_input_class` / `fields` / `exclude`), validate at class-creation (unknown `Meta` key; **no resolvable model** — in `0.0.11` a missing `Meta.model`, via the overridable `_resolve_model` seam so the `038` / `039` flavors can supply it differently, [Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root); `operation` not in `{"create", "update", "delete"}`; an `input_class` that is not a `@strawberry.input`-decorated type → [`ConfigurationError`][glossary-configurationerror]), register the mutation, and bind it at [`finalize_django_types`][glossary-finalize_django_types] phase 2.5 (resolve the model's primary type, materialize the generated input / payload classes before `strawberry.Schema(...)`).
  - [ ] No change to [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS`: a mutation `Meta` is its own validation namespace, not a `DjangoType` `Meta` key ([Decision 12](#decision-12--finalization-seam-register-at-class-creation-bind-at-phase-25-no-deferred_meta_keys-change)).
  - [ ] Package coverage: [`tests/mutations/test_sets.py`][test-mutations] — `Meta` validation matrix, registration, finalizer binding, the no-registered-primary-type error.
- [ ] Slice 3: the write resolvers + `DjangoMutationField` + optimizer / permission composition (per [Decision 8](#decision-8--resolver-pipeline-decode--full_clean--write--optimizer-refetch--payload-sync-and-async) / [Decision 9](#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff) / [Decision 10](#decision-10--permission-composition-update--delete-lookups-run-through-the-target-get_queryset))
  - [ ] [`mutations/resolvers.py`][mutations-resolvers]: the sync + async create / update / delete pipeline — decode the `data:` input (and `id:` for update / delete), run `full_clean()` (`exclude=<unprovided>` on update — Medium-3), write, re-fetch through the optimizer, return the payload; a Django `ValidationError` — including the `validate_constraints()` `UniqueConstraint` violation caught before `save()` (Major-2) — populates the `FieldError` envelope and returns the payload with a null object, and a concurrent-race `IntegrityError` at `save()` maps to the same envelope as a documented fallback.
  - [ ] [`mutations/fields.py`][mutations-fields]: `DjangoMutationField(MutationClass)` — the field factory (the write-side sibling of [`DjangoConnectionField`][glossary-djangoconnectionfield]) that synthesizes the resolver signature (`data: <Model>Input!` / `<Model>PartialInput!` + `id:` per operation) and returns a `strawberry.field(...)`; sync and async resolvers chosen by the same `is_async_callable` (construction-time, consumer resolver) / `in_async_context()` (runtime, default resolver) async-detection asymmetry [`DjangoListField`][glossary-djangolistfield] uses.
  - [ ] `update` / `delete` lookups run through `target_type.get_queryset(...)` (a hidden row is "not found", no existence leak — [Decision 10](#decision-10--permission-composition-update--delete-lookups-run-through-the-target-get_queryset)); the post-write re-fetch keeps `select_related` / `prefetch_related` with **no** `.only(...)` deferral under the mutation operation ([`spec-035`][spec-035] G2 — [Decision 9](#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff)).
  - [ ] Package coverage: [`tests/mutations/test_resolvers.py`][test-mutations] + [`tests/mutations/test_fields.py`][test-mutations] — create/update/delete happy paths, validation-error envelope, hidden-row not-found, sync + async, and the plan-shape pin (mutation re-fetch carries select/prefetch, no deferred loading).
- [ ] Slice 4: the products live write surface — **discharges the [`spec-035`][spec-035] G2 live-test handoff** (per [Decision 9](#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff))
  - [ ] `examples/fakeshop/apps/products/schema.py`: a `Mutation` type with `create_item` / `update_item` / `delete_item` (and at least one `Category` write) as `DjangoMutationField`s; `config/schema.py` wires `mutation=Mutation` into `strawberry.Schema(...)`.
  - [ ] [`test_products_api.py`][test-products-api]: live `/graphql/` create / update / delete coverage, the validation-error envelope, the permission-scoped update/delete (a `view_<model>` user cannot update a private row), and a `CaptureQueriesContext` SQL-shape assertion that a mutation response keeps `select_related` / `prefetch_related` and carries **no** deferred loading — the exact assertion the [`spec-035`][spec-035] Slice 2 test plan hands forward to "the first card that adds a fakeshop mutation returning a queryset".
- [ ] Slice 5: doc updates + card-completion wrap (per [Doc updates](#doc-updates))
  - [ ] [`docs/GLOSSARY.md`][glossary] (promote [`DjangoMutation`][glossary-djangomutation] / [Input type generation][glossary-input-type-generation] / [`FieldError` envelope][glossary-fielderror-envelope] to `shipped (0.0.11)`, add the net-new `DjangoMutationField` entry, and append the G2-handoff-discharged note to the [`only()` projection][glossary-only-projection] entry), [`docs/README.md`][docs-readme] / [`README.md`][readme] (move mutations from "Coming next" to "Shipped today"), [`GOAL.md`][goal] (the DRF-migration mutation diff now references a shipped base), [`TODAY.md`][today] (products now demonstrates a write surface), [`CHANGELOG.md`][changelog] (only if the Slice 5 maintainer prompt explicitly requests it), [`KANBAN.md`][kanban] (card → Done via the kanban DB + re-render). **No version-file edits** ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0011-cut)).

## Problem statement

The package has no write side. Every shipped surface — [`DjangoType`][glossary-djangotype], the optimizer, [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset], the Relay connection / node fields, the cascade permissions — is read-only. A consumer migrating from [`strawberry-graphql-django`][upstream-mutations] (which ships `create` / `update` / `delete`, custom mutations, and auto-generated `Input` / `PartialInput` types) or from `graphene-django` (which ships `DjangoModelFormMutation` / `SerializerMutation`) reaches the package and immediately hits a wall: there is no way to create, update, or delete a row through GraphQL. The card names this "the single largest unscoped gap against `strawberry-graphql-django`."

Three properties make the gap more than "add a resolver":

- **Input types must be generated, not hand-written.** A `Model.objects.create(...)` call needs an `Input` whose fields match the model's editable columns, with relations expressed as ids; the update path needs a `PartialInput` whose fields are all optional. Hand-declaring these per model re-introduces exactly the duplicate-field-definition burden the package exists to remove ([`GOAL.md`][goal] success-criterion 6: "no parallel field definitions"). They must derive from `Meta.model` and reuse the same scalar / relation converters the read side uses, so read and write share one wire contract.
- **Errors need a shared, typed envelope.** Validation failure must surface field-keyed messages, not a generic 500. graphene-django's `ErrorType` (a `field` name + a list of message strings) is the parity shape; the card mandates "one shared `errors: list[FieldError]` envelope across every flavor", reused unchanged by the form (`0.0.12`) and serializer / auth (`0.0.13`) cards. Defining it inconsistently now would fork the client contract across flavors forever.
- **The write side must compose with what already shipped.** A mutation that returns a queryset hits the optimizer ([`spec-035`][spec-035]'s **G2** gate exists *specifically because* this card makes that path mainstream); an `update` / `delete` must not mutate a row the target type's [`get_queryset`][glossary-get_queryset-visibility-hook] + [`apply_cascade_permissions`][glossary-apply_cascade_permissions] hide; the return / input target must resolve the model's **primary** [`DjangoType`][glossary-metaprimary]. None of these compositions exist yet, and getting any wrong bakes a correctness or security hole into the first write surface consumers touch.

This is a Required `strawberry-graphql-django` parity item (the card's own tag), foundational by the [`START.md`][start] "do both libraries provide it?" test — graphene-django and strawberry-graphql-django both ship mutations.

## Current state

A true description of the repo as this spec is authored:

- **No `mutations/` module, no write resolvers, no input generation.** [`docs/TREE.md`][tree]'s *target* layout reserves `django_strawberry_framework/mutations/` and `tests/mutations/` (both "planned by `TODO-ALPHA-036-0.0.11`"); neither exists on disk. The package root [`__init__.py`][init] exports no mutation symbol and `__all__` names none.
- **The set-family layout is the precedent.** [`filters/`][filters-sets] and [`orders/`][filters-sets] are each a four-module subpackage (`base.py` / `factories.py` / `inputs.py` / `sets.py`) with a metaclass-driven declarative class, a finalizer phase-2.5 binding pass ([`finalize_django_types`][glossary-finalize_django_types]), stable class-derived input names materialized as module globals before `strawberry.Schema(...)`, and a `tests/<subsystem>/` mirror. [`sets_mixins.py`][sets-mixins] hosts the lifecycle machinery shared across the FilterSet / OrderSet family; `mutations/` slots beside them.
- **The Meta-key machinery is stable and must not move.** [`types/base.py`][types-base] holds `DEFERRED_META_KEYS = {"aggregate_class", "fields_class", "search_fields"}` and `ALLOWED_META_KEYS`; a mutation does not add a `DjangoType` `Meta` key, so neither set changes ([Decision 12](#decision-12--finalization-seam-register-at-class-creation-bind-at-phase-25-no-deferred_meta_keys-change)).
- **The G2 gate is already in place and waiting for this card.** [`spec-035`][spec-035] shipped the operation-type `.only()` gate ([`walker.py::_enable_only_for_operation`][walker]) in `0.0.10`, explicitly "sequencing-critical *because of*" the `0.0.11` mutations cohort, and its Slice 2 test plan records a **mandatory live-test handoff**: "the first card that adds a fakeshop mutation returning a queryset **must** add a live `examples/fakeshop/test_query/` acceptance test proving the mutation queryset response keeps `select_related` / `prefetch_related` with no deferred loading." This card is that card; Slice 4 discharges the obligation.
- **The permission seam is shipped.** [`apply_cascade_permissions`][glossary-apply_cascade_permissions] ([`DONE-034-0.0.10`][kanban], [`permissions.py`][permissions]) and the [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] are live; the four products [`schema.py`][products-schema] types already call the cascade inside their hooks, so the products write surface inherits visibility scoping for free once `update` / `delete` route their lookups through `get_queryset` ([Decision 10](#decision-10--permission-composition-update--delete-lookups-run-through-the-target-get_queryset)).
- **`Meta.primary` resolution is shipped.** [`registry.py::TypeRegistry`][registry] resolves a model's primary type via `get(model)` / `primary_for(model)` ([`DONE-018-0.0.6`][kanban]); the mutation return / input target uses the same lookup auto-synthesized relation fields use.
- **The products write target is connections-only today.** [`products/schema.py`][products-schema]'s `Query` is four `DjangoConnectionField`s and there is **no** `Mutation` type; `config/schema.py` constructs `strawberry.Schema(query=..., ...)` with no `mutation=`. Slice 4 adds both. The four models ([`Category`][products-models] / `Item` / `Property` / `Entry`) are plain editable Django models with FK relations and `UniqueConstraint`s — a realistic write surface (the `unique_item_per_category` constraint exercises the create error path).
- **The sibling `0.0.11` card is unshipped.** [`TODO-ALPHA-037-0.0.11`][kanban] ([`Upload` scalar][glossary-upload-scalar] + file/image mapping) is planned, not started; it maps `FileField` / `ImageField` to `Upload` on the input side this card generates. The two share the `0.0.11` cut ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0011-cut)).

## Goals

1. **Ship the `DjangoMutation` base on the `class Meta` surface.** A consumer declares a mutation as a class with a nested `Meta` (`model` + `operation`), not a Strawberry decorator — the package's defining surface contract ([Decision 3](#decision-3--class-meta-surface-not-decorators-borrow-the-capabilities-reject-the-decorator-surface) / [Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root)).
2. **Auto-generate `Input` and `PartialInput`.** Derive both from `Meta.model`, honoring the relation-override contract from [`spec-010`][spec-010], with stable class-derived names and the read-side scalar / relation converters reused ([Decision 6](#decision-6--auto-generated-input--partialinput-types)).
3. **Define and freeze the shared `FieldError` envelope.** A public `FieldError` (`field` + `messages`) plus the `errors: list[FieldError]` payload contract, reused unchanged by the `0.0.12` / `0.0.13` flavor cards ([Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)).
4. **Ship `create` / `update` / `delete` resolvers, sync and async.** With `full_clean()` validation feeding the error envelope, and the optimizer re-fetching the post-write row for the response selection ([Decision 8](#decision-8--resolver-pipeline-decode--full_clean--write--optimizer-refetch--payload-sync-and-async)).
5. **Compose with the optimizer and discharge the G2 handoff.** The mutation re-fetch keeps `select_related` / `prefetch_related` and carries no `.only(...)` deferral under the mutation operation, proven by the live products SQL-shape test the [`spec-035`][spec-035] handoff mandates ([Decision 9](#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff)).
6. **Compose with permissions.** `update` / `delete` lookups run through the target type's `get_queryset` + cascade, so a hidden row is never mutable and never leaks its existence ([Decision 10](#decision-10--permission-composition-update--delete-lookups-run-through-the-target-get_queryset)).
7. **Ship the products live write surface.** Products gains a `Mutation` proving the whole pipeline end-to-end over `/graphql/` (Slice 4).
8. **Keep package version state owned by the joint `0.0.11` cut.** No slice edits `pyproject.toml`, `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock` ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0011-cut)).

## Non-goals

- **File / image upload inputs.** The [`Upload` scalar][glossary-upload-scalar] + `FileField` / `ImageField` mapping is the sibling `0.0.11` card ([`TODO-ALPHA-037-0.0.11`][kanban]); this card generates inputs for the shipped scalar / relation set and leaves a thin converter seam for 037 to plug `Upload` into ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **Form-based mutations.** [`DjangoFormMutation`][glossary-djangoformmutation] / [`DjangoModelFormMutation`][glossary-djangomodelformmutation] (Django `Form` / `ModelForm` validation feeding the same envelope) are `0.0.12` ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **DRF serializer mutations and auth mutations.** [`SerializerMutation`][glossary-serializermutation] (`Meta.serializer_class`, `lookup_field`, `model_operations`) and [Auth mutations][glossary-auth-mutations] (`login` / `logout` / `register`) are `0.0.13`; this card freezes the `FieldError` envelope they consume but ships neither.
- **Relay `clientMutationId` / single-input-mutation wrapping.** graphene-django's `ClientIDMutation` `clientMutationId` round-trip and strawberry-django's `input_mutation` single-`input`-argument shape are not adopted in `0.0.11` ([Decision 14](#decision-14--single-data-argument-no-relay-clientmutationid-in-0011)).
- **Bulk / batch mutations, nested writes, and `full_clean` opt-out granularity.** Upstream's nested-object create (`ParsedObject` / `ParsedObjectList`) and `FullCleanOptions` are out; `0.0.11` writes one root model with relations expressed as existing ids ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **A new `DjangoType` `Meta` key or settings key.** The mutation `Meta` is the mutation class's own namespace; no `DjangoType` `Meta` key and no `DJANGO_STRAWBERRY_FRAMEWORK` entry is added ([`AGENTS.md`][agents] #"Add settings keys only when the feature that needs them lands").
- **A version bump.** Owned by the joint `0.0.11` cut ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0011-cut)).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it? → foundational" test, mutations are **Required `strawberry-graphql-django` parity** (the card's own 🍓 Required tag) and graphene-django provides them too. The borrowing splits cleanly along the package's standing line — *behaviorally* copy `strawberry-graphql-django`'s good ideas; *surface-wise* copy `django-graphene-filters` / DRF (`class Meta`). The runtime capabilities (create / update / delete, auto-generated `Input` / `PartialInput`, the `handle_django_errors` → typed-error path, optimizer-composed return value) are adopted at the **outcome** level from strawberry-django; the consumer-facing **shape** (a base class with a nested `Meta`, a field factory on the schema's `Mutation` type, the `ErrorType`-shaped `FieldError`) is the graphene-django / DRF surface. The decorator / field-verb mechanism strawberry-django uses (`@strawberry_django.input`, `create()` / `update()` / `delete()`) is **explicitly rejected** — it is the exact API the package exists to replace.

### Reference-package parity checkpoint

| Upstream | `django-strawberry-framework` | Status |
| --- | --- | --- |
| [`strawberry_django.create` / `update` / `delete`][upstream-mutations] field-verb factories + `@strawberry_django.input` decorators | `DjangoMutation` base + `Meta.operation` selector + `DjangoMutationField` factory ([Decision 3](#decision-3--class-meta-surface-not-decorators-borrow-the-capabilities-reject-the-decorator-surface) / [Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root)) | this card — borrow the operations, reject the decorator surface |
| [strawberry-django auto-generated `Input` / `PartialInput`][upstream-mutations] from a model | generated `<Model>Input` / `<Model>PartialInput` from `Meta.model`, read-side converters reused ([Decision 6](#decision-6--auto-generated-input--partialinput-types)) | this card — required parity |
| [graphene-django `ErrorType`][graphene-rest-mutation] (`field: String!` + `messages: [String!]!`) on the mutation payload | public `FieldError` (`field` + `messages: list[str]`), `errors: list[FieldError]` on the `<Name>Payload` ([Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)) | this card — defined and frozen for reuse |
| [strawberry-django `handle_django_errors` → `Type \| OperationInfo` union][upstream-mutations] | payload wrapper carrying object + `errors` (graphene-django shape), not a disjoint union ([Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)) | borrow the error-capture outcome, not the union surface |
| [strawberry-django `full_clean` validation + optimizer-composed return][upstream-mutations] | `full_clean()` feeding the envelope; post-write re-fetch through [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] under the G2 mutation gate ([Decision 8](#decision-8--resolver-pipeline-decode--full_clean--write--optimizer-refetch--payload-sync-and-async) / [Decision 9](#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff)) | this card — required parity |
| [graphene-django `DjangoModelFormMutation` / `SerializerMutation`][graphene-rest-mutation] `Meta`-driven flavors | the same `DjangoMutation` base + `Meta`; the form (`0.0.12`) and serializer (`0.0.13`) flavors subclass it | deferred (flavor cards) — the base ships here |
| graphene-django `ClientIDMutation` `clientMutationId` round-trip | not adopted ([Decision 14](#decision-14--single-data-argument-no-relay-clientmutationid-in-0011)) | deliberate non-adoption |

### From `strawberry-graphql-django` — borrow the runtime, not the surface

- **Operations.** `create` / `update` / `delete` as the three foundational operations, each with model-derived input and a `full_clean()` validation pass — adopted; the field-verb factories that spell them are not.
- **Input generation.** Model → `Input` (required) / `PartialInput` (optional) with relations as ids — adopted; strawberry-django's nested-object `ParsedObject` / `ParsedObjectList` (nested create/connect/disconnect) is deferred ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **Optimizer-composed return.** The post-write row is re-fetched and optimizer-planned for the response selection — adopted, and refined by the package's own G2 gate so the mutation re-fetch never carries a `.only(...)` deferral ([Decision 9](#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff)).

### From `graphene-django` / DRF — borrow the user-facing shape

- **The `class Meta` declaration.** A `DjangoMutation` subclass with a nested `Meta`, parallel to `DjangoModelFormMutation` / `SerializerMutation`; the DRF / `django-graphene-filters` shape every other consumer surface in the package already uses.
- **The `ErrorType` envelope.** `FieldError` is graphene-django's `ErrorType` (a `field` name + a list of message strings), the shape the card pins for cross-flavor reuse.

### Explicitly do not borrow

- **The decorator / field-verb surface** (`@strawberry_django.input`, `create()` / `update()` / `delete()`) — the exact API [`START.md`][start] names as "the explicit reason this package exists"; the `class Meta` base class replaces it.
- **The disjoint `Type | OperationInfo` union return** — rejected for the graphene-django payload-with-`errors` shape the card's `FieldError` parity implies ([Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)).
- **The Graphene runtime** (`ClientIDMutation`, `clientMutationId`, relay-mutation argument wrapping) — Strawberry stays the engine; the Relay mutation conventions are not adopted in `0.0.11` ([Decision 14](#decision-14--single-data-argument-no-relay-clientmutationid-in-0011)).

## User-facing API

One new base class, one new field factory, and one new public payload type — no new `DjangoType` `Meta` key, no constructor argument on existing surfaces. The canonical consumer surface declares the mutation with a nested `Meta` and exposes it on the schema's `Mutation` type through the factory, mirroring the read-side `DjangoConnectionField` idiom:

```python
import strawberry

from django_strawberry_framework import DjangoMutation, DjangoMutationField

from . import models
from .schema import ItemType  # the model's primary DjangoType


class CreateItem(DjangoMutation):
    class Meta:
        model = models.Item
        operation = "create"


class UpdateItem(DjangoMutation):
    class Meta:
        model = models.Item
        operation = "update"


class DeleteItem(DjangoMutation):
    class Meta:
        model = models.Item
        operation = "delete"


@strawberry.type
class Mutation:
    # No class-attribute annotation: the return payload is generated at
    # finalization and cannot be named at import, so the factory types the
    # field itself via a `strawberry.lazy` forward-ref (Decision 7).
    create_item = DjangoMutationField(CreateItem)
    update_item = DjangoMutationField(UpdateItem)
    delete_item = DjangoMutationField(DeleteItem)
```

The generated schema fields are:

```graphql
type Mutation {
  createItem(data: ItemInput!): CreateItemPayload!
  updateItem(id: GlobalID!, data: ItemPartialInput!): UpdateItemPayload!
  deleteItem(id: GlobalID!): DeleteItemPayload!
}

input ItemInput {
  name: String!
  description: String
  categoryId: GlobalID!
  isPrivate: Boolean
}

input ItemPartialInput {
  name: String
  description: String
  categoryId: GlobalID
  isPrivate: Boolean
}

type FieldError {
  field: String!
  messages: [String!]!
}

type CreateItemPayload {
  item: ItemType
  errors: [FieldError!]!
}
```

`ItemInput` carries the model's **editable** columns with each field required **only when it has no usable default** — no Django `default`, not `null=True`, and (for text fields) not `blank=True` — so `name` / `categoryId` are required while `description` (`blank=True, default=""`) and `isPrivate` (`default=False`) are optional even in the create input (the DRF `required=False`-from-`default`/`blank`/`null` rule, [Decision 6](#decision-6--auto-generated-input--partialinput-types)). `ItemPartialInput` carries them all optional (the `update` shape). The forward FK `category` becomes `categoryId: GlobalID!` (the target's id type — `GlobalID` because `ItemType` is Relay-Node-shaped, the raw pk scalar otherwise). The `Mutation` field is assigned with **no** class-attribute annotation (`create_item = DjangoMutationField(CreateItem)`); the factory types it from the generated `<Name>Payload` via a `strawberry.lazy` forward-ref ([Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)). On success the payload's `item` is the optimizer-re-fetched node and `errors` is empty; on a `full_clean()` failure `item` is `null` and `errors` carries one `FieldError` per offending field. `update` / `delete` resolve the row through `ItemType.get_queryset(...)`, so a row the caller cannot see is "not found" (a single `FieldError` on the `id` field), never an existence leak. The async surface is automatic — a `DjangoMutationField` over an async-context schema awaits the same pipeline.

Supplying a hand-written input instead of the generated one:

```python
class CreateItem(DjangoMutation):
    class Meta:
        model = models.Item
        operation = "create"
        input_class = MyHandWrittenItemInput   # overrides the generated ItemInput
```

### Error shapes

- A `Meta` from which **no model can be resolved** (in `0.0.11`, a missing `Meta.model` — the `0.0.12` / `0.0.13` flavor cards supply it via `form_class` / `serializer_class` through the `_resolve_model` seam, [Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root)), naming an `operation` not in `{"create", "update", "delete"}`, carrying an unknown `Meta` key, or referencing an `input_class` / `partial_input_class` that is not a `@strawberry.input`-decorated type raises [`ConfigurationError`][glossary-configurationerror] at mutation-class creation, naming the offending key.
- A `DjangoMutation` over a model with no registered (or no **primary**) [`DjangoType`][glossary-djangotype] raises [`ConfigurationError`][glossary-configurationerror] at [`finalize_django_types`][glossary-finalize_django_types] (the return type and input target cannot be resolved) — the same finalize-time fail-loud the relation finalizer uses ([Decision 11](#decision-11--primary-type-resolution-return-type-and-input-target-resolve-the-models-primary-djangotype)).
- A model `ValidationError` from `full_clean()` — including a `UniqueConstraint` violation, which `validate_constraints()` catches before `save()` (Major-2) — is **not** an exception at the GraphQL boundary; it populates `errors: list[FieldError]` and returns the payload with a null object. A concurrent-race `IntegrityError` at `save()` maps to the same envelope as a documented best-effort fallback ([Decision 8](#decision-8--resolver-pipeline-decode--full_clean--write--optimizer-refetch--payload-sync-and-async)).
- A sync mutation resolver whose target type has an `async def get_queryset` raises [`SyncMisuseError`][glossary-syncmisuseerror] (coroutine closed first, no `RuntimeWarning`), pointing the consumer at an async schema or a sync hook — the same discipline the Relay node defaults and [`apply_cascade_permissions`][glossary-apply_cascade_permissions] follow ([Decision 8](#decision-8--resolver-pipeline-decode--full_clean--write--optimizer-refetch--payload-sync-and-async)).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/spec-036-mutations-0_0_11.md`** (this document).

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `TODO-ALPHA-036-0.0.11`, so `<NNN>` is `036` and `<0_0_X>` is `0_0_11`.
- The topic slug is `mutations` — the subsystem name, and the stem of the card DoD's suggested `docs/spec-mutations.md`.

Alternatives considered (and rejected):

- **The card's own `docs/spec-mutations.md`.** Rejected: predates the structured-filename convention; [`spec-034`][spec-034] Decision 1 (and `spec-033`, `spec-035` before it) set the precedent of preferring the structured name and recording the card's older one.
- **Topic slug `mutations_foundation` / `django_mutation`.** Rejected: the subsystem is "mutations"; the foundation framing belongs in the scope boundary ([Decision 2](#decision-2--card-scope-boundary-the-mutation-foundation-ships-the-flavor-cards-and-uploads-are-out-the-fielderror-envelope-is-frozen-here)), not the filename.

### Decision 2 — Card-scope boundary: the mutation foundation ships; the flavor cards and uploads are out; the `FieldError` envelope is frozen here

This card ships the **model-driven mutation foundation** end-to-end: the [`DjangoMutation`][glossary-djangomutation] base, [auto-generated `Input` / `PartialInput`][glossary-input-type-generation], `create` / `update` / `delete` resolvers (sync + async), the [`FieldError` envelope][glossary-fielderror-envelope], optimizer + permission composition, and the products live write surface. It explicitly does **not** ship the adjacent flavors, each owned by a named card:

- **Uploads** ([`Upload` scalar][glossary-upload-scalar], [`DjangoFileType`][glossary-djangofiletype] / [`DjangoImageType`][glossary-djangoimagetype]) — the sibling `0.0.11` card [`TODO-ALPHA-037-0.0.11`][kanban]. This card leaves an input-converter seam (a per-field-type input mapping) so 037 plugs `Upload` in without re-opening the generator.
- **Form-based mutations** ([`DjangoFormMutation`][glossary-djangoformmutation] / [`DjangoModelFormMutation`][glossary-djangomodelformmutation]) — `0.0.12`.
- **DRF serializer + auth mutations** ([`SerializerMutation`][glossary-serializermutation], [Auth mutations][glossary-auth-mutations]) — `0.0.13`.

The **`FieldError` envelope is defined and frozen in this card** for the downstream flavor cohorts that consume it — the form-based (`0.0.12`) and DRF-serializer / auth (`0.0.13`) cards (the [`Upload` scalar][glossary-upload-scalar] sibling `0.0.11` card does **not** touch the envelope) — mirroring [`spec-034`][spec-034] Decision 2's "define the surface here, implement the rest later" move (there: the per-field read gate signature was pinned in `0.0.10` and implemented with `FieldSet` in `0.1.1`). The card DoD makes the reuse explicit ("reused unchanged by `TODO-ALPHA-039-0.0.13`, `TODO-ALPHA-038-0.0.12`"); freezing it now is the only way the flavor cards inherit one client contract instead of three.

Justification: the card is XL and the form / serializer / upload flavors are separately carded with their own `0.0.12` / `0.0.13` / `0.0.11` targets — pulling any forward would bloat the slice exactly as [`START.md`][start]'s scope-creep rule warns. The base + envelope + model-driven operations are the irreducible foundation the flavors all subclass.

Alternatives considered (and rejected):

- **Ship the form flavor in this card too** (it is "close").** Rejected: `DjangoFormMutation` is its own `0.0.12` card with its own DoD; the form-validation-to-`FieldError` mapping is a distinct slice, and the base must exist first.
- **Defer the `FieldError` envelope to the first flavor card.** Rejected: the card DoD pins it here precisely so the flavors reuse it unchanged; deferring it forks the contract.

### Decision 3 — `class Meta` surface, not decorators: borrow the capabilities, reject the decorator surface

A `DjangoMutation` is a **base class with a nested `class Meta`**, declared and exposed exactly like every other consumer surface in the package. It is **not** a Strawberry / strawberry-django decorator (`@strawberry_django.input`, `create()` / `update()` / `delete()` field verbs).

Justification: this is the package's defining surface contract, stated verbatim in [`START.md`][start] — "Meta classes everywhere on consumer surfaces. If you find yourself writing stacked Strawberry decorators on a consumer-facing class, stop. That is the strawberry-graphql-django API and the explicit reason this package exists." [`GOAL.md`][goal]'s `1.0.0` showcase and DRF-migration diff both spell the write surface as `class CreateCategory(DjangoMutation): class Meta: ...`. The *capabilities* of upstream's decorators (operations, input generation, error capture, optimizer return) are borrowed at the outcome level ([Borrowing posture](#borrowing-posture)); the decorator mechanism is not.

Alternatives considered (and rejected):

- **strawberry-django's `create(InputType)` field-verb factories.** Rejected: that *is* the decorator-adjacent surface the package replaces; it also requires the consumer to hand-declare the input type (`@strawberry_django.input`), re-introducing the duplicate-field burden.
- **A `@django_mutation` class decorator** (Meta-shaped config, decorator trigger). Rejected: a decorator on a consumer class is exactly the shape [`START.md`][start] forbids; the base-class form is uniform with `DjangoType` / `FilterSet` / `OrderSet`.

### Decision 4 — Module and test locations: `mutations/` subpackage mirroring `filters/` / `orders/`

- **Source:** `django_strawberry_framework/mutations/` — the subpackage directory [`docs/TREE.md`][tree]'s target layout reserves, split four ways in the spirit of the [`filters/`][filters-sets] / [`orders/`][filters-sets] subpackages (a four-module declarative-set shape, though the module names differ — `inputs` / `sets` / `resolvers` / `fields` here vs. `base` / `factories` / `inputs` / `sets` there; TREE reserves only the `mutations/` directory, and the four-module split is the set-family precedent, not a TREE enumeration): [`inputs.py`][mutations-inputs] (input + payload + `FieldError` generation), [`sets.py`][mutations-sets] (`DjangoMutation` + metaclass + `Meta` validation + finalizer binding), [`resolvers.py`][mutations-resolvers] (the sync + async write pipeline), and [`fields.py`][mutations-fields] (`DjangoMutationField`). It reuses [`sets_mixins.py`][sets-mixins] where the lifecycle machinery is genuinely shared.
- **Tests:** new [`tests/mutations/`][test-mutations] mirroring the source modules (`test_inputs.py` / `test_sets.py` / `test_resolvers.py` / `test_fields.py`), per the one-to-one rule; composition pins that belong to other surfaces extend those surfaces' files ([`tests/optimizer/test_walker.py`][walker] for the G2 plan-shape, [`tests/test_permissions.py`][permissions] for the lookup-scoping pin); live coverage extends [`test_products_api.py`][test-products-api].

Justification: the card predicts `django_strawberry_framework/mutations/` and `tests/mutations/`; the set-family precedent ([`spec-027`][spec-027] / [`spec-028`][spec-028] Decision 2) is the proven shape for a declarative `class Meta` subsystem with generated input classes and finalizer binding. A four-module split keeps generation, declaration, resolution, and field-exposure separable for the flavor cards to extend.

Alternatives considered (and rejected):

- **A flat `mutations.py` module** (like [`permissions.py`][permissions]). Rejected: permissions is two functions; mutations is generation + a metaclass + a resolver pipeline + a field factory + downstream-flavor extension points — a subpackage matches the surface, and the card itself predicts `mutations/`.
- **Folding input generation into the existing [`filters/inputs.py`][filters-sets] substrate.** Rejected: filter inputs are lookup-shaped (`{exact, icontains, ...}`); mutation inputs are model-column-shaped; the [`utils/inputs.py`][utils-inputs] shared substrate is reused where it fits, but the mutation factory is its own concern.

### Decision 5 — Public surface: `DjangoMutation` base + `DjangoMutationField` factory + `FieldError`, exported from the root

Three net-new public symbols, re-exported from [`django_strawberry_framework/__init__.py`][init] and added to `__all__`:

- `DjangoMutation` — the base class.
- `DjangoMutationField` — the field factory that exposes a mutation on the schema's `Mutation` type, the write-side sibling of [`DjangoConnectionField`][glossary-djangoconnectionfield] / [`DjangoListField`][glossary-djangolistfield] / [`DjangoNodeField`][glossary-djangonodefield] (all factories assigned to class attributes on an `@strawberry.type`). Unlike those read-side factories — which read the consumer's class-attribute annotation for the field type — `DjangoMutationField` is assigned **without** an annotation (`create_item = DjangoMutationField(CreateItem)`) and types the field itself from the generated `<Name>Payload` via a `strawberry.lazy` forward-ref; an eager `create_item: CreateItem.Payload` annotation cannot exist at import (see [Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)).
- `FieldError` — the public `@strawberry.type` (`field: str`, `messages: list[str]`) consumers reference in the payload contract.

The operation is selected by `Meta.operation` ∈ `{"create", "update", "delete"}` (a single string key), not a separate base class per operation.

**Model resolution is a forward-compat seam (Medium-5).** The base metaclass does not hard-require the literal `Meta.model` attribute; it requires a *resolvable* model and raises [`ConfigurationError`][glossary-configurationerror] only when none can be found, through an overridable `_resolve_model(meta)` step. In `0.0.11` the sole source is `Meta.model`, so `model` is required in practice — but routing it through `_resolve_model` lets the `0.0.12` form flavor derive the model from `Meta.form_class._meta.model` and the `0.0.13` serializer flavor from `Meta.serializer_class.Meta.model` (exactly how [`GOAL.md`][goal]'s `class CreateCategory(DjangoMutation): class Meta: serializer_class = CategorySerializer` declares a mutation **without** a `Meta.model`) without re-opening the base validation. This freezes the `Meta`-validation contract for the flavor subclasses just as [Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper) freezes the `FieldError` envelope for them — so `038` / `039` inherit a base that does not paint them into a corner.

Justification:

- **Factory uniformity, with a timing-forced annotation exception.** Every root field the package ships is a factory assigned to a class attribute; `DjangoMutationField` keeps the write side idiomatic with the read side rather than introducing a `.Field()`-style classmethod (graphene-django's shape) or a decorator (strawberry-django's). The one difference is forced by timing, not style: the read-side factories read a consumer annotation that names a type existing at import (`DjangoConnection[CategoryType]`), but the mutation payload is **generated at finalization** ([Decision 12](#decision-12--finalization-seam-register-at-class-creation-bind-at-phase-25-no-deferred_meta_keys-change)) and has no importable name when `@strawberry.type class Mutation` evaluates its annotations — so `DjangoMutationField` carries no class-attribute annotation and types the field itself via a `strawberry.lazy` forward-ref to the generated `<Name>Payload` ([Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)).
- **Root export matches the audience.** `DjangoMutation` and `DjangoMutationField` are used in every schema that writes; `FieldError` is referenced in every payload — all belong at the root alongside [`DjangoType`][glossary-djangotype] / [`finalize_django_types`][glossary-finalize_django_types], parallel to how [`apply_cascade_permissions`][glossary-apply_cascade_permissions] ([`spec-034`][spec-034] Decision 4) is root-exported.
- **One `operation` key over three base classes.** A single nested-`Meta` key driving behavior is the most `class Meta`-idiomatic shape (it parallels `filterset_class` / `globalid_strategy` selecting behavior through one key), and keeps the public symbol count at three.

Alternatives considered (and rejected):

- **Three base classes `DjangoCreateMutation` / `DjangoUpdateMutation` / `DjangoDeleteMutation`.** Rejected: triples the public symbol surface for what one `Meta.operation` selector expresses; graphene-django itself routes all operations through one `ClientIDMutation` lineage with `model_operations`.
- **A `.field()` classmethod accessor on the mutation class** (graphene-django's `.Field()`, `create_item = CreateItem.field()`). Rejected: the no-annotation `DjangoMutationField` form already resolves the payload-timing hazard ([Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)) while keeping the single factory symbol, so a `.field()` accessor would add a second exposure idiom for no gain. It remains the fallback if Strawberry rejects a no-annotation factory assignment ([Risks](#risks-and-open-questions)).
- **Exporting only from a `django_strawberry_framework.mutations` namespace.** Rejected: the symbols are used inside schema modules alongside root-exported types; subsystem-namespace imports are for *family* surfaces (`from .filters import FilterSet`), as [`spec-034`][spec-034] Decision 4 settled for the cascade helper.

### Decision 6 — Auto-generated `Input` / `PartialInput` types

[`mutations/inputs.py`][mutations-inputs] generates two input types per mutation from the **editable fields of `Meta.model`** — *not* the read-side [`DjangoType`][glossary-djangotype] field selection (see the field-set rule below; the return *type* still resolves the primary `DjangoType`, [Decision 11](#decision-11--primary-type-resolution-return-type-and-input-target-resolve-the-models-primary-djangotype)):

- **`<Model>Input`** — every editable field, each **required only when it has no usable default** (Major-1): no Django `default`, `null=False`, and (for text / char fields) `blank=False`; otherwise the field is **optional** with a `strawberry.UNSET` default. This is DRF's `required=False`-from-`default`/`blank`/`null` rule, and it matches `Model.objects.create(...)` semantics (Django supplies the omitted columns). So a `NOT NULL`, no-default, non-blank column like `name` (and a non-null FK like `category`) is required, while `description` (`blank=True, default=""`) and `is_private` (`default=False`) are optional — the headline `ItemInput` above. (A blanket "every editable field required" rule was rejected: it would force `description` / `isPrivate` required on products *and* on [`GOAL.md`][goal]'s north-star `Galaxy` / `CelestialBody` models, which share the identical `blank=True, default=""` / `default=False` shape, diverging from DRF and strawberry-django.)
- **`<Model>PartialInput`** — every editable field optional, defaulting to `strawberry.UNSET` (matches `Model.objects.update(...)`); only the provided fields are written.

**Field set (Medium-4 — derived from editable *model* fields, not the read selection).** The input fields are the model's editable, settable columns: exclude the auto pk, non-`editable` columns (`auto_now` / `auto_now_add` timestamps and any `editable=False` field), and reverse relations — then optionally narrow by the mutation's own `Meta.fields` / `Meta.exclude` ([Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root)). The set is **not** the read-side `DjangoType` selection, which resolves the read/write mismatch in both directions: a read type's `fields = "__all__"` includes read-only `created_date` / `updated_date` that must never be writable (so they are excluded from the input), and an editable column a read type *omits* for permissions (the cookbook `ValueNode` deliberately hides `description`) is still a writable model column (so it *is* exposed on the input). To keep an editable column off the write surface, the consumer names it in the mutation's `Meta.exclude` — explicitly, not as a side effect of the read selection. Map scalars through the **same** [scalar][glossary-scalar-field-conversion] / [choice-enum][glossary-choice-enum-generation] / [specialized-scalar][glossary-specialized-scalar-conversions] converters the read side uses (so read and write share one wire contract); map a forward FK / OneToOne to a single `<field>_id` input typed as the target's id (`GlobalID` for a Relay-Node target, the raw pk scalar otherwise); map an M2M to `list[<id>]`. Names are class-derived and stable (`CategoryInput` / `CategoryPartialInput`), materialized as module globals so two mutations over one model resolve to the identical input type (Apollo-cache-friendly, exactly the [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] input-naming property). The **relation-override contract** from [`spec-010`][spec-010] holds on the input side: a consumer-authored input field on a custom `input_class` is honored, not clobbered. `Meta.input_class` / `Meta.partial_input_class` substitute a hand-written input for the generated one.

Justification: input generation is the card's headline parity item ([`GOAL.md`][goal] success-criterion 6); reusing the read-side converters guarantees the symmetric wire contract the package's "one configuration surface" pitch promises; the stable-naming + materialize-before-`Schema` discipline is the proven set-family lifecycle ([Decision 12](#decision-12--finalization-seam-register-at-class-creation-bind-at-phase-25-no-deferred_meta_keys-change)).

Alternatives considered (and rejected):

- **A single `Input` with all-optional fields for both create and update.** Rejected: it loses the create-required contract (a missing required field would only fail at `full_clean()`, not at the GraphQL layer); upstream and graphene-django both keep the required/partial split.
- **FK input as the nested object (strawberry-django's `ParsedObject` connect/create).** Rejected: nested writes are an explicit non-goal for `0.0.11` ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)); `<field>_id` is the minimal, unambiguous shape.
- **Reuse the `DjangoType` output type as the input.** Rejected: GraphQL forbids an output type in input position; the input is a distinct `@strawberry.input` type with id-shaped relations.

### Decision 7 — The shared `FieldError` envelope and the payload wrapper

The error contract is a public `FieldError` `@strawberry.type` (`field: str`, `messages: list[str]`) — graphene-django's `ErrorType` shape — surfaced through a generated per-mutation `<Name>Payload` carrying the mutated object (nullable) **and** `errors: list[FieldError]!`. On success `errors` is empty and the object is set; on validation failure the object is `null` and `errors` carries one entry per offending field (the model's `NON_FIELD_ERRORS` bucket maps to a `FieldError` with an empty / sentinel `field`).

**Payload exposure timing (resolves Major-3 — the import-time hazard).** The `<Name>Payload` is materialized at [`finalize_django_types`][glossary-finalize_django_types] phase 2.5 ([Decision 12](#decision-12--finalization-seam-register-at-class-creation-bind-at-phase-25-no-deferred_meta_keys-change)), *after* `@strawberry.type class Mutation` has already evaluated its field annotations at import. So an eager `create_item: CreateItem.Payload = DjangoMutationField(CreateItem)` annotation cannot work — `CreateItem.Payload` is not a concrete attribute at import and raises `AttributeError` (unlike `DjangoConnection[CategoryType]`, which names a class that already exists). Resolution: `DjangoMutationField` is assigned with **no** class-attribute annotation and types the field from the bound payload via a `strawberry.lazy("django_strawberry_framework.mutations.inputs")` forward-ref on its synthesized resolver's return annotation — resolved at schema build, after finalize has materialized `<Name>Payload`. The consumer writes `create_item = DjangoMutationField(CreateItem)` (see the [User-facing API](#user-facing-api)). The `.field()`-classmethod form (graphene-django's `.Field()`) is the fallback if Strawberry rejects a resolver-typed field with no class annotation ([Risks](#risks-and-open-questions)).

Justification:

- **The card pins the graphene-django shape.** "Shape mirrors graphene-django's `ErrorType` (field name + list of message strings)"; the payload-with-`errors` surface is graphene-django's `DjangoModelFormMutation` / `SerializerMutation` shape, so the `0.0.12` / `0.0.13` flavors attach the identical `errors` field unchanged.
- **Partial-success representability.** A payload that carries both the object and errors can express "created, with warnings" or "no object, here are the errors" in one type; a disjoint union cannot.

Alternatives considered (and rejected):

- **strawberry-django's disjoint `Type | OperationInfo` union return.** Rejected: `OperationInfo` is a flat `list[OperationMessage]` (each message carries an optional `field`, but it is **not** the field-keyed `errors: list[FieldError]` shape the card pins); the card pins the graphene-django `ErrorType` shape, and a disjoint union cannot host the shared `errors: list[FieldError]` field the flavor cards reuse.
- **Raising `GraphQLError` for validation failures** (errors in the top-level `errors` array). Rejected: loses the field-keyed structure clients need to attach messages to form fields, and conflates expected validation failures with execution errors.

### Decision 8 — Resolver pipeline: decode → `full_clean()` → write → optimizer re-fetch → payload (sync and async)

[`mutations/resolvers.py`][mutations-resolvers] runs one pipeline per operation, in both sync and async forms (the async form chosen by the package's `is_async_callable` detection — the `__call__` / `functools.partial`-aware superset of `inspect.iscoroutinefunction` that [`DjangoListField`][glossary-djangolistfield] commits to per-construction for a consumer resolver, while its default generated resolver dispatches at runtime via `in_async_context()`; `DjangoMutationField` mirrors that same async-detection asymmetry):

1. **Decode** the `data:` input (and `id:` for update / delete) — `GlobalID` / pk decode for relations, `UNSET` stripping for partial input.
2. **Locate** (update / delete): resolve the row through the target type's `get_queryset(...)` ([Decision 10](#decision-10--permission-composition-update--delete-lookups-run-through-the-target-get_queryset)); a miss returns a not-found `FieldError` on `id`.
3. **Validate**: build (create) or update the instance and call `full_clean()` — for `update`, `full_clean(exclude=<fields the PartialInput did not provide>)` so only provided fields validate (DRF `partial=True` parity; an unsent field never raises a spurious `FieldError`, Medium-3). `full_clean()` runs `validate_constraints()`, which **validates `Meta.constraints` `UniqueConstraint`s** (Django 4.1+; the package floor is `Django>=5.2`), so a duplicate is caught **here as a `ValidationError`** with clean field mapping, *before* `save()` (Major-2). Any `ValidationError` populates the `FieldError` envelope and short-circuits to a null-object payload.
4. **Write**: `save()` (create / update) or `delete()`. A `UniqueConstraint` race that slips past step 3's `validate_constraints()` surfaces here as an `IntegrityError`; the pipeline maps it to the constraint's fields as a **documented best-effort race fallback** (backend-specific) rather than a 500 — it is not the normal unique path and is covered by a mocked-`save()` test so the `fail_under = 100` gate is met without forcing a real concurrent race (Major-2).
5. **Re-fetch / load**: for create / update, re-read the written row **by pk** as a queryset the optimizer plans for the response selection ([Decision 9](#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff)); for delete, that optimizer-planned load runs *before* step 4's `delete()` and the loaded snapshot is returned (the optimizer plans querysets, not the located instance — see [Edge cases](#edge-cases-and-constraints), Medium-2). The re-fetch is **by pk, without the visibility `get_queryset` filter** — the actor just wrote the row, so round-tripping their own write is not an existence leak ([Decision 9](#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff) owns the GOAL crit-4 tension).
6. **Return** the `<Name>Payload`.

Justification: `full_clean()` is the Django-native validation entry strawberry-django uses; routing its errors into the envelope (rather than raising) is the graphene-django contract; the re-fetch step is where optimizer composition lives. A sync path meeting an `async def get_queryset` raises [`SyncMisuseError`][glossary-syncmisuseerror] (coroutine closed first), the package's standing async-misuse discipline.

Alternatives considered (and rejected):

- **Skip `full_clean()` and rely on DB constraints.** Rejected: loses field-level validation messages and defers errors to opaque `IntegrityError`s; upstream and DRF both validate before write.
- **A single dual-mode resolver that returns a coroutine when needed.** Rejected: the caller must know whether to await; the construction-time sync/async split is the package's settled shape ([`DjangoListField`][glossary-djangolistfield]).

### Decision 9 — Optimizer composition and the `spec-035` G2 live-test handoff

The post-write re-fetch (pipeline step 5) re-reads the mutated row as a queryset and routes it through [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] for the response selection. Because the operation is a **mutation**, the [`spec-035`][spec-035] **G2** gate ([`walker.py::_enable_only_for_operation`][walker]) keeps `select_related` / `prefetch_related` but suppresses all `.only(...)` column deferral at plan-build time — so the re-fetched instance carries no selection-shaped deferred-field set, and post-write consumer code touching an unprojected field never triggers a deferred refetch or a deferred-instance partial `save()`. [FK-id elision][glossary-fk-id-elision] stays enabled (under G2's consumer-`.only()` loaded-check), so an `{ category { id } }` response selection still reads the FK column off the parent without a join.

**Re-fetch visibility — by pk, without the `get_queryset` filter (Medium-1; a deliberate exception to [`GOAL.md`][goal] success-criterion 4).** The post-write re-fetch re-reads the just-written row **by primary key only — it does not pass through the target type's [`get_queryset`][glossary-get_queryset-visibility-hook] visibility filter.** GOAL success-criterion 4 ("the same hook covers reads *and* writes") argues for routing it through `get_queryset` for consistency, but doing so produces a confusing failure: the cookbook / products `get_queryset` filters `is_private=False` for non-privileged users, and with **no create authorization in `0.0.11`** ([Decision 10](#decision-10--permission-composition-update--delete-lookups-run-through-the-target-get_queryset) defers it) a non-staff caller can create an `is_private=True` row — re-fetching *that* row through `get_queryset` would return nothing, yielding a **null payload object after a successful write**. So the re-fetch is by pk without the visibility filter: the actor created / updated the row and its pk is already in hand from the write, so round-tripping their own write is not an existence leak. This is a **deliberate, documented exception** to GOAL crit-4 — recorded here, not silently chosen, because the literal crit-4 reading would null the payload. The `update` / `delete` *lookup* ([Decision 10](#decision-10--permission-composition-update--delete-lookups-run-through-the-target-get_queryset)) still runs through `get_queryset` — you cannot mutate a row you cannot see; only the post-write *response* re-fetch skips it.

**This card discharges the [`spec-035`][spec-035] G2 live-test handoff.** That spec's Slice 2 test plan records, verbatim: "The first card that adds such a mutation (the `0.0.11` cohort) must add or migrate a live `examples/fakeshop/test_query/` acceptance test … proving a mutation queryset response keeps `select_related` / `prefetch_related` while carrying **no** deferred loading on the applied querysets (`CaptureQueriesContext` SQL-shape assertion, not just response success)." Slice 4 adds exactly that test against the products write surface.

Justification: G2 was shipped pre-emptively in `0.0.10` for this exact path; honoring it is not optional, and the live test is a standing cross-spec obligation, not new scope. The re-fetch-and-plan return mirrors strawberry-django's optimizer-composed mutation return at the outcome level.

Alternatives considered (and rejected):

- **Return the written instance without re-fetching.** Rejected: a freshly `save()`d instance has no related rows loaded, so any relation in the response selection N+1s; the re-fetch is what makes the response selection planable.
- **Disable the optimizer for mutation returns entirely.** Rejected: the response selection still needs `select_related` / `prefetch_related`; only `.only(...)` is unsafe under a mutation, which is exactly what G2 already gates — re-implementing a coarser disable would regress the join/prefetch planning.

### Decision 10 — Permission composition: `update` / `delete` lookups run through the target `get_queryset`

The `update` / `delete` row lookup is `target_type.get_queryset(target_type.model._default_manager.all(), info).get(pk=<decoded id>)` — the same visibility queryset every read surface uses, including any [`apply_cascade_permissions`][glossary-apply_cascade_permissions] the type's hook calls. A row the caller cannot see raises `DoesNotExist`, which the pipeline maps to a not-found `FieldError` on `id` — indistinguishable from a genuinely missing row, so no existence leak. `create` has no lookup; its authorization is the consumer's responsibility (a `permission_classes`-style gate is deferred — see [Risks](#risks-and-open-questions)).

Justification: the [`DONE-034-0.0.10`][kanban] dependency exists for exactly this — "write mutations need to compose with `apply_cascade_permissions`." Routing the lookup through `get_queryset` reuses the shipped visibility contract with zero new permission machinery, and the not-found-equals-hidden semantics match the package's standing no-existence-leak posture ([`spec-034`][spec-034] Decision 6, [`DjangoNodeField`][glossary-djangonodefield]).

Alternatives considered (and rejected):

- **Look up by raw `Model.objects.get(pk=...)` and check visibility after.** Rejected: a post-hoc check leaks existence (the timing / error differs for hidden vs missing); routing through `get_queryset` makes them identical by construction.
- **A dedicated `check_mutation_permission` hook in `0.0.11`.** Rejected: the cascade + `get_queryset` already gate row reachability; a write-authorization hook layered on top is its own design (adjacent to the `0.1.1` [`FieldSet`][glossary-fieldset] read gates) and out of this card's scope.

### Decision 11 — Primary-type resolution: return type and input target resolve the model's primary `DjangoType`

The mutation's return-payload object type and its input-field set resolve the model's **primary** [`DjangoType`][glossary-djangotype] through [`registry.py::TypeRegistry`][registry]`.get(model)` / `primary_for(model)` — the same primary lookup auto-synthesized relation fields and the cascade helper use. A model with multiple registered types and no declared primary raises [`ConfigurationError`][glossary-configurationerror] at finalization (the existing `Meta.primary` ambiguity audit); a model with no registered type at all raises a finalize-time "no type to return" error.

Justification: the [`DONE-018-0.0.6`][kanban] dependency exists for this — "explicit primary type drives mutation target resolution." Reusing the primary lookup keeps the mutation return consistent with what relation traversal and node refetch resolve, so a mutated row round-trips through the same type a query would return.

Alternatives considered (and rejected):

- **An explicit `Meta.return_type` on the mutation.** Rejected: redundant with the registry primary lookup for the common case; recorded as the escape hatch if a mutation must return a *secondary* type (a Risks item), but not the default surface.
- **Resolve the first registered type for the model.** Rejected: violates `Meta.primary` semantics (secondaries never auto-resolve), exactly the ambiguity `Meta.primary` exists to forbid.

### Decision 12 — Finalization seam: register at class creation, bind at phase 2.5, no `DEFERRED_META_KEYS` change

A `DjangoMutation` subclass registers itself at class creation (its metaclass records the `Meta`) and binds at [`finalize_django_types`][glossary-finalize_django_types] **phase 2.5** — the same seam that binds [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] sidecars. Binding resolves the model's primary type, generates / materializes the `Input` / `PartialInput` / `<Name>Payload` classes as module globals of [`mutations/inputs.py`][mutations-inputs], and validates the resolved target — all before `strawberry.Schema(...)` runs. **No change to [`DEFERRED_META_KEYS`][types-base] or `ALLOWED_META_KEYS`**: a mutation `Meta` is the mutation class's own validation namespace, not a `DjangoType` `Meta` key.

Justification: the materialize-generated-classes-before-`Schema` discipline ([`spec-027`][spec-027] / [`spec-028`][spec-028] Decision 6 / Decision 9) is the proven way Strawberry resolves lazily-referenced generated input classes; reusing phase 2.5 keeps one finalization gate. Leaving `DEFERRED_META_KEYS` untouched honors the [Cross-subsystem invariants][glossary-cross-subsystem-invariants] rule (promote a `DjangoType` `Meta` key only when its subsystem applies it end-to-end) — mutations add no such key.

Alternatives considered (and rejected):

- **Generate input / payload classes lazily at first request.** Rejected: Strawberry resolves schema types at `Schema(...)` construction; lazy generation would miss the schema build, exactly the failure the phase-2.5 materialize step prevents.
- **A separate `finalize_django_mutations()` entry point.** Rejected: a second finalization gate the consumer must remember to call; phase 2.5 of the existing `finalize_django_types()` already runs after all types are registered.

### Decision 13 — Version bumps are owned by the joint `0.0.11` cut

No slice in this card edits `pyproject.toml`, `__version__` in [`__init__.py`][init], [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock`. This card shares the `0.0.11` patch line with [`TODO-ALPHA-037-0.0.11`][kanban] ([`Upload` scalar][glossary-upload-scalar] + file/image mapping); the version bump is owned by the **joint `0.0.11` cut**, not by either individual card — the same posture [`spec-035`][spec-035] Decision 9 took for the joint `0.0.10` cut it shared with [`spec-034`][spec-034].

Justification: per [`docs/SPECS/NEXT.md`][next] Step 3 / Step 6, when multiple WIP cards target one patch version the bump belongs to the joint cut, not any individual card's spec. 036 and 037 both target `0.0.11`.

Alternatives considered (and rejected):

- **Bump to `0.0.11` in this card's Slice 5.** Rejected: 037 also ships into `0.0.11`; a per-card bump races the joint cut and would have to be reconciled when the sibling lands.

### Decision 14 — Single `data:` argument, no Relay `clientMutationId` in `0.0.11`

The generated field takes a single `data: <Model>Input!` (create) / `data: <Model>PartialInput!` (update) argument plus `id: GlobalID!` for update / delete — not flattened per-field arguments — and adds no Relay `clientMutationId`.

Justification: a single `data:` argument mirrors strawberry-django's `data:` shape, avoids collisions between input field names and reserved argument names, and lets the input type evolve without re-spelling the field signature. The Relay `clientMutationId` round-trip is a Graphene-runtime convention the package does not adopt ([Borrowing posture](#borrowing-posture)).

Alternatives considered (and rejected):

- **Flattened per-field arguments** (`createItem(name: ..., description: ..., categoryId: ...)`). Rejected: collides with reserved names, bloats the field signature, and fragments the input contract the flavor cards reuse.
- **graphene-django's `input:` single-argument + `clientMutationId`.** Rejected: `clientMutationId` is the Relay-mutation-spec round-trip the package's non-Graphene-runtime stance declines; `data:` is the strawberry-native spelling.

## Implementation plan

Five slices. Slices 1–3 are package-internal and staged (each builds on the prior); Slice 4 is the live products write surface and the [`spec-035`][spec-035] G2 handoff; Slice 5 is doc-only. Line deltas are planning estimates.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — input generation + `FieldError` + payload | [`mutations/inputs.py`][mutations-inputs] (new), [`mutations/__init__.py`][mutations-init] (new), [`__init__.py`][init] (`FieldError` export) | [`tests/mutations/test_inputs.py`][test-mutations] (~14 — required/optional shape, FK/O2O/M2M id map, pk/auto exclusion, Relay-vs-non-Relay id, stable naming, consumer override preserved, `FieldError` shape) | `+260 / 0` |
| 2 — `DjangoMutation` base + `Meta` validation + binding | [`mutations/sets.py`][mutations-sets] (new), [`types/finalizer.py`][finalizer] (phase-2.5 mutation bind), [`__init__.py`][init] (`DjangoMutation` export) | [`tests/mutations/test_sets.py`][test-mutations] (~12 — `Meta` matrix, registration, binding, no-primary error) | `+230 / 0` |
| 3 — resolvers + `DjangoMutationField` + composition | [`mutations/resolvers.py`][mutations-resolvers] (new), [`mutations/fields.py`][mutations-fields] (new), [`__init__.py`][init] (`DjangoMutationField` export) | [`tests/mutations/test_resolvers.py`][test-mutations] + [`tests/mutations/test_fields.py`][test-mutations] (~18 — create/update/delete, error envelope, hidden-row not-found, sync + async, plan-shape) + [`tests/optimizer/test_walker.py`][walker] extend (G2 mutation re-fetch) | `+320 / 0` |
| 4 — products live write surface (G2 handoff) | [`products/schema.py`][products-schema] (`Mutation`), `config/schema.py` (`mutation=`), [`test_products_api.py`][test-products-api] | live create/update/delete, validation envelope, permission-scoped update/delete, `CaptureQueriesContext` SQL-shape (the G2 handoff) | `+120 / -0` |
| 5 — doc updates + card wrap | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`README.md`][readme], [`GOAL.md`][goal], [`TODAY.md`][today], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban] | 0 (doc-only) | `+90 / -30` |

Total expected delta: ~`+1020 / -60` — an XL cut, matching the card's relative size. No version-file edits ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0011-cut)).

Staged-but-not-implemented seams follow the [`AGENTS.md`][agents] design-doc anchor discipline: a source-site `TODO(spec-036 Slice N)` comment naming this spec and the owning slice, paired with `NotImplementedError` only where a reachable call path must fail loudly (e.g. the `Upload`-input converter seam Slice 1 leaves for [`TODO-ALPHA-037-0.0.11`][kanban] — a `FileField` / `ImageField` reaching the generator before 037 ships must fail loudly, not silently emit a wrong type), removed in the change that ships the slice.

## Edge cases and constraints

- **Create over a uniquely-constrained model.** Products' `Item` has the `unique_item_per_category` `UniqueConstraint`. On the normal path a duplicate `(category, name)` is caught by step 3's `full_clean()` → `validate_constraints()` (which validates `Meta.constraints` `UniqueConstraint`s since Django 4.1; floor `>=5.2`) as a **`ValidationError`** *before* `save()` — `validate_constraints()` keys a single-field unique violation to that field and surfaces a multi-field one (the 2-field `(category, name)`) under `NON_FIELD_ERRORS`, which maps to a `FieldError` with the sentinel `field` ([Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)). That is the path the products live suite pins. An `IntegrityError` at `save()` only fires on a concurrent race that beats `validate_constraints()`; the pipeline maps it to the same fields as a best-effort fallback, covered by a mocked-`save()` unit test (Major-2).
- **Partial update with `UNSET`-vs-`null`.** `ItemPartialInput.description` left out (`UNSET`) leaves the column unchanged and is added to the `full_clean(exclude=...)` set so it is not validated (Medium-3); explicitly passing `null` sets it `None` only if the column is nullable, else surfaces a `full_clean()` `FieldError` — the `UNSET`/`None`/value tri-state is distinguished at decode.
- **Delete loads its response-selection relations before `delete()`.** `deleteItem` returns the object as it was before deletion (id preserved for client cache eviction). The optimizer plans *querysets*, not instances, so a delete payload that selects a relation (`deleteItem { item { category { name } } }`) cannot be "planned against the located instance": the located row (step 2) carries no response-selection relations. The pipeline therefore re-fetches the row as an optimizer-planned queryset covering the response selection and **evaluates it (relations loaded into the instance) *before* calling `delete()`**, then returns that now-detached in-memory instance whose relations are already populated — the loaded Python objects survive the DB row's deletion (and any cascade-deleted children) (Medium-2).
- **Relation id decode failure.** A `categoryId` that is a malformed `GlobalID`, or a well-formed id for a row the caller cannot see (the target's `get_queryset` hides it), surfaces a `FieldError` on `categoryId` — the same no-existence-leak treatment as the update/delete lookup, never a raw `DoesNotExist`.
- **G2 mutation re-fetch carries no `.only()`.** The re-fetched payload object keeps `select_related` / `prefetch_related` for the response selection but no column deferral (the operation is non-`QUERY`); a response touching an unprojected column never deferred-refetches — the exact behavior [`spec-035`][spec-035] G2 guarantees and Slice 4 pins live.
- **Async mutation with a sync `get_queryset`.** Runs the sync hook through `sync_to_async`; a sync mutation with an `async def get_queryset` raises [`SyncMisuseError`][glossary-syncmisuseerror] (coroutine closed first), the standing discipline.
- **Two mutations over one model share input types.** `CreateItem` and `UpdateItem` resolve to the same materialized `ItemInput` / `ItemPartialInput` module globals (stable class-derived names) — no duplicate input type in the schema, Apollo-cache-friendly, matching the [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] input-naming property.
- **A mutation field with no `Mutation` type wired.** A `DjangoMutation` declared but never exposed via `DjangoMutationField` on a schema `Mutation` is inert (registered, never resolved); a `DjangoMutationField` on a model with no registered primary type fails at finalization, not at request time.
- **`finalize_django_types()` ordering.** Mutation binding runs in phase 2.5 after all `DjangoType`s are registered and their relations resolved, so the primary-type lookup and the relation-id input shaping see a fully-resolved registry; declaring a mutation after finalization raises [`ConfigurationError`][glossary-configurationerror] (same as declaring a `DjangoType` late).
- **No `DjangoType` `Meta` key added.** [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS` are byte-unchanged; the `Meta` validation matrix this card adds lives on the mutation metaclass, isolated from `DjangoType.__init_subclass__`.

## Test plan

Test placement follows the [`test_query/` README][test-query-readme] live-HTTP-priority rule. The write side **is** live-reachable the moment products exposes a `Mutation`, so the consumer-visible behavior is earned live in Slice 4; package-internal mechanics (input generation, `Meta` validation, the resolver pipeline shape, the plan-shape) are earned in [`tests/mutations/`][test-mutations] and [`tests/optimizer/`][walker].

- **Live, over `/graphql/`** (Slice 4, [`test_products_api.py`][test-products-api]): `createItem` / `updateItem` / `deleteItem` happy paths; the unique-constraint create error envelope; a partial update; the permission-scoped update/delete (a `view_item` user cannot update a private `Item`; an anonymous request cannot mutate at all); and the **G2 SQL-shape assertion** — a mutation response selecting a relation keeps `select_related` / `prefetch_related` and carries **no** deferred loading (`CaptureQueriesContext`), discharging the [`spec-035`][spec-035] handoff.
- **Package-internal** ([`tests/mutations/`][test-mutations]):
  - `test_inputs.py` — `Input` all-required / `PartialInput` all-optional shapes; FK/O2O → `<field>_id`, M2M → `list[id]`; pk / `auto_now` exclusion; Relay-Node target → `GlobalID` id, non-Relay → raw pk; stable class-derived naming (two mutations, one input type); consumer `input_class` override preserved; the `FieldError` / `<Name>Payload` shape.
  - `test_sets.py` — the `Meta` validation matrix (missing `model`, bad `operation`, unknown key, bad `input_class`); registration; phase-2.5 binding; the no-registered-primary-type finalize error.
  - `test_resolvers.py` — create / update / delete happy paths; `full_clean()` `ValidationError` → envelope (null object), including a `UniqueConstraint` duplicate caught by `validate_constraints()` before `save()` (Major-2); a partial update validating only provided fields (`full_clean(exclude=...)`, Medium-3); the `IntegrityError` race fallback via a mocked `save()` (the branch covered without a real race); a delete payload that selects a relation (relations loaded before `delete()`, Medium-2); hidden-row lookup → not-found `FieldError`; the post-write re-fetch skipping the visibility filter (a non-staff `is_private=True` create still returns its object, Medium-1); sync and async pipelines; the `SyncMisuseError` async-hook-from-sync path.
  - `test_fields.py` — `DjangoMutationField` synthesizes the right argument signature per operation; the payload type resolves; sync vs async resolver selection at construction.
  - [`tests/optimizer/test_walker.py`][walker] (extend) — a mutation re-fetch queryset produces a plan with empty `only_fields` while `select_related` / `prefetch_related` survive (the package-internal mirror of the Slice 4 live assertion, completing the G2 handoff at both tiers).

## Doc updates

Each slice owns its doc edits. [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" requires `CHANGELOG.md` edits to be explicitly instructed — and a standing design doc cannot itself grant that permission. This spec only *describes* the release-note work Slice 5 entails; the **Slice 5 maintainer prompt must explicitly include the `CHANGELOG.md` edit** for it to be authorized.

- **Slice 5 — GLOSSARY** ([`docs/GLOSSARY.md`][glossary]):
  - Promote [`DjangoMutation`][glossary-djangomutation], [Input type generation][glossary-input-type-generation], and [`FieldError` envelope][glossary-fielderror-envelope] from `planned for 0.0.11` to `shipped (0.0.11)`, updating each body to the shipped contract (the `Meta.operation` selector, the `Input` / `PartialInput` shape, the `<Name>Payload` wrapper).
  - Add a net-new `## \`DjangoMutationField\`` entry (the one new public symbol the glossary does not yet name) and add `DjangoMutationField` to the **Public exports** list and the **Index**.
  - Append a one-line note to the [`only()` projection][glossary-only-projection] entry that the G2 mutation gate is now exercised live by the products write surface (the handoff discharged).
  - Update the Index status column and the **Mutations** browse-by-category row.
- **Slice 5 — package docs**:
  - [`docs/README.md`][docs-readme] / [`README.md`][readme]: move mutations from "Coming next (`0.0.11`)" to "Shipped today", with the `class Meta` create/update/delete shape. **Watch-out (roadmap drift):** `README.md`'s "Coming from DRF + django-filter?" paragraph currently says "Mutations are on the roadmap (`0.0.11`) … including a DRF-serializer flavor via `Meta.serializer_class`," lumping form / DRF / auth into `0.0.11`; Slice 5 must reconcile it to the re-sequenced cards — the model-driven foundation ships `0.0.11` (`036`), the form flavor `0.0.12` (`038`), the DRF-serializer flavor `0.0.13` (`039`), and auth `0.0.13` (`040`).
  - [`GOAL.md`][goal]: the DRF-migration mutation diff (`class CreateCategory(DjangoMutation)`) now references a shipped base (the serializer flavor stays `0.0.13`).
  - [`TODAY.md`][today]: products now demonstrates a write surface — add a "Mutations on products today" section (create/update/delete, the error envelope, the permission-scoped lookups), keeping the file products-centric.
  - [`CHANGELOG.md`][changelog]: `### Added` bullets under `[Unreleased]` for the mutation foundation — authored **only when the Slice 5 maintainer prompt explicitly requests it**. No version-heading promotion (per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0011-cut)).
- **Slice 5 — card wrap**:
  - [`KANBAN.md`][kanban]: move [`TODO-ALPHA-036-0.0.11`][kanban] to Done with the next `DONE-NNN-0.0.11` id; set the card's spec reference to the **live** working path `docs/spec-036-mutations-0_0_11.md` (the `docs/SPECS/` relocation is the next spec author's [`docs/SPECS/NEXT.md`][next] Step 8 batched sweep, never a per-card move — a `SpecDoc` DB edit re-rendered via `scripts/build_kanban_md.py`). No version-file edits.

## Risks and open questions

Each item names a preferred answer for the `0.0.11` cut and a fallback if implementation reveals it is wrong.

- **`Meta.operation` selector vs three base classes.** Preferred answer ([Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root)): one `DjangoMutation` base with `Meta.operation` ∈ `{"create", "update", "delete"}`, the most `class Meta`-idiomatic shape and the smallest public surface. Fallback: if the per-operation pipelines diverge enough that one base accretes operation-conditional branches everywhere, split into `DjangoCreateMutation` / `DjangoUpdateMutation` / `DjangoDeleteMutation` sharing a private base — a contained refactor that keeps `DjangoMutation` as the abstract parent.
- **Payload exposure surface (resolved in [Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper) / [Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root); was Major-3).** The import-time hazard — `@strawberry.type class Mutation` evaluates annotations before phase 2.5 materializes `<Name>Payload`, so an eager `create_item: CreateItem.Payload` annotation would `AttributeError` — is resolved by assigning `DjangoMutationField` with **no** class-attribute annotation and typing the field via a `strawberry.lazy` forward-ref to the generated payload (resolved at schema build). Pinned before Slice 1 because the input/payload generation timing depends on it. Fallback: if Strawberry rejects a resolver-typed field that carries no class annotation, commit to a `.field()` classmethod accessor (`create_item = CreateItem.field()`, graphene-django's `.Field()` shape) that owns both resolver and return type — a contained surface swap that changes neither the generator nor the resolver pipeline.
- **`create` authorization.** Preferred answer ([Decision 10](#decision-10--permission-composition-update--delete-lookups-run-through-the-target-get_queryset)): `update` / `delete` are gated by the `get_queryset` lookup; `create` has no row to scope, so its authorization is the consumer's responsibility in `0.0.11` (a `get_queryset`-style write gate is not yet defined). Fallback: if a create-authorization hook is needed before the flavor cards, define a `check_create_permission(info)` gate on the mutation `Meta`-host — but that is adjacent to the `0.1.1` [`FieldSet`][glossary-fieldset] / [Per-field permission hooks][glossary-per-field-permission-hooks] design and is deferred unless a consumer surfaces the need.
- **Returning a secondary `DjangoType`.** Preferred answer ([Decision 11](#decision-11--primary-type-resolution-return-type-and-input-target-resolve-the-models-primary-djangotype)): the payload object resolves the model's **primary** type, matching relation traversal and node refetch. Fallback: a `Meta.return_type` escape hatch for a mutation that must return a *secondary* type (the public-vs-admin pattern) — defined only if a consumer needs it, not shipped speculatively.
- **`DjangoMutationField` has no current glossary entry.** The symbol is net-new; the glossary names `DjangoMutation` / `Input type generation` / `FieldError envelope` but not the field factory. Preferred answer: Slice 5 adds the `## \`DjangoMutationField\`` entry (GLOSSARY edits are in scope for the implementation card, out of scope for the [`docs/SPECS/NEXT.md`][next] authoring flow), so the companion `*-terms.csv` does **not** list `DjangoMutationField` (it has no heading yet and would fail the checker). Fallback: none — the entry lands with the card.
- **Card-citation note: the spec filename vs the card's `docs/spec-mutations.md`.** The card DoD names `docs/spec-mutations.md`; the structured convention authors at `docs/spec-036-mutations-0_0_11.md` ([Decision 1](#decision-1--spec-filename-and-canonical-naming)). Recorded, not silently reconciled, per the [`docs/SPECS/NEXT.md`][next] boundary rule.
- **Conflict: the card body references `031 / 032 / 033` as the envelope's reusers.** The card's "Other" note says the `FieldError` envelope is "reused by 031 / 032 / 033", but those NNNs are the shipped Relay cards ([`DONE-031`][kanban] / [`DONE-032`][kanban] / [`DONE-033`][kanban]), which have nothing to do with mutations — the card's "Card references" section lists [`TODO-ALPHA-037`][kanban] / [`TODO-ALPHA-038`][kanban] / [`TODO-ALPHA-039`][kanban]. Preferred reading: the genuine `FieldError`-envelope consumers are the form-based (`038`, `0.0.12`), DRF-serializer (`039`, `0.0.13`), and auth (`040`, `0.0.13`) flavor cards; `037` is the [`Upload` scalar][glossary-upload-scalar] sibling that shares the `0.0.11` cut but does **not** consume the envelope, and the original `031 / 032 / 033` text is a stale copy-paste from the Relay-cohort era. Recorded per the [`docs/SPECS/NEXT.md`][next] "prefer the card, surface the conflict" rule.

## Out of scope (explicitly tracked elsewhere)

- **`Upload` scalar + `FileField` / `ImageField` mapping** — the sibling `0.0.11` card [`TODO-ALPHA-037-0.0.11`][kanban] ([`Upload` scalar][glossary-upload-scalar] / [`DjangoFileType`][glossary-djangofiletype] / [`DjangoImageType`][glossary-djangoimagetype]); this card leaves a per-field input-converter seam for it.
- **Form-based mutations** ([`DjangoFormMutation`][glossary-djangoformmutation] / [`DjangoModelFormMutation`][glossary-djangomodelformmutation]) — `0.0.12` ([`TODO-ALPHA-038-0.0.12`][kanban]); subclasses this card's base and reuses the `FieldError` envelope.
- **DRF serializer mutations + auth mutations** ([`SerializerMutation`][glossary-serializermutation] — `0.0.13`, [`TODO-ALPHA-039-0.0.13`][kanban]; [Auth mutations][glossary-auth-mutations] — `0.0.13`, [`TODO-ALPHA-040-0.0.13`][kanban]); both reuse the base + envelope.
- **Nested writes / bulk mutations** (strawberry-django's `ParsedObject` / `ParsedObjectList` connect-create-disconnect, batch create) — not on the alpha roadmap; `0.0.11` writes one root model with relations as existing ids.
- **A write-authorization hook** (`check_create_permission` / per-mutation permission classes) — adjacent to the `0.1.1` [`FieldSet`][glossary-fieldset] / [Per-field permission hooks][glossary-per-field-permission-hooks] design; `update` / `delete` are gated by the `get_queryset` lookup, `create` authorization is the consumer's responsibility for now ([Risks](#risks-and-open-questions)).
- **Relay `clientMutationId` / single-`input`-mutation wrapping** — a Graphene-runtime convention the package does not adopt ([Decision 14](#decision-14--single-data-argument-no-relay-clientmutationid-in-0011)).
- **Version bump** — owned by the joint `0.0.11` cut ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0011-cut)).

## Definition of done

The completion contract the card is built against. Items map onto the card's own DoD bullets: item 1 (spec), 2 (the `mutations/` subpackage), 3 (input generation + relation-override contract), 4 (the `FieldError` envelope), 5 (the resolvers + composition), 6 (package tests), 7 (live HTTP), 8 (docs + version boundary).

**Spec + companion CSV**

1. `docs/spec-036-mutations-0_0_11.md` (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion `spec-036-mutations-0_0_11-terms.csv` anchoring every project-specific term that has a [`docs/GLOSSARY.md`][glossary] heading; `uv run python scripts/check_spec_glossary.py --spec docs/spec-036-mutations-0_0_11.md` reports `OK: <N> terms`. The one net-new symbol (`DjangoMutationField`) has no glossary heading yet (added in Slice 5), so it is intentionally absent from the CSV.

**Slice 1 — input generation + `FieldError` + payload**

2. [`mutations/inputs.py`][mutations-inputs] generates `<Model>Input` (editable fields, each required only when it has no usable `default` / `blank` / `null` — Major-1) and `<Model>PartialInput` (editable fields optional, `UNSET`-defaulted) from `Meta.model`'s editable fields narrowed by the mutation's own `Meta.fields` / `Meta.exclude` (**not** the read `DjangoType` selection — Medium-4), mapping scalars through the read-side converters and relations to id-shaped fields, with stable class-derived names materialized as module globals; the relation-override contract from [`spec-010`][spec-010] holds; the public `FieldError` (`field` + `messages`) and the `<Name>Payload` (object + `errors: list[FieldError]!`) exist ([Decision 6](#decision-6--auto-generated-input--partialinput-types) / [Decision 7](#decision-7--the-shared-fielderror-envelope-and-the-payload-wrapper)).

**Slice 2 — the `DjangoMutation` base**

3. [`mutations/sets.py`][mutations-sets] ships `DjangoMutation` + its metaclass with the `Meta` validation matrix (no resolvable model — in `0.0.11` a missing `Meta.model`, via the `_resolve_model` seam so the `038` / `039` flavors can supply it, Medium-5; bad `operation`; unknown key; an `input_class` that is not a `@strawberry.input`-decorated type → [`ConfigurationError`][glossary-configurationerror]); registration and phase-2.5 binding land in [`types/finalizer.py`][finalizer]; a model with no registered primary type fails loudly at finalization; [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS` are unchanged ([Decision 5](#decision-5--public-surface-djangomutation-base--djangomutationfield-factory--fielderror-exported-from-the-root) / [Decision 11](#decision-11--primary-type-resolution-return-type-and-input-target-resolve-the-models-primary-djangotype) / [Decision 12](#decision-12--finalization-seam-register-at-class-creation-bind-at-phase-25-no-deferred_meta_keys-change)).

**Slice 3 — resolvers + field factory + composition**

4. [`mutations/resolvers.py`][mutations-resolvers] runs the decode → `full_clean()` (`exclude=<unprovided>` on update, Medium-3) → write → optimizer-re-fetch → payload pipeline for create / update / delete, sync and async; a `full_clean()` `ValidationError` — including the `validate_constraints()` `UniqueConstraint` violation caught before `save()` (Major-2) — populates the `FieldError` envelope (null object), with a concurrent-race `IntegrityError` mapped to the same envelope as a mocked-`save()`-covered fallback; [`mutations/fields.py`][mutations-fields] ships `DjangoMutationField` (assigned with no class-attribute annotation, payload typed via a `strawberry.lazy` forward-ref, Major-3) synthesizing the per-operation argument signature; `update` / `delete` lookups run through the target `get_queryset` (hidden row → not-found, no leak) while the post-write re-fetch is **by pk without the visibility filter** (Medium-1); `delete` loads its response-selection relations before `delete()` (Medium-2); the post-write re-fetch keeps `select_related` / `prefetch_related` with no `.only(...)` under the mutation operation; `SyncMisuseError` fires for an async hook from a sync path ([Decision 8](#decision-8--resolver-pipeline-decode--full_clean--write--optimizer-refetch--payload-sync-and-async) / [Decision 9](#decision-9--optimizer-composition-and-the-spec-035-g2-live-test-handoff) / [Decision 10](#decision-10--permission-composition-update--delete-lookups-run-through-the-target-get_queryset)).

**Slice 4 — products live write surface + the G2 handoff**

5. Products exposes a `Mutation` (create/update/delete over at least `Item` and `Category`), `config/schema.py` wires `mutation=Mutation`, and [`test_products_api.py`][test-products-api] proves the create/update/delete happy paths, the unique-constraint error envelope, a partial update, the permission-scoped update/delete, and — discharging the [`spec-035`][spec-035] G2 live-test handoff — a `CaptureQueriesContext` assertion that a mutation response keeps `select_related` / `prefetch_related` with **no** deferred loading.

**Cross-cutting — no regression**

6. The full suite is green at the 100% coverage gate (`fail_under = 100`); `ruff format` + `ruff check` are clean; no B1–B8 optimizer regression and no change to the read-side surface; package tests under [`tests/mutations/`][test-mutations] plus the [`tests/optimizer/test_walker.py`][walker] G2 mirror cover every branch.

**Slice 5 — docs + card wrap**

7. [`docs/GLOSSARY.md`][glossary] promotes [`DjangoMutation`][glossary-djangomutation] / [Input type generation][glossary-input-type-generation] / [`FieldError` envelope][glossary-fielderror-envelope] to `shipped (0.0.11)`, adds the `DjangoMutationField` entry (with Public-exports + Index rows), and notes the G2 handoff on [`only()` projection][glossary-only-projection]; [`docs/README.md`][docs-readme] / [`README.md`][readme] move mutations to "Shipped today"; [`GOAL.md`][goal] / [`TODAY.md`][today] reflect the shipped base and the products write surface; [`CHANGELOG.md`][changelog] carries the `[Unreleased]` bullets **only when the Slice 5 maintainer prompt explicitly requests the edit**; [`KANBAN.md`][kanban] records the card `DONE-NNN-0.0.11` with the `SpecDoc` reference at the live `docs/spec-036-mutations-0_0_11.md` (kanban DB + re-render).
8. **No version bump lands in this card** per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0011-cut): `pyproject.toml`, `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` are unchanged; no [`CHANGELOG.md`][changelog] release heading is promoted (the joint `0.0.11` cut shared with [`TODO-ALPHA-037-0.0.11`][kanban] owns the bump). The three net-new public symbols (`DjangoMutation`, `DjangoMutationField`, `FieldError`) are added to `__all__` and the `__all__` exports pin is updated accordingly.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[backlog]: ../BACKLOG.md
[changelog]: ../CHANGELOG.md
[contributing]: ../CONTRIBUTING.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-auth-mutations]: GLOSSARY.md#auth-mutations
[glossary-choice-enum-generation]: GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-cross-subsystem-invariants]: GLOSSARY.md#cross-subsystem-invariants
[glossary-auto-typed-annotations]: GLOSSARY.md#auto-typed-annotations
[glossary-definition-order-independence]: GLOSSARY.md#definition-order-independence
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangofiletype]: GLOSSARY.md#djangofiletype
[glossary-djangoformmutation]: GLOSSARY.md#djangoformmutation
[glossary-djangoimagetype]: GLOSSARY.md#djangoimagetype
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangomodelformmutation]: GLOSSARY.md#djangomodelformmutation
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangonodefield]: GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-fielderror-envelope]: GLOSSARY.md#fielderror-envelope
[glossary-fieldset]: GLOSSARY.md#fieldset
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: GLOSSARY.md#fk-id-elision
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-input-type-generation]: GLOSSARY.md#input-type-generation
[glossary-metaexclude]: GLOSSARY.md#metaexclude
[glossary-metafields]: GLOSSARY.md#metafields
[glossary-metamodel]: GLOSSARY.md#metamodel
[glossary-metaprimary]: GLOSSARY.md#metaprimary
[glossary-only-projection]: GLOSSARY.md#only-projection
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: GLOSSARY.md#per-field-permission-hooks
[glossary-queryset-diffing]: GLOSSARY.md#queryset-diffing
[glossary-relatedfilter]: GLOSSARY.md#relatedfilter
[glossary-scalar-field-conversion]: GLOSSARY.md#scalar-field-conversion
[glossary-serializermutation]: GLOSSARY.md#serializermutation
[glossary-specialized-scalar-conversions]: GLOSSARY.md#specialized-scalar-conversions
[glossary-syncmisuseerror]: GLOSSARY.md#syncmisuseerror
[glossary-upload-scalar]: GLOSSARY.md#upload-scalar
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-010]: SPECS/spec-010-foundation-0_0_4.md
[spec-018]: SPECS/spec-018-meta_primary-0_0_6.md
[spec-027]: SPECS/spec-027-filters-0_0_8.md
[spec-028]: SPECS/spec-028-orders-0_0_8.md
[spec-030]: SPECS/spec-030-connection_field-0_0_9.md
[spec-034]: SPECS/spec-034-permissions-0_0_10.md
[spec-035]: SPECS/spec-035-optimizer_hardening-0_0_10.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[finalizer]: ../django_strawberry_framework/types/finalizer.py
[filters-sets]: ../django_strawberry_framework/filters/sets.py
[init]: ../django_strawberry_framework/__init__.py
[mutations-fields]: ../django_strawberry_framework/mutations/fields.py
[mutations-init]: ../django_strawberry_framework/mutations/__init__.py
[mutations-inputs]: ../django_strawberry_framework/mutations/inputs.py
[mutations-resolvers]: ../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../django_strawberry_framework/mutations/sets.py
[permissions]: ../django_strawberry_framework/permissions.py
[registry]: ../django_strawberry_framework/registry.py
[sets-mixins]: ../django_strawberry_framework/sets_mixins.py
[types-base]: ../django_strawberry_framework/types/base.py
[utils-inputs]: ../django_strawberry_framework/utils/inputs.py
[walker]: ../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-mutations]: ../tests/mutations/

<!-- examples/ -->
[products-models]: ../examples/fakeshop/apps/products/models.py
[products-schema]: ../examples/fakeshop/apps/products/schema.py
[test-products-api]: ../examples/fakeshop/test_query/test_products_api.py
[test-query-dir]: ../examples/fakeshop/test_query/
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[graphene-rest-mutation]: https://github.com/graphql-python/graphene-django/blob/main/graphene_django/rest_framework/mutation.py
[upstream-mutations]: https://github.com/strawberry-graphql/strawberry-django/blob/main/strawberry_django/mutations/mutations.py
