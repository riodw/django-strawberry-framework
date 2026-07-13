"""Django ``AppConfig`` - registers the package and applies its upstream patches at app load."""

from django.apps import AppConfig


class DjangoStrawberryFrameworkConfig(AppConfig):
    """Register django-strawberry-framework with Django's app loader."""

    name = "django_strawberry_framework"
    verbose_name = "Django Strawberry Framework"

    def ready(self) -> None:
        """Apply the package's defensive upstream patches at app-load time.

        Three patch modules, one per third-party dependency:
        :mod:`django_strawberry_framework._django_patches` (Django),
        :mod:`django_strawberry_framework._strawberry_patches`
        (Strawberry), and
        :mod:`django_strawberry_framework._cross_web_patches`
        (``cross_web``). Each module's own docstring is the single
        source of truth for exactly which upstream bugs it hardens;
        this dispatcher deliberately repeats none of that inventory.

        All three are gated by the ``APPLY_UPSTREAM_PATCHES`` setting
        (default on); each ``apply()`` self-gates, so a consumer who
        sets ``DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES":
        False}`` gets none of them.

        ``ready()`` is the canonical place to perform one-time setup
        that depends on Django being fully configured. Consumers get
        the patches automatically by having
        ``"django_strawberry_framework"`` in ``INSTALLED_APPS`` - no
        opt-in boilerplate is required. Each ``apply()`` is idempotent
        and self-healing, so a repeated ``ready()`` (some Django test
        runners fire it more than once) is safe.
        """
        from django_strawberry_framework._cross_web_patches import apply as apply_cross_web
        from django_strawberry_framework._django_patches import apply as apply_django
        from django_strawberry_framework._strawberry_patches import apply as apply_strawberry

        apply_django()
        apply_strawberry()
        apply_cross_web()
