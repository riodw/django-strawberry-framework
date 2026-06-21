# Review: `django_strawberry_framework/mutations/sets.py`

Status: verified

DRIFT RE-REVIEW (cycle-28 re-open). The earlier cycle-28 verify approved a comment fix (the
`_VALID_OPERATIONS` "Single source of truth" stale-claim Low, route A). The maintainer's
concurrent DRY cycle then (a) committed further changes to this file (+19/-18 net, routing
the permission async-guard through `utils/querysets.py::reject_async_in_sync_context` with
the shared `_PERMISSION_ASYNC_RECOURSE` string) AND (b) committed that `_VALID_OPERATIONS`
comment fix verbatim. Re-reviewed the CURRENT (HEAD) source from scratch.
`git diff 2ece119ea45e94dd1097067b194e5fca9e7bb4dd -- …` and `git diff HEAD -- …` are BOTH
empty — all of the above is cumulative-in-HEAD, no pending edit. This re-review finds no
new findings and produces zero source edits → no-source-edit cycle (shape #5).

## DRY analysis

- None — the module is already maximally single-sourced for its own concerns. Input
  shape/name/cache-key are derived once via `mutations/inputs.py::mutation_input_shape` and
  reused for the cache key + generated name + `build_mutation_input`
  (`sets.py::_materialize_input_for #"shape = mutation_input_shape"`,
  `sets.py::_materialize_merged_input #"shape = mutation_input_shape"`) — DRY-1, no re-walk.
  The async-coroutine guard is delegated to the canonical helper
  `utils/querysets.py::reject_async_in_sync_context` and the recourse string to
  `permissions.py::_PERMISSION_ASYNC_RECOURSE` (one import, one definition each). The
  relation/naming expectations read `inputs.py::relation_input_annotation` directly
  (`_validate_input_class`, `_expected_input_attr_names`, `_validate_relation_override_types`)
  so the validator cannot drift from the generator. The operation-verb vocabulary
  (`"create"` / `"update"` / `"delete"`) is spelled across `sets.py` / `resolvers.py` /
  `permissions.py`, but those are intentionally distinct AXES (membership-set vs
  verb→input-kind map vs verb→Django-perm-codename map); the cross-module verb-vocabulary
  consolidation candidate is already FORWARDED to the project pass
  (`rev-django_strawberry_framework.md`) and is not re-raised as a file-level finding.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** Input shape/name/cache-key single-sourced through
  `inputs.py::mutation_input_shape` (DRY-1) and reused at both materialize paths
  (`_materialize_input_for`, `_materialize_merged_input`). Async-guard delegated to
  `utils/querysets.py::reject_async_in_sync_context` with shared
  `permissions.py::_PERMISSION_ASYNC_RECOURSE` (`DjangoMutation.check_permission`
  #"reject_async_in_sync_context"). Relation/naming expectations read straight from
  `inputs.py::relation_input_annotation` (core-detect via `_annotation_core_is_global_id`
  → `utils/typing.py::unwrap_return_type`) so the validator tracks the generator.
  `_ValidatedMutationMeta` mirrors `types/base.py::_ValidatedMeta` (validate-once snapshot);
  `DjangoMutationMetaclass.__new__` mirrors `OrderSetMetaclass.__new__` with the same
  `Meta is None` in-flight-base skip; `clear_mutation_registry` is the `registry.clear()`
  co-clear hook the filter/order ledgers also use; `ConfigurationError` / `SyncMisuseError`
  are the canonical raise types.
- **New helpers considered.** None needed. `_materialize_input_for` vs
  `_materialize_merged_input` share most args but differ in caching semantics (all-generated
  caches in `_shape_build_cache`; merged is mutation-specific, never cached) — folding them
  would hide that divergence; kept separate. `_validate_input_class` (class-creation,
  name-only, `related_primary_type=None`) vs `_validate_relation_override_types` (phase-2.5,
  needs `registry.get` for the id type) correctly stay apart.
- **Duplication risk in the current file.** The repeated `"create"` / `"update"` /
  `"delete"` literals (`_VALID_OPERATIONS` set vs `_OPERATION_INPUT_KIND` map) are intentional
  sibling axes — a membership set vs a verb→input-kind map — not duplication. The repeated
  `"input_class"` / `"partial_input_class"` literals are the two `Meta` attr names threaded as
  `attr_name=` and as the create-vs-partial selector — name-as-data, not extractable.

### Other positives

- **`_VALID_OPERATIONS` comment is now accurate (HEAD), confirming the route-A fix landed.**
  The rewritten comment (`sets.py #"Single source\n# of truth for THIS module's membership
  check only"`) states the set is THIS module's membership check only and that the resolver
  "dispatches on the verb literals directly (`== "create"` / `"update"` in
  `mutations/resolvers.py`) ... so it does not import the constant." Grep confirms: the only
  consumers of `_VALID_OPERATIONS` are `_validate_mutation_meta` (`sets.py:384` membership,
  `:387` error message); `resolvers.py` dispatches on literals (`meta.operation == "create"`
  `:816`, `== "update"` `:818`, and single-verb positional args to
  `_authorize_or_raise(..., "create"/"update"/"delete", …)` `:899`/`:937`/`:990`) and does
  NOT import `_VALID_OPERATIONS`. The prior cycle-28 stale-claim Low is resolved in HEAD.
- **DRY delegations preserve semantics — no permission bypass.** `check_permission` wraps
  each `permission_class().has_permission(...)` in `reject_async_in_sync_context(...,
  owner=permission_class.__name__, method="has_permission", context="mutation",
  recourse=_PERMISSION_ASYNC_RECOURSE)`. The helper's verified contract
  (`utils/querysets.py::reject_async_in_sync_context`): if the value is a coroutine,
  `close()` it and raise `SyncMisuseError` BEFORE returning; otherwise return unchanged. So
  an `async def has_permission` is rejected loudly BEFORE the `if not allowed: return False`
  branch — a truthy orphaned coroutine can never be silently treated as ALLOW. Fail-closed
  short-circuit on the first denier intact. The kwargs match the helper signature exactly.
- **Meta validation is complete and fails loud at class creation.** Unknown-key guard
  (own-keys-only, no MRO walk), no-resolvable-model, bad/absent `operation`,
  `fields`+`exclude` mutual exclusion, bare-string + duplicate-name rejection in
  `_normalize_field_sequence` (duplicates would otherwise collapse silently under the
  effective-set frozenset), and the `delete` + `fields`/`exclude` rejection (delete generates
  no input so a typo'd field would never be validated downstream — rejecting the inapplicable
  keys is the root-cause posture). `_validate_permission_classes` rejects a bare class/str/
  bytes and any entry lacking a callable `has_permission`, all at class creation.
- **`_validate_relation_override_types` closes the AR-M2/Decision-10 gap.** A consumer
  relation override is type- and depth-locked to the generated `relay.GlobalID` /
  `list[relay.GlobalID]` core (peeling Strawberry wrappers via `_strawberry_field_shape`,
  which is `id()`-cycle-guarded), so a divergent core/container shape that would bypass the
  decode-time visibility check is rejected at the bind. Correctly deferred to phase-2.5.
- **`_resolve_primary_type` distinguishes the two finalize failure modes** (zero types →
  "no type to return"; multiple-without-primary → `Meta.primary` ambiguity) and stays robust
  if a model reaches the bind unaudited. **`bind_mutations`** clears `_shape_build_cache` at
  the start of each pass so a stale class from a failed/re-run finalize never leaks; payloads
  route through the SAME `materialize_mutation_input_class` ledger as inputs (one collision
  check, one co-clear). `register_mutation` fails loud on a post-finalization declaration.

### Summary

Drift re-review of the largest mutations file at HEAD. Both the per-cycle baseline diff and
the HEAD diff are empty — the maintainer's DRY-cycle changes (async-guard delegation through
`reject_async_in_sync_context` + shared `_PERMISSION_ASYNC_RECOURSE`, plus the
`_VALID_OPERATIONS` comment fix) are all cumulative-in-HEAD with no pending edit. Both DRY
delegations preserve semantics: the permission seam is fail-closed and rejects async
overrides BEFORE any allow-branch (no bypass), and the recourse string is single-sourced. The
committed `_VALID_OPERATIONS` comment is accurate — grep confirms the resolver dispatches on
verb literals and does not import the set. GLOSSARY `#djangomutation` matches current source
(Meta keys, verb set, phase-2.5 bind, primary-type resolution, payload materialization,
`permission_classes` default). No High/Medium/Low findings; the prior stale-comment Low is
resolved in HEAD. No source/test/GLOSSARY/CHANGELOG edits required → no-source-edit cycle
(shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — `289 files left unchanged` (COM812-vs-formatter warning only; a pre-existing config note, not a change).
- `uv run ruff check --fix .` — `All checks passed!`

### Notes for Worker 3
- Per-Low disposition: no Lows — all severities `None.`. The prior cycle-28 stale-comment Low
  (`_VALID_OPERATIONS` claimed a resolver import) is RESOLVED in HEAD: the comment now
  correctly states the resolver dispatches on verb literals and does not import the set
  (grep-verified — only consumers are `sets.py:384`/`:387` in `_validate_mutation_meta`;
  `resolvers.py` uses literals at `:816`/`:818`/`:899`/`:937`/`:990` and never imports
  `_VALID_OPERATIONS`).
- DRY delegations verified semantics-preserving: `check_permission` →
  `reject_async_in_sync_context` (kwargs `owner`/`method`/`context`/`recourse` match the
  helper signature) with shared `_PERMISSION_ASYNC_RECOURSE`; the coroutine is closed +
  raised BEFORE the `if not allowed` branch (no permission bypass; fail-closed).
- No GLOSSARY-only fix in scope — `#djangomutation` is accurate against current source.
- `git diff 2ece119ea45e94dd1097067b194e5fca9e7bb4dd -- django_strawberry_framework/mutations/sets.py`
  and `git diff HEAD -- …` both empty.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits this cycle. The one comment that was stale in the prior cycle
(`_VALID_OPERATIONS` "Single source of truth" cross-module claim) is already corrected in
HEAD by the maintainer's DRY cycle and re-verified accurate this re-review. All other
docstrings/comments match current behavior.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

`Not warranted`. No source edit this cycle (zero tracked-file changes). Per AGENTS.md #21
("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan
(`docs/review/review-0_0_11.md`), which records no changelog authorization for this item.

---

## Verification (Worker 3)

DRIFT RE-VERIFICATION of a shape-#5 (no-source-edit) cycle.

### Target stability
- `git diff HEAD -- django_strawberry_framework/mutations/sets.py` — empty.
- `git diff 1e8030114b9a4d4e3f2538095b62dfeae97ba187 -- django_strawberry_framework/mutations/sets.py` — empty.
- Zero edits to sets.py by THIS cycle; no further drift. The maintainer's DRY-cycle
  changes (async-guard delegation + `_VALID_OPERATIONS` comment fix) are all
  cumulative-in-HEAD with no pending edit.

### Shape-#5 gates
- Each Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.` (Fix
  report / Comment-docstring pass / Changelog disposition). Confirmed.
- All severities `None.` — no Lows to forward; no GLOSSARY-only fix in scope (would be
  disqualifying). Confirmed.

### Logic verification outcome (independent confirmation of maintainer DRY delegations)
- **Permission async-guard is fail-closed, no bypass.** `DjangoMutation.check_permission`
  (`sets.py::DjangoMutation.check_permission`) routes each
  `permission_class().has_permission(...)` as the FIRST arg of
  `reject_async_in_sync_context(..., owner=permission_class.__name__,
  method="has_permission", context="mutation", recourse=_PERMISSION_ASYNC_RECOURSE)`.
  Verified the helper contract live (`utils/querysets.py::reject_async_in_sync_context`
  #"if inspect.iscoroutine(value)"): a coroutine is `value.close()`d and `SyncMisuseError`
  raised BEFORE the `return value`. So an `async def has_permission` is rejected loudly
  before the `if not allowed: return False` branch (`sets.py #"if not allowed"`) — a truthy
  orphaned coroutine can never be silently treated as ALLOW. Fail-closed short-circuit on
  the first denier intact; kwargs match the helper signature exactly.
- **Recourse string single-sourced.** `_PERMISSION_ASYNC_RECOURSE` defined once
  (`permissions.py #"_PERMISSION_ASYNC_RECOURSE = ("`), one import in sets.py.
- **`_VALID_OPERATIONS` single-module + committed comment accurate.** Grep across
  `django_strawberry_framework/` confirms the only consumers are
  `_validate_mutation_meta` (`sets.py #"if operation not in _VALID_OPERATIONS"` membership +
  the `sorted(_VALID_OPERATIONS)` error message). `resolvers.py` dispatches on verb literals
  (`#"meta.operation == \"create\""`, `#"meta.operation == \"update\""`, and positional
  `_authorize_or_raise(..., "create"/"update"/"delete", ...)`) and does NOT import the set.
  The committed comment (`sets.py #"membership check only"`) is accurate.
- **Meta validation completeness.** Unknown-key guard (own keys only, no MRO walk →
  ConfigurationError), no-resolvable-model → ConfigurationError, bad/absent `operation` →
  ConfigurationError, `fields`+`exclude` mutual exclusion, bare-string + duplicate-name
  rejection in `_normalize_field_sequence`, and `delete` + fields/exclude rejection — all
  present and fail loud at class creation. `_validate_permission_classes` rejects bare
  class/str/bytes and any entry lacking a callable `has_permission`.
- **Phase-2.5 input binding** intact: `_bind_mutation` resolves primary type, materializes
  the operation input (`create`/`update`) and `<Name>Payload` through the same
  `materialize_mutation_input_class` ledger; `bind_mutations` clears `_shape_build_cache`
  per pass.
- **GLOSSARY `#djangomutation` accurate** vs current source (Meta keys, verb set
  `"create"/"update"/"delete"`, phase-2.5 bind + primary-type resolution + Input/
  PartialInput/`<Name>Payload` materialization, `permission_classes` default seam).

### DRY findings disposition
None at file level — module is maximally single-sourced for its own concerns (input
shape/name/cache-key via `inputs.py::mutation_input_shape`; async-guard delegated to
`reject_async_in_sync_context`; recourse to `_PERMISSION_ASYNC_RECOURSE`). The cross-module
verb-vocabulary candidate is correctly FORWARDED to the project pass, not re-raised here.

### Temp test verification
- None — no source/behavior change to prove; the maintainer's committed delegation is
  verified against the live helper contract and grep evidence above.

### Changelog disposition
`Not warranted`, with BOTH required citations (AGENTS.md #21 + active-plan silence). `git
diff -- CHANGELOG.md` empty. Internal-only framing matches the zero-edit diff scope.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the (re-opened)
`mutations/sets.py` checklist box in `docs/review/review-0_0_11.md`.
