"""Live GraphQL HTTP acceptance tests for the spec-043 test-client family.

The request-driving half of ``testing/client.py``'s coverage: every case here
posts a real operation to fakeshop's ``/graphql/`` through the package's own
``TestClient`` / ``AsyncTestClient`` / ``GraphQLTestCase`` family, so the live
behaviour is earned live per the ``test_query/README.md`` coverage rule and
AGENTS.md's live-first mandate. The DB-free mechanics - endpoint precedence, the
owned builder's path-keyed map rule and placeholder guard, the assertion-helper
failure directions against canned responses, and the export / collection guards
- stay in the package tier at ``tests/testing/test_client.py``.

Covered live here: the ``assert_no_errors=True`` raising direction on a real
invalid selection; the ``AsyncTestClient`` happy path (awaited transport, async
decode), its ``login()`` bracket, and its nested two-file multipart upload (the
async color of ``test_uploads_api.py``'s sync upload, so the DoD's "multipart
... on both clients" is earned live on both); and the unittest family end to end
(``self.query(...)``, both assertion helpers' PASSING directions, the per-call
and ``GRAPHQL_URL`` endpoint rungs against a real view, and the
``TransactionTestCase`` combination). The sync ``login()`` bracket and
``operation_name`` dispatch are earned live in ``test_products_api.py``.

The async tests depend on ``transactional_db``: ``django.test.AsyncClient`` runs
the (sync) GraphQL view on asgiref's executor thread, whose separate SQLite
connection cannot see rows seeded inside a non-transactional test's uncommitted
transaction; seeding happens in a sync fixture (not the async body) so the ORM
work never runs in the event loop and raises ``SynchronousOnlyOperation``.
"""

import io

import pytest
from apps.products.models import Category
from apps.products.services import create_users, seed_data
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import include, path, resolve
from strawberry import relay

from django_strawberry_framework.testing import (
    AsyncTestClient,
    GraphQLTestCase,
    GraphQLTransactionTestCase,
    TestClient,
)

# ---------------------------------------------------------------------------
# Probe URLconf: ``/alt/`` delegates to whatever the freshly reloaded
# ``/graphql/`` view is, so the GRAPHQL_URL / per-call rungs are proven by a
# POSITIVE hit on the real schema view, not an exception shape. Inert unless a
# test overrides ``ROOT_URLCONF`` to this module (``__name__``).
# ---------------------------------------------------------------------------


def _alt_graphql_view(request, *args, **kwargs):
    """Delegate ``/alt/`` to the view ``/graphql/`` currently resolves to.

    Resolving at request time (not import time) keeps the probe pointed at the
    schema view the reload fixture just rebuilt.
    """
    match = resolve("/graphql/")
    return match.func(request, *args, **kwargs)


urlpatterns = [path("", include("config.urls")), path("alt/", _alt_graphql_view)]


# The write-auth-gated products mutation the async ``login()`` bracket drives
# (the live sync twin is ``test_products_api.py``'s TestClient bracket test).
_CREATE_ITEM = (
    "mutation($d: ItemInput!) { createItem(data: $d) { node { name } errors { field messages } } }"
)

_ITEMS_QUERY = "query Items($first: Int) { allItems(first: $first) { edges { node { name } } } }"

# The nested two-file upload mutation the async multipart test drives (the sync
# twin lives in ``test_uploads_api.py``); ``attachment`` / ``image`` are both
# required ``Upload!`` fields on the generated ``MediaSpecimenInput``.
_CREATE_MEDIA = """
mutation Create($data: MediaSpecimenInput!) {
  createMediaSpecimen(data: $data) {
    result {
      label
      attachment { name size url }
      image { name width height }
    }
    errors { field messages }
  }
}
"""

# A 5x9 PNG so the live width / height assertions read distinct, deterministic
# values (a square could pass by coincidence) - the same shape as the sync
# upload suite's fixture.
_IMAGE_WIDTH = 5
_IMAGE_HEIGHT = 9


def _png_bytes() -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (_IMAGE_WIDTH, _IMAGE_HEIGHT)).save(buffer, format="PNG")
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# The sync client's raising direction against a real invalid selection.
# ---------------------------------------------------------------------------


def test_assert_no_errors_default_raises_with_the_errors_list():
    """The default gate raises on a real errors response; the message carries the errors.

    A real fakeshop request (an invalid selection is a validation error - no DB
    is touched): under the default ``assert_no_errors=True`` the errors response
    raises ``AssertionError`` (an explicit raise, so the gate holds under
    ``python -O``) instead of returning, and the errors list rides the message.
    The passing (non-raising) direction is the JSON happy path proven across the
    live suites.
    """
    client = TestClient()
    with pytest.raises(AssertionError) as excinfo:
        client.query("{ nope }")
    assert "nope" in str(excinfo.value)


# ---------------------------------------------------------------------------
# The async client: real requests through Django's in-process
# ``AsyncClientHandler`` against the reloaded fakeshop schema.
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_catalog(transactional_db):
    """``seed_data(1)`` in a sync fixture; transactional so the async view's thread sees the rows."""
    seed_data(1)


@pytest.fixture
def permitted_writer(transactional_db):
    """A ``create_users`` user granted ``add_item`` + a category GlobalID, for the async bracket.

    Seeds first (AGENTS.md seed-helper rule), then grants the explicit
    ``add_item`` codename: ``view_item_1`` is NOT a superuser, so the
    ``DjangoModelPermission`` codename check runs rather than the superuser
    short-circuit; the user is re-fetched after the grant to drop the stale
    per-request permission cache. Transactional so the async view's
    executor-thread connection sees the seeded rows.
    """
    create_users(1)
    seed_data(1)
    from django.contrib.auth.models import Permission

    user_model = get_user_model()
    user = user_model.objects.get(username="view_item_1")
    user.user_permissions.add(
        Permission.objects.get(codename="add_item", content_type__app_label="products"),
    )
    user = user_model.objects.get(pk=user.pk)  # drop the stale perm cache
    category = Category.objects.order_by("pk").first()
    category_gid = str(relay.GlobalID(type_name="products.category", node_id=str(category.pk)))
    return user, category_gid


async def test_async_query_happy_path_and_raise_direction(seeded_catalog):
    """The awaited transport, the async decode, and the package ``Response``.

    The same typed-shape assertions as the live sync happy path - ``errors`` /
    ``data`` / the raw ride-along - plus the async color of the
    ``assert_no_errors`` raising direction.
    """
    client = AsyncTestClient()
    res = await client.query(_ITEMS_QUERY, variables={"first": 1})

    assert res.errors is None
    assert len(res.data["allItems"]["edges"]) == 1
    assert res.response.status_code == 200
    assert res.response["Content-Type"].startswith("application/json")

    with pytest.raises(AssertionError) as excinfo:
        await client.query("{ nope }")
    assert "nope" in str(excinfo.value)


async def test_async_login_brackets_the_write_authorized_mutation(permitted_writer):
    """The force-login/logout bracket through ``async with client.login(user)``.

    The sync bracket's async twin (the live sync bracket lives in
    ``test_products_api.py``): the write-auth-gated ``createItem`` is denied
    anonymous (top-level error), succeeds inside the bracket, and is denied
    again after it - the ``sync_to_async``-wrapped session round trip on one
    client instance.
    """
    user, category_gid = permitted_writer
    variables = {"d": {"name": "AsyncBracketWidget", "categoryId": category_gid}}
    client = AsyncTestClient()

    denied = await client.query(_CREATE_ITEM, variables=variables, assert_no_errors=False)
    assert denied.data is None
    assert "Not authorized" in denied.errors[0]["message"]

    async with client.login(user):
        granted = await client.query(_CREATE_ITEM, variables=variables)
        assert granted.data["createItem"]["errors"] == []
        assert granted.data["createItem"]["node"]["name"] == "AsyncBracketWidget"

    denied_again = await client.query(_CREATE_ITEM, variables=variables, assert_no_errors=False)
    assert denied_again.data is None
    assert "Not authorized" in denied_again.errors[0]["message"]


@pytest.fixture
def upload_superuser(transactional_db):
    """A superuser for the async multipart upload, created in a sync fixture.

    ``createMediaSpecimen`` is gated by the default ``add_mediaspecimen``
    ``DjangoModelPermission``; a superuser short-circuits it (write-auth itself
    is exercised on its own in the async ``login()`` bracket above). Created here
    rather than in the async body so the ORM work never runs in the event loop,
    and ``transactional_db`` so the async view's executor-thread SQLite
    connection sees the committed row. The sync twin is a plain
    ``client.login(superuser)`` in
    ``test_uploads_api.py::test_multipart_create_uploads_real_files_over_http``.
    """
    return get_user_model().objects.create_superuser(
        "async_uploader",
        "async_uploader@example.com",
        "pw",
    )


async def test_async_multipart_upload_creates_media_specimen(upload_superuser, tmp_path):
    """The nested two-file multipart upload through ``AsyncTestClient`` (the DoD's "both clients").

    The async color of
    ``test_uploads_api.py::test_multipart_create_uploads_real_files_over_http``:
    the path-keyed ``files=`` contract (``data.attachment`` / ``data.image``,
    each a ``None`` placeholder in ``variables``) combined with
    ``operation_name=``, driven end to end through Django's in-process
    ``AsyncClientHandler`` (ASGI-scope multipart parse -> the sync GraphQL view
    on the executor thread -> JSON response). Before this the "multipart ... on
    both clients" DoD claim was proven live only on the sync client. Assertions
    read the returned ``result`` payload (the saved files read back through the
    resolver) rather than the ORM, so no sync query runs in the event loop.
    """
    variables = {"data": {"label": "async-uploaded", "attachment": None, "image": None}}
    files = {
        "data.attachment": SimpleUploadedFile(
            "async.txt",
            b"async multipart bytes",
            content_type="text/plain",
        ),
        "data.image": SimpleUploadedFile("async.png", _png_bytes(), content_type="image/png"),
    }
    client = AsyncTestClient()

    with override_settings(MEDIA_ROOT=str(tmp_path)):
        async with client.login(upload_superuser):
            res = await client.query(
                _CREATE_MEDIA,
                variables=variables,
                files=files,
                operation_name="Create",
            )

    assert res.response.status_code == 200
    payload = res.data["createMediaSpecimen"]
    assert payload["errors"] == []
    result = payload["result"]
    assert result["label"] == "async-uploaded"
    assert result["attachment"]["name"].endswith("async.txt")
    assert result["attachment"]["size"] == len(b"async multipart bytes")
    assert result["image"]["name"].endswith("async.png")
    assert result["image"]["width"] == _IMAGE_WIDTH
    assert result["image"]["height"] == _IMAGE_HEIGHT


# ---------------------------------------------------------------------------
# The unittest family: TestCase-shaped, in-file subclasses driving real
# ``/graphql/`` requests (the assertion helpers' PASSING directions ride here).
# ---------------------------------------------------------------------------


class GraphQLTestCaseEndToEndTests(GraphQLTestCase):
    """``self.query(...)`` + both helpers + the per-call rung, end to end."""

    def setUp(self):
        super().setUp()
        seed_data(1)

    def test_seeded_query_via_self_client_passes_no_errors(self):
        res = self.query(
            "query Items { allItems(first: 1) { edges { node { name } } } }",
            operation_name="Items",
        )
        self.assertResponseNoErrors(res)
        self.assertEqual(len(res.data["allItems"]["edges"]), 1)

    def test_invalid_query_returns_instead_of_raising_then_has_errors(self):
        # The mixin's flipped ``assert_no_errors=False`` default (graphene
        # parity): the errors response RETURNS for the helper to assert on.
        res = self.query("{ nope }")
        self.assertResponseHasErrors(res)
        self.assertIsNone(res.data)

    @override_settings(ROOT_URLCONF=__name__)
    def test_per_call_url_routes_to_the_probe_endpoint(self):
        # Rung 1 end-to-end: a positive hit on the real schema view mounted at
        # the probe URLconf's ``/alt/``, not an exception shape.
        res = self.query(
            "query Items { allItems(first: 1) { edges { node { name } } } }",
            url="/alt/",
        )
        self.assertResponseNoErrors(res)
        self.assertTrue(res.data["allItems"]["edges"])


@override_settings(ROOT_URLCONF=__name__)
class GraphQLTestCaseClassAttrEndpointTests(GraphQLTestCase):
    """The ``GRAPHQL_URL`` rung: the subclass pins its endpoint by assignment."""

    GRAPHQL_URL = "/alt/"

    def setUp(self):
        super().setUp()
        seed_data(1)

    def test_class_attr_endpoint_hits_the_real_view(self):
        res = self.query("query Items { allItems(first: 1) { edges { node { name } } } }")
        self.assertResponseNoErrors(res)
        self.assertTrue(res.data["allItems"]["edges"])


class GraphQLTransactionTestCaseSmokeTests(GraphQLTransactionTestCase):
    """The ``(Mixin, TransactionTestCase)`` combination is wired end to end."""

    def setUp(self):
        super().setUp()
        seed_data(1)

    def test_one_clean_seeded_query_round_trips(self):
        res = self.query("query Items { allItems(first: 1) { edges { node { name } } } }")
        self.assertResponseNoErrors(res)
        self.assertTrue(res.data["allItems"]["edges"])
