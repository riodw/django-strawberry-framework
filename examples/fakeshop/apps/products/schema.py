"""GraphQL schema for the fakeshop products app.

A bidirectional list-based graph over `Category` / `Item` / `Property` /
`Entry` using the shipped `DjangoType` surface. Each root field returns a
Django `QuerySet`, so `DjangoOptimizerExtension` (wired in
`config.schema`) plans `select_related` / `prefetch_related` / `only()`
across nested selections without per-resolver boilerplate.

The eventual `1.0.0` shape — Relay-node types with the cookbook-shaped
filter / order / aggregate / fields / search / permissions surface, a
1-to-1 port of the `django-graphene-filters` cookbook recipe — is
tracked in `KANBAN.md` under the Layer-3 cards (`DONE-027-0.0.8`
filters, `DONE-028-0.0.8` orders, `TODO-ALPHA-024-0.0.9` `DjangoConnectionField`,
`TODO-ALPHA-027-0.0.10` permissions, `TODO-BETA-038-0.1.1` fieldsets,
`TODO-BETA-039-0.1.2` search, `TODO-BETA-040-0.1.3` aggregates). The
shipped `filterset_class` + `orderset_class` surface is wired below;
each `*Type` class still carries commented-out future-shape Meta keys
and methods — uncomment each line as the corresponding card ships.
Sidecar keys `filterset_class` / `orderset_class` are backed by the
present `filters.py` / `orders.py` modules; `aggregate_class` /
`fields_class` additionally need their cards plus an `aggregates.py` /
`fields.py` module under this app (`fields.py` is present;
`aggregates.py` is not yet).
"""

# Future imports (uncomment as Layer-3 subsystems ship):
#
# from django_strawberry_framework import DjangoConnectionField      # TODO-ALPHA-024-0.0.9
# from django_strawberry_framework import apply_cascade_permissions  # TODO-ALPHA-027-0.0.10
# from apps.products import aggregates                               # TODO-BETA-040-0.1.3 (aggregates)
# from apps.products import fields as fieldsets                      # TODO-BETA-038-0.1.1

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
        # Future Layer-3 additions — uncomment each as the relevant card ships:
        # search_fields = ("name", "description")           # needs TODO-BETA-039-0.1.2
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
        interfaces = (relay.Node,)
        filterset_class = filters.ItemFilter
        orderset_class = orders.ItemOrder
        # TODO(spec-031-globalid_encoding-0_0_9 Slice 4): If the live HTTP
        # ``type``-strategy opt-out test is clearer with a schema fixture than
        # a settings override, add ``globalid_strategy = "type"`` to one
        # dedicated fakeshop type in the same change that updates the expected
        # GlobalID payloads.
        # Pseudocode:
        #   globalid_strategy = "type"  # noqa: ERA001
        # Future Layer-3 additions — uncomment each as the relevant card ships:
        # search_fields = ("name", "description", "category__name", "category__description")  # needs TODO-BETA-039-0.1.2
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
        interfaces = (relay.Node,)
        filterset_class = filters.PropertyFilter
        orderset_class = orders.PropertyOrder
        # Future Layer-3 additions — uncomment each as the relevant card ships:
        # search_fields = ("name", "description", "category__name", "category__description")  # needs TODO-BETA-039-0.1.2
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
        interfaces = (relay.Node,)
        filterset_class = filters.EntryFilter
        orderset_class = orders.EntryOrder
        # Future Layer-3 additions — uncomment each as the relevant card ships:
        # search_fields = ("value", "property__name", "item__name") # needs TODO-BETA-039-0.1.2
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

    @strawberry.field
    def all_items(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters.ItemFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.ItemOrder)] | None = None,
    ) -> list[ItemType]:
        queryset = ItemType.get_queryset(models.Item.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters.ItemFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.ItemOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_properties(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters.PropertyFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.PropertyOrder)] | None = None,
    ) -> list[PropertyType]:
        queryset = PropertyType.get_queryset(models.Property.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters.PropertyFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.PropertyOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_entries(
        self,
        info: strawberry.Info,
        filter: filter_input_type(filters.EntryFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.EntryOrder)] | None = None,
    ) -> list[EntryType]:
        queryset = EntryType.get_queryset(models.Entry.objects.order_by("id"), info)
        if filter is not None:
            queryset = filters.EntryFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.EntryOrder.apply_sync(order_by, queryset, info)
        return queryset


__all__ = ("Query",)
