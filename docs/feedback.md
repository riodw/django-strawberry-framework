# Review feedback — `docs/spec-014-meta_primary-0_0_6.md`

Scope: reviewed `docs/spec-014-meta_primary-0_0_6.md` against the current registry, `DjangoType` collection/finalization path, relation conversion, and optimizer code.

## High-Severity Findings

### H1. Relation binding can freeze the wrong secondary type before the primary is declared

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:95`, `docs/spec-014-meta_primary-0_0_6.md:383`, `docs/spec-014-meta_primary-0_0_6.md:490`

The spec says no `_build_annotations` call-site change is needed because `registry.get()` returning `None` will defer ambiguous relations. That misses the import-order case where exactly one non-primary type is registered when a relation source is collected, and the explicit primary is declared later.

Example failure shape:

- `AdminItemType` registers for `Item` first, with no `Meta.primary`.
- `CategoryType` is declared next. `registry.get(Item)` returns the single registered `AdminItemType`, so `CategoryType.items` is immediately annotated as `list[AdminItemType]`, not recorded as pending.
- `ItemType(primary=True)` registers later.
- Finalization sees one primary and succeeds, but `CategoryType.items` is already frozen to `AdminItemType`.

That violates the headline contract that relations resolve to the primary type and breaks definition-order independence. The spec should require `_build_annotations` to defer relation binding unless the related model has an explicit primary already, or more simply defer all relation annotations to finalization so the final primary/single-type state is known. Add a regression test where secondary-before-relation-before-primary still finalizes the relation to the primary.

### H2. Optimizer planning loses the actual secondary return type

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:387`, `docs/spec-014-meta_primary-0_0_6.md:390`, `docs/spec-014-meta_primary-0_0_6.md:508`, `docs/spec-014-meta_primary-0_0_6.md:533`

The spec says secondary-type resolvers stay planable because `model_for_type(AdminItemType) is Item`, but the current optimizer flow converts the GraphQL return type to only a model. From there, `plan_optimizations(..., model=Item)` calls `registry.get(Item)`, which the spec changes to return the primary type. A root resolver returning `AdminItemType` would therefore plan against `ItemType`'s `field_map` and `optimizer_hints`, not `AdminItemType`'s.

The spec also says the plan cache key includes the resolver return type, but current code keys on the target model, so primary and secondary resolvers for the same model can share the wrong cached plan.

The spec needs an optimizer design change: preserve the resolved origin type alongside the model, pass that source type into the walker for the root field-map/hints lookup, and include that type in the cache key. Keep `registry.get(related_model)` for nested default relation targets if the default target should be primary. Add a test where a secondary type exposes a field or hint not present on the primary, and verify the optimizer plans from the secondary definition.

### H3. The proposed schema-audit change skips reachable secondary types

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:99`, `docs/spec-014-meta_primary-0_0_6.md:388`, `docs/spec-014-meta_primary-0_0_6.md:542`

Switching `DjangoOptimizerExtension.check_schema()` from `registry.iter_types()` to `primary_or_single_per_model()` makes the audit inspect only one type per model. That misses relation fields exposed only on a reachable secondary type.

For example, if `ItemType(primary=True)` exposes only scalars and a reachable `AdminItemType` exposes `category`, the audit must still check `AdminItemType.category`. Skipping secondary types would let missing relation targets or bad optimizer coverage pass silently. The "no double-warn" goal should be solved by iterating reachable types and deduplicating warning keys if needed, not by dropping secondary types from the audit.

## Medium-Severity Findings

### M1. `register_with_definition` rollback can remove a pre-existing idempotent registration

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:45`, `docs/spec-014-meta_primary-0_0_6.md:502`, `docs/spec-014-meta_primary-0_0_6.md:522`

The rollback instruction says to pop from `_types[model]`, pop `_models`, and clear `_primaries` whenever `register_definition` fails. With the new idempotent `register()` behavior, `register_with_definition()` can call `register()` for a type that was already registered and therefore did not append anything. If `register_definition()` then raises because a different definition already exists, a naive rollback would remove the earlier valid registration.

The registry API should track whether `register()` actually appended/set state, or snapshot prior state before calling it, and only roll back state created by the current call. Add a test that pre-registers a type/definition, calls `register_with_definition()` again with the same type and a different definition, and asserts the original `_types`, `_models`, `_primaries`, and definition remain intact after the error.

### M2. The KANBAN done-card path contradicts the no-archive instruction

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:132`, `docs/spec-014-meta_primary-0_0_6.md:176`, `docs/spec-014-meta_primary-0_0_6.md:498`

The verbatim `DONE-014` body says the scope is per `docs/SPECS/spec-014-meta_primary-0_0_6.md`, but Slice 6 explicitly says this spec stays at `docs/spec-014-meta_primary-0_0_6.md` and archival is opt-in. If workers follow the no-archive instruction, the KANBAN card will point at a nonexistent or stale path.

Update the drop-in body to reference `docs/spec-014-meta_primary-0_0_6.md`, or make archival mandatory and align Slice 6 / Definition of done with that.

## Low-Severity Findings

### L1. Version-bump no-op wording is too narrow for the current repo state

Spec refs: `docs/spec-014-meta_primary-0_0_6.md:111`, `docs/spec-014-meta_primary-0_0_6.md:119`, `docs/spec-014-meta_primary-0_0_6.md:120`, `docs/spec-014-meta_primary-0_0_6.md:545`

The repo is already at `0.0.6` from the prior scalar card (`pyproject.toml`, `__init__.py`, `tests/base/test_init.py`, `docs/FEATURES.md`, `README.md`, `docs/README.md`, and `uv.lock`). The spec mostly frames no-op handling around `WIP-ALPHA-015` landing first. Broaden the wording to "if already bumped by any prior 0.0.6 card" so workers do not chase already-completed version edits.

## Notes

I did not review implementation because this request is for the new spec only. No tests were run; the feedback is based on reading the spec and current source.
