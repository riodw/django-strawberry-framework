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

from apps.scalars import filters, models, orders
from django_strawberry_framework import BigInt, DjangoType
from django_strawberry_framework.filters import filter_input_type
from django_strawberry_framework.orders import order_input_type


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
        fields = (
            "id",
            "label",
            "active",
            "tagged_specimens",
        )
        filterset_class = filters.ScalarSpecimenTagFilter
        orderset_class = orders.ScalarSpecimenTagOrder


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
        filterset_class = filters.ScalarSpecimenFilter
        orderset_class = orders.ScalarSpecimenOrder


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
        filterset_class = filters.NullableScalarSpecimenFilter
        orderset_class = orders.NullableScalarSpecimenOrder


class OverriddenScalarSpecimenType(DjangoType):
    """Demonstrates the four consumer-authored field-override corners (spec-029).

    ``_build_annotations`` skips auto-synthesis for any consumer-authored field,
    so ``manage.py inspect_django_type OverriddenScalarSpecimenType`` names the row
    that actually produced each field in its converter column — a consumer
    override, never the auto ``SCALAR_MAP`` converter:

    * ``quantity`` — annotation-only override. The ``IntegerField`` would
      auto-convert to ``Int!``; the ``float | None`` annotation forces a nullable
      ``Float`` (``consumer annotation (scalar)``), decoupling the GraphQL type
      from the column without a migration.
    * ``token`` — annotation over the unsupported ``Base36Field``. The column has
      no ``SCALAR_MAP`` entry, so the ``token: str`` annotation is the escape
      hatch that lets it build at all (``consumer annotation (scalar)``).
    * ``score`` — the ``name: T = strawberry.field(resolver=...)`` overlap idiom:
      the annotation fixes the type, the assignment supplies the resolver
      (``consumer annotation + strawberry.field (scalar)``).
    * ``label`` — an assigned ``@strawberry.field`` resolver shadowing the column
      (``consumer strawberry.field (scalar)``).
    """

    quantity: float | None
    token: str
    score: int = strawberry.field(resolver=lambda root: root.score)

    @strawberry.field
    def label(self) -> str:
        """Assigned-resolver override; upper-cases the column so the override is observable."""
        return self.label.upper()

    class Meta:
        model = models.OverrideSpecimen
        fields = (
            "id",
            "label",
            "quantity",
            "score",
            "token",
        )


@strawberry.type
class Query:
    """Scalars coverage root fields."""

    @strawberry.field
    def all_override_specimens(self) -> list[OverriddenScalarSpecimenType]:
        """Root field for the consumer-authored field-override demonstration type."""
        return list(models.OverrideSpecimen.objects.order_by("id"))

    @strawberry.field
    def all_scalar_specimens(
        self,
        info: Info,
        filter: filter_input_type(filters.ScalarSpecimenFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.ScalarSpecimenOrder)] | None = None,
    ) -> list[ScalarSpecimenType]:
        queryset = models.ScalarSpecimen.objects.order_by("id")
        if filter is not None:
            queryset = filters.ScalarSpecimenFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.ScalarSpecimenOrder.apply_sync(order_by, queryset, info)
        return queryset

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
    def all_nullable_scalar_specimens(
        self,
        info: Info,
        filter: filter_input_type(filters.NullableScalarSpecimenFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.NullableScalarSpecimenOrder)] | None = None,
    ) -> list[NullableScalarSpecimenType]:
        queryset = models.NullableScalarSpecimen.objects.order_by("id")
        if filter is not None:
            queryset = filters.NullableScalarSpecimenFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.NullableScalarSpecimenOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_scalar_specimen_tags(
        self,
        info: Info,
        filter: filter_input_type(filters.ScalarSpecimenTagFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.ScalarSpecimenTagOrder)] | None = None,
    ) -> list[ScalarSpecimenTagType]:
        queryset = models.ScalarSpecimenTag.objects.order_by("id")
        if filter is not None:
            queryset = filters.ScalarSpecimenTagFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.ScalarSpecimenTagOrder.apply_sync(order_by, queryset, info)
        return queryset

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
