# DRY review: folder `django_strawberry_framework/mutations/`

Status: verified

## System trace

`mutations/` is the model write component and the shared write-flavor substrate
(spec-036 / riders in forms + rest_framework + auth): Meta-declared mutations
materialize inputs/payloads at phase 2.5, expose `DjangoMutationField`, and run
authorize → decode → validate → write → payload under one managed transaction
(schema completion-spanning atomic is outer; pipeline `transaction.atomic` +
`write_pipeline` is inner — distinct owners, already verified at `schema.py`).

Present-day folder shape (~4315 lines across six modules; fresh pass, not a
recap of file artifacts):

- `__init__.py` (34) — four-symbol public surface (`DjangoMutation`,
  `DjangoMutationField`, `DjangoModelPermission`, `FieldError`). `DenyAll` stays
  internal (plain-form default install).
- `inputs.py` (687) — `FieldError`, editable-column generators, shape identity
  (`mutation_input_shape` / `MutationInputShape`), payload builder
  (`build_payload_type` model + model-less), materialize ledger via
  `make_input_namespace` (clear owner `mutations.input_namespace`,
  `before_bind=True`).
- `sets.py` (1467) — `DjangoMutation` + metaclass factory
  (`make_meta_validating_metaclass` / `make_declaration_registry`), Meta
  validation, declaration registry (clear owner `mutations.declarations`),
  per-pass shape cache via `make_shape_build_cache` (clear owner
  `mutations.shape_cache`), bind (`bind_mutations`), and cross-flavor Meta /
  construction helpers (`resolver_seams`, `cached_build_input`,
  `build_and_stash_input`, `NON_DELETE_*`, `validate_select_for_update`, …).
- `permissions.py` (212) — `DjangoModelPermission`, `DenyAll`, sync-bool auth
  contract (`_require_sync_bool_auth_result`), `run_permission_classes`
  (shared with plain-form base).
- `resolvers.py` (1608) — model pipeline + shared `run_write_pipeline_sync` /
  `make_resolver_entries` / `error_payload_builder` / authorize + payload
  helpers consumed by form / serializer / auth; model-only `_run_delete` and
  decode/write steps stay local.
- `fields.py` (307) — `DjangoMutationField`, duck-typed family guard,
  `_lazy_ref` / `build_lazy_field_signature` (shared with auth fixed fields),
  `MUTATION_CLASS_MARKER` for schema atomicity.

Lifecycle ownership (three clear owners, no competing ledgers):

| Owner key | Module | Role |
| --- | --- | --- |
| `mutations.input_namespace` | `inputs.py` | materialize ledger; `before_bind=True` |
| `mutations.declarations` | `sets.py` | declaration registry |
| `mutations.shape_cache` | `sets.py` | per-pass build cache; also cleared at top of `bind_mutations()` |

Connected behavior re-traced as evidence (not rewritten unless mutations is
true owner): `forms/sets.py` / `forms/resolvers.py` (ModelForm rides
`run_write_pipeline_sync` + `bind_mutations`; plain-form keeps F6 body +
`bind_form_mutations`); `rest_framework/sets.py` / `resolvers.py` (serializer
rider); `auth/mutations.py` (register rider + fixed-field factories over
fields helpers); `utils/write_transaction.py` / `utils/querysets.py` /
`utils/permissions.py` / `utils/inputs.py`; `schema.py` outer atomic;
`tests/mutations/` + live fakeshop write tests.

Folder-level axes: duplicated policy across modules; state ownership; competing
helper layers; inconsistent public flavors; lifecycle work repeated at several
phases; sibling still-open folders (`rest_framework/`, `types/`, `utils/`)
traced only as evidence.

## Verification

- Item-scoped baseline `e10db2cc49b160606692dd236e8e48eeaa3c387c`:
  `git diff e10db2cc… -- django_strawberry_framework/mutations/` is empty at
  pass start and after this review. Concurrent dirty paths outside this item
  left untouched. Plan checkbox not edited (Worker 2).
- Re-read all six mutations sources end-to-end. Grepped package for
  `run_write_pipeline_sync`, `_run_plain_form_pipeline_sync`, `_run_delete`,
  `make_shape_build_cache` / `_shape_build_cache`, `register_subsystem_clear`
  owners under `mutations.`, `_VALID_OPERATIONS` /
  `NON_DELETE_WRITE_OPERATIONS` / `_OPERATION_PERMISSION_ACTION`,
  `error_payload_builder`, `cached_build_input` / `resolver_seams` /
  `build_lazy_field_signature`, and operation-literal gates in fields /
  resolvers / permissions.
- Confirmed present-day shape cache already rides
  `make_shape_build_cache()` + `register_subsystem_clear(...,
  owner="mutations.shape_cache")` with bind-time clear retained — three-flavor
  lifecycle parity with `forms.shape_cache` / `rest_framework.shape_cache`.
  Proof site already present:
  `tests/mutations/test_sets.py::test_mutation_shape_build_cache_clears_via_registry_and_direct_clear`.
- Compared forms + rest_framework + auth as riders: model-backed create/update
  already share `run_write_pipeline_sync`; alias / auth / write-phase
  invariants already share `pipeline_alias_guard` / `authorization_phase` /
  `pipeline_write_phase` even on plain-form and delete. Remaining structural
  folds are spec-051 C1/C2 (`docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md`
  Slice 3), not a mutations-folder-only owner today.
- Did not seed findings from the prior artifact as truth; used it only to
  preserve the audit trail under Iterations. Did not concatenate file
  artifacts.
- No production `.py` edit → ruff not required. No pytest (not the gate).

## Opportunities

None — present-day folder already has clear ownership per phase (declare →
materialize → field → authorize/decode/validate/write/payload), three
subsystem-clear owners, and the shared substrate riders consume
(`run_write_pipeline_sync`, `resolver_seams`, `run_permission_classes`,
`build_lazy_field_signature`, `make_shape_build_cache`). No folder-visible
policy remains split across modules inside this remit without mode flags or
crossing into still-open sibling / spec-051 ownership.

### Rejected / deferred (freshly re-proved)

1. **Fold plain-form onto `run_write_pipeline_sync` (spec-051 C2).** Skeleton
   docstring scopes F6 to model-backed create/update; plain path has no locate,
   no `primary_type`, no object-slot refetch, and builds `{ ok, errors }` via
   `payload_cls(ok=…)` rather than `build_payload(slot, …)`. Alias / auth /
   write-phase helpers are already shared. Absorbing the body needs model-less
   / ok-payload / `tail_step` seams co-designed with C1 under spec-051 Slice 3.
   Owner is not mutations-folder-only today. Defer.

2. **Package-wide OPERATIONS vocabulary across sets / permissions / fields /
   resolvers.** Meta allow-lists (derived in-file from
   `NON_DELETE_OPERATION_INPUT_KIND`), Django perm action map
   (`_OPERATION_PERMISSION_ACTION`), GraphQL arg gates (including the `"form"`
   sentinel), and resolver verb branches are distinct change axes. Coupling
   them would force lockstep edits for independent reasons; permissions → sets
   import would also cycle. Reject.

3. **Unify `error_payload_builder` with plain-form `{ok: false}` rollback
   closure.** Same rollback invariant, different payload constructor. Belongs
   with C2's ok-builder, not a thin relocate. Defer with C2. Owner of the
   plain-form body is `forms/resolvers.py` (still-open sibling evidence).

4. **Fold `_run_delete` onto the write skeleton (spec-051 C1).** Snapshot-
   before-delete + no decode/write steps; pairs with C2's `tail_step`. Shared
   helpers already cover alias / auth / write-phase / error envelope. Defer.

5. **Merge `bind_mutations` / `bind_form_mutations`.** Plain bind keeps
   `_primary_type=None`, different `build_input` arity, ok-payload via
   `build_payload_type(object_type=None)`. Mode flags would hide Decision 6.
   Reject. Plain drain owns `forms/sets.py`.

6. **Route model shape cache through `cached_build_input`.** Forms need
   guard-before-cache + `(input_cls, specs)` values; model caches the class
   alone and has no per-declaration guard. Forcing the model path through the
   helper would invent a dummy payload / no-op guard. Reject.

7. **Collapse `_reject_generated_input_collisions` with
   `_audit_mutation_input_surface`.** Build-time generated-field collisions vs
   materialize-time final Strawberry surface (including merged consumer
   fields) are distinct lifecycle gates. Reject.

8. **Schema outer atomic vs pipeline inner atomic.** Distinct contracts
   (completion-spanning schema transaction vs per-pipeline managed write +
   rollback marking). Already verified at `schema.py`. Reject as duplication.

## Judgment

`mutations/` is a deliberately layered write substrate: inputs own generation
+ materialize, sets own declaration + bind + cross-flavor Meta helpers,
permissions own write-auth classes, resolvers own the runtime pipeline +
shared skeleton, fields own the factory + lazy signature. After file-pass
consolidations and the prior shape-cache lifecycle parity (already present at
ITEM_BASELINE), no folder-owned consolidation remains. C1/C2 stay with
spec-051 Slice 3; OPERATIONS stays multi-axis. Zero production edit. Ready
for Worker 2.

## Implementation (Worker 1)

- **Zero-edit.** No production paths changed.
- **Artifact only:** this file rewritten for present-day six-module source;
  prior 2026-07-16 pass preserved under Iterations.
- **Validation:** no `.py` edit → ruff not required. No pytest (not the gate;
  no new behavior).
- **Item-scoped diff statement:** against
  `e10db2cc49b160606692dd236e8e48eeaa3c387c`, only
  `docs/dry/dry-folder-mutations.md` changes for this item
  (`django_strawberry_framework/mutations/` remains empty vs baseline).
- **Changelog:** N/A (no code change).
- **Deferred pytest:** none owed (no production edit). Existing
  `tests/mutations/` + live fakeshop write tests remain the standing proof of
  the folder contracts (shape-cache clear probe included).

## Iterations

### Iteration 2026-07-16 (prior folder pass — shape-cache consolidation)

Status at close of that Worker 1 pass: fix-implemented. ITEM_BASELINE then:
`0bfec1992a2339477f8b318023d0c260979dff9e`.

Accepted consolidation: model `_shape_build_cache` migrated onto
`utils/inputs.py::make_shape_build_cache` +
`register_subsystem_clear(..., owner="mutations.shape_cache")`; bind-time
clear retained; docstring +
`test_mutation_shape_build_cache_clears_via_registry_and_direct_clear` added.
Migrated sources then: `mutations/sets.py`, `utils/inputs.py`,
`tests/mutations/test_sets.py`.

Rejected / deferred then (and re-proved above against present-day source):
plain-form C2 fold; OPERATIONS vocabulary; error-payload ok-builder with C2;
delete C1 fold; bind-drain merge.

A Worker 2 section in that pass claimed verified and plan-checkbox marked, but
the active `dry-0_0_13.md` folder item is still open and this cycle treats the
folder as a **fresh** integration of present-day source (~4315 lines) without
seeding findings from that pass as truth. Shape-cache parity is confirmed
already landed at the current ITEM_BASELINE (empty mutations/ diff).

### Iteration 2026-08-15 (Worker 1 — fresh folder integration)

Re-traced present-day `mutations/` as one component against ITEM_BASELINE
`e10db2cc49b160606692dd236e8e48eeaa3c387c`. Confirmed clear ownership of
input namespace / declarations / shape cache; shared substrate already
consumed by forms / serializer / auth riders; C1/C2 correctly owned by
spec-051 Slice 3; OPERATIONS multi-axis reject stands. Item-scoped
`mutations/` diff vs baseline empty; artifact-only update. Status →
`fix-implemented` for Worker 2; plan checkbox left for Worker 2.

## Independent verification (Worker 2)

Re-traced `mutations/` as one component (all six modules: `__init__`,
`inputs`, `sets`, `permissions`, `resolvers`, `fields`) against forms /
rest_framework / auth riders, `schema.py::DjangoMutationExecutionContext`,
`utils/write_transaction.py`, and `tests/mutations/test_sets.py` shape-cache
proof. Did not treat Worker 1 findings as proven. Item-scoped
`git diff e10db2cc49b160606692dd236e8e48eeaa3c387c --
django_strawberry_framework/mutations/` is empty; line totals match
(~4315). No production edit.

**Folder ownership.** Inputs own generation + materialize ledger
(`mutations.input_namespace`, `before_bind=True`); sets own declaration
registry + per-pass shape cache + cross-flavor Meta / bind helpers
(`mutations.declarations`, `mutations.shape_cache`); permissions own
write-auth classes + `run_permission_classes`; resolvers own runtime
pipeline + shared `run_write_pipeline_sync` / `error_payload_builder` /
`make_resolver_entries`; fields own `DjangoMutationField` +
`build_lazy_field_signature` / `MUTATION_CLASS_MARKER`. Public `__all__` is
the four-symbol surface. No competing ledger or helper layer inside the
folder.

**Challenged reject 1 — fold plain-form onto `run_write_pipeline_sync` (C2).**
**Deferral stands.** Skeleton is F6-scoped to model-backed create/update
(`primary_type`, locate, refetch, `build_payload(slot, …)`). Plain body in
`forms/resolvers.py::_run_plain_form_pipeline_sync` has no locate / object
slot and builds `{ ok, errors }` via `payload_cls(ok=…)`. Present-day source
already shares `pipeline_alias_guard` / `authorization_phase` /
`pipeline_write_phase` (so spec-051 Decision 6's "gains guards" framing is
stale relative to today's code); remaining work is structural seams under
spec-051 Slice 3, not a mutations-folder-only consolidation. Nit: Rejected
#3's "still-open sibling" label for `forms/` is wrong — forms folder is
already verified; ownership of the plain body remains `forms/resolvers.py`.

**Challenged reject 2 — package-wide OPERATIONS vocabulary.**
**Reject stands.** `_VALID_OPERATIONS` / `NON_DELETE_*` (Meta allow-lists),
`_OPERATION_PERMISSION_ACTION` (Django perm verbs), fields GraphQL arg gates
(including `"form"`), and resolver verb branches are distinct change axes;
sets docstring already documents the non-unification. Coupling would force
lockstep edits and risk a permissions ↔ sets import cycle.

**Challenged reject 3 — unify `error_payload_builder` with plain `{ok:false}`.**
**Deferral stands.** Same `set_rollback` invariant, different constructor
(`build_payload(slot, …)` vs `payload_cls(ok=False, …)`). Belongs with C2's
ok-builder, not a thin relocate into mutations.

**Challenged reject 4 — fold `_run_delete` onto skeleton (C1).**
**Deferral stands.** Delete keeps snapshot-before-delete + no decode/write
steps; already shares `error_payload_builder` / alias / auth / write-phase.
Pairs with C2 `tail_step` under spec-051 Slice 3.

**Challenged reject 5 — merge `bind_mutations` / `bind_form_mutations`.**
**Reject stands for this folder pass.** Drain loops are thin; bind bodies
differ (`_primary_type`, input arity, ok-payload via
`build_payload_type(object_type=None)`). Spec-051 C5
(`bind_write_declarations`) may still land a thin drain helper later — not
a present-day folder-owned must-fix, and not a Decision-6 body merge.

**Challenged reject 6 — route model shape cache through `cached_build_input`.**
**Reject stands.** Model `_materialize_input_for` caches the class alone with
no per-declaration guard; forms/serializer need guard-before-cache +
`(input_cls, specs)` values. Forcing the model path invents a dummy payload /
no-op guard. Shape-cache lifecycle already rides `make_shape_build_cache` +
`register_subsystem_clear(..., owner="mutations.shape_cache")` with
bind-time clear; proof site
`tests/mutations/test_sets.py::test_mutation_shape_build_cache_clears_via_registry_and_direct_clear`.

**Challenged reject 7 — collapse collision audit helpers.**
**Reject stands.** `_reject_generated_input_collisions` is build-time model
field collapse; `_audit_mutation_input_surface` is materialize-time final
Strawberry surface (including merged consumer fields). Distinct lifecycle
gates.

**Challenged reject 8 — schema outer vs pipeline inner atomic.**
**Reject stands.** `DjangoMutationExecutionContext` completion-spanning
atomic + `managed_write_transaction` is distinct from pipeline
`transaction.atomic` + `write_pipeline` rollback marking. Distinct owners /
contracts.

**Missed consolidations searched.** Grepped shared substrate symbols, rider
call sites, operation literals, dual atomics, and bind/cache helpers. No
folder-visible policy remains split across mutations modules without mode
flags or crossing into still-open siblings (`rest_framework/`, `types/`,
`utils/`) or unbuilt spec-051 Slice 3.

**Disposition:** verified. Plan checkbox marked `[x]`.
