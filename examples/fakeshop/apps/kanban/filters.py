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


class RelativeSizeFilter(FilterSet):
    class Meta:
        model = models.RelativeSize
        fields = {
            "id": "__all__",
            "key": "__all__",
            "label": "__all__",
            "order": "__all__",
        }


class UpstreamFilter(FilterSet):
    class Meta:
        model = models.Upstream
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class ParityLevelFilter(FilterSet):
    class Meta:
        model = models.ParityLevel
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class SectionFilter(FilterSet):
    class Meta:
        model = models.Section
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class CardReferenceKindFilter(FilterSet):
    class Meta:
        model = models.CardReferenceKind
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class BoardDocKindFilter(FilterSet):
    class Meta:
        model = models.BoardDocKind
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class TargetVersionFilter(FilterSet):
    class Meta:
        model = models.TargetVersion
        fields = {"id": "__all__", "number": "__all__"}


class AttemptOutcomeFilter(FilterSet):
    class Meta:
        model = models.AttemptOutcome
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class VerificationKindFilter(FilterSet):
    class Meta:
        model = models.VerificationKind
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class ActorFilter(FilterSet):
    class Meta:
        model = models.Actor
        fields = {
            "id": "__all__",
            "key": "__all__",
            "label": "__all__",
            "kind": "__all__",
        }


class CardTransitionFilter(FilterSet):
    from_status = RelatedFilter(StatusFilter, field_name="from_status")
    to_status = RelatedFilter(StatusFilter, field_name="to_status")
    actor = RelatedFilter(ActorFilter, field_name="actor")

    class Meta:
        model = models.CardTransition
        fields = {"id": "__all__", "note": "__all__", "occurred_at": "__all__"}


class WorkAttemptFilter(FilterSet):
    actor = RelatedFilter(ActorFilter, field_name="actor")
    outcome = RelatedFilter(AttemptOutcomeFilter, field_name="outcome")

    class Meta:
        model = models.WorkAttempt
        fields = {
            "id": "__all__",
            "summary": "__all__",
            "evidence": "__all__",
            "started_at": "__all__",
            "ended_at": "__all__",
        }


class DecisionFilter(FilterSet):
    actor = RelatedFilter(ActorFilter, field_name="actor")

    class Meta:
        model = models.Decision
        fields = {
            "id": "__all__",
            "question": "__all__",
            "choice": "__all__",
            "rationale": "__all__",
            "decided_at": "__all__",
        }


class LabelFilter(FilterSet):
    class Meta:
        model = models.Label
        fields = {"id": "__all__", "key": "__all__", "color": "__all__"}


class TrackedPathFilter(FilterSet):
    class Meta:
        model = models.TrackedPath
        fields = {
            "id": "__all__",
            "path": "__all__",
            "state": "__all__",
            "is_directory": "__all__",
        }


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

    class Meta:
        model = models.CardReference
        fields = {"id": "__all__", "raw_text": "__all__", "order": "__all__"}


class CardGlossaryTermFilter(FilterSet):
    term = RelatedFilter("apps.glossary.filters.GlossaryTermFilter", field_name="term")

    class Meta:
        model = models.CardGlossaryTerm
        fields = {"id": "__all__", "raw_text": "__all__", "order": "__all__"}


class BoardDocCardReferenceFilter(FilterSet):
    class Meta:
        model = models.BoardDocCardReference
        fields = {"id": "__all__", "raw_text": "__all__", "order": "__all__"}


class BoardDocFilter(FilterSet):
    kind = RelatedFilter(BoardDocKindFilter, field_name="kind")
    card_references = RelatedFilter(
        BoardDocCardReferenceFilter,
        field_name="card_references",
    )

    class Meta:
        model = models.BoardDoc
        fields = {
            "id": "__all__",
            "namespace": "__all__",
            "key": "__all__",
            "title": "__all__",
            "order": "__all__",
            "include_heading": "__all__",
        }


# ---------------------------------------------------------------------------
# Card -- RelatedFilter-dense, including a self-referential dependency filter
# ---------------------------------------------------------------------------


class CardFilter(FilterSet):
    status = RelatedFilter(StatusFilter, field_name="status")
    priority = RelatedFilter(PriorityFilter, field_name="priority")
    relative_size = RelatedFilter(RelativeSizeFilter, field_name="relative_size")
    # Milestone is derived from the target version, so the filter is a related
    # path through ``target_version`` rather than a direct FK.
    milestone = RelatedFilter(MilestoneFilter, field_name="target_version__milestone")
    target_version = RelatedFilter(TargetVersionFilter, field_name="target_version")
    parity = RelatedFilter(UpstreamFilter, field_name="parity")
    items = RelatedFilter(CardItemFilter, field_name="items")
    labels = RelatedFilter(LabelFilter, field_name="labels")
    # Self-referential RelatedFilters over CardReference edges (the M2M was
    # replaced) -- still exercise the cycle-safe self-reference expansion path.
    dependencies = RelatedFilter(
        "apps.kanban.filters.CardFilter",
        field_name="outgoing_references__target_card",
    )
    dependents = RelatedFilter(
        "apps.kanban.filters.CardFilter",
        field_name="incoming_references__source_card",
    )
    outgoing_references = RelatedFilter(CardReferenceFilter, field_name="outgoing_references")
    incoming_references = RelatedFilter(CardReferenceFilter, field_name="incoming_references")
    glossary_links = RelatedFilter(CardGlossaryTermFilter, field_name="glossary_links")
    changed_files = RelatedFilter(TrackedPathFilter, field_name="changed_files")

    class Meta:
        model = models.Card
        # The only direct scalar lookups left on Card; everything categorical is
        # a RelatedFilter above. Per-field "__all__" expands each to its full
        # concrete-lookup set.
        fields = {"id": "__all__", "title": "__all__", "number": "__all__"}


__all__ = (
    "ActorFilter",
    "AttemptOutcomeFilter",
    "BoardDocCardReferenceFilter",
    "BoardDocFilter",
    "BoardDocKindFilter",
    "CardFilter",
    "CardGlossaryTermFilter",
    "CardItemFilter",
    "CardReferenceFilter",
    "CardReferenceKindFilter",
    "CardTransitionFilter",
    "DecisionFilter",
    "LabelFilter",
    "MilestoneFilter",
    "ParityLevelFilter",
    "PriorityFilter",
    "RelativeSizeFilter",
    "SectionFilter",
    "StatusFilter",
    "TargetVersionFilter",
    "TrackedPathFilter",
    "UpstreamFilter",
    "VerificationKindFilter",
    "WorkAttemptFilter",
)
