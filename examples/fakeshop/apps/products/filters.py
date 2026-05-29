"""FilterSet declarations for the fakeshop products app.

Ported from the ``django-graphene-filters`` cookbook recipe
(``examples/cookbook/cookbook/recipes/filters.py``) to the
``django-strawberry-framework`` API:

* ``FilterSet`` (not the cookbook's ``AdvancedFilterSet``);
* ``Meta.fields`` (not ``Meta.filter_fields``);
* per-field ``"__all__"`` expands to every concrete (non-transform) lookup
  for the field -- the same shorthand the cookbook's ``filter_fields``
  accepts (``CategoryFilter.name`` / ``ItemFilter.name`` use it); other
  fields declare explicit lookup lists;
* ``interfaces`` lives on the owning ``DjangoType`` (``apps.products.schema``),
  NOT on the FilterSet ``Meta``.

The relation graph mirrors ``apps.products.schema``: ``Item`` / ``Property``
-> ``Category`` (forward FK) and ``Entry`` -> ``Property`` (forward FK with
an explicit visibility queryset). ``RelatedFilter`` cross-references use the
same-module unqualified-name form (e.g. ``RelatedFilter("EntryFilter")``) so
the lazy Layer-2 resolution path is exercised end to end.

Because the owning ``DjangoType``\\ s declare ``interfaces = (relay.Node,)``,
each model's own ``id`` is a Relay GlobalID over the wire -- so the
``"id": ["exact", "in"]`` entries exercise the own-PK ``GlobalIDFilter`` /
``GlobalIDMultipleChoiceFilter`` conversion.

``check_<field>_permission(self, request)`` is the filter subsystem's
(``DONE-021-0.0.8``) per-field permission gate; the queryset-scoping
``check_<field>_permission(self, queryset, request)`` variant is owned by
the permissions slice (``TODO-ALPHA-027-0.0.10``) and stays commented.
"""

from __future__ import annotations

from graphql import GraphQLError

from django_strawberry_framework.filters import FilterSet, RelatedFilter

from . import models


class CategoryFilter(FilterSet):
    class Meta:
        model = models.Category
        fields = {
            "id": ["exact", "in"],
            "name": "__all__",
            "description": ["exact", "icontains"],
        }

    def check_name_permission(self, request):
        """Only staff users may filter by ``Category.name``."""
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to filter by Category name.")


class ItemFilter(FilterSet):
    category = RelatedFilter(CategoryFilter, field_name="category")
    entries = RelatedFilter("EntryFilter", field_name="entries")

    class Meta:
        model = models.Item
        fields = {
            "id": ["exact", "in"],
            "name": "__all__",
            "description": ["exact", "icontains"],
            "category__name": ["exact"],
        }

    # TODO(TODO-ALPHA-027-0.0.10 permissions; see KANBAN.md):
    #   The queryset-scoping permission variant below is owned by the
    #   permissions slice and composes with this filterset (``DONE-021-0.0.8``).
    #   Uncomment in the same change that lands the hook contract and exempt
    #   this pseudo-code block from ERA001 per AGENTS.md's TODO-pseudo-code rule.
    # def check_entries_permission(self, queryset, request):
    #     """Only staff users may filter by Item.entries."""
    #     user = getattr(request, "user", None)
    #     if not user or not user.is_staff:
    #         return queryset.filter(category__name="Secret")
    #     return queryset


class PropertyFilter(FilterSet):
    category = RelatedFilter(CategoryFilter, field_name="category")

    class Meta:
        model = models.Property
        fields = {
            "id": ["exact", "in"],
            "name": ["exact", "icontains"],
            "description": ["exact", "icontains"],
        }


class EntryFilter(FilterSet):
    # Explicit queryset: excludes properties named "Secret", acting as a scope
    # boundary. Entries linked to a "Secret" property never appear in results.
    property = RelatedFilter(
        PropertyFilter,
        field_name="property",
        queryset=models.Property.objects.exclude(name="Secret"),
    )

    class Meta:
        model = models.Entry
        fields = {
            "id": ["exact", "in"],
            "value": ["exact", "icontains"],
            "description": ["exact", "icontains"],
            "property__name": ["exact"],
            "property__category__name": ["exact"],
        }


__all__ = ("CategoryFilter", "ItemFilter", "PropertyFilter", "EntryFilter")
