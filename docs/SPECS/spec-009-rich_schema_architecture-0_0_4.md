# Rich schema architecture

Rejected alternatives live in the companion file [`spec-009-rich_schema_architecture-0_0_4-rationale.md`][spec-009-rationale]: why finalization is triggered only by the explicit consumer call, and why the package uses none of six upstream mechanisms — a custom field class, a field-level optimizer store with request-scoped callable hints, an annotation-namespace collector, a decorator-style advanced-field factory, a generic model placeholder, and DISTINCT-flavored order directives.

## Purpose
This spec defines the long-term architecture for building a Strawberry-based package that can expose the same practical schema shape as the feature-complete Graphene reference implementation in `django-graphene-filters`, while avoiding the parts of Graphene-Django that are old, unmaintained, and less aligned with Strawberry's execution model.

The narrow definition-order problem is documented in `docs/SPECS/spec-008-definition_order_independence-0_0_4.md`. This document is broader. It answers:

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
- [`apply_cascade_permissions`][glossary-apply-cascade-permissions]
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
    object_type: ObjectTypeNode | None = DjangoNodeField(ObjectTypeNode)
    all_object_types: DjangoConnection[ObjectTypeNode] = DjangoConnectionField(ObjectTypeNode)
```

Two things about that shape are contract rather than illustration.

**Node lookup is nullable.** `relay.py` #"Resolution is **nullable by contract**" dispatches `required=False` unconditionally, so a hidden row, a missing row, and an uncoercible pk all resolve to `null`. `ObjectTypeNode | None` is therefore the supported annotation spelling; a non-null annotation builds a schema that violates non-null on the first hidden or missing row.

**Three of the `Meta` keys above are the destination, not today's declarable surface.** `aggregate_class`, `fields_class`, and `search_fields` sit in `types/base.py::DEFERRED_META_KEYS` and are refused at class creation with a [`ConfigurationError`][glossary-configurationerror] until the subsystem that consumes each one lands: `fields_class` with [`FieldSet`][glossary-fieldset] (`TODO-BETA-059-0.1.1`), `search_fields` with `Meta.search_fields` support (`TODO-BETA-060-0.1.2`), and `aggregate_class` with the aggregation subsystem (`TODO-BETA-062-0.1.3`), each promoting its key in the change that applies it end-to-end. `model`, `fields`, `interfaces`, `filterset_class`, and `orderset_class` are declarable, alongside further keys this target shape does not show; `types/base.py::ALLOWED_META_KEYS` is the enumeration.

The exact class names may change, but the architectural goal is the same:

- type classes stay `class Meta` driven
- connection fields bind filtering, ordering, search, aggregation, pagination, optimization, and permission behavior
- related object fields are rich concrete types, not generic placeholders
- bidirectional model graphs work naturally
- the optimizer stays first-class

## Local package substrate
The architecture builds on these package modules:

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/types/finalizer.py`
- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/walker.py`

and these functions:

- `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`
- `django_strawberry_framework/types/base.py::_validate_meta`
- `django_strawberry_framework/types/base.py::_select_fields`
- `django_strawberry_framework/types/base.py::_build_annotations`
- `django_strawberry_framework/types/converters.py::resolved_relation_annotation`
- `django_strawberry_framework/types/resolvers.py::_make_relation_resolver`
- `django_strawberry_framework/types/resolvers.py::_attach_relation_resolvers`
- `django_strawberry_framework/registry.py::TypeRegistry.add_pending_relation`
- `django_strawberry_framework/types/finalizer.py::finalize_django_types`
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]: `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.check_schema`
- `django_strawberry_framework/optimizer/walker.py::plan_relation`
- `django_strawberry_framework/optimizer/walker.py::_plan_prefetch_relation`

Type creation is two-phase:

1. `DjangoType.__init_subclass__` validates `Meta`, chooses Django fields (`_select_fields`), synthesizes annotations (`_build_annotations`), registers the type with its definition, and records every relation it synthesizes as a pending relation through `TypeRegistry.add_pending_relation`.
2. `finalize_django_types()` classifies every pending relation, raising `ConfigurationError` for any target with no registered `DjangoType` before mutating a class, rewrites each resolved relation's annotation through `resolved_relation_annotation`, attaches relation resolvers, and calls `strawberry.type(cls)` once per type.

Type conversion and Strawberry finalization therefore happen at different moments, which is what lets a bidirectional model graph declare both sides of a relation in any order.

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
- filter [input type][glossary-input-type-generation]
- order input type
- search argument
- aggregate output type
- queryset resolution
- permission-aware filtering
- connection result shape

The Strawberry version should have a [`DjangoConnectionField`][glossary-djangoconnectionfield] that plays the same role. It should not force users to write manual list resolvers for common model lists.

#### Take lazy related class references
`LazyRelatedClassMixin` solves circular filter/order/aggregate class graphs without depending on Python declaration order.

Take the concept and adapt it:

- accept class objects
- accept absolute import strings
- accept same-module class-name strings
- accept zero-argument callables
- bind each related declaration to its owning class
- resolve only when the factory/finalizer needs the target

This pattern is separate from model relation type finalization. `sets_mixins.py::LazyRelatedClassMixin` carries it for:

- [`RelatedFilter`][glossary-relatedfilter]
- [`RelatedOrder`][glossary-relatedorder]
- [`RelatedAggregate`][glossary-relatedaggregate], when aggregates ship
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

- declarative [`Meta.fields`][glossary-metafields]
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

Take the behavior, but implement it by wrapping the generated resolver rather than by mutating Graphene fields. Wrapping is what keeps the gate/override cascade ordering expressible and costs nothing on unmanaged fields; `spec-059-fieldset-0_1_1.md` #"Custom field class vs `permission_classes` vs resolver wrapping" owns that mechanism.

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
- `unwrap_type`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/utils/typing.py#L137`
- `get_type_from_lazy_annotation`: `file:///Users/riordenweber/projects/strawberry-django-main/strawberry_django/utils/typing.py#L149`
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

This package borrows that lifecycle, but not the decorator API:

- `DjangoType.__init_subclass__` collects and `finalize_django_types()` finalizes
- `DjangoTypeDefinition` is built during class creation
- model-to-type registration happens immediately
- `strawberry.type` is deferred until relation targets are known
- field metadata lives on the definition object rather than on per-field objects, so one lookup answers every question about a generated field

This gives us Strawberry-Django's stable field metadata model without adopting its decorator-first public API.

### Borrow `StrawberryDjangoDefinition`
The package equivalent:

```python
@dataclass
class DjangoTypeDefinition:
    origin: type
    model: type[models.Model]
    fields_spec: tuple[str, ...] | Literal["__all__"] | None
    exclude_spec: tuple[str, ...] | None
    filterset_class: type | None
    orderset_class: type | None
    fields_class: type | None
    interfaces: tuple[type, ...]
    optimizer_hints: dict[str, OptimizerHint]
    finalized: bool = False
```

That is the load-bearing subset: `types/definition.py::DjangoTypeDefinition` also carries the selection and field-map slots, the consumer-provenance frozensets, the Relay and connection sidecars, a GraphQL-type-name property, and two memoized lookup methods. A sidecar slot is a plain `type | None`, validated to a concrete class at class creation (`types/base.py::_validate_filterset_class`). `aggregate_class` and `search_fields` have **no slot at all**: their `Meta` keys sit in `types/base.py::DEFERRED_META_KEYS` and are rejected at class creation, so each slot lands with the card that promotes its key (`TODO-BETA-062-0.1.3`, `TODO-BETA-060-0.1.2`). `fields_class` alone is reserved ahead of its key, for `TODO-BETA-059-0.1.1`.

It is stored on the class as `__django_strawberry_definition__`. This mirrors Strawberry-Django's `__strawberry_django_definition__`, but keeps this package's namespace distinct.

Benefits:

- one canonical place for model/type metadata
- optimizer can read from the definition rather than scattered class attrs
- connection fields can resolve filter and order defaults from the node type
- [schema audit][glossary-schema-audit] can name the exact relation fields whose target model has no registered type

### Track annotation provenance structurally, not by re-collecting annotations
[Definition-order independence][glossary-definition-order-independence] intersects with postponed annotations, and a consumer field may reference a type declared later. Both problems are real; neither is solved by walking the annotation namespace a second time.

Required behavior:

- record, at collection time, which fields the consumer authored and in which spelling — annotated or assigned, relation or scalar — so a generated annotation can never overwrite a consumer's. `types/base.py::DjangoType.__init_subclass__` derives those provenance sets and `types/definition.py::DjangoTypeDefinition` carries them; the override validators and `types/base.py::_build_annotations` all read the same union rather than re-deriving one
- resolve postponed annotations by deferring `strawberry.type` to finalization, which is when every target type exists, rather than by an eval-time namespace capture
- keep provenance one system. A second, independently-derived view of "which annotation came from where" is a source of disagreement, not a safety net

### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField`
Borrow the **behaviors** these classes encode, not the class itself. Each is a real requirement for a generated relation field:

- Django field names distinct from Python names
- relation and origin-type metadata reachable from the resolver
- filter/order/pagination arguments on a relation or root field
- row-level `get_queryset` chaining onto the relation's own queryset
- async-safe queryset access
- connection argument injection

Upstream binds all of them to one field class because its public API is decorator-first: the decorator's return value is the only object it owns. This package's public API is `class Meta`, so the finalizer owns generation and each responsibility lives at the seam where it is cheapest to reason about. `### Layer 4: Generated relation fields` states that seam map once; it is not repeated here.

Async-safe queryset access runs through the `utils/querysets.py::apply_type_visibility_sync` / `apply_type_visibility_async` pair, with `utils/querysets.py::SyncMisuseError` closing the sync path against an `async def get_queryset`. `types/resolvers.py::_make_relation_resolver` generates plain sync callables; where one must re-check a target's visibility under an async execution it returns the awaitable the async half produces rather than touching the ORM synchronously.

The invariant this distribution has to keep is that **one object still answers every question about a generated field**: `types/definition.py::DjangoTypeDefinition` is that object, and every seam reads it rather than carrying a private copy. Scattering the metadata across generated annotations, class attributes, resolver closures, and optimizer maps is the failure mode a field class is usually reached for to prevent, and it is prevented here by the definition being single-sourced instead.

### Borrow `resolve_type`, but change relation fallback behavior
`StrawberryDjangoFieldBase.resolve_type` handles `strawberry.auto`, `Any`, and unresolved annotations by calling `resolve_model_field_type`.

Borrow that hook, but change relation semantics.

Strawberry-Django's default relation fallback maps:

- `ForeignKey` -> `DjangoModelType`
- reverse FK -> `list[DjangoModelType]`

That is useful for Strawberry-Django's goals, but it is too weak for this package. This package resolves every exposed relation field to a concrete registered [`DjangoType`][glossary-djangotype]:

1. scalar fields use a local `resolve_model_field_type`-style map
2. every auto-synthesized relation field records a pending relation at collection
3. finalization asks the package registry for the concrete target type
4. a target still missing at finalization raises [`ConfigurationError`][glossary-configurationerror]
5. no generic model placeholder ever substitutes for a concrete target type

There is no placeholder tier in this architecture — not as a default, not as an internal reserve, not as an opt-in. A relation either resolves to a concrete registered `DjangoType` or finalization fails; `### The unresolved-relation contract is error-only` states the contract and Decision 6 states why a weaker schema is not an acceptable answer to a missing type.

### Borrow `resolve_model_field_type`, `get_model_field`, `resolve_model_field_name`, and `is_optional`
These functions encode many Django edge cases:

- reverse relations are not always found by `model._meta.get_field(name)`
- FK id fields may use `attname`
- input/filter contexts have different nullability rules
- reverse one-to-one nullability is special
- file/image/JSON/GIS/array/generated fields need type maps

Borrow the shape, but align it with this package's public contract.

Recommended adaptation:

- `types/converters.py #"SCALAR_MAP: "` is the supported scalar set, grown toward Strawberry-Django's coverage one field family at a time
- use `get_model_field` logic for reverse relation lookup
- use `resolve_model_field_name` to normalize Django names
- use `is_optional` to centralize nullability
- keep relation mapping concrete, not generic

### Borrow `field` and `connection` as implementation patterns
Do not expose Strawberry-Django's decorator-first API as the main API, but borrow the implementation pattern:

- `field(...)` creates a Django-aware field object
- `connection(...)` creates a Django-aware field with a connection extension
- extensions add arguments and resolve pagination

This package exposes:

- `DjangoListField(...)` for a non-Relay `list[T]` field, keeping graphene-django's symbol so that migration site needs no shape change
- `DjangoConnectionField(...)` for root and nested connections
- `DjangoNodeField(...)` and `DjangoNodesField(...)` for [Relay node][glossary-relay-node-integration] lookup

Each is a **factory returning a Strawberry field**, so a consumer's class-body annotation stays the source of the schema type and no consumer-facing class carries a stacked decorator.

### Borrow `DjangoListConnection`
`DjangoListConnection` has a Strawberry-native connection shape with `total_count`, queryset awareness, and optimized connection resolution.

Borrow the concept, with two corrections to its shape.

**`totalCount` is opt-in per type, not a field on the base.** A count costs a second query, so the generic base carries no `total_count` member; `Meta.connection = {"total_count": True}` is what asks for one. The connection field resolves **every** node type through a generated concrete `<TypeName>Connection` subclass; the opt-in decides only whether that subclass carries the member or adds nothing over the base. The generic base owns what every connection needs regardless: the `first` + `last` mutual-exclusivity guard, consumption of optimizer-supplied windows, and cursor-mode dispatch.

```python
@strawberry.type
class DjangoConnection(relay.ListConnection[NodeType]):
    """Generic base; the totalCount members live on the generated subclass."""
```

The generated subclass is not a naming convenience — a bare generic alias loses the `resolve_connection` override at Strawberry's generic specialization, so the concrete subclass is what keeps package pagination dispatch reachable at all.

**`aggregates` is the Graphene reference's shape and is still owed.** It belongs on the connection, computed from the filtered, searched, ordered queryset before pagination. It is unbuilt: `TODO-BETA-062-0.1.3` owns it, and it lands through the same generated-subclass mechanism `totalCount` uses rather than by widening the generic base.

### Keep the current optimizer's strengths, and borrow its nested-prefetch lessons
The package's optimizer:

- root-gates query optimization
- plans `select_related`, `prefetch_related`, and `only`
- preserves consumer queryset shaping
- downgrades to `Prefetch` when target types override `get_queryset`
- supports strictness warnings/errors
- supports plan caching

Borrowed from Strawberry-Django:

- `_must_use_prefetch_related` logic for custom queryset/polymorphic/annotation cases
- `_get_prefetch_queryset` and `_optimize_prefetch_queryset` concepts for nested connection prefetches, which `optimizer/nested_planner.py` carries
- connection-aware optimization for `edges.node` and total count

Strawberry-Django's optimizer is not copied wholesale. This package's optimizer plans against the generated `DjangoType` maps on `DjangoTypeDefinition`, not against a per-field metadata store.

**A hint must be a value, not a callable.** Strategy selection is schema-static, so the cross-request plan cache is not keyed on it; a hint that could consult the request would make every cached plan unsound. `Meta.optimizer_hints` therefore carries frozen directives (`optimizer/hints.py::OptimizerHint`), and request-varying shaping belongs to `get_queryset`, which already runs per request.

### Borrow `django_resolver` and `django_getattr`
`django_resolver` handles sync/async ORM access safely. `django_getattr` centralizes:

- callable return values
- `BaseManager` to queryset conversion
- queryset evaluation hooks
- reverse one-to-one `DoesNotExist` -> `None`
- async contexts

Borrow these patterns into the generated relation resolver (`types/resolvers.py::_make_relation_resolver`) — except async contexts: that resolver is a sync callable, and under an async execution it hands back the awaitable from `utils/querysets.py::apply_type_visibility_async` instead of reading the ORM synchronously.

Centralizing them there is what keeps the N+1 probe, the prefetch-cache read, the FK-id elision, and the row-bound call out of a variant per relation kind.

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

Keep as references:

- type finalization lifecycle
- annotation handling across inheritance and postponed evaluation
- Strawberry-native connection extensions
- nested prefetch handling
- sync/async resolver wrappers

## Recommended combined architecture
The best system is a hybrid:

1. Use the `django-graphene-filters` product model.
2. Use Graphene-Django's deferred relation insight.
3. Use Strawberry-Django's type/finalization mechanics.
4. Keep this package's current optimizer and evolve it with Strawberry-Django's nested-connection prefetch lessons.

### Layer 1: Type collection
`DjangoType.__init_subclass__` collects; it neither resolves relation targets nor finalizes.

Class-creation responsibilities:

1. detect concrete subclasses
2. validate supported `Meta` keys
3. select fields
4. build `DjangoTypeDefinition`
5. register model -> class early
6. record field metadata
7. record pending relation metadata
8. mark the class as unfinalized

`strawberry.type(cls)` is not called until finalization.

The registry distinguishes:

- registered but unfinalized types
- finalized types
- pending relation fields
- unresolved target errors

### Layer 2: Pending relation registry
The pending relation record (`types/relations.py::PendingRelation`):

```python
@dataclass
class PendingRelation:
    source_type: type[DjangoType]
    source_model: type[models.Model]
    field_name: str
    django_field: models.Field | ForeignObjectRel
    related_model: type[models.Model]
```

The record carries no cardinality or nullability: `field_name` is the raw Django field name that keys `DjangoTypeDefinition.field_map`, and finalization reads both from that map.

During collection:

- scalar fields are known immediately
- every auto-synthesized relation field becomes pending, whether or not its target type is registered yet; binding at class creation would freeze the relation against whichever type was registered first

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

**The trigger is the explicit consumer call, and nothing else.** [`finalize_django_types()`][glossary-finalize-django-types] is public, and calling it is the only thing that finalizes. No shipped helper auto-triggers it: `DjangoConnectionField`, `DjangoNodeField` and `DjangoSchema` do not call the finalizer, and constructing any of them does not finalize the registry. The canonical window is after every module defining `DjangoType` classes has been imported and before `strawberry.Schema(...)` construction; `spec-010-foundation-0_0_4.md` #"## Strawberry finalization strategy" owns that contract and its wording.

The requirement the trigger has to satisfy:

- finalization happens before Strawberry schema conversion, so no post-schema patching is needed
- a schema extension cannot be the trigger, because extensions run after the schema is already built
- an unusual import layout, a test, or a cookbook-shaped schema all reach the same single entry point rather than depending on which package object they happened to construct first

The registry is deliberately lockless and finalization is a process-global mutation, so any future helper that auto-triggers it must also enforce the single-threaded setup window — either by being constrained to schema-construction time or by acquiring a real lock around the finalizer. The rationale companion's Layer 3 entry carries the constructor-triggered alternative and why it lost.

### Layer 4: Generated relation fields
Generated relation fields are produced by the finalizer, and their responsibilities are distributed across four named seams rather than gathered into one field object:

- **annotation** — `types/converters.py::resolved_relation_annotation` produces the concrete annotation once the target type is resolved, in the cardinality-correct spelling (`target`, `list[target]`, `target | None`)
- **resolution** — `types/resolvers.py::_make_relation_resolver` generates one resolver per relation, and `types/resolvers.py::_attach_relation_resolvers` installs them at finalizer Phase 2, before `strawberry.type` runs at Phase 3
- **visibility** — `utils/querysets.py::apply_type_visibility_sync` composes the target type's row-level `get_queryset` onto the relation queryset. It runs on the connection pipeline, on `list_field.py::DjangoListField`, and on the optimizer's prefetch child (`optimizer/walker.py::_build_child_queryset`); for a relation the optimizer did not plan (no optimizer, an unplanned path, a consumer's own prefetch), the generated resolver applies a custom target hook itself (`types/resolvers.py::_custom_visibility_type`)
- **arguments** — `connection.py::DjangoConnectionField` synthesizes a resolver `__signature__` carrying the sidecar arguments, which is how `filter:` and `orderBy:` appear on a field nobody hand-wrote a signature for

`types/definition.py::DjangoTypeDefinition` is what keeps this coherent: it holds the Django field name, the origin type, the relation metadata, and the sidecar bindings, and every seam above reads it. Field-level `fields_class` behavior wraps the generated resolver rather than replacing it (`spec-059-fieldset-0_1_1.md` owns that mechanism).

The load-bearing constraint on this layer: **generation happens at finalization and nowhere else.** A relation field cannot be generated at class creation, because its target may not exist yet, and it cannot be generated after `strawberry.type`, because the type is frozen by then. Phase 2 is the only window, which is why it is a permanent mechanism rather than a transitional one.

### Layer 5: Connection field
`DjangoConnectionField`:

1. accepts a target `DjangoType`
2. derives model and default queryset from the target type
3. reads `filterset_class` and `orderset_class` from the target definition, and `aggregate_class` and `search_fields` once their subsystems ship
4. adds `filter` and `orderBy` arguments, and `search` with `TODO-BETA-060-0.1.2`
5. applies row-level `get_queryset`
6. applies filters
7. applies search (`TODO-BETA-060-0.1.2`)
8. applies ordering
9. computes aggregates from the filtered pre-pagination queryset (`TODO-BETA-062-0.1.3`)
10. paginates as a Relay connection
11. exposes `totalCount` when `Meta.connection` opts in, and `aggregates` with `TODO-BETA-062-0.1.3`
12. cooperates with `DjangoOptimizerExtension`

It does **not** finalize. Constructing a connection field does not trigger finalization, for the reasons Layer 3 gives; a connection field constructed before every `DjangoType` module is imported would otherwise silently fix the schema's shape to whatever had been imported by then.

This is the Strawberry equivalent of `AdvancedDjangoFilterConnectionField`.

### Layer 6: Filter system
Use `django-graphene-filters` semantics, Strawberry implementation.

Public API:

```python
class ObjectFilter(FilterSet):
    object_type = RelatedFilter(ObjectTypeFilter, field_name="object_type")
    values = RelatedFilter("ValueFilter", field_name="values")

    class Meta:
        model = models.Object
        fields = {
            "name": "__all__",
            "description": ["exact", "icontains"],
        }
```

The base is named [`FilterSet`][glossary-filterset] rather than borrowing the Graphene package's `Advanced` prefix, because it subclasses django-filter's own `BaseFilterSet` and a DRF-shaped surface should read as the django-filter class a consumer already has. `Meta.fields` is django-filter's key and is canonical here; `Meta.filter_fields` is accepted as a cookbook-parity alias when `fields` is absent, and the per-field `"__all__"` value is supported in both spellings.

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

- [`OrderSet`][glossary-orderset]
- `RelatedOrder`
- ordered list of order directives
- nested relation ordering
- permission hooks

Borrow from Strawberry-Django:

- recursive `process_order` shape
- the [`Ordering`][glossary-ordering] enum's six-member direction vocabulary — `ASC` / `DESC` plus the four explicit NULLS-positioning variants — which is exactly what a portable null partition needs
- input object traversal and prefix handling

**A to-many order path must be row-preserving.** Ordering a parent by a child column joins, and a naive join multiplies parent rows, inflating both the page and `totalCount`. Solve it by annotation — order ascending terms by `Min(path)` and descending terms by `Max(path)`, then order by the alias — not by de-duplicating after the fact. The annotation composes with the connection's primary-key tiebreaker, which is what keeps cursors stable across pages.

Prefer the Graphene package's list-of-order-objects semantics if matching existing clients matters.

### Layer 8: Aggregate system
Use `django-graphene-filters` aggregate semantics through an [`AggregateSet`][glossary-aggregateset] base. `TODO-BETA-062-0.1.3` owns the layer.

Public API:

```python
class ObjectAggregate(AggregateSet):
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

Implementation should wrap the generated field resolver, not mutate the field object after the fact. Wrapping keeps the cascade below expressible in one place and costs nothing on a field no [`FieldSet`][glossary-fieldset] manages; `spec-059-fieldset-0_1_1.md` owns the mechanism and `TODO-BETA-059-0.1.1` owns the work.

Resolver order:

1. row already passed `get_queryset`
2. field permission check
3. field custom resolver
4. default Django attribute/relation resolver
5. type-appropriate deny value when needed

Keep computed fields support.

### Layer 10: Row permissions and cascade visibility
Keep the Graphene package's row/cascade model.

The layer consists of:

- `DjangoType.get_queryset`
- `permissions.py::apply_cascade_permissions`
- optional sentinel redaction support for Relay node types (`TODO-BETA-064-0.1.4`)
- an `is_redacted` generated field or mixin (`TODO-BETA-064-0.1.4`)

Open design point:

- Sentinel nodes are useful for non-null FK fields but can surprise clients.
- Cascade filtering is cleaner when parent rows should disappear.
- The package should support both, but docs should recommend cascade filtering for strict privacy.

### Layer 11: Optimizer integration
The optimizer must remain a first-class part of this package.

Its features:

- root-gated optimization
- plan caching
- strictness modes
- [FK-id elision][glossary-fk-id-elision]
- existing queryset reconciliation
- `get_queryset`-aware prefetch downgrade
- nested connection prefetch handling and connection-aware `edges.node` traversal (`optimizer/nested_planner.py`)
- per-field opt-out (`OptimizerHint.SKIP`)
- aggregate pre-pagination query reuse, with `TODO-BETA-062-0.1.3`

Optimization does not depend on Graphene-style connection internals.

## Definition-order strategy in this architecture
The best approach is neither pure Graphene nor pure Strawberry-Django.

Use:

- Graphene's deferred concrete relation target idea
- Strawberry-Django's type-finalization mechanics
- package-owned explicit finalization

The finalization pass, whose phases `spec-010-foundation-0_0_4.md` owns:

1. audit primary ambiguity for every model with several registered types
2. classify every pending relation, raising `ConfigurationError` for any target with no registered type before any class is mutated
3. rewrite each resolved relation's annotation to its concrete target type
4. attach the generated relation resolvers
5. apply interfaces, synthesize relation connections, bind generated mutations, and bind the filter and order sidecars, resolving their lazy related-class references against bound owners
6. call `strawberry.type` once per type

Aggregate and fieldset class references bind in the same window when those subsystems ship.

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

### The unresolved-relation contract is error-only
A `Meta.unresolved_relations` opt-in (with values such as `"generic"` or `"error"`) is **not** part of the architecture. The contract is **error-only**: every exposed relation field must resolve to a concrete registered `DjangoType` at finalization, or `finalize_django_types()` raises with the unresolved-targets format. `spec-010-foundation-0_0_4.md` #"### Unresolved-target error format" owns the wording.

If a real project surfaces a use case where error-only is too strict, relaxing it is a design change that earns its own card and design doc — not an assumption baked into Layer 3 work. No subsystem in this architecture may be designed against `Meta.unresolved_relations`.

## Module layout
The layers live in **packages** where a subsystem spans more than one module (`filters/`, not `filters.py`); the package layout is canonical because it determines import paths, public-surface promotion, and test-tree mirroring. `docs/TREE.md` is the rendered map of the whole tree.

- `django_strawberry_framework/types/base.py` — collection only (Layer 1)
- `django_strawberry_framework/types/definition.py` — `DjangoTypeDefinition`
- `django_strawberry_framework/types/relations.py` — the pending relation record and its sentinel annotation (Layer 2)
- `django_strawberry_framework/types/finalizer.py` — `finalize_django_types()`
- `django_strawberry_framework/types/converters.py` — scalar conversion and relation annotation helpers
- `django_strawberry_framework/types/resolvers.py` — generation and attachment of the relation resolvers (Layer 4)
- `django_strawberry_framework/registry.py` — type definitions, finalization state, pending relations
- `django_strawberry_framework/schema.py` — `DjangoSchema`
- `django_strawberry_framework/relay.py` — `DjangoNodeField`, `DjangoNodesField`
- `django_strawberry_framework/connection.py` — `DjangoConnection`, `DjangoConnectionField` (Layer 5)
- `django_strawberry_framework/filters/` — `base.py` (Filter classes), `sets.py` (FilterSet), `factories.py` (GraphQL-arguments factory), `inputs.py` (input types + adapters)
- `django_strawberry_framework/orders/` — `base.py` (Order classes), `sets.py` (OrderSet), `factories.py` (GraphQL-arguments factory), `inputs.py` (input types + the direction enum + adapters)
- `django_strawberry_framework/permissions.py` — cascade visibility; migrating to a `permissions/` package at `TODO-BETA-064-0.1.4`, when opt-in node-sentinel redaction joins the cascade helpers
- `django_strawberry_framework/optimizer/` — the root optimizer and nested-connection planning (Layer 11)
- `django_strawberry_framework/management/commands/export_schema.py`
- `django_strawberry_framework/aggregates/` — `base.py` (Sum/Count/Avg/Min/Max/GroupBy result types), `sets.py` (AggregateSet), `factories.py` (GraphQL-arguments factory) — planned by `TODO-BETA-062-0.1.3`
- `django_strawberry_framework/fieldset/` — planned by `TODO-BETA-059-0.1.1`

## Build order
The phases below are the order in which the layers depend on one another. Each phase's own spec owns its contract; an unshipped phase names the card that owns it.

### Phase 1: Foundation
The foundation slice, [`spec-010-foundation-0_0_4.md`][spec-010]:

- `DjangoTypeDefinition`
- the pending relation registry
- `finalize_django_types()`, the only public symbol the layer adds
- cardinality coverage through the `library` example app, cyclic acceptance tests, end-to-end schema tests, and idempotency / failure-atomicity tests

`DjangoSchema`, `DjangoConnectionField`, [`DjangoNodeField`][glossary-djangonodefield] and every Layer 6+ subsystem sit on top of it and do not change it.

### Phase 2: [Definition-order independence][glossary-definition-order-independence]
Relation conversion records a pending relation for every auto-synthesized relation; no target is looked up at class creation.

Acceptance tests:

- `CategoryType.items` before `ItemType`
- `ItemType.category` before or after `CategoryType`
- reverse FK, M2M, forward FK, forward OneToOne, reverse OneToOne
- unresolved target raises at finalization

### Phase 3: Generated relation fields
The finalizer generates the annotation and resolver for every exposed relation, in the cardinality-correct spelling — Layer 4.

Acceptance tests:

- scalar fields still resolve
- many-side relations return lists
- reverse one-to-one returns `None` when absent
- async-safe relation access
- field metadata points back to `DjangoTypeDefinition`

### Phase 4: Connection field
- [`DjangoConnection`][glossary-djangoconnection]
- `DjangoConnectionField`
- `DjangoNodeField`
- Relay node support
- `totalCount`

Acceptance tests mirror the cookbook root shape.

### Phase 5: Filters and ordering
The Graphene package's filter/order APIs, as Strawberry input types.

Acceptance tests:

- nested `filter`
- `and` / `or` / `not`
- related filters with string refs
- explicit related queryset scope
- nested `orderBy`
- a to-many order path that neither duplicates parent rows nor inflates `totalCount`
- permission hooks

### Phase 6: Aggregates
Port aggregate classes and connection `aggregates`. Owned by `TODO-BETA-062-0.1.3`.

Acceptance tests:

- aggregate field appears on root and nested connections
- aggregate results use filtered pre-pagination queryset
- selection-set-aware computation
- related aggregate traversal
- async aggregate path
- permission hooks

### Phase 7: FieldSet and permissions
- [`FieldSet`][glossary-fieldset] and `fields_class` — owned by `TODO-BETA-059-0.1.1`
- `apply_cascade_permissions`
- optional sentinel redaction and `is_redacted` — owned by `TODO-BETA-064-0.1.4`, as an explicit opt-in tier rather than a default

Acceptance tests port the field permission and nested permission tests from the Graphene package.

### Phase 8: Optimizer integration
The optimizer understands:

- generated connection fields
- `edges.node`
- nested connection prefetch
- custom queryset hooks
- aggregate querysets, with `TODO-BETA-062-0.1.3`

## Recommended decisions
### Decision 1: concrete relation target by default
Use concrete registered `DjangoType`s for relations. Do not default to generic `DjangoModelType`.

### Decision 2: explicit package finalizer
`finalize_django_types()` is public, and the consumer's explicit call is the only thing that triggers it. Package-owned schema and field helpers do not call it; see Layer 3.

### Decision 3: generated field behavior belongs to the finalizer
Generate a relation field's annotation and resolver at finalization, from one `DjangoTypeDefinition`; the visibility and argument seams belong instead to the queryset-owning components `### Layer 4: Generated relation fields` names. Composability comes from that single definition being readable by every seam, not from a per-field object carrying its own copy.

### Decision 4: Graphene feature semantics
Use `django-graphene-filters` as the product behavior reference.

### Decision 5: Strawberry implementation mechanics
Use Strawberry-Django as the implementation reference for type finalization, annotation handling, connection extensions, and nested-prefetch planning.

### Decision 6: fail loudly
Never silently skip exposed fields whose target type is missing. Raise at finalization with the source model, field, and target model named.

## Open questions
### Should plain `strawberry.Schema` remain fully supported?
**Settled: for the read surface, yes; generated mutations require `DjangoSchema`.** Finalization does not live in any schema or field object — the consumer calls `finalize_django_types()` before schema construction — so types, connection fields and node fields build and resolve the same under a plain `strawberry.Schema`. What only `schema.py::DjangoSchema` carries is execution-time: the mutation transaction held open through response completion (`schema.py::DjangoMutationExecutionContext`), without which the generated write pipeline raises `ConfigurationError` before any database work; the execution resource policy and the production error policy, built per operation from the schema's own record; and per-operation isolation of the package's own extensions. Layer 3 above states the trigger contract.

### Should multiple `DjangoType`s per model be allowed?
**Settled: yes, with exactly one primary per model.** Under [`Meta.primary`][glossary-metaprimary], multiple `DjangoType`s may register against the same model, and relation auto-resolution binds to the primary. Ambiguity is refused rather than guessed: duplicate-primary and flipped-primary-on-re-register are rejected at registration, and ambiguity-by-omission is caught at finalization. `spec-018-meta_primary-0_0_6.md` owns the contract and the error wording.

### Should sentinel redaction be required?
No. It is an opt-in tier for Relay node types (`TODO-BETA-064-0.1.4`); cascade filtering stays the recommended privacy-first path.

### Should filters/orders/aggregates copy Graphene names exactly?
**Settled for filters and orders, still open for aggregates.** Both follow the rule stated here — keep the Graphene name unless a Strawberry idiom forces a change, and document any change as a deliberate migration break. `spec-027-filters-0_0_8.md` and `spec-028-orders-0_0_8.md` own their naming decisions. For aggregates (`TODO-BETA-062-0.1.3`) the rule is the guidance.

## Success criteria
The architecture is successful when the fakeshop and cookbook-shaped examples can express:

- rich bidirectional model relations with `fields = "__all__"`
- Relay node lookup
- root and nested connection fields
- nested filters
- nested ordering
- search — owed; `TODO-BETA-060-0.1.2`
- aggregate output on connections — owed; `TODO-BETA-062-0.1.3`
- field-level permission masking — owed; `TODO-BETA-059-0.1.1`
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

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-aggregateset]: ../GLOSSARY.md#aggregateset
[glossary-apply-cascade-permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-djangoconnection]: ../GLOSSARY.md#djangoconnection
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangonodefield]: ../GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-fieldset]: ../GLOSSARY.md#fieldset
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: ../GLOSSARY.md#fk-id-elision
[glossary-input-type-generation]: ../GLOSSARY.md#input-type-generation
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-ordering]: ../GLOSSARY.md#ordering
[glossary-orderset]: ../GLOSSARY.md#orderset
[glossary-relatedaggregate]: ../GLOSSARY.md#relatedaggregate
[glossary-relatedfilter]: ../GLOSSARY.md#relatedfilter
[glossary-relatedorder]: ../GLOSSARY.md#relatedorder
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-schema-audit]: ../GLOSSARY.md#schema-audit

<!-- docs/SPECS/ -->
[spec-009-rationale]: appx/spec-009-rich_schema_architecture-0_0_4-rationale.md
[spec-010]: spec-010-foundation-0_0_4.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
