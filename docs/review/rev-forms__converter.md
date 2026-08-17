# Review: `django_strawberry_framework/forms/converter.py`

Status: verified

## Understanding

`django_strawberry_framework/forms/converter.py::convert_form_field` owns the
model-less `forms.Field` to Strawberry annotation, requiredness, and decode-kind
contract. `django_strawberry_framework/utils/converters.py::convert_with_mro`
provides the ordered kind prechecks, scalar MRO walk, and fail-loud fallthrough.
The converter's scalar registry is form-field keyed; it deliberately does not
share the model-field registry used by `types/converters.py`.

`forms/inputs.py::_field_triple_and_spec` calls this converter only for
column-less plain-`Form` fields and extra `ModelForm` fields. A
column-backed `ModelForm` field instead routes through
`types/converters.py::convert_scalar`, `mutations/inputs.py::relation_input_annotation`,
or `scalars.py::Upload`, preserving read/write enum, relation-id, and upload
symmetry. `forms/inputs.py::build_form_input_class` applies the conversion's
requiredness to the generated `Input`/`PartialInput`; `forms/resolvers.py::_decode_form_data`
uses the resulting `InputFieldSpec` kind and target name to produce form-keyed
data/files payloads.

The relation/file prechecks correctly win over parent scalar classes:
`ModelChoiceField` and `ModelMultipleChoiceField` produce relation kinds,
`FileField`/`ImageField` produce the file kind, and `MultipleChoiceField` produces
`list[str]`. The exact bare `forms.Field` is an explicit `str` case; unsupported
custom subclasses reach `ConfigurationError` rather than a base-field catch-all.
`forms/sets.py::_cached_build_form_input` caches by form class, operation, and
effective field set, while the form input namespace ledger is cleared through
the registry lifecycle; repeated shapes therefore reuse classes without leaking
stale conversion state.

## Verification

- Read the full target, `forms/inputs.py`, `forms/resolvers.py`, `forms/sets.py`,
  shared converter/input helpers, mutation input generation, scalar/choice/upload
  mappings, fakeshop products/library/scalars forms, and their package/live tests.
- Baseline focused run before edits: `uv run pytest --no-cov tests/forms/test_converter.py tests/forms/test_inputs.py -q` — 74 passed.
- A direct generated-input probe reproduced the defect for a
  `NullBooleanField` subclass restoring `forms.Field.validate`: conversion
  returned `annotation=bool | None, required=True`; generated SDL was
  `flag: Boolean` with no default, and `{ probe(inp: {}) }` raised
  `ProbeInput.__init__() missing ... 'flag'` instead of a GraphQL required-field
  error.
- Existing tests cover scalar/MRO mappings, JSON, choices, relations, upload
  kinds, unsupported fields, optionality, narrowing, shape caching/materialization,
  resolver decoding, and plain versus model-backed mutations. The new regression
  also builds a generated input and asserts its SDL is `flag: Boolean!`.
- After edits: `uv run pytest --no-cov tests/forms -q` — 175 passed.
- After edits: `uv run ruff format .` passed. Repository-wide
  `uv run ruff check --fix .` stopped on F821 errors in concurrent
  `forms/inputs.py`, `rest_framework/serializer_converter.py`, and
  `tests/mutations/test_inputs.py` (the concurrent
  `annotate_queryset_relation`, `related_model_of_queryset`, and
  `require_queryset_related_model` references); the owned
  `uv run ruff check --fix django_strawberry_framework/forms/converter.py tests/forms/test_converter.py`
  passed, and `git diff --check` passed for the scoped source/test diff.

## Improvements

### High

#### Validating `NullBooleanField` subclasses generated nullable-required inputs

- **Observation:** The MRO row for `forms.NullBooleanField` always emitted
  `bool | None`, while `form_field_required` intentionally preserved
  `required=True` for a subclass that restores real validation. The generated
  input therefore had a nullable GraphQL field with no dataclass default.
- **Evidence:** The direct probe above showed SDL `flag: Boolean` and Strawberry
  raised a constructor `TypeError` when the client omitted `flag`. Django's
  validating subclass itself correctly reported `"This field is required."`, so
  the mismatch was introduced at converter/input generation, not form validation.
- **Impact:** A custom form field could compile successfully, advertise an
  omittable GraphQL field, and then fail at argument construction before the form
  mutation could return its normal `FieldError` envelope. This violated the
  public input contract and made custom validating subclasses unusable.
- **Recommendation:** Keep the exact built-in `NullBooleanField` as optional
  `bool | None`, but make the converter's annotation follow effective
  requiredness for subclasses: required validating subclasses use non-null
  `bool`, while optional/no-op fields retain `bool | None`. The owning rule is
  `forms/converter.py`, not a test-only workaround or a caller-side default.
- **Proof:** `tests/forms/test_converter.py::test_null_boolean_validating_subclass_generates_required_input`
  asserts the conversion, generated Strawberry field, and `Boolean!` SDL. The
  full focused form suite passes.

### Medium

None.

### Low

None.

## Summary

The converter's dispatch ordering, MRO specificity, fail-loud unsupported-field
behavior, decode-kind contract, model-backed/read-side delegation, optionality
cache lifecycle, and plain/model form separation are coherent and covered. One
High public-contract defect was confirmed and fixed at the converter owner:
validating `NullBooleanField` subclasses now generate a non-null required scalar
instead of nullable-required SDL that crashed during input construction.

## Implementation (Worker 1)

- Changed `django_strawberry_framework/forms/converter.py::_SCALAR_FORM_FIELDS`
  to use `_null_boolean_converter`, which selects `bool` for genuinely required
  `NullBooleanField` subclasses and `bool | None` for the exact built-in/no-op
  behavior.
- Expanded `tests/forms/test_converter.py` with
  `test_null_boolean_validating_subclass_generates_required_input`, covering
  converter output, generated-input optionality, and schema SDL.
- Files changed by Worker 1: `django_strawberry_framework/forms/converter.py`,
  `tests/forms/test_converter.py`, and this artifact
  `docs/review/rev-forms__converter.md`. Neighboring forms input/resolver/set
  files and unrelated dirty files were preserved.
- `uv run ruff format .`, focused form tests, targeted Ruff, and scoped
  whitespace checks passed. The repository-wide Ruff failure is confined to
  concurrent neighbor/test F821 errors recorded above; those files were not
  touched or re-attributed. No changelog update is warranted.

## Independent verification (Worker 2)

- Re-traced `convert_form_field` through `utils/converters.py::convert_with_mro`,
  `forms/inputs.py::_field_triple_and_spec`,
  `utils/inputs.py::optional_input_field`, and
  `utils/inputs.py::build_strawberry_input_class`. The conversion's
  `required` value and annotation now agree at both the model-less and
  model-backed build sites; optional fields receive `bool | None` plus an
  explicit `strawberry.UNSET` default, while required fields receive `bool`
  without a default.
- `uv run pytest --no-cov tests/forms/test_converter.py tests/forms/test_inputs.py -q`
  — 75 passed. This independently covers the new validating-subclass converter
  test plus existing exact `NullBooleanField`, nullable/non-null model-column,
  choice-enum, Boolean, relation, file, unsupported-field, and generated-input
  contracts.
- `uv run pytest --no-cov tests/forms -q` — 175 passed. This includes the
  permanent runtime mutation test
  `tests/forms/test_resolvers.py::test_null_boolean_field_omitted_in_mutation_uses_unset_default`
  and the sync form pipeline around generated inputs.
- `uv run pytest --no-cov tests/forms/test_resolvers.py -q -k 'null_boolean or choice or boolean'`
  — 2 passed. The omitted exact built-in reaches form validation and does not
  surface a Strawberry constructor error; adjacent choice/Boolean resolver
  behavior remains green.
- A direct sync matrix probe (`DJANGO_SETTINGS_MODULE=config.settings uv run
  python - <<'PY' ... PY`) exercised exact `NullBooleanField` with
  `required=True` and `False`, a validating subclass with both required states,
  ordinary `BooleanField` with both states, and required/optional
  `ChoiceField`/`MultipleChoiceField`. Results: exact built-in always converted
  to `bool | None`, `required=False`, SDL `flag: Boolean`, and omitted input
  executed; validating subclass `required=True` converted to `bool`, SDL
  `flag: Boolean!`, and omission was rejected by GraphQL; every `required=False`
  case remained nullable/omittable; ordinary Boolean and choice fields retained
  their expected `Boolean`/`String`/`[String!]` nullability.
- A direct async Strawberry probe (`DJANGO_SETTINGS_MODULE=config.settings uv
  run python - <<'PY' ... PY`) executed `{ exact(inp: {}) }` against an async
  resolver and returned `errors=None, data={'exact': True}` for the exact
  built-in optional field. The validating-subclass generated field remained
  non-null (`bool`, no default), so sync and async schema paths share the same
  coercion contract.
- No revision is needed. Worker 1's production fix is scoped to the
  `NullBooleanField` scalar-table converter, preserves relation/file/choice
  prechecks and MRO ordering, and does not alter ordinary Boolean or choice
  mappings. The review item is verified; no uncoordinated production change was
  made.
