"""Admin registration smoke tests for the kanban app.

The kanban admin is the app's browsable surface (a stepping stone to the static
dashboard). These assertions are derived from the app's models and the admin
config rather than hardcoded lists/counts, so they survive new models and new
inlines without edits.
"""

from django.apps import apps
from django.contrib import admin

from apps.kanban import models


def test_every_kanban_model_is_registered_in_admin():
    """The app's policy is "register everything"; assert it dynamically."""
    for model in apps.get_app_config("kanban").get_models():
        assert admin.site.is_registered(model), f"{model.__name__} is not registered in admin"


def test_card_admin_list_display_covers_core_columns():
    card_admin = admin.site.get_model_admin(models.Card)
    assert {"number", "title", "status"} <= set(card_admin.list_display)


def test_card_admin_inlines_all_target_card_children():
    """Every Card inline must edit a model related back to Card — no fixed count."""
    card_admin = admin.site.get_model_admin(models.Card)
    assert card_admin.inlines, "Card admin should expose at least one inline"
    for inline in card_admin.inlines:
        relates_to_card = any(
            field.is_relation and field.related_model is models.Card
            for field in inline.model._meta.get_fields()
        )
        assert relates_to_card, f"{inline.model.__name__} inline does not relate to Card"
