"""Live ``/graphql/`` execution-resource-policy acceptance tests (spec-047).

Every bound in ``ResourcePolicy`` is a promise about what a real request over the
wire can spend, so the boundaries are pinned where a real request can reach them:
against mounts of the package's own Django GraphQL view, over
``django.test.Client``, with the rejection read out of the JSON envelope.

The scaffolding is one cached schema factory. Each mount narrows ONE family of
bounds and leaves every other bound at its package default, so a row that
rejects can only have rejected on the bound it is about - a single
tightened-everything schema would let a token bound silently absorb a row
written about node ids. The factory is cached per policy so a worker builds each
probe schema once.

Row groups, in the order a request meets them:

- the document text bounds (tokens, structural depth) - charged before the parse;
- the expanded-document bounds (selections, aliases, collection cost) - charged
  after validation, with fragment / alias / directive evasion rows;
- the value bounds (node ids, membership items, relation ids, nested rows,
  container width, value depth, input nodes, scalar bytes, uploads) - charged
  over a TINY document carrying a LARGE variable payload, which is the shape
  document limits cannot see, including the two shapes only a real request
  builds: one variable spliced into two fields (the same Python object twice) and
  a nested value whose depth no bracket in the document reflects;
- introspection, charged like any other document shape rather than exempted;
- the collection bounds the fields enforce (raw-list rows, connection page size,
  and the list sibling that used to bypass the connection cap);
- the cooperative deadline, one row per seam that hands work to the database; and
- the cross-cutting proofs: zero ORM work after a rejection, and one typed error
  code shared by the sync and async transports.

``examples/fakeshop/tests`` and ``tests/test_resource_policy.py`` hold what a
live request cannot reach: policy construction and validation, the
settings/constructor precedence ladder, the narrowing rule, and the walker's
degenerate inputs.
"""

from __future__ import annotations

import json
from functools import cache

import pytest
from apps.products.services import seed_data
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import AsyncClient, Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import include, path

from django_strawberry_framework import (
    RESOURCE_LIMIT_ERROR_CODE,
    DjangoSchema,
    strawberry_config,
)
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

pytestmark = pytest.mark.urls(__name__)


#: Settings that open the spec-048 error policy's pass-through gate for ONE live
#: request. ``settings.DEBUG`` is the gate, and on this tier it is the only
#: reachable instrument - the project schema is constructed by the app, not by the
#: test. Fakeshop's shipped settings also wire django-debug-toolbar behind
#: ``DEBUG``, so the toolbar middleware is dropped for the duration: left in, it
#: would try to inject a panel referencing the ``djdt`` routes that ``config.urls``
#: computed under the ambient ``DEBUG=False`` and fail the request for a reason
#: that has nothing to do with the row. Dropping the middleware is the deterministic
#: form of that - the toolbar's own show-gate is memoized per process, so overriding
#: its callback would not reliably take effect.
_ERROR_POLICY_PASS_THROUGH = {
    "DEBUG": True,
    "MIDDLEWARE": [entry for entry in settings.MIDDLEWARE if "debug_toolbar" not in entry],
}


@cache
def _probe_schema(overrides: tuple[tuple[str, int], ...]) -> DjangoSchema:
    """Build (once per worker) a schema over fakeshop's types with a narrowed policy.

    The optimizer is deliberately NOT installed on these probe schemas: the
    subject is the budget, and leaving the optimizer out keeps the query counts a
    rejection row asserts about attributable to the rejection alone.
    """
    from config.schema import Mutation, Query

    return DjangoSchema(
        query=Query,
        mutation=Mutation,
        config=strawberry_config(),
        resource_policy=dict(overrides),
    )


def _probe_view(**overrides: float):
    """Mount the package view over a probe schema narrowing exactly ``overrides``."""
    frozen = tuple(sorted(overrides.items()))

    def view(request, *args, **kwargs):
        built = DjangoGraphQLView.as_view(schema=_probe_schema(frozen))
        return built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


def _probe_upload_view(**overrides: int):
    """The upload twin: same probe schema, with upstream's multipart handling on."""
    frozen = tuple(sorted(overrides.items()))

    def view(request, *args, **kwargs):
        built = DjangoGraphQLView.as_view(
            schema=_probe_schema(frozen),
            multipart_uploads_enabled=True,
        )
        return built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


def _probe_async_view(**overrides: int):
    """The async twin of ``_probe_view``, so parity is proven on a real event loop."""
    frozen = tuple(sorted(overrides.items()))

    async def view(request, *args, **kwargs):
        built = AsyncDjangoGraphQLView.as_view(schema=_probe_schema(frozen))
        return await built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


MAX_TOKENS = 40
MAX_DEPTH = 6
MAX_SELECTIONS = 12
MAX_ALIASES = 3
MAX_COST = 5_000
MAX_LIST_ROWS = 3
MAX_PAGE_SIZE = 5
MAX_NODE_IDS = 3
MAX_MEMBERSHIP = 4
MAX_RELATION_IDS = 2
MAX_RELATION_IDS_TOTAL = 3
MAX_CONTAINER_WIDTH = 6
MAX_VALUE_DEPTH = 4
MAX_INPUT_NODES = 20
MAX_SCALAR_BYTES = 32
MAX_UPLOAD_COUNT = 1
MAX_UPLOAD_FILE_BYTES = 64
MAX_UPLOAD_TOTAL_BYTES = 96

#: A deadline small enough that it has always passed by the time a resolver
#: runs, which is what makes the cooperative seams assertable without a sleep.
DEADLINE_SECONDS = 0.000_001

_VALUE_BOUNDS = {
    "max_node_ids": MAX_NODE_IDS,
    "max_membership_items": MAX_MEMBERSHIP,
    "max_relation_ids_per_mutation": MAX_RELATION_IDS,
    "max_relation_ids_total": MAX_RELATION_IDS_TOTAL,
    "max_container_width": MAX_CONTAINER_WIDTH,
    "max_input_nodes": MAX_INPUT_NODES,
    "max_scalar_bytes": MAX_SCALAR_BYTES,
}

urlpatterns = [
    path("", include("config.urls")),
    path("rp-tokens/", _probe_view(max_document_tokens=MAX_TOKENS)),
    path("rp-depth/", _probe_view(max_depth=MAX_DEPTH)),
    path(
        "rp-shape/",
        _probe_view(max_selections=MAX_SELECTIONS, max_aliases=MAX_ALIASES),
    ),
    path("rp-cost/", _probe_view(max_collection_cost=MAX_COST)),
    path("rp-values/", _probe_view(**_VALUE_BOUNDS)),
    path("rp-value-depth/", _probe_view(max_value_depth=MAX_VALUE_DEPTH)),
    path("rp-deadline/", _probe_view(execution_deadline_seconds=DEADLINE_SECONDS)),
    path("rp-values-async/", _probe_async_view(**_VALUE_BOUNDS)),
    path(
        "rp-rows/",
        _probe_view(max_list_rows=MAX_LIST_ROWS, max_page_size=MAX_PAGE_SIZE),
    ),
    path(
        "rp-uploads/",
        _probe_upload_view(
            max_upload_count=MAX_UPLOAD_COUNT,
            max_upload_file_bytes=MAX_UPLOAD_FILE_BYTES,
            max_upload_total_bytes=MAX_UPLOAD_TOTAL_BYTES,
        ),
    ),
]


def _post(
    mount,
    query,
    variables=None,
    *,
    client=None,
):
    """POST one GraphQL document to a probe mount and return the parsed envelope."""
    body = {"query": query}
    if variables is not None:
        body["variables"] = variables
    response = (client or Client()).post(
        mount,
        data=json.dumps(body),
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    return response.json()


def _rejection(payload):
    """Return the single resource rejection in ``payload``, asserting its shape.

    Every row funnels through here, so "the request was rejected" always means
    the SAME thing: no data, exactly one error, and the one typed code. A row
    that merely asserted "errors is non-empty" would pass on a validation error
    or a resolver crash.
    """
    assert payload["data"] is None, payload
    errors = payload["errors"]
    assert len(errors) == 1, errors
    extensions = errors[0]["extensions"]
    assert extensions["code"] == RESOURCE_LIMIT_ERROR_CODE, extensions
    return extensions


def _no_rejection(payload):
    """Assert ``payload`` carries no resource rejection (it may carry other errors).

    The under/at-boundary half of each pair. It deliberately does NOT demand a
    fully successful response: several at-boundary rows drive write surfaces that
    answer with a permission or validation error, and a row about a resource
    bound must not silently start asserting the auth contract instead.
    """
    for error in payload.get("errors") or []:
        assert (error.get("extensions") or {}).get("code") != RESOURCE_LIMIT_ERROR_CODE, payload


# ---------------------------------------------------------------------------
# Document text bounds: charged before the parse
# ---------------------------------------------------------------------------


def test_document_under_the_token_bound_executes():
    payload = _post("/rp-tokens/", "{ __typename }")
    _no_rejection(payload)
    assert payload["data"]["__typename"] == "Query"


def test_document_over_the_token_bound_is_rejected():
    """Tokens are charged on the raw text, so the document never reaches the parser."""
    fields = " ".join(f"a{index}: __typename" for index in range(MAX_TOKENS))
    extensions = _rejection(_post("/rp-tokens/", "{ %s }" % fields))
    assert extensions["bound"] == "max_document_tokens"
    assert extensions["limit"] == MAX_TOKENS
    assert extensions["charged"] == MAX_TOKENS + 1


def test_document_over_the_depth_bound_is_rejected():
    """Structural nesting is charged before the parse, so deep documents cannot recurse it."""
    query = "{ " * (MAX_DEPTH + 1) + "__typename" + " }" * (MAX_DEPTH + 1)
    extensions = _rejection(_post("/rp-depth/", query))
    assert extensions["bound"] == "max_depth"
    assert extensions["charged"] == MAX_DEPTH + 1


def test_depth_counts_argument_and_input_object_nesting():
    """Argument and input-object brackets count toward depth, as the bound documents.

    The scan runs before the parse, where nothing distinguishes an argument list
    from a selection set. Pinning it here means the pre-parse bound's shape is a
    contract rather than an implementation detail a later reader might "fix".
    """
    query = (
        "{ allLibraryGenres(filter: { and: [ { and: [ { and: "
        '[ { name: { exact: "x" } } ] } ] } ] }) { name } }'
    )
    extensions = _rejection(_post("/rp-depth/", query))
    assert extensions["bound"] == "max_depth"


# ---------------------------------------------------------------------------
# Expanded-document bounds: fragments, aliases, directives, collection cost
# ---------------------------------------------------------------------------


def test_selections_are_charged_after_fragment_expansion():
    """A fragment is charged at EVERY spread site, so spreading it N times costs N times.

    The evasion this closes: moving a selection set into a fragment and spreading
    it repeatedly leaves the document small while the executed selection set is
    not.
    """
    spreads = " ".join("g%d: allLibraryGenres { ...F }" % index for index in range(4))
    query = "{ %s } fragment F on GenreType { name id }" % spreads
    extensions = _rejection(_post("/rp-shape/", query))
    assert extensions["bound"] in {"max_selections", "max_aliases"}


def test_a_directive_does_not_hide_a_selection_from_accounting():
    """``@skip`` changes what is RETURNED, never what is charged.

    Charging only the fields a directive lets through would make ``@skip(if:
    true)`` a free pass around every document bound.
    """
    fields = " ".join(
        f"s{index}: __typename @skip(if: true)" for index in range(MAX_SELECTIONS + 2)
    )
    extensions = _rejection(_post("/rp-shape/", "{ %s }" % fields))
    assert extensions["bound"] in {"max_selections", "max_aliases"}


def test_the_same_field_under_many_aliases_is_charged_once_per_alias():
    aliased = " ".join(f"a{index}: __typename" for index in range(MAX_ALIASES + 1))
    extensions = _rejection(_post("/rp-shape/", "{ %s }" % aliased))
    assert extensions["bound"] == "max_aliases"
    assert extensions["charged"] == MAX_ALIASES + 1


def test_nested_collections_are_charged_multiplicatively():
    """Two nested full pages cost their product, which is what the cost bound sees."""
    query = """
    {
      allCategories {
        edges { node { itemsConnection { edges { node { name } } } } }
      }
    }
    """
    extensions = _rejection(_post("/rp-cost/", query))
    assert extensions["bound"] == "max_collection_cost"
    assert extensions["charged"] > MAX_COST


def test_an_introspection_document_is_charged_like_any_other():
    """Introspection is a document shape, not an exemption.

    ``__schema`` opens a subtree over every type, field and argument in the
    schema. A walk that could not resolve the meta-fields charged the whole of
    it as one selection and then stopped descending, so introspection was the
    one shape no depth, selection, or collection bound could see. Here the
    nested ``types { fields { ... } }`` lists charge multiplicatively like any
    other nested collection.
    """
    extensions = _rejection(_post("/rp-cost/", "{ __schema { types { fields { name } } } }"))
    assert extensions["bound"] == "max_collection_cost"
    assert extensions["charged"] > MAX_COST


def test_an_explicit_small_page_narrows_the_collection_cost():
    """``first:`` narrows the charge, so a client that asks for less is charged less."""
    query = """
    {
      allCategories(first: 2) {
        edges { node { itemsConnection(first: 2) { edges { node { name } } } } }
      }
    }
    """
    _no_rejection(_post("/rp-cost/", query))


# ---------------------------------------------------------------------------
# Value bounds: a tiny document carrying a large variable payload
# ---------------------------------------------------------------------------

_NODES = "query N($ids: [ID!]!) { nodes(ids: $ids) { __typename } }"
_GENRE_IN = "query G($ids: [String!]) { allLibraryGenres(filter: { id: { in: $ids } }) { name } }"
_GENRE_FILTER = "query G($f: GenreFilterInputType) { allLibraryGenres(filter: $f) { name } }"


@pytest.mark.django_db
def test_node_refetch_ids_at_the_bound_are_not_rejected():
    _no_rejection(_post("/rp-values/", _NODES, {"ids": ["x"] * MAX_NODE_IDS}))


@pytest.mark.django_db
def test_node_refetch_ids_over_the_bound_are_rejected_before_any_id_is_decoded():
    """A tiny document with a large variable payload - the shape S4 names.

    The rejection is charged from the variable list, so no GlobalID is decoded
    and no queryset is built; the query-count assertion is the evidence, since a
    decoded id would have driven at least one lookup.
    """
    seed_data(1)
    with CaptureQueriesContext(connection) as captured:
        payload = _post("/rp-values/", _NODES, {"ids": ["x"] * (MAX_NODE_IDS + 1)})
    extensions = _rejection(payload)
    assert extensions["bound"] == "max_node_ids"
    assert extensions["charged"] == MAX_NODE_IDS + 1
    assert captured.captured_queries == []


@pytest.mark.django_db
def test_duplicate_node_ids_are_charged_positionally():
    """Duplicates cost what they cost: the framework reassembles every position.

    The database may collapse an ``IN`` predicate, but ``DjangoNodesField``
    preserves duplicates positionally, so charging the deduplicated width would
    charge for work the request does not do.
    """
    extensions = _rejection(_post("/rp-values/", _NODES, {"ids": ["same"] * (MAX_NODE_IDS + 1)}))
    assert extensions["charged"] == MAX_NODE_IDS + 1


@pytest.mark.django_db
def test_an_empty_id_list_is_not_rejected():
    _no_rejection(_post("/rp-values/", _NODES, {"ids": []}))


@pytest.mark.django_db
def test_membership_list_over_the_bound_is_rejected():
    extensions = _rejection(_post("/rp-values/", _GENRE_IN, {"ids": ["1"] * (MAX_MEMBERSHIP + 1)}))
    assert extensions["bound"] == "max_membership_items"


@pytest.mark.django_db
def test_membership_list_at_the_bound_is_not_rejected():
    _no_rejection(_post("/rp-values/", _GENRE_IN, {"ids": ["1"] * MAX_MEMBERSHIP}))


@pytest.mark.django_db
def test_a_wide_filter_tree_is_charged_by_container_width():
    """An ``and``/``or`` tree's WIDTH is bounded, not only its depth."""
    branches = ", ".join('{ name: { exact: "x" } }' for _ in range(MAX_CONTAINER_WIDTH + 1))
    query = "{ allLibraryGenres(filter: { and: [%s] }) { name } }" % branches
    extensions = _rejection(_post("/rp-values/", query))
    assert extensions["bound"] == "max_container_width"


@pytest.mark.django_db
def test_relation_ids_in_one_mutation_are_bounded():
    mutation = (
        "mutation B($d: BookInput!) { createBookViaCustomInput(data: $d) "
        "{ node { title } errors { field messages } } }"
    )
    variables = {
        "d": {
            "title": "t",
            "subtitle": "s",
            "shelfId": 1,
            "genres": ["1"] * (MAX_RELATION_IDS + 1),
        },
    }
    extensions = _rejection(_post("/rp-values/", mutation, variables))
    assert extensions["bound"] == "max_relation_ids_per_mutation"


@pytest.mark.django_db
def test_relation_ids_across_several_mutation_fields_are_bounded_in_aggregate():
    """Two writes that each pass the per-field bound can still exceed the request's.

    Serial mutation fields are one request's worth of work, so the aggregate
    bound is the one that sees a batch assembled out of individually-legal
    writes.
    """
    mutation = """
    mutation B($a: BookInput!, $b: BookInput!) {
      first: createBookViaCustomInput(data: $a) { node { title } }
      second: createBookViaCustomInput(data: $b) { node { title } }
    }
    """
    payload = {
        "title": "t",
        "subtitle": "s",
        "shelfId": 1,
        "genres": ["1", "2"],
    }
    extensions = _rejection(
        _post("/rp-values/", mutation, {"a": payload, "b": dict(payload)}),
    )
    assert extensions["bound"] == "max_relation_ids_total"
    assert extensions["charged"] == 4


@pytest.mark.django_db
def test_one_variable_spliced_into_two_mutation_fields_is_charged_twice():
    """The bypass a charge-once-per-container cache left open, over the wire.

    ``$g`` is ONE Python list object, and splicing it into two mutation fields
    resolves to that same object both times. Charging a container once per
    request therefore charged the second field's relation ids as free - two
    fields of two ids apiece counted as two - and the aggregate bound never
    fired. Every reference is work, so every reference is charged: 4 against an
    aggregate of 3.
    """
    mutation = """
    mutation B($g: [ID!]!) {
      first: createBookViaCustomInput(
        data: { title: "t", subtitle: "s", shelfId: 1, genres: $g }
      ) { node { title } }
      second: createBookViaCustomInput(
        data: { title: "u", subtitle: "s", shelfId: 1, genres: $g }
      ) { node { title } }
    }
    """
    extensions = _rejection(_post("/rp-values/", mutation, {"g": ["1", "2"]}))
    assert extensions["bound"] == "max_relation_ids_total"
    assert extensions["charged"] == 4


@pytest.mark.django_db
def test_a_deeply_nested_variable_value_is_rejected_on_value_depth():
    """The bound the pre-parse depth scan structurally cannot supply.

    ``max_depth`` counts brackets in the document TEXT; this document has three
    of them however deep its variable is. Without a value-depth bound a
    10,000-deep payload passes every document bound and every total, because
    each level is one node wide.
    """
    payload = {"and": [{"and": [{"name": {"exact": "x"}}]}]}
    extensions = _rejection(
        _post("/rp-value-depth/", _GENRE_FILTER, {"f": payload}),
    )
    assert extensions["bound"] == "max_value_depth"
    assert extensions["limit"] == MAX_VALUE_DEPTH


@pytest.mark.django_db
def test_a_shallow_variable_value_is_not_rejected_on_value_depth():
    _no_rejection(_post("/rp-value-depth/", _GENRE_FILTER, {"f": {"name": {"exact": "x"}}}))


@pytest.mark.django_db
def test_a_scalar_larger_than_the_byte_bound_is_rejected():
    mutation = (
        "mutation S($d: ShelfSerializerInput!) { createShelfViaSerializer(data: $d) "
        "{ result { code } errors { field messages } } }"
    )
    variables = {"d": {"code": "c" * (MAX_SCALAR_BYTES + 1), "branchId": 1}}
    extensions = _rejection(_post("/rp-values/", mutation, variables))
    assert extensions["bound"] == "max_scalar_bytes"
    assert extensions["charged"] == MAX_SCALAR_BYTES + 1


@pytest.mark.django_db
def test_total_input_nodes_are_bounded_across_several_arguments():
    """Several individually-legal arguments can still exhaust the request's node budget."""
    branches = ", ".join(
        '{ name: { exact: "x" }, id: { exact: "1" } }' for _ in range(MAX_CONTAINER_WIDTH)
    )
    query = "{ allLibraryGenres(filter: { or: [%s] }) { name } }" % branches
    extensions = _rejection(_post("/rp-values/", query))
    assert extensions["bound"] == "max_input_nodes"


# ---------------------------------------------------------------------------
# Uploads: the bytes the transport body cap deliberately never measures
# ---------------------------------------------------------------------------


def _multipart(
    client,
    mount,
    query,
    variables,
    files,
):
    """POST a GraphQL multipart request with ``files`` mapped into ``variables``."""
    body = {
        "operations": json.dumps({"query": query, "variables": variables}),
        "map": json.dumps({name: [path] for name, path in files}),
    }
    for name, _ in files:
        body[name] = SimpleUploadedFile(f"{name}.bin", b"z" * 200)
    return client.post(mount, data=body)


_SPECIMEN = (
    "mutation M($d: MediaSpecimenInput!) { createMediaSpecimen(data: $d) "
    "{ result { label } errors { field messages } } }"
)


@pytest.mark.django_db
def test_an_oversized_upload_is_rejected_by_the_policy_not_by_the_body_cap():
    """The multipart body is never materialized by the transport cap, so this is the bound.

    ``MAX_REQUEST_BODY_BYTES`` deliberately does not measure a multipart body -
    reading it would defeat Django's streaming upload handlers - which is exactly
    why per-file and aggregate upload bytes are the resource policy's job.
    """
    response = _multipart(
        Client(),
        "/rp-uploads/",
        _SPECIMEN,
        {"d": {"label": "l", "attachment": None, "image": None}},
        [("0", "variables.d.attachment"), ("1", "variables.d.image")],
    )
    assert response.status_code == 200, response.content
    extensions = _rejection(response.json())
    assert extensions["bound"] in {
        "max_upload_count",
        "max_upload_file_bytes",
        "max_upload_total_bytes",
    }


# ---------------------------------------------------------------------------
# Collection bounds the fields enforce
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_a_raw_root_list_stops_at_the_configured_maximum():
    """``DjangoListField`` is bounded whether or not the field says anything."""
    seed_data(2)
    payload = _post("/rp-rows/", "{ allLibraryBranchesViaListField { name } }")
    _no_rejection(payload)
    assert len(payload["data"]["allLibraryBranchesViaListField"]) <= MAX_LIST_ROWS


@pytest.mark.django_db
def test_the_list_sibling_cannot_bypass_the_connection_page_cap():
    """The bypass S3 names, closed from both ends.

    ``CategoryType.items`` is an explicit ``"both"`` opt-in, so the raw list
    sibling still exists - and it is bounded by ``max_list_rows`` rather than
    being the unbounded escape hatch beside a capped ``itemsConnection``.
    """
    seed_data(3)
    payload = _post(
        "/rp-rows/",
        "{ allCategories(first: 2) { edges { node { items { name } } } } }",
    )
    _no_rejection(payload)
    for edge in payload["data"]["allCategories"]["edges"]:
        assert len(edge["node"]["items"]) <= MAX_LIST_ROWS


@pytest.mark.django_db
@override_settings(**_ERROR_POLICY_PASS_THROUGH)
def test_a_connection_page_larger_than_the_policy_is_refused():
    """The policy is a ceiling over ``relay_max_results``, never a replacement for it.

    The refusal here comes from Strawberry's own ``relay_max_results`` check, which
    raises a plain ``ValueError`` rather than a ``GraphQLError`` - so the spec-048
    error policy classifies it as unexpected and masks its wording, and the bound in
    that wording is exactly what this row reads to prove the ceiling was lowered.
    ``DEBUG=True`` opens the policy's pass-through gate so the live request returns
    the ceiling's own message. The instrument is the gate rather than
    ``error_policy={"enabled": False}`` because the mounts here come from one
    ``@cache``-d ``_probe_schema`` shared by the whole suite: an opt-out at
    construction would silently change every other row's response boundary too.
    """
    seed_data(1)
    payload = _post(
        "/rp-rows/",
        "{ allCategories(first: %d) { edges { node { name } } } }" % (MAX_PAGE_SIZE + 1),
    )
    assert payload["data"] is None
    assert "cannot be higher than %d" % MAX_PAGE_SIZE in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_the_connection_only_default_leaves_no_raw_list_sibling():
    """``CategoryType.properties`` declares nothing, so the SDL carries no list form.

    The live half of the ``DEFAULT_RELATION_SHAPE`` flip: the raw sibling is
    absent from the schema, not merely bounded, so there is nothing to select.
    """
    payload = _post(
        "/rp-rows/",
        "{ allCategories(first: 1) { edges { node { properties { id } } } } }",
    )
    assert payload["data"] is None
    assert "Cannot query field 'properties'" in payload["errors"][0]["message"]


# ---------------------------------------------------------------------------
# The cooperative deadline, at every seam that hands work to the database
# ---------------------------------------------------------------------------


def _deadline_rejection(payload):
    """Return the deadline rejection in ``payload``, asserting it is the only error.

    Separate from ``_rejection`` because a deadline fires from inside a resolver
    rather than before execution, so the envelope is graphql-core's own
    resolver-error shape: the typed error rides in ``errors`` and ``data`` is
    nulled by the non-null field it propagated through.
    """
    errors = payload["errors"]
    assert len(errors) == 1, errors
    extensions = errors[0]["extensions"]
    assert extensions["code"] == RESOURCE_LIMIT_ERROR_CODE, extensions
    assert extensions["bound"] == "execution_deadline_seconds", extensions
    return extensions


@pytest.mark.django_db
def test_a_passed_deadline_stops_a_connection_before_it_reaches_the_database():
    """The connection seam: the head both ``resolve_connection`` entry points share."""
    seed_data(1)
    with CaptureQueriesContext(connection) as captured:
        payload = _post(
            "/rp-deadline/",
            "{ allCategories(first: 1) { edges { node { name } } } }",
        )
    extensions = _deadline_rejection(payload)
    assert extensions["limit"] == 1
    assert captured.captured_queries == []


@pytest.mark.django_db
def test_a_passed_deadline_stops_a_raw_list_before_it_reaches_the_database():
    """The ``bounded_rows`` seam, shared by both raw-list spellings."""
    seed_data(1)
    with CaptureQueriesContext(connection) as captured:
        payload = _post("/rp-deadline/", "{ allLibraryBranchesViaListField { name } }")
    _deadline_rejection(payload)
    assert captured.captured_queries == []


@pytest.mark.django_db
def test_a_passed_deadline_stops_a_relay_refetch_before_any_id_is_decoded():
    """The Relay refetch seam: a decode is what makes the query inevitable."""
    seed_data(1)
    with CaptureQueriesContext(connection) as captured:
        payload = _post("/rp-deadline/", _NODES, {"ids": ["x"]})
    _deadline_rejection(payload)
    assert captured.captured_queries == []


@pytest.mark.django_db
def test_a_passed_deadline_stops_a_write_before_its_transaction_opens():
    """The write seam: refusing before ``transaction.atomic()`` leaves nothing to unwind."""
    mutation = (
        'mutation { createBookViaCustomInput(data: { title: "t", subtitle: "s", shelfId: 1 }) '
        "{ node { title } errors { field messages } } }"
    )
    payload = _post("/rp-deadline/", mutation)
    _deadline_rejection(payload)


@pytest.mark.django_db
def test_an_unarmed_deadline_never_rejects():
    """The default policy carries no deadline, so no seam may reject on one."""
    seed_data(1)
    _no_rejection(_post("/rp-rows/", "{ allLibraryBranchesViaListField { name } }"))


# ---------------------------------------------------------------------------
# Cross-cutting: one typed code on both transports
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_sync_and_async_transports_share_one_typed_error_code():
    """The rejection is a ``GraphQLError``, so no transport translates it.

    Sync and async mounts of the package view must answer with the same code,
    the same bound, and the same charge - a per-transport difference here would
    mean a client cannot recognize the failure without knowing its transport.
    """
    variables = {"ids": ["x"] * (MAX_NODE_IDS + 1)}
    sync_extensions = _rejection(_post("/rp-values/", _NODES, variables))

    async_client = AsyncClient()
    response = async_client.post(
        "/rp-values-async/",
        data=json.dumps({"query": _NODES, "variables": variables}),
        content_type="application/json",
    )
    async_payload = json.loads(_await_response(response).content)
    assert _rejection(async_payload) == sync_extensions


def _await_response(coroutine):
    """Run one ``AsyncClient`` coroutine to completion on a fresh event loop."""
    import asyncio

    return asyncio.run(_resolve(coroutine))


async def _resolve(coroutine):
    return await coroutine
