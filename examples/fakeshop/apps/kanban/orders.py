"""OrderSet declarations for the kanban board app.

One ``OrderSet`` per ``FilterSet`` in ``apps.kanban.filters`` (1:1 with the
owning ``DjangoType``). Each uses the ``Meta.fields = "__all__"`` shorthand,
which expands to every column-backed model field -- the orderable scalars
(``key`` / ``label`` / ``order`` / ``rank`` / audit timestamps / ``body`` /
...) plus forward FK / OneToOne columns (``status`` -> ``status_id``, etc.).
Reverse relations, the reverse ``uuid`` OneToOne accessor, and M2M managers
are excluded by the column-backed rule, so ``"__all__"`` produces a clean
leaf-ordering surface with no nested traversal. No per-field permission
gates -- ordering is a straight wiring of the ``Ordering`` surface.
"""

from __future__ import annotations

from django_strawberry_framework.orders import OrderSet

from . import models


class MilestoneOrder(OrderSet):
    class Meta:
        model = models.Milestone
        fields = "__all__"


class StatusOrder(OrderSet):
    class Meta:
        model = models.Status
        fields = "__all__"


class PriorityOrder(OrderSet):
    class Meta:
        model = models.Priority
        fields = "__all__"


class RelativeSizeOrder(OrderSet):
    class Meta:
        model = models.RelativeSize
        fields = "__all__"


class UpstreamOrder(OrderSet):
    class Meta:
        model = models.Upstream
        fields = "__all__"


class ParityLevelOrder(OrderSet):
    class Meta:
        model = models.ParityLevel
        fields = "__all__"


class SectionOrder(OrderSet):
    class Meta:
        model = models.Section
        fields = "__all__"


class CardReferenceKindOrder(OrderSet):
    class Meta:
        model = models.CardReferenceKind
        fields = "__all__"


class BoardDocKindOrder(OrderSet):
    class Meta:
        model = models.BoardDocKind
        fields = "__all__"


class TargetVersionOrder(OrderSet):
    class Meta:
        model = models.TargetVersion
        fields = "__all__"


class CardOrder(OrderSet):
    class Meta:
        model = models.Card
        fields = "__all__"


class CardReferenceOrder(OrderSet):
    class Meta:
        model = models.CardReference
        fields = "__all__"


class CardGlossaryTermOrder(OrderSet):
    class Meta:
        model = models.CardGlossaryTerm
        fields = "__all__"


class CardItemOrder(OrderSet):
    class Meta:
        model = models.CardItem
        fields = "__all__"


class LabelOrder(OrderSet):
    class Meta:
        model = models.Label
        fields = "__all__"


class TrackedPathOrder(OrderSet):
    class Meta:
        model = models.TrackedPath
        fields = "__all__"


class BoardDocOrder(OrderSet):
    class Meta:
        model = models.BoardDoc
        fields = "__all__"


class BoardDocCardReferenceOrder(OrderSet):
    class Meta:
        model = models.BoardDocCardReference
        fields = "__all__"


class AttemptOutcomeOrder(OrderSet):
    class Meta:
        model = models.AttemptOutcome
        fields = "__all__"


class VerificationKindOrder(OrderSet):
    class Meta:
        model = models.VerificationKind
        fields = "__all__"


class ActorOrder(OrderSet):
    class Meta:
        model = models.Actor
        fields = "__all__"


class CardTransitionOrder(OrderSet):
    class Meta:
        model = models.CardTransition
        fields = "__all__"


class WorkAttemptOrder(OrderSet):
    class Meta:
        model = models.WorkAttempt
        fields = "__all__"


class DecisionOrder(OrderSet):
    class Meta:
        model = models.Decision
        fields = "__all__"


__all__ = (
    "ActorOrder",
    "AttemptOutcomeOrder",
    "BoardDocCardReferenceOrder",
    "BoardDocKindOrder",
    "BoardDocOrder",
    "CardGlossaryTermOrder",
    "CardItemOrder",
    "CardOrder",
    "CardReferenceKindOrder",
    "CardReferenceOrder",
    "CardTransitionOrder",
    "DecisionOrder",
    "LabelOrder",
    "MilestoneOrder",
    "ParityLevelOrder",
    "PriorityOrder",
    "RelativeSizeOrder",
    "SectionOrder",
    "StatusOrder",
    "TargetVersionOrder",
    "TrackedPathOrder",
    "UpstreamOrder",
    "VerificationKindOrder",
    "WorkAttemptOrder",
)
