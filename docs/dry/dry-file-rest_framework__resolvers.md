# DRY review: `django_strawberry_framework/rest_framework/resolvers.py`

Status: verified

## System trace

`rest_framework/resolvers.py` owns the **serializer-flavor write runtime** (spec-039
Slice 3): decode / construct / validate / save callbacks that ride the shared
`mutations/resolvers.py::run_write_pipeline_sync` skeleton. It does **not** own
locate, authorize-before-decode, `transaction.atomic`, optimizer re-fetch, or
payload assembly — those stay in the skeleton.

Serializer-specific ownership in this file:

- **Decode** — serializer-field-keyed `provided_data` via
  `decode_provided_fields` + flavor handlers; relation single/multi through
  `decode_visible_relation` / batched `visible_related_objects`; nested
  recursion; uploads into `data` (not a form `files=` split).
- **Error flatten** — iterative, budgeted `serializer_errors_to_field_errors`
  (DRF nested `errors` / `ValidationError.detail` → `FieldError`, reverse-mapped
  to GraphQL names; leaf via shared `utils/errors.py::field_error`).
- **Hook freeze + merge** — `_frozen_hook_view` / `UploadMetadata` /
  `SerializerHookContext` (types live in `hook_context.py`); framework-owned
  `data` / `instance` / `partial` / `context["request"|"write_alias"]` merge in
  `_merged_serializer_kwargs`.
- **Pre-write guards** — schema/runtime agreement, write-source ownership,
  relation queryset pin+visibility+lock, validator queryset pin, relation-intent
  ledger.
- **Write** — nested-atomic `serializer.save()` with DRF / Django /
  `IntegrityError` routing; write witness; saved-result checks; post-save
  relation attestation.
- **Entries** — `resolve_serializer_sync` → skeleton; async via
  `make_resolver_entries(_run_serializer_pipeline_sync)`.

Connected behavior examined:

- `mutations/resolvers.py` — write-pipeline skeleton owner; integrity mapper
  import; `make_resolver_entries`.
- `forms/resolvers.py` — sibling flavor: same single-relation spine +
  `decode_provided_fields`; different multi strategy / null policy /
  `files=` / partial reconstruction; already rides the skeleton for ModelForm.
- `rest_framework/hook_context.py` — frozen hook context + upload metadata
  types (evidence only; correct owner).
- `rest_framework/inputs.py` / `sets.py` / `serializer_converter.py` — bind
  specs, kinds, consumer hooks, resolver wiring.
- `utils/write_values.py` / `querysets.py` / `errors.py` /
  `write_transaction.py` — already-promoted shared decode / visibility / leaf /
  phase helpers.
- Tests / live — `tests/rest_framework/test_resolvers.py`; live products
  serializer mutations in `examples/fakeshop/test_query/test_products_api.py`.

## Verification

Searches / comparisons (package-wide):

- `run_write_pipeline_sync` / `resolve_serializer_sync` / form ModelForm
  entry — serializer already delegates; no second orchestration body.
- `decode_visible_relation` / `decode_provided_fields` — already shared with
  forms; this file only supplies serializer destination policy.
- `_decode_relation_multi` vs form `_decode_form_relation_multi` — same
  security outcome (hidden/missing → uniform relation `FieldError`), different
  query strategy (batched pk vs per-element object for `to_field_name`) and
  null policy. `write_values.py` documents multi staying at flavors.
- `serializer_errors_to_field_errors` vs `validation_error_to_field_errors` —
  shared leaf; DRF nested structure + reverse map is serializer-only.
- `_frozen_hook_view` vs flattener iterative stack — similar control-flow
  shape, different domains (immutable data view vs error walk); abstracting
  needs mode flags.
- Nested walkers (agreement / ownership / scope / intent / attest) — same
  tree shape, distinct per-level work; a generic walker would obscure
  ownership.
- `_write_surface_specs` — documented as the one list for top-level
  disciplines, but agreement was split into two loops, instrumentation walked
  input+injected separately, and write-source ownership inlined the concat.
  Same change axis (what counts as the write surface) lived in four spellings.

Item-scoped baseline diff at start: empty for this file. Concurrent dirty
paths elsewhere left untouched.

Focused proof (`--no-cov`):

- `tests/rest_framework/test_resolvers.py -k "agreement or injected_field or write_surface"`

## Opportunities

### O1 — Single write-surface walk for agreement / intent / ownership

- **Repeated responsibility:** "top-level write surface = GraphQL input specs ∪
  `Meta.injected_fields` specs" — one set every pre-`is_valid` discipline must
  cover identically.
- **Sites:** `_write_surface_specs` (owner); `_assert_schema_runtime_agreement`
  + `_assert_injected_field_agreement` (split loops); `_instrument_relation_intent`
  (two walks); `_guarded_serializer_write` ownership call (inline concat).
- **Evidence:** docstring of `_write_surface_specs` already names the
  disciplines; injected and input agreement called the same
  `_assert_field_agreement`; scope/attest already used the owner; write path
  called both agreement helpers then rebuilt the list by hand.
- **Owner:** `_write_surface_specs` in this file.
- **Consolidation:** expand `_assert_schema_runtime_agreement` to walk
  `_write_surface_specs` (rev6 #1 + #2); delete `_assert_injected_field_agreement`;
  instrument and ownership call sites consume the owner only.
- **Proof:** package tests for schema agreement + injected agreement (now via
  the one helper); write-surface empty-injected walk; existing live serializer
  product tests remain the end-to-end tier.
- **Risks / non-goals:** reverse map for error rekeying stays input-only
  (injected fields are not GraphQL wire names). Do not fold form plain-body
  orchestration or batched form M2M here.

## Judgment

The large serializer-specific machinery (freeze, flattener, intent ledger,
witness, attestation) is correctly local: it encodes DRF contracts the model/
form flavors do not share. Shared pipeline / decode / error-leaf ownership is
already upstream. The real drift was incomplete adoption of
`_write_surface_specs` — fixed in this pass.

Rejected / deferred candidates:

1. **Plain-form / delete fold onto `run_write_pipeline_sync` (spec-046 C2 /
   C1)** — skeleton generalization owned by `mutations/resolvers.py`; forms
   review already deferred. Serializer create/update already rides the
   skeleton. Forward.
2. **Promote `_decode_relation_multi` into `utils/write_values.py`** —
   `write_values` deliberately leaves multi strategy at flavors; form needs
   related objects for `to_field_name`. Reject / keep local.
3. **Move `serializer_errors_to_field_errors` to `utils/errors.py`** — sole
   consumer family is this module; shared leaf already in utils. Keep.
4. **Unify frozen-view + error-flattener iterative walkers** — different
   domains; a shared walker needs mode flags. Reject.
5. **Generic nested-serializer walker for agreement/scope/intent/attest** —
   same tree, different per-node rules; helper would obscure ownership.
   Reject.
6. **Fold `hook_context.py` into this file (or reverse)** — evidence only;
   types are the public frozen hook contract, correctly separate. Keep.
7. **Unify serializer three-`except` save mapping with
   `save_or_field_errors`** — DRF-first class routing is serializer-specific.
   Reject.

## Implementation (Worker 1)

- **Owner:** `_write_surface_specs` + `_assert_schema_runtime_agreement` in
  `rest_framework/resolvers.py`.
- **Migrated:** deleted `_assert_injected_field_agreement`; write-step calls
  one agreement walk; `_instrument_relation_intent` and
  `_assert_runtime_write_source_ownership` consume `_write_surface_specs`.
- **Tests:** agreement helpers carry both spec lists; injected agreement tests
  call the merged helper; noop rewritten as empty-injected write-surface walk.
- **Kept separate:** reverse-map build (input-only); form C2; multi-decode
  flavor strategies; hook_context module; flattener / freeze / ledger bodies.
- **Validation:** `uv run ruff format` + `ruff check --fix` on edited paths;
  focused pytest `-k "agreement or injected_field or write_surface" --no-cov`.
- **Changelog:** no — internal ownership completion, no public contract change.

## Independent verification (Worker 2)

Re-traced serializer write runtime against `mutations/resolvers.py::run_write_pipeline_sync`,
`forms/resolvers.py` sibling flavor, `utils/write_values.py` / `errors.py`, bind stash in
`rest_framework/sets.py` / `inputs.py`, and the item-scoped baseline diff. Challenged O1 and
every deferred / rejected candidate.

1. **Is `_write_surface_specs` consolidation real and complete?** **Yes.** Pre-fix the
   docstring already named one list for top-level disciplines, but agreement was two helpers
   both calling `_assert_field_agreement`, instrument walked input then injected, and ownership
   inlined the concat. Post-fix every write-surface discipline
   (agreement / ownership / scope / intent instrument / intent assert / M2M snapshot /
   attestation) consumes `_write_surface_specs`; the only remaining production
   `_input_field_specs`-only walks are decode and reverse-map build — GraphQL wire surface,
   not write surface. Package-wide search shows no leftover
   `_assert_injected_field_agreement` and no other inline
   `[*_input_field_specs, *_injected_field_specs]` outside the owner.
2. **Did merging agreement change the Meta early-return contract?** **Acceptable / better.**
   Deleted helper skipped when `Meta.injected_fields` was falsy; the merged walk uses the
   stashed `_injected_field_specs or []`. Bind keeps Meta and stash aligned; walking stash is
   the correct source of truth if they ever diverge.
3. **Deferred C2 / C1 (plain-form / delete onto skeleton)?** **Correct to keep deferred.**
   Serializer create/update already rides `run_write_pipeline_sync`. Fold ownership is
   `mutations/resolvers.py` + forms plain-form body (spec-045); verified on those items.
   Implementing here would be out-of-scope half-fold.
4. **Rejected multi-decode / flattener / generic walker / hook_context /
   `save_or_field_errors` unify?** **All hold.** `write_values.py` documents multi strategy at
   flavors (batched pk vs `to_field_name` objects + null policy). Flattener owns DRF nested
   structure + reverse map; leaf already shared. Freeze vs error walk and nested
   agreement/scope/intent/attest share tree shape, not per-node rules. `hook_context.py` is
   the public frozen-hook types module. Serializer three-`except` save maps DRF ValidationError
   before Django / IntegrityError — not the IntegrityError-only `save_or_field_errors` helper.
5. **Tests?** Focused
   `tests/rest_framework/test_resolvers.py -k "agreement or injected_field or write_surface"
   --no-cov` → **15 passed**. Injected agreement tests call the merged helper; fixtures carry
   both stash lists; noop rewritten as empty-injected write-surface walk.

Disposed (non-blocking):

- **No joint input+injected agreement FakeMut:** composition is concatenation of two already-
  tested walks through one owner; scope/intent suites already exercise both sides together.
  Not required for verification.
- **Repeated `_write_surface_specs()` calls in `_guarded_serializer_write`:** pure concat, not
  a second change axis; caching would be micro-optimization, not DRY.

**Outcome:** verified. Plan item checked.

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
