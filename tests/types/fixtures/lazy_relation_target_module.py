"""Cross-module fixture holding the target of a ``strawberry.lazy`` relation override.

Imported by name from ``tests/types/test_definition_order.py``, which declares a
relation override annotated ``Annotated[..., strawberry.lazy("<this module>")]``.
The module exists because that escape hatch resolves through a real importable
module path rather than the referring module's namespace (spec-010 #"Spike C").

Deliberately carries no ``from __future__ import annotations``: stringified
annotations are a separately supported forward-reference shape, and a module
carrying both would pin neither of them cleanly.
"""

from apps.products import models

from django_strawberry_framework import DjangoType


class LazyItemType(DjangoType):
    class Meta:
        model = models.Item
        fields = ("id", "name")
