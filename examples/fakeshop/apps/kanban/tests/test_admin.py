"""Admin registration smoke tests for the kanban app.

The kanban admin is the app's browsable surface (a stepping stone to the static
dashboard); these assert the registrations and the Card changelist shape exist,
mirroring how the products app carries its own admin coverage.
"""

from django.contrib import admin

from apps.kanban import models


def test_kanban_models_registered_in_admin():
    for model in (
        models.Card,
        models.CardItem,
        models.ParityClaim,
        models.Label,
        models.TargetVersion,
        models.SpecDoc,
        models.UUIDModel,
        models.Status,
        models.Milestone,
        models.Section,
    ):
        assert admin.site.is_registered(model)


def test_card_admin_exposes_list_display_and_inlines():
    card_admin = admin.site.get_model_admin(models.Card)
    assert {"number", "title", "status"} <= set(card_admin.list_display)
    assert len(card_admin.inlines) == 2  # CardItemInline + ParityClaimInline
