# Rich schema architecture

## Purpose
This spec defines the long-term architecture for building a Strawberry-based package that can expose the same practical schema shape as the feature-complete Graphene reference implementation in `django-graphene-filters`, while avoiding the parts of Graphene-Django that are old, unmaintained, and less aligned with Strawberry's execution model.

The narrow definition-order problem is documented in `docs/spec-definition_order_independence.md`. This document is broader. It answers:

- what to take from `django-graphene-filters`
- what to take from Graphene-Django
- what to take from `strawberry-graphql-django`
- what to scrap
- how to combine the strongest parts into one system that fits this package's DRF-shaped API

## Target outcome
The target user-facing schema should feel like the cookbook schema from the Graphene package:

- `file:///Users/riordenweber/projects/django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py#L17`
- `file:///Users/riordenweber/projects/django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py#L42`
- `file:///Users/riordenweber/projects/django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py#L69`
- `file:///Users/riordenweber/projects/django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py#L96`
- `file:///Users/riordenweber/projects/django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py#L131`

The Graphene reference exposes four model nodes, each with:

- `fields = "__all__"`
- `interfaces = (Node,)`
- `filterset_class`
- `orderset_class`
- `aggregate_class`
- `fields_class`
- `search_fields`
- row-level `get_queryset`
- `apply_cascade_permissions`
- root `AdvancedDjangoFilterConnectionField(...)`

The Strawberry version should preserve that high-level shape:

```python
class ObjectTypeNode(DjangoType, relay.Node):
    class Meta:
        model = models.ObjectType
        interfaces = (relay.Node,)
        fields = "__all__"
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

The exact class names may change, but the architectural goal is the same:

- type classes stay `class Meta` driven
- connection fields bind filtering, ordering, search, aggregation, pagination, optimization, and permission behavior
- related object fields are rich concrete types, not generic placeholders
- bidirectional model graphs work naturally
- the optimizer stays first-class

## Current local package baseline
Current package source:

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/walker.py`

Important current functions:

- `DjangoType.__init_subclass__`: `django_strawberry_framework/types/base.py:80`
- `_validate_meta`: `django_strawberry_framework/types/base.py:238`
- `_select_fields`: `django_strawberry_framework/types/base.py:314`
- `_build_annotations`: `django_strawberry_framework/types/base.py:377`
- `convert_relation`: `django_strawberry_framework/types/converters.py:211`
- `_make_relation_resolver`: `django_strawberry_framework/types/resolvers.py:111`
- `_attach_relation_resolvers`: `django_strawberry_framework/types/resolvers.py:168`
- `TypeRegistry.lazy_ref`: `django_strawberry_framework/registry.py:93`
- `DjangoOptimizerExtension`: `django_strawberry_framework/optimizer/extension.py:254`
- `DjangoOptimizerExtension.check_schema`: `django_strawberry_framework/optimizer/extension.py:442`
- `walker.plan_relation`: `django_strawberry_framework/optimizer/walker.py:36`
- `walker._plan_prefetch_relation`: `django_strawberry_framework/optimizer/walker.py:216`

Current behavior is simple and useful, but too eager:

1. `DjangoType.__init_subclass__` validates `Meta`.
2. `_select_fields` chooses Django fields.
3. `_build_annotations` converts every selected field immediately.
4. `convert_relation` immediately looks up the target model in the registry.
5. unresolved target types raise immediately.
6. the class is registered.
7. relation resolvers are attached.
8. `strawberry.type(cls)` finalizes the type.

This hardwires type conversion and Strawberry finalization into one class-creation moment. That makes bidirectional model graphs impossible without omitting one side of a relation.

## Reference architecture: django-graphene-filters
`django-graphene-filters` is the feature-complete proof that the desired product surface works.

Important source references:

- `AdvancedDjangoObjectType`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/object_type.py#L119`
- `AdvancedDjangoObjectType.__init_subclass_with_meta__`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/object_type.py#L156`
- `AdvancedDjangoObjectType.get_node`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/object_type.py#L251`
- `_wrap_field_resolvers`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/object_type.py#L363`
- `_convert_field_to_list_or_connection`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/object_type.py#L459`
- `AdvancedDjangoFilterConnectionField`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/connection_field.py#L67`
- `AdvancedDjangoFilterConnectionField.args`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/connection_field.py#L156`
- `AdvancedDjangoFilterConnectionField.filterset_class`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/connection_field.py#L169`
- `AdvancedDjangoFilterConnectionField.filtering_args`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/connection_field.py#L188`
- `AdvancedDjangoFilterConnectionField.resolve_queryset`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/connection_field.py#L257`
- `AdvancedDjangoFilterConnectionField._extract_aggregate_selection`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/connection_field.py#L362`
- `ClassBasedTypeNameMixin`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/mixins.py#L27`
- `LazyRelatedClassMixin`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/mixins.py#L55`
- `LazyRelatedClassMixin.resolve_lazy_class`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/mixins.py#L61`
- `FilterArgumentsFactory`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/filter_arguments_factory.py#L36`
- `FilterArgumentsFactory._ensure_built`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/filter_arguments_factory.py#L98`
- `OrderArgumentsFactory._ensure_built`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/order_arguments_factory.py#L78`
- `AggregateArgumentsFactory._ensure_built`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/aggregate_arguments_factory.py#L89`
- `AdvancedAggregateSet.compute`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/aggregateset.py#L440`
- `AdvancedAggregateSet.acompute`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/aggregateset.py#L474`
- `AdvancedFieldSet`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/fieldset.py#L80`
- `apply_cascade_permissions`: `file:///Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/permissions.py#L19`

### What to take from django-graphene-filters
Take the product semantics almost wholesale.

#### Take the public type shape
`AdvancedDjangoObjectType` proves that one model-backed node can own these `Meta` keys:

- `filterset_class`
- `orderset_class`
- `aggregate_class`
- `fields_class`
- `search_fields`
- `interfaces`

For this package, the equivalent is `DjangoType.Meta`.

The names should stay close to the Graphene package because this is a migration path from the working implementation. Renaming them to match Strawberry-Django's decorator parameters would make this package less DRF-shaped and less compatible with the proven schema.

#### Take the connection-field integration point
`AdvancedDjangoFilterConnectionField` is the correct architectural hub. It binds:

- the target node type
- filter input type
- order input type
- search argument
- aggregate output type
- queryset resolution
- permission-aware filtering
- connection result shape

The Strawberry version should have a `DjangoConnectionField` that plays the same role. It should not force users to write manual list resolvers for common model lists.

#### Take lazy related class references
`LazyRelatedClassMixin` solves circular filter/order/aggregate class graphs without depending on Python declaration order.

Take the concept and adapt it:

- accept class objects
- accept absolute import strings
- accept same-module class-name strings
- accept zero-argument callables
- bind each related declaration to its owning class
- resolve only when the factory/finalizer needs the target

This pattern is separate from model relation type finalization. It should be reused for:

- `RelatedFilter`
- `RelatedOrder`
- `RelatedAggregate`
- future related fieldset or permission declarations if needed

#### Take BFS graph factories
The Graphene package's filter/order/aggregate factories do not recursively inline related types forever. They BFS-build each reachable class once, cache by stable class-derived name, and emit lazy references for edges.

Take that architecture.

For Strawberry:

- build input and output types with `strawberry.input`, `strawberry.type`, or `strawberry.tools.create_type`
- cache by generated GraphQL type name
- detect name collisions
- use Strawberry annotations/lazy references rather than Graphene lambdas where possible
- keep BFS cycle protection

#### Take class-based generated type naming
The Graphene package moved to class-based naming to prevent duplicate client schema types.

Take this as a core invariant:

- `ObjectFilter` -> `ObjectFilterInputType`
- `ObjectFilter.name` -> `ObjectFilterNameFilterInputType`
- `ObjectOrder` -> `ObjectOrderInputType`
- `ObjectAggregate` -> `ObjectAggregateType`

Do not derive generated type names from traversal path. Path-derived names explode client schema caches and make shared related types look different depending on where they were reached.

#### Take the layered permission model
The working package distinguishes:

- row-level visibility: `get_queryset`
- cascading FK visibility: `apply_cascade_permissions`
- sentinel redaction nodes: `get_node` and `isRedacted`
- filter permission hooks
- order permission hooks
- aggregate permission hooks
- field-level visibility/content hooks

Take the layered model. Do not collapse all permission behavior into Strawberry's `permission_classes`; those are useful but not enough for DRF-style row, field, filter, order, aggregate, and cascade semantics.

#### Take aggregate semantics
`AdvancedAggregateSet` is a good design:

- declarative `Meta.fields`
- stat validation at class creation
- custom stat output types
- `compute_<field>_<stat>` overrides
- `check_<field>_permission`
- `check_<field>_<stat>_permission`
- sync and async compute paths
- selection-set-aware computation
- related aggregate traversal

Take the semantics. Implement the output type generation in Strawberry-native terms.

#### Take `fields_class`
`AdvancedFieldSet` is small but powerful:

- `check_<field>_permission`
- `resolve_<field>`
- computed field declarations
- wrapper order: check, custom resolve, default resolve

Take the behavior, but implement it as part of a custom Strawberry field class rather than mutating Graphene fields.

### What to scrap from django-graphene-filters
Do not port Graphene-specific internals.

Scrap:

- `graphene.Dynamic`
- Graphene's field mounting lifecycle
- Graphene `ConnectionField` internals
- Graphene `ObjectType` and `InputObjectType` dynamic class construction
- Graphene resolver signatures
- Graphene registry behavior that can silently skip missing dynamic fields

Keep:

- the API shape
- the feature semantics
- lazy graph-building principles
- naming and collision rules
- permission layering

## Graphene-Django: take the idea, not the engine
Graphene-Django solves bidirectional object relations with `Dynamic` relation fields. That is valuable evidence, but Graphene-Django itself is not the target runtime.

Take:

- relation fields can be represented as pending declarations at type creation time
- a later schema/finalization phase can resolve targets after all classes are imported
- unresolved targets should be explicit finalization errors

Do not take:

- skip missing fields silently
- Graphene's old schema builder
- Graphene's global dynamic field model
- runtime coupling to an unmaintained stack

For this package, the equivalent is not `Dynamic`. The equivalent is a package-owned pending relation registry plus a Strawberry-native finalization pass.

## Strawberry-Django: functions and patterns to borrow
`strawberry-graphql-django` is the modern Strawberry-native reference. It does not have the same product goal as this package, but it has many implementation techniques we should borrow.

Important source references:

- `_process_type`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py#L73`
- `StrawberryDjangoDefinition`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py#L425`
- `type`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py#L448`
- `interface`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py#L520`
- `input`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py#L565`
- `partial`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py#L616`
- `StrawberryDjangoFieldBase`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/base.py#L50`
- `StrawberryDjangoFieldBase.resolve_type`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/base.py#L185`
- `StrawberryDjangoFieldBase.get_result`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/base.py#L260`
- `StrawberryDjangoFieldBase.get_queryset`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/base.py#L263`
- `DjangoModelType`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py#L73`
- `field_type_map`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py#L229`
- `resolve_model_field_type`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py#L439`
- `resolve_model_field_name`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py#L569`
- `get_model_field`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py#L584`
- `is_optional`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py#L607`
- `StrawberryDjangoField`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/field.py#L97`
- `StrawberryDjangoField.get_result`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/field.py#L201`
- `StrawberryDjangoField.get_queryset`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/field.py#L358`
- `StrawberryDjangoConnectionExtension`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/field.py#L424`
- `field`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/field.py#L689`
- `connection`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/field.py#L895`
- `get_strawberry_annotations`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/utils/typing.py#L105`
- `unwrap_type`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/utils/typing.py#L137`
- `get_type_from_lazy_annotation`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/utils/typing.py#L149`
- `OptimizerStore`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py#L136`
- `OptimizerStore.with_hints`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py#L184`
- `OptimizerStore.with_prefix`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py#L238`
- `OptimizerStore.apply`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py#L275`
- `_get_prefetch_queryset`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py#L528`
- `_optimize_prefetch_queryset`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py#L571`
- `_must_use_prefetch_related`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py#L833`
- `optimize`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py#L1580`
- `DjangoOptimizerExtension`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py#L1694`
- `DjangoOptimizerExtension.optimize`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py#L1805`
- `process_filters`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/filters.py#L164`
- `filters.apply`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/filters.py#L287`
- `process_order`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/ordering.py#L107`
- `ordering.apply`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/ordering.py#L169`
- `order_type`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/ordering.py#L388`
- `run_type_get_queryset`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/queryset.py#L34`
- `django_resolver`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/resolvers.py#L65`
- `django_getattr`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/resolvers.py#L158`
- `DjangoListConnection`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/list_connection.py#L59`
- `DjangoListConnection.resolve_connection`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/list_connection.py#L78`

### Borrow `_process_type`, but adapt the lifecycle
`_process_type` has the right shape for a Strawberry-native type finalization function:

1. inspect model fields
2. merge existing annotations
3. inject `strawberry.auto`
4. create a definition object
5. call `strawberry.type`
6. post-process `type_def.fields`
7. replace plain Strawberry fields with Django-aware fields
8. attach origin metadata

This package should borrow that lifecycle, but not the decorator API.

Recommended adaptation:

- split current `DjangoType.__init_subclass__` into collection and finalization
- collect `DjangoTypeDefinition` during class creation
- pre-register model-to-type immediately
- defer `strawberry.type` until relation targets are known
- after `strawberry.type`, post-process fields into package-owned `DjangoModelField` objects

This gives us Strawberry-Django's stable field metadata model without adopting its decorator-first public API.

### Borrow `StrawberryDjangoDefinition`
Create a package equivalent:

```python
@dataclass
class DjangoTypeDefinition:
    origin: type
    model: type[models.Model]
    fields: tuple[str, ...] | Literal["__all__"]
    exclude: tuple[str, ...] | None
    filterset_class: type | LazyClassRef | None
    orderset_class: type | LazyClassRef | None
    aggregate_class: type | LazyClassRef | None
    fields_class: type | LazyClassRef | None
    search_fields: tuple[str, ...]
    interfaces: tuple[type, ...]
    optimizer_hints: dict[str, OptimizerHint]
    finalized: bool = False
```

Store it on the class as `__django_strawberry_definition__`. This mirrors Strawberry-Django's `__strawberry_django_definition__`, but keeps this package's namespace distinct.

Benefits:

- one canonical place for model/type metadata
- optimizer can read from the definition rather than scattered class attrs
- connection fields can resolve filter/order/aggregate defaults from the node type
- schema audit can report exact unfinalized or unresolved fields

### Borrow `get_strawberry_annotations`
`get_strawberry_annotations` preserves annotation namespaces across inheritance and postponed annotations.

Borrow this function closely.

Why:

- definition-order independence often intersects with postponed annotations
- user-declared fields may reference types declared later
- a future override system needs to distinguish package-generated fields from consumer-authored annotations
- namespace-aware `StrawberryAnnotation` avoids fragile `eval` behavior

Adaptation:

- put it in `django_strawberry_framework/utils/typing.py`
- use it during finalization, not during eager class creation
- use it to preserve consumer fields before injecting generated annotations

### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField`
This is one of the most important Strawberry-Django pieces.

The current package attaches relation resolvers as `strawberry.field(resolver=...)`. That works today, but it will become limiting once fields need:

- Django field names distinct from Python names
- relation metadata
- origin type metadata
- filter/order/pagination arguments
- field-level permissions
- optimizer hints
- get_queryset hooks
- async-safe queryset handling
- connection extensions

Borrow the custom field-class pattern.

Create a package-owned field class, for example:

```python
class DjangoModelField(StrawberryField):
    django_name: str | None
    origin_django_type: DjangoTypeDefinition | None
    django_model: type[models.Model] | None
    model_field: models.Field | ForeignObjectRel | None
    is_relation: bool
    relation_kind: Literal["forward_single", "many", "reverse_one_to_one"] | None  # mirrors utils.relations.RelationKind
    target_model: type[models.Model] | None
    target_type: type | None
    store: OptimizerStore
```

Borrow these behaviors:

- `resolve_type` from `StrawberryDjangoFieldBase.resolve_type`
- `django_type` / `django_model` computed properties
- `get_result` routing from `StrawberryDjangoField.get_result`
- `get_queryset` chaining from `StrawberryDjangoField.get_queryset`
- extension-driven argument injection from `StrawberryDjangoConnectionExtension`

This lets field behavior live with fields instead of being scattered across:

- generated annotations
- class attributes
- external resolver functions
- optimizer maps

### Borrow `resolve_type`, but change relation fallback behavior
`StrawberryDjangoFieldBase.resolve_type` handles `strawberry.auto`, `Any`, and unresolved annotations by calling `resolve_model_field_type`.

Borrow that hook, but change relation semantics.

Strawberry-Django's default relation fallback maps:

- `ForeignKey` -> `DjangoModelType`
- reverse FK -> `list[DjangoModelType]`

That is useful for Strawberry-Django's goals, but it is too weak for this package. This package should resolve relations to concrete registered `DjangoType`s whenever the relation field is exposed.

Recommended behavior:

1. scalar fields may use a local `resolve_model_field_type`-style map
2. relation fields should first ask the package registry for the concrete target type
3. if the target is missing during collection, create a pending relation record
4. if the target is still missing during finalization, raise `ConfigurationError`
5. do not expose `DjangoModelType` as the default public relation shape

Keep `DjangoModelType` only as an internal or explicitly requested fallback, not as the default for `Meta.fields = "__all__"`.

### Borrow `resolve_model_field_type`, `get_model_field`, `resolve_model_field_name`, and `is_optional`
These functions encode many Django edge cases:

- reverse relations are not always found by `model._meta.get_field(name)`
- FK id fields may use `attname`
- input/filter contexts have different nullability rules
- reverse one-to-one nullability is special
- file/image/JSON/GIS/array/generated fields need type maps

Borrow the shape, but align it with this package's public contract.

Recommended adaptation:

- keep this package's existing `SCALAR_MAP` as the initial supported set
- add Strawberry-Django's richer scalar coverage over time
- use `get_model_field` logic for reverse relation lookup
- use `resolve_model_field_name` to normalize Django names
- use `is_optional` to centralize nullability
- keep relation mapping concrete, not generic

### Borrow `field` and `connection` as implementation patterns
Do not expose Strawberry-Django's decorator-first API as the main API, but borrow the implementation pattern:

- `field(...)` creates a Django-aware field object
- `connection(...)` creates a Django-aware field with a connection extension
- extensions add arguments and resolve pagination

This package can expose:

- `DjangoField(...)` for explicit advanced fields
- `DjangoConnectionField(...)` for root and nested connections
- `DjangoNodeField(...)` for Relay node lookup

Internally those should use a custom `DjangoModelField`.

### Borrow `DjangoListConnection`
`DjangoListConnection` has a Strawberry-native connection shape with `total_count`, queryset awareness, and optimized connection resolution.

Borrow the concept.

But the target connection must also support `aggregates`, matching the Graphene reference.

Recommended shape:

```python
@strawberry.type
class DjangoConnection(relay.ListConnection[NodeType]):
    total_count: int | None
    aggregates: AggregateType | None
```

`aggregates` should compute from the filtered, searched, ordered queryset before pagination, mirroring `django-graphene-filters`.

### Borrow `OptimizerStore`, but keep the current optimizer's strengths
The current package already has an optimizer that:

- root-gates query optimization
- plans `select_related`, `prefetch_related`, and `only`
- preserves consumer queryset shaping
- downgrades to `Prefetch` when target types override `get_queryset`
- supports strictness warnings/errors
- supports plan caching

Keep that.

Borrow from Strawberry-Django:

- `OptimizerStore` as field-level optimization metadata
- `with_hints`, `with_prefix`, and `apply`
- callable prefetch/annotate hints scoped to `Info`
- `_must_use_prefetch_related` logic for custom queryset/polymorphic/annotation cases
- `_get_prefetch_queryset` and `_optimize_prefetch_queryset` concepts for nested connection prefetches
- connection-aware optimization for `edges.node` and total count

Do not blindly copy Strawberry-Django's optimizer wholesale. This package's current optimizer is simpler and tuned to the package's generated `DjangoType` maps. Instead, add the missing field-store and nested connection lessons.

### Borrow `django_resolver` and `django_getattr`
`django_resolver` handles sync/async ORM access safely. `django_getattr` centralizes:

- callable return values
- `BaseManager` to queryset conversion
- queryset evaluation hooks
- reverse one-to-one `DoesNotExist` -> `None`
- async contexts

Borrow these patterns for `DjangoModelField.get_result`.

This will be more robust than custom per-cardinality relation resolvers once fields also need filtering, ordering, pagination, permissions, and optimizer hooks.

### Borrow filter/order processing selectively
Strawberry-Django's `process_filters`, `filters.apply`, `process_order`, and `ordering.apply` are useful implementation references, but the public schema shape should follow `django-graphene-filters`.

Borrow:

- recursively walking input objects
- producing Django `Q` objects
- resolving enum/global-id values
- delegating to custom resolver methods
- applying nested order prefixes

Do not adopt:

- the exact `filters` argument name if the target Graphene-compatible shape uses `filter`
- the exact Strawberry-Django filter input naming if it conflicts with class-based naming
- generic relation filter inputs as the primary API

## What to scrap from Strawberry-Django
Do not copy Strawberry-Django as a whole. It solves a different product problem.

Scrap or avoid as default:

- decorator-first public API as the primary surface
- generic `DjangoModelType` relation output for rich model schemas
- generic `filters`/`order` shape when this package wants `filter`/`orderBy`
- implicit relation fallback that silently gives weaker nested query capabilities
- broad monkey-patching like `QuerySet._clone` unless there is no safer alternative
- deprecated filter APIs
- mutation/input complexity until the read/query surface is stable

Keep as references:

- field-class lifecycle
- annotation namespace preservation
- Strawberry-native connection extensions
- optimizer stores and nested prefetch handling
- sync/async resolver wrappers

## Recommended combined architecture
The best system is a hybrid:

1. Use the `django-graphene-filters` product model.
2. Use Graphene-Django's deferred relation insight.
3. Use Strawberry-Django's field/type/finalization mechanics.
4. Keep this package's current optimizer and evolve it with Strawberry-Django field stores.

### Layer 1: Type collection
`DjangoType.__init_subclass__` should stop doing full conversion and finalization immediately.

New class-creation responsibilities:

1. detect concrete subclasses
2. validate supported `Meta` keys
3. select fields
4. build `DjangoTypeDefinition`
5. register model -> class early
6. record field metadata
7. record pending relation metadata
8. mark the class as unfinalized

Do not call `strawberry.type(cls)` until finalization.

The registry should distinguish:

- registered but unfinalized types
- finalized types
- pending relation fields
- unresolved target errors

### Layer 2: Pending relation registry
Add a pending relation record:

```python
@dataclass
class PendingRelation:
    source_type: type[DjangoType]
    source_model: type[models.Model]
    field_name: str
    django_field: models.Field | ForeignObjectRel
    related_model: type[models.Model]
    relation_kind: Literal["forward_single", "many", "reverse_one_to_one"]  # mirrors utils.relations.RelationKind
    nullable: bool
```

During collection:

- scalar fields are known immediately
- relation fields with registered target types can be resolved immediately
- relation fields without registered target types become pending

During finalization:

- all pending relation targets are resolved
- unresolved exposed targets raise `ConfigurationError`
- relation annotations become concrete target types
- many-side relations become `list[target_type]`
- reverse one-to-one becomes `target_type | None`
- nullable forward relations become `target_type | None`

This preserves the Graphene benefit without Graphene internals.

### Layer 3: Finalization trigger
The package needs an explicit, Strawberry-safe finalization point.

Preferred triggers:

1. `DjangoConnectionField(Type)` calls `finalize_django_types()` before it returns a field.
2. `DjangoNodeField(Type)` calls `finalize_django_types()` before it returns a field.
3. `DjangoSchema(...)` calls `finalize_django_types()` before constructing `strawberry.Schema`.
4. `finalize_django_types()` remains public for advanced users.

Why this combination:

- cookbook-style schemas define node types first and root fields after, so `DjangoConnectionField` can finalize naturally
- direct manual schemas can use `DjangoSchema`
- advanced users can call the finalizer explicitly in tests or unusual import layouts
- finalization happens before Strawberry schema conversion, avoiding fragile post-schema patching

Avoid relying only on a schema extension. Extensions run too late; the schema is already built.

### Layer 4: Strawberry-native field class
Create `DjangoModelField`, based on Strawberry-Django's `StrawberryDjangoField`.

Responsibilities:

- store `django_name`
- store origin `DjangoTypeDefinition`
- store relation metadata
- resolve `strawberry.auto` and pending annotations
- apply row-level `get_queryset`
- apply field-level `fields_class`
- route relation access safely
- expose filtering, ordering, pagination, and connection arguments through extensions
- provide optimizer stores/hints

This should eventually replace `_attach_relation_resolvers` as the primary relation resolution mechanism.

Transition path:

- keep `_attach_relation_resolvers` for the 0.0.x list-based schema
- introduce `DjangoModelField` for new connection/root-field features
- migrate generated relation fields to `DjangoModelField`
- delete per-relation resolver generation once the field class covers all cardinalities

### Layer 5: Connection field
Implement `DjangoConnectionField`.

It should:

1. accept a target `DjangoType`
2. finalize pending types
3. derive model and default queryset from the target type
4. read default `filterset_class`, `orderset_class`, `aggregate_class`, and `search_fields` from the target definition
5. add `filter`, `orderBy`, and `search` arguments
6. apply row-level `get_queryset`
7. apply filters
8. apply search
9. apply ordering
10. compute or defer aggregates from the filtered pre-pagination queryset
11. paginate as a Relay connection
12. expose `aggregates` and `totalCount`
13. cooperate with `DjangoOptimizerExtension`

This is the Strawberry equivalent of `AdvancedDjangoFilterConnectionField`.

### Layer 6: Filter system
Use `django-graphene-filters` semantics, Strawberry implementation.

Public API:

```python
class ObjectFilter(AdvancedFilterSet):
    object_type = RelatedFilter(ObjectTypeFilter, field_name="object_type")
    values = RelatedFilter("ValueFilter", field_name="values")

    class Meta:
        model = models.Object
        filter_fields = {
            "name": "__all__",
            "description": ["exact", "icontains"],
        }
```

Implementation:

- `FilterSetMetaclass` collects `RelatedFilter`
- `RelatedFilter` uses lazy class refs
- `FilterArgumentsFactory` BFS-builds Strawberry input types
- generated types use class-based names
- input data converts to Django `Q`
- permission hooks run before applying filters
- explicit related queryset constraints act as scope boundaries

Borrow from Strawberry-Django:

- `process_filters` recursive input walking
- `resolve_value` enum/global-id handling
- `filter_field` custom resolver validation patterns

Do not adopt Strawberry-Django's generic relation fallback as the main shape.

### Layer 7: Order system
Use `django-graphene-filters` semantics:

- `AdvancedOrderSet`
- `RelatedOrder`
- ordered list of order directives
- `ASC`, `DESC`, `ASC_DISTINCT`, `DESC_DISTINCT`
- nested relation ordering
- permission hooks
- PostgreSQL `DISTINCT ON` plus window-function fallback

Borrow from Strawberry-Django:

- recursive `process_order` shape
- `Ordering` enum implementation details for null ordering if useful
- input object traversal and prefix handling

Prefer the Graphene package's list-of-order-objects semantics if matching existing clients matters.

### Layer 8: Aggregate system
Use `django-graphene-filters` aggregate semantics.

Public API:

```python
class ObjectAggregate(AdvancedAggregateSet):
    object_type = RelatedAggregate("ObjectTypeAggregate", field_name="object_type")
    values = RelatedAggregate("ValueAggregate", field_name="object")

    class Meta:
        model = models.Object
        fields = {
            "name": ["count", "min", "max", "mode", "uniques"],
        }
```

Implementation:

- metaclass validates fields/stats
- output type factory BFS-builds Strawberry object types
- class-based names
- selection-set-aware `compute`
- async `acompute`
- related aggregate traversal
- aggregate field attached to connection type

Borrow from Strawberry-Django:

- `DjangoListConnection` as the connection base
- resolver/async wrapping
- optimizer-compatible queryset handling

### Layer 9: FieldSet and field-level permissions
Use `AdvancedFieldSet` semantics.

Implementation should live in `DjangoModelField.get_result`, not as an after-the-fact Graphene field mutation.

Resolver order:

1. row already passed `get_queryset`
2. field permission check
3. field custom resolver
4. default Django attribute/relation resolver
5. type-appropriate deny value when needed

Keep computed fields support.

### Layer 10: Row permissions and cascade visibility
Keep the Graphene package's row/cascade model.

Implement:

- `DjangoType.get_queryset`
- `apply_cascade_permissions`
- optional sentinel redaction support for Relay node types
- `is_redacted` generated field or mixin

Open design point:

- Sentinel nodes are useful for non-null FK fields but can surprise clients.
- Cascade filtering is cleaner when parent rows should disappear.
- The package should support both, but docs should recommend cascade filtering for strict privacy.

### Layer 11: Optimizer integration
The optimizer must remain a first-class part of this package.

Keep current features:

- root-gated optimization
- plan caching
- strictness modes
- FK-id elision
- existing queryset reconciliation
- `get_queryset`-aware prefetch downgrade

Add Strawberry-Django lessons:

- field-level `OptimizerStore`
- callable prefetch/annotate hints
- nested connection prefetch handling
- connection-aware `edges.node` traversal
- aggregate pre-pagination query reuse
- opt-out per field

Do not make optimization depend on Graphene-style connection internals.

## Definition-order strategy in this architecture
The best approach is neither pure Graphene nor pure Strawberry-Django.

Use:

- Graphene's deferred concrete relation target idea
- Strawberry-Django's custom field/finalization mechanics
- package-owned explicit finalization

Recommended finalization algorithm:

1. collect all registered `DjangoTypeDefinition`s
2. detect duplicate model registrations
3. resolve lazy filter/order/aggregate/fieldset class refs
4. resolve every pending relation target model to a registered type
5. synthesize annotations for every unfinalized type
6. attach `DjangoModelField` instances for generated fields
7. apply interfaces
8. call `strawberry.type`
9. post-process `type_def.fields` and attach origin metadata
10. run schema-shape validation

Important invariant:

- unresolved exposed relation fields are errors, not skipped fields

This differs from Graphene-Django and is intentional.

## Why not use generic relation fallback by default?
Generic fallback is attractive because it avoids cycles, but it does not meet this package's goal.

If `Item.category` becomes `DjangoModelType`, users cannot naturally query:

```graphql
{
  allItems {
    category {
      name
      description
      items {
        name
      }
    }
  }
}
```

That is the core value of the package. The default must be concrete related types.

### Status: deferred design idea, no card yet
A `Meta.unresolved_relations` opt-in (with values such as `"generic"` or `"error"`) is **not** part of any accepted card and **not** part of the foundation slice. The 0.0.4 contract from `docs/spec-foundation.md` is **error-only**: every exposed relation field must resolve to a concrete registered `DjangoType` at finalization or `finalize_django_types()` raises with the unresolved-targets format.

If a real project surfaces a use case where error-only is too strict, this becomes a future card under `KANBAN.md` with its own design doc — not an assumption baked into Layer 3 work. Readers should not design Layer 3 subsystems against `Meta.unresolved_relations` until that card is accepted.

## Proposed module layout
Future modules. Layer 3 subsystems use the **package** layout from `KANBAN.md` and `docs/TREE.md` (e.g., `filters/` not `filters.py`); the package layout is canonical because it determines import paths, public-surface promotion, and test-tree mirroring. The flat-module names in older drafts of this spec have been migrated to packages below.

- `django_strawberry_framework/types/definition.py`
- `django_strawberry_framework/types/fields.py`
- `django_strawberry_framework/types/finalizer.py`
- `django_strawberry_framework/types/relations.py`
- `django_strawberry_framework/schema.py`
- `django_strawberry_framework/relay.py`
- `django_strawberry_framework/connection.py`
- `django_strawberry_framework/filters/` — `base.py` (Filter classes), `sets.py` (FilterSet), `factories.py` (filterset + GraphQL-arguments factories), `inputs.py` (input types + adapters)
- `django_strawberry_framework/orders/` — `base.py` (Order classes), `sets.py` (OrderSet), `factories.py` (GraphQL-arguments factory)
- `django_strawberry_framework/aggregates/` — `base.py` (Sum/Count/Avg/Min/Max/GroupBy result types), `sets.py` (AggregateSet), `factories.py` (GraphQL-arguments factory)
- `django_strawberry_framework/fieldset.py`
- `django_strawberry_framework/permissions.py`
- `django_strawberry_framework/management/commands/export_schema.py`

This matches the target layout in `docs/TREE.md` and replaces the earlier flat-file proposal (`filters.py`, `filterset.py`, `filter_arguments_factory.py`, `orders.py`, `orderset.py`, `order_arguments_factory.py`, `aggregateset.py`, `aggregate_arguments_factory.py`).

Existing modules to evolve:

- `types/base.py`: collection only, not full finalization
- `types/converters.py`: scalar conversion and relation annotation helpers
- `types/resolvers.py`: transitional relation resolver support
- `registry.py`: type definitions, finalization state, pending relations, generated type registries
- `optimizer/*`: keep current root optimizer, add field stores and connection awareness

## Migration path from current package
### Phase 1: Foundation (== 0.0.4 foundation slice)
This phase is the foundation slice defined in [`docs/spec-foundation.md`](spec-foundation.md). It ships:

- `DjangoTypeDefinition`
- pending relation registry
- `finalize_django_types()` (the only new public symbol)
- the cardinality fixture, cyclic acceptance tests, end-to-end schema tests, and idempotency / failure-atomicity tests

It does **not** ship:

- `DjangoSchema` — deferred to a later wrapper phase. Earlier drafts of this spec listed `DjangoSchema` here; the foundation contract has narrowed.
- `DjangoConnectionField`, `DjangoNodeField`
- any Layer 3 subsystem

Keep current behavior for acyclic simple types if possible.

### Phase 2: Definition-order independence
Move `convert_relation` from eager lookup to pending relation creation.

Acceptance tests:

- `CategoryType.items` before `ItemType`
- `ItemType.category` before or after `CategoryType`
- reverse FK, M2M, forward FK, forward OneToOne, reverse OneToOne
- unresolved target raises at finalization

### Phase 3: DjangoModelField
Introduce the custom field class and migrate generated fields onto it.

Acceptance tests:

- scalar fields still resolve
- many-side relations return lists
- reverse one-to-one returns `None` when absent
- async-safe relation access
- field metadata points back to `DjangoTypeDefinition`

### Phase 4: Connection field
Add:

- `DjangoConnection`
- `DjangoConnectionField`
- `DjangoNodeField`
- Relay node support
- `totalCount`

Acceptance tests should mirror the cookbook root shape.

### Phase 5: Filters and ordering
Port the Graphene package's filter/order APIs to Strawberry input types.

Acceptance tests:

- nested `filter`
- `and` / `or` / `not`
- related filters with string refs
- explicit related queryset scope
- nested `orderBy`
- `ASC_DISTINCT` / `DESC_DISTINCT`
- permission hooks

### Phase 6: Aggregates
Port aggregate classes and connection `aggregates`.

Acceptance tests:

- aggregate field appears on root and nested connections
- aggregate results use filtered pre-pagination queryset
- selection-set-aware computation
- related aggregate traversal
- async aggregate path
- permission hooks

### Phase 7: FieldSet and permissions
Add:

- `AdvancedFieldSet`
- `fields_class`
- `apply_cascade_permissions`
- optional sentinel redaction
- `is_redacted`

Acceptance tests should port the field permission and nested permission tests from the Graphene package.

### Phase 8: Optimizer integration
Expand optimizer to understand:

- generated connection fields
- `edges.node`
- aggregate querysets
- nested connection prefetch
- field-level optimizer stores
- custom queryset hooks

## Recommended decisions
### Decision 1: concrete relation target by default
Use concrete registered `DjangoType`s for relations. Do not default to generic `DjangoModelType`.

### Decision 2: explicit package finalizer
Add `finalize_django_types()` and call it from package-owned schema/field helpers.

### Decision 3: custom Strawberry field class
Move generated fields to `DjangoModelField` so field behavior is composable.

### Decision 4: Graphene feature semantics
Use `django-graphene-filters` as the product behavior reference.

### Decision 5: Strawberry implementation mechanics
Use Strawberry-Django as the implementation reference for field processing, annotations, connection extensions, and optimizer stores.

### Decision 6: fail loudly
Never silently skip exposed fields whose target type is missing. Raise at finalization with the source model, field, and target model named.

## Open questions
### Should plain `strawberry.Schema` remain fully supported?
Best answer: yes for simple schemas, but rich schemas should use `DjangoSchema` or package-owned fields that finalize before schema construction.

### Should multiple `DjangoType`s per model be allowed?
The Graphene package currently assumes one primary node per model. This package's docs mention a future `Meta.primary`. Rich relation auto-resolution needs one primary target per model. Multiple types can exist later, but relation auto-resolution should require exactly one primary type.

### Should generic fallback exist?
Not for 1.0 by default. Consider an explicit opt-in after concrete relation finalization ships.

### Should sentinel redaction be required?
No. It should be available for Relay node types, but cascade filtering should remain the recommended privacy-first path.

### Should filters/orders/aggregates copy Graphene names exactly?
Mostly yes, because migration from the working package matters. If Strawberry idioms require a naming change, document it as a deliberate migration break.

## Success criteria
The architecture is successful when the fakeshop and cookbook-shaped examples can express:

- rich bidirectional model relations with `fields = "__all__"`
- Relay node lookup
- root and nested connection fields
- nested filters
- nested ordering
- search
- aggregate output on connections
- field-level permission masking
- row-level permission filtering
- cascade FK visibility
- optimizer-compatible nested selections

And when the implementation avoids:

- Graphene runtime dependencies
- silent missing-field skips
- generic relation placeholders as the default
- decorator-only user APIs
- fragile post-schema mutation

The end state should feel like the Graphene package to users and like a Strawberry-native package internally.
