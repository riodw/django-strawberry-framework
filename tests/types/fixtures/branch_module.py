"""Cross-module fixture: ``BranchType`` + ``BranchFilter`` declared together.

Paired with ``shelf_module``; both modules are imported at test time so
``finalize_django_types()`` exercises the cross-module
``Meta.filterset_class`` resolution path under spec-021 Slice 3.
"""

from __future__ import annotations

from apps.library import models

from django_strawberry_framework import DjangoType
from django_strawberry_framework.filters import FilterSet


class BranchFilter(FilterSet):
    class Meta:
        model = models.Branch
        fields = {"name": ["exact"]}


class BranchType(DjangoType):
    class Meta:
        model = models.Branch
        fields = ("id", "name")
        filterset_class = BranchFilter
