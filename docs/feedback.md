# Foundation spec review feedback

Reviewed:

- `KANBAN.md`
- `docs/spec-rich_schema_architecture.md`
- `docs/spec-definition_order_independence.md`
- `docs/spec-foundation.md`

The long-term direction is coherent: the 0.0.4 foundation slice should unblock definition-order independence without prematurely shipping Layer 3 systems. The remaining issues below are mostly lifecycle/atomicity gaps where the docs currently promise more than the implementation can safely guarantee.

## P1 — Finalization atomicity is overstated

`docs/spec-foundation.md` says `finalize_django_types()` is atomic: it either resolves, attaches resolvers, finalizes every type, and marks the registry finalized, or it raises with no `DjangoTypeDefinition.finalized` flags flipped.

That is only true for the Phase 1 unresolved-target failure path in the pseudocode. It is not true for later failures:

- `_attach_relation_resolvers(...)` mutates classes by setting `strawberry.field(...)` attributes.
- `strawberry.type(type_cls, ...)` mutates each class by creating/updating `__strawberry_definition__`.
- The Phase 3 loop flips `definition.finalized = True` one type at a time after each successful `strawberry.type(...)` call.

If type N finalizes successfully and type N+1 fails because of a bad user annotation, Strawberry forward-ref error, duplicate field, etc., the process is partially mutated even though `registry.is_finalized()` remains false.

Fix the contract before implementation:

- Either weaken the guarantee to “failure-atomic only before Strawberry mutation begins; after a Strawberry-side failure, call `registry.clear()` and recreate fresh classes”.
- Or add a prevalidation phase that can catch all expected `strawberry.type(...)` failures before mutating any class, if that is actually possible.
- Add a test that deliberately makes one type fail during `strawberry.type(...)` and asserts the documented recovery behavior.

## P1 — Finalization is not thread-safe as documented

`docs/spec-foundation.md` currently says `finalize_django_types()` is safe to call from any thread and does not need a lock because tests are single-threaded and production callers run it from request thread or schema construction.

That is unsafe. The finalizer mutates a process-global registry and class objects. The current registry explicitly has no locking, and class mutation during concurrent schema/request handling can produce partial or inconsistent Strawberry definitions.

Fix the lifecycle contract:

- `finalize_django_types()` must run during single-threaded import/app/schema setup, before serving requests.
- Do not describe request-thread finalization as supported.
- If future helpers might auto-trigger finalization lazily, they need a real lock or must be constrained to schema construction only.

## P1 — Import discovery is underspecified

The foundation slice exposes only `finalize_django_types()`; it explicitly does not ship `DjangoSchema`, `DjangoConnectionField`, `DjangoNodeField`, `apps.py`, or module autodiscovery.

That means finalization can only resolve `DjangoType`s whose Python modules have already been imported. A project can have a valid `CategoryType` in another app module, but if that module has not been imported before `finalize_django_types()`, the finalizer will report `Category` as unresolved.

The spec should make this explicit and test/document it:

- Users must import every module that defines `DjangoType` classes before calling `finalize_django_types()`.
- The README setup example needs to show the import boundary, not just the finalizer call.
- Consider adding a deliberate “target type exists in code but module not imported” doc note, because this will be the most common production failure mode until `DjangoSchema`/`apps.py` or another discovery mechanism ships.

This matters for the KANBAN direction because `apps.py` remains backlog and cannot silently be assumed by the 0.0.4 foundation slice.

## P1 — Manual relation annotation contract ignores consumer resolvers/fields

The spec pins a relation-field manual annotation contract: if a consumer supplies an annotation for a relation field, collection skips placeholder synthesis and pending-relation recording, and the finalizer never rewrites that annotation.

However, Phase 2 still calls `_attach_relation_resolvers(type_cls, definition.selected_fields)` for every selected relation field. That function sets `setattr(cls, field.name, strawberry.field(resolver=resolver))`.

So a consumer shape like this can be clobbered:

- `items: list["ItemType"] = strawberry.field(resolver=custom_items)`
- `@strawberry.field def items(...) -> list["ItemType"]`
- possibly any pre-existing relation field descriptor/resolver assigned by the user

The spec should choose one behavior:

- Consumer-authored relation field/resolver wins, so finalizer must skip resolver attachment for that field.
- Or annotation-only override is supported, but field/resolver override is explicitly unsupported and should raise a clear error instead of silently overwriting.

Add tests for both annotation-only and resolver/field-assignment cases.

## P1 — M2M end-to-end test plan conflicts with unmanaged fixtures

`docs/spec-foundation.md` says the cardinality fixture models should be unmanaged (`managed = False`) and that resolver-execution tests needing persistence are out of foundation scope. Later, the end-to-end schema tests require executing an M2M query such as `{ allBooks { title tags { name } } }`.

Those requirements conflict unless the test uses a non-DB resolver stub or creates temporary tables. A real M2M resolver calls the related manager and needs both model tables plus the through table.

Fix the acceptance plan:

- Either make the M2M schema test metadata-only and reserve DB-backed M2M execution for a later fixture.
- Or explicitly create the unmanaged test tables/through table in the test setup.
- Or monkeypatch the resolver/queryset in a documented way so the test proves Strawberry shape, not Django M2M persistence.

## P2 — `registry.clear()` is described as a full clean state, but it cannot undo class mutation

The spec says `registry.clear()` returns the package to a fully clean state. It can clear registry maps, pending relations, enum cache, and finalized flags. It cannot remove:

- `__strawberry_definition__` from already-finalized classes
- relation resolver attributes attached to already-mutated classes
- `__django_strawberry_definition__` stored on class objects
- rewritten `__annotations__`

That is okay if tests always define fresh classes after `registry.clear()`, but the spec should say that explicitly.

Suggested wording:

- `registry.clear()` resets registry state for fresh type classes.
- It does not roll back mutations on already-created Python classes.
- Tests must not reuse finalized `DjangoType` classes after clearing unless a helper explicitly strips class-level Strawberry/DSF metadata.

## P2 — Successful finalization leaves “pending” records unless cleared

The pseudocode resolves entries from `registry.iter_pending_relations()` but never clears `_pending` after success. After finalization, `iter_pending_relations()` would still return historical records that are no longer pending.

That can confuse diagnostics and future schema audit code.

Pick one:

- Clear `_pending` after all relations resolve successfully.
- Rename the storage/API to something like `_relation_records` if resolved records intentionally remain.
- Track a resolved/unresolved state on each record.

Add an assertion to the idempotency tests for the chosen behavior.

## P2 — Same-module/manual forward-reference behavior needs an explicit test

The spec defers borrowing Strawberry-Django’s `get_strawberry_annotations`, while also promising manual relation annotations can flow through unchanged.

That leaves a risky gap for these user forms:

- `from __future__ import annotations` with `items: list[ItemType]`
- string annotations such as `items: list["ItemType"]`
- `Annotated[..., strawberry.lazy(...)]`
- same-module versus cross-module target types

If the finalizer simply mutates `cls.__annotations__` and later calls `strawberry.type(...)`, Strawberry may handle these, but the spec should not assume it.

Add acceptance tests for:

- same-module string forward refs without `strawberry.lazy`
- future-annotations stringified refs
- cross-module lazy refs
- a manual annotation to a non-primary or alternate target type, even if multi-type support remains deferred

If any of those are unsupported in 0.0.4, document the exact supported manual annotation forms.

## P2 — Rich architecture Phase 1 conflicts with the foundation slice

`docs/spec-rich_schema_architecture.md` says Phase 1/Foundation adds:

- `DjangoTypeDefinition`
- pending relation registry
- `finalize_django_types()`
- schema helper `DjangoSchema`
- tests for finalization order

But `docs/spec-foundation.md` explicitly says `DjangoSchema` does not ship in this slice. KANBAN also frames the current focus as the explicit finalizer, not schema helpers.

Update the rich architecture migration path so Phase 1 matches the final foundation contract:

- Foundation ships only `finalize_django_types()`.
- `DjangoSchema` is a later wrapper/helper phase.

## P2 — `PendingRelation.relation_kind` naming is inconsistent across specs

`docs/spec-rich_schema_architecture.md` uses:

- `Literal["one", "many", "reverse_one_to_one"]`

`docs/spec-foundation.md` and the current utility type use:

- `Literal["forward_single", "many", "reverse_one_to_one"]`

Use the current `utils.relations.RelationKind` names everywhere. Otherwise implementation and tests can drift on the forward single-valued relation name.

## P2 — Spike workflow is a gate but not an implementation phase

The foundation spec correctly says no production code should be written before Spike A passes, but the phased implementation order starts with adding production dataclasses and registry APIs.

Add an explicit Phase 0:

1. Add/run Spike A, B, and C under `scripts/spikes/`.
2. Record the outcome in the spec or README.
3. Delete the throwaway scripts only after their conclusions are captured.
4. Only then begin production implementation.

Without this phase, the implementation checklist contradicts the gate.

## P2 — The spec has a stale self-reference to `docs/feedback.md`

`docs/spec-foundation.md` says “the eight clarifications from the verification report and the fifteen items in `docs/feedback.md` together form the checklist...”

That is brittle and currently circular: this feedback file is being created after the spec, and the number of items may change.

Replace it with wording like:

- “The current review feedback in `docs/feedback.md` forms the review checklist until resolved.”

Avoid pinning an item count in the implementation contract.

## P3 — Source line references are already drifting

The specs include many exact line references to current source files. Several are already stale after recent optimizer refactors, for example `DjangoOptimizerExtension` now has `_get_or_build_plan`, `_publish_plan_to_context`, `_context` helpers, string AST cache keys, and B8 diffing that the architecture spec’s baseline does not mention.

This is not a blocker, but it makes specs harder to trust during implementation.

Suggestion:

- Keep exact line references only for external prior-art snapshots.
- For in-repo source, reference symbols and files rather than line numbers unless the line is part of a review target.
- Refresh the current baseline section before starting the slice.

## P3 — Proposed Layer 3 module layout conflicts with KANBAN package layout

`docs/spec-rich_schema_architecture.md` proposes flat modules such as:

- `django_strawberry_framework/filters.py`
- `filterset.py`
- `orders.py`
- `orderset.py`
- `aggregateset.py`

KANBAN lists planned Layer 3 subsystems as packages:

- `filters/`
- `orders/`
- `aggregates/`

This should be aligned before Layer 3 specs land. The package layout affects import paths, public surface promotion, and test tree mirroring.

## P3 — Generic unresolved-relation fallback is discussed as a Meta key without a card

The rich architecture spec sketches:

- `Meta.unresolved_relations = "generic"`
- default `"error"`

KANBAN and the foundation spec both say generic fallback is not part of 0.0.4 and should not ship by default. If this remains as a possible future feature, it should be framed as a deferred design idea with its own future card. Otherwise readers may assume `Meta.unresolved_relations` is planned soon and start designing around an unaccepted Meta key.