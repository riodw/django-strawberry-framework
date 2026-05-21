"""Tests for ``django_strawberry_framework/apps.py`` — Django AppConfig.

Staged for ``WIP-ALPHA-017-0.0.7``; spec lives at ``docs/spec-017-apps-0_0_7.md``.

Test plan (per spec Slice 2 / Test plan section) — 5 pytest items total.

Positive tests (4):

- ``test_djangostrawberryframeworkconfig_importable_from_apps_module``
  — Pin: ``from django_strawberry_framework.apps import
  DjangoStrawberryFrameworkConfig`` resolves without ``ImportError``.
  Catches a future move to a nested ``apps/`` subpackage or to
  ``django_strawberry_framework/django/apps.py``.  Decision 1.

- ``test_djangostrawberryframeworkconfig_is_appconfig_subclass``
  — Pin: ``issubclass(DjangoStrawberryFrameworkConfig, django.apps.AppConfig)``
  is ``True``.  Catches a refactor that accidentally rebases the class onto
  a custom intermediate or onto ``django.apps.config.AppConfig`` via direct
  import.

- ``test_djangostrawberryframeworkconfig_pins_name_and_verbose_name``
  — Pin: ``DjangoStrawberryFrameworkConfig.name == "django_strawberry_framework"``
  AND ``DjangoStrawberryFrameworkConfig.verbose_name == "Django Strawberry
  Framework"``.  Catches a cosmetic edit to either string.  Decision 2.

- ``test_djangostrawberryframeworkconfig_resolves_through_django_app_registry``
  — Pin: ``django.apps.apps.get_app_config("django_strawberry_framework")``
  returns an instance of ``DjangoStrawberryFrameworkConfig`` (NOT the
  implicit fallback Django synthesized pre-Slice-1).  Load-bearing
  end-to-end assertion: without this test, the explicit AppConfig could
  silently fail to register and the implicit one could stand in unnoticed.

Negative-shape test (1):

- ``test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes``
  — Single pytest item, plain ``for``-loop, NOT ``pytest.mark.parametrize``
  per rev4 informational #2 (keeps the "5 tests" count unambiguous against
  pytest's collection output; a parametrized test would fan out to 4 items
  and yield 8 total, contradicting the spec's Implementation-plan table and
  DoD item 4).  Loops over the four forbidden behavioral keys and asserts
  each is absent from ``DjangoStrawberryFrameworkConfig.__dict__``::

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

  Checks the class body explicitly via ``__dict__`` — inherited base
  attributes from ``django.apps.AppConfig`` are NOT in the subclass's
  ``__dict__`` and are not flagged.  The implicit ``__doc__`` key
  (populated by the class docstring required by ``D101``) is intentionally
  NOT in the iteration set — documentation is not behavior, per rev3 H1 /
  rev4 L2.  If a future drive-by edit adds ``def ready(self): pass``,
  ``label = "dsf"``, ``default_auto_field = "django.db.models.BigAutoField"``,
  or ``default = True`` / ``default = False`` — each violating its
  corresponding Decision — this test fails and the edit is caught before
  merge.

No live ``/graphql/`` HTTP test is required.  The
``examples/fakeshop/test_query/test_library_api.py`` suite already exercises
the package through ``INSTALLED_APPS`` end-to-end; once Slice 1 lands, those
tests pass through the explicit AppConfig with zero modifications.

When the TODO below disappears, Slice 2 has shipped.
"""

# TODO(WIP-ALPHA-017-0.0.7 Slice 2): implement the 5 tests above per
# docs/spec-017-apps-0_0_7.md Slice 2 / Test plan.
# Definition of done: DoD item 4 in the spec.
#
# Pseudo (Slice 2 — see spec Test plan section for full contracts):
#
#     import django.apps
#
#     from django_strawberry_framework.apps import DjangoStrawberryFrameworkConfig
#
#     def test_djangostrawberryframeworkconfig_importable_from_apps_module():
#         # The import above is the assertion; if it fails, pytest collection fails.
#         assert DjangoStrawberryFrameworkConfig is not None
#
#     def test_djangostrawberryframeworkconfig_is_appconfig_subclass():
#         assert issubclass(DjangoStrawberryFrameworkConfig, django.apps.AppConfig)
#
#     def test_djangostrawberryframeworkconfig_pins_name_and_verbose_name():
#         assert DjangoStrawberryFrameworkConfig.name == "django_strawberry_framework"
#         assert DjangoStrawberryFrameworkConfig.verbose_name == "Django Strawberry Framework"
#
#     def test_djangostrawberryframeworkconfig_resolves_through_django_app_registry():
#         config = django.apps.apps.get_app_config("django_strawberry_framework")
#         assert isinstance(config, DjangoStrawberryFrameworkConfig)
#
#     def test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes():
#         forbidden = {
#             "ready": "Decision 4 (no AppConfig.ready() body in 0.0.7)",
#             "label": "Decision 2 (default last-segment label is already unique)",
#             "default_auto_field": "Decision 5 (package ships zero Django models)",
#             "default": "Decision 8 (no `default` attribute at any value, rev4 L4)",
#         }
#         for key, why in forbidden.items():
#             assert key not in DjangoStrawberryFrameworkConfig.__dict__, (
#                 f"{key!r} is forbidden on DjangoStrawberryFrameworkConfig: {why}"
#             )
