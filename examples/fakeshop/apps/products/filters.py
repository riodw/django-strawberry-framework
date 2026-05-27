from graphql import GraphQLError
from strawberry import relay

import django_strawberry_framework as filters

from . import models


class CategoryFilter(filters.AdvancedFilterSet):
    class Meta:
        model = models.Category
        interfaces = (relay.Node,)
        filter_fields = {
            "name": "__all__",
            # "name": ["exact", "icontains"],
            "description": ["exact", "icontains"],
        }

    def check_name_permission(self, request):
        """Only staff users may filter by Category.name."""
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to filter by Category name.")


class ItemFilter(filters.AdvancedFilterSet):
    category = filters.RelatedFilter(
        CategoryFilter,
        field_name="category",
    )
    # Relationships
    entries = filters.RelatedFilter(
        "EntryFilter",
        field_name="entries",
    )

    class Meta:
        model = models.Item
        interfaces = (relay.Node,)
        filter_fields = {
            "name": "__all__",
            "description": ["exact", "icontains"],
            # "category": ["exact"],
            "category__name": ["exact"],
        }

    # TODO(TODO-ALPHA-027-0.0.10 permissions; see KANBAN.md):
    #   Per-field ``check_<field>_permission`` hooks are owned by the
    #   permissions slice (``TODO-ALPHA-027-0.0.10``) and compose with the
    #   filter subsystem (``WIP-ALPHA-021-0.0.8``). The commented method
    #   below is the target shape: scope ``queryset`` based on the request
    #   user so non-staff callers cannot filter by ``Item.entries``.
    #   Uncomment in the same change that lands the hook contract and
    #   exempt this pseudo-code block from ERA001 per AGENTS.md's
    #   TODO-pseudo-code rule.
    # def check_entries_permission(self, queryset, request):
    #     """Only staff users may filter by Item.entries."""
    #     user = getattr(request, "user", None)
    #     if not user or not user.is_staff:
    #         return queryset.filter(category__name="Secret")
    #     return queryset


class PropertyFilter(filters.AdvancedFilterSet):
    category = filters.RelatedFilter(
        CategoryFilter,
        field_name="category",
    )
    # Relationships
    # entries = filters.RelatedFilter(
    #     "EntryFilter",
    #     field_name="entries",
    #     queryset=models.Entry.objects.all(),
    # )

    class Meta:
        model = models.Property
        interfaces = (relay.Node,)
        filter_fields = {
            "name": ["exact", "icontains"],
            "description": ["exact", "icontains"],
        }


class EntryFilter(filters.AdvancedFilterSet):
    # Explicit queryset: excludes properties named "Secret", acting as a scope
    # boundary. Entries linked to a "Secret" property will never appear in results.
    property = filters.RelatedFilter(
        PropertyFilter,
        field_name="property",
        queryset=models.Property.objects.exclude(name="Secret"),
    )

    class Meta:
        model = models.Entry
        interfaces = (relay.Node,)
        filter_fields = {
            "value": ["exact", "icontains"],
            "description": ["exact", "icontains"],
            "property__name": ["exact"],
            "property__category__name": ["exact"],
        }
