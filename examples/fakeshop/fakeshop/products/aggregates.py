"""Aggregate class definitions for the fakeshop example.

All aggregate classes override ``get_child_queryset`` to filter out
private rows (``is_private=True``) when traversing relationships.
This mirrors the ``get_queryset`` visibility logic in schema.py.
"""

from graphql import GraphQLError

import django_strawberry_framework as aggregates
from django_strawberry_framework import RelatedAggregate

from . import models


def _private_aware_child_qs(self, rel_name, rel_agg):
    """Shared get_child_queryset that excludes is_private=True rows."""
    qs = super(type(self), self).get_child_queryset(rel_name, rel_agg)
    target_model = rel_agg.aggregate_class.Meta.model
    if hasattr(target_model, "is_private"):
        qs = qs.filter(is_private=False)
    return qs


class CategoryAggregate(aggregates.AdvancedAggregateSet):
    # Category → Item (Item.category FK)
    items = RelatedAggregate("ItemAggregate", field_name="category")
    # Category → Property (Property.category FK)
    properties = RelatedAggregate("PropertyAggregate", field_name="category")

    class Meta:
        model = models.Category
        fields = {
            "name": ["count", "min", "max", "mode", "uniques"],
            "description": ["count", "min", "max"],
        }

    get_child_queryset = _private_aware_child_qs


class PropertyAggregate(aggregates.AdvancedAggregateSet):
    category = RelatedAggregate("CategoryAggregate", field_name="properties")
    entries = RelatedAggregate("EntryAggregate", field_name="property")

    class Meta:
        model = models.Property
        fields = {"name": ["count", "min", "max", "mode", "uniques"]}

    get_child_queryset = _private_aware_child_qs


class ItemAggregate(aggregates.AdvancedAggregateSet):
    category = RelatedAggregate("CategoryAggregate", field_name="items")
    entries = RelatedAggregate("EntryAggregate", field_name="item")

    class Meta:
        model = models.Item
        fields = {
            "name": ["count", "min", "max", "mode", "uniques"],
            "description": ["count", "min", "max"],
        }

    get_child_queryset = _private_aware_child_qs

    def check_name_uniques_permission(self, request):
        """Only staff can see unique name distribution."""
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to view name uniques.")


class EntryAggregate(aggregates.AdvancedAggregateSet):
    """Aggregate for Entry model with a custom geographic centroid stat."""

    property = RelatedAggregate(PropertyAggregate, field_name="entries")
    item_ref = RelatedAggregate(ItemAggregate, field_name="entries")

    class Meta:
        model = models.Entry
        fields = {
            "value": ["count", "min", "max", "mode", "uniques", "centroid"],
        }
        custom_stats = {
            "centroid": str,
        }

    get_child_queryset = _private_aware_child_qs

    def compute_value_centroid(self, queryset):
        """Compute the geographic centroid from latitude/longitude Entries.

        Filters the queryset to only latitude and longitude properties,
        parses the text values to floats, and returns the mean as "lat, lng".

        Returns None if no geo data is present in the queryset.
        """
        geo_values = queryset.filter(
            property__name__in=["latitude", "longitude"],
        ).values_list("property__name", "value")

        latitudes = []
        longitudes = []
        for prop_name, val in geo_values:
            try:
                num = float(val)
            except (ValueError, TypeError):
                continue
            if prop_name == "latitude":
                latitudes.append(num)
            else:
                longitudes.append(num)

        if not latitudes or not longitudes:
            return None

        mean_lat = round(sum(latitudes) / len(latitudes), 6)
        mean_lng = round(sum(longitudes) / len(longitudes), 6)
        return f"{mean_lat}, {mean_lng}"
