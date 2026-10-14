"""Cross-module fixture declaring BranchType and BranchFilter together.

Paired with ``shelf_module``; both modules are imported at test time so
``finalize_django_types()`` exercises the cross-module
``Meta.filterset_class`` resolution path under spec-027.
"""

from __future__ import annotations

from apps.library import models

from django_strawberry_framework import DjangoType
from django_strawberry_framework.filters import FilterSet


class BranchFilter(FilterSet):
    """Filters ``Branch`` rows by ``name``; resolved from ``BranchType.Meta.filterset_class``."""

    class Meta:
        model = models.Branch
        fields = {"name": ["exact"]}


class BranchType(DjangoType):
    """Type over ``Branch`` that names its filterset across the module boundary."""

    class Meta:
        model = models.Branch
        fields = ("id", "name")
        filterset_class = BranchFilter
