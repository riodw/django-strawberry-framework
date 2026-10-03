"""Django app configuration that registers kanban consistency signals at startup."""

from importlib import import_module

from django.apps import AppConfig
from typing_extensions import override


class KanbanConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # Keep the app import path explicit so the example never relies on
    # adding apps/ itself to sys.path.
    name = "apps.kanban"
    verbose_name = "Kanban"

    @override
    def ready(self) -> None:
        # Importing the signals module connects its receivers.
        import_module(f"{self.name}.signals")
