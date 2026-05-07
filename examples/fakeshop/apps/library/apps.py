from django.apps import AppConfig


class LibraryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # Keep the app import path explicit so the example never relies on
    # adding apps/ itself to sys.path.
    name = "apps.library"
