"""GraphQL schema for the kanban board.

One ``DjangoType`` per model. ``CardType`` is a Relay node (own-PK GlobalID
filtering); ``CardItemType`` is deliberately non-Relay (plain-integer ``id``
filtering). Every type selects its inherited ``created_date`` / ``updated_date``
audit columns and its reverse ``uuid`` accessor, so a query can read both the
audit trail and the stable side-table UUID for any row
(``card { uuid { id } createdDate }``).

The lookup filtersets are attached to their owning types via
``Meta.filterset_class`` so owner-binding resolves at finalization, the same
pattern the scalars app uses.
"""

import strawberry
from strawberry import relay
from strawberry.types import Info

from apps.kanban import filters, models
from django_strawberry_framework import DjangoType, OptimizerHint
from django_strawberry_framework.filters import filter_input_type

# ---------------------------------------------------------------------------
# UUID side-table
# ---------------------------------------------------------------------------


class UUIDModelType(DjangoType):
    """Non-Relay; exposes the UUID ``id`` (a ``UUIDField`` primary key).

    The forward O2O back-links are intentionally not selected -- exactly one is
    non-null per row, so they would be mostly-null noise. Domain types reach
    this through their reverse ``uuid`` accessor.
    """

    class Meta:
        model = models.UUIDModel
        fields = ("id",)


# ---------------------------------------------------------------------------
# Lookup types
# ---------------------------------------------------------------------------


class MilestoneType(DjangoType):
    class Meta:
        model = models.Milestone
        fields = (
            "id",
            "key",
            "label",
            "order",
            "version_floor",
            "version_ceiling",
            "created_date",
            "updated_date",
            "uuid",
            "cards",
            "target_versions",
        )
        filterset_class = filters.MilestoneFilter


class StatusType(DjangoType):
    class Meta:
        model = models.Status
        fields = (
            "id",
            "key",
            "label",
            "order",
            "created_date",
            "updated_date",
            "uuid",
            "cards",
        )
        filterset_class = filters.StatusFilter


class PriorityType(DjangoType):
    class Meta:
        model = models.Priority
        fields = (
            "id",
            "key",
            "label",
            "order",
            "created_date",
            "updated_date",
            "uuid",
            "cards",
        )
        filterset_class = filters.PriorityFilter


class SeverityType(DjangoType):
    class Meta:
        model = models.Severity
        fields = (
            "id",
            "key",
            "label",
            "order",
            "created_date",
            "updated_date",
            "uuid",
            "cards",
        )
        filterset_class = filters.SeverityFilter


class RelativeSizeType(DjangoType):
    class Meta:
        model = models.RelativeSize
        fields = (
            "id",
            "key",
            "label",
            "order",
            "rank",
            "created_date",
            "updated_date",
            "uuid",
            "cards",
            "cards_high",
        )
        filterset_class = filters.RelativeSizeFilter


class PlanningStateType(DjangoType):
    class Meta:
        model = models.PlanningState
        fields = (
            "id",
            "key",
            "label",
            "order",
            "created_date",
            "updated_date",
            "uuid",
            "cards",
        )
        filterset_class = filters.PlanningStateFilter


class UpstreamType(DjangoType):
    class Meta:
        model = models.Upstream
        fields = (
            "id",
            "key",
            "label",
            "order",
            "emoji",
            "created_date",
            "updated_date",
            "uuid",
            "cards",
            "parity_claims",
        )
        filterset_class = filters.UpstreamFilter


class ParityLevelType(DjangoType):
    class Meta:
        model = models.ParityLevel
        fields = (
            "id",
            "key",
            "label",
            "order",
            "created_date",
            "updated_date",
            "uuid",
            "parity_claims",
        )
        filterset_class = filters.ParityLevelFilter


class SectionType(DjangoType):
    class Meta:
        model = models.Section
        fields = (
            "id",
            "key",
            "label",
            "order",
            "created_date",
            "updated_date",
            "uuid",
            "items",
        )
        filterset_class = filters.SectionFilter


class CardReferenceKindType(DjangoType):
    class Meta:
        model = models.CardReferenceKind
        fields = (
            "id",
            "key",
            "label",
            "order",
            "created_date",
            "updated_date",
            "uuid",
            "card_references",
        )
        filterset_class = filters.CardReferenceKindFilter


class CardReferenceSourceType(DjangoType):
    class Meta:
        model = models.CardReferenceSource
        fields = (
            "id",
            "key",
            "label",
            "order",
            "created_date",
            "updated_date",
            "uuid",
            "card_references",
        )
        filterset_class = filters.CardReferenceSourceFilter


class BoardDocKindType(DjangoType):
    class Meta:
        model = models.BoardDocKind
        fields = (
            "id",
            "key",
            "label",
            "order",
            "created_date",
            "updated_date",
            "uuid",
            "docs",
        )
        filterset_class = filters.BoardDocKindFilter


# ---------------------------------------------------------------------------
# Version + spec
# ---------------------------------------------------------------------------


class TargetVersionType(DjangoType):
    class Meta:
        model = models.TargetVersion
        fields = (
            "id",
            "number",
            "milestone",
            "created_date",
            "updated_date",
            "uuid",
            "cards",
        )
        filterset_class = filters.TargetVersionFilter


class SpecDocType(DjangoType):
    class Meta:
        model = models.SpecDoc
        fields = (
            "id",
            "name",
            "url",
            "created_date",
            "updated_date",
            "uuid",
            "card",
        )


# ---------------------------------------------------------------------------
# Card + edges
# ---------------------------------------------------------------------------


class CardType(DjangoType):
    slug: str

    class Meta:
        model = models.Card
        fields = (
            "id",
            "title",
            "number",
            "created_date",
            "updated_date",
            "planning_note",
            "status",
            "priority",
            "severity",
            "relative_size",
            "relative_size_high",
            "planning_state",
            "milestone",
            "target_version",
            "spec",
            "uuid",
            "items",
            "parity_claims",
            "dependencies",
            "dependents",
            "outgoing_references",
            "incoming_references",
            "parity",
            "labels",
        )
        interfaces = (relay.Node,)
        filterset_class = filters.CardFilter
        optimizer_hints = {
            "items": OptimizerHint.prefetch_related(),
            "parity_claims": OptimizerHint.prefetch_related(),
            "dependencies": OptimizerHint.prefetch_related(),
            "outgoing_references": OptimizerHint.prefetch_related(),
            "incoming_references": OptimizerHint.prefetch_related(),
        }


class CardReferenceType(DjangoType):
    class Meta:
        model = models.CardReference
        fields = (
            "id",
            "source_card",
            "target_card",
            "kind",
            "source",
            "raw_text",
            "order",
            "created_date",
            "updated_date",
            "uuid",
        )
        filterset_class = filters.CardReferenceFilter


class ParityClaimType(DjangoType):
    class Meta:
        model = models.ParityClaim
        fields = (
            "id",
            "card",
            "upstream",
            "level",
            "created_date",
            "updated_date",
            "uuid",
        )


class CardItemType(DjangoType):
    """Intentionally NON-Relay so its own ``id`` is a plain integer filter."""

    class Meta:
        model = models.CardItem
        fields = (
            "id",
            "text",
            "order",
            "is_complete",
            "section",
            "card",
            "created_date",
            "updated_date",
            "uuid",
        )
        filterset_class = filters.CardItemFilter


class LabelType(DjangoType):
    class Meta:
        model = models.Label
        fields = (
            "id",
            "key",
            "color",
            "created_date",
            "updated_date",
            "uuid",
            "cards",
        )
        filterset_class = filters.LabelFilter


class BoardDocType(DjangoType):
    class Meta:
        model = models.BoardDoc
        fields = (
            "id",
            "key",
            "kind",
            "title",
            "order",
            "body",
            "created_date",
            "updated_date",
            "uuid",
            "card_references",
        )
        filterset_class = filters.BoardDocFilter
        optimizer_hints = {"card_references": OptimizerHint.prefetch_related()}


class BoardDocCardReferenceType(DjangoType):
    class Meta:
        model = models.BoardDocCardReference
        fields = (
            "id",
            "doc",
            "card",
            "raw_text",
            "order",
            "created_date",
            "updated_date",
            "uuid",
        )
        filterset_class = filters.BoardDocCardReferenceFilter


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------


@strawberry.type
class Query:
    """Kanban board root fields."""

    @strawberry.field
    def all_cards(
        self,
        info: Info,
        filter: filter_input_type(filters.CardFilter) | None = None,  # noqa: A002
    ) -> list[CardType]:
        queryset = models.Card.objects.order_by("number")
        if filter is not None:
            queryset = filters.CardFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_card_items(
        self,
        info: Info,
        filter: filter_input_type(filters.CardItemFilter) | None = None,  # noqa: A002
    ) -> list[CardItemType]:
        queryset = models.CardItem.objects.order_by("id")
        if filter is not None:
            queryset = filters.CardItemFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_statuses(
        self,
        info: Info,
        filter: filter_input_type(filters.StatusFilter) | None = None,  # noqa: A002
    ) -> list[StatusType]:
        queryset = models.Status.objects.order_by("order")
        if filter is not None:
            queryset = filters.StatusFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_priorities(
        self,
        info: Info,
        filter: filter_input_type(filters.PriorityFilter) | None = None,  # noqa: A002
    ) -> list[PriorityType]:
        queryset = models.Priority.objects.order_by("order")
        if filter is not None:
            queryset = filters.PriorityFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_severities(
        self,
        info: Info,
        filter: filter_input_type(filters.SeverityFilter) | None = None,  # noqa: A002
    ) -> list[SeverityType]:
        queryset = models.Severity.objects.order_by("order")
        if filter is not None:
            queryset = filters.SeverityFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_milestones(
        self,
        info: Info,
        filter: filter_input_type(filters.MilestoneFilter) | None = None,  # noqa: A002
    ) -> list[MilestoneType]:
        queryset = models.Milestone.objects.order_by("order")
        if filter is not None:
            queryset = filters.MilestoneFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_planning_states(
        self,
        info: Info,
        filter: filter_input_type(filters.PlanningStateFilter) | None = None,  # noqa: A002
    ) -> list[PlanningStateType]:
        queryset = models.PlanningState.objects.order_by("order")
        if filter is not None:
            queryset = filters.PlanningStateFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_upstreams(
        self,
        info: Info,
        filter: filter_input_type(filters.UpstreamFilter) | None = None,  # noqa: A002
    ) -> list[UpstreamType]:
        queryset = models.Upstream.objects.order_by("order")
        if filter is not None:
            queryset = filters.UpstreamFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_parity_levels(
        self,
        info: Info,
        filter: filter_input_type(filters.ParityLevelFilter) | None = None,  # noqa: A002
    ) -> list[ParityLevelType]:
        queryset = models.ParityLevel.objects.order_by("order")
        if filter is not None:
            queryset = filters.ParityLevelFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_sections(
        self,
        info: Info,
        filter: filter_input_type(filters.SectionFilter) | None = None,  # noqa: A002
    ) -> list[SectionType]:
        queryset = models.Section.objects.order_by("order")
        if filter is not None:
            queryset = filters.SectionFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_reference_kinds(
        self,
        info: Info,
        filter: filter_input_type(filters.CardReferenceKindFilter) | None = None,  # noqa: A002
    ) -> list[CardReferenceKindType]:
        queryset = models.CardReferenceKind.objects.order_by("order")
        if filter is not None:
            queryset = filters.CardReferenceKindFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_reference_sources(
        self,
        info: Info,
        filter: filter_input_type(filters.CardReferenceSourceFilter) | None = None,  # noqa: A002
    ) -> list[CardReferenceSourceType]:
        queryset = models.CardReferenceSource.objects.order_by("order")
        if filter is not None:
            queryset = filters.CardReferenceSourceFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_board_doc_kinds(
        self,
        info: Info,
        filter: filter_input_type(filters.BoardDocKindFilter) | None = None,  # noqa: A002
    ) -> list[BoardDocKindType]:
        queryset = models.BoardDocKind.objects.order_by("order")
        if filter is not None:
            queryset = filters.BoardDocKindFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_target_versions(
        self,
        info: Info,
        filter: filter_input_type(filters.TargetVersionFilter) | None = None,  # noqa: A002
    ) -> list[TargetVersionType]:
        queryset = models.TargetVersion.objects.order_by("number")
        if filter is not None:
            queryset = filters.TargetVersionFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_labels(
        self,
        info: Info,
        filter: filter_input_type(filters.LabelFilter) | None = None,  # noqa: A002
    ) -> list[LabelType]:
        queryset = models.Label.objects.order_by("key")
        if filter is not None:
            queryset = filters.LabelFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_relative_sizes(
        self,
        info: Info,
        filter: filter_input_type(filters.RelativeSizeFilter) | None = None,  # noqa: A002
    ) -> list[RelativeSizeType]:
        queryset = models.RelativeSize.objects.order_by("rank")
        if filter is not None:
            queryset = filters.RelativeSizeFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_board_docs(
        self,
        info: Info,
        filter: filter_input_type(filters.BoardDocFilter) | None = None,  # noqa: A002
    ) -> list[BoardDocType]:
        queryset = models.BoardDoc.objects.order_by("order")
        if filter is not None:
            queryset = filters.BoardDocFilter.apply_sync(filter, queryset, info)
        return queryset


__all__ = ("Query",)
