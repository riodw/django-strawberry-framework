# Pre-BETA review: forms/

Scope: the Django Form/ModelForm integration -- `converter.py` (form-field ->
GraphQL input), `inputs.py`, `resolvers.py` (form-backed write pipeline),
`sets.py` (`DjangoFormMutation` declaration + binding).

Method: full logic read of `resolvers.py` in `docs/shadow/current/` plus the
diffs since `0.0.13` (this cycle rebased `FormFieldConversion` onto the shared
`FieldConversionBase`, moved the write-value decoders into `utils/`, and routed
permission execution through `mutations/permissions.py::run_permission_classes`).
Read-only; no tests run.

Bottom line: solid. m2m is delegated to Django's own `form.save()` (so save
ordering is correct by construction), the write runs in the shared atomic
pipeline, and partial updates are reconstructed to work around ModelForm's
all-or-nothing validation. No P0 or P1.

## P0 -- correctness suspicions

None found.

## P1 -- fix before BETA

None found.

## P2 -- polish / hardening

### `resolvers.py::_reconstruct_partial_data` -- unprovided fields are seeded from the instance and re-validated
Confidence: low (document + verify one edge). A ModelForm validates *all* its
fields, so for an update the resolver rebuilds full form data from the current
instance (`model_to_dict` for scalars, current keys for m2m and
`to_field_name` relations) and overlays the provided fields. This makes partial
updates work, but it means an *unprovided* field whose current stored value is
invalid under the form (e.g. a field that gained a stricter validator after the
row was written) will fail validation even though the client did not touch it.
This is inherent to reusing ModelForm validation for partial updates; document
the behavior, and confirm the intended resolution is "the client must send a
valid value" rather than silently excluding the field.
Verify: store a row, tighten a field's validator, then update a *different*
field and observe whether the untouched field's stale value blocks the mutation.

### `resolvers.py` FileField handling -- confirm the multipart contract end to end
Confidence: low. `_file` handlers route file inputs into `provided_files` and
the form is built with `files=provided_files`. The live multipart path is
exercised by the test client; make sure a BETA acceptance test covers an actual
`FileField`/`ImageField` ModelForm mutation over HTTP (not just the in-process
form), since file handling is a common integration gap.

## API & consistency notes

- The plain-form path (`_run_plain_form_pipeline_sync`, non-Model forms) and the
  ModelForm path diverge on payload shape (`ok`/`errors` vs the object payload):
  the plain path returns `payload_cls(ok=..., errors=...)`. Confirm this
  `ok`-flag payload is documented as the non-Model form contract so consumers
  know which shape they get.
- Error mapping goes through the same `validation_error_to_field_errors` as the
  mutations path (via `form.errors.as_data()`), so form field errors share the
  vocabulary of the other write families. Good consistency.

## Verified sound (do not re-flag)

- m2m save ordering: `_modelform_write_step` calls `save_or_field_errors(form.save)`
  with Django's default `commit=True`, so Django's ModelForm machinery performs
  the instance save and `save_m2m()` in the correct order -- there is no manual
  save/save_m2m sequencing to get wrong, and it all runs inside the shared
  pipeline's `transaction.atomic()`.
- Relation visibility: `_decode_form_relation_single`/`_multi` resolve through
  the shared `decode_visible_relation`, so a form ModelChoiceField cannot bind a
  hidden row (same IDOR posture as mutations/rest_framework).
- `_to_form_key_value` honors `to_field_name` (uses `serializable_value`),
  falling back to pk -- so non-pk `to_field_name` relations round-trip correctly.
- Async parity via `make_resolver_entries` -> `run_in_one_sync_boundary`
  (`sync_to_async(thread_sensitive=True)`), so form/ORM work stays in a sync
  boundary off the event loop.

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
