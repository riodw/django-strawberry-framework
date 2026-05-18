# Review feedback — `docs/spec-014-meta_primary-0_0_6.md` revision 2

Scope: second-pass review of the updated spec against current registry, type collection/finalization, relation override tests, and optimizer code.

## High-Severity Findings

### H1. The "always defer every relation field" wording can break consumer-authored relation overrides

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:106`, `docs/spec-014-meta_primary-0_0_6.md:467`, `docs/spec-014-meta_primary-0_0_6.md:653`, `docs/spec-014-meta_primary-0_0_6.md:657`

Revision 2 correctly removes eager binding for auto-generated relation annotations, but the spec repeatedly says "every relation field" should become `PendingRelationAnnotation`. That is too broad. Current `types/base.py` deliberately skips synthesis when the relation is consumer-authored (`consumer_authored_fields`) so annotation overrides and assigned `strawberry.field` resolvers survive. Existing tests pin this in `tests/types/test_definition_order.py:174` and `tests/types/test_definition_order.py:201`.

If Worker 2 implements the wording literally, assigned relation fields can receive a synthetic `PendingRelationAnnotation` class annotation even though the consumer-owned `StrawberryField` should be the only source of truth. That risks changing Strawberry field construction and violates the spec's own risk note that direct relation annotations remain unchanged.

Required spec change: say "always defer auto-synthesized relation fields" and explicitly preserve the existing early `if field.name in consumer_authored_fields: continue` behavior. Add Slice 4 regression checks that annotation-only and assigned relation overrides still pass after the always-defer change.

## Medium-Severity Findings

### M1. `register()` still allows a primary flag flip from `True` to `False`

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:49`, `docs/spec-014-meta_primary-0_0_6.md:50`, `docs/spec-014-meta_primary-0_0_6.md:316`, `docs/spec-014-meta_primary-0_0_6.md:606`

The text says primary state is immutable and same-type re-registration with a flipped primary flag raises. The pseudocode only catches the `False -> True` flip:

`if primary and self._primaries.get(model) is not type_cls: raise ...`

If `T` is already registered as primary, `register(Model, T, primary=False)` returns `False` and silently leaves the primary in place. That contradicts the stated "primary flag cannot be flipped" contract.

Recommended fix: in the same-type branch, compare the requested flag to stored state:

`stored_primary = self._primaries.get(model) is type_cls`

`if primary != stored_primary: raise ConfigurationError(...)`

Add a test for `register(Model, T, primary=True)` followed by `register(Model, T, primary=False)`.

### M2. Existing tests that assert old behavior need explicit slice ownership

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:63`, `docs/spec-014-meta_primary-0_0_6.md:116`, `docs/spec-014-meta_primary-0_0_6.md:592`

The spec adds new tests but does not explicitly update current tests that will fail as soon as the behavior changes:

- `tests/test_registry.py:57` still expects registering a second type for the same model to raise.
- `tests/types/test_base.py:68` still expects declaring a second `DjangoType` for the same model to raise.
- `tests/types/test_base.py:509`, `:526`, `:549`, and `:598` assert eager relation annotations before `finalize_django_types()`. The always-defer change makes those pre-finalize assertions intentionally stale.

Add checklist items in the relevant slices to rewrite these tests in the same commit as the behavior change. Otherwise a worker following only the added-test list can produce a locally focused green run while the full suite fails.

## Low-Severity Findings

### L1. Plan-cache wording still contradicts the H2 fix

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:612`, `docs/spec-014-meta_primary-0_0_6.md:516`, `docs/spec-014-meta_primary-0_0_6.md:658`

Line 612 says the plan cache key includes the resolver return type, "not the model." The H2 fix elsewhere says the key includes the origin type alongside the model. The latter matches current cache shape and the intended change. Rewrite the edge-case bullet to say "includes the resolver's origin type alongside the model."

### L2. One Slice 5 no-op sentence still names only `WIP-ALPHA-015`

Spec ref: `docs/spec-014-meta_primary-0_0_6.md:598`

The detailed Slice 5 checklist now correctly says the repo is already at `0.0.6` from `spec-013`, but the Implementation plan summary still says "No-op if `WIP-ALPHA-015-0.0.6` already bumped them." Broaden that sentence to "no-op if any prior `0.0.6` card already bumped them" to match the rest of the revision.

### L3. Finalizer idempotency language does not match the current guard

Spec ref: `docs/spec-014-meta_primary-0_0_6.md:614`

The spec says calling `finalize_django_types()` after a successful finalize re-runs the audit. Current finalizer behavior returns immediately when `registry.is_finalized()` is true. Either behavior is defensible because registry mutation is already blocked after finalization, but the spec should choose one explicitly: keep the current no-op guard and say the audit does not re-run after finalization, or require moving the audit before the finalized guard.

## Notes

The prior high-severity findings around wrong-primary relation binding, root optimizer planning for secondary return types, schema-audit secondary coverage, rollback corruption, KANBAN path, and broad version no-op handling are substantially addressed in revision 2. No tests were run; this is a spec review only.
