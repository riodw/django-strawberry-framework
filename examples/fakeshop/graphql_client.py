"""Shared live-``/graphql/`` HTTP helpers for the fakeshop acceptance suites.

Single-sites the live-tier request contracts: JSON GraphQL posts, raw-body posts,
status-code assertions, parsed payload extraction, GraphQL-error rejection, and
exact-data assertions. Superset signatures keep simple callers terse while
letting variable-driven and custom-client tests use the same envelope.

The JSON path now routes through the package's own
:class:`django_strawberry_framework.testing.TestClient` (spec-043 Slice 2), so
every live suite's ordinary GraphQL post shares the one body-builder / decode
path instead of re-spelling the ``json.dumps`` + content-type + envelope-split
boilerplate. The functions keep their raw-``HttpResponse`` return contract (the
client stashes it on ``Response.response``) so the existing ``.status_code`` /
``.json()`` call sites are unchanged. ``post_graphql_raw`` deliberately stays a
raw ``client.post`` - its subject is the raw request envelope (malformed bodies,
content-type negotiation), which ``TestClient`` exists to abstract away.
"""

from __future__ import annotations

from typing import Any

from django.test import Client

from django_strawberry_framework.testing import TestClient


def post_graphql(query: str, *, client: Client | None = None, variables: dict | None = None):
    """POST one GraphQL document to the live ``/graphql/`` endpoint via ``TestClient``.

    Routes through the package client's body-build + decode path;
    ``assert_no_errors`` is off here so error-expecting callers still read
    ``response.json()["errors"]`` (the shared assertion helpers below own the
    error policy). Returns the raw ``HttpResponse`` ``TestClient`` kept on
    ``Response.response``.
    """
    result = TestClient(client=client).query(query, variables=variables, assert_no_errors=False)
    return result.response


def post_graphql_raw(body: str | bytes, *, client: Client | None = None):
    """POST a raw JSON body to the live ``/graphql/`` endpoint.

    Deliberately a raw ``client.post`` (not ``TestClient``): the subject is the
    wire envelope itself - a hand-built or malformed body - which the client's
    body-builder would otherwise replace. This is the documented raw-envelope
    exemption (spec-043 Slice 2).
    """
    graphql_client = client or Client()
    return graphql_client.post(
        "/graphql/",
        data=body,
        content_type="application/json",
    )


def graphql_payload(
    query: str,
    *,
    client: Client | None = None,
    variables: dict | None = None,
) -> dict[str, Any]:
    """POST ``query`` and return parsed JSON after asserting HTTP 200."""
    response = post_graphql(query, client=client, variables=variables)
    assert response.status_code == 200
    return response.json()


def assert_graphql_success(
    query: str,
    *,
    client: Client | None = None,
    variables: dict | None = None,
) -> dict[str, Any]:
    """POST ``query``, assert HTTP 200 and no GraphQL errors, then return ``data``."""
    payload = graphql_payload(query, client=client, variables=variables)
    assert "errors" not in payload, payload
    return payload["data"]


def assert_graphql_data(
    query: str,
    expected: dict,
    *,
    client: Client | None = None,
    variables: dict | None = None,
):
    """POST ``query`` and assert a 200, no ``errors``, and exact ``data`` equality.

    Returns the response so callers can layer extra asserts (headers, query
    capture) on top of the shared preamble.
    """
    response = post_graphql(query, client=client, variables=variables)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"] == expected
    return response
