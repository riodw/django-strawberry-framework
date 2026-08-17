# Review: `django_strawberry_framework/forms/resolvers.py`

Status: verified

## Understanding

`django_strawberry_framework/forms/resolvers.py::_decode_form_data` consumes the
bind-time `InputFieldSpec` reverse map and produces Django-form-keyed `data` plus
an independent `files` mapping. Relation values route through
`utils/write_values.py::decode_visible_relation`, which type-checks and
visibility-checks both Relay and raw-pk ids before projecting a resolved object
through `to_field_name`. `_reconstruct_partial_data` rebuilds omitted
`ModelForm` fields from the located row, preserving files through the bound
form's instance initial state and normalizing M2M / `to_field_name` relations to
the same shape as provided values.

`_run_modelform_pipeline_sync` and `_run_plain_form_pipeline_sync` provide only
form-specific decode/write callbacks to
`mutations/resolvers.py::run_write_pipeline_sync`. That shared skeleton owns the
managed transaction, alias guard, locate-before-authorize ordering, error
rollback, and ModelForm post-save refetch. The form callbacks construct one form,
call `is_valid()` once, map `form.errors` through
`validation_error_to_field_errors` (including the `NON_FIELD_ERRORS` /
`"__all__"` sentinel), then write through `save_or_field_errors`. The async entry
from `make_resolver_entries` executes the same sync body in one
`sync_to_async(thread_sensitive=True)` boundary.

The current resolver revision also reads the mutation-owned
`get_form_fields()` basis during decode and partial reconstruction. That
revision belongs to the concurrent forms-inputs hook work, not this review item.

## Verification

- Traced callers in `forms/sets.py`, the generated field dispatch in
  `mutations/fields.py`, the shared orchestration in
  `mutations/resolvers.py`, and the alias/phase implementation in
  `utils/write_transaction.py`.
- Traced relation decoding through `utils/write_values.py::type_check_relation_id`,
  `utils/write_values.py::decode_visible_relation`, and
  `utils/querysets.py::visible_related_object`; hidden, missing, wrong-model,
  and uncoercible ids all collapse to the relation field's `FieldError`.
- Examined update lookup and not-found behavior through
  `mutations/resolvers.py::coerce_lookup_id` and
  `mutations/resolvers.py::locate_instance`. Lookup is visibility-scoped,
  malformed ids fail before a query, and hidden rows are indistinguishable from
  missing rows.
- Examined form construction and exception paths:
  `forms/resolvers.py::_bound_form_or_field_errors` constructs once and validates
  once; `_modelform_write_step` uses `form.save()`; `_plain_form_write_step`
  uses `perform_mutate`; `IntegrityError` is converted to the in-band envelope;
  non-validation hook exceptions leave the shared atomic boundary and are not
  silently converted.
- Existing tests cover ModelForm versus plain Form payloads, sync and async
  execution, repeated success/failure invocation, relation visibility for Relay
  and raw-pk single and multi branches, `to_field_name`, null relation values,
  malformed relation ids, form field and non-field errors, write-time
  `IntegrityError`, construction hooks, update reconstruction, authorization
  ordering, alias/write-phase enforcement, and optimized post-save refetch.
- Focused verification before this artifact-only edit:
  `uv run pytest --no-cov tests/forms/test_resolvers.py -q` — 52 passed.
- Complete form-subsystem verification:
  `uv run pytest --no-cov tests/forms -q` — 184 passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

No resolver-owned correctness or security defect was confirmed. The form
pipeline delegates shared locate/authorize/transaction/refetch behavior rather
than reimplementing it; its form-specific relation decoder closes the raw-pk
visibility branch, partial reconstruction keeps omitted values valid, and both
form flavors preserve the shared error-envelope and write-phase contracts.

## Implementation (Worker 1)

No review-owned production or permanent-test change was necessary. The artifact
records the evidence for the existing implementation and the focused
verification results above.

Concurrent boundaries preserved:

- `django_strawberry_framework/forms/resolvers.py` had concurrent changes from
  the mutation-owned `get_form_fields()` revision: the module-level import was
  removed and `_decode_form_data` / `_reconstruct_partial_data` now read
  `mutation_cls.get_form_fields()`. Those hunks were not altered or
  re-attributed.
- `django_strawberry_framework/forms/inputs.py` and `forms/sets.py` contained
  the same concurrent field-basis revision and were left untouched.
- `tests/forms/test_resolvers.py` contained a concurrent
  `test_plain_form_expired_deadline_rejects_before_perform_mutate_write` test
  plus its imports; it was preserved unchanged.
- All unrelated dirty files present at dispatch were left untouched. No
  changelog update or commit was made.

## Independent verification (Worker 2)

Status: verified

I independently re-traced the resolver's sync and async entries, the shared
locate/authorize/decode/write/refetch skeleton, both `ModelForm` and plain
`Form` riders, relation-id visibility and projection, partial reconstruction,
error-envelope mapping, write-phase enforcement, and context cleanup. No
resolver-owned correctness, security, transaction, or parity defect was found.

Evidence:

- `uv run pytest --no-cov tests/forms/test_resolvers.py -q` — 52 passed.
- `uv run pytest --no-cov tests/forms -q` — 184 passed.
- A deterministic subset covering repeated calls, async `ModelForm` and plain
  `Form` execution, authorization-before-relation-decode, `to_field_name`
  partial reconstruction, and explicit-null M2M handling — 6 passed.
- Disposable probes under
  `docs/review/temp-tests/_worker2_forms_resolvers/` — 4 passed: a stable
  `get_form_fields()` injected relation paired with a matching `get_form()`
  override decoded and validated successfully; `_reconstruct_partial_data`
  honored the custom field basis and `to_field_name`; and a raised
  `get_form()` exception left `current_write_pipeline()` cleared so a repeated
  call succeeded.
- The post-bind drift probe (monkeypatching `get_form_fields()` to remove a
  relation field) produced a raw `KeyError` during decode. That is an
  intentional violation of the documented `get_form_fields()` contract, which
  requires a stable, request-independent field mapping; it is not a
  review-owned behavior defect in the supported contract.
- `git --no-pager diff --check -- django_strawberry_framework/forms/resolvers.py tests/forms/test_resolvers.py` — clean.

The only dirty hunks in the target files remain the concurrent
`mutation_cls.get_form_fields()` basis revision and its deadline test/imports;
they were preserved unchanged. No production changes or commits were made.

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
