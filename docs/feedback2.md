# Review feedback - `spec-038-form_mutations-0_0_12.md`

## Findings

### [P1] Form input type identity is under-specified and will collide across narrowed shapes

The spec now says the form flavor materializes `<FormClass>Input` and `<FormClass>PartialInput` as module globals (`docs/spec-038-form_mutations-0_0_12.md:294`, `docs/spec-038-form_mutations-0_0_12.md:1205`, `docs/spec-038-form_mutations-0_0_12.md:1217`). That name is not enough to identify the generated GraphQL type shape.

Two common cases collide:

- The same `ItemModelForm` used by two mutations with different `Meta.fields` / `Meta.exclude` effective field sets.
- Two apps defining different `ItemForm` / `NewsletterForm` classes with the same class name.

`spec-036` already had to solve this for model-generated inputs: shape identity is `(model, operation kind, effective field set)`, with deterministic narrowed-shape names and fail-loud duplicate-name checks. The form spec needs the same level of precision. Right now an implementer could either silently reuse the wrong input class or hit a late Strawberry schema error from two distinct classes with the same GraphQL name.

Pin a form-input shape identity and naming rule before implementation. It should include at least operation kind, the form class identity, the effective field set after `Meta.fields` / `Meta.exclude`, and the generated representation metadata where it affects GraphQL names/types. Add tests for same form + different narrowing, different forms with the same `__name__`, and identical shapes deduping idempotently.

### [P1] `ModelChoiceField` decode no longer enforces related-object visibility

The revised reverse map correctly decodes `categoryId` into form field `category` (`docs/spec-038-form_mutations-0_0_12.md:1177`, `docs/spec-038-form_mutations-0_0_12.md:1188`, `docs/spec-038-form_mutations-0_0_12.md:1257`). But the spec says the resolver decodes the `GlobalID` to a pk and lets `ModelChoiceField.to_python` resolve through the form field's queryset (`docs/spec-038-form_mutations-0_0_12.md:1189`).

That drops a security invariant from `spec-036`: relation IDs are type-checked and visibility-checked through the related model's primary `DjangoType.get_queryset` before assignment. A default `ModelForm` field queryset is usually `Category.objects.all()`, not request-scoped. So a caller who can write an `Item` can attach it to a hidden `Category` by guessing or holding its GlobalID, unless every consumer remembers to scope each form field queryset manually.

Keep the form's queryset validation, but do not make it the only guard. The decode for `relation_single` / `relation_multi` should first reuse the `036` related-id type + visibility path, then feed the visible pk(s) into the form. Add live coverage where a permitted writer tries to submit a hidden category GlobalID and receives the same field-keyed `FieldError` as the model mutation path.

### [P2] `DjangoFormMutation` still accepts a `ModelForm` unless the validation explicitly rejects it

The architecture says plain `DjangoFormMutation` is model-less, has no `DjangoType` object slot, and returns only `ok` + `errors` (`docs/spec-038-form_mutations-0_0_12.md:1051`, `docs/spec-038-form_mutations-0_0_12.md:1065`). But the validation checklist says `DjangoFormMutation.Meta.form_class` must be a `forms.Form` subclass (`docs/spec-038-form_mutations-0_0_12.md:334`).

`forms.ModelForm` is also a `forms.Form` subclass. Under the written validation, a consumer can accidentally put a `ModelForm` on the model-less base, get a model write through the default `form.save()` path, and receive only `{ ok errors }` with no object slot, no `DjangoModelPermission` default, and no optimizer re-fetch. That contradicts the entire split between the two bases.

Make the validation explicit: plain `DjangoFormMutation` accepts `forms.Form` subclasses **excluding** `forms.ModelForm`; `DjangoModelFormMutation` accepts only `forms.ModelForm`. Add a class-creation test proving a `ModelForm` on the plain base raises a `ConfigurationError` naming the correct base.

### [P2] Partial-update reconstruction does not define what happens to required extra `ModelForm` fields

The spec derives input from `form_class().fields`, not only model fields, and generates an all-optional `<FormClass>PartialInput` for update (`docs/spec-038-form_mutations-0_0_12.md:1205`). The partial reconstruction then fills omitted values from `model_to_dict(instance, fields=<the form's non-file fields>)` (`docs/spec-038-form_mutations-0_0_12.md:1298`).

That works for model-backed fields, but not for extra `ModelForm` fields with no model column: `confirm`, captcha-like fields, action flags, or any required field declared on the form class. There is no instance value to reconstruct. Making every update field optional means callers can omit a required extra field, but the bound form will still fail required validation or get a meaningless initial value.

Pin the contract. Good options:

- Extra non-model fields remain required even in the partial update input.
- Extra non-model fields can be omitted only when the form field has an explicit `initial`.
- ModelForms with required extra fields are rejected for `operation = "update"` unless the spec defines a resolver hook to supply them.

Whichever rule is chosen, add tests for a `ModelForm` with a required extra field and for an optional extra field, so partial update behavior is not accidental.

### [P3] `Meta.fields` / `Meta.exclude` validation needs the same fail-loud treatment as model mutations

The form spec states that `Meta.fields` / `Meta.exclude` narrow `form.fields` and are mutually exclusive (`docs/spec-038-form_mutations-0_0_12.md:197`, `docs/spec-038-form_mutations-0_0_12.md:343`). It does not pin the failure behavior for a bare string, duplicate names, unknown form field names, or an empty effective field set.

Those are not just polish. A typo like `fields = ("emial",)` can produce an empty generated input, a late schema error, or a mutation that silently exposes less than intended. The model mutation base already normalizes and rejects malformed declarations early; the form base should do the same against `form_class().fields`.

Add explicit `ConfigurationError` requirements and tests for bare string, duplicate names, unknown `fields` / `exclude` names, and effective empty input shape.

## Checks run

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-038-form_mutations-0_0_12.md` passed: `OK: 31 terms`.
