"""Live /graphql/ multi-database cooperation tests against the sharded fakeshop layout.

TODO(spec-019 Slice 2, examples/fakeshop/test_query/test_multi_db.py — NEW):
pre-staged scaffold per ``docs/spec-019-multi_db-0_0_7.md`` Slice 2.
Worker 2 replaces the ``raise NotImplementedError`` body in each test
below with the pseudocode that follows it, and confirms the harness
shape (holder + view + URLConf + autouse reload fixture + per-test
schema fixture + seed helper) matches Decision 6 + Decision 7 verbatim.

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

from django_strawberry_framework import DjangoOptimizerExtension  # noqa: E402
from django_strawberry_framework.registry import registry  # noqa: E402


# ---------------------------------------------------------------------------
# Autouse reload fixture (copied verbatim from test_library_api.py:17-43)
# ---------------------------------------------------------------------------
#
# TODO(spec-019 Slice 2 — Decision 7): copy this fixture body verbatim from
# ``examples/fakeshop/test_query/test_library_api.py:17-43``. Per Decision 7
# the copy is intentional (the "do not pre-emptively factor" boundary —
# conftest extraction is a follow-up card when 3+ files need it). Same
# docstring, same module-reload sequence (apps.library.schema →
# config.schema → config.urls). The fixture is autouse so it runs before
# every test in this module.


@pytest.fixture(autouse=True)
def _reload_project_schema_for_acceptance_tests():
    """Recreate imported DjangoType classes if package tests cleared the registry."""
    # TODO(spec-019 Slice 2): copy body from test_library_api.py:17-43 verbatim.
    #
    # Expected body (paste into here unchanged from the source):
    #
    #     registry.clear()
    #     library_schema = sys.modules.get("apps.library.schema")
    #     if library_schema is None:
    #         importlib.import_module("apps.library.schema")
    #     else:
    #         importlib.reload(library_schema)
    #
    #     project_schema = sys.modules.get("config.schema")
    #     if project_schema is None:
    #         importlib.import_module("config.schema")
    #     else:
    #         importlib.reload(project_schema)
    #
    #     urls = sys.modules.get("config.urls")
    #     if urls is not None:
    #         importlib.reload(urls)
    #         clear_url_caches()
    raise NotImplementedError("TODO(spec-019 Slice 2 — copy fixture body from test_library_api.py:17-43)")


# ---------------------------------------------------------------------------
# Holder-pattern URLConf (per Decision 6 + rev3 R4 + rev3 R5)
# ---------------------------------------------------------------------------
#
# TODO(spec-019 Slice 2 — Decision 6 holder pattern): the temp URLConf binds
# at module load, but the schema is built per-test (after the autouse reload
# clears the registry). The holder lets the URLConf's view read whichever
# schema the current test's fixture stored.
#
# Pseudocode shape (per spec Decision 6 ``**The holder-pattern URLConf**``
# block lines 367-391):

_current: dict[str, object | None] = {"schema": None}


def _graphql_view(request):
    """Closure-bound view that reads ``_current['schema']`` per request."""
    # TODO(spec-019 Slice 2): delegate to GraphQLView.as_view(schema=...).
    #
    # Pseudocode:
    #
    #     schema = _current["schema"]
    #     assert schema is not None, (
    #         "_build_test_schema fixture must run before any /graphql/ request"
    #     )
    #     return GraphQLView.as_view(schema=schema)(request)
    raise NotImplementedError("TODO(spec-019 Slice 2 — graphql view body)")


urlpatterns = [path("graphql/", _graphql_view)]


# ---------------------------------------------------------------------------
# Per-test schema fixture (runs AFTER the autouse reload — rev3 R4)
# ---------------------------------------------------------------------------


@pytest.fixture
def _build_test_schema(_reload_project_schema_for_acceptance_tests):
    """Build the per-test schema against the freshly-reloaded ``BookType``."""
    # TODO(spec-019 Slice 2 — per-test schema build, rev3 R4):
    #
    # IMPORTANT: import ``BookType`` HERE (inside the fixture body), not at
    # module top — module-level imports of ``apps.library.schema.BookType``
    # would hold stale class objects after each autouse reload cycle
    # (per the test_library_api.py:24-26 invariant). The fixture's
    # dependency on _reload_project_schema_for_acceptance_tests ensures
    # the import runs AFTER reload.
    #
    # Pseudocode:
    #
    #     from apps.library.schema import BookType  # freshly-reloaded class
    #
    #     @strawberry.type
    #     class _MultiDbTestQuery:
    #         @strawberry.field
    #         def books_on_shard_b(self, info) -> list[BookType]:
    #             return models.Book.objects.using("shard_b").select_related(
    #                 "shelf__branch",
    #             )
    #
    #     _current["schema"] = strawberry.Schema(
    #         query=_MultiDbTestQuery,
    #         extensions=[DjangoOptimizerExtension()],
    #     )
    #     yield
    #     _current["schema"] = None  # teardown
    raise NotImplementedError("TODO(spec-019 Slice 2 — _build_test_schema body)")


# ---------------------------------------------------------------------------
# Seed helper — full Branch → Shelf → Book chain per alias (rev2 H9)
# ---------------------------------------------------------------------------


def _seed_book_chain(alias: str, *, title: str) -> "models.Book":
    """Seed a full ``Branch → Shelf → Book`` chain on ``alias``."""
    # TODO(spec-019 Slice 2 — rev2 H9 seeding contract): both ``Book.shelf``
    # (non-null FK to Shelf at apps/library/models.py:98) and ``Shelf.branch``
    # (non-null FK to Branch at apps/library/models.py:56) require the full
    # upstream chain on the same alias.
    #
    # Pseudocode (per spec Test plan ``**Fixture-chain contract**`` block):
    #
    #     branch = models.Branch.objects.using(alias).create(
    #         name=f"Branch-{alias}",
    #         city="Boston",
    #     )
    #     shelf = models.Shelf.objects.using(alias).create(
    #         code=f"S-{alias}",
    #         topic="Test",
    #         branch=branch,
    #     )
    #     return models.Book.objects.using(alias).create(
    #         title=title,
    #         circulation_status=models.Book.CirculationStatus.AVAILABLE,
    #         shelf=shelf,
    #     )
    raise NotImplementedError("TODO(spec-019 Slice 2 — _seed_book_chain body)")


# ---------------------------------------------------------------------------
# Tests — live /graphql/ HTTP against the sharded layout
# ---------------------------------------------------------------------------


@pytest.mark.django_db(databases=["default", "shard_b"])
def test_using_shard_b_resolver_returns_rows_seeded_on_shard_b(_build_test_schema):
    """Seeded ``shard_b`` rows are visible through a ``.using('shard_b')`` resolver."""
    # TODO(spec-019 Slice 2 — test 1): seed two chains on shard_b and read
    # them back through /graphql/.
    #
    # Pseudocode (per spec Goals item 3a + Test plan):
    #
    #     _seed_book_chain("shard_b", title="A")
    #     _seed_book_chain("shard_b", title="B")
    #
    #     query = """
    #       query {
    #         booksOnShardB {
    #           title
    #           shelf { code branch { name } }
    #         }
    #       }
    #     """
    #
    #     client = Client()
    #     with override_settings(ROOT_URLCONF=__name__):
    #         clear_url_caches()  # enter the override
    #         try:
    #             response = client.post(
    #                 "/graphql/",
    #                 data={"query": query},
    #                 content_type="application/json",
    #             )
    #         finally:
    #             clear_url_caches()  # teardown
    #
    #     assert response.status_code == 200
    #     payload = response.json()
    #     assert "errors" not in payload, payload
    #     titles = {b["title"] for b in payload["data"]["booksOnShardB"]}
    #     assert titles == {"A", "B"}
    raise NotImplementedError("TODO(spec-019 Slice 2 — test 1 body)")


@pytest.mark.django_db(databases=["default", "shard_b"])
def test_cross_shard_isolation_default_rows_not_visible_via_shard_b_resolver(_build_test_schema):
    """A chain seeded on ``default`` is invisible to a ``.using('shard_b')`` resolver."""
    # TODO(spec-019 Slice 2 — test 2): seed independent chains on default
    # and shard_b; assert only shard_b rows appear in the response.
    #
    # Pseudocode (per spec Goals item 3b + Test plan):
    #
    #     _seed_book_chain("default", title="default-only")
    #     _seed_book_chain("shard_b", title="shard-b-only")
    #
    #     query = """
    #       query {
    #         booksOnShardB { title }
    #       }
    #     """
    #
    #     client = Client()
    #     with override_settings(ROOT_URLCONF=__name__):
    #         clear_url_caches()
    #         try:
    #             response = client.post(
    #                 "/graphql/",
    #                 data={"query": query},
    #                 content_type="application/json",
    #             )
    #         finally:
    #             clear_url_caches()
    #
    #     assert response.status_code == 200
    #     payload = response.json()
    #     assert "errors" not in payload, payload
    #     titles = {b["title"] for b in payload["data"]["booksOnShardB"]}
    #     assert titles == {"shard-b-only"}
    #     assert "default-only" not in titles  # explicit negative pin
    raise NotImplementedError("TODO(spec-019 Slice 2 — test 2 body)")
