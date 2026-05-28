"""Fixture filtersets for cross-module lazy-resolution tests.

Carries minimal `FilterSet` subclasses over the fakeshop library models
so the Slice-1 tests can exercise the absolute-import-path and
unqualified-name resolution branches of
`LazyRelatedClassMixin.resolve_lazy_class`.
"""

from __future__ import annotations

from apps.library import models

from django_strawberry_framework.filters import FilterSet, RelatedFilter


class ShelfFilter(FilterSet):
    class Meta:
        model = models.Shelf
        fields = {"code": ["exact", "icontains"]}


class BranchFilter(FilterSet):
    """Forward-FK to `ShelfFilter` referenced by class object."""

    shelves = RelatedFilter(ShelfFilter, field_name="shelves")

    class Meta:
        model = models.Branch
        fields = {"name": ["exact", "icontains"]}


class BranchFilterByString(FilterSet):
    """Same model as `BranchFilter` but references `ShelfFilter` by string."""

    shelves = RelatedFilter("ShelfFilter", field_name="shelves")

    class Meta:
        model = models.Branch
        fields = {"name": ["exact"]}


class BranchFilterByPath(FilterSet):
    """References `ShelfFilter` via an absolute import path string."""

    shelves = RelatedFilter(
        "tests.filters.fixtures.filtersets.ShelfFilter",
        field_name="shelves",
    )

    class Meta:
        model = models.Branch
        fields = {"name": ["exact"]}


class SelfReferentialBranchFilter(FilterSet):
    """References itself by unqualified name — exercises the cycle guard."""

    self_link = RelatedFilter("SelfReferentialBranchFilter", field_name="id")

    class Meta:
        model = models.Branch
        fields = {"name": ["exact"]}
