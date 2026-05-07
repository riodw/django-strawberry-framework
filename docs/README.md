# django-strawberry-framework

`django-strawberry-framework` is a DRF-shaped Django integration for Strawberry GraphQL. It lets Django teams build GraphQL APIs from Django models using the familiar `class Meta` style instead of a decorator-heavy surface.

For install, local development, testing, and the canonical documentation map, start from [`../README.md`](../README.md). For the long-term destination, see [`../GOAL.md`](../GOAL.md). For the current capability snapshot, see [`../TODAY.md`](../TODAY.md).

## Quick start

<!-- TODO(spec-foundation 0.0.4): when the foundation slice ships,
update this quick-start snippet per `docs/spec-foundation.md` Phase 10
so it shows the new `finalize_django_types()` call site at the
Spike-A-proven safe boundary. If finalization must happen before any
`@strawberry.type` class references a `DjangoType`, the snippet must call
the finalizer before decorating `Query`, not merely before
`strawberry.Schema(...)` construction. The alpha caveat below ("requires
relation target types to be declared before fields that reference them")
goes away in lockstep — definition-order independence is exactly what
this slice ships. -->

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

## What just happened?

- `class Meta` tells the package which Django model and fields become a Strawberry type.
- Returning a Django `QuerySet` from the root resolver gives the optimizer something it can shape.
- `DjangoOptimizerExtension()` walks the selected GraphQL fields once at the root and applies one ORM plan.
- Nested relations become joins, prefetches, projections, and strictness checks without replacing your queryset.
- [`FEATURES.md`](FEATURES.md) has the full capability catalog when you need details.

## Why this package exists

Django teams already think in `Meta.model`, `fields`, `exclude`, querysets, and DRF/django-filter idioms. Strawberry is the modern Python GraphQL engine, but its Django ecosystem leans on decorators. This package keeps Strawberry as the engine and the configuration shape consumers already know.

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

How this stacks up against the alternatives: see the [quick comparison in `FEATURES.md`](FEATURES.md#quick-comparison).

For a more narrative snapshot of what the package can do right now in the example project, see [`../TODAY.md`](../TODAY.md). For the full north-star goal, see [`../GOAL.md`](../GOAL.md).

## Optimizer behavior

The optimizer is opt-in and only changes root resolvers that return Django `QuerySet`s. It walks the selected GraphQL fields once, builds an ORM plan, then applies that plan without taking ownership of querysets you already shaped.

Shipped optimizer value:
- **Forward relations** use `select_related`.
- **Many-side relations** use `prefetch_related`.
- **Nested many-side selections** become nested `Prefetch` objects.
- **Scalar selections** become `only` projections with connector columns preserved.
- **`category { id }`** can read `category_id` from the parent row without a join.
- **Resolver-defined `get_queryset` filters** survive relation traversal through a `Prefetch` downgrade.
- **Consumer-shaped querysets** keep their existing `select_related`, `prefetch_related`, and `Prefetch` entries.
- **Strictness mode** can warn or raise when development/test queries would accidentally lazy-load.

## Status

**Status: 0.0.3, single-maintainer.** Stable enough for internal tools and prototypes; not for production. Today's shipped names — `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `auto` — are intended to remain stable through `0.1.0`. API names are the stability promise; correctness and edge-case behavior are still hardening.

Expect the deferred `Meta` keys (`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`) to move from rejected to accepted as their subsystems ship. The registry will gain `Meta.primary` for multiple `DjangoType`s per model. None of those changes break code that uses today's surface.

## Contributor notes

Detailed package/test layout lives in [`TREE.md`](TREE.md). Future in-flight design work continues to use `docs/spec-<topic>.md`; once a slice ships, its behavior should be folded into [`FEATURES.md`](FEATURES.md) or `TREE.md` and the completed design doc should be archived.
