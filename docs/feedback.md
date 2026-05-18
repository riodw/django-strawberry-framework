# Review feedback — `docs/spec-014-meta_primary-0_0_6.md` revision 3

Scope: third-pass review of the updated spec against current registry, type collection/finalization, relation override tests, and optimizer code. The headline rev2 findings (H1 always-defer scope, M1 symmetric flip guard, M2 stale-test ownership, L1 plan-cache wording, L2 prior-card wording, L3 finalizer idempotency) are substantially addressed in rev3. The findings below are smaller — one medium correctness gap, two medium clarification gaps, and four low-severity precision fixes.

## Medium-Severity Findings

### M1. Audit placement vs `is_finalized()` guard is ambiguous in Slice 3

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:109`, `docs/spec-014-meta_primary-0_0_6.md:450`, `docs/spec-014-meta_primary-0_0_6.md:631`

Slice 3 instructs: "Run at the **start** of `finalize_django_types()`, before pending-relation resolution." The L3 fix in Edge cases (line 631) only resolves correctly if the audit runs **below** the existing `is_finalized()` short-circuit at `types/finalizer.py:58-59` (`if registry.is_finalized(): return`). Above the guard the audit re-runs on every `finalize_django_types()` call — contradicting the rev3 L3 contract — and the existing test suite would not catch the regression because the audit is side-effect free against a locked registry.

Worker 2 reading Slice 3 in isolation can plausibly place the audit at the first line of the function. The L3 contract sits ~520 lines later in Edge cases, easy to miss.

Required spec change: rewrite Slice 3's audit-placement sentence to: "Run inside `finalize_django_types()`, **after the existing `is_finalized()` short-circuit** but before pending-relation resolution." Apply the same wording to Decision 5's prose. Optionally add a test that calls `finalize_django_types()` twice and asserts the audit did not raise / did not re-execute (e.g., observe a spy on `models_with_multiple_types`).

### M2. `_resolve_field_map` has two call sites; spec names only one for the `source_type` thread

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:120`, `docs/spec-014-meta_primary-0_0_6.md:122`, `docs/spec-014-meta_primary-0_0_6.md:487`, `docs/spec-014-meta_primary-0_0_6.md:528`

The H2 fix instructs Worker 2 to add a `source_type` keyword to `_resolve_field_map` and thread the resolver's origin Strawberry type to "the walker's first `_resolve_field_map(model, source_type=origin)` call". Current `optimizer/walker.py` calls `_resolve_field_map(model)` from **two** sites:

- `_walk_selections` at `optimizer/walker.py:125` — the obvious root path from `plan_optimizations`.
- `_selected_scalar_names` at `optimizer/walker.py:474` — a second helper that also resolves the field map.

If `_selected_scalar_names` is reachable from the root planning path (and not exclusively a nested recursion helper), it needs the same `source_type` propagation — otherwise scalar-only selections on a secondary-type root resolver still plan against the primary's field map. The spec does not direct Worker 1 to audit both call sites.

Required spec change: in the Slice 4 bullet for `_resolve_field_map`, name **both** call sites (`_walk_selections:125` and `_selected_scalar_names:474`) and instruct Worker 1's planning pass to determine which are root-path callers needing the keyword. Add a regression test where a secondary-type resolver selects only scalar fields and the planner uses the secondary's field map.

## Low-Severity Findings

### L1. Plan-cache key shape is under-described

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:123`, `docs/spec-014-meta_primary-0_0_6.md:490`, `docs/spec-014-meta_primary-0_0_6.md:533`, `docs/spec-014-meta_primary-0_0_6.md:629`

The spec describes today's cache key as "model + selection-set fingerprint" (Decision 6 row "Plan cache key") and tells Worker 1 to "pin the exact key tuple shape during planning". The actual structure at `optimizer/extension.py:437-440` is a four-element tuple: `(doc_key: str, relevant_vars: frozenset[tuple[str, Any]], target_model: type, response_path: tuple[str, ...])`. Worker 1 grepping for "selection-set fingerprint" finds nothing.

Recommended fix: in Decision 9 (or the Slice 4 plan-cache bullet) reference `extension.py:437-440` directly and quote the current tuple shape so Worker 1 knows what to extend (probable shape: add `origin: type | None` as a fifth slot, or replace slot 3 with `(target_model, origin)`).

### L2. Quoted disappearing collision message does not match the live string

Spec ref: `docs/spec-014-meta_primary-0_0_6.md:407`

Decision 3's "What disappears" sentence quotes the old message as `"<existing> is already registered as <existing>"`. The actual format at `registry.py:64-72` (`_already_registered` helper, label `"as"`) produces `"<ModelName> is already registered as <ExistingTypeName>"` — the first slot is the model name, the second is the type name, not two copies of "existing". The stale test at `tests/test_registry.py:57` matches `"already registered"` (loose substring), so the rewrite Worker 1 plans still passes, but the spec's quoted form misrepresents the real string and could mislead anyone refining the message.

Recommended fix: replace the quoted form with the actual template, e.g. `"<model_name> is already registered as <existing_type_name>"`.

### L3. `consumer_authored_fields` short-circuit is "in the per-field loop", not "at the top of `_build_annotations`"

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:117`, `docs/spec-014-meta_primary-0_0_6.md:484`, `docs/spec-014-meta_primary-0_0_6.md:698`

The H1 fix description repeatedly places the `if field.name in consumer_authored_fields: continue` guard "at the top of `_build_annotations`". In `types/base.py` the actual location is line 610 (relations branch) and line 631 (scalars branch) — both inside the per-field iteration, not the function preamble. Calling it "at the top" implies it short-circuits the whole function rather than skipping individual consumer-authored fields. Functional intent is correct; the description is just imprecise.

Recommended fix: rewrite as "the existing `if field.name in consumer_authored_fields: continue` short-circuit early in the per-field loop body (`types/base.py:610` for relations, `:631` for scalars)".

### L4. Finalizer line reference is off by one

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:118`, `docs/spec-014-meta_primary-0_0_6.md:245`, `docs/spec-014-meta_primary-0_0_6.md:485`

The spec references `types/finalizer.py:69` as the `target_type = registry.get(...)` line. The actual `target_type = registry.get(pending.related_model)` assignment is at line 68; line 69 is the subsequent `if target_type is None:` check. Worker 1 grepping `:69` lands on the conditional, not the call. Minor.

Recommended fix: change references from `types/finalizer.py:69` to `types/finalizer.py:68`.

### L5. Two named tests files do not exist today; spec frames them as "new or existing"

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:110`, `docs/spec-014-meta_primary-0_0_6.md:128`, `docs/spec-014-meta_primary-0_0_6.md:502`, `docs/spec-014-meta_primary-0_0_6.md:503`

Slices 3 and 4 point new tests at `tests/types/test_finalizer.py` and `tests/types/test_relations.py`. Neither file exists today:

- Finalizer test coverage currently lives in `tests/test_registry.py` (idempotency / finalization sections) and `tests/types/test_definition_order.py` (relation resolution after finalize).
- Relation-conversion test coverage currently lives in `tests/types/test_converters.py` (~1455 lines) and `tests/utils/test_relations.py`.

Decision 7's "new or existing — Worker 1 picks" framing is fine, but Worker 1 could create new files when an existing host is the lower-touch fit. Suggest the spec affirmatively name the existing hosts as the default (e.g., "extend `tests/types/test_converters.py`; create `tests/types/test_finalizer.py` only if the audit-test cluster grows past comfortable size in `test_converters.py`").

## Notes

- Rev2's high-severity findings (H1 wrong-primary relation binding, H2 root optimizer planning + plan-cache, H3 schema audit secondary coverage), the M1 rollback corruption, the M2 stale-test ownership trail, the L1 plan-cache wording, the L2 broader prior-card framing, and the L3 finalizer idempotency contract are all addressed in rev3 with explicit pseudocode, regression tests, and edge-case clarifications.
- The verbatim `DONE-014-0.0.6` KANBAN body now points at `docs/spec-014-meta_primary-0_0_6.md` (the working location), matching Slice 6's "spec stays at working location" rule.
- Pre-existing single-type-no-primary path stays backward compatible (`registry.get` still returns the lone type without `Meta.primary`), pinned by the `test_get_returns_single_type_when_one_registered_no_primary` test.
- No tests were run; this is a spec review only.
