"""GraphQL schema for scalar conversion, overrides, optimizer visibility, and file/image uploads.

Exposes ``ScalarSpecimen`` and its all-nullable counterpart
``NullableScalarSpecimen`` with every concrete scalar field selected so a
single live ``/graphql/`` query exercises both the non-null and nullable
branch of each non-trivial entry in the package's converter table. See
``apps/scalars/models.py`` for the rationale on which converter rows live
here vs. in ``tests/``.

The two models are linked via ``NullableScalarSpecimen.partner`` (cross-
model nullable FK with ``on_delete=SET_NULL``) so a single GraphQL query
can traverse both shapes - and ``ScalarSpecimen.nullable_partners`` exposes
the reverse side for composite queries.

``scalar_specimen_by_signed_big`` accepts a ``BigInt!`` argument so the
input-position parser (``BigInt.parse_value``) is exercised end-to-end -
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

from apps.scalars import filters, forms, models, orders
from django_strawberry_framework import (
    BigInt,
    DjangoModelFormMutation,
    DjangoMutation,
    DjangoMutationField,
    DjangoType,
    auto,
)
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
    def get_queryset(cls, queryset: Any, info: Info, **kwargs: Any) -> Any:
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
    """Demonstrates the consumer-authored field corners (spec-029) plus ``auto``.

    ``_build_annotations`` skips auto-synthesis for any consumer-authored field,
    so ``manage.py inspect_django_type OverriddenScalarSpecimenType`` names the row
    that actually produced each field in its converter column - a consumer
    override, never the auto ``SCALAR_MAP`` converter:

    * ``quantity`` - annotation-only override. The ``IntegerField`` would
      auto-convert to ``Int!``; the ``float | None`` annotation forces a nullable
      ``Float`` (``consumer annotation (scalar)``), decoupling the GraphQL type
      from the column without a migration.
    * ``token`` - annotation over the unsupported ``Base36Field``. The column has
      no ``SCALAR_MAP`` entry, so the ``token: str`` annotation is the escape
      hatch that lets it build at all (``consumer annotation (scalar)``).
    * ``score`` - the ``name: T = strawberry.field(resolver=...)`` overlap idiom:
      the annotation fixes the type, the assignment supplies the resolver
      (``consumer annotation + strawberry.field (scalar)``).
    * ``label`` - an assigned ``@strawberry.field`` resolver shadowing the column
      (``consumer strawberry.field (scalar)``).

    The fifth corner is the inverse of the four overrides:

    * ``note`` - declared as ``note: auto``. ``auto`` is "declare-but-infer": the
      field is listed as a class annotation (so every field is co-located here
      rather than split between annotations and the ``Meta.fields`` tuple), but its
      type is synthesized from the model exactly as bare selection would
      (``TextField`` -> ``String!``). It is *not* a consumer override, so its
      converter column still names the auto ``SCALAR_MAP`` row. Selection still
      belongs to ``Meta.fields``; ``auto`` never adds a field.
    """

    quantity: float | None
    token: str
    score: int = strawberry.field(resolver=lambda root: root.score)
    note: auto

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
            "note",
        )


class MediaSpecimenType(DjangoType):
    """``DjangoType`` over a ``FileField`` + ``ImageField`` model (spec-037).

    On read, ``attachment`` converts to the structured ``DjangoFileType`` and
    ``image`` to ``DjangoImageType`` - and both are **nullable by default** in
    the live SDL even though the Django columns are required, because an empty /
    absent stored file resolves the whole object to ``null`` (spec-037
    Decision 4). Not Relay-Node-shaped (matching the other scalar specimens), so
    the generated mutation payload carries the row in the ``result`` slot.
    """

    class Meta:
        model = models.MediaSpecimen
        fields = (
            "id",
            "label",
            "attachment",
            "image",
        )


@strawberry.type
class Query:
    """Scalars coverage root fields."""

    @strawberry.field
    def all_override_specimens(self) -> list[OverriddenScalarSpecimenType]:
        """Root field for the consumer-authored field-override demonstration type."""
        return list(models.OverrideSpecimen.objects.order_by("id"))

    @strawberry.field
    def all_media_specimens(self) -> list[MediaSpecimenType]:
        """Root field for the file/image read-output demonstration type (spec-037)."""
        return list(models.MediaSpecimen.objects.order_by("id"))

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
        ``.all()`` before the plan can be applied - otherwise the
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


class CreateMediaSpecimen(DjangoMutation):
    """Create mutation over ``MediaSpecimen`` - the write side of the spec-037 surface.

    The generated ``MediaSpecimenInput`` maps the ``attachment`` / ``image``
    file columns to Strawberry's ``Upload`` scalar (the input-side half of
    spec-037), so a live multipart ``/graphql/`` request can create a row with
    real uploaded files. Uses the default ``[DjangoModelPermission]`` write
    authorization, so the caller needs the ``scalars.add_mediaspecimen`` perm.
    """

    class Meta:
        model = models.MediaSpecimen
        operation = "create"


class CreateMediaSpecimenImageViaForm(DjangoModelFormMutation):
    """Create a ``MediaSpecimen`` via ``MediaSpecimenImageForm`` - the FORM ``ImageField`` path.

    The spec-038 form-mutation twin of ``createMediaSpecimen`` (the spec-037 model path),
    for the named ``ImageField -> Upload`` gap: the form's ``image`` ``ImageField`` maps to
    the ``Upload`` scalar, the resolver routes the upload into the bound form's ``files=``,
    and the bound ``ImageField`` validates it as a real image (Pillow). The live test
    asserts the stored image's dimensions, which the products ``FileField`` form test
    skips. ``permission_classes = []`` keeps write-auth out of the path under test.
    """

    class Meta:
        form_class = forms.MediaSpecimenImageForm
        operation = "create"
        permission_classes = []


@strawberry.type
class Mutation:
    """Scalars coverage write surface - the live ``Upload`` mutation path (spec-037)."""

    create_media_specimen = DjangoMutationField(CreateMediaSpecimen)
    create_media_specimen_image_via_form = DjangoMutationField(CreateMediaSpecimenImageViaForm)


__all__ = ("Mutation", "Query")
