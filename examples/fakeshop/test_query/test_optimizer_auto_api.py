"""Live ``/graphql/`` coverage for routed nested-fetch strategy selection.

Postgres-marked rows pin per-field ``OptimizerHint.strategy`` overrides over
HTTP: a windowed hint under a lateral extension default emits no
``CROSS JOIN LATERAL``, and a lateral hint under a windowed default emits one.
SQLite rows pin the auto fallback's window SQL, a per-field windowed hint
that wins over a refusing extension default (OVER cannot come from the
default), a ``.distinct()`` child that refuses the window, and an unhashable
custom-scalar variable that still shares one plan-cache identity across
requests.
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
def test_auto_strategy_picks_the_vendor_body_and_pages_truthfully_over_http(
    install_auto_strategy_schema,
):
    """Auto runs LATERAL on Postgres, the windowed body elsewhere, with truthful page metadata."""
    branch = Branch.objects.create(name="Auto strategy", city="Boston")
    shelf = Shelf.objects.create(code="AUTO", topic="Routing", branch=branch)
    for title in ("a", "b", "c"):
        Book.objects.create(title=title, shelf=shelf)

    document = """
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
        """
    with CaptureQueriesContext(connection) as captured:
        response = TestClient().query(document)

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
    book_sql = [
        entry["sql"] for entry in captured.captured_queries if "library_book" in entry["sql"]
    ]
    windowed = [sql for sql in book_sql if "OVER (" in sql]
    assert len(windowed) == 1, book_sql
    if connection.vendor == "postgresql":
        assert "CROSS JOIN LATERAL" in windowed[0], book_sql
        assert "PARTITION BY" not in windowed[0], book_sql
    else:
        assert "PARTITION BY" in windowed[0], book_sql
        assert "LATERAL" not in windowed[0], book_sql


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


@pytest.fixture
def install_unhashable_set_scalar_cache_schema(_reload_project_schema_for_acceptance_tests):
    """Install a live schema whose custom scalar parser returns a ``set``."""
    from typing import NewType

    registry.clear()
    category_type = make_django_type(
        "SetCacheCategoryType",
        Category,
        ("id", "name"),
        node=False,
    )

    SetValue = NewType("SetValue", object)
    set_scalar = strawberry.scalar(
        name="SetValue",
        serialize=lambda value: sorted(value),
        parse_value=set,
    )

    @strawberry.type
    class Misc:
        @strawberry.field
        def logs(self, after: SetValue) -> list[str]:
            return sorted(after)

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
        config=strawberry_config(extra_scalar_map={SetValue: set_scalar}),
        extensions=[lambda: optimizer],
    )
    yield optimizer
    _current["schema"] = None


@pytest.mark.django_db
def test_repeated_live_query_shares_plan_cache_for_unhashable_set_scalar(
    install_unhashable_set_scalar_cache_schema,
):
    """A ``set``-valued custom scalar is frozen structurally, so two requests share one plan.

    The sibling ``EqualityBomb`` row is the opaque-identity miss; this is the
    must-not: a library-owned container freeze still hits the cache. Returning
    the raw set from the freezer would ``TypeError`` inside the plan-key
    ``frozenset``.
    """
    services.seed_data(1)
    query = """
        query Q($x: SetValue!) {
          objs { name }
          misc { logs(after: $x) }
        }
    """

    first = TestClient().query(query, variables={"x": ["b", "a"]})
    second = TestClient().query(query, variables={"x": ["a", "b"]})

    assert first.data["misc"]["logs"] == ["a", "b"]
    assert second.data["misc"]["logs"] == ["a", "b"]
    assert install_unhashable_set_scalar_cache_schema.cache_info().misses == 1
    assert install_unhashable_set_scalar_cache_schema.cache_info().hits == 1
    assert install_unhashable_set_scalar_cache_schema.cache_info().size == 1


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
            "code": "A",
            "booksConnection": {
                "edges": [{"node": {"title": "a0"}}, {"node": {"title": "a1"}}],
            },
        },
        {
            "code": "B",
            "booksConnection": {
                "edges": [{"node": {"title": "b0"}}],
            },
        },
        {
            "code": "C",
            "booksConnection": {
                "edges": [],
            },
        },
    ],
}


def _seed_hint_shelf():
    """Three shelves with 5, 1 and 0 books.

    More than one parent keeps the nested page off the single-parent fetch
    (``django_strawberry_framework/optimizer/single_parent_fetch.py``), whose
    SQL carries neither a window nor a lateral join, and the uneven counts make
    ``first: 2`` a real bounded page on one parent only.
    """
    branch = Branch.objects.create(name="Hint strategy", city="Boston")
    shelf_a = Shelf.objects.create(code="A", topic="Strategy", branch=branch)
    shelf_b = Shelf.objects.create(code="B", topic="Strategy", branch=branch)
    Shelf.objects.create(code="C", topic="Strategy", branch=branch)
    for index in range(5):
        Book.objects.create(title=f"a{index}", shelf=shelf_a)
    Book.objects.create(title="b0", shelf=shelf_b)


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


class _RefusingNestedStrategy:
    """Extension default that never accepts a nested connection plan.

    A windowed per-field hint must still emit ``OVER (``; if the hint is
    ignored, the refusing default leaves per-parent fallback SQL with no window.
    """

    name = "refusing"

    def plan(self, _request, _plan):
        return False


@pytest.mark.django_db
def test_per_field_strategy_hint_windowed_emits_over_when_the_default_refuses(
    install_hinted_strategy_schema,
):
    """``OptimizerHint.strategy("windowed")`` plans ``ROW_NUMBER() OVER`` on SQLite.

    Postgres HTTP rows pin the same branch against LATERAL; this row is the
    SQLite pin and the must-not (a refusing extension default cannot be the
    source of the window).
    """
    _seed_hint_shelf()
    install_hinted_strategy_schema(_RefusingNestedStrategy(), OptimizerHint.strategy("windowed"))

    with CaptureQueriesContext(connection) as captured:
        response = TestClient().query(_HINT_PAGE_DOCUMENT)

    assert response.data == _HINT_PAGE_DATA
    book_sql = _book_sql(captured)
    assert any("OVER (" in sql and "PARTITION BY" in sql for sql in book_sql), book_sql
    windowed = [sql for sql in book_sql if "OVER (" in sql]
    assert len(windowed) == 1, book_sql


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
    assert any("OVER (" in sql and "PARTITION BY" in sql for sql in book_sql), book_sql
    assert all("LATERAL" not in sql for sql in book_sql), book_sql


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
    assert any("LATERAL" in sql for sql in book_sql), book_sql


@pytest.fixture
def install_distinct_child_schema(_reload_project_schema_for_acceptance_tests):
    """Install a library graph whose nested book queryset is ``.distinct()``."""

    def _distinct(cls, queryset, info, **kwargs):
        return queryset.distinct()

    registry.clear()
    make_django_type(
        "DistinctBookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}},
        namespace_extra={"get_queryset": classmethod(_distinct)},
    )
    shelf_type = make_django_type("DistinctShelfType", Shelf, ("id", "code", "books"))
    finalize_django_types()
    query_type = strawberry.type(
        type(
            "DistinctChildQuery",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type]},
                "shelves": DjangoListField(shelf_type),
            },
        ),
    )
    _current["schema"] = build_strategy_schema(query_type, "windowed")
    yield
    _current["schema"] = None


@pytest.mark.django_db
def test_distinct_child_queryset_never_windows_over_http(install_distinct_child_schema):
    """A target ``get_queryset`` returning ``.distinct()`` leaves the nested page unplanned.

    The nested planner refuses the whole relation (Decision 6), so each parent
    pays its own child query and no ``ROW_NUMBER() OVER`` window is emitted.
    """
    _seed_hint_shelf()

    with CaptureQueriesContext(connection) as captured:
        response = TestClient().query(_HINT_PAGE_DOCUMENT)

    assert response.data == _HINT_PAGE_DATA
    book_sql = _book_sql(captured)
    assert book_sql, captured.captured_queries
    assert not any("OVER (" in sql for sql in book_sql), book_sql
    assert len(book_sql) > 1, book_sql
