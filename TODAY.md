# Today

This document is the current-state playbook for the local fakeshop example. It is intentionally hyper-specific to `examples/fakeshop/apps/products/schema.py` and answers: “what can this package do in the example project right now?”

For the package-wide capability catalog, shipped/planned feature status, optimizer hints, strictness modes, and future work, see [`docs/GLOSSARY.md`][glossary].

## Current fakeshop state

Three example apps are wired today:

- `examples/fakeshop/apps/library/schema.py` — the **rich live demonstration** of the shipped surface. Seven `DjangoType` classes exercise, in one place: forward FK, reverse FK, forward OneToOne, reverse OneToOne, forward M2M, reverse M2M, choice-enum generation (`Book.circulation_status`), `Meta.interfaces = (relay.Node,)` on `GenreType`, `Meta.optimizer_hints` on `LoanType` (`OptimizerHint.prefetch_related()` + `OptimizerHint.SKIP`), a consumer-authored relation override on `Branch.shelves`, a consumer-shaped queryset cooperating with the optimizer (`all_library_prefetched_books` uses `select_related("shelf").prefetch_related("genres")`), and definition-order-independent finalization (the type declaration order is intentionally awkward — `LoanType` before `BookType` and `PatronType`, etc.). The live `/graphql/` HTTP tests in `examples/fakeshop/test_query/test_library_api.py` exercise all of these end-to-end, including the Relay GlobalID round trip via `test_library_relay_node_global_id_round_trips`. The `all_library_branches_via_list_field` root field added in `0.0.7` exercises `DjangoListField`'s default-resolver path — added as a sibling, no existing resolver was replaced. `Patron.lifetime_fines_cents` (`BigIntegerField`) added in `0.0.7` exercises the `BigIntegerField → BigInt` converter on a real-domain model, with a live HTTP test pinning the decimal-string wire format past `2**53 - 1`. The new `BranchFilter` / `ShelfFilter` / `BookFilter` / `LoanFilter` / `PatronFilter` declarations at `examples/fakeshop/apps/library/filters.py` (plus `GenreFilter` at `filters_genre.py` for the cross-module absolute-import-path case) and the 14 live `/graphql/` HTTP filter tests at `examples/fakeshop/test_query/test_library_api.py` exercise the `FilterSet` / `RelatedFilter` / `Meta.filterset_class` wiring end-to-end through finalizer phase 2.5.
- `examples/fakeshop/apps/products/schema.py` — the **minimal "wire up a model app today" demonstration**. A bidirectional list-based graph over `Category` / `Item` / `Property` / `Entry`: four `DjangoType` classes with FK + reverse-FK traversal and four root list resolvers (`all_categories`, `all_items`, `all_properties`, `all_entries`). Non-Relay; intentionally narrower than `library` to show the absolute minimum a consumer needs to type to get a model app queryable through GraphQL today.
- `examples/fakeshop/apps/scalars/schema.py` — the **converter-table coverage substrate** added in `0.0.7`. Two paired `DjangoType` classes: `ScalarSpecimenType` (all scalar fields non-null, plus a self-FK `parent` / reverse `children`) and `NullableScalarSpecimenType` (all scalar fields nullable, plus a cross-model FK `partner` to `ScalarSpecimen` with `on_delete=SET_NULL`, reverse-exposed on `ScalarSpecimenType.nullable_partners`). The pairing exercises Django's two-`CreateModel` initial migration path, package finalization across sibling `DjangoType` classes in one app, Strawberry type registration across sibling types, optimizer planning across two managed models in one query, and the only `SET_NULL` ondelete in the example tree. The live `/graphql/` HTTP tests in `examples/fakeshop/test_query/test_scalars_api.py` pin every non-trivial `SCALAR_MAP` entry in both nullable and non-null shapes — `BooleanField`, `FloatField`, `DecimalField`, `DateField`, `DateTimeField`, `TimeField`, `JSONField`, `UUIDField`, `BigIntegerField`, `PositiveBigIntegerField` — plus the self-FK and cross-model FK traversals. `ArrayField` and `HStoreField` are absent because the fakeshop runs on SQLite; their converter rows stay covered by `tests/`.

The eventual `1.0.0` shape for products — Relay `DjangoConnectionField`s with `filterset_class` / `orderset_class` / `aggregate_class` / `fields_class` / `search_fields` / `apply_cascade_permissions` — is tracked in `KANBAN.md` under the Layer-3 cards (`WIP-ALPHA-021-0.0.8` filters, `WIP-ALPHA-022-0.0.8` orders, `TODO-BETA-040-0.1.3` aggregates, `TODO-ALPHA-027-0.0.10` permissions, etc.). The list-based schema below is what's there today; the Relay shape grows in as those cards land.

The products design depends on these unshipped APIs and features to reach its `1.0.0` shape:

- `DjangoConnectionField`
- `apply_cascade_permissions`
- `Meta.filterset_class`
- `Meta.orderset_class`
- `Meta.aggregate_class`
- `Meta.fields_class`
- `Meta.search_fields`

## What's in `examples/fakeshop/apps/products/schema.py` today

This is the actual current contents of the products app's schema — list-based Strawberry query fields using `DjangoType` and manual root resolvers that return Django `QuerySet`s:
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

## What to put in `examples/fakeshop/config/schema.py` today
Enable the optimizer at the project schema boundary and finalize all imported `DjangoType`s before constructing the Strawberry schema:
```python
import strawberry
from apps.library.schema import Query as LibraryQuery
from apps.products.schema import Query as ProductsQuery
from apps.scalars.schema import Query as ScalarsQuery

from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types, strawberry_config


finalize_django_types()


@strawberry.type
class Query(LibraryQuery, ProductsQuery, ScalarsQuery):
    """Top-level Query — extends each app's Query."""


schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[DjangoOptimizerExtension()],
)
```

## What fakeshop model fields work today

Across the products, library, and scalars example apps, `DjangoType` currently generates:

Scalar conversions:
- `BigAutoField` / `AutoField` / `IntegerField` → `int`
- `BigIntegerField` / `PositiveBigIntegerField` → `BigInt` (JSON-safe string-serialized scalar; `PositiveBigIntegerField` switched from `int` to `BigInt` in `0.0.6` — breaking wire-format change)
- `TextField` / `CharField` → `str`
- `BooleanField` → `bool`
- `DateTimeField` / `DateField` / `TimeField` / `DurationField` → Python-native time types
- `DecimalField` → `decimal.Decimal`
- `FloatField` → `float`
- `UUIDField` → `uuid.UUID`
- `BinaryField` → `bytes`
- `FileField` / `ImageField` → `str`
- `JSONField` → `strawberry.scalars.JSON`
- PostgreSQL `ArrayField` → `list[T]` (recursive through `field.base_field`; soft-registered, only when `django.contrib.postgres.fields` imports successfully)
- PostgreSQL `HStoreField` → `strawberry.scalars.JSON` (soft-registered, only when `django.contrib.postgres.fields` imports successfully)
- `null=True` → `T | None`
- `CharField` / `TextField` with `choices` → generated Strawberry enum (live: `Book.circulation_status` in library)
- Relay `GlobalID` when `Meta.interfaces = (relay.Node,)` is declared (live: `GenreType` in library)

Relation conversions:
- forward `ForeignKey` → related `DjangoType`
- reverse `ForeignKey` → `list[RelatedType]`
- forward `OneToOneField` → related `DjangoType` or `None`
- reverse `OneToOneField` → related `DjangoType` or `None` (live: `Patron.card` in library)
- forward `ManyToManyField` → `list[RelatedType]` (live: `Book.genres` in library)
- reverse `ManyToManyField` → `list[RelatedType]` (live: `Genre.books` in library)

Products-catalog bidirectional relations exercised in the schema below:
- `Item.category` / `Property.category` / `Entry.item` / `Entry.property` (forward FK)
- `Category.items` / `Category.properties` / `Item.entries` / `Property.entries` (reverse FK)

Library bidirectional relations exercised live in `examples/fakeshop/apps/library/schema.py`:
- `Shelf.branch` / `Loan.book` / `Loan.patron` / `Book.shelf` / `MembershipCard.patron` (forward FK / OneToOne)
- `Branch.shelves` / `Patron.loans` / `Shelf.books` / `Book.loans` (reverse FK)
- `Patron.card` (reverse OneToOne, nullable)
- `Book.genres` / `Genre.books` (M2M, bidirectional)

## Optimized fakeshop queries that work today

If the fakeshop root resolvers return `QuerySet`s and `examples/fakeshop/config/schema.py` uses `DjangoOptimizerExtension()`, nested selections are optimized.

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
- filters, ordering, aggregates, and fieldsets
- search fields
- permission cascade helpers

## Shipped capabilities available but not currently demonstrated in fakeshop

- `Meta.primary` (shipped in `0.0.6`) — multiple `DjangoType` subclasses per Django model with one explicit primary. Fakeshop's `apps/products/schema.py` and `apps/library/schema.py` each declare one `DjangoType` per model, so the multi-type contract is not exercised in the example today; the feature is fully covered by the package test suite. See [`docs/GLOSSARY.md#metaprimary`][glossary-metaprimary].
- Consumer override semantics for scalar fields (shipped in `0.0.6`) — annotation-only and `strawberry.field` scalar overrides bypass `convert_scalar` validations, and `relay.Node` `id` collisions raise `ConfigurationError` at type-creation time. Fakeshop's `apps/products/schema.py` and `apps/library/schema.py` exercise the relation-override path (`Branch.shelves` in library) but no scalar override; the four-corner override matrix is fully covered by the package test suite. See [`docs/GLOSSARY.md#scalar-field-override-semantics`][glossary-scalar-field-override-semantics].

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: docs/GLOSSARY.md
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
