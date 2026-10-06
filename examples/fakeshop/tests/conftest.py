"""Shared fixtures for the fakeshop project/config-level tests.

Modules here that import the aggregate ``config.schema`` (directly, through
``config.urls``, or through a management command's schema selector) opt in to
``reload_project_schemas`` with ``pytestmark``. Package tests clear the global
``DjangoType`` registry while app schema modules stay cached in ``sys.modules``,
so the first aggregate build after such a clear finds only the apps it imports
fresh and fails to finalize. The fixture delegates to the shared
``schema_reload.reload_all_project_schemas`` (``examples/fakeshop/schema_reload.py``)
so the full project schema is rebuilt once per module, independent of test order.
"""

from __future__ import annotations

import pytest
from schema_reload import reload_all_project_schemas


@pytest.fixture(scope="module")
def reload_project_schemas() -> None:
    """Rebuild the full project schema once per module on every assigned worker."""
    reload_all_project_schemas()
