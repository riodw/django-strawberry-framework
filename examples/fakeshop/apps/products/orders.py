"""OrderSet declarations for the fakeshop products app.

Ported from the ``django-graphene-filters`` cookbook recipe to the
``django-strawberry-framework`` ordering API (``DONE-028-0.0.8``):

* ``OrderSet`` (not the cookbook's ``AdvancedOrderSet``), imported from
  ``django_strawberry_framework.orders``;
* ``Meta.fields`` as a list, or the ``"__all__"`` shorthand which expands
  to every column-backed model field (includes forward FK columns such as
  ``category`` -> sorts by ``category_id``; excludes reverse relations and
  M2M managers);
* ``RelatedOrder`` cross-references mirror ``apps.products.filters``'s
  relation graph: ``Item`` / ``Property`` -> ``Category`` (forward FK) and
  ``Item.entries`` / ``Entry.property`` (reverse + forward FK). Targets that
  are already defined use the class-reference form
  (``RelatedOrder(CategoryOrder, ...)``); a forward-declared target uses the
  same-module unqualified-name string form (``RelatedOrder("EntryOrder", ...)``)
  so the lazy Layer-2 resolution path is exercised end to end.

``check_<field>_permission(self, request)`` is the ordering subsystem's
per-field permission gate (mirrors ``CategoryFilter.check_name_permission``
on the filter side): only staff users may order by ``Category.name``. The
gate is active-input-only -- it fires only when the consumer's ``orderBy``
input names the gated field.
"""

from __future__ import annotations

from graphql import GraphQLError

from django_strawberry_framework.orders import OrderSet, RelatedOrder

from . import models


class CategoryOrder(OrderSet):
    class Meta:
        model = models.Category
        fields = "__all__"

    def check_name_permission(self, request):
        """Only staff users may order by ``Category.name``."""
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to order by Category name.")


class ItemOrder(OrderSet):
    category = RelatedOrder(CategoryOrder, field_name="category")
    entries = RelatedOrder("EntryOrder", field_name="entries")

    class Meta:
        model = models.Item
        fields = "__all__"


class PropertyOrder(OrderSet):
    category = RelatedOrder(CategoryOrder, field_name="category")

    class Meta:
        model = models.Property
        fields = "__all__"


class EntryOrder(OrderSet):
    property = RelatedOrder(PropertyOrder, field_name="property")

    class Meta:
        model = models.Entry
        # Explicitly list only "value" -- "description" is intentionally
        # excluded (mirrors the field-permission-gating story EntryType
        # reserves for the permissions slice).
        fields = ["value"]


__all__ = (
    "CategoryOrder",
    "EntryOrder",
    "ItemOrder",
    "PropertyOrder",
)
