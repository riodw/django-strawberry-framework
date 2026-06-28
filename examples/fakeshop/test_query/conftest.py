"""Shared fixtures for the fakeshop acceptance (live ``/graphql/``) suites.

The complete-reload discipline these suites depend on lives in the shared
``schema_reload`` module (``examples/fakeshop/schema_reload.py``, importable via
``pytest.ini``'s ``pythonpath = examples/fakeshop``) so it is single-sited across
every fakeshop suite that rebuilds the aggregate ``config.schema`` - both these
acceptance suites and the in-process ``apps.products`` schema tests. See that
module's docstring for why a partial reload leaves the combined build raising a
``LazyType`` ``KeyError`` or a ``DuplicatedTypeName``.

``reload_all_project_schemas`` rebuilds the full project schema by reloading every
contributing app in a dependency-safe order, so the rebuild is complete and
order-independent. EVERY acceptance suite's autouse fixture delegates to it via the
``reload_all_project_app_schemas`` fixture below - there are no per-file narrower
reloads left: the combined ``config.schema`` build needs all five apps registered
no matter which app a given file targets, so each file reconstructs the WHOLE
project rather than only its own app.
"""

from __future__ import annotations

import pytest
from schema_reload import reload_all_project_schemas


@pytest.fixture
def reload_all_project_app_schemas():
    """Return the :func:`schema_reload.reload_all_project_schemas` callable for an autouse fixture."""
    return reload_all_project_schemas
