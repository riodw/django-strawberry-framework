# Spec: Multiple `DjangoType`s per model with `Meta.primary`

Target release: `0.0.6`.
Status: shipped in `0.0.6` (2026-05-19).
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [`DjangoType`][glossary-djangotype], [`Meta.primary`][glossary-metaprimary], [`Relation handling`][glossary-relation-handling], [`finalize_django_types`][glossary-finalize-django-types]), [`KANBAN.md`][kanban] card `DONE-018-0.0.6`.
Card line: ["Multiple DjangoTypes per model with `Meta.primary` — registry-multiplicity + primary-type-resolution work for the remaining `0.0.6` patch."][kanban]

Deliberation, rejected alternatives, the six rounds of review feedback that shaped this spec, and
every claim it may no longer make live in the companion
[`spec-018-meta_primary-0_0_6-rationale.md`][spec-018-rationale]. This file states only the
contract that holds at `HEAD`.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoType`][glossary-djangotype] — the base class whose one-type-per-model alpha constraint this card lifts.
- [`Meta.primary`][glossary-metaprimary] — the `Meta` key this card ships; `shipped (0.0.6)`.
- [`finalize_django_types`][glossary-finalize-django-types] — runs the cross-type ambiguity audit after every subclass has registered.
- [`Relation handling`][glossary-relation-handling] — the resolution path that binds a relation target to the **primary** `DjangoType` for the related model (or to the lone registered type when no primary is declared).
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
  - [ ] Update `register(model, type_cls, *, primary: bool = False) -> bool` per [Decision 3](#decision-3--register-signature-and-collision-rules). **Return value (new):** `True` if state was added (a new entry appended to `_types[model]` and/or `_primaries[model]` set); `False` if the call was an idempotent no-op (same `type_cls` already in `_types[model]`). Drives the snapshot-rollback path in `register_with_definition`.
    - First registration for `model`: append; if `primary=True`, set `_primaries[model] = type_cls`. Returns `True`.
    - Subsequent registration for `model` of the *same* `type_cls` (idempotent re-import) **with the same effective `primary` state** (both `False`, or both `True` against the already-stored primary): no-op. Returns `False`.
    - Subsequent registration for `model` of the *same* `type_cls` with a `primary` flag that disagrees with the stored value — in **either direction** (`False`→`True` *or* `True`→`False`): raise `ConfigurationError("<type> is already registered for <model>; primary flag cannot be flipped on re-register")`.
    - Subsequent registration for `model` of a *different* `type_cls`: append. If new `primary=True` and `_primaries[model]` already set to a different class: raise `ConfigurationError` (duplicate primary). Otherwise add to list; if `primary=True`, set `_primaries[model] = type_cls`. Returns `True`.
    - Reverse-collision guard (same `type_cls`, different `model`) remains; raise `ConfigurationError` as today.
  - [ ] Update `register_with_definition(model, type_cls, definition, *, primary: bool = False)` to forward the `primary` keyword through. **Rollback:** snapshot `pre_primary = self._primaries.get(model)` before calling `register()`; capture `appended = self.register(model, type_cls, primary=primary)`. If `register_definition` then raises, roll back only what this call added: if `appended` is `True`, remove `type_cls` from `_types[model]` (and pop the model key if the list becomes empty), pop `_models[type_cls]`, and restore `_primaries[model]` to `pre_primary` (popping the key when `pre_primary is None`). If `appended` is `False`, perform no rollback — the existing state was not touched by this call.
  - [ ] Update `get(model) -> type | None` per [Decision 4](#decision-4--registryget-semantics):
    - If `_primaries[model]` set: return it.
    - Else if exactly one type registered for `model`: return that single type.
    - Else (multiple types, no primary): return `None`. This is the "ambiguous; awaiting finalization audit" state.
  - [ ] Add `primary_for(model) -> type | None` — returns `_primaries.get(model)` directly. Distinct from `get()` so callers can tell the difference between "single registered type with no primary flag" and "explicitly declared primary".
  - [ ] Add `types_for(model) -> tuple[type, ...]` — returns the immutable tuple of every type registered against `model` in registration order. Used by [`_audit_primary_ambiguity`](#decision-5--ambiguity-rules) and by future tests / introspection.
  - [ ] Add `models_with_multiple_types() -> Iterator[type[models.Model]]` — yields each model with `>=2` registered types. A one-shot generator: the finalizer materializes it into a tuple once per build and feeds that tuple to the audit, so the walk is never re-run per consumer. Enumerates the ambiguity-candidate set without exposing `_types` to the finalizer.
  - [ ] Add `iter_types()` shape note: now yields `(model, type_cls)` pairs **once per registered type**, so the same `model` can appear in the iterator multiple times. [Schema audit][glossary-schema-audit] (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.check_schema`) continues to use this iterator (with warning-collection dedupe — see the Slice 4 `check_schema` item).
  - [ ] Update `clear()` to also clear `_primaries`.
  - [ ] Tests in `tests/test_registry.py`:
    - [ ] **Retire the superseded collision test.** The legacy `test_register_collision_raises` in `tests/test_registry.py` expected a second `register(Model, T2)` call to raise `ConfigurationError(match="already registered")` — the one-type-per-model contract this card lifts. Under this card that second call must *not* raise (the no-primary multi-type case). It is deleted in the same commit as the registry change: `tests/test_registry.py::test_register_two_types_same_model_without_primary_allows_both_in_types_for` covers the inverse contract and `tests/test_registry.py::test_register_same_class_against_two_models_raises` keeps the reverse-collision assertion the legacy name is easily confused with.
    - [ ] `test_register_two_types_same_model_without_primary_allows_both_in_types_for` — verifies multi-storage works; `types_for(Model)` returns both in registration order.
    - [ ] `test_register_second_type_for_same_model_no_longer_raises_collision` — verifies a second type for an already-mapped model no longer raises in the no-primary case (see [Decision 3](#decision-3--register-signature-and-collision-rules)).
    - [ ] `test_register_same_type_twice_is_idempotent` — calling `register(Model, T)` twice does not duplicate the entry in `_types[Model]`.
    - [ ] `test_register_primary_flag_sets_primary_for` — single type with `primary=True` populates `_primaries`.
    - [ ] `test_register_two_primaries_for_same_model_raises_configuration_error` — second `register(Model, T2, primary=True)` after `register(Model, T1, primary=True)` raises with message containing the attempted class name, the model name, and `"is already the primary type"`.
    - [ ] `test_register_same_type_re_register_with_flipped_primary_false_raises` (regression) — register `(Model, T, primary=True)`, then call `register(Model, T, primary=False)`. Assert the second call raises `ConfigurationError` containing `"primary flag cannot be flipped"`. Pins the `True → False` direction of the symmetric flip guard.
    - [ ] `test_register_same_type_re_register_with_flipped_primary_true_raises` — register `(Model, T)` (or `primary=False`), then call `register(Model, T, primary=True)`. Assert `ConfigurationError`. Pins the `False → True` direction.
    - [ ] `test_register_with_definition_rollback_clears_primary` — when `register_definition` raises mid-`register_with_definition` for a *new* type, the `_primaries` entry is also rolled back to its pre-call state (snapshot-restore, not unconditional pop).
    - [ ] `test_register_with_definition_idempotent_re_register_does_not_corrupt_state` — regression: pre-register `(Item, ItemType, def1)`. Call `register_with_definition(Item, ItemType, def2)` where `def2 is not def1`. Assert: (a) the second call raises `ConfigurationError` from `register_definition` (re-register collision); (b) `registry.types_for(Item) == (ItemType,)` (the original registration is intact); (c) `registry.model_for_type(ItemType) is Item`; (d) `registry.get_definition(ItemType) is def1` (the original definition is preserved); (e) if `def1` had registered as primary, `registry.primary_for(Item) is ItemType` post-failure.
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
  - [ ] Add `primary: bool = False` field to `django_strawberry_framework/types/definition.py:DjangoTypeDefinition`. Populated from the `Meta.primary` read above. Stored on the dataclass for introspection and future-work read sites (the schema audit and optimizer walker route through `registry.primary_for(model)` and the threaded origin type respectively — they do NOT consume `definition.primary`; the single source of truth for "which type is primary for which model" remains `registry._primaries`, accessed via the `primary_for(model)` helper).
  - [ ] Tests in `tests/types/test_base.py` (or `tests/test_registry.py` if more naturally placed there — see test placement note in [Decision 7](#decision-7--test-strategy)):
    - [ ] **Rewrite `tests/types/test_base.py::test_registry_collision_raises_configuration_error`.** It pinned the *old* one-type-per-model behavior at the class-creation layer (the `__init_subclass__` path). Keep its assertion shape and give both subclasses `Meta.primary = True` so the duplicate-primary error fires instead — the lower-touch option, since the new tests below already cover the two-types-one-primary success path.
    - [ ] `test_meta_primary_true_registers_type_as_primary` — declares one `DjangoType` with `Meta.primary = True`; asserts `registry.primary_for(Model) is TheType`.
    - [ ] `test_meta_primary_false_does_not_register_primary` — declares with `Meta.primary = False` explicitly; asserts `registry.primary_for(Model) is None`.
    - [ ] `test_meta_primary_absent_does_not_register_primary` — no `Meta.primary` key; asserts `registry.primary_for(Model) is None`.
    - [ ] `test_meta_primary_non_bool_raises_configuration_error` — `Meta.primary = "yes"` raises with message containing `"must be a bool"`.
    - [ ] `test_meta_primary_propagates_to_definition` — `registry.get_definition(TheType).primary is True`.
    - [ ] `test_two_types_same_model_one_primary_both_register_successfully` — declares `ItemType` and `AdminItemType(Meta.primary=True)` on `Item`; asserts no error, `types_for(Item) == (ItemType, AdminItemType)`, `primary_for(Item) is AdminItemType`.
    - [ ] `test_two_primary_types_same_model_raises` — declares two `DjangoType` subclasses on `Item`, both with `Meta.primary = True`; the second declaration raises `ConfigurationError` with message containing `"Cannot register"` and `"is already the primary type"`.
- [ ] Slice 3: Cross-type ambiguity audit at finalization
  - [ ] Add `_audit_primary_ambiguity(multi_type_models)` in `django_strawberry_framework/types/finalizer.py` per [Decision 5](#decision-5--ambiguity-rules). Module-private: the audit is a finalizer-internal step, not a public surface.
    - Walk the `multi_type_models` tuple the caller materialized from `registry.models_with_multiple_types()` (the helper landed in Slice 1). For each model, if `registry.primary_for(model) is None`: collect into the offenders list along with `registry.types_for(model)`.
    - If the offenders list is non-empty, raise `ConfigurationError` listing every offending model name and every registered class name, with the fix sentence: `"Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."`.
    - **Placement.** Run inside `finalize_django_types()` **after the existing `if registry.is_finalized(): return` short-circuit** and **before** pending-relation resolution. Only pure reads may precede it inside the guard — the `multi_type_models` materialization the audit consumes, and the validated `RELAY_GLOBALID_STRATEGY` snapshot — because a read cannot mutate a collected class and so cannot disturb the failure-atomic contract; no class-mutating work may. Placing the audit above the `is_finalized()` guard would make it re-run on every `finalize_django_types()` call, contradicting the [`finalize_django_types` idempotency](#edge-cases-and-constraints) contract. The post-guard, pre-resolution placement gives: (a) the ambiguity error fires before the existing unresolved-target error so consumers see the root cause; (b) the pending-relation resolution path can rely on `registry.get(model)` returning the primary (or the single registered type) without re-checking for ambiguity; (c) the audit runs exactly once per build, on the first successful finalize.
  - [ ] Tests split between `tests/test_registry.py` (idempotency / finalization cluster) and `tests/types/test_definition_order.py` (post-finalize relation resolution) — the two finalize-test hosts this card's audit cluster lands in, one per test by thematic fit:
    - [ ] `test_finalize_raises_when_model_has_multiple_types_no_primary` — declares two `DjangoType` subclasses on `Item`, neither primary; `finalize_django_types()` raises `ConfigurationError` with message containing the model name and both class names.
    - [ ] `test_finalize_succeeds_when_model_has_multiple_types_one_primary` — declares two `DjangoType` subclasses, one primary; finalize succeeds.
    - [ ] `test_finalize_succeeds_when_model_has_single_type_no_primary` — backward-compat path.
    - [ ] `test_finalize_ambiguity_error_message_contains_actionable_fix` — assertion on the `"Declare Meta.primary = True"` substring.
    - [ ] `test_finalize_ambiguity_error_fires_before_unresolved_target_error` — set up both conditions; assert the ambiguity error is the one raised.
    - [ ] `test_audit_runs_once_per_build` (regression) — monkey-patch `registry.models_with_multiple_types` to a spy (counting wrapper). Call `finalize_django_types()` once (success path; no offenders). Call `finalize_django_types()` a second time. Assert the spy was invoked exactly once. Pins that the audit sits *below* the `is_finalized()` guard. Without the post-guard placement, the spy would be invoked twice and the test would catch the regression even though no `ConfigurationError` is raised.
- [ ] Slice 4: Consumer-site updates (relation conversion + optimizer)
  - [ ] **`django_strawberry_framework/types/base.py::_build_annotations`** relation resolution. Replace the eager-bind-or-defer branch with **always-defer for auto-synthesized relations**: every relation field whose annotation the package generates is recorded as `PendingRelationAnnotation` and added to the registry's pending list during `__init_subclass__`. The pre-existing `if field.name in consumer_authored_fields: continue` short-circuit early in the per-field loop body of `_build_annotations` (relations branch and scalars branch) STAYS — consumer-authored relation fields (annotation overrides like `category: CategoryType` and assigned `strawberry.field` resolvers) continue to skip synthesis entirely, so a consumer-owned `StrawberryField` is never overwritten with a `PendingRelationAnnotation`. The eager path for auto-synthesized fields was unsafe under multi-type semantics — a single secondary registered before the relation source would freeze the relation against the secondary even when the primary registered later. Always-defer removes that import-order trap and centralizes auto-synthesized relation resolution in `finalize_django_types()`. Net post-finalize behavior is identical for the existing single-type case; the only observable difference is that `target_type` is `None`-and-pending during the `__init_subclass__` window instead of resolved-immediately when the target happened to be declared first.
  - [ ] **`django_strawberry_framework/types/finalizer.py::finalize_django_types` #"target_type = registry.get"** pending-relation resolution. Still calls `registry.get(pending.related_model)`. Per Slice 3, the ambiguity audit runs first; by the time this line executes, `get()` returns the primary (or the single registered type) or `None` for "no type registered at all" (the unchanged "unresolved target" case). No code change required; behavior follows from Slice 1's `get()` and Slice 3's audit.
  - [ ] **`django_strawberry_framework/types/converters.py::resolved_relation_annotation`** (the relation-annotation builder). No change. It takes the already-resolved `target_type` as a parameter and performs no registry lookup of its own, so multi-type semantics reach it only through whatever its caller resolved — which, post-audit, is the primary (or the lone registered type). Primary selection is the caller's job, not this helper's.
  - [ ] **`django_strawberry_framework/optimizer/walker.py::_resolve_field_map`**. Add a keyword-only `source_type: type | None = None` parameter. When `source_type` is provided (the root call from `plan_optimizations`), use it as `type_cls` directly — do **not** call `registry.get(model)`. When `source_type` is `None` (recursive nested calls), keep the current `registry.get(model)` behavior; that path resolves nested relation targets to the primary, which is the spec's intended contract for nested relations.
  - [ ] **`django_strawberry_framework/optimizer/walker.py::_resolve_field_map` call-site split.** `optimizer/walker.py` has two callers: `django_strawberry_framework/optimizer/walker.py::_walk_selections` (the root path from `plan_optimizations`) and `django_strawberry_framework/optimizer/walker.py::_selected_scalar_names` (called only from `django_strawberry_framework/optimizer/walker.py::_plan_select_relation` for nested [FK-id elision][glossary-fk-id-elision]; its model argument is `django_field.related_model`, never the resolver's root return type). Only `_walk_selections` is threaded with `source_type`. `_selected_scalar_names` stays unchanged — it continues to call `_resolve_field_map(model)` with no `source_type`, which routes through `registry.get(model)` and correctly returns the primary for the nested target. Do NOT add `source_type` plumbing to `_selected_scalar_names`: a pure nested FK-id-elision path must keep `source_type=None`, or a nested step would plan against a root resolver's return type.
  - [ ] **`django_strawberry_framework/optimizer/walker.py::_resolve_relation_target`** — the nested relation-target lookup reached from `django_strawberry_framework/optimizer/walker.py::_walk_selections`. Unchanged by this card. It prefers the finalized `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.related_target_for` metadata and falls back to `registry.get(related_model)`; both legs land on the primary, because `related_target_for` itself resolves its target through `registry.get(target_model)`. Nested relation targets resolve to the primary by design — the contract that drove this spec.
  - [ ] **The extension's root planning path**, entered at `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize`. Thread the resolved origin Strawberry type from where it is resolved through to the walker's first call (the one that becomes the root `_resolve_field_map(model, source_type=origin)`). The landed call shape: `django_strawberry_framework/optimizer/walker.py::plan_optimizations` grows a keyword-only `source_type: type | None = None` parameter and passes it straight into its single root `_walk_selections(...)` call; the extension's cache-miss branch inside `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._get_or_build_plan` — the extension's sole `plan_optimizations` invocation, reached from `DjangoOptimizerExtension._optimize` via `DjangoOptimizerExtension.apply_to` — invokes it as `plan_optimizations(resolved_selections, target_model, info=info, source_type=origin)`. (The alternative call shapes the spec once left open are in [the rationale companion][spec-018-rationale].)
  - [ ] **`django_strawberry_framework/optimizer/extension.py::_resolve_model_from_return_type`.** The helper resolves a resolver's Strawberry return type to the underlying model; before this card it computed the origin locally and discarded it, returning the model alone. The root-planning contract needs the origin alongside the model at the extension call site (to feed `plan_optimizations` and the plan-cache key), so the helper returns both, as the `django_strawberry_framework/optimizer/extension.py::_OriginAndModel` NamedTuple with `origin` and `model` fields — named rather than a bare 2-tuple so call sites read `resolved.origin` / `resolved.model` instead of positional unpacking. **Failure contract:** the helper returns `None` whenever **either** `origin` OR `model` is unresolvable (non-object leaf type, missing Strawberry schema, missing schema type, unregistered origin), and the pair **only** when both resolve. The guard inside `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize` is therefore `if resolved is None: return`, preserving the existing skip-when-unresolvable pass-through — a pair with a `None` model would send the walker a `None` model to dereference.
  - [ ] **Update the four `_resolve_model_from_return_type` tests**, split by case.
    - `tests/optimizer/test_extension.py::test_resolve_model_from_return_type_unwraps_nested_wrappers` is the **success case**. Assert the `_OriginAndModel` shape: the underlying model on `.model`, and the resolved Strawberry origin type on `.origin`.
    - `tests/optimizer/test_extension.py::test_resolve_model_returns_none_for_non_object_leaf`, `tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_no_strawberry_schema`, `tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_type_not_in_schema` are **failure cases** (non-object leaf, missing schema, missing schema type) that currently assert `None`. **Keep them asserting `None`** — the failure contract above returns `None` outright; do not rewrite these to expect `(origin, None)` or any other pair shape.
    - Land all four updates in the same commit as the helper change.
  - [ ] **Plan cache key.** The pre-card cache key is the four-element tuple `(doc_key, relevant_vars, target_model, response_path)` at `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._build_cache_key`. Extend it with the origin Strawberry type as a fifth slot `origin: type | None` (see [Decision 9](#decision-9--optimizer-origin-type-propagation)). **Scope:** `DjangoOptimizerExtension._plan_cache` is root-only — `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._get_or_build_plan` is the sole insertion site. Nested plans built inside walker recursion / `_build_prefetch_child_queryset` are NOT inserted through `_build_cache_key`, so the new slot always receives the concrete root origin. The slot's `None` value is reserved for direct or test-only callers of `_build_cache_key` that deliberately build a plan without an origin. Do NOT introduce a nested extension-cache path or thread `None` origins through walker recursion. After the change, a primary-type root resolver and a secondary-type root resolver for the same model produce distinct cache entries.
  - [ ] **`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.check_schema`** schema audit. Keep iterating every reachable registered type via `registry.iter_types()` (do not switch to a "primary only" helper — that would silently skip relation fields exposed only on a reachable secondary type). To avoid duplicate warnings when the same `(source_model, field_name)` is visited via multiple registered types, dedupe warning collection: use a `set[str]` for the warning sink (or a `set[tuple[type[models.Model], str]]` key + a string-builder pass at the end). Document the dedupe rationale in a one-line comment so future readers understand it is a multi-type artifact, not a generic defensiveness.
  - [ ] **`django_strawberry_framework/optimizer/extension.py::_collect_schema_reachable_types` #"registry.get_definition(origin)"** `registry.get_definition(origin)` — works unchanged for any registered type (primary or secondary). No change.
  - [ ] **`django_strawberry_framework/optimizer/extension.py::_resolve_model_from_return_type` #"registry.model_for_type(origin)"** — the **registry API and lookup semantics are unchanged**. `model_for_type` continues to return the correct model for any registered type, primary or secondary. What changes is the wrapper around it: `_resolve_model_from_return_type` now returns both `origin` and `model` instead of discarding the origin (see the dedicated checklist item above). Unchanged lookup semantics is not permission to leave the wrapper returning only the model.
  - [ ] **Rewrite the pre-finalize relation-annotation assertions.** Assertions in `tests/types/test_base.py` and the two siblings `tests/types/test_definition_order.py::test_reverse_fk_resolves_when_parent_declared_before_child` and `tests/types/test_definition_order.py::test_reverse_fk_resolves_when_child_declared_before_parent` read `cls.__annotations__[field_name]` **before** `finalize_django_types()` and expect the resolved target type. Under always-defer those annotations are `PendingRelationAnnotation` until finalize. Rewrite each to whichever is smallest-touch for that site: (a) assert after calling `finalize_django_types()` first, (b) assert the annotation IS `PendingRelationAnnotation` pre-finalize where pinning the pending state was the test's intent, or (c) delete where the new auto-deferred regression tests below already cover it. Land the rewrites in the same commit as the `_build_annotations` change.
  - [ ] Tests in `tests/types/test_converters.py`, the relation-conversion host this card's relation-resolution cluster lands in:
    - [ ] `test_consumer_authored_relation_annotation_override_survives_always_defer` (always-defer regression) — declare `CategoryType` with `items: list["AdminItemType"]` annotation (consumer-authored), plus `AdminItemType` on `Item` *without* `primary=True`, plus `ItemType(primary=True)` on `Item`. Finalize. Assert `CategoryType.items` resolves to `AdminItemType` (the consumer's explicit annotation), not `ItemType` (the primary). Pins that the `consumer_authored_fields` short-circuit still wins over the primary-resolution path. Mirrors `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver` and `tests/types/test_definition_order.py::test_assigned_relation_field_override_keeps_consumer_resolver`.
    - [ ] `test_consumer_assigned_strawberry_field_relation_survives_always_defer` (always-defer regression) — declare `CategoryType` with `items = strawberry.field(...)` (assigned, not annotated), targeting `AdminItemType`. Multi-type `Item` setup as above. Assert the assigned `StrawberryField` is preserved through `__init_subclass__` and `finalize_django_types()` — no `PendingRelationAnnotation` replaces it.
    - [ ] `test_relation_resolves_to_primary_type_when_target_model_has_multiple` — declares `ItemType(primary=True)` and `AdminItemType` on `Item`; declares `CategoryType` with an `items` reverse relation; finalizes; introspects the schema and asserts the `items` field's GraphQL type is `ItemType` (not `AdminItemType`).
    - [ ] `test_relation_resolves_to_primary_when_secondary_registered_before_source_before_primary` (always-defer regression) — declares `AdminItemType` on `Item` *without* `Meta.primary`; declares `CategoryType` referencing the `items` reverse relation; declares `ItemType(Meta.primary=True)` on `Item` *after* the source; finalizes; introspects the schema and asserts `CategoryType.items` resolves to `ItemType`. Pins the always-defer contract; without it, the eager-bind path would have frozen `items` to `AdminItemType`.
    - [ ] `test_relation_resolves_when_target_model_has_one_type_no_primary` — backward compat: a relation still binds to the lone type when no `primary` flag is set (resolved at finalize via `registry.get()` returning the single type).
    - [ ] `test_relation_target_with_multiple_no_primary_surfaces_audit_error_at_finalize` — declares `CategoryType` with `items` relation to `Item`, plus two `Item` types neither primary. Asserts `finalize_django_types()` raises the audit error (not the unresolved-target error).
  - [ ] Tests in `tests/optimizer/test_walker.py` and `tests/optimizer/test_extension.py`:
    - [ ] `test_optimizer_walker_plans_root_from_resolver_return_type_when_secondary` (root-origin regression) — multi-type `Item` with `ItemType(primary=True)` and `AdminItemType`. Build a schema where the root field returns `list[AdminItemType]`. `AdminItemType.field_map` includes a field or `optimizer_hints` entry not present on `ItemType` (e.g., a `prefetch_related` hint on a relation field exposed only on `AdminItemType`). Execute the query and assert the optimizer plan reflects `AdminItemType`'s hints (not `ItemType`'s). Pins the "use the resolver's actual return type for the root field-map" contract.
    - [ ] `test_scalar_only_secondary_resolver_uses_secondary_field_map` (root-origin scalar-projection regression) — multi-type `Item`; build a schema where the root field returns `list[AdminItemType]` and the query selects **only scalar fields** that exist on `AdminItemType` but are absent from `ItemType` (e.g., `internal_notes`). Execute and assert the planner used `AdminItemType.field_map` for the scalar projection (the `.only(...)` list contains the secondary's scalar column). Pins that the **root** `_walk_selections` / `_resolve_field_map(..., source_type=origin)` path resolves to the secondary's field map — without the root-origin threading, the root `_resolve_field_map(model)` would call `registry.get(model)` and plan against the primary's scalar set, dropping the secondary-only column. Note: this regression does NOT exercise `_selected_scalar_names`; that helper is nested-only and stays on the primary.
    - [ ] `test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model` (root-origin regression) — multi-type `Item`; build two schemas (or two root fields on one schema) — one returning `list[ItemType]` and one returning `list[AdminItemType]`. Trigger planning for both. Assert the plan cache holds two distinct entries keyed by origin type (not one shared entry keyed by model alone).
    - [ ] `test_optimizer_walker_uses_primary_for_nested_relation_target` — multi-type `Item` reached via a nested relation field on `CategoryType.items`. Assert the walker plans the nested step against `ItemType.field_map` (the primary), confirming the nested-path contract is unchanged.
    - [ ] `test_schema_audit_warns_on_relation_field_exposed_only_on_secondary_type` (reachable-secondary regression) — declare `ItemType(primary=True)` exposing only scalar fields, and `AdminItemType` exposing a `category` relation whose target model has no registered `DjangoType`. Assert the audit produces a `"Item.category has no registered target DjangoType"` warning. Switching the audit to a "primary only" iteration would silently skip the secondary type's `category` field; this test is what forbids it.
    - [ ] `test_schema_audit_dedupes_when_same_relation_field_visited_via_multiple_types` (reachable-secondary regression) — declare `ItemType(primary=True)` and `AdminItemType` on `Item`, both selecting `category` (a relation whose target has no registered `DjangoType`). Assert exactly one warning is produced for `Item.category` (not two — one per reachable type). Pins the dedupe contract.
    - [ ] `test_model_for_type_reverse_lookup_works_for_secondary_type` — `registry.model_for_type(AdminItemType) is Item`. Secondary types remain discoverable for the optimizer when a resolver returns an `AdminItemType` directly.
- [ ] Slice 5: Atomic version-bump quintet (single commit). Same shape as [`spec-017-deferred_scalars-0_0_6.md`][spec-017] Slice 5: covers programmatically-checked sites only (`pyproject.toml`, `__init__.py`, `tests/base/test_init.py`'s pinned `__version__`, `docs/GLOSSARY.md`'s "Current package version" line, `uv.lock`). The two consumer-facing version strings (`README.md`, `docs/README.md`) move in Slice 6. `0.0.6` carries several cards and the tree reaches `0.0.6` at whichever lands first, so every checkbox below is expected to be a no-op. The slice still exists in the plan so the build cycle's Worker 1 final-verification pass explicitly `grep`s for stale `0.0.5` strings before marking complete — if a future spec change inadvertently regressed the version, this slice catches it.
  - [ ] `pyproject.toml` — `version = "0.0.6"` (no-op if already at `0.0.6` from any prior `0.0.6` card).
  - [ ] `django_strawberry_framework/__init__.py` — `__version__ = "0.0.6"` (no-op if already bumped).
  - [ ] `tests/base/test_init.py` — pinned `__version__` assertion to `"0.0.6"` (no-op if already bumped).
  - [ ] `docs/GLOSSARY.md` — "Current package version: `0.0.6`" line (no-op if already bumped).
  - [ ] `uv.lock` — re-lock with `uv lock` (no-op if already at `0.0.6`).
  - [ ] **Prior-`0.0.6`-card note.** `0.0.6` carries several cards — `DONE-016-0.0.6`, `DONE-017-0.0.6`, this card, and `DONE-019-0.0.6`. The first to land does the real bump; every subsequent card's Slice 5 is a no-op. The Worker 1 final-verification pass MUST `grep` for stale `0.0.5` strings rather than blindly editing — if the bump has already happened, mark every checkbox above complete without re-editing.
- [ ] Slice 6: Docs, KANBAN, CHANGELOG, archive (separate commit; may follow Slice 5 by any interval). **Size note:** this is the largest commit of the six. Consider opening as a draft PR via `gh pr create --draft` for staged review before merge.
  - [ ] Root `README.md` — confirm the package-version line reads `0.0.6` (no-op if any prior `0.0.6` card already bumped it).
  - [ ] `docs/README.md` — confirm the "shipped today is `0.0.6`" line (no-op if any prior `0.0.6` card already bumped it). Add a one-line mention of `Meta.primary` to the shipped-capability summary.
  - [ ] `docs/GLOSSARY.md` entries updated:
    - [`Meta.primary`][glossary-metaprimary] → `shipped (0.0.6)`. Rewrite the body to describe the actual delivered contract (ambiguity rules; `primary_for` / `types_for` registry surface; relation-target resolution semantics). Drop the "planned for `0.0.6`" framing.
    - [`DjangoType`][glossary-djangotype] → remove the "one `DjangoType` per Django model" alpha constraint bullet (currently inside [`docs/GLOSSARY.md` #"DjangoType"][glossary-djangotype] under "Current alpha constraints"). Replace with a one-line "multiple `DjangoType`s per model supported via [`Meta.primary`](#metaprimary)" entry under the shipped-capability list.
    - [Index][glossary-index] → flip the status badge on `Meta.primary` to `shipped (0.0.6)`.
  - [ ] `docs/TREE.md` — no source-tree changes (no new files); add `Meta.primary` to the `[alpha]` milestone tag for `DjangoType` if relevant; otherwise no-op.
  - [ ] `TODAY.md` — add `Meta.primary` to the "what fakeshop demonstrates today" section if the example project exercises it; otherwise mention it under "available but not currently demonstrated in fakeshop".
  - [ ] `KANBAN.md` — the card lands in the Done section as `DONE-018-0.0.6`, linked to this
    spec, with a body recording the slice-by-slice scope. `KANBAN.md` renders from the fakeshop
    kanban app's database ([`START.md`][start] "Rendered docs"), so the card body is authored in
    the DB and regenerated - never hand-edited here, and never reproduced verbatim in this spec,
    where a copy would drift against the live card by construction. The body as shipped is
    recorded in [`spec-018-meta_primary-0_0_6-rationale.md`][spec-018-rationale].
  - [ ] `CHANGELOG.md` — `[Unreleased]` entries (**permission granted by this spec**, overriding [`AGENTS.md`][agents]'s default prohibition):
    - `Added`: `Meta.primary` boolean flag. Multiple `DjangoType` subclasses per Django model. Registry surface: `primary_for`, `types_for`, `models_with_multiple_types`.
    - `Changed`: `registry.register` now returns `bool` (whether state was added; was `None`). `registry.register` and `registry.register_with_definition` gained a keyword-only `primary: bool = False` parameter. `registry.get(model)` semantics: returns the primary if declared; the single type if only one is registered; `None` if multiple types are registered with no primary.
    - `Changed`: `registry.iter_types()` now yields once per registered type — a model with multiple types appears multiple times. Consumers iterating to drive a per-model action should explicitly dedupe by model, or use `models_with_multiple_types()` + `types_for(model)` for an explicit grouping.
    - `Changed`: `_build_annotations` (`types/base.py`) always defers **auto-synthesized** relation annotations to `PendingRelationAnnotation` + the registry's pending list; the eager-bind shortcut is removed. Consumer-authored relation fields (annotation overrides and assigned `strawberry.field`) continue to skip synthesis entirely — the existing `if field.name in consumer_authored_fields: continue` short-circuit is preserved.
    - `Changed`: optimizer plan cache key includes the resolver's origin Strawberry type alongside the model. Primary-return and secondary-return resolvers on the same model produce distinct cache entries.
  - [ ] **Archival is not this card's step.** The spec closes out at its working location per [`docs/builder/BUILD.md`][build] "Specs stay at their working location after closeout"; the [Definition of done](#definition-of-done) does not gate on a move. A later spec author's `docs/SPECS/NEXT.md` Step 8 sweep relocates it to `docs/SPECS/` and its `-terms.csv` / `-rationale.md` companions to `docs/SPECS/appx/`, rewriting every cross-reference in one pass — which is where this spec now lives.

## Problem statement

Before this card the package carried an alpha constraint of "one [`DjangoType`][glossary-djangotype] per Django model", enforced at `register()` time: a second type registering against an already-mapped model raised `ConfigurationError`.

DRF-style usage (the package's stated target audience) commonly defines public, admin, list, and detail variants of the same model. Under that constraint, declaring `class AdminItemType(DjangoType): class Meta: model = Item` after `ItemType` already existed for `Item` raised at import time, with no escape hatch — consumers either forked the model into a proxy or restructured the schema around the limitation, neither of which composes with the rest of the type-conversion machinery.

The card mandates an explicit primary-declaration contract: multiple types per model are allowed when ambiguity is resolved by `Meta.primary = True` on exactly one of them. Relation conversion, schema audit, and the optimizer's reverse-lookup all need a deterministic answer to "which type backs this model" — without `Meta.primary` that answer would be import-order-dependent, which is the un-stated behavior this card upgrades to an explicit, declared one.

## Goals

- Allow registering multiple `DjangoType` subclasses for the same Django model.
- Introduce `Meta.primary: bool` (default `False`) — declares the type that drives nested-relation resolution and optimizer reverse lookup.
- Ambiguity rules, enforced precisely as specified in the card body:
  - One type only, no `primary`: allowed (backward compat).
  - One type only, `primary = True`: allowed.
  - Multiple types, exactly one `primary`: allowed.
  - Multiple types, multiple primaries: error at registration time.
  - Multiple types, no primary: error at finalization (`finalize_django_types`).
- **Auto-synthesized relation binding centralized at finalization.** `_build_annotations` always defers every **auto-synthesized** relation field to `PendingRelationAnnotation` + the registry's pending list; `finalize_django_types()` resolves to the primary (or the single registered type). Consumer-authored relation fields (annotation overrides, assigned `strawberry.field`) are unaffected — the existing `if field.name in consumer_authored_fields: continue` short-circuit is preserved. Eliminates the import-order trap where a secondary type registered before the relation source would freeze the auto-synthesized relation against the wrong type, which is what extends the package's [definition-order independence][glossary-definition-order-independence] guarantee to multi-type models.
- **Optimizer root planning uses the resolver's actual return type.** A root resolver returning `AdminItemType` plans against `AdminItemType.field_map` / `optimizer_hints`, not the primary's. Nested relation steps continue to route through the primary via `registry.get(related_model)`.
- Schema audit iterates every reachable registered type and dedupes warning collection — secondary types whose relation fields the primary does not expose are still audited.
- Registry surface gains `primary_for(model)`, `types_for(model)`, and `models_with_multiple_types()`. The internal `_types: dict[Model, list[Type]]` shape is private; consumers go through the helpers.
- 100% coverage on the new registration paths, the new audit, and the consumer-site updates.

## Non-goals

- **No `set_primary(model, type)` mutator on the registry.** `Meta.primary` is a per-class declaration; promoting / demoting a primary at runtime is out of scope (would invalidate every cached relation annotation built so far).
- **No NEW override API ships in this card.** The already-shipped consumer-side relation override surface stays in scope and is exercised by the Slice 4 always-defer regression tests: a direct annotation like `category: AdminCategoryType` (annotation-only) and an assigned `category = strawberry.field(...)` resolver (assigned) continue to win over the primary-resolution path via the existing `consumer_authored_fields` short-circuit. They may legitimately target a secondary `DjangoType` after this card ships. What is **not** in scope: a new declarative override key (e.g., `Meta.field_types = {"category": AdminCategoryType}`). No such key exists on the package's `Meta` surface; the sibling `0.0.6` card `DONE-019-0.0.6` widened the *already-shipped* annotation-and-assignment override path to scalar columns rather than adding a declarative key.
- **No GraphQL-type-name auto-deduplication.** If two `DjangoType` subclasses on the same model both set `Meta.name = "Item"`, Strawberry catches the collision; this spec does not add a pre-check. Practical guidance: rely on distinct Python class names (Strawberry's default behavior derives the GraphQL type name from the class name).
- **No change to choice enum sharing.** Two types on the same model that both select the same choice column continue to share one cached `(model, field_name)` enum. That is desirable: it means the GraphQL schema has one enum per choice column, not one per type.
- **No removal of the existing single-type backward-compat path.** Single-type declarations without `primary` continue to work unchanged.
- **No `Meta.primary` propagation through proxy / abstract model chains.** A subclass `DjangoType` with `Meta.model = ProxyOfItem` is independent of a `DjangoType` with `Meta.model = Item` — they are different `Model` keys in the registry.

## Architectural decisions

### Decision 1 — `Meta.primary` shape and validation

`Meta.primary` is a plain `bool` (default `False` when absent). Validation lives in `_validate_meta` (`django_strawberry_framework/types/base.py::_validate_meta`):

```python
# inside _validate_meta, after the fields/exclude exclusivity check and
# before the DEFERRED_META_KEYS check. The slot is pinned rather than left
# free: the two positions are contract-equivalent, because "primary" is in
# ALLOWED_META_KEYS and so neither the deferred check nor the unknown-key
# check can fire on a Meta.primary declaration — but a pinned slot keeps
# spec and source readable against each other. Lives alongside the existing
# fields/exclude/optimizer_hints normalization calls so the bool guard
# runs on every subclass declaration.
primary = getattr(meta, "primary", False)
if not isinstance(primary, bool):
    raise ConfigurationError("Meta.primary must be a bool")
```

`"primary"` is added to `ALLOWED_META_KEYS` so the unknown-key guard does not reject it. The validated value is read again at the `__init_subclass__` call site for plumbing through `register_with_definition`.

The shape is a plain `bool` rather than a tri-state or an enum; the alternatives and why each lost are in [the rationale companion][spec-018-rationale].

### Decision 2 — Registry data model

`_types` becomes `dict[type[models.Model], list[type]]`. Append-on-register; preserve insertion order; treat re-registration of the *same* type as a no-op. This is import/retry-tolerant behavior the card introduces, not a pre-existing precedent it continues.

New parallel map `_primaries: dict[type[models.Model], type]` tracks the declared primary per model. A model is in `_primaries` iff exactly one of its registered types has `Meta.primary = True`. Two-primary collisions raise before `_primaries` is mutated, so the dict's invariant ("one primary per model") is always intact.

`_models: dict[type, type[models.Model]]` is unchanged. A `DjangoType` subclass is still mapped to exactly one model (a class can't have two `Meta.model =` values). The reverse-collision guard ("same type registered against two models") is unchanged by this card.

The primary lives in its own map rather than being marked inside `_types[model]`; the rejected alternative and the reasons it lost are in [the rationale companion][spec-018-rationale].

### Decision 3 — `register` signature and collision rules

`register()` returns `bool`: `True` if state was added; `False` if the call was an idempotent no-op. The return value drives the snapshot-restore rollback in `register_with_definition`; see [Decision 3a](#decision-3a--register_with_definition-rollback-shape).

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
            raise ConfigurationError(
                f"{type_cls.__name__} is already registered for {model.__name__}; "
                "primary flag cannot be flipped on re-register",
            )
        return False

    if primary:
        existing_primary = self._primaries.get(model)
        if existing_primary is not None:
            raise ConfigurationError(
                f"Cannot register {type_cls.__name__} as primary for {model.__name__}; "
                f"{existing_primary.__name__} is already the primary type",
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
            # Remove only the entry this call appended. The detach is the
            # exact inverse of register's own two mutations and is shared
            # with the public `unregister` so the two cannot drift on how
            # the "no empty list for a model with zero types" invariant is
            # maintained; _primaries is deliberately NOT its business,
            # because the two callers disagree on it (unregister purges the
            # slot; this rollback restores whatever predated its own call).
            self._detach_type_from_model(model, type_cls)
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

`register()` is called even when the type is already registered; the alternative and why it lost are in [the rationale companion][spec-018-rationale].

**Collision messages, grep-stable:**

- Reverse-collision (unchanged): `"<type_cls> is already registered against <other_model>"`.
- Duplicate-primary: `"Cannot register <new_type_cls> as primary for <model>; <existing_primary_type> is already the primary type"`. The model name is load-bearing: one model can now carry several `DjangoType`s, so a stack-trace grep that names only the two classes cannot say which model the collision is about.
- Primary-flag-flip on idempotent re-register: `"<type_cls> is already registered for <model>; primary flag cannot be flipped on re-register"`.

`register` raises no "<model> is already registered as <type>" collision at all: a second type registration for a model is the normal multi-type case. `django_strawberry_framework/registry.py::TypeRegistry._already_registered` survives as the shared phrasing for the two remaining cross-key collisions — `register`'s reverse-collision and `register_enum`'s `(model, field_name)` collision.

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

- `primary_for(model: type[models.Model]) -> type | None` — strict primary lookup. Returns `None` for single-type-no-primary (where `get()` would return the type). Useful when a caller wants to *distinguish* "explicit primary" from "implicit single". Used by `_audit_primary_ambiguity` and by tests.
- `types_for(model: type[models.Model]) -> tuple[type, ...]` — immutable tuple of every registered type for `model`, in registration order. Used by `_audit_primary_ambiguity` and by tests.
- `models_with_multiple_types() -> Iterator[type[models.Model]]` — yields each model that has `>=2` registered types, walking the ambiguity-candidate set in O(unique models) instead of O(total types). It is a **one-shot generator**, so its single consumer is `finalize_django_types`, which materializes it into a tuple once per build and passes that tuple to every audit that needs it.

**Note on `iter_types()`.** The [schema audit][glossary-schema-audit] iterates every reachable type via `iter_types()` and dedupes the warning collection; it does NOT filter to one type per model, because skipping secondary types would silently miss relation fields exposed only on a secondary. There is deliberately no "primary or single per model" helper on the registry — the rejected alternative is in [the rationale companion][spec-018-rationale].

### Decision 5 — Ambiguity rules

Catalog, by detection point:

| Configuration | Detection point | Outcome |
|---|---|---|
| One type, `Meta.primary` absent or `False` | n/a | Allowed (backward compat). `registry.get(model)` returns that type. |
| One type, `Meta.primary = True` | n/a | Allowed. `registry.get(model)` returns that type; `primary_for(model)` returns it. |
| Multiple types, exactly one with `Meta.primary = True` | n/a | Allowed. `registry.get(model)` returns the primary. |
| Multiple types, two or more with `Meta.primary = True` | `registry.register` (second primary tries to register) | `ConfigurationError("Cannot register <new> as primary for <model>; <existing> is already the primary type")` |
| Multiple types, no `Meta.primary = True` | `finalize_django_types` (`_audit_primary_ambiguity`) | `ConfigurationError` listing the model and every registered class, with fix sentence: `"Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."` |

`_audit_primary_ambiguity` runs inside `finalize_django_types`, **after the existing `if registry.is_finalized(): return` short-circuit** and **before** pending-relation resolution. It is the first *class-mutating-phase* gate the function reaches: only pure reads precede it inside the guard (the `multi_type_models` materialization it consumes, and the validated `RELAY_GLOBALID_STRATEGY` snapshot). Subsequent `finalize_django_types()` calls hit the `is_finalized()` guard and return without re-auditing.

It takes the multi-type-model walk as a parameter rather than calling `registry.models_with_multiple_types()` itself. That generator is one-shot, and the finalizer runs more than one audit over the same candidate set, so the caller materializes it once per build and hands the same tuple to each:

```python
def _audit_primary_ambiguity(multi_type_models: tuple[type[models.Model], ...]) -> None:
    """Reject models with multiple registered types and no declared primary."""
    offenders: list[tuple[type[models.Model], tuple[type, ...]]] = [
        (model, registry.types_for(model))
        for model in multi_type_models
        if registry.primary_for(model) is None
    ]
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

The offenders are sorted by model name before rendering so the error body is deterministic regardless of consumer import order.

`models_with_multiple_types()` is a one-liner on `TypeRegistry`, and its one-shot generator shape is why the finalizer materializes it:

```python
def models_with_multiple_types(self) -> Iterator[type[models.Model]]:
    return (model for model, types in self._types.items() if len(types) >= 2)
```

### Decision 6 — Consumer-site routing semantics

| Call site | Pre-change | Post-change | Net behavior |
|---|---|---|---|
| `django_strawberry_framework/types/base.py::_build_annotations` (`__init_subclass__`-time, **auto-synthesized branch only**) | `target_type = registry.get(...)`; if `None`, defer to pending; else bind eagerly | **Always defer** — every auto-synthesized relation field becomes a `PendingRelationAnnotation` and is appended to the registry's pending list. The eager-bind shortcut is removed. The earlier `if field.name in consumer_authored_fields: continue` short-circuit in the per-field loop body (relations branch and scalars branch) is preserved, so consumer-authored fields are still skipped entirely. | Auto-synthesized relation binding centralized at `finalize_django_types()`. Eliminates the import-order trap where a secondary type registered first would freeze the relation against the wrong type. Consumer annotation overrides and assigned `strawberry.field` resolvers stay untouched. Post-finalize result identical for single-type usage. |
| `django_strawberry_framework/types/finalizer.py::finalize_django_types` #"target_type = registry.get" (post-audit) | `target_type = registry.get(...)`; if `None`, raise "unresolved target" | unchanged code; the audit (Slice 3) runs first, so `get(...)` returns the primary or the single registered type, or `None` for "no type registered" | Relation binds to primary at finalize; the "no type at all" error keeps its existing shape. |
| `django_strawberry_framework/types/converters.py::resolved_relation_annotation` | takes the already-resolved `target_type` as a parameter; performs no registry lookup | unchanged | The helper only shapes the annotation (`list[T]` / `T | None` / `T`). Which type it shapes is the caller's resolution, which post-audit is the primary. |
| `django_strawberry_framework/optimizer/walker.py::_resolve_field_map` (root, query-time) | `type_cls = registry.get(model)` | **Use the resolver's actual return type** (threaded as `source_type=` from `plan_optimizations`) instead of `registry.get(model)`. The keyword is `None` for nested recursive calls, which keep the existing `registry.get(...)` behavior. See [Decision 9](#decision-9--optimizer-origin-type-propagation). | Root planning uses the resolver's actual return type's `field_map` / `optimizer_hints` (matters when a secondary type exposes fields/hints absent from the primary). Nested relation steps still use the primary. |
| `django_strawberry_framework/optimizer/walker.py::_resolve_relation_target` (the nested relation-target lookup reached from `_walk_selections`) | unchanged | unchanged | Nested relation steps resolve to the primary — via `DjangoTypeDefinition.related_target_for` where the definition is finalized, else the `registry.get(related_model)` fallback. Both legs land on the primary, because `related_target_for` resolves through `registry.get(target_model)` itself. |
| `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._get_or_build_plan` — the extension's sole `plan_optimizations` invocation, reached from `DjangoOptimizerExtension._optimize` via `DjangoOptimizerExtension.apply_to` | the root `plan_optimizations` invocation passed `model` only | also threads the resolved origin Strawberry type through `plan_optimizations(..., source_type=origin)` to the root `_resolve_field_map(model, source_type=origin)`. `_optimize` resolves the origin (`_resolve_model_from_return_type`) and hands it down the chain as `apply_to`'s `target_type`; the invocation itself is `_get_or_build_plan`'s. | Root planning sees the resolver's actual return type. |
| Plan cache key (live tuple at `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._build_cache_key`: `(doc_key, relevant_vars, target_model, response_path)`) | four-element tuple, no origin slot | five-element tuple — `origin: type \| None` as a fifth slot per [Decision 9](#decision-9--optimizer-origin-type-propagation). | Primary-type and secondary-type resolvers on the same model do not share a cached plan. |
| `django_strawberry_framework/optimizer/extension.py::_collect_schema_reachable_types` #"registry.get_definition(origin)" (`registry.get_definition(origin)`) and `django_strawberry_framework/optimizer/extension.py::_resolve_model_from_return_type` #"registry.model_for_type(origin)" (`registry.model_for_type(origin)`) — the **registry API and lookup semantics** | both calls preserved unchanged | both calls preserved unchanged | `registry.get_definition` / `registry.model_for_type` work for primary AND secondary types; secondary-type resolvers stay planable. The wrapper `_resolve_model_from_return_type` that USES `model_for_type` does change shape (returns an `_OriginAndModel` pair instead of a bare model) — see the dedicated checklist item. |
| `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.check_schema` (schema audit) | iterates `registry.iter_types()`; one pair per registered type | **Keep iterating every reachable registered type**; dedupe warning collection (e.g. `set[str]` for the warning sink, or a `(source_model, field_name)`-keyed `set` plus a render pass). | Reachable secondary types whose relation fields the primary does not expose are still audited. Identical-string duplicate warnings from overlapping field maps are collapsed. |

Secondary types are still **discoverable** for any `(type → model)` reverse-lookup path — `_models[AdminItemType] is Item` regardless of primary status. That keeps the optimizer's `model_for_type(resolver_return_type)` working when a consumer's resolver returns an `AdminItemType` directly.

### Decision 7 — Test strategy

**Test file layout.** Per [`docs/TREE.md`][tree]'s mirror rule, tests live alongside the source they cover:

- `tests/test_registry.py` (extended) — registration behavior, primary tracking, helpers, idempotence, rollback. The largest test addition.
- `tests/types/test_base.py` (extended) — the `Meta.primary` validation and declaration tests, grouped with the existing Meta-validation cluster.
- `tests/test_registry.py` (extended; the idempotency / finalization cluster) and `tests/types/test_definition_order.py` (extended; the post-finalize relation-resolution cluster) — the audit-error tests land in whichever of the two is the closer thematic fit per test.
- `tests/types/test_converters.py` (extended; the relation-conversion host) — the relation-resolution multi-type tests.
- `tests/optimizer/test_walker.py` and `tests/optimizer/test_extension.py` (extended) — the walker / schema-audit multi-type tests.

**Fake fixtures.** This card does not need fake field classes (unlike [`spec-017-deferred_scalars-0_0_6.md`][spec-017] Slice 3/4). Real Django models from the existing test fixtures (`Category`, `Item`) are sufficient; the multi-type test only declares two `DjangoType` subclasses pointing at the same real model.

**Registry-isolation fixture.** Every test file that touches the registry declares its own `@pytest.fixture(autouse=True) def _isolate_registry()` that calls `registry.clear()` on entry and exit. The existing fixture `tests/test_registry.py::_isolate_global_registry` is the model.

**Schema-execution coverage.** Per [`AGENTS.md`][agents], every new public-facing behavior change has at least one `schema.execute_sync` test. For this card:

- Relation resolution picks the primary type → introspect the schema and assert the relation field's type name.
- A multi-type model with both types reachable from `Query` produces a schema with both Strawberry types defined → introspect for both type names.
- An `AdminItemType` resolver returning real model rows → executes through `schema.execute_sync` without the optimizer falling over.

**Coverage target: 100%.**

### Decision 8 — `DjangoTypeDefinition.primary`

Adding `primary: bool = False` to `DjangoTypeDefinition` (`types/definition.py`) gives introspection callers and future-work read sites (e.g., a follow-up that exposes the primary flag through the `DjangoType` public surface) a way to read the flag without re-querying the registry. The dataclass default is `False`, so existing tests and existing call sites that build `DjangoTypeDefinition(...)` keyword-argument-free continue to work.

**What does NOT read `definition.primary`.** The Slice 3 ambiguity audit calls `registry.primary_for(model)`. The Slice 4 optimizer root-planning path receives the resolver's origin Strawberry type via `source_type=` threading. The schema audit iterates `registry.iter_types()` for warning collection. None of these read `definition.primary`. The single source of truth for "which type is primary for which model" is `registry._primaries`, accessed via the `primary_for(model)` helper; `definition.primary` is a per-type denormalization for read convenience, not a separate authority. Worker 2 must NOT introduce code paths that read `definition.primary` and then make ambiguity-routing decisions from it — those decisions belong on the registry side so the helper-trio (`get`, `primary_for`, `types_for`) stays the unambiguous lookup surface.

### Decision 9 — Optimizer origin-type propagation

**Problem.** With multi-type semantics, a root resolver returning `AdminItemType` plans against the wrong `field_map` / `optimizer_hints` if the walker calls `registry.get(model)` to recover the type — that lookup returns the *primary* (`ItemType`), not the resolver's actual return type. The plan cache also keys on the model alone, so a primary-return and a secondary-return resolver on the same model would share a cached plan.

**Contract.** The optimizer's *root* field-map / hints lookup uses the resolver's actual Strawberry return type. The *nested* relation-target lookup continues to use `registry.get(related_model)`, which correctly returns the primary (that is the spec's intended nested-relation contract).

**Mechanism.** Thread the resolved origin Strawberry type from `optimizer/extension.py` through `plan_optimizations` to the walker's root `_resolve_field_map(model, source_type=origin)` call(s). `_resolve_field_map` gains a keyword-only `source_type: type | None = None` argument:

- When `source_type` is provided (root call): use it directly as the `type_cls`; do NOT call `registry.get(model)`.
- When `source_type` is `None` (recursive nested calls): use the existing `registry.get(model)` behavior, which returns the primary.

`django_strawberry_framework/optimizer/walker.py` currently has two `_resolve_field_map(model)` call sites: `django_strawberry_framework/optimizer/walker.py::_walk_selections` (root path from `plan_optimizations`) and `django_strawberry_framework/optimizer/walker.py::_selected_scalar_names` (called only from `django_strawberry_framework/optimizer/walker.py::_plan_select_relation` for nested FK-id elision; model argument is `django_field.related_model`). **Only `_walk_selections` is threaded with `source_type`**; `_selected_scalar_names` stays nested-only and continues to resolve via `registry.get(model)` (which returns the primary by design for nested targets). See the Slice 4 call-site bullet for the full rationale.

**Plan cache key — concrete shape.** The live cache key inside `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._build_cache_key` is the four-element tuple:

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

**Cache scope.** `DjangoOptimizerExtension._plan_cache` is root-only — `_get_or_build_plan` is the sole insertion site. Nested plans built inside walker recursion or `_build_prefetch_child_queryset` are NOT inserted through `_build_cache_key`, so the new `origin` slot always receives the concrete root origin type in production paths. The `None` value of the slot is reserved for direct or test-only callers of `_build_cache_key` that deliberately build a plan without an origin. Nested walker recursion stays uncached by `DjangoOptimizerExtension` and keeps `source_type=None` at the walker level — no nested extension-cache path is introduced by this card. The contract is "two resolvers for the same model with different root Strawberry return types must not share a cached plan."

**What does not change.** `model_for_type` continues to work for any registered type (primary or secondary), so the extension's `origin → model` resolution path stays one line. `registry.get(model)` remains the right lookup for nested relation targets where the *primary* is the documented default.

The origin is threaded through the walker rather than passed to `registry.get(model)` as a hint; the rejected alternative and its two reasons are in [the rationale companion][spec-018-rationale].

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

- Two `DjangoType` subclasses on `Item`, both with `Meta.primary = True` → `ConfigurationError("Cannot register AdminItemType as primary for Item; ItemType is already the primary type")` at the second declaration.
- Two `DjangoType` subclasses on `Item`, neither with `Meta.primary` → `ConfigurationError` at `finalize_django_types()` listing both class names and the fix sentence.
- `Meta.primary = "yes"` (any non-bool) → `ConfigurationError("Meta.primary must be a bool")` at `__init_subclass__` time.

## Implementation plan

Six slices, each landing in a separate commit.

### Slice 1 — Registry multi-type storage + primary tracking

Files: `django_strawberry_framework/registry.py`, `tests/test_registry.py`.

Pure registry-internal changes. No `DjangoType` subclass touches the new surface yet — `register` and `register_with_definition` gain the `primary` keyword but `types/base.py` does not pass it (Slice 2 wires that). All new tests in `tests/test_registry.py` call `registry.register(...)` and `registry.register_with_definition(...)` directly with plain test classes (not real `DjangoType` subclasses) to avoid coupling Slice 1's commit to Slice 2's `Meta.primary` plumbing.

### Slice 2 — `Meta.primary` recognition

Files: `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/definition.py`, `tests/types/test_base.py`.

Adds `"primary"` to `ALLOWED_META_KEYS`; validates type in `_validate_meta`; reads in `__init_subclass__` and threads to `register_with_definition`; adds `primary: bool = False` to `DjangoTypeDefinition`. After this slice, multi-type declarations on the same model **work** but the ambiguity audit has not yet been wired into `finalize_django_types` — the multi-type-no-primary case is currently a no-op (no error, but `registry.get(model)` returns `None` so relation resolution to that model fails at finalize with the existing unresolved-target error). Slice 3 promotes that to the actionable audit error.

### Slice 3 — Cross-type ambiguity audit at finalization

Files: `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/registry.py` (adds `models_with_multiple_types`), `tests/test_registry.py` and `tests/types/test_definition_order.py` (the two finalize-test hosts, one per test by thematic fit — see [Decision 7](#decision-7--test-strategy)).

The audit runs inside `finalize_django_types` **after the existing `is_finalized()` short-circuit** and **before** pending-relation resolution. After this slice, the "multiple types, no primary" case produces the actionable error; subsequent finalize calls are no-ops via the `is_finalized()` guard without re-auditing.

### Slice 4 — Consumer-site updates (relation conversion + optimizer)

Files: `django_strawberry_framework/types/base.py` (always-defer relation binding), `django_strawberry_framework/optimizer/walker.py` (`source_type` parameter on `_resolve_field_map`), `django_strawberry_framework/optimizer/extension.py` (thread the origin through `plan_optimizations`, expand the plan-cache key, dedupe schema-audit warnings), `tests/types/test_converters.py`, `tests/optimizer/test_walker.py`, `tests/optimizer/test_extension.py`. `django_strawberry_framework/types/converters.py` and `django_strawberry_framework/types/finalizer.py` are unchanged by this slice.

The remaining call sites **do not change**: `django_strawberry_framework/types/finalizer.py::finalize_django_types` #"target_type = registry.get" and `django_strawberry_framework/optimizer/walker.py::_resolve_relation_target` already route through `registry.get(...)`, which now returns the primary post-finalize for nested relation targets, and `django_strawberry_framework/types/converters.py::resolved_relation_annotation` never consulted the registry at all. Three code changes land in this slice: (1) `_build_annotations` always-defer, (2) optimizer root planning uses the resolver's actual return type via `source_type` threading plus plan-cache key expansion, (3) the schema audit dedupes warning collection while keeping full reachable-type iteration.

### Slice 5 — Atomic version-bump quintet

Single commit; five files: `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `docs/GLOSSARY.md` package-version line, `uv.lock`. **No-op if any prior `0.0.6` card already bumped them.** `0.0.6` carries several cards and the first to land does the real bump, so a no-op here is the expected state; the slice exists so final verification `grep`s for a stale `0.0.5` rather than assuming. See the detailed Slice 5 checklist.

### Slice 6 — Docs, KANBAN, CHANGELOG, archive

Separate commit. Files: root `README.md`, `docs/README.md`, `docs/GLOSSARY.md` (entries beyond the version line), `docs/TREE.md`, `TODAY.md`, the fakeshop kanban DB behind `KANBAN.md` (card moved to Done, body authored, doc regenerated), `CHANGELOG.md` (`Added` / `Changed`). The spec closes out at its working location per [`docs/builder/BUILD.md`][build] "Specs stay at their working location after closeout"; a later spec author's archival sweep moves it and its companions.

## Edge cases and constraints

- **Idempotent re-import.** `register(Model, T)` called twice (e.g., a test rerun without `registry.clear()`, or a module re-import) is a no-op for the first call's primary state. If the second call sets `primary=True` while the first set `primary=False` (or omitted it), raise — primary status is a declaration, not a mutable property.
- **Same class, different model.** Unchanged by this card — the `_models[T]` reverse-collision guard raises.
- **`Meta.primary` with no [`Meta.model`][glossary-metamodel].** Falls through to the existing `Meta.model is required` check before `primary` is inspected. No new error needed.
- **`Meta.primary` on an abstract / intermediate `DjangoType` base** (one without `Meta` or with no `Meta.model`). `__init_subclass__` returns early when `meta is None` (`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` #"if meta is None"), so `primary` is never read. Intermediate bases that *do* declare a `Meta.model` are registered like any other — if a consumer declares an intermediate base with `Meta.primary = True` and then a concrete subclass with `Meta.primary = True` on the same model, the duplicate-primary error fires.
- **Two types on the same model with the same [`Meta.name`][glossary-metaname].** Out of scope (not a registry concern — Strawberry catches type-name collisions at schema construction). Mentioned for completeness.
- **Choice enum sharing.** Two types on the same model both selecting `Item.status` (a choice field) continue to share one cached enum keyed by `(Item, "status")`. No new behavior; existing `register_enum` collision guard already enforces "same enum or raise".
- **Optimizer [plan cache][glossary-plan-cache].** Per [Decision 9](#decision-9--optimizer-origin-type-propagation), the plan cache key includes the resolver's origin Strawberry type **alongside** the model (and the selection-set fingerprint already in use today). Multiple types on the same model produce distinct plan-cache entries — that's intentional. The origin is an addition to the key, never a replacement for the model.
- **[Relay Node integration][glossary-relay-node-integration].** A `DjangoType` with `relay.Node` in [`Meta.interfaces`][glossary-metainterfaces] declares an `id` resolver. Two types on the same model can both be Relay nodes; their global IDs differ by type name (Strawberry's default Relay global-ID encoding). No new error needed.
- **`finalize_django_types` idempotency.** The existing `if registry.is_finalized(): return` short-circuit at the top of `finalize_django_types()` is preserved. The audit runs exactly **once**, on the first successful call, before pending-relation resolution and after only the pure reads it and its sibling audits consume. A second `finalize_django_types()` call after a successful finalize is the existing no-op (returns immediately via the `is_finalized()` guard) — the audit does **not** re-run. Safe because the registry rejects every post-finalize mutator, so the state the first audit saw is the state any later audit would see.
- **`registry.clear()` between tests.** Already wipes `_types`, `_models`, `_enums`, `_definitions`, `_pending`, `_finalized`. Must also wipe `_primaries`.

## Test plan

Per [`AGENTS.md`][agents], every new public mapping has at least one `schema.execute_sync` test. Per [`CONTRIBUTING.md`][contributing], coverage must remain at 100%.

Test categories (numbered for traceability against the slice checklist):

1. Registry multi-type storage: append-on-register, idempotent same-class re-register, registration order preserved, reverse-collision still raises.
2. Registry primary tracking: `primary=True` populates `_primaries`; `primary=False` does not; duplicate primary raises; primary-flag-flip on re-register raises.
3. Registry helper surface: `primary_for`, `types_for`, `models_with_multiple_types` — every branch (single, multiple-with-primary, multiple-without-primary).
4. `register()` return value: `True` on real append, `False` on idempotent no-op.
5. `register_with_definition` atomicity: rollback path also clears `_primaries` *only when this call appended state*; pre-existing registrations survive a re-register-with-different-definition failure (regression).
6. `Meta.primary` validation: bool-only; `getattr` default `False`; `ALLOWED_META_KEYS` membership.
7. `DjangoTypeDefinition.primary` propagation.
8. Two-type declaration without primary: both register; `types_for` returns both; finalize raises the audit error.
9. Two-type declaration with one primary: both register; `primary_for` returns the declared primary; finalize succeeds; relation resolution picks the primary.
10. Two-type declaration with two primaries: second declaration raises at registration time.
11. Single-type backward compat: `Meta.primary` absent and `False` both work; `registry.get(model)` returns the lone type.
12. Audit error message shape: contains the model name, every registered class name, and the actionable fix sentence.
13. Audit-before-unresolved-target ordering: when both errors apply, audit fires first.
14. Relation resolution: `Category.items` binds to primary `ItemType` when `Item` has multiple types; verified via schema introspection.
15. **Always-defer regression**: secondary-before-source-before-primary import order still finalizes the relation to the primary (pins the always-defer contract).
16. **Root-origin regression**: optimizer root planning uses the resolver's actual return type for `field_map` / `optimizer_hints` (pins the `source_type` threading).
17. **Root-origin regression**: plan cache holds distinct entries keyed by origin Strawberry type, not by model alone.
18. Optimizer nested-relation planning: still uses `registry.get(related_model)` (the primary).
19. **Reachable-secondary regression**: schema audit warns on a relation field exposed only on a reachable secondary type whose target is unregistered.
20. **Reachable-secondary regression**: schema audit dedupes when the same `(source_model, field_name)` is visited via multiple reachable types — exactly one warning per `(model, field)` pair.
21. Optimizer reverse lookup: secondary types remain reachable via `model_for_type` for resolvers returning them.
22. `registry.clear()` resets `_primaries`.

## Doc updates

Per [Slice 6](#slice-6--docs-kanban-changelog-archive). The `Meta.primary` entry rewrite in `docs/GLOSSARY.md` and the `DjangoType` alpha-constraint removal are the two largest doc edits.

## Out of scope (explicitly tracked elsewhere)

- A new declarative override API such as `Meta.field_types = {"category": AdminCategoryType}`. No such key is on the `Meta` surface; the consumer override path is the annotation-and-assignment one, widened to scalar columns by the sibling `0.0.6` card `DONE-019-0.0.6`. Those already-shipped relation overrides (direct annotation and assigned `strawberry.field`) stay in scope here and are preserved by this card.
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
- `_audit_primary_ambiguity` runs inside `finalize_django_types` after the existing `is_finalized()` short-circuit and before pending-relation resolution, over a multi-type-model tuple the caller materialized once for the build; it raises a `ConfigurationError` listing the model and every registered class plus the actionable fix sentence. The audit executes exactly once per build (subsequent finalize calls hit the `is_finalized()` guard).
- Duplicate-primary collisions raise at registration time with message `"Cannot register <new> as primary for <model>; <existing> is already the primary type"`.
- `types/base.py` `_build_annotations` always defers **auto-synthesized** relation fields to `PendingRelationAnnotation` + the registry's pending list; no eager-bind branch. The existing `if field.name in consumer_authored_fields: continue` short-circuit is preserved so annotation overrides and assigned `strawberry.field` resolvers are unaffected.
- `optimizer/walker.py` `_resolve_field_map` accepts a keyword-only `source_type`; the root call from `plan_optimizations` passes the resolver's origin Strawberry type; nested calls leave `source_type=None` and resolve the target through `django_strawberry_framework/optimizer/walker.py::_resolve_relation_target`, which lands on the primary.
- Plan cache key includes the resolver's origin Strawberry type.
- `optimizer/extension.py` schema audit iterates every reachable registered type via `registry.iter_types()` and dedupes warning collection; secondary types whose relation fields the primary does not expose are still audited.
- Atomic version-bump quintet aligned at `0.0.6` (a no-op when a prior `0.0.6` card already bumped it, which is the expected case).
- Root `README.md`, `docs/README.md`, `docs/GLOSSARY.md` (entries beyond the version line), `docs/TREE.md`, `TODAY.md`, `CHANGELOG.md`, and `KANBAN.md`'s `DONE-018-0.0.6` card all reflect shipped state.
- `docs/GLOSSARY.md` entries flipped: [`Meta.primary`][glossary-metaprimary] → `shipped (0.0.6)`; [`DjangoType`][glossary-djangotype] alpha-constraint bullet replaced.
- **PyPI publish gate** — do not `uv publish` the `0.0.6` distribution until Slice 6 closes, mirroring [`spec-017-deferred_scalars-0_0_6.md`][spec-017]'s gate. Every `0.0.6` card shares one distribution; whichever finishes Slice 6 last unblocks the publish.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[contributing]: ../../CONTRIBUTING.md
[kanban]: ../../KANBAN.md
[start]: ../../START.md

<!-- docs/ -->
[glossary-choice-enum-generation]: ../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: ../GLOSSARY.md#fk-id-elision
[glossary-index]: ../GLOSSARY.md#index
[glossary-metainterfaces]: ../GLOSSARY.md#metainterfaces
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metaname]: ../GLOSSARY.md#metaname
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-plan-cache]: ../GLOSSARY.md#plan-cache
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-schema-audit]: ../GLOSSARY.md#schema-audit
[glossary]: ../GLOSSARY.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-017]: spec-017-deferred_scalars-0_0_6.md
[spec-018-rationale]: appx/spec-018-meta_primary-0_0_6-rationale.md

<!-- docs/builder/ -->
[build]: ../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
