"""Package-tier tests for ``testing/client.py`` - DB-free mechanics only (spec-043).

Placement per spec-043 Decision 11 and the feedback's live-first split: every
case that drives a real ``/graphql/`` request (the sync raising direction on a
live invalid selection, the ``AsyncTestClient`` paths, and the unittest family
end to end) lives in ``examples/fakeshop/test_query/test_client_api.py`` so it is
earned live per the ``test_query/README.md`` coverage rule. This file owns only
what a live request cannot (or need not) pin:

- the endpoint-resolution precedence ladder (per-call > constructor > class attr
  > settings key > default), proven against recording transports;
- the owned builder's uniform path-keyed map rule and its placeholder guards -
  the empty-``variables`` guard and the per-path walker that fails a malformed
  ``files=`` call at the source (the top-level, nested, list-index, and
  not-a-placeholder shapes fakeshop carries no live vehicle for);
- ``files={}`` staying a plain JSON post, and ``extensions`` surfacing decoded
  or ``None``;
- the assertion helpers' FAILURE directions against canned responses (their
  PASSING directions ride the live unittest tests);
- the mixin's ``self.client`` delegation and endpoint rungs against a recording
  stand-in;
- the ``__test__ = False`` collection guard and the export surface.

Every test here is DB-free: no schema reload, no ``seed_data``, no real request.
"""

import json
import unittest

import pytest
from django.http import HttpResponse
from django.test import override_settings

import django_strawberry_framework
from django_strawberry_framework import testing as testing_root
from django_strawberry_framework.testing import (
    AsyncTestClient,
    GraphQLTestMixin,
    Response,
    TestClient,
)

# ---------------------------------------------------------------------------
# Recording / canned transport doubles: a recording ``request()`` (or ``post``)
# override proves TARGET SELECTION and body shape directly, so a mechanics test
# never depends on a live view. Every test in this file is DB-free.
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
# The owned builder's raising directions (the empty-variables guard and the
# per-path placeholder walker) and the uniform map rule.
# ---------------------------------------------------------------------------


def test_files_without_variables_raises_the_placeholder_guard():
    """``files=`` without variables raises before any request, for ``None`` and ``{}`` alike.

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


def test_files_placeholder_missing_top_level_path_raises():
    """A top-level ``files=`` path with no matching key in variables raises, naming the path.

    The owned builder validates each ``files=`` path against ``variables`` before
    emitting the multipart ``map`` (spec-043 Decision 9): a path whose key is
    absent at the top level is a malformed call, failed at the source rather than
    emitted as a spec-invalid envelope the server has to diagnose later.
    """
    with pytest.raises(AssertionError, match="no key"):
        TestClient().query(
            "mutation($file: Upload!) { up }",
            variables={"other": None},
            files={"file": object()},
        )


def test_files_placeholder_missing_nested_key_raises():
    """A nested ``files=`` path whose leaf key is absent raises, naming the path."""
    with pytest.raises(AssertionError, match="no key"):
        TestClient().query(
            "mutation($data: SpecInput!) { up }",
            variables={"data": {}},
            files={"data.image": object()},
        )


def test_files_placeholder_cannot_descend_into_a_scalar_raises():
    """A ``files=`` path that descends through a non-container value raises."""
    with pytest.raises(AssertionError, match="cannot descend"):
        TestClient().query(
            "mutation($data: SpecInput!) { up }",
            variables={"data": None},
            files={"data.image": object()},
        )


@pytest.mark.parametrize(
    "index",
    [
        "x",
        "\u00b2",
        "\u0663",
        "01",
        "-1",
        "1" * 5000,
    ],
)
def test_files_placeholder_noncanonical_list_index_raises(index):
    """Every invalid ``object-path`` list index uses the placeholder guard's error type."""
    with pytest.raises(AssertionError, match="valid index"):
        TestClient().query(
            "mutation($tags: [Upload!]!) { up }",
            variables={
                "tags": [
                    None,
                    None,
                    None,
                    None,
                ],
            },
            files={f"tags.{index}": object()},
        )


def test_files_placeholder_out_of_range_list_index_raises():
    """A list-path index past the end of the list raises."""
    with pytest.raises(AssertionError, match="valid index"):
        TestClient().query(
            "mutation($tags: [Upload!]!) { up }",
            variables={"tags": [None]},
            files={"tags.5": object()},
        )


def test_files_placeholder_present_but_not_none_raises():
    """A ``files=`` path resolving to a non-``None`` value raises: it must be a placeholder."""
    with pytest.raises(AssertionError, match="None placeholder"):
        TestClient().query(
            "mutation($file: Upload!) { up }",
            variables={"file": "not-a-placeholder"},
            files={"file": object()},
        )


def test_files_key_shadowing_a_reserved_envelope_field_raises():
    """A ``files=`` key named ``operations`` or ``map`` raises instead of clobbering the envelope.

    Each ``files`` key becomes a multipart field name and ``**files`` spreads
    last, so a key colliding with the reserved ``operations`` / ``map`` envelope
    fields would overwrite them and post a corrupt body the server has to
    diagnose. The owned ``_build_body`` rejects it at the source. A valid ``None``
    placeholder is present at that path, so it is the reserved-field guard firing,
    not the placeholder walker - and the raise beats any request being posted.
    """
    for reserved in ("operations", "map"):
        with pytest.raises(AssertionError, match="reserved multipart envelope"):
            TestClient().query(
                "mutation($x: Upload!) { up }",
                variables={reserved: None},
                files={reserved: object()},
            )


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
    so the top-level and list-index paths are pinned here against the builder
    directly, alongside ``operationName`` landing INSIDE the JSON-encoded
    ``operations`` field. Each path also resolves to a ``None`` placeholder, so
    this doubles as the walker's success path (dict, list, and top-level).
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


def test_build_body_sends_empty_operation_name_instead_of_dropping_it():
    """An explicit ``operation_name=""`` rides the body; the default ``None`` omits the key.

    The owned ``_build_body`` gates ``operationName`` on ``is not None``, not
    truthiness: a provided empty string is a malformed value sent for the server
    to reject with a real GraphQL error, not silently reinterpreted as "no
    operation name" (the module's fail-at-the-source posture). ``None`` (the
    default) omits the key entirely - never an ``operationName: null`` the server
    would reject as a validation error against a multi-operation document. No
    fakeshop live vehicle can pin the *absence* of the key, so it is pinned
    against the builder directly here.
    """
    client = TestClient()

    with_empty = client._build_body("{ x }", None, None, "")
    assert with_empty["operationName"] == ""

    absent = client._build_body("{ x }", None, None, None)
    assert "operationName" not in absent


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
# proven against the recording stand-in; the rungs are proven end-to-end live).
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
# The assertion helpers' FAILURE directions, against canned Responses (their
# PASSING directions are earned live in test_query/test_client_api.py).
# ---------------------------------------------------------------------------


class AssertionHelperFailureDirectionTests(GraphQLTestMixin, unittest.TestCase):
    """Both assertion helpers FAIL in the right direction, carrying the decoded content.

    Canned Responses, no live request: the helpers are pure functions over a
    typed :class:`Response`, so their FAILURE directions are pinned against
    constructed responses here (spec-043 Decision 11 + the feedback's live-first
    split). Composed over ``unittest.TestCase`` (not the DB-backed
    ``GraphQLTestCase``) so this file stays DB-free.
    """

    @staticmethod
    def _canned(*, errors, data, status_code=200):
        raw = _CannedJSONResponse({"data": data})
        raw.status_code = status_code
        return Response(errors=errors, data=data, extensions=None, response=raw)

    def test_assert_response_no_errors_fails_on_an_errors_response(self):
        res = self._canned(errors=[{"message": "nope"}], data=None)
        with self.assertRaises(AssertionError) as ctx:
            self.assertResponseNoErrors(res)
        self.assertIn("nope", str(ctx.exception))  # the decoded errors ride the message

    def test_assert_response_no_errors_fails_readably_on_a_non_200_without_errors(self):
        # A transport failure whose JSON body has no ``errors`` key: the status
        # check fails and the message still carries the decoded content (both
        # fields), never a bare ``None``.
        res = self._canned(errors=None, data={"detail": "boom"}, status_code=500)
        with self.assertRaises(AssertionError) as ctx:
            self.assertResponseNoErrors(res)
        self.assertIn("boom", str(ctx.exception))

    def test_assert_response_has_errors_fails_on_a_clean_response(self):
        res = self._canned(errors=None, data={"__typename": "Query"})
        with self.assertRaises(AssertionError):
            self.assertResponseHasErrors(res)
