"""GraphQL schema for the glossary data app."""

import strawberry
from strawberry.types import Info

from apps.glossary import filters, models, orders
from apps.kanban import models as kanban_models
from django_strawberry_framework import DjangoType, OptimizerHint
from django_strawberry_framework.filters import filter_input_type
from django_strawberry_framework.orders import order_input_type


class GlossaryStatusType(DjangoType):
    class Meta:
        model = models.GlossaryStatus
        fields = (
            "id",
            "key",
            "label",
            "order",
            "description",
            "created_date",
            "updated_date",
            "terms",
        )
        filterset_class = filters.GlossaryStatusFilter
        orderset_class = orders.GlossaryStatusOrder


class GlossaryCategoryType(DjangoType):
    class Meta:
        model = models.GlossaryCategory
        fields = (
            "id",
            "key",
            "label",
            "order",
            "description",
            "created_date",
            "updated_date",
            "terms",
            "memberships",
        )
        filterset_class = filters.GlossaryCategoryFilter
        orderset_class = orders.GlossaryCategoryOrder
        optimizer_hints = {"memberships": OptimizerHint.prefetch_related()}


class GlossaryTermType(DjangoType):
    class Meta:
        model = models.GlossaryTerm
        fields = (
            "id",
            "title",
            "title_sort",
            "anchor",
            "status",
            "status_text",
            "body",
            "entry_order",
            "index_order",
            "created_date",
            "updated_date",
            "categories",
            "aliases",
            "related_terms",
            "related_from",
            "outgoing_links",
            "incoming_links",
            "category_memberships",
            "spec_mentions",
            "source_links",
        )
        filterset_class = filters.GlossaryTermFilter
        orderset_class = orders.GlossaryTermOrder
        optimizer_hints = {
            "categories": OptimizerHint.prefetch_related(),
            "aliases": OptimizerHint.prefetch_related(),
            "outgoing_links": OptimizerHint.prefetch_related(),
            "incoming_links": OptimizerHint.prefetch_related(),
            "category_memberships": OptimizerHint.prefetch_related(),
            "spec_mentions": OptimizerHint.prefetch_related(),
            "source_links": OptimizerHint.prefetch_related(),
        }


class GlossaryAliasType(DjangoType):
    class Meta:
        model = models.GlossaryAlias
        fields = (
            "id",
            "term",
            "label",
            "normalized",
            "created_date",
            "updated_date",
        )
        filterset_class = filters.GlossaryAliasFilter
        orderset_class = orders.GlossaryAliasOrder


class GlossaryTermLinkKindType(DjangoType):
    class Meta:
        model = models.GlossaryTermLinkKind
        fields = (
            "id",
            "key",
            "label",
            "order",
            "description",
            "created_date",
            "updated_date",
            "links",
        )
        filterset_class = filters.GlossaryTermLinkKindFilter
        orderset_class = orders.GlossaryTermLinkKindOrder


class GlossaryTermLinkType(DjangoType):
    class Meta:
        model = models.GlossaryTermLink
        fields = (
            "id",
            "source_term",
            "target_term",
            "kind",
            "raw_label",
            "order",
            "created_date",
            "updated_date",
        )
        filterset_class = filters.GlossaryTermLinkFilter
        orderset_class = orders.GlossaryTermLinkOrder


class GlossaryCategoryMembershipType(DjangoType):
    class Meta:
        model = models.GlossaryCategoryMembership
        fields = (
            "id",
            "category",
            "term",
            "order",
            "created_date",
            "updated_date",
        )
        filterset_class = filters.GlossaryCategoryMembershipFilter
        orderset_class = orders.GlossaryCategoryMembershipOrder


class GlossarySpecMentionType(DjangoType):
    spec_name: str

    class Meta:
        model = models.GlossarySpecMention
        fields = (
            "id",
            "term",
            "spec_path",
            "term_text",
            "notes",
            "order",
            "created_date",
            "updated_date",
        )
        filterset_class = filters.GlossarySpecMentionFilter
        orderset_class = orders.GlossarySpecMentionOrder


class GlossarySourceLinkType(DjangoType):
    class Meta:
        model = models.GlossarySourceLink
        fields = (
            "id",
            "term",
            "label",
            "target",
            "kind",
            "order",
            "created_date",
            "updated_date",
        )
        filterset_class = filters.GlossarySourceLinkFilter
        orderset_class = orders.GlossarySourceLinkOrder


class GlossaryDocumentType(DjangoType):
    class Meta:
        model = kanban_models.BoardDoc
        fields = (
            "id",
            "namespace",
            "key",
            "title",
            "order",
            "body",
            "include_heading",
            "created_date",
            "updated_date",
        )
        filterset_class = filters.GlossaryDocumentFilter
        orderset_class = orders.GlossaryDocumentOrder
        primary = False


@strawberry.type
class Query:
    """Glossary root fields."""

    @strawberry.field
    def all_glossary_terms(
        self,
        info: Info,
        filter: filter_input_type(filters.GlossaryTermFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.GlossaryTermOrder)] | None = None,
    ) -> list[GlossaryTermType]:
        queryset = models.GlossaryTerm.objects.order_by("entry_order", "title_sort")
        if filter is not None:
            queryset = filters.GlossaryTermFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.GlossaryTermOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_glossary_statuses(
        self,
        info: Info,
        filter: filter_input_type(filters.GlossaryStatusFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.GlossaryStatusOrder)] | None = None,
    ) -> list[GlossaryStatusType]:
        queryset = models.GlossaryStatus.objects.order_by("order", "label")
        if filter is not None:
            queryset = filters.GlossaryStatusFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.GlossaryStatusOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_glossary_categories(
        self,
        info: Info,
        filter: filter_input_type(filters.GlossaryCategoryFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.GlossaryCategoryOrder)] | None = None,
    ) -> list[GlossaryCategoryType]:
        queryset = models.GlossaryCategory.objects.order_by("order", "label")
        if filter is not None:
            queryset = filters.GlossaryCategoryFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.GlossaryCategoryOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_glossary_category_memberships(
        self,
        info: Info,
        filter: filter_input_type(filters.GlossaryCategoryMembershipFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.GlossaryCategoryMembershipOrder)] | None = None,
    ) -> list[GlossaryCategoryMembershipType]:
        queryset = models.GlossaryCategoryMembership.objects.order_by("category__order", "order")
        if filter is not None:
            queryset = filters.GlossaryCategoryMembershipFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.GlossaryCategoryMembershipOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_glossary_aliases(
        self,
        info: Info,
        filter: filter_input_type(filters.GlossaryAliasFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.GlossaryAliasOrder)] | None = None,
    ) -> list[GlossaryAliasType]:
        queryset = models.GlossaryAlias.objects.order_by("term__title_sort", "label")
        if filter is not None:
            queryset = filters.GlossaryAliasFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.GlossaryAliasOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_glossary_term_link_kinds(
        self,
        info: Info,
        filter: filter_input_type(filters.GlossaryTermLinkKindFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.GlossaryTermLinkKindOrder)] | None = None,
    ) -> list[GlossaryTermLinkKindType]:
        queryset = models.GlossaryTermLinkKind.objects.order_by("order", "label")
        if filter is not None:
            queryset = filters.GlossaryTermLinkKindFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.GlossaryTermLinkKindOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_glossary_term_links(
        self,
        info: Info,
        filter: filter_input_type(filters.GlossaryTermLinkFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.GlossaryTermLinkOrder)] | None = None,
    ) -> list[GlossaryTermLinkType]:
        queryset = models.GlossaryTermLink.objects.order_by("source_term__title_sort", "order")
        if filter is not None:
            queryset = filters.GlossaryTermLinkFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.GlossaryTermLinkOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_glossary_spec_mentions(
        self,
        info: Info,
        filter: filter_input_type(filters.GlossarySpecMentionFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.GlossarySpecMentionOrder)] | None = None,
    ) -> list[GlossarySpecMentionType]:
        queryset = models.GlossarySpecMention.objects.order_by("spec_path", "order")
        if filter is not None:
            queryset = filters.GlossarySpecMentionFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.GlossarySpecMentionOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_glossary_source_links(
        self,
        info: Info,
        filter: filter_input_type(filters.GlossarySourceLinkFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.GlossarySourceLinkOrder)] | None = None,
    ) -> list[GlossarySourceLinkType]:
        queryset = models.GlossarySourceLink.objects.order_by("term__title_sort", "order")
        if filter is not None:
            queryset = filters.GlossarySourceLinkFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.GlossarySourceLinkOrder.apply_sync(order_by, queryset, info)
        return queryset

    @strawberry.field
    def all_glossary_documents(
        self,
        info: Info,
        filter: filter_input_type(filters.GlossaryDocumentFilter) | None = None,  # noqa: A002
        order_by: list[order_input_type(orders.GlossaryDocumentOrder)] | None = None,
    ) -> list[GlossaryDocumentType]:
        queryset = kanban_models.BoardDoc.objects.filter(namespace="glossary").order_by("order")
        if filter is not None:
            queryset = filters.GlossaryDocumentFilter.apply_sync(filter, queryset, info)
        if order_by is not None:
            queryset = orders.GlossaryDocumentOrder.apply_sync(order_by, queryset, info)
        return queryset


__all__ = ("Query",)
