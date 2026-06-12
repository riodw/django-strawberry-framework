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

from apps.kanban import filters, models, orders
from django_strawberry_framework import DjangoType, OptimizerHint
from django_strawberry_framework.filters import filter_input_type
from django_strawberry_framework.orders import order_input_type

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
        orderset_class = orders.MilestoneOrder


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
        orderset_class = orders.StatusOrder


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
        orderset_class = orders.PriorityOrder


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
        orderset_class = orders.SeverityOrder


class RelativeSizeType(DjangoType):
    class Meta:
        model = models.RelativeSize
        fields = (
            "id",
            "key",
            "label",
            "order",
            "rank",
            "description",
            "created_date",
            "updated_date",
            "uuid",
            "cards",
        )
        filterset_class = filters.RelativeSizeFilter
        orderset_class = orders.RelativeSizeOrder


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
        orderset_class = orders.PlanningStateOrder


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
        orderset_class = orders.UpstreamOrder


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
        orderset_class = orders.ParityLevelOrder


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
        orderset_class = orders.SectionOrder


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
        orderset_class = orders.CardReferenceKindOrder


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
        orderset_class = orders.BoardDocKindOrder


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
        orderset_class = orders.TargetVersionOrder


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


class PackageFileType(DjangoType):
    class Meta:
        model = models.PackageFile
        fields = (
            "id",
            "path",
            "is_current",
            "created_date",
            "updated_date",
            "uuid",
            "cards",
        )
        filterset_class = filters.PackageFileFilter
        orderset_class = orders.PackageFileOrder


# ---------------------------------------------------------------------------
# Card + edges
# ---------------------------------------------------------------------------


class CardType(DjangoType):
    slug: str
    is_blocked: bool
    card_id: str

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
            "glossary_links",
            "changed_files",
        )
        interfaces = (relay.Node,)
        filterset_class = filters.CardFilter
        orderset_class = orders.CardOrder
        optimizer_hints = {
            "items": OptimizerHint.prefetch_related(),
            "parity_claims": OptimizerHint.prefetch_related(),
            "dependencies": OptimizerHint.prefetch_related(),
            "outgoing_references": OptimizerHint.prefetch_related(),
            "incoming_references": OptimizerHint.prefetch_related(),
            "glossary_links": OptimizerHint.prefetch_related(),
            "changed_files": OptimizerHint.prefetch_related(),
        }


class CardReferenceType(DjangoType):
    class Meta:
        model = models.CardReference
        fields = (
            "id",
            "source_card",
            "target_card",
            "kind",
            "raw_text",
            "order",
            "created_date",
            "updated_date",
            "uuid",
        )
        filterset_class = filters.CardReferenceFilter
        orderset_class = orders.CardReferenceOrder


class CardGlossaryTermType(DjangoType):
    class Meta:
        model = models.CardGlossaryTerm
        fields = (
            "id",
            "card",
            "term",
            "raw_text",
            "order",
            "created_date",
            "updated_date",
            "uuid",
        )
        filterset_class = filters.CardGlossaryTermFilter
        orderset_class = orders.CardGlossaryTermOrder


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
        orderset_class = orders.CardItemOrder


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
        orderset_class = orders.LabelOrder


class BoardDocType(DjangoType):
    class Meta:
        model = models.BoardDoc
        fields = (
            "id",
            "namespace",
            "key",
            "kind",
            "title",
            "order",
            "body",
            "include_heading",
            "created_date",
            "updated_date",
            "uuid",
            "card_references",
        )
        filterset_class = filters.BoardDocFilter
        orderset_class = orders.BoardDocOrder
        optimizer_hints = {"card_references": OptimizerHint.prefetch_related()}
        primary = True


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
        orderset_class = orders.BoardDocCardReferenceOrder


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
        order_by: list[order_input_type(orders.CardOrder)] | None = None,
    ) -> list[CardType]:
        queryset = models.Card.objects.order_by("number")
        if filter is not None:
            queryset = filters.CardFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.CardOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_card_items(
        self,
        info: Info,
        filter: filter_input_type(filters.CardItemFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.CardItemOrder)] | None = None,
    ) -> list[CardItemType]:
        queryset = models.CardItem.objects.order_by("id")
        if filter is not None:
            queryset = filters.CardItemFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.CardItemOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_card_glossary_terms(
        self,
        info: Info,
        filter: filter_input_type(filters.CardGlossaryTermFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.CardGlossaryTermOrder)] | None = None,
    ) -> list[CardGlossaryTermType]:
        queryset = models.CardGlossaryTerm.objects.order_by("card__number", "order")
        if filter is not None:
            queryset = filters.CardGlossaryTermFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.CardGlossaryTermOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_statuses(
        self,
        info: Info,
        filter: filter_input_type(filters.StatusFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.StatusOrder)] | None = None,
    ) -> list[StatusType]:
        queryset = models.Status.objects.order_by("order")
        if filter is not None:
            queryset = filters.StatusFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.StatusOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_priorities(
        self,
        info: Info,
        filter: filter_input_type(filters.PriorityFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.PriorityOrder)] | None = None,
    ) -> list[PriorityType]:
        queryset = models.Priority.objects.order_by("order")
        if filter is not None:
            queryset = filters.PriorityFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.PriorityOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_severities(
        self,
        info: Info,
        filter: filter_input_type(filters.SeverityFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.SeverityOrder)] | None = None,
    ) -> list[SeverityType]:
        queryset = models.Severity.objects.order_by("order")
        if filter is not None:
            queryset = filters.SeverityFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.SeverityOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_milestones(
        self,
        info: Info,
        filter: filter_input_type(filters.MilestoneFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.MilestoneOrder)] | None = None,
    ) -> list[MilestoneType]:
        queryset = models.Milestone.objects.order_by("order")
        if filter is not None:
            queryset = filters.MilestoneFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.MilestoneOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_planning_states(
        self,
        info: Info,
        filter: filter_input_type(filters.PlanningStateFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.PlanningStateOrder)] | None = None,
    ) -> list[PlanningStateType]:
        queryset = models.PlanningState.objects.order_by("order")
        if filter is not None:
            queryset = filters.PlanningStateFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.PlanningStateOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_upstreams(
        self,
        info: Info,
        filter: filter_input_type(filters.UpstreamFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.UpstreamOrder)] | None = None,
    ) -> list[UpstreamType]:
        queryset = models.Upstream.objects.order_by("order")
        if filter is not None:
            queryset = filters.UpstreamFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.UpstreamOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_parity_levels(
        self,
        info: Info,
        filter: filter_input_type(filters.ParityLevelFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.ParityLevelOrder)] | None = None,
    ) -> list[ParityLevelType]:
        queryset = models.ParityLevel.objects.order_by("order")
        if filter is not None:
            queryset = filters.ParityLevelFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.ParityLevelOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_sections(
        self,
        info: Info,
        filter: filter_input_type(filters.SectionFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.SectionOrder)] | None = None,
    ) -> list[SectionType]:
        queryset = models.Section.objects.order_by("order")
        if filter is not None:
            queryset = filters.SectionFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.SectionOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_reference_kinds(
        self,
        info: Info,
        filter: filter_input_type(filters.CardReferenceKindFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.CardReferenceKindOrder)] | None = None,
    ) -> list[CardReferenceKindType]:
        queryset = models.CardReferenceKind.objects.order_by("order")
        if filter is not None:
            queryset = filters.CardReferenceKindFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.CardReferenceKindOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_board_doc_kinds(
        self,
        info: Info,
        filter: filter_input_type(filters.BoardDocKindFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.BoardDocKindOrder)] | None = None,
    ) -> list[BoardDocKindType]:
        queryset = models.BoardDocKind.objects.filter(docs__namespace="kanban").distinct()
        queryset = queryset.order_by("order")
        if filter is not None:
            queryset = filters.BoardDocKindFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.BoardDocKindOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_target_versions(
        self,
        info: Info,
        filter: filter_input_type(filters.TargetVersionFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.TargetVersionOrder)] | None = None,
    ) -> list[TargetVersionType]:
        queryset = models.TargetVersion.objects.order_by("number")
        if filter is not None:
            queryset = filters.TargetVersionFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.TargetVersionOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_labels(
        self,
        info: Info,
        filter: filter_input_type(filters.LabelFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.LabelOrder)] | None = None,
    ) -> list[LabelType]:
        queryset = models.Label.objects.order_by("key")
        if filter is not None:
            queryset = filters.LabelFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.LabelOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_package_files(
        self,
        info: Info,
        filter: filter_input_type(filters.PackageFileFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.PackageFileOrder)] | None = None,
    ) -> list[PackageFileType]:
        queryset = models.PackageFile.objects.order_by("path")
        if filter is not None:
            queryset = filters.PackageFileFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.PackageFileOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_relative_sizes(
        self,
        info: Info,
        filter: filter_input_type(filters.RelativeSizeFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.RelativeSizeOrder)] | None = None,
    ) -> list[RelativeSizeType]:
        queryset = models.RelativeSize.objects.order_by("rank")
        if filter is not None:
            queryset = filters.RelativeSizeFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.RelativeSizeOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_board_docs(
        self,
        info: Info,
        filter: filter_input_type(filters.BoardDocFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.BoardDocOrder)] | None = None,
    ) -> list[BoardDocType]:
        queryset = models.BoardDoc.objects.filter(namespace="kanban").order_by("order")
        if filter is not None:
            queryset = filters.BoardDocFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.BoardDocOrder.apply_sync(order_by, queryset, info)
        return queryset


__all__ = ("Query",)
