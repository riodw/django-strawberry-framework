# DRY review: `django_strawberry_framework/mutations/resolvers.py`

Status: verified

Iteration 2026-07-16: internal sync-boundary imports now target the canonical
utils owner directly, and the permission-class/auth-alias gate is single-sited
in `utils/permissions.py`. Independent verification is complete.

## System trace

`mutations/resolvers.py` owns the **write-pipeline runtime skeleton** and the
model flavor's decode / write / delete bodies (spec-036 Slice 3, spec-039 P1.5):

- **`run_write_pipeline_sync`** — F6-scoped shared create/update orchestration
  (`atomic` + `write_pipeline` → locate → authorize-before-decode →
  `decode_step` / `write_step` → pk-drift check → `refetch_optimized` →
  object-slot `build_payload`). Ridden by the model dispatcher, ModelForm, and
  serializer flavors via decode/write callbacks.
- **`error_payload_builder` / `build_payload` / `payload_cls_for`** — rollback-
  then-envelope for object-slot payloads; success/error instantiation.
- **Model decode / write** — `_decode_relations` (+ relation visibility /
  existence / null guards), `_model_decode_step`, `_model_write_step`,
  `forced_save_or_field_errors`, `save_or_field_errors`,
  `_full_clean_or_field_errors`.
- **`_run_delete`** — snapshot-before-delete body (F6-scoped out of the create/
  update skeleton); same BETA-055 alias / auth / write-phase helpers.
- **Auth / async entries** — `authorize_or_raise` (consumes
  `permissions._require_sync_bool_auth_result`); `run_pipeline_async` →
  `utils/querysets.run_in_one_sync_boundary` (re-exported from this module for
  historical callers); `make_resolver_entries` →
  `resolve_mutation_sync` / `resolve_mutation_async`.

Connected behavior examined:

- `forms/resolvers.py` — ModelForm rides the skeleton; plain form keeps a
  local `{ ok, errors }` atomic body but already calls
  `pipeline_alias_guard` / `authorization_phase` / `pipeline_write_phase` /
  `require_managed_write` (forms DRY O1; Decision 6 *behavior* landed early).
- `rest_framework/resolvers.py` — serializer create/update rides the skeleton;
  bespoke sync entry, shared async via `make_resolver_entries`.
- `mutations/permissions.py` — sync-bool auth result owner;
  `authorize_or_raise` is the GraphQLError gate only.
- `mutations/sets.py` / `fields.py` / `inputs.py` — bind, field factory,
  payload slot / `FieldError` types.
- `utils/querysets.py` — true owner of `run_in_one_sync_boundary`; this file
  re-exports (must not reverse).
- `utils/write_transaction.py` / `write_values.py` / `errors.py` — phase
  helpers, scalar/relation decode primitives already extracted.
- `auth/mutations.py` / `schema.py` — import the canonical
  `utils/querysets.py::run_in_one_sync_boundary` owner directly (register also
  rides `run_write_pipeline_sync`); this module retains only a compatibility
  re-export.
- Tests / live — `tests/mutations/test_resolvers.py`,
  `tests/forms/test_resolvers.py` (plain-form phase), live products mutation
  APIs (`createItem` / form / serializer / `submitContact`).

ITEM_BASELINE `f3921b78660e4535c27c2a4e16def96e0c0af25e`: target matched baseline
at review start. Concurrent WIP already present in the working tree (vs HEAD):
`_require_sync_bool_auth_result` adoption + `run_in_one_sync_boundary`
re-export from utils — left untouched.

## Verification

Searches: `run_write_pipeline_sync`, `_run_plain_form_pipeline_sync`,
`error_payload_builder`, `_run_delete`, `make_resolver_entries`,
`run_pipeline_async`, `run_in_one_sync_boundary`, `authorize_or_raise`,
`pipeline_alias_guard`, `authorization_phase`, `open_write_pipeline`,
`tail_step`, `spec-046` C1/C2 / Decision 6 across package + tests +
`docs/spec-046-boundary_dry_squeeze-0_0_16.md`.

Compared contracts:

- **Model / ModelForm / serializer create-update** — same skeleton; only
  decode/write callbacks differ. Already consolidated.
- **Plain form vs skeleton** — shared BETA-055 *helpers* already; remaining
  parallel is orchestration shape (`payload_cls(ok=…)` vs object-slot
  `build_payload`; no `primary_type` / locate / refetch / `authorized_pk`).
  Absorbing it needs a model-less + ok-payload seam, not a mode flag on the
  current F6 body. Spec-046 C2 pairs that fold with C1 (`tail_step`) after
  Slice-2 B4 (`open_write_pipeline`) substrate. Decision 6's security goal
  (alias guard + auth phase) is already satisfied at the forms call site —
  confirmed by forms file + folder W2.
- **Delete vs skeleton** — locate / auth / alias / write-phase twin of create/
  update, but snapshot-before-delete + no decode/write callbacks. Spec-046 C1
  (`tail_step`), not a solo opportunistic extract.
- **`run_in_one_sync_boundary`** — definition in `utils/querysets.py`; this
  module re-exports. Auth / schema / filters / orders / root permissions all
  consume the utils owner directly now (auth / schema import
  `..utils.querysets` at module scope; no in-repo caller reaches through this
  re-export). Preserving the re-export is correct for historical / external
  importers; reversing ownership would re-introduce a mutations→read-side
  dependency.
- **`error_payload_builder` ↔ plain `_error_payload`** — same
  `set_rollback` then envelope rule, different payload constructor. Belongs
  with the C2 ok-builder, not a one-site thin relocate.
- **`require_write_pipeline` error text** (utils) still names only
  `run_write_pipeline_sync / _run_delete` — wording understatement; plain form
  also opens `write_pipeline`. Not a second implementation of a rule; drive-by
  string edit out of this item's ownership.

No scratch under `docs/dry/temp-tests/`: contract comparison + prior focused
plain-form phase tests + spec-045 sequencing sufficed. Permanent proof of the
already-landed Decision 6 behavior lives in
`tests/forms/test_resolvers.py`
(`test_plain_form_rejects_write_sql_outside_the_write_phase`,
`test_plain_form_perform_mutate_may_write_inside_the_write_phase`) and live
`submitContact` / `submitPing`.

Rejected / deferred candidates:

1. **Fold plain-form onto `run_write_pipeline_sync` (spec-046 C2)** — deferred
   (see Opportunities "None" + Judgment). True owner is this file; fold is
   real but premature without C1's `tail_step` / model-less / ok-payload seams
   and B4's `open_write_pipeline`. Decision 6 behavior already closed.
2. **Fold `_run_delete` onto the skeleton (spec-046 C1)** — deferred with C2;
   needs the shared `tail_step` design, not a half-baked locate/auth extract.
3. **Promote ok-envelope builder beside `error_payload_builder` alone** —
   single plain-form caller; consolidating the closure without deleting the
   parallel orchestration moves code without removing a change axis. With C2.
4. **Extract `open_write_pipeline` now (spec-045 B4)** — mechanical substrate
   for C1/C2; implementing it here without migrating plain/delete leaves the
   deferred fold unfinished and churns the skeleton surface mid-cycle. Defer
   to the sequenced card.
5. **Reverse `run_in_one_sync_boundary` ownership back into this file** —
   rejected; utils is the neutral owner (explicit assignment + existing
   read-side consumers).
6. **Unify model / form / serializer relation decode** — deliberate flavor
   coloring over `decode_visible_relation` / membership helpers; D3 is the
   contract-level re-expression. Reject for this file pass.
7. **Touch concurrent `_require_sync_bool_auth_result` / sync-boundary WIP** —
   already correct consumption; out of scope.

## Opportunities

None — every confirmed shared responsibility this file owns is already
single-sited for model-backed create/update (skeleton + entries + auth gate +
error envelope). The deferred plain-form / delete structural folds are real
consolidations owned here, but implementing them now would invent mode-flagged
or half-finished seams ahead of the co-designed C1+C2 surface in
[spec-045][spec-045] Slice 3 (after B4). Decision 6's behavioral gap is already
closed at `forms/resolvers.py::_run_plain_form_pipeline_sync` without folding.

## Judgment

Zero-edit. The write skeleton correctly owns model-backed create/update for
three flavors; plain-form and delete keep distinct orchestration for distinct
payload / lifecycle contracts while sharing BETA-055 helpers. Preserve the
utils ownership of `run_in_one_sync_boundary` and the concurrent permissions
sync-bool wiring. Ready for Worker 2.

## Implementation (Worker 1)

- **Zero-edit.** No production, test, or export changes.
- **Owner chosen:** n/a — no accepted consolidation for this pass.
- **Kept separate / deferred:** plain-form ↔ `run_write_pipeline_sync` (C2;
  Decision 6 behavior already at forms call site); delete ↔ skeleton (C1);
  ok-envelope builder with C2; `open_write_pipeline` (B4); relation-decode
  flavor coloring; concurrent permissions / sync-boundary WIP.
- **Preserved:** `run_in_one_sync_boundary` re-export from
  `utils/querysets.py`; `_require_sync_bool_auth_result` consumption.
- **Validation:** item-scoped
  `git diff f3921b78660e4535c27c2a4e16def96e0c0af25e --
  django_strawberry_framework/mutations/resolvers.py` empty at finish
  (artifact-only). No ruff (no Python edits). No pytest.
- **Changelog:** no.
- **Concurrent paths preserved:** edits only this artifact. Pre-existing WIP
  on `mutations/resolvers.py` (vs HEAD) and sibling dirty files left alone.
  Plan checkbox not touched.

## Independent verification (Worker 2)

Re-traced `mutations/resolvers.py` as the write-pipeline runtime owner
(`run_write_pipeline_sync`, `error_payload_builder` / `build_payload`, model
decode/write, `_run_delete`, `authorize_or_raise`, `run_pipeline_async` /
`make_resolver_entries`) against forms / serializer riders, `_run_plain_form_pipeline_sync`,
`utils/querysets.py::run_in_one_sync_boundary` consumers, and
[spec-046][spec-046] C1/C2 / Decision 6 / B4 sequencing.

**Zero-edit diff confirmed.**
`git diff f3921b78660e4535c27c2a4e16def96e0c0af25e --
django_strawberry_framework/mutations/resolvers.py` is empty (0 bytes). Working
tree vs HEAD still shows concurrent WIP (`_require_sync_bool_auth_result` +
`run_in_one_sync_boundary` re-export from utils) — that content is already in
`ITEM_BASELINE`, not introduced by this item.

### Challenges

1. **Should this item have implemented the plain-form fold (spec-046 C2)?**
   **No — deferral stands.** Independently compared
   `forms/resolvers.py::_run_plain_form_pipeline_sync` to
   `run_write_pipeline_sync`: shared BETA-055 *helpers* already
   (`require_managed_write` → `atomic` + `write_pipeline` →
   `pipeline_alias_guard` → `authorization_phase` → `pipeline_write_phase`).
   Remaining parallel is orchestration shape only — `{ ok, errors }` vs
   object-slot `build_payload`, no `primary_type` / locate / refetch /
   `authorized_pk`. Absorbing it now needs a model-less + ok-payload seam
   (and pairs with C1 `tail_step` after B4 `open_write_pipeline`). Doing it
   here would invent mode flags or half-finished seams ahead of the
   co-designed Slice-3 surface — the DRY.md anti-pattern. Decision 6's
   *security* goal (alias guard + auth phase) already closed at the forms
   call site (forms file + folder W2); C2's leftover is structural, not a
   re-open of that gap.

2. **Should `run_in_one_sync_boundary` ownership reverse back into this file?**
   **No.** Definition is `utils/querysets.py::run_in_one_sync_boundary`
   (neutral, cycle-safe). Read-side already imports the utils owner
   (`filters/sets.py`, `orders/sets.py`, root `permissions.py`);
   `auth/mutations.py` / `schema.py` now import the utils owner directly as
   well, so no in-repo caller reaches through this module — the re-export is
   retained only for historical / external importers.
   `tests/utils/test_querysets.py::test_run_in_one_sync_boundary_is_single_sourced_from_utils`
   pins identity. Reversing ownership would re-introduce a mutations→read-side
   dependency the promotion removed.

### Missed opportunities (independent search)

- Grepped package resolvers for `set_rollback` / `pipeline_alias_guard` /
  `authorization_phase` / `require_managed_write` / `run_write_pipeline_sync` /
  `_run_plain_form` / `error_payload_builder` / `run_in_one_sync_boundary`.
  No second skeleton, no inlined sync-boundary wrapper, no plain-form body
  skipping the shared phases.
- **`error_payload_builder` ↔ plain `_error_payload`:** same rollback-then-envelope
  rule, different constructor — belongs with C2's ok-builder, not a thin
  one-site relocate this pass.
- **`_run_delete` ↔ skeleton:** locate/auth/alias twin, snapshot-before-delete
  lifecycle differs — C1 `tail_step`, not a solo extract.
- **`require_write_pipeline` error text** still names only
  `run_write_pipeline_sync / _run_delete` while plain form also opens
  `write_pipeline` — wording understatement in `utils/write_transaction.py`,
  not a second rule implementation; drive-by string edit out of this item's
  ownership (same disposition as forms W2).
- Relation-decode flavor coloring (model / form / serializer) remains
  deliberate over shared membership primitives — reject for this file pass.

No production edits. Plan item checked.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[spec-046]: ../spec-046-boundary_dry_squeeze-0_0_16.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
