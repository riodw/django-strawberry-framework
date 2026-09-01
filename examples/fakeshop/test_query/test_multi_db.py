"""Live GraphQL HTTP tests for sharded resolver isolation and multi-database debug capture.

Scope (per spec Goals item 3 + Test plan ``### examples/fakeshop/test_query/test_multi_db.py``):
three live ``/graphql/`` HTTP tests against the sharded fakeshop layout.

- Seeding rows on ``shard_b`` and reading them through ``/graphql/`` via a
  ``.using("shard_b")`` root resolver returns the seeded rows.
- Cross-shard isolation: a chain seeded on ``default`` is NOT visible through a
  ``using("shard_b")`` resolver.
- A debug-enabled probe captures SQL from ``shard_b`` with the correct database
  alias and restores every connection's debug-cursor state.

Critical contract pins (do not violate without an explicit spec revision):

- Module-level ``pytest.skip(allow_module_level=True)`` gate per Decision 6
  (NOT ``pytest.mark.skipif`` - the env var changes ``config.settings.DATABASES``
  at module import time; mark evaluation happens after import).
- ``@pytest.mark.django_db(databases=["default", "shard_b"])`` on each test
  (pytest-django blocks non-default-DB access otherwise).
- Full ``Branch -> Shelf -> Book`` chain per alias via ``_seed_book_chain``
  (``Book.shelf`` and ``Shelf.branch`` are non-null FKs).
- Live ``/graphql/`` HTTP exclusively via ``django.test.Client.post(...)`` - NO
  in-process ``execute_sync(...)`` alternative.
- Schema built inside a per-test fixture that depends on the shared module
  reload - the holder pattern below defers schema construction until after
  the registry clear so the test sees freshly-reloaded ``BookType``.
- ``override_settings(ROOT_URLCONF=__name__)`` with
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
from strawberry import relay
from strawberry.django.views import GraphQLView
from strawberry.types import Info

from django_strawberry_framework import (
    DjangoMutation,
    DjangoMutationField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.extensions import DjangoDebugExtension
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import TestClient
from django_strawberry_framework.testing.relay import global_id_for

_UPDATE_BOOK_TITLE_VALIDATOR_MUTATION = """
mutation($id: ID!, $d: AliasValidatedBookSerializerPartialInput!) {
  updateBookTitleWithAliasValidator(id: $id, data: $d) {
    node { title }
    errors { field messages }
  }
}
"""

# ---------------------------------------------------------------------------
# Holder-pattern URLConf (per Decision 6)
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


# TODO(spec-050 slice 4): Add the sharded-only post-OrderSet routing rejection
# to this existing holder mount, never to the default single-DB suite.
#
# Pseudocode:
#
# - Inside a per-test fixture imported after the schema reload, use monkeypatch
#   to replace the already-bound ``BranchOrder.apply_sync`` public override for
#   this test only. It receives a queryset explicitly routed to ``shard_b`` and
#   maliciously returns a same-model queryset routed to ``default``; do not
#   create a throwaway DjangoType or rewrite its finalized sidecar.
# - Expose that type through a test-local DjangoListField resolver returning the
#   real ``.using("shard_b")`` source, finalize only through the established
#   fixture discipline, and mount it through ``_current``.
# - Seed distinguishable rows on both aliases with inline ``using(alias).create``
#   calls. Request non-null orderBy over live HTTP and assert an actionable
#   post-order ``ConfigurationError`` names ``OrderSet.apply_sync`` and the
#   routing mismatch before either alias fetches rows for completion.
# - Keep the module-level ``FAKESHOP_SHARDED=1`` gate and
#   ``django_db(databases=["default", "shard_b"])`` marker; clear the holder and
#   URL caches in teardown exactly like the existing fixtures.


# ---------------------------------------------------------------------------
# Per-test schema fixture (runs AFTER the autouse reload)
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
    plus ``DjangoDebugExtension`` beside the optimizer's factory - the canonical
    consumer wiring under test.

    The debug extension is spelled as the acknowledgement factory
    (``lambda: DjangoDebugExtension(allow_unsafe_production=True)``) rather than
    a bare class entry: the extension fails closed under ``settings.DEBUG``
    false (spec-048 Decision 5) and pytest-django holds the setting false for
    the whole suite, so a bare class entry would publish nothing and this
    per-alias capture proof would assert against an absent payload. The factory
    still constructs one fresh instance per operation, which is the property the
    class entry was chosen for.
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
        extensions=[lambda: optimizer, lambda: DjangoDebugExtension(allow_unsafe_production=True)],
    )
    yield
    _current["schema"] = None


@pytest.fixture
def _build_loan_filter_test_schema(_reload_project_schema_for_acceptance_tests):
    """Build a per-test schema exposing a ``.using('shard_b')`` Loan LIST field with ``LoanFilter``.

    The shard-alias twin of ``_build_test_schema`` for the row-preserving
    relational-leaf predicate proof (spec-060 Part 1): the
    resolver applies the PRODUCTION ``LoanFilter`` (whose deep
    ``book__loans__patron__email`` leaf compiles to a correlated ``EXISTS``) over a
    queryset pinned to ``shard_b``, so the predicate primitive's ``.using(queryset.db)``
    pin must carry the ``EXISTS`` subquery to that alias. ``LoanFilter`` / ``LoanType``
    are imported inside the fixture body (like ``BookType`` above) so the freshly
    reloaded classes are used after the autouse registry clear.
    """
    from apps.library import filters as library_filters
    from apps.library.schema import LoanType

    from django_strawberry_framework.filters import filter_input_type

    @strawberry.type
    class _LoanFilterShardQuery:
        @strawberry.field
        def loans_on_shard_b(
            self,
            info: Info,
            filter: filter_input_type(library_filters.LoanFilter) | None = None,  # noqa: A002
        ) -> list[LoanType]:
            queryset = models.Loan.objects.using("shard_b").order_by("id")
            if filter is not None:
                queryset = library_filters.LoanFilter.apply_sync(filter, queryset, info)
            return queryset

    optimizer = DjangoOptimizerExtension()
    _current["schema"] = strawberry.Schema(
        query=_LoanFilterShardQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    yield
    _current["schema"] = None


# ---------------------------------------------------------------------------
# Seed helper - full Branch -> Shelf -> Book chain per alias
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


def _seed_loan_relation_graph_on_shard_b() -> dict[str, int]:
    """Seed a small row-preserving relational-leaf graph on ``shard_b``.

    A ``shared_book`` carries two loans whose patrons both have "Cardio" emails,
    plus an ``other_book`` with a single non-matching ("Ortho") loan. The deep
    leaf ``book__loans__patron__email icontains "Cardio"`` matches a root loan
    when its BOOK has any loan to a "Cardio" patron - so both shared-book loans
    match (each once, row-preserving) and the other-book loan does not. Returns
    the captured pks (``unique_open_loan_per_book_patron`` forbids repeating a
    ``(book, patron)`` pair, so patrons are distinct per loan).
    """
    branch = models.Branch.objects.using("shard_b").create(name="Shard Medtrics", city="Boston")
    shelf = models.Shelf.objects.using("shard_b").create(
        code="SHARD-MED-1",
        topic="ward",
        branch=branch,
    )
    shared_book = models.Book.objects.using("shard_b").create(shelf=shelf, title="Shard Shared")
    other_book = models.Book.objects.using("shard_b").create(shelf=shelf, title="Shard Other")
    patron_a = models.Patron.objects.using("shard_b").create(name="Shard A", email="Cardio A")
    patron_b = models.Patron.objects.using("shard_b").create(name="Shard B", email="Cardio B")
    patron_c = models.Patron.objects.using("shard_b").create(name="Shard C", email="Ortho")
    relation_a = models.Loan.objects.using("shard_b").create(
        book=shared_book,
        patron=patron_a,
        note="checkout",
    )
    relation_b = models.Loan.objects.using("shard_b").create(
        book=shared_book,
        patron=patron_b,
        note="checkout",
    )
    unrelated = models.Loan.objects.using("shard_b").create(
        book=other_book,
        patron=patron_c,
        note="checkout",
    )
    return {"relation_a": relation_a.pk, "relation_b": relation_b.pk, "unrelated": unrelated.pk}


@pytest.mark.django_db(databases=["default", "shard_b"])
def test_row_preserving_relational_leaf_predicate_executes_on_shard_b_alias(
    _build_loan_filter_test_schema,
):
    """The correlated-``EXISTS`` relational-leaf predicate runs on the ``shard_b`` alias.

    The production ``LoanFilter`` deep leaf ``book__loans__patron__email`` (spelled
    ``bookLoansPatronEmail`` on the wire) is applied over a ``.using('shard_b')``
    queryset. The predicate primitive pins its correlated ``EXISTS`` subquery to
    ``queryset.db``, so the whole filter - outer root scan AND the ``EXISTS``
    re-entry - must execute on ``shard_b``: the seeded shard rows return
    row-preserved (both shared-book loans, each once), and the captured ``shard_b``
    SQL carries the ``EXISTS`` with no framework ``DISTINCT``.
    """
    from django.db import connection as default_connection
    from django.test.utils import CaptureQueriesContext

    pks = _seed_loan_relation_graph_on_shard_b()

    client = TestClient()
    with override_settings(ROOT_URLCONF=__name__):
        clear_url_caches()
        try:
            with (
                CaptureQueriesContext(connections["shard_b"]) as shard_captured,
                CaptureQueriesContext(default_connection) as default_captured,
            ):
                res = client.query(
                    """
                    query {
                      loansOnShardB(filter: { bookLoansPatronEmail: { iContains: "Cardio" } }) {
                        id
                      }
                    }
                    """,
                )
        finally:
            clear_url_caches()

    # Row-preserving: exactly both shared-book loans, id-ordered, each once.
    assert [loan["id"] for loan in res.data["loansOnShardB"]] == [
        pks["relation_a"],
        pks["relation_b"],
    ]

    # The correlated EXISTS re-entry ran on shard_b (the .using(queryset.db) pin),
    # never on default.
    shard_loan_sql = [
        query["sql"]
        for query in shard_captured.captured_queries
        if "library_loan" in query["sql"].lower() and "EXISTS(" in query["sql"].upper()
    ]
    assert shard_loan_sql, shard_captured.captured_queries
    for sql in shard_loan_sql:
        assert "SELECT DISTINCT" not in sql.upper()
    assert not [
        query["sql"]
        for query in default_captured.captured_queries
        if "library_loan" in query["sql"].lower()
    ], default_captured.captured_queries


# ---------------------------------------------------------------------------
# Mutation atomicity (shipped 0.0.14): write-alias pinning for generated mutations (live sharded HTTP)
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
def test_custom_nodeid_mutation_resolves_real_pk_on_write_alias():
    """A custom NodeID mutation resolves its non-pk payload on ``shard_b``.

    ``CategoryNode.name`` is the Relay id, while the mutation locate still needs
    the row's real integer pk. The target exists only on the write alias and the
    router sends fresh reads to ``default``; resolving the NodeID through the
    default manager would produce an in-band not-found error before the locate.
    """
    from apps.products import models as product_models

    registry.clear()
    category_pk = 92021
    product_models.Category.objects.using("default").create(
        pk=category_pk,
        name="read-alias-category",
        description="default untouched",
    )
    target = product_models.Category.objects.using("shard_b").create(
        pk=category_pk,
        name="write-alias-category",
        description="before",
    )

    class CategoryNode(DjangoType):
        name: relay.NodeID[str]

        class Meta:
            model = product_models.Category
            fields = ("id", "name", "description")
            interfaces = (relay.Node,)
            primary = True

    class UpdateCategory(DjangoMutation):
        class Meta:
            model = product_models.Category
            operation = "update"

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class Mutation:
        update_category = DjangoMutationField(UpdateCategory)

    finalize_django_types()
    _current["schema"] = DjangoSchema(
        query=Query,
        mutation=Mutation,
        config=strawberry_config(),
        extensions=[],
    )
    client = _login_products_writer("change_category")
    query = """
      mutation($id: ID!, $d: CategoryPartialInput!) {
        updateCategory(id: $id, data: $d) {
          node { id description }
          errors { field messages }
        }
      }
    """
    try:
        with override_settings(
            ROOT_URLCONF=__name__,
            DATABASE_ROUTERS=[_ProductsWriteToShardBRouter()],
        ):
            clear_url_caches()
            try:
                response = TestClient(client=client).query(
                    query,
                    variables={
                        "id": global_id_for(CategoryNode, target.name),
                        "d": {"description": "write-alias-updated"},
                    },
                )
            finally:
                clear_url_caches()
    finally:
        _current["schema"] = None

    assert response.data["updateCategory"]["errors"] == []
    assert response.data["updateCategory"]["node"]["description"] == "write-alias-updated"
    assert (
        product_models.Category.objects.using("shard_b").get(pk=category_pk).description
        == "write-alias-updated"
    )
    assert (
        product_models.Category.objects.using("default").get(pk=category_pk).description
        == "default untouched"
    )


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


# ---------------------------------------------------------------------------
# Serializer-flavor write-alias pinning (the DRF hardening pass)
# ---------------------------------------------------------------------------
#
# The serializer twin of the model-flavor pinning tests above: the SERIALIZER
# pipeline's locate, relation decode, DRF's second relation lookup (the scoped
# field queryset), the save, the re-fetch, and the envelope rollback must all
# ride the router's ONE write answer. Routed on the library app so the project
# schema's ``updateBookGenresViaSerializer`` (a ``SerializerMutation`` with an
# M2M ``genres`` relation) is the surface under test.


class _LibraryWriteToShardBRouter:
    """Route library reads to ``default`` and library writes to ``shard_b``."""

    def db_for_read(self, model, **hints):
        if model._meta.app_label != "library":
            return None
        instance = hints.get("instance")
        instance_db = getattr(getattr(instance, "_state", None), "db", None)
        if instance_db is not None:
            return instance_db
        return "default"

    def db_for_write(self, model, **hints):
        if model._meta.app_label == "library":
            return "shard_b"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return True


def _seed_same_pk_book_pair(pk_base: int) -> None:
    """Seed a same-pk ``Branch -> Shelf -> Book`` chain on BOTH aliases.

    Same rationale as ``_seed_same_pk_item_pair``: only per-alias field values
    can prove which alias each pipeline step really used.
    """
    for alias in ("default", "shard_b"):
        branch = models.Branch.objects.using(alias).create(
            pk=pk_base,
            name=f"ser-branch-{alias}-{pk_base}",
            city="Boston",
        )
        shelf = models.Shelf.objects.using(alias).create(
            pk=pk_base,
            code=f"ser-shelf-{alias}",
            topic="Test",
            branch=branch,
        )
        models.Book.objects.using(alias).create(
            pk=pk_base,
            title=f"ser-book-{alias}",
            shelf=shelf,
        )


_UPDATE_BOOK_GENRES_MUTATION = """
mutation($id: ID!, $d: BookGenresSerializerPartialInput!) {
  updateBookGenresViaSerializer(id: $id, data: $d) {
    node { title }
    errors { field messages }
  }
}
"""


def _library_gid(type_name: str, pk: int) -> str:
    import strawberry.relay as relay_module

    return str(relay_module.GlobalID(type_name=type_name, node_id=str(pk)))


@pytest.mark.django_db(databases=["default", "shard_b"], transaction=True)
def test_serializer_mutation_pins_locate_relation_save_and_refetch_to_write_alias(
    _project_schema,
):
    """Under a divergent read/write router the WHOLE serializer update rides ``shard_b``.

    The genre attached exists ONLY on ``shard_b``, so the relation decode, DRF's
    second relation lookup (the pinned, visibility-scoped field queryset), and the
    M2M write all had to run on the write alias - any step slipping to the read
    alias would fail to find the genre. The shard_b book twin is the one written;
    the default twin (same pk) is untouched.
    """
    _seed_same_pk_book_pair(91001)
    shard_genre = models.Genre.objects.using("shard_b").create(
        pk=91001,
        name="ser-genre-shard-b-only",
    )

    with override_settings(
        ROOT_URLCONF=__name__,
        DATABASE_ROUTERS=[_LibraryWriteToShardBRouter()],
    ):
        clear_url_caches()
        try:
            res = TestClient().query(
                _UPDATE_BOOK_GENRES_MUTATION,
                variables={
                    "id": _library_gid("library.book", 91001),
                    "d": {
                        "title": "ser-pinned-write",
                        "genres": [_library_gid("library.genre", shard_genre.pk)],
                    },
                },
            )
        finally:
            clear_url_caches()

    payload = res.data["updateBookGenresViaSerializer"]
    assert payload["errors"] == []
    assert payload["node"]["title"] == "ser-pinned-write"
    shard_book = models.Book.objects.using("shard_b").get(pk=91001)
    assert shard_book.title == "ser-pinned-write"
    assert list(shard_book.genres.values_list("name", flat=True)) == ["ser-genre-shard-b-only"]
    default_book = models.Book.objects.using("default").get(pk=91001)
    assert default_book.title == "ser-book-default"
    assert default_book.genres.count() == 0


@pytest.mark.django_db(databases=["default", "shard_b"], transaction=True)
def test_serializer_unique_validator_reads_write_alias(_project_schema):
    """A default-only collision does not poison validation of the shard_b update."""
    _seed_same_pk_book_pair(91006)
    default_shelf = models.Shelf.objects.using("default").get(pk=91006)
    models.Book.objects.using("default").create(
        title="validator-default-only-collision",
        shelf=default_shelf,
    )

    with override_settings(
        ROOT_URLCONF=__name__,
        DATABASE_ROUTERS=[_LibraryWriteToShardBRouter()],
    ):
        clear_url_caches()
        try:
            res = TestClient().query(
                _UPDATE_BOOK_TITLE_VALIDATOR_MUTATION,
                variables={
                    "id": _library_gid("library.book", 91006),
                    "d": {"title": "validator-default-only-collision"},
                },
            )
        finally:
            clear_url_caches()

    payload = res.data["updateBookTitleWithAliasValidator"]
    assert payload["errors"] == []
    assert payload["node"]["title"] == "validator-default-only-collision"
    assert (
        models.Book.objects.using("shard_b").get(pk=91006).title
        == "validator-default-only-collision"
    )
    assert models.Book.objects.using("default").get(pk=91006).title == "ser-book-default"


@pytest.mark.django_db(databases=["default", "shard_b"], transaction=True)
def test_serializer_mutation_envelope_rolls_back_on_the_write_alias(_project_schema):
    """A serializer save-time failure rolls back on ``shard_b`` (the pinned alias).

    Renaming the shard_b book to a same-shelf sibling's title trips the
    ``unique_book_title_per_shelf`` constraint at ``save()`` as the in-band
    ``"__all__"`` envelope, and the pinned rollback leaves both twins untouched
    on both aliases.
    """
    _seed_same_pk_book_pair(91011)
    shard_shelf = models.Shelf.objects.using("shard_b").get(pk=91011)
    models.Book.objects.using("shard_b").create(
        title="ser-sibling",
        shelf=shard_shelf,
    )

    with override_settings(
        ROOT_URLCONF=__name__,
        DATABASE_ROUTERS=[_LibraryWriteToShardBRouter()],
    ):
        clear_url_caches()
        try:
            res = TestClient().query(
                _UPDATE_BOOK_GENRES_MUTATION,
                variables={
                    "id": _library_gid("library.book", 91011),
                    "d": {"title": "ser-sibling"},
                },
                assert_no_errors=False,
            )
        finally:
            clear_url_caches()

    payload = res.data["updateBookGenresViaSerializer"]
    assert payload["node"] is None
    assert payload["errors"], payload
    # Nothing changed on either alias.
    assert models.Book.objects.using("shard_b").get(pk=91011).title == "ser-book-shard_b"
    assert models.Book.objects.using("default").get(pk=91011).title == "ser-book-default"
