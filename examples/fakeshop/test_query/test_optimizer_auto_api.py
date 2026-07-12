"""Live ``/graphql/`` coverage for routed nested-fetch strategy selection."""

import pytest
import strawberry
from apps.library.models import Book, Branch, Shelf
from debug_toolbar.toolbar import debug_toolbar_urls
from django.urls import path
from strategy_schemas import build_strategy_schema, make_django_type
from strawberry.django.views import GraphQLView

from django_strawberry_framework import DjangoListField, finalize_django_types
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import TestClient

pytestmark = pytest.mark.urls(__name__)

_current: dict[str, object | None] = {"schema": None}


def _graphql_view(request):
    """Serve the probe schema installed by ``install_auto_strategy_schema``."""
    schema = _current["schema"]
    assert schema is not None
    return GraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql/", _graphql_view), *debug_toolbar_urls()]


@pytest.fixture
def install_auto_strategy_schema(_reload_project_schema_for_acceptance_tests):
    """Install a minimal library graph whose nested queryset is lateral-capable."""
    registry.clear()
    make_django_type(
        "AutoBookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}},
    )
    shelf_type = make_django_type("AutoShelfType", Shelf, ("id", "code", "books"))
    finalize_django_types()
    query_type = strawberry.type(
        type(
            "AutoStrategyQuery",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type]},
                "shelves": DjangoListField(shelf_type),
            },
        ),
    )
    _current["schema"] = build_strategy_schema(query_type, "auto")
    yield
    _current["schema"] = None


@pytest.mark.django_db
def test_auto_strategy_non_postgres_fallback_is_bounded_over_http(
    install_auto_strategy_schema,
):
    """SQLite executes the windowed body and returns truthful page metadata."""
    branch = Branch.objects.create(name="Auto strategy", city="Boston")
    shelf = Shelf.objects.create(code="AUTO", topic="Routing", branch=branch)
    for title in ("a", "b", "c"):
        Book.objects.create(title=title, shelf=shelf)

    response = TestClient().query(
        """
        query {
          shelves {
            code
            booksConnection(first: 2) {
              edges { node { title } }
              totalCount
              pageInfo { hasNextPage }
            }
          }
        }
        """,
    )

    assert response.data == {
        "shelves": [
            {
                "code": "AUTO",
                "booksConnection": {
                    "edges": [{"node": {"title": "a"}}, {"node": {"title": "b"}}],
                    "totalCount": 3,
                    "pageInfo": {"hasNextPage": True},
                },
            },
        ],
    }
