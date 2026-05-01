# Spec: DjangoType Contract & Boundary

## Problem statement

The DjangoType pipeline (`spec-django_types.md` Slices 1–4 and 7, plus `spec-optimizer.md` Slice O1) is shipped, but the *contract* between the package and its consumers — which Meta knobs work, which are deferred, which are silently dropped, what consumers can and cannot rely on — has not been pinned in a single document. The alpha review surfaced four concrete gaps:

1. Registry uniqueness. `TypeRegistry.register` raises `ConfigurationError` on collision, forcing one `DjangoType` per Django model. DRF allows multiple Serializers per model; `graphene-django` and `strawberry-graphql-django` both allow multiple types per model. The constraint was real but not previously documented as temporary.
2. Consumer override semantics. `DjangoType.__init_subclass__` claimed in its docstring that consumer-declared annotations override synthesized ones, but `@strawberry.type` rewrites `cls.__annotations__` after the merge so the override doesn't actually hold. The skipped `test_consumer_annotation_overrides_synthesized` pinned the failure.
3. Invalid `Meta.fields` / `Meta.exclude` names. Until 0.0.3, `_select_fields` did a set intersection and silently dropped unknown names — typos became partial-type bugs without any signal.
4. Accepted-but-unwired Meta keys. `Meta.interfaces` was in `ALLOWED_META_KEYS` (validation passed) but never applied to the Strawberry type — a misleading "supported" surface for a feature that did nothing.

The unifying thread: an alpha-stage Meta-driven generator must be narrow and explicit about what it accepts. Silent acceptance of unwired surfaces, silent drops of unknown names, and undocumented hard constraints all corrupt user feedback and break the Meta-class clarity pitch the package is built around.

## Current state

0.0.2 shipped:

- Registry uniqueness enforcement (collision raises).
- Override-merge code path (consumer annotations merged on top of synthesized ones, but Strawberry overrides the merge — known broken).
- `Meta.interfaces` accepted by `ALLOWED_META_KEYS` and silently ignored.
- `Meta.fields` / `Meta.exclude` typos silently dropped.

0.0.3 shipped (in flight):

- `Meta.interfaces` moved to `DEFERRED_META_KEYS`; `_validate_meta` rejects it with the existing deferred-key error message pointing at a future relay spec.
- `_select_fields` raises `ConfigurationError` naming the model, the unknown names, and the available field set when `Meta.fields` or `Meta.exclude` references nonexistent fields.
- `_is_default_get_queryset` sentinel flip in `__init_subclass__` and the implemented `has_custom_get_queryset` body (covered by `spec-optimizer.md` for the O6 consumer; covered here for the type-system half of the contract).

The two remaining contract items — the override claim removal and the registry uniqueness rule — are pinned by this spec. The override claim removal ships in 0.0.3; the registry uniqueness resolution is deferred to a future `Meta.primary` spec.

## Goal

Make the DjangoType contract precise and honest:

- Every knob accepted by `Meta` is either applied today or rejected with a clear error pointing at the spec that will own it.
- Consumer-visible promises (override behavior, registry rules, error shapes) match the actual implementation. Nothing in the docstring or README says "X works" when X doesn't.
- Hard constraints that look temporary are labeled as such, with a named follow-up spec.

## Non-goals

This spec does not cover filtering, ordering, aggregation, permissions, the optimizer rebuild, the future `Meta.primary` mechanism itself, or the future consumer-overrides mechanism itself. Those belong to their own specs. This spec only pins the contract shape they will plug into.

## Topics

### One-model-one-type (alpha constraint)

`TypeRegistry.register` raises `ConfigurationError` when the same Django model is registered twice. This is intentional for the alpha because it keeps the optimizer's `model_for_type` reverse-lookup unambiguous and gives `convert_relation` a single target to point at when a relation is resolved.

The constraint is real friction. DRF projects routinely define multiple Serializers per model — public vs admin, list vs detail, internal vs external, permission-scoped variants. The package's own test suite already works around it manually: `tests/types/test_resolvers.py`, `tests/types/test_converters.py`, and the new `test_has_custom_get_queryset_inherits_through_intermediate_base` all call `registry.clear()` (or directly clear the internal dicts) between defining sibling types over the same model.

**Decision for 0.0.3.** Keep the current "one model, one type, collision raises" behavior. Document it as a temporary alpha constraint in `docs/README.md` "Current surface" with a status marker and a back-reference to this spec.

**Future direction.** Introduce `Meta.primary: bool = False`. The rule is strict and import-order-free:

- A single type per model continues to register without declaring `Meta.primary` — the new key only matters when more than one type wants the same model.
- When two or more types register the same model, **exactly one** must declare `Meta.primary = True`. That primary type wins for `model_for_type` and `convert_relation` reverse lookups; siblings are still registered (and importable) but never selected by reverse lookups.
- Two or more types claim primary -> registration raises (ambiguous primary).
- Two or more types and none claims primary -> registration raises (ambiguous primary by omission). This is the explicit rejection of "first-registered wins": import order will not be part of the API contract under any path.

This work belongs to its own future spec (`spec-meta_primary.md` or similar) which will need to address:

- Migration from current strict-collision behavior (probably opt-in via a new setting or implicit relaxation when any `Meta.primary` is declared).
- Per-type relation routing (does `Item.category` -> `CategoryType` always pick the primary, or does the relation field declare a target?).
- Optimizer impact (does the `Prefetch` downgrade decision use the primary type's `get_queryset`, or does the relation target's chosen type take precedence?).

The alpha review noted that "first-registered wins" without an explicit primary marker would be the worst of the three options because it makes import order part of the API contract. The future spec is explicitly choosing `Meta.primary`, not first-registered-wins.

### Consumer override semantics (deferred to a future spec)

`DjangoType.__init_subclass__` merges consumer-declared annotations on top of the synthesized ones (`cls.__annotations__ = {**synthesized, **existing}`). The intent was to let consumers opt out of any auto-generated field by re-annotating it on the class body. That contract does not actually hold today: `@strawberry.type` regenerates `cls.__annotations__` from its own field metadata after the merge, and the consumer-declared annotation loses to the synthesized one in the final `__strawberry_definition__`.

The skipped `test_consumer_annotation_overrides_synthesized` test in `tests/types/test_base.py` pins the failure mode.

**Decision for 0.0.3.** Remove the override claim from the `__init_subclass__` docstring. The merge code can stay — it's harmless when Strawberry overrides it — but the documentation must not promise behavior we can't deliver. The `docs/README.md` "Current surface" section will explicitly call out consumer overrides as currently *not guaranteed*. The skipped test stays as a contract pin and unskips when the real mechanism ships.

**Future direction.** The override path needs a real implementation, but the design is non-trivial. Three approaches that have been mentioned in passing:

1. Bypass Strawberry's annotation rewrite by reaching into its internals to preserve consumer-declared annotations.
2. Route consumer overrides through Strawberry's own field-customization API (e.g., consumers write `name: str = strawberry.field(description="...")` instead of re-annotating the type).
3. Drop the implicit-override claim entirely and require an explicit Meta-level mechanism (e.g., `Meta.field_overrides = {"name": int}`).

None of these belongs in this spec. They belong to a future `spec-consumer_overrides.md` (or whatever it ends up being called) that picks one of the three after evaluating Strawberry's field-customization API in detail. Until then: limited, not guaranteed.

### Invalid `Meta.fields` / `Meta.exclude` (shipped in 0.0.3)

`_select_fields` validates that every name in `Meta.fields` or `Meta.exclude` corresponds to a real field on `Meta.model`. Unknown names raise `ConfigurationError` whose message names the model, lists the unknowns, and lists the available fields so typos are obvious. Implementation lives in `django_strawberry_framework/types/base.py`; tests in `tests/types/test_base.py` (`test_meta_fields_unknown_name_raises`, `test_meta_fields_unknown_name_includes_model_and_available`, `test_meta_exclude_unknown_name_raises`).

This rule is final. The error shape — model + unknowns + available — is part of the public contract: a consumer can rely on every `ConfigurationError` from this code path naming both the bad input and the valid surface.

### Accepted vs deferred Meta keys (shipped in 0.0.3)

The Meta validator partitions every consumer-supplied key into one of three buckets:

- `ALLOWED_META_KEYS` — keys whose feature is shipped and applied. Today: `model`, `fields`, `exclude`, `name`, `description`.
- `DEFERRED_META_KEYS` — keys reserved for a future feature; rejected with a `ConfigurationError` whose message names them and points at the spec that will own them. Today: `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`.
- Unknown keys — anything outside both sets raises a typo-guard `ConfigurationError` listing the bad keys.

The promotion rule from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` is **strict**: a key only moves to `ALLOWED_META_KEYS` when both of these are true:

1. The validator accepts it.
2. The pipeline applies it to the resulting class / type end-to-end.

A key that is validated but not applied (the original `Meta.interfaces` mistake) is a bug. The reverse is fine — a key that is applied via a different mechanism (consumers subclassing `relay.Node` directly, for example) doesn't need a Meta key at all.

This rule should be checked at every spec slice that introduces or moves a Meta key.

## Coordination with `spec-django_types.md` and `spec-optimizer.md`

`spec-django_types.md` defines the pipeline (Meta validation, scalar synthesis, relation conversion, choice enums, `get_queryset` hook). This spec defines the boundary of that pipeline — what is rejected, what is reserved for the future, what consumers can and cannot rely on.

`spec-optimizer.md` defines the N+1 optimizer subsystem. The `has_custom_get_queryset` sentinel landed alongside the override-detection contract in 0.0.3 and is consumed by O6's `Prefetch` downgrade rule; this spec covers the type-system half of the contract.

When a future spec (filtering, ordering, aggregates, permissions, connection field, relay interfaces, `Meta.primary`, consumer overrides) adds a new Meta key or changes an existing one, that spec must update this contract spec accordingly.

## Open questions

None blocking 0.0.3. The two follow-on specs (`Meta.primary` and consumer overrides) are deliberately deferred — naming them here is enough; designing them is future work tracked under their own spec docs when those land.

## References

- `docs/alpha-review-feedback.md` — recommendations #1 (silent acceptance), #3 (invalid field names), and the consumer-override portion of #5.
- `docs/spec-django_types.md` — the implementation spec this contract spec sits on top of.
- `docs/spec-optimizer.md` — for the `has_custom_get_queryset` sentinel that consumers of this contract spec will eventually use.
- `docs/spec-public_surface.md` — companion spec covering the package-level public-surface and documentation-discipline rules that this contract feeds into.
- `tests/types/test_base.py` — pins the contract for accepted Meta keys, deferred Meta keys, unknown-name validation, the override-merge skipped placeholder, and the `has_custom_get_queryset` sentinel.
