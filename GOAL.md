# GOAL

## North star

`django-strawberry-framework` should be **the DRF-shaped, `class Meta`-driven Django integration for Strawberry GraphQL**. The destination is the developer experience proven by `django-graphene-filters` — declarative `Meta` classes, automatic input-type generation, rich filter / order / aggregate / fieldset sidecars, layered permissions including cascade visibility — on a modern Strawberry foundation, without Graphene runtime baggage.

For the shipped surface today, see [`docs/GLOSSARY.md`][glossary]. For the per-card sequencing toward this north star, see [`KANBAN.md`][kanban].

## What success looks like in your code

When the package is feature-complete at `1.0.0`, a single Django app — call it `astronomy`, with one parent model (`Galaxy`) and one child model (`CelestialBody`) — is laid out across six files. Every file is short. Nothing is hand-rolled that the package can generate.

> **Reading this as a glossary lookup**: every symbol you see below (`DjangoType`, `FilterSet`, `RelatedFilter`, `apply_cascade_permissions`, `Meta.filterset_class`, `Meta.orderset_class`, `Meta.aggregate_class`, `Meta.fields_class`, `Meta.search_fields`, `DjangoConnectionField`, `DjangoNodeField`, `OrderSet`, `RelatedOrder`, `AggregateSet`, `RelatedAggregate`, `FieldSet`, …) has a per-feature entry in [`docs/GLOSSARY.md`][glossary]. Use that file when a symbol is unfamiliar — it answers *"is this shipped today, and what exactly does it do?"* for every symbol shown below. The [alphabetical Index][glossary-index] at the top of `GLOSSARY.md` is the fastest entry point — every entry is deep-linked, so you can also URL-jump straight to e.g. [`#filterset`][glossary-filterset] or [`#metafilterset_class`][glossary-metafilterset-class].

```text
apps/astronomy/
├── models.py        # Django models
├── schema.py        # DjangoType nodes + Query
├── filters.py       # FilterSet + RelatedFilter (filterset_class)
├── orders.py        # OrderSet + RelatedOrder       (orderset_class)
├── aggregates.py    # AggregateSet + RelatedAggregate (aggregate_class)
└── fields.py        # FieldSet                     (fields_class)
```

### `models.py`

Standard Django — no GraphQL coupling. `CelestialBody.body_type` is a `TextChoices`-backed `CharField`; the package turns it into a Strawberry enum automatically.

```python
from django.db import models


class Galaxy(models.Model):
    name = models.TextField()
    description = models.TextField(blank=True, default="")
    is_private = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True, editable=False)
    updated_date = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        verbose_name = "Galaxy"
        verbose_name_plural = "Galaxies"

    def __str__(self):
        return self.name


class CelestialBody(models.Model):
    class BodyType(models.TextChoices):
        STAR = "STAR", "Star"
        PLANET = "PLANET", "Planet"
        MOON = "MOON", "Moon"
        ASTEROID = "ASTEROID", "Asteroid"

    name = models.TextField()
    description = models.TextField(blank=True, default="")
    body_type = models.CharField(
        max_length=16,
        choices=BodyType.choices,
        default=BodyType.PLANET,
    )
    galaxy = models.ForeignKey(
        Galaxy,
        related_name="celestial_bodies",
        on_delete=models.CASCADE,
    )
    is_private = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True, editable=False)
    updated_date = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        verbose_name = "Celestial Body"
        verbose_name_plural = "Celestial Bodies"

    def __str__(self):
        return self.name
```

### `schema.py`

One `DjangoType` per model, each with the full `class Meta` sidecar declaration. `Meta.filterset_class` / `orderset_class` / `aggregate_class` / `fields_class` / `search_fields` point at the four sibling files below. `get_queryset` is the DRF-style visibility hook, composed with `apply_cascade_permissions` so the same row-level rule applies to direct lookups, connection pagination, and nested relation traversal.

```python
import strawberry
from strawberry import relay

from django_strawberry_framework import (
    DjangoType,
    DjangoNodeField,
    DjangoConnection,
    DjangoConnectionField,
    apply_cascade_permissions,
    finalize_django_types,
    strawberry_config,
)

from . import aggregates, filters, models, orders
from . import fields as fieldsets


class GalaxyNode(DjangoType):
    class Meta:
        model = models.Galaxy
        fields = "__all__"
        interfaces = (relay.Node,)
        filterset_class = filters.GalaxyFilter
        orderset_class = orders.GalaxyOrder
        aggregate_class = aggregates.GalaxyAggregate
        fields_class = fieldsets.GalaxyFieldSet
        search_fields = ("name", "description")

    @classmethod
    def get_queryset(cls, queryset, info):
        """Staff or users with view_galaxy permission see everything; others see public only."""
        user = getattr(info.context, "user", None)
        if user and user.is_staff:
            return queryset
        if user and user.has_perm("astronomy.view_galaxy"):
            return queryset.filter(is_private=False)
        return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


class CelestialBodyNode(DjangoType):
    class Meta:
        model = models.CelestialBody
        fields = "__all__"
        interfaces = (relay.Node,)
        filterset_class = filters.CelestialBodyFilter
        orderset_class = orders.CelestialBodyOrder
        aggregate_class = aggregates.CelestialBodyAggregate
        fields_class = fieldsets.CelestialBodyFieldSet
        search_fields = ("name", "description", "galaxy__name", "galaxy__description")

    @classmethod
    def get_queryset(cls, queryset, info):
        """Staff or users with view_celestialbody permission see everything; others see public only."""
        user = getattr(info.context, "user", None)
        if user and user.is_staff:
            return queryset
        if user and user.has_perm("astronomy.view_celestialbody"):
            return queryset.filter(is_private=False)
        return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


@strawberry.type
class Query:
    galaxy: GalaxyNode = DjangoNodeField(GalaxyNode)
    all_galaxies: DjangoConnection[GalaxyNode] = DjangoConnectionField(GalaxyNode)

    celestial_body: CelestialBodyNode = DjangoNodeField(CelestialBodyNode)
    all_celestial_bodies: DjangoConnection[CelestialBodyNode] = DjangoConnectionField(CelestialBodyNode)


finalize_django_types()
schema = strawberry.Schema(query=Query, config=strawberry_config())
```

### `filters.py` — declarative filters (`filterset_class`)

`FilterSet` mirrors `django-filter`'s `FilterSet`. `Meta.fields` accepts the same `{"field": [lookups]}` dict shape and the `"__all__"` shorthand. `RelatedFilter` traverses across relations — accepts a class reference, an absolute import path string, or an unqualified name for circular cases. `check_*_permission` methods are per-field gates that the framework calls before applying the filter.

```python
from graphql import GraphQLError

from django_strawberry_framework.filters import FilterSet, RelatedFilter

from . import models


class GalaxyFilter(FilterSet):
    # Reverse FK — referenced lazily by string so Galaxy and CelestialBody
    # filtersets can live in the same file without an import cycle.
    celestial_bodies = RelatedFilter("CelestialBodyFilter", field_name="celestial_bodies")

    class Meta:
        model = models.Galaxy
        fields = {
            "name": "__all__",
            "description": ["exact", "icontains"],
        }

    def check_name_permission(self, request):
        """Only staff users may filter by Galaxy.name."""
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to filter by Galaxy name.")


class CelestialBodyFilter(FilterSet):
    # Explicit queryset acts as a security/scope boundary: nested filters can
    # narrow it but cannot escape "public galaxies only".
    galaxy = RelatedFilter(
        GalaxyFilter,
        field_name="galaxy",
        queryset=models.Galaxy.objects.filter(is_private=False),
    )

    class Meta:
        model = models.CelestialBody
        fields = {
            "name": ["exact", "icontains"],
            "description": ["exact", "icontains"],
            "body_type": ["exact", "in"],
            "galaxy__name": ["exact"],
        }
```

### `orders.py` — declarative ordering (`orderset_class`)

`OrderSet` generates the GraphQL `OrderBy` input from the same `Meta.fields` shape. `RelatedOrder` traverses relations — order by `galaxy.name` from a `CelestialBody` query, for example. `check_*_permission` gates apply the same way they do on filters.

```python
from graphql import GraphQLError

from django_strawberry_framework.orders import OrderSet, RelatedOrder

from . import models


class GalaxyOrder(OrderSet):
    celestial_bodies = RelatedOrder("CelestialBodyOrder", field_name="celestial_bodies")

    class Meta:
        model = models.Galaxy
        fields = "__all__"

    def check_name_permission(self, request):
        """Only staff users may order by Galaxy.name."""
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to order by Galaxy name.")


class CelestialBodyOrder(OrderSet):
    galaxy = RelatedOrder(GalaxyOrder, field_name="galaxy")

    class Meta:
        model = models.CelestialBody
        # Explicitly list only "name" and "body_type" — "description" is intentionally
        # excluded so consumers can't `ORDER BY description` (large TEXT column).
        fields = ["name", "body_type"]
```

### `aggregates.py` — declarative aggregates (`aggregate_class`)

`AggregateSet` generates a per-type output type carrying `count` / `min` / `max` / `mode` / `uniques` / custom stats. Aggregation runs from the filtered pre-pagination queryset, cooperates with `RelatedAggregate` traversal, and supports both sync and async `compute` paths. `get_child_queryset` lets a parent aggregate enforce a cascade rule on its children (here: drop private rows).

```python
from collections import Counter

from graphql import GraphQLError

from django_strawberry_framework.aggregates import AggregateSet, RelatedAggregate

from . import models


def _private_aware_child_qs(self, rel_name, rel_agg):
    """Shared get_child_queryset that excludes is_private=True rows when traversing."""
    qs = super(type(self), self).get_child_queryset(rel_name, rel_agg)
    target_model = rel_agg.aggregate_class.Meta.model
    if hasattr(target_model, "is_private"):
        qs = qs.filter(is_private=False)
    return qs


class GalaxyAggregate(AggregateSet):
    # Galaxy → CelestialBody (reverse FK)
    celestial_bodies = RelatedAggregate("CelestialBodyAggregate", field_name="galaxy")

    class Meta:
        model = models.Galaxy
        fields = {
            "name": ["count", "min", "max", "mode", "uniques"],
            "description": ["count", "min", "max"],
        }

    get_child_queryset = _private_aware_child_qs

    def check_name_uniques_permission(self, request):
        """Only staff can see the unique Galaxy-name distribution."""
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to view Galaxy name uniques.")


class CelestialBodyAggregate(AggregateSet):
    galaxy = RelatedAggregate(GalaxyAggregate, field_name="celestial_bodies")

    class Meta:
        model = models.CelestialBody
        fields = {
            "name": ["count", "min", "max", "mode", "uniques"],
            "body_type": ["count", "mode", "uniques", "type_breakdown"],
        }
        custom_stats = {
            "type_breakdown": str,   # custom stat — see compute_body_type_type_breakdown below
        }

    get_child_queryset = _private_aware_child_qs

    def compute_body_type_type_breakdown(self, queryset):
        """Custom stat: comma-separated `BODY_TYPE=count` breakdown across the filtered queryset."""
        counts = Counter(queryset.values_list("body_type", flat=True))
        return ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
```

### `fields.py` — declarative field-level behavior (`fields_class`)

`FieldSet` is where field-level permission gates, custom resolvers, and computed fields live. `resolve_<field>` overrides the generated resolver, `check_<field>_permission` is a denial gate that runs before resolve, and class-level annotations (`display_name: str | None`) declare computed fields the model doesn't have.

```python
import strawberry
from graphql import GraphQLError

from django_strawberry_framework.fieldset import FieldSet

from . import models


def _user(info):
    return getattr(info.context, "user", None)


def _resolve_date(dt, info, perm):
    """Tiered date visibility.

    Staff             → full datetime
    has_perm(view_*)  → day precision
    Authenticated     → month precision
    Anonymous         → year precision
    """
    user = _user(info)
    if user and user.is_staff:
        return dt
    if user and user.has_perm(perm):
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if user and user.is_authenticated:
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


class GalaxyFieldSet(FieldSet):
    display_name: str | None = strawberry.field(description="Computed: '{id} - {name}'")

    class Meta:
        model = models.Galaxy

    def resolve_description(self, root, info):
        """Staff sees description; everyone else gets an empty string."""
        user = _user(info)
        return root.description if user and user.is_staff else ""

    def resolve_display_name(self, root, info):
        """Computed field — visible to all signed-in users."""
        user = _user(info)
        return f"{root.id} - {root.name}" if user and user.is_authenticated else None

    def resolve_created_date(self, root, info):
        return _resolve_date(root.created_date, info, "astronomy.view_galaxy")

    def check_updated_date_permission(self, info):
        """Anonymous users cannot see updated_date at all — denial gate before resolve."""
        user = _user(info)
        if not user or not user.is_authenticated:
            raise GraphQLError("Login required to view updated date.")

    def resolve_updated_date(self, root, info):
        return _resolve_date(root.updated_date, info, "astronomy.view_galaxy")


class CelestialBodyFieldSet(FieldSet):
    display_name: str | None = strawberry.field(description="Computed: '{body_type}: {name}'")

    class Meta:
        model = models.CelestialBody

    def resolve_is_private(self, root, info):
        """Staff sees is_private; non-staff always gets False (redaction, not error)."""
        user = _user(info)
        return root.is_private if user and user.is_staff else False

    def resolve_display_name(self, root, info):
        user = _user(info)
        return f"{root.body_type}: {root.name}" if user and user.is_authenticated else None

    def resolve_created_date(self, root, info):
        return _resolve_date(root.created_date, info, "astronomy.view_celestialbody")

    def check_updated_date_permission(self, info):
        user = _user(info)
        if not user or not user.is_authenticated:
            raise GraphQLError("Login required to view updated date.")

    def resolve_updated_date(self, root, info):
        return _resolve_date(root.updated_date, info, "astronomy.view_celestialbody")
```

That is the entire `astronomy` app. **Six files, ~270 lines of consumer code total**, and it ships a richly-shaped Relay-node GraphQL API with: filtering across all fields and the FK relation; ordering across all fields and the FK relation; per-field aggregates with a custom stat; per-field redaction, denial, and tiered visibility; cascade row-level permissions; full-text-like search across two fields plus the relation; choice-enum generation for `body_type`; FK-id elision for `{ celestialBody { galaxy { id } } }`; N+1-safe queryset planning across every nested selection. The shipped `0.0.5` foundation already does the `DjangoType` half of this; the Layer-3 cards in [`KANBAN.md`][kanban] bring the four sidecar files online between now and `1.0.0`.

## Migration shape

The package's audience is teams who already know one of three stacks. Each migration story is a small `class Meta` shape change on top of code they already have.

### Coming from `graphene-django`

`DjangoObjectType` becomes `DjangoType`, you drop the Graphene runtime, and you gain the N+1 optimizer for free:

```diff
- from graphene_django import DjangoObjectType
+ from django_strawberry_framework import DjangoType, finalize_django_types

- class CategoryType(DjangoObjectType):
+ class CategoryType(DjangoType):
      class Meta:
          model = Category
          fields = ("id", "name")

+ finalize_django_types()
```

- `DjangoListField` replaces graphene-django's symbol of the same name with no shape change at the migration site: `all_branches: list[BranchType] = DjangoListField(BranchType)` is the same one-line declaration graphene-django consumers already type — the package picks up the consumer's class-attribute annotation for outer nullability and the type-level `get_queryset` keeps cooperating with the optimizer.

Your `Meta.filterset_class` / `Meta.orderset_class` / `Meta.fields_class` / `Meta.search_fields` declarations carry over verbatim. The mental model is identical; only the import line and the GraphQL engine underneath change.

### Coming from `strawberry-graphql-django`

The decorator becomes a nested `Meta` class — same Strawberry engine, Django-shaped configuration surface:

```diff
- import strawberry_django
+ from django_strawberry_framework import DjangoType, finalize_django_types

- @strawberry_django.type(Category)
- class CategoryType:
-     id: strawberry.auto
-     name: strawberry.auto
+ class CategoryType(DjangoType):
+     class Meta:
+         model = Category
+         fields = ("id", "name")

+ finalize_django_types()
```

The optimizer, scalar conversions, and relation resolution machinery are richer than the upstream's — plan caching, FK-id elision, queryset diffing, strictness mode for accidental N+1 detection. See [`docs/GLOSSARY.md`][glossary] for the enhancement catalog.

### Coming from DRF + `django-filter`

Your existing `django_filters.FilterSet` migrates to `Meta.filterset_class` via a one-line parent-class swap to `django_strawberry_framework.filters.FilterSet`; the package's `FilterSet` IS a `django_filters.filterset.BaseFilterSet` subclass, so every `Filter` / `FilterMethod` / form-cleaning primitive you already use carries over unchanged. The DRF `Serializer` becomes the basis for the auto-generated mutation `Input` type via `Meta.serializer_class`.

```python
from django_strawberry_framework.filters import FilterSet

# Your existing django-filter FilterSet — swap the parent class:
class CategoryFilter(FilterSet):
    class Meta:
        model = Category
        fields = ("name",)

# Your existing DRF ModelSerializer — no changes:
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name")

# New: one DjangoType declaration that reuses both, plus one mutation:
class CategoryType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name")
        filterset_class = CategoryFilter


class CreateCategory(DjangoMutation):
    class Meta:
        serializer_class = CategorySerializer
```

GraphQL becomes another transport for the same business logic — no parallel field definitions, no re-validated payloads, no duplicate filter declarations.

## Working reference

`django-graphene-filters` is the working feature-complete reference. The goal is not to copy its Graphene internals — it's to recreate **what the package enables for the schema author**: declarative filter / order / aggregate / fieldset sidecars, lazy related class references, generated input / output types with stable class-derived names, layered permissions including cascade visibility, async aggregate paths, and Relay-node-shaped output. The `Galaxy` / `CelestialBody` example above is a structural twin of the `django-graphene-filters` `recipes` cookbook (`ObjectType` / `Object` / `Attribute` / `Value`), reduced to two models so the shape stays legible. The per-feature shipped / planned breakdown lives in [`docs/GLOSSARY.md`][glossary].

## Success criteria

The project hits the goal when a Django developer can:

1. **Define rich model-backed GraphQL types with `DjangoType`** — model, fields, interfaces, sidecars, permissions, and `get_queryset`, all in one nested `class Meta`.
2. **Expose model collections with `DjangoConnectionField` or `DjangoListField`** without hand-written list resolvers.
3. **Add nested filtering / ordering / aggregation / search** without hand-built input or output types.
4. **Enforce row, field, and cascade permissions declaratively** — the same hook covers reads and writes.
5. **Rely on automatic ORM optimization** — nested GraphQL selections get the right `select_related` / `prefetch_related` / `only()` plan from one selection-tree walk that cooperates with consumer-shaped querysets.
6. **Write mutations declaratively from `ModelForm`, `ModelSerializer`, or auto-generated `Input` types** — one shared `errors: list[FieldError]` envelope across every flavor, plus `Upload` scalar for `FileField` / `ImageField`.
7. **Migrate from `graphene-django`, `strawberry-graphql-django`, `django-graphene-filters`, or DRF + `django-filter`** without bringing the source package along — the `Meta` mental model carries over; only the import line changes.

The project misses the goal if users must routinely hand-build the same schema machinery the package is supposed to generate.

## Non-goals

This package should not become:

- a thin wrapper around `strawberry-graphql-django`
- a direct port of Graphene internals
- a Graphene compatibility runtime
- a decorator-first framework
- an ORM abstraction layer that hides Django querysets
- a system that silently weakens rich relations into generic placeholders

The destination is a Django-native, Strawberry-powered framework that makes rich GraphQL schemas easy to build and efficient to execute.

## Target examples

Two example projects prove the goal:

- **Fakeshop** (`examples/fakeshop/`) grows from today's bidirectional list-based products demo + the rich library demo into the full Relay-shaped showcase: per-model connection fields with filter / order / aggregate / fieldset / search / cascade-permission sidecars; create / update / delete mutations driven by both Django `ModelForm`s and DRF `ModelSerializer`s; file / image upload mutations; auth mutations exercised by the existing test users; sharded multi-database stress mode.
- **Cookbook parity**: a Strawberry version of `django-graphene-filters`'s `recipes/schema.py` should be a clean port — same node graph (object types, attributes, values), same sidecar shape, equivalent capabilities. The astronomy example above is the structural reduction of that port; the full cookbook is the proof.

For the per-card sequencing of each capability, see [`KANBAN.md`][kanban].

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: KANBAN.md

<!-- docs/ -->
[glossary]: docs/GLOSSARY.md
[glossary-filterset]: docs/GLOSSARY.md#filterset
[glossary-index]: docs/GLOSSARY.md#index
[glossary-metafilterset-class]: docs/GLOSSARY.md#metafilterset_class

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
