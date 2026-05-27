"""GraphQL schema for end-to-end scalar conversion coverage.

Exposes ``ScalarSpecimen`` and its all-nullable counterpart
``NullableScalarSpecimen`` with every concrete scalar field selected so a
single live ``/graphql/`` query exercises both the non-null and nullable
branch of each non-trivial entry in the package's converter table. See
``apps/scalars/models.py`` for the rationale on which converter rows live
here vs. in ``tests/``.

The two models are linked via ``NullableScalarSpecimen.partner`` (cross-
model nullable FK with ``on_delete=SET_NULL``) so a single GraphQL query
can traverse both shapes — and ``ScalarSpecimen.nullable_partners`` exposes
the reverse side for composite queries.
"""

import strawberry

from apps.scalars import models
from django_strawberry_framework import DjangoType


class ScalarSpecimenType(DjangoType):
    """``DjangoType`` exposing every converted scalar on ``ScalarSpecimen``."""

    class Meta:
        model = models.ScalarSpecimen
        fields = (
            "id",
            "label",
            "flag",
            "score",
            "price",
            "occurred_on",
            "occurred_at",
            "occurred_time",
            "payload",
            "external_id",
            "signed_big",
            "unsigned_big",
            "parent",
            "children",
            "nullable_partners",
        )


class NullableScalarSpecimenType(DjangoType):
    """``DjangoType`` exposing every converted scalar on ``NullableScalarSpecimen``.

    Every scalar field is nullable on the model so introspection reports the
    bare ``SCALAR`` shape (no ``NON_NULL`` wrapper). The ``partner`` FK is
    nullable too, exercising forward-FK selection where the related instance
    may be absent.
    """

    class Meta:
        model = models.NullableScalarSpecimen
        fields = (
            "id",
            "label",
            "flag",
            "score",
            "price",
            "occurred_on",
            "occurred_at",
            "occurred_time",
            "payload",
            "external_id",
            "signed_big",
            "unsigned_big",
            "partner",
        )


@strawberry.type
class Query:
    """Scalars coverage root fields."""

    @strawberry.field
    def all_scalar_specimens(self) -> list[ScalarSpecimenType]:
        return models.ScalarSpecimen.objects.order_by("id")

    @strawberry.field
    def all_nullable_scalar_specimens(self) -> list[NullableScalarSpecimenType]:
        return models.NullableScalarSpecimen.objects.order_by("id")


__all__ = ("Query",)
