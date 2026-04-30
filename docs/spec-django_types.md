# Spec: DjangoType Foundation

## Problem statement

`django-strawberry-framework` needs a first load-bearing primitive that both graphene-django and strawberry-graphql-django already provide: a way to turn a Django model into a GraphQL type. In this package that primitive must be DRF-shaped, meaning configuration lives in a nested `Meta` class, not in stacked decorators. This same primitive must also solve the most common GraphQL performance failure mode — N+1 relation queries — because every later subsystem (`FilterSet`, `OrderSet`, `AggregateSet`, permissions, connection fields) will sit on top of it.

## Current state

The package source currently contains only `django_strawberry_framework/conf.py`. The aspirational example schema at `examples/fakeshop/fakeshop/products/schema.py` already assumes the existence of `DjangoType`, `DjangoConnectionField`, and `apply_cascade_permissions`. The sibling files `examples/fakeshop/fakeshop/products/filters.py`, `orders.py`, `aggregates.py`, and `fields.py` likewise assume a future package surface, but none of those names exist yet.

The example data model is already stable enough to drive this spec: `Category`, `Item`, `Property`, and `Entry` in `examples/fakeshop/fakeshop/products/models.py`, with seed helpers in `examples/fakeshop/fakeshop/products/services.py` and real-world integration tests in `tests/`.

graphene-django's overlapping foundation is `DjangoObjectType` plus the model/type registry and the field converter layer at `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py:132-258`, `registry.py:1-42`, and `converter.py:182-507`. That gives us the core Meta options, the model registry, scalar field conversion, enum-from-choices, Relay node support, and relation-field generation.

strawberry-graphql-django's overlapping foundation is `@strawberry_django.type(...)`, `StrawberryDjangoField`, and the `DjangoOptimizerExtension`, documented at `https://strawberry.rocks/docs/django/guide/types`, `https://strawberry.rocks/docs/django/guide/optimizer`, and implemented in `strawberry_django/type.py` / `strawberry_django/fields/field.py`. That gives us the modern parts graphene-django lacks: automatic `select_related` / `prefetch_related` / `only()` optimization, field-level optimization hints, and a clean integration with Strawberry's type system.

## What both libraries overlap on

Both libraries, despite different APIs, solve the same foundational problem set:

model -> GraphQL type generation

scalar Django field -> GraphQL scalar conversion

relation field generation for FK / OneToOne / reverse FK / M2M

a type-level queryset hook (`get_queryset`) for scoping data

a registry that lets relation conversion look up the target GraphQL type by model

Relay node / global ID support

choices -> enum conversion

This overlap is the right scope for the first spec. Anything beyond that — filter argument generation, ordering, aggregations, per-field permissions, sentinel nodes — depends on this foundation and should be deferred.

## Goal

Add a `DjangoType` base class and a `DjangoOptimizerExtension` so that consumers can declare a Strawberry GraphQL type from a Django model using a DRF-shaped `Meta` class and have relation resolution optimized by default.

## Non-goals

This spec does not implement `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `DjangoConnectionField`, `apply_cascade_permissions`, per-field permission hooks, mutations, polymorphic interfaces, or the full relay connection story. Those follow later. The first spec only creates the foundation that later specs can attach to.

## Proposed public surface

This spec adds three public names at the package root:

`DjangoType`

`DjangoOptimizerExtension`

`auto` (re-exported from `strawberry`)

It also adds internal support modules: `registry.py`, `converters.py`, `exceptions.py`, and a `py.typed` marker.

## `DjangoType`

`DjangoType` is a base class with a metaclass (or equivalent `__init_subclass__` pipeline) that reads a nested `Meta` class, synthesizes Strawberry annotations from the Django model, registers the resulting type for later relation lookup, and then finalizes the class as a Strawberry type.

The consumer surface is intentionally DRF-like:

required: `Meta.model`

optional: `Meta.fields` as `"__all__"` or a list of field names

optional: `Meta.exclude` as a list of field names, mutually exclusive with `fields`

optional: `Meta.interfaces`, for example `(relay.Node,)`

optional: `Meta.name` to override the GraphQL type name

optional: `Meta.description`

The metaclass must reject unsupported future-surface keys for now. If a consumer declares `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, or `search_fields` before those specs ship, raise `ConfigurationError` rather than silently accepting noop config.

## Scalar field conversion

The converter layer should mirror graphene-django's coverage but emit Strawberry/Python-native types instead of graphene field instances.

`CharField`, `TextField`, `SlugField`, `EmailField`, `URLField` -> `str`

`IntegerField`, `SmallIntegerField`, `PositiveIntegerField` -> `int`

`BigIntegerField` -> custom `BigInt` scalar

`BooleanField` -> `bool`

`FloatField` -> `float`

`DecimalField` -> `decimal.Decimal`

`DateField` -> `datetime.date`

`DateTimeField` -> `datetime.datetime`

`TimeField` -> `datetime.time`

`DurationField` -> `datetime.timedelta`

`UUIDField` -> `uuid.UUID`

`JSONField` / `HStoreField` -> Strawberry JSON scalar

`BinaryField` -> `bytes`

`FileField` / `ImageField` -> `str` (URL/path)

`ArrayField` -> `list[inner_type]`

`null=True` maps to `T | None`.

Choice fields produce a generated strawberry `Enum` named `<TypeName><FieldName>Enum`. Those enums are cached in the registry keyed by `(model, field_name)` so multiple `DjangoType`s reading the same model field reuse the same enum.

## Relation field conversion

Forward FK and OneToOne map to the target `DjangoType`, nullable iff the Django field is nullable.

Reverse FK and reverse OneToOne map to the target `DjangoType` or `list[target_type]` depending on cardinality.

Forward and reverse M2M map to `list[target_type]`.

If the target model's `DjangoType` has not yet been registered, use Strawberry forward references so definition order does not matter.

This spec intentionally keeps relation field resolution inside the type system rather than introducing a separate consumer-facing decorator API. Consumers should be able to write one `class CategoryType(DjangoType): class Meta: ...` and have relations appear automatically.

## Registry

A global registry maps model -> `DjangoType` and `(model, field_name)` -> generated enum. It exists so relation fields and enum conversion can look up already-built types. Registering the same model twice should raise `ConfigurationError` by default. The registry also needs a test-only `clear()` helper for isolation.

## `get_queryset`

`DjangoType` exposes `@classmethod get_queryset(cls, queryset, info, **kwargs)` with a default identity implementation. This is the single authoritative hook for permission scoping, multi-tenancy, soft-delete filtering, and any future consumer-side queryset constraints. The optimizer must respect it, especially on related fields.

## N+1 strategy

The first spec should not treat N+1 as a later enhancement; it is part of the foundation.

The package should ship a Strawberry schema extension named `DjangoOptimizerExtension`. Consumers opt in once at schema construction time. The extension inspects the selected field tree and optimizes the root queryset before evaluation.

Rules:

forward FK / OneToOne -> `select_related`

reverse FK / reverse OneToOne -> `prefetch_related`

M2M -> `prefetch_related`

selected scalar columns -> `only()`

The load-bearing edge case is custom `get_queryset` on the target type. strawberry-graphql-django hit this exact bug in issue #572 and fixed it in PR #583 by converting what would have been `select_related` into a `Prefetch(queryset=target_type.get_queryset(...))` when the target type defines a non-default `get_queryset`. This rule must be part of the first spec because otherwise FK joins bypass per-type visibility filtering and leak rows. We should copy the behaviour, not the decorator surface.

So the rule here is:

if a related field would normally use `select_related`, but the target `DjangoType` overrides `get_queryset`, downgrade that relation to `Prefetch` with the target type's filtered queryset.

That gives us the best part of strawberry-graphql-django's optimizer without adopting its decorator-first public API.

## Type naming

Default GraphQL type name is the consumer class's `__name__`, matching both graphene-django and Strawberry norms. Relay connection types and edges should follow the same naming family later, but this spec only needs the object-type naming rule and the choice-enum naming rule.

## What this enables immediately after implementation

Once this spec lands, the placeholder example schema in `examples/fakeshop/fakeshop/products/schema.py` can begin shedding its commented scaffold in favor of real `DjangoType` classes. The next spec can then focus narrowly on wiring `filterset_class` into the type and connection field, instead of having to re-solve model conversion and N+1 at the same time.

## Testing strategy

All new package tests go in a new root-level file, not `tests/base/`, because `tests/base/` is reserved for `conf.py` and version checking per AGENTS.md.

The new tests should verify:

Meta validation (`fields`/`exclude`, missing `model`, deferred-key rejection)

scalar field mapping on the fakeshop models

choice-field enum generation on a small test-only model fixture

registry behaviour

FK / reverse / M2M relation field generation

optimizer query counts on relation traversal

the `get_queryset` + optimizer downgrade rule using a hidden related row scenario in the example app

The example tests already exercise admin, services, commands, schema, urls, and models through real Django flows. Those stay as-is; this spec adds focused package tests around the new core types and optimizer.

## Suggested implementation slices

Slice 1: scaffolding — `exceptions.py`, `registry.py`, `py.typed`, package re-exports, package logger.

Slice 2: `DjangoType` with scalar field conversion only, enough to map `Category`.

Slice 3: relation conversion for FK / reverse / M2M, still without optimization.

Slice 4: `DjangoOptimizerExtension` with `select_related` / `prefetch_related`.

Slice 5: `only()` optimization.

Slice 6: the `get_queryset` + downgrade-to-`Prefetch` rule.

Slice 7: choice-field enum generation and enum caching.

Each slice should land with tests in the same change so package coverage remains at 100%.

## Open questions

Should the optimizer be opt-in via schema extensions or auto-attached whenever a `DjangoType` appears? Recommendation: opt-in, matching strawberry-graphql-django.

Should `id` auto-map to relay `GlobalID` behind a setting, similar to strawberry-graphql-django's `MAP_AUTO_ID_AS_GLOBAL_ID`? Recommendation: defer until relay support is implemented.

Do we want model-property optimization hints (`model_property`, `cached_model_property`) now? Recommendation: no; defer until the core optimizer exists.

## References

graphene-django Meta and registry foundation: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py:132-258`, `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/registry.py:1-42`

graphene-django field conversion coverage: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py:182-507`

strawberry-graphql-django type generation: `https://strawberry.rocks/docs/django/guide/types`

strawberry-graphql-django optimizer: `https://strawberry.rocks/docs/django/guide/optimizer`

strawberry-graphql-django custom-`get_queryset` / optimizer edge case: issue #572 and PR #583 on `strawberry-graphql/strawberry-django`
