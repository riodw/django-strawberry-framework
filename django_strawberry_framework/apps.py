"""Django AppConfig — registers django-strawberry-framework with Django's app loader.

Staged for ``WIP-ALPHA-017-0.0.7``; spec lives at ``docs/spec-017-apps-0_0_7.md``.

Slice 1 ships ``DjangoStrawberryFrameworkConfig`` so consumers can list
``"django_strawberry_framework"`` in ``INSTALLED_APPS`` and Django's check /
signal hooks resolve through the package's explicit AppConfig instead of the
implicit fallback Django synthesizes from the package name.  Until Slice 1
lands, this module is intentionally empty of behavior — Django's implicit
single-AppConfig discovery continues to synthesize the fallback from the
package directory name, matching the pre-``0.0.7`` behavior the example
project already runs under.

Pseudo (Slice 1 — see ``docs/spec-017-apps-0_0_7.md`` Slice 1, Decisions 1 / 2)::

    from django.apps import AppConfig

    class DjangoStrawberryFrameworkConfig(AppConfig):
        \"\"\"Register django-strawberry-framework with Django's app loader.\"\"\"

        name = "django_strawberry_framework"           # Decision 2
        verbose_name = "Django Strawberry Framework"   # Decision 2

Forbidden in 0.0.7 (the consolidated negative-shape test in
``tests/test_apps.py`` fails if any of these appear on the class body):

- ``ready()`` body              — Decision 4 (no preemptive side effects;
  consumer owns ``finalize_django_types`` synchronization point).
- ``label = ...``               — Decision 2 (default last-segment label is
  already unique; aliasing introduces a second lookup string).
- ``default_auto_field = ...``  — Decision 5 (package ships zero Django
  models; the attribute is meaningless here).
- ``default = ...`` (any value) — Decision 8 (rev4 L4 forbids the attribute
  outright at any value; Django 3.2+ resolves a single explicit AppConfig as
  the default without the marker).

Also forbidden:

- Re-export from ``django_strawberry_framework/__init__.py`` — Decision 3
  (Django's app loader resolves AppConfigs through the dotted module path,
  not through the package's ``__all__``).
- ``# noqa: D100`` / ``# noqa: D101`` to skip the module / class docstring
  — rev3 H1 / rev4 L3.  Both ``D100`` and ``D101`` are in
  ``pyproject.toml``'s ``[tool.ruff.lint] select`` and not in ``ignore``;
  the per-file-ignores at ``pyproject.toml:100-107`` do not exempt this
  module.  The docstrings ARE the root-cause fix per ``AGENTS.md`` line 4.

When the TODO below disappears, Slice 1 has shipped.
"""

# TODO(WIP-ALPHA-017-0.0.7 Slice 1): implement DjangoStrawberryFrameworkConfig
# per the Pseudo block above and docs/spec-017-apps-0_0_7.md Slice 1.
# Definition of done: DoD items 1 + 6 in the spec.
