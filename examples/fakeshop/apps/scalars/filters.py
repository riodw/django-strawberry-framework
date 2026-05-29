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
which makes ``"id": ["exact", "in"]`` exercise the django-filter-generated
``BaseInFilter`` -> ``list[int]`` converter path (the non-Relay
counterpart to the library app's own-PK ``GlobalIDMultipleChoiceFilter``).

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
            "id": ["exact", "in"],
            "label": ["exact", "icontains"],
            "active": ["exact"],
        }


class ScalarSpecimenFilter(FilterSet):
    tag = RelatedFilter(ScalarSpecimenTagFilter, field_name="tag")

    class Meta:
        model = models.ScalarSpecimen
        # Every converted scalar except ``payload`` (JSONField has no
        # django-filter default). ``gt`` / ``lt`` on the ordered scalars
        # exercises comparison-lookup inputs alongside ``exact``.
        fields = {
            "id": ["exact", "in"],
            "label": ["exact", "icontains"],
            "flag": ["exact"],
            "score": ["exact", "gt", "lt"],
            "price": ["exact", "gt", "lt"],
            "occurred_on": ["exact", "gt", "lt"],
            "occurred_at": ["exact"],
            "occurred_time": ["exact"],
            "external_id": ["exact"],
            "signed_big": ["exact", "gt", "lt"],
            "unsigned_big": ["exact"],
        }


class NullableScalarSpecimenFilter(FilterSet):
    partner = RelatedFilter(ScalarSpecimenFilter, field_name="partner")

    class Meta:
        model = models.NullableScalarSpecimen
        fields = {
            "id": ["exact", "in"],
            "label": ["exact", "icontains"],
            "flag": ["exact"],
            "score": ["exact"],
            "price": ["exact"],
            "occurred_on": ["exact"],
            "external_id": ["exact"],
            "signed_big": ["exact"],
        }


__all__ = (
    "ScalarSpecimenTagFilter",
    "ScalarSpecimenFilter",
    "NullableScalarSpecimenFilter",
)
