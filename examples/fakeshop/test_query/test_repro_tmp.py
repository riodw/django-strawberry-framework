import pytest
from apps.library import models


def _post(client, query):
    return client.post("/graphql/", data={"query": query}, content_type="application/json")


def _seed(client):
    for n in ("Alpha", "Beta", "Gamma"):
        models.Genre.objects.create(name=n)


@pytest.mark.django_db
def test_no_pagination_sibling(client):
    _seed(client)
    resp = _post(client, """
        query { allLibraryGenresConnection { edges { node { name } } ... { totalCount } } }
    """)
    print("A", resp.json())
    assert "errors" not in resp.json(), resp.json()


@pytest.mark.django_db
def test_no_pagination_fragwrap(client):
    _seed(client)
    resp = _post(client, """
        query { allLibraryGenresConnection { ... { totalCount } } }
    """)
    print("B", resp.json())
    assert "errors" not in resp.json(), resp.json()


@pytest.mark.django_db
def test_skip_node_field(client):
    _seed(client)
    resp = _post(client, """
        query { allLibraryGenresConnection(first: 2) { edges { node { name ... @skip(if: true) { id } } } } }
    """)
    print("C", resp.json())
    assert "errors" not in resp.json(), resp.json()


@pytest.mark.django_db
def test_named_fragment_sibling(client):
    _seed(client)
    resp = _post(client, """
        query { allLibraryGenresConnection(first: 2) { edges { node { name } } ...CF }
        }
        fragment CF on GenreTypeConnection { totalCount }
    """)
    print("D", resp.json())
    assert "errors" not in resp.json(), resp.json()
