"""Cross-module fixture: ``ShelfType`` + ``ShelfFilter`` declared together.

Paired with ``branch_module`` to exercise the cross-module
``Meta.filterset_class`` resolution path under spec-021 Slice 3.
"""

from __future__ import annotations

from apps.library import models

from django_strawberry_framework import DjangoType
from django_strawberry_framework.filters import FilterSet


class ShelfFilter(FilterSet):
    class Meta:
        model = models.Shelf
        fields = {"code": ["exact"]}


class ShelfType(DjangoType):
    class Meta:
        model = models.Shelf
        fields = ("id", "code")
        filterset_class = ShelfFilter
