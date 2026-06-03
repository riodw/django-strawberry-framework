"""OrderSet declarations for the scalars acceptance app.

Mirrors ``apps.scalars.filters``'s model set on the ordering side. Each
``OrderSet`` lists the orderable scalar columns explicitly -- the same
field set the matching ``FilterSet`` exposes, which deliberately excludes
``payload`` (a ``JSONField``: ordering by a raw JSON column is not a
meaningful surface and mirrors the filter side's exclusion). Forward-FK
columns (``tag`` / ``partner``) are left out of the leaf set -- ordering
here is a straight wiring of the ``Ordering`` surface onto the scalar
columns, with no per-field permission gates.
"""

from __future__ import annotations

from django_strawberry_framework.orders import OrderSet

from . import models


class ScalarSpecimenTagOrder(OrderSet):
    class Meta:
        model = models.ScalarSpecimenTag
        fields = ["id", "label", "active"]


class ScalarSpecimenOrder(OrderSet):
    class Meta:
        model = models.ScalarSpecimen
        fields = [
            "id",
            "label",
            "flag",
            "score",
            "price",
            "occurred_on",
            "occurred_at",
            "occurred_time",
            "external_id",
            "signed_big",
            "unsigned_big",
        ]


class NullableScalarSpecimenOrder(OrderSet):
    class Meta:
        model = models.NullableScalarSpecimen
        fields = [
            "id",
            "label",
            "flag",
            "score",
            "price",
            "occurred_on",
            "external_id",
            "signed_big",
        ]


__all__ = ("NullableScalarSpecimenOrder", "ScalarSpecimenOrder", "ScalarSpecimenTagOrder")
