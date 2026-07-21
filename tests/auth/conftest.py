"""Shared fixtures for the auth test modules.

Holds the ``_sync_boundary_spy`` fixture (previously duplicated verbatim in
``test_mutations`` and ``test_queries``). Plain, non-fixture helpers shared
across the modules live in ``tests/auth/_helpers.py``.
"""

from __future__ import annotations

import pytest

from django_strawberry_framework.auth import mutations as auth_mutations


@pytest.fixture
def _sync_boundary_spy(monkeypatch):
    """Spy on ``run_in_one_sync_boundary`` so async-body entry is counted deterministically.

    Both ``login`` / ``logout`` and ``current_user`` ride the same
    ``_make_auth_field`` dispatch seam and the same ``_sync_bridged_async_body``
    interim async body, which bridges to the sync body through this ONE shared
    worker. Counting its calls counts how many times the native async body was
    awaited (and so proves which path resolved the field). The async closure
    resolves the module-global name at call time, so patching the module attribute
    is observed.
    """
    calls = []
    real = auth_mutations.run_in_one_sync_boundary

    async def _spy(fn, *args, **kwargs):
        calls.append(fn)
        return await real(fn, *args, **kwargs)

    monkeypatch.setattr(auth_mutations, "run_in_one_sync_boundary", _spy)
    return calls
