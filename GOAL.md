# GOAL — the North Star

**This file is the destination.** Everything else in the repo describes where we are ([`TODAY.md`][today], [`docs/GLOSSARY.md`][glossary]), how to work ([`AGENTS.md`][agents], [`START.md`][start], [`docs/builder/BUILD.md`][build]), or what to do next ([`KANBAN.md`][kanban]). When a card, a spec, or a review disagrees with this file, this file wins until the maintainer changes it. Nothing here narrates what has shipped; that is the snapshot's job and it rots here.

## North star

`django-strawberry-framework` is **the DRF-shaped, `class Meta`-driven Django integration for Strawberry GraphQL**. The destination is the developer experience `django-graphene-filters` proved — declarative `Meta` classes, generated input and output types, filter / order / aggregate / fieldset sidecars, layered permissions including cascade visibility — on a Strawberry engine, with no Graphene runtime and no decorators on consumer classes. `django-graphene-filters` is the surface reference (what the schema author writes); `strawberry-graphql-django` is the behavioral reference for the engine side (optimizer downgrade rules, scalar conversion). Its `recipes` cookbook ([`recipes/schema.py`][cookbook-schema]) is the structural parent of the example below.

## How to continue the board from this file

1. Learn the repo: [`AGENTS.md`][agents] (law), [`START.md`][start] (context), [`docs/README.md`][docs-readme] (how consumers use it), [`docs/TREE.md`][tree] (where things live).
2. Pick the next card: the first `To Do` card in version order on [`KANBAN.md`][kanban]. Spec and slice mechanics are in [`docs/builder/BUILD.md`][build]; shipped behavior folds into the glossary, tree, and board in the closing slice.
3. Judge every card against this file before building it: it must move the `astronomy` app below closer to running verbatim, satisfy a success criterion, and violate no non-goal. A card that fails that test is a question for the maintainer, not a build.
4. Stop when the board is empty and the definition of done below holds.

## Definition of done

- **`0.1.0` beta.** Feature parity with the overlap of `graphene-django` and `strawberry-graphql-django`. A feature both ship is foundational; a feature only one ships is optional and earns its own card or none.
- **`0.1.x`.** The Layer-3 sidecars land one card each (`FieldSet`, search, aggregates, redaction, explain mode, migration guides, the adversarial suite), until the `astronomy` app runs as written.
- **`1.0.0` stable.** API freeze and strict SemVer from here. The `astronomy` app and the cookbook port both run verbatim against a production-profile mount, the production security profile in [`docs/README.md`][docs-readme] is package-enforced or documented row by row, coverage stays at 100%, and every migration guide has been walked from a real upstream project.
- **Wide production ready** means a Django team can adopt it from the docs alone, deploy it behind the documented mount, and never hand-build schema machinery this package exists to generate.

## What success looks like in your code

At `1.0.0`, a single Django app — call it `astronomy`, one parent model (`Galaxy`) and one child model (`CelestialBody`) — is laid out across seven short files. Nothing is hand-rolled that the package can generate. This app is the acceptance test for the whole project: when it runs as written, the destination is reached. Every symbol below has a [`docs/GLOSSARY.md`][glossary] entry answering "is this shipped today, and what exactly does it do?" (start at its [Index][glossary-index], e.g. [`#filterset`][glossary-filterset]).

```bash
apps/astronomy/
├── models.py        # Django models
├── schema.py        # DjangoType nodes + Query + the schema
├── mutations.py     # DjangoMutation writes + Mutation
├── filters.py       # FilterSet + RelatedFilter        (filterset_class)
├── orders.py        # OrderSet + RelatedOrder          (orderset_class)
├── aggregates.py    # AggregateSet + RelatedAggregate  (aggregate_class)
└── fields.py        # FieldSet                         (fields_class)
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
```

### `schema.py`

One `DjangoType` per model, each with the full `class Meta` sidecar declaration pointing at the sibling files below. `get_queryset` is the DRF-style visibility hook, composed with `apply_cascade_permissions` so one row-level rule covers direct lookups, connection pagination, nested relation traversal, and the mutation locate.

```python
import strawberry
from strawberry import relay

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoNodeField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    apply_cascade_permissions,
    finalize_django_types,
    strawberry_config,
)

from . import aggregates, filters, models, orders
from . import fields as fieldsets
from .mutations import Mutation


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
        """Staff see everything; everyone else sees public rows behind the cascade."""
        user = getattr(getattr(info.context, "request", None), "user", None)
        if user and user.is_staff:
            return queryset
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
        """Staff see everything; everyone else sees public rows behind the cascade.

        The cascade narrows through the non-null ``galaxy`` FK, so a visible
        body can never point at a galaxy the viewer cannot see (and a nested
        ``galaxy { ... }`` selection can never raise ``RelatedObjectDoesNotExist``).
        """
        user = getattr(getattr(info.context, "request", None), "user", None)
        if user and user.is_staff:
            return queryset
        return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


@strawberry.type
class Query:
    galaxy: GalaxyNode | None = DjangoNodeField(GalaxyNode)
    all_galaxies: DjangoConnection[GalaxyNode] = DjangoConnectionField(GalaxyNode)

    celestial_body: CelestialBodyNode | None = DjangoNodeField(CelestialBodyNode)
    all_celestial_bodies: DjangoConnection[CelestialBodyNode] = DjangoConnectionField(CelestialBodyNode)


finalize_django_types()
_optimizer = DjangoOptimizerExtension(strictness="raise")
schema = DjangoSchema(
    query=Query,
    mutation=Mutation,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
```

### `mutations.py` — declarative writes

One `DjangoMutation` per operation; the `Input` / `PartialInput` types, the `FieldError` envelope, and the deny-by-default `DjangoModelPermission` check are generated. The form and DRF-serializer flavors share this exact shape via `Meta.form_class` / `Meta.serializer_class`.

```python
import strawberry

from django_strawberry_framework import DjangoMutation, DjangoMutationField

from . import models


class CreateCelestialBody(DjangoMutation):
    class Meta:
        model = models.CelestialBody
        operation = "create"


class UpdateCelestialBody(DjangoMutation):
    class Meta:
        model = models.CelestialBody
        operation = "update"


class DeleteCelestialBody(DjangoMutation):
    class Meta:
        model = models.CelestialBody
        operation = "delete"


@strawberry.type
class Mutation:
    create_celestial_body = DjangoMutationField(CreateCelestialBody)
    update_celestial_body = DjangoMutationField(UpdateCelestialBody)
    delete_celestial_body = DjangoMutationField(DeleteCelestialBody)
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
    return getattr(getattr(info.context, "request", None), "user", None)


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

That is the entire `astronomy` app: **seven files, about 370 lines of consumer code**, shipping a Relay-node GraphQL API with filtering and ordering across every field and the FK relation; per-field aggregates with a custom stat; per-field redaction, denial, and tiered visibility; cascade row-level permissions; search across two fields plus the relation; create / update / delete with generated inputs and a shared error envelope; choice-enum generation for `body_type`; FK-id elision for `{ celestialBody { galaxy { id } } }`; and N+1-safe planning across every nested selection, with `strictness="raise"` turning any miss into a test failure. Which of these run today is [`TODAY.md`][today]'s question; which card brings each remaining one is [`KANBAN.md`][kanban]'s.

## Migration shape

The audience is teams who already know one of three stacks. Each migration is a small `class Meta` shape change on top of code they already have; the full guides are a board card, these are the shapes they must preserve.

### Coming from `graphene-django`

`DjangoObjectType` becomes `DjangoType`, the Graphene runtime goes, the N+1 optimizer arrives:

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

`DjangoListField` keeps its name and its one-line shape. `Meta.filterset_class` / `orderset_class` / `fields_class` / `search_fields` declarations carry over verbatim: same mental model, different import line and engine.

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

An unregistered relation target raises at `finalize_django_types()` here, where upstream silently substitutes a `pk`-only stub. That is deliberate and a non-goal guards it.

### Coming from DRF + `django-filter`

An existing `django_filters.FilterSet` migrates with a one-line parent-class swap: the package's `FilterSet` **is** a `django_filters.filterset.BaseFilterSet` subclass, so every `Filter` / `FilterMethod` / form-cleaning primitive carries over unchanged. An existing `ModelSerializer` or `ModelForm` becomes a mutation by naming it in `Meta`, and all three mutation flavors share one `FieldError` envelope.

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


# The DRF-serializer mutation flavor (the model-driven one is in `astronomy/mutations.py` above):
class CreateCategoryFromSerializer(SerializerMutation):
    class Meta:
        serializer_class = CategorySerializer
        operation = "create"
    # Generated input drops the read-only `id`: CategorySerializerInput { name: String! }
```

GraphQL becomes another transport for the same business logic — no parallel field definitions, no re-validated payloads, no duplicate filter declarations.

## Success criteria

The project hits the goal when a Django developer can:

1. **Define rich model-backed GraphQL types with `DjangoType`** — model, fields, interfaces, sidecars, permissions, and `get_queryset`, all in one nested `class Meta`.
2. **Expose model collections with `DjangoConnectionField` or `DjangoListField`** without hand-written list resolvers.
3. **Add nested filtering / ordering / aggregation / search** without hand-built input or output types.
4. **Enforce row, field, and cascade permissions declaratively** — the same hook covers reads and writes.
5. **Rely on automatic ORM optimization** — nested GraphQL selections get the right `select_related` / `prefetch_related` / `only()` plan from one selection-tree walk that cooperates with consumer-shaped querysets.
6. **Write mutations declaratively from `ModelForm`, `ModelSerializer`, or auto-generated `Input` types** — one shared `errors: [FieldError!]!` envelope across every flavor, `Upload` for `FileField` / `ImageField`, deny-by-default write permissions, and a transaction that spans the response.
7. **Migrate from `graphene-django`, `strawberry-graphql-django`, `django-graphene-filters`, or DRF + `django-filter`** without bringing the source package along. The import-only promise covers `Meta`-driven domain declarations; project-level engine configuration (`extensions=`, the `GRAPHENE` settings block) migrates by documented recipe.
8. **Deploy it internet-facing from the docs alone** — the production security profile is the package's default posture, not a checklist the consumer discovers after an incident.

The project misses the goal if users must routinely hand-build the same schema machinery the package is supposed to generate, or must read the source to deploy it safely.

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

- **Fakeshop** (`examples/fakeshop/`) grows into the full Relay-shaped showcase: every sidecar the `astronomy` app declares, every mutation flavor, session auth, file and image uploads, and the sharded multi-database mode, each exercised by live `/graphql/` tests. It stays a development fixture and never a deployment.
- **Cookbook parity**: a Strawberry port of `django-graphene-filters`'s [`recipes/schema.py`][cookbook-schema] — same node graph (object types, attributes, values), same sidecar shape, equivalent capabilities. The `astronomy` app is the two-model reduction of that port; the full cookbook is the proof.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: AGENTS.md
[kanban]: KANBAN.md
[start]: START.md
[today]: TODAY.md

<!-- docs/ -->
[docs-readme]: docs/README.md
[glossary]: docs/GLOSSARY.md
[glossary-filterset]: docs/GLOSSARY.md#filterset
[glossary-index]: docs/GLOSSARY.md#index
[tree]: docs/TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build]: docs/builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[cookbook-schema]: https://github.com/riodw/django-graphene-filters/blob/master/examples/cookbook/cookbook/recipes/schema.py
