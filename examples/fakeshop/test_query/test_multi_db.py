"""Live /graphql/ multi-database cooperation tests against the sharded fakeshop layout.

Scope (per spec Goals item 3 + Test plan ``### examples/fakeshop/test_query/test_multi_db.py``):
two live ``/graphql/`` HTTP tests against the sharded fakeshop layout.

- Test 1 — seeding rows on ``shard_b`` and reading them through ``/graphql/``
  via a ``.using("shard_b")`` root resolver returns the seeded rows.
- Test 2 — cross-shard isolation: a chain seeded on ``default`` is NOT
  visible through a ``using("shard_b")`` resolver.

Critical contract pins (do not violate without an explicit spec revision):

- Module-level ``pytest.skip(allow_module_level=True)`` gate per Decision 6
  (NOT ``pytest.mark.skipif`` — the env var changes ``config.settings.DATABASES``
  at module import time; mark evaluation happens after import).
- ``@pytest.mark.django_db(databases=["default", "shard_b"])`` per rev2 H8
  on each test (pytest-django blocks non-default-DB access otherwise).
- Full ``Branch → Shelf → Book`` chain per alias via ``_seed_book_chain``
  per rev2 H9 (``Book.shelf`` and ``Shelf.branch`` are non-null FKs).
- Live ``/graphql/`` HTTP exclusively via ``django.test.Client.post(...)``
  per rev2 H7 — NO in-process ``execute_sync(...)`` alternative.
- Schema built INSIDE a per-test fixture that runs AFTER the autouse
  reload (rev3 R4) — the holder pattern below defers schema construction
  past the registry clear so the test sees freshly-reloaded ``BookType``.
- ``override_settings(ROOT_URLCONF=__name__)`` per rev3 R5 with
  ``clear_url_caches()`` on enter AND in teardown.
"""

# Top-block imports support the autouse reload fixture per Decision 7 +
# rev4 V6 — sys.modules.get(...), importlib.reload(...) /
# importlib.import_module(...). os is the env-var gate.

import importlib
import os
import sys

import pytest

if os.environ.get("FAKESHOP_SHARDED") != "1":
    pytest.skip(
        "requires FAKESHOP_SHARDED=1 (the sharded DATABASES layout)",
        allow_module_level=True,
    )

# Below this line, FAKESHOP_SHARDED=1 is set and ``shard_b`` is in DATABASES.
# These imports run only after the skip check passes — otherwise
# ``from apps.library import models`` would crash in single-DB mode where
# ``shard_b`` is not registered in DATABASES.

import strawberry  # noqa: E402
from apps.library import models  # noqa: E402
from django.test import Client, override_settings  # noqa: E402
from django.urls import clear_url_caches, path  # noqa: E402
from strawberry.django.views import GraphQLView  # noqa: E402
from strawberry.types import Info  # noqa: E402

from django_strawberry_framework import DjangoOptimizerExtension  # noqa: E402
from django_strawberry_framework.registry import registry  # noqa: E402

# ---------------------------------------------------------------------------
# Autouse reload fixture (copied verbatim from
# ``examples/fakeshop/test_query/test_library_api.py::_reload_project_schema_for_acceptance_tests``)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reload_project_schema_for_acceptance_tests():
    """Recreate imported DjangoType classes if package tests cleared the registry."""
    # This reload is mandatory for order-independent suite isolation:
    # package tests clear the global registry, while the example project
    # schema finalizes import-time DjangoType classes. Reload only schema
    # modules (not apps.library.models) so Django model classes stay stable and
    # DjangoType subclasses are recreated against a fresh registry.
    # Hidden invariant: tests must not module-level import classes from
    # apps.library.schema, or they will hold stale class objects after reload.
    registry.clear()
    library_schema = sys.modules.get("apps.library.schema")
    if library_schema is None:
        importlib.import_module("apps.library.schema")
    else:
        importlib.reload(library_schema)

    project_schema = sys.modules.get("config.schema")
    if project_schema is None:
        importlib.import_module("config.schema")
    else:
        importlib.reload(project_schema)

    urls = sys.modules.get("config.urls")
    if urls is not None:
        importlib.reload(urls)
        clear_url_caches()


# ---------------------------------------------------------------------------
# Holder-pattern URLConf (per Decision 6 + rev3 R4 + rev3 R5)
# ---------------------------------------------------------------------------
#
# The temp URLConf binds at module load, but the schema is built per-test
# (after the autouse reload clears the registry). The holder lets the URLConf's
# view read whichever schema the current test's fixture stored.


_current: dict[str, object | None] = {"schema": None}


def _graphql_view(request):
    """Closure-bound view that reads ``_current['schema']`` per request."""
    schema = _current["schema"]
    assert schema is not None, "_build_test_schema fixture must run before any /graphql/ request"
    return GraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql/", _graphql_view)]


# ---------------------------------------------------------------------------
# Per-test schema fixture (runs AFTER the autouse reload — rev3 R4)
# ---------------------------------------------------------------------------


@pytest.fixture
def _build_test_schema(_reload_project_schema_for_acceptance_tests):
    """Build the per-test schema against the freshly-reloaded ``BookType``."""
    # IMPORTANT: import ``BookType`` HERE (inside the fixture body), not at
    # module top — module-level imports of ``apps.library.schema.BookType``
    # would hold stale class objects after each autouse reload cycle
    # (per the ``examples/fakeshop/test_query/test_library_api.py::_reload_project_schema_for_acceptance_tests #"tests must not module-level import classes"``
    # invariant). The fixture's
    # dependency on _reload_project_schema_for_acceptance_tests ensures
    # the import runs AFTER reload.
    from apps.library.schema import BookType  # freshly-reloaded class

    @strawberry.type
    class _MultiDbTestQuery:
        @strawberry.field
        def books_on_shard_b(self, info: Info) -> list[BookType]:
            return models.Book.objects.using("shard_b").select_related(
                "shelf__branch",
            )

    _current["schema"] = strawberry.Schema(
        query=_MultiDbTestQuery,
        extensions=[DjangoOptimizerExtension()],
    )
    yield
    _current["schema"] = None


# ---------------------------------------------------------------------------
# Seed helper — full Branch → Shelf → Book chain per alias (rev2 H9)
# ---------------------------------------------------------------------------


def _seed_book_chain(alias: str, *, title: str) -> "models.Book":
    """Seed a full ``Branch → Shelf → Book`` chain on ``alias``.

    ``Branch.name`` is ``unique=True`` (``examples/fakeshop/apps/library/models.py::Branch #"name = models.TextField(unique=True)"``), so the
    branch / shelf field values are varied by ``title`` to keep two calls on
    the same alias from colliding when a test seeds multiple chains.
    """
    branch = models.Branch.objects.using(alias).create(
        name=f"Branch-{alias}-{title}",
        city="Boston",
    )
    shelf = models.Shelf.objects.using(alias).create(
        code=f"S-{alias}-{title}",
        topic="Test",
        branch=branch,
    )
    return models.Book.objects.using(alias).create(
        title=title,
        circulation_status=models.Book.CirculationStatus.AVAILABLE,
        shelf=shelf,
    )


# ---------------------------------------------------------------------------
# Tests — live /graphql/ HTTP against the sharded layout
# ---------------------------------------------------------------------------


@pytest.mark.django_db(databases=["default", "shard_b"])
def test_using_shard_b_resolver_returns_rows_seeded_on_shard_b(_build_test_schema):
    """Seeded ``shard_b`` rows are visible through a ``.using('shard_b')`` resolver."""
    _seed_book_chain("shard_b", title="A")
    _seed_book_chain("shard_b", title="B")

    query = """
      query {
        booksOnShardB {
          title
          shelf { code branch { name } }
        }
      }
    """

    client = Client()
    with override_settings(ROOT_URLCONF=__name__):
        clear_url_caches()
        try:
            response = client.post(
                "/graphql/",
                data={"query": query},
                content_type="application/json",
            )
        finally:
            clear_url_caches()

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    titles = {b["title"] for b in payload["data"]["booksOnShardB"]}
    assert titles == {"A", "B"}


@pytest.mark.django_db(databases=["default", "shard_b"])
def test_cross_shard_isolation_default_rows_not_visible_via_shard_b_resolver(_build_test_schema):
    """A chain seeded on ``default`` is invisible to a ``.using('shard_b')`` resolver."""
    _seed_book_chain("default", title="default-only")
    _seed_book_chain("shard_b", title="shard-b-only")

    # Query selects the full select_related("shelf__branch") chain so the
    # optimizer's `.only(...)` projection is compatible with the resolver's
    # pinned select_related shape (Django raises FieldError when a field is
    # both deferred and traversed via select_related). Pinning only `title`
    # would conflict with the spec-pinned resolver shape at line 393 / 545.
    query = """
      query {
        booksOnShardB {
          title
          shelf { code branch { name } }
        }
      }
    """

    client = Client()
    with override_settings(ROOT_URLCONF=__name__):
        clear_url_caches()
        try:
            response = client.post(
                "/graphql/",
                data={"query": query},
                content_type="application/json",
            )
        finally:
            clear_url_caches()

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    titles = {b["title"] for b in payload["data"]["booksOnShardB"]}
    assert titles == {"shard-b-only"}
    assert "default-only" not in titles  # explicit negative pin
