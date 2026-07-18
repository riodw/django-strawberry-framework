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
    models.RelativeSize,
    models.Upstream,
    models.ParityLevel,
    models.Section,
    models.CardReferenceKind,
    models.BoardDocKind,
    models.AttemptOutcome,
    models.VerificationKind,
):
    admin.site.register(_model, _LookupAdmin)


@admin.register(models.Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = (
        "key",
        "label",
        "kind",
        "order",
    )
    list_filter = ("kind",)
    search_fields = ("key", "label")
    ordering = ("order",)


@admin.register(models.CardTransition)
class CardTransitionAdmin(admin.ModelAdmin):
    list_display = (
        "card",
        "from_status",
        "to_status",
        "actor",
        "occurred_at",
    )
    list_filter = ("to_status", "from_status", "actor")
    search_fields = ("card__title", "note")
    autocomplete_fields = ("card", "actor")


@admin.register(models.WorkAttempt)
class WorkAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "card",
        "actor",
        "outcome",
        "started_at",
        "ended_at",
    )
    list_filter = ("outcome", "actor")
    search_fields = ("card__title", "summary", "evidence")
    autocomplete_fields = ("card", "actor")


@admin.register(models.Decision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = (
        "question",
        "choice",
        "card",
        "actor",
        "decided_at",
    )
    list_filter = ("actor",)
    search_fields = (
        "question",
        "choice",
        "rationale",
        "card__title",
    )
    autocomplete_fields = ("card", "actor", "supersedes")


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


@admin.register(models.TrackedPath)
class TrackedPathAdmin(admin.ModelAdmin):
    list_display = ("path", "state", "is_directory")
    list_filter = ("state", "is_directory")
    search_fields = ("path",)


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
    autocomplete_fields = ("target_card", "kind")


class CardGlossaryTermInline(admin.TabularInline):
    model = models.CardGlossaryTerm
    extra = 0
    show_change_link = True
    autocomplete_fields = ("term",)


class CardPathLinkInline(admin.TabularInline):
    model = models.CardPathLink
    extra = 0
    show_change_link = True
    autocomplete_fields = ("path",)


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
    )
    list_filter = (
        "status",
        "target_version__milestone",
        "priority",
        "relative_size",
    )
    search_fields = ("title",)
    autocomplete_fields = ("status", "target_version", "priority")
    filter_horizontal = ("labels",)
    inlines = [
        CardItemInline,
        ParityClaimInline,
        CardReferenceInline,
        CardGlossaryTermInline,
        CardPathLinkInline,
    ]

    @admin.display(description="milestone")
    def milestone(self, obj: models.Card) -> str:
        """Show the card's derived milestone (via target version) in the list."""
        return obj.milestone.label


@admin.register(models.CardReference)
class CardReferenceAdmin(admin.ModelAdmin):
    list_display = (
        "source_card",
        "target_card",
        "kind",
        "order",
    )
    list_filter = ("kind",)
    search_fields = ("source_card__title", "target_card__title", "raw_text")
    autocomplete_fields = ("source_card", "target_card", "kind")


@admin.register(models.CardGlossaryTerm)
class CardGlossaryTermAdmin(admin.ModelAdmin):
    list_display = (
        "card",
        "term",
        "order",
        "raw_text",
    )
    search_fields = ("card__title", "term__title", "raw_text")
    autocomplete_fields = ("card", "term")


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
