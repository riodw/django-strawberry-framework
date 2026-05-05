# Features

`django-strawberry-framework` is a DRF-shaped feature layer for building GraphQL APIs on top of Django, Django's ORM, and Strawberry. This page describes what the package enables. It intentionally mixes shipped and planned features; each section calls out the current status.

This file is the capability catalog. It answers “what can this package do?” and stays separate from operational setup and internal layout details.

Related docs:
- [`../README.md`](../README.md) — install, run, seed example data, test, build, publish, and contributor operations.
- [`README.md`](README.md) — friendly docs landing page for goals, positioning, current surface, and status.
- [`TREE.md`](TREE.md) — detailed architecture and layout reference.
- [`../KANBAN.md`](../KANBAN.md) — active shipped/planned/deferred project board.

## Feature status
- `shipped` — implemented, tested, and available in the current package surface.
- `planned` — committed package direction, not implemented yet.
- `deferred` — reserved for later design or blocked on another feature.
- `alpha constraint` — current behavior that works but is intentionally narrower than the eventual API.

## DRF-shaped GraphQL API
Status: shipped foundation, planned Layer 3 expansion.

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
- `Meta.interfaces`
- `Meta.primary` for multiple GraphQL types over the same Django model
- stable consumer field override mechanisms

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
- abstract/intermediate base support when a subclass has no `Meta`

Current alpha constraints:
- one `DjangoType` per Django model
- relation target types must be registered before relation conversion can target them
- consumer annotation overrides are not a guaranteed public contract yet
- real M2M model coverage is still deferred even though many-side code paths exist

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
- Relay `GlobalID` mapping for auto IDs
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

## Queryset visibility hook
Status: shipped.

`DjangoType.get_queryset(cls, queryset, info, **kwargs)` is the central hook for type-level visibility and request-scoped queryset shaping.

Common uses:
- permission filtering
- tenancy filtering
- soft-delete filtering
- staff/public visibility splits
- request-user scoping
- future connection and filtering integration

The default implementation is identity. `has_custom_get_queryset()` reports whether a type or inherited intermediate base overrides it. The optimizer uses that signal so a relation with custom visibility is fetched through `Prefetch` instead of a raw SQL join that would bypass the target type's queryset filter.

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

Shipped features:
- AST-keyed plan cache for repeated GraphQL operations
- cache keys based on selected operation AST, directive variables, target model, and root runtime path
- directive-variable extraction limited to `@skip` and `@include`
- named-fragment directive support
- multi-operation document safety
- `cache_info()` for hit/miss/size introspection
- uncacheable plans when request-scoped `get_queryset` results are embedded
- precomputed optimizer field metadata on `DjangoType` classes
- cached-plan safety during queryset diffing

## Join avoidance and projection
Status: shipped.

The optimizer can avoid unnecessary database work in common relation shapes.

Shipped features:
- FK-id elision for selections like `{ relation { id } }` when the parent row already has `<field>_id`
- fallback to a join when the target selection needs more than the primary key
- fallback to a join when a custom ID resolver or custom target `get_queryset` makes elision unsafe
- branch-sensitive elision state so aliases and sibling root fields do not leak behavior
- `only` projection for scalar selections
- connector-column injection for `select_related`, reverse FK, FK/OneToOne, and M2M attachment paths

## Optimizer hints
Status: shipped.

`Meta.optimizer_hints` lets a type override automatic relation planning per field.

Supported hints:
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

Shipped behavior:
- exact `select_related` entries already on the queryset are dropped from the optimizer delta
- existing `prefetch_related` lookups are compared by lookup path
- consumer `Prefetch` objects win over less-specific optimizer work
- safe consumer plain-string prefetches can be absorbed by richer optimizer `Prefetch` objects
- cached plans are never mutated while diffing against a specific queryset

## Planned Layer 3 features
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
- Layer 3 `Meta` keys become accepted only when their subsystem applies them end-to-end
- filters, orders, aggregates, permissions, and connection fields compose with the optimizer
- fakeshop GraphQL schema activates only as its dependencies ship

## Enhancements over strawberry-graphql-django
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
Tracked in [`../KANBAN.md`](../KANBAN.md):
- definition-order independence
- multiple types per model
- consumer override semantics
- stable choice enum naming
- Relay interfaces and `GlobalID`
- specialized scalar conversions
- real M2M coverage
- Layer 3 filters, orders, aggregates, fieldsets, connections, and permissions
- model-property and cached-property optimizer hints

Migration guides will be split into dedicated docs so this file can stay focused on package capabilities.
