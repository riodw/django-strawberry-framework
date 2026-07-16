# DRY review: folder `django_strawberry_framework/mutations/`

Status: fix-implemented

Iteration 2026-07-16: reopened after the canonical sync-boundary import and
permission-class/auth-alias gate migrations; independent folder verification is pending.

## System trace

`mutations/` is the model write component and the shared write-flavor substrate
(spec-036 / riders in forms + rest_framework + auth): Meta-declared mutations
materialize inputs/payloads at phase 2.5, expose `DjangoMutationField`, and run
authorize → decode → validate → write → payload under one managed transaction.

Folder shape:

- `__init__.py` — four-symbol public surface (`DjangoMutation`,
  `DjangoMutationField`, `DjangoModelPermission`, `FieldError`).
- `inputs.py` — `FieldError`, editable-column generators, shape identity
  (`mutation_input_shape`), payload builder, materialize ledger (clear owner
  `mutations.input_namespace`, `before_bind=True`).
- `sets.py` — `DjangoMutation` + metaclass factory, Meta validation, declaration
  registry (clear owner `mutations.declarations`), per-pass shape cache, bind,
  and cross-flavor Meta/construction helpers (`resolver_seams`,
  `cached_build_input`, `NON_DELETE_*`, …).
- `permissions.py` — `DjangoModelPermission`, `DenyAll`, sync-bool auth contract,
  `run_permission_classes`.
- `resolvers.py` — model pipeline + shared `run_write_pipeline_sync` /
  `make_resolver_entries` / auth + payload helpers consumed by form / serializer
  / auth.
- `fields.py` — `DjangoMutationField`, lazy signature helpers shared with auth.

Connected behavior re-traced for this folder pass (not inherited as proven):
`forms/sets.py` / `forms/resolvers.py` (plain-form F6 body + ModelForm rider);
`rest_framework/sets.py` / `resolvers.py` (serializer rider on
`run_write_pipeline_sync`); `utils/inputs.py::make_shape_build_cache`;
`utils/write_transaction.py`; auth mutation holders; live fakeshop write tests
under `examples/fakeshop/test_query/`; package `tests/mutations/`.

Folder-level axes examined: duplicated policy across fields / inputs /
permissions / resolvers / sets; state ownership (input namespace, declarations,
shape cache); competing helper layers; public export flavor; lifecycle work
repeated at several phases; assignment-named deferrals (plain-form C2 fold;
OPERATIONS vocabulary).

## Verification

- Item-scoped baseline `0bfec1992a2339477f8b318023d0c260979dff9e`: working
  tree matched baseline for `mutations/` at pass start (empty item-scoped
  diff). Concurrent dirt vs HEAD on mutations modules is pre-baseline WIP
  (file-pass consolidations: metaclass factory, Meta operation frozenset
  derivation, related helper promotions) — treated as present state, not
  reverted. Concurrent dirty paths outside this item left untouched. Plan
  checkbox not edited.
- Re-read all six mutations sources end-to-end. Grepped package for
  `run_write_pipeline_sync`, `_run_plain_form_pipeline_sync`,
  `make_shape_build_cache` / `_shape_build_cache`, `register_subsystem_clear`
  owners under `mutations.`, `_VALID_OPERATIONS` /
  `NON_DELETE_WRITE_OPERATIONS` / `_OPERATION_PERMISSION_ACTION`, and
  operation-literal gates in fields / resolvers.
- Compared forms + rest_framework as evidence: both already consume
  `make_shape_build_cache()` + `register_subsystem_clear` for their shape
  caches; mutations alone still hand-rolled a module dict cleared only inside
  `bind_mutations()`. `utils/inputs.py::make_shape_build_cache` docstring still
  described the mutation cache as a hand-mirror of that pair.
- Independently re-traced assignment-named deferrals from source (below). Did
  not concatenate file artifacts; used their deferred labels only as search
  flags.
- No full pytest. Ruff format + check after edits.

## Opportunities

### 1. Model shape-build cache on `make_shape_build_cache` (accepted)

- **Repeated responsibility:** per-pass `(cache dict, clear)` for identical
  generated-input shapes, emptied at bind start and on `registry.clear()`.
- **Sites:** `mutations/sets.py::_shape_build_cache` (hand-rolled dict +
  bind-only clear); `forms/sets.py` / `rest_framework/inputs.py` (factory +
  registered clear); `utils/inputs.py::make_shape_build_cache` (declared owner).
- **Evidence:** same lifecycle contract (dedupe by shape identity; clear so
  stale classes never leak). Forms register `forms.shape_cache`; serializer
  registers `rest_framework.shape_cache`. Mutations cleared only in
  `bind_mutations()`, so a `registry.clear()` without a following bind left
  stale entries — the exact gap the form docstring documents as why the clear
  is registered. File reviews did not surface this because each cache site was
  in-scope for a different file/folder.
- **Owner:** `mutations/sets.py` consuming `make_shape_build_cache`.
- **Consolidation:** `_shape_build_cache, clear_mutation_shape_build_cache =
  make_shape_build_cache()`; `register_subsystem_clear(...,
  owner="mutations.shape_cache")`; keep `bind_mutations()` top-of-pass clear;
  align `make_shape_build_cache` docstring.
- **Proof:**
  `tests/mutations/test_sets.py::test_mutation_shape_build_cache_clears_via_registry_and_direct_clear`
  (direct clear + `registry.clear()` empty the same dict). Existing bind /
  dedupe / retry-idempotent tests remain the shape-identity guards. Lifecycle
  plumbing is not newly earnable over live `/graphql`.
- **Risks / non-goals:** do not merge the three flavor caches; do not change
  cache key/value shapes (mutations still cache the class alone; forms cache
  `(input_cls, specs)`).

### Rejected / deferred (re-proved)

1. **Fold plain-form onto `run_write_pipeline_sync` (spec-046 C2).** Re-proved:
   skeleton docstring scopes F6 to model-backed create/update; plain path has
   no locate, no `primary_type`, no object-slot refetch, and builds
   `{ ok, errors }` via `payload_cls(ok=…)` rather than `build_payload(slot, …)`.
   Alias / auth / write-phase invariants already share
   `pipeline_alias_guard` / `authorization_phase` / `pipeline_write_phase`.
   Absorbing the body needs model-less / ok-payload / `tail_step` seams
   co-designed with C1 (`_run_delete`) under spec-046 Slice 3 — ownership is
   not clear for a mutations-folder-only change today. Defer.

2. **Package-wide OPERATIONS vocabulary across sets / permissions / fields /
   resolvers.** Re-proved: Meta allow-lists (already derived in-file from
   `NON_DELETE_OPERATION_INPUT_KIND`), Django perm action map, GraphQL arg
   gates (including the `"form"` sentinel), and resolver verb branches are
   distinct change axes. Coupling them would force lockstep edits for
   independent reasons; permissions → sets import would also cycle. Reject.

3. **Unify `error_payload_builder` with plain-form `{ok: false}` rollback
   closure.** Same rollback invariant, different payload constructor. Belongs
   with C2's ok-builder, not a thin relocate. Defer with C2.

4. **Fold `_run_delete` onto the write skeleton (spec-046 C1).** Snapshot-
   before-delete + no decode/write steps; pairs with C2's `tail_step`. Defer.

5. **Merge `bind_mutations` / `bind_form_mutations`.** Plain bind keeps
   `_primary_type=None`, different `build_input` arity, ok-payload. Mode flags
   would hide Decision 6. Reject.

## Judgment

Folder-visible lifecycle ownership for the model shape cache was the one
remaining three-flavor asymmetry after file-pass consolidations: forms and
serializer already used `make_shape_build_cache` + subsystem clear; mutations
did not. That consolidation is implemented. Assignment-named C2 / OPERATIONS
items stay correctly deferred or rejected — C2 still needs the co-designed
skeleton surface in spec-045; OPERATIONS remains multi-axis.

## Implementation (Worker 1)

- **Owner chosen:** `mutations/sets.py` consuming
  `utils/inputs.py::make_shape_build_cache`, clear owner
  `mutations.shape_cache`.
- **Migrated sources:**
  - `django_strawberry_framework/mutations/sets.py` — factory pair +
    `register_subsystem_clear`; bind-time clear retained.
  - `django_strawberry_framework/utils/inputs.py` —
    `make_shape_build_cache` docstring (no longer claims a hand-mirror).
  - `tests/mutations/test_sets.py` — clear/registry probe + fixture docstring.
- **Behavior kept separate:** three flavor caches stay disjoint; plain-form /
  delete orchestration; multi-axis operation verbs outside Meta allow-lists;
  public four-symbol `__init__` surface.
- **Validation:** `uv run ruff format .` + `uv run ruff check --fix .`. No
  full pytest. Worker 1 added the focused test without executing it; later
  independent verification ran the focused mutation tests (results below).
- **Changelog:** no (no maintainer authorization).
- **Concurrent paths preserved:** only the cycle paths above edited. Pre-
  existing WIP under other packages / plan checkbox / forms sources not
  touched. Item-scoped diff vs ITEM_BASELINE is this artifact plus the three
  files above.

## Independent verification (Worker 2)

Re-traced `mutations/` as one component against ITEM_BASELINE
`0bfec1992a2339477f8b318023d0c260979dff9e` and the three-file scoped diff
(`sets.py` / `utils/inputs.py` / `tests/mutations/test_sets.py`). No production
edits.

### Shape-cache consolidation — accepted

- Factory pair + `register_subsystem_clear(..., owner="mutations.shape_cache")`
  matches `forms.shape_cache` and `rest_framework.shape_cache`. Bind still
  clears at top of `bind_mutations()`; registry clear now empties the same
  dict (the gap forms already documented).
- Value of the change is lifecycle parity, not fewer lines: a bare module dict
  cleared only in bind left stale classes after `registry.clear()` without a
  following bind.
- Three flavor caches stay disjoint; mutations still cache the class alone.
  `before_bind=False` matches forms (serializer's `before_bind=True` is the
  pre-finalize prime path — not a mutations miss).
- Proof: `test_mutation_shape_build_cache_clears_via_registry_and_direct_clear`
  and `tests/utils/test_inputs.py::test_make_shape_build_cache_returns_dict_and_clear`
  both passed (`uv run pytest … --no-cov`).

### C2 deferral — re-challenged, kept

Plain `_run_plain_form_pipeline_sync` still differs on locate / `primary_type` /
object-slot refetch / `{ok, errors}` vs `build_payload`. Alias / auth /
write-phase helpers are already shared. Folding needs model-less / ok-payload /
`tail_step` seams with C1 under spec-046 Slice 3 — not a mutations-folder-only
owner today. Note: Decision 6's alias-guard behavior is already present on the
plain path; remaining C2 work is structural. Defer stands.

### OPERATIONS rejection — re-challenged, kept

Meta allow-lists (`_VALID_OPERATIONS` / `NON_DELETE_*` from the input-kind map),
`_OPERATION_PERMISSION_ACTION` (Django add/change/delete), fields GraphQL arg
gates (including `"form"`), and resolver verb branches are distinct change
axes. `sets.py` already imports `permissions`; a permissions→sets OPERATIONS
table would cycle. Reject stands.

### Missed folder-level consolidations

Searched subsystem clears under `mutations.*`, pipeline / bind / OPERATIONS
sites, and rider consumers. No further folder-owned consolidation warranted
now. Remaining deferred items (C1 delete fold, error-payload ok-builder with
C2, bind-drain merge) stay with spec-045 / prior reject reasons.

### Disposition

All accepted and rejected findings disposed. Status → verified; plan checkbox
marked.
