# django-strawberry-framework

`django-strawberry-framework` is a DRF-shaped Django integration for Strawberry GraphQL. It lets Django teams build GraphQL APIs from Django models using the familiar `class Meta` style instead of a decorator-heavy surface.

For install, local development, testing, and the canonical documentation map, start from [`../README.md`](../README.md).

## Quick start

```python
import strawberry
from django_strawberry_framework import DjangoOptimizerExtension, DjangoType
from myapp.models import Category, Item


class CategoryType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name")


class ItemType(DjangoType):
    class Meta:
        model = Item
        fields = ("id", "name", "category")


@strawberry.type
class Query:
    @strawberry.field
    def all_items(self) -> list[ItemType]:
        return Item.objects.all()


schema = strawberry.Schema(
    query=Query,
    extensions=[DjangoOptimizerExtension()],
)
```

That is the shipped surface: `class Meta` configures the type, and the optimizer extension turns nested selections into Django ORM `select_related`, `prefetch_related`, and `only` calls. The current alpha requires relation target types to be declared before fields that reference them; definition-order independence is planned.

## Three-minute path

1. Define `DjangoType` classes for the Django models you want in GraphQL.
2. Return a Django `QuerySet` from a root Strawberry resolver.
3. Add `DjangoOptimizerExtension()` to the schema.
4. Query nested relations; the optimizer handles joins, prefetches, projections, and strictness checks.
5. Read [`FEATURES.md`](FEATURES.md) when you want the full capability catalog.

## Why this package exists

- Django developers already know `Meta.model`, `fields`, `exclude`, filtersets, serializers, and queryset hooks.
- Strawberry is the modern Python GraphQL engine, but its Django ecosystem is decorator-oriented.
- This package keeps the Strawberry engine while making the public API feel like DRF, django-filter, and Django itself.
- The package builds directly on Strawberry; it does not depend on `strawberry-graphql-django`.

## Today and coming next

Today:
- `DjangoType` for model-backed Strawberry types
- scalar, relation, and choice-enum conversion
- generated relation resolvers
- `get_queryset` visibility hook
- model/type registry
- `DjangoOptimizerExtension` for automatic ORM optimization
- `OptimizerHint` for per-field optimizer overrides
- `auto` re-export from Strawberry

Coming:
- fieldsets
- filters
- orders
- aggregates
- connection fields
- permissions and cascade permissions
- schema export helpers

## Optimizer behavior

The optimizer is opt-in and only changes root resolvers that return Django `QuerySet`s. It walks the selected GraphQL fields once, builds an ORM plan, then applies that plan without taking ownership of querysets you already shaped.

Shipped optimizer value:
- forward relations use `select_related`
- many-side relations use `prefetch_related`
- nested many-side selections become nested `Prefetch` objects
- scalar selections become `only` projections with connector columns preserved
- `category { id }` can read `category_id` from the parent row without a join
- resolver-defined `get_queryset` filters survive relation traversal through a `Prefetch` downgrade
- consumer-applied `select_related`, `prefetch_related`, and `Prefetch` entries are respected
- `strictness="warn"` or `strictness="raise"` helps catch accidental N+1s in development and tests

## Status

**Status: 0.0.3, single-maintainer.** Stable enough for internal tools and prototypes; not for production. Today's shipped names — `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `auto` — are intended to remain stable through `0.1.0`.

Expect the deferred `Meta` keys (`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`) to move from rejected to accepted as their subsystems ship. The registry will gain `Meta.primary` for multiple `DjangoType`s per model. None of those changes break code that uses today's surface.

## Contributor notes

Detailed package/test layout lives in [`TREE.md`](TREE.md). Future in-flight design work continues to use `docs/spec-<topic>.md`; once a slice ships, its behavior should be folded into [`FEATURES.md`](FEATURES.md) or `TREE.md` and the completed design doc should be archived.
