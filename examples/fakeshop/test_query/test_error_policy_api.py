"""Live ``/graphql/`` production-error-policy acceptance tests.

``ErrorPolicy`` is a promise about what a REAL client reads out of a REAL
response, so the category matrix is pinned where a client can see it: over the
package's own sync and async GraphQL test clients against mounts of its Django
GraphQL view, reading the JSON envelope.

The matrix is the whole point, and it has exactly three columns (spec-048
Decision 8):

- **masked** - a plain Python exception that escaped a resolver. The client gets
  the policy message plus a correlation id, and the original text appears nowhere
  in the body.
- **untouched, no originating exception** - a parse error and a validation error.
  graphql-core built them from the client's own document.
- **masked, surfaced through value COMPLETION** rather than from the resolve phase -
  a non-null field's null propagation and a failing list completion. Both arrive
  ``located_error``-wrapped with the original exception attached, so the same
  structural rule covers them; they get their own rows because a masked surface
  with a hole shaped like the completion phase looks identical to a correct one on
  every other row here.
- **masked, raised from a HOOK** rather than from a field at all - a consumer
  extension failing in either half of ``on_validate``, in the teardown half of
  ``on_operation``, or in ``on_execute``. Upstream converts such an exception into
  a response only after every teardown has unwound, so no extension is left to
  mask it and the schema's own return is the seam that does; the halves get their
  own rows because each escapes from a different stage.
- **untouched, deliberate** - anything raised as a ``GraphQLError``: the
  ``GLOBALID_INVALID`` boundary, a ``RESOURCE_LIMIT_EXCEEDED`` rejection, the
  mutation pipeline's ``"Not authorized to ..."`` denial, and a consumer's own
  ``GraphQLError``. A ``FieldError`` envelope needs no column at all - it is
  returned in ``data``, so nothing classifies it.

Around the matrix sit the properties a single row cannot state: one FRESH id per
masked error, the id reaching the server log with the original traceback, the
retained ``path``, sync/async parity, the two ways out (``DEBUG=True`` and
``error_policy={"enabled": False}``), a ``DEBUG`` value that is set but is not
the boolean ``True`` (still masked), a resolver that writes
``info.schema.error_policy`` (still masked: the attribute is a copy), and an
extension entry that resolves to the masking authority (the request is refused
with the configuration code rather than masked by consumer code).

The scaffolding is one probe-schema factory over fakeshop's own ``Query`` /
``Mutation``, extended with resolvers that raise on demand - a real schema
carrying deliberate failures, rather than a synthetic one that would not exercise
the framework's own rejection sites. It is built per request rather than cached
because the acceptance tier reloads ``config.schema`` before every test.

``tests/test_error_policy.py`` holds what no request can express: the policy
object's validation and precedence ladder, the correlation-id format sampled
from the generator, the extension's install position and what a directly
supplied entry of its own kind declares, the standalone-schema fallback,
teardown no-ops, and fail-closed degrades over objects no engine builds.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import re
import threading
from functools import cache

import pytest
import strawberry
from apps.products import models as product_models
from apps.products.services import create_users, seed_data
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client
from django.test import override_settings as _override_settings
from django.urls import include, path
from graphql import GraphQLError
from graphql_client import post_graphql
from strawberry import relay
from strawberry.extensions.base_extension import SchemaExtension

from django_strawberry_framework import (
    RESOURCE_LIMIT_ERROR_CODE,
    SCHEMA_CONFIGURATION_ERROR_CODE,
    DjangoErrorPolicyExtension,
    DjangoSchema,
    strawberry_config,
)
from django_strawberry_framework.error_policy import DEFAULT_ERROR_POLICY
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

pytestmark = pytest.mark.urls(__name__)

#: The string a masked response must not contain. Shaped like something a real
#: exception would carry by accident - a tenant identifier and a server path - so
#: the "appears nowhere in the body" assertion is about disclosure, not about a
#: token chosen to be easy to find.
_SENSITIVE = "internal tenant secret /srv/private/tenant-42.key"

#: A second, DIFFERENT sensitive string, so the two-errors-one-response row can tell
#: which failure produced which entry.
_SENSITIVE_OTHER = "second internal secret /srv/private/tenant-99.key"

_PACKAGE_LOGGER = "django_strawberry_framework"

#: 32 lowercase hex characters and nothing else - the pinned ``uuid4().hex`` shape.
_CORRELATION_ID = re.compile(r"\A[0-9a-f]{32}\Z")

_CUSTOM_MESSAGE = "The request could not be completed."
_CUSTOM_KEY = "supportReference"


#: Settings that open the policy's ``DEBUG`` pass-through gate for one live request.
#: Fakeshop's shipped settings also wire django-debug-toolbar behind ``DEBUG``, so
#: the toolbar middleware is dropped for the duration: left in, it would try to
#: inject a panel referencing the ``djdt`` routes that ``config.urls`` computed
#: under the ambient ``DEBUG=False`` and fail the request for a reason that has
#: nothing to do with the policy.
_DEBUG_PASS_THROUGH = {
    "DEBUG": True,
    "MIDDLEWARE": [entry for entry in settings.MIDDLEWARE if "debug_toolbar" not in entry],
}


def _probe_query_type():
    """Fakeshop's own ``Query``, extended with resolvers that fail on demand.

    Inheriting rather than replacing keeps every framework rejection site the
    matrix needs - the library app's ``GLOBALID_INVALID`` filter boundary in
    particular - reachable through the same schema that carries the deliberate
    failures, so no row has to be split across two mounts to get its comparison.

    The raising fields are NULLABLE on purpose. A non-null field's error
    propagates to the root and nulls ``data`` wholesale, which would make the
    two-errors-in-one-response row depend on graphql-core's propagation rules
    rather than on the policy; nullable fields let each error stay attributed to
    its own ``path``.
    """
    from config.schema import Query

    @strawberry.type
    class ProbeQuery(Query):
        """The fakeshop query surface plus resolvers that fail or mutate on demand."""

        @strawberry.field
        def boom(self) -> str | None:
            """Raise a plain ``ValueError`` carrying a sensitive string."""
            raise ValueError(_SENSITIVE)

        @strawberry.field
        def boom_other(self) -> str | None:
            """Raise a DIFFERENT plain exception, for the two-ids row."""
            raise RuntimeError(_SENSITIVE_OTHER)

        @strawberry.field
        def deliberate(self) -> str | None:
            """Raise a consumer-authored ``GraphQLError`` - a client-facing statement."""
            raise GraphQLError(
                "This message was written for the client.",
                extensions={"code": "CONSUMER_REJECTION"},
            )

        @strawberry.field
        def fine(self) -> str:
            """Succeed, so a partially-failing response has something in ``data``."""
            return "fine"

        @strawberry.field
        def unmask(self, info: strawberry.Info) -> str:
            """Write ``enabled=False`` on the schema policy a resolver can reach."""
            info.schema.error_policy.__dict__["enabled"] = False
            return "written"

        @strawberry.field
        def boom_non_null(self) -> str:
            """Raise from a NON-NULL field, so the error reaches the client through
            graphql-core's value-COMPLETION phase (null propagation) rather than as
            a nullable field's own entry.
            """
            raise ValueError(_SENSITIVE)

        @strawberry.field
        def boom_items(self) -> list[str]:
            """Raise while completing a LIST item, the other completion-phase shape."""
            raise RuntimeError(_SENSITIVE_OTHER)

    return ProbeQuery


def _probe_schema(**schema_kwargs) -> DjangoSchema:
    """Build a probe schema over fakeshop's types, passing ``schema_kwargs`` through.

    Deliberately NOT cached: the acceptance tier's autouse fixture reloads
    ``config.schema`` before every test, so a cached schema would hold types from
    a previous test's registry.
    """
    from config.schema import Mutation

    return DjangoSchema(
        query=_probe_query_type(),
        mutation=Mutation,
        config=strawberry_config(),
        **schema_kwargs,
    )


def _probe_view(**schema_kwargs):
    """Mount the sync package view over a probe schema built per request."""

    def view(request, *args, **kwargs):
        built = DjangoGraphQLView.as_view(schema=_probe_schema(**schema_kwargs))
        return built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


def _probe_async_view(**schema_kwargs):
    """The async twin of ``_probe_view``, so parity is proven on a real event loop."""

    async def view(request, *args, **kwargs):
        built = AsyncDjangoGraphQLView.as_view(schema=_probe_schema(**schema_kwargs))
        return await built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


#: The document-token ceiling the ``RESOURCE_LIMIT_EXCEEDED`` row trips. Small
#: enough that any real document exceeds it, so the row is about the CODE
#: surviving the policy, not about where the bound sits (spec-047 owns that).
_MAX_TOKENS = 4


def _error_policy_factory():
    """A factory resolving to the masking authority, which is not a thing an entry can be."""
    return DjangoErrorPolicyExtension()


class _FactoryHookWitness(SchemaExtension):
    """Record every hook a consumer entry gets to run on the factory mount."""

    ran: list[str] = []

    def on_operation(self):
        """Note the operation seam, on both sides of the request."""
        _FactoryHookWitness.ran.append("operation")
        yield
        _FactoryHookWitness.ran.append("operation-done")

    def on_parse(self):
        """Note the parse seam, which a refused request still passes through."""
        _FactoryHookWitness.ran.append("parse")
        yield

    def on_execute(self):
        """Note execution, which a refused request must never reach."""
        _FactoryHookWitness.ran.append("execute")
        yield


def _hook_exception():
    """The plain exception a failing consumer hook raises by default."""
    return RuntimeError(_SENSITIVE)


#: What a hook raising a ``GraphQLError`` says. Deliberate, client-facing, and
#: therefore the one hook failure that travels unchanged.
_DELIBERATE_HOOK_MESSAGE = "This hook message was written for the client."


def _deliberate_hook_exception():
    """A hook's own ``GraphQLError`` - a statement written for the client."""
    return GraphQLError(_DELIBERATE_HOOK_MESSAGE, extensions={"code": "CONSUMER_HOOK_REJECTION"})


#: Which hook and half the consumer extension below fails at for the row running
#: now, and what it raises there. Module state rather than a constructor
#: argument, because the entry is a CLASS: the schema resolves a fresh extension
#: per operation, so the row arms the failure before it posts and whatever
#: extension the operation builds carries it.
_HOOK_FAILURE = {"where": None, "build": _hook_exception}


class _HookFailure(SchemaExtension):
    """An ordinary consumer extension that raises at one chosen hook and half.

    Nothing about it is an enforcement authority - it is the plain
    ``DjangoSchema(extensions=[...])`` entry any deployment writes, failing the
    way consumer code fails.
    """

    def on_operation(self):
        """Fail at the teardown half, which unwinds INSIDE the masking authority's."""
        yield
        _fail_hook("operation-teardown")

    def on_validate(self):
        """Fail at either half of the validation stage."""
        _fail_hook("validate-setup")
        yield
        _fail_hook("validate-teardown")

    def on_execute(self):
        """Fail as execution begins."""
        _fail_hook("execute-setup")
        yield


def _fail_hook(where):
    """Raise the armed exception when ``where`` is the armed failure point."""
    if _HOOK_FAILURE["where"] != where:
        return
    failure = _HOOK_FAILURE["build"]()
    raise failure


@contextlib.contextmanager
def _failing_hook(where, build=_hook_exception):
    """Arm the consumer extension to fail at ``where`` for the duration of one row."""
    _HOOK_FAILURE["where"] = where
    _HOOK_FAILURE["build"] = build
    try:
        yield
    finally:
        _HOOK_FAILURE["where"] = None
        _HOOK_FAILURE["build"] = _hook_exception


#: Every hook and half a consumer extension can fail at where the failure escapes
#: into upstream's own error conversion rather than into a located field error.
HOOK_HALVES = (
    "validate-setup",
    "validate-teardown",
    "operation-teardown",
    "execute-setup",
)

#: The two transports every hook row is answered over.
HOOK_COLORS = ("sync", "async")

HOOK_ROWS = [(where, color) for where in HOOK_HALVES for color in HOOK_COLORS]
HOOK_IDS = [f"{where}-{color}" for where, color in HOOK_ROWS]

#: Where the hook-failure mounts live, per view color, and the opt-out twin.
HOOK_MOUNTS = {"sync": "/ep-hook/", "async": "/ep-hook-async/"}
HOOK_OFF_MOUNTS = {"sync": "/ep-hook-off/", "async": "/ep-hook-off-async/"}


#: The four spellings Strawberry accepts for an extension entry. A class and a
#: fresh entry resolve to a new extension per operation; an instance and a
#: factory returning a singleton resolve to ONE object every operation shares,
#: which is what makes the masking question different for them.
ENTRY_SPELLINGS = (
    "class",
    "fresh-factory",
    "instance",
    "singleton-factory",
)


@strawberry.type
class _SharedEntryQuery:
    """A standalone surface with one failing field and one that nests an operation.

    Deliberately not fakeshop's ``Query``: these mounts are CACHED, because the
    shared spellings only mean anything when every request meets the same schema
    object, and a cached schema over reloaded fakeshop types would hold a
    previous test's registry.
    """

    @strawberry.field
    def fine(self) -> str:
        """Succeed, so a later request can prove the mount still answers normally."""
        return "fine"

    @strawberry.field
    def boom(self) -> str | None:
        """Raise a plain exception carrying the sensitive string."""
        raise ValueError(_SENSITIVE)

    @strawberry.field
    def nested_then_boom(self, info: strawberry.Info) -> str | None:
        """Run a whole inner operation through this schema, then fail.

        The inner operation is the second assignment onto a shared entry, made
        while the outer operation is still running. When the outer teardown
        masks by reading its own state, the inner call changes nothing; when it
        reads an attribute, the outer failure is the one that goes to the client
        unmasked.
        """
        inner = info.schema.execute_sync("{ fine }")
        assert inner.errors is None, inner.errors
        raise ValueError(_SENSITIVE)


class _SharedEntryCoordinator(SchemaExtension):
    """Hold one operation open between the parse hooks while another one runs.

    Parks in the parsing hook's setup half and changes nothing else - no policy,
    no execution context, no extension list, no result - so the overlap is a
    property of the schedule rather than of anything this wrote. Bounded by an
    event, never a sleep.
    """

    parked = threading.Event()
    released = threading.Event()
    armed = False

    def on_parse(self):
        """Park the failing document, once, while the overlap row is armed."""
        if _SharedEntryCoordinator.armed and "boom" in (self.execution_context.query or ""):
            _SharedEntryCoordinator.parked.set()
            _SharedEntryCoordinator.released.wait(timeout=10)
        yield


class _SharedEntryConsumer(SchemaExtension):
    """An ordinary consumer extension: present in the chain, enforcing nothing.

    It carries the factory spellings. A factory is opaque until it is called, so
    nothing it returns can be the schema's masker; what a factory spelling is
    still needed for is the object-lifetime axis - one extension per operation
    against one shared between all of them - and an unrelated extension puts
    exactly that axis under test without asking consumer code to enforce
    anything.
    """

    def on_operation(self):
        """Occupy the operation seam and change nothing about the result."""
        yield


@cache
def _shared_error_extension() -> DjangoErrorPolicyExtension:
    """The error-policy object the instance spelling declares the schema's policy with."""
    return DjangoErrorPolicyExtension()


@cache
def _shared_consumer_extension() -> _SharedEntryConsumer:
    """The ONE consumer extension the singleton-factory spelling hands every operation."""
    return _SharedEntryConsumer()


def _fresh_consumer_extension() -> _SharedEntryConsumer:
    """A NEW consumer extension per operation, the other half of the lifetime axis."""
    return _SharedEntryConsumer()


def _shared_entry_entry(spelling: str):
    """The ``extensions=[...]`` entry that spells ``spelling``.

    Strawberry resolves an entry as ``ext if isinstance(ext, SchemaExtension)
    else ext()`` once per operation, so a class and a factory take the same
    branch and differ only in what the call returns. The fresh spelling is
    therefore a real callable rather than the class a second time: handing back
    the class would make that row the class row under another id, and the pair
    would be counted twice while only one of them was ever built.

    The class and instance spellings are the policy's own type, which
    ``DjangoSchema`` reads as a declaration and folds into the schema's own
    configuration; the factory spellings are an unrelated consumer extension.
    Either way the masker is the schema's own authority, built fresh per
    operation - so all four rows ask the same question about the same masker and
    differ only in what else the consumer put in the chain.
    """
    if spelling == "class":
        return DjangoErrorPolicyExtension
    if spelling == "fresh-factory":
        return _fresh_consumer_extension
    if spelling == "instance":
        return _shared_error_extension()
    return _shared_consumer_extension


@cache
def _shared_entry_schema(spelling: str) -> DjangoSchema:
    """One cached schema per entry spelling.

    Whatever the consumer spelled, the masker is the one the schema installs
    around the chain, so the row cannot be answered by a second masker arriving
    from somewhere else.
    """
    return DjangoSchema(
        query=_SharedEntryQuery,
        extensions=[_shared_entry_entry(spelling), _SharedEntryCoordinator],
    )


def _shared_entry_view(spelling: str):
    """Mount the synchronous package view over one entry spelling."""

    def view(request, *args, **kwargs):
        built = DjangoGraphQLView.as_view(schema=_shared_entry_schema(spelling))
        return built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


def _shared_entry_async_view(spelling: str):
    """Mount the asynchronous package view over one entry spelling."""

    async def view(request, *args, **kwargs):
        built = AsyncDjangoGraphQLView.as_view(schema=_shared_entry_schema(spelling))
        return await built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


#: Where each entry spelling is mounted, per view color.
ENTRY_MOUNTS = {
    (spelling, color): f"/ep-entry-{spelling}-{color}/"
    for spelling in ENTRY_SPELLINGS
    for color in ("sync", "async")
}


#: Every shared-entry row, with the node id its spelling and color read as.
ENTRY_ROWS = list(ENTRY_MOUNTS)
ENTRY_IDS = [f"{spelling}-{color}" for spelling, color in ENTRY_ROWS]


urlpatterns = [
    path("", include("config.urls")),
    path("ep/", _probe_view()),
    # Mounted from ``ENTRY_MOUNTS`` rather than spelled out, so the mounts and the
    # parametrized rows cannot disagree about which spellings exist.
    *(
        path(
            mount.lstrip("/"),
            (_shared_entry_view if color == "sync" else _shared_entry_async_view)(spelling),
        )
        for (spelling, color), mount in ENTRY_MOUNTS.items()
    ),
    path("ep-async/", _probe_async_view()),
    path("ep-off/", _probe_view(error_policy={"enabled": False})),
    path(
        "ep-custom/",
        _probe_view(
            error_policy={"message": _CUSTOM_MESSAGE, "correlation_extension_key": _CUSTOM_KEY},
        ),
    ),
    path("ep-limits/", _probe_view(resource_policy={"max_document_tokens": _MAX_TOKENS})),
    path(
        "ep-factory/",
        _probe_view(extensions=[_error_policy_factory, _FactoryHookWitness]),
    ),
    path(HOOK_MOUNTS["sync"].lstrip("/"), _probe_view(extensions=[_HookFailure])),
    path(HOOK_MOUNTS["async"].lstrip("/"), _probe_async_view(extensions=[_HookFailure])),
    path(
        HOOK_OFF_MOUNTS["sync"].lstrip("/"),
        _probe_view(extensions=[_HookFailure], error_policy={"enabled": False}),
    ),
    path(
        HOOK_OFF_MOUNTS["async"].lstrip("/"),
        _probe_async_view(extensions=[_HookFailure], error_policy={"enabled": False}),
    ),
]


def _post(
    mount,
    query,
    variables=None,
    *,
    client=None,
):
    """POST one GraphQL document to a mount and return ``(response, parsed envelope)``."""
    response = post_graphql(query, client=client, variables=variables, url=mount)
    assert response.status_code == 200, response.content
    return response, response.json()


def _masked_error(payload, *, key=DEFAULT_ERROR_POLICY.correlation_extension_key):
    """Return the single masked error in ``payload``, asserting the masked shape.

    Every masking row funnels through here, so "the error was masked" always means
    the same three things: the policy's message verbatim, a well-formed correlation
    id under the configured extensions key, and no other extension keys smuggled
    alongside it. A row that only asserted "the sensitive text is absent" would
    also pass on a response that had dropped the error entirely.
    """
    assert len(payload["errors"]) == 1, payload
    error = payload["errors"][0]
    assert error["message"] == DEFAULT_ERROR_POLICY.message, error
    correlation_id = error["extensions"][key]
    assert _CORRELATION_ID.fullmatch(correlation_id), correlation_id
    return error


def _await_response(coroutine):
    """Run one ``AsyncTestClient.query`` coroutine to completion on a fresh event loop."""
    return asyncio.run(_resolve(coroutine))


async def _resolve(coroutine):
    return await coroutine


# ---------------------------------------------------------------------------
# Masked: a plain exception that escaped a resolver
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_an_unexpected_exception_reaches_the_client_as_the_policy_message_only():
    """The masking contract, stated once over a real response body.

    Three claims, and the third is the one that matters: the client reads exactly
    the policy message, it can quote a correlation id back to an operator, and the
    exception's own text is absent from the WHOLE body - not merely from the
    message field, where a naive implementation would leave it duplicated under
    ``extensions`` or in a nested ``originalError``.
    """
    response, payload = _post("/ep/", "{ boom fine }")
    _masked_error(payload)
    assert payload["data"] == {"boom": None, "fine": "fine"}
    body = response.content.decode()
    assert _SENSITIVE not in body, body
    assert "tenant-42" not in body, body
    assert "ValueError" not in body, body


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("document", "sensitive"),
    [("{ boomNonNull }", _SENSITIVE), ("{ boomItems }", _SENSITIVE_OTHER)],
    ids=["non-null-completion", "list-completion"],
)
def test_an_exception_surfaced_through_value_completion_is_masked_too(document, sensitive):
    """graphql-core raises from two phases, and both are masked (spec-048 Decision 8).

    A resolver exception does not always reach the client from the resolve phase:
    a NON-NULL field propagates its failure while COMPLETING the resolved value,
    and a list field fails while completing its items. Both arrive
    ``located_error``-wrapped with the original exception attached, so the
    structural classifier covers them - but a masked surface with a hole shaped
    like the completion phase would look identical on every other row in this
    file, which is why these two are their own.
    """
    response, payload = _post("/ep/", document)
    _masked_error(payload)
    assert payload["data"] is None
    assert sensitive not in response.content.decode()


@pytest.mark.django_db
def test_the_masked_error_retains_the_path_of_the_field_that_failed():
    """Masking removes the message, never the attribution (spec-048 Decision 9).

    The client wrote the query, so ``path`` discloses nothing - and without it
    every partial failure becomes unattributable and client-side error-to-field
    mapping breaks. Read on a response where a sibling field SUCCEEDED, so the
    path is load-bearing rather than trivially the only field present.
    """
    _, payload = _post("/ep/", "{ fine boom }")
    assert _masked_error(payload)["path"] == ["boom"]
    assert payload["data"]["fine"] == "fine"


@pytest.mark.django_db
def test_the_correlation_id_reaches_the_server_log_with_the_original_exception(caplog):
    """The id the client holds resolves to the original exception, or masking is just deletion.

    Pinned on the exact log destination the spec fixes: the package logger
    ``django_strawberry_framework``, at ``ERROR``, with the id in the MESSAGE TEXT
    (so a plain-text logging stack resolves a support call with one ``grep``) and
    ``exc_info`` carrying the original exception and its traceback.
    """
    caplog.set_level(logging.ERROR, logger=_PACKAGE_LOGGER)
    _, payload = _post("/ep/", "{ boom }")
    correlation_id = _masked_error(payload)["extensions"]["correlationId"]

    records = [
        record
        for record in caplog.records
        if record.name == _PACKAGE_LOGGER and record.levelno == logging.ERROR
    ]
    assert len(records) == 1, caplog.records
    record = records[0]
    assert correlation_id in record.getMessage()
    assert record.exc_info is not None
    assert isinstance(record.exc_info[1], ValueError)
    assert str(record.exc_info[1]) == _SENSITIVE
    assert record.exc_info[2] is not None  # the traceback the operator needs


@pytest.mark.django_db
def test_a_factory_resolving_to_the_masker_refuses_the_request_instead_of_masking(caplog):
    """A factory cannot become the schema's masker; the schema refuses the operation.

    The masker is the schema's own, built per operation from the configuration
    the schema was accepted with. A factory is opaque until it is called, so a
    factory that resolves to one is a second masker arriving from consumer code
    on a request that is already running - and what it would mask is exactly
    what could not be established. The whole request is refused instead: the
    stable configuration code, no resolver, no correlation id minted, and no
    consumer hook past the seams the refusal itself passes through.
    """
    caplog.set_level(logging.ERROR, logger=_PACKAGE_LOGGER)
    _FactoryHookWitness.ran.clear()

    _, payload = _post("/ep-factory/", "{ boom }")

    assert payload["data"] is None, payload
    assert [error["extensions"]["code"] for error in payload["errors"]] == [
        SCHEMA_CONFIGURATION_ERROR_CODE,
    ]
    assert _SENSITIVE not in json.dumps(payload)
    assert "correlationId" not in json.dumps(payload)
    assert "execute" not in _FactoryHookWitness.ran, _FactoryHookWitness.ran

    records = [
        record
        for record in caplog.records
        if record.name == _PACKAGE_LOGGER and record.levelno == logging.ERROR
    ]
    # The refusal names the cause for the operator. A mask would instead log the
    # correlation id the client was handed, with the original traceback attached.
    assert [record.exc_info for record in records] == [None] * len(records), caplog.records


@pytest.mark.django_db
def test_two_unexpected_errors_in_one_response_carry_two_different_ids(caplog):
    """One FRESH id PER MASKED ERROR, not one per operation.

    A response reporting two unrelated failures is exactly when a shared id would
    be ambiguous: the user quotes one id and the operator cannot tell which of the
    two exceptions they hit. Both ids must also appear in the log, one record each.
    """
    caplog.set_level(logging.ERROR, logger=_PACKAGE_LOGGER)
    _, payload = _post("/ep/", "{ boom boomOther }")

    assert len(payload["errors"]) == 2, payload
    ids = [error["extensions"]["correlationId"] for error in payload["errors"]]
    assert all(_CORRELATION_ID.fullmatch(value) for value in ids), ids
    assert ids[0] != ids[1]
    assert {error["message"] for error in payload["errors"]} == {DEFAULT_ERROR_POLICY.message}

    logged = " ".join(
        record.getMessage() for record in caplog.records if record.name == _PACKAGE_LOGGER
    )
    assert all(value in logged for value in ids)


# ---------------------------------------------------------------------------
# Untouched: no originating exception (parse / validation)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_a_parse_error_keeps_its_own_message_and_carries_no_correlation_id():
    """``original_error is None``, so nothing was masked - and nothing should be.

    A syntax error describes the client's own document. Masking it would tell a
    developer "an unexpected error occurred" about their own typo.
    """
    _, payload = _post("/ep/", "{ boom")
    error = payload["errors"][0]
    assert "Syntax Error" in error["message"], error
    assert "correlationId" not in (error.get("extensions") or {})


@pytest.mark.django_db
def test_a_validation_error_keeps_its_own_message_and_carries_no_correlation_id():
    """The validation half of the ``original_error is None`` column.

    An unknown field is named back to the client verbatim; the schema is public,
    so the name discloses nothing the client could not introspect.
    """
    _, payload = _post("/ep/", "{ noSuchFieldAnywhere }")
    assert payload["data"] is None, payload
    error = payload["errors"][0]
    assert "Cannot query field 'noSuchFieldAnywhere'" in error["message"], error
    assert (error.get("extensions") or {}) == {}, error


@pytest.mark.django_db
def test_an_async_validation_error_keeps_its_own_message_and_carries_no_correlation_id():
    """The async validation half of the ``original_error is None`` column."""
    async_response = _await_response(
        AsyncTestClient().query(
            "{ noSuchFieldAnywhere }",
            assert_no_errors=False,
            url="/ep-async/",
        ),
    )
    payload = json.loads(async_response.response.content)
    assert payload["data"] is None, payload
    assert len(payload["errors"]) == 1, payload
    error = payload["errors"][0]
    assert "Cannot query field 'noSuchFieldAnywhere'" in error["message"], error
    assert (error.get("extensions") or {}) == {}, error


# ---------------------------------------------------------------------------
# Untouched: a deliberate ``GraphQLError``
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_an_audited_globalid_rejection_keeps_its_message_and_its_code():
    """The ``GLOBALID_INVALID`` boundary survives the policy intact.

    The regression this row exists to catch is the one Strawberry's own
    ``MaskErrors`` would cause: a coded, audited, client-facing rejection becoming
    indistinguishable from a crash. Both halves are asserted - the message a client
    reads and the ``extensions.code`` a client branches on.
    """
    _, payload = _post(
        "/ep/",
        '{ allLibraryGenres(filter: { id: { exact: "not-a-valid-base64!!!" } }) { name } }',
    )
    error = payload["errors"][0]
    assert error["extensions"]["code"] == "GLOBALID_INVALID", error
    assert "Invalid GlobalID" in error["message"], error
    assert "correlationId" not in error["extensions"]


@pytest.mark.django_db
def test_an_audited_resource_limit_rejection_keeps_its_message_and_its_code():
    """A ``RESOURCE_LIMIT_EXCEEDED`` refusal survives the policy intact.

    ``ResourceLimitExceeded`` multiple-inherits ``GraphQLError``, so the structural
    classifier sees a deliberate client-facing error with no allowlist entry
    required - the property the rule exists for. Mounted on its own narrowed
    ``max_document_tokens`` so the refusal is unambiguous.
    """
    _, payload = _post("/ep-limits/", "{ fine deliberate boomOther }")
    error = payload["errors"][0]
    assert error["extensions"]["code"] == RESOURCE_LIMIT_ERROR_CODE, error
    assert str(_MAX_TOKENS) in error["message"], error
    assert "correlationId" not in error["extensions"]


@pytest.mark.django_db
def test_a_consumer_raised_graphql_error_keeps_its_own_message():
    """Consumer code is trusted: a ``GraphQLError`` IS the statement "this is for the client".

    The classifier is not a heuristic about this package's internals, so a
    resolver a consumer wrote gets the same treatment as a framework rejection
    site, with no registration step.
    """
    _, payload = _post("/ep/", "{ deliberate }")
    error = payload["errors"][0]
    assert error["message"] == "This message was written for the client."
    assert error["extensions"]["code"] == "CONSUMER_REJECTION"
    assert "correlationId" not in error["extensions"]


@pytest.mark.django_db(transaction=True)
def test_a_permission_denial_keeps_its_not_authorized_message():
    """The mutation pipeline's denial is a ``GraphQLError``, so it reaches the client verbatim.

    Masking this one would be a real UX regression rather than a security gain:
    the client cannot distinguish "you may not do this" from "the server broke",
    and would retry. Driven over the SHIPPED ``/graphql/`` mount, so it is the
    deployed schema's auto-installed policy under test, not a probe's.
    """
    create_users(1)
    seed_data(1)
    category = product_models.Category.objects.first()
    _, payload = _post(
        "/graphql/",
        "mutation($d: ItemInput!) { createItem(data: $d) { node { name } errors { field } } }",
        variables={
            "d": {
                "name": "DeniedWidget",
                "categoryId": str(
                    relay.GlobalID(type_name="products.category", node_id=str(category.pk)),
                ),
            },
        },
    )
    assert payload["data"] is None
    assert "Not authorized to" in payload["errors"][0]["message"], payload
    assert not product_models.Item.objects.filter(name="DeniedWidget").exists()


@pytest.mark.django_db(transaction=True)
def test_a_field_error_envelope_is_untouched_because_it_is_data_not_an_error():
    """A validation envelope needs no carve-out - the policy never sees it.

    A form / serializer validation failure is returned in ``data`` as a structured
    payload rather than raised, so it is outside the classifier by construction.
    Asserted rather than assumed, because "the policy ate my validation messages"
    is the failure a future reader would suspect first.
    """
    create_users(1)
    seed_data(1)
    category = product_models.Category.objects.first()
    existing = product_models.Item.objects.create(name="EnvelopeDup", category=category)

    user = get_user_model().objects.get(username="view_item_1")
    user.user_permissions.add(
        Permission.objects.get(codename="add_item", content_type__app_label="products"),
    )
    client = Client()
    client.force_login(get_user_model().objects.get(pk=user.pk))

    _, payload = _post(
        "/graphql/",
        "mutation($d: ItemInput!) { createItem(data: $d) { "
        "node { name } errors { field messages } } }",
        variables={
            "d": {
                "name": existing.name,
                "categoryId": str(
                    relay.GlobalID(type_name="products.category", node_id=str(category.pk)),
                ),
            },
        },
        client=client,
    )
    assert "errors" not in payload, payload
    envelope = payload["data"]["createItem"]
    assert envelope["node"] is None
    assert envelope["errors"][0]["field"] == "__all__"
    # The validation prose reaches the client unaltered - the envelope is data.
    assert envelope["errors"][0]["messages"], envelope


# ---------------------------------------------------------------------------
# Transport parity and the two ways out
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_the_sync_and_async_transports_produce_the_same_masked_entry():
    """One synchronous teardown serves both execution colors (spec-048 Decision 11).

    Both mounts are compared entry-for-entry with only the correlation id removed:
    a per-transport difference in message, path, or extension key would mean a
    client had to know its transport to read an error.
    """
    _, sync_payload = _post("/ep/", "{ boom fine }")
    sync_error = _masked_error(sync_payload)

    async_response = _await_response(
        AsyncTestClient().query(
            "{ boom fine }",
            assert_no_errors=False,
            url="/ep-async/",
        ),
    )
    async_payload = json.loads(async_response.response.content)
    async_error = _masked_error(async_payload)

    assert async_payload["data"] == sync_payload["data"]
    assert sync_error["extensions"]["correlationId"] != async_error["extensions"]["correlationId"]
    sync_error["extensions"].pop("correlationId")
    async_error["extensions"].pop("correlationId")
    assert async_error == sync_error


@pytest.mark.django_db
def test_debug_true_restores_the_original_message_end_to_end():
    """Under ``settings.DEBUG`` the policy is a pass-through, read at OPERATION time.

    The local traceback is the reason the setting exists, and the gate is read per
    operation rather than captured at construction - which this row proves
    incidentally, since the schema is built while the override is already active
    but the sibling rows above built theirs under the ambient ``DEBUG=False``.
    """
    with _override_settings(**_DEBUG_PASS_THROUGH):
        _, payload = _post("/ep/", "{ boom }")
    error = payload["errors"][0]
    assert _SENSITIVE in error["message"], error
    assert "correlationId" not in (error.get("extensions") or {})


@pytest.mark.django_db
@pytest.mark.parametrize(
    "debug_value",
    [
        pytest.param("False", id="string-false"),
        pytest.param(1, id="truthy-int"),
        pytest.param(object(), id="object"),
    ],
)
def test_a_malformed_debug_setting_keeps_production_masking_end_to_end(debug_value):
    """Only an explicit ``DEBUG=True`` opens the development pass-through gate."""
    with _override_settings(
        DEBUG=debug_value,
        MIDDLEWARE=[entry for entry in settings.MIDDLEWARE if "debug_toolbar" not in entry],
    ):
        _, payload = _post("/ep/", "{ boom }")
    error = _masked_error(payload)
    assert _SENSITIVE not in json.dumps(payload)
    assert error["path"] == ["boom"]


@pytest.mark.django_db
def test_a_resolver_cannot_turn_masking_off_by_writing_the_schemas_policy():
    """``info.schema.error_policy`` is a copy, so a resolver write cannot unmask this request."""
    response, payload = _post("/ep/", "{ unmask boom }")
    _masked_error(payload)
    assert payload["data"] == {"unmask": "written", "boom": None}
    body = response.content.decode()
    assert _SENSITIVE not in body, body


@pytest.mark.django_db
def test_a_written_exported_default_cannot_unmask_a_later_schema():
    """The exported default is a value template; masking reads the package's own policy.

    ``DEFAULT_ERROR_POLICY`` is a root export, so any consumer module holds it,
    and a frozen dataclass admits a ``__dict__`` write. The write lands before the
    schema exists - this mount builds one per request - so a schema that read the
    exported object would be built with masking off and would put the resolver's
    own exception text on the wire for every client of the process. The response
    is masked with the package's message and a correlation id instead.

    The assertions run after the write is undone, because the shared helpers read
    the exported policy at call time and a row that compared the response against
    a tampered template would agree with the tampering.
    """
    assert settings.DEBUG is False
    declared = dict(DEFAULT_ERROR_POLICY.__dict__)
    DEFAULT_ERROR_POLICY.__dict__["enabled"] = False
    DEFAULT_ERROR_POLICY.__dict__["message"] = "Written after startup."
    try:
        response, payload = _post("/ep/", "{ boom fine }")
    finally:
        # The export is process-global: a write left behind would answer every
        # later row in the session.
        DEFAULT_ERROR_POLICY.__dict__.update(declared)
    error = _masked_error(payload)
    assert error["path"] == ["boom"]
    assert payload["data"] == {"boom": None, "fine": "fine"}
    assert _SENSITIVE not in response.content.decode()


@pytest.mark.django_db
def test_the_explicit_opt_out_returns_the_original_message_under_debug_false():
    """``error_policy={"enabled": False}`` is the recorded decision to own your own masking.

    Distinct from the ``DEBUG`` gate: this deployment is in production and has
    said so explicitly, which is the point - safety is not opt-in, but opting OUT
    is a written choice rather than an omission.
    """
    assert settings.DEBUG is False
    _, payload = _post("/ep-off/", "{ boom }")
    error = payload["errors"][0]
    assert _SENSITIVE in error["message"], error
    assert "correlationId" not in (error.get("extensions") or {})


@pytest.mark.django_db
def test_a_custom_message_and_extension_key_both_reach_the_wire():
    """Both configurable fields are honored on a real response."""
    _, payload = _post("/ep-custom/", "{ boom }")
    error = payload["errors"][0]
    assert error["message"] == _CUSTOM_MESSAGE
    assert _CORRELATION_ID.fullmatch(error["extensions"][_CUSTOM_KEY])
    assert "correlationId" not in error["extensions"]
    assert _SENSITIVE not in json.dumps(payload)


def _entry_request(entry, query):
    """POST one document to a shared-entry mount through that entry's own view color.

    ``entry`` is the ``(spelling, color)`` key rather than the mount, because the
    mount is display text ``ENTRY_MOUNTS`` derives from that key: reading the color
    back out of the URL would route an async mount through the synchronous client
    the moment the mount naming changes, and the row would still pass.
    """
    _, color = entry
    mount = ENTRY_MOUNTS[entry]
    if color == "async":
        response = _await_response(
            AsyncTestClient().query(query, assert_no_errors=False, url=mount),
        )
        return json.loads(response.response.content)
    _, payload = _post(mount, query)
    return payload


def _assert_masked_and_clean(payload, body):
    """The whole masking contract for one shared-entry row, in one place."""
    error = _masked_error(payload)
    assert _SENSITIVE not in body
    assert error["message"] == DEFAULT_ERROR_POLICY.message
    return error


@pytest.mark.parametrize(
    ("spelling", "color"),
    ENTRY_ROWS,
    ids=ENTRY_IDS,
)
def test_a_nested_operation_does_not_unmask_the_outer_failure(spelling, color):
    """A whole inner operation runs mid-resolver, and the outer failure still masks.

    The masking teardown reads the completed result off this operation's engine
    context. On a shared entry the inner operation assigned its own context over
    that read's source, and the inner result carries no errors - so the teardown
    would find nothing to mask and the outer exception's own text would reach the
    client. No scheduling is involved: one request is enough.

    The following request proves the mount was not left in some other state by
    the nesting.
    """
    entry = (spelling, color)
    payload = _entry_request(entry, "{ nestedThenBoom }")
    _assert_masked_and_clean(payload, json.dumps(payload))
    assert payload["data"] == {"nestedThenBoom": None}

    after = _entry_request(entry, "{ fine }")
    assert after["data"] == {"fine": "fine"}
    assert after.get("errors") is None


@pytest.mark.parametrize(
    ("spelling", "color"),
    ENTRY_ROWS,
    ids=ENTRY_IDS,
)
def test_an_overlapping_request_does_not_unmask_a_failing_one(spelling, color):
    """Two requests overlap on one entry, and the failing one is still masked.

    The failing request is held open between its parse hooks, a benign request
    runs to completion, and only then is the first released. Both a fresh id and
    the policy message have to be on the failing response, and the sensitive text
    on neither.
    """
    entry = (spelling, color)
    _SharedEntryCoordinator.parked.clear()
    _SharedEntryCoordinator.released.clear()
    _SharedEntryCoordinator.armed = True
    overlapped = {}

    def _run_failing():
        overlapped["payload"] = _entry_request(entry, "{ boom }")

    held = threading.Thread(target=_run_failing)
    held.start()
    try:
        assert _SharedEntryCoordinator.parked.wait(timeout=10), "the failing request never parked"
        benign = _entry_request(entry, "{ fine }")
    finally:
        _SharedEntryCoordinator.released.set()
        held.join(timeout=10)
        _SharedEntryCoordinator.armed = False

    assert benign["data"] == {"fine": "fine"}
    assert benign.get("errors") is None
    payload = overlapped["payload"]
    _assert_masked_and_clean(payload, json.dumps(payload))

    after = _entry_request(entry, "{ fine }")
    assert after["data"] == {"fine": "fine"}


# ---------------------------------------------------------------------------
# Masked: a plain exception that escaped a consumer extension HOOK
# ---------------------------------------------------------------------------


def _hook_request(color, mount=None, document="{ fine }"):
    """POST one document to a hook mount of ``color``, returning ``(body, payload)``.

    The color selects both the mount and the client, so an async row cannot be
    answered by the synchronous transport the moment a mount is renamed.
    """
    target = HOOK_MOUNTS[color] if mount is None else mount
    if color == "sync":
        response, payload = _post(target, document)
        return response.content.decode(), payload
    response = _await_response(
        AsyncTestClient().query(document, assert_no_errors=False, url=target),
    )
    body = response.response.content.decode()
    return body, json.loads(body)


def _package_error_records(caplog):
    """Every ``ERROR`` the package logger emitted during one row."""
    return [
        record
        for record in caplog.records
        if record.name == _PACKAGE_LOGGER and record.levelno == logging.ERROR
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(("where", "color"), HOOK_ROWS, ids=HOOK_IDS)
def test_an_exception_from_a_consumer_hook_is_masked_like_a_resolver_exception(where, color):
    """A hook failure is an unexpected exception, and reads as one on the wire.

    A consumer extension raising a plain exception is exactly the resolver case
    one stack frame further out: the message is written by whatever raised, and
    the client is not the reader it was written for. The four halves are their
    own rows because each escapes from a DIFFERENT place - the validation stage,
    the execution stage, and the operation teardown the masking authority itself
    unwinds behind - and a masked surface with a hole shaped like any one of them
    looks identical to a correct one on every resolver row in this file.
    """
    with _failing_hook(where):
        body, payload = _hook_request(color)
    _masked_error(payload)
    assert payload["data"] is None, payload
    assert _SENSITIVE not in body, body
    assert "tenant-42" not in body, body
    assert "RuntimeError" not in body, body


@pytest.mark.django_db
@pytest.mark.parametrize("color", HOOK_COLORS, ids=HOOK_COLORS)
def test_the_hook_correlation_id_reaches_the_server_log_with_the_original_exception(caplog, color):
    """The id a hook failure hands the client resolves to the exception that raised it.

    The same guarantee the resolver row states, over the seam where the masking
    authority's own teardown has already unwound: masking that only deleted the
    message would leave an operator with a support call and nothing to join it to.
    """
    caplog.set_level(logging.ERROR, logger=_PACKAGE_LOGGER)
    with _failing_hook("operation-teardown"):
        _, payload = _hook_request(color)
    correlation_id = _masked_error(payload)["extensions"]["correlationId"]

    records = _package_error_records(caplog)
    assert len(records) == 1, caplog.records
    record = records[0]
    assert correlation_id in record.getMessage()
    assert record.exc_info is not None
    assert isinstance(record.exc_info[1], RuntimeError)
    assert str(record.exc_info[1]) == _SENSITIVE
    assert record.exc_info[2] is not None  # the traceback the operator needs


@pytest.mark.django_db
@pytest.mark.parametrize(("where", "color"), HOOK_ROWS, ids=HOOK_IDS)
def test_one_hook_failure_produces_exactly_one_masked_entry_and_one_log_record(
    caplog,
    where,
    color,
):
    """One failure is masked once, whichever seam ends up doing it.

    The operation teardown and the schema's own return of the result upstream
    built are both masking seams, and a failure that travelled through both would
    show it here twice over: two entries on the wire, two correlation ids, or two
    server log records for one exception - and a second id would name a log record
    the client's first id does not.
    """
    caplog.set_level(logging.ERROR, logger=_PACKAGE_LOGGER)
    with _failing_hook(where):
        _, payload = _hook_request(color)

    assert len(payload["errors"]) == 1, payload
    records = _package_error_records(caplog)
    assert len(records) == 1, caplog.records
    assert payload["errors"][0]["extensions"]["correlationId"] in records[0].getMessage()


@pytest.mark.django_db
@pytest.mark.parametrize("color", HOOK_COLORS, ids=HOOK_COLORS)
def test_debug_true_restores_the_original_hook_message(color):
    """The development pass-through covers the hook seam as well as the resolver one."""
    with _override_settings(**_DEBUG_PASS_THROUGH), _failing_hook("operation-teardown"):
        _, payload = _hook_request(color)
    error = payload["errors"][0]
    assert _SENSITIVE in error["message"], error
    assert "correlationId" not in (error.get("extensions") or {})


@pytest.mark.django_db
@pytest.mark.parametrize("color", HOOK_COLORS, ids=HOOK_COLORS)
def test_the_explicit_opt_out_returns_the_original_hook_message(color):
    """``error_policy={"enabled": False}`` is honored at the hook seam too."""
    assert settings.DEBUG is False
    with _failing_hook("operation-teardown"):
        _, payload = _hook_request(color, mount=HOOK_OFF_MOUNTS[color])
    error = payload["errors"][0]
    assert _SENSITIVE in error["message"], error
    assert "correlationId" not in (error.get("extensions") or {})


@pytest.mark.django_db
@pytest.mark.parametrize(("where", "color"), HOOK_ROWS, ids=HOOK_IDS)
def test_a_hook_raising_a_graphql_error_keeps_its_own_message(where, color):
    """A hook's deliberate ``GraphQLError`` is a client-facing statement and travels.

    The same structural rule the resolver rows state, asked at the seam this file's
    other hook rows mask: what is masked is an exception nobody wrote for the
    client, not every exception a hook can raise.
    """
    with _failing_hook(where, build=_deliberate_hook_exception):
        _, payload = _hook_request(color)
    assert len(payload["errors"]) == 1, payload
    error = payload["errors"][0]
    assert error["message"] == _DELIBERATE_HOOK_MESSAGE, error
    assert error["extensions"]["code"] == "CONSUMER_HOOK_REJECTION", error
    assert "correlationId" not in error["extensions"], error
