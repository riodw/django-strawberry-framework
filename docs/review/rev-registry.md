# Review: `django_strawberry_framework/registry.py`

Status: verified

## DRY analysis

- **Defer `register_with_definition`'s rollback block until a third snapshot site lands or a fourth rollback field is added.** Today the inverse-of-`register` rollback in `django_strawberry_framework/registry.py::TypeRegistry.register_with_definition` (registry.py:302-313) is the only site that hand-rolls the `(types, _models, _primaries)` undo, and `unregister` (registry.py:172-188) is the only other site that performs the same three-map drop. The two have different shapes: `unregister` always drops, `register_with_definition`'s rollback only drops state appended by THIS call AND restores a possibly-pre-existing `_primaries[model]` entry. Pulling them through a shared `_drop_type_state(model, type_cls, *, restore_primary=None)` helper would couple two intentionally-different contracts. Defer until a third site appears (e.g., a public `replace_type` mutator) OR until `register` grows a fourth model-keyed map; the helper signature should be `_drop_type_state(model, type_cls, *, restore_primary=<sentinel>)` so the "no restore vs. restore-this-class" semantics stay greppable.
- **Defer collapsing the two `_already_registered`-shaped error sites into a single helper until a third "X is already Y for Z" site lands.** The static helper `TypeRegistry._already_registered` (registry.py:67-79) already centralises the two cross-key collision phrasings — the reverse-collision in `register` (registry.py:121) and the `(model, field_name)` collision in `register_enum` (registry.py:384-388). The remaining three `ConfigurationError` raises — primary-flip on idempotent re-register (registry.py:126-129), duplicate-primary collision (registry.py:134-137), and `register_definition`'s definition-already-set (registry.py:274-276) — use distinct phrasings test-pinned by substring, so they cannot be folded into the same helper without churning the test suite. Defer until a fourth call site emerges that genuinely shares the "X is already <label> Y" phrasing; the helper signature is already proven and re-extending it costs nothing.
- **Defer cycle-safe filter-namespace co-clear consolidation until a third co-cleared submodule lands.** The `clear()` epilogue (registry.py:412-432) carries two parallel `try: from .filters...; except ImportError: pass; else: <clear>` blocks per spec-021 Decision 9. The blocks are deliberately independent so a partial-rollback build state where one cache is reachable and the other is not still clears whatever IS reachable. Folding them through a `_best_effort_clear(module_name, attr_name, action)` helper would inline-document the same property less clearly than the current paired blocks. Defer until a third filter-side cache enters the co-clear contract; at that point a small helper of the shape `_best_effort_clear(import_path, action_callable)` becomes the right factoring.

## High:

None.

## Medium:

None.

## Low:

### Stale spec-021 sub-revision citation in `clear()` comment

The `clear()` filter-namespace co-clear comment (registry.py:412-419) cites `spec-021 Decision 9, M5 of rev3 + M4 of rev8`. Worker 1 confirmed `docs/SPECS/spec-021-apps-0_0_7.md` exists (no archival-path drift on the spec stem), and the rev3/rev8 sub-revision pointers are an audit trail of the design conversation, not file paths. Citation is correct; no edit warranted. Recorded here so a future reviewer doesn't second-guess the rev-anchors during the next round of `docs/SPECS/NEXT.md` Step 8 archive sweeps.

### `register_with_definition` rollback comment cites a removed-from-text contract phrase

The inline comment at registry.py:302 — `# Inverse of register's mutations above; mirror any new register side-effect here on rollback.` — references "the mutations above". `register` (registry.py:81-142) is in a separate method, not "above" lexically; the phrase would read more clearly as `# Inverse of register's mutations (registry.py::TypeRegistry.register); mirror any new register side-effect here on rollback.` Defer until any other rollback site is added or until `register` grows a fourth side-effect; both triggers force a re-read of this comment anyway.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_check_mutable()` (registry.py:52-65) is the single mutation-gate helper called by every public mutator except `clear()` — `register`, `unregister`, `register_definition`, `register_with_definition` (via `register`/`register_definition`), `add_pending_relation`, `discard_pending`, and `register_enum`. `_already_registered` (registry.py:67-79) centralises the two cross-key collision phrasings (reverse-collision in `register`, `(model, field_name)` collision in `register_enum`). `register_with_definition` (registry.py:279-313) delegates to `register` + `register_definition` rather than touching `_types`/`_models`/`_primaries` directly, keeping the lock-step invariant in a single place.
- **New helpers considered.** Considered pulling `register_with_definition`'s rollback through a shared `_drop_type_state` helper alongside `unregister`'s drop; rejected because the two contracts diverge on primary handling (always-drop vs. snapshot-and-maybe-restore). Considered folding the three primary-mismatch / definition-already-set error sites into `_already_registered`; rejected because each is test-pinned by a distinct phrasing substring and the helper's two-arg `label` shape doesn't fit them. Considered consolidating the two filter-namespace `try/except ImportError` blocks in `clear()`; rejected because their independence is load-bearing (partial-rollback build state).
- **Duplication risk in the current file.** The asymmetry between `unregister`'s drop and `register_with_definition`'s rollback is intentional: `unregister` is the public "drop this type entirely" path, while the rollback only undoes state THIS call added (preserving idempotent re-register survival). The duplicated three-map-update sequence reads more clearly inline at each site than it would through a shared helper.

### Other positives

- Identity-matched `discard_pending` (registry.py:341-352) avoids coupling the registry module to `PendingRelation`'s `__eq__`/`__hash__` semantics; `test_discard_pending_tolerates_non_hashable_django_field` (tests/test_registry.py:595-614) pins this contract directly with a `__hash__ = None` django_field.
- `iter_pending_relations`'s docstring (registry.py:329-338) accurately captures the rebinding semantics of `discard_pending` (which does `self._pending = [...]`, rebinding rather than mutating in place), and the documented consumer (`types/finalizer.py::finalize_django_types`, finalizer.py:190-225) drains into local lists before calling `discard_pending`, matching the documented contract exactly.
- `clear()`'s `_check_mutable` bypass is intentional and documented (registry.py:395-403) — test teardown needs to reset a finalized registry; the bypass is greppable as "the only public mutator that bypasses the guard".
- The `_primaries` rollback in `register_with_definition` (registry.py:309-312) correctly distinguishes "pre-existing primary survives" from "we added the primary and now drop it" via the snapshot at registry.py:297, pinned by `test_register_with_definition_rollback_restores_pre_existing_primary` (tests/test_registry.py:833-865) and `test_register_with_definition_rollback_clears_primary` (tests/test_registry.py:812-830).
- `register`'s ordering is correct: the reverse-collision check at registry.py:119-121 runs BEFORE `_types.setdefault(model, [])` at registry.py:122, so a reverse-collision raise never leaves an empty list in `_types[model]` for a previously-unregistered model.
- `register`'s idempotent-re-register branch (registry.py:123-130) correctly handles the primary-flip case in both directions, pinned by `test_register_same_type_re_register_with_flipped_primary_false_raises` (tests/test_registry.py:790-798) and `test_register_same_type_re_register_with_flipped_primary_true_raises` (tests/test_registry.py:801-809).
- The `TYPE_CHECKING` guard (registry.py:28-30) carries an explicit `# pragma: no cover` comment so the import-time-only branch doesn't depress coverage; this is the canonical pattern for TYPE_CHECKING blocks per AGENTS.md.
- `model_for_type(None)` short-circuits to `None` (registry.py:221-223) so `DjangoOptimizerExtension` can pipeline through unwrapped wrapper types without an extra guard — load-bearing for the optimizer's `unwrap_graphql_type` → `model_for_type` chain, pinned by `test_model_for_type_returns_none_for_none` (tests/test_registry.py:76-83).
- `models_with_multiple_types()` (registry.py:253-259) returns a generator rather than a materialised list, keeping the finalize-time audit path lazy and consumer-driveable.

### Summary

`registry.py` is the process-global type registry with eight public mutators, eleven public readers, and three internal invariants (`_types`/`_models` lock-step, `_primaries` is a subset of `_types`, `_pending` identity-stable across `discard_pending`'s rebinding). The class is densely documented, with each load-bearing branch pinned by a dedicated test in `tests/test_registry.py` (1358 lines covering 60+ test cases including 4 different `register_with_definition` rollback contracts). Two control-flow hotspots — `register` at 62 lines / 7 branches and `unregister` at 45 lines / 3 branches — are appropriately complex given the multi-map lock-step invariants they maintain, and the docstrings carry the reasoning that the bodies would otherwise need inline comments to explain. GLOSSARY drift quick-check on `Meta.primary`, `primary_for`, `types_for`, and `models_with_multiple_types` confirms the GLOSSARY entry (docs/GLOSSARY.md:694-711) is aligned with current behaviour: shipped (0.0.6) status, all four ambiguity rules accurate, registry-surface paragraph naming all three helpers with their actual return shapes. No High or Medium findings; one trigger-gated Low (rollback comment phrasing) and one no-edit Low (rev-anchor citation hygiene confirmation). No source/test/GLOSSARY edits warranted — shape #5 (no-source-edit cycle).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched

None — no-source-edit cycle.

### Tests added or updated

None — no-source-edit cycle.

### Validation run

- `uv run ruff format .` — not run; no source edits to format.
- `uv run ruff check --fix .` — not run; no source edits to lint.

### Notes for Worker 3

- Both Lows are forward-looking with explicit triggers:
  - Stale spec-021 sub-revision citation in `clear()` comment — citation is correct as-is; the Low records the audit trail confirmation so the next `docs/SPECS/NEXT.md` Step 8 archive sweep author doesn't re-flag it.
  - `register_with_definition` rollback comment phrasing — defer until any other rollback site is added OR until `register` grows a fourth side-effect; either trigger forces a re-read of the comment anyway.
- No GLOSSARY-only fix in scope. GLOSSARY entry on `Meta.primary` (docs/GLOSSARY.md:694-711) is aligned with current registry behaviour and surface methods (`primary_for`, `types_for`, `models_with_multiple_types`).
- DRY analysis carries three deferrals, all with explicit grep-able triggers: (a) third snapshot site for `register_with_definition`'s rollback helper, (b) fourth shared-phrasing site for `_already_registered`, (c) third co-cleared submodule for the filter-namespace `clear()` block. Worth grepping at the folder/project pass.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits warranted. The module's docstrings already carry the load-bearing contracts (mutation-after-finalize guard, identity-vs-equality `discard_pending` semantics, `register_with_definition` atomicity, `model_for_type(None)` short-circuit purpose, `clear()` test-only mutator with documented `_check_mutable` bypass). The two Low-severity comment observations recorded above are either trigger-gated (rollback comment) or no-edit-warranted (rev-anchor citation).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

**Not warranted.** No source/test/GLOSSARY/CHANGELOG edits. Per AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" and the active plan (docs/review/review-0_0_7.md) silence on registry-side changelog work, this cycle produces no consumer-visible behaviour change to document.

---

## Verification (Worker 3)

### Logic verification outcome

Shape #5 (no-source-edit cycle) terminal-verify. Scoped diff `git diff --stat HEAD -- django_strawberry_framework/registry.py tests/ docs/GLOSSARY.md CHANGELOG.md` showed only `docs/GLOSSARY.md` modified — that hunk is the list_field.py async-`__call__` widening from the prior list_field cycle (dispatch flagged it as out-of-scope for THIS cycle baseline) and contains no registry-related content. No registry.py, tests/test_registry.py, or CHANGELOG.md edits.

High and Medium are both `None.` — accepted on the artifact's no-source-edit framing.

Two Lows, both non-edit:
- Stale spec-021 sub-revision citation in `clear()` comment (registry.py:412-419) — Worker 1 confirmed `spec-021` exists and the `rev3`/`rev8` pointers are design-conversation audit anchors, not file paths; recorded as a no-edit confirmation so the next NEXT.md Step 8 sweep author doesn't re-flag.
- `register_with_definition` rollback comment phrasing at registry.py:302 — explicit "Defer until any other rollback site is added OR until `register` grows a fourth side-effect" trigger.

No GLOSSARY-only fix in scope.

### Spot-checks against source

- `_check_mutable` body at registry.py:52-65, `_already_registered` helper at registry.py:67-79, `register` reverse-collision at registry.py:119-121 BEFORE `setdefault` at registry.py:122, idempotent-re-register at registry.py:123-130, duplicate-primary at registry.py:134-137, `register_with_definition` rollback at registry.py:297-313 (snapshot at 297, conditional rollback at 303-312), `clear()` test-only mutator with `_check_mutable` bypass at registry.py:395-403, two independent `try/except ImportError` filter co-clear blocks at registry.py:420-432 — all match the artifact's `What looks solid` claims verbatim.
- All six cited test names grep-confirmed at the cited lines in `tests/test_registry.py`: `test_model_for_type_returns_none_for_none` (line 76), `test_discard_pending_tolerates_non_hashable_django_field` (line 595), `test_register_same_type_re_register_with_flipped_primary_false_raises` (line 790), `test_register_same_type_re_register_with_flipped_primary_true_raises` (line 801), `test_register_with_definition_rollback_clears_primary` (line 812), `test_register_with_definition_rollback_restores_pre_existing_primary` (line 833).

### DRY findings disposition

Three deferrals, all with explicit grep-able triggers and signature sketches:
1. `_drop_type_state(model, type_cls, *, restore_primary=<sentinel>)` — deferred until a third snapshot site lands or `register` grows a fourth model-keyed map.
2. Extending `_already_registered` to cover the three remaining `ConfigurationError` raises — deferred until a fourth call site shares the "X is already <label> Y" phrasing; the remaining three are test-pinned by distinct substrings.
3. `_best_effort_clear(import_path, action_callable)` — deferred until a third co-cleared filter-side submodule joins the contract.

All three deferrals correctly preserve test-pinned phrasings and the load-bearing independence of the current shapes.

### Temp test verification

None — no temp tests created; no behavior to falsify on a no-source-edit cycle.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `registry.py` checklist box in `docs/review/review-0_0_7.md`.

All shape #5 gates pass: (1) scoped diff is empty modulo the prior-cycle GLOSSARY hunk explicitly flagged out-of-scope in the dispatch; (2) all three Worker 2 sections open with `Filled by Worker 1 per no-source-edit cycle pattern.`; (3) both Lows are non-edit (one trigger-gated, one no-edit-warranted confirmation), no GLOSSARY-only fix; (4) Changelog `Not warranted` cites both AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") and active-plan silence on registry-side changelog work; (5) ruff outcomes "not run; no source edits to format / lint" are plausible for a no-source-edit cycle.

---

## Iteration log

None.
