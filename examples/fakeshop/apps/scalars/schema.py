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

``scalar_specimen_by_signed_big`` accepts a ``BigInt!`` argument so the
input-position parser (``BigInt.parse_value``) is exercised end-to-end —
both for the decimal-string literal form and the JSON-int literal form.

``ScalarSpecimenTagType`` declares a custom ``get_queryset(cls, queryset,
info)`` classmethod filtering to ``active=True``. The optimizer's O6
rule downgrades any forward-FK select_related into that type to a
``Prefetch(queryset=cls.get_queryset(...))`` so the consumer's filter
survives plan execution. Visible in the live HTTP test by an inactive
tag resolving to ``null`` on the source specimen.
"""

from typing import Any

import strawberry
from strawberry.types import Info

from apps.scalars import models
from django_strawberry_framework import BigInt, DjangoType


class ScalarSpecimenTagType(DjangoType):
    """``DjangoType`` with a custom ``get_queryset`` filtering to ``active=True``.

    The classmethod is the consumer-facing API the optimizer detects via
    ``has_custom_get_queryset`` to trigger O6: any forward FK whose target
    type declares ``get_queryset`` is planned as ``Prefetch(queryset)``
    rather than ``select_related`` so the filter survives end-to-end.
    """

    @classmethod
    def get_queryset(cls, queryset: Any, info: Info, **kwargs: Any) -> Any:  # noqa: ARG003
        return queryset.filter(active=True)

    class Meta:
        model = models.ScalarSpecimenTag
        fields = ("id", "label", "active", "tagged_specimens")


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
            "tag",
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
    def all_scalar_specimens_via_manager(self) -> list[ScalarSpecimenType]:
        """Resolver returning a bare ``Manager`` instead of ``Manager.all()``.

        Consumers frequently write ``return Model.objects`` rather than
        ``return Model.objects.all()``. Both shapes are equivalent for
        Strawberry's default resolver path, but the optimizer's
        ``isinstance(QuerySet)`` gate must coerce the Manager via
        ``.all()`` before the plan can be applied — otherwise the
        Manager passes through unoptimized and the consumer pays N+1 on
        any forward-FK selection. This field exposes that coercion path
        end-to-end (no ``DjangoListField`` wrapping involved).
        """
        return models.ScalarSpecimen.objects  # type: ignore[return-value]

    @strawberry.field
    def all_nullable_scalar_specimens(self) -> list[NullableScalarSpecimenType]:
        return models.NullableScalarSpecimen.objects.order_by("id")

    @strawberry.field
    def all_scalar_specimen_tags(self) -> list[ScalarSpecimenTagType]:
        return models.ScalarSpecimenTag.objects.order_by("id")

    @strawberry.field
    def scalar_specimen_by_signed_big(self, signed_big: BigInt) -> ScalarSpecimenType | None:
        """Lookup-by-``BigInt`` query field exercising input-position parsing.

        Returns the ``ScalarSpecimen`` whose ``signed_big`` column matches
        the requested value, or ``None`` if no row matches. The
        ``BigInt!`` argument exercises ``BigInt.parse_value`` end-to-end
        for both wire forms: decimal-string literals
        (``signedBig: "9223372036854775000"``) and JSON-int literals
        (``signedBig: 42``).
        """
        return models.ScalarSpecimen.objects.filter(signed_big=signed_big).first()


__all__ = ("Query",)
