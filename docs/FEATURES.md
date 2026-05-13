# Features

`django-strawberry-framework` is a DRF-shaped feature layer for building GraphQL APIs on top of Django, Django's ORM, and Strawberry. This page describes what the package enables. It intentionally mixes shipped and planned features; each section calls out the current status.

This file is the capability catalog. It answers “what can this package do?” and stays separate from operational setup and internal layout details.

For install, local development, testing, and the canonical documentation map, start from [`../README.md`](../README.md).

## Feature status
- `shipped` — implemented, tested, and available in the current package surface.
- `planned` — committed package direction, not implemented yet.
- `deferred` — reserved for later design or blocked on another feature.
- `alpha constraint` — current behavior that works but is intentionally narrower than the eventual API.

Most users only care about `shipped` and `planned`. The other two labels are for contributors deciding what to work on next.

## Current package surface
Status: shipped alpha.

Current package version: `0.0.5`.

Public exports:
- `DjangoType`
- `DjangoOptimizerExtension`
- `OptimizerHint`
- `finalize_django_types`
- `auto`

Current posture:
- alpha-quality: suitable for internal tools and prototypes, not production
- package-wide capabilities are cataloged in this file
- example-specific current usage belongs in [`../TODAY.md`](../TODAY.md)

## Quick comparison

| Concern | graphene-django | strawberry-graphql-django | this package |
| --- | --- | --- | --- |
| Configuration shape | `class Meta` | decorators | `class Meta` |
| Async resolvers | retrofitted | native | native |
| Modern typing | `graphene.String()` style declarations | type hints | type hints |
| Built-in N+1 optimizer | external patterns | shipped | shipped + plan cache + FK-id elision + queryset diffing + strictness |
| Filter / order / aggregate | shipped | shipped | planned |
| Stable today | yes | yes | alpha |

## DRF-shaped GraphQL API
Status: shipped foundation, planned query features.

The package uses nested `Meta` classes as the consumer-facing configuration surface. The goal is a GraphQL API style that feels like DRF, django-filter, and Django model declarations instead of a stack of Strawberry decorators.

Shipped today:
- `DjangoType` declares GraphQL object types from Django models through `class Meta`.
- `Meta.model`, `fields`, `exclude`, `name`, `description`, and `optimizer_hints` are accepted and applied.
- Unknown `Meta` keys raise `ConfigurationError` so typos do not silently alter the schema.
- Deferred `Meta` keys are rejected until the feature that owns them ships.
- `auto` is re-exported from Strawberry for consumers who want Strawberry-style automatic annotations inside this package's import surface.

Planned:
- `Meta.filterset_class`
- `Meta.orderset_class`
- `Meta.aggregate_class`
- `Meta.fields_class`
- `Meta.search_fields`
- `Meta.primary` for multiple GraphQL types over the same Django model
- stable consumer field override mechanisms for scalar fields

### Relay Node integration
Status: shipped.

`Meta.interfaces` accepts a tuple of Strawberry interface classes; when `relay.Node` is among them, the `DjangoType` becomes a Relay-node-shaped GraphQL type with `id: GlobalID!` and the four `resolve_*` defaults wired through `cls.get_queryset` (the model's default manager plus the type's visibility hook). Optimizer-extension cooperation on the node-lookup path is deferred to a follow-up slice; root-level list resolvers continue to receive full `DjangoOptimizerExtension` treatment.

```python
import strawberry
from strawberry import relay
from django_strawberry_framework import DjangoType
from myapp.models import Category


class CategoryNode(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name")
        interfaces = (relay.Node,)
```

Shipped behavior:
- Default `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes` classmethods are injected when `relay.Node` is declared; consumer-declared overrides are preserved via Strawberry's `__func__` identity test (matches `strawberry-django`).
- When `relay.Node` is in `Meta.interfaces`, the synthesized Django `id: int!` annotation is suppressed and the Relay-supplied `id: GlobalID!` from the interface is used instead. The Django primary key remains selected as a connector column for the optimizer.
- Both sync and async paths for `resolve_node` and `resolve_nodes`; `resolve_id_attr` and `resolve_id` are sync.
- `is_type_of` injection is unconditional for every `DjangoType` (Relay-declared or not); consumer-declared `is_type_of` is preserved.
- Models whose primary key is a Django 5.2+ `CompositePrimaryKey` raise `ConfigurationError` at finalization; declare an explicit `id: relay.NodeID[...]` annotation or remove `relay.Node` from `Meta.interfaces` to remediate.
- Non-Relay Strawberry interfaces (`@strawberry.interface`-decorated classes) are accepted without Relay-specific wiring.

## Django model to Strawberry type generation
Status: shipped with alpha constraints.

`DjangoType` reads Django model metadata and builds a Strawberry type. It preserves Django concepts rather than replacing them with a custom data layer.

Shipped today:
- model field selection with `fields` and `exclude`
- default `fields = "__all__"` behavior when neither selector is supplied
- GraphQL type-name and description overrides
- scalar annotation generation
- relation annotation generation
- choice enum generation
- relation resolver generation
- type registry registration
- definition-order-independent relation finalization with `finalize_django_types()`
- abstract/intermediate base support when a subclass has no `Meta`

Current alpha constraints:
- one `DjangoType` per Django model
- manual override validation for relation cardinality is deferred; 0.0.4 trusts relation-field annotations supplied by the consumer

### Definition-order independence
Status: shipped.

`DjangoType` collection is split from Strawberry finalization. Class creation records Django metadata and pending relation targets, while `finalize_django_types()` resolves those pending relations, attaches generated relation resolvers, and decorates each collected type with `strawberry.type`.

Call `finalize_django_types()` once during single-threaded schema setup, after every module that defines `DjangoType` classes has been imported and before `strawberry.Schema(...)` is constructed. Calling it a second time is a no-op. Declaring a new concrete `DjangoType` after finalization raises `ConfigurationError`; tests should use `registry.clear()` and fresh type classes when they need a new registry lifecycle.

Supported relation cycles:
- forward FK and reverse FK
- forward OneToOne and reverse OneToOne
- forward and reverse M2M
- multi-cycle graphs that combine those relation shapes

Unresolved relation targets fail during finalization with an error that names the source model, source field, and target model. The most common cause is that a Python module containing the target `DjangoType` was never imported before finalization.

Supported forward-reference/manual relation shapes in 0.0.4:
- generated relation annotations for target types declared before or after the source type
- same-module string annotations such as `items: list["ItemType"]`
- stringified annotations from `from __future__ import annotations`
- cross-module `Annotated[..., strawberry.lazy("module.path")]` annotations when the consumer wants Strawberry's explicit lazy import path
- annotation-only relation overrides, which keep the generated resolver
- `strawberry.field(resolver=...)` and `@strawberry.field` relation overrides, which keep the consumer resolver

Validation that a manual relation annotation matches the Django relation cardinality is deferred. Manual scalar-field override semantics remain an implementation detail.

## Django field conversion
Status: shipped for common Django fields, deferred for some specialized fields.

Shipped scalar support:
- text-like fields to `str`
- integer and auto fields to `int`
- boolean fields to `bool`
- float fields to `float`
- decimal fields to `decimal.Decimal`
- date, datetime, time, and duration fields to Python-native time types
- UUID fields to `uuid.UUID`
- binary fields to `bytes`
- file and image fields to string path/URL values
- `null=True` to `T | None`
- Relay `GlobalID` mapping for auto IDs when `Meta.interfaces = (relay.Node,)` is declared

Shipped choice support:
- Django choices generate Strawberry enums
- enum objects are cached by `(model, field_name)`
- member names are sanitized from stored database values, not display labels
- grouped choices are rejected clearly

Deferred field conversion:
- plain `BigIntegerField` with JSON-safe `BigInt`
- PostgreSQL `ArrayField`
- `JSONField`
- PostgreSQL `HStoreField`
- stable explicit choice enum naming override

## Relation handling
Status: shipped.

The package maps Django relation cardinality into GraphQL type shape and resolver behavior.

Shipped relation conversion:
- forward `ForeignKey` to target type, nullable when the field is nullable
- forward `OneToOneField` to target type, nullable when the field is nullable
- reverse `ForeignKey` to `list[target_type]`
- many-to-many to `list[target_type]`
- reverse one-to-one to target type or `None`

Shipped resolver behavior:
- many-side resolvers return lists, not Django managers
- reverse one-to-one resolvers return `None` when the related row does not exist
- forward resolvers can return FK-id stubs when the optimizer safely elides a join
- relation access cooperates with Django's prefetch and relation caches
- consumer-authored `strawberry.field` relation overrides are preserved instead of being clobbered by generated resolvers

Consumer overrides are responsible for their own queryset shape. If an override re-shapes a relation queryset with `.order_by(...)`, `.filter(...)`, or similar, it can bypass the framework's prefetched relation cache and introduce per-parent lazy queries.

## Queryset visibility hook
Status: shipped.

If you've used DRF, you already know this hook. `DjangoType.get_queryset(cls, queryset, info, **kwargs)` runs once per type, defaults to identity, and is where permission filters, tenant scoping, soft-delete, staff/public visibility splits, and request-user filters live.

The load-bearing behavior is optimizer cooperation: `has_custom_get_queryset()` reports whether a type or inherited intermediate base overrides the hook, and the optimizer downgrades a JOIN to a `Prefetch` when a target type defines one. Your visibility filter survives relation traversal instead of being bypassed by a raw `select_related` join.

## Automatic ORM optimization
Status: shipped.

`DjangoOptimizerExtension` translates selected GraphQL fields into Django ORM optimization calls. It is opt-in at Strawberry schema construction time.

Shipped behavior:
- root-gated optimization for root resolvers returning Django `QuerySet`s
- passthrough for non-root resolvers and non-`QuerySet` results
- `select_related` for safe single-valued relation chains
- `prefetch_related` for many-side relations
- generated `Prefetch` objects for child querysets
- nested prefetch chains for nested GraphQL selections
- `only` projection for selected scalar columns
- connector-column inclusion so Django can attach joined and prefetched rows without lazy loads
- custom `get_queryset` downgrade from join to `Prefetch`
- async resolver support

## Optimizer cache and planning features
Status: shipped.

The optimizer includes performance and correctness features beyond the baseline N+1 avoidance pattern.

Shipped value:
- **Plan cache.** The same query 10,000×/sec walks the selection tree once, not 10,000 times. Cache keys ignore filter variables that do not affect selection shape, so a query with many filter combinations can still reuse one cached plan.
- **Selection-shape keys.** Cache keys include the selected operation AST, relevant `@skip` / `@include` variables, target model, and root runtime path.
- **Multi-operation safety.** `query A { ... } query B { ... }` in one document never shares a plan across operations.
- **Named-fragment safety.** Directives inside named fragments are tracked into the cache key.
- **Introspection.** `cache_info()` exposes hit, miss, and size counts.
- **Request-scope safety.** Plans that embed request-scoped `get_queryset` results are marked uncacheable.
- **Low per-request overhead.** `DjangoType` precomputes optimizer field metadata at class creation, and cached plans are never mutated while reconciling against a specific queryset.

## Join avoidance and projection
Status: shipped.

The optimizer can avoid unnecessary database work in common relation shapes.

Shipped value:
- **FK-id elision.** `{ category { id } }` reads `category_id` off the parent row — no JOIN, no second query.
- **Safe fallback.** The optimizer falls back to a join when the target selection needs more than the primary key, when the target ID has a custom resolver, or when a target `get_queryset` hook must run.
- **Branch isolation.** Aliases and sibling root fields do not leak elision state into each other.
- **Column projection.** Scalar selections become `only()` projections.
- **Connector preservation.** Projection plans include connector columns for `select_related`, reverse FK, FK/OneToOne, and M2M attachment paths so Django can stitch related rows without lazy loads.

## Optimizer hints
Status: shipped.

Override the optimizer per relation when you know better than it does — skip a relation entirely, force a join, or hand it your own `Prefetch` for filtered children. Configure it in the same `class Meta` you already declared the type with:

```python
from django.db.models import Prefetch
from django_strawberry_framework import DjangoType, OptimizerHint
from myapp.models import Category, Item


class CategoryType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name", "items")
        optimizer_hints = {
            "items": OptimizerHint.prefetch(
                Prefetch("items", queryset=Item.objects.filter(is_published=True)),
            ),
        }
```

Supported hint modes:
- `OptimizerHint.SKIP` — exclude a relation from automatic planning
- `OptimizerHint.select_related()` — force `select_related`
- `OptimizerHint.prefetch_related()` — force `prefetch_related`
- `OptimizerHint.prefetch(Prefetch(...))` — use a consumer-provided `Prefetch` object and stop walking below that relation

Validation:
- hint field names must exist on the model
- hint values must be `OptimizerHint` instances
- invalid hints fail at type creation with `ConfigurationError`

## Optimizer observability and safety
Status: shipped.

The optimizer exposes what it did instead of forcing consumers to infer behavior from SQL logs.

Shipped observability:
- latest plan stashed on `info.context.dst_optimizer_plan`
- FK-id elisions stashed on context
- strictness planned resolver keys stashed on context
- lookup paths stashed on context in strictness mode
- dict and object context support

Shipped N+1 detection:
- `strictness="off"` for silent production default
- `strictness="warn"` for logged warnings
- `strictness="raise"` for fail-fast tests/dev checks
- warnings/errors only when an unplanned relation access would actually lazy-load

Shipped schema audit:
- `DjangoOptimizerExtension.check_schema(schema)` audits schema-reachable `DjangoType`s
- hidden fields and `OptimizerHint.SKIP` fields are ignored
- relation targets without registered `DjangoType`s are reported as warnings

## Queryset diffing and consumer cooperation
Status: shipped.

The optimizer does not assume it owns the queryset. It reconciles framework-generated plans against queryset work the consumer already applied.

Shipped value:
- **Queryset cooperation.** If your resolver already calls `select_related("category")`, the optimizer does not reapply it.
- **Prefetch cooperation.** If your resolver returns `Category.objects.prefetch_related(Prefetch("items", queryset=...))`, the consumer `Prefetch` wins over less-specific automatic work.
- **Subtree-aware reconciliation.** `prefetch_related("items", "items__entries")` cooperates with the optimizer's nested `Prefetch("items", ...)` instead of raising Django's "lookup already seen with a different queryset" error.
- **Plain-string absorption.** Safe consumer string prefetches can be absorbed by richer optimizer `Prefetch` objects.
- **Cache safety.** Cached plans are copied before queryset-specific diffing, so one resolver's queryset shape cannot mutate a plan reused by another request.

## Planned query features
Status: planned.

These are the user-facing features intended to turn the foundation into the full DRF-shaped GraphQL stack.

Planned type/query surfaces:
- `FieldSet` for reusable declarative field selection
- `FilterSet` and individual filters
- `OrderSet` and ordering declarations
- `AggregateSet` with `Sum`, `Count`, `Avg`, `Min`, `Max`, and `GroupBy`
- `DjangoConnectionField` for Relay-style connection queries
- `apply_cascade_permissions`
- per-field permission hooks
- schema export management command
- Django `AppConfig`
- shared queryset utility helpers

Planned integration goals:
- deferred `Meta` keys become accepted only when their subsystem applies them end-to-end
- filters, orders, aggregates, permissions, and connection fields compose with the optimizer
- fakeshop GraphQL schema activates only as its dependencies ship

## Enhancements over strawberry-graphql-django

###  Migration notes
For teams migrating from `strawberry-graphql-django`: keep Strawberry as the engine, but move decorator-heavy Django configuration into nested `Meta` classes. The main differences today are the DRF-shaped type surface, loud rejection of unshipped `Meta` keys, typed optimizer hints, plan caching, FK-id elision, strictness mode, and queryset diffing.

The package keeps Strawberry as the GraphQL engine but improves the Django integration surface and extends optimizer behavior.

API enhancements:
- DRF-shaped nested `Meta` configuration instead of decorator-first configuration
- field selection, future filters, future orders, future aggregates, future permissions, and optimizer hints all belong to one class-local configuration surface
- deferred features fail loudly instead of becoming accepted no-ops
- typed optimizer hints replace mixed strings/dicts/decorator flags

Optimizer performance enhancements:
- cached optimization plans for hot repeated operations
- directive-aware cache keys that ignore variables unrelated to selection shape
- named-fragment directive support in cache keys
- selected-operation hashing for multi-operation documents
- precomputed field metadata instead of per-request `_meta.get_fields()` walks
- FK-id elision for `id`-only forward relation selections
- queryset diffing before applying framework plans
- subtree-aware prefetch reconciliation

Optimizer correctness and debugging enhancements:
- branch-sensitive resolver keys for aliases and sibling root fields
- strictness mode for warning or raising on accidental N+1s
- plan introspection through `info.context`
- schema audit for unregistered relation targets
- cached-plan immutability during queryset-specific diffing
- consumer `Prefetch` objects respected as more specific than automatic plans

Django-stack enhancements:
- visibility filtering remains in `get_queryset`
- query planning uses standard Django ORM primitives
- database routing and relation/prefetch caches are preserved
- future features are shaped around DRF/django-filter conventions rather than Strawberry decorator conventions

## Enhancements over graphene-django

###  Migration notes
For teams migrating from `graphene-django`: keep the familiar Django-shaped `Meta` mental model while moving to Strawberry's modern Python annotations and async-compatible resolver lifecycle. The main differences today are Strawberry enums/types, built-in ORM optimization, and an alpha query-feature surface while filters, orders, aggregates, connections, and permissions are still planned.

The package keeps the Django-shaped API ideas that made graphene-django familiar while moving the GraphQL engine and type system forward.

Engine and typing enhancements:
- Strawberry is the underlying GraphQL engine
- modern Python annotations drive GraphQL type generation
- async-compatible resolver lifecycle
- typed package marker for static-analysis consumers
- no dependency on Graphene's older type system

Django API enhancements:
- DRF-style `Meta` surface stays familiar to graphene-django users
- `ConfigurationError` catches unsupported and misspelled config early
- choice fields generate Strawberry enums while preserving database values
- relation cardinality is inferred from Django model metadata
- type-level `get_queryset` remains the central visibility hook

ORM optimization enhancements:
- built-in N+1 optimizer is part of the shipped foundation
- nested relation selections are optimized automatically
- `only` projection reduces selected columns
- `Prefetch` downgrade preserves permission/visibility filtering across relation boundaries
- strictness mode and plan introspection make query behavior testable

Future migration advantage:
- planned filters, orders, aggregates, connection fields, and permissions target the familiar Django/DRF mental model
- teams can move toward Strawberry without giving up Django-shaped schema declarations

## Deferred and future work
Tracked in the contributor/maintainer board, [`../KANBAN.md`](../KANBAN.md):
- multiple types per model
- consumer override semantics for scalar fields
- stable choice enum naming
- specialized scalar conversions
- filters, orders, aggregates, fieldsets, connections, and permissions
- model-property and cached-property optimizer hints

Dedicated migration guides are tracked in [`../KANBAN.md`](../KANBAN.md#backlog-009--migration-and-adoption-guides) so this file can stay focused on package capabilities.
