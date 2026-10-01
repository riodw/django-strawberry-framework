"""Django app configuration that registers kanban consistency signals at startup."""

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
        # basedpyright: imported for its side effect: importing the module connects its receivers
        from . import signals  # noqa: F401  # pyright: ignore[reportUnusedImport]
