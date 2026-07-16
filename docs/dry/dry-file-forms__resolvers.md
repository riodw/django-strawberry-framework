# DRY review: `django_strawberry_framework/forms/resolvers.py`

Status: verified

Iteration 2026-07-16: the permission-class/auth-alias gate is now single-sited
in `utils/permissions.py::auth_aliases_for_permission_classes`. Independent
verification is complete.

## System trace

`forms/resolvers.py` owns the form-flavor write runtime (spec-038 Slice 3):

- **Decode** — `_decode_form_data` walks bind-stashed `_input_field_specs`
  (`utils/inputs.py::InputFieldSpec`) via `decode_provided_fields`, splitting
  scalars / relations / files into FORM-field-keyed `provided_data` +
  `provided_files`. Relation branches color
  `utils/write_values.py::decode_visible_relation` with form `empty_values` skip
  + `to_field_name` projection (`_to_form_key_value`); multi maps the single
  decoder (null/`empty_values` → `[]`, deliberate form semantics).
- **Partial update reconstruction** — `_reconstruct_partial_data` rebuilds a
  full bound `data=` from the located row (scalars/`to_field_name`-less FK via
  `model_to_dict`; M2M + `to_field_name` FK via `_to_form_key_value`) so
  omitted fields bind byte-compatibly with provided ones.
- **ModelForm pipeline** — `_run_modelform_pipeline_sync` rides
  `mutations/resolvers.py::run_write_pipeline_sync` with form `decode_step` /
  `write_step` (`get_form` → `is_valid` → `form.save` under
  `pipeline_write_phase`, errors via `_form_errors_to_field_errors` →
  `validation_error_to_field_errors`).
- **Plain-form pipeline** — `_run_plain_form_pipeline_sync` keeps a model-less
  atomic block (`{ ok, errors }` payload, no locate / refetch) but calls the
  same BETA-055 helpers as every other write flavor:
  `pipeline_alias_guard` + `authorization_phase` + `pipeline_write_phase`
  around `perform_mutate`.
- **Entries** — `resolve_form_sync` / `resolve_form_async` via
  `make_resolver_entries(_run_form_pipeline_sync)`.

Connected behavior examined:

- `mutations/resolvers.py` — shared skeleton (`run_write_pipeline_sync`,
  `authorize_or_raise`, `save_or_field_errors`, `payload_cls_for`,
  `make_resolver_entries`, `error_payload_builder`); model relation decode
  deliberately weaker on raw-pk visibility; delete hand-rolls the same alias /
  auth / write-phase pattern the plain form now mirrors.
- `rest_framework/resolvers.py` — sibling serializer coloring of
  `decode_visible_relation` / `decode_provided_fields` / skeleton; batched M2M
  visibility; files land in `data=` (not `files=`).
- `utils/write_values.py`, `utils/write_transaction.py`, `utils/errors.py` —
  already-extracted decode spine + transaction phases + validation mapper.
- `forms/sets.py` — bases delegate `resolve_*` here; `get_form` /
  `get_form_kwargs` / `perform_mutate` hooks.
- `forms/inputs.py` / `forms/converter.py` — reverse-map + kind constants
  (`InputFieldSpec` migration already landed).
- Tests — `tests/forms/test_resolvers.py` (package pipeline); live
  `examples/fakeshop/test_query/test_products_api.py` (`createItemViaForm` /
  `updateItemViaForm` / `submitContact` / `submitPing`).

ITEM_BASELINE `42ea700d5e3032b0e057ee0ddafe22acee591efb`: target matched baseline
at review start (InputFieldSpec rename already present). Concurrent dirty
`mutations/resolvers.py` left untouched.

## Verification

Searches: `run_write_pipeline_sync`, `_run_plain_form`, `error_payload_builder`,
`pipeline_alias_guard`, `authorization_phase`, `pipeline_write_phase`,
`decode_visible_relation`, `decode_provided_fields`, `_to_form_key_value`,
`_form_errors_to_field_errors`, `reconstruct_partial`, `perform_mutate`,
`form.errors.as_data` across package + tests + live products API.

Compared contracts:

- Form vs serializer relation single — same spine, different `skip` /
  `project` (form `empty_values` + `to_field_name`; serializer `None` + `pk`).
- Form vs serializer relation multi — form per-element (needs objects for
  `to_field_name`; null clears via `empty_values`); serializer batched pk
  visibility + rejects whole-list null differently. Intentional.
- Form vs model M2M null — form allows null→`[]` (Django form empty); model
  rejects null (`_relation_null_error`). Documented divergence.
- Plain form vs `run_write_pipeline_sync` — shared locate/refetch/slot
  skeleton cannot absorb `{ ok, errors }` without a model-less seam (owned by
  `mutations/resolvers.py`; planned as spec-046 C2). Local body stays; phase
  helpers are called.

Focused proof (`--no-cov`):

- `test_plain_form_rejects_write_sql_outside_the_write_phase`
- `test_plain_form_perform_mutate_may_write_inside_the_write_phase`
- `test_plain_form_valid_returns_ok_true`
- `test_plain_form_perform_mutate_integrity_error_maps_to_envelope`

Rejected / deferred candidates:

1. **Fold `_run_plain_form_pipeline_sync` onto `run_write_pipeline_sync`** —
   true consolidation of orchestration (spec-046 C2). Owner is
   `mutations/resolvers.py` (skeleton generalization for model-less / ok
   payload). Concurrent dirty on that file; assignment forbids consolidating
   sibling-owned pieces here. Forward.
2. **`error_payload_builder` ↔ plain-form `_error_payload`** — same
   `set_rollback` then envelope rule, different payload shape (`slot` vs
   `ok=`). Promoting an ok-builder belongs beside `error_payload_builder` in
   `mutations/resolvers.py`. Forward with C2.
3. **Batched form M2M visibility (serializer `_decode_relation_multi`)** —
   form needs related objects for `to_field_name`; batching would still
   re-fetch or change projection ownership. Reject.
4. **Unify form / model M2M-null policy** — deliberate form-vs-model contract
   (Decision 8). Reject.
5. **Extract shared `get_form` + `is_valid` glue between ModelForm write step
   and plain body** — two lines of construct/validate around different write
   hooks and payload builders; a helper would obscure flavor ownership.
   Reject.
6. **`_form_errors_to_field_errors` → `utils/errors`** — sole caller family is
   this module; thin adapter over the shared mapper. Keep local. Reject.
7. **`_to_form_key_value` elsewhere** — form-only projection; no second site.
   Reject.

## Opportunities

### O1 — Plain-form pipeline adopts shared BETA-055 phase helpers

- **Repeated responsibility:** write pipelines must (a) pin SQL to one alias
  under `pipeline_alias_guard`, (b) wrap permission evaluation in
  `authorization_phase`, (c) open `pipeline_write_phase` only around the
  flavor save. The model / ModelForm / serializer / delete paths already
  obey this; the plain-form body opened `write_pipeline` but skipped the
  guard / auth phase / write phase — an incomplete re-encoding of the same
  invariant, not a deliberate exemption.
- **Sites:** `forms/resolvers.py::_run_plain_form_pipeline_sync` (gap);
  `mutations/resolvers.py::run_write_pipeline_sync` and `_run_delete`
  (reference call pattern); helpers in `utils/write_transaction.py` /
  `utils/permissions.py::auth_aliases_for_permission_classes` (the gate that
  returns `frozenset()` for an empty `permission_classes` opt-out, else
  `resolve_auth_aliases()`).
- **Evidence:** before the fix, a `clean_*` ORM write on the pinned alias
  succeeded during plain-form validation; ModelForm path rejects the same
  shape via the skeleton's guard. Docstrings on the plain body never
  defended the exemption.
- **Owner:** call-site adoption belongs in this file (it owns the
  model-less body). Skeleton fold that would delete the parallel
  orchestration remains owned by `mutations/resolvers.py` (forwarded above).
- **Consolidation:** wrap authorize / decode / validate / write in
  `pipeline_alias_guard`; wrap `authorize_or_raise` in
  `authorization_phase(auth_aliases)`; wrap `perform_mutate` in
  `pipeline_write_phase`. Keep the local atomic + `{ ok, errors }` envelope.
- **Proof:** package tests above (phase rejection + write-window success);
  existing plain-form envelope / IntegrityError / auth-denial tests still
  pass. Live `submitContact` / `submitPing` already cover the happy / deny
  wire; phase violation is not earnable on the stock products forms without
  polluting the example.
- **Risks / non-goals:** behavior change for plain-form permission backends
  that issued auth-alias SQL (now force-rolled-back inside
  `authorization_phase`, matching other flavors). Does not fold onto
  `run_write_pipeline_sync` (C2). Does not touch concurrently dirty
  `mutations/resolvers.py`.

## Judgment

Form decode / ModelForm skeleton riding / shared write_values helpers are
already at their true owners. The one warranted change owned by this file was
closing the plain-form BETA-055 phase gap by calling the existing helpers.
Larger orchestration merge with the model-less skeleton stays forwarded to
`mutations/resolvers.py`. Ready for Worker 2.

## Implementation (Worker 1)

- **Owner chosen:** `forms/resolvers.py::_run_plain_form_pipeline_sync` adopts
  `pipeline_alias_guard` / `authorization_phase` / `pipeline_write_phase` /
  `auth_aliases_for_permission_classes` (transaction helpers unchanged; the
  `permission_classes`-gated alias helper is new in `utils/permissions.py`).
- **Migrated:** plain-form authorize → decode → validate → `perform_mutate`
  body; module imports.
- **Tests:** `tests/forms/test_resolvers.py` —
  `test_plain_form_rejects_write_sql_outside_the_write_phase`,
  `test_plain_form_perform_mutate_may_write_inside_the_write_phase`.
- **Kept separate:** local `{ ok, errors }` atomic orchestration (not folded
  onto `run_write_pipeline_sync`); form vs serializer / model relation
  contracts; concurrent `mutations/resolvers.py` edits.
- **Validation:** focused pytest `--no-cov` (4 passing); `ruff format` +
  `ruff check --fix` clean on edited paths.
- **Changelog:** no — invariant completion; maintainer decides if BETA-055
  plain-form hardening warrants a note.
- **Item-scoped diff vs baseline:**
  `django_strawberry_framework/forms/resolvers.py`,
  `tests/forms/test_resolvers.py`,
  `docs/dry/dry-file-forms__resolvers.md`.

## Independent verification (Worker 2)

Re-traced `_run_plain_form_pipeline_sync` against `run_write_pipeline_sync`,
`_run_delete`, `_modelform_write_step`, and the BETA-055 helpers in
`utils/write_transaction.py` / `utils/permissions.py::auth_aliases_for_permission_classes`.
Item-scoped diff vs `42ea700d5e3032b0e057ee0ddafe22acee591efb` is exactly the
plain-form phase adoption + the two package tests claimed.

### Challenges

1. **Same alias / auth / write-phase contract as ModelForm / model / serializer /
   delete?** **Confirmed.** Plain form now sequences
   `require_managed_write` → `atomic` + `write_pipeline` →
   `auth_aliases_for_permission_classes(meta.permission_classes)` →
   `pipeline_alias_guard` spanning authorize / decode / validate / write →
   `authorization_phase` around the single `authorize_or_raise` →
   `pipeline_write_phase` only around `perform_mutate` (mirrors ModelForm's
   write-phase around `form.save` with `get_form` / `is_valid` outside). Gating
   and helper call pattern match the skeleton and `_run_delete` byte-for-byte on
   the shared phases; model-only locate / `authorized_pk` / refetch / slot
   payload remain correctly absent.

2. **Migration complete for this file's ownership?** **Confirmed.** The prior gap
   (opened `write_pipeline` but skipped guard / auth phase / write phase) is
   closed at the only plain-form body; ModelForm already rides the skeleton;
   no second plain-form orchestration site.

3. **Deferred fold onto `run_write_pipeline_sync`?** **Correct to keep deferred.**
   The skeleton is scoped to model-backed create/update (locate / refetch /
   object-slot `build_payload`); absorbing `{ ok, errors }` needs a model-less
   seam owned by `mutations/resolvers.py` (spec-046 C2). Local atomic +
   `_error_payload(ok=False)` stay. Note: Decision 6's *behavior* (close the
   alias-guard gap) landed early via call-site helper adoption; C2's remaining
   work is the structural fold, not re-closing the security gap.

4. **Tests?** **Confirmed.** Focused `--no-cov` run of
   `test_plain_form_rejects_write_sql_outside_the_write_phase`,
   `test_plain_form_perform_mutate_may_write_inside_the_write_phase`,
   `test_plain_form_valid_returns_ok_true`,
   `test_plain_form_perform_mutate_integrity_error_maps_to_envelope` — 4 passed.
   Phase violation surfaces as top-level GraphQL `ConfigurationError` with
   "OUTSIDE the mutation's write phase"; `perform_mutate` writes succeed.

### Disposed findings

- **`error_payload_builder` ↔ plain `_error_payload`:** same rollback-then-envelope
  rule, different payload shape; belongs beside a future ok-builder with C2.
  Not this file's incomplete migration.
- **`require_write_pipeline` error text** still names only
  `run_write_pipeline_sync / _run_delete` — pre-existing understatement (delete
  already called through `write_pipeline`); stale wording in
  `utils/write_transaction.py`, not a forms/resolvers behavioral gap.
- **No plain-form-specific auth-alias divergent-router test:** helpers are shared
  and covered elsewhere; O1 wiring is proven by the phase write-window tests.
  Live-tier Decision 6 coverage remains a spec-046 C2 concern.
- **Rejected O2–O7** (batched M2M, M2M-null unify, get_form glue,
  `_form_errors_to_field_errors` relocate, `_to_form_key_value` extract):
  contracts still intentionally diverge or have a single caller family.

No production edits. Plan item checked.

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
