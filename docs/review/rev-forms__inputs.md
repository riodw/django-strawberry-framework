# Review: `django_strawberry_framework/forms/inputs.py`

Status: verified

## Understanding

`django_strawberry_framework/forms/inputs.py::get_form_fields` discovers a form's
stable `base_fields` without instantiating it. The mutation-owned
`forms/sets.py::DjangoFormMutation.get_form_fields` and
`forms/sets.py::DjangoModelFormMutation.get_form_fields` hooks can replace or
extend that stable basis; `resolve_effective_form_fields` owns
the shared `Meta.fields` / `Meta.exclude` normalization and fail-loud narrowing
against that declaration. `build_form_input_class` converts each effective field
through the model-column path (`relation_input_annotation`, `convert_scalar`, or
`Upload`) or the model-less `forms/converter.py::convert_form_field` path, then
applies create/partial requiredness and records an `InputFieldSpec` reverse map.
`build_form_inputs` builds the create-shaped and `PARTIAL` classes, while
`form_input_type_name` and the `make_input_namespace` ledger provide stable
canonical/shape-derived names and lazy-module materialization.

The bind path in `forms/sets.py::_cached_build_form_input` resolves the same
effective fields, caches by `(form_class, operation_kind, frozenset(names))`, and
materializes the selected class before `mutations/fields.py::DjangoMutationField`
constructs its lazy `data:` reference. `forms/resolvers.py::_decode_form_data`
consumes the stashed `InputFieldSpec` rows by `target_name`, so relation aliases
such as `categoryId` become form-keyed `category` data and file fields go to
`files=`. The finalizer and fakeshop/library form mutations exercise this path
through both model-backed and model-less consumers.

## Verification

- Read the complete target and traced callers/consumers through
  `forms/converter.py`, `forms/sets.py`, `forms/resolvers.py`,
  `mutations/inputs.py`, `mutations/fields.py`, `types/finalizer.py`, and the
  products/library form schemas and live tests.
- Examined requiredness for model-backed and non-model fields, including
  `NullBooleanField`, nullable/defaulted columns, required column-less extras,
  partial reconstruction, relation single/multi cardinality, `to_field_name`,
  uploads, choice enums, and unsupported custom fields.
- Replayed the pre-existing one-shot iterable boundary with direct generator
  probes for `fields` and `exclude`, including the create-required guard. Both
  generated classes retain the validated effective names, and dropping a
  required field still raises the typed `ConfigurationError`.
- `uv run pytest --no-cov tests/forms/test_inputs.py -q` — 46 passed before this
  artifact edit.
- `uv run pytest --no-cov tests/forms/test_sets.py tests/forms/test_resolvers.py
  -q` — 100 passed after the artifact edit, covering the bind, lazy input
  references, reverse-map decode, and sync/async resolver consumers.
- Revision validation: `uv run pytest --no-cov tests/forms/test_sets.py -q` —
  51 passed; `uv run pytest --no-cov tests/forms/test_inputs.py
  tests/forms/test_resolvers.py -q` — 98 passed.
- `uv run ruff check django_strawberry_framework/forms/inputs.py
  tests/forms/test_inputs.py` — passed. The repository-wide `uv run ruff check .`
  also passed at review time; the earlier neighboring F821/NameError report was
  investigated rather than attributed to this target.
- The shape-token probe covered distinct legal-looking field names and
  combinations without collisions. Materialization/repeated-shape behavior is
  covered by `tests/forms/test_inputs.py` and the bind cache tests.

## Improvements

### High

None.

### Medium

### Form-field discovery hook is documented but ignored — resolved in revision

- **Observation:** `django_strawberry_framework/forms/inputs.py::get_form_fields`
  documents an overridable `get_form_fields(cls)` classmethod on the form-mutation
  base, but neither `DjangoFormMutation` nor `DjangoModelFormMutation` defines that
  hook. Their build path calls `get_form_fields(meta.form_class)` directly through
  `forms/sets.py::_cached_build_form_input`, so a consumer override cannot customize
  the stable discovery basis.
- **Evidence:** A direct Django probe defined a plain `DjangoFormMutation` with
  `@classmethod get_form_fields` returning an `injected` field for a form whose
  `base_fields` contained only `name`. Calling its real `build_input` generated
  only `name`; the override was never consulted. The spec-038 Decision 7
  discovery contract also explicitly promises this classmethod.
- **Impact:** Consumers that need a stable schema-time field set differing from
  `form_class.base_fields` cannot implement the documented extension point; their
  customization is silently ignored and the generated GraphQL input can omit the
  intended field.
- **Recommendation:** Route form input basis discovery through an overridable
  `get_form_fields` classmethod on both form mutation bases (or an equivalent
  mutation-class callback owned by `forms/sets.py`), with
  `forms/inputs.py::get_form_fields` remaining the default `base_fields` helper.
  Re-resolve narrowing and required-field guards against that same returned basis
  so name, build, cache, and decode remain consistent.
- **Proof:** `tests/forms/test_sets.py::test_plain_form_get_form_fields_hook_controls_input_basis`,
  `tests/forms/test_sets.py::test_modelform_get_form_fields_hook_controls_input_basis`, and
  `tests/forms/test_sets.py::test_get_form_fields_hook_basis_drives_required_guard` define
  permanent coverage asserting
  the generated input includes the injected stable field, and asserting narrowing
  plus required guards use the override's returned mapping.

The target and test were already dirty at dispatch. Their
pre-existing hunk is a confirmed Medium iterator-consumption fix in
`forms/inputs.py::build_form_inputs`: it freezes the validated effective names
before building both child inputs. The accompanying
`tests/forms/test_inputs.py::test_build_form_inputs_freezes_one_shot_narrowing_iterables`
proves both one-shot `fields` and `exclude` behavior. This was preserved as
concurrent work, not reimplemented or attributed to this review.

### Low

None.

## Summary

The pre-existing one-shot iterable fix is sound. The revision now honors the
documented mutation-owned discovery hook through narrowing, required guards,
name/build/cache identity, and reverse-map reconstruction/decoding. The form
input surface is coherent and covered by the focused form suites.

## Implementation (Worker 1)

No review-owned production or permanent-test change was necessary. The exact
pre-existing target changes at dispatch were preserved:

- `django_strawberry_framework/forms/inputs.py` — 9 additions and 5 deletions
  freeze the validated effective names before the two child builds.
- `tests/forms/test_inputs.py` — 42 added lines cover one-shot `fields` and
  `exclude` iterables across create and partial shapes.

The initial pass added only this artifact. The revision owns the following
production/test changes; neighboring concurrent edits in
`django_strawberry_framework/mutations/inputs.py`,
`django_strawberry_framework/rest_framework/serializer_converter.py`, and
`tests/mutations/test_inputs.py` provide the currently imported
`annotate_queryset_relation`/serializer helper context; their NameError/lint
boundary is outside this target and was not changed. No changelog entry is
warranted. No commit was made.

## Independent verification (Worker 2)

The target diff against `HEAD` contains only the effective-name tuple freeze in
`django_strawberry_framework/forms/inputs.py::build_form_inputs` and its
permanent generator test in
`tests/forms/test_inputs.py::test_build_form_inputs_freezes_one_shot_narrowing_iterables`.
The freeze is correctly placed after
`django_strawberry_framework/forms/inputs.py::resolve_effective_form_fields` has
validated and normalized the input, and before both create/partial child builds;
it preserves the effective order while preventing a second consumption of a
one-shot `fields` or `exclude`.

Evidence:

- `uv run pytest --no-cov tests/forms/test_inputs.py -q` — 46 passed.
- A standalone Django probe exercised bare-string, duplicate, unknown, non-string,
  and mutually-exclusive `fields` / `exclude` declarations; all failed with the
  expected `ConfigurationError`.
- One-shot `fields` and `exclude` generators both retained the same effective
  names for create and partial builds, and both still triggered
  `guard_create_required_fields` when a required field was dropped.
- Generated required fields had no dataclass default and rejected omission;
  optional fields had nullable annotations, `strawberry.UNSET`, and remained
  omittable. Plain `forms.Form` model-choice fields used the model-less relation
  path, while `ModelForm` foreign keys used the model-column path and
  `category_id` reverse-map metadata.
- Repeated shape-derived naming was stable and order-insensitive, distinct
  shapes differed, and materialization was idempotent only for the same class;
  a distinct class claiming the same name raised the family-specific
  `ConfigurationError`.
- An injectivity probe over 2,800 capitalization/underscore/digit field-name
  tokens found no collisions in `utils/inputs.py::pascalize_token`.

The one-shot dirty-field/exclude behavior is sound, but the documented discovery
hook gap above remains unresolved. Apart from that finding, no new defect was
reproduced across dirty-field/exclude freezing,
input-name/materialization behavior, required/default/nullable semantics, file
and choice conversion paths covered by the permanent tests, malformed
declarations, or plain `Form` versus `ModelForm` handling. Verification was
limited to the requested target and its permanent inputs tests; no production
change or commit was made. Targeted Ruff validation is reported separately
because the review artifact itself is Markdown and the checkout contains broad
unrelated concurrent edits.

## Iterations

### Worker 1 revision

Worker 2's finding is resolved at the form discovery/bind owner. Both
`DjangoFormMutation` and `DjangoModelFormMutation` now expose a
`get_form_fields(cls)` classmethod whose default reads the module-level
`forms/inputs.py::get_form_fields` `base_fields` snapshot. The returned mapping is
threaded through `resolve_effective_form_fields`, `build_form_input_class`,
`build_form_inputs`, `form_input_type_name`, and both required-field guards, so
custom fields participate in narrowing, required validation, generated naming, and
the create/partial shapes. Custom discovery hooks receive a cache discriminator;
the default hook retains cross-mutation shape deduplication.

The two directly related resolver reads,
`forms/resolvers.py::_decode_form_data` and
`forms/resolvers.py::_reconstruct_partial_data`, now consult the same mutation hook
so injected relation/scalar fields do not disappear from decode or reconstruction.
No unrelated resolver behavior was changed.

Permanent coverage was added in
`tests/forms/test_sets.py::test_plain_form_get_form_fields_hook_controls_input_basis`,
`tests/forms/test_sets.py::test_modelform_get_form_fields_hook_controls_input_basis`,
and `tests/forms/test_sets.py::test_get_form_fields_hook_basis_drives_required_guard`.
Focused validation: `tests/forms/test_sets.py` — 51 passed; combined
`tests/forms/test_inputs.py` and `tests/forms/test_resolvers.py` — 98 passed.
Required `uv run ruff format .` left 423 files unchanged, and
`uv run ruff check --fix .` passed. Status is `fix-implemented`; no commit was made.

### Worker 2 re-verification

The hook revision correctly threads the mutation-owned basis through
`forms/inputs.py::resolve_effective_form_fields`,
`forms/inputs.py::build_form_input_class`,
`forms/inputs.py::build_form_inputs`,
`forms/inputs.py::form_input_type_name`, both required-field guards, and the
`forms/sets.py::_cached_build_form_input` cache. Default hooks retain the
cross-mutation cache shape; custom hook classes receive a cache discriminator so
different representations cannot reuse the wrong generated class.

Evidence:

- `uv run pytest --no-cov tests/forms/test_sets.py -q` — 51 passed.
- `uv run pytest --no-cov tests/forms/test_inputs.py tests/forms/test_resolvers.py -q`
  — 98 passed.
- Targeted Ruff over the revised form sources/tests passed.
- Direct probes passed for both plain and ModelForm hook discovery, narrowed
  shape-derived names, required guards, same-mutation cache reuse, plain decode
  and bind, and ModelForm partial decode/reconstruction/binding for injected
  scalar fields (with matching `get_form` overrides).
- A custom CharField-versus-IntegerField representation probe produced distinct
  cached classes and the expected materialization collision rather than reusing
  the wrong annotation.

### Previously identified Medium finding: malformed hook returns leak raw exceptions

- **Observation:** `forms/sets.py::_mutation_form_fields` eagerly calls
  `dict(mutation_cls.get_form_fields())` before the shared
  `forms/inputs.py::_form_field_basis` validator can normalize the result. A
  malformed custom hook return therefore bypasses the documented
  `ConfigurationError` path.
- **Evidence:** For both `DjangoFormMutation` and `DjangoModelFormMutation`,
  direct class declarations whose hook returned `None`, `["name"]`, or
  `[("name",)]` raised raw `TypeError` / `ValueError` during class creation.
  Mapping returns with a non-string key or non-`forms.Field` value correctly
  produce `ConfigurationError`, proving the failure is specifically the
  eager conversion boundary.
- **Impact:** A consumer typo or malformed hook result produces an untyped
  declaration-time exception instead of the package's fail-loud
  `ConfigurationError`, with inconsistent diagnostics across equivalent
  malformed inputs.
- **Recommendation:** Pass the raw hook result into one shared normalizer owned
  by `forms/inputs.py` (or wrap the `dict(...)` conversion in
  `_mutation_form_fields`) so every non-mapping/invalid mapping result becomes
  a `ConfigurationError` before narrowing, cache, or bind work.
- **Proof:** Add permanent plain- and ModelForm tests covering `None`, a
  non-pair iterable, and malformed pairs, asserting `ConfigurationError` and
  stable wording; retain the existing mapping-value validation tests.

### Worker 2 follow-up

Worker 1's second revision removes the eager `dict(...)` conversion from
`forms/sets.py::_mutation_form_fields` and routes raw hook results through
`forms/inputs.py::normalize_form_field_basis`. Re-running both mutation
metaclasses with `None`, a scalar, a non-pair iterable, a malformed pair,
an invalid field value, and an invalid key produced typed
`ConfigurationError` diagnostics in every case.

The valid hook contract remained intact: plain and ModelForm discovery,
narrowing/name/cache/guard behavior, decode, and ModelForm partial
reconstruction/binding all passed the direct probes above. Focused validation
after this revision was `tests/forms/test_sets.py` — 57 passed;
`tests/forms/test_inputs.py tests/forms/test_resolvers.py` — 98 passed; and
targeted Ruff over all revised form sources/tests passed.

The malformed-return finding is resolved. No production or permanent-test
changes were made by Worker 2; no commit was made.

### Worker 1 second revision

The remaining malformed-return boundary is resolved in the shared
`forms/inputs.py::normalize_form_field_basis` helper. `_mutation_form_fields`
now passes the raw hook result into that normalizer instead of eagerly calling
`dict(...)`; explicit `None`, non-pair iterables, and malformed pairs all become
the typed `ConfigurationError` before narrowing, cache, or bind work. Existing
mapping key/value validation remains unchanged.

Permanent coverage was added in
`tests/forms/test_sets.py::test_malformed_get_form_fields_return_is_configuration_error`,
parameterized across both mutation bases and `None`, a scalar iterable, and a
malformed pair. Final focused validation:
`uv run pytest --no-cov tests/forms/test_inputs.py tests/forms/test_sets.py
tests/forms/test_resolvers.py -q` — 155 passed.
Required `uv run ruff format .` left 423 files unchanged and
`uv run ruff check --fix .` passed. Status remains `fix-implemented`; no commit
was made.
