"""Package-tier tests for ``testing/client.py`` - only what a live request cannot pin (spec-043).

Placement per spec-043 Decision 11, honoring the ``test_query/README.md``
coverage rule: the helper's sync request shapes (the JSON happy path and typed
``Response``, the ``assert_no_errors=False`` errors outcome, ``operation_name``
dispatch, ``login()`` scoping, and the nested multipart upload) are earned LIVE
by the converted ``examples/fakeshop/test_query/`` suites
(``test_uploads_api.py``, ``test_products_api.py``) and are deliberately NOT
restated here. This file owns the rest:

- the ``assert_no_errors=True`` raising direction and the
  ``files=``-with-``variables=None`` guard (the helper's own behaviours - a
  live suite asserts outcomes, not the helper's raising);
- the endpoint-resolution precedence ladder (per-call > constructor > class
  attr > settings key > default) - the live suites all use the default;
- the owned builder's uniform path-keyed map rule for the shapes no fakeshop
  mutation carries a live vehicle for (a top-level file, a list index);
- the ``AsyncTestClient`` real-request paths (the live tier is sync-only);
- the unittest family's mechanics (``self.client`` delegation, ``GRAPHQL_URL``,
  both assertion helpers' failure directions, the transaction case);
- the ``__test__ = False`` collection guard and the export surface.

Request-driving tests follow the acceptance suites' schema-reload discipline
(the ``fresh_project_schema`` fixture delegates to the single-sited
``schema_reload.reload_all_project_schemas``) and the ``seed_data`` rule. The
async tests depend on ``transactional_db``: ``django.test.AsyncClient`` runs
the (sync) GraphQL view on asgiref's executor thread, whose separate SQLite
connection cannot see rows seeded inside a non-transactional test's
uncommitted transaction. Mechanics tests (precedence, the builder map, the
guards, the exports) are DB-free and unmarked.
"""

import json

import pytest
from apps.products.models import Category
from apps.products.services import create_users, seed_data
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import override_settings
from django.urls import include, path, resolve
from schema_reload import reload_all_project_schemas
from strawberry import relay

import django_strawberry_framework
from django_strawberry_framework import testing as testing_root
from django_strawberry_framework.testing import (
    AsyncTestClient,
    GraphQLTestCase,
    GraphQLTestMixin,
    GraphQLTransactionTestCase,
    Response,
    TestClient,
)

# ---------------------------------------------------------------------------
# Probe URLconf (Test 11): ``/alt/`` delegates to whatever the freshly reloaded
# ``/graphql/`` view is, so the GRAPHQL_URL / per-call rungs are proven by a
# POSITIVE hit on the real schema view, not an exception shape. Inert unless a
# test overrides ``ROOT_URLCONF`` to this module.
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


@pytest.fixture
def fresh_project_schema():
    """Rebuild the FULL project schema before a request-driving test.

    The acceptance suites' schema-reload discipline (``test_query/README.md``):
    delegates to the single-sited ``schema_reload.reload_all_project_schemas``
    so a package-test ``registry.clear()`` on the same worker cannot leave the
    aggregate ``config.schema`` build raising a ``LazyType`` ``KeyError``.
    """
    reload_all_project_schemas()


@pytest.fixture
def seeded_catalog(fresh_project_schema, transactional_db):
    """``seed_data(1)`` after the reload; transactional so the async view's thread sees rows."""
    seed_data(1)


@pytest.fixture
def permitted_writer(fresh_project_schema, transactional_db):
    """A ``create_users`` user granted the explicit ``add_item`` perm + a category GlobalID.

    Mirrors the live suite's ``_login_with_perm`` discipline: ``view_item_1`` is
    NOT a superuser, so the ``DjangoModelPermission`` codename check runs rather
    than the superuser short-circuit; the user is re-fetched after the grant to
    drop the stale per-request permission cache.
    """
    from django.contrib.auth.models import Permission

    create_users(1)
    seed_data(1)
    user_model = get_user_model()
    user = user_model.objects.get(username="view_item_1")
    user.user_permissions.add(
        Permission.objects.get(codename="add_item", content_type__app_label="products"),
    )
    user = user_model.objects.get(pk=user.pk)  # drop the stale perm cache
    category = Category.objects.order_by("pk").first()
    category_gid = str(relay.GlobalID(type_name="products.category", node_id=str(category.pk)))
    return user, category_gid


# ---------------------------------------------------------------------------
# Canned-transport doubles (Test 8's blessed shape): a recording ``request()``
# override proves TARGET SELECTION directly, so the test cannot accidentally
# pass on a ``/percall/`` 404 or non-JSON body. Mechanics only - every
# request-driving test in this file hits the real fakeshop view.
# ---------------------------------------------------------------------------


class _CannedJSONResponse(HttpResponse):
    """A minimal 200 response carrying the ``.json()`` the client's ``_decode`` calls."""

    def __init__(self, payload=None):
        super().__init__()
        self._payload = payload if payload is not None else {"data": {"ok": True}}

    def json(self):
        return self._payload


class _RecordingTestClient(TestClient):
    """A ``TestClient`` whose transport records the effective URL and returns canned JSON."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_urls = []

    def request(
        self,
        body,
        headers=None,
        files=None,
        *,
        url=None,
    ):
        self.seen_urls.append(url if url is not None else self.path)
        return _CannedJSONResponse()


class _RecordingDjangoClient:
    """A ``django.test.Client`` stand-in recording ``post`` targets for the mixin probe."""

    def __init__(self):
        self.posts = []

    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        return _CannedJSONResponse()


class _MixinProbe(GraphQLTestMixin):
    """A bare mixin composition proving ``query()`` reads only ``self.client``."""

    def __init__(self):
        self.client = _RecordingDjangoClient()


# ---------------------------------------------------------------------------
# Endpoint resolution (Tests 6-8) - DB-free mechanics.
# ---------------------------------------------------------------------------


def test_default_endpoint_is_graphql_with_trailing_slash():
    """Test 6: no settings key -> ``"/graphql/"`` (fakeshop's mount, slash kept)."""
    assert TestClient().path == "/graphql/"


def test_settings_key_sets_the_endpoint_and_the_default_restores_after_override():
    """Test 7: the ``TESTING_ENDPOINT`` key is read at construction, on both clients.

    The second half pins the ``conf.py`` ``setting_changed`` receiver: after the
    override exits, a fresh client is back on the default - the settings read is
    live, not baked in at import.
    """
    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"TESTING_ENDPOINT": "/alt/"}):
        assert TestClient().path == "/alt/"
        assert AsyncTestClient().path == "/alt/"  # the async twin rides the same ladder
    assert TestClient().path == "/graphql/"


def test_constructor_path_outranks_the_settings_key():
    """Test 8 (constructor rung): an explicit ``path=`` wins over the settings key.

    The resolved endpoint is also forwarded to the engine base, so the
    inherited ``url`` attribute mirrors ``path`` instead of reading the base's
    ``"/graphql/"`` default while ``path`` reads the real endpoint.
    """
    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"TESTING_ENDPOINT": "/settings/"}):
        client = TestClient("/explicit/")
    assert client.path == "/explicit/"
    assert client.url == "/explicit/"  # the base's attribute, kept in sync


def test_per_call_url_outranks_the_constructor_and_never_persists():
    """Test 8 (per-call rung): ``query(url=)`` wins for ONE request; ``self.path`` is untouched.

    The recording transport receives ``/percall/`` for the overridden call, the
    stored ``path`` is unchanged afterward (the non-persistence guarantee), and
    the next un-overridden call falls back to the constructor path.
    """
    client = _RecordingTestClient("/constructor/")

    res = client.query("{ ok }", url="/percall/")
    assert client.seen_urls == ["/percall/"]
    assert client.path == "/constructor/"
    assert isinstance(res, Response)
    assert res.data == {"ok": True}
    assert isinstance(res.response, _CannedJSONResponse)

    client.query("{ ok }")
    assert client.seen_urls == ["/percall/", "/constructor/"]


# ---------------------------------------------------------------------------
# The helper's own raising directions (the package-tier halves of scenarios
# 2 and 5) and the owned builder's map rule.
# ---------------------------------------------------------------------------


def test_assert_no_errors_default_raises_with_the_errors_list(fresh_project_schema):
    """Scenario 2's raising direction: the default gate raises, message carries the errors.

    A real fakeshop request (an invalid selection is a validation error - no DB
    is touched): under the default ``assert_no_errors=True`` the errors response
    raises ``AssertionError`` (an explicit raise, so the gate also holds under
    ``python -O``) instead of returning, and the errors list rides the message.
    """
    client = TestClient()
    with pytest.raises(AssertionError) as excinfo:
        client.query("{ nope }")
    assert "nope" in str(excinfo.value)


def test_files_without_variables_raises_the_placeholder_guard():
    """Scenario 5's guard direction: ``files=`` without variables raises before any request.

    The owned ``_build_body``'s explicit ``AssertionError`` (not the engine
    base's bare ``assert``): the multipart ``map`` needs variable paths to point
    at, so the guard fires before a request is ever posted - for ``None`` and
    for an empty dict alike (an empty ``variables`` has no placeholder either,
    and silently omitting the ``variables`` key while ``map`` points into it
    would be a spec-invalid multipart envelope).
    """
    with pytest.raises(AssertionError, match="placeholder"):
        TestClient().query("mutation { x }", files={"file": object()})
    with pytest.raises(AssertionError, match="placeholder"):
        TestClient().query("mutation { x }", variables={}, files={"file": object()})


def test_empty_files_dict_is_a_plain_json_post():
    """``files={}`` is falsy on every switch: JSON body, JSON content type, JSON decode.

    The three ``files`` gates (body build, content-type selection, decode mode)
    all use truthiness, so an empty dict cannot produce the mixed envelope of a
    multipart body posted as JSON.
    """
    transport = _RecordingDjangoClient()
    res = TestClient(client=transport).query("{ ok }", variables={"a": 1}, files={})

    url, kwargs = transport.posts[0]
    assert url == "/graphql/"
    assert kwargs["content_type"] == "application/json"
    assert kwargs["data"] == {"query": "{ ok }", "variables": {"a": 1}}  # no operations/map
    assert res.data == {"ok": True}


def test_build_body_map_rule_is_uniform_across_path_shapes():
    """The owned builder's one rule - ``map[key] = ["variables." + key]`` - for every shape.

    The nested input-object shape is earned live (``test_uploads_api.py``); no
    fakeshop mutation takes a TOP-LEVEL ``Upload`` variable or a list of them,
    so the top-level and list-index paths (scenario 5's rounding shapes) are
    pinned here against the builder directly, alongside ``operationName``
    landing INSIDE the JSON-encoded ``operations`` field.
    """
    client = TestClient()
    f_top, f_nested, f_listed = object(), object(), object()

    body = client._build_body(
        "mutation Up($file: Upload!, $data: SpecInput!, $tags: [Upload!]!) { up }",
        {"file": None, "data": {"image": None}, "tags": [None, None]},
        {"file": f_top, "data.image": f_nested, "tags.0": f_listed},
        "Up",
    )

    operations = json.loads(body["operations"])
    assert operations["operationName"] == "Up"
    assert operations["variables"] == {"file": None, "data": {"image": None}, "tags": [None, None]}
    assert json.loads(body["map"]) == {
        "file": ["variables.file"],
        "data.image": ["variables.data.image"],
        "tags.0": ["variables.tags.0"],
    }
    # The file parts ride the body under their path keys, identity-preserved.
    assert body["file"] is f_top
    assert body["data.image"] is f_nested
    assert body["tags.0"] is f_listed


def test_response_extensions_surface_decoded_or_none():
    """Scenario 1's ``extensions`` leg: the decoded value when present, ``None`` when absent.

    The engine ``_decode`` hands back the raw JSON body; the package
    ``Response`` construction reads all three GraphQL response members with
    ``.get``, so an ``extensions`` member surfaces typed and an absent one
    reads ``None`` (fakeshop's live responses carry none, hence the canned
    transport here).
    """

    class _ExtensionsTransport(_RecordingDjangoClient):
        def post(self, url, **kwargs):
            self.posts.append((url, kwargs))
            return _CannedJSONResponse({"data": {"ok": True}, "extensions": {"traceId": "t-1"}})

    with_extensions = TestClient(client=_ExtensionsTransport()).query("{ ok }")
    assert with_extensions.extensions == {"traceId": "t-1"}

    without = TestClient(client=_RecordingDjangoClient()).query("{ ok }")
    assert without.extensions is None


# ---------------------------------------------------------------------------
# Surface guards (Tests 13-14) - DB-free.
# ---------------------------------------------------------------------------


def test_clients_carry_the_pytest_collection_guard():
    """Test 13: ``__test__ is False`` on both ``Test*``-named classes.

    Without the guard, pytest collects the imported class as a suite and warns -
    a hard failure under the repo's ``-W error`` posture the moment any test
    module imports the client.
    """
    assert TestClient.__test__ is False
    assert AsyncTestClient.__test__ is False


def test_export_surface_is_the_testing_root_not_the_package_root():
    """Test 14: the six names live on ``testing``'s ``__all__``; the package root has none.

    The no-root-export contract is pinned by its two accurate shapes (spec-043
    Decision 4): ``getattr`` on the root raises ``AttributeError`` (the PEP 562
    ``__getattr__`` seam), and the ``from ... import`` STATEMENT form surfaces
    that as ``ImportError`` - Python's import machinery converts the module
    ``__getattr__``'s ``AttributeError`` for ``from ... import ...``.
    """
    exported = (
        "TestClient",
        "AsyncTestClient",
        "Response",
        "GraphQLTestMixin",
        "GraphQLTestCase",
        "GraphQLTransactionTestCase",
    )
    for name in exported:
        assert name in testing_root.__all__
        assert getattr(testing_root, name) is not None

    root_name = "TestClient"  # via a variable so the probe is a real dynamic getattr
    assert not hasattr(django_strawberry_framework, root_name)
    with pytest.raises(AttributeError):
        getattr(django_strawberry_framework, root_name)
    with pytest.raises(ImportError):
        from django_strawberry_framework import TestClient  # noqa: F401


# ---------------------------------------------------------------------------
# Mixin mechanics (the ``self.client`` delegation and endpoint rungs 3-5,
# proven against the recording stand-in; Test 11 proves the rungs end-to-end).
# ---------------------------------------------------------------------------


def test_mixin_query_delegates_to_the_test_cases_own_client():
    """The mixin's delegate ``TestClient`` posts through ``self.client``, JSON-typed.

    The state-free contract: the mixin reads only ``self.client`` and its own
    class attributes, so login/cookie state configured on the case's client
    applies to every ``self.query(...)`` call.
    """
    probe = _MixinProbe()
    res = probe.query("{ ok }")

    url, kwargs = probe.client.posts[0]
    assert url == "/graphql/"  # rung 5: the default, GRAPHQL_URL unset
    assert kwargs["content_type"] == "application/json"
    assert isinstance(res, Response)
    assert res.data == {"ok": True}


def test_mixin_endpoint_rungs_class_attr_settings_and_per_call():
    """Rungs 1, 3, and 4 through the mixin: per-call > ``GRAPHQL_URL`` > settings key.

    The mixin constructs its delegate per call, so a settings override observed
    mid-class behaves predictably (rung 4 is read at call time, not import time).
    """

    class _AltProbe(_MixinProbe):
        GRAPHQL_URL = "/classattr/"

    alt = _AltProbe()
    alt.query("{ ok }")
    assert alt.client.posts[-1][0] == "/classattr/"  # rung 3 beats settings/default

    alt.query("{ ok }", url="/percall/")
    assert alt.client.posts[-1][0] == "/percall/"  # rung 1 beats the class attr

    plain = _MixinProbe()
    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"TESTING_ENDPOINT": "/settings/"}):
        plain.query("{ ok }")
    assert plain.client.posts[-1][0] == "/settings/"  # rung 4 with GRAPHQL_URL unset


# ---------------------------------------------------------------------------
# The async client (Tests 9-10): real requests through Django's in-process
# ``AsyncClientHandler`` against the reloaded fakeshop schema.
# ---------------------------------------------------------------------------


async def test_async_query_happy_path_and_raise_direction(seeded_catalog):
    """Test 9: the awaited transport, the async decode, and the package ``Response``.

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
    """Test 10: the force-login/logout bracket through ``async with client.login(user)``.

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


# ---------------------------------------------------------------------------
# The unittest family (Tests 11-12): TestCase-shaped, in-file subclasses.
# ---------------------------------------------------------------------------


class GraphQLTestCaseEndToEndTests(GraphQLTestCase):
    """Test 11: ``self.query(...)`` + both helpers + the per-call rung, end to end."""

    def setUp(self):
        super().setUp()
        reload_all_project_schemas()
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

    @override_settings(ROOT_URLCONF="tests.testing.test_client")
    def test_per_call_url_routes_to_the_probe_endpoint(self):
        # Rung 1 end-to-end: a positive hit on the real schema view mounted at
        # the probe URLconf's ``/alt/``, not an exception shape.
        res = self.query(
            "query Items { allItems(first: 1) { edges { node { name } } } }",
            url="/alt/",
        )
        self.assertResponseNoErrors(res)
        self.assertTrue(res.data["allItems"]["edges"])


@override_settings(ROOT_URLCONF="tests.testing.test_client")
class GraphQLTestCaseClassAttrEndpointTests(GraphQLTestCase):
    """Test 11's ``GRAPHQL_URL`` rung: the subclass pins its endpoint by assignment."""

    GRAPHQL_URL = "/alt/"

    def setUp(self):
        super().setUp()
        reload_all_project_schemas()
        seed_data(1)

    def test_class_attr_endpoint_hits_the_real_view(self):
        res = self.query("query Items { allItems(first: 1) { edges { node { name } } } }")
        self.assertResponseNoErrors(res)
        self.assertTrue(res.data["allItems"]["edges"])


class AssertionHelperFailureDirectionTests(GraphQLTestCase):
    """Test 12: both helpers FAIL in the right direction, carrying the decoded content."""

    def setUp(self):
        super().setUp()
        reload_all_project_schemas()

    def test_assert_response_no_errors_fails_on_an_errors_response(self):
        res = self.query("{ nope }")
        with self.assertRaises(AssertionError) as ctx:
            self.assertResponseNoErrors(res)
        self.assertIn("nope", str(ctx.exception))  # the decoded errors ride the message

    def test_assert_response_no_errors_fails_readably_on_a_non_200_without_errors(self):
        # A transport failure whose JSON body has no ``errors`` key: the status
        # check fails and the message still carries the decoded content (both
        # fields), never a bare ``None``.
        raw = _CannedJSONResponse({"data": {"detail": "boom"}})
        raw.status_code = 500
        res = Response(errors=None, data={"detail": "boom"}, extensions=None, response=raw)
        with self.assertRaises(AssertionError) as ctx:
            self.assertResponseNoErrors(res)
        self.assertIn("boom", str(ctx.exception))

    def test_assert_response_has_errors_fails_on_a_clean_response(self):
        res = self.query("{ __typename }")
        with self.assertRaises(AssertionError):
            self.assertResponseHasErrors(res)


class GraphQLTransactionTestCaseSmokeTests(GraphQLTransactionTestCase):
    """Test 12's second half: the ``(Mixin, TransactionTestCase)`` combination is wired."""

    def setUp(self):
        super().setUp()
        reload_all_project_schemas()
        seed_data(1)

    def test_one_clean_seeded_query_round_trips(self):
        res = self.query("query Items { allItems(first: 1) { edges { node { name } } } }")
        self.assertResponseNoErrors(res)
        self.assertTrue(res.data["allItems"]["edges"])
