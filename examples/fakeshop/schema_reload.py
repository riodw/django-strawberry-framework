"""Shared complete-reload helper for fakeshop tests that rebuild ``config.schema``.

``config.schema`` aggregates EVERY app's ``Query`` / ``Mutation`` (glossary,
kanban, library, products, scalars). Package tests under ``../../tests/`` clear
the global ``DjangoType`` registry for isolation, so rebuilding ``config.schema``
after a clear requires re-registering ALL contributing apps - not just the one a
given test file targets. ``importlib.reload(config.schema)`` does NOT re-execute
the already-cached ``apps.<app>.schema`` modules, so reloading only one app's
schema leaves the other apps' types unregistered. Two failure modes follow from
a partial reload, depending on incoming dirty state:

* a still-referenced lazy input (e.g. ``CategoryFilterInputType``) raises a
  ``LazyType`` ``KeyError`` at the combined build whenever an earlier package
  test imported but never finalized that app's schema; and
* a duplicate ``<Model>Input`` / enum class object survives in ``sys.modules``
  (e.g. a re-imported ``apps.library.schema`` left by a sibling test that
  ``sys.modules.pop``-ed it without restoring it), so the aggregate build raises
  ``DuplicatedTypeName`` (e.g. ``BookInputCirculationStatusEnum``).

:func:`reload_all_project_schemas` rebuilds the FULL project schema by reloading
every contributing app in a dependency-safe order, so the rebuild is complete and
order-independent regardless of the incoming registry / ``sys.modules`` state.
Every fakeshop suite that rebuilds the aggregate schema delegates here - the
``test_query`` acceptance suites and the in-process ``apps.products`` schema
tests - so the reload discipline is single-sited.

``pythonpath = examples/fakeshop`` (``pytest.ini``) makes this module importable
as ``schema_reload`` from any conftest in the project.
"""

from __future__ import annotations

import importlib
import sys

# Dependency-safe reload order: glossary precedes kanban because
# ``kanban.schema``'s ``CardGlossaryTermType.term`` is a FK to
# ``glossary.GlossaryTerm`` and finalize rejects the kanban registration unless
# ``GlossaryTermType`` is already registered; the remaining apps are independent.
# ``apps.accounts.schema`` (spec-040) is independent - it references only
# ``auth.User`` - and MUST be listed here so a post-``registry.clear()`` rebuild
# re-registers ``UserType`` and re-binds the full auth surface (``login`` /
# ``logout`` / ``register`` / ``me``);
# without it the combined build raises a ``LazyType`` ``KeyError`` on the auth
# payload / ``UserType`` lazy refs or silently drops the auth surface (this
# module's own documented failure mode).
# ``config.schema`` (the aggregate) is reloaded after all apps, then ``config.urls``.
_PROJECT_APP_SCHEMA_MODULES = (
    "apps.glossary.schema",
    "apps.kanban.schema",
    "apps.accounts.schema",
    "apps.library.schema",
    "apps.products.schema",
    "apps.scalars.schema",
)


def _reload_or_import(module_name: str) -> None:
    """Reload ``module_name`` if already imported, else import it fresh."""
    module = sys.modules.get(module_name)
    if module is None:
        importlib.import_module(module_name)
    else:
        importlib.reload(module)


def reload_all_project_schemas() -> None:
    """Clear the registry and rebuild the FULL project schema (every app + config).

    Re-registers every contributing app schema (dependency-safe order) before
    reloading ``config.schema`` + ``config.urls``, so the combined schema build
    can resolve every app's lazy input refs after a package-test
    ``registry.clear()`` and cannot collide on a duplicate type-name left behind
    by a sibling test that evicted a schema module from ``sys.modules`` without
    restoring it. The per-suite fixtures wrap this callable rather than importing
    it directly into the test bodies, so there is no ``import conftest`` boundary
    in the test modules.
    """
    from django.urls import clear_url_caches

    from django_strawberry_framework.registry import registry

    registry.clear()
    for module_name in _PROJECT_APP_SCHEMA_MODULES:
        _reload_or_import(module_name)
    _reload_or_import("config.schema")
    urls = sys.modules.get("config.urls")
    if urls is not None:
        importlib.reload(urls)
        clear_url_caches()
