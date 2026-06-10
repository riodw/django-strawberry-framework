"""Django AppConfig - registers django-strawberry-framework with Django's app loader."""

from django.apps import AppConfig


class DjangoStrawberryFrameworkConfig(AppConfig):
    """Register django-strawberry-framework with Django's app loader."""

    name = "django_strawberry_framework"
    verbose_name = "Django Strawberry Framework"

    def ready(self) -> None:
        """Apply the package's Django defensive patches at app-load time.

        Currently applies the Trac #37064 hardening for
        ``SimpleTestCase._remove_databases_failures``, which every
        ``SimpleTestCase`` subclass (including ``TransactionTestCase``
        and ``TestCase``) inherits. See
        :mod:`django_strawberry_framework._django_patches` for the
        list of patches and the rationale for each.

        ``ready()`` is the canonical place to perform one-time setup
        that depends on Django being fully configured. Consumers get
        the patches automatically by having
        ``"django_strawberry_framework"`` in ``INSTALLED_APPS`` - no
        opt-in boilerplate is required.
        """
        from django_strawberry_framework._django_patches import apply

        apply()
