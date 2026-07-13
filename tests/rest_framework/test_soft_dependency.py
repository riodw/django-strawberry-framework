"""The DRF soft-dependency import guard (spec-039 Decision 12, Slice 2).

Covers the ``rest_framework/__init__.py::require_drf()`` guard + the root
``django_strawberry_framework.__getattr__`` plumbing:

- ``import django_strawberry_framework`` succeeds without DRF;
- every lazy root serializer-export lookup, ``import ...rest_framework``, and
  ``import ...rest_framework.sets`` ALL raise ``ImportError`` with the install hint
  when DRF is absent;
- ``from django_strawberry_framework import *`` stays DRF-free and binds no
  serializer export (F1);
- the root ``__getattr__`` does NOT memoize any successful serializer export
  access (the absent-DRF test can re-hit the guard on the next access).

DRF is INSTALLED in the test env, so absence is SIMULATED via the shared
``sys.modules["rest_framework"] = None`` sentinel (``tests/_soft_dependency.py``), which
raises ``ImportError`` for ``require_drf()``'s import. The eviction discipline is strict -
both ``rest_framework*`` AND ``django_strawberry_framework.rest_framework*`` are evicted
and restored (the two-sided restore) so this test does not poison sibling tests that DO
use DRF (the spec-037 ``pillow``-absent-path precedent) - and the fixture defensively
clears the root ``SerializerMutation`` binding state. The initial root-import contract runs
in a fresh subprocess, because re-importing the already-loaded test-process module cannot
detect a newly introduced eager DRF import.
"""

from __future__ import annotations

import contextlib
import importlib
import subprocess
import sys

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


def test_fresh_root_package_import_and_star_import_succeed_without_drf():
    """A fresh process imports the root and its ``__all__`` while DRF is absent (review P2)."""
    script = """
import sys

sys.modules["rest_framework"] = None
import django_strawberry_framework as package

assert "django_strawberry_framework.rest_framework" not in sys.modules
namespace = {}
exec("from django_strawberry_framework import *", namespace)
assert not set(package._DRF_SOFT_EXPORTS) & namespace.keys()
try:
    package.SerializerMutation
except ImportError as exc:
    assert "djangorestframework>=3.17.0" in str(exc)
else:
    raise AssertionError("SerializerMutation must reach the DRF install guard")
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, (
        f"fresh DRF-absent import failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


@pytest.mark.parametrize("name", tuple(django_strawberry_framework._DRF_SOFT_EXPORTS))
def test_each_root_serializer_surface_lookup_raises_install_hint(_simulate_drf_absent, name):
    """Every root serializer export stays lazy and raises the guarded install hint."""
    with pytest.raises(ImportError, match=_HINT_SUBSTRING):
        getattr(django_strawberry_framework, name)


def test_rest_framework_package_import_raises_install_hint(_simulate_drf_absent):
    """``import django_strawberry_framework.rest_framework`` raises the same guarded hint."""
    with pytest.raises(ImportError, match=_HINT_SUBSTRING):
        importlib.import_module("django_strawberry_framework.rest_framework")


def test_rest_framework_sets_import_raises_install_hint(_simulate_drf_absent):
    """``import django_strawberry_framework.rest_framework.sets`` raises the same guarded hint."""
    with pytest.raises(ImportError, match=_HINT_SUBSTRING):
        importlib.import_module("django_strawberry_framework.rest_framework.sets")


def test_star_import_stays_drf_free_and_binds_no_serializer_surface(_simulate_drf_absent):
    """``from django_strawberry_framework import *`` succeeds and binds no DRF surface (F1)."""
    namespace: dict[str, object] = {}
    exec("from django_strawberry_framework import *", namespace)
    # The star import consulted ``__all__`` (DRF-free) and never tripped the guard.
    assert not set(django_strawberry_framework._DRF_SOFT_EXPORTS) & namespace.keys()
    assert "DjangoMutation" in namespace  # a normal eager export still binds


def test_other_attribute_miss_raises_attribute_error():
    """A non-``SerializerMutation`` attribute miss raises the normal ``AttributeError`` (not ImportError)."""
    with pytest.raises(AttributeError, match="DefinitelyNotAName"):
        _ = django_strawberry_framework.DefinitelyNotAName


@pytest.mark.parametrize("name", tuple(django_strawberry_framework._DRF_SOFT_EXPORTS))
def test_successful_lookup_does_not_memoize(name):
    """A successful serializer-surface access (DRF present) does not bind into root globals.

    Non-memoization (Decision 12): the resolved class is NOT written into the root
    module ``globals()``, so each access re-fires the guard (the absent-DRF test can
    evict + re-hit it). Run WITHOUT the absence fixture (DRF present), so the access
    succeeds; then assert the name is not in ``vars(...)``.
    """
    with contextlib.suppress(AttributeError):
        delattr(django_strawberry_framework, name)
    exported = getattr(django_strawberry_framework, name)
    assert exported is not None
    assert name not in vars(django_strawberry_framework)
