# Today

This document is the current-state playbook for the local fakeshop example. It is intentionally hyper-specific to `examples/fakeshop/products/schema.py` and answers: “what can this package do in the example project right now?”

For the package-wide capability catalog, shipped/planned feature status, optimizer hints, strictness modes, and future work, see [`docs/FEATURES.md`](docs/FEATURES.md).

## Current fakeshop state

- `examples/fakeshop/products/schema.py` still exposes a placeholder `hello` field.
- The large commented design in `examples/fakeshop/products/schema.py` is intentionally ahead of the shipped package.
- The package can support a practical list-based schema for the fakeshop product models today.
- The best current fakeshop shape is a bidirectional list-based graph: root list fields for each model, with FK and reverse-FK traversal across `Category`, `Item`, `Property`, and `Entry`.

The commented rich fakeshop design is not directly usable yet because it depends on unshipped APIs and features:

- `DjangoConnectionField`
- `apply_cascade_permissions`
- `Meta.interfaces`
- `Meta.filterset_class`
- `Meta.orderset_class`
- `Meta.aggregate_class`
- `Meta.fields_class`
- `Meta.search_fields`
- Relay node and connection integration

## What to put in `examples/fakeshop/products/schema.py` today
Replace the placeholder with list-based Strawberry query fields using `DjangoType` and manual root resolvers that return Django `QuerySet`s.
Use this bidirectional schema:
```python
import strawberry

from django_strawberry_framework import DjangoType

from . import models


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


class ItemType(DjangoType):
    class Meta:
        model = models.Item
        fields = (
            "id",
            "name",
            "description",
            "category",
            "entries",
            "is_private",
            "created_date",
            "updated_date",
        )


class PropertyType(DjangoType):
    class Meta:
        model = models.Property
        fields = (
            "id",
            "name",
            "description",
            "category",
            "entries",
            "is_private",
            "created_date",
            "updated_date",
        )


class EntryType(DjangoType):
    class Meta:
        model = models.Entry
        fields = (
            "id",
            "value",
            "description",
            "property",
            "item",
            "is_private",
            "created_date",
            "updated_date",
        )


@strawberry.type
class Query:
    @strawberry.field
    def all_categories(self) -> list[CategoryType]:
        return models.Category.objects.all()

    @strawberry.field
    def all_items(self) -> list[ItemType]:
        return models.Item.objects.all()

    @strawberry.field
    def all_properties(self) -> list[PropertyType]:
        return models.Property.objects.all()

    @strawberry.field
    def all_entries(self) -> list[EntryType]:
        return models.Entry.objects.all()


__all__ = ("Query",)
```

## What to put in `examples/fakeshop/schema.py` today
Enable the optimizer at the project schema boundary and finalize all imported `DjangoType`s before constructing the Strawberry schema:
```python
import strawberry
from products.schema import Query as ProductsQuery
from library.schema import Query as LibraryQuery

from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types


finalize_django_types()


@strawberry.type
class Query(LibraryQuery, ProductsQuery):
    """Top-level Query — extends each app's Query."""


schema = strawberry.Schema(
    query=Query,
    extensions=[DjangoOptimizerExtension()],
)
```

## What fakeshop model fields work today
For the fakeshop product models, `DjangoType` can currently generate:
- `BigAutoField` and IDs -> `int`
- `TextField` -> `str`
- `BooleanField` -> `bool`
- `DateTimeField` -> `datetime.datetime`
- `ForeignKey` -> related `DjangoType`
- reverse FK -> `list[RelatedType]`

Use these bidirectional relations in the current fakeshop schema:
- `Item.category`
- `Property.category`
- `Entry.item`
- `Entry.property`
- `Category.items`
- `Category.properties`
- `Item.entries`
- `Property.entries`

## Optimized fakeshop queries that work today

If the fakeshop root resolvers return `QuerySet`s and `examples/fakeshop/schema.py` uses `DjangoOptimizerExtension()`, nested selections are optimized.

Example:

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

Expected behavior: `select_related("category")`.

Example:

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

Expected behavior: nested `select_related` paths and `only()` projections.

## Optional fakeshop visibility filtering today

Because automatic connection/query fields do not exist yet, fakeshop root query fields are manual. If a root fakeshop list should apply public/staff visibility rules, call the type hook from the root resolver yourself.

Example:

```python
class ItemType(DjangoType):
    class Meta:
        model = models.Item
        fields = ("id", "name", "description", "category", "is_private")

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        user = getattr(info.context, "user", None)
        if user and user.is_staff:
            return queryset
        return queryset.filter(is_private=False)


@strawberry.type
class Query:
    @strawberry.field
    def all_items(self, info) -> list[ItemType]:
        return ItemType.get_queryset(models.Item.objects.all(), info)
```

Relation traversal to a type with custom `get_queryset` is handled by the optimizer with a `Prefetch` downgrade, so target visibility filters are not bypassed by raw joins.

## What the fakeshop example should wait for

Do not turn the commented rich fakeshop design into active code until the features it depends on ship. In practice, that means waiting for:
- `DjangoConnectionField`
- Relay node and connection support
- filters, ordering, aggregates, and fieldsets
- search fields
- permission cascade helpers
