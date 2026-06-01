# Spec: Multiple `DjangoType`s per model with `Meta.primary`

Target release: `0.0.6`.
Status: draft (revision 6, post-TODO-anchor review).
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [`DjangoType`][glossary-djangotype], [`Meta.primary`][glossary-metaprimary], [`Relation handling`][glossary-relation-handling], [`finalize_django_types`][glossary-finalize-django-types]), [`KANBAN.md`][kanban] card `DONE-018-0.0.6`.
Card line: ["Multiple DjangoTypes per model with `Meta.primary` — registry-multiplicity + primary-type-resolution work for the remaining `0.0.6` patch."][kanban]

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft.
- **Revision 2** (post-feedback review) — three high-severity corrections plus two medium and one low:
  1. **H1**: relation binding in `_build_annotations` (`django_strawberry_framework/types/base.py::_build_annotations`) was specified as "no code change required; deferral happens when `registry.get()` returns `None`". That misses the import-order trap where a *single* secondary type registers first (so `registry.get()` returns it eagerly), the relation source binds against it, then the explicit primary registers later. The audit passes but the relation is frozen to the wrong type, breaking the headline contract and definition-order independence. Fix: **defer all relation annotations to finalization** regardless of registry state. Drops the eager-bind shortcut. Net post-finalize result is identical for single-type usage; multi-type usage now resolves correctly. New regression test pins secondary-before-source-before-primary.
  2. **H2**: optimizer planning was specified as "no code change; `model_for_type` already works for secondary types". That misses the **root** planning path: `django_strawberry_framework/optimizer/extension.py` resolves a resolver's return type to a model, then `django_strawberry_framework/optimizer/walker.py::_resolve_field_map` calls `registry.get(model)` to get back a type — which under multi-type semantics returns the *primary*, not the resolver's actual return type. A root resolver returning `AdminItemType` would plan against `ItemType.field_map` / `optimizer_hints`. The plan cache also keys on the model alone, so primary/secondary resolvers on the same model would share the wrong cached plan. Fix: thread the resolved origin type (the resolver's actual Strawberry return type) through `plan_optimizations` to the walker's root `_resolve_field_map` call; only the **nested** relation lookup uses `registry.get(related_model)` (which correctly returns the primary). [Plan cache][glossary-plan-cache] key includes the origin type. New Decision 9 captures the contract; Slice 4 expands accordingly.
  3. **H3**: schema audit was specified to switch from `registry.iter_types()` to `primary_or_single_per_model()` to avoid double-warning. That correctly avoids duplicate warnings but **skips reachable secondary types entirely** — if a secondary type exposes a relation field that the primary does not (e.g., `AdminItemType.category` where `ItemType` has only scalars), the audit silently misses it. Fix: keep iterating every reachable registered type but dedupe the warning collection (a `set` over the warning strings, or a `(source_model, field_name)`-keyed `set`). Drops the unused `primary_or_single_per_model()` helper from Decision 4; the schema audit no longer needs it. Adds a regression test where a secondary type exposes a unique relation field and the audit warns when its target is unregistered.
  4. **M1**: `register_with_definition` rollback was specified to unconditionally pop from `_types[model]`, `_models`, and `_primaries`. Under the new idempotent `register()` behavior, a re-registration of an already-stored type is a no-op for `register()`, so a subsequent `register_definition` failure would naively roll back *pre-existing* state. Fix: `register()` returns `bool` indicating whether state was added; `register_with_definition` snapshots `_primaries[model]` and only rolls back what its own call added. New regression test covers the pre-registered-type-then-fail-on-different-definition path.
  5. **M2**: the verbatim `DONE-018-0.0.6` KANBAN body referenced `docs/SPECS/spec-018-meta_primary-0_0_6.md`, but Slice 6 explicitly says the spec stays at `docs/spec-018-meta_primary-0_0_6.md` and archival is opt-in. Fix: rewrite the body to reference the working location. Archival decision stays with the maintainer post-merge.
  6. **L1**: version-bump no-op wording was framed around "if `DONE-019-0.0.6` lands first". Repo is *already* at `0.0.6` from `spec-017-deferred_scalars-0_0_6.md`, so the bump is a no-op against the current tree. Fix: broaden the wording to "any prior `0.0.6` card" so workers do not chase already-completed edits.
- **Revision 3** (post-feedback-2 review) — one high-severity correction plus four medium / low tightenings:
  1. **H1**: revision 2's always-defer language said *every* relation field becomes `PendingRelationAnnotation`. Too broad — current `types/base.py` deliberately skips synthesis when the field is consumer-authored (annotation overrides like `category: CategoryType` and assigned `strawberry.field` resolvers). Pinned by `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver` and `tests/types/test_definition_order.py::test_assigned_relation_field_override_keeps_consumer_resolver`. A literal reading of revision 2 would have Worker 2 overwrite a consumer's `StrawberryField` with a synthetic `PendingRelationAnnotation`, breaking annotation-override semantics that this card explicitly preserves. Fix: every "always defer" sentence now reads "always defer **auto-synthesized** relation fields" and points to the existing `if field.name in consumer_authored_fields: continue` short-circuit as the contract to keep. New Slice 4 regression checks pin annotation-only and assigned relation overrides still pass after the always-defer change.
  2. **M1**: revision 2's `register()` pseudocode only caught the `primary=False → primary=True` flip on idempotent re-register (`if primary and self._primaries.get(model) is not type_cls: raise`). The reverse direction — type already stored as primary, re-register called with `primary=False` — silently returned `False` and left the primary in place, contradicting the "primary flag cannot be flipped on re-register" contract. Fix: replace the asymmetric guard with a symmetric `requested != stored` comparison so both directions raise. New regression test pins the `True → False` direction explicitly.
  3. **M2**: revision 2 added new tests but never marked the **existing** tests that pin the *old* behavior as stale. Three test sites depend on contracts this card changes: `tests/test_registry.py` #"test_register_collision_raises" (the original collision-on-second-register test, now superseded), `tests/types/test_base.py::test_registry_collision_raises_configuration_error` (duplicate-`DjangoType` declaration raises), and `tests/types/test_base.py` #"pre-finalize relation annotation" (pre-`finalize_django_types()` eager relation annotations). Fix: each affected slice now carries an explicit "rewrite stale test" checkbox naming the file and line so Worker 2 lands the test update in the same commit as the behavior change. Without it, a worker following only the *added*-tests list could produce a locally-green run while the full suite fails.
  4. **L1**: the "Edge cases" plan-cache bullet said the key includes the resolver return type "not the model", contradicting the H2 contract elsewhere in the spec that adds the origin type *alongside* the model. Fix: rewrite to "origin Strawberry type alongside the model" so the edge case matches Decision 9.
  5. **L2**: one Slice 5 sentence in the Implementation Plan summary still framed the no-op around `DONE-019-0.0.6` specifically, even though the detailed Slice 5 checklist correctly references "any prior `0.0.6` card". Fix: broaden the summary sentence to match.
  6. **L3**: revision 2 said the finalize-time audit "re-runs" on a second `finalize_django_types()` call. Current finalizer code returns early when `registry.is_finalized()` is true, so the audit does **not** re-run. Either contract is defensible (the registry is locked after finalization, so no state can change), but the spec should match the implementation. Fix: state explicitly that the audit runs once, at the first successful finalize, and that subsequent `finalize_django_types()` calls are the existing `is_finalized()`-guarded no-op without re-auditing.
- **Revision 4** (post-feedback-3 review) — two medium clarifications plus four low-severity precision fixes against rev3:
  1. **M1**: rev3 still told Worker 2 to "run [the audit] at the **start** of `finalize_django_types()`". Read literally, that could mean the very top of the function — **above** the existing `if registry.is_finalized(): return` short-circuit. Above the guard the audit re-runs on every call, contradicting the rev3 L3 contract (audit runs once) and silently regressing without a failing test (the audit is side-effect free against a locked registry). Fix: rewrite Slice 3 and Decision 5 to say "after the existing `is_finalized()` short-circuit but before pending-relation resolution". Add a Slice 3 regression test that calls `finalize_django_types()` twice and pins the audit ran only once (e.g., monkey-patched spy on `models_with_multiple_types`).
  2. **M2**: rev3's H2 fix instructed Worker 2 to thread `source_type` into "the walker's first `_resolve_field_map(model)` call", but `optimizer/walker.py` actually has **two** call sites: `django_strawberry_framework/optimizer/walker.py::_walk_selections` (the obvious root path) and `django_strawberry_framework/optimizer/walker.py::_selected_scalar_names` (a sibling helper). If `_selected_scalar_names` is reachable from the root planning path, a secondary-type resolver selecting only scalar fields still plans against the primary's field map. Fix: Slice 4 now names both call sites and instructs Worker 1 to determine during planning which sites are root-path callers and therefore need `source_type`. Add a regression test where a secondary-type resolver selects only scalar fields and the planner uses the secondary's field map.
  3. **L1**: rev3 described today's plan-cache key as "model + selection-set fingerprint" but did not reference the actual implementation. The live tuple at `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._build_cache_key` is `(doc_key: str, relevant_vars: frozenset[tuple[str, Any]], target_model: type, response_path: tuple[str, ...])`. Fix: Decision 9 now quotes the exact four-element tuple shape and the file:line, so Worker 1 knows the surface to extend (likely shape: add `origin: type | None` as a fifth slot).
  4. **L2**: Decision 3's "What disappears" quoted the retired message as `"<existing> is already registered as <existing>"`. The actual format from `django_strawberry_framework/registry.py::TypeRegistry._already_registered` is `"<ModelName> is already registered as <ExistingTypeName>"` — the first slot is the model, the second is the type. Fix: rewrite the quoted template to match the live string.
  5. **L3**: rev3 said the `consumer_authored_fields` short-circuit lives "at the top of `_build_annotations`", implying a function preamble that aborts the whole call. The actual short-circuit is in the per-field loop body — the relations branch and the scalars branch each have their own `continue` — and skips only the current iteration. Functional intent unchanged; description was imprecise. Fix: rewrite the H1 prose to say "the existing `if field.name in consumer_authored_fields: continue` short-circuit in the per-field loop body of `django_strawberry_framework/types/base.py::_build_annotations` (relations branch and scalars branch)".
  6. **L4 / L5**: rev3 referenced `django_strawberry_framework/types/finalizer.py::finalize_django_types` #"target_type = registry.get" for the `target_type = registry.get(...)` assignment; the assignment and the `if target_type is None:` check live inside that function. Fix: pin the symbol-qualified path for every reference rather than chasing a moving line number. Additionally, rev3 named `tests/types/test_finalizer.py` and `tests/types/test_relations.py` as test hosts with a "new or existing" framing, but neither file existed in the tree at spec-authoring time — finalize tests are split across `tests/test_registry.py` (idempotency) and `tests/types/test_definition_order.py` (post-finalize relation resolution); relation tests live in `tests/types/test_converters.py`. Fix: rewrite the test-host bullets to affirmatively name the existing hosts as the default, with "create a new file only if the cluster pushes the existing file past a comfortable size" as the escape hatch.
- **Revision 5** (post-feedback-4 review) — one high-severity correction plus two medium and three low-severity precision fixes:
  1. **H1**: rev4's `Non-goals` and `Out of scope` sections still listed "consumer-side override of relation resolution per field" as deferred to `WIP-ALPHA-015`. That contradicts the live package contract — annotation-only relation overrides (`category: AdminCategoryType`) and assigned-`strawberry.field` relation resolvers already ship today (pinned by `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver`, `tests/types/test_definition_order.py::test_assigned_relation_field_override_keeps_consumer_resolver`, `tests/types/test_definition_order.py::test_assigned_scalar_field_override_keeps_consumer_resolver`, and surfaced in [`docs/GLOSSARY.md` #"Definition-order independence"][glossary-definition-order-independence]). Worse, this card's own Slice 4 H1 regression tests *rely* on consumer overrides surviving and targeting a secondary `DjangoType`. A worker reading the contradictory Non-goal could plausibly weaken the H1 preservation path that the spec elsewhere demands. Fix: rewrite both entries to "no **new override API** ships in this card (no `Meta.field_types = {...}` style key)" and explicitly state the already-shipped direct-annotation / assigned-`strawberry.field` relation override contract remains in scope and may target a secondary type.
  2. **M1**: the verbatim `DONE-018-0.0.6` KANBAN body in Slice 6 still says relation conversion "defers ALL relation annotations to `finalize_django_types()`" — the exact rev2 over-broad wording that rev3 fixed everywhere else. Since the verbatim body becomes the closeout source of truth in `KANBAN.md`, the stale wording would re-surface a contradicted contract. Fix: rewrite the bullet to "defers all auto-synthesized relation annotations" and add the consumer-authored-fields exception clause.
  3. **M2**: rev4 said to "thread the resolved origin Strawberry type" through `optimizer/extension.py` but did not name `_resolve_model_from_return_type()` at `django_strawberry_framework/optimizer/extension.py::_resolve_model_from_return_type` as the helper that currently throws away the origin (it returns `registry.model_for_type(origin)`). Worker 2 can update the walker / cache-key surface and still have no clean way to obtain `origin` at the extension call site. Fix: add an explicit Slice 4 checklist item to change `_resolve_model_from_return_type` to a helper that returns BOTH values — e.g. `(origin, model)` or a small named tuple — and to update the existing tests `tests/optimizer/test_extension.py::test_resolve_model_from_return_type_unwraps_nested_wrappers`, `tests/optimizer/test_extension.py::test_resolve_model_returns_none_for_non_object_leaf`, `tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_no_strawberry_schema`, and `tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_type_not_in_schema` that pin the helper's current `model`-only return shape.
  4. **L1**: rev4's mass-replace flipped every old `finalizer.py` line-number reference. The rev3 reviewer claimed the earlier number was correct; verification against the current tree at the time showed the `target_type = registry.get(pending.related_model)` assignment was actually at the spot below the `continue` in the consumer-authored branch. Fix: revert the affected references. (Subsequently superseded: per the post-TODO-anchor work all references in this spec are now symbol-qualified — `django_strawberry_framework/types/finalizer.py::finalize_django_types` #"target_type = registry.get" — so this historical line-vs-line debate no longer appears anywhere except this revision-history bullet.)
  5. **L2**: the Definition of done still said the Slice 5 version-bump is a "no-op if `DONE-019-0.0.6` already bumped" — the narrow rev2 wording. Rev3 broadened the Slice 5 checklist and the Implementation Plan summary to "any prior `0.0.6` card" but missed the DoD entry. Fix: broaden the DoD wording to match.
  6. **L3 / L4**: rev4's `DjangoTypeDefinition.primary` rationale said the flag is consumed by "the schema audit, the optimizer walker, future override-semantics work". Schema audit and optimizer walker actually route their ambiguity / origin lookups through `registry.primary_for(model)` and the threaded origin type respectively — they never read `definition.primary`. Fix: drop the misleading "schema audit, optimizer walker" claim from the rationale (the flag is still worth storing for introspection / future-work read sites; rationale narrowed accordingly). Additionally, Decision 2 says the idempotent same-type re-registration "matches the existing idempotent-import behavior" — but `TypeRegistry.register()` previously raised in `django_strawberry_framework/registry.py::TypeRegistry.register` #"already_registered" on a same-type second call (because it checked `model in self._types` first). Fix: rephrase to "introduces a new import/retry-tolerant behavior" rather than claiming pre-existing precedent.
- **Revision 6** (post-TODO-anchor review) — two medium clarifications plus two low-severity precision fixes after the maintainer wired `TODO(spec-018-meta_primary-0_0_6.md Slice X)` comments into the package files (visible in the working-tree diff against the current tree):
  1. **M1**: rev4/rev5 framed `_selected_scalar_names` as a possible scalar-only-root path that *might* need `source_type` threading. Audit against the current call graph (`django_strawberry_framework/optimizer/walker.py::_walk_selections`, `django_strawberry_framework/optimizer/walker.py::_plan_select_relation`, `django_strawberry_framework/optimizer/walker.py::_selected_scalar_names`) shows the helper is invoked only from `_plan_select_relation`, where the model argument is `django_field.related_model` for nested FK-id elision — never the resolver's root return type. The root scalar projection actually lives directly in `_walk_selections` after the root `_resolve_field_map(model)` call. Fix: pin the audit decision explicitly in Slice 4 — `_selected_scalar_names` STAYS nested-only with `source_type=None`; the scalar-only secondary regression test pins `_walk_selections` / the root `_resolve_field_map(..., source_type=origin)` path, not `_selected_scalar_names`. (Aligns with the maintainer's TODO inside `django_strawberry_framework/optimizer/walker.py::_selected_scalar_names` which already hints "pure nested FK-id elision paths should keep `source_type=None`".)
  2. **M2**: rev5 told Worker 2 to rewrite all four existing tests `tests/optimizer/test_extension.py::test_resolve_model_from_return_type_unwraps_nested_wrappers`, `tests/optimizer/test_extension.py::test_resolve_model_returns_none_for_non_object_leaf`, `tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_no_strawberry_schema`, `tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_type_not_in_schema` to assert the new `(origin, model)` pair shape. Three of those tests (the failure ones) are **failure cases** that currently assert `None` (non-object leaf, missing Strawberry schema, missing schema type). Asserting `(origin, None)` against those would mean the helper returns a truthy pair on failure, and the caller at `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize` #"if resolved is None" (`if target_model is None: ...`) would dereference into the walker with a `None` model. Fix: pin the helper's failure contract explicitly — return `None` whenever **either** `origin` or `model` is unresolvable; return the pair **only** when both are resolved. Update the stale-test instruction so the success case (`test_resolve_model_from_return_type_unwraps_nested_wrappers`) asserts the pair shape and the three failure cases continue to assert `None`.
  3. **L1**: rev5 said the cache-key `origin` slot is `None` for "nested planning". The current extension's `_plan_cache` is root-only — `_get_or_build_plan` is the only insertion site (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._get_or_build_plan`), and nested plans are constructed inside walker recursion / `_build_prefetch_child_queryset`, **not** through `DjangoOptimizerExtension._build_cache_key`. Worker 2 could mis-read the rev5 wording and either over-engineer a nested extension-cache path or thread a `None` origin through surfaces that do not use the extension cache. Fix: rephrase to "the extension cache key always receives the concrete root origin; nested walker recursion is uncached by `DjangoOptimizerExtension` and keeps `source_type=None` at the walker level. Direct/test-only callers of `_build_cache_key` that deliberately build a plan without an origin may pass `None`."
  4. **L2**: rev5's "no change" bullet for `django_strawberry_framework/optimizer/extension.py::_resolve_model_from_return_type` #"registry.model_for_type(origin)" reads — if Worker 2 follows it literally — as permission to leave `_resolve_model_from_return_type` returning only the model. The intent was to preserve the `registry.model_for_type` *API and lookup semantics*, not the helper's old return shape. Fix: rephrase to "`registry.model_for_type(origin)` remains the model leg inside the expanded origin+model helper; the registry API and lookup semantics are unchanged, but the helper's return shape changes (M2 fix)."

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoType`][glossary-djangotype] — the base class whose one-type-per-model alpha constraint this card lifts.
- [`Meta.primary`][glossary-metaprimary] — the new `Meta` key this card ships. Currently `planned for 0.0.6`; flipped to `shipped (0.0.6)` in [Slice 6](#slice-6--docs-kanban-changelog-archive).
- [`finalize_django_types`][glossary-finalize-django-types] — runs the cross-type ambiguity audit after every subclass has registered.
- [`Relation handling`][glossary-relation-handling] — the resolution path that today binds a relation target to whichever single `DjangoType` happens to be registered for the related model. After this card, the resolution picks the **primary** type.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — its reverse-lookup (`model_for_type`) and schema-audit pass must keep working when a model has multiple registered types.
- [`ConfigurationError`][glossary-configurationerror] — raised at registration time for duplicate-primary collisions and at finalization for unresolved-primary models.
- [Choice enum generation][glossary-choice-enum-generation] — enums are cached by `(model, field_name)`; multiple types reading the same choice column **continue to share one enum** (unchanged from today).

Project conventions to follow:

- [`AGENTS.md`][agents] — schema testing via `schema.execute_sync`. **Note:** `AGENTS.md` prohibits `CHANGELOG.md` edits without explicit permission; [Slice 6](#slice-6--docs-kanban-changelog-archive) grants that permission.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; release-bump checklist.
- [`KANBAN.md`][kanban] — card-ID format; column movement at Slice 6.
- [`docs/TREE.md`][tree] — package layout; tests mirror source one-to-one.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan).

- [ ] Slice 1: Registry multi-type storage + primary tracking
  - [ ] In `django_strawberry_framework/registry.py`, change `_types: dict[type[models.Model], type]` to `_types: dict[type[models.Model], list[type]]` per [Decision 2](#decision-2--registry-data-model). Append-on-register; preserve insertion order; preserve identity-based duplicate-no-op.
  - [ ] Add `_primaries: dict[type[models.Model], type] = {}` for explicit-primary tracking. Single source of truth for which type is primary for each model.
  - [ ] Keep `_models: dict[type, type[models.Model]]` unchanged (reverse lookup is still one-type-to-one-model).
  - [ ] Update `register(model, type_cls, *, primary: bool = False) -> bool` per [Decision 3](#decision-3--register-signature-and-collision-rules). **Return value (new):** `True` if state was added (a new entry appended to `_types[model]` and/or `_primaries[model]` set); `False` if the call was an idempotent no-op (same `type_cls` already in `_types[model]`). Drives the snapshot-rollback path in `register_with_definition` (M1 fix — see Decision 3).
    - First registration for `model`: append; if `primary=True`, set `_primaries[model] = type_cls`. Returns `True`.
    - Subsequent registration for `model` of the *same* `type_cls` (idempotent re-import) **with the same effective `primary` state** (both `False`, or both `True` against the already-stored primary): no-op. Returns `False`.
    - Subsequent registration for `model` of the *same* `type_cls` with a `primary` flag that disagrees with the stored value — in **either direction** (`False`→`True` *or* `True`→`False`): raise `ConfigurationError("<type> is already registered for <model>; primary flag cannot be flipped on re-register")`. (M1 fix.)
    - Subsequent registration for `model` of a *different* `type_cls`: append. If new `primary=True` and `_primaries[model]` already set to a different class: raise `ConfigurationError` (duplicate primary). Otherwise add to list; if `primary=True`, set `_primaries[model] = type_cls`. Returns `True`.
    - Reverse-collision guard (same `type_cls`, different `model`) remains; raise `ConfigurationError` as today.
  - [ ] Update `register_with_definition(model, type_cls, definition, *, primary: bool = False)` to forward the `primary` keyword through. **Rollback (M1 fix):** snapshot `pre_primary = self._primaries.get(model)` before calling `register()`; capture `appended = self.register(model, type_cls, primary=primary)`. If `register_definition` then raises, roll back only what this call added: if `appended` is `True`, remove `type_cls` from `_types[model]` (and pop the model key if the list becomes empty), pop `_models[type_cls]`, and restore `_primaries[model]` to `pre_primary` (popping the key when `pre_primary is None`). If `appended` is `False`, perform no rollback — the existing state was not touched by this call.
  - [ ] Update `get(model) -> type | None` per [Decision 4](#decision-4--registryget-semantics):
    - If `_primaries[model]` set: return it.
    - Else if exactly one type registered for `model`: return that single type.
    - Else (multiple types, no primary): return `None`. This is the "ambiguous; awaiting finalization audit" state.
  - [ ] Add `primary_for(model) -> type | None` — returns `_primaries.get(model)` directly. Distinct from `get()` so callers can tell the difference between "single registered type with no primary flag" and "explicitly declared primary".
  - [ ] Add `types_for(model) -> tuple[type, ...]` — returns the immutable tuple of every type registered against `model` in registration order. Used by [`audit_primary_ambiguity`](#decision-5--ambiguity-rules) and by future tests / introspection.
  - [ ] Add `models_with_multiple_types() -> Iterator[type[models.Model]]` — yields each model with `>=2` registered types. Used by `audit_primary_ambiguity` (Slice 3) to enumerate the ambiguity-candidate set without exposing `_types` to the finalizer.
  - [ ] Add `iter_types()` shape note: now yields `(model, type_cls)` pairs **once per registered type**, so the same `model` can appear in the iterator multiple times. [Schema audit][glossary-schema-audit] (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.check_schema`) continues to use this iterator (with warning-collection dedupe — see Slice 4 H3 fix).
  - [ ] Update `clear()` to also clear `_primaries`.
  - [ ] Tests in `tests/test_registry.py`:
    - [ ] **Rewrite stale test** (M2): `tests/test_registry.py` #"test_register_collision_raises" — the legacy `test_register_collision_raises` test (now superseded by `test_register_same_class_against_two_models_raises`) expected a second `register(Model, T2)` call to raise `ConfigurationError(match="already registered")`. Under this card the second call must *not* raise (no-primary multi-type case). Rewrite the test in the same commit as the registry change: either rename to `test_register_two_primaries_raises` and switch both calls to `primary=True`, or delete and let `test_register_two_types_same_model_without_primary_allows_both_in_types_for` cover the inverse contract. Worker 1 picks during planning.
    - [ ] `test_register_two_types_same_model_without_primary_allows_both_in_types_for` — verifies multi-storage works; `types_for(Model)` returns both in registration order.
    - [ ] `test_register_second_type_for_same_model_no_longer_raises_collision` — verifies the old `_already_registered("as", ...)` path is gone for the no-primary case (the message is recycled with new framing — see Decision 3).
    - [ ] `test_register_same_type_twice_is_idempotent` — calling `register(Model, T)` twice does not duplicate the entry in `_types[Model]`.
    - [ ] `test_register_primary_flag_sets_primary_for` — single type with `primary=True` populates `_primaries`.
    - [ ] `test_register_two_primaries_for_same_model_raises_configuration_error` — second `register(Model, T2, primary=True)` after `register(Model, T1, primary=True)` raises with message containing `"already declared primary"`.
    - [ ] `test_register_same_type_re_register_with_flipped_primary_false_raises` (M1 regression) — register `(Model, T, primary=True)`, then call `register(Model, T, primary=False)`. Assert the second call raises `ConfigurationError` containing `"primary flag cannot be flipped"`. Pins the `True → False` direction of the symmetric flip guard.
    - [ ] `test_register_same_type_re_register_with_flipped_primary_true_raises` — register `(Model, T)` (or `primary=False`), then call `register(Model, T, primary=True)`. Assert `ConfigurationError`. Pins the `False → True` direction.
    - [ ] `test_register_with_definition_rollback_clears_primary` — when `register_definition` raises mid-`register_with_definition` for a *new* type, the `_primaries` entry is also rolled back to its pre-call state (snapshot-restore, not unconditional pop).
    - [ ] `test_register_with_definition_idempotent_re_register_does_not_corrupt_state` — M1 regression: pre-register `(Item, ItemType, def1)`. Call `register_with_definition(Item, ItemType, def2)` where `def2 is not def1`. Assert: (a) the second call raises `ConfigurationError` from `register_definition` (re-register collision); (b) `registry.types_for(Item) == (ItemType,)` (the original registration is intact); (c) `registry.model_for_type(ItemType) is Item`; (d) `registry.get_definition(ItemType) is def1` (the original definition is preserved); (e) if `def1` had registered as primary, `registry.primary_for(Item) is ItemType` post-failure.
    - [ ] `test_register_returns_true_for_new_state` — `register(Item, ItemType)` returns `True` on first call.
    - [ ] `test_register_returns_false_for_idempotent_re_register` — second `register(Item, ItemType)` returns `False`; no state was added.
    - [ ] `test_get_returns_single_type_when_one_registered_no_primary` — backward-compat: `get(Model)` returns the lone type even without `primary=True`.
    - [ ] `test_get_returns_primary_when_multiple_and_primary_declared`.
    - [ ] `test_get_returns_none_when_multiple_and_no_primary` — distinguishes the ambiguous-pending state.
    - [ ] `test_primary_for_returns_none_when_only_implicit_single_type` — `primary_for(Model)` is strictly the `_primaries` lookup; the "single type implicitly the primary" convenience lives only on `get()`.
    - [ ] `test_types_for_preserves_registration_order`.
    - [ ] `test_iter_types_yields_each_type_once_when_multiple_registered_for_same_model`.
    - [ ] `test_register_same_type_against_two_models_still_raises` — reverse-collision unchanged.
    - [ ] `test_clear_resets_primaries`.
- [ ] Slice 2: `Meta.primary` recognition in `DjangoType.__init_subclass__`
  - [ ] In `django_strawberry_framework/types/base.py`, add `"primary"` to `ALLOWED_META_KEYS`.
  - [ ] Extend `_validate_meta` per [Decision 1](#decision-1--metaprimary-shape-and-validation): if `Meta.primary` is declared, it must be a `bool`; otherwise raise `ConfigurationError("Meta.primary must be a bool")`. Default is `False` when absent.
  - [ ] Read `primary = getattr(meta, "primary", False)` in `__init_subclass__` and pass it through `registry.register_with_definition(..., primary=primary)`.
  - [ ] Add `primary: bool = False` field to `django_strawberry_framework/types/definition.py:DjangoTypeDefinition`. Populated from the `Meta.primary` read above. Stored on the dataclass for introspection and future-work read sites (L3 fix: the schema audit and optimizer walker route through `registry.primary_for(model)` and the threaded origin type respectively — they do NOT consume `definition.primary`; the single source of truth for "which type is primary for which model" remains `registry._primaries`, accessed via the `primary_for(model)` helper).
  - [ ] Tests in `tests/types/test_base.py` (or `tests/test_registry.py` if more naturally placed there — see test placement note in [Decision 7](#decision-7--test-strategy)):
    - [ ] **Rewrite stale test** (M2): `tests/types/test_base.py::test_registry_collision_raises_configuration_error` — the existing duplicate-`DjangoType`-raises test pins the *old* one-type-per-model behavior at the class-creation layer (mirrors `tests/test_registry.py` #"test_register_collision_raises" but exercises the `__init_subclass__` path). Rewrite to either (a) keep the assertion shape but make both subclasses `Meta.primary = True` so the duplicate-primary error fires, or (b) replace with the new two-types-one-primary success case. Worker 1 picks during planning; the new tests below cover the success path, so option (a) is the lower-touch choice.
    - [ ] `test_meta_primary_true_registers_type_as_primary` — declares one `DjangoType` with `Meta.primary = True`; asserts `registry.primary_for(Model) is TheType`.
    - [ ] `test_meta_primary_false_does_not_register_primary` — declares with `Meta.primary = False` explicitly; asserts `registry.primary_for(Model) is None`.
    - [ ] `test_meta_primary_absent_does_not_register_primary` — no `Meta.primary` key; asserts `registry.primary_for(Model) is None`.
    - [ ] `test_meta_primary_non_bool_raises_configuration_error` — `Meta.primary = "yes"` raises with message containing `"must be a bool"`.
    - [ ] `test_meta_primary_propagates_to_definition` — `registry.get_definition(TheType).primary is True`.
    - [ ] `test_two_types_same_model_one_primary_both_register_successfully` — declares `ItemType` and `AdminItemType(Meta.primary=True)` on `Item`; asserts no error, `types_for(Item) == (ItemType, AdminItemType)`, `primary_for(Item) is AdminItemType`.
    - [ ] `test_two_primary_types_same_model_raises` — declares two `DjangoType` subclasses on `Item`, both with `Meta.primary = True`; the second declaration raises `ConfigurationError` with message containing `"already declared primary"`.
- [ ] Slice 3: Cross-type ambiguity audit at finalization
  - [ ] Add `audit_primary_ambiguity()` in `django_strawberry_framework/types/finalizer.py` per [Decision 5](#decision-5--ambiguity-rules):
    - Iterate `registry.models_with_multiple_types()` (the helper landed in Slice 1). For each model, if `registry.primary_for(model) is None`: collect into the offenders list along with `registry.types_for(model)`.
    - If the offenders list is non-empty, raise `ConfigurationError` listing every offending model name and every registered class name, with the fix sentence: `"Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."`.
    - **Placement (M1 fix):** run inside `finalize_django_types()` **after the existing `if registry.is_finalized(): return` short-circuit** but **before** pending-relation resolution. Concretely: the audit is the first work the function does on a non-finalized registry. Placing it above the `is_finalized()` guard would make the audit re-run on every `finalize_django_types()` call, contradicting the [`finalize_django_types` idempotency](#edge-cases-and-constraints) contract. The post-guard placement gives: (a) the ambiguity error fires before the existing unresolved-target error so consumers see the root cause; (b) the pending-relation resolution path can rely on `registry.get(model)` returning the primary (or the single registered type) without re-checking for ambiguity; (c) the audit runs exactly once per build, on the first successful finalize.
  - [ ] Tests in `tests/test_registry.py` (idempotency / finalization cluster) and/or `tests/types/test_definition_order.py` (post-finalize relation resolution) — both are the existing finalize-test hosts (L5 fix; no `tests/types/test_finalizer.py` exists today). Worker 1 chooses the file with the closer thematic fit per test during planning. Create a new `tests/types/test_finalizer.py` only if the audit-test cluster grows past comfortable size in the existing hosts:
    - [ ] `test_finalize_raises_when_model_has_multiple_types_no_primary` — declares two `DjangoType` subclasses on `Item`, neither primary; `finalize_django_types()` raises `ConfigurationError` with message containing the model name and both class names.
    - [ ] `test_finalize_succeeds_when_model_has_multiple_types_one_primary` — declares two `DjangoType` subclasses, one primary; finalize succeeds.
    - [ ] `test_finalize_succeeds_when_model_has_single_type_no_primary` — backward-compat path.
    - [ ] `test_finalize_ambiguity_error_message_contains_actionable_fix` — assertion on the `"Declare Meta.primary = True"` substring.
    - [ ] `test_finalize_ambiguity_error_fires_before_unresolved_target_error` — set up both conditions; assert the ambiguity error is the one raised.
    - [ ] `test_audit_runs_once_per_build` (M1 regression) — monkey-patch `registry.models_with_multiple_types` to a spy (counting wrapper). Call `finalize_django_types()` once (success path; no offenders). Call `finalize_django_types()` a second time. Assert the spy was invoked exactly once. Pins that the audit sits *below* the `is_finalized()` guard. Without the post-guard placement, the spy would be invoked twice and the test would catch the regression even though no `ConfigurationError` is raised.
- [ ] Slice 4: Consumer-site updates (relation conversion + optimizer)
  - [ ] **`django_strawberry_framework/types/base.py::_build_annotations`** relation resolution (H1 fix). Replace the eager-bind-or-defer branch with **always-defer for auto-synthesized relations**: every relation field whose annotation the package generates is recorded as `PendingRelationAnnotation` and added to the registry's pending list during `__init_subclass__`. The pre-existing `if field.name in consumer_authored_fields: continue` short-circuit early in the per-field loop body of `_build_annotations` (relations branch and scalars branch) STAYS — consumer-authored relation fields (annotation overrides like `category: CategoryType` and assigned `strawberry.field` resolvers) continue to skip synthesis entirely, so a consumer-owned `StrawberryField` is never overwritten with a `PendingRelationAnnotation`. The eager path for auto-synthesized fields was unsafe under multi-type semantics — a single secondary registered before the relation source would freeze the relation against the secondary even when the primary registered later. Always-defer removes that import-order trap and centralizes auto-synthesized relation resolution in `finalize_django_types()`. Net post-finalize behavior is identical for the existing single-type case; the only observable difference is that `target_type` is `None`-and-pending during the `__init_subclass__` window instead of resolved-immediately when the target happened to be declared first.
  - [ ] **`django_strawberry_framework/types/finalizer.py::finalize_django_types` #"target_type = registry.get"** pending-relation resolution. Still calls `registry.get(pending.related_model)`. Per Slice 3, the ambiguity audit runs first; by the time this line executes, `get()` returns the primary (or the single registered type) or `None` for "no type registered at all" (the unchanged "unresolved target" case). No code change required; behavior follows from Slice 1's `get()` and Slice 3's audit.
  - [ ] **`django_strawberry_framework/types/converters.py::resolved_relation_annotation`** (the relation-annotation builder; was historically referenced as `convert_relation`). Same call shape; same reasoning. No change.
  - [ ] **`django_strawberry_framework/optimizer/walker.py::_resolve_field_map`** (H2 fix). Add a keyword-only `source_type: type | None = None` parameter. When `source_type` is provided (the root call from `plan_optimizations`), use it as `type_cls` directly — do **not** call `registry.get(model)`. When `source_type` is `None` (recursive nested calls), keep the current `registry.get(model)` behavior; that path resolves nested relation targets to the primary, which is the spec's intended contract for nested relations.
  - [ ] **`django_strawberry_framework/optimizer/walker.py::_resolve_field_map` call-site decision (rev6 M1 audit, pinned).** `optimizer/walker.py` has two callers: `django_strawberry_framework/optimizer/walker.py::_walk_selections` (the root path from `plan_optimizations`) and `django_strawberry_framework/optimizer/walker.py::_selected_scalar_names` (called only from `_plan_select_relation` for nested FK-id elision; the model argument is `django_field.related_model`, never the resolver's root return type). **The post-audit decision is pinned in this spec:** `_walk_selections` receives `source_type=origin` when invoked from `plan_optimizations` (root path); `_selected_scalar_names` STAYS unchanged — it continues to call `_resolve_field_map(model)` with no `source_type`, which routes through `registry.get(model)` and correctly returns the primary for the nested target. Worker 2 should NOT add `source_type` plumbing to `_selected_scalar_names`. (Matches the maintainer's TODO inside `django_strawberry_framework/optimizer/walker.py::_selected_scalar_names`, which says "pure nested FK-id elision paths should keep `source_type=None`".)
  - [ ] **`django_strawberry_framework/optimizer/walker.py::_walk_selections` #"registry.get(django_field.related_model)"** nested `target_type = registry.get(django_field.related_model)` lookup. Unchanged. Nested relation targets resolve to the primary by design (this is the contract that drove the spec).
  - [ ] **`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize` root planning path** (H2 fix). Where `plan_optimizations` is invoked from the extension hook, thread the resolved origin Strawberry type through to the walker's first call (the one that becomes the root `_resolve_field_map(model, source_type=origin)`). Worker 1 pins the exact call shape during planning (`plan_optimizations` may need a new keyword-only `source_type=` argument, or `_walk_selections` may need it threaded one level deeper — the spec contract is "the root field-map/hints lookup uses the resolver's actual return type"; the call-graph detail is an implementation choice).
  - [ ] **`django_strawberry_framework/optimizer/extension.py::_resolve_model_from_return_type`** (M2 fix). Today the helper resolves a resolver's Strawberry return type to the underlying model and returns the model only — the origin is computed locally and discarded via `registry.model_for_type(origin)`. The H2 contract needs the origin alongside the model at the extension call site (to feed `plan_optimizations` and the plan-cache key). Rewrite the helper to return BOTH values — Worker 1 picks the shape during planning (named tuple `Origin(origin, model)` or a plain `(origin, model)` tuple; the spec contract is "callers can read both without re-resolving"). **Failure contract (rev6 M2):** the helper returns `None` whenever **either** `origin` OR `model` is unresolvable (non-object leaf type, missing Strawberry schema, missing schema type, unregistered origin). It returns the pair **only** when both are resolved. The `if target_model is None: return` guard inside `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize` therefore becomes `if resolved is None: return` (or equivalent on whichever name the unpacked variable holds), preserving the existing skip-when-unresolvable pass-through.
  - [ ] **Rewrite stale tests** (M2): split by case.
    - `tests/optimizer/test_extension.py::test_resolve_model_from_return_type_unwraps_nested_wrappers` is the **success case**. Rewrite to assert the new `(origin, model)`-or-named-tuple shape; preserve the underlying model assertion as the second element and add an assertion on the first element (the resolved Strawberry origin type).
    - `tests/optimizer/test_extension.py::test_resolve_model_returns_none_for_non_object_leaf`, `tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_no_strawberry_schema`, `tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_type_not_in_schema` are **failure cases** (non-object leaf, missing schema, missing schema type) that currently assert `None`. **Keep them asserting `None`** — the failure contract above returns `None` outright; do not rewrite these to expect `(origin, None)` or any other pair shape.
    - Land all four rewrites in the same commit as the helper change.
  - [ ] **Plan cache key** (H2 fix). The live cache key is the four-element tuple `(doc_key, relevant_vars, target_model, response_path)` at `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._build_cache_key`. Extend it to include the origin Strawberry type — recommended position: a fifth slot `origin: type | None` (see [Decision 9](#decision-9--optimizer-origin-type-propagation-h2-fix) for rationale). **Scope (rev6 L1):** `DjangoOptimizerExtension._plan_cache` is root-only — `_get_or_build_plan` is the sole insertion site. Nested plans built inside walker recursion / `_build_prefetch_child_queryset` are NOT inserted through `_build_cache_key`, so the new `origin` slot always receives the concrete root origin type. The `None` value of the slot is reserved for direct/test-only callers of `_build_cache_key` that deliberately build a plan without an origin. Do NOT introduce a nested extension-cache path or thread `None` origins through walker recursion. After the change, a primary-type root resolver and a secondary-type root resolver for the same model produce distinct cache entries.
  - [ ] **`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.check_schema`** schema audit (H3 fix). Keep iterating every reachable registered type via `registry.iter_types()` (do not switch to a "primary only" helper — that would silently skip relation fields exposed only on a reachable secondary type). To avoid duplicate warnings when the same `(source_model, field_name)` is visited via multiple registered types, dedupe warning collection: use a `set[str]` for the warning sink (or a `set[tuple[type[models.Model], str]]` key + a string-builder pass at the end). Document the dedupe rationale in a one-line comment so future readers understand it is a multi-type artifact, not a generic defensiveness.
  - [ ] **`django_strawberry_framework/optimizer/extension.py::_collect_schema_reachable_types` #"registry.get_definition(origin)"** `registry.get_definition(origin)` — works unchanged for any registered type (primary or secondary). No change.
  - [ ] **`django_strawberry_framework/optimizer/extension.py::_resolve_model_from_return_type` #"registry.model_for_type(origin)"** `registry.model_for_type(origin)` — the **registry API and lookup semantics are unchanged**. `model_for_type` continues to return the correct model for any registered type (primary or secondary). The helper that calls it (`_resolve_model_from_return_type`) DOES change: it now returns both `origin` and `model` instead of discarding the origin — see the dedicated `_resolve_model_from_return_type` checklist item above. (Rev6 L2 clarification: do NOT read this bullet as permission to leave the wrapper helper returning only the model.)
  - [ ] **Rewrite stale tests** (M2): the four pre-finalize relation-annotation assertions in `tests/types/test_base.py` #"pre-finalize relation annotation" (verify against current tree before editing) currently assert eager relation annotations are present **before** `finalize_django_types()` runs (they read `cls.__annotations__[field_name]` and expect the resolved type, not `PendingRelationAnnotation`). Under the always-defer (auto-synthesized) change, those pre-finalize annotations are `PendingRelationAnnotation` until finalize. The same staleness affects two sibling assertions in `tests/types/test_definition_order.py::test_reverse_fk_resolves_when_parent_declared_before_child` and `tests/types/test_definition_order.py::test_reverse_fk_resolves_when_child_declared_before_parent` — also rewrite in the same commit. Rewrite each pre-finalize assertion to one of: (a) post-finalize assertion after calling `finalize_django_types()` first, (b) assertion that the annotation is `PendingRelationAnnotation` pre-finalize (if the test's *intent* was to pin the pending state), or (c) delete if the test is now covered by the new auto-deferred regression tests below. Worker 1 reads each site during planning and picks the smallest-touch option per test. Land the rewrites in the same commit as the `_build_annotations` change.
  - [ ] Tests in `tests/types/test_converters.py` (the existing relation-conversion host — currently ~1455 lines; no `tests/types/test_relations.py` exists today — L5 fix). Create a new `tests/types/test_relations.py` only if `test_converters.py` would otherwise grow past a comfortable size:
    - [ ] `test_consumer_authored_relation_annotation_override_survives_always_defer` (H1 regression) — declare `CategoryType` with `items: list["AdminItemType"]` annotation (consumer-authored), plus `AdminItemType` on `Item` *without* `primary=True`, plus `ItemType(primary=True)` on `Item`. Finalize. Assert `CategoryType.items` resolves to `AdminItemType` (the consumer's explicit annotation), not `ItemType` (the primary). Pins that the `consumer_authored_fields` short-circuit still wins over the primary-resolution path. Mirrors `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver` and `tests/types/test_definition_order.py::test_assigned_relation_field_override_keeps_consumer_resolver`.
    - [ ] `test_consumer_assigned_strawberry_field_relation_survives_always_defer` (H1 regression) — declare `CategoryType` with `items = strawberry.field(...)` (assigned, not annotated), targeting `AdminItemType`. Multi-type `Item` setup as above. Assert the assigned `StrawberryField` is preserved through `__init_subclass__` and `finalize_django_types()` — no `PendingRelationAnnotation` replaces it.
    - [ ] `test_relation_resolves_to_primary_type_when_target_model_has_multiple` — declares `ItemType(primary=True)` and `AdminItemType` on `Item`; declares `CategoryType` with an `items` reverse relation; finalizes; introspects the schema and asserts the `items` field's GraphQL type is `ItemType` (not `AdminItemType`).
    - [ ] `test_relation_resolves_to_primary_when_secondary_registered_before_source_before_primary` (H1 regression) — declares `AdminItemType` on `Item` *without* `Meta.primary`; declares `CategoryType` referencing the `items` reverse relation; declares `ItemType(Meta.primary=True)` on `Item` *after* the source; finalizes; introspects the schema and asserts `CategoryType.items` resolves to `ItemType`. Pins the always-defer contract; without it, the eager-bind path would have frozen `items` to `AdminItemType`.
    - [ ] `test_relation_resolves_when_target_model_has_one_type_no_primary` — backward compat: a relation still binds to the lone type when no `primary` flag is set (resolved at finalize via `registry.get()` returning the single type).
    - [ ] `test_relation_target_with_multiple_no_primary_surfaces_audit_error_at_finalize` — declares `CategoryType` with `items` relation to `Item`, plus two `Item` types neither primary. Asserts `finalize_django_types()` raises the audit error (not the unresolved-target error).
  - [ ] Tests in `tests/optimizer/test_walker.py` and `tests/optimizer/test_extension.py`:
    - [ ] `test_optimizer_walker_plans_root_from_resolver_return_type_when_secondary` (H2 regression) — multi-type `Item` with `ItemType(primary=True)` and `AdminItemType`. Build a schema where the root field returns `list[AdminItemType]`. `AdminItemType.field_map` includes a field or `optimizer_hints` entry not present on `ItemType` (e.g., a `prefetch_related` hint on a relation field exposed only on `AdminItemType`). Execute the query and assert the optimizer plan reflects `AdminItemType`'s hints (not `ItemType`'s). Pins the "use the resolver's actual return type for the root field-map" contract.
    - [ ] `test_scalar_only_secondary_resolver_uses_secondary_field_map` (rev6 M1 regression) — multi-type `Item`; build a schema where the root field returns `list[AdminItemType]` and the query selects **only scalar fields** that exist on `AdminItemType` but are absent from `ItemType` (e.g., `internal_notes`). Execute and assert the planner used `AdminItemType.field_map` for the scalar projection (the `.only(...)` list contains the secondary's scalar column). Pins that the **root** `_walk_selections` / `_resolve_field_map(..., source_type=origin)` path resolves to the secondary's field map — without the H2 threading, the root `_resolve_field_map(model)` would call `registry.get(model)` and plan against the primary's scalar set, dropping the secondary-only column. Note: this regression does NOT exercise `_selected_scalar_names`; that helper is nested-only and stays on the primary (rev6 M1).
    - [ ] `test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model` (H2 regression) — multi-type `Item`; build two schemas (or two root fields on one schema) — one returning `list[ItemType]` and one returning `list[AdminItemType]`. Trigger planning for both. Assert the plan cache holds two distinct entries keyed by origin type (not one shared entry keyed by model alone).
    - [ ] `test_optimizer_walker_uses_primary_for_nested_relation_target` — multi-type `Item` reached via a nested relation field on `CategoryType.items`. Assert the walker plans the nested step against `ItemType.field_map` (the primary), confirming the nested-path contract is unchanged.
    - [ ] `test_schema_audit_warns_on_relation_field_exposed_only_on_secondary_type` (H3 regression) — declare `ItemType(primary=True)` exposing only scalar fields, and `AdminItemType` exposing a `category` relation whose target model has no registered `DjangoType`. Assert the audit produces a `"Item.category has no registered target DjangoType"` warning. Without the H3 fix, switching to a "primary only" iteration would have silently skipped the secondary type's `category` field.
    - [ ] `test_schema_audit_dedupes_when_same_relation_field_visited_via_multiple_types` (H3 regression) — declare `ItemType(primary=True)` and `AdminItemType` on `Item`, both selecting `category` (a relation whose target has no registered `DjangoType`). Assert exactly one warning is produced for `Item.category` (not two — one per reachable type). Pins the dedupe contract.
    - [ ] `test_model_for_type_reverse_lookup_works_for_secondary_type` — `registry.model_for_type(AdminItemType) is Item`. Secondary types remain discoverable for the optimizer when a resolver returns an `AdminItemType` directly.
- [ ] Slice 5: Atomic version-bump quintet (single commit). Same shape as `spec-017-deferred_scalars-0_0_6.md` Slice 5: covers programmatically-checked sites only (`pyproject.toml`, `__init__.py`, `tests/base/test_init.py`'s pinned `__version__`, `docs/GLOSSARY.md`'s "Current package version" line, `uv.lock`). The two consumer-facing version strings (`README.md`, `docs/README.md`) move in Slice 6. **At spec-authoring time the tree is already at `0.0.6` from `spec-017-deferred_scalars-0_0_6.md`'s Slice 5**, so every checkbox below is expected to be a no-op. The slice still exists in the plan so the build cycle's Worker 1 final-verification pass explicitly `grep`s for stale `0.0.5` strings before marking complete — if a future spec change inadvertently regressed the version, this slice catches it.
  - [ ] `pyproject.toml` — `version = "0.0.6"` (no-op if already at `0.0.6` from any prior `0.0.6` card).
  - [ ] `django_strawberry_framework/__init__.py` — `__version__ = "0.0.6"` (no-op if already bumped).
  - [ ] `tests/base/test_init.py` — pinned `__version__` assertion to `"0.0.6"` (no-op if already bumped).
  - [ ] `docs/GLOSSARY.md` — "Current package version: `0.0.6`" line (no-op if already bumped).
  - [ ] `uv.lock` — re-lock with `uv lock` (no-op if already at `0.0.6`).
  - [ ] **Prior-`0.0.6`-card note.** `0.0.6` carries multiple cards (`spec-013-deferred_scalars`, this card, `DONE-019-0.0.6`). The first card to land does the real bump; every subsequent card's Slice 5 is a no-op. The Worker 1 final-verification pass MUST `grep` for stale `0.0.5` strings rather than blindly editing — if the bump has already happened, mark every checkbox above complete without re-editing.
- [ ] Slice 6: Docs, KANBAN, CHANGELOG, archive (separate commit; may follow Slice 5 by any interval). **Size note:** this is the largest commit of the six. Consider opening as a draft PR via `gh pr create --draft` for staged review before merge.
  - [ ] Root `README.md` — confirm the package-version line reads `0.0.6` (no-op if any prior `0.0.6` card already bumped it).
  - [ ] `docs/README.md` — confirm the "shipped today is `0.0.6`" line (no-op if any prior `0.0.6` card already bumped it). Add a one-line mention of `Meta.primary` to the shipped-capability summary.
  - [ ] `docs/GLOSSARY.md` entries updated:
    - [`Meta.primary`][glossary-metaprimary] → `shipped (0.0.6)`. Rewrite the body to describe the actual delivered contract (ambiguity rules; `primary_for` / `types_for` registry surface; relation-target resolution semantics). Drop the "planned for `0.0.6`" framing.
    - [`DjangoType`][glossary-djangotype] → remove the "one `DjangoType` per Django model" alpha constraint bullet (currently inside [`docs/GLOSSARY.md` #"DjangoType"][glossary-djangotype] under "Current alpha constraints"). Replace with a one-line "multiple `DjangoType`s per model supported via [`Meta.primary`](#metaprimary)" entry under the shipped-capability list.
    - [Index][glossary-index] → flip the status badge on `Meta.primary` to `shipped (0.0.6)`.
  - [ ] `docs/TREE.md` — no source-tree changes (no new files); add `Meta.primary` to the `[alpha]` milestone tag for `DjangoType` if relevant; otherwise no-op.
  - [ ] `TODAY.md` — add `Meta.primary` to the "what fakeshop demonstrates today" section if the example project exercises it; otherwise mention it under "available but not currently demonstrated in fakeshop".
  - [ ] `KANBAN.md` — move `DONE-018-0.0.6` → `DONE-018-0.0.6`. **Drop in the verbatim body below:**

    ```markdown
    ### DONE-018-0.0.6 — Multiple DjangoTypes per model with `Meta.primary`

    Slice-by-slice scope (per `docs/spec-018-meta_primary-0_0_6.md`):

    - Registry stores multiple types per model (`_types: dict[Model, list[Type]]`).
    - New `Meta.primary: bool` flag (default `False`); validated in `_validate_meta`.
    - `registry.register(..., *, primary: bool = False) -> bool` and
      `registry.register_with_definition(..., *, primary=...)` accept the flag.
      `register()` now returns `bool` indicating whether state was added; drives
      snapshot-restore rollback in `register_with_definition`.
    - New registry surface: `primary_for(model)`, `types_for(model)`,
      `models_with_multiple_types()`.
    - `registry.get(model)` returns the primary if declared, else the single
      registered type, else `None`. Multiple types with no primary is an
      ambiguous-pending state that the finalizer audits.
    - `finalize_django_types()` runs `audit_primary_ambiguity()` first: any
      model with `>=2` registered types and no primary raises
      `ConfigurationError` naming the model and every registered class plus an
      actionable fix sentence.
    - Two primary types for the same model: rejected at registration time
      with message `"<class> is already declared primary as <existing>"`.
    - Relation conversion in `types/base.py` defers all **auto-synthesized**
      relation annotations to `finalize_django_types()` (eager-bind shortcut
      removed; eliminates the secondary-registered-before-source-before-
      primary import-order trap). The existing `consumer_authored_fields`
      short-circuit is preserved, so direct relation annotations (`category:
      AdminCategoryType`) and assigned `strawberry.field` resolvers continue
      to bypass synthesis entirely and may target a secondary `DjangoType`.
      `types/converters.py` and `types/finalizer.py` resolve auto-synthesized
      relations to the primary at finalize time.
    - Optimizer planning threads the resolved origin Strawberry type from
      `optimizer/extension.py` through `plan_optimizations` to the walker's
      root `_resolve_field_map(model, source_type=origin)` call. Root planning
      uses the resolver's actual return type; nested relation steps continue
      to use `registry.get(related_model)` (the primary). Plan cache key
      includes the origin type so primary-return and secondary-return
      resolvers on the same model do not share a cached plan.
    - Schema audit (`optimizer/extension.py`) iterates every reachable
      registered type via `registry.iter_types()` and dedupes warning
      collection. Secondary types whose relation fields the primary does not
      expose are still audited; identical-string duplicate warnings from
      overlapping field maps are collapsed.
    - `model_for_type` continues to work for any registered type so
      secondary-type resolvers stay planable.
    - `DjangoTypeDefinition` gains `primary: bool = False`.
    - 100% coverage across `tests/test_registry.py`, `tests/types/test_base.py`,
      `tests/test_registry.py` / `tests/types/test_definition_order.py`
      (the existing finalize-test hosts), `tests/types/test_converters.py`
      (the existing relation-conversion host), and `tests/optimizer/`.

    Design notes carried into `0.0.6`:

    - Single-type-no-primary stays backward compatible: `registry.get(model)`
      still returns the lone type without requiring an explicit `primary` flag.
    - `Meta.primary` is a per-class declaration, not a registry-level
      `set_primary(Model, Type)` mutation — keeps the contract immutable
      after `__init_subclass__` runs.
    - Already-shipped consumer relation overrides (direct annotation
      `category: AdminItemType` and assigned `category = strawberry.field(...)`)
      stay in scope and are preserved by this card via the existing
      `consumer_authored_fields` short-circuit — they may legitimately
      target a secondary `DjangoType` after `Meta.primary` ships. A NEW
      declarative override API (e.g., `Meta.field_types = {...}`) is the
      `DONE-019-0.0.6 — Consumer override semantics` design space and
      is out of scope here.
    ```
  - [ ] `CHANGELOG.md` — `[Unreleased]` entries (**permission granted by this spec**, overriding [`AGENTS.md`][agents]'s default prohibition):
    - `Added`: `Meta.primary` boolean flag. Multiple `DjangoType` subclasses per Django model. Registry surface: `primary_for`, `types_for`, `models_with_multiple_types`.
    - `Changed`: `registry.register` now returns `bool` (whether state was added; was `None`). `registry.register` and `registry.register_with_definition` gained a keyword-only `primary: bool = False` parameter. `registry.get(model)` semantics: returns the primary if declared; the single type if only one is registered; `None` if multiple types are registered with no primary.
    - `Changed`: `registry.iter_types()` now yields once per registered type — a model with multiple types appears multiple times. Consumers iterating to drive a per-model action should explicitly dedupe by model, or use `models_with_multiple_types()` + `types_for(model)` for an explicit grouping.
    - `Changed`: `_build_annotations` (`types/base.py`) always defers **auto-synthesized** relation annotations to `PendingRelationAnnotation` + the registry's pending list; the eager-bind shortcut is removed. Consumer-authored relation fields (annotation overrides and assigned `strawberry.field`) continue to skip synthesis entirely — the existing `if field.name in consumer_authored_fields: continue` short-circuit is preserved.
    - `Changed`: optimizer plan cache key includes the resolver's origin Strawberry type alongside the model. Primary-return and secondary-return resolvers on the same model produce distinct cache entries.
  - [ ] **Before archiving**, the spec stays at its working location per [`docs/builder/BUILD.md`][build] "Specs stay at their working location after closeout". Opt-in archival to `docs/SPECS/` is the maintainer's call; the [Definition of done](#definition-of-done) does not gate on it.

## Problem statement

[`docs/GLOSSARY.md`'s `DjangoType` entry][glossary-djangotype] calls out an alpha constraint: "one `DjangoType` per Django model". The registry enforces it at `register()` time in `django_strawberry_framework/registry.py::TypeRegistry.register` #"already_registered" by raising `ConfigurationError` whenever a second type registers against an already-mapped model.

DRF-style usage (the package's stated target audience) commonly defines public, admin, list, and detail variants of the same model. Today, declaring `class AdminItemType(DjangoType): class Meta: model = Item` after `ItemType` already exists for `Item` raises at import time. There is no current escape hatch — consumers either fork the model into a proxy or restructure the schema around the limitation, neither of which composes with the rest of the type-conversion machinery.

The card mandates an explicit primary-declaration contract: multiple types per model are allowed when ambiguity is resolved by `Meta.primary = True` on exactly one of them. Relation conversion, schema audit, and the optimizer's reverse-lookup all need a deterministic answer to "which type backs this model" — without `Meta.primary`, the answer is import-order-dependent, which is the package's existing un-stated behavior and exactly the contract the card upgrades to explicit.

## Current state

`TypeRegistry` (`django_strawberry_framework/registry.py::TypeRegistry`) stores four maps:

- `_types: dict[type[models.Model], type]` — forward map. **One-to-one.**
- `_models: dict[type, type[models.Model]]` — reverse map. One-to-one.
- `_enums: dict[tuple[type[models.Model], str], type[Enum]]` — choice-enum cache.
- `_definitions: dict[type, DjangoTypeDefinition]` — collected metadata per type.

`register(model, type_cls)` raises `ConfigurationError` with message `"<model_name> is already registered as <existing_type_name>"` whenever `model in self._types` (`django_strawberry_framework/registry.py::TypeRegistry.register` #"already_registered" — produced by `_already_registered("as", model.__name__, type_cls.__name__)`). The reverse direction (`type_cls` already mapped to a different model) raises `"<type_name> is already registered against <existing_model_name>"`.

Consumers calling `registry.get(model)` today (in `django_strawberry_framework/types/base.py::_build_annotations`, `django_strawberry_framework/types/converters.py::resolved_relation_annotation`, `django_strawberry_framework/types/finalizer.py::finalize_django_types` #"target_type = registry.get", `django_strawberry_framework/optimizer/walker.py::_resolve_field_map`, `django_strawberry_framework/optimizer/walker.py::_walk_selections` #"registry.get(django_field.related_model)", `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._get_or_build_plan`) all assume the lookup is deterministic. With one type per model, it is.

`Meta` options today (`django_strawberry_framework/types/base.py` #"ALLOWED_META_KEYS"): `model`, `fields`, `exclude`, `name`, `description`, `optimizer_hints`, `interfaces`. Deferred keys (`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`) raise at `_validate_meta` time. `Meta.primary` is not currently in either set — declaring it raises `"Unknown Meta keys: ['primary']"`.

`DjangoTypeDefinition` (`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`) is a dataclass holding the collected metadata. No `primary` field today.

## Goals

- Allow registering multiple `DjangoType` subclasses for the same Django model.
- Introduce `Meta.primary: bool` (default `False`) — declares the type that drives nested-relation resolution and optimizer reverse lookup.
- Ambiguity rules, enforced precisely as specified in the card body:
  - One type only, no `primary`: allowed (backward compat).
  - One type only, `primary = True`: allowed.
  - Multiple types, exactly one `primary`: allowed.
  - Multiple types, multiple primaries: error at registration time.
  - Multiple types, no primary: error at finalization (`finalize_django_types`).
- **Auto-synthesized relation binding centralized at finalization.** `_build_annotations` always defers every **auto-synthesized** relation field to `PendingRelationAnnotation` + the registry's pending list; `finalize_django_types()` resolves to the primary (or the single registered type). Consumer-authored relation fields (annotation overrides, assigned `strawberry.field`) are unaffected — the existing `if field.name in consumer_authored_fields: continue` short-circuit is preserved. Eliminates the import-order trap where a secondary type registered before the relation source would freeze the auto-synthesized relation against the wrong type.
- **Optimizer root planning uses the resolver's actual return type.** A root resolver returning `AdminItemType` plans against `AdminItemType.field_map` / `optimizer_hints`, not the primary's. Nested relation steps continue to route through the primary via `registry.get(related_model)`.
- Schema audit iterates every reachable registered type and dedupes warning collection — secondary types whose relation fields the primary does not expose are still audited.
- Registry surface gains `primary_for(model)`, `types_for(model)`, and `models_with_multiple_types()`. The internal `_types: dict[Model, list[Type]]` shape is private; consumers go through the helpers.
- 100% coverage on the new registration paths, the new audit, and the consumer-site updates.

## Non-goals

- **No `set_primary(model, type)` mutator on the registry.** `Meta.primary` is a per-class declaration; promoting / demoting a primary at runtime is out of scope (would invalidate every cached relation annotation built so far).
- **No NEW override API ships in this card.** The already-shipped consumer-side relation override surface stays in scope and is exercised by the Slice 4 H1 regression tests: a direct annotation like `category: AdminCategoryType` (annotation-only) and an assigned `category = strawberry.field(...)` resolver (assigned) continue to win over the primary-resolution path via the existing `consumer_authored_fields` short-circuit. They may legitimately target a secondary `DjangoType` after this card ships. What is **not** in scope: a new declarative override key (e.g., `Meta.field_types = {"category": AdminCategoryType}`) — that pattern is `DONE-019-0.0.6` territory.
- **No GraphQL-type-name auto-deduplication.** If two `DjangoType` subclasses on the same model both set `Meta.name = "Item"`, Strawberry catches the collision; this spec does not add a pre-check. Practical guidance: rely on distinct Python class names (Strawberry's default behavior derives the GraphQL type name from the class name).
- **No change to choice enum sharing.** Two types on the same model that both select the same choice column continue to share one cached `(model, field_name)` enum. That is desirable: it means the GraphQL schema has one enum per choice column, not one per type.
- **No removal of the existing single-type backward-compat path.** Single-type declarations without `primary` continue to work unchanged.
- **No `Meta.primary` propagation through proxy / abstract model chains.** A subclass `DjangoType` with `Meta.model = ProxyOfItem` is independent of a `DjangoType` with `Meta.model = Item` — they are different `Model` keys in the registry.

## Architectural decisions

### Decision 1 — `Meta.primary` shape and validation

`Meta.primary` is a plain `bool` (default `False` when absent). Validation lives in `_validate_meta` (`django_strawberry_framework/types/base.py::_validate_meta`):

```python
# inside _validate_meta, after the fields/exclude exclusivity check and
# before the DEFERRED_META_KEYS check (the maintainer's pre-Slice-2 TODO
# anchor lands the guard here; the two positions are contract-equivalent
# because "primary" is in ALLOWED_META_KEYS — neither the deferred check
# nor the unknown-key check can fire on a Meta.primary declaration —
# but pinning the anchor's slot keeps spec and source aligned for future
# readers). Lives alongside the existing fields/exclude/optimizer_hints
# normalization calls so the bool guard runs on every subclass declaration.
primary = getattr(meta, "primary", False)
if not isinstance(primary, bool):
    raise ConfigurationError("Meta.primary must be a bool")
```

`"primary"` is added to `ALLOWED_META_KEYS` so the unknown-key guard does not reject it. The validated value is read again at the `__init_subclass__` call site for plumbing through `register_with_definition`.

**Why a plain bool, not a tri-state or enum.** The card's contract is binary: "is this type the primary for its model, yes or no". Tri-state (`PRIMARY` / `SECONDARY` / `UNSET`) would muddy the backward-compat single-type path (which is "unset" today and stays that way). Future variants ("primary for queries, secondary for mutations") are out of scope and would land as a separate Meta key.

### Decision 2 — Registry data model

`_types` becomes `dict[type[models.Model], list[type]]`. Append-on-register; preserve insertion order; treat re-registration of the *same* type as a no-op. (L4 clarification: this is **new** import/retry-tolerant behavior, not a continuation of pre-existing precedent. Pre-spec `register(Model, T)` followed by `register(Model, T)` raised in `django_strawberry_framework/registry.py::TypeRegistry.register` #"already_registered" because the `model in self._types` guard fired before any same-type check; this card's idempotent no-op replaces that hard error for the same-class case.)

New parallel map `_primaries: dict[type[models.Model], type]` tracks the declared primary per model. A model is in `_primaries` iff exactly one of its registered types has `Meta.primary = True`. Two-primary collisions raise before `_primaries` is mutated, so the dict's invariant ("one primary per model") is always intact.

`_models: dict[type, type[models.Model]]` is unchanged. A `DjangoType` subclass is still mapped to exactly one model (a class can't have two `Meta.model =` values). The reverse-collision guard ("same type registered against two models") stays the way it is today.

**Why a separate `_primaries` map instead of marking the primary inside `_types[model]`.** Three reasons:

1. Lookup is O(1) — `_primaries.get(model)` is hot-path for `registry.get(model)`.
2. The "no primary declared" state is the absence of a key, not a sentinel value — fewer special cases.
3. The audit walk (Decision 5) reads `_primaries.get(model) is None and len(_types[model]) >= 2` directly, no scan.

### Decision 3 — `register` signature and collision rules

`register()` returns `bool`: `True` if state was added; `False` if the call was an idempotent no-op. The return value drives the snapshot-restore rollback in `register_with_definition` (M1 fix); see [Decision 3a](#decision-3a--registerwithdefinition-rollback-shape).

```python
def register(
    self,
    model: type[models.Model],
    type_cls: type,
    *,
    primary: bool = False,
) -> bool:
    self._check_mutable()
    # Reverse-collision guard (unchanged).
    existing_model = self._models.get(type_cls)
    if existing_model is not None and existing_model is not model:
        raise self._already_registered("against", type_cls.__name__, existing_model.__name__)

    existing_types = self._types.setdefault(model, [])

    # Idempotent re-register of the same class: no-op.
    if type_cls in existing_types:
        stored_as_primary = self._primaries.get(model) is type_cls
        if primary != stored_as_primary:
            # Re-register with a flag flip in EITHER direction is rejected —
            # primary status is set at class-declaration time and is immutable.
            # (M1 fix: revision 2 only caught False -> True; True -> False
            # silently returned False and left the primary unchanged.)
            raise ConfigurationError(
                f"{type_cls.__name__} is already registered for {model.__name__}; "
                "primary flag cannot be flipped on re-register",
            )
        return False

    if primary:
        existing_primary = self._primaries.get(model)
        if existing_primary is not None:
            raise ConfigurationError(
                f"{type_cls.__name__} is already declared primary as "
                f"{existing_primary.__name__}",
            )

    existing_types.append(type_cls)
    self._models[type_cls] = model
    if primary:
        self._primaries[model] = type_cls
    return True
```

### Decision 3a — `register_with_definition` rollback shape

The idempotent `register()` behavior means a re-registration of an already-stored type is a no-op for `register()`. A naive rollback that unconditionally pops from `_types[model]` / `_models` / `_primaries` would corrupt the pre-existing state. The fix is a snapshot-and-conditional-restore around the inner `register_definition` call:

```python
def register_with_definition(
    self,
    model: type[models.Model],
    type_cls: type,
    definition: DjangoTypeDefinition,
    *,
    primary: bool = False,
) -> None:
    # Snapshot pre-state for conditional rollback.  Only state added by THIS
    # call is rolled back if register_definition raises — pre-existing
    # registrations (idempotent re-registers of the same type) must survive.
    pre_primary = self._primaries.get(model)
    appended = self.register(model, type_cls, primary=primary)
    try:
        self.register_definition(type_cls, definition)
    except Exception:
        if appended:
            # Remove only the entry this call appended.
            types = self._types.get(model, [])
            if type_cls in types:
                types.remove(type_cls)
            if not types:
                self._types.pop(model, None)
            self._models.pop(type_cls, None)
            # Restore _primaries to the pre-call snapshot. When pre_primary
            # is None, pop the key entirely so primary_for(model) is None.
            if pre_primary is None:
                self._primaries.pop(model, None)
            else:
                self._primaries[model] = pre_primary
        # If `appended` is False, this call did not mutate _types / _models /
        # _primaries; the pre-existing state is intact and there is nothing
        # to roll back.
        raise
```

**Why not skip the call to `register()` when the type is already registered.** Because `register_definition` may still legitimately raise (different definition for the same type) and the caller needs the consistent contract that `register_with_definition` either fully succeeds or leaves the registry untouched. The snapshot/conditional-restore is the simplest contract that satisfies both the idempotent and the rollback paths.

**Collision messages, grep-stable:**

- Reverse-collision (unchanged): `"<type_cls> is already registered against <other_model>"`.
- Duplicate-primary: `"<new_type_cls> is already declared primary as <existing_primary_type>"`.
- Primary-flag-flip on idempotent re-register: `"<type_cls> is already registered for <model>; primary flag cannot be flipped on re-register"`.

**What disappears:** the old `"<model_name> is already registered as <existing_type_name>"` message (raised pre-spec inside `django_strawberry_framework/registry.py::TypeRegistry.register` #"already_registered" via `_already_registered("as", model.__name__, type_cls.__name__)` — first slot is the model name, second is the type name). The message is no longer accurate because a second type registration is now the normal multi-type case.

### Decision 4 — `registry.get` semantics

```python
def get(self, model: type[models.Model]) -> type | None:
    primary = self._primaries.get(model)
    if primary is not None:
        return primary
    candidates = self._types.get(model)
    if candidates is not None and len(candidates) == 1:
        return candidates[0]
    return None
```

Three call states:

1. **Primary declared** → return primary.
2. **Single registered type, no primary flag** → return that type. Backward compat for the existing single-type-per-model case; `Meta.primary` stays optional for single-type declarations.
3. **Multiple registered types, no primary declared** → return `None`. The caller treats this the same as "no type registered for this model" — pending relations defer, the finalizer audits and raises.

**Why `None` instead of "raise here":** `registry.get` is called from multiple contexts. `__init_subclass__`-time relation binding wants the deferral path (the second type hasn't been declared yet at that point in import order). Finalize-time relation resolution wants a deterministic answer (or a clear error pointing at the ambiguity). Returning `None` lets both paths fall through to existing handling — pending list during `__init_subclass__`; the audit + unresolved-target error during finalize. The audit-first ordering (Decision 5) ensures the ambiguity error fires before the unresolved-target error.

New helpers (additive, public on `TypeRegistry`):

- `primary_for(model: type[models.Model]) -> type | None` — strict primary lookup. Returns `None` for single-type-no-primary (where `get()` would return the type). Useful when a caller wants to *distinguish* "explicit primary" from "implicit single". Used by `audit_primary_ambiguity` and by tests.
- `types_for(model: type[models.Model]) -> tuple[type, ...]` — immutable tuple of every registered type for `model`, in registration order. Used by `audit_primary_ambiguity` and by tests.
- `models_with_multiple_types() -> Iterator[type[models.Model]]` — yields each model that has `>=2` registered types. Used by `audit_primary_ambiguity` to walk the ambiguity-candidate set in O(unique models) instead of O(total types).

**Note on `iter_types()`.** A previous draft (revision 1) proposed a `primary_or_single_per_model()` helper to drive the schema audit. Revision 2 dropped that helper after the H3 fix: the schema audit now iterates every reachable type (via `iter_types()`) and dedupes the warning collection, because skipping secondary types would silently miss relation fields exposed only on a secondary type. The helper has no remaining consumer and is omitted.

### Decision 5 — Ambiguity rules

Catalog, by detection point:

| Configuration | Detection point | Outcome |
|---|---|---|
| One type, `Meta.primary` absent or `False` | n/a | Allowed (backward compat). `registry.get(model)` returns that type. |
| One type, `Meta.primary = True` | n/a | Allowed. `registry.get(model)` returns that type; `primary_for(model)` returns it. |
| Multiple types, exactly one with `Meta.primary = True` | n/a | Allowed. `registry.get(model)` returns the primary. |
| Multiple types, two or more with `Meta.primary = True` | `registry.register` (second primary tries to register) | `ConfigurationError("<new> is already declared primary as <existing>")` |
| Multiple types, no `Meta.primary = True` | `finalize_django_types` (`audit_primary_ambiguity`) | `ConfigurationError` listing the model and every registered class, with fix sentence: `"Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."` |

`audit_primary_ambiguity` runs inside `finalize_django_types`, **after the existing `if registry.is_finalized(): return` short-circuit** and **before** pending-relation resolution (M1 placement). It is the first work the function does on a non-finalized registry; subsequent `finalize_django_types()` calls hit the `is_finalized()` guard and return without re-auditing:

```python
def audit_primary_ambiguity() -> None:
    """Reject models with multiple registered types and no declared primary."""
    offenders: list[tuple[type[models.Model], tuple[type, ...]]] = []
    for model in registry.models_with_multiple_types():
        if registry.primary_for(model) is None:
            offenders.append((model, registry.types_for(model)))
    if not offenders:
        return
    parts = [
        f"  {model.__name__}: {', '.join(t.__name__ for t in types)}"
        for model, types in offenders
    ]
    raise ConfigurationError(
        "Models with multiple registered DjangoType subclasses and no primary:\n"
        + "\n".join(parts)
        + "\n\nDeclare Meta.primary = True on exactly one of the registered "
          "DjangoType subclasses.",
    )
```

`models_with_multiple_types()` is a one-liner on `TypeRegistry`:

```python
def models_with_multiple_types(self) -> Iterator[type[models.Model]]:
    return (model for model, types in self._types.items() if len(types) >= 2)
```

### Decision 6 — Consumer-site routing semantics

| Call site | Pre-change | Post-change | Net behavior |
|---|---|---|---|
| `django_strawberry_framework/types/base.py::_build_annotations` (`__init_subclass__`-time, **auto-synthesized branch only**) | `target_type = registry.get(...)`; if `None`, defer to pending; else bind eagerly | **Always defer** — every auto-synthesized relation field becomes a `PendingRelationAnnotation` and is appended to the registry's pending list. The eager-bind shortcut is removed. The earlier `if field.name in consumer_authored_fields: continue` short-circuit in the per-field loop body (relations branch and scalars branch) is preserved, so consumer-authored fields are still skipped entirely. (H1 fix) | Auto-synthesized relation binding centralized at `finalize_django_types()`. Eliminates the import-order trap where a secondary type registered first would freeze the relation against the wrong type. Consumer annotation overrides and assigned `strawberry.field` resolvers stay untouched. Post-finalize result identical for single-type usage. |
| `django_strawberry_framework/types/finalizer.py::finalize_django_types` #"target_type = registry.get" (post-audit) | `target_type = registry.get(...)`; if `None`, raise "unresolved target" | unchanged code; the audit (Slice 3) runs first, so `get(...)` returns the primary or the single registered type, or `None` for "no type registered" | Relation binds to primary at finalize; the "no type at all" error keeps its existing shape. |
| `django_strawberry_framework/types/converters.py::resolved_relation_annotation` (was historically `convert_relation`) | `target_type = registry.get(...)` | unchanged | Resolves to primary post-finalize. |
| `django_strawberry_framework/optimizer/walker.py::_resolve_field_map` (root, query-time) | `type_cls = registry.get(model)` | **Use the resolver's actual return type** (threaded as `source_type=` from `plan_optimizations`) instead of `registry.get(model)`. The keyword is `None` for nested recursive calls, which keep the existing `registry.get(...)` behavior. (H2 fix — see [Decision 9](#decision-9--optimizer-origin-type-propagation)) | Root planning uses the resolver's actual return type's `field_map` / `optimizer_hints` (matters when a secondary type exposes fields/hints absent from the primary). Nested relation steps still use the primary. |
| `django_strawberry_framework/optimizer/walker.py::_walk_selections` #"registry.get(django_field.related_model)" (nested `target_type = registry.get(related_model)`) | unchanged | unchanged | Nested relation steps resolve to the primary — matches the spec's "nested relations route through the primary" contract. |
| `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize` (root `plan_optimizations` invocation) | passes `model` only | also threads the resolved origin Strawberry type to `_resolve_field_map(model, source_type=origin)` (H2 fix) | Worker 1 pins exact call-graph during planning. |
| Plan cache key (live tuple at `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._build_cache_key`: `(doc_key, relevant_vars, target_model, response_path)`) | four-element tuple, no origin slot | five-element tuple — add `origin: type \| None` as a fifth slot per [Decision 9](#decision-9--optimizer-origin-type-propagation-h2-fix). (H2 fix) | Primary-type and secondary-type resolvers on the same model do not share a cached plan. |
| `django_strawberry_framework/optimizer/extension.py::_collect_schema_reachable_types` #"registry.get_definition(origin)" (`registry.get_definition(origin)`) and `django_strawberry_framework/optimizer/extension.py::_resolve_model_from_return_type` #"registry.model_for_type(origin)" (`registry.model_for_type(origin)`) — the **registry API and lookup semantics** | both calls preserved unchanged | both calls preserved unchanged | `registry.get_definition` / `registry.model_for_type` work for primary AND secondary types; secondary-type resolvers stay planable. The wrapper `_resolve_model_from_return_type` that USES `model_for_type` does change shape (returns `(origin, model)` instead of `model`) — see the dedicated checklist item. (Rev6 L2.) |
| `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.check_schema` (schema audit) | iterates `registry.iter_types()`; one pair per registered type | **Keep iterating every reachable registered type**; dedupe warning collection (e.g. `set[str]` for the warning sink, or a `(source_model, field_name)`-keyed `set` plus a render pass). (H3 fix) | Reachable secondary types whose relation fields the primary does not expose are still audited. Identical-string duplicate warnings from overlapping field maps are collapsed. |

Secondary types are still **discoverable** for any `(type → model)` reverse-lookup path — `_models[AdminItemType] is Item` regardless of primary status. That keeps the optimizer's `model_for_type(resolver_return_type)` working when a consumer's resolver returns an `AdminItemType` directly.

### Decision 7 — Test strategy

**Test file layout.** Per [`docs/TREE.md`][tree]'s mirror rule, tests live alongside the source they cover:

- `tests/test_registry.py` (extended) — registration behavior, primary tracking, helpers, idempotence, rollback. The largest test addition.
- `tests/types/test_base.py` (extended) or a new `tests/types/test_meta_primary.py` if the additions push `test_base.py` past a comfortable size. Worker 1's planning pass picks based on the file's current line count and the natural grouping with existing Meta-validation tests.
- `tests/test_registry.py` (extended; existing idempotency / finalization tests live here) and/or `tests/types/test_definition_order.py` (extended; existing post-finalize relation-resolution tests live here) — the audit-error tests land in whichever file is the closer thematic fit per test. `tests/types/test_finalizer.py` does NOT exist today (L5 fix); only create it if the audit cluster grows beyond comfortable size in the existing hosts.
- `tests/types/test_converters.py` (extended; ~1455 lines today and the existing relation-conversion host) — the relation-resolution multi-type tests. `tests/types/test_relations.py` does NOT exist today; only create it if `test_converters.py` would otherwise outgrow a comfortable size.
- `tests/optimizer/test_walker.py` and `tests/optimizer/test_extension.py` (extended) — the walker / schema-audit multi-type tests.

**Fake fixtures.** This card does not need fake field classes (unlike `spec-017-deferred_scalars-0_0_6.md` Slice 3/4). Real Django models from the existing test fixtures (`Category`, `Item`) are sufficient; the multi-type test only declares two `DjangoType` subclasses pointing at the same real model.

**Registry-isolation fixture.** Every test file that touches the registry declares its own `@pytest.fixture(autouse=True) def _isolate_registry()` that calls `registry.clear()` on entry and exit. The existing fixture `tests/test_registry.py::_isolate_global_registry` is the model.

**Schema-execution coverage.** Per [`AGENTS.md`][agents], every new public-facing behavior change has at least one `schema.execute_sync` test. For this card:

- Relation resolution picks the primary type → introspect the schema and assert the relation field's type name.
- A multi-type model with both types reachable from `Query` produces a schema with both Strawberry types defined → introspect for both type names.
- An `AdminItemType` resolver returning real model rows → executes through `schema.execute_sync` without the optimizer falling over.

**Coverage target: 100%.**

### Decision 8 — `DjangoTypeDefinition.primary`

Adding `primary: bool = False` to `DjangoTypeDefinition` (`types/definition.py`) gives introspection callers and future-work read sites (e.g., a follow-up that exposes the primary flag through the `DjangoType` public surface) a way to read the flag without re-querying the registry. The dataclass default is `False`, so existing tests and existing call sites that build `DjangoTypeDefinition(...)` keyword-argument-free continue to work.

**L3 clarification — what does NOT read `definition.primary` in this card.** The Slice 3 ambiguity audit calls `registry.primary_for(model)`. The Slice 4 optimizer root-planning path receives the resolver's origin Strawberry type via `source_type=` threading. The schema audit iterates `registry.iter_types()` for warning collection. None of these read `definition.primary`. The single source of truth for "which type is primary for which model" is `registry._primaries`, accessed via the `primary_for(model)` helper; `definition.primary` is a per-type denormalization for read convenience, not a separate authority. Worker 2 must NOT introduce code paths that read `definition.primary` and then make ambiguity-routing decisions from it — those decisions belong on the registry side so the helper-trio (`get`, `primary_for`, `types_for`) stays the unambiguous lookup surface.

### Decision 9 — Optimizer origin-type propagation (H2 fix)

**Problem.** With multi-type semantics, a root resolver returning `AdminItemType` plans against the wrong `field_map` / `optimizer_hints` if the walker calls `registry.get(model)` to recover the type — that lookup returns the *primary* (`ItemType`), not the resolver's actual return type. The plan cache also keys on the model alone, so a primary-return and a secondary-return resolver on the same model would share a cached plan.

**Contract.** The optimizer's *root* field-map / hints lookup uses the resolver's actual Strawberry return type. The *nested* relation-target lookup continues to use `registry.get(related_model)`, which correctly returns the primary (that is the spec's intended nested-relation contract).

**Mechanism.** Thread the resolved origin Strawberry type from `optimizer/extension.py` through `plan_optimizations` to the walker's root `_resolve_field_map(model, source_type=origin)` call(s). `_resolve_field_map` gains a keyword-only `source_type: type | None = None` argument:

- When `source_type` is provided (root call): use it directly as the `type_cls`; do NOT call `registry.get(model)`.
- When `source_type` is `None` (recursive nested calls): use the existing `registry.get(model)` behavior, which returns the primary.

`django_strawberry_framework/optimizer/walker.py` currently has two `_resolve_field_map(model)` call sites: `django_strawberry_framework/optimizer/walker.py::_walk_selections` (root path from `plan_optimizations`) and `django_strawberry_framework/optimizer/walker.py::_selected_scalar_names` (called only from `django_strawberry_framework/optimizer/walker.py::_plan_select_relation` for nested FK-id elision; model argument is `django_field.related_model`). The pinned post-audit decision (rev6 M1) is that **only `_walk_selections` is threaded with `source_type`**; `_selected_scalar_names` stays nested-only and continues to resolve via `registry.get(model)` (which returns the primary by design for nested targets). See the Slice 4 call-site bullet for the full rationale.

**Plan cache key — concrete shape (L1).** The live cache key inside `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._build_cache_key` is the four-element tuple:

```python
(
    doc_key: str,
    relevant_vars: frozenset[tuple[str, Any]],
    target_model: type,
    response_path: tuple[str, ...],
)
```

This card extends the key to distinguish primary-return and secondary-return resolvers on the same model. Recommended shape: add `origin: type | None` as a fifth slot, yielding:

```python
(
    doc_key: str,
    relevant_vars: frozenset[tuple[str, Any]],
    target_model: type,
    response_path: tuple[str, ...],
    origin: type | None,
)
```

**Cache scope (rev6 L1).** `DjangoOptimizerExtension._plan_cache` is root-only — `_get_or_build_plan` is the sole insertion site. Nested plans built inside walker recursion or `_build_prefetch_child_queryset` are NOT inserted through `_build_cache_key`, so the new `origin` slot always receives the concrete root origin type in production paths. The `None` value of the slot is reserved for direct or test-only callers of `_build_cache_key` that deliberately build a plan without an origin. Nested walker recursion stays uncached by `DjangoOptimizerExtension` and keeps `source_type=None` at the walker level — no nested extension-cache path is introduced by this card. The contract is "two resolvers for the same model with different root Strawberry return types must not share a cached plan."

**What does not change.** `model_for_type` continues to work for any registered type (primary or secondary), so the extension's `origin → model` resolution path stays one line. `registry.get(model)` remains the right lookup for nested relation targets where the *primary* is the documented default.

**Why not extend `registry.get(model)` itself to accept an origin hint.** Two reasons: (a) the registry should not need to know about Strawberry types beyond the registered set; (b) the nested-relation path *wants* the primary lookup unchanged, so giving `registry.get` a parameter that only the root path uses would invite call-site confusion. Threading the origin through the walker keeps the contract local to the optimizer subsystem.

## User-facing API

Before this card:

```python
class ItemType(DjangoType):
    class Meta:
        model = Item

class AdminItemType(DjangoType):  # ConfigurationError at import.
    class Meta:
        model = Item
```

After this card:

```python
class ItemType(DjangoType):
    class Meta:
        model = Item
        primary = True  # explicit; drives relation resolution.

class AdminItemType(DjangoType):
    class Meta:
        model = Item
        # primary defaults to False; secondary type.
        fields = ("id", "name", "internal_notes")
```

Both types are registered. `Category.items` relation resolves to `ItemType` (the primary). A resolver returning `AdminItemType` instances stays planable through the optimizer (reverse lookup via `model_for_type(AdminItemType) is Item`).

Backward compat: a single `DjangoType` declared without `Meta.primary` continues to work without modification:

```python
class CategoryType(DjangoType):
    class Meta:
        model = Category
        # primary not declared; single type for Category; works as today.
```

Error cases:

- Two `DjangoType` subclasses on `Item`, both with `Meta.primary = True` → `ConfigurationError("AdminItemType is already declared primary as ItemType")` at the second declaration.
- Two `DjangoType` subclasses on `Item`, neither with `Meta.primary` → `ConfigurationError` at `finalize_django_types()` listing both class names and the fix sentence.
- `Meta.primary = "yes"` (any non-bool) → `ConfigurationError("Meta.primary must be a bool")` at `__init_subclass__` time.

## Implementation plan

Six slices, each landing in a separate commit.

### Slice 1 — Registry multi-type storage + primary tracking

Files: `django_strawberry_framework/registry.py`, `tests/test_registry.py`.

Pure registry-internal changes. No `DjangoType` subclass touches the new surface yet — `register` and `register_with_definition` gain the `primary` keyword but `types/base.py` does not pass it (Slice 2 wires that). All new tests in `tests/test_registry.py` call `registry.register(...)` and `registry.register_with_definition(...)` directly with plain test classes (not real `DjangoType` subclasses) to avoid coupling Slice 1's commit to Slice 2's `Meta.primary` plumbing.

### Slice 2 — `Meta.primary` recognition

Files: `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/definition.py`, `tests/types/test_base.py` (or `tests/types/test_meta_primary.py`).

Adds `"primary"` to `ALLOWED_META_KEYS`; validates type in `_validate_meta`; reads in `__init_subclass__` and threads to `register_with_definition`; adds `primary: bool = False` to `DjangoTypeDefinition`. After this slice, multi-type declarations on the same model **work** but the ambiguity audit has not yet been wired into `finalize_django_types` — the multi-type-no-primary case is currently a no-op (no error, but `registry.get(model)` returns `None` so relation resolution to that model fails at finalize with the existing unresolved-target error). Slice 3 promotes that to the actionable audit error.

### Slice 3 — Cross-type ambiguity audit at finalization

Files: `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/registry.py` (adds `models_with_multiple_types`), `tests/test_registry.py` and/or `tests/types/test_definition_order.py` (the existing finalize-test hosts — see Decision 7 L5 note for the "create a new file only if cluster outgrows" guidance).

The audit runs inside `finalize_django_types` **after the existing `is_finalized()` short-circuit** and **before** pending-relation resolution. After this slice, the "multiple types, no primary" case produces the actionable error; subsequent finalize calls are no-ops via the `is_finalized()` guard without re-auditing.

### Slice 4 — Consumer-site updates (relation conversion + optimizer)

Files: `django_strawberry_framework/types/base.py` (always-defer relation binding — H1 fix), `django_strawberry_framework/optimizer/walker.py` (`source_type` parameter on `_resolve_field_map` — H2 fix), `django_strawberry_framework/optimizer/extension.py` (thread origin through `plan_optimizations`, schema-audit warning dedupe — H2 + H3 fixes), `django_strawberry_framework/types/converters.py` (no change expected; spot-check during planning), `django_strawberry_framework/types/finalizer.py` (no change expected; spot-check during planning), `tests/types/test_converters.py` (the existing relation-conversion host), `tests/optimizer/test_walker.py`, `tests/optimizer/test_extension.py`.

The remaining call sites (`django_strawberry_framework/types/converters.py::resolved_relation_annotation`, `django_strawberry_framework/types/finalizer.py::finalize_django_types` #"target_type = registry.get", `django_strawberry_framework/optimizer/walker.py::_walk_selections` #"registry.get(django_field.related_model)") **do not change** — they already call `registry.get(...)`, which now returns the primary post-finalize for nested relation targets. Three code changes land in this slice: (1) `_build_annotations` always-defer (H1), (2) optimizer root planning uses the resolver's actual return type via `source_type` threading + plan-cache key expansion (H2), (3) schema audit dedupes warning collection while keeping full reachable-type iteration (H3).

### Slice 5 — Atomic version-bump quintet

Single commit; five files: `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `docs/GLOSSARY.md` package-version line, `uv.lock`. **No-op if any prior `0.0.6` card already bumped them** — the tree is already at `0.0.6` from `spec-017-deferred_scalars-0_0_6.md`'s Slice 5 at spec-authoring time, so this is the expected state. See the detailed Slice 5 checklist for the prior-`0.0.6`-card note.

### Slice 6 — Docs, KANBAN, CHANGELOG, archive

Separate commit. Files: root `README.md`, `docs/README.md`, `docs/GLOSSARY.md` (entries beyond the version line), `docs/TREE.md`, `TODAY.md`, `KANBAN.md` (move + verbatim body), `CHANGELOG.md` (`Added` / `Changed`). The spec stays at `docs/spec-018-meta_primary-0_0_6.md` per [`docs/builder/BUILD.md`][build] "Specs stay at their working location after closeout"; opt-in archive to `docs/SPECS/` is the maintainer's call post-merge.

## Edge cases and constraints

- **Idempotent re-import.** `register(Model, T)` called twice (e.g., a test rerun without `registry.clear()`, or a module re-import) is a no-op for the first call's primary state. If the second call sets `primary=True` while the first set `primary=False` (or omitted it), raise — primary status is a declaration, not a mutable property.
- **Same class, different model.** Unchanged from today — `_models[T]` reverse-collision guard raises.
- **`Meta.primary` with no [`Meta.model`][glossary-metamodel].** Falls through to the existing `Meta.model is required` check before `primary` is inspected. No new error needed.
- **`Meta.primary` on an abstract / intermediate `DjangoType` base** (one without `Meta` or with no `Meta.model`). `__init_subclass__` returns early when `meta is None` (`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` #"if meta is None"), so `primary` is never read. Intermediate bases that *do* declare a `Meta.model` are registered like any other — if a consumer declares an intermediate base with `Meta.primary = True` and then a concrete subclass with `Meta.primary = True` on the same model, the duplicate-primary error fires.
- **Two types on the same model with the same [`Meta.name`][glossary-metaname].** Out of scope (not a registry concern — Strawberry catches type-name collisions at schema construction). Mentioned for completeness.
- **Choice enum sharing.** Two types on the same model both selecting `Item.status` (a choice field) continue to share one cached enum keyed by `(Item, "status")`. No new behavior; existing `register_enum` collision guard already enforces "same enum or raise".
- **Optimizer plan cache.** Per [Decision 9](#decision-9--optimizer-origin-type-propagation-h2-fix), the plan cache key includes the resolver's origin Strawberry type **alongside** the model (and the selection-set fingerprint already in use today). Multiple types on the same model produce distinct plan-cache entries — that's intentional. (L1 fix: revision 2 phrased this as "return type, not the model", which contradicted Decision 9; the correct contract is *both*.)
- **[Relay Node integration][glossary-relay-node-integration].** A `DjangoType` with `relay.Node` in [`Meta.interfaces`][glossary-metainterfaces] declares an `id` resolver. Two types on the same model can both be Relay nodes; their global IDs differ by type name (Strawberry's default Relay global-ID encoding). No new error needed.
- **`finalize_django_types` idempotency.** The existing `if registry.is_finalized(): return` short-circuit at the top of `finalize_django_types()` is preserved. The audit runs exactly **once**, on the first successful call, as the new first step before pending-relation resolution. A second `finalize_django_types()` call after a successful finalize is the existing no-op (returns immediately via the `is_finalized()` guard) — the audit does **not** re-run. Defensible because the registry rejects all post-finalize mutators, so the state the first audit saw is the same state any later audit would see. (L3 fix: revision 2 said "the audit re-runs and is a deterministic no-op"; that's inaccurate against the current `is_finalized()` guard, which returns before the audit could re-run.)
- **`registry.clear()` between tests.** Already wipes `_types`, `_models`, `_enums`, `_definitions`, `_pending`, `_finalized`. Must also wipe `_primaries`.

## Test plan

Per [`AGENTS.md`][agents], every new public mapping has at least one `schema.execute_sync` test. Per [`CONTRIBUTING.md`][contributing], coverage must remain at 100%.

Test categories (numbered for traceability against the slice checklist):

1. Registry multi-type storage: append-on-register, idempotent same-class re-register, registration order preserved, reverse-collision still raises.
2. Registry primary tracking: `primary=True` populates `_primaries`; `primary=False` does not; duplicate primary raises; primary-flag-flip on re-register raises.
3. Registry helper surface: `primary_for`, `types_for`, `models_with_multiple_types` — every branch (single, multiple-with-primary, multiple-without-primary).
4. `register()` return value: `True` on real append, `False` on idempotent no-op.
5. `register_with_definition` atomicity: rollback path also clears `_primaries` *only when this call appended state*; pre-existing registrations survive a re-register-with-different-definition failure (M1 regression).
6. `Meta.primary` validation: bool-only; `getattr` default `False`; `ALLOWED_META_KEYS` membership.
7. `DjangoTypeDefinition.primary` propagation.
8. Two-type declaration without primary: both register; `types_for` returns both; finalize raises the audit error.
9. Two-type declaration with one primary: both register; `primary_for` returns the declared primary; finalize succeeds; relation resolution picks the primary.
10. Two-type declaration with two primaries: second declaration raises at registration time.
11. Single-type backward compat: `Meta.primary` absent and `False` both work; `registry.get(model)` returns the lone type.
12. Audit error message shape: contains the model name, every registered class name, and the actionable fix sentence.
13. Audit-before-unresolved-target ordering: when both errors apply, audit fires first.
14. Relation resolution: `Category.items` binds to primary `ItemType` when `Item` has multiple types; verified via schema introspection.
15. **H1 regression**: secondary-before-source-before-primary import order still finalizes the relation to the primary (pins the always-defer contract).
16. **H2 regression**: optimizer root planning uses the resolver's actual return type for `field_map` / `optimizer_hints` (pins the `source_type` threading).
17. **H2 regression**: plan cache holds distinct entries keyed by origin Strawberry type, not by model alone.
18. Optimizer nested-relation planning: still uses `registry.get(related_model)` (the primary).
19. **H3 regression**: schema audit warns on a relation field exposed only on a reachable secondary type whose target is unregistered.
20. **H3 regression**: schema audit dedupes when the same `(source_model, field_name)` is visited via multiple reachable types — exactly one warning per `(model, field)` pair.
21. Optimizer reverse lookup: secondary types remain reachable via `model_for_type` for resolvers returning them.
22. `registry.clear()` resets `_primaries`.

## Doc updates

Per [Slice 6](#slice-6--docs-kanban-changelog-archive). The `Meta.primary` entry rewrite in `docs/GLOSSARY.md` and the `DjangoType` alpha-constraint removal are the two largest doc edits.

## Risks and open questions

- **`registry.iter_types()` semantic change.** Today yields one pair per model. After this card, yields one pair per registered type — a model with multiple types appears multiple times. Existing in-tree consumer (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.check_schema`, the schema audit) continues to use `iter_types()` and instead dedupes warning collection so secondary-type relation fields are still audited without producing duplicate warnings (H3 fix). Any external consumer (none known) would see a behavior change. Documented in the `CHANGELOG.md` `Changed` entry.
- **Auto-synthesized relation binding moves entirely to finalize.** Today, `_build_annotations` eagerly binds an auto-synthesized relation when `registry.get(target_model)` returns a type; this card always defers to `PendingRelationAnnotation`. Net behavior post-finalize is identical for single-type usage; the only observable difference is that `cls.__annotations__[field.name]` is `PendingRelationAnnotation` between `__init_subclass__` and `finalize_django_types()` for auto-synthesized fields. Any consumer reading `__annotations__` inside that window (e.g., a custom metaclass probing `DjangoType` subclasses before finalization) would now see the placeholder. Acceptable: finalization is the documented synchronization point for relation resolution. **Consumer-authored relation fields are unaffected** — the `consumer_authored_fields` short-circuit in the per-field loop body of `django_strawberry_framework/types/base.py::_build_annotations` (relations branch and scalars branch) already skips synthesis for them, so the always-defer change does not reach those fields and a consumer-owned `StrawberryField` is never replaced by a `PendingRelationAnnotation`.
- **Multi-type declarations without `primary` are a registration-time silent success.** The error is deferred to `finalize_django_types`. Consumers who forget to call the finalizer (or call it lazily) would observe the package's existing "finalizer not called" failure mode instead of the new audit error. Acceptable: the finalizer is mandatory for any usable schema; this is documented in `docs/GLOSSARY.md`'s `finalize_django_types` entry.
- **`Meta.primary` on a single-type declaration is a no-op for behavior but populates `_primaries`.** That means `registry.primary_for(model)` returns the type even though it would also be returned by `registry.get(model)` without the flag. Distinct-but-equivalent paths. Acceptable; tests pin both.
- **Concurrent landing with `DONE-019-0.0.6` (Consumer override semantics).** Slice 5 and Slice 6's version-bump steps need explicit no-op handling if 015 lands first. The Worker 1 final-verification pass grep-checks for stale `0.0.5` strings before editing.
- **Already-shipped consumer relation override paths stay in scope; only a new declarative override API is deferred.** A direct annotation (`category: AdminCategoryType`) or an assigned `strawberry.field` resolver on a `DjangoType` already bypasses the primary lookup today via the `consumer_authored_fields` short-circuit, and this card preserves that contract — including its ability to target a secondary `DjangoType`. The Slice 4 H1 regression tests pin that behavior. **What this card does NOT add** is a new override-as-`Meta`-key pattern (e.g., `Meta.field_types = {"category": AdminCategoryType}`) — that pattern is the `DONE-019-0.0.6` (Consumer override semantics) design space.
- **Plan cache key shape.** Today the cache keys on model + selection-set fingerprint. This card extends the key to include the resolver's origin Strawberry type (H2 fix — Decision 9), so primary-return and secondary-return resolvers on the same model produce distinct cache entries. No invalidation of existing cache entries is required at upgrade time because the cache is per-process and re-populates on first use; the key-shape change is forward-only.
- **Optimizer origin-type plumbing.** The H2 fix threads an extra `source_type=` argument from `optimizer/extension.py` through `plan_optimizations` to the walker's root `_resolve_field_map` call. Nested walker recursion does not pass `source_type` — it continues to use `registry.get(related_model)`. Worker 1 pins the exact call-graph during planning; the spec's contract is "root planning uses the resolver's actual return type; nested planning uses the primary", not the specific keyword-threading shape.
- **`Meta.primary` on a `DjangoType` declared inside a test function.** Same registration path; the test's autouse `registry.clear()` wipes the entries on teardown. No new fixture pattern needed.

## Out of scope (explicitly tracked elsewhere)

- A new declarative override API such as `Meta.field_types = {"category": AdminCategoryType}` — `DONE-019-0.0.6` (Consumer override semantics). The *already-shipped* consumer relation overrides (direct annotation and assigned `strawberry.field`) stay in scope and are preserved by this card.
- Runtime `set_primary(model, type)` mutator on the registry — no card; design rationale captured in [Non-goals](#non-goals).
- Per-mutation / per-query primary disambiguation (e.g., "primary for queries, secondary for mutations") — no card; if it surfaces, design a separate `Meta` key.
- Auto-deduplication of `Meta.name` across multi-type declarations — relies on Strawberry's existing type-name collision detection.

## Definition of done

- All six slices land per the [Slice checklist](#slice-checklist).
- Test suite green, coverage at 100%.
- `Meta.primary` validated in `_validate_meta`; rejected with `"Meta.primary must be a bool"` for non-bool values.
- `registry.register` returns `bool` (whether state was added); `registry.register_with_definition` snapshots `_primaries[model]` before calling `register` and rolls back only state added by the current call.
- `registry.register` and `registry.register_with_definition` accept a keyword-only `primary: bool = False`.
- `registry.get(model)` returns the primary if declared, the single registered type otherwise, or `None` for multi-type-pending-primary.
- `registry.primary_for(model)`, `registry.types_for(model)`, `registry.models_with_multiple_types()` exist and are tested.
- `DjangoTypeDefinition.primary` populated from `Meta.primary`.
- `audit_primary_ambiguity` runs inside `finalize_django_types` after the existing `is_finalized()` short-circuit and before pending-relation resolution; it raises a `ConfigurationError` listing the model and every registered class plus the actionable fix sentence. The audit executes exactly once per build (subsequent finalize calls hit the `is_finalized()` guard).
- Duplicate-primary collisions raise at registration time with message `"<new> is already declared primary as <existing>"`.
- `types/base.py` `_build_annotations` always defers **auto-synthesized** relation fields to `PendingRelationAnnotation` + the registry's pending list; no eager-bind branch. The existing `if field.name in consumer_authored_fields: continue` short-circuit is preserved so annotation overrides and assigned `strawberry.field` resolvers are unaffected.
- `optimizer/walker.py` `_resolve_field_map` accepts a keyword-only `source_type`; the root call from `plan_optimizations` passes the resolver's origin Strawberry type; nested calls leave `source_type=None` and use `registry.get(related_model)`.
- Plan cache key includes the resolver's origin Strawberry type.
- `optimizer/extension.py` schema audit iterates every reachable registered type via `registry.iter_types()` and dedupes warning collection; secondary types whose relation fields the primary does not expose are still audited.
- Atomic version-bump quintet aligned at `0.0.6` (no-op if any prior `0.0.6` card already bumped — the tree is at `0.0.6` from `spec-017-deferred_scalars-0_0_6.md` at spec-authoring time).
- Root `README.md`, `docs/README.md`, `docs/GLOSSARY.md` (entries beyond the version line), `docs/TREE.md`, `TODAY.md`, `CHANGELOG.md`, `KANBAN.md` (verbatim `DONE-018-0.0.6` body) all reflect shipped state.
- `docs/GLOSSARY.md` entries flipped: [`Meta.primary`][glossary-metaprimary] → `shipped (0.0.6)`; [`DjangoType`][glossary-djangotype] alpha-constraint bullet replaced.
- **PyPI publish gate** — do not `uv publish` the `0.0.6` distribution until Slice 6 closes, mirroring `spec-017-deferred_scalars-0_0_6.md`'s gate. The two cards share the `0.0.6` distribution; whichever finishes Slice 6 last unblocks the publish.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[contributing]: ../../CONTRIBUTING.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-choice-enum-generation]: ../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-index]: ../GLOSSARY.md#index
[glossary-metainterfaces]: ../GLOSSARY.md#metainterfaces
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metaname]: ../GLOSSARY.md#metaname
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-plan-cache]: ../GLOSSARY.md#plan-cache
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-schema-audit]: ../GLOSSARY.md#schema-audit
[tree]: ../TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build]: ../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
