# Spec: Form-based mutations — `DjangoFormMutation` / `DjangoModelFormMutation` on the DRF-shaped `class Meta` surface, reusing the frozen `FieldError` envelope and the `DjangoMutation` foundation

Planned for `0.0.12` (card [`TODO-ALPHA-038-0.0.12`][kanban]). This card adds the
**form-validated** write flavor on top of the model-driven mutation foundation
[`DONE-036-0.0.11`][kanban] ([`spec-036`][spec-036]) shipped: two new bases —
[`DjangoFormMutation`][glossary-djangoformmutation] (a Django `Form`) and
[`DjangoModelFormMutation`][glossary-djangomodelformmutation] (a `ModelForm`) —
declared through a nested `class Meta` (`Meta.form_class`, the DRF / graphene-django
shape, **not** graphene's `MutationOptions` / `__init_subclass_with_meta__`
pattern). It is a Required [`graphene-django`][upstream-forms-mutation] parity item
(the card's own ⚛️ Required tag): graphene-django ships `DjangoFormMutation` /
`DjangoModelFormMutation` as the dominant write-side abstraction for consumers who
already encode their validation in a `Form` / `ModelForm`, and without an equivalent
every graphene-django migrant must rewrite each form-backed mutation against the
lower-level [`DjangoMutation`][glossary-djangomutation] surface
[`spec-036`][spec-036] built. The flavor reuses, **byte-identical**, the contracts
[`spec-036`][spec-036] **froze for exactly this**: the shared
[`errors: list[FieldError]`][glossary-fielderror-envelope] envelope (populated here
from `form.errors`), the generated `<Name>Payload` wrapper with its uniform
`node` / `result` object slot, the [`DjangoMutationField`][glossary-djangomutationfield]
exposure factory, the write-authorization seam
([`DjangoModelPermission`][glossary-djangomodelpermission] /
`Meta.permission_classes` / `check_permission`), and the overridable
[`_resolve_model`][spec-036] seam ([`spec-036`][spec-036] Decision 5) that lets the
form flavor supply its model from `form_class._meta.model` **without** re-opening the
base validation. The only genuinely new machinery is a `forms/converter.py`
form-field → Strawberry-input mapping and a form-pipeline (`is_valid()` →
`form.errors` → `FieldError` → `form.save()`) that swaps the model-construct +
`full_clean()` heart of the [`spec-036`][spec-036] resolver for the form's own
validation and write.

**Version boundary** (see
[Decision 14](#decision-14--this-card-owns-the-0012-version-bump)): unlike
[`spec-036`][spec-036] (which shared its `0.0.11` patch line with the sibling
[`Upload`][glossary-upload-scalar] card [`spec-037`][spec-037] and so deferred the
bump to the joint cut), `038` is the **lone** `0.0.12` card — no other WIP / To-Do
card targets `0.0.12` — so the `pyproject.toml` / `__version__` /
[`tests/base/test_init.py::test_version`][test-base-init] bump from `0.0.11` to
`0.0.12` **lands here**, exactly as [`spec-037`][spec-037] Decision 10 owned the
final `0.0.11` cut.

Status: **IN PROGRESS** — authored for [`TODO-ALPHA-038-0.0.12`][kanban] via the
[`docs/SPECS/NEXT.md`][next] flow; Slices 1–4 built and accepted (the form
converter + form-derived inputs; the two bases + `Meta` validation + the phase-2.5
bind; the resolver pipeline + `DjangoMutationField` exposure; the products live form
surface), only Slice 5 remains. Slice 5 flips this line to shipped at the `0.0.12` cut.
Five slices: Slice 1
(**form-field → Strawberry input mapping** — `forms/converter.py` + the
form-derived input generator;
[Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)),
Slice 2 (**the `DjangoFormMutation` / `DjangoModelFormMutation` bases + `Meta`
validation + the phase-2.5 bind** — `forms/sets.py`;
[Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)
/
[Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)),
Slice 3 (**the form resolver pipeline + `DjangoMutationField` exposure** —
`forms/resolvers.py`;
[Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)
/
[Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path)),
Slice 4 (**the products live form surface** — a `ModelForm` and a plain `Form`
mutation over `/graphql/`;
[Decision 12](#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation)),
and Slice 5 (**docs + the `0.0.12` version cut + card wrap**; the per-card
[`CHANGELOG.md`][changelog] edit must be named explicitly in the Slice 5 maintainer
prompt — this spec describes the edit but cannot grant the permission
[`AGENTS.md`][agents] reserves for an explicit instruction). The card's hard
dependency is satisfied: [`DONE-036-0.0.11`][kanban] (the mutation foundation this
card subclasses) has shipped.

Owner: package maintainer.

Predecessors: [`spec-037-upload_file_image_mapping-0_0_11.md`][spec-037] (the
most-recently-authored spec and the canonical voice / depth / section-layout
reference; its [`Upload`][glossary-upload-scalar] scalar is the input type a form's
`forms.FileField` / `forms.ImageField` maps to, [Edge cases](#edge-cases-and-constraints));
[`spec-036-mutations-0_0_11.md`][spec-036] (the foundation this card extends — it
**froze** the [`FieldError` envelope][glossary-fielderror-envelope], the
`<Name>Payload` uniform slot, the [`DjangoMutationField`][glossary-djangomutationfield]
factory, the [`DjangoModelPermission`][glossary-djangomodelpermission] write-auth
seam, and the [`_resolve_model`][spec-036] hook **explicitly for the form / serializer
flavor cards**, [Decision 2](#decision-2--card-scope-boundary-the-two-form-flavors-ship-serializer--auth-stay-out-the-frozen-036-contracts-are-reused-unchanged));
[`spec-034-permissions-0_0_10.md`][spec-034] (the [`get_queryset`][glossary-get_queryset-visibility-hook]
visibility hook the `update` locate composes with);
[`spec-027-filters-0_0_8.md`][spec-027] / [`spec-028-orders-0_0_8.md`][spec-028]
(the set-family subpackage layout / phase-2.5 binding / materialize-before-`Schema`
discipline `mutations/` mirrored and `forms/` mirrors again);
[`spec-010-foundation-0_0_4.md`][spec-010] (the relation-override contract the
input generation honors). [`docs/GLOSSARY.md`][glossary] carries
[`DjangoFormMutation`][glossary-djangoformmutation] and
[`DjangoModelFormMutation`][glossary-djangomodelformmutation] as
`planned for 0.0.12`; Slice 5 promotes both to `shipped (0.0.12)` and moves the
package-version line to `0.0.12`.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the [`TODO-ALPHA-038-0.0.12`][kanban]
  card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-06-20). Pinned: the
  canonical structured filename
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the card-scope
  boundary that ships the two form flavors and reuses the frozen `036` contracts,
  parking serializer / auth for `0.0.13`
  ([Decision 2](#decision-2--card-scope-boundary-the-two-form-flavors-ship-serializer--auth-stay-out-the-frozen-036-contracts-are-reused-unchanged));
  the **`class Meta`-not-`MutationOptions`** surface
  ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions));
  the `forms/` subpackage layout
  ([Decision 4](#decision-4--module-and-test-locations-forms-subpackage-mirroring-mutations));
  the two-base public surface
  ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root));
  the base-class strategy — `DjangoModelFormMutation` rides the
  [`DjangoMutation`][glossary-djangomutation] base via the
  [`_resolve_model`][spec-036] seam, the plain `DjangoFormMutation` is the
  model-less sibling
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling));
  the form-derived input mapping
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth));
  the `form.errors` → [`FieldError`][glossary-fielderror-envelope] pipeline
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload));
  the optimizer composition reusing the `036` re-fetch path
  ([Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path));
  the operation set (`create` / `update`, no form `delete`)
  ([Decision 10](#decision-10--operations-create--update-for-the-modelform-no-form-delete));
  permission reuse
  ([Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form));
  the products live form surface
  ([Decision 12](#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation));
  the finalizer-bind reuse
  ([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change));
  and **this card owning the `0.0.12` version bump**
  ([Decision 14](#decision-14--this-card-owns-the-0012-version-bump)). Two
  card-body tensions are carried into
  [Risks and open questions](#risks-and-open-questions) rather than silently
  reconciled (the card's `Meta.return_field_name` key vs the `036`-frozen uniform
  `node` / `result` slot, and the spec-filename vs the card's `docs/spec-form_mutations.md`),
  each with a preferred reading.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the
vocabulary used throughout the spec:

- [`DjangoFormMutation`][glossary-djangoformmutation] /
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation] — the two subjects.
  Both consume a Django `Form` / `ModelForm` (`Meta.form_class`) and surface
  validation through the shared [`FieldError` envelope][glossary-fielderror-envelope]
  (populated from `form.errors`). **The current glossary text is provisional and
  Slice 5 must correct it on one point:** it describes *both* as `DjangoMutation`
  subclasses, but this card's settled architecture
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling))
  is that **only `DjangoModelFormMutation` subclasses [`DjangoMutation`][glossary-djangomutation]**
  (it has a model, returns the post-save object in the uniform `node` / `result`
  slot), while the **plain `DjangoFormMutation` is a model-less sibling** (its own
  metaclass; no `DjangoType` object slot — the pinned `ok` + `errors` payload of
  [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling))
  accepted by the **generalized mutation-field family**
  ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)).
  Slice 5 promotes both entries from `planned for 0.0.12` to `shipped (0.0.12)` and
  rewrites the `DjangoFormMutation` entry's "`DjangoMutation` subclass" /
  "post-save object as the return value" claims to this sibling shape (see
  [Doc updates](#doc-updates)).
- [`DjangoMutation`][glossary-djangomutation] /
  [Input type generation][glossary-input-type-generation] /
  [`DjangoMutationField`][glossary-djangomutationfield] — the shipped
  [`spec-036`][spec-036] foundation this card builds on. The form flavor reuses the
  [`DjangoMutationField`][glossary-djangomutationfield] exposure factory and the
  generated-payload lifecycle, and `DjangoModelFormMutation` subclasses the
  [`DjangoMutation`][glossary-djangomutation] base outright; the input *generation*,
  by contrast, is **form-derived here**, not model-derived
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- [`FieldError` envelope][glossary-fielderror-envelope] — the shared error contract
  [`spec-036`][spec-036] **defined and froze** for this card. A form mutation maps
  `form.errors` (a `field → [messages]` dict, with the form's `NON_FIELD_ERRORS`
  bucket) onto the byte-identical envelope, keying form-level errors to the same
  `"__all__"` sentinel `036` pinned
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)).
- [`DjangoModelPermission`][glossary-djangomodelpermission] — the default
  write-authorization class the `ModelForm` flavor inherits unchanged (the form's
  model resolves the `add` / `change` perm); the plain-`Form` flavor's permission
  default is settled in
  [Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form).
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] /
  [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — the
  visibility seam the `update` locate composes with: a `DjangoModelFormMutation`
  `update` binds the form to a row located through the target type's
  [`get_queryset`][glossary-get_queryset-visibility-hook], so a hidden row is
  not-found, never an existence leak — the same contract `036`'s model-driven
  `update` uses
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] /
  [`only()` projection][glossary-only-projection] — the post-save re-fetch
  cooperation. The `ModelForm` payload's object is re-fetched and optimizer-planned
  for the response selection through the **same** `036` re-fetch path, so the
  [`spec-035`][spec-035] **G2** mutation gate (keep `select_related` /
  `prefetch_related`, suppress `.only(...)`) comes for free
  ([Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path)).
- [`Meta.primary`][glossary-metaprimary] / [`Meta.model`][glossary-metamodel] /
  [`DjangoType`][glossary-djangotype] — the return-payload type resolves the form
  model's **primary** [`DjangoType`][glossary-djangotype] through the registry
  primary lookup, exactly as `036`'s `DjangoMutation` does
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)).
- [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] —
  the `only_fields` / `exclude_fields` graphene-django surface, here named for the
  package's own [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude]
  shape, narrowing which **form** fields become input fields
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- [Scalar field conversion][glossary-scalar-field-conversion] /
  [Choice enum generation][glossary-choice-enum-generation] /
  [`Upload` scalar][glossary-upload-scalar] — the converters the form-field mapping
  reuses where a form field's type overlaps a Django column type (so a
  form-derived input field resolves to the same scalar / enum / `Upload` the
  read side and the `036` model-driven input use)
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- [`ConfigurationError`][glossary-configurationerror] /
  [`SyncMisuseError`][glossary-syncmisuseerror] — the validation / misuse
  exceptions this card raises: `ConfigurationError` at form-mutation-class creation
  (missing `Meta.form_class`, a non-`Form` / non-`ModelForm` value, a `ModelForm`
  with no resolvable model), and `SyncMisuseError` when a sync form pipeline meets
  an `async def` target [`get_queryset`][glossary-get_queryset-visibility-hook]
  (the standing discipline `036` already routes through).
- [`SerializerMutation`][glossary-serializermutation] / [Auth mutations][glossary-auth-mutations]
  — the `0.0.13` flavor cards that reuse this card's nothing-new and `036`'s
  envelope; named here only to fix the out-of-scope boundary
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] /
  [`FieldSet`][glossary-fieldset] / [Per-field permission hooks][glossary-per-field-permission-hooks]
  — the `1.0.0` invariant this card must not violate (a `DjangoType` `Meta` key is
  promoted only when its subsystem applies it end-to-end). A form mutation adds **no**
  `DjangoType` `Meta` key, so [`DEFERRED_META_KEYS`][types-base] is untouched
  ([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package-internal form-converter /
  base / resolver mechanics under [`tests/forms/`][test-forms] mirroring source;
  live consumer behavior over `/graphql/` when a realistic request reaches it —
  [Decision 12](#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation));
  the settings-keys-only-when-needed rule (this card adds no settings key); the
  no-pytest-after-edits rule; the CHANGELOG-edit-permission rule at
  [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" —
  Slice 5's release-note edit must be named in its maintainer prompt.
- [`START.md`][start] — "Meta classes everywhere on consumer surfaces. If you find
  yourself writing stacked Strawberry decorators on a consumer-facing class, stop."
  This is the decisive rule for
  [Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions); also
  the "behaviorally we copy `strawberry-graphql-django`'s good ideas, surface-wise
  we copy `django-graphene-filters`" rule (the form mutation is a graphene-django
  surface borrow, on a Strawberry engine) and the reference-style markdown link
  convention.
- [`CONTRIBUTING.md`][contributing] — the 100% coverage target
  (`fail_under = 100`); every converter branch, the `is_valid()` / `form.errors`
  paths, the `save()` path, and both base classes earn coverage in
  [`tests/forms/`][test-forms] plus the live products suite.
- [`docs/TREE.md`][tree] — the target layout reserves
  `django_strawberry_framework/forms/` (planned by this card) and
  [`tests/forms/`][test-forms]; this card creates those trees and adds no module
  outside them beyond the products-example wiring.
- [`GOAL.md`][goal] — success-criterion 6 ("Write mutations declaratively from
  `ModelForm`, `ModelSerializer`, or auto-generated `Input` types — one shared
  `errors: list[FieldError]` envelope across every flavor"); this card ships
  criterion 6's `ModelForm` flavor (the `ModelSerializer` flavor stays `0.0.13`),
  plus the plain-`Form` flavor — the latter is **not** a criterion-6 item
  (criterion 6 names `ModelForm` / `ModelSerializer` / `Input`, not a bare `Form`):
  it is the card's own ⚛️ graphene-django parity addition.

## Slice checklist

Each top-level item maps to one commit / PR. **Five slices: form-field converter +
input generation (Slice 1), the two base classes (Slice 2), the resolver pipeline +
field exposure (Slice 3), the products live form surface (Slice 4), and the doc +
`0.0.12` cut (Slice 5).** Slices 1–3 are package-internal and staged (each builds on
the prior); Slice 4 is the live consumer surface; Slice 5 is doc + version-cut only.

- [ ] Slice 1: form-field → Strawberry input mapping + the form-derived input
  generator (per
  [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth))
  - [ ] [`forms/converter.py`][forms-converter]: a `convert_form_field(field)`
    registry (the graphene-django [`convert_form_field`][upstream-forms-converter]
    parity shape) returning the Strawberry annotation + required-ness for each
    supported form-field class (`CharField` / `ChoiceField` → `str`, `IntegerField` →
    `int`, `BooleanField` → `bool`, `FloatField` → `float`, `DecimalField` → `Decimal`,
    `DateField` / `DateTimeField` / `TimeField` → Python-native, `UUIDField` →
    `uuid.UUID`, `ModelChoiceField` → the target's id, `ModelMultipleChoiceField` /
    `MultipleChoiceField` → `list[<id>]` / `list[str]`, `forms.FileField` /
    `forms.ImageField` → [`Upload`][glossary-upload-scalar]). **Fail-loud dispatch
    (P2):** the fallthrough default **raises** — supported classes are registered
    individually (subclasses map via MRO), bare `forms.Field` is an explicit exact-type
    special case → `str`, and **no base-`forms.Field` catch-all** is registered (which
    would shadow the raise), so a custom `forms.Field` subclass with no supported
    ancestor raises [`ConfigurationError`][glossary-configurationerror] naming the field
    and class. Where a form field maps to a Django column type the read side already
    converts, reuse the [Scalar field conversion][glossary-scalar-field-conversion] /
    [Choice enum generation][glossary-choice-enum-generation] registry rather than
    re-deriving the scalar.
    Record, per generated input field, the `input_attr → (form_field_name, kind)`
    reverse map (`kind ∈ {scalar, relation_single, relation_multi, file}`) the
    resolver needs to build a form-field-keyed payload — `categoryId` / `category_id`
    → `category` / `relation_single`, an `Upload` field flagged `file`
    ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth), P1).
  - [ ] [`forms/inputs.py`][forms-inputs] (its own module, per the committed
    four-module `forms/` layout — [Decision 4](#decision-4--module-and-test-locations-forms-subpackage-mirroring-mutations)):
    build **two** `@strawberry.input` classes from the **form's declared fields**
    (`form_class.base_fields`, narrowed by `Meta.fields` / `Meta.exclude`) — `<FormClass>Input`
    (create; each field's requiredness from `field.required`, graphene-django parity)
    and `<FormClass>PartialInput` (update; model-backed fields optional, a **non-model
    extra field keeps its `field.required`**, P2) — under the **shape-identity +
    naming + collision discipline** of `036` adapted to forms: identity `(form_class,
    operation kind, frozenset(effective field names))`, canonical `<FormClass>Input` /
    shape-derived narrowed names, identical shapes dedupe, two distinct shapes on one
    name → finalize-time [`ConfigurationError`][glossary-configurationerror] (P1).
    Reuse [`utils/inputs.py`][utils-inputs]'s `build_strawberry_input_class` +
    `materialize_generated_input_class` core (the latter's ledger gives the collision
    raise for free) and materialize as module globals of the `forms` input namespace
    for the [`strawberry.lazy`][glossary-djangomutationfield] forward-ref. Normalize +
    fail-loud `Meta.fields` / `Meta.exclude` against `form_class.base_fields` (bare string,
    duplicates, unknown names, empty effective set → `ConfigurationError`, mirroring
    `036`'s `_normalize_field_sequence`, P3).
  - [ ] Package coverage: [`tests/forms/test_converter.py`][test-forms] — each
    supported form-field class → its annotation + required-ness; the
    `ModelChoiceField` / `ModelMultipleChoiceField` id mapping (Relay-`GlobalID`
    vs raw pk by the target's primary [`DjangoType`][glossary-djangotype]); the
    `forms.FileField` → [`Upload`][glossary-upload-scalar] mapping; the unknown
    form-field [`ConfigurationError`][glossary-configurationerror]. And
    [`tests/forms/test_inputs.py`][test-forms] — the form-derived input shape (fields
    from `form_class.base_fields`, required-ness from `field.required`, `Meta.fields` /
    `Meta.exclude` narrowing, a form-only non-model field included), materialized as a
    module global.
- [ ] Slice 2: the `DjangoFormMutation` / `DjangoModelFormMutation` bases + `Meta`
  validation + the phase-2.5 bind (per
  [Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)
  /
  [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling))
  - [ ] [`mutations/sets.py`][mutations-sets]: refactor the class-creation
    validation into an overridable `DjangoMutation._validate_meta(meta)` classmethod
    the metaclass invokes (the model base keeps today's `_validate_mutation_meta`
    body), and add the overridable `build_input(meta, primary_type)` bind hook +
    `input_type_name(meta)` / `input_module_path` + `resolve_sync` / `resolve_async`
    seams ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)
    / [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)),
    each defaulting to today's model behavior (no model-flavor regression).
  - [ ] [`forms/sets.py`][forms-sets]: `DjangoModelFormMutation` (subclasses
    [`DjangoMutation`][glossary-djangomutation], overriding [`_resolve_model`][spec-036]
    → `Meta.form_class._meta.model`, plus the `_validate_meta` / `build_input` /
    `input_type_name` / `input_module_path` / `resolve_*` seams above) and
    `DjangoFormMutation` (the model-less sibling — its own metaclass + declaration
    registry + `bind_form_mutations()` wired into [`types/finalizer.py`][types-finalizer],
    [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)
    / [Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).
    The form-flavor `_validate_meta` override: `Meta.form_class` is required. In
    Django, **`forms.ModelForm` is NOT a subclass of `forms.Form`** — both are
    siblings under `forms.BaseForm` (`issubclass(ModelForm, Form)` is `False`;
    `ModelForm` → `BaseModelForm` → `BaseForm`, `Form` → `BaseForm`). So the plain
    `DjangoFormMutation` **checks `issubclass(form_class, forms.ModelForm)` first** and
    raises a `ConfigurationError` naming `DjangoModelFormMutation` as the correct base
    (a *targeted* message — without this explicit check a bare `issubclass(…,
    forms.Form)` gate would still reject a `ModelForm`, but with a confusing generic
    "not a `Form`" message; and the targeting matters because, were a `ModelForm` let
    through, it would silently write via `form.save()` and return only `{ ok errors }`
    with no object slot, no `DjangoModelPermission` default, and no optimizer re-fetch,
    defeating the two-base split, P2). It then requires a `forms.Form` subclass.
    `DjangoModelFormMutation` requires a `forms.ModelForm` subclass. The check runs
    **before** `_resolve_model` (so a missing / wrong-type `form_class` is a clean
    [`ConfigurationError`][glossary-configurationerror], never a raw `AttributeError`
    from `form_class._meta.model`); a `ModelForm` with no resolvable `_meta.model`
    raises. **`operation` is split by base (P2):** `DjangoModelFormMutation` requires
    `Meta.operation ∈ {"create", "update"}` (a `"delete"` form mutation is **rejected**
    — the form flavor has no delete pipeline,
    [Decision 10](#decision-10--operations-create--update-for-the-modelform-no-form-delete)),
    and its shape-identity operation component is that value; the plain
    `DjangoFormMutation` **rejects any `Meta.operation`** as unsupported (a model-less
    mutation has no model operation — Decision 10) and uses the fixed identity
    sentinel **`"form"`** for its input-shape cache key
    ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
    The form allowed-key set adds `form_class` and drops `model` / `input_class` /
    `partial_input_class`; `Meta.fields` / `Meta.exclude` are mutually exclusive.
  - [ ] No change to [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS`: a
    form-mutation `Meta` is its own validation namespace
    ([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).
  - [ ] Package coverage: [`tests/forms/test_sets.py`][test-forms] — the `Meta`
    validation matrix (missing / wrong-type `form_class`, a `ModelForm` on the plain
    base rejected naming `DjangoModelFormMutation`, `ModelForm`-with-no-model,
    `DjangoModelFormMutation` `operation = "delete"` rejected, **any `Meta.operation`
    on the plain base rejected** (P2), `form_class` accepted as a known key,
    `fields` + `exclude` both set, unknown key), **plain-form input dedupe** (the
    `"form"` sentinel — two plain mutations over one form + effective set dedupe),
    registration, finalizer binding (both the `DjangoMutation`-path bind and the
    `bind_form_mutations()` path), the no-registered-primary-type error for
    `DjangoModelFormMutation`, and the
    model-flavor seam defaults unchanged (a `DjangoMutation` still validates +
    materializes its model-column input exactly as before).
- [ ] Slice 3: the form resolver pipeline + `DjangoMutationField` exposure (per
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)
  /
  [Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path))
  - [ ] [`forms/resolvers.py`][forms-resolvers]: the sync + async pipeline —
    **decode** the `data:` input via the reverse map into a form-field-keyed
    `provided_data` and a `provided_files` (files kept out of `data`), using the
    **dedicated form relation decoder** (NOT `036`'s `_decode_relation_id_set`): each
    relation id — `GlobalID` *or* **raw pk** — is type-checked, resolved to the
    **visible** object through the related primary `DjangoType.get_queryset` (closing
    the raw-pk visibility gap, P1#1), and converted by `to_field_name`
    (`obj.serializable_value(field.to_field_name)` else `obj.pk`, P2#6) before landing
    under the form field name; a hidden target → field-keyed `FieldError`
    ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload));
    (`update`) **locate** the row through the target type's
    [`get_queryset`][glossary-get_queryset-visibility-hook] (not-found → a `FieldError`
    on `id`, no existence leak); **authorize** via the inherited `check_permission` /
    `Meta.permission_classes`; **construct** the form once via the overridable
    `get_form_kwargs(info, *, data, files, instance=None)` hook (P2#3) — create:
    `form_class(**get_form_kwargs(info, data=provided_data, files=provided_files))`;
    **update (partial):** reconstruct `data = {**model_to_dict(instance, non-file
    fields), **provided_data}`, `files = provided_files`, then
    `form_class(**get_form_kwargs(info, data=, files=, instance=<row>))` (omitted
    fields preserved, P1); **validate** via `form.is_valid()` — a failure maps
    `form.errors` onto the [`FieldError` envelope][glossary-fielderror-envelope] (the
    form's `NON_FIELD_ERRORS` bucket → the `"__all__"` sentinel `036` froze, via the
    reused `_validation_error_to_field_errors(ValidationError(form.errors.as_data()))`)
    and returns a null-object payload; **write** via `form.save()` (`ModelForm`) /
    `perform_mutate` (plain form), **wrapped by the `036` `_save_or_field_errors`
    `IntegrityError` → envelope mapper** (P1, no top-level error at write); **re-fetch**
    the saved object by pk + optimizer-plan (the `ModelForm` flavor); **return** the
    `<Name>Payload` (`node` / `result` for the `ModelForm`, the pinned `ok` + `errors`
    for the plain form). The whole pipeline runs inside one `transaction.atomic()`, and
    the async path runs the sync body in one `sync_to_async(thread_sensitive=True)`
    call — the same boundary `036` set.
  - [ ] [`mutations/fields.py`][mutations-fields]: generalize
    [`DjangoMutationField`][glossary-djangomutationfield] along three axes
    ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)) —
    (a) the `_validate_mutation_target` check (accept the mutation/form family, not
    only `issubclass(DjangoMutation)`); (b) the `_resolve` dispatch (call
    `mutation_cls.resolve_sync` / `resolve_async` instead of the hardcoded
    [`mutations/resolvers.py`][mutations-resolvers] import, so a form flavor routes to
    [`forms/resolvers.py`][forms-resolvers]); (c) the synthesized `data:` lazy ref
    (consult `mutation_cls.input_type_name(meta)` + `input_module_path` instead of the
    hardcoded model-column `_input_type_name` + `INPUTS_MODULE_PATH`). All three keep
    today's behavior for a `DjangoMutation` target.
  - [ ] Package coverage: [`tests/forms/test_resolvers.py`][test-forms] — create /
    update happy paths, the `form.errors` → envelope (incl. a `NON_FIELD_ERRORS`
    `clean()` error → `"__all__"`), the **decode split** (`categoryId` → `{"category":
    pk}` in `data=`, an `Upload` → `files=`), the **partial-update reconstruction**
    (omitted scalar / FK / M2M / file preserved; `unique_item_per_category` on a
    one-field change), the **plain-form `ok` + `errors` payload + `perform_mutate`
    default/override**, the visibility-scoped `update` locate (hidden row →
    not-found), write-auth denial vs success, sync + async, and the G2 plan-shape (the
    `ModelForm` re-fetch keeps `select_related` / `prefetch_related`, no `.only(...)`).
- [ ] Slice 4: the products live form surface (per
  [Decision 12](#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation))
  - [ ] [`examples/fakeshop/apps/products/forms.py`][products-forms] (new): an
    `ItemModelForm` (`forms.ModelForm` over `Item`, with a `clean_<field>`) and a
    plain `Form` (e.g. a small contact / action form); `products/schema.py` gains a
    `DjangoModelFormMutation` (create + update) and a `DjangoFormMutation`;
    `config/schema.py` already wires `mutation=Mutation` ([`spec-036`][spec-036] Slice 4).
    If `Item` (or a small example model) needs a file column for the multipart test,
    add the minimal `FileField` + migration here.
  - [ ] [`test_products_api.py`][test-products-api] (seeded via `seed_data` /
    `create_users`): live `/graphql/` create / update through the `ModelForm`
    mutation; `categoryId` validating + writing through the form's `category` field;
    **partial-update preservation** (a `name`-only update preserves `category` /
    `description`, and `unique_item_per_category` fires on a one-field change); the
    `form.errors` envelope (`clean_<field>` keyed to the field; the constraint error
    keyed to `"__all__"`); write authorization; the visibility-scoped `update`; **a
    raw `django.test.Client` multipart upload** to a form-backed `Upload` field
    (the P1 file-routing contract); and the plain `Form` mutation's **success**
    (`ok: true`) **and** validation-failure (`ok: false`, field-keyed `errors`) shapes.
- [ ] Slice 5: doc updates + the `0.0.12` version cut + card wrap (per
  [Doc updates](#doc-updates) /
  [Decision 14](#decision-14--this-card-owns-the-0012-version-bump))
  - [ ] **Version files to `0.0.12`**
    ([Decision 14](#decision-14--this-card-owns-the-0012-version-bump)):
    [`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init],
    [`tests/base/test_init.py::test_version`][test-base-init], the
    [`docs/GLOSSARY.md`][glossary] package-version line, and `uv.lock` if it
    carries the package version.
  - [ ] [`docs/GLOSSARY.md`][glossary] (promote
    [`DjangoFormMutation`][glossary-djangoformmutation] /
    [`DjangoModelFormMutation`][glossary-djangomodelformmutation] to
    `shipped (0.0.12)`; add both to **Public exports** + the **Index** + the
    **Mutations** browse-by-category row; move the package-version line to `0.0.12`),
    [`docs/README.md`][docs-readme] / [`README.md`][readme] (move form mutations
    from "Coming next (`0.0.12`)" to "Shipped today" and the README **Status** line
    from `0.0.11` to `0.0.12`), [`GOAL.md`][goal] (criterion 6's `ModelForm` flavor
    now ships; the `ModelSerializer` flavor stays `0.0.13`), [`TODAY.md`][today]
    (note form mutations as a package capability — products now demonstrates a
    `ModelForm` write surface), [`docs/TREE.md`][tree] (fill the planned `forms/` /
    [`tests/forms/`][test-forms] summary lines), [`CHANGELOG.md`][changelog] (only
    if the Slice 5 maintainer prompt explicitly requests it), [`KANBAN.md`][kanban]
    (card → Done via the kanban DB + re-render).

## Problem statement

The package shipped its **write side** in [`DONE-036-0.0.11`][kanban]: the
model-driven [`DjangoMutation`][glossary-djangomutation] base, auto-generated
[`Input` / `PartialInput`][glossary-input-type-generation] types, the shared
[`FieldError` envelope][glossary-fielderror-envelope], and `create` / `update` /
`delete` resolvers. That foundation validates a write through Django **model**
machinery — construct / locate the instance, call `full_clean()`, `save()`.

But a large class of Django consumers already encode their write validation in a
`Form` / `ModelForm`, not on the model. graphene-django serves them with
[`DjangoFormMutation`][upstream-forms-mutation] (a plain `Form`) and
`DjangoModelFormMutation` (a `ModelForm`): the mutation runs `form.is_valid()`,
surfaces `form.errors` to the client, and `form.save()`s the object — reusing the
consumer's existing form, including its custom `clean_<field>` / `clean()` validation,
its widget coercions, and its declared (non-model) fields. Without an equivalent in
this package, a graphene-django migrant with form-backed mutations must:

- rewrite each form's field-level and cross-field validation against the model's
  `full_clean()` (losing the `clean_<field>` / `clean()` logic the form already
  carries), and
- re-declare the input shape against the model's editable columns rather than the
  form's declared fields (a plain `Form` may declare fields that are *not* model
  columns — a `confirm_email`, a `captcha`, a computed field — which the
  model-driven [`spec-036`][spec-036] generator cannot express).

This is a Required `graphene-django` parity item (the card's own ⚛️ Required tag),
foundational by the [`START.md`][start] "do both libraries provide it?" test:
graphene-django ships form mutations as a first-class write surface, and
[`GOAL.md`][goal] success-criterion 6 names `ModelForm` explicitly as a target
write flavor. The work is **small in new machinery** precisely because
[`spec-036`][spec-036] froze the reusable contracts (the
[`FieldError` envelope][glossary-fielderror-envelope], the payload wrapper, the
[`DjangoMutationField`][glossary-djangomutationfield] factory, the
[`DjangoModelPermission`][glossary-djangomodelpermission] seam, the
[`_resolve_model`][spec-036] hook) **for exactly this card**: the only genuinely new
parts are the form-field → input mapping and the `is_valid()` → `form.errors` →
`save()` pipeline that replaces the model-construct + `full_clean()` heart.

## Current state

A true description of the repo as this spec is authored:

- **The mutation foundation is shipped.** [`mutations/sets.py`][mutations-sets]
  ships [`DjangoMutation`][glossary-djangomutation] with the overridable
  [`_resolve_model(meta)`][spec-036] classmethod (in `0.0.11` it reads `Meta.model`;
  the docstring names the `0.0.12` form flavor as the intended override:
  "the 0.0.12 form flavor (`Meta.form_class._meta.model`) … replace[s] [it] so
  they supply the model WITHOUT a literal `Meta.model`"). [`mutations/inputs.py`][mutations-inputs]
  ships the public [`FieldError`][glossary-fielderror-envelope] type, the
  `build_payload_type` wrapper (the uniform `node` / `result` slot via
  `payload_object_slot`), and the `NON_FIELD_ERROR_KEY = "__all__"` sentinel.
  [`mutations/resolvers.py`][mutations-resolvers] ships the
  `_validation_error_to_field_errors` mapper (the same envelope-population shape
  the form pipeline needs from `form.errors`), the `_locate_instance`
  visibility-scoped locate, `_refetch_optimized`, `_authorize_or_raise`, and the
  one-`transaction.atomic()` / one-`sync_to_async` boundary.
  [`mutations/fields.py`][mutations-fields] ships
  [`DjangoMutationField`][glossary-djangomutationfield], which validates
  `issubclass(mutation_cls, DjangoMutation)` and types the field from the bound
  `<Name>Payload` via a [`strawberry.lazy`][glossary-djangomutationfield]
  forward-ref. [`mutations/permissions.py`][mutations-permissions] ships
  [`DjangoModelPermission`][glossary-djangomodelpermission], whose `has_permission`
  reads the model via `mutation._resolve_model(mutation.Meta)` — so a form flavor
  overriding `_resolve_model` authorizes through the same default with **no
  permission-class change**.
- **No `forms/` module exists.** [`docs/TREE.md`][tree]'s *target* layout reserves
  `django_strawberry_framework/forms/` and [`tests/forms/`][test-forms] (both
  "planned by `TODO-ALPHA-038-0.0.12`"); neither is on disk. The package root
  [`__init__.py`][init] exports the four `036` mutation symbols
  ([`DjangoMutation`][glossary-djangomutation] /
  [`DjangoMutationField`][glossary-djangomutationfield] /
  [`FieldError`][glossary-fielderror-envelope] /
  [`DjangoModelPermission`][glossary-djangomodelpermission]) but no form symbol.
- **The version line reads `0.0.11`.** [`spec-037`][spec-037] Slice 4 bumped
  [`__init__.py`][init], [`pyproject.toml`][pyproject], and
  [`tests/base/test_init.py::test_version`][test-base-init] to `0.0.11`; this card
  moves them to `0.0.12`
  ([Decision 14](#decision-14--this-card-owns-the-0012-version-bump)).
- **`0.0.12` has exactly one card.** `038` is the only [`KANBAN.md`][kanban] card
  targeting `0.0.12` (`039` / `040` are `0.0.13`); there is no joint cut to defer
  the version bump to
  ([Decision 14](#decision-14--this-card-owns-the-0012-version-bump)).
- **The products write surface is live.** [`spec-036`][spec-036] Slice 4 added a
  products `Mutation` with model-driven `DjangoMutationField`s and wired
  `mutation=Mutation` in `config/schema.py`; products has **no** `forms.py` yet.
  The `Item` model carries the `unique_item_per_category` `UniqueConstraint` — a
  `ModelForm` over `Item` surfaces that as a `NON_FIELD_ERRORS` form error, the
  live `"__all__"`-sentinel coverage
  ([Decision 12](#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation)).

## Goals

1. **Ship `DjangoFormMutation` and `DjangoModelFormMutation` on the `class Meta`
   surface.** Both declared as a class with a nested `Meta` (`form_class` +
   optional `fields` / `exclude`), not a graphene `MutationOptions` /
   `__init_subclass_with_meta__` flow
   ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions) /
   [Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)).
2. **Derive the input from the form's declared fields.** A `forms/converter.py`
   form-field → Strawberry-annotation registry, reusing the read-side scalar /
   enum / [`Upload`][glossary-upload-scalar] converters where the field types
   overlap, so the input shape is the form's contract — including fields a model
   does not have
   ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
3. **Reuse the frozen `FieldError` envelope.** Map `form.errors` (and the form's
   `NON_FIELD_ERRORS` bucket) onto the byte-identical
   [`FieldError`][glossary-fielderror-envelope] envelope `036` defined
   ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)).
4. **Run the write through the form.** `form.is_valid()` → `form.save()`, sync and
   async, inside the one-`transaction.atomic()` boundary `036` set; the `ModelForm`
   payload's object is re-fetched and optimizer-planned for the response selection
   ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)
   /
   [Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path)).
5. **Compose with the shipped permission + visibility seams.** The `ModelForm`
   flavor inherits [`DjangoModelPermission`][glossary-djangomodelpermission]
   write-auth and the visibility-scoped `update` locate unchanged
   ([Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form)).
6. **Ship the products live form surface** (Slice 4).
7. **Complete the `0.0.12` cut.** This card is the lone `0.0.12` card, so Slice 5
   owns the version-file alignment
   ([Decision 14](#decision-14--this-card-owns-the-0012-version-bump)).

## Non-goals

- **DRF serializer mutations and auth mutations.** [`SerializerMutation`][glossary-serializermutation]
  (`Meta.serializer_class`, `0.0.13`, [`TODO-ALPHA-039-0.0.13`][kanban]) and
  [Auth mutations][glossary-auth-mutations] (`0.0.13`, [`TODO-ALPHA-040-0.0.13`][kanban])
  are separately carded; they reuse the same envelope but ship later
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **Changing the `036` model-driven generator or the `FieldError` envelope.** The
  frozen contracts are reused **unchanged**; this card adds no field to
  [`FieldError`][glossary-fielderror-envelope] and does not re-open
  [`mutations/inputs.py`][mutations-inputs]'s model-column generator
  ([Decision 2](#decision-2--card-scope-boundary-the-two-form-flavors-ship-serializer--auth-stay-out-the-frozen-036-contracts-are-reused-unchanged)).
- **The `TestClient` *ergonomic* helper, NOT file-field correctness.** This card
  **owns the runtime correctness** of `forms.FileField` / `forms.ImageField`: the
  `Upload` input typing, the `data=` / `files=` decode split, and `form_class(data=,
  files=, instance=)` construction
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)),
  proven by **at least one raw `django.test.Client` multipart live test** for a
  form-backed `Upload` field (Slice 4). The raw multipart HTTP path already exists
  from the `0.0.11` upload work, so correctness does **not** wait on a helper; only
  the *ergonomic* `TestClient`/`AsyncTestClient` wrapper is deferred to the `0.0.14`
  [`TestClient`][glossary-testclient] card ([Edge cases](#edge-cases-and-constraints)).
- **Form `delete`.** graphene-django form mutations are create / update only; a
  `ModelForm` does not delete. A `delete` write stays the model-driven
  [`DjangoMutation`][glossary-djangomutation] (`Meta.operation = "delete"`) the
  consumer already has ([Decision 10](#decision-10--operations-create--update-for-the-modelform-no-form-delete)).
- **`Meta.return_field_name`.** graphene-django's per-mutation output-field-name
  key is **not** adopted; the `036`-frozen uniform `node` / `result` slot
  supersedes it for one cross-flavor client contract
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling),
  carried in [Risks](#risks-and-open-questions) as a card-body tension).
- **A new `DjangoType` `Meta` key or settings key**
  ([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it? → foundational" test,
form mutations are **Required `graphene-django` parity** (the card's own ⚛️ Required
tag). The borrowing splits along the package's standing line — *surface-wise* copy
`graphene-django` / DRF (the `class Meta` + `Form` / `ModelForm` shape every Django
developer already knows), *behaviorally* keep the Strawberry engine and the
package's own optimizer-composed, permission-scoped, async-capable pipeline. The
*capabilities* of graphene-django's form mutations (run the form's validation,
surface `form.errors`, `form.save()` the object) are adopted at the **outcome**
level; the graphene `MutationOptions` / `ClientIDMutation` / `__init_subclass_with_meta__`
mechanism is **explicitly rejected** — it is the decorator-adjacent
metaclass-options surface the package replaces with a nested `class Meta`.

### Reference-package parity checkpoint

| Upstream | `django-strawberry-framework` | Status |
| --- | --- | --- |
| [`graphene_django.forms.mutation.DjangoFormMutation`][upstream-forms-mutation] (plain `Form`, `MutationOptions`) | [`DjangoFormMutation`][glossary-djangoformmutation] base + nested `Meta.form_class` ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions) / [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)) | this card — borrow the capability, reject the `MutationOptions` surface |
| [`graphene_django.forms.mutation.DjangoModelFormMutation`][upstream-forms-mutation] (`ModelForm`, `model` from `form_class._meta.model`) | [`DjangoModelFormMutation`][glossary-djangomodelformmutation] subclassing [`DjangoMutation`][glossary-djangomutation] via the [`_resolve_model`][spec-036] seam ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)) | this card — required parity |
| [`fields_for_form` + `convert_form_field`][upstream-forms-converter] (Django form field → GraphQL type) | [`forms/converter.py`][forms-converter] `convert_form_field` registry, reusing the read-side [scalar][glossary-scalar-field-conversion] / [choice-enum][glossary-choice-enum-generation] / [`Upload`][glossary-upload-scalar] converters where overlapping ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)) | this card — required parity |
| [`ErrorType.from_errors(form.errors)`][upstream-forms-types] on the payload | `form.errors` → the frozen [`FieldError` envelope][glossary-fielderror-envelope], `NON_FIELD_ERRORS` → the `"__all__"` sentinel ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)) | this card — reuse the `036`-frozen envelope, byte-identical |
| graphene-django `Meta.return_field_name` (per-mutation output field name) | not adopted — the `036` uniform `node` / `result` slot supersedes it ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)) | deliberate non-adoption (card-body tension, [Risks](#risks-and-open-questions)) |
| graphene-django `DjangoModelFormMutation` **full** update (a bound form over the raw input) | **partial** update via full-payload reconstruction from the located instance ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)) | deliberate divergence — matches the package's own `036` `PartialInput` contract |
| graphene-django form file fields (multipart `request.FILES` → form `files=`) | `Upload` input typing + the `data=` / `files=` decode split + `form_class(data=, files=, instance=)` ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)) | this card — runtime correctness owned here (raw multipart live test) |
| graphene-django [`get_form` / `get_form_kwargs`][upstream-forms-mutation] (constructor-kwarg seam) | `get_form_kwargs(info, *, data, files, instance=None)` / `get_form(...)` hooks (default the package kwargs) + schema-time discovery via `form_class.base_fields` / `get_form_fields()` ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth) / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)) | this card — parity seam for migrated forms needing `user` / request / tenant |
| graphene-django relation visibility (none — form's own queryset only) | every relation id (Relay + raw pk) visibility-checked through the related primary `get_queryset` before the form, then `to_field_name`-converted ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)) | package security invariant beyond graphene parity (the `036` contract, raw-pk gap closed) |
| graphene `MutationOptions` / `ClientIDMutation` / `__init_subclass_with_meta__` | rejected for a nested `class Meta` base ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions)) | deliberately not borrowed |

### From `graphene-django` — borrow the user-facing shape

- **`Form` / `ModelForm` consumption.** The mutation runs the consumer's existing
  form — `form_class(data=…, files=…)` (create) / a full-payload-reconstructed
  `form_class(data=…, files=…, instance=<row>)` (update), `form.is_valid()`,
  `form.save()`. The form's `clean_<field>` / `clean()` validation and widget
  coercions are honored for free; the one deliberate divergence is **partial** update
  semantics (graphene-django's form update is full), via the
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)
  reconstruction, for consistency with the model-driven `036` `PartialInput`.
- **`form.errors` → field-keyed envelope.** graphene-django's
  `ErrorType.from_errors(form.errors)` is the parity shape; here it maps onto the
  `036`-frozen [`FieldError`][glossary-fielderror-envelope].

### From `strawberry-graphql-django` — borrow the runtime composition

- **Optimizer-composed return + permission scoping.** The `ModelForm` payload's
  object rides the same `036` optimizer re-fetch + visibility-scoped `update`
  locate the model-driven mutation uses — Strawberry-native, async-capable.

### Explicitly do not borrow

- **graphene's `MutationOptions` / `__init_subclass_with_meta__` / `ClientIDMutation`.**
  Rejected: the metaclass-options + relay-mutation surface the package's nested
  `class Meta` replaces ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions)).
- **`Meta.return_field_name`.** Rejected for the `036`-frozen uniform slot
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)).
- **A second `errors` envelope shape.** Rejected: the card mandates one shared
  envelope across flavors; the `036` [`FieldError`][glossary-fielderror-envelope]
  is reused unchanged.

## User-facing API

Two new base classes, no new `DjangoType` `Meta` key. A consumer wraps a
`ModelForm` they already have:

```python
import strawberry
from django import forms

from django_strawberry_framework import (
    DjangoModelFormMutation,
    DjangoMutationField,
)

from . import models


class ItemModelForm(forms.ModelForm):
    class Meta:
        model = models.Item
        fields = ("name", "description", "category", "is_private")

    def clean_name(self):
        name = self.cleaned_data["name"]
        if name.lower() == "forbidden":
            raise forms.ValidationError("That name is reserved.")
        return name


class CreateItemViaForm(DjangoModelFormMutation):
    class Meta:
        form_class = ItemModelForm        # model resolves via form_class._meta.model
        operation = "create"


class UpdateItemViaForm(DjangoModelFormMutation):
    class Meta:
        form_class = ItemModelForm
        operation = "update"


@strawberry.type
class Mutation:
    # Exposed through the shipped DjangoMutationField — no class-attribute
    # annotation; the <Name>Payload is materialized at finalization.
    create_item_via_form = DjangoMutationField(CreateItemViaForm)
    update_item_via_form = DjangoMutationField(UpdateItemViaForm)
```

generates:

```graphql
type Mutation {
  createItemViaForm(data: ItemModelFormInput!): CreateItemViaFormPayload!
  updateItemViaForm(id: ID!, data: ItemModelFormPartialInput!): UpdateItemViaFormPayload!
}

input ItemModelFormInput {
  name: String!
  description: String
  categoryId: GlobalID!
  isPrivate: Boolean
}

type CreateItemViaFormPayload {
  node: ItemType
  errors: [FieldError!]!
}
```

The input fields are the **form's** declared fields (`ItemModelForm.Meta.fields`),
not the model's editable columns — `description` is optional because the form field
`required` is `False` (graphene-django parity). The relation input keeps the
cross-flavor `categoryId` GraphQL name, but the resolver decodes it to the **form
field** `category` (`{"category": pk}`) so the bound `ModelForm` validates it
natively — not via a raw model `setattr`
([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)
reverse map). On success the payload's `node` is the saved object re-fetched and
optimizer-planned for the response selection; on a `form.is_valid()` failure `node`
is `null` and `errors` carries one [`FieldError`][glossary-fielderror-envelope] per
offending field, with the form's `NON_FIELD_ERRORS` (cross-field `clean()`,
model-constraint) bucket keyed to the `"__all__"` sentinel.

**`update` is a true partial update.** `updateItemViaForm` takes
`ItemModelFormPartialInput` — all-optional here because `ItemModelForm` declares only
model-backed fields (a required *non-model* extra field, were there one, stays
required, [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload));
the resolver locates the row through
`ItemType.get_queryset(...)` (a row the caller cannot see is a not-found `FieldError`
on `id`, never an existence leak), then reconstructs the **full** bound-form payload
from the located row's current values overlaid with the provided fields before
constructing the form
([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)).
So changing only `name` preserves `category` / `description` / `isPrivate` (and any
file field), while `unique_item_per_category` still validates against the unchanged
`category` — the `036` `PartialInput` contract, not graphene-django's full-update
form. Write authorization is the inherited
[`DjangoModelPermission`][glossary-djangomodelpermission] default (the `add` /
`change` model perm).

A plain `Form` (no model) wraps the same way through
[`DjangoFormMutation`][glossary-djangoformmutation], but its payload has **no
`DjangoType` object slot** — it is the pinned two-field shape
([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)):

```graphql
type Mutation {
  subscribeToNewsletter(data: NewsletterFormInput!): SubscribeToNewsletterPayload!
}

type SubscribeToNewsletterPayload {
  ok: Boolean!
  errors: [FieldError!]!
}
```

On success `perform_mutate(self, form, info)` runs (default: `form.save()` if present,
else no-op; the consumer overrides it for the real side effect) and the payload is
`ok: true, errors: []`; on a validation failure `ok: false` with the field-keyed
`errors`. No cleaned-data is echoed (a model-less form returns a success flag, not
data — a consumer needing data back uses a `DjangoModelFormMutation`).

### Error shapes

- A `Meta` with no `form_class`; a `DjangoFormMutation` whose `form_class` is a
  `forms.ModelForm` (wrong base — checked first, the error names
  `DjangoModelFormMutation`) or is not a `forms.Form` subclass; a
  `DjangoModelFormMutation` whose `form_class` is not a `forms.ModelForm`, or whose
  `form_class._meta.model` is unresolvable; a bare-string
  / duplicate-name / unknown-name `Meta.fields` / `Meta.exclude` (validated against
  `form_class.base_fields`); or an empty effective field set — each raises
  [`ConfigurationError`][glossary-configurationerror] at mutation-class creation /
  finalization, naming the offending key.
- A `form.is_valid()` failure populates the
  [`FieldError` envelope][glossary-fielderror-envelope] (a null-object payload),
  **not** a top-level `GraphQLError`. A form field error keys to the form field
  name; a `clean()` / `NON_FIELD_ERRORS` error keys to the `"__all__"` sentinel.
- A write the caller is not authorized to perform
  ([`DjangoModelPermission`][glossary-djangomodelpermission] / `check_permission`
  denial) raises a top-level `GraphQLError`, **not** a `FieldError` entry — the same
  split [`spec-036`][spec-036] Decision 15 set.
- A sync form mutation whose target type has an `async def`
  [`get_queryset`][glossary-get_queryset-visibility-hook] raises
  [`SyncMisuseError`][glossary-syncmisuseerror] (coroutine closed first), the
  standing discipline.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/SPECS/spec-038-form_mutations-0_0_12.md`**.

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in
  [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN (`038`) and target patch
  (`0_0_12`) into the filename.
- The topic slug is `form_mutations` — short, snake-case, and naming the subsystem
  (the stem of the card DoD's suggested `docs/spec-form_mutations.md`).

Alternatives considered (and rejected):

- **The card's own `docs/spec-form_mutations.md`.** Rejected: predates the
  structured-filename convention; [`spec-036`][spec-036] Decision 1 (and the cards
  before it) set the precedent of preferring the structured name and recording the
  card's older one (carried in [Risks](#risks-and-open-questions)).
- **Topic slug `forms` / `modelform`.** Rejected: `forms` collides conceptually
  with the Django `forms` module name, and `modelform` undersells the plain-`Form`
  half the card also ships.

### Decision 2 — Card-scope boundary: the two form flavors ship; serializer / auth stay out; the frozen `036` contracts are reused unchanged

This card ships the **form-validated** write flavor end-to-end: the
[`DjangoFormMutation`][glossary-djangoformmutation] /
[`DjangoModelFormMutation`][glossary-djangomodelformmutation] bases, the
form-field → input mapping, the `is_valid()` → `form.errors` → `save()` pipeline,
and the products live form surface. It explicitly does **not** ship the adjacent
flavors, each owned by a named `0.0.13` card:

- **DRF serializer mutations** ([`SerializerMutation`][glossary-serializermutation])
  — [`TODO-ALPHA-039-0.0.13`][kanban].
- **Auth mutations** ([Auth mutations][glossary-auth-mutations]) —
  [`TODO-ALPHA-040-0.0.13`][kanban].

And it **reuses, byte-identical, the contracts [`spec-036`][spec-036] froze for
exactly this**: the [`FieldError` envelope][glossary-fielderror-envelope], the
`<Name>Payload` wrapper (uniform `node` / `result` slot), the
[`DjangoMutationField`][glossary-djangomutationfield] factory, the
[`DjangoModelPermission`][glossary-djangomodelpermission] / `Meta.permission_classes`
/ `check_permission` write-auth seam, and the [`_resolve_model`][spec-036] hook.
This card adds **no** field to [`FieldError`][glossary-fielderror-envelope] and does
not re-open the `036` model-column input generator (the form generator is a separate
module) — mirroring [`spec-036`][spec-036] Decision 2's "define the surface, reuse
it later" discipline from the other direction (`036` defined; `038` consumes).

Justification: the card is sized **L** and the serializer / auth flavors are
separately carded with their own `0.0.13` targets — pulling either forward would
bloat the slice exactly as [`START.md`][start]'s scope-creep rule warns. The
foundation already exists; this card's job is the form-specific generation + pipeline
on top of it.

Alternatives considered (and rejected):

- **Ship the serializer flavor too** (it is "close"). Rejected:
  [`SerializerMutation`][glossary-serializermutation] is its own `0.0.13` card with
  a soft DRF dependency and a serializer-field converter; the form flavor's
  Django-core `Form` dependency is unconditional and a distinct slice.
- **Extend the `036` `FieldError` with form metadata.** Rejected: the card mandates
  the envelope is **reused unchanged**; forking it would break the one-contract
  promise the `0.0.13` cards also depend on.

### Decision 3 — `class Meta` surface, not graphene's `MutationOptions`

A form mutation is a **base class with a nested `class Meta`** (`form_class` +
optional `fields` / `exclude` + `operation` for the `ModelForm` flavor), declared
exactly like every other consumer surface in the package. It is **not** graphene's
`MutationOptions` / `__init_subclass_with_meta__(form_class=..., model=...,
return_field_name=...)` keyword-options flow, and **not** a `ClientIDMutation`
lineage.

Justification: this is the package's defining surface contract, stated verbatim in
[`START.md`][start] ("Meta classes everywhere on consumer surfaces"). The
[`spec-036`][spec-036] [`DjangoMutation`][glossary-djangomutation] base already
established the nested-`Meta` mutation shape; the form flavor is uniform with it (and
with [`DjangoType`][glossary-djangotype] / [`FilterSet`][glossary-filterset] /
[`OrderSet`][glossary-orderset]). The *capabilities* of graphene-django's form
mutations are borrowed at the outcome level; the `MutationOptions` mechanism is not.

Alternatives considered (and rejected):

- **graphene's `__init_subclass_with_meta__` keyword options.** Rejected: it is the
  metaclass-options surface the nested `class Meta` replaces; it also fragments the
  declaration shape away from [`DjangoMutation`][glossary-djangomutation].
- **A `@django_form_mutation(form_class=...)` decorator.** Rejected: a decorator on
  a consumer class is exactly the shape [`START.md`][start] forbids.

### Decision 4 — Module and test locations: `forms/` subpackage mirroring `mutations/`

- **Source:** `django_strawberry_framework/forms/` — the subpackage
  [`docs/TREE.md`][tree]'s target layout reserves, split in the spirit of the
  [`mutations/`][mutations-sets] subpackage: [`converter.py`][forms-converter] (the
  form-field → annotation registry), [`inputs.py`][forms-inputs] (the form-derived
  input + the namespace materialization), [`sets.py`][forms-sets]
  (`DjangoFormMutation` / `DjangoModelFormMutation` + metaclass + `Meta` validation
  + the bind hook), and [`resolvers.py`][forms-resolvers] (the form pipeline). It
  reuses [`mutations/`][mutations-fields]'s
  [`DjangoMutationField`][glossary-djangomutationfield] and
  [`FieldError`][glossary-fielderror-envelope] rather than re-declaring them.
- **Tests:** new [`tests/forms/`][test-forms] mirroring the source modules
  (`test_converter.py` / `test_inputs.py` / `test_sets.py` / `test_resolvers.py`);
  live coverage extends [`test_products_api.py`][test-products-api].

Justification: the card predicts `django_strawberry_framework/forms/` and
[`tests/forms/`][test-forms]; the [`mutations/`][mutations-sets] subpackage
([`spec-036`][spec-036] Decision 4) is the proven shape for a `class Meta`-driven
write subsystem. A separate `forms/` subpackage keeps the form-specific generation +
pipeline cleanly distinct from the model-driven `mutations/` while sharing its
public contracts.

Alternatives considered (and rejected):

- **Fold the form bases into [`mutations/`][mutations-sets].** Rejected: the card
  predicts a `forms/` subpackage, the form-field converter is a distinct concern
  from the model-column generator, and the upcoming serializer flavor gets its own
  `rest_framework/` subpackage too — one subpackage per flavor keeps each
  extension point separable.
- **A flat `forms.py` module.** Rejected: the surface is a converter + a metaclass +
  a resolver pipeline + input generation — a subpackage matches it, and the card
  predicts `forms/`.

### Decision 5 — Public surface: `DjangoFormMutation` / `DjangoModelFormMutation` exported from the root

Two net-new public symbols, re-exported from [`__init__.py`][init] and added to
`__all__`:

- `DjangoFormMutation` — the plain-`Form` base.
- `DjangoModelFormMutation` — the `ModelForm` base.

No net-new field factory or error type: both flavors are exposed through the
**existing** [`DjangoMutationField`][glossary-djangomutationfield] and return the
frozen [`FieldError`][glossary-fielderror-envelope] envelope. But "exposed through
`DjangoMutationField`" is **not** "the factory is unchanged" — the shipped factory is
hardwired to the model write path on three axes, each of which this card must
generalize into an overridable seam on the mutation base (the seam set is the spine
of [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling),
and the future `0.0.13` [`SerializerMutation`][glossary-serializermutation] flavor is
designed to reuse every one of them — though `039` is not yet specced, so that reuse
is a forward intent, not a commitment this card can bind):

1. **Target check.** [`mutations/fields.py`][mutations-fields] `_validate_mutation_target`
   asserts `issubclass(mutation_cls, DjangoMutation)`. The `ModelForm` flavor passes
   (it *is* a subclass); the model-less plain `DjangoFormMutation` does not, so the
   check is generalized to "a concrete member of the mutation/form family" (a shared
   marker base or a duck-typed `_mutation_meta` + `_payload_type_name` check).
2. **Resolver dispatch.** `DjangoMutationField._resolve` hardcodes
   `resolve_mutation_sync` / `resolve_mutation_async` imported from
   [`mutations/resolvers.py`][mutations-resolvers] — the **model** pipeline
   (`model(**attrs)` + `full_clean()` + `save()`), which never reads `Meta.form_class`.
   If the factory called that for a form flavor, [`forms/resolvers.py`][forms-resolvers]
   would be dead code and the form's `is_valid()` / `save()` would never run. So the
   dispatch is generalized: the mutation base gains overridable `resolve_sync(cls,
   info, *, data, id)` / `resolve_async(...)` classmethods (the model base delegates to
   [`mutations/resolvers.py`][mutations-resolvers]; the form flavors override to
   [`forms/resolvers.py`][forms-resolvers]), and `_resolve` calls
   `mutation_cls.resolve_sync` / `resolve_async`
   ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)).
3. **The `data:` input-ref.** `_synthesized_mutation_signature` builds the `data:`
   annotation from `_lazy_ref(_input_type_name(meta))`, and `_input_type_name` derives
   the name from `editable_input_fields(meta.model, …)` (the **model columns**, e.g.
   `ItemInput`) wrapped in `strawberry.lazy(INPUTS_MODULE_PATH)` (the `mutations.inputs`
   module). A form-derived input (a different shape, materialized in the `forms` input
   namespace under a form-derived name, e.g. `ItemModelFormInput`) would never resolve
   against that ref. So the name + module become overridable seams the factory
   consults (`mutation_cls.input_type_name(meta)` + `mutation_cls.input_module_path`),
   the model flavor keeping the current defaults
   ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).

These generalizations are **behavior-preserving for the model flavor** (every seam
defaults to today's model path) — the cross-cutting "no regression" gate
([Definition of done](#definition-of-done)) pins the shipped `036` model-driven
surface unchanged.

Justification: keeping the public surface at two symbols (the two bases) — reusing
the field factory + error type via seams rather than a parallel factory — honors the
"one exposure idiom, one error contract" posture the package and the card both want,
and the seams are exactly what the `0.0.13` serializer flavor needs next (so the
generalization is the DRY investment, not throwaway). The audience for both bases is
every schema with a form-backed write, so the root export matches
[`DjangoMutation`][glossary-djangomutation]'s placement.

Alternatives considered (and rejected):

- **A net-new `DjangoFormMutationField`.** Rejected as the default (a second exposure
  idiom for the same job once the seams exist); retained only as the
  [Risks](#risks-and-open-questions) fallback if generalizing the shipped factory's
  dispatch / input-ref proves invasive.
- **Claiming the factory is reused "unchanged."** Rejected as factually wrong: the
  shipped factory's resolver dispatch and `data:`-ref derivation are hardwired to the
  model path (verified in [`mutations/fields.py`][mutations-fields]), so the form
  flavor demands the three seam generalizations above — a real `fields.py` change, not
  a no-op reuse.
- **Exposing only from `django_strawberry_framework.forms`.** Rejected: the bases are
  used in schema modules alongside root-exported types, exactly as
  [`DjangoMutation`][glossary-djangomutation] is root-exported.

### Decision 6 — Base-class strategy: `DjangoModelFormMutation` rides the `DjangoMutation` base; the plain form is the model-less sibling

**`DjangoModelFormMutation` subclasses [`DjangoMutation`][glossary-djangomutation]**,
overriding [`_resolve_model`][spec-036] to return `Meta.form_class._meta.model`. It
reuses the *value* the base provides — the primary
[`DjangoType`][glossary-djangotype] payload resolution (the uniform `node` / `result`
slot), the [`DjangoModelPermission`][glossary-djangomodelpermission] default (which
reads the model via `_resolve_model`, so the override authorizes it for free), the
visibility-scoped `update` locate, the optimizer re-fetch, and the existing
phase-2.5 [`bind_mutations`][mutations-sets] pass — but **the base is hardwired to
the model write path in four places that this card refactors into overridable seams**
(the model flavor keeps every default; the form flavor overrides; the `0.0.13`
serializer flavor is expected to reuse the same seams once it is specced):

- **Class-creation `Meta` validation.** The shipped `DjangoMutationMetaclass` calls
  the module function `_validate_mutation_meta`, whose allowed-key set
  (`_ALLOWED_MUTATION_META_KEYS`) has **no** `form_class` and which **requires**
  `operation ∈ {"create", "update", "delete"}`. Inherited as-is, a
  `DjangoModelFormMutation` would (a) reject `Meta.form_class` as an unknown key and
  (b) accept `operation = "delete"`, which the form flavor does not support
  ([Decision 10](#decision-10--operations-create--update-for-the-modelform-no-form-delete)).
  So the validation is refactored into an overridable `DjangoMutation._validate_meta(meta)`
  classmethod the metaclass invokes (the model base keeps today's body); the form base
  overrides it with the form allowed-key set (adds `form_class`; drops `model` /
  `input_class` / `partial_input_class`), restricts `operation` to `{"create",
  "update"}` (rejecting `delete` at class creation), and validates `Meta.form_class`
  presence + `forms.ModelForm`-subclass **before** delegating to `_resolve_model`, so a
  missing / wrong-type `form_class` is a clean [`ConfigurationError`][glossary-configurationerror]
  naming the key, never a raw `AttributeError` from `form_class._meta.model` and never
  the base's misleading "set `Meta.model`" message.
- **Input generation (at the bind).** The bind's `_materialize_input_for` builds a
  **model-column** `<Model>Input` via `build_mutation_input(meta.model, …)`. The form
  flavor materializes a **form-derived** input instead, so `_bind_mutation`'s
  input-materialization step routes through an overridable
  `DjangoMutation.build_input(meta, primary_type)` hook (model default vs the
  [`forms/`][forms-inputs] generator,
  [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
  The bind does **not** apply unchanged for the input half.
- **The `data:` input-ref name + module** (the [`DjangoMutationField`][glossary-djangomutationfield]
  seam, [Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)).
- **Resolver dispatch** (`form.is_valid()` / `form.save()` vs `model(**attrs)` +
  `full_clean()`, [Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)
  / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)).

That [`_resolve_model`][spec-036] is overridable is the seam [`spec-036`][spec-036]
Decision 5 designed ("the 0.0.12 form flavor derive[s] the model from
`Meta.form_class._meta.model` … without re-opening the base validation") — but it is
*one* of the four seams, not the whole story; the spec-036 author scoped only the
model-source seam, and the other three are net-new generalizations this card lands.

**`DjangoFormMutation` (plain `Form`) is the model-less sibling.** A plain `Form` has
no model, so it cannot resolve a primary [`DjangoType`][glossary-djangotype] payload
or inherit [`DjangoMutation`][glossary-djangomutation]'s resolvable-model contract.
It is a lighter base (its own metaclass) that shares the form pipeline (`is_valid()`
→ `form.errors` → `FieldError` → `perform_mutate`) and the converter, but its payload
carries **no DjangoType object slot**. Because it is **not** a
[`DjangoMutation`][glossary-djangomutation] subclass, it is **not** caught by
`register_mutation` / [`bind_mutations`][mutations-sets] (which iterate the
`DjangoMutation` declaration registry), so it needs its **own** registration + bind
machinery, specified explicitly (no "if needed" hedge) in
[Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change):
a `forms/sets.py` declaration registry + a `clear_form_mutation_registry`
co-cleared from `registry.clear()` + a `bind_form_mutations()` entry point wired into
[`types/finalizer.py`][types-finalizer]'s phase-2.5 window alongside `bind_mutations()`.
**Pinned plain-form payload contract (P2 — a fixed schema rule, not a preferred /
fallback branch).** The generated `<Name>Payload` for a plain `DjangoFormMutation` is
**exactly two fields**: `ok: Boolean!` and `errors: [FieldError!]!`. No cleaned-data
output fields are generated. The success/failure contract: on `form.is_valid()`
success, `perform_mutate` runs and the payload is `ok: true, errors: []`; on a
validation failure, `perform_mutate` does **not** run and the payload is `ok: false`
with one `FieldError` per offending field (the form's `NON_FIELD_ERRORS` bucket under
the `"__all__"` sentinel) — the same envelope every flavor returns. A write-auth
denial is a top-level `GraphQLError`, never a payload (`036` Decision 15). The
side-effect hook is **`perform_mutate(self, form, info) -> None`**: the default calls
`form.save()` when the form exposes it (a `ModelForm` would, but the plain flavor is
for non-`ModelForm` forms) and is otherwise a no-op; a consumer overrides it for the
real action (send mail, enqueue a job) and returns `None`. The payload shape does not
mirror input narrowing (there are no output fields to narrow), has no nullable
ambiguity (`ok` is non-null, `errors` is the non-null list of non-null `FieldError`),
and needs no per-field descriptions. This is the **fully-pinned** resolution of the
prior preferred/fallback uncertainty: an implementer cannot ship a divergent
plain-form shape.

Rejected (recorded, not silently dropped): **cleaned-data echo** — graphene-django's
plain `DjangoFormMutation` echoes `form.cleaned_data` as output fields (its
`fields_for_form` is dual-purposed for input *and* output). Rejected for `0.0.12`
because (a) `cleaned_data` is heterogeneous and includes values with no clean GraphQL
output mapping (a `forms.FileField`'s cleaned value is an `UploadedFile`; a
`ModelChoiceField`'s is a model instance), so a faithful echo would need a second
output-type generator and ad-hoc per-type rules; (b) the plain form is a
parity-completeness flavor where a predictable success flag is sufficient — a consumer
that needs to return data uses a model-backed `DjangoModelFormMutation` (which returns
the `node` / `result` object); and (c) `ok` + `errors` is trivially well-typed for a
model-less payload and keeps the cross-flavor `errors` envelope identical. The
asymmetry still mirrors graphene-django's split (its `DjangoModelFormMutation` is
model-backed; its `DjangoFormMutation` is not) — only the model-less *output* shape
differs, deliberately.

**`Meta.return_field_name` is not adopted.** graphene-django lets a `ModelForm`
mutation name its output field; [`spec-036`][spec-036] Decision 7 (AR-H5) **froze**
the uniform `node` / `result` slot precisely to keep one client contract across
flavors and to dodge model-name collisions (`Property` → `property`). The form flavor
inherits that frozen slot. The card body lists `Meta.return_field_name` as part of
the surface; preferring the frozen `036` slot is a deliberate divergence recorded in
[Risks](#risks-and-open-questions) per the [`docs/SPECS/NEXT.md`][next] "prefer the
card, surface the conflict" rule (the conflict is between the card body and a
*frozen downstream contract* `036` established, which the card itself depends on).

Justification: subclassing [`DjangoMutation`][glossary-djangomutation] for the
`ModelForm` flavor reuses the maximum shipped machinery for zero new
model-pipeline code, and the [`_resolve_model`][spec-036] seam was built for it. The
plain-form model-less case is genuinely different (no model row to return), so a
sibling base is the honest shape rather than bending the model-required base.

Alternatives considered (and rejected):

- **Make the plain `Form` also subclass [`DjangoMutation`][glossary-djangomutation]
  by relaxing the model requirement (the unified architecture).** Rejected: even
  with the `_validate_meta` seam making the model-requirement overridable, a
  model-less plain form would force model-less branches into *every* model-centric
  step of [`bind_mutations`][mutations-sets] (`_resolve_primary_type(meta.model)`,
  `build_payload_type(object_type=primary_type, …)`) and the payload-slot derivation,
  rippling the no-model case through the model-driven path the model + ModelForm
  flavors share. A contained sibling base with its own small registry + bind keeps
  the model-driven `_bind_mutation` free of model-less conditionals. (The cost — a
  parallel registry + `bind_form_mutations()` + a `finalizer.py` wiring line — is
  named explicitly in [Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change),
  not hand-waved.)
- **Honor `Meta.return_field_name`.** Rejected: it forks the payload object-field
  name across flavors, the exact collision the `036` uniform slot was frozen to
  prevent.

### Decision 7 — Form-field → Strawberry input mapping: the form is the input source of truth

The input type derives from the **form's declared fields**
(`form_class.base_fields`, the stable class-level set — schema-time field discovery
above), not the model's editable columns. [`forms/converter.py`][forms-converter]
ships a `convert_form_field(field)` registry (the [graphene-django parity
shape][upstream-forms-converter]) returning each form field's Strawberry annotation +
required-ness from `field.required`:

- text-like (`CharField` / `EmailField` / `SlugField` / `URLField` / `RegexField` /
  `ChoiceField` / base `Field`) → `str`; `IntegerField` → `int`; `BooleanField` →
  `bool`; `NullBooleanField` → `bool | None`; `FloatField` → `float`;
  `DecimalField` → `Decimal`; `UUIDField` → `uuid.UUID`; `DateField` /
  `DateTimeField` / `TimeField` → the Python-native types; `MultipleChoiceField` →
  `list[str]`.
- `ModelChoiceField` → the target model's id (a Relay-`GlobalID` when the target's
  primary [`DjangoType`][glossary-djangotype] is Relay-Node-shaped, else the raw pk
  scalar — reusing the [`mutations/inputs.py`][mutations-inputs]
  `relation_input_annotation` strategy); `ModelMultipleChoiceField` →
  `list[<id>]`.
- `forms.FileField` / `forms.ImageField` → the [`Upload`][glossary-upload-scalar]
  scalar ([`spec-037`][spec-037]).

**The related model for a relation field's id basis.** A `ModelForm` relation
field has a backing column, so the related model (and its primary
[`DjangoType`][glossary-djangotype], which decides Relay-`GlobalID` vs raw pk) is
resolved through that column (`form_class._meta.model._meta.get_field(name)` →
`column.related_model`). A **plain `Form`** `ModelChoiceField` /
`ModelMultipleChoiceField` (a form-declared relation with no model column) has no
such column, so its related model is its **`field.queryset.model`**; the identical
Relay-`GlobalID`-vs-raw-pk rule and `<name>_id` / `list[<id>]` scheme then apply, so
the wire contract is uniform across the model-backed and model-less relation paths.
The [`forms/resolvers.py`][forms-resolvers] decode (the relation visibility check in
[Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload))
resolves the same related primary type by the **same basis** — `column.related_model`
for a model-backed relation, `field.queryset.model` for a model-less one — so the
input id type and the decode's visibility query agree.

**Where a form field overlaps a Django column type, reuse the read-side converters.**
A `ChoiceField` whose choices come from a model's `choices` should resolve to the
**same** generated Strawberry enum the read [`DjangoType`][glossary-djangotype] and
the `036` model-driven input synthesize (a symmetric wire contract), routing through
the [Choice enum generation][glossary-choice-enum-generation] /
[Scalar field conversion][glossary-scalar-field-conversion] registry rather than a
parallel mapping. **The reuse mechanism matters** because
[`types/converters.py`][types-converters]'s `convert_scalar` / `scalar_for_field` are keyed
on `models.Field` subclasses (an MRO walk), **not** on `forms.Field`: the overlap
reuse is reachable only for a **`ModelForm`** field that has a backing column —
resolve it via `form_class._meta.model._meta.get_field(name)` and route the column
through `convert_scalar` / `convert_choices_to_enum` (and a relation through
[`mutations/inputs.py`][mutations-inputs] `relation_input_annotation`). A **plain
`Form`** field with no model column (a `captcha`, a `confirm_email`) has no read-side
equivalent and necessarily uses the form-field → Strawberry table in
[`forms/converter.py`][forms-converter] — which is therefore genuinely net-new
machinery for the model-less case, **not** a parallel copy of the scalar table for the
model-backed case (the explicit guard against the over-DRY-into-drift trap). An
unknown form-field class raises [`ConfigurationError`][glossary-configurationerror]
naming the field and class (the graphene-django `convert_form_field`
`ImproperlyConfigured` parity, raised as the package's own exception).

**The fail-loud contract requires NOT registering a base-`forms.Field` catch-all
(P2).** A naive `functools.singledispatch` with `forms.Field` registered → `str` makes
**every** custom `forms.Field` subclass dispatch to that catch-all, so the
unknown-field raise becomes **unreachable** and a consumer's custom field silently
becomes `String`. So the registry's **fallthrough (unregistered) default RAISES**
`ConfigurationError`, and the supported classes are registered *individually*
(`CharField`, `IntegerField`, … — their subclasses, e.g. `EmailField` /
`SlugField` / `RegexField` under `CharField`, still map via the dispatch MRO, the
parity behavior). A bare **`forms.Field`** is handled as an **explicit exact-type
special case** → `str` (so the listed "base `Field` → `str`" still holds), **not** as a
catch-all registration. The upshot: a known field or a subclass of one maps; a bare
`forms.Field` maps to `str`; a custom `class CustomField(forms.Field)` with no
supported ancestor hits the raising default — proven by a `CustomField(forms.Field)`
test asserting the raise.

**Per-field metadata: the `input_attr` → `form_field_name` reverse map (P1).** The
generated input GraphQL names follow the cross-flavor `036` convention so the wire
contract is uniform across mutation flavors — a `ModelChoiceField` named `category`
generates `categoryId` (python attr `category_id`), a scalar/`MultipleChoice`/file
field keeps its own name. But a **bound Django form is keyed by form-field name**
(`ItemModelForm(data={"category": pk})`, **not** `{"category_id": pk}` — the latter
makes the form think `category` is missing). So `forms/inputs.py` **retains, per
generated input field, an `(input_attr, graphql_name) → (form_field_name, kind)`
metadata record** that `forms/resolvers.py` consults at decode, where `kind ∈
{scalar, relation_single, relation_multi, file}`:

- `category_id` / `categoryId` → form field `category`, kind `relation_single`
  (the form relation decoder below type-checks the id — `GlobalID` *or* raw pk —
  resolves the **visible** object through the related primary type's `get_queryset`,
  and places its `to_field_name` value (default `obj.pk`) under `category`, which the
  bound `ModelChoiceField.to_python` then resolves).
- `genres` → form field `genres`, kind `relation_multi` (each element decoded,
  visibility-checked, and `to_field_name`-converted the same way, then placed as a
  list under `genres` for `ModelMultipleChoiceField`).
- `avatar` → form field `avatar`, kind `file` (routed to `files=`, see
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)).
- every plain scalar → identity (`name` → `name`, kind `scalar`).

The reverse map is the single fix for the P1 "`category_id` vs `category`" hazard: the
generated input may *expose* `categoryId` (parity), but the decode always produces a
**form-field-keyed** dict the bound form validates natively — never accidental
model-assignment semantics. Package + live tests prove the relation field validates
**through the form** (`clean_<field>` runs), not through a raw model `setattr`.

**A dedicated form relation decoder visibility-checks EVERY branch — Relay `GlobalID`
AND raw pk (P1 — a security fix, NOT a reuse of the `036` helper unchanged).** A
default `ModelForm`'s relation queryset is `Category.objects.all()` — **not**
request-scoped — so the visibility gate must run before the form. The shipped `036`
[`mutations/resolvers.py`][mutations-resolvers]`::_decode_relation_id_set` is **not**
reused as-is, because it deliberately passes a **raw pk scalar through with no
visibility hook** (`#"A raw pk scalar"` — it only visibility-checks the Relay
`GlobalID` branch, since a raw-pk target has no `GlobalID` to scope; a raw-pk M2M gets
an existence check but still not a visibility check). Reusing it unchanged would let
the **non-Relay raw-pk branch** attach a hidden related object — the exact invariant
this card claims to hold. So [`forms/resolvers.py`][forms-resolvers] runs its **own**
`relation_single` / `relation_multi` decoder that reuses the `036` *primitives*
(`decode_model_global_id` for a `GlobalID`, `_coerce_relation_pk_or_none` for a raw pk —
type-check / coerce; a wrong-model or uncoercible id → field-keyed `FieldError`) and
then, for **both** the Relay and the raw-pk branch, **resolves the object from the
related primary [`DjangoType`][glossary-djangotype]'s
[`get_queryset`][glossary-get_queryset-visibility-hook]** (the same
`apply_type_visibility_sync(initial_queryset(...))` query every read surface applies);
a pk not in that visible set is the same no-existence-leak field-keyed `FieldError`,
whether it arrived as a `GlobalID` or a raw pk. The form's own `queryset` is then a
*secondary* guard, not the only one.

**`to_field_name` is honored when converting the object back to the form's key (P2 —
#6).** A `ModelChoiceField` may set `to_field_name` (and a
`ForeignKey(to_field="slug")` generates exactly that), so `to_python` looks the object
up by the configured field, **not** `pk` — feeding a raw `pk` would make a valid
GraphQL id fail form validation. So after the visibility query yields the visible
**object**, the decoder converts it with the form field's own key:
`obj.serializable_value(field.to_field_name)` when `to_field_name` is set, else
`obj.pk`, and places that under the form field name (per element for
`ModelMultipleChoiceField`). A hidden-`Category` id (Relay or raw pk) therefore returns
the **identical** field-keyed `FieldError` the model-driven mutation returns — proven
by live + package tests over a Relay primary AND a non-Relay (raw-pk) primary, for both
single and multi relations.

**Two generated inputs: create (`field.required`) + partial.** Like the `036`
`Input` / `PartialInput` split, the form flavor generates `<FormClass>Input` (create;
each field's requiredness from the form field's `field.required`) and
`<FormClass>PartialInput` (update). In the partial input, **model-backed** form fields
are forced optional — [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)'s
reconstruction supplies them from the located row — but a **non-model** extra form
field (a `confirm`, a captcha, an action flag, with no model column to reconstruct
from) keeps its declared `field.required` (P2 — see
[Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)'s
required-extra-field rule), so a required extra field stays required on update and an
optional one may be omitted.

**Shape identity + naming + collision (the `036` discipline, P1).** A generated form
input's identity is **not** its name — it is the tuple **`(form_class, operation
kind, frozenset(effective field names after `Meta.fields` / `Meta.exclude`))`**,
exactly parallel to `036`'s `(model, operation kind, effective field set)`
([`mutations/inputs.py`][mutations-inputs] `mutation_input_shape` /
`mutation_input_type_name`). The **operation kind** component is the
`DjangoModelFormMutation`'s `"create"` / `"update"`, or the fixed sentinel **`"form"`**
for a plain `DjangoFormMutation` (which has no model operation, P2) — so a plain
form's input cache key is well-defined (`(form_class, "form", effective set)`) and two
plain mutations over the same form + effective set dedupe. Keying on the **form class object** (not its `__name__`)
captures the field *representation* — two forms with the same field names but
different field types are different `form_class`es, so they never wrongly dedupe. The
generated GraphQL **name** is the canonical `<FormClass.__name__>Input` /
`<FormClass.__name__>PartialInput` for the **full** effective shape, and a
**deterministic shape-derived name** (the model-flavor's injective sorted-field-token
scheme) for a **narrowed** (`Meta.fields` / `Meta.exclude`) shape — so two different
narrowings of one form get distinct names, and two narrowings to the *same* effective
set dedupe. **Two distinct shapes that resolve to the same generated GraphQL name
raise [`ConfigurationError`][glossary-configurationerror] at finalization** — this is
the **fail-loud fix** for the two collision cases the review names: (a) the same
`ItemModelForm` used by two mutations with different effective field sets (distinct
shape-derived names; no clash, but if a narrowing collides with the canonical name it
raises), and (b) two **different** `ItemForm` / `NewsletterForm` classes with the same
`__name__` — both emit `<__name__>Input`, and because they are **distinct `form_class`
identities they can never dedupe** (dedupe is only within one `form_class` + effective
set), so this **always raises** regardless of whether their field shapes happen to
match; the consumer disambiguates by renaming one form (a future explicit
name-override `Meta` key is out of scope). Only repeats of the **same** `(form_class,
operation kind, effective set)` dedupe to one materialized class. The raise comes
**for free** from reusing
[`utils/inputs.py`][utils-inputs]`::materialize_generated_input_class`, whose ledger
already raises on a second *different* class under one name (the `036` AR-H1 / AR-M6
raise) — so the form flavor inherits the early-`ConfigurationError`-not-late-Strawberry-error
posture rather than re-deriving it.

**`Meta.fields` / `Meta.exclude` are normalized + fail-loud against `form_class.base_fields`
(P3).** Mirroring `036`'s `_normalize_field_sequence`, the form base validates the
narrowing at **class creation**: a bare string (`fields = "name"`) is rejected (it
would iterate as characters), duplicate names are rejected, `fields` and `exclude`
are mutually exclusive, and a name in neither `form_class.base_fields` raises
[`ConfigurationError`][glossary-configurationerror] naming the unknown field (a typo
like `fields = ("emial",)` fails loud, never silently shrinks the input). An
**empty effective field set** (a `fields = ()`, an `exclude` that drops every field,
or a form with no fields) raises [`ConfigurationError`][glossary-configurationerror]
at finalization — never a bare empty `@strawberry.input` that Strawberry rejects only
at schema build (the `036` empty-input guard, applied to `form.base_fields`).

**A `create` narrowing that drops a required form field is rejected (P2).** A bound
form fails required-validation for any `field.required` field absent from its bound
`data=`, and `initial` is **not** a substitute for submitted data — so a `create`
whose effective field set (after `Meta.fields` / `Meta.exclude`) omits a still-declared
required form field would compile to a schema that *looks* valid but can **never**
succeed. The form base therefore raises [`ConfigurationError`][glossary-configurationerror]
at class creation, naming the missing required field(s), when `operation = "create"`
and the narrowing excludes any `field.required` form field (covering **both**
`Meta.fields` and `Meta.exclude`). The escape hatch is an overridable
`get_form_kwargs` / `get_form` ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload))
that supplies those values before binding: when the consumer has overridden that hook,
the guard is waived (it cannot know *which* fields the override injects, so it trusts
the explicit override rather than block a legitimate scoped form). `update` is exempt —
its reconstruction supplies model-backed fields from the instance, and a required
non-model extra field stays required in the input anyway.

**Materialization + the `data:`-ref seam.** [`forms/inputs.py`][forms-inputs] builds
one `@strawberry.input` from the form fields — reusing
[`utils/inputs.py`][utils-inputs]'s single-sited `build_strawberry_input_class` +
`materialize_generated_input_class` core (the same machinery `mutations/inputs.py` /
`orders/inputs.py` wrap, with its own `forms` module path + `family_label` + ledger),
not a hand-rolled `setattr` — and materializes it as a module global of the **`forms`
input namespace** under a form-derived name (`<FormClass>Input`, e.g.
`ItemModelFormInput`) — a name and a shape distinct from the `036` model-column
`<Model>Input` in `mutations.inputs`. So the [`DjangoMutationField`][glossary-djangomutationfield]
`data:` lazy ref **cannot** use the shipped `_input_type_name(meta)` (model columns) +
`INPUTS_MODULE_PATH` (`mutations.inputs`): the form flavor overrides the
`input_type_name(meta)` + `input_module_path` seams
([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root))
so the synthesized `data:` ref names the form input in the `forms` namespace, and the
bind's `build_input(meta, primary_type)` hook
([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling))
materializes exactly that class — so the ref the field synthesizes and the class the
bind materializes are one and the same (the lifecycle discipline the set families and
`036` already follow).

**Schema-time field discovery reads `form_class.base_fields`, never an instance
(P2 — the kwarg-requiring-form fix).** The input shape is derived from
**`form_class.base_fields`** — the class-level declared-fields dict Django's
`DeclarativeFieldsMetaclass` / `ModelFormMetaclass` populate at class creation (for a
`ModelForm`, `base_fields` already includes the model-derived fields). Reading it
needs **no instantiation**, so a form whose `__init__` requires constructor kwargs
(`user`, `request`, a tenant — common in migrated forms) still has a discoverable,
**request-independent stable** field shape (a form that mutates `self.fields` in
`__init__` by request could not be a stable GraphQL input anyway). An overridable
classmethod **`get_form_fields(cls) -> dict[str, forms.Field]`** (default:
`form_class.base_fields`) lets a consumer customize the discovered set; whatever it
returns must be stable across requests. This replaces the earlier "instantiate
`form_class()` no-arg to read `form.fields`" plan, which broke for kwarg-requiring
forms.

Justification: the form — not the model — is the validation and field contract a
form-mutation consumer chose; a plain `Form` can declare fields with no model column
(a `confirm_email`, a `captcha`), which the model-column `036` generator cannot
express. Deriving from `form_class.base_fields` (the stable class-level field set) is
the only correct source, and it is exactly what graphene-django's `fields_for_form`
does. Reusing the read-side converters where types overlap keeps the wire contract
symmetric without duplicating the scalar table.

Alternatives considered (and rejected):

- **Derive the input from the model's editable columns (reuse the `036`
  generator).** Rejected: it drops form-only fields and ignores form-level
  `required` overrides — wrong for a plain `Form`, and divergent from the consumer's
  declared form contract for a `ModelForm`.
- **A parallel form-field scalar table independent of the read converters.**
  Rejected: it would let a `choices` form field resolve to a different enum than the
  read side, breaking the symmetric wire contract; reuse the shipped registry.

### Decision 8 — Resolver pipeline: instantiate → `is_valid()` → `form.errors` → `save()` → optimizer re-fetch → payload

[`forms/resolvers.py`][forms-resolvers] runs one pipeline per flavor, sync and async,
swapping the model-construct + `full_clean()` heart of the
[`mutations/resolvers.py`][mutations-resolvers] pipeline for the form's own
validation and write, but **reusing the surrounding `036` steps**:

**Ordering correction — authorize runs BEFORE the relation decode (post-ship security
fix).** The step numbers below reflect the original draft sequence, but the shipped
pipeline runs **authorize before step 1's relation decode** (for `update`: locate →
authorize → decode), matching the `036` model path's authorize-first order. The relation
decode (step 1) issues visibility-scoped `get_queryset` queries, so running it before the
write-authorization check (step 3) let an unauthorized caller probe related-object
visibility by id — a write-auth denial (top-level `GraphQLError`) versus an in-band
relation [`FieldError`][glossary-fielderror-envelope] is an observable distinction. The
corrected order collapses both to the denial and closes that side channel; any flavor
reusing this pipeline (the `0.0.13` [`SerializerMutation`][glossary-serializermutation])
**must authorize before decoding relations**.

1. **Decode** the `data:` input into **two `dict`s keyed by FORM-field name** —
   `provided_data` (scalars, choice-enum raw values, and relation pks / pk-lists) and
   `provided_files` (uploaded files) — using the
   [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)
   `input_attr → (form_field_name, kind)` reverse map (`UNSET` stripped). A
   `relation_single` / `relation_multi` field runs the **dedicated form relation
   decoder** ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth),
   **not** the `036` `_decode_relation_id_set` — which skips the visibility hook on the
   raw-pk branch): it type-checks each id (`GlobalID` *or* raw pk; wrong-model /
   uncoercible → field-keyed `FieldError`, the `036` AR-H4 contract), **resolves the
   visible object through the related primary `DjangoType.get_queryset` for BOTH
   branches** (a hidden / unseeable target is the same field-keyed `FieldError`, no
   existence leak), and lands the object's `to_field_name` value (default `obj.pk`)
   under the form field name (`{form_field_name: value}` / `{form_field_name: [value,
   …]}`); a `file` field lands its uploaded value in **`provided_files`**, not
   `provided_data` (the P1 file-routing fix below); a `scalar` choice-enum member is
   unwrapped to its raw value. The split by `kind` is the single point that keeps
   form-field names,
   visibility-checked relation pks, and file uploads each going to the right place.
2. **Locate** (`update`, `ModelForm` only): the top-level `id:` argument is
   `strawberry.ID` (a raw GlobalID **string** the package decodes server-side via the
   reused `036` `_coerce_lookup_id` — the same `node(id: ID!)` contract the shipped
   [`DjangoNodeField`][glossary-djangonodefield] uses, **distinct** from a relation
   `data:` field whose value is a
   Strawberry-coerced `GlobalID`); a malformed / wrong-model / uncoercible `id:` is an
   `id`-keyed `FieldError` **before** any lookup (no existence leak — the mutation
   surface returns the `FieldError` envelope, **not** the node field's
   `null` / `GLOBALID_INVALID`). The row is then resolved through the target type's
   [`get_queryset`][glossary-get_queryset-visibility-hook] (the `036`
   `_locate_instance`); a miss (hidden or genuinely absent — indistinguishable) is a
   not-found `FieldError` on `id`. This step
   **only locates** — the form is **not** constructed here (the located row is
   carried to step 4 as the `instance=` kwarg), so the form is built exactly once, in
   step 4, from the reconstructed `data=` / `files=` payload. (graphene-django builds
   its form once too via `get_form_kwargs`, but as a *full* update; the package's
   step-4 merge is what adds true partial semantics on top of that single
   construction.)
3. **Authorize**: the inherited `check_permission` / `Meta.permission_classes`
   (before validation for `create`; after the locate for `update`). A denial raises
   a top-level `GraphQLError` ([`spec-036`][spec-036] Decision 15).
4. **Construct + validate** the form **once**, through the overridable
   **`get_form_kwargs(self, info, *, data, files, instance=None) -> dict`** hook (P2 —
   the graphene-django `get_form_kwargs` parity seam, used by `create`, `update`, and
   the plain form). The default returns `{"data": data, "files": files}` (plus
   `"instance": instance` when non-`None`), and the resolver builds the form as
   `form_class(**self.get_form_kwargs(info, data=…, files=…, instance=…))`. A consumer
   overrides it to inject constructor kwargs migrated forms need — `user=…`,
   `request=…`, a tenant — or to scope a `ModelChoiceField.queryset` **without
   changing the generated input shape** (the input is derived from
   `get_form_fields()`, [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth),
   independent of `get_form_kwargs`). A `get_form(self, info, *, data, files,
   instance=None)` hook (default: `form_class(**self.get_form_kwargs(...))`) is the
   coarser override for full control. This **does not replace** the relation-visibility
   gate (step 1, which runs before the form regardless) — `get_form_kwargs` adds
   request-scoping on top of, not instead of, the visibility check. The form is built
   with the `data=` / `files=` split Django requires (a bound form reads
   scalars/relations from `data=` and uploaded files from `files=` — an `UploadedFile`
   in `data=` does **not** validate):
   - **`create`** — `data = provided_data`, `files = provided_files`, then
     `form_class(**get_form_kwargs(info, data=provided_data, files=provided_files))`.
   - **`update` (the pinned partial-update contract, P1)** — a bound `ModelForm`
     validates **every** field, so handing it only the provided fields would reject a
     valid partial update (missing-required) or clear omitted optional fields. So the
     resolver **reconstructs the complete bound payload from the located instance plus
     the provided values**: `data = {**model_to_dict(instance, fields=<the form's
     non-file fields>), **provided_data}` (the instance's current values — FK as pk
     under `category`, M2M as `[pk]` under `genres` — overlaid by the provided
     fields), and `files = provided_files` **only** (an omitted file field is
     preserved by the bound `form_class(instance=…)` via its `initial`, never
     re-supplied and never cleared); then `form_class(**get_form_kwargs(info,
     data=data, files=files, instance=<located row>))`. This yields true partial
     semantics — omitted scalars,
     FKs, M2Ms, and files are preserved; provided fields update — **and** the form
     validates the full merged set, so `unique_item_per_category` validates correctly
     when only `name` changes (the unchanged `category` comes from the instance). It
     matches the `036` model-driven `PartialInput` contract (consistent partial-update
     UX across both mutation flavors), not graphene-django's full-update form.
     - **Required extra (non-model) form fields (P2).** `model_to_dict` only supplies
       **model-backed** fields, so a `ModelForm`'s extra declared field with no model
       column (a `confirm`, a captcha, an action flag) has **no instance value to
       reconstruct**. The pinned rule: in the `<FormClass>PartialInput`, model-backed
       fields are forced optional (reconstructed), but a **non-model form field keeps
       its declared `field.required`** ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
       So a **required** extra field stays required on update (the caller must supply
       it — it is in `provided_data`, never silently `None`), while an **optional**
       extra field may be omitted (and the bound form applies its own `initial` /
       empty value). This avoids both failure modes the review names — an all-optional
       input that lets a caller omit a required extra field (then the bound form fails
       required validation confusingly) and a meaningless reconstructed `initial`.
   Then `form.is_valid()`. A failure maps `form.errors` onto the
   [`FieldError` envelope][glossary-fielderror-envelope] by **reusing the `036`
   mapper directly, not a parallel one**: `form.errors.as_data()` yields the
   `{field: [ValidationError, …]}` shape that
   [`mutations/resolvers.py`][mutations-resolvers] `_validation_error_to_field_errors`
   already consumes through its `error_dict` branch, so the form pipeline calls
   `_validation_error_to_field_errors(ValidationError(form.errors.as_data()))` — the
   form's `NON_FIELD_ERRORS` bucket lands on the `"__all__"` sentinel
   (`NON_FIELD_ERROR_KEY`) for free, byte-identical to a model `full_clean()` failure
   (the same field-keyed flatten graphene-django's `ErrorType.from_errors(form.errors)`
   produces). That mapper is promoted out of module-private as part of the shared
   pipeline surface (the helper-promotion paragraph below). Returns a null-object
   payload.
5. **Write**: for a `ModelForm`, `form.save()` (commit=True; M2M written via the
   internal `save_m2m()`) returns the saved instance. For a plain `Form`,
   `perform_mutate(self, form, info)` runs the form's side effect per the pinned
   plain-form contract
   ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)):
   the default calls `form.save()` when present, else is a no-op, and a consumer
   overrides it for a custom action. **The save is wrapped by the `036` save-time
   `IntegrityError` → `FieldError` mapper (P1), not left to bubble.** A `form.is_valid()`
   pass can still lose a concurrent-uniqueness race or hit a residual DB constraint at
   `save()`; the write runs through the shipped
   [`mutations/resolvers.py`][mutations-resolvers]`::save_or_field_errors` (promoted
   to the shared surface), so that `IntegrityError` class returns the **same
   null-object + `FieldError` envelope** the model-driven path returns (the same
   message policy / `"__all__"` keying), **never** a top-level `GraphQLError` / 500 —
   preserving the cross-flavor envelope contract at write time as well as validation
   time. This wraps **both** the `ModelForm` `form.save()` and the plain-form
   `perform_mutate` default save path. Runs inside the one `transaction.atomic()`
   boundary (the `IntegrityError` is caught at the resolver, so the atomic block is
   exited cleanly with the envelope as the result).
6. **Re-fetch** (`ModelForm`): re-read the saved row by pk and optimizer-plan it for
   the response selection through the `036` `refetch_optimized`
   ([Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path)).
7. **Return** the `<Name>Payload` (the saved object in the uniform slot + empty
   `errors` on success; null object + populated `errors` on failure).

**Helper reuse — share, do not re-implement.** Steps 2 / 3 / 4 / 6 / 7 are not new
code: the form pipeline **calls the shipped `036` pipeline helpers by name** (now
promoted to the public, underscore-dropped surface this slice landed) —
`locate_instance` (the visibility-scoped `update` locate, a security contract),
`coerce_lookup_id` / `not_found_error` (the server-side `id` decode + not-found
shape), `authorize_or_raise` (the write-auth gate), `refetch_optimized`
([Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path)),
`build_payload` + `payload_object_slot` (the uniform-slot envelope),
`validation_error_to_field_errors` (the validation-error mapper reused per step 4),
and `save_or_field_errors` (the save-time `IntegrityError` → `FieldError` mapper
reused per step 5, P1, generalized to wrap a zero-arg save callable) — plus the
`transaction.atomic()` + `sync_to_async(thread_sensitive=True)` boundary. These are
**module-private (`_`-prefixed) in [`mutations/resolvers.py`][mutations-resolvers]
today**, so this card is the first cross-module consumer: rather than have
[`forms/resolvers.py`][forms-resolvers] reach into another module's privates (a new
anti-pattern) or re-implement them (the duplication this avoids), Slice 3 **promotes
the reused subset to a shared, importable surface** — the lighter edit is dropping the
leading underscore on exactly that subset in [`mutations/resolvers.py`][mutations-resolvers];
the cleaner edit is lifting them to a neutral `mutations/_pipeline.py` (or
[`utils/querysets.py`][utils-querysets]'s neighborhood) that both
[`mutations/resolvers.py`][mutations-resolvers] and [`forms/resolvers.py`][forms-resolvers]
import — mirroring how the set families lifted their shared scaffold to
[`utils/`][utils-querysets] / `sets_mixins.py` in the `0.0.9` DRY pass. Slice 3 picks one
and names it; "reuses the surrounding steps" is not left to the implementer to
re-derive.

**How this pipeline actually fires.** [`mutations/fields.py`][mutations-fields]'s
`DjangoMutationField._resolve` hardcodes the **model** resolver
(`resolve_mutation_sync` / `resolve_mutation_async` from
[`mutations/resolvers.py`][mutations-resolvers]); if it called that for a form flavor,
this `forms/resolvers.py` pipeline would be dead code. So the field factory is
generalized to call the overridable `resolve_sync` / `resolve_async` classmethods on
the mutation base
([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)):
the model base delegates to [`mutations/resolvers.py`][mutations-resolvers]; both form
flavors override them to delegate **here**. A `ModelForm`'s
[`form.save()`][upstream-forms-mutation] with `commit=True` writes its M2M rows
(`save_m2m()` runs inside `save()`), so step 5 stays a single `form.save()` inside the
one `transaction.atomic()` — no separate M2M step.

The async path runs the whole sync body in one
`sync_to_async(thread_sensitive=True)` call, and a sync pipeline meeting an
`async def` [`get_queryset`][glossary-get_queryset-visibility-hook] raises
[`SyncMisuseError`][glossary-syncmisuseerror] — both inherited from the `036`
boundary discipline.

Justification: `form.is_valid()` / `form.save()` is the Django-native form contract
graphene-django uses; routing `form.errors` into the frozen envelope (rather than
raising) is the one-contract promise; reusing the `036` locate / authorize /
transaction / re-fetch steps means the form flavor inherits every composition `036`
already proved.

Alternatives considered (and rejected):

- **Run the model's `full_clean()` in addition to `form.is_valid()`.** Rejected:
  double validation, and a plain `Form` has no model to clean; the form's validation
  is authoritative.
- **A separate per-flavor transaction / async shape.** Rejected: the one-`atomic()`
  / one-`sync_to_async` boundary `036` set is the proven foundation; reuse it.

### Decision 9 — Optimizer composition: the `ModelForm` payload re-fetch rides the `spec-036` G2 path

The `ModelForm` payload's object (pipeline step 6) is re-fetched by pk and routed
through the **same** `036` `_refetch_optimized` /
[`DjangoOptimizerExtension`][glossary-djangooptimizerextension] path the model-driven
mutation uses. Because the operation is a mutation, the [`spec-035`][spec-035] **G2**
gate keeps `select_related` / `prefetch_related` but suppresses
[`.only(...)`][glossary-only-projection] — so the re-fetched instance carries no
selection-shaped deferred-field set. The re-fetch is **by pk without the visibility
filter** (the `036` Medium-1 exception: the actor just wrote the row, so round-tripping
their own write is not an existence leak).

Justification: reusing the `036` re-fetch is the whole point of subclassing
[`DjangoMutation`][glossary-djangomutation] — the G2 composition and the
by-pk-without-visibility contract come for free, with no new optimizer code and no
new live-test handoff (the `036` Slice 4 G2 test already discharged the
[`spec-035`][spec-035] obligation).

Alternatives considered (and rejected):

- **Return `form.save()`'s instance without re-fetching.** Rejected: a freshly
  saved instance has no related rows loaded, so any relation in the response
  selection N+1s — exactly the failure the `036` re-fetch prevents.

### Decision 10 — Operations: `create` / `update` for the `ModelForm`, no form `delete`

`DjangoModelFormMutation` reuses `Meta.operation` ∈ `{"create", "update"}` (the
`036` selector). A form `delete` is **not** shipped: graphene-django's form mutations
are create / update only, a `ModelForm` does not delete a row, and the model-driven
[`DjangoMutation`][glossary-djangomutation] (`Meta.operation = "delete"`) already
covers deletion. The plain `DjangoFormMutation` has no model operation — its action
is the form's `perform_mutate`, so it does not declare `Meta.operation`, and its
`_validate_meta` **rejects** any `Meta.operation` (create / update / delete alike) as
unsupported rather than silently accepting a meaningless value (P2); its input-shape
identity uses the fixed `"form"` sentinel for the operation component
([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
This split — `DjangoModelFormMutation` validates `operation ∈ {"create","update"}`,
plain `DjangoFormMutation` rejects `operation` outright — is the single resolution of
the prior contradiction (one shared checklist rule that read as if the plain base also
took `create` / `update`).

Justification: matching the upstream operation set keeps the parity surface honest;
a form `delete` would be a new contract with no graphene-django precedent and a
redundant overlap with the shipped model-driven `delete`.

Alternatives considered (and rejected):

- **Add a form `delete`.** Rejected: no upstream precedent, and the model-driven
  `delete` is the existing path; adding it would invent surface the card does not
  ask for.

### Decision 11 — Write authorization: reuse the `036` seam (`DjangoModelPermission` for the `ModelForm`, explicit classes for the plain form)

The `ModelForm` flavor inherits [`DjangoModelPermission`][glossary-djangomodelpermission]
unchanged: because `has_permission` reads the model via
`mutation._resolve_model(mutation.Meta)`, the `_resolve_model` override
([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling))
makes the `add` / `change` model-permission default work for free — an anonymous or
under-privileged caller is denied before the form runs. The visibility-scoped
`update` locate (Decision 8 step 2) and the write-auth check are the same separate
layers `036` set ("can view" ≠ "can write").

The **plain `Form`** has no model, so the model-permission default cannot apply.
**Preferred resolution:** the plain `DjangoFormMutation` requires the consumer to set
`Meta.permission_classes` explicitly for a real gate (there is no safe
model-permission default without a model); shipping it with the safe-by-default
posture means an *unset* `permission_classes` on a plain form denies (a deny-by-default
class), so a public plain-form write is an explicit opt-in (`Meta.permission_classes
= []`, the `036` AllowAny opt-out) — settled with its fallback in
[Risks](#risks-and-open-questions).

Justification: reusing the `036` write-auth seam is the card's explicit
reuse-the-foundation posture; the `ModelForm` flavor gets it for free, and the
plain-form case keeps the safe-by-default stance `036` established rather than
silently shipping an unauthenticated write surface.

Alternatives considered (and rejected):

- **A new form-specific permission class.** Rejected: the `036` seam already covers
  the `ModelForm` flavor, and a plain form's authorization is a consumer choice, not
  a model-permission one.

### Decision 12 — Live coverage: products grows a `ModelForm` and a plain `Form` mutation

Slice 4 adds `examples/fakeshop/apps/products/forms.py` with an `ItemModelForm`
(`forms.ModelForm` over `Item`, with a `clean_<field>` for field-level coverage and
the model's `unique_item_per_category` constraint for the `"__all__"`-sentinel
coverage) and a small plain `Form`. `products/schema.py` exposes a
`DjangoModelFormMutation` (create + update) and a `DjangoFormMutation` via
[`DjangoMutationField`][glossary-djangomutationfield]; `config/schema.py` already
wires `mutation=Mutation` ([`spec-036`][spec-036] Slice 4).
[`test_products_api.py`][test-products-api] (seeded via `seed_data` /
`create_users`) pins the create / update happy paths, the `form.errors` envelope
(field-level and `"__all__"`), write authorization, and the visibility-scoped
`update`. (The card DoD phrases the live path as the `examples/fakeshop/test_query/`
*directory*; this spec narrows it to the existing `test_products_api.py` inside that
directory, since products already carries the `Item` constraint and the `036`
`Mutation` wiring — a faithful narrowing, not a deviation.)

Justification: the [`AGENTS.md`][agents] live-HTTP-priority rule makes the products
write surface the right home for form-mutation acceptance coverage; products already
has the `Item` constraint and the `Mutation` wiring `036` added, so the form surface
is a small additive extension, not a new app.

Alternatives considered (and rejected):

- **Synthetic-model-only coverage (no live surface).** Rejected: form mutations are
  live-reachable the moment products exposes them, and the
  [`AGENTS.md`][agents] rule prioritizes the live `/graphql/` test where a realistic
  request reaches the path.

### Decision 13 — Finalization seam: reuse the mutation phase-2.5 bind, no `DEFERRED_META_KEYS` change

**`DjangoModelFormMutation` binds through the existing
[`bind_mutations`][mutations-sets] pass** (it is a
[`DjangoMutation`][glossary-djangomutation] subclass, so its metaclass calls
`register_mutation` and the shipped `_bind_mutation` resolves its primary
[`DjangoType`][glossary-djangotype] and materializes its `<Name>Payload`) — but **not
unchanged**: the bind's input-materialization step (`_materialize_input_for`, which
today calls the model-column `build_mutation_input(meta.model, …)`) routes through
the overridable `build_input(meta, primary_type)` hook
([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)),
so the form flavor materializes the **form-derived** input under its form-derived name
in the `forms` input namespace, before `strawberry.Schema(...)`, exactly as the `036`
and set-family inputs materialize (the lifecycle discipline is reused; the *generator*
is swapped). The payload (`build_payload_type`), primary-type resolution, and the
`registry.clear()` co-clear all apply unchanged for this flavor.

**The plain `DjangoFormMutation` is model-less and not a
[`DjangoMutation`][glossary-djangomutation] subclass**, so `bind_mutations` never sees
it. It gets its **own** explicit machinery (no "if needed"): a `forms/sets.py`
declaration registry (`register_form_mutation` / `iter_form_mutations`), a
`clear_form_mutation_registry()` co-cleared from `registry.clear()` (mirroring
`clear_mutation_registry`), and a `bind_form_mutations()` entry point that
materializes each plain form's model-less input + payload. **`registry.clear()`
co-clears THREE form rows** (Slice 2, verified): `clear_form_input_namespace` (the
Slice-1 generated-input/payload-globals ledger, finally wired here),
`clear_form_mutation_registry` (the plain-form declaration registry above), and
`clear_form_shape_build_cache` (the form-input build cache — the deliberate twin of
the model-flavor `_shape_build_cache`, needed so two mutations over one form-shape
dedupe to one materialized input instead of tripping the materialize collision; it
is cleared at `bind_form_mutations()` start AND co-cleared here so a stale class from
a failed / re-run finalize cannot leak). `bind_form_mutations()` is
**wired into [`types/finalizer.py`][types-finalizer]'s phase-2.5 window** alongside the
existing `bind_mutations()` / `_bind_filtersets()` / `_bind_ordersets()` calls — a
single named `finalizer.py` edit, not a new public finalize entry point the consumer
must call.

**The two ledgers stay separate; the registry *mechanics* are shared (DRY without
over-DRY).** The `DjangoMutation` registry and the plain-form registry **must remain
two independent `list[type]` ledgers** — they are different declaration namespaces
with different `bind_*` bodies and different `registry.clear()` co-clear rows, so
merging the *storage* is the over-DRY trap to avoid. But the four functions'
*bodies* — identity-dedup append, post-`mark_finalized()` reject, `.clear()`, ordered
`tuple(...)` snapshot — are mechanically identical to `mutations/sets.py`'s
`register_mutation` quad (verified: `register_mutation` is exactly that dedup +
post-finalize-reject). Rather than clone the four bodies, factor the shared mechanics
into a small `make_declaration_registry(label)` helper (returning bound `register` /
`clear` / `iter` callables over a fresh private list) that **both**
`mutations/sets.py` and `forms/sets.py` instantiate — single-sourcing the
dedup/reject/clear logic while keeping the ledgers disjoint. This is the same
single-source-the-mechanics-keep-the-ledgers move the `0.0.9` DRY pass made for the
set families' materialize/collision machinery in [`utils/inputs.py`][utils-inputs].

**No change to [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS`**: a
form-mutation `Meta` is its own validation namespace
([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)),
not a [`DjangoType`][glossary-djangotype] `Meta` key — honoring the
[Cross-subsystem invariants][glossary-cross-subsystem-invariants] rule (promote a
`DjangoType` `Meta` key only when its subsystem applies it end-to-end).

Justification: the `ModelForm` flavor reuses the one finalization gate via the
`build_input` seam (the materialize-before-`Schema` discipline
[`spec-027`][spec-027] / [`spec-028`][spec-028] / `036` all share); the plain form's
own registry + `bind_form_mutations()` is the contained cost of keeping the
model-driven `_bind_mutation` free of model-less branches
([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)),
and it still hangs off the single [`finalize_django_types()`][glossary-finalize_django_types]
call (no second public finalize entry point). Leaving `DEFERRED_META_KEYS` untouched
honors the cross-subsystem invariant.

Alternatives considered (and rejected):

- **A separate public `finalize_django_forms()` entry point.** Rejected: a second
  gate the consumer must remember to call; `bind_form_mutations()` hangs off the
  existing `finalize_django_types()` phase-2.5 window instead.
- **Claiming the `036` bind materializes the form input "unchanged."** Rejected as
  false: `_materialize_input_for` builds a model-column input from `meta.model`
  (verified in [`mutations/sets.py`][mutations-sets]); the form flavor must swap the
  generator via the `build_input` seam.

### Decision 14 — This card owns the `0.0.12` version bump

Unlike [`spec-036`][spec-036] (which shared `0.0.11` with the sibling
[`Upload`][glossary-upload-scalar] card [`spec-037`][spec-037] and so deferred to the
joint cut), **`038` is the lone `0.0.12` card.** [`docs/SPECS/NEXT.md`][next] Step 3
scopes "multiple cards share the patch" to a shared version cut; no other WIP / To-Do
card targets `0.0.12` (`039` / `040` are `0.0.13`), so the deferral condition is not
met. Leaving the version at `0.0.11` after `038` ships would make the docs and
exports claim `0.0.12` behavior under a `0.0.11` identity, and nobody would bump it.
Slice 5 therefore aligns the version quintet — exactly as [`spec-037`][spec-037]
Decision 10 owned the final `0.0.11` cut:

- [`pyproject.toml`][pyproject]
- `__version__` in [`__init__.py`][init]
- [`tests/base/test_init.py::test_version`][test-base-init]
- the [`docs/GLOSSARY.md`][glossary] package-version line
- `uv.lock` if it carries the package version

Justification: `038` closes the `0.0.12` feature set (it is the only card in it), so
it owns the cut. The bump moves only after the bases, tests, and docs are complete
(Slice 5), never in Slice 1.

Alternatives considered (and rejected):

- **Defer the bump to a separate release-alignment card.** Rejected: no such
  `0.0.12` card exists; a deferral would orphan the bump.
- **Bump in Slice 1.** Rejected: the version should move only after the feature and
  docs are complete.

## Implementation plan

Five slices. Slices 1–3 are package-internal and staged; Slice 4 is the live
products form surface; Slice 5 is doc + version-cut only. Line deltas are planning
estimates.

| Slice | Files touched | New / changed tests | Approx. delta |
| --- | --- | --- | --- |
| 1 — form-field converter + reverse map + the two form-derived inputs | [`forms/converter.py`][forms-converter] (new; `convert_form_field` fail-loud dispatch + the `input_attr → (form_field_name, kind)` reverse map), [`forms/inputs.py`][forms-inputs] (new; `<FormClass>Input` + `<FormClass>PartialInput` from `base_fields`, shape identity, narrowing + create-required guards, `get_form_fields()`), [`forms/__init__.py`][forms-init] (new) | [`tests/forms/test_converter.py`][test-forms] + [`tests/forms/test_inputs.py`][test-forms] (~36 — every form-field class, id mapping, `Upload`, the reverse-map + `kind` flag, custom-field raise, `base_fields` discovery, the create + partial input shapes, shape-identity collision/dedupe, `Meta.fields`/`exclude` fail-loud + empty-set + create-required guard) | `+420 / 0` |
| 2 — the two base classes + `Meta` validation + bind seams | [`forms/sets.py`][forms-sets] (new; the form bases + a `make_declaration_registry` shared helper both registries instantiate), [`mutations/sets.py`][mutations-sets] (refactor validation into the overridable `_validate_meta`; add the `build_input` / `input_type_name` / `input_module_path` / `resolve_sync` / `resolve_async` seams, all model-defaulted; adopt the `make_declaration_registry` helper for its own quad), [`mutations/inputs.py`][mutations-inputs] (`build_payload_type(object_type=None)` emits the model-less `{ ok errors }` plain-form payload from ONE builder + ONE materialize ledger per Decision 6 — the model branch byte-unchanged), [`types/finalizer.py`][types-finalizer] (wire `bind_form_mutations()` into phase 2.5), [`registry.py`][registry] (THREE form co-clear rows: `clear_form_input_namespace` + `clear_form_mutation_registry` + `clear_form_shape_build_cache`), [`mutations/fields.py`][mutations-fields] (TODO-anchor only — the `_input_type_name` body is now byte-identical to the `input_type_name` seam; Slice 3 deletes it), [`__init__.py`][init] (two exports) | [`tests/forms/test_sets.py`][test-forms] + [`tests/mutations/test_sets.py`][test-mutations] extend (~20 — `Meta` matrix incl. `delete`-rejected + `form_class`-accepted, both bind paths, no-primary error, model-flavor seam defaults unchanged) | `+340 / -30` |
| 3 — form relation decoder + resolver pipeline + field-factory generalization | [`forms/resolvers.py`][forms-resolvers] (new; the visibility-on-every-branch form relation decoder + the `kind`-split decode + the partial-update reconstruction + the sync/async pipeline entries), [`mutations/resolvers.py`][mutations-resolvers] (promote the reused pipeline helpers — `locate_instance` / `coerce_lookup_id` / `authorize_or_raise` / `refetch_optimized` / `build_payload` / `not_found_error` / `validation_error_to_field_errors` / `save_or_field_errors` (generalized to wrap a zero-arg save callable) / `raw_choice_value` — to an importable shared surface, underscore-dropped in place, so `forms/` reuses by call, not by re-implementation; `authorize_or_raise` denial message falls back to the mutation class name when `_primary_type is None`), [`forms/sets.py`][forms-sets] (fill the four `resolve_*` stubs to delegate to `forms/resolvers.py`; add the `get_form_kwargs` / `get_form` construction hooks on both bases + `perform_mutate` / `check_permission` on the plain base; wire the `guard_required` create-required waiver; extend `_cached_build_form_input` to return `(input_cls, field_specs)` and stash `_input_field_specs` at bind for the decode reverse map), [`mutations/fields.py`][mutations-fields] (generalize the target check (duck-typed `_has_mutation_protocol`, no `issubclass(DjangoMutation)` / no form-base import) **and** the `_resolve` dispatch (call `mutation_cls.resolve_sync` / `resolve_async`, `id`-gate on `operation != "form"`) **and** the `data:` lazy-ref derivation (consult `input_type_name` / `input_module_path`; payload-return ref stays `mutations.inputs`); delete the transient `_input_type_name` twin — [Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)), [`mutations/sets.py`][mutations-sets] / [`mutations/permissions.py`][mutations-permissions] / [`relay.py`][relay] (docstring-only `::OldName` rename-sweep refs from the helper promotion, per the AGENTS.md symbol-rename mandate) | [`tests/forms/test_resolvers.py`][test-forms] + [`tests/mutations/test_fields.py`][test-mutations] extend (~46 — create/update, decode `data=`/`files=` split, relation visibility on Relay **and** raw-pk single+multi, `to_field_name`, `IntegrityError` envelope, `get_form_kwargs`/`get_form` hooks, partial-update preservation + required-extra rule, envelope + `"__all__"`, plain-form `ok`+`errors`, visibility locate, write-auth, sync+async, G2 plan-shape, model-flavor dispatch unchanged) + the `::OldName` call-site/docstring rename sweep in [`tests/mutations/test_resolvers.py`][test-mutations] / `test_permissions.py` / [`test_products_api.py`][test-products-api] | `+660 / -30` |
| 4 — products live form surface | `examples/fakeshop/apps/products/forms.py` (new; + a minimal file column/migration if needed for the multipart test), [`products/schema.py`][products-schema] (form mutations), [`test_products_api.py`][test-products-api] | live create/update via `ModelForm`, `categoryId`-through-form, partial-update preservation, `form.errors` envelope, write-auth, **a raw multipart `Upload` test**, plain-form success + validation | `+220 / -0` |
| 5 — docs + `0.0.12` version cut + card wrap | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`README.md`][readme], [`GOAL.md`][goal], [`TODAY.md`][today], [`docs/TREE.md`][tree], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban], version files | `test_version` → `0.0.12` | `+120 / -50` |

Total expected delta: ~`+1740 / -90` — an L cut, matching the card's relative size.
The `036`-surface generalization (the `mutations/sets.py` / `mutations/fields.py`
seams + the `types/finalizer.py` wiring) is a real, named part of that delta — not the
"single additive target-check edit" an earlier draft budgeted; it is justified because
the seams default to today's model behavior (no model-flavor regression) **and** are
the same extension points the `0.0.13` [`SerializerMutation`][glossary-serializermutation]
flavor is designed to reuse (a forward intent — `039` is not yet specced). Staged-but-not-implemented seams follow the [`AGENTS.md`][agents]
design-doc anchor discipline (a source-site `TODO(spec-038 Slice N)` comment naming
this spec, removed in the slice that ships it).

## Edge cases and constraints

- **Form-only fields (no model column).** A plain `Form` field with no model column
  (a `confirm_email`, a `captcha`) becomes an input field via the form converter and
  is validated by the form; it never reaches a model write. This is exactly why the
  input derives from the form, not the model
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- **`ModelForm` `clean()` / `NON_FIELD_ERRORS`.** A cross-field `clean()` error or a
  model-constraint error (`Item.unique_item_per_category`) surfaces in
  `form.errors[NON_FIELD_ERRORS]`, mapped to the `"__all__"` sentinel `036` froze —
  the same key a model-driven multi-field-constraint `ValidationError` uses, so the
  client contract is identical across flavors.
- **`update` partial-update preservation (P1).** The resolver reconstructs the full
  bound payload (`data = {**model_to_dict(instance, fields=<non-file form fields>),
  **provided_data}`, `files = provided_files`) before
  `form_class(data=, files=, instance=<row located via get_queryset>)`
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)).
  So a `name`-only update preserves the unprovided scalar (`description`), the FK
  (`category`, as its current pk), the M2M (`genres`, as the current pk list), and any
  file field (omitted → kept via the bound form's `initial`); a provided **non-file**
  optional field the consumer wants emptied is sent explicitly (e.g. `""` for a
  `CharField`). A hidden row is not-found before the form runs.
- **File / image form fields run live in this card; CLEARING is out of scope (P1 /
  P3).** `forms.FileField` / `forms.ImageField` map to the
  [`Upload`][glossary-upload-scalar] scalar ([`spec-037`][spec-037]) on input, and the
  resolver routes uploaded values into the form's **`files=`** argument (a bound Django
  form reads files from `files=`, never `data=`), so `form_class(data=…, files=…,
  instance=…)` validates them — a **runtime correctness contract this card owns**,
  proven by a raw `django.test.Client` multipart live test (Slice 4); only the
  ergonomic `TestClient` helper is deferred to `0.0.14` ([Non-goals](#non-goals)). The
  two supported file actions are **upload** (provide an `Upload`) and **preserve**
  (omit it on partial update → kept via the bound `ModelForm(instance=…)`'s `initial`).
  **Clearing** a stored file is **explicitly out of scope for `0.0.12`**: Django's
  `ClearableFileInput` distinguishes "no change" from "clear" with a *false sentinel*,
  not an uploaded value, and a nullable `Upload` gives the resolver no clear signal
  (omitting means preserve). A future card may add an explicit `<field>Clear: Boolean`
  routed through the widget's clear path ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **A `ModelForm` whose `Meta.fields` omits an editable column.** The omitted column
  is simply not an input field — the form's contract governs the write surface
  (graphene-django parity), and the model's column default applies on `save()`.
- **A `ChoiceField` over model `choices`.** Resolves to the same generated enum the
  read side uses ([Choice enum generation][glossary-choice-enum-generation]); the
  decode unwraps the enum member to its raw choice value before the form sees it
  (reusing the `036` `_raw_choice_value` discipline).
- **Relation visibility is not delegated to the form's queryset (P1).** A
  `ModelChoiceField`'s default queryset is `Category.objects.all()` (not
  request-scoped), so the decode type- and visibility-checks the id through the
  related primary `DjangoType.get_queryset` **before** the form sees it; a hidden /
  unseeable target is a field-keyed `FieldError`, identical to the model-mutation
  path. The form's own queryset remains a secondary guard
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- **A `ModelForm` placed on the plain `DjangoFormMutation` base (P2).** Rejected at
  class creation with a [`ConfigurationError`][glossary-configurationerror] naming
  `DjangoModelFormMutation`. `forms.ModelForm` is **not** a `forms.Form` subclass (a
  sibling under `forms.BaseForm`), so the plain base checks
  `issubclass(form_class, forms.ModelForm)` **first** to emit the targeted message —
  otherwise a `ModelForm` would silently write with no object slot / no
  `DjangoModelPermission` default / no optimizer re-fetch
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)).
- **A required extra (non-model) `ModelForm` field on `update` (P2).** It has no
  instance value to reconstruct, so it keeps its `field.required` in the partial
  input (the caller must supply it); an optional extra field may be omitted
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)).
- **A relation field with `to_field_name` (P2).** A `ModelChoiceField` /
  `ModelMultipleChoiceField` whose `to_field_name` (or backing `ForeignKey(to_field=…)`)
  looks the object up by a non-pk field: after the visibility query resolves the
  object, the decoder feeds the form `obj.serializable_value(field.to_field_name)`
  (else `obj.pk`), so a valid GraphQL id does not fail form validation
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- **A form whose `__init__` requires constructor kwargs (P2).** Schema-time discovery
  reads `form_class.base_fields` (no instantiation), and runtime construction goes
  through `get_form_kwargs(info, *, data, files, instance=None)` — the consumer
  overrides it to inject `user` / `request` / tenant or to scope a
  `ModelChoiceField.queryset` without changing the generated input shape
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)).
- **A `create` narrowing that drops a required form field (P2).** Rejected at class
  creation with a [`ConfigurationError`][glossary-configurationerror] naming the
  missing required field(s) — a bound form cannot succeed without it and `initial` is
  no substitute; waived only when `get_form_kwargs` / `get_form` is overridden to
  supply it ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- **Write-time `IntegrityError` (P1).** A valid `form.save()` (or the plain-form
  `perform_mutate` save) that loses a concurrent-uniqueness race or hits a residual DB
  constraint returns the null-object + `FieldError` envelope via the `036`
  `_save_or_field_errors` mapper — never a top-level `GraphQLError`
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)).
- **Two distinct generated form inputs colliding on one GraphQL name (P1).** Two
  **different** form classes with the same `__name__` both emit `<__name__>Input` and
  **always** raise a finalize-time [`ConfigurationError`][glossary-configurationerror]
  (distinct `form_class` identities never dedupe — the reused
  `materialize_generated_input_class` ledger raise); only repeats of the **same**
  `(form_class, operation kind, effective set)` dedupe to one materialized class, and
  two different narrowings of one form get distinct shape-derived names
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- **Plain-form write authorization.** With no model, the
  [`DjangoModelPermission`][glossary-djangomodelpermission] default cannot apply; a
  plain `DjangoFormMutation` requires an explicit `Meta.permission_classes`
  ([Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form)).
- **No `DjangoType` `Meta` key added.** [`DEFERRED_META_KEYS`][types-base] /
  `ALLOWED_META_KEYS` are byte-unchanged
  ([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).

## Test plan

Test placement follows the [`AGENTS.md`][agents] mirror rule; the live surface owns
behavior reachable through `/graphql/`, package tests own internals.

- **Live, over `/graphql/`** (Slice 4, [`test_products_api.py`][test-products-api],
  seeded via `seed_data` / `create_users`): `createItemViaForm` / `updateItemViaForm`
  happy paths; the `form.errors` envelope (a `clean_<field>` error keyed to the form
  field, the `unique_item_per_category` `clean()` error keyed to `"__all__"`);
  **`categoryId` validates and writes through the `ModelForm`'s `category` field**
  (not via model `setattr` — proving the P1 reverse map); **partial-update
  preservation** — a `name`-only `updateItemViaForm` preserves `description` and
  `category` (FK), and `unique_item_per_category` still fires when only `name` changes
  to a value already taken under the unchanged `category` (the P1 partial-update
  contract); a non-colliding partial update; write authorization (anonymous denied, a
  caller missing the model perm denied, a permitted caller succeeds); the
  visibility-scoped `update` (a caller who cannot see a private `Item` gets
  not-found); **relation visibility** — a permitted writer submitting a **hidden**
  `Category` `GlobalID` as `categoryId` gets the same field-keyed `FieldError` the
  model-driven mutation returns (the restored P1 `036` invariant, proving the form's
  default `Category.objects.all()` queryset is not the only guard); **a raw
  `django.test.Client` multipart upload** to a form-backed `Upload` field, proving the
  `data=` / `files=` split validates and writes the file (the P1 file-routing contract
  — owned here, not deferred); **a `get_form_kwargs` override injecting `user`** drives
  a form whose `__init__` requires it (the P2 construction-hook migration case); and
  the plain `Form` mutation's **success** (`ok: true`, empty `errors`) **and**
  validation-failure (`ok: false`, field-keyed `errors`) shapes. **Write-time
  `IntegrityError`** — a valid `ModelForm.save()` that loses a concurrent-uniqueness
  race surfaces the **`FieldError` envelope**, not a top-level GraphQL error (P1).
- **Package-internal** ([`tests/forms/`][test-forms]):
  - `test_converter.py` — each supported form-field class → annotation +
    required-ness; `ModelChoiceField` / `ModelMultipleChoiceField` id mapping
    (Relay-`GlobalID` vs raw pk); `forms.FileField` → [`Upload`][glossary-upload-scalar];
    **the `input_attr → (form_field_name, kind)` reverse map** (`category_id` /
    `categoryId` → `category` / `relation_single`; a `file`-kind flag for an
    `Upload` field); field discovery from **`form_class.base_fields`** (a form whose
    `__init__` requires kwargs still yields a shape, P2); and **the fail-loud dispatch
    (P2): a bare `forms.Field` → `str`, a known subclass (`EmailField`) maps, but a
    custom `class CustomField(forms.Field)` raises [`ConfigurationError`][glossary-configurationerror]**
    (the catch-all-shadowing regression test).
  - `test_inputs.py` — the **two generated inputs** (`<FormClass>Input` with
    `field.required` requiredness for create; `<FormClass>PartialInput` — model-backed
    fields optional, **a required non-model extra field still required**, P2); fields
    from `form_class.base_fields` (no instantiation; an overridable `get_form_fields()`
    honored, P2), narrowed by `Meta.fields` / `Meta.exclude`; materialization as
    a module global; a form-only (non-model) field included. **Shape identity (P1):**
    the same form with two different `Meta.fields` narrowings → two **distinct**
    generated names; two repeats of the **same** `(form_class, op, effective set)` →
    **dedupe** (one materialized class); two **different** form classes with the
    **same `__name__`** → a finalize-time [`ConfigurationError`][glossary-configurationerror]
    collision **always** (distinct `form_class` identities never dedupe, even with
    matching field shapes); an **empty effective field set** → `ConfigurationError`.
  - `test_sets.py` — the `Meta` validation matrix (missing `form_class`; a `ModelForm`
    on **`DjangoFormMutation`** rejected naming `DjangoModelFormMutation`, P2; a
    non-`ModelForm` on `DjangoModelFormMutation` rejected; `ModelForm`-with-no-model;
    `DjangoModelFormMutation` `operation = "delete"` rejected; **any `Meta.operation`
    on the plain base rejected** (P2); **a `create` narrowing (`Meta.fields` *or*
    `Meta.exclude`) that drops a required form field → `ConfigurationError` naming the
    missing field(s), waived when `get_form_kwargs` is overridden** (P2);
    **`Meta.fields` bare-string / duplicate-name / unknown-name against
    `form.base_fields`**, P3; `fields` + `exclude` both set; unknown key); **plain-form
    input dedupe via the `"form"` sentinel**; registration; phase-2.5 binding (both
    paths); the no-registered-primary-type error for `DjangoModelFormMutation`.
  - `test_resolvers.py` — create / update happy paths; `form.is_valid()` failure →
    envelope (null object), incl. a `NON_FIELD_ERRORS` `clean()` error → `"__all__"`;
    **the decode split** — `categoryId` → `{"category": pk}` in `data=`, an `Upload`
    → `files=` (never `data=`); **relation visibility on EVERY branch** — a hidden
    target → field-keyed `FieldError` before the form, for **both** a Relay-`GlobalID`
    primary AND a **non-Relay raw-pk** primary, and for **both** `ModelChoiceField` and
    `ModelMultipleChoiceField` (P1, the raw-pk gap the `036` helper left); **a raw-pk /
    wrong-model relation id** → `FieldError`; **`to_field_name`** — a `ModelChoiceField`
    / `ModelMultipleChoiceField` with `to_field_name` set validates the decoded value
    by the target field, not pk (P2, #6); **write-time `IntegrityError`** — a valid
    `form.save()` raising `IntegrityError` (and the plain-form `perform_mutate` save
    path) → `FieldError` envelope, not a top-level error (P1, via `_save_or_field_errors`);
    **the `get_form_kwargs` / `get_form` hook** — an override injecting `user` and one
    scoping a `ModelChoiceField.queryset` (input shape unchanged), P2; **partial-update
    reconstruction at the unit tier** — omitted scalar / FK / M2M preserved from the
    located instance, omitted file preserved via the bound form's `initial`, a
    **required extra non-model field omitted → required error** while an optional one
    may be omitted (P2), and `unique_item_per_category` validating on a one-field
    change; the **plain-form `ok` + `errors` payload** and the `perform_mutate(self,
    form, info)` default (calls `form.save()` if present, else no-op) + a consumer
    override; the visibility-scoped `update` locate (hidden row → not-found); write-auth
    denial vs success; sync + async (the async path runs the body in one
    `sync_to_async(thread_sensitive=True)` call); the
    [`SyncMisuseError`][glossary-syncmisuseerror] async-hook-from-sync path; the G2
    re-fetch plan-shape (`select_related` / `prefetch_related` kept, no `.only(...)`).
  - [`tests/mutations/test_fields.py`][test-mutations] (extend) — the generalized
    [`DjangoMutationField`][glossary-djangomutationfield] target check accepts a
    `DjangoModelFormMutation` and (per the
    [Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)
    resolution) the plain-form flavor.
- **Cross-cutting — no regression.** The full suite is green at the 100% coverage
  gate (`fail_under = 100`); `ruff format` + `ruff check` are clean; the `036`
  model-driven mutation surface and the read side are unchanged.

## Doc updates

Each slice owns its doc edits. [`AGENTS.md`][agents] #"Do not update CHANGELOG.md
unless explicitly instructed" requires `CHANGELOG.md` edits to be explicitly
instructed — and a standing design doc cannot itself grant that permission. This
spec only *describes* the release-note work; the **Slice 5 maintainer prompt must
explicitly include the `CHANGELOG.md` edit** for it to be authorized.

- **Slice 5 — version cut**
  ([Decision 14](#decision-14--this-card-owns-the-0012-version-bump)): align
  [`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init],
  [`tests/base/test_init.py::test_version`][test-base-init], the
  [`docs/GLOSSARY.md`][glossary] package-version line, and `uv.lock` (if applicable)
  on `0.0.12`.
- **Slice 5 — GLOSSARY** ([`docs/GLOSSARY.md`][glossary]): promote
  [`DjangoFormMutation`][glossary-djangoformmutation] /
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation] from
  `planned for 0.0.12` to `shipped (0.0.12)` (updating each body to the shipped
  contract — the `Meta.form_class` surface, the form-derived input, the `form.errors`
  → [`FieldError`][glossary-fielderror-envelope] mapping, the `036` reuse). **Correct
  the now-stale `DjangoFormMutation` entry (P2):** its current text calls the plain
  `DjangoFormMutation` a "`DjangoMutation` subclass" with "the post-save object as the
  return value" — rewrite it to the settled architecture
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)):
  only `DjangoModelFormMutation` subclasses `DjangoMutation` (returns the post-save
  object in the uniform `node` / `result` slot), while the plain `DjangoFormMutation`
  is a model-less sibling accepted by the generalized mutation-field family, returning
  the pinned `ok: Boolean!` + `errors: [FieldError!]!` payload (no object slot). Add
  both symbols to **Public exports**, the **Index** (status column), and the
  **Mutations** browse-by-category row; move the package-version line to `0.0.12`.
- **Slice 5 — package docs**: [`docs/README.md`][docs-readme] / [`README.md`][readme]
  move form mutations from "Coming next (`0.0.12`)" to "Shipped today" and the
  README **Status** line from `0.0.11` to `0.0.12`; [`GOAL.md`][goal] — criterion
  6's `ModelForm` flavor now ships (the `ModelSerializer` flavor stays `0.0.13`);
  [`TODAY.md`][today] notes form mutations as a package capability and the products
  `ModelForm` write surface; [`docs/TREE.md`][tree] fills the planned `forms/` /
  [`tests/forms/`][test-forms] summary lines; [`CHANGELOG.md`][changelog] carries the
  `[Unreleased]` → `0.0.12` bullets **only when the Slice 5 maintainer prompt
  explicitly requests it** (this repo's [`CHANGELOG.md`][changelog] cuts a dated
  `## [0.0.X] - DATE` block per release rather than maintaining a standing
  `[Unreleased]` section, so mechanically the entry is a fresh dated `0.0.12` block
  matching the `[0.0.11]` template; "`[Unreleased]` → `0.0.12`" names the conceptual move).
- **Slice 5 — card wrap**: [`KANBAN.md`][kanban] moves
  [`TODO-ALPHA-038-0.0.12`][kanban] to Done with the next `DONE-NNN-0.0.12` id,
  keeping its `SpecDoc` pointing at the canonical card spec (a `SpecDoc` DB edit
  re-rendered via `scripts/build_kanban_md.py`, never a hand-edit).

## Risks and open questions

Each item names a preferred answer for the `0.0.12` cut and a fallback if
implementation reveals it is wrong.

- **The plain-`Form` payload shape (model-less) — RESOLVED, no longer open (P2).**
  Pinned in [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)
  as the fixed two-field shape `ok: Boolean!` + `errors: [FieldError!]!` with the
  `perform_mutate(self, form, info) -> None` hook (default `form.save()`-if-present
  else no-op). Cleaned-data echo (graphene parity) was considered and rejected for
  `0.0.12` (heterogeneous `cleaned_data` has no clean GraphQL output mapping; the
  plain form is a parity-completeness flavor; a data-returning consumer uses a
  `DjangoModelFormMutation`). There is no remaining preferred/fallback ambiguity — an
  implementer cannot ship a divergent plain-form shape.
- **`ModelForm` partial-update semantics — RESOLVED (P1).** Pinned in
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload):
  `update` reconstructs the full bound payload from the located instance overlaid with
  the provided fields (`data = {**model_to_dict(instance, non-file fields),
  **provided_data}`, `files = provided_files`), so a bound `ModelForm` validates the
  whole set while omitted fields are preserved — the `036` `PartialInput` contract,
  not graphene-django's full update. The alternative (graphene-style full update,
  dropping `PartialInput` and requiring all form-required fields) was rejected for
  cross-flavor consistency with the model-driven `DjangoMutation.update`. Fallback if
  the reconstruction proves leaky for an exotic form (custom non-model fields with
  required-on-partial semantics): narrow to graphene-style full update for that form
  via an opt-in, never silently — but the package default is partial.
- **Form-input shape identity + collision — RESOLVED (P1).** Pinned in
  [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)
  as the `036`-parallel identity `(form_class, operation kind, frozenset(effective
  field names))` with canonical / shape-derived names, dedupe, and a finalize-time
  [`ConfigurationError`][glossary-configurationerror] for two distinct shapes on one
  generated name (same form / different narrowings, and different forms / same
  `__name__`). No remaining ambiguity — an implementer cannot silently reuse the wrong
  input class or hit a late Strawberry name clash.
- **Relation-id visibility in the form decode — RESOLVED (P1, a restored `036`
  invariant).** Pinned in
  [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)
  / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload):
  the `relation_single` / `relation_multi` decode type- and visibility-checks the id
  through the related primary `DjangoType.get_queryset` **before** the form, so the
  form's non-request-scoped default queryset is not the only guard — a hidden target
  is the same field-keyed `FieldError` as the model-mutation path. (Earlier revisions
  delegated this to `ModelChoiceField.to_python`, which dropped the invariant; fixed.)
- **Form `Meta` / base validation hardening — RESOLVED (P2 / P3).** Pinned: a
  `ModelForm` on the plain `DjangoFormMutation` base is rejected at class creation
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)),
  a required non-model extra field stays required on `update`
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)),
  and `Meta.fields` / `Meta.exclude` are normalized + fail-loud against `form_class.base_fields`
  (bare string / duplicate / unknown name / empty set →
  [`ConfigurationError`][glossary-configurationerror],
  [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)),
  mirroring the `036` model-mutation validators.
- **Raw-pk relation visibility — RESOLVED (P1, security).** The `036`
  `_decode_relation_id_set` passes a raw pk through with **no** visibility hook (only
  the Relay-`GlobalID` branch is scoped), so it is **not** reused unchanged; a
  dedicated form relation decoder
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)
  / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload))
  resolves every branch (Relay + raw pk, single + multi) through the related primary
  `get_queryset` before the form, closing the non-Relay hole.
- **Write-time `IntegrityError` — RESOLVED (P1).** The form write reuses the `036`
  `_save_or_field_errors` mapper, so a post-validation concurrent-race / residual
  constraint at `form.save()` (or the plain-form save) returns the `FieldError`
  envelope, not a top-level error
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)).
- **Form-construction hooks — RESOLVED (P2).** Schema-time discovery reads
  `form_class.base_fields` (no instantiation; overridable `get_form_fields()`), and
  runtime construction goes through `get_form_kwargs(info, *, data, files,
  instance=None)` / `get_form(...)` (the graphene-django parity seam) so a
  kwarg-requiring or queryset-scoping migrated form works
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)
  / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)).
- **`to_field_name`, plain-form `operation`, create-narrowing, converter dispatch,
  file-clear — RESOLVED (P2 / P3).** `to_field_name` honored in the relation decoder
  (#6); plain `DjangoFormMutation` rejects any `Meta.operation` and uses the `"form"`
  shape sentinel (#4); a `create` narrowing dropping a required field raises (#7,
  waived under a `get_form_kwargs` override); the converter's fallthrough raises with
  no base-`forms.Field` catch-all (#5); file **clearing** is explicitly out of scope
  for `0.0.12` (upload + preserve only, #8).
- **Generalizing the field factory (dispatch + ref + target check).** Preferred
  answer ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)):
  generalize [`DjangoMutationField`][glossary-djangomutationfield] along all three
  hardwired-to-model axes — the target check (accept the mutation/form family), the
  `_resolve` dispatch (call `mutation_cls.resolve_sync` / `resolve_async` so a form
  flavor routes to [`forms/resolvers.py`][forms-resolvers]), and the `data:` lazy-ref
  derivation (consult `mutation_cls.input_type_name` + `input_module_path`) — each
  defaulting to today's model behavior, so one factory exposes every flavor with no
  model-flavor regression. Fallback: a thin net-new `DjangoFormMutationField` (its own
  dispatch + ref) for the form flavors only, if generalizing the shipped factory's
  dispatch proves invasive — but the seam approach is preferred because the `0.0.13`
  [`SerializerMutation`][glossary-serializermutation] flavor needs the same three
  generalizations.
- **Plain-form write-authorization default.** Preferred answer
  ([Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form)):
  the plain form keeps the safe-by-default posture — an unset `permission_classes`
  denies (no model-permission default exists without a model), so a public plain-form
  write is an explicit `Meta.permission_classes = []` opt-in. Fallback: ship a
  permissive `AllowAny`-style built-in the plain form defaults to, if deny-by-default
  proves too strict for the common "public contact form" case — never weaken the
  `ModelForm` default.
- **Card conflict — `Meta.return_field_name`.** The card lists
  `Meta.return_field_name` as part of the DRF-style surface, but [`spec-036`][spec-036]
  Decision 7 (AR-H5) **froze** the uniform `node` / `result` payload slot to keep one
  cross-flavor client contract. Preferred reading: honor the frozen `036` slot and
  do **not** adopt `Meta.return_field_name` (the card's own dependency, the
  [`FieldError` envelope][glossary-fielderror-envelope] reuse, implies the frozen
  payload shape). Recorded per the [`docs/SPECS/NEXT.md`][next] "prefer the card,
  surface the conflict" rule; the fallback is to support `return_field_name` as an
  optional override aliasing the uniform slot if a consumer needs the graphene-django
  field name verbatim for migration.
- **Card-citation note — the spec filename vs the card's `docs/spec-form_mutations.md`.**
  The card DoD names `docs/spec-form_mutations.md`; the structured convention
  authors at `docs/SPECS/spec-038-form_mutations-0_0_12.md`
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)). Recorded, not
  silently reconciled, per the [`docs/SPECS/NEXT.md`][next] boundary rule.
- **`form.save(commit=False)` vs `form.save()` for relation timing.** Preferred
  answer ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)):
  the `ModelForm` flavor calls `form.save()` (commit=True) directly — for a `ModelForm`
  with M2M fields this already runs `save_m2m()` **internally**, so a single
  `form.save()` inside the one `transaction.atomic()` is correct and complete (no
  separate M2M step). Fallback: switch to `commit=False` + explicit `instance.save()`
  + `form.save_m2m()` (still inside the transaction) only if a consumer needs the saved
  instance *before* its M2M rows are written (e.g. a `clean()` that inspects the pk) —
  a contained resolver change, not a contract change.

## Out of scope (explicitly tracked elsewhere)

- **DRF serializer mutations** ([`SerializerMutation`][glossary-serializermutation])
  — `0.0.13` ([`TODO-ALPHA-039-0.0.13`][kanban]); reuses the same
  [`FieldError` envelope][glossary-fielderror-envelope] and a serializer-field
  converter, not this card's form converter.
- **Auth mutations** ([Auth mutations][glossary-auth-mutations]) — `0.0.13`
  ([`TODO-ALPHA-040-0.0.13`][kanban]).
- **The ergonomic `TestClient` / `AsyncTestClient` helper** —
  [`TestClient`][glossary-testclient] (`TODO-ALPHA-043-0.0.14`). **File-field
  correctness is NOT deferred:** this card owns the `forms.FileField` /
  `forms.ImageField` → [`Upload`][glossary-upload-scalar] typing **and** the runtime
  `data=` / `files=` decode split + `form_class(data=, files=, instance=)`
  construction, proven by a raw `django.test.Client` multipart live test (Slice 4,
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)).
  Only the *ergonomic* multipart test-client wrapper lands with the `0.0.14` helper.
- **Form `delete`** — not shipped; the model-driven
  [`DjangoMutation`][glossary-djangomutation] (`Meta.operation = "delete"`) covers
  deletion ([Decision 10](#decision-10--operations-create--update-for-the-modelform-no-form-delete)).
- **Field-level read gates** ([`FieldSet`][glossary-fieldset] /
  [Per-field permission hooks][glossary-per-field-permission-hooks]) — `0.1.1`,
  composing on top of (not replacing) write authorization.
- **Clearing a stored file/image on update** (the `ClearableFileInput` false-sentinel
  "clear" semantics) — a future `<field>Clear: Boolean` input routed through the
  widget clear path; `0.0.12` supports only upload + preserve
  ([Edge cases](#edge-cases-and-constraints)).
- **A new `DjangoType` `Meta` key or settings key**
  ([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).

## Definition of done

The completion contract the card is built against. Items map onto the card's own DoD
bullets: item 1 (spec), 2 (the `forms/` subpackage on the DRF Meta surface), 3 (the
form-field converter reusing the scalar registry), 4 (the `FieldError` envelope from
`form.errors`), 5 (package tests), 6 (live HTTP for both `Form` and `ModelForm`) —
plus the exports / version-cut the [`docs/SPECS/NEXT.md`][next] flow adds.

**Spec + companion CSV**

1. `docs/SPECS/spec-038-form_mutations-0_0_12.md` (the canonical card spec) and its
   companion `spec-038-form_mutations-0_0_12-terms.csv` exist;
   `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-038-form_mutations-0_0_12.md`
   reports `OK: <N> terms`.

**Slice 1 — form-field converter + form-derived input**

2. [`forms/converter.py`][forms-converter] ships `convert_form_field` (every
   supported form-field class → its Strawberry annotation + required-ness, reusing
   the read-side [scalar][glossary-scalar-field-conversion] /
   [choice-enum][glossary-choice-enum-generation] /
   [`Upload`][glossary-upload-scalar] converters where overlapping) with a **fail-loud
   dispatch — no base-`forms.Field` catch-all**: a bare `forms.Field` → `str` (exact
   special case), a known subclass maps via MRO, but a custom `forms.Field` subclass
   hits the **raising** default → [`ConfigurationError`][glossary-configurationerror]
   (P2); **and the `input_attr → (form_field_name, kind)` reverse map** (`category_id`
   / `categoryId` → `category` / `relation_single`; an `Upload` field flagged `file`).
   [`forms/inputs.py`][forms-inputs] builds **both** the form-derived `<FormClass>Input`
   (create, `field.required` requiredness) and `<FormClass>PartialInput` (update;
   model-backed fields optional, **a required non-model extra field still required**)
   from **`form_class.base_fields`** (no instantiation — kwarg-requiring forms work;
   overridable `get_form_fields()`, P2), under the `036`-parallel **shape identity**
   `(form_class, operation kind, effective field set)` — the operation component is the
   `DjangoModelFormMutation` verb or the plain `"form"` sentinel — with canonical /
   shape-derived names, dedupe, and a finalize-time **collision
   [`ConfigurationError`][glossary-configurationerror]** for two distinct shapes on one
   name (incl. different forms sharing a `__name__`, which always collide);
   `Meta.fields` / `Meta.exclude` are normalized + fail-loud against
   `form_class.base_fields` (bare string / duplicate / unknown name / empty set →
   `ConfigurationError`), and a **`create` narrowing that drops a required form field
   raises** unless `get_form_kwargs` is overridden (P2); all materialized as module
   globals ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).

**Slice 2 — the two base classes**

3. [`mutations/sets.py`][mutations-sets] refactors the class-creation validation
   into the overridable `DjangoMutation._validate_meta(meta)` and adds the
   `build_input` / `input_type_name` / `input_module_path` / `resolve_sync` /
   `resolve_async` seams (each model-defaulted, no model-flavor regression);
   [`forms/sets.py`][forms-sets] ships `DjangoModelFormMutation` (subclasses
   [`DjangoMutation`][glossary-djangomutation], overriding
   [`_resolve_model`][spec-036] → `Meta.form_class._meta.model` plus those seams) and
   `DjangoFormMutation` (the model-less sibling — its own metaclass + declaration
   registry + `bind_form_mutations()` wired into [`types/finalizer.py`][types-finalizer]'s
   phase-2.5 window, with a `registry.clear()` co-clear). The form-flavor
   `_validate_meta` override enforces the matrix (missing `form_class`; **a
   `ModelForm` on the plain `DjangoFormMutation` base rejected naming
   `DjangoModelFormMutation`**, and a non-`ModelForm` on `DjangoModelFormMutation`
   rejected — validated **before** `_resolve_model`; `ModelForm`-with-no-model;
   **`operation` split by base** — `DjangoModelFormMutation` validates `∈ {"create",
   "update"}` (reject `"delete"`), plain `DjangoFormMutation` **rejects any
   `Meta.operation`** and uses the `"form"` shape sentinel (P2); `form_class` a known
   key; mutually exclusive / normalized / fail-loud `fields` / `exclude`;
   unknown key → [`ConfigurationError`][glossary-configurationerror]); the model
   flavor's seam
   defaults are unchanged (a `DjangoMutation` still validates + binds its model-column
   input exactly as `036` shipped); [`DEFERRED_META_KEYS`][types-base] /
   `ALLOWED_META_KEYS` are unchanged; both symbols export from [`__init__.py`][init]
   ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)
   / [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)
   / [Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).

**Slice 3 — resolver pipeline + field exposure**

4. [`forms/resolvers.py`][forms-resolvers] runs the decode → locate → authorize →
   `is_valid()` → write → re-fetch → payload pipeline (sync + async, one
   `transaction.atomic()` / one `sync_to_async(thread_sensitive=True)`). Decode
   produces a **form-field-keyed** `provided_data` via the **dedicated form relation
   decoder** (NOT `036`'s `_decode_relation_id_set`): every relation id — `GlobalID`
   *or* **raw pk** — is type-checked, resolved to the **visible** object through the
   related primary `DjangoType.get_queryset` (closing the raw-pk visibility gap, P1),
   and converted by `to_field_name` (`obj.serializable_value(field.to_field_name)` else
   `obj.pk`, P2) before landing under the form field name; a hidden target → field-keyed
   `FieldError` + a **separate `provided_files`** (uploaded `Upload` values, never in
   `data=`); construction goes through the overridable `get_form_kwargs(info, *, data,
   files, instance=None)` hook (P2) — `create` builds `form_class(**get_form_kwargs(…,
   data=provided_data, files=provided_files))`, `update` reconstructs the **full partial
   payload** (`data = {**model_to_dict(instance, non-file fields), **provided_data}`,
   `files = provided_files`) then `form_class(**get_form_kwargs(…, instance=<located
   row>))` — so omitted scalar / FK / M2M / file values are preserved and
   `unique_item_per_category` validates on a one-field change (P1). `form.errors` maps
   onto the [`FieldError` envelope][glossary-fielderror-envelope] (`NON_FIELD_ERRORS` →
   `"__all__"`, via the reused `_validation_error_to_field_errors(ValidationError(
   form.errors.as_data()))`); **the write is wrapped by the `036` `_save_or_field_errors`
   `IntegrityError` → envelope mapper** (no top-level error on a save-time race, P1);
   the `ModelForm` payload object is re-fetched through the
   `036` optimizer path (G2: `select_related` / `prefetch_related` kept, no
   [`.only(...)`][glossary-only-projection]); the **plain `DjangoFormMutation`
   returns the pinned `ok: Boolean!` + `errors: [FieldError!]!` payload** with
   `perform_mutate(self, form, info)` (default `form.save()`-if-present else no-op);
   [`mutations/fields.py`][mutations-fields]'s
   [`DjangoMutationField`][glossary-djangomutationfield] is generalized along all
   three model-hardwired axes (target check, `_resolve` dispatch →
   `mutation_cls.resolve_sync` / `resolve_async`, and the `data:` lazy-ref →
   `mutation_cls.input_type_name` + `input_module_path`) so it exposes both flavors
   **and** the form pipeline actually fires, with the model-flavor path unchanged
   ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)
   / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)
   / [Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path)).

**Slice 4 — products live form surface**

5. Products exposes a `DjangoModelFormMutation` (create + update over `Item`) and a
   plain `DjangoFormMutation`, and [`test_products_api.py`][test-products-api]
   (seeded via `seed_data` / `create_users`) proves the create / update happy paths,
   `categoryId` validating through the form's `category` field, **a hidden-`Category`
   `GlobalID` → field-keyed `FieldError`** (the restored relation-visibility
   invariant), **partial-update preservation** (a `name`-only update preserves
   `category` / `description`, and `unique_item_per_category` fires on a one-field
   change), the `form.errors` envelope (field-level + the `unique_item_per_category`
   `"__all__"` case), write authorization, the visibility-scoped `update`, **a raw
   `django.test.Client` multipart upload to a form-backed `Upload` field** (the P1
   file-routing contract, owned here), **a write-time `IntegrityError` returning the
   `FieldError` envelope** (P1), **a `get_form_kwargs` override injecting `user`** for a
   kwarg-requiring form (P2), and the plain `Form` mutation's **success** (`ok: true`)
   **and** validation-failure shapes
   ([Decision 12](#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation)).

**Cross-cutting — no regression**

6. The full suite is green at the 100% coverage gate (`fail_under = 100`);
   `ruff format` + `ruff check` are clean; the `036` model-driven mutation surface
   and the read side are unchanged.

**Slice 5 — docs + the `0.0.12` cut + card wrap**

7. [`docs/GLOSSARY.md`][glossary] promotes
   [`DjangoFormMutation`][glossary-djangoformmutation] /
   [`DjangoModelFormMutation`][glossary-djangomodelformmutation] to
   `shipped (0.0.12)` (with Public-exports + Index + Mutations-category rows) and
   moves the package-version line to `0.0.12`; [`docs/README.md`][docs-readme] /
   [`README.md`][readme] move form mutations to "Shipped today" and the Status to
   `0.0.12`; [`GOAL.md`][goal] / [`TODAY.md`][today] / [`docs/TREE.md`][tree] reflect
   the shipped flavor; [`CHANGELOG.md`][changelog] carries the bullets **only when
   the Slice 5 maintainer prompt explicitly requests the edit**; [`KANBAN.md`][kanban]
   records the card `DONE-NNN-0.0.12` with the `SpecDoc` reference at the canonical
   card spec (kanban DB + re-render).
8. **The `0.0.12` version bump lands in this card**
   ([Decision 14](#decision-14--this-card-owns-the-0012-version-bump)):
   [`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init],
   [`tests/base/test_init.py::test_version`][test-base-init], the
   [`docs/GLOSSARY.md`][glossary] package-version line, and `uv.lock` (if
   applicable) align on `0.0.12`. The two net-new public symbols
   (`DjangoFormMutation`, `DjangoModelFormMutation`) are added to `__all__` and the
   export pin updated accordingly.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
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
[glossary-choice-enum-generation]: ../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-cross-subsystem-invariants]: ../GLOSSARY.md#cross-subsystem-invariants
[glossary-djangoformmutation]: ../GLOSSARY.md#djangoformmutation
[glossary-djangomodelformmutation]: ../GLOSSARY.md#djangomodelformmutation
[glossary-djangomodelpermission]: ../GLOSSARY.md#djangomodelpermission
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: ../GLOSSARY.md#djangomutationfield
[glossary-djangonodefield]: ../GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-fielderror-envelope]: ../GLOSSARY.md#fielderror-envelope
[glossary-fieldset]: ../GLOSSARY.md#fieldset
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-finalize_django_types]: ../GLOSSARY.md#finalize_django_types
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-input-type-generation]: ../GLOSSARY.md#input-type-generation
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-orderset]: ../GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: ../GLOSSARY.md#per-field-permission-hooks
[glossary-scalar-field-conversion]: ../GLOSSARY.md#scalar-field-conversion
[glossary-serializermutation]: ../GLOSSARY.md#serializermutation
[glossary-syncmisuseerror]: ../GLOSSARY.md#syncmisuseerror
[glossary-testclient]: ../GLOSSARY.md#testclient
[glossary-upload-scalar]: ../GLOSSARY.md#upload-scalar
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[next]: NEXT.md
[spec-010]: spec-010-foundation-0_0_4.md
[spec-027]: spec-027-filters-0_0_8.md
[spec-028]: spec-028-orders-0_0_8.md
[spec-034]: spec-034-permissions-0_0_10.md
[spec-035]: spec-035-optimizer_hardening-0_0_10.md
[spec-036]: spec-036-mutations-0_0_11.md
[spec-037]: spec-037-upload_file_image_mapping-0_0_11.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[init]: ../../django_strawberry_framework/__init__.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[relay]: ../../django_strawberry_framework/relay.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-forms]: ../../tests/forms/
[test-mutations]: ../../tests/mutations/

<!-- examples/ -->
[products-forms]: ../../examples/fakeshop/apps/products/forms.py
[products-schema]: ../../examples/fakeshop/apps/products/schema.py
[test-products-api]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->
[upstream-forms-converter]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/converter.py
[upstream-forms-mutation]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/mutation.py
[upstream-forms-types]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/types.py

<!-- External -->
