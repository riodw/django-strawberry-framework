"""Shared live-``/graphql/`` HTTP helpers for the fakeshop acceptance suites.

Single-sites the live-tier request contracts: JSON GraphQL posts, raw-body posts,
status-code assertions, parsed payload extraction, GraphQL-error rejection, and
exact-data assertions. Superset signatures keep simple callers terse while
letting variable-driven and custom-client tests use the same envelope.
"""

from __future__ import annotations

from typing import Any

from django.test import Client


def post_graphql(query: str, *, client: Client | None = None, variables: dict | None = None):
    """POST one GraphQL document to the live ``/graphql/`` endpoint."""
    graphql_client = client or Client()
    payload: dict = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    return graphql_client.post(
        "/graphql/",
        data=payload,
        content_type="application/json",
    )


def post_graphql_raw(body: str | bytes, *, client: Client | None = None):
    """POST a raw JSON body to the live ``/graphql/`` endpoint."""
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
