"""Shared live-``/graphql/`` HTTP helpers for the fakeshop acceptance suites.

The one ``Client().post("/graphql/", ...)`` wrapper (and its status-200 +
data-equality assert) every ``test_query`` module historically re-declared -
single-sited here like ``schema_reload.py`` (importable via ``pytest.ini``'s
``pythonpath = examples/fakeshop``) so the live-tier request shape has ONE
implementation (docs/feedback.md DRY pass, T5). Superset signature: modules
that never pass ``client`` / ``variables`` simply omit them.
"""

from __future__ import annotations

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


def assert_graphql_data(query: str, expected: dict, *, client: Client | None = None):
    """POST ``query`` and assert a 200, no ``errors``, and exact ``data`` equality.

    Returns the response so callers can layer extra asserts (headers, query
    capture) on top of the shared preamble.
    """
    response = post_graphql(query, client=client)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"] == expected
    return response
