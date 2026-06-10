"""FilterSet declarations for the glossary data app."""

from __future__ import annotations

from apps.kanban import models as kanban_models
from django_strawberry_framework.filters import FilterSet, RelatedFilter

from . import models


class GlossaryStatusFilter(FilterSet):
    class Meta:
        model = models.GlossaryStatus
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class GlossaryCategoryFilter(FilterSet):
    class Meta:
        model = models.GlossaryCategory
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class GlossaryAliasFilter(FilterSet):
    class Meta:
        model = models.GlossaryAlias
        fields = {"id": "__all__", "label": "__all__", "normalized": "__all__"}


class GlossaryTermLinkKindFilter(FilterSet):
    class Meta:
        model = models.GlossaryTermLinkKind
        fields = {"id": "__all__", "key": "__all__", "label": "__all__"}


class GlossaryTermLinkFilter(FilterSet):
    kind = RelatedFilter(GlossaryTermLinkKindFilter, field_name="kind")

    class Meta:
        model = models.GlossaryTermLink
        fields = {"id": "__all__", "raw_label": "__all__", "order": "__all__"}


class GlossaryCategoryMembershipFilter(FilterSet):
    category = RelatedFilter(GlossaryCategoryFilter, field_name="category")

    class Meta:
        model = models.GlossaryCategoryMembership
        fields = {"id": "__all__", "order": "__all__"}


class GlossarySpecMentionFilter(FilterSet):
    class Meta:
        model = models.GlossarySpecMention
        fields = {
            "id": "__all__",
            "spec_path": "__all__",
            "term_text": "__all__",
            "notes": "__all__",
            "order": "__all__",
        }


class GlossarySourceLinkFilter(FilterSet):
    class Meta:
        model = models.GlossarySourceLink
        fields = {
            "id": "__all__",
            "label": "__all__",
            "target": "__all__",
            "kind": "__all__",
            "order": "__all__",
        }


class GlossaryDocumentFilter(FilterSet):
    class Meta:
        model = kanban_models.BoardDoc
        fields = {
            "id": "__all__",
            "namespace": "__all__",
            "key": "__all__",
            "title": "__all__",
            "order": "__all__",
            "include_heading": "__all__",
        }


class GlossaryTermFilter(FilterSet):
    status = RelatedFilter(GlossaryStatusFilter, field_name="status")
    categories = RelatedFilter(GlossaryCategoryFilter, field_name="categories")
    aliases = RelatedFilter(GlossaryAliasFilter, field_name="aliases")
    spec_mentions = RelatedFilter(GlossarySpecMentionFilter, field_name="spec_mentions")
    outgoing_links = RelatedFilter(GlossaryTermLinkFilter, field_name="outgoing_links")
    incoming_links = RelatedFilter(GlossaryTermLinkFilter, field_name="incoming_links")

    class Meta:
        model = models.GlossaryTerm
        fields = {
            "id": "__all__",
            "title": "__all__",
            "title_sort": "__all__",
            "anchor": "__all__",
            "status_text": "__all__",
            "body": "__all__",
            "entry_order": "__all__",
            "index_order": "__all__",
        }


__all__ = (
    "GlossaryAliasFilter",
    "GlossaryCategoryFilter",
    "GlossaryCategoryMembershipFilter",
    "GlossaryDocumentFilter",
    "GlossarySourceLinkFilter",
    "GlossarySpecMentionFilter",
    "GlossaryStatusFilter",
    "GlossaryTermFilter",
    "GlossaryTermLinkFilter",
    "GlossaryTermLinkKindFilter",
)
