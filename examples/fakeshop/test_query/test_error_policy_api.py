"""Live ``/graphql/`` production-error-policy acceptance tests (spec-048).

``ErrorPolicy`` is a promise about what a REAL client reads out of a REAL
response, so the category matrix is pinned where a client can see it: over
``django.test.Client`` against mounts of the package's own Django GraphQL view,
reading the JSON envelope.

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
- **untouched, deliberate** - anything raised as a ``GraphQLError``: the
  ``GLOBALID_INVALID`` boundary, a ``RESOURCE_LIMIT_EXCEEDED`` rejection, the
  mutation pipeline's ``"Not authorized to ..."`` denial, and a consumer's own
  ``GraphQLError``. A ``FieldError`` envelope needs no column at all - it is
  returned in ``data``, so nothing classifies it.

Around the matrix sit the properties a single row cannot state: one FRESH id per
masked error, the id reaching the server log with the original traceback, the
retained ``path``, sync/async parity, and the two ways out (``DEBUG=True`` and
``error_policy={"enabled": False}``).

The scaffolding is one probe-schema factory over fakeshop's own ``Query`` /
``Mutation``, extended with resolvers that raise on demand - a real schema
carrying deliberate failures, rather than a synthetic one that would not exercise
the framework's own rejection sites. It is built per request rather than cached
because the acceptance tier reloads ``config.schema`` before every test.

``tests/test_error_policy.py`` holds what no request can express: the policy
object's validation and precedence ladder, the correlation-id format, the
extension's install position, and the standalone-schema fallback.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re

import pytest
import strawberry
from apps.products import models as product_models
from apps.products.services import create_users, seed_data
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import AsyncClient, Client
from django.test import override_settings as _override_settings
from django.urls import include, path
from graphql import GraphQLError
from strawberry import relay

from django_strawberry_framework import (
    RESOURCE_LIMIT_ERROR_CODE,
    DjangoSchema,
    strawberry_config,
)
from django_strawberry_framework.error_policy import DEFAULT_ERROR_POLICY
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
        """The fakeshop query surface plus four deliberate failure modes."""

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

urlpatterns = [
    path("", include("config.urls")),
    path("ep/", _probe_view()),
    path("ep-async/", _probe_async_view()),
    path("ep-off/", _probe_view(error_policy={"enabled": False})),
    path(
        "ep-custom/",
        _probe_view(
            error_policy={"message": _CUSTOM_MESSAGE, "correlation_extension_key": _CUSTOM_KEY},
        ),
    ),
    path("ep-limits/", _probe_view(resource_policy={"max_document_tokens": _MAX_TOKENS})),
]


def _post(
    mount,
    query,
    variables=None,
    *,
    client=None,
):
    """POST one GraphQL document to a mount and return ``(response, parsed envelope)``."""
    body = {"query": query}
    if variables is not None:
        body["variables"] = variables
    response = (client or Client()).post(
        mount,
        data=json.dumps(body),
        content_type="application/json",
    )
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
    """Run one ``AsyncClient`` coroutine to completion on a fresh event loop."""
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
    error = payload["errors"][0]
    assert "Cannot query field 'noSuchFieldAnywhere'" in error["message"], error
    assert "correlationId" not in (error.get("extensions") or {})


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

    response = AsyncClient().post(
        "/ep-async/",
        data=json.dumps({"query": "{ boom fine }"}),
        content_type="application/json",
    )
    async_payload = json.loads(_await_response(response).content)
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
