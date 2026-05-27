"""GraphQL schema for the fakeshop products app.

A bidirectional list-based graph over `Category` / `Item` / `Property` /
`Entry` using the shipped `DjangoType` surface. Each root field returns a
Django `QuerySet`, so `DjangoOptimizerExtension` (wired in
`config.schema`) plans `select_related` / `prefetch_related` / `only()`
across nested selections without per-resolver boilerplate.

The eventual `1.0.0` shape — Relay-node types with the cookbook-shaped
filter / order / aggregate / fields / search / permissions surface, a
1-to-1 port of the `django-graphene-filters` cookbook recipe — is
tracked in `KANBAN.md` under the Layer-3 cards (`TODO-ALPHA-021-0.0.8`
filters, `TODO-ALPHA-022-0.0.8` orders, `TODO-ALPHA-024-0.0.9` `DjangoConnectionField`,
`TODO-ALPHA-027-0.0.10` permissions, `TODO-BETA-038-0.1.1` fieldsets,
`TODO-BETA-039-0.1.2` search, `TODO-BETA-040-0.1.3` aggregates). Each `*Type`
class below carries commented-out future-shape Meta keys and methods —
uncomment each line as the corresponding card ships. Sidecar keys
(`filterset_class`, `orderset_class`, `aggregate_class`,
`fields_class`) additionally need a `filters.py` / `orders.py` /
`aggregates.py` / `fields.py` module under this app — the sibling
files are not yet present.
"""

# Future imports (uncomment as Layer-3 subsystems ship):
#
# from strawberry import relay                                       # works today (DONE-011)
# from django_strawberry_framework import DjangoConnectionField      # TODO-ALPHA-024-0.0.9
# from django_strawberry_framework import apply_cascade_permissions  # TODO-ALPHA-027-0.0.10
# from apps.products import aggregates, filters, orders              # TODO-ALPHA-021-0.0.8 (filters) + TODO-ALPHA-022-0.0.8 (orders) + TODO-BETA-040-0.1.3 (aggregates)
# from apps.products import fields as fieldsets                      # TODO-BETA-038-0.1.1

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
        # Future Layer-3 additions — uncomment each as the relevant card ships:
        # interfaces = (relay.Node,)                        # works today (DONE-011)
        # search_fields = ("name", "description")           # needs TODO-BETA-039-0.1.2
        # filterset_class = filters.CategoryFilter          # needs TODO-ALPHA-021-0.0.8 + filters.py
        # orderset_class = orders.CategoryOrder             # needs TODO-ALPHA-022-0.0.8 + orders.py
        # aggregate_class = aggregates.CategoryAggregate    # needs TODO-BETA-040-0.1.3 + aggregates.py
        # fields_class = fieldsets.CategoryFieldSet         # needs TODO-BETA-038-0.1.1 + fields.py

    # Future cascade-permission visibility hook — uncomment when TODO-ALPHA-027-0.0.10 ships:
    #
    # @classmethod
    # def get_queryset(cls, queryset, info):
    #     """Staff or users with view_category permission see everything; others see public only."""
    #     user = getattr(info.context, "user", None)
    #     if user and user.is_staff:
    #         return queryset
    #     elif user and user.has_perm("products.view_category"):
    #         return queryset.filter(is_private=False)
    #     return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


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
        # Future Layer-3 additions — uncomment each as the relevant card ships:
        # interfaces = (relay.Node,)                                                  # works today (DONE-011)
        # search_fields = ("name", "description", "category__name", "category__description")  # needs TODO-BETA-039-0.1.2
        # filterset_class = filters.ItemFilter           # needs TODO-ALPHA-021-0.0.8 + filters.py
        # orderset_class = orders.ItemOrder              # needs TODO-ALPHA-022-0.0.8 + orders.py
        # aggregate_class = aggregates.ItemAggregate     # needs TODO-BETA-040-0.1.3 + aggregates.py
        # fields_class = fieldsets.ItemFieldSet          # needs TODO-BETA-038-0.1.1 + fields.py

    # Future cascade-permission visibility hook — uncomment when TODO-ALPHA-027-0.0.10 ships:
    #
    # @classmethod
    # def get_queryset(cls, queryset, info):
    #     """Staff or users with view_item permission see everything; others see public only."""
    #     user = getattr(info.context, "user", None)
    #     if user and user.is_staff:
    #         return queryset
    #     elif user and user.has_perm("products.view_item"):
    #         return queryset.filter(is_private=False)
    #     return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


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
        # Future Layer-3 additions — uncomment each as the relevant card ships:
        # interfaces = (relay.Node,)                                                  # works today (DONE-011)
        # search_fields = ("name", "description", "category__name", "category__description")  # needs TODO-BETA-039-0.1.2
        # filterset_class = filters.PropertyFilter        # needs TODO-ALPHA-021-0.0.8 + filters.py
        # orderset_class = orders.PropertyOrder           # needs TODO-ALPHA-022-0.0.8 + orders.py
        # aggregate_class = aggregates.PropertyAggregate  # needs TODO-BETA-040-0.1.3 + aggregates.py
        # fields_class = fieldsets.PropertyFieldSet       # needs TODO-BETA-038-0.1.1 + fields.py

    # Future cascade-permission visibility hook — uncomment when TODO-ALPHA-027-0.0.10 ships:
    #
    # @classmethod
    # def get_queryset(cls, queryset, info):
    #     """Staff or users with view_property permission see everything; others see public only."""
    #     user = getattr(info.context, "user", None)
    #     if user and user.is_staff:
    #         return queryset
    #     elif user and user.has_perm("products.view_property"):
    #         return queryset.filter(is_private=False)
    #     return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


class EntryType(DjangoType):
    class Meta:
        model = models.Entry
        fields = (
            "id",
            "value",
            "description",  # Future: drop this entry to exercise field-level permission gating (TODO-ALPHA-027-0.0.10)
            "property",
            "item",
            "is_private",
            "created_date",
            "updated_date",
        )
        # Future Layer-3 additions — uncomment each as the relevant card ships:
        # interfaces = (relay.Node,)                                # works today (DONE-011)
        # search_fields = ("value", "property__name", "item__name") # needs TODO-BETA-039-0.1.2
        # filterset_class = filters.EntryFilter        # needs TODO-ALPHA-021-0.0.8 + filters.py
        # orderset_class = orders.EntryOrder           # needs TODO-ALPHA-022-0.0.8 + orders.py
        # aggregate_class = aggregates.EntryAggregate  # needs TODO-BETA-040-0.1.3 + aggregates.py
        # fields_class = fieldsets.EntryFieldSet       # needs TODO-BETA-038-0.1.1 + fields.py

    # Future cascade-permission visibility hook — uncomment when TODO-ALPHA-027-0.0.10 ships:
    #
    # @classmethod
    # def get_queryset(cls, queryset, info):
    #     """Staff or users with view_entry permission see everything; others see public only."""
    #     user = getattr(info.context, "user", None)
    #     if user and user.is_staff:
    #         return queryset
    #     elif user and user.has_perm("products.view_entry"):
    #         return queryset.filter(is_private=False)
    #     return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


@strawberry.type
class Query:
    """Fakeshop products app root fields."""

    # Future shape — once TODO-ALPHA-024-0.0.9 (`DjangoConnectionField` + Relay
    # `node()` root helpers) ships, the four `@strawberry.field` resolvers
    # below collapse into eight class-level attributes:
    #
    #     category: CategoryType = relay.node()
    #     all_categories: relay.ListConnection[CategoryType] = DjangoConnectionField(CategoryType)
    #
    #     item: ItemType = relay.node()
    #     all_items: relay.ListConnection[ItemType] = DjangoConnectionField(ItemType)
    #
    #     property: PropertyType = relay.node()
    #     all_properties: relay.ListConnection[PropertyType] = DjangoConnectionField(PropertyType)
    #
    #     entry: EntryType = relay.node()
    #     all_entries: relay.ListConnection[EntryType] = DjangoConnectionField(EntryType)
    #
    # The per-type `interfaces = (relay.Node,)` declarations in each
    # `*Type` class's Meta block above are what make `relay.node()` work
    # — uncomment those first.

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
