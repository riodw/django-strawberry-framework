# Spec: Form-based mutations — `DjangoFormMutation` / `DjangoModelFormMutation` on the DRF-shaped `class Meta` surface, reusing the shared `FieldError` envelope and the `DjangoMutation` foundation

Shipped in `0.0.12` (card [`DONE-038-0.0.12`][kanban]). This card adds the
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
[`spec-036`][spec-036] built. The flavor reuses, **unchanged**, the contracts
[`spec-036`][spec-036] **defined for exactly this**: the shared
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

Status: **SHIPPED (`0.0.12`)** — card [`DONE-038-0.0.12`][kanban], released
under the [`CHANGELOG.md`][changelog] `## [0.0.12]` heading; authored via the
[`docs/SPECS/NEXT.md`][next] flow, **all five slices final-accepted** (the form
converter + form-derived inputs; the two bases + `Meta` validation + the phase-2.5
bind; the resolver pipeline + `DjangoMutationField` exposure; the products live form
surface; docs + the `0.0.12` version cut + card wrap). The
[Slice checklist](#slice-checklist) below stays unticked because the `Status:` line
is the completion source of truth (the shipped-spec convention).
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
[Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
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
**defined** the [`FieldError` envelope][glossary-fielderror-envelope], the
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

This spec's deliberative layer — the authoring revision history that produced
the contract, every Decision's justification, every alternative each Decision
rejected, and the risk / open-question deliberation that settled the card's
design questions — lives in the rationale companion
[`docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md`][spec-038-rationale].

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the
vocabulary used throughout the spec:

- [`DjangoFormMutation`][glossary-djangoformmutation] /
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation] — the two subjects.
  Both consume a Django `Form` / `ModelForm` (`Meta.form_class`) and surface
  validation through the shared [`FieldError` envelope][glossary-fielderror-envelope]
  (populated from `form.errors`). **The one point the entries must not blur:**
  **only `DjangoModelFormMutation` subclasses [`DjangoMutation`][glossary-djangomutation]**
  (it has a model, so it returns the post-save object in the uniform `node` / `result`
  slot), while the **plain `DjangoFormMutation` is a model-less sibling** — its own
  metaclass, no `DjangoType` object slot, the pinned `ok` + `errors` payload of
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)) —
  accepted by the **generalized mutation-field family**
  ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)).
  Both entries carry `shipped (0.0.12)` and the sibling shape
  (see [Doc updates](#doc-updates)).
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
  [`spec-036`][spec-036] **defined** for this card. A form mutation maps
  `form.errors` (a `field → [messages]` dict, with the form's `NON_FIELD_ERRORS`
  bucket) onto that same envelope, keying form-level errors to the same
  `"__all__"` sentinel `036` pinned
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
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
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
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
  [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" —
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
    `uuid.UUID`, `JSONField` → `strawberry.scalars.JSON` (its own row, or the
    `CharField` parent types a JSON payload as `String`),
    `ModelChoiceField` → the target's id, `ModelMultipleChoiceField` /
    `MultipleChoiceField` → `list[<id>]` / `list[str]`, `forms.FileField` /
    `forms.ImageField` → [`Upload`][glossary-upload-scalar]). **Fail-loud dispatch:** the fallthrough default **raises** — supported classes are registered
    individually (subclasses map via MRO), bare `forms.Field` is an explicit exact-type
    special case → `str`, and **no base-`forms.Field` catch-all** is registered (which
    would shadow the raise), so a custom `forms.Field` subclass with no supported
    ancestor raises [`ConfigurationError`][glossary-configurationerror] naming the field
    and class. Where a form field maps to a Django column type the read side already
    converts, reuse the [Scalar field conversion][glossary-scalar-field-conversion] /
    [Choice enum generation][glossary-choice-enum-generation] registry rather than
    re-deriving the scalar.
    Record, per generated input field, a
    [`utils/inputs.py`][utils-inputs]`::InputFieldSpec` — the one reverse-map record
    type every write flavor shares, whose `target_name` on this path is the form's
    declared field name — carrying `kind ∈ {scalar, relation_single, relation_multi,
    file}` and a relation's build-time `related_model`, so the resolver can build a
    form-field-keyed payload: `categoryId` / `category_id`
    → `category` / `relation_single`, an `Upload` field flagged `file`
    ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)). This module owns
    the four `kind` constants and re-exports them from
    [`utils/inputs.py`][utils-inputs]; it does not own the record type.
  - [ ] [`forms/inputs.py`][forms-inputs] (its own module, per the committed
    four-module `forms/` layout — [Decision 4](#decision-4--module-and-test-locations-forms-subpackage-mirroring-mutations)):
    build **two** `@strawberry.input` classes from the **form's declared fields**
    (`form_class.base_fields`, narrowed by `Meta.fields` / `Meta.exclude`) — `<FormClass>Input`
    (create; each field's requiredness from `field.required`, graphene-django parity)
    and `<FormClass>PartialInput` (update; model-backed fields optional, a **non-model
    extra field keeps its `field.required`**) — under the **shape-identity +
    naming + collision discipline** of `036` adapted to forms: identity `(form_class,
    operation kind, frozenset(effective field names), field-discovery hook
    discriminator)`, canonical `<FormClass>Input` /
    shape-derived narrowed names, identical shapes dedupe, two distinct shapes on one
    name → finalize-time [`ConfigurationError`][glossary-configurationerror].
    Reuse [`utils/inputs.py`][utils-inputs]'s `build_strawberry_input_class` +
    `materialize_generated_input_class` core (the latter's ledger gives the collision
    raise for free) and materialize as module globals of the `forms` input namespace
    for the [`strawberry.lazy`][glossary-djangomutationfield] forward-ref. Normalize +
    fail-loud `Meta.fields` / `Meta.exclude` against `form_class.base_fields` (bare string,
    duplicates, unknown names, empty effective set → `ConfigurationError`, mirroring
    `036`'s `_normalize_field_sequence`).
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
    defeating the two-base split). It then requires a `forms.Form` subclass.
    `DjangoModelFormMutation` requires a `forms.ModelForm` subclass. The check runs
    **before** `_resolve_model` (so a missing / wrong-type `form_class` is a clean
    [`ConfigurationError`][glossary-configurationerror], never a raw `AttributeError`
    from `form_class._meta.model`); a `ModelForm` with no resolvable `_meta.model`
    raises. **`operation` is split by base:** `DjangoModelFormMutation` requires
    `Meta.operation ∈ {"create", "update"}` (a `"delete"` form mutation is **rejected**
    — the form flavor has no delete pipeline,
    [Decision 10](#decision-10--operations-create--update-for-the-modelform-no-form-delete)),
    and its shape-identity operation component is that value; the plain
    `DjangoFormMutation` **rejects any `Meta.operation`** as unsupported (a model-less
    mutation has no model operation — Decision 10) and uses the fixed identity
    sentinel **`"form"`** for the operation component of its input-shape cache key,
    whose fourth component is the field-discovery hook discriminator
    ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
    There are **two** allowed-key sets, not one:
    `forms/sets.py::_ALLOWED_MODELFORM_META_KEYS` is
    `MODEL_BACKED_WRITE_META_KEYS | {form_class}` =
    `{fields, exclude, permission_classes, operation, select_for_update, form_class}`,
    and `forms/sets.py::_ALLOWED_PLAIN_FORM_META_KEYS` is
    `COMMON_WRITE_META_KEYS | {form_class}` =
    `{fields, exclude, permission_classes, form_class}`. Both add `form_class` and drop
    `model` / `input_class` / `partial_input_class`; the plain set additionally drops
    `operation` (Decision 10) **and** `select_for_update`, since row locking is a
    model-backed key a model-less mutation has nothing to lock with.
    `Meta.fields` / `Meta.exclude` are mutually exclusive.
  - [ ] No change to [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS`: a
    form-mutation `Meta` is its own validation namespace
    ([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).
  - [ ] Package coverage: [`tests/forms/test_sets.py`][test-forms] — the `Meta`
    validation matrix (missing / wrong-type `form_class`, a `ModelForm` on the plain
    base rejected naming `DjangoModelFormMutation`, `ModelForm`-with-no-model,
    `DjangoModelFormMutation` `operation = "delete"` rejected, **any `Meta.operation`
    on the plain base rejected**, `form_class` accepted as a known key,
    `fields` + `exclude` both set, unknown key), **plain-form input dedupe** (the
    `"form"` sentinel — two plain mutations over one form + effective set dedupe),
    registration, finalizer binding (both the `DjangoMutation`-path bind and the
    `bind_form_mutations()` path), the no-registered-primary-type error for
    `DjangoModelFormMutation`, and the
    model-flavor seam defaults unchanged (a `DjangoMutation` still validates +
    materializes its model-column input exactly as before).
- [ ] Slice 3: the form resolver pipeline + `DjangoMutationField` exposure (per
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
  /
  [Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path))
  - [ ] [`forms/resolvers.py`][forms-resolvers]: the sync + async pipeline, in the
    order **locate → authorize → decode → construct/validate → write → re-fetch →
    return** ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)) —
    (`update`) **locate** the row through the target type's
    [`get_queryset`][glossary-get_queryset-visibility-hook] (not-found → a `FieldError`
    on `id`, no existence leak); **authorize** via the inherited `check_permission` /
    `Meta.permission_classes`, **before** the decode, since the decode issues
    visibility-scoped queries an unauthorized caller must not be able to probe;
    **decode** the `data:` input via the reverse map into a form-field-keyed
    `provided_data` and a `provided_files` (files kept out of `data`), each relation id
    — `GlobalID` *or* **raw pk** — type-checked, resolved to the **visible** object
    through the related primary `DjangoType.get_queryset` (both branches, closing the
    raw-pk visibility gap) and converted by `to_field_name`
    (`obj.serializable_value(field.to_field_name)` else `obj.pk`) before landing
    under the form field name, a hidden target → field-keyed `FieldError`;
    **construct** the form once via the overridable
    `get_form_kwargs(info, *, data, files, instance=None)` hook — create:
    `form_class(**get_form_kwargs(info, data=provided_data, files=provided_files))`;
    **update (partial):** reconstruct the full bound `data` from the located row's
    values under the form's **full declared** field set, overlaid by `provided_data`,
    with `files = provided_files`, then
    `form_class(**get_form_kwargs(info, data=, files=, instance=<row>))` (omitted
    fields preserved); **validate** via `form.is_valid()` — a failure maps
    `form.errors` onto the [`FieldError` envelope][glossary-fielderror-envelope] (the
    form's `NON_FIELD_ERRORS` bucket → the `"__all__"` sentinel `036` defined, via the
    reused `validation_error_to_field_errors(ValidationError(form.errors.as_data()))`)
    and returns a null-object payload; **write** via `form.save()` (`ModelForm`) /
    `perform_mutate` (plain form), **wrapped by the `036` `save_or_field_errors`
    `IntegrityError` → envelope mapper** (no top-level error at write); **re-fetch**
    the saved object by pk + optimizer-plan (the `ModelForm` flavor); **return** the
    `<Name>Payload` (`node` / `result` for the `ModelForm`, the pinned `ok` + `errors`
    for the plain form). The whole pipeline runs inside one `transaction.atomic()`
    pinned to one write alias, behind a pre-transaction deadline check and over an
    immutable post-locate `authorized_pk` / `target_state` snapshot, and
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
    (the file-routing contract); and the plain `Form` mutation's **success**
    (`ok: true`) **and** validation-failure (`ok: false`, field-keyed `errors`) shapes.
- [ ] Slice 5: doc updates + the `0.0.12` version cut + card wrap (per
  [Doc updates](#doc-updates) /
  [Decision 14](#decision-14--this-card-owns-the-0012-version-bump))
  - [ ] **Version files to `0.0.12`**
    ([Decision 14](#decision-14--this-card-owns-the-0012-version-bump)): `__version__`
    in [`__init__.py`][init],
    [`tests/base/test_init.py::test_version`][test-base-init] and the
    [`docs/GLOSSARY.md`][glossary] package-version line — the three surfaces that
    carry the version, the release being single-sourced in `__version__`.
  - [ ] [`docs/GLOSSARY.md`][glossary] (promote
    [`DjangoFormMutation`][glossary-djangoformmutation] /
    [`DjangoModelFormMutation`][glossary-djangomodelformmutation] to
    `shipped (0.0.12)`; add both to **Public exports** + the **Index** + the
    **Mutations** browse-by-category row; move the package-version line to `0.0.12`),
    [`docs/README.md`][docs-readme] / [`README.md`][readme] (form mutations
    listed as shipped rather than upcoming, and the README **Status** line
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
[`spec-036`][spec-036] defined the reusable contracts (the
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
3. **Reuse the shared `FieldError` envelope.** Map `form.errors` (and the form's
   `NON_FIELD_ERRORS` bucket) onto the one
   [`FieldError`][glossary-fielderror-envelope] envelope `036` defined
   ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
4. **Run the write through the form.** `form.is_valid()` → `form.save()`, sync and
   async, inside the one-`transaction.atomic()` boundary `036` set; the `ModelForm`
   payload's object is re-fetched and optimizer-planned for the response selection
   ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
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
  (`Meta.serializer_class`) and [Auth mutations][glossary-auth-mutations] are separately
  carded and ship after this one, in `0.0.13`; they reuse the same envelope
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **Changing the `036` model-driven generator or the `FieldError` envelope.** The
  `036` contracts are reused **unchanged**; this card adds no member to
  [`FieldError`][glossary-fielderror-envelope] and does not re-open
  [`mutations/inputs.py`][mutations-inputs]'s model-column generator
  ([Decision 2](#decision-2--card-scope-boundary-the-two-form-flavors-ship-serializer--auth-stay-out-the-frozen-036-contracts-are-reused-unchanged)).
- **The `TestClient` *ergonomic* helper, NOT file-field correctness.** This card
  **owns the runtime correctness** of `forms.FileField` / `forms.ImageField`: the
  `Upload` input typing, the `data=` / `files=` decode split, and `form_class(data=,
  files=, instance=)` construction
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)),
  proven by **at least one raw `django.test.Client` multipart live test** for a
  form-backed `Upload` field (Slice 4). The raw multipart HTTP path already exists
  from the `0.0.11` upload work, so correctness does **not** wait on a helper; only
  the *ergonomic* `TestClient` / `AsyncTestClient` wrapper is carded separately, and it
  ships in `0.0.14` as [`django_strawberry_framework/testing/`][testing-package]
  ([`TestClient`][glossary-testclient], [Edge cases](#edge-cases-and-constraints)).
- **Form `delete`.** graphene-django form mutations are create / update only; a
  `ModelForm` does not delete. A `delete` write stays the model-driven
  [`DjangoMutation`][glossary-djangomutation] (`Meta.operation = "delete"`) the
  consumer already has ([Decision 10](#decision-10--operations-create--update-for-the-modelform-no-form-delete)).
- **`Meta.return_field_name`.** graphene-django's per-mutation output-field-name
  key is **not** adopted; the `036`-frozen uniform `node` / `result` slot
  supersedes it for one cross-flavor client contract
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling),
  carried in [Risks and open questions][rationale-risks] as a card-body tension).
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
| [`ErrorType.from_errors(form.errors)`][upstream-forms-types] on the payload | `form.errors` → the shared [`FieldError` envelope][glossary-fielderror-envelope], `NON_FIELD_ERRORS` → the `"__all__"` sentinel ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)) | this card — reuse the `036` envelope, adding no member |
| graphene-django `Meta.return_field_name` (per-mutation output field name) | not adopted — the `036` uniform `node` / `result` slot supersedes it ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)) | deliberate non-adoption (card-body tension, [Risks and open questions][rationale-risks]) |
| graphene-django `DjangoModelFormMutation` **full** update (a bound form over the raw input) | **partial** update via full-payload reconstruction from the located instance ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)) | deliberate divergence — matches the package's own `036` `PartialInput` contract |
| graphene-django form file fields (multipart `request.FILES` → form `files=`) | `Upload` input typing + the `data=` / `files=` decode split + `form_class(data=, files=, instance=)` ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)) | this card — runtime correctness owned here (raw multipart live test) |
| graphene-django [`get_form` / `get_form_kwargs`][upstream-forms-mutation] (constructor-kwarg seam) | `get_form_kwargs(info, *, data, files, instance=None)` / `get_form(...)` hooks (default the package kwargs) + schema-time discovery via `form_class.base_fields` / `get_form_fields()` ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth) / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)) | this card — parity seam for migrated forms needing `user` / request / tenant |
| graphene-django relation visibility (none — form's own queryset only) | every relation id (Relay + raw pk) visibility-checked through the related primary `get_queryset` before the form, then `to_field_name`-converted ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)) | package security invariant beyond graphene parity (the `036` contract, raw-pk gap closed) |
| graphene `MutationOptions` / `ClientIDMutation` / `__init_subclass_with_meta__` | rejected for a nested `class Meta` base ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions)) | deliberately not borrowed |

### From `graphene-django` — borrow the user-facing shape

- **`Form` / `ModelForm` consumption.** The mutation runs the consumer's existing
  form — `form_class(data=…, files=…)` (create) / a full-payload-reconstructed
  `form_class(data=…, files=…, instance=<row>)` (update), `form.is_valid()`,
  `form.save()`. The form's `clean_<field>` / `clean()` validation and widget
  coercions are honored for free; the one deliberate divergence is **partial** update
  semantics (graphene-django's form update is full), via the
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
  reconstruction, for consistency with the model-driven `036` `PartialInput`.
- **`form.errors` → field-keyed envelope.** graphene-django's
  `ErrorType.from_errors(form.errors)` is the parity shape; here it maps onto the
  shared `036` [`FieldError`][glossary-fielderror-envelope].

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
required, [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload));
the resolver locates the row through
`ItemType.get_queryset(...)` (a row the caller cannot see is a not-found `FieldError`
on `id`, never an existence leak), then reconstructs the **full** bound-form payload
from the located row's current values overlaid with the provided fields before
constructing the form
([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
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

Rationale companion — this Decision's justification and its two rejected
alternatives: [Decision 1][rationale-d1].

### Decision 2 — Card-scope boundary: the two form flavors ship; serializer / auth stay out; the frozen `036` contracts are reused unchanged

This card ships the **form-validated** write flavor end-to-end: the
[`DjangoFormMutation`][glossary-djangoformmutation] /
[`DjangoModelFormMutation`][glossary-djangomodelformmutation] bases, the
form-field → input mapping, the `is_valid()` → `form.errors` → `save()` pipeline,
and the products live form surface. It explicitly does **not** ship the adjacent
flavors, each owned by a named `0.0.13` card:

- **DRF serializer mutations** ([`SerializerMutation`][glossary-serializermutation])
  — the `0.0.13` sibling, landing as
  [`django_strawberry_framework/rest_framework/`][rest-framework-package].
- **Auth mutations** ([Auth mutations][glossary-auth-mutations]) — the `0.0.13`
  sibling, landing as
  [`django_strawberry_framework/auth/mutations.py`][auth-mutations].

And it **reuses, unchanged, the contracts [`spec-036`][spec-036] defined for
exactly this**: the [`FieldError` envelope][glossary-fielderror-envelope], the
`<Name>Payload` wrapper (uniform `node` / `result` slot), the
[`DjangoMutationField`][glossary-djangomutationfield] factory, the
[`DjangoModelPermission`][glossary-djangomodelpermission] / `Meta.permission_classes`
/ `check_permission` write-auth seam, and the [`_resolve_model`][spec-036] hook.
This card adds **no** member to [`FieldError`][glossary-fielderror-envelope] and does
not re-open the `036` model-column input generator (the form generator is a separate
module). The envelope type itself is **additive, not frozen** — a member may be added
(the type has since gained `codes` and `path`), never removed or retyped — so
"reused unchanged" is a statement about *this* card's own footprint on it, not a
promise that the type will never grow. Mirroring [`spec-036`][spec-036] Decision 2's "define the surface, reuse
it later" discipline from the other direction (`036` defined; `038` consumes).

Rationale companion — this Decision's justification and its two rejected
alternatives: [Decision 2][rationale-d2].

### Decision 3 — `class Meta` surface, not graphene's `MutationOptions`

A form mutation is a **base class with a nested `class Meta`** (`form_class` +
optional `fields` / `exclude` + `operation` for the `ModelForm` flavor), declared
exactly like every other consumer surface in the package
([`DjangoType`][glossary-djangotype] / [`FilterSet`][glossary-filterset] /
[`OrderSet`][glossary-orderset]). It is **not** graphene's
`MutationOptions` / `__init_subclass_with_meta__(form_class=..., model=...,
return_field_name=...)` keyword-options flow, and **not** a `ClientIDMutation`
lineage.

Rationale companion — this Decision's justification and its two rejected
alternatives: [Decision 3][rationale-d3].

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

Rationale companion — this Decision's justification and its two rejected
alternatives: [Decision 4][rationale-d4].

### Decision 5 — Public surface: `DjangoFormMutation` / `DjangoModelFormMutation` exported from the root

Two net-new public symbols, re-exported from [`__init__.py`][init] and added to
`__all__`:

- `DjangoFormMutation` — the plain-`Form` base.
- `DjangoModelFormMutation` — the `ModelForm` base.

No net-new field factory or error type: both flavors are exposed through the
**existing** [`DjangoMutationField`][glossary-djangomutationfield] and return the
shared [`FieldError`][glossary-fielderror-envelope] envelope. But "exposed through
`DjangoMutationField`" is **not** "the factory is unchanged" — the shipped factory is
hardwired to the model write path on three axes, each generalized into an
overridable seam on the mutation base (the seam set is the spine
of [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling),
and the `0.0.13` [`SerializerMutation`][glossary-serializermutation] flavor is
designed to reuse every one of them):

1. **Target check.** [`mutations/fields.py`][mutations-fields]
   `_validate_mutation_target` cannot assert
   `issubclass(mutation_cls, DjangoMutation)`: the `ModelForm` flavor would pass (it
   *is* a subclass), but the model-less plain `DjangoFormMutation` is not one, and
   importing the form bases here would close a load cycle
   ([`forms/sets.py`][forms-sets] imports [`mutations/sets.py`][mutations-sets]). The
   check is therefore **duck-typed** over the protocol every flavor carries
   ([`mutations/fields.py`][mutations-fields]`::_has_mutation_protocol`): a
   `_mutation_meta` attribute (present even as `None` on an abstract base, so the next
   guard can tell "abstract base" from "not a mutation at all"), callable
   `resolve_sync` / `resolve_async` / `input_type_name`, and a non-`None`
   `input_module_path`. It must **not** require `_input_class` / `_payload_type_name`:
   those are **bind** outputs, and the field is constructed at import — when
   `@strawberry.type class Mutation` evaluates — before the bind runs, so a check
   requiring them could never pass. Concreteness is then a separate check of the
   class's **own** `_mutation_meta` snapshot plus current membership of a declaration
   ledger, because an MRO lookup would let an unregistered child inherit its parent's
   snapshot and a stale own snapshot can outlive a `registry.clear()`.
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
   ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
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

Rationale companion — this Decision's justification and its three rejected
alternatives: [Decision 5][rationale-d5].

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
  overrides it with a form allowed-key set — **two** of them, since the two flavors
  differ: the `ModelForm` set is `MODEL_BACKED_WRITE_META_KEYS | {form_class}` and the
  plain set is `COMMON_WRITE_META_KEYS | {form_class}`, so both add `form_class` and
  drop `model` / `input_class` / `partial_input_class`, and the plain set additionally
  has neither `operation` nor `select_for_update`. It restricts `operation` to
  `{"create", "update"}` (rejecting `delete` at class creation), and validates `Meta.form_class`
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
  / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).

That [`_resolve_model`][spec-036] is overridable is the seam [`spec-036`][spec-036]
Decision 5 designed ("the 0.0.12 form flavor derive[s] the model from
`Meta.form_class._meta.model` … without re-opening the base validation") — but it is
*one* of the four seams, not the whole story; the spec-036 author scoped only the
model-source seam, and the other three are net-new generalizations this card lands.

**`DjangoFormMutation` (plain `Form`) is the model-less sibling.** A plain `Form` has
no model, so it cannot resolve a primary [`DjangoType`][glossary-djangotype] payload
or inherit [`DjangoMutation`][glossary-djangomutation]'s resolvable-model contract.
It is a lighter base with its **own** metaclass —
`DjangoFormMutationMetaclass = make_meta_validating_metaclass(register_form_mutation, …)`,
the shared metaclass factory [`mutations/sets.py`][mutations-sets] exposes, bound over
the plain form's own disjoint declaration ledger — that shares the form pipeline (`is_valid()`
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
**Pinned plain-form payload contract — a fixed schema rule.** The generated `<Name>Payload` for a plain `DjangoFormMutation` is
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
and needs no per-field descriptions. The shape is fixed, so an implementer cannot
ship a divergent plain-form payload.

**`Meta.return_field_name` is not adopted.** graphene-django lets a `ModelForm`
mutation name its output field; [`spec-036`][spec-036] Decision 7 **froze**
the uniform `node` / `result` slot precisely to keep one client contract across
flavors and to dodge model-name collisions (`Property` → `property`). The form flavor
inherits that frozen slot. The card body lists `Meta.return_field_name` as part of
the surface; preferring the frozen `036` slot is a deliberate divergence recorded
in [Risks and open questions][rationale-risks] per the [`docs/SPECS/NEXT.md`][next]
"prefer the card, surface the conflict" rule (the conflict is between the card
body and a *frozen downstream contract* `036` established, which the card itself
depends on).

Rationale companion — this Decision's justification, its two rejected
alternatives, and the rejected cleaned-data-echo output shape:
[Decision 6][rationale-d6].

### Decision 7 — Form-field → Strawberry input mapping: the form is the input source of truth

The input type derives from the **form's declared fields**
(`form_class.base_fields`, the stable class-level set — schema-time field discovery
above), not the model's editable columns. [`forms/converter.py`][forms-converter]
ships a `convert_form_field(field)` registry (the [graphene-django parity
shape][upstream-forms-converter]) returning each form field's Strawberry annotation +
required-ness from `field.required`:

- text-like (`CharField` / `EmailField` / `SlugField` / `URLField` / `RegexField` /
  `ChoiceField` / base `Field`) → `str`; `IntegerField` → `int`; `BooleanField` →
  `bool`; `FloatField` → `float`; `DecimalField` → `Decimal`; `UUIDField` →
  `uuid.UUID`; `JSONField` → `strawberry.scalars.JSON`; `DateField` /
  `DateTimeField` / `TimeField` → the Python-native types; `MultipleChoiceField` →
  `list[str]`. Resolution is a `type(field).__mro__` walk, so the most-specific
  registered class wins regardless of registration order — and `JSONField` **must**
  carry its own row even though it subclasses `CharField`, because otherwise the
  parent's entry types a JSON payload as `String` and rejects the object / array
  literals the form field itself accepts.
- `NullBooleanField` → `bool | None`. Its requiredness is a **three**-case rule and
  the one requiredness decision in the subsystem, single-sited in
  [`forms/converter.py`][forms-converter]`::form_field_required` and shared by the
  annotation path and [`forms/inputs.py`][forms-inputs]'s build site so the
  column-backed and column-less paths cannot drift: an **exact** `NullBooleanField` is
  forced optional (its `validate` is a no-op, so a declared `required=True` could
  never be enforced); a **subclass** keeps its declared requiredness, since it may
  override validation and genuinely reject omission (and so carries a non-null
  `bool`); and a field backed by a **non-null model column** keeps `required=True`,
  since model validation rejects `None` after the form field's no-op and the non-null
  annotation refuses it before execution instead.
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
[Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload))
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

**The fail-loud contract requires NOT registering a base-`forms.Field` catch-all.** A naive `functools.singledispatch` with `forms.Field` registered → `str` makes
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

**Per-field metadata: the `input_attr` → `form_field_name` reverse map.** The
generated input GraphQL names follow the cross-flavor `036` convention so the wire
contract is uniform across mutation flavors — a `ModelChoiceField` named `category`
generates `categoryId` (python attr `category_id`), a scalar/`MultipleChoice`/file
field keeps its own name. But a **bound Django form is keyed by form-field name**
(`ItemModelForm(data={"category": pk})`, **not** `{"category_id": pk}` — the latter
makes the form think `category` is missing). So `forms/inputs.py` **retains, per
generated input field, a [`utils/inputs.py`][utils-inputs]`::InputFieldSpec`** that
`forms/resolvers.py` consults at decode. That is the single reverse-map record type
every write flavor shares: `input_attr` (the generated Strawberry attr) and
`graphql_name` (the camel-cased wire name) map to `target_name` — the form's own
declared field name on this path — plus a `kind ∈ {scalar, relation_single,
relation_multi, file}` and, for a relation, the `related_model` recorded at build time
so the decode never re-discovers it per request. The four `kind` constants are defined
in [`utils/inputs.py`][utils-inputs] and re-exported by
[`forms/converter.py`][forms-converter], which owns the constants and not the record
type:

- `category_id` / `categoryId` → form field `category`, kind `relation_single`
  (the form relation decoder below type-checks the id — `GlobalID` *or* raw pk —
  resolves the **visible** object through the related primary type's `get_queryset`,
  and places its `to_field_name` value (default `obj.pk`) under `category`, which the
  bound `ModelChoiceField.to_python` then resolves).
- `genres` → form field `genres`, kind `relation_multi` (each element decoded,
  visibility-checked, and `to_field_name`-converted the same way, then placed as a
  list under `genres` for `ModelMultipleChoiceField`).
- `avatar` → form field `avatar`, kind `file` (routed to `files=`, see
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
- every plain scalar → identity (`name` → `name`, kind `scalar`).

The reverse map is the single fix for the "`category_id` vs `category`" hazard: the
generated input may *expose* `categoryId` (parity), but the decode always produces a
**form-field-keyed** dict the bound form validates natively — never accidental
model-assignment semantics. Package + live tests prove the relation field validates
**through the form** (`clean_<field>` runs), not through a raw model `setattr`.

**The relation decode visibility-checks EVERY branch — Relay `GlobalID` AND raw pk.**
A default `ModelForm`'s relation queryset is `Category.objects.all()` — **not**
request-scoped — so the visibility gate must run before the form, and it must cover
the **non-Relay raw-pk branch** too: a raw-pk target has no `GlobalID` to scope, so a
decoder that visibility-checks only the Relay branch lets a writer attach a hidden
related object. The gate is therefore owned by one shared spine,
[`utils/write_values.py`][utils-write-values]`::decode_visible_relation`, which every
write flavor rides and which the form flavor only *colors*: the spine (i) skips a
clear / no-value unchanged, so the bound form's own validation decides required-ness,
(ii) type-checks and coerces the id (a bad `GlobalID` or an uncoercible raw pk is the
uniform field-keyed `FieldError`), (iii) for **both** branches **resolves the object
from the related primary [`DjangoType`][glossary-djangotype]'s
[`get_queryset`][glossary-get_queryset-visibility-hook]** (the same
`apply_type_visibility_sync(initial_queryset(...))` query every read surface applies) —
a pk not in that visible set is the same no-existence-leak field-keyed `FieldError`,
whether it arrived as a `GlobalID` or a raw pk — and (iv) projects the visible object
to the flavor's bound value. The form's colouring is the `empty_values` skip and the
`to_field_name` projection below; `decode_field_handlers` /
`decode_provided_fields` own the `UNSET` strip and the `kind` dispatch around it. The
form's own `queryset` is then a *secondary* guard, not the only one.

**`to_field_name` is honored when converting the object back to the form's key.**
A `ModelChoiceField` may set `to_field_name` (and a
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
are forced optional — [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)'s
reconstruction supplies them from the located row — but a **non-model** extra form
field (a `confirm`, a captcha, an action flag, with no model column to reconstruct
from) keeps its declared `field.required` (see
[Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)'s
required-extra-field rule), so a required extra field stays required on update and an
optional one may be omitted.

**Shape identity + naming + collision (the `036` discipline).** A generated form
input's identity is **not** its name — it is the tuple **`(form_class, operation
kind, frozenset(effective field names after `Meta.fields` / `Meta.exclude`),
field-discovery hook discriminator)`**, parallel to `036`'s `(model, operation kind,
effective field set)` ([`mutations/inputs.py`][mutations-inputs]
`mutation_input_shape` / `mutation_input_type_name`) plus one component the form
flavor needs. The fourth component is a **hook discriminator**, not a fifth concept:
[`forms/sets.py`][forms-sets]`::_form_input_hook_identity` is `None` unless the
mutation overrides `get_form_fields`, in which case it is the mutation class, so two
mutations over one form with **different** field-discovery overrides cannot dedupe to
one input. The **operation kind** component is the
`DjangoModelFormMutation`'s `"create"` / `"update"`, or the fixed sentinel **`"form"`**
for a plain `DjangoFormMutation` (which has no model operation) — so a plain
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
the **fail-loud fix** for the two collision cases: (a) the same
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
already raises on a second *different* class under one name (the `036`
second-different-class-under-one-name raise) — so the form flavor inherits the early-`ConfigurationError`-not-late-Strawberry-error
posture rather than re-deriving it.

**`Meta.fields` / `Meta.exclude` are normalized + fail-loud against
`form_class.base_fields`.** Mirroring `036`'s `_normalize_field_sequence`, the form base validates the
narrowing at **class creation**: a bare string (`fields = "name"`) is rejected (it
would iterate as characters), duplicate names are rejected, `fields` and `exclude`
are mutually exclusive, and a name in neither `form_class.base_fields` raises
[`ConfigurationError`][glossary-configurationerror] naming the unknown field (a typo
like `fields = ("emial",)` fails loud, never silently shrinks the input). An
**empty effective field set** (a `fields = ()`, an `exclude` that drops every field,
or a form with no fields) raises [`ConfigurationError`][glossary-configurationerror]
at finalization — never a bare empty `@strawberry.input` that Strawberry rejects only
at schema build (the `036` empty-input guard, applied to `form.base_fields`).

**A `create` narrowing that drops a required form field is rejected.** A bound
form fails required-validation for any `field.required` field absent from its bound
`data=`, and `initial` is **not** a substitute for submitted data — so a `create`
whose effective field set (after `Meta.fields` / `Meta.exclude`) omits a still-declared
required form field would compile to a schema that *looks* valid but can **never**
succeed. The form base therefore raises [`ConfigurationError`][glossary-configurationerror]
at class creation, naming the missing required field(s), when `operation = "create"`
and the narrowing excludes any `field.required` form field (covering **both**
`Meta.fields` and `Meta.exclude`). The escape hatch is an overridable
`get_form_kwargs` / `get_form` ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload))
that supplies those values before binding: when the consumer has overridden that hook,
the guard is waived (it cannot know *which* fields the override injects, so it trusts
the explicit override rather than block a legitimate scoped form).

**There are TWO narrowing guards, keyed on that one waiver.** `update` is not exempt,
only narrower: a required **model-backed** field dropped from a partial input is
harmless, because [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)'s reconstruction supplies it
from the located row — but a required **column-less** field (a declarative
`confirm = forms.CharField(required=True)`) has no row value to reconstruct from, so
dropping it finalizes a form whose bound validation fails on every request while the
schema still builds. [`forms/inputs.py`][forms-inputs]`::guard_partial_required_column_less_fields`
rejects that narrowing at bind, naming the field(s). Scoping the partial guard to
column-less fields is load-bearing: reusing the create guard here would wrongly reject
the reconstructable model-backed fields the partial path legitimately drops.

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
(the kwarg-requiring-form case).** The input shape is derived from
**`form_class.base_fields`** — the class-level declared-fields dict Django's
`DeclarativeFieldsMetaclass` / `ModelFormMetaclass` populate at class creation (for a
`ModelForm`, `base_fields` already includes the model-derived fields). Reading it
needs **no instantiation**, so a form whose `__init__` requires constructor kwargs
(`user`, `request`, a tenant — common in migrated forms) still has a discoverable,
**request-independent stable** field shape (a form that mutates `self.fields` in
`__init__` by request could not be a stable GraphQL input anyway). An overridable
classmethod **`get_form_fields(cls) -> dict[str, forms.Field]`** (default:
`form_class.base_fields`) lets a consumer customize the discovered set; whatever it
returns must be stable across requests. Instantiating `form_class()` no-arg to read
`form.fields` is **not** an option: it breaks for exactly the kwarg-requiring forms
this rule exists to serve.

Rationale companion — this Decision's justification and its two rejected
alternatives: [Decision 7][rationale-d7].

### Decision 8 — Resolver pipeline: instantiate → `is_valid()` → `form.errors` → `save()` → optimizer re-fetch → payload

[`forms/resolvers.py`][forms-resolvers] runs one pipeline per flavor, sync and async,
swapping the model-construct + `full_clean()` heart of the
[`mutations/resolvers.py`][mutations-resolvers] pipeline for the form's own
validation and write, but **reusing the surrounding `036` steps**. The order is
**locate → authorize → decode → construct/validate → write → re-fetch → return**, and
**authorize runs BEFORE the relation decode** — the same authorize-first order the `036`
model path uses. That ordering is a security boundary, not a preference: the decode
issues visibility-scoped `get_queryset` queries, so decoding first would let an
unauthorized caller probe related-object visibility by id, and a write-auth denial
(top-level `GraphQLError`) versus an in-band relation
[`FieldError`][glossary-fielderror-envelope] is an observable distinction. Authorizing
first collapses both to the denial. Any flavor reusing this pipeline (the `0.0.13`
[`SerializerMutation`][glossary-serializermutation]) **must authorize before decoding
relations**. The order is single-sited in
[`mutations/resolvers.py`][mutations-resolvers]`::run_write_pipeline_sync`,
whose own docstring pins it (#"authorize BEFORE decode") and which every
write flavor rides.

1. **Locate** (`update`, `ModelForm` only): the top-level `id:` argument is
   `strawberry.ID` (a raw GlobalID **string** the package decodes server-side via the
   reused `036` `coerce_lookup_id` — the same `node(id: ID!)` contract the shipped
   [`DjangoNodeField`][glossary-djangonodefield] uses, **distinct** from a relation
   `data:` field whose value is a
   Strawberry-coerced `GlobalID`); a malformed / wrong-model / uncoercible `id:` is an
   `id`-keyed `FieldError` **before** any lookup (no existence leak — the mutation
   surface returns the `FieldError` envelope, **not** the node field's
   `null` / `GLOBALID_INVALID`). The row is then resolved through the target type's
   [`get_queryset`][glossary-get_queryset-visibility-hook] (the `036`
   `locate_instance`); a miss (hidden or genuinely absent — indistinguishable) is a
   not-found `FieldError` on `id`. This step
   **only locates** — the form is **not** constructed here (the located row is
   carried to step 4 as the `instance=` kwarg), so the form is built exactly once, in
   step 4, from the reconstructed `data=` / `files=` payload. (graphene-django builds
   its form once too via `get_form_kwargs`, but as a *full* update; the package's
   step-4 merge is what adds true partial semantics on top of that single
   construction.)
2. **Authorize**: the inherited `check_permission` / `Meta.permission_classes`
   (before validation for `create`; after the locate for `update`). A denial raises
   a top-level `GraphQLError` ([`spec-036`][spec-036] Decision 15).
3. **Decode** the `data:` input into **two `dict`s keyed by FORM-field name** —
   `provided_data` (scalars, choice-enum raw values, and relation pks / pk-lists) and
   `provided_files` (uploaded files) — using the shared
   [`utils/inputs.py`][utils-inputs]`::InputFieldSpec` reverse-map record of
   [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)
   (`UNSET` stripped). A
   `relation_single` / `relation_multi` field runs the **form relation decoder**
   ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)) over the
   shared [`utils/write_values.py`][utils-write-values]`::decode_visible_relation`
   spine, the single owner of the cross-flavor invariant that a writer never attaches
   a row it cannot see: it type-checks each id (`GlobalID` *or* raw pk; wrong-model /
   uncoercible → field-keyed `FieldError`, the `036` id-type-check contract), **resolves the
   visible object through the related primary `DjangoType.get_queryset` for BOTH
   branches** (a hidden / unseeable target is the same field-keyed `FieldError`, no
   existence leak), and lands the object's `to_field_name` value (default `obj.pk`)
   under the form field name (`{form_field_name: value}` / `{form_field_name: [value,
   …]}`); a `file` field lands its uploaded value in **`provided_files`**, not
   `provided_data` (the file-routing fix below); a `scalar` choice-enum member is
   unwrapped to its raw value. The split by `kind` is the single point that keeps
   form-field names,
   visibility-checked relation pks, and file uploads each going to the right place.
4. **Construct + validate** the form **once**, through the overridable
   **`get_form_kwargs(self, info, *, data, files, instance=None) -> dict`** hook (the
   graphene-django `get_form_kwargs` parity seam, used by `create`, `update`, and
   the plain form). The default returns `{"data": data, "files": files}` (plus
   `"instance": instance` when non-`None`), and the resolver builds the form as
   `form_class(**self.get_form_kwargs(info, data=…, files=…, instance=…))`. A consumer
   overrides it to inject constructor kwargs migrated forms need — `user=…`,
   `request=…`, a tenant — or to pass the request-scoped `ModelChoiceField` queryset
   the form narrows with in its own `__init__`: `get_form_kwargs` returns
   **constructor kwargs**, so the hook is the channel and the form applies it,
   **without changing the generated input shape** (the input is derived from
   `get_form_fields()`, [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth),
   independent of `get_form_kwargs`). A hook that injects a value the narrowed input
   cannot carry is only **observably** working if a test asserts the **written row**:
   the wire envelope of a failed write is identical whether the injection ran or not,
   because a missing non-nullable FK raises `IntegrityError` too and maps to the same
   `"__all__"` envelope. A `get_form(self, info, *, data, files,
   instance=None)` hook (default: `form_class(**self.get_form_kwargs(...))`) is the
   coarser override for full control. This **does not replace** the relation-visibility
   gate (step 3, which runs before the form regardless) — `get_form_kwargs` adds
   request-scoping on top of, not instead of, the visibility check. The form is built
   with the `data=` / `files=` split Django requires (a bound form reads
   scalars/relations from `data=` and uploaded files from `files=` — an `UploadedFile`
   in `data=` does **not** validate):
   - **`create`** — `data = provided_data`, `files = provided_files`, then
     `form_class(**get_form_kwargs(info, data=provided_data, files=provided_files))`.
   - **`update` (the pinned partial-update contract)** — a bound `ModelForm`
     validates **every** field, so handing it only the provided fields would reject a
     valid partial update (missing-required) or clear omitted optional fields. So the
     resolver **reconstructs the complete bound payload from the located instance plus
     the provided values**, overlaid by `provided_data`, and passes
     `files = provided_files` **only** (an omitted file field is
     preserved by the bound `form_class(instance=…)` via its `initial`, never
     re-supplied and never cleared); then `form_class(**get_form_kwargs(info,
     data=data, files=files, instance=<located row>))`.
     - **The reconstruction reads the form's FULL declared field set**
       (`get_form_fields()`), not the narrowed input: a `Meta.fields` /
       `Meta.exclude` narrowing drops fields from the GraphQL input, but the bound
       `ModelForm` still validates every field it declares, so an excluded
       model-backed field must still be supplied from the located row.
     - **Every omitted field binds in the shape a provided one decodes to**, which
       takes **three** forms, single-sited in
       [`forms/resolvers.py`][forms-resolvers]`::_reconstruct_partial_data`:
       `model_to_dict` for scalars and a `to_field_name`-**less** FK / one-to-one
       (whose `model_to_dict` value is already the key the bound `ModelChoiceField`
       resolves); `_to_form_key_value` per member for a real forward M2M (the
       `to_field_name` value, default `obj.pk` — not `model_to_dict`'s list of
       related *instances*); and `_to_form_key_value` for a `ModelChoiceField`
       **with** `to_field_name` set (whose `model_to_dict` pk would fail `to_python`).
       Getting any of the three wrong makes an omitted unchanged field fail where a
       provided unchanged field passes.
     - **A file field contributes no key at all.** `model_to_dict` yields the stored
       relative path, which is not a re-bindable `data=` value for a field fed from
       `files=`, so file fields are excluded from the reconstruction entirely.

     This yields true partial
     semantics — omitted scalars,
     FKs, M2Ms, and files are preserved; provided fields update — **and** the form
     validates the full merged set, so `unique_item_per_category` validates correctly
     when only `name` changes (the unchanged `category` comes from the instance). It
     matches the `036` model-driven `PartialInput` contract (consistent partial-update
     UX across both mutation flavors), not graphene-django's full-update form.
     - **Required extra (non-model) form fields.** The reconstruction only supplies
       **model-backed** fields, so a `ModelForm`'s extra declared field with no model
       column (a `confirm`, a captcha, an action flag) has **no instance value to
       reconstruct**. The pinned rule: in the `<FormClass>PartialInput`, model-backed
       fields are forced optional (reconstructed), but a **non-model form field keeps
       its declared `field.required`** ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
       So a **required** extra field stays required on update (the caller must supply
       it — it is in `provided_data`, never silently `None`), while an **optional**
       extra field may be omitted (and the bound form applies its own `initial` /
       empty value). This avoids both failure modes — an all-optional
       input that lets a caller omit a required extra field (then the bound form fails
       required validation confusingly) and a meaningless reconstructed `initial`.
   Then `form.is_valid()`. A failure maps `form.errors` onto the
   [`FieldError` envelope][glossary-fielderror-envelope] by **reusing the `036`
   mapper directly, not a parallel one**: `form.errors.as_data()` yields the
   `{field: [ValidationError, …]}` shape that
   [`utils/errors.py`][utils-errors]`::validation_error_to_field_errors`
   already consumes through its `error_dict` branch, so the form pipeline calls
   `validation_error_to_field_errors(ValidationError(form.errors.as_data()))` — the
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
   `IntegrityError` → `FieldError` mapper, not left to bubble.** A `form.is_valid()`
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

**Helper reuse — share, do not re-implement.** Steps 1 / 2 / 4 / 6 / 7 are not
form-local code. The seven-step sequence above is a **shared pipeline runner the form
flavor parameterizes**, not a form-local body calling helpers one by one:
[`forms/resolvers.py`][forms-resolvers] imports `make_resolver_entries` and
`run_write_pipeline_sync` from [`mutations/resolvers.py`][mutations-resolvers] and
`pipeline_write_phase` from
[`utils/write_transaction.py`][utils-write-transaction], and supplies only the
form-specific decode and write steps; the orchestration, the transaction boundary and
the authorize-before-decode ordering are owned once, in the runner. The pipeline
helpers the runner composes are public, and live in three modules:

- [`mutations/resolvers.py`][mutations-resolvers] — `locate_instance` (the
  visibility-scoped `update` locate, a security contract), `coerce_lookup_id` /
  `not_found_error` (the server-side `id` decode + not-found shape),
  `authorize_or_raise` (the write-auth gate), `refetch_optimized`
  ([Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path)),
  `build_payload` (the uniform-slot envelope), and `save_or_field_errors` (the
  save-time `IntegrityError` → `FieldError` mapper reused per step 5, wrapping a
  zero-arg save callable).
- [`utils/errors.py`][utils-errors] — `validation_error_to_field_errors` (the
  validation-error mapper reused per step 4).
- [`utils/write_values.py`][utils-write-values] — `raw_choice_value` (the choice-enum
  unwrap) alongside the relation-decode spine of step 3.

`payload_object_slot`, the uniform-slot accessor `build_payload` writes through, lives
in [`mutations/inputs.py`][mutations-inputs]. The form flavor reaches none of this by
re-implementation and none of it through another module's privates.

**How this pipeline actually fires.** `DjangoMutationField._resolve` must not
hardcode the **model** resolver, or this `forms/resolvers.py` pipeline would be dead
code: it calls the overridable `resolve_sync` / `resolve_async` classmethods on the
mutation class ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)), and the model
base is what delegates to [`mutations/resolvers.py`][mutations-resolvers]. Both form
flavors' pair comes from one shared factory,
[`mutations/sets.py`][mutations-sets]`::resolver_seams`, invoked with `with_id=False`
for the plain flavor — matching the `id`-gate
[`mutations/fields.py`][mutations-fields] applies on its #"operation != \"form\"" test,
so a model-less mutation is never given an `id:`
argument. `bind_form_mutations()` is likewise one call to the shared
`bind_write_declarations`, and the operation vocabulary the sentences above spell out
(`NON_DELETE_WRITE_OPERATIONS`, `NON_DELETE_OPERATION_INPUT_KIND`,
`non_delete_operation_error`) is owned by
[`mutations/operations.py`][mutations-operations] so no flavor re-spells it. A
`ModelForm`'s
[`form.save()`][upstream-forms-mutation] with `commit=True` writes its M2M rows
(`save_m2m()` runs inside `save()`), so step 5 stays a single `form.save()` inside the
one `transaction.atomic()` — no separate M2M step.

The async path runs the whole sync body in one
`sync_to_async(thread_sensitive=True)` call, and a sync pipeline meeting an
`async def` [`get_queryset`][glossary-get_queryset-visibility-hook] raises
[`SyncMisuseError`][glossary-syncmisuseerror] — both inherited from the `036`
boundary discipline.

**The runner's boundary is more than the one `transaction.atomic()`**, and a form
mutation inherits every part of it: `check_deadline(info)` runs **before** the
transaction opens, so an operation already past its budget never starts a write; the
transaction is opened and pinned to one write alias
(`open_write_pipeline` / `pipeline_alias_guard` / `check_instance_write_alias`), so a
step cannot silently write through a second connection; and an immutable
`authorized_pk` / `target_state` snapshot is captured right after the locate, so a
later step cannot retarget the write to a row the caller was not authorized for. A
step returning a `list[FieldError]` marks the block for rollback, so a partial write
followed by a validation failure never commits.

Rationale companion — this Decision's justification and its two rejected
alternatives: [Decision 8][rationale-d8].

### Decision 9 — Optimizer composition: the `ModelForm` payload re-fetch rides the `spec-036` G2 path

The `ModelForm` payload's object (pipeline step 6) is re-fetched by pk and routed
through the **same** `036` `refetch_optimized` /
[`DjangoOptimizerExtension`][glossary-djangooptimizerextension] path the model-driven
mutation uses. Because the operation is a mutation, the [`spec-035`][spec-035] **G2**
gate keeps `select_related` / `prefetch_related` but suppresses
[`.only(...)`][glossary-only-projection] — so the re-fetched instance carries no
selection-shaped deferred-field set. The re-fetch is **by pk without the visibility
filter** (the `036` re-fetch exception: the actor just wrote the row, so round-tripping
their own write is not an existence leak).

Rationale companion — this Decision's justification and its one rejected
alternative: [Decision 9][rationale-d9].

### Decision 10 — Operations: `create` / `update` for the `ModelForm`, no form `delete`

`DjangoModelFormMutation` reuses `Meta.operation` ∈ `{"create", "update"}` (the
`036` selector). A form `delete` is **not** shipped: graphene-django's form mutations
are create / update only, a `ModelForm` does not delete a row, and the model-driven
[`DjangoMutation`][glossary-djangomutation] (`Meta.operation = "delete"`) already
covers deletion. The plain `DjangoFormMutation` has no model operation — its action
is the form's `perform_mutate`, so it does not declare `Meta.operation`, and its
`_validate_meta` **rejects** any `Meta.operation` (create / update / delete alike) as
unsupported rather than silently accepting a meaningless value; its input-shape
identity uses the fixed `"form"` sentinel for the operation component
([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
The split is per base and total: `DjangoModelFormMutation` validates
`operation ∈ {"create", "update"}`; the plain `DjangoFormMutation` rejects `operation`
outright. No shared rule spans both.

Rationale companion — this Decision's justification and its one rejected
alternative: [Decision 10][rationale-d10].

### Decision 11 — Write authorization: reuse the `036` seam (`DjangoModelPermission` for the `ModelForm`, explicit classes for the plain form)

The `ModelForm` flavor inherits [`DjangoModelPermission`][glossary-djangomodelpermission]
unchanged: because `has_permission` reads the model via
`mutation._resolve_model(mutation.Meta)`, the `_resolve_model` override
([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling))
makes the `add` / `change` model-permission default work for free — an anonymous or
under-privileged caller is denied before the form runs. The visibility-scoped
`update` locate (Decision 8 step 1) and the write-auth check are the same separate
layers `036` set ("can view" ≠ "can write").

The **plain `Form`** has no model, so the model-permission default cannot apply, and
the posture is **deny by default**: an *unset* `Meta.permission_classes` on a plain
form resolves to `(DenyAll,)`
([`forms/sets.py`][forms-sets]`::DjangoFormMutation._validate_meta`), so a real gate is the
consumer's explicit `Meta.permission_classes` and a **public** plain-form write is an
explicit opt-in (`Meta.permission_classes = []`, the `036` AllowAny opt-out). An unset
key is never a configuration error.

The plain base additionally **rejects a `DjangoModelPermission` subclass** in
`Meta.permission_classes` at class creation. That class resolves the write permission
from `mutation._resolve_model(mutation.Meta)` and maps the operation to an `add` /
`change` / `delete` codename; a model-less `DjangoFormMutation` supplies neither (it is
not a [`DjangoMutation`][glossary-djangomutation] subclass, so it has no
`_resolve_model`, and its operation is the `"form"` sentinel). The generic
permission-class validation accepts it — it *is* a class with a callable
`has_permission` — so without the targeted reject the misconfiguration finalizes
cleanly and surfaces only as a raw `AttributeError` at request time. The error names
[`DjangoModelFormMutation`][glossary-djangomodelformmutation] as the model-backed base
and the two valid plain-form postures.

Rationale companion — this Decision's justification and its one rejected
alternative: [Decision 11][rationale-d11].

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
`update`. Products is the card's own home because it already carries the `Item`
constraint and the `036` `Mutation` wiring.

**The live form surface spans three example apps**, and each earns its place:

- **`products`** — eight form mutations: `createItemViaForm`, `updateItemViaForm`,
  `createItemWithFileViaForm`, `updateItemWithFileViaForm`,
  `createDefaultCategoryItemViaForm`, `createStampedItemViaForm`, `submitContact`,
  `submitPing`, over `ItemModelForm` (with a `clean_<field>`), `ItemFileModelForm`,
  `StampedItemModelForm` (kwarg-requiring, the `get_form_kwargs` case), `ContactForm`
  and `PingForm`.
- **`library`** — `CreateShelfViaForm`, `UpdateBookViaForm`, `CreateBranchWithShelf`
  and `CreateBranchPair` over `ShelfRelationsForm` / `BookGenresModelForm` /
  `BranchWithShelfForm` / `BranchPairForm`. Library carries the cases products cannot:
  the **non-Relay raw-pk** relation decode, the `to_field_name` conversion, the
  request-scoped-`queryset` idiom, and the plain-form `perform_mutate` rollback.
- **`scalars`** — `CreateMediaSpecimenImageViaForm`, the image-column flavor of the
  `Upload` routing.

Rationale companion — this Decision's justification and its one rejected
alternative: [Decision 12][rationale-d12].

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
`clear_form_mutation_registry()` reached from `registry.clear()` (mirroring
`clear_mutation_registry`), and a `bind_form_mutations()` entry point that
materializes each plain form's model-less input + payload. **`registry.clear()` clears
THREE form rows**, and it names none of them: each owner **announces its own clear**
via `register_subsystem_clear(...)` under a stable owner key, and `registry.clear()`
drains `iter_subsystem_clears()`. That keeps [`registry.py`][registry] free of any
per-subsystem import, and makes a reload replace an owner's callback rather than
duplicate it. The three rows are `clear_form_input_namespace` (owner
`forms.input_namespace`, registered `before_bind=True` — the generated
input/payload-globals ledger), `clear_form_mutation_registry` (owner
`forms.declarations` — the plain-form declaration registry above), and
`clear_form_shape_build_cache` (owner `forms.shape_cache` — the form-input build cache,
the deliberate twin of the model-flavor `_shape_build_cache`, needed so two mutations
over one form-shape dedupe to one materialized input instead of tripping the
materialize collision; it is cleared at `bind_form_mutations()` start as well, so a
stale class from a failed / re-run finalize cannot leak). `bind_form_mutations()` is
**wired into [`types/finalizer.py`][types-finalizer]'s phase-2.5 window** alongside the
existing `bind_mutations()` / `_bind_filtersets()` / `_bind_ordersets()` calls — a
single named `finalizer.py` edit, not a new public finalize entry point the consumer
must call. It still hangs off the single
[`finalize_django_types()`][glossary-finalize_django_types] call.

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

Rationale companion — this Decision's justification and its two rejected
alternatives: [Decision 13][rationale-d13].

### Decision 14 — This card owns the `0.0.12` version bump

Unlike [`spec-036`][spec-036] (which shared `0.0.11` with the sibling
[`Upload`][glossary-upload-scalar] card [`spec-037`][spec-037] and so deferred to the
joint cut), **`038` is the lone `0.0.12` card.** [`docs/SPECS/NEXT.md`][next] Step 3
scopes "multiple cards share the patch" to a shared version cut; no other WIP / To-Do
card targets `0.0.12` (`039` / `040` are `0.0.13`), so the deferral condition is not
met. Leaving the version at `0.0.11` after `038` ships would make the docs and
exports claim `0.0.12` behavior under a `0.0.11` identity, and nobody would bump it.
Slice 5 therefore aligns every surface that carries the version — exactly as
[`spec-037`][spec-037] Decision 10 owned the final `0.0.11` cut. There are three, not
five: the release is **single-sourced** in `__version__`
([`AGENTS.md`][agents] #"The release is single-sourced"), so
[`pyproject.toml`][pyproject] carries no `version` literal at all
(`[tool.hatch.version]` derives its packaging metadata from `__init__.py`) and
`uv.lock` records the package as `source = { editable = "." }` with no version key.

- `__version__` in [`__init__.py`][init]
- [`tests/base/test_init.py::test_version`][test-base-init]
- the [`docs/GLOSSARY.md`][glossary] package-version line

Rationale companion — this Decision's justification and its two rejected
alternatives: [Decision 14][rationale-d14].

## Implementation plan

Five slices. Slices 1–3 are package-internal and staged; Slice 4 is the live
products form surface; Slice 5 is doc + version-cut only. Line deltas are planning
estimates.

| Slice | Files touched | New / changed tests | Approx. delta |
| --- | --- | --- | --- |
| 1 — form-field converter + reverse map + the two form-derived inputs | [`forms/converter.py`][forms-converter] (new; `convert_form_field` fail-loud dispatch + the four `kind` constants, re-exported from [`utils/inputs.py`][utils-inputs]), [`forms/inputs.py`][forms-inputs] (new; `<FormClass>Input` + `<FormClass>PartialInput` from `base_fields`, the per-field [`utils/inputs.py`][utils-inputs]`::InputFieldSpec` reverse-map record, shape identity, narrowing + create-required guards, `get_form_fields()`), [`forms/__init__.py`][forms-init] (new) | [`tests/forms/test_converter.py`][test-forms] + [`tests/forms/test_inputs.py`][test-forms] (~36 — every form-field class, id mapping, `Upload`, the reverse-map + `kind` flag, custom-field raise, `base_fields` discovery, the create + partial input shapes, shape-identity collision/dedupe, `Meta.fields`/`exclude` fail-loud + empty-set + create-required guard) | `+420 / 0` |
| 2 — the two base classes + `Meta` validation + bind seams | [`forms/sets.py`][forms-sets] (new; the form bases + a `make_declaration_registry` shared helper both registries instantiate), [`mutations/sets.py`][mutations-sets] (refactor validation into the overridable `_validate_meta`; add the `build_input` / `input_type_name` / `input_module_path` / `resolve_sync` / `resolve_async` seams, all model-defaulted; adopt the `make_declaration_registry` helper for its own quad), [`mutations/inputs.py`][mutations-inputs] (`build_payload_type(mutation_name, *, object_type: type | None, object_slot: str | None = None)` emits the model-less `{ ok errors }` plain-form payload from ONE builder + ONE materialize ledger per Decision 6 — `object_type` is keyword-required with no default, and the bind selects the model-less shape by passing a `resolve_object_type` returning `None`; the model branch byte-unchanged), [`types/finalizer.py`][types-finalizer] (wire `bind_form_mutations()` into phase 2.5), THREE form clear rows announced by their owning modules via `register_subsystem_clear` and drained by [`registry.py`][registry]'s `iter_subsystem_clears()`: `clear_form_input_namespace` + `clear_form_mutation_registry` + `clear_form_shape_build_cache`, [`__init__.py`][init] (two exports) | [`tests/forms/test_sets.py`][test-forms] + [`tests/mutations/test_sets.py`][test-mutations] extend (~20 — `Meta` matrix incl. `delete`-rejected + `form_class`-accepted, both bind paths, no-primary error, model-flavor seam defaults unchanged) | `+340 / -30` |
| 3 — form relation decoder + resolver pipeline + field-factory generalization | [`forms/resolvers.py`][forms-resolvers] (new; the visibility-on-every-branch form relation decoder + the `kind`-split decode + the partial-update reconstruction + the sync/async pipeline entries), [`mutations/resolvers.py`][mutations-resolvers] (the reused pipeline helpers are public and importable, so `forms/` reuses by call, not by re-implementation: `locate_instance` / `coerce_lookup_id` / `authorize_or_raise` / `refetch_optimized` / `build_payload` / `not_found_error` / `save_or_field_errors` (wrapping a zero-arg save callable) live here, `validation_error_to_field_errors` in [`utils/errors.py`][utils-errors] and `raw_choice_value` in [`utils/write_values.py`][utils-write-values]; `authorize_or_raise` denial message falls back to the mutation class name when `_primary_type is None`), [`forms/sets.py`][forms-sets] (fill the four `resolve_*` stubs to delegate to `forms/resolvers.py`; add the `get_form_kwargs` / `get_form` construction hooks on both bases + `perform_mutate` / `check_permission` on the plain base; wire the `guard_required` create-required waiver; extend `_cached_build_form_input` to return `(input_cls, field_specs)` and stash `_input_field_specs` at bind for the decode reverse map), [`mutations/fields.py`][mutations-fields] (generalize the target check (duck-typed `_has_mutation_protocol`, no `issubclass(DjangoMutation)` / no form-base import) **and** the `_resolve` dispatch (call `mutation_cls.resolve_sync` / `resolve_async`, `id`-gate on `operation != "form"`) **and** the `data:` lazy-ref derivation (consult `input_type_name` / `input_module_path`; payload-return ref stays `mutations.inputs`); delete the transient `_input_type_name` twin — [Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)), [`mutations/sets.py`][mutations-sets] / [`mutations/permissions.py`][mutations-permissions] / [`relay.py`][relay] (docstring-only `::OldName` rename-sweep refs from the helper promotion, per the AGENTS.md symbol-rename mandate) | [`tests/forms/test_resolvers.py`][test-forms] + [`tests/mutations/test_fields.py`][test-mutations] extend (~46 — create/update, decode `data=`/`files=` split, relation visibility on Relay **and** raw-pk single+multi, `to_field_name`, `IntegrityError` envelope, `get_form_kwargs`/`get_form` hooks, partial-update preservation + required-extra rule, envelope + `"__all__"`, plain-form `ok`+`errors`, visibility locate, write-auth, sync+async, G2 plan-shape, model-flavor dispatch unchanged) + the `::OldName` call-site/docstring rename sweep in [`tests/mutations/test_resolvers.py`][test-mutations] / `test_permissions.py` / [`test_products_api.py`][test-products-api] | `+660 / -30` |
| 4 — products live form surface | `examples/fakeshop/apps/products/forms.py` (new; + a minimal file column/migration if needed for the multipart test), [`products/schema.py`][products-schema] (form mutations), [`test_products_api.py`][test-products-api] | live create/update via `ModelForm`, `categoryId`-through-form, partial-update preservation, `form.errors` envelope, write-auth, **a raw multipart `Upload` test**, plain-form success + validation | `+220 / -0` |
| 5 — docs + `0.0.12` version cut + card wrap | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`README.md`][readme], [`GOAL.md`][goal], [`TODAY.md`][today], [`docs/TREE.md`][tree], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban], version files | `test_version` → `0.0.12` | `+120 / -50` |

Total expected delta: ~`+1740 / -90` — an L cut, matching the card's relative size.
The `036`-surface generalization (the `mutations/sets.py` / `mutations/fields.py`
seams + the `types/finalizer.py` wiring) is a real, named part of that delta — not the
"single additive target-check edit" an earlier draft budgeted; it is justified because
the seams default to today's model behavior (no model-flavor regression) **and** are
the same extension points the `0.0.13` [`SerializerMutation`][glossary-serializermutation]
flavor is designed to reuse. Staged-but-not-implemented seams follow the [`AGENTS.md`][agents]
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
  `form.errors[NON_FIELD_ERRORS]`, mapped to the `"__all__"` sentinel `036` defined —
  the same key a model-driven multi-field-constraint `ValidationError` uses, so the
  client contract is identical across flavors.
- **`update` partial-update preservation.** The resolver reconstructs the full
  bound payload from the located row's values over the form's **full declared** field
  set, overlaid by the provided fields, with `files = provided_files`, before
  `form_class(data=, files=, instance=<row located via get_queryset>)` — in **three**
  shapes, so an omitted field binds exactly as a provided one decodes to
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
  So a `name`-only update preserves the unprovided scalar (`description`), the FK
  (`category`, as its current pk), the M2M (`genres`, as the current pk list), and any
  file field (omitted → kept via the bound form's `initial`); a provided **non-file**
  optional field the consumer wants emptied is sent explicitly (e.g. `""` for a
  `CharField`). A hidden row is not-found before the form runs.
- **File / image form fields run live in this card; CLEARING is out of scope.**
  `forms.FileField` / `forms.ImageField` map to the
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
  (through the shared [`utils/write_values.py`][utils-write-values]`::raw_choice_value`).
- **Relation visibility is not delegated to the form's queryset.** A
  `ModelChoiceField`'s default queryset is `Category.objects.all()` (not
  request-scoped), so the decode type- and visibility-checks the id through the
  related primary `DjangoType.get_queryset` **before** the form sees it; a hidden /
  unseeable target is a field-keyed `FieldError`, identical to the model-mutation
  path. The form's own queryset remains a secondary guard
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- **A `ModelForm` placed on the plain `DjangoFormMutation` base.** Rejected at
  class creation with a [`ConfigurationError`][glossary-configurationerror] naming
  `DjangoModelFormMutation`. `forms.ModelForm` is **not** a `forms.Form` subclass (a
  sibling under `forms.BaseForm`), so the plain base checks
  `issubclass(form_class, forms.ModelForm)` **first** to emit the targeted message —
  otherwise a `ModelForm` would silently write with no object slot / no
  `DjangoModelPermission` default / no optimizer re-fetch
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)).
- **A required extra (non-model) `ModelForm` field on `update`.** It has no
  instance value to reconstruct, so it keeps its `field.required` in the partial
  input (the caller must supply it); an optional extra field may be omitted
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
- **A relation field with `to_field_name`.** A `ModelChoiceField` /
  `ModelMultipleChoiceField` whose `to_field_name` (or backing `ForeignKey(to_field=…)`)
  looks the object up by a non-pk field: after the visibility query resolves the
  object, the decoder feeds the form `obj.serializable_value(field.to_field_name)`
  (else `obj.pk`), so a valid GraphQL id does not fail form validation
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- **A form whose `__init__` requires constructor kwargs.** Schema-time discovery
  reads `form_class.base_fields` (no instantiation), and runtime construction goes
  through `get_form_kwargs(info, *, data, files, instance=None)` — the consumer
  overrides it to inject `user` / `request` / tenant, or to pass the request-scoped
  queryset a form narrows a `ModelChoiceField` with in its own `__init__` — the hook
  returns constructor kwargs, so the form applies it — without changing the generated
  input shape
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
- **A narrowing that drops a required form field.** Two guards keyed on one waiver
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)): a **create**
  narrowing that drops any required form field is rejected at class creation with a
  [`ConfigurationError`][glossary-configurationerror] naming the missing field(s) — a
  bound form cannot succeed without it and `initial` is no substitute; an **update**
  narrowing that drops a required **column-less** field is rejected at bind for the
  same reason, since the reconstruction can only supply model-backed fields. Both are
  waived when `get_form_kwargs` / `get_form` is overridden to supply the values.
- **Write-time `IntegrityError`.** A valid `form.save()` (or the plain-form
  `perform_mutate` save) that loses a concurrent-uniqueness race or hits a residual DB
  constraint returns the null-object + `FieldError` envelope via the `036`
  `save_or_field_errors` mapper — never a top-level `GraphQLError`
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
- **Two distinct generated form inputs colliding on one GraphQL name.** Two
  **different** form classes with the same `__name__` both emit `<__name__>Input` and
  **always** raise a finalize-time [`ConfigurationError`][glossary-configurationerror]
  (distinct `form_class` identities never dedupe — the reused
  `materialize_generated_input_class` ledger raise); only repeats of the **same**
  `(form_class, operation kind, effective set)` dedupe to one materialized class, and
  two different narrowings of one form get distinct shape-derived names
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
- **Plain-form write authorization.** With no model, the
  [`DjangoModelPermission`][glossary-djangomodelpermission] default cannot apply, so an
  unset `Meta.permission_classes` resolves to `(DenyAll,)` — deny by default, with a
  public write the explicit `Meta.permission_classes = []` opt-in. An entry that is a
  [`DjangoModelPermission`][glossary-djangomodelpermission] subclass is **rejected** at
  class creation, since it resolves its codename from a model a model-less mutation
  never supplies ([Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form)).
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
  (not via model `setattr` — proving the reverse map); **partial-update
  preservation** — a `name`-only `updateItemViaForm` preserves `description` and
  `category` (FK), and `unique_item_per_category` still fires when only `name` changes
  to a value already taken under the unchanged `category` (the partial-update
  contract); a non-colliding partial update; write authorization (anonymous denied, a
  caller missing the model perm denied, a permitted caller succeeds); the
  visibility-scoped `update` (a caller who cannot see a private `Item` gets
  not-found); **relation visibility** — a permitted writer submitting a **hidden**
  `Category` `GlobalID` as `categoryId` gets the same field-keyed `FieldError` the
  model-driven mutation returns (the `036` relation-visibility invariant, proving the form's
  default `Category.objects.all()` queryset is not the only guard); **a raw
  `django.test.Client` multipart upload** to a form-backed `Upload` field, proving the
  `data=` / `files=` split validates and writes the file (the file-routing contract
  — owned here, not deferred); **a `get_form_kwargs` override injecting `user`** drives
  a form whose `__init__` requires it (the construction-hook migration case); and
  the plain `Form` mutation's **success** (`ok: true`, empty `errors`) **and**
  validation-failure (`ok: false`, field-keyed `errors`) shapes. **Write-time
  `IntegrityError`** — a valid `ModelForm.save()` that loses a concurrent-uniqueness
  race surfaces the **`FieldError` envelope**, not a top-level GraphQL error.
- **Package-internal** ([`tests/forms/`][test-forms]):
  - `test_converter.py` — each supported form-field class → annotation +
    required-ness; `ModelChoiceField` / `ModelMultipleChoiceField` id mapping
    (Relay-`GlobalID` vs raw pk); `forms.FileField` → [`Upload`][glossary-upload-scalar];
    **the [`utils/inputs.py`][utils-inputs]`::InputFieldSpec` reverse-map record**
    (`category_id` / `categoryId` → `category` / `relation_single`; a `file`-kind flag for an
    `Upload` field); field discovery from **`form_class.base_fields`** (a form whose
    `__init__` requires kwargs still yields a shape); and **the fail-loud dispatch:
    a bare `forms.Field` → `str`, a known subclass (`EmailField`) maps, but a
    custom `class CustomField(forms.Field)` raises [`ConfigurationError`][glossary-configurationerror]**
    (the catch-all-shadowing regression test).
  - `test_inputs.py` — the **two generated inputs** (`<FormClass>Input` with
    `field.required` requiredness for create; `<FormClass>PartialInput` — model-backed
    fields optional, **a required non-model extra field still required**); fields
    from `form_class.base_fields` (no instantiation; an overridable `get_form_fields()`
    honored), narrowed by `Meta.fields` / `Meta.exclude`; materialization as
    a module global; a form-only (non-model) field included. **Shape identity:**
    the same form with two different `Meta.fields` narrowings → two **distinct**
    generated names; two repeats of the **same** `(form_class, op, effective set)` →
    **dedupe** (one materialized class); two **different** form classes with the
    **same `__name__`** → a finalize-time [`ConfigurationError`][glossary-configurationerror]
    collision **always** (distinct `form_class` identities never dedupe, even with
    matching field shapes); an **empty effective field set** → `ConfigurationError`.
  - `test_sets.py` — the `Meta` validation matrix (missing `form_class`; a `ModelForm`
    on **`DjangoFormMutation`** rejected naming `DjangoModelFormMutation`; a
    non-`ModelForm` on `DjangoModelFormMutation` rejected; `ModelForm`-with-no-model;
    `DjangoModelFormMutation` `operation = "delete"` rejected; **any `Meta.operation`
    on the plain base rejected**; **a `create` narrowing (`Meta.fields` *or*
    `Meta.exclude`) that drops a required form field → `ConfigurationError` naming the
    missing field(s), waived when `get_form_kwargs` is overridden**;
    **`Meta.fields` bare-string / duplicate-name / unknown-name against
    `form.base_fields`**; `fields` + `exclude` both set; unknown key); **plain-form
    input dedupe via the `"form"` sentinel**; registration; phase-2.5 binding (both
    paths); the no-registered-primary-type error for `DjangoModelFormMutation`.
  - `test_resolvers.py` — create / update happy paths; `form.is_valid()` failure →
    envelope (null object), incl. a `NON_FIELD_ERRORS` `clean()` error → `"__all__"`;
    **the decode split** — `categoryId` → `{"category": pk}` in `data=`, an `Upload`
    → `files=` (never `data=`); **relation visibility on EVERY branch** — a hidden
    target → field-keyed `FieldError` before the form, for **both** a Relay-`GlobalID`
    primary AND a **non-Relay raw-pk** primary, and for **both** `ModelChoiceField` and
    `ModelMultipleChoiceField` (the raw-pk branch the `036` helper left unscoped); **a raw-pk /
    wrong-model relation id** → `FieldError`; **`to_field_name`** — a `ModelChoiceField`
    / `ModelMultipleChoiceField` with `to_field_name` set validates the decoded value
    by the target field, not pk; **write-time `IntegrityError`** — a valid
    `form.save()` raising `IntegrityError` (and the plain-form `perform_mutate` save
    path) → `FieldError` envelope, not a top-level error (via `save_or_field_errors`);
    **the `get_form_kwargs` / `get_form` hook** — an override injecting `user` and one
    scoping a `ModelChoiceField.queryset` (input shape unchanged); **partial-update
    reconstruction at the unit tier** — omitted scalar / FK / M2M preserved from the
    located instance, omitted file preserved via the bound form's `initial`, a
    **required extra non-model field omitted → required error** while an optional one
    may be omitted), and `unique_item_per_category` validating on a one-field
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

Each slice owns its doc edits. [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" requires `CHANGELOG.md` edits to be explicitly
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
  → [`FieldError`][glossary-fielderror-envelope] mapping, the `036` reuse). **The
  `DjangoFormMutation` entry must state the sibling shape, not a `DjangoMutation`
  subclass returning the post-save object**
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)):
  only `DjangoModelFormMutation` subclasses `DjangoMutation` (returns the post-save
  object in the uniform `node` / `result` slot), while the plain `DjangoFormMutation`
  is a model-less sibling accepted by the generalized mutation-field family, returning
  the pinned `ok: Boolean!` + `errors: [FieldError!]!` payload (no object slot). Add
  both symbols to **Public exports**, the **Index** (status column), and the
  **Mutations** browse-by-category row; move the package-version line to `0.0.12`.
- **Slice 5 — package docs**: [`docs/README.md`][docs-readme] / [`README.md`][readme]
  list form mutations as shipped rather than upcoming and move the
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
- **Slice 5 — card wrap**: [`KANBAN.md`][kanban] carries the card in Done as
  [`DONE-038-0.0.12`][kanban], its `SpecDoc` pointing at the canonical card spec (a
  `SpecDoc` DB edit re-rendered via `scripts/build_kanban_md.py`, never a hand-edit).

## Risks and open questions

Every question this card opened is answered by a Decision above. The
deliberation that answered them — each question's preferred answer for the
`0.0.12` cut, its fallback if implementation proved the preferred answer
wrong, and the two card-citation tensions the cut chose to record rather than
silently reconcile — is recorded in the rationale companion under
[Risks and open questions][rationale-risks].

## Out of scope (explicitly tracked elsewhere)

- **DRF serializer mutations** ([`SerializerMutation`][glossary-serializermutation])
  — the `0.0.13` sibling flavor, landing as
  [`django_strawberry_framework/rest_framework/`][rest-framework-package]; it reuses the
  same [`FieldError` envelope][glossary-fielderror-envelope] and a serializer-field
  converter, not this card's form converter.
- **Auth mutations** ([Auth mutations][glossary-auth-mutations]) — the `0.0.13`
  sibling flavor, landing as
  [`django_strawberry_framework/auth/mutations.py`][auth-mutations]. It becomes the
  **third** `make_declaration_registry` consumer, which is live evidence for
  Decision 13's shared-mechanics / disjoint-ledgers call.
- **The ergonomic `TestClient` / `AsyncTestClient` helper** —
  [`TestClient`][glossary-testclient], landing in `0.0.14` as
  [`django_strawberry_framework/testing/`][testing-package]. **File-field
  correctness is NOT deferred:** this card owns the `forms.FileField` /
  `forms.ImageField` → [`Upload`][glossary-upload-scalar] typing **and** the runtime
  `data=` / `files=` decode split + `form_class(data=, files=, instance=)`
  construction, proven by a raw `django.test.Client` multipart live test (Slice 4,
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
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
   supported form-field class → its Strawberry annotation + required-ness — including
   `JSONField` → `strawberry.scalars.JSON` on its own row, and the three-case
   `NullBooleanField` requiredness rule single-sited in `form_field_required` — reusing
   the read-side [scalar][glossary-scalar-field-conversion] /
   [choice-enum][glossary-choice-enum-generation] /
   [`Upload`][glossary-upload-scalar] converters where overlapping) with a **fail-loud
   dispatch — no base-`forms.Field` catch-all**: a bare `forms.Field` → `str` (exact
   special case), a known subclass maps via MRO, but a custom `forms.Field` subclass
   hits the **raising** default → [`ConfigurationError`][glossary-configurationerror]
   — plus the four `kind` constants it re-exports from
   [`utils/inputs.py`][utils-inputs] and does not itself define.
   [`forms/inputs.py`][forms-inputs] records, per generated input field, the shared
   [`utils/inputs.py`][utils-inputs]`::InputFieldSpec` the resolver consults at decode
   (`category_id` / `categoryId` → `category` / `relation_single`; an `Upload` field
   flagged `file`), and builds **both** the form-derived `<FormClass>Input`
   (create, `field.required` requiredness) and `<FormClass>PartialInput` (update;
   model-backed fields optional, **a required non-model extra field still required**)
   from **`form_class.base_fields`** (no instantiation — kwarg-requiring forms work;
   overridable `get_form_fields()`), under the `036`-parallel **shape identity**
   `(form_class, operation kind, effective field set, field-discovery hook
   discriminator)` — the operation component is the
   `DjangoModelFormMutation` verb or the plain `"form"` sentinel, and the fourth
   component is `None` unless the mutation overrides `get_form_fields` — with canonical /
   shape-derived names, dedupe, and a finalize-time **collision
   [`ConfigurationError`][glossary-configurationerror]** for two distinct shapes on one
   name (incl. different forms sharing a `__name__`, which always collide);
   `Meta.fields` / `Meta.exclude` are normalized + fail-loud against
   `form_class.base_fields` (bare string / duplicate / unknown name / empty set →
   `ConfigurationError`), and a narrowing that drops a required form field
   **raises** — any required field on `create`, a required **column-less** field on
   `update` — unless `get_form_kwargs` / `get_form` is overridden; all materialized as module
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
   `Meta.operation`** and uses the `"form"` shape sentinel; `form_class` a known
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

4. [`forms/resolvers.py`][forms-resolvers] runs the locate → authorize → decode →
   `is_valid()` → write → re-fetch → payload pipeline (sync + async, one
   `transaction.atomic()` / one `sync_to_async(thread_sensitive=True)`), **authorizing
   before the decode** so an unauthorized caller cannot probe relation visibility.
   Decode produces a **form-field-keyed** `provided_data` over the shared
   `decode_visible_relation` spine: every relation id — `GlobalID`
   *or* **raw pk** — is type-checked, resolved to the **visible** object through the
   related primary `DjangoType.get_queryset` (both branches, closing the raw-pk
   visibility gap), and converted by `to_field_name`
   (`obj.serializable_value(field.to_field_name)` else
   `obj.pk`) before landing under the form field name; a hidden target → field-keyed
   `FieldError` + a **separate `provided_files`** (uploaded `Upload` values, never in
   `data=`); construction goes through the overridable `get_form_kwargs(info, *, data,
   files, instance=None)` hook — `create` builds `form_class(**get_form_kwargs(…,
   data=provided_data, files=provided_files))`, `update` reconstructs the **full partial
   payload** from the located row over the form's full declared field set, overlaid by
   `provided_data` and in the three shapes a provided field decodes to, with
   `files = provided_files`, then `form_class(**get_form_kwargs(…, instance=<located
   row>))` — so omitted scalar / FK / M2M / file values are preserved and
   `unique_item_per_category` validates on a one-field change. `form.errors` maps
   onto the [`FieldError` envelope][glossary-fielderror-envelope] (`NON_FIELD_ERRORS` →
   `"__all__"`, via the reused `validation_error_to_field_errors(ValidationError(
   form.errors.as_data()))`); **the write is wrapped by the `036` `save_or_field_errors`
   `IntegrityError` → envelope mapper** (no top-level error on a save-time race);
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
   / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
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
   `django.test.Client` multipart upload to a form-backed `Upload` field** (the
   file-routing contract, owned here), **a write-time `IntegrityError` returning the
   `FieldError` envelope**, **a `get_form_kwargs` override injecting `user`** for a
   kwarg-requiring form, and the plain `Form` mutation's **success** (`ok: true`)
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
   ([Decision 14](#decision-14--this-card-owns-the-0012-version-bump)): `__version__`
   in [`__init__.py`][init], [`tests/base/test_init.py::test_version`][test-base-init]
   and the [`docs/GLOSSARY.md`][glossary] package-version line align on `0.0.12`.
   [`pyproject.toml`][pyproject] and `uv.lock` carry no version literal to align —
   the release is single-sourced in `__version__`. The two net-new public symbols
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
[rationale-d10]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-10--operations-create--update-for-the-modelform-no-form-delete
[rationale-d11]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form
[rationale-d12]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation
[rationale-d13]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change
[rationale-d14]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-14--this-card-owns-the-0012-version-bump
[rationale-d1]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d2]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-2--card-scope-boundary-the-two-form-flavors-ship-serializer--auth-stay-out-the-frozen-036-contracts-are-reused-unchanged
[rationale-d3]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-3--class-meta-surface-not-graphenes-mutationoptions
[rationale-d4]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-4--module-and-test-locations-forms-subpackage-mirroring-mutations
[rationale-d5]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root
[rationale-d6]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling
[rationale-d7]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth
[rationale-d8]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload
[rationale-d9]: appx/spec-038-form_mutations-0_0_12-rationale.md#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path
[rationale-risks]: appx/spec-038-form_mutations-0_0_12-rationale.md#risks-and-open-questions
[spec-010]: spec-010-foundation-0_0_4.md
[spec-027]: spec-027-filters-0_0_8.md
[spec-028]: spec-028-orders-0_0_8.md
[spec-034]: spec-034-permissions-0_0_10.md
[spec-035]: spec-035-optimizer_hardening-0_0_10.md
[spec-036]: spec-036-mutations-0_0_11.md
[spec-037]: spec-037-upload_file_image_mapping-0_0_11.md
[spec-038-rationale]: appx/spec-038-form_mutations-0_0_12-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[init]: ../../django_strawberry_framework/__init__.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-operations]: ../../django_strawberry_framework/mutations/operations.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[relay]: ../../django_strawberry_framework/relay.py
[rest-framework-package]: ../../django_strawberry_framework/rest_framework/
[testing-package]: ../../django_strawberry_framework/testing/
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-errors]: ../../django_strawberry_framework/utils/errors.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-write-transaction]: ../../django_strawberry_framework/utils/write_transaction.py
[utils-write-values]: ../../django_strawberry_framework/utils/write_values.py

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

<!-- External -->
[upstream-forms-converter]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/converter.py
[upstream-forms-mutation]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/mutation.py
[upstream-forms-types]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/types.py
