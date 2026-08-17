# Review: `django_strawberry_framework/forms/sets.py`

Status: verified

## Understanding

`django_strawberry_framework/forms/sets.py::DjangoModelFormMutation` is the model-backed form
adapter over `mutations/sets.py::DjangoMutation`: its metaclass snapshot resolves
`Meta.form_class._meta.model`, validates the ModelForm-only operation and narrowing matrix, and
registers the declaration for `mutations/sets.py::bind_mutations`. The bind resolves the model's
primary `DjangoType`, builds the form-derived input, materializes it in
`forms/inputs.py`, and materializes the shared payload in `mutations/inputs.py`.
`DjangoFormMutation` is deliberately separate: its metaclass and declaration ledger feed
`bind_form_mutations`, which materializes one form input and the model-less `{ok, errors}` payload.

The target owns the declaration registries, class-creation `Meta` validation, form-input build
cache, mutation-owned `get_form_fields` hook dispatch, construction-hook waiver for required-field
guards, generated input-name selection, and phase-2.5 binding. `DjangoMutationField` consumes the
target's `input_type_name`, `input_module_path`, and resolver seams only after the declaration has
registered; the finalizer binds ModelForm declarations first and plain-form declarations second,
before Strawberry freezes the schema. Payload generation and output slots remain shared with the
model mutation layer.

The pre-existing revision in the target threaded `get_form_fields()` through effective-field
normalization, required guards, naming, cache identity, and build/materialization. The connected
`forms/inputs.py` and `forms/resolvers.py` hook consumers are prior cross-file ownership and were
read for consistency but not rewritten here: input generation owns basis validation/conversion,
while resolver decoding and partial reconstruction own runtime form-field mapping.

## Verification

- Compared the dirty target files with `git show HEAD:<path>` and inspected the complete current
  source before judging. The scoped pre-existing diff was
  `django_strawberry_framework/forms/sets.py` (102 additions, 13 deletions) and
  `tests/forms/test_sets.py` (145 additions); those hunks were preserved.
- Traced the generated input lifecycle through
  `forms/inputs.py::resolve_effective_form_fields`,
  `forms/inputs.py::build_form_input_class`,
  `mutations/sets.py::build_and_stash_input`,
  `mutations/fields.py::DjangoMutationField`, and
  `types/finalizer.py::finalize_django_types`. The field-factory lazy name and the bind name both
  call the same `forms/sets.py::_form_input_type_name_for` path.
- Traced both ledgers through `make_declaration_registry`, registry co-clears, and the finalizer's
  phase-2.5 order. ModelForm declarations ride the model ledger; plain forms never enter it.
  Repeated default shapes use the `(form_class, operation_kind, effective names)` cache identity,
  while a custom hook receives a mutation discriminator so a differing representation cannot
  reuse stale field specs; distinct classes under one generated name are rejected by the
  materialization collision policy.
- Checked `Meta.form_class` type gates, inherited `Meta.operation` handling, operation-specific
  narrowing, permission defaults, `select_for_update`, empty/unknown/bare-string/duplicate
  selectors, required-field guards, and no-primary bind failures against the permanent tests.
- Examined sync/async resolver seam generation and the plain `FORM` sentinel: the plain field
  factory omits `id`, while ModelForm create/update retain the model mutation signature. The
  construction and relation decode implementation is outside this target's ownership; its
  bind-stashed reverse map remains the sets-owned handoff.
- `uv run pytest --no-cov tests/forms/test_sets.py -q` — 57 passed.
- `uv run pytest --no-cov tests/forms/test_inputs.py tests/forms/test_resolvers.py -q` — 98 passed.
- A disposable ModelForm finalizer-retry probe (failure after the bind, then retry) passed and
  confirmed the existing `bind_form_mutations` cache clear leaves the regenerated declaration
  usable.
- A direct cache probe confirmed repeated default-shape calls return the same generated class,
  while different custom hook representations do not reuse that class. No source or permanent
  test change was needed to resolve the observed policy.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

No sets-owned correctness, lifecycle, naming, collision, validation, or sync/async defect was
confirmed. The target's prior hook revision is internally consistent: one normalized field basis
drives guards, names, generated inputs, cache discrimination, and the bind handoff, while the two
form flavors retain separate declaration/output lifecycles. The related input and resolver hook
revisions remain prior cross-file ownership.

## Implementation (Worker 1)

None — zero-edit cycle.

The only new file is this review artifact:
`docs/review/rev-forms__sets.md`. No production code or permanent test was changed. The existing
sets/test modifications listed under Verification were present before this pass and remain
untouched; no prior `get_form_fields` audit trail was rewritten. No changelog entry is warranted.
No commit was made.

## Independent verification (Worker 2)

Status: verified

The focused suites pass:

- `uv run pytest --no-cov tests/forms/test_sets.py -q` — 57 passed.
- `uv run pytest --no-cov tests/forms/test_inputs.py tests/forms/test_resolvers.py -q` — 98 passed.
The lifecycle was re-traced through `forms/sets.py::_default_mutation_get_form_fields`,
`forms/sets.py::_mutation_form_fields`, `forms/inputs.py::resolve_effective_form_fields`,
`forms/inputs.py::build_form_input_class`, `mutations/sets.py::build_and_stash_input`,
`mutations/fields.py::DjangoMutationField`, `forms/resolvers.py::_decode_form_data`, and
`types/finalizer.py::finalize_django_types`. Default repeated declarations still dedupe by the
form-class/operation/effective-name shape; distinct form classes or custom-hook identities
remain collision-protected. Existing relation-id (including `to_field_name`), update
reconstruction, sync/async, and lazy-signature tests passed.

### Medium — the default hook reads a mutable live `Meta` instead of the validated snapshot

**Observation:** `forms/sets.py::_default_mutation_get_form_fields` first reads
`getattr(cls, "Meta").form_class` and only falls back to `_mutation_meta`. Every bind and lazy
signature call therefore re-resolves the live `Meta`, even though class creation already froze
`_ValidatedMutationMeta.form_class`; `forms/sets.py::_default_get_form` correctly uses the
snapshot.

**Evidence:** A direct probe declared `Submit.Meta.form_class = FormA` (`alpha: CharField`),
then changed `Submit.Meta.form_class = FormB` (`beta: IntegerField`) before
`finalize_django_types()`. It printed:

```text
validated snapshot: FormA
materialized input: FormAInput
materialized fields: ['beta']
default construction form: FormA
```

The same mismatch is visible without finalization:
`_mutation_form_fields(Submit, Submit._mutation_meta.form_class)` returns `['beta']` after
the mutation. A request carrying `beta` can therefore pass GraphQL input generation but is
bound to `FormA`, while a request carrying `alpha` is not represented by the generated input.
This also lets a custom `get_form_fields` implementation that delegates to the default hook
observe a different form than the one in the snapshot.

**Impact:** Generated field specs, required guards, input names, cache contents, and resolver
decode basis can diverge from the form class validated at declaration time. The mismatch is
especially dangerous for ModelForms because relation specs and `to_field_name` decoding are
derived from the generated basis while `get_form` constructs the snapshot form.

**Recommendation:** In `forms/sets.py::_default_mutation_get_form_fields`, resolve an own
`_mutation_meta` snapshot first (`cls.__dict__.get("_mutation_meta")`) and use live `Meta` only
while the metaclass is validating a newly created class (before the own snapshot is stamped).
The own-dict check avoids accidentally using a parent mutation's snapshot while validating a
child that declares a new `Meta`. Add a permanent test that mutates `Meta.form_class` after
declaration and proves bind/name/decode continue to use the frozen form (or fail closed).

### Low — malformed non-callable hook leaks a raw `TypeError`

**Observation:** A concrete declaration that sets `get_form_fields = None` reaches
`forms/sets.py::_mutation_form_fields` and attempts to call it without a callable guard.

**Evidence:** A direct class-creation probe with a valid `forms.Form` produced:

```text
TypeError 'NoneType' object is not callable
```

The existing malformed-return tests prove that a callable returning `None`, a list, or a
one-tuple becomes `ConfigurationError`, but they do not cover a missing/non-callable
classmethod declaration.

**Impact:** A malformed consumer declaration escapes the package's typed configuration boundary
and can be reported as an unrelated framework error during import.

**Recommendation:** Validate that `get_form_fields` is callable before invocation and raise a
`ConfigurationError` naming the mutation and required classmethod shape; add coverage for
`None` and a plain non-classmethod declaration. Preserve the existing typed mapping validation
in `forms/inputs.py::normalize_form_field_basis`.

### Verification summary

The current revision is internally sound for the covered, immutable declaration path, including
generated input caching/materialization/collision behavior, fields/exclude and required guards,
plain versus ModelForm metaclass paths, relation IDs/to-field, sync/async dispatch, lazy
signatures, repeated default declarations, and input/resolver handoff. The two configuration
boundary issues are addressed below; Worker 2 should independently verify the result.

## Iterations

### Worker 1 revision

Implemented both Worker 2 findings at the sets-owned configuration boundaries:

- `forms/sets.py::_default_mutation_get_form_fields` now reads the concrete class's own frozen
  `_mutation_meta.form_class` after metaclass validation. It consults live `Meta.form_class` only
  during the pre-snapshot validation window, and uses `cls.__dict__` so a child declaration cannot
  inherit a parent snapshot. This keeps generated fields, names, guards, reverse specs, and the
  default `get_form` constructor on one validated form class.
- `forms/sets.py::_mutation_form_fields` now rejects a missing/non-callable hook with a typed
  `ConfigurationError` before invocation; callable hooks continue through the existing
  `forms/inputs.py::normalize_form_field_basis` validator.

Permanent coverage was added in
`tests/forms/test_sets.py::test_default_get_form_fields_uses_frozen_form_class_snapshot` and
`tests/forms/test_sets.py::test_non_callable_get_form_fields_is_configuration_error`, the latter
covering both plain and ModelForm bases and both `None` and a non-callable value.

Focused validation:

- `uv run pytest --no-cov tests/forms/test_sets.py -q` — 62 passed.
- `uv run pytest --no-cov tests/forms/test_inputs.py tests/forms/test_resolvers.py -q` — blocked by
  unrelated concurrent edits in `forms/inputs.py`: 21 passed and 77 failed with
  `NameError: name 'pascalize_token' is not defined` during the connected input-name path. No
  concurrent forms-inputs changes were modified or attributed to this sets revision.

Required formatting/linting was run after these edits:
`uv run ruff format .` and `uv run ruff check --fix .` (results recorded in the handoff).
No changelog entry is warranted. No commit was made.

### Worker 2 re-verification

The two fixes are independently verified; the final status is `verified`.

- `uv run pytest --no-cov tests/forms/test_sets.py -q` — 62 passed.
- `uv run pytest --no-cov tests/forms/test_inputs.py tests/forms/test_resolvers.py -q` — 98
  passed. The earlier `pascalize_token` `NameError` reported in the Worker 1 handoff did not
  reproduce on this rerun; the concurrent `forms/inputs.py` dirty work was preserved and not
  edited by this worker.

Direct probes also passed:

- Plain snapshot: after declaring a mutation with `FormA`, changing live `Meta.form_class` to
  `FormB` still left `_mutation_form_fields` on `FormA`; finalization materialized `FormAInput`
  with only `alpha`, and the default constructor returned `FormA`.
- ModelForm snapshot: the same post-declaration mutation kept the validated
  `ItemFormA` basis (`name`, `category`) rather than switching to `ItemFormB`
  (`name`, `is_private`).
- Validation-time live `Meta`: a child declaration inheriting a parent snapshot but declaring
  `Meta.form_class = FormB` and `fields = ("beta",)` validated successfully as `FormB`; the
  `cls.__dict__` own-snapshot check did not leak the parent's `FormA` snapshot.
- Lazy signature: after mutating live `Meta.form_class`, `DjangoMutationField` still exposed
  `data: Annotated[ForwardRef('FormAInput'), strawberry.lazy(...)]`, matching the frozen input.
- Non-callable hooks: `get_form_fields = None` and `get_form_fields = "not-callable"` each
  raised the typed `ConfigurationError` naming the required callable classmethod on both
  `DjangoFormMutation` and `DjangoModelFormMutation`.

The permanent tests cover the same plain/ModelForm and `None`/string matrix. No production or
test changes were made by Worker 2, and the concurrent `forms/inputs.py` changes remain
untouched.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
