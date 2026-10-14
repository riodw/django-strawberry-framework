"""Django app configuration for the glossary data app."""

from django.apps import AppConfig


class GlossaryConfig(AppConfig):
    """Registers the glossary data app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.glossary"
    verbose_name = "Glossary"
