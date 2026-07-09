"""The DRF soft-dependency import guard (spec-039 Decision 12, Slice 2).

Covers the ``rest_framework/__init__.py::require_drf()`` guard + the root
``django_strawberry_framework.__getattr__`` plumbing:

- ``import django_strawberry_framework`` succeeds without DRF;
- the root ``SerializerMutation`` lookup, ``import ...rest_framework``, and
  ``import ...rest_framework.sets`` ALL raise ``ImportError`` with the install hint
  when DRF is absent;
- ``from django_strawberry_framework import *`` stays DRF-free + binds no
  ``SerializerMutation`` (F1);
- the root ``__getattr__`` does NOT memoize a successful ``SerializerMutation``
  access (the absent-DRF test can re-hit the guard on the next access).

DRF is INSTALLED in the test env, so absence is SIMULATED via the shared
``sys.modules["rest_framework"] = None`` sentinel (``tests/_soft_dependency.py``), which
raises ``ImportError`` for ``require_drf()``'s import. The eviction discipline is strict -
both ``rest_framework*`` AND ``django_strawberry_framework.rest_framework*`` are evicted
and restored (the two-sided restore) so this test does not poison sibling tests that DO
use DRF (the spec-037 ``pillow``-absent-path precedent) - and the fixture defensively
clears the root ``SerializerMutation`` binding state.
"""

from __future__ import annotations

import contextlib
import importlib

import pytest

import django_strawberry_framework
from tests._soft_dependency import simulated_absence

# The verified DRF floor (Slice 0); the install hint must name it (place 2 of the
# three-places-that-must-agree). The test matches this substring.
_HINT_SUBSTRING = "djangorestframework>=3.17.0"


@pytest.fixture
def _simulate_drf_absent():
    """Simulate DRF absence via the shared ``sys.modules[...] = None`` sentinel; restore on teardown.

    Evicts the framework's own ``rest_framework`` subpackage too so the module-body
    ``require_drf()`` guard re-executes on the next import (the package/sets import tests
    depend on it), and defensively clears any bound root ``SerializerMutation`` attribute
    (the non-memoizing ``__getattr__`` never binds one, but the delete keeps the absent
    path clean even if a prior test mutated globals). The two-sided restore belongs to the
    shared helper (``tests/_soft_dependency.py::evicted_modules``).
    """
    with simulated_absence(
        "rest_framework",
        "rest_framework",
        "django_strawberry_framework.rest_framework",
        parent=django_strawberry_framework,
        attr="rest_framework",
    ):
        with contextlib.suppress(AttributeError):
            delattr(django_strawberry_framework, "SerializerMutation")
        yield


def test_root_package_imports_without_drf(_simulate_drf_absent):
    """``import django_strawberry_framework`` still succeeds under simulated DRF absence."""
    # The root module is already imported; re-importing must not trip the guard
    # (the root never eagerly imports rest_framework/).
    mod = importlib.import_module("django_strawberry_framework")
    assert mod is django_strawberry_framework


def test_root_serializer_mutation_lookup_raises_install_hint(_simulate_drf_absent):
    """The root ``SerializerMutation`` lookup raises ``ImportError`` with the install hint."""
    with pytest.raises(ImportError, match=_HINT_SUBSTRING):
        _ = django_strawberry_framework.SerializerMutation


def test_rest_framework_package_import_raises_install_hint(_simulate_drf_absent):
    """``import django_strawberry_framework.rest_framework`` raises the same guarded hint."""
    with pytest.raises(ImportError, match=_HINT_SUBSTRING):
        importlib.import_module("django_strawberry_framework.rest_framework")


def test_rest_framework_sets_import_raises_install_hint(_simulate_drf_absent):
    """``import django_strawberry_framework.rest_framework.sets`` raises the same guarded hint."""
    with pytest.raises(ImportError, match=_HINT_SUBSTRING):
        importlib.import_module("django_strawberry_framework.rest_framework.sets")


def test_star_import_stays_drf_free_and_binds_no_serializer_mutation(_simulate_drf_absent):
    """``from django_strawberry_framework import *`` succeeds + binds no ``SerializerMutation`` (F1)."""
    namespace: dict[str, object] = {}
    exec("from django_strawberry_framework import *", namespace)
    # The star import consulted ``__all__`` (DRF-free) and never tripped the guard.
    assert "SerializerMutation" not in namespace
    assert "DjangoMutation" in namespace  # a normal eager export still binds


def test_other_attribute_miss_raises_attribute_error():
    """A non-``SerializerMutation`` attribute miss raises the normal ``AttributeError`` (not ImportError)."""
    with pytest.raises(AttributeError, match="DefinitelyNotAName"):
        _ = django_strawberry_framework.DefinitelyNotAName


def test_successful_lookup_does_not_memoize():
    """A SUCCESSFUL ``SerializerMutation`` access (DRF present) does not bind into root globals.

    Non-memoization (Decision 12): the resolved class is NOT written into the root
    module ``globals()``, so each access re-fires the guard (the absent-DRF test can
    evict + re-hit it). Run WITHOUT the absence fixture (DRF present), so the access
    succeeds; then assert the name is not in ``vars(...)``.
    """
    with contextlib.suppress(AttributeError):
        delattr(django_strawberry_framework, "SerializerMutation")
    cls = django_strawberry_framework.SerializerMutation
    assert cls is not None
    assert "SerializerMutation" not in vars(django_strawberry_framework)
