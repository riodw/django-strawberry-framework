"""Tests for ``django_strawberry_framework.apps`` — Django AppConfig."""

import django.apps

from django_strawberry_framework.apps import DjangoStrawberryFrameworkConfig


def test_djangostrawberryframeworkconfig_importable_from_apps_module():
    # The top-level import is the load-bearing assertion; if it fails,
    # pytest collection fails before this body runs.
    assert DjangoStrawberryFrameworkConfig is not None


def test_djangostrawberryframeworkconfig_is_appconfig_subclass():
    assert issubclass(DjangoStrawberryFrameworkConfig, django.apps.AppConfig)


def test_djangostrawberryframeworkconfig_pins_name_and_verbose_name():
    assert DjangoStrawberryFrameworkConfig.name == "django_strawberry_framework"
    assert DjangoStrawberryFrameworkConfig.verbose_name == "Django Strawberry Framework"


def test_djangostrawberryframeworkconfig_resolves_through_django_app_registry():
    config = django.apps.apps.get_app_config("django_strawberry_framework")
    assert isinstance(config, DjangoStrawberryFrameworkConfig)


def test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes():
    # ``ready`` IS allowed (and present) — the package ships a
    # ``ready()`` body to apply the Django Trac #37064 patch via
    # ``django_strawberry_framework._django_patches.apply``. The
    # spec-017 "no ready() body in 0.0.7" stance is deliberately
    # superseded by the package's adoption of the Trac #37064 fix.
    # See ``django_strawberry_framework/apps.py`` ``ready()`` docstring
    # and ``django_strawberry_framework/_django_patches.py``.
    forbidden = {
        "label": "Decision 2 (default last-segment label is already unique)",
        "default_auto_field": "Decision 5 (package ships zero Django models)",
        "default": "Decision 8 (no `default` attribute at any value, rev4 L4)",
    }
    for key, why in forbidden.items():
        assert key not in DjangoStrawberryFrameworkConfig.__dict__, (
            f"{key!r} is forbidden on DjangoStrawberryFrameworkConfig: {why}"
        )


def test_djangostrawberryframeworkconfig_defines_ready_for_django_patches():
    """The package's ``AppConfig.ready()`` applies the Trac #37064
    patch. Pinned so a future refactor that removes the ``ready()``
    body (and thereby silently breaks the patch) fails loudly.
    """
    assert "ready" in DjangoStrawberryFrameworkConfig.__dict__
    assert callable(DjangoStrawberryFrameworkConfig.__dict__["ready"])
