# Review feedback - `spec-038-form_mutations-0_0_12.md`

## Findings

### [P1] Raw-pk relation inputs are promised visibility-scoped, but the reused `036` helper does not do that

The spec supports `ModelChoiceField` / `ModelMultipleChoiceField` inputs as Relay
`GlobalID` when the target primary type is Relay-shaped, otherwise as a raw pk scalar
(`docs/spec-038-form_mutations-0_0_12.md #"the raw pk scalar"`). It also says relation
decode runs type and visibility checks through the related primary `DjangoType.get_queryset`
before the form sees the value (`docs/spec-038-form_mutations-0_0_12.md #"visibility-checks the pk through the related"`).
But the text also says to reuse the shipped `036` related-id path
(`docs/spec-038-form_mutations-0_0_12.md #"first runs the shipped"`),
and that helper explicitly passes raw pk scalars through with no visibility hook:
`django_strawberry_framework/mutations/resolvers.py::_decode_relation_id_set #"A raw pk scalar"`.

That means the non-Relay relation branch can violate the restored security invariant the
spec claims to fix. A raw pk for a hidden related object will be placed into
`data={"category": pk}` and then validated by the form. With a default `ModelForm`
relation queryset, that is usually `Category.objects.all()`, so the form can accept an
object the GraphQL caller cannot see. Raw-pk M2M gets an existence check in the shipped
helper, but still not a visibility check; raw-pk FK gets neither until Django form/model
validation, which is not request scoped.

Pin a separate form relation decoder instead of reusing the `036` helper unchanged: for
raw pk single and multi relation inputs, resolve/coerce the pk and check it through the
related primary type's `get_queryset` before handing any value to the form. Keep the same
no-existence-leak `FieldError` shape. Add tests for a non-Relay related primary type
where `get_queryset` hides a row, covering both `ModelChoiceField` and
`ModelMultipleChoiceField` raw-pk inputs.

### [P1] `form.save()` can still leak a raw database error instead of the frozen envelope

The resolver pipeline maps `form.is_valid()` failures through the shared `FieldError`
envelope (`docs/spec-038-form_mutations-0_0_12.md #"A failure maps"`), then writes
with bare `form.save()` / `perform_mutate(...)` inside `transaction.atomic()`
(`docs/spec-038-form_mutations-0_0_12.md #"commit=True; M2M written"`). The
helper-reuse paragraph promotes the validation mapper and payload helpers, but it still
does not name the `036` save-time `IntegrityError` mapping helper
(`django_strawberry_framework/mutations/resolvers.py::_finalize_validated_write #"_save_or_field_errors"`).

That reopens the race / residual-constraint hole `036` already closed. A `ModelForm` can
validate successfully, then lose a concurrent uniqueness race or hit a database
constraint at `save()`. The model mutation path returns a null object plus `FieldError`
payload for that class of failure; the form path as written can bubble a top-level
GraphQL error / 500, breaking the cross-flavor envelope contract at write time.

Require the form resolver to catch `IntegrityError` from `form.save()` and from the
default plain-form `perform_mutate` save path, using the same message policy as model
mutations. Add a package resolver test with a valid `ModelForm.save()` that raises
`IntegrityError` and asserts envelope output, not a top-level GraphQL error.

### [P2] There is still no form-construction hook, so common migrated forms cannot be reused

The input generator instantiates the form with no arguments to read `form.fields`
(`docs/spec-038-form_mutations-0_0_12.md #"The form is instantiated once at bind time"`),
and runtime construction is fixed to `form_class(data=provided_data, files=provided_files)`
or `form_class(data=data, files=files, instance=<located row>)`
(`docs/spec-038-form_mutations-0_0_12.md #"data=provided_data, files=provided_files"`).
The spec mentions graphene-django's `get_form_kwargs`, but does not provide an equivalent
package hook (`docs/spec-038-form_mutations-0_0_12.md #"as a *full* update"`).

That is a migration blocker. Existing Django forms often require constructor kwargs such
as `user`, `request`, tenant, or service objects to scope querysets, choose choices, or
run validation. Relation visibility before the form is required, but it does not replace
a form's own constructor contract or request-scoped queryset setup.

Pin both schema-time and runtime extension points. Schema-time field discovery needs
either a documented no-arg form requirement or an overridable `get_unbound_form()` /
`get_form_fields()` hook whose field shape is stable. Runtime needs a
`get_form_kwargs(info, data, files, instance=None)` or `get_form(...)` hook used by
create, update, and plain forms. Add tests for a form that requires `user` and for a hook
that scopes a `ModelChoiceField.queryset` without changing the generated input shape.

### [P2] Plain `DjangoFormMutation` still has contradictory `operation` rules

Decision 10 says plain `DjangoFormMutation` has no model operation and does not declare
`Meta.operation` (`docs/spec-038-form_mutations-0_0_12.md #"has no model operation"`).
But the Slice 2 checklist and DoD still describe one form-flavor `_validate_meta` override
that restricts `operation` to `{"create", "update"}` and rejects `"delete"`
(`docs/spec-038-form_mutations-0_0_12.md #"operation is restricted";
`docs/spec-038-form_mutations-0_0_12.md #"form flavor has no delete pipeline"`).
The generated form input identity also includes `operation kind`
(`docs/spec-038-form_mutations-0_0_12.md #"operation kind, frozenset(effective field names)"`).

That leaves implementers two incompatible readings: accept meaningless
`operation = "create"` / `"update"` on a model-less mutation, or reject it despite the
shared validation checklist. It also leaves the plain-form input cache key without a
defined operation component.

Split the rules by base class. `DjangoModelFormMutation` should default / validate
`operation in {"create", "update"}`. Plain `DjangoFormMutation` should reject any
`Meta.operation` as unsupported and use a fixed identity sentinel such as `"plain"` for
input-shape caching. Add tests for `Meta.operation` on the plain base and for plain-form
input dedupe.

### [P2] The converter cannot both map base `forms.Field` to `str` and fail on unknown custom fields

Decision 7 specifies a single-dispatch registry on `forms.Field`
(`docs/spec-038-form_mutations-0_0_12.md #"single-dispatch on the Django"`), maps
base `Field` to `str` (`docs/spec-038-form_mutations-0_0_12.md #"text-like"`),
and also requires an unknown form-field class to raise `ConfigurationError`
(`docs/spec-038-form_mutations-0_0_12.md #"unknown form-field class raises"`).

With normal `functools.singledispatch`, registering `forms.Field` is a catch-all for
every custom field subclass. The unknown-field error becomes unreachable, and a
consumer's custom field silently becomes `String` even when its cleaned value is not a
string or its widget semantics need a different input shape.

Choose one contract. For the fail-loud contract the spec already claims, do not use a
base `forms.Field` fallback in the dispatch table. Either handle exact `forms.Field`
specially before dispatch, or implement an explicit registry that raises when
`type(field)` is not one of the supported classes. Add a custom
`class CustomField(forms.Field)` test proving it raises.

### [P2] `ModelChoiceField.to_field_name` is ignored by the relation decode

The spec decodes `categoryId` and then feeds the bound form a pk under the form field
name (`docs/spec-038-form_mutations-0_0_12.md #"then place the *visible*"`).
The same pk-list shape is specified for multi relations
(`docs/spec-038-form_mutations-0_0_12.md #"is type-/visibility-checked the same way"`).

Django form relation fields can set `to_field_name`, and `ForeignKey(to_field=...)` can
generate exactly that form field. In that case `ModelChoiceField.to_python()` looks up by
the configured target field, not by `pk`. Feeding the decoded pk into the form makes a
valid GraphQL id fail form validation whenever the form expects a slug, code, or other
unique target value.

After the type and visibility check finds the related object, convert the value passed to
the form with the form field's own key: `obj.serializable_value(field.to_field_name)` when
`to_field_name` is set, otherwise `obj.pk`. Do the same per element for
`ModelMultipleChoiceField`. Add tests for single and multi relation fields with
`to_field_name`.

### [P2] Create-time narrowing can exclude a required form field and produce an always-invalid mutation

The spec validates malformed `Meta.fields` / `Meta.exclude` names and empty effective
sets (`docs/spec-038-form_mutations-0_0_12.md #"empty effective field set"`), but it does
not reject a create mutation that narrows out a required form field. Create construction
passes only provided input fields to the bound form
(`docs/spec-038-form_mutations-0_0_12.md #"data=provided_data, files=provided_files"`).

For standard Django form fields, a required field omitted from bound `data=` fails
required validation; `initial` is not a substitute for submitted data in the general
case. So `Meta.fields = ("name",)` on a form whose required `category` remains in
`form.fields` creates a schema that looks valid but cannot succeed.

Add a create-time validation rule: if `operation = "create"` excludes any
`field.required` form field, raise `ConfigurationError` naming the missing required form
fields, unless a hook explicitly supplies those values before binding. Cover both
`Meta.fields` and `Meta.exclude`.

### [P3] Optional file clearing is still not expressible

Partial update preserves omitted file fields by leaving them out of `files=`
(`docs/spec-038-form_mutations-0_0_12.md #"an omitted file field is preserved"`), and
the edge-case text says an optional field the consumer wants emptied is sent explicitly
(`docs/spec-038-form_mutations-0_0_12.md #"wants emptied is sent explicitly"`). For
`FileField` / `ImageField`, however, the only specified input shape is `Upload`
(`docs/spec-038-form_mutations-0_0_12.md #"forms.FileField"`).

Django's clearable file semantics distinguish "no change" from "clear" with a false
sentinel produced by `ClearableFileInput`, not with an uploaded file. A nullable `Upload`
value does not give the resolver a clear signal, and sending no file means preserve.
That leaves optional file/image fields uploadable and preservable, but not clearable.

Either document file clearing as out of scope for `0.0.12`, or add an explicit input
representation such as `<field>Clear: Boolean` for clearable file fields and route it
through the form/widget-compatible clear path. Add a partial-update test for clearing a
blank/null file field if it is in scope.

## Checks run

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-038-form_mutations-0_0_12.md`
- `uv run ruff format .`
- `uv run ruff check --fix .`
- `git diff --check`
