# Review feedback - `spec-038-form_mutations-0_0_12.md`

## Findings

### [P1] `form.save()` can still leak a raw database error instead of the frozen envelope

The resolver pipeline pins `form.is_valid()` errors to the shared `FieldError`
envelope, then writes with a bare `form.save()` (`docs/spec-038-form_mutations-0_0_12.md:1414`,
`docs/spec-038-form_mutations-0_0_12.md:1427`). Unlike the shipped model-mutation
pipeline, this path does not specify an `IntegrityError` fallback around the write.

That reopens the race / residual-constraint hole `036` already closed: a
`ModelForm` can validate successfully, then lose a concurrent uniqueness race or hit a
database constraint at `save()`. Today the model path maps that class of failure back
to the payload envelope (`django_strawberry_framework/mutations/resolvers.py:867`);
the form path as written would bubble a top-level GraphQL error / 500, breaking the
cross-flavor `FieldError` contract exactly where the spec says the contract is frozen.

Require the form resolver to catch `IntegrityError` from `form.save()` inside the same
`transaction.atomic()` and map it through the same helper / message policy as the
model mutation path. Add a package test that mocks a valid `ModelForm.save()` raising
`IntegrityError` and asserts a null object plus `errors: [{ field: "__all__", ... }]`,
not a top-level GraphQL error.

### [P2] There is no form-construction hook, so common existing forms cannot be reused

The input generator instantiates the form with no arguments to read `form.fields`
(`docs/spec-038-form_mutations-0_0_12.md:1317`), and the runtime constructs bound forms
only as `form_class(data=..., files=...)` / `form_class(data=..., files=..., instance=...)`
(`docs/spec-038-form_mutations-0_0_12.md:1385`, `docs/spec-038-form_mutations-0_0_12.md:1395`).
The text even references graphene-django's `get_form_kwargs`, but does not provide an
equivalent hook (`docs/spec-038-form_mutations-0_0_12.md:1376`).

That is a real migration blocker. Existing Django forms often require constructor
kwargs such as `user`, `request`, or tenant context to scope querysets, choose choices,
or attach service dependencies. The current contract only supports forms with a
no-argument constructor and no request-time kwargs. Relation visibility before the form
is necessary, but it does not replace a form's own queryset scoping or custom
constructor requirements.

Pin both halves explicitly: schema-time field discovery requires either a no-arg form
or an overridable `get_unbound_form()` / `get_form_fields()` hook whose field shape is
stable; runtime needs a `get_form_kwargs(info, data, files, instance=None)` or
`get_form(...)` hook used by create and update. Add tests for a form that requires a
`user` kwarg and for a hook that scopes a `ModelChoiceField.queryset` without changing
the generated input shape.

### [P2] Plain `DjangoFormMutation` has contradictory `operation` rules

Decision 10 says the plain form flavor has no model operation and does not declare
`Meta.operation` (`docs/spec-038-form_mutations-0_0_12.md:1528`). But the validation
matrix says the form-flavor override restricts `operation` to `{"create", "update"}`
(`docs/spec-038-form_mutations-0_0_12.md:352`, `docs/spec-038-form_mutations-0_0_12.md:2096`),
and the generated input identity includes `operation kind`
(`docs/spec-038-form_mutations-0_0_12.md:1257`).

That leaves implementers two incompatible readings: accept meaningless
`operation = "create"` / `"update"` on a model-less mutation, or reject it despite the
shared validation checklist. It also leaves the plain-form input cache key without a
defined operation component.

Split the rules by base class. `DjangoModelFormMutation` should require / default and
validate `operation in {"create", "update"}`. Plain `DjangoFormMutation` should reject
any `Meta.operation` as an unknown / unsupported key and use a fixed identity sentinel
such as `"plain"` for input-shape caching. Add tests for `Meta.operation` on the plain
base and for plain-form input dedupe.

### [P2] The converter cannot both map base `forms.Field` to `str` and fail on unknown fields

Decision 7 specifies a single-dispatch registry on `forms.Field`
(`docs/spec-038-form_mutations-0_0_12.md:1158`), maps "base `Field`" to `str`
(`docs/spec-038-form_mutations-0_0_12.md:1162`), and also requires an unknown
form-field class to raise `ConfigurationError`
(`docs/spec-038-form_mutations-0_0_12.md:1194`, `docs/spec-038-form_mutations-0_0_12.md:2063`).

With normal `functools.singledispatch`, registering `forms.Field` is a catch-all for
every custom field subclass. The unknown-field error becomes unreachable, and a
consumer's custom field silently becomes `String` even when its cleaned value is not a
string or its widget semantics need a different input shape.

Choose one contract. For the fail-loud contract the spec already claims, do not use a
base `forms.Field` fallback. Either handle exact `forms.Field` specially before the
dispatch, or implement an explicit registry that raises when `type(field)` is not one
of the supported classes. Add a custom `class CustomField(forms.Field)` test that
proves it raises.

### [P2] `ModelChoiceField.to_field_name` is ignored by the relation decode

The spec maps `ModelChoiceField` / `ModelMultipleChoiceField` to the target id
(`docs/spec-038-form_mutations-0_0_12.md:1168`) and decodes `categoryId` to
`{"category": pk}` before handing the value to the bound form
(`docs/spec-038-form_mutations-0_0_12.md:1209`, `docs/spec-038-form_mutations-0_0_12.md:1212`).

Django form relation fields can set `to_field_name`, and `ForeignKey(to_field=...)`
can generate exactly that shape. In that case `ModelChoiceField.to_python()` looks up
by the configured target field, not by `pk`. Feeding the decoded pk into the form makes
a valid GraphQL id fail form validation whenever the form expects a slug/code/other
unique target value.

After the type + visibility check finds the related object, convert the value passed
to the form with the form field's own key: `obj.serializable_value(field.to_field_name)`
when `to_field_name` is set, else `obj.pk`. Do the same per element for
`ModelMultipleChoiceField`. Add tests for single and multi relation fields with
`to_field_name`.

### [P2] Create-time narrowing can exclude a required form field and produce an always-invalid mutation

The spec validates malformed `Meta.fields` / `Meta.exclude` names and empty effective
sets (`docs/spec-038-form_mutations-0_0_12.md:1287`), but it does not reject a create
mutation that narrows out a required form field. Create construction only passes the
provided input fields to the bound form (`docs/spec-038-form_mutations-0_0_12.md:1385`).

For standard Django form fields, a required field omitted from bound `data=` fails
required validation; `initial` is not a substitute for submitted data in the general
case. So `Meta.fields = ("name",)` on a form whose required `category` remains in
`form.fields` creates a schema that looks valid but cannot succeed.

Add a create-time validation rule: if `operation = "create"` excludes any
`field.required` form field, raise `ConfigurationError` naming the missing required
form fields, unless the spec deliberately defines a hook that supplies those values
before binding. Cover both `Meta.fields` and `Meta.exclude`.

### [P3] Optional file clearing is not expressible

Partial update explicitly preserves omitted file fields by leaving them out of
`files=` (`docs/spec-038-form_mutations-0_0_12.md:1393`,
`docs/spec-038-form_mutations-0_0_12.md:1755`), and the edge-case text says an optional
field the consumer wants emptied is sent explicitly
(`docs/spec-038-form_mutations-0_0_12.md:1745`). For `FileField` / `ImageField`,
however, the only input shape is `Upload`.

Django's clearable file semantics distinguish "no change" from "clear" with a false
sentinel produced by `ClearableFileInput`, not with an uploaded file. A nullable
`Upload` value does not give the resolver a clear signal, and sending no file means
preserve. That leaves optional file/image fields uploadable and preservable, but not
clearable.

Either document file clearing as out of scope for `0.0.12`, or add an explicit input
representation such as `<field>Clear: Boolean` for clearable file fields and route it
through the form/widget-compatible clear path. Add a partial-update test for clearing a
blank/null file field if it is in scope.

## Checks run

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-038-form_mutations-0_0_12.md` passed: `OK: 31 terms`.
