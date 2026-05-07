# GOAL

## North star
`django-strawberry-framework` should become the DRF-shaped, `class Meta`-driven Django integration for Strawberry GraphQL.

The goal is to recreate the practical capabilities and ease of implementation proven by `django-graphene-filters`, but on a modern Strawberry foundation:

- keep the model/type/registry ergonomics that made Graphene-Django productive
- preserve the rich feature set from `django-graphene-filters`
- use Strawberry as the GraphQL engine
- borrow the best performance and implementation patterns from `strawberry-graphql-django`
- keep the public API familiar to Django, DRF, and django-filter users

The end result should feel like a modernized Graphene-Django experience for schema authors, but it should behave internally like a Strawberry-native package.

## Source of truth from the current docs
The current docs define the package direction clearly:

- Meta classes, not decorators.
- Strawberry GraphQL on Django.
- Existing querysets remain owned by the application.
- The optimizer cooperates with querysets instead of replacing them.
- Today’s stable early names are `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, and `auto`.
- Planned features include filters, orders, aggregates, connection fields, permissions, cascade permissions, fieldsets, richer `Meta` keys, and schema helpers.
- Definition-order independence is planned so model relation graphs can be expressed naturally.

`GOAL.md` describes the intended destination. `README.md` and `docs/README.md` continue to describe the operational entry point and the current shipped surface.

## Working reference to recreate
The working feature-complete reference is `django-graphene-filters`.

The target is not to copy Graphene internals. The target is to recreate what that package enables:

- `AdvancedDjangoObjectType`-style model-backed nodes
- `AdvancedDjangoFilterConnectionField`-style root and nested connection fields
- declarative filter classes
- declarative order classes
- declarative aggregate classes
- declarative fieldset classes
- search fields
- Relay node support
- row-level queryset permissions
- cascade permissions across related objects
- field-level permissions and custom field resolvers
- nested relation filtering
- nested relation ordering
- nested relation aggregation
- async and sync aggregate paths
- generated input/output types with stable names
- schema shape that remains easy to implement in cookbook-sized projects

The cookbook recipes example in `django-graphene-filters` demonstrates the desired developer experience: define model nodes, attach filter/order/aggregate/fieldset/search metadata in `Meta`, then expose root connection fields with minimal resolver boilerplate.

## Target schema author experience
The desired end-state API should support a shape like this:

```python
class ObjectTypeNode(DjangoType):
    class Meta:
        model = models.ObjectType
        fields = "__all__"
        interfaces = (relay.Node,)
        filterset_class = filters.ObjectTypeFilter
        orderset_class = orders.ObjectTypeOrder
        aggregate_class = aggregates.ObjectTypeAggregate
        fields_class = fieldsets.ObjectTypeFieldSet
        search_fields = ("name", "description")

    @classmethod
    def get_queryset(cls, queryset, info):
        user = getattr(info.context, "user", None)
        if user and user.is_staff:
            return queryset
        return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


@strawberry.type
class Query:
    object_type: ObjectTypeNode = DjangoNodeField(ObjectTypeNode)
    all_object_types: DjangoConnection[ObjectTypeNode] = DjangoConnectionField(ObjectTypeNode)
```

The package should make this shape possible without requiring users to hand-write most resolvers, hand-build input types, or manually optimize nested selections.

## What the end result should enable
### Model-backed type declarations
`DjangoType` should remain the central public type abstraction.

It should support:

- `Meta.model`
- `Meta.fields`
- `Meta.exclude`
- `Meta.interfaces`
- `Meta.filterset_class`
- `Meta.orderset_class`
- `Meta.aggregate_class`
- `Meta.fields_class`
- `Meta.search_fields`
- `Meta.primary` for resolving one primary type when multiple types exist for one model
- `get_queryset` for row-level visibility and queryset customization
- model fields, reverse relations, many-to-many relations, one-to-one relations, and choice enums
- explicit field overrides when automatic conversion is not enough

### Definition-order-independent relation graphs
Schema authors should be able to write natural bidirectional Django model graphs without caring which `DjangoType` class is declared first.

The package should:

- register model-backed types early
- defer unresolved relation targets
- finalize all exposed relations before schema construction
- use concrete target `DjangoType`s by default
- fail loudly when an exposed related model has no registered type
- avoid generic relation placeholders as the default schema shape

### Strawberry-native schema finalization
The package should provide a safe finalization point for rich model schemas.

Finalization should be triggered by package-owned helpers such as:

- `DjangoSchema`
- `DjangoConnectionField`
- `DjangoNodeField`
- an explicit `finalize_django_types()` escape hatch

This keeps the public API simple while avoiding fragile post-schema mutation.

### Connection fields
The package should provide a Strawberry-native equivalent of `AdvancedDjangoFilterConnectionField`.

Connection fields should:

- accept a `DjangoType`
- derive the model and queryset automatically
- apply the type-level `get_queryset`
- expose Relay pagination
- expose `totalCount`
- expose aggregate output when an aggregate class is configured
- accept filter input
- accept ordering input
- accept search input
- cooperate with the optimizer
- work at root fields and nested relation fields

### Filters
The package should recreate the expressive filter system from `django-graphene-filters`.

Filters should support:

- declarative filter classes
- Django lookup expressions
- `and`, `or`, and `not`
- related filters
- lazy related filter class references
- generated Strawberry input types
- stable class-derived generated type names
- custom filter methods
- permission hooks
- queryset scoping for related filters

### Orders
The package should recreate the rich ordering system from `django-graphene-filters`.

Orders should support:

- declarative order classes
- related orders
- lazy related order class references
- generated Strawberry input types
- stable class-derived generated type names
- ascending and descending ordering
- distinct ordering semantics where supported
- nested relation ordering
- permission hooks
- database-aware implementations for PostgreSQL and portable fallbacks where practical

### Aggregates
The package should recreate the aggregate system from `django-graphene-filters`.

Aggregates should support:

- declarative aggregate classes
- related aggregate traversal
- lazy related aggregate class references
- generated Strawberry output types
- stable class-derived generated type names
- common stats such as count, min, max, average, sum, mode, and uniques where appropriate
- custom aggregate methods
- field/stat permission hooks
- selection-set-aware computation
- sync and async computation paths
- computation from the filtered pre-pagination queryset

### Fieldsets and field-level behavior
The package should support fieldset-style customization.

Fieldsets should enable:

- field-level permission checks
- custom field resolvers
- computed fields
- redaction or deny-value behavior where appropriate
- integration with generated model fields instead of after-the-fact schema mutation

### Permissions and cascade visibility
The package should support layered permissions similar to the working Graphene package.

It should enable:

- type-level `get_queryset`
- row-level visibility
- field-level visibility
- filter permission hooks
- order permission hooks
- aggregate permission hooks
- cascade permissions across FK/object relationships
- optional Relay node redaction behavior
- predictable behavior for non-null relation fields

### Optimizer and performance
The optimizer is a core part of the package, not an optional afterthought.

The end state should preserve and expand today’s optimizer behavior:

- root-gated query planning
- `select_related` for forward single relations
- `prefetch_related` for many-side relations
- nested `Prefetch` planning
- `only` projections
- connector-column preservation
- FK-id elision for `related { id }` selections
- compatibility with consumer-shaped querysets
- compatibility with type-level `get_queryset`
- strictness modes for accidental lazy loading
- plan caching where safe

It should also borrow Strawberry-Django performance patterns:

- custom Strawberry field classes carrying Django metadata
- field-level optimizer stores
- connection-aware optimization
- nested connection prefetch handling
- async-safe resolver wrappers
- safe queryset/materialization handling
- aggregate queryset reuse where possible

### Developer ergonomics
The package should minimize boilerplate for the common path.

Users should not need to:

- hand-write list resolvers for every model collection
- hand-build filter input types
- hand-build order input types
- hand-build aggregate output types
- manually add relation resolvers
- manually optimize common nested selections
- learn a decorator-heavy API when they already know Django `Meta` classes

Users should be able to opt into explicit Strawberry fields and resolvers when needed, but the default experience should be declarative and model-driven.

## What to take from each inspiration
### From Graphene-Django
Take:

- model-backed type ergonomics
- registry-based relation resolution concepts
- deferred relation target resolution
- productive schema authoring patterns

Do not take:

- Graphene runtime dependencies
- unmaintained internals
- silent skipping of unresolved fields
- Graphene-specific connection machinery

### From django-graphene-filters
Take:

- the public feature set
- the cookbook-level schema ergonomics
- class-based filter/order/aggregate/fieldset sidecars
- lazy related class references
- generated type factories
- stable generated type naming
- layered permission model
- cascade permissions
- aggregate semantics

Do not take:

- Graphene-specific field mounting
- Graphene-specific input/object type construction
- Graphene-specific resolver signatures

### From strawberry-graphql-django
Take:

- Strawberry-native type processing ideas
- custom field classes
- annotation handling
- model field type resolution patterns
- connection extension patterns
- optimizer-store ideas
- async-safe resolver utilities
- queryset-aware connection behavior

Do not take as the primary user experience:

- decorator-first APIs
- generic relation placeholders as the default rich schema output
- broad internal monkey-patching unless unavoidable
- a schema shape that diverges from the `django-graphene-filters` goal without a clear reason

## Target examples
The examples should eventually prove the goal in two forms.

### Fakeshop
The local fakeshop example should grow from the current list/queryset demonstration into a rich package showcase:

- model nodes for category, property, item, and entry
- bidirectional relations
- connection fields
- nested filters
- nested ordering
- search
- aggregates
- fieldsets
- permissions
- cascade visibility
- optimizer-visible nested selections
- sharded/multi-database stress cases where practical

### Cookbook parity
A Strawberry version of the `django-graphene-filters` cookbook recipes schema should be possible with equivalent capabilities:

- object type nodes
- object nodes
- attribute nodes
- value nodes
- root connection fields
- sidecar filter/order/aggregate/fieldset classes
- search fields
- cascade permissions
- Relay node lookup

## Success criteria
The project is on target when a Django developer can:

1. define rich model-backed GraphQL types with `DjangoType`
2. expose model collections with `DjangoConnectionField`
3. add nested filtering without manual input type construction
4. add nested ordering without manual input type construction
5. add aggregate outputs without manual output type construction
6. add field-level behavior with fieldsets
7. enforce row and cascade permissions declaratively
8. rely on automatic ORM optimization for common nested selections
9. use explicit Strawberry escape hatches for uncommon cases
10. migrate mental models from `django-graphene-filters` without bringing Graphene along

The project misses the goal if users must routinely hand-build the same schema machinery that the package is supposed to generate.

## Non-goals
This package should not become:

- a thin wrapper around `strawberry-graphql-django`
- a direct port of Graphene internals
- a Graphene compatibility runtime
- a decorator-first framework
- an ORM abstraction layer that hides Django querysets
- a system that silently weakens rich relations into generic placeholders

The goal is a Django-native, Strawberry-powered framework that makes rich GraphQL schemas easy to build and efficient to execute.
