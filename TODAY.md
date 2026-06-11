# Today

`TODAY.md` is the current-state playbook for **what `django-strawberry-framework` (the package) can do right now**, demonstrated through one canonical example: `examples/fakeshop/apps/products/`. It answers: "if I wire a model app with this package today, what works?"

> **Scope of this file — keep it this way.** This document is about **package capabilities**, not the example apps. `products` is the *single canonical demonstration vehicle* and the only app this file talks about. The other fakeshop apps (`library`, `scalars`, `kanban`, `glossary`) deliberately re-exercise the same package surface against different model shapes — cataloguing them here would only repeat these capabilities. Do **not** broaden this file to enumerate the other apps; keep every example and edit products-centric and capability-focused.
>
> For the package-wide capability catalog, shipped/planned status, optimizer hints, strictness modes, and future work, see [`docs/GLOSSARY.md`][glossary].

## What products demonstrates today

`examples/fakeshop/apps/products/` is a full model-backed GraphQL app over `Category` / `Item` / `Property` / `Entry`. As of `0.0.8` it exercises, end to end, the package capabilities a real consumer reaches for:

- **`DjangoType` schema** — four types configured entirely through `class Meta` (`model` + `fields`), with forward-FK + reverse-FK traversal and four root list resolvers (`allCategories` / `allItems` / `allProperties` / `allEntries`).
- **Relay nodes** — every type declares `Meta.interfaces = (relay.Node,)`, so each `id` is a Relay `GlobalID` (own-PK GlobalID filtering, `node(id:)` refetch shape). As of `0.0.9` the default `GlobalID` payload is the Django model label (`products.item:<pk>`) rather than the GraphQL type name, so a `CategoryType` → `ProductCategoryType` rename no longer invalidates cached IDs; `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` select `model` (default) / `type` (legacy opt-out) / `type+model` (transitional) / callable.
- **Filtering** — `Meta.filterset_class` on every type (declared in `apps/products/filters.py`), surfaced on each root resolver via a `filter:` argument from `filter_input_type(...)`. Includes a per-field `check_name_permission` denial gate on `CategoryFilter` (active-input-only).
- **Ordering** — `Meta.orderset_class` on every type (declared in `apps/products/orders.py`), surfaced via an `orderBy:` argument from `order_input_type(...)`. Includes the matching `check_name_permission` gate on `CategoryOrder`.
- **Optimizer cooperation** — root resolvers return `QuerySet`s, so `DjangoOptimizerExtension` plans `select_related` / `prefetch_related` / `only()` across nested selections without per-resolver boilerplate.
- **Filter + order composition** — each resolver chains `<Type>.get_queryset(queryset, info)` → `<Type>Filter.apply_sync(filter, queryset, info)` → `<Type>Order.apply_sync(order_by, queryset, info)` (visibility scopes, filter narrows, order arranges).

The live `/graphql/` HTTP suite at `examples/fakeshop/test_query/test_products_api.py` pins all of the above end to end.

## What's in `products/schema.py` today

A representative slice — one type and its resolver. The full file declares all four types and all four resolvers the same way:

```python
import strawberry
from strawberry import relay

from django_strawberry_framework import DjangoType
from django_strawberry_framework.filters import filter_input_type
from django_strawberry_framework.orders import order_input_type

from . import filters, models, orders


class CategoryType(DjangoType):
    class Meta:
        model = models.Category
        fields = (
            "id",
            "name",
            "description",
            "items",
            "properties",
            "is_private",
            "created_date",
            "updated_date",
        )
        interfaces = (relay.Node,)
        filterset_class = filters.CategoryFilter
        orderset_class = orders.CategoryOrder
        # Future Layer-3 keys — uncomment each as the relevant card ships:
        # search_fields = ("name", "description")        # 0.1.2
        # aggregate_class = aggregates.CategoryAggregate # 0.1.3
        # fields_class = fieldsets.CategoryFieldSet      # 0.1.1


@strawberry.type
class Query:
    @strawberry.field
    def all_categories(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters.CategoryFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.CategoryOrder)] | None = None,
    ) -> list[CategoryType]:
        queryset = CategoryType.get_queryset(models.Category.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters.CategoryFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.CategoryOrder.apply_sync(order_by, queryset, info)
        return queryset
```

## What to put in `config/schema.py` today

Enable the optimizer at the project-schema boundary and finalize every imported `DjangoType` before constructing the Strawberry schema:

```python
import strawberry
from apps.products.schema import Query as ProductsQuery

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    finalize_django_types,
    strawberry_config,
)


@strawberry.type
class Query(ProductsQuery):
    """Top-level Query — extend with each app's Query as bases."""


finalize_django_types()

_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
```

Two rules the package enforces: `finalize_django_types()` must run **after** every module that defines `DjangoType` classes is imported and **before** `strawberry.Schema(...)` is constructed; and the optimizer is added as a module-level `DjangoOptimizerExtension` singleton wrapped in a factory (`extensions=[lambda: _optimizer]`), which preserves the instance-bound plan cache and emits no deprecation warning.

## Package scalar conversions

`DjangoType` converts these model fields to Strawberry scalars. **Products exercises the integer / text / boolean / datetime subset** (its models are `TextField` / `BooleanField` / `DateTimeField` + FK + the `BigAutoField` PK); the remaining conversions are package capabilities covered by the package test suite.

- `BigAutoField` / `AutoField` / `IntegerField` → `int`  *(products: every PK)*
- `TextField` / `CharField` → `str`  *(products: `name` / `value` / `description`)*
- `BooleanField` → `bool`  *(products: `is_private`)*
- `DateTimeField` / `DateField` / `TimeField` / `DurationField` → Python-native time types  *(products: `created_date` / `updated_date`)*
- `BigIntegerField` / `PositiveBigIntegerField` → `BigInt` (JSON-safe string-serialized; `PositiveBigIntegerField` switched from `int` to `BigInt` in `0.0.6` — breaking wire-format change)
- `DecimalField` → `decimal.Decimal`
- `FloatField` → `float`
- `UUIDField` → `uuid.UUID`
- `BinaryField` → `bytes`
- `FileField` / `ImageField` → `str`
- `JSONField` → `strawberry.scalars.JSON`
- PostgreSQL `ArrayField` → `list[T]` (recursive through `field.base_field`; soft-registered when `django.contrib.postgres.fields` imports)
- PostgreSQL `HStoreField` → `strawberry.scalars.JSON` (soft-registered)
- `null=True` → `T | None`
- `CharField` / `TextField` with `choices` → generated Strawberry enum
- Relay `GlobalID` when `Meta.interfaces = (relay.Node,)` is declared  *(products: every type)*

## Package relation conversions

- forward `ForeignKey` → related `DjangoType`  *(products: `Item.category` / `Property.category` / `Entry.item` / `Entry.property`)*
- reverse `ForeignKey` → `list[RelatedType]`  *(products: `Category.items` / `Category.properties` / `Item.entries` / `Property.entries`)*
- forward `OneToOneField` → related `DjangoType` or `None`
- reverse `OneToOneField` → related `DjangoType` or `None`
- forward `ManyToManyField` → `list[RelatedType]`
- reverse `ManyToManyField` → `list[RelatedType]`

Products' graph is FK-only; `OneToOneField` and `ManyToManyField` conversions are package capabilities covered by the package test suite.

## Optimized products queries that work today

Root resolvers return `QuerySet`s and `config/schema.py` adds `DjangoOptimizerExtension`, so nested selections are planned into one ORM query.

```graphql
{
  allItems {
    name
    category {
      name
    }
  }
}
```

Expected: `select_related("category")`.

```graphql
{
  allEntries {
    value
    item {
      name
      category {
        name
      }
    }
    property {
      name
      category {
        name
      }
    }
  }
}
```

Expected: nested `select_related` paths and `only()` projections.

## Filtering and ordering on products today

Both ship in `0.0.8` and are wired on every products resolver. `filter:` narrows, `orderBy:` arranges, and they compose:

```graphql
{
  allItems(
    filter: {
      category: {
        id: {
          exact: "<GlobalID: base64 of products.category:<pk>>"
        }
      }
    }
    orderBy: [
      {
        name: ASC
      }
    ]
  ) {
    name
    category {
      name
    }
  }
}
```

`CategoryFilter` / `CategoryOrder` additionally declare a `check_name_permission` gate, so an anonymous request that filters or orders by `Category.name` is denied — the gate fires only when the input actually names the gated field (active-input-only scope).

> **Breaking wire-format change in `0.0.9` (the model-anchored `GlobalID` default).** Through `0.0.8` a products `GlobalID` was the base64 of `<GraphQL type name>:<pk>` (`CategoryType:42`). As of `0.0.9` the default is the Django model label (`products.category:42`), so **every emitted products `GlobalID` changes** and the filter examples above use the model-label payload. This is parallel to the `PositiveBigIntegerField → BigInt` `0.0.6` breaking-wire-format change above; it is acceptable pre-`1.0.0` and there is a clean per-type / project-wide opt-out (`type` reproduces the byte-identical pre-`0.0.9` payload). In `0.0.9` the break lands **live** alongside its consumer — root `node(id:)` / `nodes(ids:)` (`DONE-032-0.0.9`) decode every emitted ID, so every old client-cached type-anchored ID is undecodable under the `model` default the moment the upgrade deploys. The migration-safe upgrade sequence for a deployed schema:
>
> 1. Deploy `RELAY_GLOBALID_STRATEGY = "type+model"` **while the old GraphQL type names still exist** — new IDs emit model-anchored, old type-anchored IDs still decode.
> 2. Let clients receive model-label IDs and age out the cached old type-name IDs.
> 3. **Only then** rename GraphQL types (or `Meta.name`) or flip to `model`.
>
> The step-3 ordering is load-bearing: `type+model` decodes an old type-anchored ID only while its old GraphQL type name still resolves. Renaming a type / `Meta.name` *during* the window still orphans cached old-type-name IDs — `type+model` is a strategy bridge, **not** a rename-history alias map (that is `BACKLOG.md` item 39). A consumer who must rename mid-window owns a consumer alias / callable migration until then.

## Visibility filtering via `get_queryset`

Automatic connection/query fields do not exist yet, so root resolvers are manual — which means a root list applies visibility rules by calling the type's `get_queryset` hook itself (already part of the filter/order chain above):

```python
class ItemType(DjangoType):
    class Meta:
        model = models.Item
        fields = (
            "id",
            "name",
            "description",
            "category",
            "is_private",
        )

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        user = getattr(info.context, "user", None)
        if user and user.is_staff:
            return queryset
        return queryset.filter(is_private=False)
```

Relation traversal into a type with a custom `get_queryset` is handled by the optimizer with a `Prefetch` downgrade, so target visibility filters are not bypassed by raw joins. (The `products/schema.py` types carry commented cascade-permission `get_queryset` hooks that activate once the permissions card ships — see below.)

## What products is still waiting for

Products grows toward its `1.0.0` Relay shape as these unshipped surfaces land (tracked in [`KANBAN.md`][kanban]). Filtering and ordering are **not** on this list — they shipped in `0.0.8` and are wired today. `DjangoConnectionField` (Relay connections) is **not** on this list either — it shipped in `0.0.9`; products lights it up at fakeshop activation (`TODO-BETA-051-0.1.5`).

- permissions / `apply_cascade_permissions` (`0.0.10`: `TODO-ALPHA-033-0.0.10`) — activates the commented cascade `get_queryset` hooks in `products/schema.py`
- `Meta.fields_class` — `FieldSet` (`0.1.1`)
- `Meta.search_fields` (`0.1.2`)
- `Meta.aggregate_class` — aggregation (`0.1.3`)

## Shipped package capabilities not exercised by products

These ship today but products' model shapes don't reach them; they're covered by the package test suite (see [`docs/GLOSSARY.md`][glossary]):

- **`Meta.primary`** (shipped `0.0.6`) — multiple `DjangoType` subclasses per model with one explicit primary. Products declares one type per model. See [`docs/GLOSSARY.md#metaprimary`][glossary-metaprimary].
- **Consumer override semantics for scalar fields** (shipped `0.0.6`) — annotation-only and `strawberry.field` scalar overrides bypass `convert_scalar`; `relay.Node` `id` collisions raise `ConfigurationError` at type-creation time. Products exercises no scalar override. See [`docs/GLOSSARY.md#scalar-field-override-semantics`][glossary-scalar-field-override-semantics].
- **OneToOne / M2M relation conversion, choice-enum generation, and the specialized scalar conversions** (`BigInt`, `JSON`, `UUID`, `Decimal`, `Array`, `HStore`) — products has no OneToOne, M2M, `choices`, or those field types.
- **`Meta.nullable_overrides` / `Meta.required_overrides`** (shipped `0.0.9`) — force a scalar field's GraphQL nullability independent of its Django column (`T!`→`T` or `T`→`T!`), scalar-only, validated at type creation. Products declares no override; the library app's `NullabilityOverrideBookType` exercises both directions. See [`docs/GLOSSARY.md#metanullable_overrides`][glossary-metanullable_overrides].

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: KANBAN.md

<!-- docs/ -->
[glossary]: docs/GLOSSARY.md
[glossary-metanullable_overrides]: docs/GLOSSARY.md#metanullable_overrides
[glossary-metaprimary]: docs/GLOSSARY.md#metaprimary
[glossary-scalar-field-override-semantics]: docs/GLOSSARY.md#scalar-field-override-semantics

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
