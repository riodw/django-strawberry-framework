"""AppConfig tests for package registration and upstream patch dispatch."""

import importlib

import django.apps
from cross_web import DjangoHTTPRequestAdapter
from django.test.testcases import SimpleTestCase
from strawberry.http.async_base_view import AsyncBaseHTTPView
from strawberry.http.base import BaseView
from strawberry.http.sync_base_view import SyncBaseHTTPView

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
        "default": "Decision 8 (no `default` attribute at any value)",
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


# Every upstream class attribute the three patch modules replace. A test that
# drives ``apply()`` (directly or through ``ready()``) mutates process-global
# state at each of these slots, so a test that also perturbs the patch modules
# themselves restores both halves from this one table.
_PATCHED_SLOTS = (
    (SimpleTestCase, "_remove_databases_failures"),
    (BaseView, "parse_json"),
    (BaseView, "parse_query_params"),
    (SyncBaseHTTPView, "parse_multipart"),
    (AsyncBaseHTTPView, "parse_multipart"),
    (DjangoHTTPRequestAdapter, "body"),
)


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


def test_ready_reinstalls_patches_after_their_modules_reload():
    """A reloaded applier retains its true upstream capture and re-installs cleanly.

    An interactive test session can reload a private patch module while its
    process-global method replacement remains installed. The next AppConfig
    ``ready()`` call must distinguish that prior package replacement from an
    unsupported upstream change: retain the original capture, then install the
    reloaded replacement instead of rejecting the prior replacement's source.

    Each module is reloaded TWICE. The first pass reloads a module whose
    installed replacement was built by the module's original execution; the
    second reloads one whose installed replacement is itself a product of the
    first reload, so the capture contract is pinned for repeated reloads rather
    than only for the first one.

    The reload rebinds every module global (captures, replacements, and the
    identity operands each ``_patch_is_installed`` compares against), and
    ``ready()`` then writes the post-reload replacements onto the upstream
    classes. Both halves are process-global and both are restored together:
    restoring only the class attributes would leave them pointing at
    pre-reload objects while the modules hold post-reload ones, i.e. every
    ``_patch_is_installed`` reporting a spurious ``False`` for the rest of the
    worker's run.
    """
    config = django.apps.apps.get_app_config("django_strawberry_framework")
    modules_and_originals = (
        (_django_patches, ("_original_remove_databases_failures",)),
        (
            _strawberry_patches,
            (
                "_original_parse_json",
                "_original_parse_query_params",
                "_original_sync_parse_multipart",
                "_original_async_parse_multipart",
            ),
        ),
        (_cross_web_patches, ("_original_body_fget",)),
    )
    saved_namespaces = {module: dict(module.__dict__) for module, _ in modules_and_originals}
    saved_slots = tuple(
        (owner, attribute, owner.__dict__[attribute]) for owner, attribute in _PATCHED_SLOTS
    )
    try:
        for module, original_names in modules_and_originals:
            original_captures = tuple(getattr(module, name) for name in original_names)

            for _ in range(2):
                importlib.reload(module)

                assert tuple(getattr(module, name) for name in original_names) == original_captures
                config.ready()
                assert _all_patches_installed() == (True, True, True)
    finally:
        for module, namespace in saved_namespaces.items():
            module.__dict__.clear()
            module.__dict__.update(namespace)
        for owner, attribute, descriptor in saved_slots:
            setattr(owner, attribute, descriptor)
