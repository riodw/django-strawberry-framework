"""OrderSet declarations for the kanban board app.

One ``OrderSet`` per ``FilterSet`` in ``apps.kanban.filters`` (1:1 with the
owning ``DjangoType``). Each uses the ``Meta.fields = "__all__"`` shorthand,
which expands to every column-backed model field -- the orderable scalars
(``key`` / ``label`` / ``order`` / ``rank`` / audit timestamps / ``body`` /
...) plus forward FK / OneToOne columns (``status`` -> ``status_id``, etc.) --
and any forward ``ForeignObject``, ordered by its carrier columns. Reverse
relations, the reverse ``uuid`` OneToOne accessor, and M2M managers are
excluded, so ``"__all__"`` produces a clean
leaf-ordering surface with no nested traversal. No per-field permission
gates -- ordering is a straight wiring of the ``Ordering`` surface.
"""

from __future__ import annotations

from django_strawberry_framework.orders import OrderSet

from . import models


class MilestoneOrder(OrderSet):
    """Orders ``Milestone`` rows by every column-backed field."""

    class Meta:
        model = models.Milestone
        fields = "__all__"


class StatusOrder(OrderSet):
    """Orders ``Status`` rows by every column-backed field."""

    class Meta:
        model = models.Status
        fields = "__all__"


class PriorityOrder(OrderSet):
    """Orders ``Priority`` rows by every column-backed field."""

    class Meta:
        model = models.Priority
        fields = "__all__"


class RelativeSizeOrder(OrderSet):
    """Orders ``RelativeSize`` rows by every column-backed field."""

    class Meta:
        model = models.RelativeSize
        fields = "__all__"


class UpstreamOrder(OrderSet):
    """Orders ``Upstream`` rows by every column-backed field."""

    class Meta:
        model = models.Upstream
        fields = "__all__"


class ParityLevelOrder(OrderSet):
    """Orders ``ParityLevel`` rows by every column-backed field."""

    class Meta:
        model = models.ParityLevel
        fields = "__all__"


class SectionOrder(OrderSet):
    """Orders ``Section`` rows by every column-backed field."""

    class Meta:
        model = models.Section
        fields = "__all__"


class CardReferenceKindOrder(OrderSet):
    """Orders ``CardReferenceKind`` rows by every column-backed field."""

    class Meta:
        model = models.CardReferenceKind
        fields = "__all__"


class BoardDocKindOrder(OrderSet):
    """Orders ``BoardDocKind`` rows by every column-backed field."""

    class Meta:
        model = models.BoardDocKind
        fields = "__all__"


class TargetVersionOrder(OrderSet):
    """Orders ``TargetVersion`` rows by every column-backed field."""

    class Meta:
        model = models.TargetVersion
        fields = "__all__"


class CardOrder(OrderSet):
    """Orders ``Card`` rows by every column-backed field."""

    class Meta:
        model = models.Card
        fields = "__all__"


class CardReferenceOrder(OrderSet):
    """Orders ``CardReference`` rows by every column-backed field."""

    class Meta:
        model = models.CardReference
        fields = "__all__"


class CardGlossaryTermOrder(OrderSet):
    """Orders ``CardGlossaryTerm`` rows by every column-backed field."""

    class Meta:
        model = models.CardGlossaryTerm
        fields = "__all__"


class CardItemOrder(OrderSet):
    """Orders ``CardItem`` rows by every column-backed field."""

    class Meta:
        model = models.CardItem
        fields = "__all__"


class LabelOrder(OrderSet):
    """Orders ``Label`` rows by every column-backed field."""

    class Meta:
        model = models.Label
        fields = "__all__"


class TrackedPathOrder(OrderSet):
    """Orders ``TrackedPath`` rows by every column-backed field."""

    class Meta:
        model = models.TrackedPath
        fields = "__all__"


class BoardDocOrder(OrderSet):
    """Orders ``BoardDoc`` rows by every column-backed field."""

    class Meta:
        model = models.BoardDoc
        fields = "__all__"


class BoardDocCardReferenceOrder(OrderSet):
    """Orders ``BoardDocCardReference`` rows by every column-backed field."""

    class Meta:
        model = models.BoardDocCardReference
        fields = "__all__"


class AttemptOutcomeOrder(OrderSet):
    """Orders ``AttemptOutcome`` rows by every column-backed field."""

    class Meta:
        model = models.AttemptOutcome
        fields = "__all__"


class VerificationKindOrder(OrderSet):
    """Orders ``VerificationKind`` rows by every column-backed field."""

    class Meta:
        model = models.VerificationKind
        fields = "__all__"


class ActorOrder(OrderSet):
    """Orders ``Actor`` rows by every column-backed field."""

    class Meta:
        model = models.Actor
        fields = "__all__"


class CardTransitionOrder(OrderSet):
    """Orders ``CardTransition`` rows by every column-backed field."""

    class Meta:
        model = models.CardTransition
        fields = "__all__"


class WorkAttemptOrder(OrderSet):
    """Orders ``WorkAttempt`` rows by every column-backed field."""

    class Meta:
        model = models.WorkAttempt
        fields = "__all__"


class DecisionOrder(OrderSet):
    """Orders ``Decision`` rows by every column-backed field."""

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
