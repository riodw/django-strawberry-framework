# Review: `django_strawberry_framework/mutations/` (folder pass)

Status: verified

DRIFT RE-DO of the `mutations/` folder pass. The folder was verified earlier this
run, then three of its files (`permissions.py`, `resolvers.py`, `sets.py`) drifted
via the maintainer's concurrent DRY cycle — the verb-handle / coroutine-guard /
decode logic routed through `utils/` helpers and the async-recourse string shared
between both seams. Those three files were individually re-reviewed + re-verified
against current source (`rev-mutations__permissions.md`, `rev-mutations__resolvers.md`,
`rev-mutations__sets.md`, all `Status: verified`); `fields.py` and `inputs.py` stayed
`verified`. This folder pass re-collects the forwarded items and re-confirms the
cross-file consistency against HEAD `d63d77f8`.

**Zero-edit folder pass.** `git diff 4a6c6ffd9652c9dd2da0c542b176d576c98abbb9 --
django_strawberry_framework/mutations/` is EMPTY and `git diff HEAD --
django_strawberry_framework/mutations/` is EMPTY — the maintainer's DRY-cycle
changes are all cumulative-in-HEAD with no pending edit. The only dirty working-tree
files are `docs/review/` cycle scratchpads (the three sibling re-reviews + the plan),
out of scope per AGENTS.md #34. No High, no behaviour-changing Medium, every Low
forward-looking/forwarded, GLOSSARY clean for the folder's public surface → genuine
no-source-edit folder pass (shape #5). Worker 2 sections filled inline below; both
ruff commands run; bare `Status: fix-implemented`.

## DRY analysis

- **Defer-with-trigger — fold `mutations/fields.py::_input_type_name` into `mutations/inputs.py::mutation_input_shape(...).type_name` (KEPT AT FOLDER LEVEL).** `_input_type_name` (`mutations/fields.py:95-124`) independently re-walks `editable_input_fields(meta.model, fields=, exclude=)` for the selected names AND `editable_input_fields(meta.model)` for the full set, then re-calls `mutation_input_type_name(...)` at `fields.py:119` — byte-for-byte the same name computation `mutations/inputs.py::mutation_input_shape` performs to produce `shape.type_name`, the DRY-1 descriptor that exists to single-source exactly this. Both call sites are `mutations/`-internal: `fields.py:174` derives the name (`_lazy_ref(_input_type_name(meta))`); `sets.py::_materialize_input_for`/`_materialize_merged_input` consume `shape.type_name` (`sets.py:651`/`:709`/`:730-731`). So this is a `mutations/`-internal consolidation, not a project-wide one — keep it here. Correctness-neutral today (identical pure-function inputs, names provably agree; verified in `rev-mutations__fields.md` / `rev-mutations__inputs.md`). Consolidation shape: `_input_type_name(meta)` calls `mutation_input_shape(meta.model, _OPERATION_INPUT_KIND[meta.operation], fields=meta.fields, exclude=meta.exclude).type_name` and drops the local two-walk. Do NOT act now: forcing the finalizer-free import-time `fields.py` factory to build a full `MutationInputShape` for a name-only need is heavier than the current two-walk, and the bind/merge path already consumes the descriptor. **Trigger (quote verbatim): "Defer until `mutation_input_type_name`'s identity rule changes OR a fourth name-derivation caller lands; then route `_input_type_name` through `mutation_input_shape(...).type_name`."** The maintainer's DRY cycle did NOT touch this item (the cycle's reach was the permission/decode/model-handle helpers, not the input-name derivation) — still open, still folder-internal.

- **Defer-with-trigger — shared mutation `OPERATIONS` verb vocabulary across `sets`/`resolvers`/`permissions`/`fields` (FORWARDED to the project pass `rev-django_strawberry_framework.md`).** The verb literals `"create"` / `"update"` / `"delete"` are spelled inline in four of the five modules: `sets.py::_VALID_OPERATIONS` (`frozenset`, `sets.py:92` — the membership single-source for `Meta.operation` validation, consumed at `:384`/`:387`), `resolvers.py` (equality dispatch `meta.operation == "create"`/`"update"` at `:816`/`:818`, plus single-verb positional authorize args `_authorize_or_raise(..., "create"/"update"/"delete", ...)` at `:899`/`:937`/`:990`), `permissions.py::_OPERATION_PERMISSION_ACTION` (dict KEYS, `permissions.py:37-41`, consumed `:99`), and `fields.py::_synthesized_mutation_signature` (membership tests `operation in ("update","delete")` / `("create","update")` at `:167`/`:173`). The only true single-source candidate is the bare verb *vocabulary* (the three strings as a canonical `OPERATIONS = ("create","update","delete")` tuple the membership set / dict keys / per-op branches could each reference); the verb→Django-codename MAP (`_OPERATION_PERMISSION_ACTION` values) and the verb→input-kind MAP (`_OPERATION_INPUT_KIND`, `sets.py:99`) are distinct axes and must NOT be folded into it. Forwarded to the project pass rather than kept at folder level because (a) the `rev-mutations__sets.md` cycle already resolved the *local* defect (the stale "resolver imports the set" comment) and explicitly scoped the cross-module vocabulary question onward, and (b) a canonical verb tuple is plausibly a package-level constant (the read side has no verb axis today, but a future `aggregates`/bulk-write family would share it), so the project pass is the right altitude to decide ownership. Do NOT act now: `resolvers.py`'s equality-against-single-literal dispatch and single-verb authorize args cannot consume a membership set (route B is a forced fit — confirmed in `rev-mutations__sets.md`), so a vocabulary tuple buys clarity, not call-site reduction, until a real iterator/membership consumer beyond `sets.py` exists. **Trigger (quote verbatim): "Promote a shared `OPERATIONS` verb tuple when a second module needs to iterate or membership-test the verb set (beyond `sets._VALID_OPERATIONS`), OR when a fourth mutation operation lands; then single-source the vocabulary and rebuild `_VALID_OPERATIONS` / the dict keys / the per-op branches from it."** The maintainer's DRY cycle did NOT collapse this (it shared the recourse *string* and routed the *guard*, not the verb vocabulary) — still open, still forwarded.

## High:

None.

## Medium:

None.

## Low:

### Repeated `"many_to_many"` getattr probe literal across `inputs.py` and `resolvers.py` (forward-looking)

`getattr(field, "many_to_many", False)` (or the bare `"many_to_many"` attribute name) appears in `inputs.py` (3x — selector inclusion `:186`, annotation collection-vs-scalar `:279`, requiredness exemption `:509`) and `resolvers.py` (2x — `_relation_field_index` `:300`, `_decode_relation_id_set` `:375`). The forward-M2M predicate `utils/relations.py::is_forward_many_to_many` already owns the *forward*-only case and is imported by both `inputs.py` (`:56`) and `resolvers.py` (`:95`). The bare `many_to_many` probe is deliberately broader (any M2M incl. reverse) and the sites read different field objects in different control flow, so a shared `_is_m2m(field)` helper would add a named indirection without removing logic. Forward-looking: defer until a third module grows a bare `many_to_many` probe OR `is_forward_many_to_many` gains a non-forward companion; then route all M2M-shape probes through `utils/relations`. Not actionable this cycle. (Already logged file-locally in `rev-mutations__resolvers.md`; recorded here as the only cross-sibling repeated-literal worth a folder note — confirmed unchanged by the maintainer's DRY cycle.)

## What looks solid

### DRY recap

- **Existing patterns reused (cross-file, folder-wide).** Every shared concern in the subpackage bottoms out in ONE canonical primitive rather than a per-module re-derivation: input shape/name/cache-key through `inputs.py::mutation_input_shape` (the DRY-1 descriptor) consumed by `sets.py::_materialize_input_for`/`_materialize_merged_input` (`sets.py:651`/`:709`); the public `FieldError` envelope + `payload_object_slot` + `NON_FIELD_ERROR_KEY` defined once in `inputs.py` and imported by `resolvers.py` (`resolvers.py:96`); GlobalID decode through `relay.py::decode_model_global_id` (spec-036 DRY-2) at every relation/lookup seam in `resolvers.py` (`:366`, `:1095`); the model handle through `utils/querysets.py::model_for` (`resolvers.py:575`/`:811`/`:1094` — the maintainer's `7a17ba75` promotion, now single-sited package-wide); sync visibility + `SyncMisuseError` discipline through `utils/querysets.py::apply_type_visibility_sync` (`resolvers.py:480`/`:576`); the sync-context coroutine guard through `utils/querysets.py::reject_async_in_sync_context` with the shared `permissions.py::_PERMISSION_ASYNC_RECOURSE` string at BOTH seams (`resolvers.py:1022-1027`, `sets.py:564`); the request-user resolver through `utils/permissions.py::request_from_info` reused identically by `permissions.py` and the read-side filter/order pipelines; the write-finalization tail single-sourced as `resolvers.py::_validate_save_assign_refetch_payload` (DRY-3). No sibling re-implements another sibling's logic.
- **New helpers considered.** A shared "synthesized-signature" helper across `fields.py` / `relay.py` / `connection.py` was evaluated and rejected (per-family variable arg sets — `relay` uses explicit typed params, `fields` uses `**kwargs`+`__signature__` override). A unified relation-pk gate across `resolvers.py::_relation_visibility_error` / `_relation_existence_error` was evaluated and deferred (two distinct contracts — `get_queryset` visibility vs default-manager existence — sharing only a one-line subset tail; tracked in `rev-mutations__resolvers.md`). A merged `_OPERATION_*` map (permission-action vs input-kind) was rejected — different axes that would diverge. None warranted at folder level. The maintainer's DRY cycle realized exactly the consolidations these recaps anticipated (shared recourse string, `model_for` promotion, guard routing) — there is no remaining act-now folder helper.
- **Duplication risk in the folder.** Cross-sibling repeated literals are limited and intentional: `DjangoMutation` (self-naming brand across `__init__`/`sets`/`inputs`/`fields` error messages — a family identifier, not extractable; 13x in `sets.py`, 2x in `inputs.py`, all within-file family naming); `many_to_many` (the forward-looking Low above — the only literal in 2+ siblings that is logic rather than brand); the verb vocabulary (the forwarded DRY item above). The `DjangoMutation for ...` `ConfigurationError` prefixes in `inputs.py` (3x) and the `input_class`/`partial_input_class` attr-name literals in `sets.py` (5x each) are within-file name-as-data, not cross-sibling. The shared `_PERMISSION_ASYNC_RECOURSE` recourse string — previously a byte-identical inline copy in `resolvers.py` and `sets.py` — is now single-sourced in `permissions.py:52` and imported (the maintainer's DRY consolidation; grep confirms no inline copy survives), so it is no longer a duplication risk.

### Other positives

- **Import direction is a clean one-way DAG, no circular-import risk (re-confirmed at HEAD).** Within the folder: `inputs.py` and `permissions.py` are leaves (zero sibling imports — grep returns none); `resolvers.py` → `inputs`, `permissions` (`resolvers.py:96`/`:97`); `sets.py` → `inputs`, `permissions` (`sets.py:54`/`:65`); `fields.py` → `inputs`, `resolvers`, `sets` (`fields.py:61`/`:66`/`:67`) — the apex. No sibling imports a module that (transitively) imports it back. The deepest leaf is `inputs.py` (the generation substrate), which every consumer points INWARD to. The maintainer's DRY cycle added one new sibling edge — `resolvers.py:97 from .permissions import _PERMISSION_ASYNC_RECOURSE` — which is `resolvers → permissions`, a forward edge consistent with the DAG (both `resolvers` and `sets` already pointed at `permissions`/`inputs`), NOT a back-edge. All cross-package imports point outward to `..exceptions` / `..registry` / `..scalars` / `..types.*` / `..utils.*` / `..relay` / `..optimizer.*`; nothing in `mutations/` is imported by those layers, so the subpackage is a clean downstream leaf of the package graph.
- **`__init__.py` export shape is correct and complete.** Re-exports exactly the four-symbol public surface — `DjangoMutationField` (from `.fields`), `FieldError` (from `.inputs`), `DjangoModelPermission` (from `.permissions`), `DjangoMutation` (from `.sets`) — with a sorted `__all__` tuple (`DjangoModelPermission`, `DjangoMutation`, `DjangoMutationField`, `FieldError`) matching the dispatch's named four symbols and the package-root re-export (`django_strawberry_framework/__init__.py:20-23` imports + `:45-52` `__all__`). Mirrors the `filters/__init__.py` / `orders/__init__.py` re-export idiom. No private symbol leaks into `__all__`; the generation internals (`mutation_input_shape`, `editable_input_fields`, `mutation_input_type_name`, `_OPERATION_INPUT_KIND`, `_VALID_OPERATIONS`, `_PERMISSION_ASYNC_RECOURSE`) stay module-private and are reached by siblings via explicit `from .X import` rather than the package namespace.
- **Error-handling shape is consistent across the folder.** Class-creation / construction-time misuse raises `ConfigurationError` naming the offending family symbol (`fields.py::_validate_mutation_target` → `DjangoMutationField`; `sets.py` Meta validation → `DjangoMutation`; `inputs.py::build_mutation_input` empty-input → model+operation); request-time write failures map to the in-band field-keyed `FieldError` envelope; sync-context misuse of an async hook raises `SyncMisuseError` at the right seam (`sets.py::check_permission` for the entry hook `sets.py:564`, `resolvers.py::_authorize_or_raise` for the override `:1022`). No sibling swallows an error into a silent allow; the security-sensitive `permissions.py` leaf has exactly one `True`-producer (`bool(user.has_perm(codename))`) with every other path denying. The maintainer's DRY routing of both async-guard seams through the SAME `reject_async_in_sync_context` helper TIGHTENED this consistency (the coroutine is `.close()`d and `SyncMisuseError` raised BEFORE any `if not allowed` / `if not allowed: return False` branch at both seams — no permission bypass; re-verified in the three sibling re-reviews).
- **Sync/async pattern is consistent and single-bodied.** The async write path (`resolvers.py::resolve_mutation_async`) does NOT re-implement the pipeline — it runs the SAME `_run_pipeline_sync` under one `sync_to_async(thread_sensitive=True)`; `fields.py::_resolve` dispatches `in_async_context()` per call (one factory output for both `execute_sync` / `await execute`), mirroring `relay.py::DjangoNodesField._resolve`. Async-hook bypass is rejected loud (coroutine `.close()` + `SyncMisuseError`) at both the `check_permission` entry seam and the override seam — never treated as a truthy allow.
- **Comment consistency holds (re-confirmed at HEAD).** The one cross-module comment that had misdescribed sibling behaviour — `sets.py`'s `_VALID_OPERATIONS` "Slice 3's resolver imports this" claim, false because `resolvers.py` re-spells the verbs inline and never imports the constant — was corrected to state the true single-source scope (this module's membership check only, `sets.py:88`); grep re-confirms the only `_VALID_OPERATIONS` consumers are `sets.py:384`/`:387`, and `resolvers.py` does not import it. No remaining sibling comment makes an unverified cross-module claim; `permissions.py`'s `_OPERATION_PERMISSION_ACTION` comment is accurately hedged.

### Summary

DRIFT RE-DO of the `mutations/` folder pass against current HEAD. After the maintainer's concurrent DRY cycle drifted `permissions.py` / `resolvers.py` / `sets.py` (shared `_PERMISSION_ASYNC_RECOURSE` recourse string, `model_for` promotion, both async-guard seams routed through `reject_async_in_sync_context`), all five siblings are individually `verified`, and the cross-file consistency holds cleanly: a one-way acyclic import DAG with `inputs.py`/`permissions.py` as leaves and `fields.py` at the apex (the new `resolvers → permissions` edge for the shared recourse string is a forward edge, not a back-edge), a complete and correctly-sorted four-symbol `__init__.py` re-export matching the package root, consistent error-handling (creation-time `ConfigurationError` / request-time `FieldError` / sync-misuse `SyncMisuseError`) and a single-bodied sync/async pipeline with the async-bypass hole closed at the right seams. Every shared concern is single-sourced through a canonical primitive (`mutation_input_shape`, `decode_model_global_id`, `model_for`, `apply_type_visibility_sync`, `reject_async_in_sync_context` + `_PERMISSION_ASYNC_RECOURSE`, `request_from_info`, the `_validate_save_assign_refetch_payload` finalization tail). No High/Medium; one forward-looking Low (the cross-sibling `many_to_many` probe). Two DRY items re-confirmed: the `fields.py::_input_type_name` name re-derivation stays at folder level (both call sites `mutations/`-internal, defer-with-trigger; untouched by the DRY cycle), while the shared `OPERATIONS` verb-vocabulary candidate is forwarded to the project pass (untouched by the DRY cycle — it shared the recourse string and routed the guard, not the verb vocabulary). Folder-pass diff vs the cycle baseline `4a6c6ffd` AND vs HEAD is empty (all DRY-cycle work is cumulative-in-HEAD) → genuine no-source-edit folder pass.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle (folder-pass diff vs the cycle baseline `4a6c6ffd9652c9dd2da0c542b176d576c98abbb9` is EMPTY and vs HEAD is EMPTY; the maintainer's DRY-cycle changes to `permissions.py`/`resolvers.py`/`sets.py` are cumulative-in-HEAD and were already individually verified).

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; `289 files left unchanged` (COM812-vs-formatter warning is informational config noise only).
- `uv run ruff check --fix .` — pass; `All checks passed!`.

### Notes for Worker 3
- All five siblings are `verified` against current source (the three drifted files re-verified this run); the folder pass introduces no behaviour change.
- `git diff 4a6c6ffd9652c9dd2da0c542b176d576c98abbb9 -- django_strawberry_framework/mutations/` empty. `git diff HEAD -- django_strawberry_framework/mutations/` empty. The dirty working-tree files are `docs/review/` cycle scratchpads (three sibling re-reviews + the plan), AGENTS.md #34 in-flight review-cycle work, out of scope.
- Cross-file consistency re-confirmed at HEAD via grep: one-way acyclic import DAG (`inputs`/`permissions` leaves; `resolvers → inputs, permissions`; `sets → inputs, permissions`; `fields → inputs, resolvers, sets`), four-symbol `__init__` re-export (`DjangoMutation`/`DjangoMutationField`/`FieldError`/`DjangoModelPermission`) sorted and matching the package root, shared `_PERMISSION_ASYNC_RECOURSE` single-sourced in `permissions.py:52` and imported by both seams (no inline copy survives), `model_for`/`decode_model_global_id`/`reject_async_in_sync_context` routed canonically.
- No GLOSSARY-only fix in scope: the folder's public surface (`DjangoMutation` `:384`, `DjangoMutationField` `:392`, `DjangoModelPermission` `:376`, `FieldError` envelope `:495` in `docs/GLOSSARY.md`) was grep-confirmed present and accurate across the five per-file cycles this run; no drift.
- Low disposition: the cross-sibling `many_to_many` probe Low is forward-looking (explicit trigger), not an act-now edit.
- DRY dispositions: `_input_type_name` → DRY-1, KEPT at folder level, defer-with-trigger (verbatim trigger in `## DRY analysis`); untouched by the maintainer's DRY cycle. `OPERATIONS` verb vocabulary → FORWARDED to `rev-django_strawberry_framework.md`, defer-with-trigger; untouched by the maintainer's DRY cycle. Neither is act-now.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits. The package docstring in `__init__.py` accurately enumerates the five modules and the four-symbol re-export; the one previously-stale cross-module comment (`sets.py` `_VALID_OPERATIONS`) was corrected in the earlier `rev-mutations__sets.md` cycle and reads accurate now (grep re-confirms the resolver does not import the set). No remaining sibling comment makes an unverified cross-module claim. The `resolvers.py`/`sets.py` module docstrings naming the shared `decode_model_global_id` / `apply_type_visibility_sync` / `reject_async_in_sync_context` helpers match the post-DRY-cycle source.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source/test/doc edits this folder-pass cycle (review-only; folder diff empty vs baseline AND vs HEAD). The maintainer's DRY-cycle changes are internal single-siting already committed by the maintainer. Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md` (silent on changelog for review artifacts), no changelog entry is warranted.

---

## Verification (Worker 3)

DRIFT RE-DO terminal-verify of the re-opened `mutations/` folder pass (shape #5, no-source-edit) against HEAD `d63d77f8`, cycle baseline `4a6c6ffd9652c9dd2da0c542b176d576c98abbb9`.

### Logic verification outcome

- **Zero-edit proof.** `git diff 4a6c6ffd…  -- django_strawberry_framework/mutations/` EMPTY and `git diff HEAD -- django_strawberry_framework/mutations/` EMPTY. Owned-paths stat `git diff --stat 4a6c6ffd… -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` EMPTY — target absent from the stat, no sibling-cycle attribution needed. The only dirty working-tree files are `docs/review/` scratchpads (`rev-mutations.md`, the three sibling re-reviews, the plan) — AGENTS.md #34 in-flight review work, out of scope. Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern." (shape-#5 gate satisfied).
- **All five siblings `Status: verified`** (`rev-mutations__permissions/resolvers/sets/fields/inputs.md` grep-confirmed).
- **Import DAG (acyclic, re-confirmed at HEAD).** Sibling edges grepped: `inputs.py`/`permissions.py` are leaves (no sibling imports out); `resolvers → inputs (:96), permissions (:97)`; `sets → inputs (:54), permissions (:65)`; `fields → inputs (:61), resolvers (:66), sets (:67)` apex. The `resolvers.py:97 from .permissions import _PERMISSION_ASYNC_RECOURSE` edge is a FORWARD edge into the `permissions` leaf (which imports nothing back) — not a cycle. Confirmed sound.
- **`__init__.py` 4-symbol re-export** verified verbatim: `DjangoMutationField`/`FieldError`/`DjangoModelPermission`/`DjangoMutation`, `__all__` sorted (`DjangoModelPermission`, `DjangoMutation`, `DjangoMutationField`, `FieldError`). No private symbol leaks.
- **`_PERMISSION_ASYNC_RECOURSE`** single-defined `permissions.py:52`, imported + consumed at BOTH async-guard seams (`resolvers.py:1027`, `sets.py:564`); grep confirms no inline copy survives.
- **Async-bypass closed at both seams (read, not assumed).** `sets.py:553-567` (entry seam, `has_permission`): `reject_async_in_sync_context(...)` wraps the hook as first positional arg, return assigned to `allowed` BEFORE `if not allowed: return False`. `resolvers.py:1022-1032` (override seam, `check_permission`): same shape, close/raise BEFORE the `GraphQLError`. Both fail-closed; coroutine `.close()` + `SyncMisuseError` fire before any allow branch.
- **Error-handling consistency** holds: creation-time `ConfigurationError` / request-time `FieldError` / sync-misuse `SyncMisuseError` at the right seams. `_VALID_OPERATIONS` is single-module (`sets.py:92`, consumed `:384`/`:387`); resolver does NOT import it (grep-confirmed) — the corrected cross-module comment claim is accurate at live HEAD.
- **Maintainer DRY-cycle scope confirmed bounded:** recourse string (single-sited `permissions.py:52`) + `model_for` promotion (resolvers.py:575/811/1094, imported `:92`) + guard routing (`reject_async_in_sync_context` at the two seams). It did NOT touch `_input_type_name` nor collapse the verb vocabulary (grep-confirmed below).

### DRY findings disposition

- **DRY-1 `_input_type_name` KEPT folder-level (defer-with-trigger).** Verified `_input_type_name` defined `fields.py:95`, sole caller `fields.py:174` (`_lazy_ref(_input_type_name(meta))`) — `mutations/`-internal. It re-derives the name via `mutation_input_type_name(...)` at `fields.py:119`, the same primitive `inputs.py::mutation_input_shape` uses for `shape.type_name` (`inputs.py:413`). Both consume-sites internal → folder-level keep is correct, not a project forward. Untouched by the maintainer DRY cycle (no `_input_type_name` hit in the cycle's reach). Verbatim trigger present.
- **`OPERATIONS` verb vocabulary FORWARDED to the project pass (defer-with-trigger).** Correct forward: the verb→codename map and verb→input-kind map are distinct axes (not folded); the bare-vocabulary single-source is plausibly package-level (future read-side family), so project-pass altitude is right. Untouched by the maintainer DRY cycle. Verbatim trigger present. Carry-forward obligation to `rev-django_strawberry_framework.md`.

### Low disposition

The one folder Low (cross-sibling `many_to_many` getattr probe) is genuinely forward-looking, not act-now: grep confirms `"many_to_many"` at `inputs.py:186/279/509` and `resolvers.py:300/375`, while the narrower forward-only `is_forward_many_to_many` is already imported by both (`inputs.py:56`, `resolvers.py:95`). The bare probe is deliberately broader (incl. reverse) reading different field objects in different control flow — a shared `_is_m2m` helper adds indirection without removing logic. Explicit trigger; not actionable this cycle. Confirmed unchanged by the DRY cycle.

### Temp test verification
- None created — zero-source-edit folder pass; no behavior to pin beyond the five individually-verified siblings. No focused pytest run warranted (no test introduced).

### Changelog disposition
- `git diff -- CHANGELOG.md` EMPTY. "Not warranted" cites BOTH AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence — both citations present. Internal-only framing matches the empty diff scope (review-only, no public-surface edit). Verified.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the re-opened `mutations/` folder-pass checkbox in `docs/review/review-0_0_11.md`. Cross-file reasoning sound at HEAD `d63d77f8`: acyclic one-way DAG, complete 4-symbol re-export, consistent error-handling, async-bypass closed at both seams. Both DRY dispositions correct (DRY-1 kept folder-level, OPERATIONS forwarded), Low genuinely forward-looking, maintainer DRY cycle confirmed bounded to the recourse string + `model_for` + guard routing.
