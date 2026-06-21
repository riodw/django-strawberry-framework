# Review: `django_strawberry_framework/mutations/` (folder pass)

Status: verified

Folder pass over the NEW `mutations/` subpackage (spec-036, shipped 0.0.11): `fields.py`, `inputs.py`, `permissions.py`, `resolvers.py`, `sets.py`, and the package `__init__.py`. All five in-scope siblings are individually `verified` this cycle; there is no prior folder artifact.

**Zero-edit folder pass relative to the cycle baseline.** `git diff 212b2953d1bf046525ea1fabeb84661d5d34b86e -- django_strawberry_framework/mutations/` is EMPTY. The working tree carries one uncommitted hunk vs HEAD — the `sets.py` `_VALID_OPERATIONS` comment correction (`+5/-1`, already verified earlier this run under `rev-mutations__sets.md` shape #4) — but that edit is IN the per-cycle baseline, so the folder-pass diff against baseline is empty. No High, no behaviour-changing Medium, every Low forward-looking/forwarded, GLOSSARY clean for the folder's public surface → genuine no-source-edit folder pass (shape #5). Worker 2 sections filled inline below; both ruff commands run; bare `Status: fix-implemented`.

## DRY analysis

- **Defer-with-trigger — fold `mutations/fields.py::_input_type_name` into `mutations/inputs.py::mutation_input_shape(...).type_name` (KEPT AT FOLDER LEVEL).** `_input_type_name` (`mutations/fields.py::_input_type_name`, lines 113-124) independently re-walks `editable_input_fields(meta.model, fields=, exclude=)` for the selected names AND `editable_input_fields(meta.model)` for the full set, then re-calls `mutation_input_type_name(...)` — byte-for-byte the same name computation `mutations/inputs.py::mutation_input_shape` (lines 393-427) performs to produce `shape.type_name`, the DRY-1 descriptor that exists to single-source exactly this. Both call sites live inside this folder (`fields.py` derives the name; `sets.py::_materialize_input_for` / `_materialize_merged_input` consume `shape.type_name`), so this is a `mutations/`-internal consolidation, not a project-wide one — keep it here. Correctness-neutral today (identical pure-function inputs, names provably agree; verified in `rev-mutations__fields.md` / `rev-mutations__inputs.md`). Consolidation shape: `_input_type_name(meta)` calls `mutation_input_shape(meta.model, _OPERATION_INPUT_KIND[meta.operation], fields=meta.fields, exclude=meta.exclude).type_name` and drops the local two-walk. Do NOT act now: forcing the finalizer-free import-time `fields.py` factory to build a full `MutationInputShape` for a name-only need is heavier than the current two-walk, and the bind/merge path already consumes the descriptor. **Trigger (quote verbatim): "Defer until `mutation_input_type_name`'s identity rule changes OR a fourth name-derivation caller lands; then route `_input_type_name` through `mutation_input_shape(...).type_name`."**

- **Defer-with-trigger — shared mutation `OPERATIONS` verb vocabulary across `sets`/`resolvers`/`permissions`/`fields` (FORWARDED to the project pass `rev-django_strawberry_framework.md`).** The verb literals `"create"` / `"update"` / `"delete"` are spelled inline in four of the five modules: `sets.py::_VALID_OPERATIONS` (`frozenset`, line 93 — the membership single-source for `Meta.operation` validation), `resolvers.py` (equality dispatch `meta.operation == "create"`/`"update"` at lines 825/827, plus single-verb positional authorize args `_authorize_or_raise(..., "create"/"update"/"delete", ...)` at 908/946/999), `permissions.py::_OPERATION_PERMISSION_ACTION` (dict KEYS, lines 38-40), and `fields.py::_synthesized_mutation_signature` (membership tests `operation in ("update","delete")` / `("create","update")` at 167/173). The only true single-source candidate is the bare verb *vocabulary* (the three strings as a canonical `OPERATIONS = ("create","update","delete")` tuple the membership set / dict keys / per-op branches could each reference); the verb→Django-codename MAP (`_OPERATION_PERMISSION_ACTION` values) and the verb→input-kind MAP (`_OPERATION_INPUT_KIND`) are distinct axes and must NOT be folded into it. This is forwarded to the project pass rather than kept at folder level because (a) the `rev-mutations__sets.md` cycle already resolved the *local* defect (the stale "resolver imports the set" comment) via route A and explicitly scoped the cross-module vocabulary question onward, and (b) a canonical verb tuple is plausibly a package-level constant (the read side has no verb axis today, but a future `aggregates`/bulk-write family would share it), so the project pass is the right altitude to decide ownership. Do NOT act now: `resolvers.py`'s equality-against-single-literal dispatch and single-verb authorize args cannot consume a membership set (route B is a forced fit — confirmed in `rev-mutations__sets.md`), so a vocabulary tuple buys clarity, not call-site reduction, until a real iterator/membership consumer beyond `sets.py` exists. **Trigger (quote verbatim): "Promote a shared `OPERATIONS` verb tuple when a second module needs to iterate or membership-test the verb set (beyond `sets._VALID_OPERATIONS`), OR when a fourth mutation operation lands; then single-source the vocabulary and rebuild `_VALID_OPERATIONS` / the dict keys / the per-op branches from it."**

## High:

None.

## Medium:

None.

## Low:

### Repeated `"many_to_many"` getattr probe literal across `inputs.py` and `resolvers.py` (forward-looking)

`getattr(field, "many_to_many", False)` (or the bare `"many_to_many"` attribute name) appears in `inputs.py` (3x — selector inclusion, annotation collection-vs-scalar, requiredness exemption) and `resolvers.py` (2x — `_relation_field_index` line 309, `_decode_relation_id_set` line 384). The forward-M2M predicate `utils/relations.py::is_forward_many_to_many` already owns the *forward*-only case and is imported by both `inputs.py` (line 56) and `resolvers.py` (line 91). The bare `many_to_many` probe is deliberately broader (any M2M incl. reverse) and the sites read different field objects in different control flow, so a shared `_is_m2m(field)` helper would add a named indirection without removing logic. Forward-looking: defer until a third module grows a bare `many_to_many` probe OR `is_forward_many_to_many` gains a non-forward companion; then route all M2M-shape probes through `utils/relations`. Not actionable this cycle. (Already logged file-locally in `rev-mutations__resolvers.md`; recorded here as the only cross-sibling repeated-literal worth a folder note.)

## What looks solid

### DRY recap

- **Existing patterns reused (cross-file, folder-wide).** Every shared concern in the subpackage bottoms out in ONE canonical primitive rather than a per-module re-derivation: input shape/name/cache-key through `inputs.py::mutation_input_shape` (the DRY-1 descriptor) consumed by `sets.py::_materialize_input_for` / `_materialize_merged_input`; the public `FieldError` envelope + `payload_object_slot` + `NON_FIELD_ERROR_KEY` defined once in `inputs.py` and consumed by `resolvers.py` (payload assembly + `full_clean` error keying); GlobalID decode through `relay.py::decode_model_global_id` (spec-036 DRY-2) at every relation/lookup seam in `resolvers.py`; sync visibility + `SyncMisuseError` discipline through `utils/querysets.py::apply_type_visibility_sync`; the request-user resolver through `utils/permissions.py::request_from_info` reused identically by `permissions.py` and the read-side filter/order pipelines; the write-finalization tail single-sourced as `resolvers.py::_validate_save_assign_refetch_payload` (DRY-3). No sibling re-implements another sibling's logic.
- **New helpers considered.** A shared "synthesized-signature" helper across `fields.py` / `relay.py` / `connection.py` was evaluated and rejected (per-family variable arg sets — `relay` uses explicit typed params, `fields` uses `**kwargs`+`__signature__` override). A unified relation-pk gate across `resolvers.py::_relation_visibility_error` / `_relation_existence_error` was evaluated and deferred (two distinct contracts — `get_queryset` visibility vs default-manager existence — sharing only a one-line subset tail; tracked in `rev-mutations__resolvers.md`). A merged `_OPERATION_*` map (permission-action vs input-kind) was rejected — different axes that would diverge. None warranted at folder level.
- **Duplication risk in the folder.** Cross-sibling repeated literals are limited and intentional: `DjangoMutation` (self-naming brand across `__init__`/`sets`/`inputs`/`fields` error messages — a family identifier, not extractable); `many_to_many` (the forward-looking Low above); the verb vocabulary (the forwarded DRY item above). The `DjangoMutation for ...` `ConfigurationError` prefixes in `inputs.py` (3x) and the `input_class`/`partial_input_class` attr-name literals in `sets.py` (5x each) are within-file name-as-data, not cross-sibling.

### Other positives

- **Import direction is a clean one-way DAG, no circular-import risk.** Within the folder: `inputs.py` and `permissions.py` are leaves (zero sibling imports); `resolvers.py` → `inputs`; `sets.py` → `inputs`, `permissions`; `fields.py` → `inputs`, `resolvers`, `sets` (the apex). No sibling imports a module that (transitively) imports it back. The deepest leaf is `inputs.py` (the generation substrate), which every consumer points INWARD to — the correct shape. All cross-package imports point outward to `..exceptions` / `..registry` / `..scalars` / `..types.*` / `..utils.*` / `..relay` / `..optimizer.*`; nothing in `mutations/` is imported by those layers, so the subpackage is a clean downstream leaf of the package graph.
- **`__init__.py` export shape is correct and complete.** Re-exports exactly the four-symbol public surface — `DjangoModelPermission` (from `.permissions`), `DjangoMutation` (from `.sets`), `DjangoMutationField` (from `.fields`), `FieldError` (from `.inputs`) — with a sorted `__all__` tuple matching the package root's re-export claim (the dispatch's named four symbols). Mirrors the `filters/__init__.py` / `orders/__init__.py` re-export idiom. No private symbol leaks into `__all__`; the generation internals (`mutation_input_shape`, `editable_input_fields`, `mutation_input_type_name`, `_OPERATION_INPUT_KIND`, `_VALID_OPERATIONS`) stay module-private and are reached by siblings via explicit `from .X import` rather than the package namespace.
- **Error-handling shape is consistent across the folder.** Class-creation / construction-time misuse raises `ConfigurationError` naming the offending family symbol (`fields.py::_validate_mutation_target` → `DjangoMutationField`; `sets.py` Meta validation → `DjangoMutation`; `inputs.py::build_mutation_input` empty-input → model+operation); request-time write failures map to the in-band field-keyed `FieldError` envelope; sync-context misuse of an async hook raises `SyncMisuseError` at the right seam (`sets.py::check_permission` for the entry hook, `resolvers.py::_authorize_or_raise` for the override). No sibling swallows an error into a silent allow; the security-sensitive `permissions.py` leaf has exactly one `True`-producer (`bool(user.has_perm(codename))`) with every other path denying.
- **Sync/async pattern is consistent and single-bodied.** The async write path (`resolvers.py::resolve_mutation_async`) does NOT re-implement the pipeline — it runs the SAME `_run_pipeline_sync` under one `sync_to_async(thread_sensitive=True)`; `fields.py::_resolve` dispatches `in_async_context()` per call (one factory output for both `execute_sync` / `await execute`), mirroring `relay.py::DjangoNodesField._resolve`. Async-hook bypass is rejected loud (coroutine `.close()` + `SyncMisuseError`) at both the `check_permission` entry seam and the override seam — never treated as a truthy allow.
- **Comment consistency restored this run.** The one cross-module comment that misdescribed sibling behaviour — `sets.py`'s `_VALID_OPERATIONS` "Slice 3's resolver imports this" claim, false because `resolvers.py` re-spells the verbs inline and never imports the constant — was corrected to state the true single-source scope (this module's membership check only) in the earlier `rev-mutations__sets.md` cycle. No remaining sibling comment makes an unverified cross-module claim; `permissions.py`'s `_OPERATION_PERMISSION_ACTION` comment ("Single-sited so Slice 3's resolver reuses it if it needs the action verb") is accurately hedged ("if it needs", not "imports").

### Summary

The `mutations/` subpackage holds up cleanly as a unit: a one-way acyclic import DAG with `inputs.py`/`permissions.py` as leaves and `fields.py` at the apex, a complete and correctly-sorted four-symbol `__init__.py` re-export, consistent error-handling (creation-time `ConfigurationError` / request-time `FieldError` / sync-misuse `SyncMisuseError`) and a single-bodied sync/async pipeline with the async-bypass hole closed at the right seams. Every shared concern is single-sourced through a canonical primitive (`mutation_input_shape`, `decode_model_global_id`, `apply_type_visibility_sync`, `request_from_info`, the `_validate_save_assign_refetch_payload` finalization tail). No High/Medium; one forward-looking Low (the cross-sibling `many_to_many` probe). Two DRY items: the `fields.py::_input_type_name` name re-derivation stays at folder level (both call sites are `mutations/`-internal, defer-with-trigger), while the shared `OPERATIONS` verb-vocabulary candidate is forwarded to the project pass (it is plausibly a package-level constant and the local comment defect was already resolved). Folder-pass diff vs the cycle baseline `212b2953` is empty (the verified `sets.py` comment fix is in the baseline) → genuine no-source-edit folder pass.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle (folder-pass diff vs the cycle baseline `212b2953d1bf046525ea1fabeb84661d5d34b86e` is empty; the `sets.py` `_VALID_OPERATIONS` comment correction is IN the baseline and was already verified under `rev-mutations__sets.md`).

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 289 files left unchanged.
- `uv run ruff check --fix .` — pass; all checks passed.

### Notes for Worker 3
- All five siblings are `verified`; the folder pass introduces no behaviour change.
- `git diff 212b2953d1bf046525ea1fabeb84661d5d34b86e -- django_strawberry_framework/mutations/` empty. `git diff HEAD -- django_strawberry_framework/mutations/` shows ONLY the `sets.py` comment hunk (already-verified, in baseline). The dirty `optimizer/walker.py` / `utils/relations.py` working-tree edits are AGENTS.md #33/#34 concurrent-maintainer work, out of scope.
- No GLOSSARY-only fix in scope: the folder's public surface (`DjangoMutation`, `DjangoMutationField`, `DjangoModelPermission`, `FieldError`, input-type generation) was grep-confirmed accurate vs implementation across all five per-file cycles this run; no drift.
- Low disposition: the cross-sibling `many_to_many` probe Low is forward-looking (explicit trigger), not an act-now edit.
- DRY dispositions: `_input_type_name` → DRY-1, kept at folder level, defer-with-trigger (verbatim trigger in `## DRY analysis`). `OPERATIONS` verb vocabulary → forwarded to `rev-django_strawberry_framework.md`, defer-with-trigger. Neither is act-now.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits. The package docstring in `__init__.py` accurately enumerates the five modules and the four-symbol re-export; the one previously-stale cross-module comment (`sets.py` `_VALID_OPERATIONS`) was corrected in the earlier `rev-mutations__sets.md` cycle and reads accurate now. No remaining sibling comment makes an unverified cross-module claim.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source/test/doc edits this folder-pass cycle (review-only; folder diff empty vs baseline). Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md` (silent on changelog for review artifacts), no changelog entry is warranted.

---

## Verification (Worker 3)

Terminal-verify of a shape #5 no-source-edit folder pass over the NEW `mutations/` subpackage (spec-036, 0.0.11). All five in-scope siblings (`fields.py`, `inputs.py`, `permissions.py`, `resolvers.py`, `sets.py`) are individually `[x]` in `docs/review/review-0_0_11.md:107-111`; this is the folder pass over the unit.

### Logic verification outcome
- **High / Medium: `None.` — genuine.** No behaviour-changing defect skipped. The folder-pass altitude question is the cross-sibling one (no helper duplicated between two siblings in the same folder); confirmed below.
- **Low (cross-sibling `many_to_many` getattr probe) — forward-looking, not actionable.** Carries an explicit deferral trigger ("defer until a third module grows a bare `many_to_many` probe OR `is_forward_many_to_many` gains a non-forward companion"). Already logged file-locally in `rev-mutations__resolvers.md`; recorded here only as the one cross-sibling repeated-literal worth a folder note. Not an act-now edit. Verbatim-trigger / forwarded discipline (shape #5 check 3) satisfied; no GLOSSARY-only fix in scope.

### Import-DAG verification (the load-bearing folder claim)
Grepped sibling import edges directly in source. Confirmed the artifact's DAG verbatim:
- `inputs.py` — zero sibling imports (leaf). `permissions.py` — zero sibling imports (leaf). Both confirmed by grep returning NONE.
- `resolvers.py` → `inputs` (`resolvers.py:92` top-level `from .inputs import NON_FIELD_ERROR_KEY, FieldError, payload_object_slot`; `resolvers.py:1137` deferred `from . import inputs`).
- `sets.py` → `inputs`, `permissions` (`sets.py:55`, `:66`).
- `fields.py` → `inputs`, `resolvers`, `sets` (`fields.py:61`, `:66`, `:67`) — the apex.

No sibling imports a module that (transitively) imports it back; nothing imports `fields.py`. **One-way, acyclic confirmed.** Note: `_OPERATION_INPUT_KIND` lives in `sets.py:100` (not `inputs.py`) and `fields.py:67` imports it from `.sets` — this is consistent with the DAG (`fields → sets`), not a back-edge.

### `__init__.py` re-export shape
Read directly. Re-exports exactly the four-symbol public surface — `DjangoMutationField` (`.fields`), `FieldError` (`.inputs`), `DjangoModelPermission` (`.permissions`), `DjangoMutation` (`.sets`) — with a sorted `__all__` tuple (`DjangoModelPermission`, `DjangoMutation`, `DjangoMutationField`, `FieldError`). Matches the dispatch's named four. No private symbol (`mutation_input_shape`, `_OPERATION_INPUT_KIND`, `_VALID_OPERATIONS`, etc.) leaks into `__all__`; siblings reach internals via explicit `from .X import`. Complete and correct.

### Error-handling / sync-async consistency
Confirmed at source against the artifact's "What looks solid": creation-time `ConfigurationError` (naming the family symbol) / request-time field-keyed `FieldError` / sync-misuse `SyncMisuseError` at the right seams; the async write path (`resolvers.py::resolve_mutation_async`) runs the same sync pipeline under one `sync_to_async`, not a re-implementation; the truthy-coroutine async-bypass is rejected loud at both the `sets.py::check_permission` entry seam and the `resolvers.py::_authorize_or_raise` override seam. `permissions.py` leaf has exactly one `True`-producer (`bool(user.has_perm(codename))`) — no fall-through to allow. Consistent across the folder (all pinned by named tests per the five closed sibling cycles, re-verified in my own memory entries this run).

### DRY findings disposition
- **DRY-1 `_input_type_name` KEPT at folder level — verified correct.** Grepped both call sites: `_input_type_name` is defined at `fields.py:95` and consumed at `fields.py:174` (`_lazy_ref(_input_type_name(meta))`); it calls `mutation_input_type_name(...)` at `fields.py:119`. The `mutation_input_shape(...).type_name` descriptor it would route through is consumed by `sets.py::_materialize_input_for`/`_materialize_merged_input` (`sets.py:654`/`:712`, via `shape.type_name`). Both name-derivation/consumption sites are `mutations/`-internal → a `mutations/`-internal consolidation, correctly KEPT here with a verbatim defer-with-trigger. Identity is test-pinned (the three `mutation_input_type_name` identity tests, per the fields/inputs sibling cycles), so the trigger has its early-warning canary.
- **Shared `OPERATIONS` verb vocabulary FORWARDED to project pass — verified correct.** `grep -rn _VALID_OPERATIONS` returns ONLY `sets.py` (def `:93`, two use-sites `:385`/`:388`) → genuinely single-module; the resolver dispatches on verb literals (`meta.operation == "create"`/`"update"` at `resolvers.py:825`/`:827`; positional `"create"`/`"update"`/`"delete"` at `:908`/`:946`/`:999`), which a frozenset membership set provably cannot replace (route B is a forced fit). `fields.py::_synthesized_mutation_signature` membership tests (`operation in ("update","delete")` `:167` / `("create","update")` `:173`) likewise read bare literals. A canonical verb *tuple* is plausibly a package-level constant with no second iterator/membership consumer beyond `sets.py` today → correctly FORWARDED to `rev-django_strawberry_framework.md`, not folder-fixable.
- **verb→codename and verb→input-kind maps NOT folded — verified correct.** `_OPERATION_PERMISSION_ACTION` (`permissions.py:37` dict keys, consumed `:84`) and `_OPERATION_INPUT_KIND` (`sets.py:100`, consumed `fields.py:113` hard index + `sets.py:634` `.get`) are distinct axes (verb→Django-codename vs verb→input-kind) that would diverge — correctly NOT folded into the vocabulary.

### Zero-edit proof (shape #5)
- `git diff 212b2953d1bf046525ea1fabeb84661d5d34b86e -- django_strawberry_framework/mutations/` is **EMPTY** — confirmed.
- Owned-paths `git diff --stat HEAD` shows two hunks, both attributed:
  - `mutations/sets.py` (+5/-1) is the `_VALID_OPERATIONS` comment correction — read the hunk; it is exactly the stale "Slice 3's resolver imports this" → "THIS module's membership check only" fix, already verified under the closed sibling cycle `rev-mutations__sets.md` (`Status: verified`, `[x]` at `review-0_0_11.md:111`). It is IN the per-cycle baseline, so the folder-pass diff vs baseline is empty. Not a rejection trigger.
  - `docs/GLOSSARY.md` (the apps.py three-patch-module `## Relation cardinality`-adjacent entry, line 305) is AGENTS.md #33 concurrent-maintainer work — out of the mutations folder's public surface, left untouched.
- `git diff -- CHANGELOG.md` empty. Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` Changelog `Not warranted` cites BOTH AGENTS.md #21 and plan silence; internal-only framing honest (folder diff empty, no public-API change this cycle). `uv run ruff format --check` (6 files already formatted) + `uv run ruff check` (all passed) clean.

### Temp test verification
- None — no temp tests needed; the zero-edit proof + grep-confirmed DAG/DRY/re-export claims are decisive, and the underlying behaviour is already pinned by the five closed sibling cycles.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the mutations/ folder-pass checklist box `[x]` in `docs/review/review-0_0_11.md`. Carry-forward for the project pass: the shared `OPERATIONS` verb-vocabulary DRY item is forwarded here (defer-with-trigger; `_VALID_OPERATIONS`/`_OPERATION_PERMISSION_ACTION` keys/`_OPERATION_INPUT_KIND`/per-op branches all rebuild from the would-be tuple); the verb→codename and verb→input-kind maps must stay distinct. `_input_type_name` DRY-1 stays folder-internal (NOT forwarded).
