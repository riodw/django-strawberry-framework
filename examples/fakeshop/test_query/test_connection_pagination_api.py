"""Live /graphql pagination error containment and ``totalCount`` gating for connections.

Covers the exception-containment invariant for the connection surface:
malformed pagination arguments (negative ``first``/``last``, over-cap ``first``,
malformed ``after``/``before`` cursors) must surface as ``GraphQLError``
entries, never as raw ``ValueError``/``TypeError`` tracebacks. Exercised
through the live ``/graphql/`` HTTP endpoint (``django.test.Client``) so the
full Strawberry ``ConnectionExtension`` stack is involved - the
through-schema mandate for connections.

The ``Meta.connection`` opt-in is pinned here too, read off the two shipped
shapes it produces: the products connections declare no ``connection`` key, so
``totalCount`` is not a field of their generated connection type at all, while
``GenreType.Meta.connection`` opts in and its connection both declares and
resolves one. The generated non-opted connection type's inherited SDL
description is read from the same endpoint, since that description is the only
part of the bare shape a client can observe.
"""

import pytest
from apps.library import models as library_models
from apps.products.services import seed_data
from graphql_client import assert_graphql_success, graphql_payload


@pytest.mark.django_db
def test_live_negative_first_is_graphql_error():
    """``first: -1`` via live HTTP is a GraphQLError (not a raw ValueError)."""
    seed_data(1)
    payload = graphql_payload("{ allItems(first: -1) { edges { node { id } } } }")
    assert "errors" in payload
    assert any("non-negative" in str(e.get("message", "")).lower() for e in payload["errors"])
    # Ensure the error is not a raw ValueError traceback leaking
    for err in payload["errors"]:
        # GraphQLError entries have message, not Python traceback
        assert "ValueError" not in str(err.get("message", ""))
        assert "Traceback" not in str(err.get("message", ""))


@pytest.mark.django_db
def test_live_over_cap_first_is_graphql_error():
    """``first`` over the configured ``relay_max_results`` is a GraphQLError."""
    seed_data(1)
    # Default relay_max_results is 100 (strawberry default)
    payload = graphql_payload("{ allItems(first: 101) { edges { node { id } } } }")
    assert "errors" in payload
    assert any("cannot be higher than" in str(e.get("message", "")) for e in payload["errors"])


@pytest.mark.django_db
def test_live_malformed_after_cursor_is_graphql_error():
    """A malformed ``after:`` cursor is a GraphQLError (not ValueError/TypeError)."""
    seed_data(1)
    payload = graphql_payload(
        '{ allItems(first: 1, after: "not-a-cursor") { edges { node { id } } } }',
    )
    assert "errors" in payload
    # The error should mention cursor / pagination, not leak Python types
    assert len(payload["errors"]) >= 1
    for err in payload["errors"]:
        msg = str(err.get("message", ""))
        # Should not leak raw ValueError/TypeError class names
        assert "ValueError" not in msg
        assert "TypeError" not in msg


@pytest.mark.django_db
def test_live_malformed_before_cursor_is_graphql_error():
    """A malformed ``before:`` cursor is a GraphQLError."""
    seed_data(1)
    payload = graphql_payload(
        '{ allItems(last: 1, before: "bad-base64!") { edges { node { id } } } }',
    )
    assert "errors" in payload
    assert len(payload["errors"]) >= 1


@pytest.mark.django_db
def test_live_first_and_last_together_is_graphql_error():
    """``first`` + ``last`` together is the package's mutual-exclusivity GraphQLError."""
    seed_data(1)
    payload = graphql_payload("{ allItems(first: 1, last: 1) { edges { node { id } } } }")
    assert "errors" in payload
    assert any("mutually exclusive" in str(e.get("message", "")) for e in payload["errors"])


@pytest.mark.django_db
def test_live_keyset_negative_first_is_graphql_error():
    """Keyset ``first: -5`` is a GraphQLError on the declared-cursor connection too.

    ``allLibraryIssuesConnection`` resolves ``IssueType``, whose
    ``Meta.cursor_field = ("-number", "id")`` routes the page through the
    keyset path rather than the offset path the other cases exercise. The
    bound is rejected during argument validation, so the containment holds
    for both connection flavors.
    """
    seed_data(1)
    payload = graphql_payload(
        "{ allLibraryIssuesConnection(first: -5) { edges { node { id } } } }",
    )
    assert "errors" in payload
    assert any("non-negative" in str(e.get("message", "")).lower() for e in payload["errors"])


@pytest.mark.django_db
def test_total_count_is_a_field_only_on_the_connection_that_opted_in():
    """``Meta.connection = {"total_count": True}`` is what puts ``totalCount`` in the schema.

    Both shipped shapes are read in one request each, because the claim is the
    CONTRAST: a client asking a products connection for ``totalCount`` is told
    the field does not exist (a validation error naming it, so the opt-out is
    visible in the schema rather than answered with a null), while the opted-in
    genre connection answers the unpaginated count beside a one-edge page - the
    count is of the whole set, not of the window.
    """
    seed_data(1)
    library_models.Genre.objects.create(name="Alpha")
    library_models.Genre.objects.create(name="Beta")

    not_opted = graphql_payload("{ allItems(first: 1) { totalCount } }")
    assert "errors" in not_opted, not_opted
    assert any(
        "Cannot query field 'totalCount'" in str(error.get("message", ""))
        for error in not_opted["errors"]
    ), not_opted
    assert not_opted.get("data") is None, not_opted

    opted = assert_graphql_success(
        "{ allLibraryGenresConnection(first: 1) { edges { node { name } } totalCount } }",
    )
    connection = opted["allLibraryGenresConnection"]
    assert len(connection["edges"]) == 1
    assert connection["totalCount"] == 2


@pytest.mark.django_db
def test_the_non_opted_connection_type_keeps_the_inherited_sdl_description():
    """The always-concrete generated connection still describes itself to a client.

    A non-opted type gets a generated ``<TypeName>Connection`` subclass rather
    than the bare ``DjangoConnection[T]`` alias, and the description Strawberry's
    own ``Connection`` base carries has to survive that generation: it is the
    only part of the bare connection shape introspection can show, so a silent
    drop would be invisible everywhere else.
    """
    data = assert_graphql_success('{ __type(name: "ItemTypeConnection") { description } }')

    assert data["__type"]["description"] == "A connection to a list of items."
