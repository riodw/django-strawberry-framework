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
order-independent. A module-scoped fixture applies that discipline once per worker
receiving tests from a module. A function-scoped guard then rebuilds only the cheap
aggregate schema/URL shell for every test and fingerprints the complete registration
state. If a test changes any app registration or contributing module, teardown runs
the full rebuild under ambient settings, including after an assertion failure.
"""

from __future__ import annotations

import sys

import pytest
from schema_reload import (
    _PROJECT_APP_SCHEMA_MODULES,
    reload_all_project_schemas,
    reload_project_schema_shell,
)


def _registry_registration_identity() -> tuple:
    """Fingerprint every registration map plus contributing module identities."""
    from django_strawberry_framework.registry import registry

    return (
        registry._finalized,
        tuple(
            sorted(
                (id(model), tuple(id(type_cls) for type_cls in type_classes))
                for model, type_classes in registry._types.items()
            ),
        ),
        tuple(
            sorted((id(model), id(type_cls)) for model, type_cls in registry._primaries.items()),
        ),
        tuple(sorted((id(type_cls), id(model)) for type_cls, model in registry._models.items())),
        tuple(
            sorted(
                (id(model), field_name, id(enum_cls))
                for (model, field_name), enum_cls in registry._enums.items()
            ),
        ),
        tuple(
            sorted(
                (id(type_cls), id(definition))
                for type_cls, definition in registry._definitions.items()
            ),
        ),
        tuple(id(pending) for pending in registry._pending),
        tuple(id(sys.modules.get(module_name)) for module_name in _PROJECT_APP_SCHEMA_MODULES),
    )


@pytest.fixture(scope="module")
def reload_all_project_app_schemas():
    """Return the :func:`schema_reload.reload_all_project_schemas` callable for an autouse fixture."""
    return reload_all_project_schemas


@pytest.fixture(scope="module", autouse=True)
def _reload_project_schema_for_acceptance_tests(reload_all_project_app_schemas):
    """Rebuild the full project schema once per module on every assigned worker."""
    reload_all_project_app_schemas()


@pytest.fixture(autouse=True)
def _isolate_project_schema_for_acceptance_test(
    _reload_project_schema_for_acceptance_tests,
    reload_all_project_app_schemas,
):
    """Give each test a fresh shell and fully restore any registration mutation."""
    registration_identity = _registry_registration_identity()
    reload_project_schema_shell()
    if _registry_registration_identity() != registration_identity:
        raise AssertionError("Reloading the project schema shell mutated app registrations")
    try:
        yield
    finally:
        if _registry_registration_identity() != registration_identity:
            reload_all_project_app_schemas()


@pytest.fixture
def project_schema_override(reload_all_project_app_schemas):
    """Rebuild under temporary settings; the autouse state guard restores afterward."""
    return reload_all_project_app_schemas
