"""Live /graphql pagination error containment and ``totalCount`` gating for connections.

Covers the exception-containment invariant for the connection surface:
malformed pagination arguments (negative ``first``/``last``, over-cap ``first``,
malformed ``after``/``before`` cursors) must surface as ``GraphQLError``
entries, never as raw ``ValueError``/``TypeError`` tracebacks. Offset and
keyset connections each pin negative ``first`` and over-cap ``first``: the
keyset slicer cannot reuse ``SliceMetadata.from_arguments``. Exercised
through the live ``/graphql/`` HTTP endpoint (``django.test.Client``) so the
full Strawberry ``ConnectionExtension`` stack is involved - the
through-schema mandate for connections.

The ``Meta.connection`` opt-in is pinned here too, read off the two shipped
shapes it produces: the products connections declare no ``connection`` key, so
``totalCount`` is not a field of their generated connection type at all, while
``GenreType.Meta.connection`` opts in and its connection both declares and
resolves one. The generated non-opted connection type's inherited SDL
description is read from the same endpoint, since that description is the only
part of the bare shape a client can observe. Sidecar argument presence follows
the node type: ``allLibraryGenresConnection`` publishes ``filter:`` and
``orderBy:``; ``allLibraryIssuesConnection`` publishes ``orderBy:`` only.

The post-``OrderSet`` seal on the connection field is pinned here as well. The
connection takes the Relay window on whatever ordering returned, so a consumer
``apply_sync`` override handing back an evaluated, materialized, projected,
wrong-model, sliced, combined, awaitable, re-routed or unrebuildable-state
value would otherwise
produce a silently wrong page or foreign rows. One row per defect shape
(``materialized-list`` and ``none`` share the ``type`` branch) drives
``GenreOrder.apply_sync`` on the shipped ``allLibraryGenresConnection`` and
asserts both the exact rejection and that no ``library_genre`` read happened
that the defect should have prevented; a ``super()`` pass-through override is
the positive control that the seal accepts a healthy ``OrderSet``.

Both pipelines run that seal, so the matrix is mirrored over the async one, on
the field shape each pipeline belongs to. The sync matrix runs on the shipped
``allLibraryGenresConnection`` through ``/graphql/``: that field declares no
``resolver=``, so its public resolver is a sync one and the field runs
``connection.py::_pipeline_sync``. The async matrix runs on a test-local
connection field this module builds over the same shipped ``GenreType`` with an
``async def`` consumer resolver, which is the only field shape that selects
``connection.py::_pipeline_async``; it is served over a ``/graphql-async/``
mount this module owns (``graphql_client.py`` is sync-only, so those rows take
the documented ``AsyncTestClient`` + ``django_db(transaction=True)``
exemption). The async rows cover an evaluated, sliced, combined, wrong-model,
re-routed and non-awaitable return plus the same pass-through control; each
asserts the typed rejection, that no raw exception text reaches the payload,
and - through a sentinel the override records before it returns - that
``apply_async`` was actually entered.
"""

import pytest
import strawberry
from apps.library import models as library_models
from apps.library.orders_genre import GenreOrder
from apps.products.services import seed_data
from django.conf import settings
from django.db import connection, models
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import clear_url_caches, path
from graphql_client import assert_graphql_success, graphql_payload

from django_strawberry_framework import DjangoConnectionField, DjangoSchema, strawberry_config
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView

_ERROR_POLICY_PASS_THROUGH = {
    "DEBUG": True,
    "MIDDLEWARE": [entry for entry in settings.MIDDLEWARE if "debug_toolbar" not in entry],
}


@pytest.mark.django_db
def test_live_negative_first_is_graphql_error():
    """``first: -1`` via live HTTP is a GraphQLError (not a raw ValueError)."""
    seed_data(1)
    payload = graphql_payload("{ allItems(first: -1) { edges { node { id } } } }")
    assert "errors" in payload
    assert payload["data"] is None, payload
    assert any("non-negative" in str(e.get("message", "")).lower() for e in payload["errors"])
    # GraphQLError entries carry a message, never a Python traceback
    messages = [str(e.get("message", "")) for e in payload["errors"]]
    assert not any("ValueError" in message for message in messages), messages
    assert not any("Traceback" in message for message in messages), messages


@pytest.mark.django_db
def test_live_over_cap_first_is_graphql_error():
    """``first`` over the configured ``relay_max_results`` is a GraphQLError."""
    seed_data(1)
    # Default relay_max_results is 100 (strawberry default)
    payload = graphql_payload("{ allItems(first: 101) { edges { node { id } } } }")
    assert "errors" in payload
    assert payload["data"] is None, payload
    assert any("cannot be higher than" in str(e.get("message", "")) for e in payload["errors"])


@pytest.mark.django_db
def test_live_malformed_after_cursor_is_graphql_error():
    """A malformed ``after:`` cursor is a GraphQLError (not ValueError/TypeError)."""
    seed_data(1)
    payload = graphql_payload(
        '{ allItems(first: 1, after: "not-a-cursor") { edges { node { id } } } }',
    )
    assert "errors" in payload
    assert payload["data"] is None, payload
    # The error should mention cursor / pagination, not leak Python types
    assert len(payload["errors"]) >= 1
    # The envelope must not leak raw ValueError / TypeError class names
    messages = [str(e.get("message", "")) for e in payload["errors"]]
    assert not any("ValueError" in message for message in messages), messages
    assert not any("TypeError" in message for message in messages), messages


@pytest.mark.django_db
def test_live_malformed_before_cursor_is_graphql_error():
    """A malformed ``before:`` cursor is a GraphQLError."""
    seed_data(1)
    payload = graphql_payload(
        '{ allItems(last: 1, before: "bad-base64!") { edges { node { id } } } }',
    )
    assert "errors" in payload
    assert payload["data"] is None, payload
    assert len(payload["errors"]) >= 1


@pytest.mark.django_db
def test_live_first_and_last_together_is_graphql_error():
    """``first`` + ``last`` together is the package's mutual-exclusivity GraphQLError."""
    seed_data(1)
    payload = graphql_payload("{ allItems(first: 1, last: 1) { edges { node { id } } } }")
    assert "errors" in payload
    assert payload["data"] is None, payload
    assert any("mutually exclusive" in str(e.get("message", "")) for e in payload["errors"])


@pytest.mark.django_db
def test_live_keyset_negative_first_is_graphql_error():
    """Keyset ``first: -5`` is a GraphQLError on the declared-cursor connection too.

    ``allLibraryIssuesConnection`` resolves ``IssueType``, whose
    ``Meta.cursor_field = ("-number", "id")`` routes the page through the
    keyset path rather than the offset path the other cases exercise. The
    bound is rejected during argument validation, so the containment holds
    for both connection flavors.
    """
    seed_data(1)
    payload = graphql_payload(
        "{ allLibraryIssuesConnection(first: -5) { edges { node { id } } } }",
    )
    assert "errors" in payload
    assert payload["data"] is None, payload
    assert any("non-negative" in str(e.get("message", "")).lower() for e in payload["errors"])


@pytest.mark.django_db
def test_live_keyset_over_cap_first_is_graphql_error():
    """Keyset ``first: 101`` is a GraphQLError on the declared-cursor connection too.

    Offset over-cap is pinned on ``allItems``. The keyset slicer re-spells the
    same bound because a value cursor cannot pass through ``SliceMetadata``.
    """
    payload = graphql_payload(
        "{ allLibraryIssuesConnection(first: 101) { edges { node { id } } } }",
    )
    assert "errors" in payload
    assert payload["data"] is None, payload
    assert any("cannot be higher than" in str(e.get("message", "")) for e in payload["errors"])


@pytest.mark.django_db
def test_total_count_is_a_field_only_on_the_connection_that_opted_in():
    """``Meta.connection = {"total_count": True}`` is what puts ``totalCount`` in the schema.

    Both shipped shapes are read in one request each, because the claim is the
    CONTRAST: a client asking a products connection for ``totalCount`` is told
    the field does not exist (a validation error naming it, so the opt-out is
    visible in the schema rather than answered with a null), while the opted-in
    genre connection answers the unpaginated count beside a one-edge page - the
    count is of the whole set, not of the window.
    """
    seed_data(1)
    library_models.Genre.objects.create(name="Alpha")
    library_models.Genre.objects.create(name="Beta")

    not_opted = graphql_payload("{ allItems(first: 1) { totalCount } }")
    assert "errors" in not_opted, not_opted
    assert any(
        "Cannot query field 'totalCount'" in str(error.get("message", ""))
        for error in not_opted["errors"]
    ), not_opted
    assert not_opted["data"] is None, not_opted

    opted = assert_graphql_success(
        "{ allLibraryGenresConnection(first: 1) { edges { node { name } } totalCount } }",
    )
    connection = opted["allLibraryGenresConnection"]
    assert len(connection["edges"]) == 1
    assert connection["totalCount"] == 2


@pytest.mark.django_db
def test_the_non_opted_connection_type_keeps_the_inherited_sdl_description():
    """The always-concrete generated connection still describes itself to a client.

    A non-opted type gets a generated ``<TypeName>Connection`` subclass rather
    than the bare ``DjangoConnection[T]`` alias, and the description Strawberry's
    own ``Connection`` base carries has to survive that generation: it is the
    only part of the bare connection shape introspection can show, so a silent
    drop would be invisible everywhere else.
    """
    data = assert_graphql_success('{ __type(name: "ItemTypeConnection") { description } }')

    assert data["__type"]["description"] == "A connection to a list of items."


_QUERY_FIELD_ARGS = """
query {
  __type(name: "Query") {
    fields {
      name
      args { name }
    }
  }
}
"""


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("field_name", "required", "forbidden"),
    [
        (
            "allLibraryGenresConnection",
            (
                "filter",
                "orderBy",
                "first",
                "last",
                "before",
                "after",
            ),
            (),
        ),
        (
            "allLibraryIssuesConnection",
            (
                "orderBy",
                "first",
                "last",
                "before",
                "after",
            ),
            ("filter",),
        ),
    ],
    ids=["genres-both-sidecars", "issues-order-only"],
)
def test_root_connection_arguments_follow_declared_sidecars(field_name, required, forbidden):
    """``filter:`` / ``orderBy:`` are published exactly when the node type declared those sidecars."""
    data = assert_graphql_success(_QUERY_FIELD_ARGS)
    fields = {field["name"]: field for field in data["__type"]["fields"]}
    assert field_name in fields, sorted(fields)
    names = {arg["name"] for arg in fields[field_name]["args"]}
    assert set(required) <= names, names
    assert names.isdisjoint(forbidden), names


_NESTED_CONNECTION_FIELD_ARGS = """
query {
  genre: __type(name: "GenreType") {
    fields {
      name
      args {
        name
        type {
          name
          kind
          ofType {
            name
            kind
          }
        }
      }
    }
  }
  periodical: __type(name: "PeriodicalType") {
    fields {
      name
      args {
        name
        type {
          name
          kind
          ofType {
            name
            kind
          }
        }
      }
    }
  }
  genre_conn: __type(name: "GenreTypeConnection") {
    fields {
      name
    }
  }
  book_conn: __type(name: "BookTypeConnection") {
    fields {
      name
    }
  }
}
"""


@pytest.mark.django_db
def test_nested_connection_arguments_follow_declared_sidecars():
    """Nested connection fields expose ``filter`` and ``orderBy`` only when target declared them.

    Target-driven contract: ``GenreType.booksConnection`` targets ``BookType`` which declares
    both ``filterset_class`` and ``orderset_class``, so it exposes ``filter: BookFilterInputType``
    and ``orderBy: [BookOrderInputType!]``. Conversely, ``PeriodicalType.issuesConnection`` targets
    ``IssueType`` which declares ``orderset_class`` but no ``filterset_class``, so it exposes
    ``orderBy`` but never ``filter``. Opted-in connection types carry ``totalCount``, while
    unopted types omit it.
    """
    data = assert_graphql_success(_NESTED_CONNECTION_FIELD_ARGS)

    genre_fields = {f["name"]: f for f in data["genre"]["fields"]}
    assert "booksConnection" in genre_fields
    books_conn_args = {a["name"]: a for a in genre_fields["booksConnection"]["args"]}
    assert "first" in books_conn_args
    assert "last" in books_conn_args
    assert "before" in books_conn_args
    assert "after" in books_conn_args
    assert "filter" in books_conn_args
    assert books_conn_args["filter"]["type"]["name"] == "BookFilterInputType"
    assert "orderBy" in books_conn_args

    periodical_fields = {f["name"]: f for f in data["periodical"]["fields"]}
    assert "issuesConnection" in periodical_fields
    issues_conn_args = {a["name"]: a for a in periodical_fields["issuesConnection"]["args"]}
    assert "first" in issues_conn_args
    assert "last" in issues_conn_args
    assert "before" in issues_conn_args
    assert "after" in issues_conn_args
    assert "orderBy" in issues_conn_args
    assert "filter" not in issues_conn_args

    genre_conn_fields = {f["name"] for f in data["genre_conn"]["fields"]}
    assert "totalCount" in genre_conn_fields

    book_conn_fields = {f["name"] for f in data["book_conn"]["fields"]}
    assert "totalCount" not in book_conn_fields


_GENRE_ORDER_SHAPE_PREFIX = (
    "GenreOrder.apply_sync must return an unevaluated, unsliced, uncombined "
    "QuerySet of Genre rows; got "
)

_GENRE_CONNECTION_ORDER_QUERY = (
    "{ allLibraryGenresConnection(orderBy: [{ name: ASC }]) { edges { node { name } } } }"
)


class _DeferredFilterQuerySet(models.QuerySet):
    """A project queryset class, used here to carry a deferred filter Django never writes.

    A PENDING predicate is ordinary: Django's related-manager machinery leaves
    one on every relation queryset whatever class built it, and the seal bakes
    it. What cannot be faithfully rebuilt is a deferred-filter STATE outside the
    exact shape Django writes, which is what this class is planted with.
    """


async def _awaitable_queryset(queryset):
    return queryset


def _override_evaluated(
    cls,
    order_input,
    queryset,
    info,
):
    list(queryset)
    return queryset


def _override_untrusted(
    cls,
    order_input,
    queryset,
    info,
):
    candidate = _DeferredFilterQuerySet(model=library_models.Genre)
    # ``negate`` decides whether the predicate is inverted and is truth-tested to
    # do it, so Django's exact ``bool`` is the only shape the bake accepts there.
    candidate._deferred_filter = (1, (), {"name": "A"})
    return candidate


def _override_in_place_routing(
    cls,
    order_input,
    queryset,
    info,
):
    queryset._hints = {"tenant": 2}
    return queryset


def _override_passthrough(
    cls,
    order_input,
    queryset,
    info,
):
    return super(GenreOrder, cls).apply_sync(order_input, queryset, info)


#: One row per defect shape the post-``OrderSet`` seal can name on the shipped
#: connection; ``materialized-list`` and ``none`` share the ``type`` branch.
#: ``(id, override, expected message start, required substrings, genre
#: queries)``. The query count is the must-not half - a defect caught before the
#: Relay window is taken must leave ``library_genre`` untouched, and the
#: ``evaluated`` and ``materialized-list`` rows, which issue exactly one
#: statement (the override's own evaluation), prove the count is measured rather
#: than assumed.
_CONNECTION_MALFORMED_APPLY_SYNC_ROWS = (
    (
        "evaluated",
        _override_evaluated,
        _GENRE_ORDER_SHAPE_PREFIX + "evaluated defect",
        (),
        1,
    ),
    (
        "materialized-list",
        lambda cls, order_input, queryset, info: list(queryset),
        _GENRE_ORDER_SHAPE_PREFIX + "type defect",
        (),
        1,
    ),
    (
        "none",
        lambda cls, order_input, queryset, info: None,
        _GENRE_ORDER_SHAPE_PREFIX + "type defect",
        (),
        0,
    ),
    (
        "projection",
        lambda cls, order_input, queryset, info: queryset.values("name"),
        _GENRE_ORDER_SHAPE_PREFIX + "projection defect",
        (),
        0,
    ),
    (
        "wrong-model",
        lambda cls, order_input, queryset, info: library_models.Book.objects.all(),
        _GENRE_ORDER_SHAPE_PREFIX + "table defect",
        (),
        0,
    ),
    (
        "sliced",
        lambda cls, order_input, queryset, info: queryset.order_by("name")[:1],
        _GENRE_ORDER_SHAPE_PREFIX + "sliced defect",
        (),
        0,
    ),
    (
        "combined",
        lambda cls, order_input, queryset, info: queryset.filter(name="A").union(
            queryset.filter(name="B"),
        ),
        _GENRE_ORDER_SHAPE_PREFIX + "combined defect",
        (),
        0,
    ),
    (
        "awaitable-in-sync",
        lambda cls, order_input, queryset, info: _awaitable_queryset(queryset),
        "GenreOrder.apply_sync returned an awaitable in a sync resolver context.",
        (),
        0,
    ),
    (
        "routing-rewritten-in-place",
        _override_in_place_routing,
        "GenreOrder.apply_sync changed database routing intent",
        ("expected db=None, hints={}", "got db=None, hints={'tenant': 2}"),
        0,
    ),
    (
        "malformed-deferred-filter",
        _override_untrusted,
        _GENRE_ORDER_SHAPE_PREFIX + "untrusted defect",
        ("deferred filter negate is a int",),
        0,
    ),
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "override",
        "message_start",
        "substrings",
        "genre_queries",
    ),
    [row[1:] for row in _CONNECTION_MALFORMED_APPLY_SYNC_ROWS],
    ids=[row[0] for row in _CONNECTION_MALFORMED_APPLY_SYNC_ROWS],
)
def test_connection_branches_a_malformed_apply_sync_result_names_its_own_defect(
    monkeypatch,
    override,
    message_start,
    substrings,
    genre_queries,
):
    """Each malformed ``apply_sync`` result names its exact defect on the shipped connection.

    The connection field runs the same post-``OrderSet`` seal the list field
    runs, so every defect class has to arrive here too; unsealed, the Relay
    window would simply be taken on whatever the override returned. Every row
    runs a real ``/graphql/`` request and captures SQL, so a row that must not
    reach the database proves it did not.
    """
    library_models.Genre.objects.create(name="A")
    monkeypatch.setattr(GenreOrder, "apply_sync", classmethod(override))

    with (
        override_settings(**_ERROR_POLICY_PASS_THROUGH),
        CaptureQueriesContext(connection) as ctx,
    ):
        payload = graphql_payload(_GENRE_CONNECTION_ORDER_QUERY)

    assert payload["data"] is None
    message = payload["errors"][0]["message"]
    assert message.startswith(message_start), message
    for substring in substrings:
        assert substring in message, message
    genre_sql = [q["sql"] for q in ctx.captured_queries if "library_genre" in q["sql"].lower()]
    assert len(genre_sql) == genre_queries, genre_sql


@pytest.mark.django_db
def test_connection_healthy_apply_sync_override_still_returns_ordered_edges(monkeypatch):
    """A ``super()`` pass-through override is ACCEPTED and the ordered page is served.

    The seal's positive control on the shipped connection: it rejects malformed
    results without rejecting an ``OrderSet`` that simply delegates.
    """
    for name in ("C", "A", "B"):
        library_models.Genre.objects.create(name=name)
    monkeypatch.setattr(GenreOrder, "apply_sync", classmethod(_override_passthrough))

    data = assert_graphql_success(_GENRE_CONNECTION_ORDER_QUERY)

    names = [edge["node"]["name"] for edge in data["allLibraryGenresConnection"]["edges"]]
    assert names == ["A", "B", "C"]


_ASYNC_SCHEMA: dict = {"schema": None}


async def _async_genres_resolver(root, info):
    """An ``async def`` consumer resolver - the shape that selects ``_pipeline_async``."""
    return library_models.Genre.objects.all()


def _async_genre_connection_schema():
    """Build (once) a schema whose genre connection runs the ASYNC pipeline.

    ``connection.py::_build_connection_resolver`` commits sync-vs-async dispatch
    per construction: the async branch is selected only when the field is given
    an ``is_async_callable`` ``resolver=``. The shipped
    ``allLibraryGenresConnection`` declares none, so its wrapped resolver is the
    sync one; this field supplies an ``async def`` resolver over the same
    ``GenreType`` and therefore carries the async half of the seal.
    """
    if _ASYNC_SCHEMA["schema"] is None:
        # The composed project schema is imported first so the sidecar input
        # classes this field's synthesized signature forward-references have
        # been materialized by ``finalize_django_types``.
        import config.schema  # noqa: F401
        from apps.library.schema import GenreType

        @strawberry.type
        class Query:
            genres = DjangoConnectionField(GenreType, resolver=_async_genres_resolver)

        _ASYNC_SCHEMA["schema"] = DjangoSchema(query=Query, config=strawberry_config())
    return _ASYNC_SCHEMA["schema"]


async def _async_genre_graphql_view(request):
    """The test-local async-resolver schema on an async view."""
    return await AsyncDjangoGraphQLView.as_view(schema=_async_genre_connection_schema())(request)


urlpatterns = [
    path("graphql-async/", _async_genre_graphql_view),
]


async def _post_async_genres(query: str) -> dict:
    """POST ``query`` against the async-resolver genre connection over ``/graphql-async/``.

    ``graphql_client.py`` is sync-only, so the async rows take the documented
    exemption and drive ``AsyncTestClient`` against a mount this module owns.
    """
    try:
        with override_settings(ROOT_URLCONF=__name__, **_ERROR_POLICY_PASS_THROUGH):
            clear_url_caches()
            result = await AsyncTestClient().query(
                query,
                assert_no_errors=False,
                url="/graphql-async/",
            )
    finally:
        clear_url_caches()
    assert result.response.status_code == 200
    return result.response.json()


_GENRE_ASYNC_CONNECTION_ORDER_QUERY = (
    "{ genres(orderBy: [{ name: ASC }]) { edges { node { name } } } }"
)

#: Names of the overrides ``apply_async`` actually entered during one request.
#: An override that is never called cannot append to it, so an empty list after
#: a request means the field never took the async pipeline.
_ASYNC_APPLY_CALLS: list = []


_GENRE_ORDER_ASYNC_SHAPE_PREFIX = (
    "GenreOrder.apply_async must return an unevaluated, unsliced, uncombined "
    "QuerySet of Genre rows; got "
)


async def _override_async_evaluated(
    cls,
    order_input,
    queryset,
    info,
):
    [genre async for genre in queryset]
    _ASYNC_APPLY_CALLS.append("evaluated")
    return queryset


async def _override_async_sliced(
    cls,
    order_input,
    queryset,
    info,
):
    _ASYNC_APPLY_CALLS.append("sliced")
    return queryset.order_by("name")[:1]


async def _override_async_combined(
    cls,
    order_input,
    queryset,
    info,
):
    _ASYNC_APPLY_CALLS.append("combined")
    return queryset.filter(name="A").union(queryset.filter(name="B"))


async def _override_async_wrong_model(
    cls,
    order_input,
    queryset,
    info,
):
    _ASYNC_APPLY_CALLS.append("wrong-model")
    return library_models.Book.objects.all()


async def _override_async_in_place_routing(
    cls,
    order_input,
    queryset,
    info,
):
    queryset._hints = {"tenant": 2}
    _ASYNC_APPLY_CALLS.append("routing-rewritten-in-place")
    return queryset


def _override_async_non_awaitable(
    cls,
    order_input,
    queryset,
    info,
):
    _ASYNC_APPLY_CALLS.append("non-awaitable")
    return queryset


async def _override_async_passthrough(
    cls,
    order_input,
    queryset,
    info,
):
    _ASYNC_APPLY_CALLS.append("passthrough")
    return await super(GenreOrder, cls).apply_async(order_input, queryset, info)


#: Defect rows the post-``OrderSet`` seal names on the ASYNC connection
#: pipeline: ``(id, override, expected message start, required substrings)``.
#: The sync matrix above drives ``apply_sync`` through
#: ``connection.py::_pipeline_sync`` on the shipped connection, whose public
#: resolver is sync; these drive ``apply_async`` through
#: ``connection.py::_pipeline_async`` on the test-local connection field whose
#: ``async def`` consumer resolver is what selects that branch. Every override
#: records itself in ``_ASYNC_APPLY_CALLS`` so each row can prove the seal it
#: names was entered rather than bypassed.
_CONNECTION_MALFORMED_APPLY_ASYNC_ROWS = (
    (
        "evaluated",
        _override_async_evaluated,
        _GENRE_ORDER_ASYNC_SHAPE_PREFIX + "evaluated defect",
        (),
    ),
    (
        "sliced",
        _override_async_sliced,
        _GENRE_ORDER_ASYNC_SHAPE_PREFIX + "sliced defect",
        (),
    ),
    (
        "combined",
        _override_async_combined,
        _GENRE_ORDER_ASYNC_SHAPE_PREFIX + "combined defect",
        (),
    ),
    (
        "wrong-model",
        _override_async_wrong_model,
        _GENRE_ORDER_ASYNC_SHAPE_PREFIX + "table defect",
        (),
    ),
    (
        "routing-rewritten-in-place",
        _override_async_in_place_routing,
        "GenreOrder.apply_async changed database routing intent",
        ("expected db=None, hints={}", "got db=None, hints={'tenant': 2}"),
    ),
    (
        "non-awaitable",
        _override_async_non_awaitable,
        "GenreOrder.apply_async returned a non-awaitable value",
        ("expected an awaitable coroutine or Future.",),
    ),
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("override", "message_start", "substrings"),
    [row[1:] for row in _CONNECTION_MALFORMED_APPLY_ASYNC_ROWS],
    ids=[row[0] for row in _CONNECTION_MALFORMED_APPLY_ASYNC_ROWS],
)
async def test_connection_async_branches_a_malformed_apply_async_result_names_its_own_defect(
    monkeypatch,
    override,
    message_start,
    substrings,
):
    """Each malformed ``apply_async`` result names its exact defect over ``/graphql-async/``.

    The async pipeline awaits the SAME post-``OrderSet`` seal the sync one
    calls, so every defect class the sync matrix pins has to arrive here too;
    unsealed, the Relay window would be taken on whatever the override handed
    back. The field carries an ``async def`` consumer resolver, which is what
    puts the request on that pipeline. Each row asserts the typed rejection,
    that the override was entered, and that no raw exception text reaches the
    payload.
    """
    await library_models.Genre.objects.acreate(name="A")
    monkeypatch.setattr(GenreOrder, "apply_async", classmethod(override))

    _ASYNC_APPLY_CALLS.clear()

    payload = await _post_async_genres(_GENRE_ASYNC_CONNECTION_ORDER_QUERY)

    assert _ASYNC_APPLY_CALLS, payload
    assert payload["data"] is None, payload
    message = payload["errors"][0]["message"]
    assert message.startswith(message_start), message
    for substring in substrings:
        assert substring in message, message
    assert "Traceback" not in message, message
    assert not any(
        token in message for token in ("ValueError", "TypeError", "SynchronousOnlyOperation")
    ), message


@pytest.mark.django_db(transaction=True)
async def test_connection_async_healthy_apply_async_override_still_returns_ordered_edges(
    monkeypatch,
):
    """A ``super()`` pass-through ``apply_async`` is ACCEPTED and the ordered page is served.

    The async seal's positive control on the async-resolver connection: it
    rejects malformed results without rejecting an ``OrderSet`` that simply
    delegates, and the sentinel shows the accepted result came through
    ``apply_async``.
    """
    for name in ("C", "A", "B"):
        await library_models.Genre.objects.acreate(name=name)
    monkeypatch.setattr(GenreOrder, "apply_async", classmethod(_override_async_passthrough))

    _ASYNC_APPLY_CALLS.clear()

    payload = await _post_async_genres(_GENRE_ASYNC_CONNECTION_ORDER_QUERY)

    assert _ASYNC_APPLY_CALLS == ["passthrough"], payload
    assert "errors" not in payload, payload
    names = [edge["node"]["name"] for edge in payload["data"]["genres"]["edges"]]
    assert names == ["A", "B", "C"]
