# Rationale: spec-018 — Multiple `DjangoType`s per model with `Meta.primary` (reasons and rejected alternatives)

Companion to [`spec-018-meta_primary-0_0_6.md`][spec-018]. The spec states the contract; this file records why each Decision is shaped the way it is and which alternatives it rejected.

## Decision 1 — `Meta.primary` shape and validation

- **A tri-state or enum (`PRIMARY` / `SECONDARY` / `UNSET`) rejected.** The contract is binary — "is this type the primary for its model, yes or no" — and a third state would muddy the single-type path, which is "unset" and stays that way.
- **A richer per-context flag** ("primary for queries, secondary for mutations") is out of scope; it would be a separate `Meta` key rather than a widening of this one.

## Decision 2 — Registry data model

- **Marking the primary inside `_types[model]`** (a flag on the list entries, or a sentinel position) rejected: `_primaries.get(model)` is an O(1) lookup on `registry.get`'s hot path; "no primary declared" is the absence of a key rather than a sentinel value; and the audit reads `_primaries.get(model) is None` against a multi-type model directly, with no scan.
- **`_detach_type_from_model` owns the `_types` / `_models` lock-step removal**, shared by the rollback (Decision 3a) and the public `unregister`, so the two cannot drift on the "no empty list for a model with zero types" invariant. `_primaries` is deliberately outside it because the two callers disagree: `unregister` purges the primary slot, the rollback restores whatever primary predated its own call.

## Decision 3 — `register` signature and collision rules

- **The flip guard is symmetric.** A guard catching only `primary=False -> primary=True` on re-register would let a type stored as primary be re-registered with `primary=False` silently, contradicting the same contract from the other side. `requested != stored` covers both directions, and each direction has its own test.
- **The duplicate-primary message names the model.** Once one model can carry several `DjangoType`s, an error naming only the two classes leaves a reader guessing which model the collision is about.

## Decision 3a — `register_with_definition` rollback shape

- **Skipping `register()` when the type is already registered rejected.** `register_definition` may still raise (a *different* definition for the same type), and the caller needs `register_with_definition` to either fully succeed or leave the registry untouched; snapshot-and-conditional-restore satisfies both the idempotent and the rollback paths.
- **An unconditional pop on failure rejected.** A re-registration of an already-stored type is a no-op for `register()`, so an unconditional rollback would tear down pre-existing state the failing call never created.

## Decision 4 — `registry.get` semantics

- **A `primary_or_single_per_model()` helper for the schema audit rejected.** Filtering the audit to one type per model avoids duplicate warnings but silently skips relation fields exposed only on a reachable secondary type; the audit iterates every type and dedupes its warning sink instead, so the helper has no consumer.
- **`None` rather than a raise for the ambiguous state.** It is why `get` has three return states: a raise from the lookup would pre-empt the audit's actionable error and break the `__init_subclass__`-time deferral path.

## Decision 5 — Ambiguity rules

- **Below the `is_finalized()` guard, above pending-relation resolution.** Above the guard the audit would re-run on every call; a side-effect-free audit against a locked registry raises nothing, so the regression would be silent — `test_audit_runs_once_per_build` pins the placement. Above resolution keeps Phase 1 failure-atomic: an ambiguity raise leaves every collected class intact. Only pure reads (the `multi_type_models` materialization and the `RELAY_GLOBALID_STRATEGY` snapshot) may precede it, because a read cannot mutate a collected class.
- **The walk is a parameter.** `models_with_multiple_types()` is a one-shot generator and two audits consume the same candidate set, so the caller materializes it once per build.
- **Offenders sorted by model name** so the error body does not depend on consumer import order.

## Decision 6 — Consumer-site routing semantics

- **Always-defer for auto-synthesized relations.** An eager bind at `__init_subclass__` freezes a relation against whichever type is registered when the source declares; a secondary registered before the source would win over a primary registered after it. Deferring everything to finalize makes the answer independent of import order.
- **`resolved_relation_annotation` stays a pure annotation shaper.** It takes the resolved `target_type` as a parameter; adding a registry lookup inside it would put primary resolution in two places.

## Decision 7 — Test strategy

The tests sit in the modules that own the behavior: `Meta.primary` validation in `tests/types/test_base.py`, the audit cluster across `tests/test_registry.py` and `tests/types/test_definition_order.py`, relation resolution in `tests/types/test_converters.py`, the optimizer cases in `tests/optimizer/`.

## Decision 8 — `DjangoTypeDefinition.primary`

The field is a per-type denormalization for introspection. Routing decisions read the registry (`primary_for`, `get`, `types_for`) so there is one authority for "which type is primary".

## Decision 9 — Optimizer origin-type propagation

- **An origin hint on `registry.get(model)` rejected.** The registry should not need to know about Strawberry types beyond the registered set, and the nested-relation path wants the primary lookup as it is; a parameter only the root path uses would invite call-site confusion. Threading the origin through the walker keeps the contract inside the optimizer.
- **`source_type` enters at `plan_optimizations`, not deeper.** `plan_optimizations` is the walker's public entry point; a caller reaching past it to `_walk_selections` would have to re-derive the root-walk arguments the entry point derives once (`enable_only`, the runtime prefixes, the plan `finalize()` handoff).
- **No `source_type` on `_selected_scalar_names`.** It is reached only from `_plan_select_relation`, whose model argument is `django_field.related_model` for nested FK-id elision; a root origin there would make a nested step plan against the root's field map.
- **No nested extension-cache path.** `_plan_cache` is root-only and `_get_or_build_plan` is its sole insertion site, so the `origin` slot always holds the concrete root origin in production; `None` is for direct or test-only callers.
- **`_resolve_model_from_return_type` returns `None` when either half is unresolvable.** A pair with a `None` model would be truthy, and `_optimize`'s guard would hand the walker a `None` model to dereference. `_OriginAndModel` is a `NamedTuple` so call sites read `resolved.origin` / `resolved.model`.
- **The plan-cache key is per-process** and re-populates on first use, so the origin slot needs no invalidation step.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-018]: ../spec-018-meta_primary-0_0_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
