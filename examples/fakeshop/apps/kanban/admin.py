"""Admin registrations so the board is browsable at ``/admin``.

A stepping-stone toward the phase-3 static dashboard: the same data the GraphQL
surface serves is also navigable through Django admin.
"""

from django.contrib import admin

from apps.kanban import models


class _LookupAdmin(admin.ModelAdmin):
    list_display = ("key", "label", "order")
    search_fields = ("key", "label")
    ordering = ("order",)


for _model in (
    models.Milestone,
    models.Status,
    models.Priority,
    models.Severity,
    models.RelativeSize,
    models.PlanningState,
    models.Upstream,
    models.ParityLevel,
    models.Section,
    models.CardReferenceKind,
    models.CardReferenceSource,
    models.BoardDocKind,
):
    admin.site.register(_model, _LookupAdmin)


@admin.register(models.TargetVersion)
class TargetVersionAdmin(admin.ModelAdmin):
    list_display = ("number", "milestone")
    list_filter = ("milestone",)
    search_fields = ("number",)


@admin.register(models.SpecDoc)
class SpecDocAdmin(admin.ModelAdmin):
    list_display = ("name", "card", "url")
    search_fields = ("name", "url", "card__title")
    autocomplete_fields = ("card",)


class CardItemInline(admin.TabularInline):
    model = models.CardItem
    extra = 0
    show_change_link = True


class ParityClaimInline(admin.TabularInline):
    model = models.ParityClaim
    extra = 0


class CardReferenceInline(admin.TabularInline):
    model = models.CardReference
    fk_name = "source_card"
    extra = 0
    show_change_link = True
    autocomplete_fields = ("target_card", "kind", "source")


@admin.register(models.Card)
class CardAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "title",
        "status",
        "milestone",
        "target_version",
        "priority",
        "relative_size",
        "planning_state",
    )
    list_filter = (
        "status",
        "milestone",
        "priority",
        "relative_size",
        "planning_state",
    )
    search_fields = ("title",)
    autocomplete_fields = (
        "status",
        "milestone",
        "target_version",
        "priority",
        "severity",
    )
    filter_horizontal = ("dependencies", "labels")
    inlines = [CardItemInline, ParityClaimInline, CardReferenceInline]


@admin.register(models.CardReference)
class CardReferenceAdmin(admin.ModelAdmin):
    list_display = (
        "source_card",
        "target_card",
        "kind",
        "source",
        "order",
    )
    list_filter = ("kind", "source")
    search_fields = ("source_card__title", "target_card__title", "raw_text")
    autocomplete_fields = (
        "source_card",
        "target_card",
        "kind",
        "source",
    )


@admin.register(models.CardItem)
class CardItemAdmin(admin.ModelAdmin):
    list_display = (
        "card",
        "section",
        "order",
        "is_complete",
        "text",
    )
    list_filter = ("section", "is_complete")
    search_fields = ("text",)


class BoardDocCardReferenceInline(admin.TabularInline):
    model = models.BoardDocCardReference
    extra = 0
    show_change_link = True
    autocomplete_fields = ("card",)


@admin.register(models.BoardDoc)
class BoardDocAdmin(admin.ModelAdmin):
    list_display = (
        "namespace",
        "key",
        "kind",
        "title",
        "order",
        "include_heading",
    )
    list_filter = ("namespace", "kind", "include_heading")
    search_fields = ("key", "title", "body")
    autocomplete_fields = ("kind",)
    inlines = [BoardDocCardReferenceInline]


@admin.register(models.BoardDocCardReference)
class BoardDocCardReferenceAdmin(admin.ModelAdmin):
    list_display = (
        "doc",
        "card",
        "order",
        "raw_text",
    )
    list_filter = ("doc",)
    search_fields = (
        "doc__key",
        "doc__title",
        "card__title",
        "raw_text",
    )
    autocomplete_fields = ("doc", "card")


@admin.register(models.ParityClaim)
class ParityClaimAdmin(admin.ModelAdmin):
    list_display = ("card", "upstream", "level")
    list_filter = ("upstream", "level")


@admin.register(models.Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("key", "color")
    search_fields = ("key",)


@admin.register(models.UUIDModel)
class UUIDModelAdmin(admin.ModelAdmin):
    list_display = ("id",)
