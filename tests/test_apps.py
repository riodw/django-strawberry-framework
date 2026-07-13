"""AppConfig tests for package registration and upstream patch dispatch."""

import django.apps
from cross_web import DjangoHTTPRequestAdapter
from django.test.testcases import SimpleTestCase
from strawberry.http.base import BaseView

from django_strawberry_framework import _cross_web_patches, _django_patches, _strawberry_patches
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
    # ``ready`` IS allowed (and present) - the package ships a
    # ``ready()`` body that dispatches the three upstream patch
    # modules' ``apply()`` calls. The spec-017 "no ready() body in
    # 0.0.7" stance is deliberately superseded by the package's
    # adoption of the upstream patches. See
    # ``django_strawberry_framework/apps.py`` ``ready()`` docstring
    # and the three ``_*_patches`` module docstrings.
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
    """The package's ``AppConfig.ready()`` applies the upstream
    patches. Pinned so a future refactor that removes the ``ready()``
    body outright fails loudly; the dispatch behavior itself is pinned
    by ``test_ready_dispatches_all_three_patch_appliers_and_refires_safely``.
    """
    assert "ready" in DjangoStrawberryFrameworkConfig.__dict__
    assert callable(DjangoStrawberryFrameworkConfig.__dict__["ready"])


def _all_patches_installed():
    return (
        _django_patches._patch_is_installed(),
        _strawberry_patches._patch_is_installed(),
        _cross_web_patches._patch_is_installed(),
    )


def test_ready_dispatches_all_three_patch_appliers_and_refires_safely():
    """``ready()`` itself installs all three upstream patches; a re-fire is safe.

    The patch-module suites each pin "installed at collection via
    ``ready()``", but those assertions are masked by the direct
    ``apply()`` calls ``test_apply_is_idempotent`` makes earlier in file
    order on the same worker - a ``ready()`` that lost a dispatch line
    would still pass them. This test owns the dispatch contract
    deterministically: it reverts all three patches to the captured
    upstream originals, drives ``ready()`` through the registered
    AppConfig, and asserts every patch is installed. A second
    ``ready()`` pins dispatch-layer idempotence (some Django test
    runners fire it more than once).
    """
    saved_django = SimpleTestCase.__dict__["_remove_databases_failures"]
    saved_parse_json = BaseView.__dict__["parse_json"]
    saved_parse_query_params = BaseView.__dict__["parse_query_params"]
    saved_body = DjangoHTTPRequestAdapter.__dict__["body"]
    try:
        SimpleTestCase._remove_databases_failures = (
            _django_patches._original_remove_databases_failures
        )
        BaseView.parse_json = _strawberry_patches._original_parse_json
        BaseView.parse_query_params = _strawberry_patches._original_parse_query_params
        DjangoHTTPRequestAdapter.body = property(_cross_web_patches._original_body_fget)
        assert _all_patches_installed() == (False, False, False)

        config = django.apps.apps.get_app_config("django_strawberry_framework")
        config.ready()
        assert _all_patches_installed() == (True, True, True)

        config.ready()
        assert _all_patches_installed() == (True, True, True)
    finally:
        SimpleTestCase._remove_databases_failures = saved_django
        BaseView.parse_json = saved_parse_json
        BaseView.parse_query_params = saved_parse_query_params
        DjangoHTTPRequestAdapter.body = saved_body
