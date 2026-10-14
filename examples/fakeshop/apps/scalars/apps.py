"""Django app configuration for the scalar acceptance app."""

from django.apps import AppConfig


class ScalarsConfig(AppConfig):
    """Registers the scalars app under the ``apps.scalars`` import path."""

    default_auto_field = "django.db.models.BigAutoField"
    # Keep the app import path explicit so the example never relies on
    # adding apps/ itself to sys.path.
    name = "apps.scalars"
    verbose_name = "Scalars"
