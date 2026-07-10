"""Shared fixtures for the in-process ``apps.products`` schema tests.

``test_schema.py`` recomposes ``config.schema`` to exercise the products app via
``schema.execute_sync``. ``config.schema`` aggregates ALL five apps, so the rebuild
must re-register every app, not just products - a products-only partial reload
leaves a sibling app's schema module re-imported-but-unfinalized in ``sys.modules``
(e.g. an ``apps.library.schema`` evicted-without-restore by a worker-sharing
``examples/fakeshop/tests/test_inspect_django_type.py`` test), so the combined build
can raise ``DuplicatedTypeName`` (``BookInputCirculationStatusEnum``).

This fixture mirrors the ``test_query`` acceptance suites: it exposes the same
``reload_all_project_app_schemas`` fixture, backed by the single-sited
``schema_reload.reload_all_project_schemas`` complete-reload helper, so the products
in-process schema tests rebuild on the SAME order-independent discipline.
"""

from __future__ import annotations

import pytest
from schema_reload import reload_all_project_schemas


@pytest.fixture(scope="module")
def reload_all_project_app_schemas():
    """Return the :func:`schema_reload.reload_all_project_schemas` callable for the schema fixture."""
    return reload_all_project_schemas
