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
    forbidden = {
        "ready": "Decision 4 (no AppConfig.ready() body in 0.0.7)",
        "label": "Decision 2 (default last-segment label is already unique)",
        "default_auto_field": "Decision 5 (package ships zero Django models)",
        "default": "Decision 8 (no `default` attribute at any value, rev4 L4)",
    }
    for key, why in forbidden.items():
        assert key not in DjangoStrawberryFrameworkConfig.__dict__, (
            f"{key!r} is forbidden on DjangoStrawberryFrameworkConfig: {why}"
        )
