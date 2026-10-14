"""Cross-module fixture declaring ShelfType and ShelfFilter together.

Paired with ``branch_module`` to exercise the cross-module
``Meta.filterset_class`` resolution path under spec-027.
"""

from __future__ import annotations

from apps.library import models

from django_strawberry_framework import DjangoType
from django_strawberry_framework.filters import FilterSet


class ShelfFilter(FilterSet):
    """Filters ``Shelf`` rows by exact ``code``."""

    class Meta:
        model = models.Shelf
        fields = {"code": ["exact"]}


class ShelfType(DjangoType):
    """``DjangoType`` over ``Shelf`` wired to ``ShelfFilter`` from the same module."""

    class Meta:
        model = models.Shelf
        fields = ("id", "code")
        filterset_class = ShelfFilter
