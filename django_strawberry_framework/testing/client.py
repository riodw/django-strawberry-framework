"""Consumer-facing GraphQL test client family - live HTTP test ergonomics (spec-043).

``TestClient`` / ``AsyncTestClient`` are thin wrappers over Django's
``django.test.Client`` / ``django.test.AsyncClient`` that post GraphQL
operations with the right content type, decode the response, and return the
typed :class:`Response` - the ``strawberry_django.test.client`` shape under a
distinctly-ours import path (``django_strawberry_framework.testing``).
``GraphQLTestMixin`` and its two concrete two-line combinations
``GraphQLTestCase`` / ``GraphQLTransactionTestCase`` are the
``graphene_django.utils.testing``-shaped unittest family, delegating to
``TestClient`` so the body building and decoding exist exactly once
(spec-043 Decision 10).

The clients subclass Strawberry's ``strawberry.test.BaseGraphQLTestClient``
(engine-owned over the package's hard ``strawberry-graphql`` dependency - no
soft-dependency machinery, spec-043 Decision 5), reusing its ``_decode``, the
``Response`` field schema, and the abstract ``request()`` seam. The package
owns the sync and async ``query()`` orchestration (both gain ``operation_name=``
and a per-call ``url=`` and return the package :class:`Response` carrying the
raw ``HttpResponse``) and the body/multipart builder (the base's
``_build_multipart_file_map`` returns an empty map for nested input-object
uploads and carries no ``operationName``, spec-043 Decision 9).

Endpoint precedence, highest first (spec-043 Decision 7): per-call
``query(..., url=...)`` > constructor ``TestClient(path=...)`` > class-attr
``GraphQLTestMixin.GRAPHQL_URL`` > ``DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]``
> the ``"/graphql/"`` default.
"""

from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async
from django.test import AsyncClient, Client, TestCase, TransactionTestCase
from strawberry.test import BaseGraphQLTestClient
from strawberry.test.client import Response as _EngineResponse

from django_strawberry_framework.conf import testing_endpoint_setting

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from collections.abc import AsyncIterator, Iterator

    from django.contrib.auth.base_user import AbstractBaseUser

__all__ = [
    "AsyncTestClient",
    "GraphQLTestCase",
    "GraphQLTestMixin",
    "GraphQLTransactionTestCase",
    "Response",
    "TestClient",
]


@dataclass
class Response(_EngineResponse):
    """A decoded GraphQL response: the engine's typed triple plus the raw ``HttpResponse``.

    Subclasses ``strawberry.test.client.Response``, inheriting the ``errors``
    / ``data`` / ``extensions`` field schema (the engine's wire contract), and
    adds ``response`` - the raw ``django.http.HttpResponse`` the operation
    rode - so status, header, and cookie assertions need no separate raw post
    (spec-043 Decision 6). The clients always populate ``response``; the
    ``None`` default is never observed in practice.

    Assert on fields (``res.data``, ``res.errors``,
    ``res.response.status_code``), never on whole ``Response`` objects -
    ``response`` is a live ``HttpResponse``, so whole-object equality is
    meaningless.
    """

    response: Any = None


class TestClient(BaseGraphQLTestClient):
    """A GraphQL test client over ``django.test.Client`` - post, decode, typed result.

    The ``strawberry_django.test.client.TestClient`` shape (spec-043
    Decision 3): construct one (optionally with an explicit endpoint ``path``
    and/or a pre-configured Django test ``client``), call :meth:`query`, and
    assert on the returned :class:`Response`. A GraphQL *mutation* posts
    through :meth:`query` like any operation - there is deliberately no
    ``mutate()`` (neither upstream ships one; spec-043 Decision 6).

    Endpoint resolution happens once, at construction: an explicit ``path``
    wins, else ``DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]``, else
    ``"/graphql/"``. The resolved value is stored as ``self.path`` and never
    mutated; the per-call ``query(..., url=...)`` override routes a single
    request without touching it (spec-043 Decision 7).

    The wrapped Django client stays reachable as ``.client`` for anything the
    helper does not wrap - session-cookie inspection, or passing
    ``client=Client(enforce_csrf_checks=True)`` to test CSRF enforcement
    (Django's default test client skips CSRF checks).
    """

    # Pytest collection guard: the class name matches ``Test*``, so without
    # this pytest tries to collect the class as a test suite and warns - a
    # hard failure under the repo's ``-W error`` posture. Upstream carries the
    # same guard.
    __test__ = False

    def __init__(self, path: str | None = None, client: Client | None = None) -> None:
        resolved = path if path is not None else testing_endpoint_setting()
        self.path = resolved
        # Forward the resolved endpoint as the base's ``url`` too, so the
        # inherited attribute never reads the base default while ``path``
        # reads the real endpoint. ``path`` stays the documented surface.
        super().__init__(client or Client(), resolved)

    @property
    def client(self) -> Client:
        """The wrapped ``django.test.Client`` (the base stores it as ``self._client``)."""
        return self._client

    def query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        headers: dict[str, object] | None = None,
        files: dict[str, object] | None = None,
        assert_no_errors: bool | None = True,
        *,
        operation_name: str | None = None,
        url: str | None = None,
    ) -> Response:
        """Post a GraphQL operation and return the decoded, typed :class:`Response`.

        Mutations and subscriptions-over-POST go through this same method -
        an operation is an operation.

        The first five parameters are positionally byte-compatible with
        ``strawberry_django``'s client; the two keyword-only extensions are
        package-owned (spec-043 Decision 6):

        - ``operation_name=`` - sent as ``operationName`` whenever it is not
          ``None`` (the default ``None`` omits the key entirely - never an
          explicit ``operationName: null``, which is a GraphQL validation
          error against a multi-operation document). An explicit ``""`` is a
          *provided* value and IS sent, for the server to reject as the
          malformed name it is, rather than silently reinterpreted as "no
          operation name" (the module's fail-at-the-source posture).
        - ``url=`` - a per-call endpoint override, honored for this one
          request only and never persisted on the client.

        With ``assert_no_errors=True`` (this client's default - the
        unittest-flavored ``GraphQLTestMixin.query()`` defaults to ``False``,
        matching its own upstream) a response carrying ``errors`` raises
        ``AssertionError`` with the errors list as the message (an explicit
        raise, so it survives ``python -O``). Tests that *expect* errors pass
        ``assert_no_errors=False`` and assert on ``res.errors`` - remember
        GraphQL returns HTTP 200 with an ``errors`` key for most failures.

        ``files=`` switches the post to multipart. Each key is the variable
        path the file binds to, and ``variables`` must carry a ``None``
        placeholder at that path::

            # top-level file
            client.query(mutation, variables={"file": None}, files={"file": f})

            # nested input object, two file fields
            client.query(
                mutation,
                variables={"data": {"label": "x", "attachment": None, "image": None}},
                files={"data.attachment": f1, "data.image": f2},
            )

        A transport-level misconfiguration (an endpoint typo, or a
        ``TESTING_ENDPOINT`` that does not match the project's URLconf) is not
        wrapped: the JSON decode is Django's ``response.json()``, which raises
        ``ValueError`` naming the non-JSON ``Content-Type`` of the 404/HTML
        body; ``json.JSONDecodeError`` surfaces only when the header *is* JSON
        but the body is malformed (or on the multipart decode path, which does
        not sniff the header).
        """
        body = self._build_body(query, variables, files, operation_name)

        resp = self.request(body, headers, files, url=url)
        return self._finish_response(resp, files=files, assert_no_errors=assert_no_errors)

    def _finish_response(
        self,
        resp: Any,
        *,
        files: dict[str, object] | None,
        assert_no_errors: bool | None,
    ) -> Response:
        """Decode ``resp`` into the typed :class:`Response` + the ``assert_no_errors`` raise.

        The un-colored tail both ``query()`` colors share (DRY review B4): only
        the ``request()`` call is sync/async-colored, so the ``_decode`` ->
        ``Response`` construction -> Decision-5 guard (an EXPLICIT raise, not a
        bare ``assert``, so it survives ``python -O``) is written once. This
        factors BELOW the not-calling-``super().query()`` decision, not around
        it - the async color still owns its own ``await self.request(...)``.
        """
        data = self._decode(resp, type="multipart" if files else "json")

        response = Response(
            errors=data.get("errors"),
            data=data.get("data"),
            extensions=data.get("extensions"),
            response=resp,
        )

        if assert_no_errors and response.errors is not None:
            raise AssertionError(response.errors)

        return response

    def request(
        self,
        body: dict[str, object],
        headers: dict[str, object] | None = None,
        files: dict[str, object] | None = None,
        *,
        url: str | None = None,
    ) -> Any:
        """POST ``body`` to ``url`` (default ``self.path``) through the wrapped client.

        The concrete implementation of the base's one abstract seam, widened
        with the keyword-only ``url=`` so the package-owned :meth:`query` can
        route a single call without mutating stored state (spec-043
        Decision 7). JSON posts carry ``content_type="application/json"``;
        when ``files`` is provided the ``content_type`` argument is *omitted*
        so ``django.test.Client.post`` falls back to its default
        ``MULTIPART_CONTENT`` encoding - that omission IS the multipart
        switch. (Upstream strawberry-django sets ``format="multipart"``
        instead - a DRF-``APIClient``-shaped kwarg Django's test client does
        not accept, landing as an inert WSGI-environ extra; the inert kwarg is
        deliberately dropped here, do not "fix" it back in. Spec-043
        Decision 9.)
        """
        kwargs: dict[str, object] = {"data": body, "headers": headers}
        if not files:
            kwargs["content_type"] = "application/json"

        return self.client.post(url if url is not None else self.path, **kwargs)

    def _build_body(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        files: dict[str, object] | None = None,
        operation_name: str | None = None,
    ) -> dict[str, object]:
        """Build the JSON envelope, or the multipart ``operations`` / ``map`` envelope.

        Package-owned, shadowing the base's ``_build_body`` (spec-043
        Decision 9): the base cannot send ``operationName`` at all, and its
        ``_build_multipart_file_map`` folder heuristic returns an empty map
        for nested input-object uploads. Here the ``files=`` contract carries
        each file's variable path explicitly, so the map is one uniform rule -
        ``map[key] = ["variables." + key]`` - covering a top-level file
        (``"file"``), a nested input-object field (``"data.image"``), and a
        list index (``"tags.0"``) alike. ``operationName`` is injected before
        the ``operations`` JSON-encoding so a named upload operation lands in
        the right field.
        """
        body: dict[str, object] = {"query": query}

        # ``is not None`` (not truthiness): an explicit ``operation_name=""`` is
        # a provided-but-malformed value, sent for the server to reject with a
        # real GraphQL error rather than silently reinterpreted as "no operation
        # name" - the module's fail-at-the-source posture. ``None`` (the default)
        # omits the key entirely, never sending ``operationName: null`` (a
        # validation error against a multi-operation document).
        if operation_name is not None:
            body["operationName"] = operation_name

        if variables:
            body["variables"] = variables

        # Truthiness, matching the ``files`` switches in ``query()`` and
        # ``request()``: ``files={}`` is a JSON post, never a mixed envelope.
        if not files:
            return body

        if not variables:
            # Explicit raise (not a bare ``assert``) so the guard survives
            # ``python -O``; the multipart ``map`` needs variable paths to
            # point at.
            raise AssertionError(
                "query(..., files=...) requires variables= carrying a None placeholder "
                "at each file's variable path (e.g. variables={'data': {'image': None}} "
                "for files={'data.image': f}).",
            )

        # Reserved-field guard: each ``files`` key becomes a multipart field
        # name alongside the envelope's own ``operations`` / ``map`` fields, and
        # ``**files`` spreads last - a key named ``operations`` or ``map`` would
        # silently clobber the envelope and post a corrupt body the server has to
        # diagnose. Reject it at the source. Explicit raise (not a bare assert)
        # so the guard holds under ``python -O``, matching the sibling guards.
        reserved = {"operations", "map"} & set(files)
        if reserved:
            raise AssertionError(
                f"files= keys may not use the reserved multipart envelope field "
                f"name(s) {sorted(reserved)!r}; the 'operations' / 'map' fields "
                f"are built by this client - rename the variable path.",
            )

        self._assert_file_placeholders(variables, files)

        file_map = {key: [f"variables.{key}"] for key in files}
        return {"operations": json.dumps(body), "map": json.dumps(file_map), **files}

    @staticmethod
    def _assert_file_placeholders(variables: dict[str, Any], files: dict[str, object]) -> None:
        """Verify each ``files=`` path resolves to a ``None`` placeholder in ``variables``.

        The path-keyed ``files=`` contract (spec-043 Decision 9) makes the
        client - not the server - the owner of the multipart ``map``: each key
        is a dotted variable path (dict keys and list indexes) and ``variables``
        must carry a ``None`` placeholder at exactly that path. Walking the path
        here fails a typo or a malformed call at the source, naming the bad path,
        rather than emitting a spec-invalid envelope the server has to diagnose
        later. Explicit ``AssertionError`` (not a bare ``assert``) so the guard
        holds under ``python -O``, matching the empty-``variables`` guard above.
        """
        for key in files:
            current: Any = variables
            for segment in key.split("."):
                if isinstance(current, list):
                    # Multipart operation paths use ``object-path`` numeric segments:
                    # a list index is its canonical non-negative decimal rendering.
                    # Guard the conversion itself because digit-like Unicode and very
                    # long decimal strings do not share ``int()``'s acceptance domain.
                    try:
                        index = int(segment)
                    except ValueError:
                        index = None
                    if (
                        index is None
                        or index < 0
                        or str(index) != segment
                        or index >= len(current)
                    ):
                        raise AssertionError(
                            f"files= path {key!r} has no matching placeholder in "
                            f"variables: {segment!r} is not a valid index into a "
                            f"{len(current)}-item list.",
                        )
                    current = current[index]
                elif isinstance(current, dict):
                    if segment not in current:
                        raise AssertionError(
                            f"files= path {key!r} has no matching placeholder in "
                            f"variables: no key {segment!r} at that level.",
                        )
                    current = current[segment]
                else:
                    # AssertionError (not the TRY004-suggested TypeError) on
                    # purpose: every placeholder failure here is one malformed
                    # test call, raised as the same type as the sibling guards so
                    # ``pytest.raises(AssertionError)`` catches every bad shape.
                    raise AssertionError(  # noqa: TRY004 - uniform guard type, not a runtime TypeError
                        f"files= path {key!r} has no matching placeholder in "
                        f"variables: cannot descend into {segment!r} (the value "
                        f"there is not a dict or list).",
                    )
            if current is not None:
                raise AssertionError(
                    f"files= path {key!r} must point at a None placeholder in "
                    f"variables, but the value there is {current!r}.",
                )

    @contextlib.contextmanager
    def login(self, user: AbstractBaseUser) -> Iterator[None]:
        """Run the block authenticated as ``user`` - ``force_login`` on entry, ``logout`` on exit.

        The logout runs even when the block raises, so a failing assertion
        inside the block cannot leak session state into the rest of the test.
        For session-cookie assertions the wrapped client rides along as
        ``.client`` (and each response as ``res.response``).
        """
        self.client.force_login(user)
        try:
            yield
        finally:
            self.client.logout()


class AsyncTestClient(TestClient):
    """The async twin: ``TestClient`` over ``django.test.AsyncClient``, awaited transport.

    Drives Django's own in-process ``AsyncClientHandler`` - no ``asgi.py``
    (and no Channels; this is not a Channels communicator) is required, so it
    works against a WSGI-only project (spec-043 Decision 8). The body build,
    file-map rule, and per-call ``url=`` routing are shared with the sync
    client; only the transport await and the ``login()`` color differ.
    """

    def __init__(self, path: str | None = None, client: AsyncClient | None = None) -> None:
        super().__init__(path, client or AsyncClient())

    @property
    def client(self) -> AsyncClient:
        """The wrapped ``django.test.AsyncClient``."""
        return self._client

    async def query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        headers: dict[str, object] | None = None,
        files: dict[str, object] | None = None,
        assert_no_errors: bool | None = True,
        *,
        operation_name: str | None = None,
        url: str | None = None,
    ) -> Response:
        """Post a GraphQL operation and return the typed :class:`Response` - awaited.

        The async re-color of :meth:`TestClient.query` (upstream's own
        ``AsyncTestClient`` re-implements the flow the same way rather than
        calling ``super().query()``); see the sync docstring for the full
        contract - ``operation_name=`` / ``url=`` semantics, the
        ``assert_no_errors`` raise, the path-keyed ``files=`` multipart
        contract, and the non-JSON failure shapes are identical.
        """
        body = self._build_body(query, variables, files, operation_name)

        # ``request()`` is sync-shaped but returns whatever the wrapped
        # client's ``post()`` returns - an awaitable here, because the wrapped
        # client is ``AsyncClient`` (upstream's ``cast("Awaitable", ...)`` as
        # a plain await).
        resp = await self.request(body, headers, files, url=url)
        return self._finish_response(resp, files=files, assert_no_errors=assert_no_errors)

    @contextlib.asynccontextmanager
    async def login(self, user: AbstractBaseUser) -> AsyncIterator[None]:
        """The async ``login()`` bracket - ``force_login`` / ``logout`` via ``sync_to_async``.

        Session writes are ORM work, hence the ``sync_to_async`` wrapping;
        the logout runs even when the block raises.
        """
        await sync_to_async(self.client.force_login)(user)
        try:
            yield
        finally:
            await sync_to_async(self.client.logout)()


class GraphQLTestMixin:
    """The graphene-django-shaped unittest mixin: ``self.query(...)`` + assertion helpers.

    Compose it over any ``unittest.TestCase``-family base (``GraphQLTestCase``
    and ``GraphQLTransactionTestCase`` are the two-line concrete
    combinations); the mixin is deliberately state-free beyond ``GRAPHQL_URL``
    and reads only ``self.client`` - Django's ``TestCase`` provides it, and a
    consumer's custom base works the same way (spec-043 Decision 10).

    ``query()`` delegates to a :class:`TestClient` constructed over the test
    case's own ``self.client``, so ``self.client.force_login(...)``, cookie
    state, and per-case client configuration all apply, and the body building
    exists once. Note the flipped default: ``assert_no_errors=False`` here
    (graphene's mixin never auto-asserted, and its documented flow is "call
    ``self.query(...)``, then ``assertResponseNoErrors`` /
    ``assertResponseHasErrors``"); the pytest-flavored :class:`TestClient`
    defaults to ``True``. Each flavor matches its own upstream.
    """

    #: Per-class endpoint override (graphene's knob). ``None`` falls through
    #: to ``DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]``, then the
    #: ``"/graphql/"`` default; the per-call ``query(..., url=...)`` outranks
    #: all three (spec-043 Decision 7).
    GRAPHQL_URL: str | None = None

    def query(
        self,
        query: str,
        *,
        variables: dict[str, Any] | None = None,
        operation_name: str | None = None,
        headers: dict[str, object] | None = None,
        files: dict[str, object] | None = None,
        url: str | None = None,
        assert_no_errors: bool | None = False,
    ) -> Response:
        """Post a GraphQL operation through the test case's own ``self.client``.

        The same call as :meth:`TestClient.query`, keyword-only after the
        query string (graphene's positional ``operation_name`` becomes
        ``operation_name=``; its ``input_data=`` convenience is not carried -
        write ``variables={"input": ...}``), returning the same typed
        :class:`Response`. Unlike the pytest-flavored client this does NOT
        raise on GraphQL errors by default (``assert_no_errors=False``,
        graphene parity) - follow with :meth:`assertResponseNoErrors` /
        :meth:`assertResponseHasErrors`, or opt into the raise per call.
        """
        client = TestClient(self.GRAPHQL_URL, client=self.client)
        return client.query(
            query,
            variables=variables,
            headers=headers,
            files=files,
            assert_no_errors=assert_no_errors,
            operation_name=operation_name,
            url=url,
        )

    def assertResponseNoErrors(self, resp: Response, msg: str | None = None) -> None:  # noqa: N802 - unittest/graphene assertion vocabulary
        """Assert the response is HTTP 200 AND carries no GraphQL ``errors``.

        Both of graphene's checks, against the typed :class:`Response`;
        failures carry the decoded content (or ``msg``) as the message -
        both fields, so a non-200 whose body has no ``errors`` key still
        fails with something readable.
        """
        details = msg if msg is not None else {"errors": resp.errors, "data": resp.data}
        self.assertEqual(resp.response.status_code, 200, details)
        self.assertIsNone(resp.errors, details)

    def assertResponseHasErrors(self, resp: Response, msg: str | None = None) -> None:  # noqa: N802 - unittest/graphene assertion vocabulary
        """Assert the response carries GraphQL ``errors``.

        Deliberately no status assertion - even with errors, GraphQL returns
        HTTP 200 (graphene's own warning, kept). Failures carry the decoded
        ``data`` (or ``msg``) as the message.
        """
        self.assertTrue(resp.errors, msg or resp.data)


class GraphQLTestCase(GraphQLTestMixin, TestCase):
    """``GraphQLTestMixin`` over ``django.test.TestCase`` - the common concrete combination."""


class GraphQLTransactionTestCase(GraphQLTestMixin, TransactionTestCase):
    """``GraphQLTestMixin`` over ``django.test.TransactionTestCase``.

    Reach for this flavor when the code under test uses
    ``transaction.on_commit`` or needs real commits - Django's own
    ``TestCase`` / ``TransactionTestCase`` split, unchanged.
    """
