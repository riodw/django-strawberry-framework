"""FilterSet declarations for the kanban board.

Because every categorical card field is a foreign key into a lookup table,
filtering "by status / priority / size / milestone / version" is done with a
``RelatedFilter`` onto a small lookup filterset that matches on ``key`` (or
``label``). So this is the most ``RelatedFilter``-dense surface in the example
tree -- it exercises the cross-relation filter path from ``DONE-021-0.0.8`` far
harder than the other apps, while still meaning something concrete ("all
``done`` cards in milestone ``alpha`` sized ``xl`` with a ``strawberry_django``
parity claim").

``CardType`` is a Relay node, so own-PK ``id`` filtering rides the
``GlobalID`` path. ``CardItemType`` is intentionally NOT a Relay node, so its
own ``id`` stays a plain integer -- exercising the django-filter
``BaseInFilter -> list[int]`` branch (the non-Relay counterpart).

Each lookup filterset is attached to its owning ``DjangoType`` via
``Meta.filterset_class`` in ``schema.py`` so owner-binding resolves at
finalization (the same pattern the scalars app uses for ``tag``).
"""

from __future__ import annotations

from django_strawberry_framework.filters import FilterSet, RelatedFilter

from . import models

# ---------------------------------------------------------------------------
# Lookup filtersets (matched on key / label)
# ---------------------------------------------------------------------------


class MilestoneFilter(FilterSet):
    class Meta:
        model = models.Milestone
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class StatusFilter(FilterSet):
    class Meta:
        model = models.Status
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class PriorityFilter(FilterSet):
    class Meta:
        model = models.Priority
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class SeverityFilter(FilterSet):
    class Meta:
        model = models.Severity
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class RelativeSizeFilter(FilterSet):
    class Meta:
        model = models.RelativeSize
        fields = {
            "id": "__all__",
            "key": "__all__",
            "label": "__all__",
            "rank": "__all__",
        }


class UpstreamFilter(FilterSet):
    class Meta:
        model = models.Upstream
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class CardReferenceKindFilter(FilterSet):
    class Meta:
        model = models.CardReferenceKind
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class CardReferenceSourceFilter(FilterSet):
    class Meta:
        model = models.CardReferenceSource
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class TargetVersionFilter(FilterSet):
    class Meta:
        model = models.TargetVersion
        fields = {"id": "__all__", "number": "__all__"}


class CardItemFilter(FilterSet):
    class Meta:
        model = models.CardItem
        # CardItemType is intentionally non-Relay, so ``id`` is a plain integer
        # filter -> exercises the django-filter ``BaseInFilter -> list[int]``
        # path (the non-Relay counterpart to Card's own-PK GlobalID set).
        fields = {
            "id": "__all__",
            "text": "__all__",
            "order": "__all__",
            "is_complete": "__all__",
        }


class CardReferenceFilter(FilterSet):
    kind = RelatedFilter(CardReferenceKindFilter, field_name="kind")
    source = RelatedFilter(CardReferenceSourceFilter, field_name="source")

    class Meta:
        model = models.CardReference
        fields = {
            "id": "__all__",
            "raw_text": "__all__",
            "order": "__all__",
        }


# ---------------------------------------------------------------------------
# Card -- RelatedFilter-dense, including a self-referential dependency filter
# ---------------------------------------------------------------------------


class CardFilter(FilterSet):
    status = RelatedFilter(StatusFilter, field_name="status")
    priority = RelatedFilter(PriorityFilter, field_name="priority")
    severity = RelatedFilter(SeverityFilter, field_name="severity")
    relative_size = RelatedFilter(RelativeSizeFilter, field_name="relative_size")
    milestone = RelatedFilter(MilestoneFilter, field_name="milestone")
    target_version = RelatedFilter(TargetVersionFilter, field_name="target_version")
    parity = RelatedFilter(UpstreamFilter, field_name="parity")
    items = RelatedFilter(CardItemFilter, field_name="items")
    # Self-referential RelatedFilter -- exercises the cycle-safe expansion path
    # against a genuine self-reference (a CardFilter pointing back at itself).
    dependencies = RelatedFilter("apps.kanban.filters.CardFilter", field_name="dependencies")
    outgoing_references = RelatedFilter(CardReferenceFilter, field_name="outgoing_references")
    incoming_references = RelatedFilter(CardReferenceFilter, field_name="incoming_references")

    class Meta:
        model = models.Card
        # The only direct scalar lookups left on Card; everything categorical is
        # a RelatedFilter above. Per-field "__all__" expands each to its full
        # concrete-lookup set.
        fields = {"id": "__all__", "title": "__all__", "number": "__all__"}


__all__ = (
    "MilestoneFilter",
    "StatusFilter",
    "PriorityFilter",
    "SeverityFilter",
    "RelativeSizeFilter",
    "UpstreamFilter",
    "CardReferenceKindFilter",
    "CardReferenceSourceFilter",
    "TargetVersionFilter",
    "CardItemFilter",
    "CardReferenceFilter",
    "CardFilter",
)
