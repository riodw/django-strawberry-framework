"""The suite-wide app-registry restore keeps a module-scope model registered.

``tests/conftest.py::_restore_app_registry`` hands every test a ``django.apps``
registry holding exactly the models it found. A model declared inside a test is
the test's to discard; a model declared at module scope of a module first
imported inside a test body stays bound to that module in ``sys.modules``, so
unregistering it would leave every later test holding a class Django no longer
knows, its reverse relations gone (``FieldDoesNotExist`` on the next reverse
read). ``tests/conftest.py::_restore_app_registry_to`` keeps such a model
registered and returns it so the fixture fails the importing test.

Each row registers a probe model with a reverse relation onto ``Category`` and
drives the restore helper directly; a failing teardown of the autouse fixture
itself is not observable from inside the test it tears down. No live request
reaches the test harness, so there is no ``examples/fakeshop/test_query/``
sibling.
"""

import sys
import types
from collections.abc import Iterator

import pytest
from apps.products.models import Category
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models

from tests.conftest import _restore_app_registry_to

_PROBE_MODULE = "tests._app_registry_restore_probe"


def _declare_probe(module_name: str) -> type[models.Model]:
    """Declare a ``products`` model with a reverse relation onto ``Category``."""
    meta = type("Meta", (), {"app_label": "products", "managed": False})
    return type(
        "RegistryRestoreProbe",
        (models.Model,),
        {
            "__module__": module_name,
            "category": models.ForeignKey(
                Category,
                on_delete=models.CASCADE,
                related_name="registry_restore_probes",
            ),
            "Meta": meta,
        },
    )


@pytest.fixture
def probe_cleanup() -> Iterator[None]:
    """Drop the probe module and any probe registration the row left behind."""
    yield
    sys.modules.pop(_PROBE_MODULE, None)
    apps.all_models["products"].pop("registryrestoreprobe", None)
    apps.clear_cache()


def test_restore_keeps_a_model_bound_at_module_scope(probe_cleanup: None) -> None:
    """A model its still-imported module binds stays registered with its reverse relation."""
    snapshot = {label: dict(registered) for label, registered in apps.all_models.items()}
    module = types.ModuleType(_PROBE_MODULE)
    sys.modules[_PROBE_MODULE] = module
    probe = _declare_probe(_PROBE_MODULE)
    module.__dict__["RegistryRestoreProbe"] = probe

    kept = _restore_app_registry_to(snapshot)

    assert kept == [probe]
    assert apps.get_model("products", "RegistryRestoreProbe") is probe
    reverse = Category._meta.get_field("registry_restore_probes")
    assert reverse.related_model is probe


def test_restore_unregisters_a_model_no_module_binds(probe_cleanup: None) -> None:
    """A model only the test holds is unregistered and its reverse relation expires."""
    snapshot = {label: dict(registered) for label, registered in apps.all_models.items()}
    sys.modules[_PROBE_MODULE] = types.ModuleType(_PROBE_MODULE)
    _declare_probe(_PROBE_MODULE)

    kept = _restore_app_registry_to(snapshot)

    assert kept == []
    assert "registryrestoreprobe" not in apps.all_models["products"]
    with pytest.raises(FieldDoesNotExist):
        Category._meta.get_field("registry_restore_probes")
