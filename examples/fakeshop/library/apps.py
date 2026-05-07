from django.apps import AppConfig


class LibraryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # This short app label relies on the flattened example-project layout
    # and pytest.ini's `pythonpath = examples/fakeshop`; real projects
    # should use their own dotted app path.
    name = "library"
