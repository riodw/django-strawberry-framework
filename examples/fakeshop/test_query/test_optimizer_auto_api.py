"""Live ``/graphql/`` coverage for routed nested-fetch strategy selection.

Postgres-marked rows pin per-field ``OptimizerHint.strategy`` overrides over
HTTP: a windowed hint under a lateral extension default emits no
``CROSS JOIN LATERAL``, and a lateral hint under a windowed default emits one.
"""

import pytest
import strawberry
from apps.library.models import Book, Branch, Shelf
from apps.products import services
from apps.products.models import Category
from debug_toolbar.toolbar import debug_toolbar_urls
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import path
from strategy_schemas import build_strategy_schema, make_django_type
from strawberry.django.views import GraphQLView

from django_strawberry_framework import (
    DjangoListField,
    DjangoOptimizerExtension,
    OptimizerHint,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import TestClient

pytestmark = pytest.mark.urls(__name__)

_current: dict[str, object | None] = {"schema": None}


def _graphql_view(request):
    """Serve the probe schema installed by the current test's holder fixture."""
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


@pytest.fixture
def install_hashable_scalar_cache_schema(_reload_project_schema_for_acceptance_tests):
    """Install a live schema whose custom scalar returns hostile hashable values."""
    from typing import NewType

    registry.clear()
    category_type = make_django_type(
        "CacheCategoryType",
        Category,
        ("id", "name"),
        node=False,
    )

    class EqualityBomb:
        def __hash__(self):
            return 1

        def __eq__(self, _other):
            raise RuntimeError("custom scalar equality must not run in cache lookup")

    BombValue = NewType("BombValue", object)
    bomb_scalar = strawberry.scalar(
        name="BombValue",
        serialize=lambda _value: "ok",
        parse_value=lambda _value: EqualityBomb(),
    )

    @strawberry.type
    class Misc:
        @strawberry.field
        def logs(self, after: BombValue) -> list[str]:
            return ["ok"]

    @strawberry.type
    class Query:
        objs: list[category_type] = DjangoListField(category_type)

        @strawberry.field
        def misc(self) -> Misc:
            return Misc()

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    _current["schema"] = strawberry.Schema(
        query=Query,
        config=strawberry_config(extra_scalar_map={BombValue: bomb_scalar}),
        extensions=[lambda: optimizer],
    )
    yield optimizer
    _current["schema"] = None


@pytest.mark.django_db
def test_repeated_live_query_survives_hashable_custom_scalar_equality(
    install_hashable_scalar_cache_schema,
):
    """A hostile custom scalar cannot abort a repeated optimizer cache lookup."""
    services.seed_data(1)
    query = """
        query Q($value: BombValue!) {
          objs { name }
          misc { logs(after: $value) }
        }
    """

    first = TestClient().query(query, variables={"value": "marker"})
    second = TestClient().query(query, variables={"value": "marker"})

    assert first.data["misc"]["logs"] == ["ok"]
    assert second.data["misc"]["logs"] == ["ok"]
    assert install_hashable_scalar_cache_schema.cache_info().misses == 2
    assert install_hashable_scalar_cache_schema.cache_info().hits == 0


_HINT_PAGE_DOCUMENT = """
query {
  shelves {
    code
    booksConnection(first: 2) {
      edges { node { title } }
    }
  }
}
"""

_HINT_PAGE_DATA = {
    "shelves": [
        {
            "code": "HINT",
            "booksConnection": {
                "edges": [{"node": {"title": "Alpha"}}, {"node": {"title": "Beta"}}],
            },
        },
    ],
}


def _seed_hint_shelf():
    """One shelf with three books so ``first: 2`` is a real bounded page."""
    branch = Branch.objects.create(name="Hint strategy", city="Boston")
    shelf = Shelf.objects.create(code="HINT", topic="Strategy", branch=branch)
    for title in ("Alpha", "Beta", "Gamma"):
        Book.objects.create(title=title, shelf=shelf)


def _book_sql(captured):
    """Captured statements that touch ``library_book`` (the nested child table)."""
    return [entry["sql"] for entry in captured.captured_queries if "library_book" in entry["sql"]]


@pytest.fixture
def install_hinted_strategy_schema(_reload_project_schema_for_acceptance_tests):
    """Install a library graph whose ``booksConnection`` carries a strategy hint."""

    def _install(default_strategy, books_hint):
        registry.clear()
        make_django_type(
            "HintBookType",
            Book,
            ("id", "title"),
            meta_extra={"connection": {"total_count": True}},
        )
        shelf_type = make_django_type(
            "HintShelfType",
            Shelf,
            ("id", "code", "books"),
            meta_extra={"optimizer_hints": {"books": books_hint}},
        )
        finalize_django_types()
        query_type = strawberry.type(
            type(
                "HintStrategyQuery",
                (),
                {
                    "__annotations__": {"shelves": list[shelf_type]},
                    "shelves": DjangoListField(shelf_type),
                },
            ),
        )
        _current["schema"] = build_strategy_schema(query_type, default_strategy)

    yield _install
    _current["schema"] = None


@pytest.mark.django_db
@pytest.mark.pg
def test_per_field_strategy_hint_windowed_under_lateral_default_skips_lateral_over_http(
    install_hinted_strategy_schema,
):
    """``OptimizerHint.strategy("windowed")`` wins over a lateral extension default."""
    _seed_hint_shelf()
    install_hinted_strategy_schema("lateral", OptimizerHint.strategy("windowed"))

    with CaptureQueriesContext(connection) as captured:
        response = TestClient().query(_HINT_PAGE_DOCUMENT)

    assert response.data == _HINT_PAGE_DATA
    book_sql = _book_sql(captured)
    assert book_sql, captured.captured_queries
    assert all("CROSS JOIN LATERAL" not in sql for sql in book_sql), book_sql


@pytest.mark.django_db
@pytest.mark.pg
def test_per_field_strategy_hint_lateral_under_windowed_default_emits_lateral_over_http(
    install_hinted_strategy_schema,
):
    """``OptimizerHint.strategy("lateral")`` wins over a windowed extension default."""
    _seed_hint_shelf()
    install_hinted_strategy_schema("windowed", OptimizerHint.strategy("lateral"))

    with CaptureQueriesContext(connection) as captured:
        response = TestClient().query(_HINT_PAGE_DOCUMENT)

    assert response.data == _HINT_PAGE_DATA
    book_sql = _book_sql(captured)
    assert book_sql, captured.captured_queries
    assert any("CROSS JOIN LATERAL" in sql for sql in book_sql), book_sql
