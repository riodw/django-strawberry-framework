"""Shared auth-test helpers hoisted out of the individual test modules.

Plain (non-fixture) helpers the auth test modules share: the bounded event-loop
barrier ``_drain_until`` (previously defined in ``test_sessions`` and
cross-imported by ``test_mutations``) and the session-carrying request builder
``_session_request`` (previously duplicated byte-for-byte between
``test_mutations`` and ``test_queries``). Fixtures live in ``conftest.py``; these
are ordinary callables, so they are imported explicitly rather than injected.
"""

from __future__ import annotations

import asyncio

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory


async def _drain_until(predicate, *, budget=10_000):
    """Yield control (``sleep(0)``) until ``predicate()`` holds, bounded by a counter.

    A loop-implementation-agnostic barrier: it advances the event loop a bounded
    number of times rather than trusting any single scheduling turn or a wall-clock
    sleep. The budget guards against a real deadlock hanging the suite -- if the
    predicate never holds the test fails loudly instead of blocking forever.
    """
    for _ in range(budget):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("barrier predicate never became true within the yield budget")


def _session_request(user=None):
    """Build a real request with a working session (the auth transport contract)."""
    request = RequestFactory().post("/graphql/")
    SessionMiddleware(lambda _request: None).process_request(request)
    request.user = user if user is not None else AnonymousUser()
    return request
