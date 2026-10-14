"""Admin registrations for the glossary data app."""

from django.contrib import admin

from apps.glossary import models


class _LookupAdmin(admin.ModelAdmin[models.LookupBase]):
    """Admin shared by the status, category and link-kind lookup tables."""

    list_display = ("key", "label", "order")
    search_fields = ("key", "label", "description")
    ordering = ("order", "label")


admin.site.register(models.GlossaryStatus, _LookupAdmin)
admin.site.register(models.GlossaryCategory, _LookupAdmin)
admin.site.register(models.GlossaryTermLinkKind, _LookupAdmin)


class GlossaryAliasInline(admin.TabularInline[models.GlossaryAlias, models.GlossaryTerm]):
    """Inline editor for a term's alternate labels."""

    model = models.GlossaryAlias
    extra = 0


class GlossaryTermLinkInline(admin.TabularInline[models.GlossaryTermLink, models.GlossaryTerm]):
    """Inline editor for a term's outgoing links to other terms."""

    model = models.GlossaryTermLink
    fk_name = "source_term"
    extra = 0
    show_change_link = True
    autocomplete_fields = ("target_term", "kind")


class GlossaryCategoryMembershipInline(
    admin.TabularInline[models.GlossaryCategoryMembership, models.GlossaryTerm],
):
    """Inline editor for the categories a term belongs to."""

    model = models.GlossaryCategoryMembership
    extra = 0
    show_change_link = True
    autocomplete_fields = ("category",)


class GlossarySpecMentionInline(
    admin.TabularInline[models.GlossarySpecMention, models.GlossaryTerm],
):
    """Inline editor for the specs that mention a term."""

    model = models.GlossarySpecMention
    extra = 0
    show_change_link = True


class GlossarySourceLinkInline(
    admin.TabularInline[models.GlossarySourceLink, models.GlossaryTerm],
):
    """Inline editor for a term's source links."""

    model = models.GlossarySourceLink
    extra = 0
    show_change_link = True


@admin.register(models.GlossaryTerm)
class GlossaryTermAdmin(admin.ModelAdmin[models.GlossaryTerm]):
    """Admin for glossary terms, with every edge type edited inline."""

    list_display = (
        "title",
        "anchor",
        "status",
        "entry_order",
        "index_order",
    )
    list_filter = ("status", "categories")
    search_fields = (
        "title",
        "title_sort",
        "anchor",
        "status_text",
        "body",
    )
    autocomplete_fields = ("status",)
    inlines = [
        GlossaryAliasInline,
        GlossaryCategoryMembershipInline,
        GlossaryTermLinkInline,
        GlossarySpecMentionInline,
        GlossarySourceLinkInline,
    ]


@admin.register(models.GlossaryAlias)
class GlossaryAliasAdmin(admin.ModelAdmin[models.GlossaryAlias]):
    """Admin for term aliases, searchable by label and owning term."""

    list_display = ("label", "term", "normalized")
    search_fields = ("label", "normalized", "term__title")
    autocomplete_fields = ("term",)


@admin.register(models.GlossaryTermLink)
class GlossaryTermLinkAdmin(admin.ModelAdmin[models.GlossaryTermLink]):
    """Admin for term-to-term links, filterable by link kind."""

    list_display = (
        "source_term",
        "target_term",
        "kind",
        "order",
        "raw_label",
    )
    list_filter = ("kind",)
    search_fields = ("source_term__title", "target_term__title", "raw_label")
    autocomplete_fields = ("source_term", "target_term", "kind")


@admin.register(models.GlossaryCategoryMembership)
class GlossaryCategoryMembershipAdmin(admin.ModelAdmin[models.GlossaryCategoryMembership]):
    """Admin for category memberships, filterable by category."""

    list_display = ("category", "term", "order")
    list_filter = ("category",)
    search_fields = ("category__label", "term__title")
    autocomplete_fields = ("category", "term")


@admin.register(models.GlossarySpecMention)
class GlossarySpecMentionAdmin(admin.ModelAdmin[models.GlossarySpecMention]):
    """Admin for spec mentions, filterable by spec path."""

    list_display = (
        "spec_path",
        "term",
        "term_text",
        "order",
    )
    list_filter = ("spec_path",)
    search_fields = (
        "spec_path",
        "term_text",
        "notes",
        "term__title",
    )
    autocomplete_fields = ("term",)


@admin.register(models.GlossarySourceLink)
class GlossarySourceLinkAdmin(admin.ModelAdmin[models.GlossarySourceLink]):
    """Admin for term source links, filterable by kind."""

    list_display = (
        "term",
        "label",
        "target",
        "kind",
        "order",
    )
    list_filter = ("kind",)
    search_fields = (
        "term__title",
        "label",
        "target",
        "kind",
    )
    autocomplete_fields = ("term",)
