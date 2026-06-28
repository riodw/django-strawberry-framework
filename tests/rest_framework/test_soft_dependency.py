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

DRF is INSTALLED in the test env, so absence is SIMULATED by monkeypatching
``builtins.__import__`` to raise on a guarded ``import rest_framework`` and
evicting the relevant ``sys.modules`` entries. The eviction discipline is strict:
both ``rest_framework*`` AND ``django_strawberry_framework.rest_framework*`` are
evicted (and restored) so this test does not poison sibling tests that DO use DRF
(the spec-037 ``pillow``-absent-path precedent). The teardown restores every
evicted module + the root ``SerializerMutation`` binding state.
"""

from __future__ import annotations

import builtins
import contextlib
import importlib
import sys

import pytest

import django_strawberry_framework

# The verified DRF floor (Slice 0); the install hint must name it (place 2 of the
# three-places-that-must-agree). The test matches this substring.
_HINT_SUBSTRING = "djangorestframework>=3.17.0"

_REAL_IMPORT = builtins.__import__


def _evict_drf_modules() -> dict[str, object]:
    """Pop every ``rest_framework*`` + framework-rest-framework module; return them for restore."""
    saved: dict[str, object] = {}
    for name in list(sys.modules):
        if (
            name == "rest_framework"
            or name.startswith("rest_framework.")
            or name == "django_strawberry_framework.rest_framework"
            or name.startswith(
                "django_strawberry_framework.rest_framework.",
            )
        ):
            saved[name] = sys.modules.pop(name)
    return saved


def _block_drf_import(
    name,
    globals=None,  # noqa: A002 - mirrors builtins.__import__'s exact signature
    locals=None,  # noqa: A002 - mirrors builtins.__import__'s exact signature
    fromlist=(),
    level=0,
):
    """An ``__import__`` shim that raises ``ImportError`` for the TOP-LEVEL DRF import.

    Only an ABSOLUTE (``level == 0``) ``import rest_framework`` / ``from
    rest_framework import ...`` is blocked - that is what ``require_drf()`` runs to
    detect DRF. A RELATIVE import (``from .rest_framework import require_drf``, which
    resolves the framework's OWN ``rest_framework`` SUBPACKAGE with ``level == 1``)
    must pass through so the guard itself is reachable; blocking it would raise a raw
    ``ImportError`` before ``require_drf()`` can wrap the absence in the install hint.
    """
    if level == 0 and (name == "rest_framework" or name.startswith("rest_framework.")):
        raise ImportError(f"No module named {name!r} (simulated DRF absence)")
    return _REAL_IMPORT(name, globals, locals, fromlist, level)


@pytest.fixture
def _simulate_drf_absent(monkeypatch):
    """Simulate DRF absence: block its import + evict its modules; restore on teardown.

    Strict eviction + restore so sibling tests (which DO use DRF) are unaffected.
    Also clears any bound root ``SerializerMutation`` attribute (the non-memoizing
    ``__getattr__`` never binds one, but a defensive delete keeps the absent path
    clean even if a prior test mutated globals).
    """
    saved = _evict_drf_modules()
    monkeypatch.setattr(builtins, "__import__", _block_drf_import)
    with contextlib.suppress(AttributeError):
        delattr(django_strawberry_framework, "SerializerMutation")
    try:
        yield
    finally:
        monkeypatch.undo()
        # Drop any partially-imported modules created under the block, then restore
        # the originally-evicted real modules so siblings see a clean DRF.
        for name in list(sys.modules):
            if (
                name == "rest_framework"
                or name.startswith("rest_framework.")
                or name == "django_strawberry_framework.rest_framework"
                or name.startswith("django_strawberry_framework.rest_framework.")
            ):
                del sys.modules[name]
        sys.modules.update(saved)


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
