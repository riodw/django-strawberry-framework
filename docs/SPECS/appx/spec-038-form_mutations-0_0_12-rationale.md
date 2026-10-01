# Rationale companion: spec-038 (Form-based mutations — `DjangoFormMutation` / `DjangoModelFormMutation`)

Companion to [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038]. It
carries the reasons behind that spec's contract: each Decision's justification,
the alternatives it rejected and why, and the risk / open-question reasoning
behind the design. The spec carries the contract; this file carries why the code
is shaped that way.

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-038-d1].

### Justification

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in
  [`docs/SPECS/NEXT.md`][next] bakes the card's NNN (`038`) and target patch
  (`0_0_12`) into the filename.
- The topic slug is `form_mutations` — short, snake-case, and naming the subsystem.

### Alternatives considered (and rejected)

- **An unstructured `docs/spec-form_mutations.md`.** Rejected: the structured
  filename is the convention every spec follows.
- **Topic slug `forms` / `modelform`.** Rejected: `forms` collides conceptually
  with the Django `forms` module name, and `modelform` undersells the plain-`Form`
  half.

## Decision 2 — Card-scope boundary: the two form flavors ship; serializer / auth stay out; the frozen `036` contracts are reused unchanged

Spec: [Decision 2 — Card-scope boundary: the two form flavors ship; serializer / auth stay out; the frozen `036` contracts are reused unchanged][spec-038-d2].

### Justification

The serializer and auth flavors are separate subsystems with their own specs; folding
either into the form flavor would bloat it exactly as [`START.md`][start]'s
scope-creep rule warns. The foundation exists in `036`; the form flavor's job is the
form-specific generation + pipeline on top of it.

### Alternatives considered (and rejected)

- **One subsystem for the serializer and form flavors.** Rejected:
  [`SerializerMutation`][glossary-serializermutation] carries a soft DRF dependency
  and a serializer-field converter; the form flavor's Django-core `Form` dependency
  is unconditional.
- **Extend the `036` `FieldError` with form metadata.** Rejected: one envelope across
  every flavor is the contract; a form-specific fork would break it for the sibling
  flavors that depend on it.

## Decision 3 — `class Meta` surface, not graphene's `MutationOptions`

Spec: [Decision 3 — `class Meta` surface, not graphene's `MutationOptions`][spec-038-d3].

### Justification

This is the package's defining surface contract ([`START.md`][start] "Meta classes
on every consumer surface"). The [`spec-036`][spec-036]
[`DjangoMutation`][glossary-djangomutation] base established the nested-`Meta`
mutation shape; the form flavor is uniform with it. The *capabilities* of
graphene-django's form mutations are borrowed at the outcome level; the
`MutationOptions` mechanism is not.

### Alternatives considered (and rejected)

- **graphene's `__init_subclass_with_meta__` keyword options.** Rejected: it is the
  metaclass-options surface the nested `class Meta` replaces; it also fragments the
  declaration shape away from [`DjangoMutation`][glossary-djangomutation].
- **A `@django_form_mutation(form_class=...)` decorator.** Rejected: a decorator on
  a consumer class is exactly the shape [`START.md`][start] forbids.

## Decision 4 — Module and test locations: `forms/` subpackage mirroring `mutations/`

Spec: [Decision 4 — Module and test locations: `forms/` subpackage mirroring `mutations/`][spec-038-d4].

### Justification

The [`mutations/`][mutations-sets] subpackage ([`spec-036`][spec-036] Decision 4) is
the proven shape for a `class Meta`-driven write subsystem. A separate `forms/`
subpackage keeps the form-specific generation + pipeline distinct from the
model-driven `mutations/` while sharing its public contracts, and
[`tests/forms/`][test-forms] mirrors it.

### Alternatives considered (and rejected)

- **Fold the form bases into [`mutations/`][mutations-sets].** Rejected: the
  form-field converter is a distinct concern from the model-column generator, and the
  serializer flavor has its own `rest_framework/` subpackage too — one subpackage per
  flavor keeps each extension point separable.
- **A flat `forms.py` module.** Rejected: the surface is a converter + a metaclass +
  a resolver pipeline + input generation — a subpackage matches it.

## Decision 5 — Public surface: `DjangoFormMutation` / `DjangoModelFormMutation` exported from the root

Spec: [Decision 5 — Public surface: `DjangoFormMutation` / `DjangoModelFormMutation` exported from the root][spec-038-d5].

### Justification

Keeping the public surface at two symbols (the two bases) — reusing the field
factory + error type via seams rather than a parallel factory — keeps one exposure
idiom and one error contract, and the same seams serve the serializer flavor. The
audience for both bases is every schema with a form-backed write, so the root export
matches [`DjangoMutation`][glossary-djangomutation]'s placement.

### Alternatives considered (and rejected)

- **A separate `DjangoFormMutationField`.** Rejected: a second exposure idiom for the
  same job once the seams exist.
- **An `issubclass(DjangoMutation)` target check.** Rejected: the plain form is not a
  `DjangoMutation`, and importing the form bases into
  [`mutations/fields.py`][mutations-fields] would close a load cycle; the duck-typed
  protocol check accepts every flavor.
- **Exposing only from `django_strawberry_framework.forms`.** Rejected: the bases are
  used in schema modules alongside root-exported types, exactly as
  [`DjangoMutation`][glossary-djangomutation] is root-exported.

## Decision 6 — Base-class strategy: `DjangoModelFormMutation` rides the `DjangoMutation` base; the plain form is the model-less sibling

Spec: [Decision 6 — Base-class strategy: `DjangoModelFormMutation` rides the `DjangoMutation` base; the plain form is the model-less sibling][spec-038-d6].

### Justification

Subclassing [`DjangoMutation`][glossary-djangomutation] for the `ModelForm` flavor
reuses the model machinery with no new model-pipeline code, through the
[`_resolve_model`][spec-036] seam. The plain-form model-less case is genuinely
different (no model row to return), so a sibling base is the honest shape rather than
bending the model-required base.

### Alternatives considered (and rejected)

- **Make the plain `Form` also subclass [`DjangoMutation`][glossary-djangomutation]
  by relaxing the model requirement (the unified architecture).** Rejected: even
  with the `_validate_meta` seam making the model-requirement overridable, a
  model-less plain form would force model-less branches into *every* model-centric
  step of [`bind_mutations`][mutations-sets] (primary-type resolution,
  `build_payload_type(object_type=primary_type, …)`) and the payload-slot derivation,
  rippling the no-model case through the model-driven path the model + ModelForm
  flavors share. A contained sibling base with its own small registry + bind keeps
  the model-driven bind free of model-less conditionals; the cost — a parallel
  registry + `bind_form_mutations()` + a `finalizer.py` wiring line — is named in
  [Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change).
- **Honor `Meta.return_field_name`.** Rejected: it forks the payload object-field
  name across flavors, the exact collision the `036` uniform slot prevents.
- **Cleaned-data echo** on the plain form — graphene-django's plain
  `DjangoFormMutation` echoes `form.cleaned_data` as output fields (its
  `fields_for_form` is dual-purposed for input *and* output). Rejected because (a)
  `cleaned_data` is heterogeneous and includes values with no clean GraphQL output
  mapping (a `forms.FileField`'s cleaned value is an `UploadedFile`; a
  `ModelChoiceField`'s is a model instance), so a faithful echo would need a second
  output-type generator and ad-hoc per-type rules; (b) a predictable success flag is
  sufficient — a consumer that needs to return data uses a model-backed
  `DjangoModelFormMutation` (which returns the `node` / `result` object); and (c)
  `ok` + `errors` is trivially well-typed for a model-less payload and keeps the
  cross-flavor `errors` envelope identical. The asymmetry mirrors graphene-django's
  split (its `DjangoModelFormMutation` is model-backed; its `DjangoFormMutation` is
  not) — only the model-less *output* shape differs, deliberately.

## Decision 7 — Form-field → Strawberry input mapping: the form is the input source of truth

Spec: [Decision 7 — Form-field → Strawberry input mapping: the form is the input source of truth][spec-038-d7].

### Justification

The form — not the model — is the validation and field contract a form-mutation
consumer chose; a plain `Form` can declare fields with no model column (a
`confirm_email`, a `captcha`), which the model-column `036` generator cannot express.
Deriving from `form_class.base_fields` (the stable class-level field set) is the only
correct source, and it is what graphene-django's `fields_for_form` does. Reusing the
read-side converters where types overlap keeps the wire contract symmetric without
duplicating the scalar table.

### Alternatives considered (and rejected)

- **Derive the input from the model's editable columns (reuse the `036`
  generator).** Rejected: it drops form-only fields and ignores form-level
  `required` overrides — wrong for a plain `Form`, and divergent from the consumer's
  declared form contract for a `ModelForm`.
- **A parallel form-field scalar table independent of the read converters.**
  Rejected: it would let a `choices` form field resolve to a different enum than the
  read side, breaking the symmetric wire contract.
## Decision 8 — Resolver pipeline: instantiate → `is_valid()` → `form.errors` → `save()` → optimizer re-fetch → payload

Spec: [Decision 8 — Resolver pipeline: instantiate → `is_valid()` → `form.errors` → `save()` → optimizer re-fetch → payload][spec-038-d8].

### Justification

`form.is_valid()` / `form.save()` is the Django-native form contract
graphene-django uses; routing `form.errors` into the shared envelope (rather than
raising) keeps one error contract across flavors; reusing the `036` locate /
authorize / transaction / re-fetch steps means the form flavor inherits every
composition `036` proves.

### Alternatives considered (and rejected)

- **Run the model's `full_clean()` in addition to `form.is_valid()`.** Rejected:
  double validation, and a plain `Form` has no model to clean; the form's validation
  is authoritative.
- **A separate per-flavor transaction / async shape.** Rejected: the one-`atomic()`
  / one-`sync_to_async` boundary of the shared runner is the foundation every flavor
  rides.
- **Graphene-style full update** (dropping `PartialInput` and requiring every
  form-required field on update). Rejected for cross-flavor consistency with the
  model-driven `DjangoMutation.update`: the reconstruction from the located instance
  gives partial semantics while the bound `ModelForm` still validates the whole set.
- **`form.save(commit=False)` + explicit `instance.save()` + `form.save_m2m()`.**
  Rejected: for a `ModelForm` with M2M fields, `form.save()` (commit=True) already runs
  `save_m2m()` internally, so a single `form.save()` inside the one
  `transaction.atomic()` is complete.

## Decision 9 — Optimizer composition: the `ModelForm` payload re-fetch rides the `spec-036` G2 path

Spec: [Decision 9 — Optimizer composition: the `ModelForm` payload re-fetch rides the `spec-036` G2 path][spec-038-d9].

### Justification

Reusing the `036` re-fetch is the point of subclassing
[`DjangoMutation`][glossary-djangomutation] — the G2 composition and the
by-pk-without-visibility contract come with it, with no form-specific optimizer code
(the `036` G2 live test covers the [`spec-035`][spec-035] obligation).

### Alternatives considered (and rejected)

- **Return `form.save()`'s instance without re-fetching.** Rejected: a freshly
  saved instance has no related rows loaded, so any relation in the response
  selection N+1s — exactly the failure the `036` re-fetch prevents.

## Decision 10 — Operations: `create` / `update` for the `ModelForm`, no form `delete`

Spec: [Decision 10 — Operations: `create` / `update` for the `ModelForm`, no form `delete`][spec-038-d10].

### Justification

Matching the upstream operation set keeps the parity surface honest; a form `delete`
would be a new contract with no graphene-django precedent and a redundant overlap with
the model-driven `delete`.

### Alternatives considered (and rejected)

- **Add a form `delete`.** Rejected: no upstream precedent, and the model-driven
  `delete` is the existing path.

## Decision 11 — Write authorization: reuse the `036` seam (`DjangoModelPermission` for the `ModelForm`, explicit classes for the plain form)

Spec: [Decision 11 — Write authorization: reuse the `036` seam (`DjangoModelPermission` for the `ModelForm`, explicit classes for the plain form)][spec-038-d11].

### Justification

The `ModelForm` flavor gets the `036` write-auth seam through `_resolve_model`, and
the plain-form case keeps the safe-by-default stance `036` established (`DenyAll`
when `permission_classes` is unset) rather than silently shipping an unauthenticated
write surface; a public plain form is the explicit `Meta.permission_classes = []`.

### Alternatives considered (and rejected)

- **A new form-specific permission class.** Rejected: the `036` seam covers the
  `ModelForm` flavor, and a plain form's authorization is a consumer choice, not a
  model-permission one.
- **A permissive `AllowAny`-style default for the plain form.** Rejected: it would
  ship every unconfigured plain form as an open write surface; the explicit `[]` is
  one line.

## Decision 12 — Live coverage: products grows a `ModelForm` and a plain `Form` mutation

Spec: [Decision 12 — Live coverage: products grows a `ModelForm` and a plain `Form` mutation][spec-038-d12].

### Justification

The [`AGENTS.md`][agents] live-HTTP-priority rule makes the products write surface
the right home for form-mutation acceptance coverage; products has the `Item`
constraint and the `036` `Mutation` wiring, so the form surface is an extension, not
a new app.

### Alternatives considered (and rejected)

- **Synthetic-model-only coverage (no live surface).** Rejected: form mutations are
  live-reachable once products exposes them, and the [`AGENTS.md`][agents] rule
  prioritizes the live `/graphql/` test where a realistic request reaches the path.

## Decision 13 — Finalization seam: reuse the mutation phase-2.5 bind, no `DEFERRED_META_KEYS` change

Spec: [Decision 13 — Finalization seam: reuse the mutation phase-2.5 bind, no `DEFERRED_META_KEYS` change][spec-038-d13].

### Justification

The `ModelForm` flavor reuses the one finalization gate via the `build_input` seam
(the materialize-before-`Schema` discipline [`spec-027`][spec-027] /
[`spec-028`][spec-028] / `036` share); the plain form's own registry +
`bind_form_mutations()` is the contained cost of keeping the model-driven bind free
of model-less branches
([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)).
Leaving `DEFERRED_META_KEYS` untouched honors the cross-subsystem invariant.

### Alternatives considered (and rejected)

- **A separate public `finalize_django_forms()` entry point.** Rejected: a second
  gate the consumer must remember to call; `bind_form_mutations()` hangs off the
  `finalize_django_types()` phase-2.5 window instead.
- **One merged declaration ledger for both registries.** Rejected: the two are
  different declaration namespaces with different binds; only the mechanics are
  shared (`make_declaration_registry`).

## Decision 14 — This card owns the `0.0.12` version bump

Spec: [Decision 14 — This card owns the `0.0.12` version bump][spec-038-d14].

### Justification

The release is single-sourced in `__version__`, so a version line is one literal and
needs no per-file alignment.

## Risks and open questions

- **The plain-`Form` payload shape (model-less).** Fixed at `ok: Boolean!` +
  `errors: [FieldError!]!` with the `perform_mutate(self, form, info) -> None` hook
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling));
  the rejected cleaned-data echo is under Decision 6.
- **Partial update for an exotic form.** The reconstruction supplies model-backed
  fields only; a required column-less field stays required in the partial input and a
  narrowing that drops one is rejected at bind
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
  A stored value that no longer satisfies a tightened validator blocks the update
  until the caller supplies a valid replacement — the reconstructed form revalidates
  every declared field and never silently excludes an untouched one.
- **Relation visibility is not the form's queryset.** A default `ModelChoiceField`
  queryset is not request-scoped, so the decode resolves every relation id (Relay and
  raw pk, single and multi) through the related primary `get_queryset` before the
  form ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth));
  the form's own queryset is a secondary guard.
- **`Meta.return_field_name`.** graphene-django lets a `ModelForm` mutation name its
  output field; [`spec-036`][spec-036] Decision 7 fixes the uniform `node` / `result`
  payload slot to keep one cross-flavor client contract and dodge model-name
  collisions. The form flavor keeps the uniform slot and does not adopt
  `Meta.return_field_name`; a migrating consumer reads `node` / `result` instead of the
  graphene field name.
- **File clearing.** Only upload + preserve are supported: a nullable `Upload` gives
  the resolver no clear signal (omitting means preserve), and Django's
  `ClearableFileInput` clear is a false sentinel, not an uploaded value.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary-djangomutation]: ../../GLOSSARY.md#djangomutation
[glossary-serializermutation]: ../../GLOSSARY.md#serializermutation

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-027]: ../spec-027-filters-0_0_8.md
[spec-028]: ../spec-028-orders-0_0_8.md
[spec-035]: ../spec-035-optimizer_hardening-0_0_10.md
[spec-036]: ../spec-036-mutations-0_0_11.md
[spec-038-d10]: ../spec-038-form_mutations-0_0_12.md#decision-10--operations-create--update-for-the-modelform-no-form-delete
[spec-038-d11]: ../spec-038-form_mutations-0_0_12.md#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form
[spec-038-d12]: ../spec-038-form_mutations-0_0_12.md#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation
[spec-038-d13]: ../spec-038-form_mutations-0_0_12.md#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change
[spec-038-d14]: ../spec-038-form_mutations-0_0_12.md#decision-14--this-card-owns-the-0012-version-bump
[spec-038-d1]: ../spec-038-form_mutations-0_0_12.md#decision-1--spec-filename-and-canonical-naming
[spec-038-d2]: ../spec-038-form_mutations-0_0_12.md#decision-2--card-scope-boundary-the-two-form-flavors-ship-serializer--auth-stay-out-the-frozen-036-contracts-are-reused-unchanged
[spec-038-d3]: ../spec-038-form_mutations-0_0_12.md#decision-3--class-meta-surface-not-graphenes-mutationoptions
[spec-038-d4]: ../spec-038-form_mutations-0_0_12.md#decision-4--module-and-test-locations-forms-subpackage-mirroring-mutations
[spec-038-d5]: ../spec-038-form_mutations-0_0_12.md#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root
[spec-038-d6]: ../spec-038-form_mutations-0_0_12.md#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling
[spec-038-d7]: ../spec-038-form_mutations-0_0_12.md#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth
[spec-038-d8]: ../spec-038-form_mutations-0_0_12.md#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload
[spec-038-d9]: ../spec-038-form_mutations-0_0_12.md#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path
[spec-038]: ../spec-038-form_mutations-0_0_12.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[mutations-fields]: ../../../django_strawberry_framework/mutations/fields.py
[mutations-sets]: ../../../django_strawberry_framework/mutations/sets.py

<!-- tests/ -->
[test-forms]: ../../../tests/forms/

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
