from django.apps import AppConfig


class KanbanConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # Keep the app import path explicit so the example never relies on
    # adding apps/ itself to sys.path.
    name = "apps.kanban"
    verbose_name = "Kanban"
