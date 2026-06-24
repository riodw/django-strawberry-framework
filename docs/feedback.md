# Review feedback — spec-038 form mutations
Review target: `docs/SPECS/spec-038-form_mutations-0_0_12.md` implementation currently on `main`.
Scope reviewed: full `0.0.11..HEAD` form-mutation surface, with focused attention on `django_strawberry_framework/forms/`, the mutation-field/generalization seams, products live coverage, docs/version wrap-up, and current working-tree artifacts.
No pytest run was performed, per repo instruction.
## Findings
### [High] Plain `DjangoFormMutation` falls into `DjangoModelPermission` when `permission_classes` is omitted
`docs/SPECS/spec-038-form_mutations-0_0_12.md::Decision 11` says a plain model-less `DjangoFormMutation` has no model-permission default: unset permissions must be safe by default, and a public plain-form write should be an explicit opt-in via `Meta.permission_classes = []` or equivalent explicit classes.
The implementation does not enforce that split. `django_strawberry_framework/forms/sets.py::DjangoFormMutation._validate_meta` calls the shared `django_strawberry_framework/mutations/sets.py::_validate_permission_classes` with `getattr(meta, "permission_classes", None)`. That shared helper normalizes `None` to `[DjangoModelPermission]`. At request time, `django_strawberry_framework/mutations/permissions.py::DjangoModelPermission.has_permission` assumes a model-backed mutation: it calls `mutation._resolve_model(mutation.Meta)` and then looks up `_OPERATION_PERMISSION_ACTION[operation]`. A plain `DjangoFormMutation` provides neither `_resolve_model` nor a model operation (`operation == "form"`), so an omitted `permission_classes` produces a request-time crash/top-level implementation error instead of the spec’s safe default or class-creation rejection.
This is also codified by an accepting test: `tests/forms/test_sets.py::test_plain_form_class_accepted_as_known_key` declares a plain form without explicit `permission_classes`.
Recommended fix:
- Split permission normalization by flavor. For plain forms, either require `Meta.permission_classes` to be explicitly present, or install a plain-form deny-by-default class that does not inspect model metadata.
- Preserve explicit `permission_classes = []` as the documented allow-any opt-out.
- Add coverage for the omitted plain-form case: class-creation rejection or request-time deny-by-default, depending on the chosen contract.
### [High] Required generated input fields are non-null in SDL but still omittable at runtime
`django_strawberry_framework/utils/inputs.py::build_strawberry_input_class` assigns `None` as the Python class default whenever a generated field has no explicit `default` in `field_kwargs`. For required fields, callers pass no default, so the generated dataclass field becomes something like `name: str = None`.
Strawberry still renders this as non-null SDL (`String!`), but omission during execution can instantiate the input with `None` instead of producing the expected GraphQL variable/input coercion error. I confirmed this with a minimal Strawberry schema: `name: str = None` renders as `name: String!`, yet `mutation { submit(data: {}) }` reaches the resolver with `data.name is None`. With no class default, the same SDL correctly rejects the request before the resolver.
For spec-038 this breaks the form-derived input contract in `docs/SPECS/spec-038-form_mutations-0_0_12.md::Decision 7`: create inputs should honor `field.required`, and required non-model extras in partial inputs should remain required. The current behavior lets clients omit those supposedly non-null fields and turns schema-level requiredness into resolver/form-level `None` handling. That masks missing-input errors and makes tests such as `tests/forms/test_resolvers.py::test_required_extra_field_omitted_on_update_raises_field_error` pass for the wrong reason: the resolver sees `confirm=None` only because the generated required input field had a default.
Recommended fix:
- Change `build_strawberry_input_class` so required generated fields have no class attribute/default at all; only optional fields should receive `strawberry.UNSET` or another explicit default.
- Keep aliases (`strawberry.field(name=...)`) required by omitting `default`, not by passing `None`.
- Add tests that execute a schema and assert omitting a generated required form field produces a GraphQL coercion error before the resolver, while optional fields still arrive as `UNSET`.
- Audit existing model-mutation tests because this helper is shared by mutation/form input generation.
### [High] Narrowed `DjangoModelFormMutation.update` does not reconstruct excluded model-backed fields
`docs/SPECS/spec-038-form_mutations-0_0_12.md::Decision 8` requires update to reconstruct the full bound form payload from the located instance and overlay provided input data. That is necessary because a `ModelForm` validates all of its declared fields, not only the narrowed generated input fields.
The current reconstruction uses only the generated input specs. `django_strawberry_framework/forms/resolvers.py::_non_file_form_field_names` returns names from `mutation_cls._input_field_specs`, and `django_strawberry_framework/forms/resolvers.py::_reconstruct_partial_data` calls `model_to_dict(instance, fields=<those names>)`. When a `DjangoModelFormMutation` narrows `Meta.fields` to only a subset of a form’s model-backed fields, required model-backed form fields excluded from the GraphQL input are also excluded from reconstruction. The bound form then sees them as missing even though the instance has values for them.
Example: a `ModelForm` declares `("name", "category")`, and the update mutation narrows `Meta.fields = ("name",)`. A `name`-only update should preserve `category` from the instance. Instead, reconstruction builds data only for `name`, so the form can fail `category` required validation or skip constraint validation that depends on the preserved field.
Recommended fix:
- For update reconstruction, derive the non-file model-backed field list from the form’s declared `base_fields` plus model columns, not from generated input specs.
- Still overlay only the provided input fields; do not expose the excluded fields in the GraphQL input.
- Preserve current file behavior: omitted file fields should remain out of `data=`/`files=` and be preserved via `instance=`.
- Add package coverage for a narrowed update where an excluded required FK is preserved and a composite uniqueness constraint still validates against the preserved FK.
### [Medium] Explicit `null` relation inputs are accepted but mishandled by the form decoder
Partial/update-generated relation fields are optional (`annotation | None` with `UNSET` default), so clients can send explicit `null`. The decoder does not distinguish explicit `null` from an invalid id.
In `django_strawberry_framework/forms/resolvers.py::_decode_form_relation_single`, `None` takes the raw-pk branch and becomes an “Invalid id for relation …” `FieldError`. That prevents valid nullable/optional `ModelChoiceField` clears from reaching the form as an empty value, and it produces a decode-level error rather than the form’s own required/nullability validation for required relations.
In `django_strawberry_framework/forms/resolvers.py::_decode_form_relation_multi`, `None` is iterated as `values`, which can raise a top-level `TypeError` instead of returning the frozen `FieldError` envelope or delegating to form validation. The model mutation path has an explicit M2M-null guard; the form path needs its own equivalent that respects form semantics.
Recommended fix:
- Before id decoding, check `value in form_field.empty_values`.
- For single relations, pass an empty value through under the form field name when the form field allows it; otherwise let `form.is_valid()` produce the field-keyed required error.
- For multi relations, reject explicit `null` with a field-keyed error or pass the appropriate empty list through, but never iterate `None`.
- Add tests for optional FK clear, required FK explicit null, optional multi clear/null, and required multi explicit null.
### [Low] Plain `DjangoFormMutation` accepts an explicit `Meta.operation = None`
`docs/SPECS/spec-038-form_mutations-0_0_12.md::Decision 10` says the plain model-less base rejects any `Meta.operation`. The implementation checks `if getattr(meta, "operation", None) is not None`, so `operation = None` is treated the same as absence and silently accepted.
This is a small contract gap, but it matters because the plain base has a fixed `"form"` operation sentinel and should not accept copied `Meta.operation` keys at all.
Recommended fix:
- In `django_strawberry_framework/forms/sets.py::DjangoFormMutation._validate_meta`, reject key presence via `if "operation" in declared` or `if "operation" in vars(meta)` rather than checking the value.
- Add `None` to `tests/forms/test_sets.py::test_plain_base_rejects_any_operation`.
### [Low] Release/docs wrap-up still has stale or untracked artifacts
`TODAY.md` still describes the current state as `0.0.11` while also listing `0.0.12` form mutations. That should be updated to `0.0.12` as part of the spec-038 release wrap.
The current working tree also contains untracked `docs/dry/dry-0_0_12.md`. The dry-run docs describe `dry-<0_0_X>.md` files as tracked records, so this should be intentional: either add it to the release diff or remove/regenerate it outside this handoff if it is scratch output.
## Checks performed
- Read `AGENTS.md`.
- Inspected `git status`, `origin/main...HEAD`, and `0.0.11..HEAD`.
- Reviewed `docs/SPECS/spec-038-form_mutations-0_0_12.md`.
- Reviewed focused implementation files under `django_strawberry_framework/forms/`, mutation seams, registry/finalizer wiring, products form/schema changes, and form/live tests.
- Ran small read-only Python/Strawberry probes to confirm generated required input default behavior.
- Did not run pytest.