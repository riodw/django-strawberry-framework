"""GraphQL schema for the fakeshop products app.

This file is the *intended* end-state of the example schema once
``django-strawberry-framework`` has the ``DjangoType``,
``DjangoConnectionField``, and ``apply_cascade_permissions`` machinery
built out.  Until then, the design below is fully commented so that
``urls.py`` can still import a working (placeholder) ``schema``.

The design is a 1-to-1 port of the ``django-graphene-filters`` cookbook
example (``recipes/schema.py``), translated to Strawberry idioms and
the new model names: ``Category`` / ``Item`` / ``Property`` / ``Entry``.

Within the commented design block, each ``filterset_class``,
``orderset_class``, ``aggregate_class``, ``fields_class`` line and the
permission-aware ``get_queryset`` method is *doubly* commented so that
when the outer block is later uncommented, those lines remain
commented out — matching "comment out filters/orders/aggregates/perms
for now" — until those subsystems ship.
"""

# import strawberry
# from strawberry import relay
#
# from django_strawberry_framework import (
#     DjangoConnectionField,
#     DjangoType,
#     # apply_cascade_permissions,
# )
#
# from . import models
# # from . import aggregates, filters, orders
# # from . import fields as fieldsets
#
#
# # ---------------------------------------------------------------------------
# # Nodes
# # ---------------------------------------------------------------------------
#
#
# class CategoryNode(DjangoType):
#     class Meta:
#         model = models.Category
#         interfaces = (relay.Node,)
#         fields = "__all__"
#         # filterset_class = filters.CategoryFilter
#         # orderset_class = orders.CategoryOrder
#         # aggregate_class = aggregates.CategoryAggregate
#         # fields_class = fieldsets.CategoryFieldSet
#         search_fields = (
#             "name",
#             "description",
#         )
#
#     # @classmethod
#     # def get_queryset(cls, queryset, info):
#     #     """Staff or users with view_category permission see everything; others see public only."""
#     #     user = getattr(info.context, "user", None)
#     #     if user and user.is_staff:
#     #         return queryset
#     #     elif user and user.has_perm("products.view_category"):
#     #         return queryset.filter(is_private=False)
#     #     return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
#
#
# class ItemNode(DjangoType):
#     class Meta:
#         model = models.Item
#         interfaces = (relay.Node,)
#         fields = "__all__"
#         # filterset_class = filters.ItemFilter
#         # orderset_class = orders.ItemOrder
#         # aggregate_class = aggregates.ItemAggregate
#         # fields_class = fieldsets.ItemFieldSet
#         search_fields = (
#             "name",
#             "description",
#             "category__name",
#             "category__description",
#         )
#
#     # @classmethod
#     # def get_queryset(cls, queryset, info):
#     #     """Staff or users with view_item permission see everything; others see public only."""
#     #     user = getattr(info.context, "user", None)
#     #     if user and user.is_staff:
#     #         return queryset
#     #     elif user and user.has_perm("products.view_item"):
#     #         return queryset.filter(is_private=False)
#     #     return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
#
#
# class PropertyNode(DjangoType):
#     class Meta:
#         model = models.Property
#         interfaces = (relay.Node,)
#         fields = "__all__"
#         # filterset_class = filters.PropertyFilter
#         # orderset_class = orders.PropertyOrder
#         # aggregate_class = aggregates.PropertyAggregate
#         # fields_class = fieldsets.PropertyFieldSet
#         search_fields = (
#             "name",
#             "description",
#             "category__name",
#             "category__description",
#         )
#
#     # @classmethod
#     # def get_queryset(cls, queryset, info):
#     #     """Staff or users with view_property permission see everything; others see public only."""
#     #     user = getattr(info.context, "user", None)
#     #     if user and user.is_staff:
#     #         return queryset
#     #     elif user and user.has_perm("products.view_property"):
#     #         return queryset.filter(is_private=False)
#     #     return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
#
#
# class EntryNode(DjangoType):
#     class Meta:
#         model = models.Entry
#         interfaces = (relay.Node,)
#         fields = [
#             "id",
#             "value",
#             # description - not included for permissions testing
#             "property",
#             "item",
#             "is_private",
#             "created_date",
#             "updated_date",
#         ]
#         # filterset_class = filters.EntryFilter
#         # orderset_class = orders.EntryOrder
#         # aggregate_class = aggregates.EntryAggregate
#         # fields_class = fieldsets.EntryFieldSet
#         search_fields = (
#             "value",
#             "property__name",
#             "item__name",
#         )
#
#     # @classmethod
#     # def get_queryset(cls, queryset, info):
#     #     """Staff or users with view_entry permission see everything; others see public only."""
#     #     user = getattr(info.context, "user", None)
#     #     if user and user.is_staff:
#     #         return queryset
#     #     elif user and user.has_perm("products.view_entry"):
#     #         return queryset.filter(is_private=False)
#     #     return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
#
#
# # ---------------------------------------------------------------------------
# # Query
# # ---------------------------------------------------------------------------
#
#
# @strawberry.type
# class Query:
#     category: CategoryNode = relay.node()
#     all_categories: relay.ListConnection[CategoryNode] = DjangoConnectionField(CategoryNode)
#
#     item: ItemNode = relay.node()
#     all_items: relay.ListConnection[ItemNode] = DjangoConnectionField(ItemNode)
#
#     property: PropertyNode = relay.node()
#     all_properties: relay.ListConnection[PropertyNode] = DjangoConnectionField(PropertyNode)
#
#     entry: EntryNode = relay.node()
#     all_entries: relay.ListConnection[EntryNode] = DjangoConnectionField(EntryNode)


# ---------------------------------------------------------------------------
# Placeholder
# ---------------------------------------------------------------------------
# Until ``DjangoType`` and ``DjangoConnectionField`` are implemented, expose
# an empty ``Query`` so the project-level schema can still be assembled.

import strawberry


@strawberry.type
class Query:
    """Placeholder until ``DjangoType`` and ``DjangoConnectionField`` ship."""

    @strawberry.field
    def hello(self) -> str:
        return "fakeshop placeholder"
