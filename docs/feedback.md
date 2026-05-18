# Review feedback - `docs/spec-014-meta_primary-0_0_6.md` revision 4

Scope: final-pass review of revision 4 against the current registry, type-finalization, relation-override, and optimizer code. The previous high-severity implementation issues are mostly resolved; the remaining items are contradictions and worker traps that can still leak into the implementation or closeout docs.

## High-Severity Findings

### H1. Non-goals still classify the already-shipped direct relation override path as deferred

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:281`, `docs/spec-014-meta_primary-0_0_6.md:710`, `docs/spec-014-meta_primary-0_0_6.md:717`

Revision 4 correctly preserves consumer-authored relation fields in the H1 fix and even adds regression tests for direct secondary-type overrides. But the Non-goals section still says "No consumer-side override of relation resolution per field (e.g., `category: AdminCategoryType = ...` syntax)" and the Out-of-scope list repeats that consumer-side relation override resolution is deferred.

That contradicts the live package contract:

- `docs/FEATURES.md:230-237` lists annotation-only and `strawberry.field` relation overrides as supported relation shapes.
- `tests/types/test_definition_order.py:174`, `:201`, and `:319` pin annotation-only, assigned resolver, decorator, and string relation override behavior.
- This spec's own Slice 4 tests at `docs/spec-014-meta_primary-0_0_6.md:138-139` require consumer-authored relation overrides to survive and target a secondary type instead of the primary.

If a worker follows the Non-goals wording, they can treat `category: AdminCategoryType` as future work and weaken the H1 preservation path this card explicitly needs.

Required spec change: rephrase the Non-goal and Out-of-scope entries to say no **new override API** ships in this card, especially no `Meta.field_types = {...}` style override. Explicitly state that the already-shipped direct annotation / assigned `strawberry.field` relation override contract remains in scope and may target a secondary `DjangoType`.

## Medium-Severity Findings

### M1. The verbatim KANBAN body still says "ALL relation annotations"

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:168`, `docs/spec-014-meta_primary-0_0_6.md:192`, `docs/spec-014-meta_primary-0_0_6.md:233`, `docs/spec-014-meta_primary-0_0_6.md:734`

Slice 6 tells the worker to drop in the KANBAN body verbatim. That body still says relation conversion "defers ALL relation annotations to `finalize_django_types()`." This reintroduces the exact rev2 over-broad wording that rev3 fixed everywhere else.

The implementation and changelog bullets now correctly say **auto-synthesized** relation annotations are deferred and consumer-authored annotations / assigned `strawberry.field` resolvers skip synthesis. The KANBAN body should use the same wording, because it becomes the closeout source of truth.

Required spec change: replace "defers ALL relation annotations" with "defers all auto-synthesized relation annotations" and add the short consumer-authored-fields exception in the KANBAN body.

### M2. Optimizer origin plumbing needs explicit ownership of `_resolve_model_from_return_type`

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:131`, `docs/spec-014-meta_primary-0_0_6.md:132`, `docs/spec-014-meta_primary-0_0_6.md:539`, `docs/spec-014-meta_primary-0_0_6.md:557`

The H2 contract needs the resolver's origin Strawberry type in `_get_or_build_plan`, `_build_cache_key`, and `plan_optimizations`. In the current code, that origin exists only inside `_resolve_model_from_return_type()` and is discarded when the helper returns `registry.model_for_type(origin)` at `optimizer/extension.py:396`.

The spec says to "thread the resolved origin Strawberry type" but does not name this helper as a required change or name the existing tests that assert the old return shape (`tests/optimizer/test_extension.py:469`, `:499`, `:508`, `:517`). A worker can update the walker/cache key surface and still be left without a reliable `origin` value at the extension call site.

Required spec change: add an explicit Slice 4 checklist item to change `_resolve_model_from_return_type` into a helper that returns both values, for example `(origin, model)` or a small named tuple, or to add a sibling `_resolve_origin_and_model_from_return_type`. Include the existing test rewrites for the helper's return shape and the `_build_cache_key` signature tests.

## Low-Severity Findings

### L1. Finalizer line references are still off in this tree

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:126`, `docs/spec-014-meta_primary-0_0_6.md:256`, `docs/spec-014-meta_primary-0_0_6.md:496`, `docs/spec-014-meta_primary-0_0_6.md:647`

The spec now references `types/finalizer.py:68` for `target_type = registry.get(...)`, but the current assignment is at `django_strawberry_framework/types/finalizer.py:69`; line 68 is the `continue` in the consumer-authored branch. Minor, but this spec has been deliberately line-reference-heavy for worker planning, so the reference should be corrected or softened to "near the pending-relation loop."

### L2. Definition of done still has the narrow version no-op wording

Spec ref: `docs/spec-014-meta_primary-0_0_6.md:738`

The detailed Slice 5 wording correctly says the version bump is a no-op if any prior `0.0.6` card already bumped it. The Definition of done still says no-op if `WIP-ALPHA-015-0.0.6` already bumped. Broaden this final checklist item to "any prior `0.0.6` card" so it matches the rest of revision 4.

### L3. `DjangoTypeDefinition.primary` is described as consumed by code that does not use it

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:102`, `docs/spec-014-meta_primary-0_0_6.md:529`, `docs/spec-014-meta_primary-0_0_6.md:531`

The spec says `DjangoTypeDefinition.primary` is stored so the schema audit and optimizer walker can read the flag without re-querying the registry. The actual decisions route ambiguity checks through `registry.primary_for(model)` and optimizer root planning through the origin type, not through `definition.primary`.

The field is harmless and useful for introspection/future work, but the stated consumers are misleading. Either remove "schema audit, optimizer walker" from the rationale, or add a concrete planned read site. Otherwise Worker 2 may add redundant definition-primary checks that drift from `_primaries`, the stated single source of truth.

### L4. The same-type re-register rationale overstates current behavior

Spec ref: `docs/spec-014-meta_primary-0_0_6.md:308`

Decision 2 says treating re-registration of the same type as a no-op "matches the existing idempotent-import behavior." The current `TypeRegistry.register()` checks `model in self._types` before checking `type_cls`, so `register(Model, T)` followed by `register(Model, T)` raises today at `registry.py:88-89`.

The new idempotent behavior is fine and well-tested in the spec; just phrase it as a new import/retry-tolerant behavior rather than an existing one.

## Notes

Revision 4 substantially addresses the earlier relation-binding, primary-flip, rollback, audit-placement, stale-test ownership, schema-audit secondary coverage, and optimizer call-site issues. No tests were run; this is a spec review only.
