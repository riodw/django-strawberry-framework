# Review: `django_strawberry_framework/forms/`

Status: verified

## Understanding

The folder is one write component with deliberately separated phases. `forms/sets.py` validates and snapshots the declaration, registers the plain-form ledger or rides the model mutation ledger, and binds both flavors during finalizer phase 2.5. `forms/inputs.py` resolves one effective field basis, derives stable shape/name identity, builds the create or partial Strawberry input, and stashes `InputFieldSpec` rows. `forms/resolvers.py` consumes those exact specs to decode GraphQL names into Django form-field names, split uploads into `files=`, project relations through `to_field_name`, reconstruct omitted `ModelForm` state, and hand only form-specific decode/write steps to the shared transaction pipeline. `forms/converter.py` owns only model-less `forms.Field` conversion and the shared form requiredness rule.

The declaration-to-schema path is coherent across the folder boundary. The validated `Meta.form_class` snapshot is used by the default discovery hook and constructor; custom `get_form_fields()` results are normalized once per call and receive a mutation-specific cache discriminator. The same effective names drive narrowing guards, generated input names, shape caches, materialization, and the bind-stashed reverse map. Model-backed fields delegate to the model-column input converters, while plain fields use the form converter; both land in the form namespace, whereas payloads remain in `mutations.inputs`.

At execution, `DjangoMutationField` synthesizes the lazy input/payload signature before finalization, and the finalizer materializes both namespaces before Strawberry freezes the schema. ModelForm mutations use `run_write_pipeline_sync` for locate → authorize → decode → construct/validate → save → optimized refetch. Plain forms intentionally retain a model-less `{ok, errors}` tail, but now share the managed transaction, alias guard, authorization phase, and write-phase helpers. The async entry wraps the same sync body in one thread-sensitive boundary.

## Verification

- Read all five forms modules end-to-end and followed their callers through `mutations/sets.py`, `mutations/fields.py`, `mutations/resolvers.py`, `mutations/permissions.py`, `utils/inputs.py`, `utils/write_values.py`, `utils/write_transaction.py`, `types/finalizer.py`, and `schema.py`.
- Compared every dirty forms/test hunk with `git show HEAD:<path>`; the dirty converter/input/set/resolver and test changes are prior file-pass work, including the `forms/inputs.py` effective-name freeze and hook revision. No review-owned production or test hunk was mixed into that work.
- Rechecked the cross-file invariants: one effective basis and reverse map; frozen form-class identity; exact-vs-validating `NullBooleanField` nullability; form/model converter separation; stable lazy namespace and collision policy; required/default/partial semantics; relation visibility for Relay and raw-pk values; `to_field_name` and M2M reconstruction; form `files=` routing; authorization-before-decode; alias pinning and write-phase enforcement; rollback envelopes; and sync/async parity.
- `uv run pytest --no-cov tests/forms -q` — 191 passed.
- Live products form mutation coverage: `uv run pytest --no-cov examples/fakeshop/test_query/test_products_api.py -q -k 'form or stamped or submit_contact or submit_ping'` — 22 passed.
- Live library form mutation coverage: serial rerun with `uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_library_api.py -q -k 'form or branch_with_shelf or branch_pair'` — 12 passed. An initial xdist invocation hit a worker-process internal error before the library tests ran; the serial run passed and no forms assertion failed.
- Live upload coverage: `uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_uploads_api.py -q -k 'image_via_form'` — 1 passed.
- Existing direct probes and permanent tests cover malformed discovery returns, non-callable hooks, one-shot narrowing iterables, generated-name/materialization collisions, post-declaration `Meta.form_class` mutation, relation decode/reconstruction, authorization ordering, deadline refusal, write-phase rejection, rollback after a partial plain-form write, and async ModelForm/plain-form execution.

## Improvements

### High

None. No transaction, permission, hidden-row, relation-isolation, schema-lifecycle, or public input-contract failure was reproduced.

### Medium

None. The model-less plain-form orchestration remains intentionally separate from `mutations/resolvers.py::run_write_pipeline_sync` because it has no locate/refetch/object slot and returns `{ok, errors}`; its shared phase helpers enforce the same security and transaction policy without inventing a cross-flavor mode flag.

### Low

None.

## Summary

The integrated forms component is internally consistent. Declaration metadata, generated input identity, reverse-map decoding, form binding, validation envelopes, write authorization, transaction/alias policy, and schema finalization agree across both ModelForm and plain Form flavors. The package and live HTTP evidence cover the reachable lifecycle, including uploads, raw-pk and Relay relations, partial M2M preservation, custom construction hooks, authorization denial, and rollback. No folder-owned production fix or permanent test addition is warranted in this pass.

## Implementation (Worker 1)

Zero-edit review cycle. Created this integrated artifact only; no production code, permanent tests, exports, changelog, branch, or commit was changed. Existing dirty forms files and their prior review artifacts were preserved. No changelog entry is warranted.
## Iterations

### Worker 1 revision

Worker 2 found a collection-time contract drift: the dirty `forms/sets.py` revision
called `normalize_form_field_basis()` and threaded `form_fields=` through the
input builders, while `forms/inputs.py` had concurrently regressed to the
HEAD-era surface with only `get_form_fields(form_class)`. This produced an
`ImportError` before the library live form tests could collect.

The consistent discovery-hook contract is restored in the current
`forms/inputs.py`: `_form_field_basis()` and `normalize_form_field_basis()` now
validate hook output; `resolve_effective_form_fields()`,
`build_form_input_class()`, `build_form_inputs()`, both required-field guards,
and required-field discovery accept the stable `form_fields` basis; and the
one-shot effective-name freeze remains in place. `forms/sets.py` therefore has
matching imports/call signatures across declaration validation, cache/build,
naming, and bind. `git show HEAD:django_strawberry_framework/forms/inputs.py`
confirms the hook surface is review/concurrent WIP rather than a committed
baseline API; the current source now matches the already-verified
`rev-forms__inputs.md` / `rev-forms__sets.md` contract.

Permanent tests already present in `tests/forms/test_inputs.py` and
`tests/forms/test_sets.py` cover malformed hook returns, non-callable hooks,
custom basis narrowing/required guards, and one-shot selectors. Revision
validation:

- `uv run pytest --no-cov tests/forms -q` — 191 passed.
- `uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_products_api.py -q -k 'form or stamped or submit_contact or submit_ping'` — 22 passed.
- `uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_library_api.py -q -k 'form or branch_with_shelf or branch_pair'` — 12 passed.

No unrelated source or test path was changed by this revision. The artifact status
is `fix-implemented`; Worker 2 should re-run collection and the focused live
paths against the repaired shared contract.

## Independent verification (Worker 2)

Status: revision-needed

The integrated no-finding conclusion does not hold on the current checkout because
the dirty `forms/sets.py` revision is not loadable with the current
`forms/inputs.py`. This is a cross-file import/API mismatch, not a failing edge-case
assertion.

Evidence:

- `uv run pytest --no-cov tests/forms -q` initially passed (`191 passed in 4.91s`),
  and `uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_products_api.py
  -q -k 'form or stamped or submit_contact or submit_ping'` passed (`22 passed`).
  These runs completed before the current source mismatch was observed.
- The requested live library run,
  `uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_library_api.py -q
  -k 'form or branch_with_shelf or branch_pair'`, then failed during collection:
  `ImportError: cannot import name 'normalize_form_field_basis' from
  django_strawberry_framework.forms.inputs`.
- Re-running `uv run pytest --no-cov tests/forms -q` after that observation failed
  during collection with the same `ImportError`, so the package result is no longer
  reproducible on the current tree. The live upload slice could not be collected
  independently after this import failure.
- `forms/sets.py::_mutation_form_fields` imports and calls
  `normalize_form_field_basis`, and its revised
  `_cached_build_form_input`, `_resolve_effective_form_field_names`,
  `_normalized_form_field_selection`, and `_build_and_stash_form_input` pass
  `form_fields` into the input layer. The current `forms/inputs.py` has no
  `normalize_form_field_basis` or `_form_field_basis`, and its
  `resolve_effective_form_fields`, `build_form_input_class`,
  `build_form_inputs`, `guard_create_required_fields`, and
  `guard_partial_required_column_less_fields` signatures accept no `form_fields`
  parameter. `git show HEAD:django_strawberry_framework/forms/inputs.py` confirms
  those symbols are absent at `HEAD`; after the required repository formatter/lint
  run, both `forms/inputs.py` and `forms/sets.py` are dirty from concurrent work,
  but the symbol/signature mismatch remains.
- Required formatting/linting: `uv run ruff format .` left `423 files unchanged`.
  `uv run ruff check --fix .` exited with two remaining F821 errors in
  `forms/inputs.py` (`relation_input_annotation` and `convert_scalar`), further
  confirming that this source pair is mid-revision. No lint fix was attributed to
  Worker 2 or reverted.
- This prevents import, finalization, generated type materialization, and every
  live ModelForm/plain Form schema path. It also means frozen `Meta`/hook identity,
  relation reverse-map, upload routing, transaction cleanup, and async parity
  cannot be independently re-verified until the two halves are restored to one
  compatible revision.

Recommendation: restore or complete the owning `forms/inputs.py` companion for
the dirty `forms/sets.py` hook revision (without dropping either concurrent edit),
then rerun the complete package forms suite and the live products, library, and
upload slices. No production or permanent-test change was made by Worker 2.

### Worker 2 re-verification (repaired synchronized contract)

Status: verified

The prior collection blocker is resolved in the current source. The repaired
`forms/inputs.py` now imports with `forms/sets.py`; `_form_field_basis()` and
`normalize_form_field_basis()` exist, and
`resolve_effective_form_fields()`, `build_form_input_class()`,
`build_form_inputs()`, `guard_create_required_fields()`, and
`guard_partial_required_column_less_fields()` all accept the threaded
`form_fields` basis. The sets-side hook/cache/name/bind callers and the
input-side signatures now agree.

Evidence:

- Direct import/signature probe:
  `DJANGO_SETTINGS_MODULE=config.settings uv run python - <<'PY' ... PY` —
  both form modules imported; the normalizer and basis helper were present; all
  five threaded signatures exposed `form_fields` where required.
- `uv run pytest --no-cov tests/forms -q` — 191 passed.
- `uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_products_api.py -q
  -k 'form or stamped or submit_contact or submit_ping'` — 22 passed.
- `uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_library_api.py -q
  -k 'form or branch_with_shelf or branch_pair'` — 12 passed.
- `uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_uploads_api.py -q
  -k 'image_via_form'` — 1 passed.
- `uv run pytest --no-cov tests/forms/test_resolvers.py -q -k 'async'` — 3
  passed, covering async ModelForm/plain Form dispatch after the repair.
- A direct adversarial probe passed for post-declaration `Meta.form_class`
  mutation (the frozen `FormA` snapshot remained authoritative), custom
  `get_form_fields()` basis injection through input generation, narrowed/full
  generated-name identity, and `None`/non-pair/malformed-pair hook returns
  raising `ConfigurationError`.
- After `django.setup()`, a real fakeshop schema probe imported `config.schema`,
  confirmed `DjangoSchema`, and found `ItemModelFormInput`,
  `ItemModelFormPartialInput`, `ContactFormInput`,
  `createItemViaForm`, `submitContact`, and
  `createItemWithFileViaForm` in the finalized SDL.
- `git --no-pager diff --check -- django_strawberry_framework/forms
  docs/review/rev-forms.md` — clean. The dirty forms source files remain
  concurrent Worker 1 changes; Worker 2 made no production or permanent-test
  edits and no commit.

The former ImportError and signature drift no longer reproduce. Declaration
snapshotting, hook basis propagation, generated identity/materialization,
relation/upload paths, transaction-backed live writes, schema finalization, and
sync/async parity are independently verified; no remaining folder-owned finding
requires revision.

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
