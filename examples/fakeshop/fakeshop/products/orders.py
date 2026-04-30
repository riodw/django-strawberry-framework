from graphql import GraphQLError

import django_strawberry_framework as orders

from . import models


class CategoryOrder(orders.AdvancedOrderSet):
    class Meta:
        model = models.Category
        fields = "__all__"

    def check_name_permission(self, request):
        """Only staff users may order by Category.name."""
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to order by Category name.")


class ItemOrder(orders.AdvancedOrderSet):
    category = orders.RelatedOrder(
        CategoryOrder,
        field_name="category",
    )
    # Relationships
    entries = orders.RelatedOrder(
        "EntryOrder",
        field_name="entries",
    )

    class Meta:
        model = models.Item
        fields = "__all__"


class PropertyOrder(orders.AdvancedOrderSet):
    category = orders.RelatedOrder(
        CategoryOrder,
        field_name="category",
    )

    class Meta:
        model = models.Property
        fields = "__all__"


class EntryOrder(orders.AdvancedOrderSet):
    property = orders.RelatedOrder(
        PropertyOrder,
        field_name="property",
    )

    class Meta:
        model = models.Entry
        # Explicitly list only "value" — "description" is intentionally excluded
        fields = ["value"]
