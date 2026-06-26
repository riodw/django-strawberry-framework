"""Shared fixtures for the fakeshop acceptance (live ``/graphql/``) suites.

``config.schema`` aggregates EVERY app's ``Query`` / ``Mutation`` (glossary,
kanban, library, products, scalars). Package tests under ``../../../tests/`` clear
the global ``DjangoType`` registry for isolation, so rebuilding ``config.schema``
after a clear requires re-registering ALL contributing apps - not just the one a
given acceptance file targets. ``importlib.reload(config.schema)`` does NOT
re-execute the already-cached ``apps.<app>.schema`` modules, so reloading only the
file's own app leaves the other apps' types unregistered and makes the combined
``config.schema`` build raise a ``LazyType`` ``KeyError`` for a still-referenced
input (e.g. ``CategoryFilterInputType`` from products) whenever an earlier package
test imported but never finalized that app's schema.

``reload_all_project_app_schemas`` rebuilds the full project schema by reloading
every contributing app in a dependency-safe order, so the rebuild is complete and
order-independent. The per-file fixtures that only need their own app keep their
narrower reloads; the suites whose fixture must reconstruct the WHOLE combined
schema (kanban / glossary, which sit downstream of the products/library/scalars
types in ``config.schema``) use this helper.
"""

from __future__ import annotations

import importlib
import sys

import pytest
from django.urls import clear_url_caches

# Dependency-safe reload order: glossary precedes kanban because
# ``kanban.schema``'s ``CardGlossaryTermType.term`` is a FK to
# ``glossary.GlossaryTerm`` and finalize rejects the kanban registration unless
# ``GlossaryTermType`` is already registered; the remaining apps are independent.
# ``config.schema`` (the aggregate) is reloaded after all apps, then ``config.urls``.
_PROJECT_APP_SCHEMA_MODULES = (
    "apps.glossary.schema",
    "apps.kanban.schema",
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


@pytest.fixture
def reload_all_project_app_schemas():
    """Return a callable that clears the registry and rebuilds the FULL project schema.

    Re-registers every contributing app schema (dependency-safe order) before
    reloading ``config.schema`` + ``config.urls``, so the combined schema build can
    resolve every app's lazy input refs after a package-test ``registry.clear()``.
    """

    def _reload() -> None:
        from django_strawberry_framework.registry import registry

        registry.clear()
        for module_name in _PROJECT_APP_SCHEMA_MODULES:
            _reload_or_import(module_name)
        _reload_or_import("config.schema")
        urls = sys.modules.get("config.urls")
        if urls is not None:
            importlib.reload(urls)
            clear_url_caches()

    return _reload
