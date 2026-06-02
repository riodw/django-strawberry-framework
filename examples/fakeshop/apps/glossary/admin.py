"""Admin registrations for the glossary data app."""

from django.contrib import admin

from apps.glossary import models


class _LookupAdmin(admin.ModelAdmin):
    list_display = ("key", "label", "order")
    search_fields = ("key", "label", "description")
    ordering = ("order", "label")


admin.site.register(models.GlossaryStatus, _LookupAdmin)
admin.site.register(models.GlossaryCategory, _LookupAdmin)
admin.site.register(models.GlossaryTermLinkKind, _LookupAdmin)


class GlossaryAliasInline(admin.TabularInline):
    model = models.GlossaryAlias
    extra = 0


class GlossaryTermLinkInline(admin.TabularInline):
    model = models.GlossaryTermLink
    fk_name = "source_term"
    extra = 0
    show_change_link = True
    autocomplete_fields = ("target_term", "kind")


class GlossaryCategoryMembershipInline(admin.TabularInline):
    model = models.GlossaryCategoryMembership
    extra = 0
    show_change_link = True
    autocomplete_fields = ("category",)


class GlossarySpecMentionInline(admin.TabularInline):
    model = models.GlossarySpecMention
    extra = 0
    show_change_link = True


class GlossarySourceLinkInline(admin.TabularInline):
    model = models.GlossarySourceLink
    extra = 0
    show_change_link = True


@admin.register(models.GlossaryTerm)
class GlossaryTermAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "anchor",
        "status",
        "entry_order",
        "index_order",
    )
    list_filter = ("status", "categories")
    search_fields = ("title", "title_sort", "anchor", "status_text", "body")
    autocomplete_fields = ("status",)
    inlines = [
        GlossaryAliasInline,
        GlossaryCategoryMembershipInline,
        GlossaryTermLinkInline,
        GlossarySpecMentionInline,
        GlossarySourceLinkInline,
    ]


@admin.register(models.GlossaryAlias)
class GlossaryAliasAdmin(admin.ModelAdmin):
    list_display = ("label", "term", "normalized")
    search_fields = ("label", "normalized", "term__title")
    autocomplete_fields = ("term",)


@admin.register(models.GlossaryTermLink)
class GlossaryTermLinkAdmin(admin.ModelAdmin):
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
class GlossaryCategoryMembershipAdmin(admin.ModelAdmin):
    list_display = ("category", "term", "order")
    list_filter = ("category",)
    search_fields = ("category__label", "term__title")
    autocomplete_fields = ("category", "term")


@admin.register(models.GlossarySpecMention)
class GlossarySpecMentionAdmin(admin.ModelAdmin):
    list_display = ("spec_path", "term", "term_text", "order")
    list_filter = ("spec_path",)
    search_fields = ("spec_path", "term_text", "notes", "term__title")
    autocomplete_fields = ("term",)


@admin.register(models.GlossarySourceLink)
class GlossarySourceLinkAdmin(admin.ModelAdmin):
    list_display = ("term", "label", "target", "kind", "order")
    list_filter = ("kind",)
    search_fields = ("term__title", "label", "target", "kind")
    autocomplete_fields = ("term",)


@admin.register(models.GlossaryDocument)
class GlossaryDocumentAdmin(admin.ModelAdmin):
    list_display = ("key", "title", "order", "include_heading")
    list_filter = ("include_heading",)
    search_fields = ("key", "title", "body")
