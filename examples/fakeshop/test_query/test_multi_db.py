"""Live GraphQL HTTP tests for sharded resolver isolation and multi-database debug capture.

Scope (per spec Goals item 3 + Test plan ``### examples/fakeshop/test_query/test_multi_db.py``):
three live ``/graphql/`` HTTP tests against the sharded fakeshop layout.

- Test 1 - seeding rows on ``shard_b`` and reading them through ``/graphql/``
  via a ``.using("shard_b")`` root resolver returns the seeded rows.
- Test 2 - cross-shard isolation: a chain seeded on ``default`` is NOT
  visible through a ``using("shard_b")`` resolver.
- Test 3 - a debug-enabled probe captures SQL from ``shard_b`` with the
  correct database alias and restores every connection's debug-cursor state.

Critical contract pins (do not violate without an explicit spec revision):

- Module-level ``pytest.skip(allow_module_level=True)`` gate per Decision 6
  (NOT ``pytest.mark.skipif`` - the env var changes ``config.settings.DATABASES``
  at module import time; mark evaluation happens after import).
- ``@pytest.mark.django_db(databases=["default", "shard_b"])`` per rev2 H8
  on each test (pytest-django blocks non-default-DB access otherwise).
- Full ``Branch -> Shelf -> Book`` chain per alias via ``_seed_book_chain``
  per rev2 H9 (``Book.shelf`` and ``Shelf.branch`` are non-null FKs).
- Live ``/graphql/`` HTTP exclusively via ``django.test.Client.post(...)``
  per rev2 H7 - NO in-process ``execute_sync(...)`` alternative.
- Schema built inside a per-test fixture that depends on the shared module
  reload - the holder pattern below defers schema construction until after
  the registry clear so the test sees freshly-reloaded ``BookType``.
- ``override_settings(ROOT_URLCONF=__name__)`` per rev3 R5 with
  ``clear_url_caches()`` on enter AND in teardown.
"""

# ``os`` owns the import-time environment gate below.

import os

import pytest

if os.environ.get("FAKESHOP_SHARDED") != "1":
    pytest.skip(
        "requires FAKESHOP_SHARDED=1 (the sharded DATABASES layout)",
        allow_module_level=True,
    )

# Below this line, FAKESHOP_SHARDED=1 is set and ``shard_b`` is in DATABASES.
# These imports run only after the skip check passes - otherwise
# ``from apps.library import models`` would crash in single-DB mode where
# ``shard_b`` is not registered in DATABASES.

import strawberry
from apps.library import models
from django.db import connections
from django.test import Client, override_settings
from django.urls import clear_url_caches, path
from graphql_client import assert_graphql_success as _graphql_data
from strawberry.django.views import GraphQLView
from strawberry.types import Info

from django_strawberry_framework import DjangoOptimizerExtension, strawberry_config
from django_strawberry_framework.extensions import DjangoDebugExtension
from django_strawberry_framework.testing import TestClient

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
# Per-test schema fixture (runs AFTER the autouse reload - rev3 R4)
# ---------------------------------------------------------------------------


@pytest.fixture
def _build_test_schema(_reload_project_schema_for_acceptance_tests):
    """Build the per-test schema against the freshly-reloaded ``BookType``."""
    # IMPORTANT: import ``BookType`` HERE (inside the fixture body), not at
    # module top - module-level imports of ``apps.library.schema.BookType``
    # would hold stale class objects after each autouse reload cycle
    # (per the shared ``test_query/conftest.py::_reload_project_schema_for_acceptance_tests``
    # invariant). The dependency ensures the import runs after that reload.
    from apps.library.schema import BookType  # freshly-reloaded class

    @strawberry.type
    class _MultiDbTestQuery:
        @strawberry.field
        def books_on_shard_b(self, info: Info) -> list[BookType]:
            return models.Book.objects.using("shard_b").select_related(
                "shelf__branch",
            )

    optimizer = DjangoOptimizerExtension()
    _current["schema"] = strawberry.Schema(
        query=_MultiDbTestQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    yield
    _current["schema"] = None


@pytest.fixture
def _build_debug_test_schema(_reload_project_schema_for_acceptance_tests):
    """The debug-enabled sibling of ``_build_test_schema`` (spec-044 scenario 16).

    Same freshly-reloaded ``BookType`` / ``.using("shard_b")`` resolver shape,
    plus ``DjangoDebugExtension`` as the CLASS beside the optimizer's factory -
    the canonical consumer wiring under test.
    """
    from apps.library.schema import BookType  # freshly-reloaded class

    @strawberry.type
    class _MultiDbDebugTestQuery:
        @strawberry.field
        def books_on_shard_b(self, info: Info) -> list[BookType]:
            return models.Book.objects.using("shard_b").select_related(
                "shelf__branch",
            )

    optimizer = DjangoOptimizerExtension()
    _current["schema"] = strawberry.Schema(
        query=_MultiDbDebugTestQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer, DjangoDebugExtension],
    )
    yield
    _current["schema"] = None


# ---------------------------------------------------------------------------
# Seed helper - full Branch -> Shelf -> Book chain per alias (rev2 H9)
# ---------------------------------------------------------------------------


def _seed_book_chain(alias: str, *, title: str) -> "models.Book":
    """Seed a full ``Branch -> Shelf -> Book`` chain on ``alias``.

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
# Tests - live /graphql/ HTTP against the sharded layout
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
            data = _graphql_data(query, client=client)
        finally:
            clear_url_caches()

    titles = {b["title"] for b in data["booksOnShardB"]}
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
    # would conflict with the spec-pinned resolver shape at
    # spec-019 #"return models.Book.objects.using(\"shard_b\").select_related(\"shelf__branch\")"
    # / spec-019 #"A `_build_test_schema` per-test fixture".
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
            data = _graphql_data(query, client=client)
        finally:
            clear_url_caches()

    titles = {b["title"] for b in data["booksOnShardB"]}
    assert titles == {"shard-b-only"}
    assert "default-only" not in titles  # explicit negative pin


@pytest.mark.django_db(databases=["default", "shard_b"])
def test_debug_extension_captures_shard_b_alias_rows(_build_debug_test_schema):
    """The real multi-database capture proof (spec-044 Test plan scenario 16).

    A live query routed to ``shard_b`` through a debug-enabled probe schema
    reports a captured row with ``alias == "shard_b"`` and the correct vendor,
    and BOTH configured aliases restore their prior ``force_debug_cursor``
    values - the per-alias contract must not rest solely on
    ``alias == "default"`` assertions plus fakes.
    """
    _seed_book_chain("shard_b", title="DebugShard")
    prior_flags = {
        database_connection.alias: database_connection.force_debug_cursor
        for database_connection in connections.all()
    }

    query = """
      query {
        booksOnShardB {
          title
          shelf { code branch { name } }
        }
      }
    """

    client = TestClient()
    with override_settings(ROOT_URLCONF=__name__):
        clear_url_caches()
        try:
            res = client.query(query)
        finally:
            clear_url_caches()

    assert [book["title"] for book in res.data["booksOnShardB"]] == ["DebugShard"]
    payload = (res.extensions or {})["debug"]
    shard_rows = [row for row in payload["sql"] if row["alias"] == "shard_b"]
    assert shard_rows, payload["sql"]
    assert shard_rows[0]["vendor"] == connections["shard_b"].vendor
    assert shard_rows[0]["isSelect"] is True
    assert payload["exceptions"] == []
    for database_connection in connections.all():
        assert database_connection.force_debug_cursor is prior_flags[database_connection.alias]


# ---------------------------------------------------------------------------
# BETA-055: write-alias pinning for generated mutations (live sharded HTTP)
# ---------------------------------------------------------------------------
#
# The write tests drive the PROJECT schema (config.schema - the real products
# write surface over DjangoSchema) under a router whose READ and WRITE answers
# diverge for the products app: reads route to ``default``, writes to
# ``shard_b``. The pipeline must pin EVERYTHING - locate, relation visibility,
# the write, the re-fetch, and the envelope rollback - to the ONE write alias,
# so the shard_b twin of a same-pk row pair is the one affected and the
# default twin never is.


class _ProductsWriteToShardBRouter:
    """Route products reads to ``default`` and products writes to ``shard_b``.

    Only the products app is routed; auth/session/user machinery stays on
    ``default`` so login and permissions behave normally.
    """

    def db_for_read(self, model, **hints):
        if model._meta.app_label != "products":
            return None
        # Honor the instance hint (the standard primary/replica router shape,
        # per Django's own router conventions): a relation loaded FROM a
        # shard_b-materialized instance reads beside it. Fresh reads with no
        # instance context go to the divergent read alias - the divergence the
        # pipeline's pinning must override.
        instance = hints.get("instance")
        instance_db = getattr(getattr(instance, "_state", None), "db", None)
        if instance_db is not None:
            return instance_db
        return "default"

    def db_for_write(self, model, **hints):
        if model._meta.app_label == "products":
            return "shard_b"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return True


@pytest.fixture
def _project_schema(_reload_project_schema_for_acceptance_tests):
    """Serve the freshly-reloaded PROJECT schema (the real write surface)."""
    from config.schema import schema as project_schema

    _current["schema"] = project_schema
    yield
    _current["schema"] = None


def _seed_same_pk_item_pair(pk_base: int) -> None:
    """Seed a same-pk ``Category``/``Item`` pair on BOTH aliases.

    The pk collision is the point: an alias-pinning bug that lets any pipeline
    step slip to the read alias would still find A row, so only differing
    per-alias field values can prove which alias each step really used.
    """
    from apps.products import models as product_models

    for alias in ("default", "shard_b"):
        category = product_models.Category.objects.using(alias).create(
            pk=pk_base,
            name=f"pin-category-{alias}-{pk_base}",
        )
        product_models.Item.objects.using(alias).create(
            pk=pk_base,
            name=f"pin-item-{alias}",
            category=category,
        )


def _login_products_writer(*codenames: str) -> Client:
    from apps.products.services import create_users
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Permission

    create_users(1)
    user = get_user_model().objects.get(username="staff_1")
    for codename in codenames:
        user.user_permissions.add(
            Permission.objects.get(codename=codename, content_type__app_label="products"),
        )
    client = Client()
    client.force_login(get_user_model().objects.get(pk=user.pk))
    return client


_UPDATE_ITEM_MUTATION = """
mutation($id: ID!, $d: ItemPartialInput!) {
  updateItem(id: $id, data: $d) {
    node { name category { name } }
    errors { field messages }
  }
}
"""


def _item_gid(pk: int) -> str:
    import strawberry.relay as relay_module

    return str(relay_module.GlobalID(type_name="products.item", node_id=str(pk)))


@pytest.mark.django_db(databases=["default", "shard_b"], transaction=True)
def test_mutation_write_pins_locate_write_and_refetch_to_the_write_alias(_project_schema):
    """Under a divergent read/write router the WHOLE update pipeline rides ``shard_b``.

    The locate (visibility), the write, and the post-write re-fetch must all use
    the router's WRITE answer - a step that slipped to the read alias would
    either miss the row, write the wrong twin, or re-fetch stale data. The
    response's ``category`` relation also proves the relation ride-along: it
    renders the SHARD_B category's name.
    """
    from apps.products import models as product_models

    _seed_same_pk_item_pair(90001)
    client = _login_products_writer("change_item", "view_category")

    with override_settings(
        ROOT_URLCONF=__name__,
        DATABASE_ROUTERS=[_ProductsWriteToShardBRouter()],
    ):
        clear_url_caches()
        try:
            res = TestClient(client=client).query(
                _UPDATE_ITEM_MUTATION,
                variables={"id": _item_gid(90001), "d": {"name": "pinned-write"}},
            )
        finally:
            clear_url_caches()

    payload = res.data["updateItem"]
    assert payload["errors"] == []
    assert payload["node"]["name"] == "pinned-write"
    # The re-fetch and its relation came from shard_b (the write alias)...
    assert payload["node"]["category"]["name"] == "pin-category-shard_b-90001"
    # ...the shard_b twin was written, and the default twin never touched.
    assert product_models.Item.objects.using("shard_b").get(pk=90001).name == "pinned-write"
    assert product_models.Item.objects.using("default").get(pk=90001).name == "pin-item-default"


@pytest.mark.django_db(databases=["default", "shard_b"], transaction=True)
def test_mutation_validation_envelope_rolls_back_on_the_write_alias(_project_schema):
    """A validation-envelope failure rolls back on ``shard_b`` (the pinned alias).

    Two shard_b items share a category; renaming one to the other's name trips
    ``unique_item_per_category`` as the in-band envelope - and the pinned
    ``set_rollback`` must discard any partial work on the WRITE alias, leaving
    both twins untouched on both aliases.
    """
    from apps.products import models as product_models

    _seed_same_pk_item_pair(90011)
    sibling = product_models.Item.objects.using("shard_b").create(
        name="pin-sibling",
        category_id=90011,
    )
    client = _login_products_writer("change_item", "view_category")

    with override_settings(
        ROOT_URLCONF=__name__,
        DATABASE_ROUTERS=[_ProductsWriteToShardBRouter()],
    ):
        clear_url_caches()
        try:
            res = TestClient(client=client).query(
                _UPDATE_ITEM_MUTATION,
                variables={"id": _item_gid(sibling.pk), "d": {"name": "pin-item-shard_b"}},
                assert_no_errors=False,
            )
        finally:
            clear_url_caches()

    payload = res.data["updateItem"]
    assert payload["node"] is None
    assert payload["errors"], payload
    # Nothing changed on either alias.
    assert product_models.Item.objects.using("shard_b").get(pk=sibling.pk).name == "pin-sibling"
    assert product_models.Item.objects.using("default").get(pk=90011).name == "pin-item-default"
