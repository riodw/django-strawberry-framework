# Definition-order independence

## Problem
`django_strawberry_framework.DjangoType` currently resolves relation target types eagerly during class creation.

The current pipeline is:

1. `DjangoType.__init_subclass__` selects Django fields.
2. `_build_annotations(cls, fields)` dispatches relation fields through `convert_relation`.
3. `convert_relation(field)` immediately asks the registry for `field.related_model`.
4. If the related model has no registered `DjangoType`, `ConfigurationError` is raised.

That means bidirectional model graphs cannot be represented as one rich `DjangoType` per model without careful ordering or field omission. For example:

- `ItemType.category` requires `CategoryType` to already exist.
- `CategoryType.items` requires `ItemType` to already exist.

Both cannot be true at Python class-definition time.

## Why this matters for the goal
`GOAL.md` defines the destination as a DRF-shaped, `class Meta`-driven Strawberry/Django framework that recreates the practical capabilities of `django-graphene-filters` without carrying Graphene runtime dependencies.

Definition-order independence is not just a convenience feature. It is a foundation requirement for that goal.

The intended end state includes:

- `Meta.fields = "__all__"` on rich primary model types
- concrete related `DjangoType`s for automatic relation fields
- root and nested connection fields
- related filters
- related orders
- related aggregates
- fieldsets
- cascade permissions
- Relay node lookup
- automatic optimizer planning across nested selections
- cookbook-style schemas with minimal resolver boilerplate

All of those features assume that the package can build a stable graph of model-backed types before the GraphQL schema is served. If relation resolution remains eager, users must choose between declaration-order workarounds, omitted relation fields, generic fallback types, or manual annotations for every cycle. That would undercut the package's core goal: a Django-native, model-driven schema authoring experience.

The design question is therefore broader than "how do we avoid one import-order error?" The real question is:

- how do we let users declare normal Django model graphs naturally?
- how do we preserve concrete rich relation types?
- how do we finalize those types safely in Strawberry?
- how do we keep optimizer, filters, orders, aggregates, permissions, and connection fields aligned with the finalized graph?
- how do we fail loudly when the schema is incomplete?

## Current package behavior
Current source path:

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/registry.py`

The current behavior is intentionally fail-loud:

- relation target types must be declared first
- one `DjangoType` may register per Django model
- unresolved relation targets raise during type creation

This is simple and safe, but it blocks fully automatic bidirectional schemas for normal Django model graphs.

The current fail-loud behavior is still valuable. The goal is not to replace fail-loud errors with silent degradation. The goal is to move the failure point from "too early, during class creation" to "late enough to allow imports to complete, but still before schema construction or serving."

Current behavior also gives the optimizer a useful invariant: relation fields point to concrete registered target types. Any future design should preserve that invariant after finalization.

## Prior art: Graphene-Django
Graphene-Django solves definition-order independence with lazy relation fields.

Source snapshot inspected:

- `file:///Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py`
- `file:///Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py`
- `file:///Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/registry.py`
- `file:///Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene/types/dynamic.py`
- `file:///Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene/types/schema.py`

Key source references:

- `graphene_django/types.py:222` builds Django fields with `construct_fields(...)`.
- `graphene_django/types.py:264` registers the `DjangoObjectType` after field construction.
- `graphene_django/registry.py:6` registers a type by model.
- `graphene_django/registry.py:19` returns the type for a model.
- `graphene_django/converter.py:274`, `342`, and `381` define relation converters.
- `graphene_django/converter.py:336`, `376`, and `471` return `Dynamic(dynamic_type)` for relation fields.
- `graphene/types/dynamic.py:7` defines `Dynamic`.
- `graphene/types/dynamic.py:19` resolves the dynamic field.
- `graphene/types/schema.py:308-310` resolves `Dynamic` fields while building the schema and skips the field if the dynamic function returns nothing.

Graphene-Django relation conversion does not immediately return the target Graphene object type. It returns a `graphene.Dynamic` placeholder. The placeholder closes over the Django `related_model` and later calls:

```python
registry.get_type_for_model(model)
```

The lookup happens during Graphene schema construction, after more modules have had a chance to import and register their `DjangoObjectType` classes.

### Graphene-Django behavior
This class order can work:

```python
class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = ("id", "items")


class ItemType(DjangoObjectType):
    class Meta:
        model = Item
        fields = ("id", "category")
```

`CategoryType.items` is initially a dynamic placeholder. When the Graphene schema builds, the placeholder resolves `Item` through the registry.

If the target type was never imported or registered by schema construction time, the dynamic relation returns nothing and Graphene skips the field.

### Pros
- Supports bidirectional rich model graphs without requiring declaration order.
- Keeps automatic relation typing: relation fields become the concrete related Graphene type when available.
- Avoids needing a generic fallback object for normal relation fields.
- Works naturally with Graphene's own schema-building lifecycle.

### Cons
- Missing target types can become skipped fields rather than immediate class-definition errors.
- Errors move later, from class creation to schema build or introspection.
- The dynamic placeholder is Graphene-specific; Strawberry does not expose the same exact field lifecycle.
- The registry must tolerate incomplete graphs during class creation.

### Relevance to this package
Graphene-Django proves that automatic concrete relation typing and declaration-order independence can coexist. That is the most important lesson to carry forward.

The parts to borrow are conceptual:

- relation declarations may be recorded before their target type is available
- a model/type registry can resolve those declarations later
- schema construction is a natural boundary for final validation
- concrete target types should be preferred over generic placeholders

The parts to avoid are implementation-specific:

- `graphene.Dynamic`
- Graphene's field mounting lifecycle
- silent field skipping
- dependency on Graphene's old schema builder

The package should treat Graphene-Django as evidence for the desired behavior, not as an implementation substrate.

## Prior art: Strawberry-Django
Strawberry-Django solves the problem differently. It does not generally perform eager model-to-type lookup for relation fields.

Source snapshot inspected:

- `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py`
- `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/base.py`
- `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py`
- `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/utils/typing.py`
- `file:///Users/riordenweber/projects/strawberry-django-main/tests/types.py`

Key source references:

- `strawberry_django/type.py:118` injects `strawberry.auto` for model fields.
- `strawberry_django/type.py:246` calls `strawberry.type(cls, **kwargs)`.
- `strawberry_django/type.py:252` post-processes Strawberry fields.
- `strawberry_django/type.py:272` detects fields that came from `auto`.
- `strawberry_django/type.py:367` updates Django field annotations/descriptions.
- `strawberry_django/type.py:403` records the origin Django type on each field.
- `strawberry_django/type.py:410` stores `__strawberry_django_definition__`.
- `strawberry_django/fields/base.py:185-246` resolves `auto` field types.
- `strawberry_django/fields/types.py:229` defines the Django model-field type map.
- `strawberry_django/fields/types.py:261` maps `ForeignKey` to generic `DjangoModelType`.
- `strawberry_django/fields/types.py:265` maps reverse FK to `list[DjangoModelType]`.
- `strawberry_django/utils/typing.py:105`, `113`, and `116` preserve annotation namespaces through `StrawberryAnnotation`.
- `tests/types.py:1` enables postponed annotations.
- `tests/types.py:15` references `Color` before it is declared.
- `tests/types.py:25` references `Fruit` from the reverse side.
- `tests/types.py:112` and onward show another cyclic graph using explicit annotations.

Strawberry-Django has two effective relation modes.

### Explicit annotation mode
Consumers annotate relation fields with the concrete target Strawberry-Django type:

```python
from __future__ import annotations

@strawberry_django.type(models.Fruit)
class Fruit:
    color: Color | None


@strawberry_django.type(models.Color)
class Color:
    fruits: list[Fruit]
```

Definition-order independence comes from Python's postponed annotations plus Strawberry's annotation resolver. `StrawberryAnnotation` stores the module namespace so forward references can be resolved later.

### `auto` relation mode
Consumers use `strawberry.auto`, `fields="__all__"`, or selected fields with no explicit type annotation.

For relation fields, Strawberry-Django maps to generic fallback types:

- `ForeignKey` -> `DjangoModelType`
- reverse FK -> `list[DjangoModelType]`
- relation fields under relay settings -> `relay.Node` or lists of `relay.Node`

This avoids declaration-order problems because no concrete related Strawberry type is needed. The trade-off is that generic relation fields expose only the generic shape, not the rich related type.

### Pros
- Fits Strawberry's annotation-driven design.
- Explicit relation annotations support rich cyclic graphs through postponed annotations.
- `auto` remains safe without requiring every related type to be known.
- Missing concrete target types do not block type creation when using `auto`.

### Cons
- Fully automatic relation fields do not become the concrete related type by default.
- Users must explicitly annotate rich relations.
- DRF-style `fields="__all__"` does not produce the same rich relation graph that this package aims to produce.
- Generic `DjangoModelType` is less useful for nested querying.

### Relevance to this package
Strawberry-Django proves that Strawberry can support cyclic graphs through annotation namespaces, postponed annotations, and post-processing of Strawberry fields. Those mechanics are worth borrowing.

The parts to borrow are implementation patterns:

- namespace-aware annotation handling
- preserving user-authored annotations
- injecting generated annotations before Strawberry finalization
- custom Strawberry field classes with Django metadata
- field post-processing after `strawberry.type`
- async-safe resolver and queryset handling

The parts to avoid as the default public behavior are product choices that do not match this package's goal:

- requiring explicit annotations for ordinary rich relations
- using generic `DjangoModelType` or `relay.Node` fallback for automatic relation fields
- making decorator-first type declarations the primary API

Explicit annotations should remain an escape hatch. They should not be required for the normal `Meta.fields = "__all__"` path.

## Design options for this package
This package has a DRF-shaped goal: consumers should be able to declare model-backed GraphQL types with `class Meta` and get useful relation fields without writing every relation annotation by hand.

This section is not a final implementation plan. It exists to preserve enough context to make the best decision before implementation.

### Decision criteria
The best design should be judged against these criteria:

- supports cookbook-style rich schemas
- supports fakeshop-style bidirectional model graphs
- preserves concrete related `DjangoType`s by default
- keeps `Meta.fields = "__all__"` useful
- fails loudly before serving an incomplete schema
- avoids Graphene runtime dependencies
- avoids generic relation placeholders as the default schema shape
- works with Strawberry's type lifecycle instead of fighting it
- preserves explicit Strawberry annotations as an override path
- keeps the optimizer able to inspect concrete relation metadata
- creates a foundation for related filters, orders, aggregates, fieldsets, permissions, and connections
- minimizes boilerplate for users
- avoids fragile post-schema mutation when a cleaner pre-schema lifecycle is possible

### Features that depend on this decision
Definition-order independence becomes the shared foundation for later systems:

- `DjangoConnectionField` needs the target node and nested relation types to be concrete before argument and return types are built.
- `DjangoNodeField` needs a finalized primary type per model for Relay lookup.
- related filters need stable related model/type metadata.
- related orders need stable relation paths and generated input types.
- related aggregates need stable related aggregate class graphs and output types.
- fieldsets need generated fields that point back to Django model metadata.
- cascade permissions need a predictable graph of relation fields.
- the optimizer needs to know when a selected field is a forward relation, reverse relation, many-to-many relation, or scalar.

If this layer is weak, every later rich-schema subsystem will need its own workaround.

### Option 1: Keep eager resolution
Keep the current behavior.

Pros:

- Small implementation.
- Fail-loud at class creation.
- No schema-finalization complexity.
- Current optimizer can assume relation targets are concrete.

Cons:

- Bidirectional schemas remain awkward.
- `fields="__all__"` cannot represent normal Django graphs.
- Fakeshop cannot expose both `Category.items` and `Item.category` on the primary types.

### Option 2: Strawberry-Django-style explicit relation annotations
Allow or require consumers to provide explicit relation annotations when they want rich cyclic relations.

Pros:

- Aligns with Strawberry's native forward-reference system.
- Avoids building a custom lazy relation registry.
- Lets advanced users resolve cycles with `from __future__ import annotations`.

Cons:

- Moves away from the package's DRF-first goal.
- `Meta.fields = "__all__"` still needs a fallback for relation fields.
- Requires a stable consumer-override contract, which is currently not promised.

### Option 3: Generic relation fallback
When the related `DjangoType` is not registered, emit a generic relation type similar to Strawberry-Django's `DjangoModelType`.

Pros:

- Breaks definition-order cycles.
- Keeps type creation from failing.
- Easy to explain as an alpha fallback.

Cons:

- Relation fields become less useful.
- Nested querying is limited.
- The generated schema can silently degrade from rich relation type to generic placeholder.
- It is not the best long-term fit for DRF-shaped automatic schema generation.

### Option 4: Graphene-style deferred relation resolution
Record unresolved relation fields during `DjangoType` class creation and resolve them after all relevant `DjangoType`s are registered, before or during Strawberry schema construction.

Pros:

- Best fit for automatic rich relation generation.
- Preserves DRF-shaped `Meta.fields` behavior.
- Supports bidirectional model graphs.
- Keeps the current "relations become concrete related `DjangoType`s" promise.

Cons:

- Requires a package-level pending-relation registry.
- Errors move from type creation to a later finalization point.
- Strawberry type definitions may need to be patched or delayed carefully.
- The optimizer and relation resolver attachment must handle pending targets until finalization.

## Current strongest direction, not a final plan
The strongest direction is still Option 4: a Graphene-style deferred relation model adapted to Strawberry's type lifecycle.

This should not be treated as a finalized implementation plan yet. The high-level product behavior is clear, but the exact type-finalization mechanics still need implementation research and tests.

The target behavior:

- `DjangoType` class creation should not raise just because a related model has not registered yet.
- The package should still fail loudly before serving a schema if an exposed relation target remains unresolved.
- Resolved relation fields should become the concrete target `DjangoType`, not a generic placeholder.
- Explicit user annotations should remain available as an escape hatch.
- The optimizer should continue to see concrete registered target types for selected relations.
- Rich-schema systems should read one shared finalized model/type graph.

### Hard invariants
Any acceptable design should preserve these invariants:

- no Graphene runtime dependency
- no silent Graphene-style field skipping
- no generic relation fallback by default
- no serving a schema with unresolved exposed model relations
- no requirement for manual relation annotations on the normal `Meta.fields = "__all__"` path
- no optimizer regression where finalized relations become opaque
- no hidden schema-shape degradation based only on import order
- clear reset/isolation story for tests that create temporary `DjangoType` classes

### Proposed shape to evaluate
Introduce a pending-relation mechanism in the registry or a sibling module.

During `DjangoType.__init_subclass__`:

1. Validate `Meta`.
2. Select Django fields.
3. Create or update a type-definition object for the class.
4. Register the model/type pair early enough for later classes to discover it.
5. For scalar fields, record enough metadata to build annotations.
6. For relation fields:
   - if the related model is already registered, record the concrete target type
   - otherwise create a pending relation record with source type, source model, field name, related model, relation kind, and nullability/cardinality metadata
7. Preserve user-authored annotations before generating package annotations.
8. Avoid finalizing with Strawberry until the relation strategy is known, unless tests prove placeholder patching is safer.

Before schema construction:

1. Resolve all pending relations against the registry.
2. Resolve lazy type metadata needed by the rich-schema systems.
3. For each resolved relation, compute the concrete annotation:
   - many-side -> `list[target_type]`
   - reverse OneToOne -> `target_type | None`
   - forward nullable -> `target_type | None`
   - forward non-null -> `target_type`
4. Merge generated annotations with user-authored annotations.
5. Attach or rebuild generated Strawberry fields.
6. Attach Django relation metadata for the optimizer and future field classes.
7. If any exposed relation target is still missing, raise `ConfigurationError` with the source model, source field, and related model named.

### Finalization trigger choices
The main unresolved technical question is the Strawberry finalization point.

Possible approaches:

1. Delay `strawberry.type(cls, ...)` until relation targets are resolved.
2. Finalize immediately with placeholders, then patch `__strawberry_definition__.fields`.
3. Require schema construction through a package helper that finalizes pending relations before creating `strawberry.Schema`.
4. Use a hybrid: collect early, finalize through package-owned fields or schema helpers, and keep an explicit `finalize_django_types()` escape hatch for tests and advanced import layouts.

The tradeoffs:

- Option 1 may be cleanest if class registration can be separated from Strawberry finalization without losing current ergonomics.
- Option 2 preserves normal `strawberry.Schema(...)` usage but couples the package to Strawberry internals and risks fragile post-finalization mutation.
- Option 3 is explicit and safe, but adds a new top-level API and may surprise users who expect plain `strawberry.Schema`.
- Option 4 probably fits the broader goal best, but it needs careful API design so simple schemas remain simple and rich schemas finalize predictably.

The newer rich-schema architecture spec leans toward a hybrid finalization story:

- `DjangoConnectionField(Type)` finalizes before building a rich field.
- `DjangoNodeField(Type)` finalizes before building a node field.
- `DjangoSchema(...)` finalizes before constructing `strawberry.Schema`.
- `finalize_django_types()` remains public for explicit control.

This spec should continue to treat that as the leading direction, not an already proven implementation.

### Registry questions
The registry will need to answer more than "which type owns this model?"

Questions to settle:

- Can there be multiple `DjangoType`s per model before `Meta.primary` exists?
- If multiple types exist, which one should automatic relations choose?
- Should automatic relation resolution require exactly one primary type?
- How should abstract/interface types participate?
- How should generated input/output types for filters, orders, and aggregates share the registry?
- How should tests reset registry state without leaking temporary classes?

Likely direction:

- keep one primary output type per model for automatic relation resolution
- allow non-primary model-backed types later
- make ambiguous automatic relation targets a configuration error
- store pending relation records separately from finalized type records

### User annotation questions
Explicit annotations should remain useful.

Questions to settle:

- If a user manually annotates a relation field, should that override automatic conversion?
- Should the package validate that manual annotations match the Django relation cardinality?
- Can a manual annotation intentionally point to a non-primary type for a model?
- How should forward references and `from __future__ import annotations` interact with generated annotations?

Likely direction:

- preserve manual annotations as an escape hatch
- validate them when enough metadata is available
- let manual annotations opt into non-primary target types
- keep automatic `Meta.fields = "__all__"` relations concrete by default

### Generic fallback questions
Generic fallback is useful as an emergency escape hatch but conflicts with the goal if it becomes the default.

Questions to settle:

- Should generic fallback exist at all in 1.0?
- If it exists, should it be per-field, per-type, or global?
- Should it be allowed only for intentionally skipped relation targets?
- How would it appear in schema audit output?

Likely direction:

- do not implement generic fallback first
- default unresolved exposed relations to `ConfigurationError`
- consider explicit fallback later only if real projects need it

### Rich-schema dependency questions
Definition-order independence should be designed with later systems in mind.

Questions to settle before implementation:

- Should filters/orders/aggregates resolve related class graphs during the same finalization pass?
- Should `DjangoTypeDefinition` store `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, and `search_fields` from the start?
- Should connection fields trigger finalization of only reachable types or the whole registry?
- Should aggregate output types be generated before or after relation finalization?
- Should cascade permission traversal use the same relation graph as the optimizer?

Likely direction:

- collect all rich `Meta` keys early
- finalization should produce one shared graph of model/type/relation metadata
- filters/orders/aggregates can have their own factories, but they should consume the same finalized graph
- optimizer and permissions should not maintain separate relation maps that can drift from type generation

## Acceptance criteria
A complete definition-order independence feature should support the narrow relation problem:

- `CategoryType` exposing `items` while `ItemType` is declared later.
- `ItemType` exposing `category` while `CategoryType` is declared earlier or later.
- reverse FK, forward FK, forward OneToOne, reverse OneToOne, and M2M relation shapes.
- `Meta.fields = "__all__"` for bidirectional model graphs.
- clear `ConfigurationError` for exposed relation fields whose target type is never registered.
- optimizer plans that still see concrete target types after finalization.
- schema audit behavior that distinguishes unresolved targets from intentionally skipped fields.

It should also support the broader goal:

- primary model types can be declared in natural application order.
- automatic relation fields resolve to concrete rich `DjangoType`s.
- manual annotations can override generated relation annotations when needed.
- generic relation fallback is not used silently.
- root `DjangoConnectionField` can finalize reachable model types before schema construction.
- `DjangoNodeField` can rely on finalized primary type metadata.
- future related filter/order/aggregate factories can consume finalized relation metadata.
- fieldsets and cascade permissions can traverse the same relation graph as generated fields.
- simple schemas remain possible without forcing every user through a complex schema builder.
- rich schemas have an explicit finalization path when plain `strawberry.Schema` is not enough.

### Failure criteria
The design should be rejected or revised if:

- import order changes the public schema shape.
- missing related types are silently skipped.
- automatic `fields = "__all__"` relation fields degrade to generic placeholders by default.
- relation metadata is finalized in one subsystem but not visible to another.
- optimizer planning loses relation target information.
- generated filter/order/aggregate types need to recreate a separate relation graph.
- schema construction can succeed while exposed relation targets are unresolved.

## Fakeshop implication
The fakeshop product graph is a good acceptance fixture:

- `Category.items` should resolve to `list[ItemType]`.
- `Category.properties` should resolve to `list[PropertyType]`.
- `Item.category` should resolve to `CategoryType`.
- `Property.category` should resolve to `CategoryType`.
- `Item.entries` should resolve to `list[EntryType]`.
- `Property.entries` should resolve to `list[EntryType]`.
- `Entry.item` should resolve to `ItemType`.
- `Entry.property` should resolve to `PropertyType`.

Today this cannot be represented as one rich primary type per model without omitting some relation fields. Definition-order independence should make that schema natural.

## Cookbook implication
The `django-graphene-filters` cookbook recipes schema is the higher-level acceptance fixture.

Definition-order independence should make a Strawberry version possible where each node can use:

- `fields = "__all__"`
- `interfaces = (relay.Node,)`
- `filterset_class`
- `orderset_class`
- `aggregate_class`
- `fields_class`
- `search_fields`
- type-level `get_queryset`
- cascade permissions

The root query should be able to expose connection fields for each primary model type without users manually resolving relation cycles.

This spec does not need to solve filters, orders, aggregates, fieldsets, or permissions directly. It does need to make the relation graph strong enough that those systems can be built on top of it without later redesign.

## Decision context to preserve
Before implementation, keep these conclusions visible:

- Graphene-Django gives the right product insight: defer relation lookup until the registry has enough information.
- Graphene-Django gives the wrong implementation substrate: do not port `Dynamic` or silent field skipping.
- Strawberry-Django gives the right implementation lessons: annotation handling, custom fields, field post-processing, and async-safe resolvers.
- Strawberry-Django gives the wrong default relation shape for this package's goal: generic relation placeholders should not be the normal automatic output.
- `django-graphene-filters` gives the product target: concrete rich nodes with sidecar filters, orders, aggregates, fieldsets, permissions, and connection fields.
- The package should combine those lessons into a Strawberry-native, fail-loud, concrete-relation finalization model.
