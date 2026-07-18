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
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef
from strawberry import relay
from strawberry.types import Info

from apps.kanban import filters, models, orders, services
from django_strawberry_framework import (
    DjangoFormMutation,
    DjangoMutationField,
    DjangoType,
    OptimizerHint,
)
from django_strawberry_framework.filters import filter_input_type
from django_strawberry_framework.mutations.resolvers import payload_cls_for
from django_strawberry_framework.orders import order_input_type
from django_strawberry_framework.utils.errors import field_error, validation_error_to_field_errors

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


class RelativeSizeType(DjangoType):
    class Meta:
        model = models.RelativeSize
        fields = (
            "id",
            "key",
            "label",
            "order",
            "description",
            "created_date",
            "updated_date",
            "uuid",
            "cards",
        )
        filterset_class = filters.RelativeSizeFilter
        orderset_class = orders.RelativeSizeOrder


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


class AttemptOutcomeType(DjangoType):
    class Meta:
        model = models.AttemptOutcome
        fields = (
            "id",
            "key",
            "label",
            "order",
            "created_date",
            "updated_date",
            "uuid",
            "work_attempts",
        )
        filterset_class = filters.AttemptOutcomeFilter
        orderset_class = orders.AttemptOutcomeOrder


class VerificationKindType(DjangoType):
    class Meta:
        model = models.VerificationKind
        fields = (
            "id",
            "key",
            "label",
            "order",
            "created_date",
            "updated_date",
            "uuid",
            "card_items",
        )
        filterset_class = filters.VerificationKindFilter
        orderset_class = orders.VerificationKindOrder


class ActorType(DjangoType):
    class Meta:
        model = models.Actor
        fields = (
            "id",
            "key",
            "label",
            "order",
            "kind",
            "created_date",
            "updated_date",
            "uuid",
            "transitions",
            "work_attempts",
            "decisions",
            "verified_items",
        )
        filterset_class = filters.ActorFilter
        orderset_class = orders.ActorOrder


# ---------------------------------------------------------------------------
# Version + spec
# ---------------------------------------------------------------------------


class TargetVersionType(DjangoType):
    class Meta:
        model = models.TargetVersion
        fields = (
            "id",
            "number",
            "major",
            "minor",
            "patch",
            "milestone",
            "created_date",
            "updated_date",
            "uuid",
            "cards",
        )
        filterset_class = filters.TargetVersionFilter
        orderset_class = orders.TargetVersionOrder


class SpecDocType(DjangoType):
    # ``url`` is a derived model property (composed from the repo-relative
    # ``path``); declared here as a resolver-backed scalar field so the GraphQL
    # ``url`` surface keeps working for the KANBAN.html renderer.
    url: str

    class Meta:
        model = models.SpecDoc
        fields = (
            "id",
            "name",
            "path",
            "created_date",
            "updated_date",
            "uuid",
            "card",
        )


class TrackedPathType(DjangoType):
    # ``is_current`` is a derived model property (``state == "current"``);
    # declared as a resolver-backed scalar so the GraphQL ``isCurrent`` surface
    # keeps working for the exporters alongside the richer ``state`` field.
    is_current: bool

    class Meta:
        model = models.TrackedPath
        fields = (
            "id",
            "path",
            "state",
            "is_directory",
            "created_date",
            "updated_date",
            "uuid",
            "cards",
        )
        filterset_class = filters.TrackedPathFilter
        orderset_class = orders.TrackedPathOrder


# ---------------------------------------------------------------------------
# Card + edges
# ---------------------------------------------------------------------------


class CardType(DjangoType):
    slug: str
    is_blocked: bool
    is_ready: bool
    card_id: str
    # ``milestone`` is derived from ``target_version`` (the FK was removed);
    # ``dependencies`` / ``dependents`` resolve from CardReference edges via the
    # model's queryset properties. All three are resolver-backed relation fields
    # (the same "declare-but-resolve-from-attribute" idiom as ``slug`` above).
    #
    # LIMITATION (feedback P2-3): ``dependencies`` / ``dependents`` are N+1 on the
    # full-board export and ``optimizer_hints`` cannot prefetch them. They are
    # backed by Card *properties* (``dependency_cards`` / ``dependent_cards``),
    # not ORM relations, and each property runs a fresh ``Card.objects.filter(...)``
    # per parent. An ``optimizer_hints`` entry cannot express this on two counts:
    # (1) ``types/base.py::_validate_optimizer_hints`` rejects any hint key that is
    # not in ``model._meta.get_fields()`` -- a property is not a model field -- so a
    # ``{"dependencies": ...}`` hint raises ConfigurationError at class-build time;
    # (2) even if it were reachable, the walker resolves no ``django_field`` for a
    # property and skips it before the hint dispatch (``optimizer/walker.py`` #"if
    # django_field is None"), and a property never reads Django's prefetch cache.
    # Prefetching ``outgoing_references__target_card`` / ``incoming_references__
    # source_card`` (the two hops the properties traverse) would require rewriting
    # both as consumer-assigned resolvers that read a ``to_attr`` Prefetch -- which
    # only the consumer's own resolver may own -- and even then the nested Card
    # fields under the ``to_attr`` subtree are a prefetch leaf (not walked), so it
    # trades one N+1 for another while forcing the plan non-cacheable. Left as-is;
    # the export runs once offline. The sibling real relations ``outgoingReferences``
    # / ``incomingReferences`` ARE prefetched (see ``optimizer_hints`` below).
    milestone: "MilestoneType"
    dependencies: list["CardType"]
    dependents: list["CardType"]

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
            "relative_size",
            "target_version",
            "spec",
            "uuid",
            "items",
            "parity_claims",
            "path_links",
            "outgoing_references",
            "incoming_references",
            "parity",
            "labels",
            "glossary_links",
            "changed_files",
            "transitions",
            "work_attempts",
            "decisions",
        )
        interfaces = (relay.Node,)
        filterset_class = filters.CardFilter
        orderset_class = orders.CardOrder
        optimizer_hints = {
            "items": OptimizerHint.prefetch_related(),
            "parity_claims": OptimizerHint.prefetch_related(),
            "path_links": OptimizerHint.prefetch_related(),
            "outgoing_references": OptimizerHint.prefetch_related(),
            "incoming_references": OptimizerHint.prefetch_related(),
            "glossary_links": OptimizerHint.prefetch_related(),
            "changed_files": OptimizerHint.prefetch_related(),
            "transitions": OptimizerHint.prefetch_related(),
            "work_attempts": OptimizerHint.prefetch_related(),
            "decisions": OptimizerHint.prefetch_related(),
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
            "resolved_at",
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


class CardPathLinkType(DjangoType):
    """A ``Card`` <-> ``TrackedPath`` link carrying its ``kind`` (changed/predicted)."""

    class Meta:
        model = models.CardPathLink
        fields = (
            "id",
            "card",
            "path",
            "kind",
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
            "verified_at",
            "verified_by",
            "verification_kind",
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


class CardTransitionType(DjangoType):
    class Meta:
        model = models.CardTransition
        fields = (
            "id",
            "card",
            "from_status",
            "to_status",
            "actor",
            "note",
            "occurred_at",
            "created_date",
            "updated_date",
            "uuid",
        )
        filterset_class = filters.CardTransitionFilter
        orderset_class = orders.CardTransitionOrder


class WorkAttemptType(DjangoType):
    class Meta:
        model = models.WorkAttempt
        fields = (
            "id",
            "card",
            "actor",
            "started_at",
            "ended_at",
            "outcome",
            "summary",
            "evidence",
            "created_date",
            "updated_date",
            "uuid",
        )
        filterset_class = filters.WorkAttemptFilter
        orderset_class = orders.WorkAttemptOrder


class DecisionType(DjangoType):
    class Meta:
        model = models.Decision
        fields = (
            "id",
            "card",
            "actor",
            "question",
            "choice",
            "rationale",
            "decided_at",
            "supersedes",
            "superseded_by_set",
            "created_date",
            "updated_date",
            "uuid",
        )
        filterset_class = filters.DecisionFilter
        orderset_class = orders.DecisionOrder


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
    def ready_cards(
        self,
        info: Info,
        filter: filter_input_type(filters.CardFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.CardOrder)] | None = None,
    ) -> list[CardType]:
        """Cards ready to start now: ``todo``, unblocked, all dependencies done.

        Implemented as a single annotated queryset (``~Exists`` over the card's
        unfinished dependency/blocked_by edges) so selecting the ready set is
        N+1-free, ordered by ``priority.order`` then ``number``.
        """
        unfinished_dependencies = models.CardReference.objects.filter(
            source_card=OuterRef("pk"),
            kind__key__in=models.DEPENDENCY_REFERENCE_KIND_KEYS,
        ).exclude(target_card__status__key=models.DONE_STATUS_KEY)
        queryset = (
            models.Card.objects.filter(status__key=models.TODO_STATUS_KEY)
            .annotate(_has_unfinished_dependency=Exists(unfinished_dependencies))
            .filter(_has_unfinished_dependency=False)
            .order_by("priority__order", "number")
        )
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
    def all_kanban_tracked_paths(
        self,
        info: Info,
        filter: filter_input_type(filters.TrackedPathFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.TrackedPathOrder)] | None = None,
    ) -> list[TrackedPathType]:
        queryset = models.TrackedPath.objects.order_by("path")
        if filter is not None:
            queryset = filters.TrackedPathFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.TrackedPathOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_relative_sizes(
        self,
        info: Info,
        filter: filter_input_type(filters.RelativeSizeFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.RelativeSizeOrder)] | None = None,
    ) -> list[RelativeSizeType]:
        queryset = models.RelativeSize.objects.order_by("order")
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

    @strawberry.field
    def all_kanban_actors(
        self,
        info: Info,
        filter: filter_input_type(filters.ActorFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.ActorOrder)] | None = None,
    ) -> list[ActorType]:
        queryset = models.Actor.objects.order_by("order", "key")
        if filter is not None:
            queryset = filters.ActorFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.ActorOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_attempt_outcomes(
        self,
        info: Info,
        filter: filter_input_type(filters.AttemptOutcomeFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.AttemptOutcomeOrder)] | None = None,
    ) -> list[AttemptOutcomeType]:
        queryset = models.AttemptOutcome.objects.order_by("order")
        if filter is not None:
            queryset = filters.AttemptOutcomeFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.AttemptOutcomeOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_verification_kinds(
        self,
        info: Info,
        filter: filter_input_type(filters.VerificationKindFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.VerificationKindOrder)] | None = None,
    ) -> list[VerificationKindType]:
        queryset = models.VerificationKind.objects.order_by("order")
        if filter is not None:
            queryset = filters.VerificationKindFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.VerificationKindOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_card_transitions(
        self,
        info: Info,
        filter: filter_input_type(filters.CardTransitionFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.CardTransitionOrder)] | None = None,
    ) -> list[CardTransitionType]:
        queryset = models.CardTransition.objects.order_by("card__number", "occurred_at")
        if filter is not None:
            queryset = filters.CardTransitionFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.CardTransitionOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_work_attempts(
        self,
        info: Info,
        filter: filter_input_type(filters.WorkAttemptFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.WorkAttemptOrder)] | None = None,
    ) -> list[WorkAttemptType]:
        queryset = models.WorkAttempt.objects.order_by("card__number", "started_at")
        if filter is not None:
            queryset = filters.WorkAttemptFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.WorkAttemptOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_kanban_decisions(
        self,
        info: Info,
        filter: filter_input_type(filters.DecisionFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.DecisionOrder)] | None = None,
    ) -> list[DecisionType]:
        queryset = models.Decision.objects.order_by("decided_at")
        if filter is not None:
            queryset = filters.DecisionFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.DecisionOrder.apply_sync(order_by, queryset, info)
        return queryset


# ---------------------------------------------------------------------------
# Mutation surface (WS-3B) -- thin GraphQL wrappers over apps.kanban.services
# ---------------------------------------------------------------------------
#
# Every board write goes through the sanctioned service API (services.py); these
# mutations only decode the GraphQL input, call the matching service, and map its
# failures onto the framework's ``{ ok, errors }`` write envelope. We dogfood the
# framework's model-less ``DjangoFormMutation`` (spec-038): each mutation is a plain
# ``forms.Form`` (its fields ARE the generated GraphQL input) whose ``perform_mutate``
# calls the service inside the framework's managed write transaction. Cards are
# identified by their Relay ``GlobalID`` (the framework idiom) via a plain
# ``ModelChoiceField`` over the Relay-Node ``CardType``; ``CardItem`` / ``WorkAttempt``
# are non-Relay, so their ``ModelChoiceField`` inputs are raw integer pks. The
# framework's normal relation decode resolves each id -- no parallel resolver.
#
# Errors: the service raises ``KanbanServiceError`` (carrying a stable ``.code``) for
# caller-correctable failures and Django ``ValidationError`` for an illegal status
# transition (the 2F state-machine guard). ``save_or_field_errors`` (the plain-form
# write hook wrapper) only maps ``IntegrityError``, so ``_ServiceErrorMixin`` overrides
# the resolver seams to catch both service error classes and return the ``{ ok: false,
# errors }`` envelope (the write already rolled back when the exception propagated out
# of the pipeline's ``transaction.atomic()`` block). ValidationErrors flatten via the
# shared ``validation_error_to_field_errors``; a ``KanbanServiceError`` becomes a single
# model-wide (``__all__``) ``FieldError`` whose ``codes`` carry the stable service code.


class IsStaffUser:
    """Board writes require an authenticated staff user -- never anonymous.

    The write side of a board is maintainer/agent territory, so it mirrors the
    strictest sibling posture (products' ``DjangoModelPermission`` default, which
    denies anonymous callers). A model-less ``DjangoFormMutation`` cannot use
    ``DjangoModelPermission`` (it resolves an ``add`` / ``change`` / ``delete`` model
    codename, and these custom-action mutations have no such model operation), so
    this plain permission class enforces the same "not anonymous" contract via
    ``request.user.is_staff``. ``has_permission`` must return a real ``bool`` -- the
    framework rejects a truthy non-bool as an authorization bypass.
    """

    def has_permission(
        self,
        info,
        mutation,
        operation,
        data,
        instance=None,
    ):
        del mutation, operation, data, instance
        context = getattr(info, "context", None)
        request = getattr(context, "request", None) or context
        user = getattr(request, "user", None)
        return bool(user is not None and getattr(user, "is_staff", False))


def _service_error_payload(mutation_cls: type, exc: Exception):
    """Map a service failure onto the mutation's ``{ ok: false, errors }`` payload."""
    payload_cls = payload_cls_for(mutation_cls)
    if isinstance(exc, ValidationError):
        errors = validation_error_to_field_errors(exc)
    else:  # services.KanbanServiceError
        errors = [field_error("", str(exc), codes=exc.code)]
    return payload_cls(ok=False, errors=errors)


class _ServiceErrorMixin:
    """Resolver-seam override translating service errors into the write envelope.

    Placed FIRST in the MRO so its ``resolve_sync`` / ``resolve_async`` win over the
    ``DjangoFormMutation`` seams. It delegates to the framework's plain-form pipeline
    and only adds an outer ``except`` for the two service error classes; the pipeline's
    own ``transaction.atomic()`` has already rolled the partial write back by the time
    the exception surfaces here (mirrors the pipeline's own error-envelope contract).
    """

    @classmethod
    def resolve_sync(cls, info, *, data):
        from django_strawberry_framework.forms.resolvers import resolve_form_sync

        try:
            return resolve_form_sync(cls, info, data=data)
        except (services.KanbanServiceError, ValidationError) as exc:
            return _service_error_payload(cls, exc)

    @classmethod
    async def resolve_async(cls, info, *, data):
        from django_strawberry_framework.forms.resolvers import resolve_form_async

        try:
            return await resolve_form_async(cls, info, data=data)
        except (services.KanbanServiceError, ValidationError) as exc:
            return _service_error_payload(cls, exc)


# --- Forms (each form's fields ARE the generated GraphQL input) ------------- #


class CreateCardFromSpecForm(forms.Form):
    """Scalar card-creation input; the service builds the full card + child rows."""

    title = forms.CharField()
    target_version = forms.CharField()
    relative_size = forms.CharField()
    priority = forms.CharField(required=False)
    status = forms.CharField(required=False)
    planning_note = forms.CharField(required=False)
    number = forms.IntegerField(required=False)


class SetCardStatusForm(forms.Form):
    card = forms.ModelChoiceField(queryset=models.Card.objects.all())
    status_key = forms.CharField()
    actor_key = forms.CharField()
    note = forms.CharField(required=False)


class MoveCardNumberForm(forms.Form):
    card = forms.ModelChoiceField(queryset=models.Card.objects.all())
    number = forms.IntegerField()


class AddDependencyForm(forms.Form):
    source_card = forms.ModelChoiceField(queryset=models.Card.objects.all())
    target_card = forms.ModelChoiceField(queryset=models.Card.objects.all())
    kind = forms.CharField(required=False)
    raw_text = forms.CharField(required=False)


class RemoveDependencyForm(forms.Form):
    source_card = forms.ModelChoiceField(queryset=models.Card.objects.all())
    target_card = forms.ModelChoiceField(queryset=models.Card.objects.all())
    kind = forms.CharField(required=False)


class SetCardItemCompleteForm(forms.Form):
    item = forms.ModelChoiceField(queryset=models.CardItem.objects.all())
    # ``NullBooleanField`` -> ``Boolean`` input: omitted / null falls back to the
    # service default (``complete=True``); an explicit ``false`` un-checks the bullet.
    complete = forms.NullBooleanField(required=False)


class VerifyCardItemForm(forms.Form):
    item = forms.ModelChoiceField(queryset=models.CardItem.objects.all())
    actor_key = forms.CharField()
    kind_key = forms.CharField()


class RecordWorkAttemptForm(forms.Form):
    card = forms.ModelChoiceField(queryset=models.Card.objects.all())
    actor_key = forms.CharField()
    summary = forms.CharField()
    evidence = forms.CharField(required=False)


class FinishWorkAttemptForm(forms.Form):
    attempt = forms.ModelChoiceField(queryset=models.WorkAttempt.objects.all())
    outcome_key = forms.CharField()
    summary = forms.CharField(required=False)


class RecordDecisionForm(forms.Form):
    actor_key = forms.CharField()
    question = forms.CharField()
    choice = forms.CharField()
    rationale = forms.CharField(required=False)
    card = forms.ModelChoiceField(queryset=models.Card.objects.all(), required=False)


class SetCardFilesForm(forms.Form):
    card = forms.ModelChoiceField(queryset=models.Card.objects.all())
    kind = forms.ChoiceField(
        choices=(
            (models.CARD_PATH_LINK_PREDICTED, "predicted"),
            (models.CARD_PATH_LINK_CHANGED, "changed"),
        ),
    )
    # A ``[String!]`` list has no plain-``forms.Field`` shape, so paths ride a
    # ``JSONField`` (-> the ``JSON`` scalar); the service normalizes + allowlist-checks.
    paths = forms.JSONField(required=False)


# --- Mutations (thin wrappers over the services) ---------------------------- #


class CreateCardFromSpec(_ServiceErrorMixin, DjangoFormMutation):
    """Create a card and its child rows from a scalar spec (``services.create_card_from_spec``)."""

    class Meta:
        form_class = CreateCardFromSpecForm
        permission_classes = [IsStaffUser]

    def perform_mutate(self, form, info):
        del info
        data = form.cleaned_data
        spec = {
            "title": data["title"],
            "target_version": data["target_version"],
            "relative_size": data["relative_size"],
        }
        for key in ("priority", "status", "planning_note"):
            if data.get(key):
                spec[key] = data[key]
        if data.get("number") is not None:
            spec["number"] = data["number"]
        services.create_card_from_spec(spec)


class SetCardStatus(_ServiceErrorMixin, DjangoFormMutation):
    """Move a card to a new status, logging a ``CardTransition`` (``services.set_card_status``)."""

    class Meta:
        form_class = SetCardStatusForm
        permission_classes = [IsStaffUser]

    def perform_mutate(self, form, info):
        del info
        data = form.cleaned_data
        services.set_card_status(
            data["card"],
            data["status_key"],
            actor=data["actor_key"],
            note=data.get("note", ""),
        )


class MoveCardNumber(_ServiceErrorMixin, DjangoFormMutation):
    """Move a card to a board number, shifting neighbours (``services.move_card_number``)."""

    class Meta:
        form_class = MoveCardNumberForm
        permission_classes = [IsStaffUser]

    def perform_mutate(self, form, info):
        del info
        data = form.cleaned_data
        services.move_card_number(data["card"], data["number"])


class AddDependency(_ServiceErrorMixin, DjangoFormMutation):
    """Add a dependency edge between two cards (``services.add_dependency``)."""

    class Meta:
        form_class = AddDependencyForm
        permission_classes = [IsStaffUser]

    def perform_mutate(self, form, info):
        del info
        data = form.cleaned_data
        kwargs = {"raw_text": data.get("raw_text", "")}
        if data.get("kind"):
            kwargs["kind"] = data["kind"]
        services.add_dependency(data["source_card"], data["target_card"], **kwargs)


class RemoveDependency(_ServiceErrorMixin, DjangoFormMutation):
    """Remove dependency edge(s) between two cards (``services.remove_dependency``)."""

    class Meta:
        form_class = RemoveDependencyForm
        permission_classes = [IsStaffUser]

    def perform_mutate(self, form, info):
        del info
        data = form.cleaned_data
        services.remove_dependency(
            data["source_card"],
            data["target_card"],
            kind=data.get("kind") or None,
        )


class SetCardItemComplete(_ServiceErrorMixin, DjangoFormMutation):
    """Set a card item's completion checkbox (``services.set_item_complete``)."""

    class Meta:
        form_class = SetCardItemCompleteForm
        permission_classes = [IsStaffUser]

    def perform_mutate(self, form, info):
        del info
        data = form.cleaned_data
        complete = data.get("complete")
        services.set_item_complete(data["item"], True if complete is None else complete)


class VerifyCardItem(_ServiceErrorMixin, DjangoFormMutation):
    """Record auditable verification of a card item (``services.verify_item``)."""

    class Meta:
        form_class = VerifyCardItemForm
        permission_classes = [IsStaffUser]

    def perform_mutate(self, form, info):
        del info
        data = form.cleaned_data
        services.verify_item(data["item"], actor=data["actor_key"], kind=data["kind_key"])


class RecordWorkAttempt(_ServiceErrorMixin, DjangoFormMutation):
    """Open a work attempt on a card (``services.record_attempt``)."""

    class Meta:
        form_class = RecordWorkAttemptForm
        permission_classes = [IsStaffUser]

    def perform_mutate(self, form, info):
        del info
        data = form.cleaned_data
        services.record_attempt(
            data["card"],
            actor=data["actor_key"],
            summary=data["summary"],
            evidence=data.get("evidence", ""),
        )


class FinishWorkAttempt(_ServiceErrorMixin, DjangoFormMutation):
    """Close a work attempt, stamping its outcome (``services.finish_attempt``)."""

    class Meta:
        form_class = FinishWorkAttemptForm
        permission_classes = [IsStaffUser]

    def perform_mutate(self, form, info):
        del info
        data = form.cleaned_data
        services.finish_attempt(
            data["attempt"],
            outcome_key=data["outcome_key"],
            summary=data.get("summary") or None,
        )


class RecordDecision(_ServiceErrorMixin, DjangoFormMutation):
    """Record a design decision, board-level or scoped to a card (``services.record_decision``)."""

    class Meta:
        form_class = RecordDecisionForm
        permission_classes = [IsStaffUser]

    def perform_mutate(self, form, info):
        del info
        data = form.cleaned_data
        services.record_decision(
            actor=data["actor_key"],
            question=data["question"],
            choice=data["choice"],
            rationale=data.get("rationale", ""),
            card=data.get("card"),
        )


class SetCardFiles(_ServiceErrorMixin, DjangoFormMutation):
    """Replace a card's tracked-path links by ``kind`` (predicted / changed).

    Routes to ``services.set_card_predicted_files`` or ``services.set_card_changed_files``
    -- the same strict-vs-planned allowlist split the file importers use.
    """

    class Meta:
        form_class = SetCardFilesForm
        permission_classes = [IsStaffUser]

    def perform_mutate(self, form, info):
        del info
        data = form.cleaned_data
        paths = data.get("paths") or []
        if data["kind"] == models.CARD_PATH_LINK_CHANGED:
            services.set_card_changed_files(data["card"], paths)
        else:
            services.set_card_predicted_files(data["card"], paths)


@strawberry.type
class Mutation:
    """Kanban board write surface -- staff-only, thin wrappers over ``apps.kanban.services``."""

    create_card_from_spec = DjangoMutationField(CreateCardFromSpec)
    set_card_status = DjangoMutationField(SetCardStatus)
    move_card_number = DjangoMutationField(MoveCardNumber)
    add_dependency = DjangoMutationField(AddDependency)
    remove_dependency = DjangoMutationField(RemoveDependency)
    set_card_item_complete = DjangoMutationField(SetCardItemComplete)
    verify_card_item = DjangoMutationField(VerifyCardItem)
    record_work_attempt = DjangoMutationField(RecordWorkAttempt)
    finish_work_attempt = DjangoMutationField(FinishWorkAttempt)
    record_decision = DjangoMutationField(RecordDecision)
    set_card_files = DjangoMutationField(SetCardFiles)


__all__ = ("Mutation", "Query")
