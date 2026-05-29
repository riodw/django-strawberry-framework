"""FilterSet declarations for the scalars acceptance app.

Where ``apps.scalars.schema`` exercises the converter table on the OUTPUT
side (every scalar field selected in a query), these filtersets exercise
the same converters on the INPUT side: each ``Meta.fields`` lookup flows
through ``convert_filter_to_input_annotation`` /
``_scalar_from_model_field`` to produce a Strawberry filter-input scalar
(``Decimal``, ``UUID``, ``date`` / ``datetime`` / ``time``, ``BigInt``,
``float``, ``bool``). ``JSONField`` (``payload``) is intentionally absent
-- django-filter ships no default filter for it, so it raises at
``get_filters()`` rather than producing an input.

These types are NOT Relay nodes (no ``interfaces`` on the owning
``DjangoType``), so each model's own ``id`` is a plain integer filter --
which makes the ``id`` ``"__all__"`` set (notably its ``in`` lookup)
exercise the django-filter-generated ``BaseInFilter`` -> ``list[int]``
converter path (the non-Relay counterpart to the library app's own-PK
``GlobalIDMultipleChoiceFilter``).

``ScalarSpecimenFilter.tag`` is a ``RelatedFilter`` onto
``ScalarSpecimenTagFilter``, whose owning ``ScalarSpecimenTagType``
declares a custom ``get_queryset`` (``active=True``) -- so the related
branch also exercises the ``get_queryset`` visibility hook through a
relation traversal.
"""

from __future__ import annotations

from django_strawberry_framework.filters import FilterSet, RelatedFilter

from . import models


class ScalarSpecimenTagFilter(FilterSet):
    class Meta:
        model = models.ScalarSpecimenTag
        fields = {
            "id": "__all__",
            "label": "__all__",
            "active": "__all__",
        }


class ScalarSpecimenFilter(FilterSet):
    tag = RelatedFilter(ScalarSpecimenTagFilter, field_name="tag")

    class Meta:
        model = models.ScalarSpecimen
        # Every converted scalar except ``payload`` (JSONField has no
        # django-filter default). Each ``"__all__"`` expands to that field's
        # full concrete-lookup set, exercising the lookup-expansion path
        # across bool / float / Decimal / date / datetime / time / UUID /
        # BigInt as well as the integer PK.
        fields = {
            "id": "__all__",
            "label": "__all__",
            "flag": "__all__",
            "score": "__all__",
            "price": "__all__",
            "occurred_on": "__all__",
            "occurred_at": "__all__",
            "occurred_time": "__all__",
            "external_id": "__all__",
            "signed_big": "__all__",
            "unsigned_big": "__all__",
        }


class NullableScalarSpecimenFilter(FilterSet):
    partner = RelatedFilter(ScalarSpecimenFilter, field_name="partner")

    class Meta:
        model = models.NullableScalarSpecimen
        fields = {
            "id": "__all__",
            "label": "__all__",
            "flag": "__all__",
            "score": "__all__",
            "price": "__all__",
            "occurred_on": "__all__",
            "external_id": "__all__",
            "signed_big": "__all__",
        }


__all__ = (
    "ScalarSpecimenTagFilter",
    "ScalarSpecimenFilter",
    "NullableScalarSpecimenFilter",
)
