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
exemption). The async rows mirror the sync matrix shape for shape - evaluated,
materialized-list, none, projection, wrong-model, sliced, combined,
routing-rewritten-in-place and malformed-deferred-filter - with one
substitution the pipelines force: the sync-only ``awaitable-in-sync`` row has
two async twins, ``non-awaitable`` for a public method that never returned an
awaitable and ``residual-awaitable`` for one that awaited to a second
awaitable. Each row asserts the typed rejection, that no raw exception text
reaches the payload, and - through a sentinel the override records before it
returns - that ``apply_async`` was actually entered; the pass-through control
is the same. The residual row also reads the disposal, since the refused
awaitable must be RELEASED rather than awaited: its coroutine is closed and the
sentinel its body would have appended is absent, so no second await happened.

The same async matrix is mirrored for the FILTER arm, row for row. Both public
sidecar methods answer to one post-sidecar seal, so ``GenreFilter.apply_async``
is driven over the same ``/graphql-async/`` mount with a request carrying a
real ``filter:`` argument - the argument is what makes the pipeline invoke the
method at all - through the same defect shapes, the same sentinel, the same
disposal read and the same ``super()`` pass-through control, which asserts the
filtered page. The filter step runs before ordering, the optimizer plan and the
Relay window, so an unsealed return would reach all three.

Offset cursor decoding is pinned last, under the default (``DEBUG=False``)
error policy so each row reads the exact message a client gets. A correctly
prefixed cursor naming a negative index, and every non-minted shape (bad
base64, no colon, foreign prefix, sign, padding, leading zero, underscore,
non-ASCII digit, a 5000-digit string, an index of ``sys.maxsize``), answers with
``Argument '<after|before>' contains a non-existing value.`` on every source a
connection slices: list and tuple consumer resolvers, sync and async, under a
three-row ``max_page_size`` (where a wrapped negative slice would serve 39 of
40 rows); a generator resolver; a ``QuerySet`` from an async resolver; and the
shipped root ``allLibraryGenresConnection``. Index 0, a minted ``endCursor``,
``after: ""`` (absent) and the largest accepted index ``sys.maxsize - 1`` (an
ordinary past-the-end page on the root ``QuerySet`` and a list resolver) are the
positive controls. Each ``first`` / ``last`` bound message (negative, over the
three-row cap) is read exactly on both colours. The test-local resolvers
are served over module-owned ``/graphql-cursor/`` and ``/graphql-cursor-async/``
mounts with no error-policy pass-through.

Only the package's own argument validation speaks to the client. An exception
from a consumer source or from row hydration is not a pagination error: it is
masked by the default error policy (the policy message plus a ``correlationId``,
the exception's text nowhere in the body) like any other unexpected exception,
on the sync and async views alike. That is pinned for a failing row hydration on
a root offset connection and on a nested connection under one (planned window
and per-parent pipeline, told apart by their ``library_book`` statement count),
and for a consumer generator source raising ``KeyError`` or ``ValueError``, whose
original exception is read back from the policy's server log.

Each test-local mount serves whichever schema the test in flight published in
its holder: the acceptance harness reloads every contributing app schema
around each test, so the local field is built inside the request helper, after
that reload, and the slot is cleared when the request ends.
"""

import base64
import importlib
import inspect
import json
import logging
import re
import sys
from collections.abc import Callable, Coroutine, Iterator
from typing import TypeAlias

import pytest
import strawberry
from apps.library import models as library_models
from apps.library.filters_genre import GenreFilter
from apps.library.orders_genre import GenreOrder
from apps.products.services import seed_data
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import connection, models
from django.http import HttpRequest
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import clear_url_caches, path
from graphql_client import JSONObject, assert_graphql_success, graphql_payload
from strawberry import relay

from django_strawberry_framework import DjangoConnectionField, DjangoSchema, strawberry_config
from django_strawberry_framework.error_policy import DEFAULT_ERROR_POLICY
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.utils._queryset_private import (
    set_queryset_hints,
)
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

_ApplySyncOverride: TypeAlias = Callable[
    [
        type[GenreOrder],
        object,
        models.QuerySet[library_models.Genre],
        object,
    ],
    object,
]

#: An ``apply_async`` override on either sidecar: the async matrices also carry a
#: plain ``def`` (the non-awaitable rows), so the return is left as ``object``.
_OrderApplyAsyncOverride: TypeAlias = Callable[
    [
        type[GenreOrder],
        object,
        models.QuerySet[library_models.Genre],
        object,
    ],
    object,
]
_FilterApplyAsyncOverride: TypeAlias = Callable[
    [
        type[GenreFilter],
        object,
        models.QuerySet[library_models.Genre],
        object,
    ],
    object,
]

_ResidualHolder: TypeAlias = dict[str, Coroutine[object, object, None] | None]
#: A residual-awaitable row's holder pair: the coroutine slot and the body sentinel.
_ResidualHolders: TypeAlias = tuple[
    _ResidualHolder,
    list[str],
]

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
    assert payload["data"] is None, payload
    assert [error["message"] for error in payload["errors"]] == [
        "Argument 'first' must be a non-negative integer.",
    ], payload


@pytest.mark.django_db
def test_live_keyset_over_cap_first_is_graphql_error():
    """Keyset ``first: 101`` is a GraphQLError on the declared-cursor connection too.

    Offset over-cap is pinned on ``allItems``. The keyset slicer re-spells the
    same bound because a value cursor cannot pass through ``SliceMetadata``.
    """
    payload = graphql_payload(
        "{ allLibraryIssuesConnection(first: 101) { edges { node { id } } } }",
    )
    assert payload["data"] is None, payload
    assert [error["message"] for error in payload["errors"]] == [
        "Argument 'first' cannot be higher than 100.",
    ], payload


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
def test_root_connection_arguments_follow_declared_sidecars(
    field_name: str,
    required: tuple[str, ...],
    forbidden: tuple[str, ...],
):
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
    "GenreOrder.apply_sync must return an unevaluated, unsliced QuerySet of Genre rows; got "
)

_GENRE_CONNECTION_ORDER_QUERY = (
    "{ allLibraryGenresConnection(orderBy: [{ name: ASC }]) { edges { node { name } } } }"
)


class _DeferredFilterQuerySet(models.QuerySet[library_models.Genre]):
    """A project queryset class, used here to carry a deferred filter Django never writes.

    A PENDING predicate is ordinary: Django's related-manager machinery leaves
    one on every relation queryset whatever class built it, and the seal bakes
    it. What cannot be faithfully rebuilt is a deferred-filter STATE outside the
    exact shape Django writes, which is what this class is planted with.
    """

    # The pending ``(negate, args, kwargs)`` slot ``QuerySet.__init__`` sets, which the
    # stubs leave undeclared.
    _deferred_filter: tuple[object, tuple[object, ...], dict[str, object]] | None


async def _awaitable_queryset(
    queryset: models.QuerySet[library_models.Genre],
) -> models.QuerySet[library_models.Genre]:
    return queryset


def _seed_genres(*names: str) -> None:
    """Create one ``Genre`` per name, in the order given.

    The pass-through controls all need the same unordered spread of rows so the
    served page proves an ordering rather than an insertion order; the setup
    lives here so each control body carries one case.
    """
    for name in names:
        library_models.Genre.objects.create(name=name)


async def _aseed_genres(*names: str) -> None:
    """Async colour of :func:`_seed_genres`, for the rows served over ``/graphql-async/``."""
    for name in names:
        await library_models.Genre.objects.acreate(name=name)


def _override_evaluated(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    list(queryset)
    return queryset


def _untrusted_genre_queryset():
    """Build the deferred-filter state Django never writes, for the untrusted rows.

    Both the sync and the async arms plant the same shape, so the state lives
    in one place and each override simply returns it.
    """
    candidate = _DeferredFilterQuerySet(model=library_models.Genre)
    # ``negate`` decides whether the predicate is inverted and is truth-tested to
    # do it, so Django's exact ``bool`` is the only shape the bake accepts there.
    candidate._deferred_filter = (1, (), {"name": "A"})
    return candidate


def _override_untrusted(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    return _untrusted_genre_queryset()


def _override_in_place_routing(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    set_queryset_hints(queryset, {"tenant": 2})
    return queryset


def _override_passthrough(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    return super(GenreOrder, cls).apply_sync(order_input, queryset, info)


def _assert_rejection_message(
    message: str,
    message_start: str,
    substrings: tuple[str, ...],
) -> None:
    """Assert one rejection message opens with ``message_start`` and names each fragment.

    A row's claim is the whole message, not its opening: the prefix says which
    seal spoke and which defect it named, and the fragments are the operand
    detail that separates a real diagnosis from a generic rejection. The two
    are one claim about one message, so they are asserted together here rather
    than spelled out in every parametrized body.
    """
    assert message.startswith(message_start), message
    for substring in substrings:
        assert substring in message, message


def _assert_async_rejection_message(
    message: str,
    message_start: str,
    substrings: tuple[str, ...],
) -> None:
    """The async arms' rejection assertion: the typed message and nothing raw behind it.

    The async rows run under the error-policy pass-through, so a masked
    envelope cannot hide a leak: whatever the seal raised is what the reader
    gets. That makes the absence of a traceback and of the raising exception's
    own class name part of the claim - a rejection that names its defect but
    ships the interpreter's wording with it has not contained anything.
    """
    _assert_rejection_message(message, message_start, substrings)
    assert "Traceback" not in message, message
    assert not any(
        token in message for token in ("ValueError", "TypeError", "SynchronousOnlyOperation")
    ), message


#: One row per defect shape the post-``OrderSet`` seal can name on the shipped
#: connection; ``materialized-list`` and ``none`` share the ``type`` branch.
#: ``(id, override, expected message start, required substrings, genre
#: queries)``. The query count is the must-not half - a defect caught before the
#: Relay window is taken must leave ``library_genre`` untouched, and the
#: ``evaluated`` and ``materialized-list`` rows, which issue exactly one
#: statement (the override's own evaluation), prove the count is measured rather
#: than assumed.
_CONNECTION_MALFORMED_APPLY_SYNC_ROWS: tuple[
    tuple[str, _ApplySyncOverride, str, tuple[str, ...], int],
    ...,
] = (
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
        "combined-duplicates",
        lambda cls, order_input, queryset, info: queryset.union(queryset, all=True),
        "GenreOrder.apply_sync returned a combined queryset; the visibility boundary serves "
        "a combined queryset as the set of Genre primary keys it selects",
        ("union: union(all=True) keeps duplicate rows, which a primary-key set cannot",),
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
    monkeypatch: pytest.MonkeyPatch,
    override: _ApplySyncOverride,
    message_start: str,
    substrings: tuple[str, ...],
    genre_queries: int,
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
    _assert_rejection_message(message, message_start, substrings)
    genre_sql = [q["sql"] for q in ctx.captured_queries if "library_genre" in q["sql"].lower()]
    assert len(genre_sql) == genre_queries, genre_sql


@pytest.mark.django_db
def test_connection_healthy_apply_sync_override_still_returns_ordered_edges(
    monkeypatch: pytest.MonkeyPatch,
):
    """A ``super()`` pass-through override is ACCEPTED and the ordered page is served.

    The seal's positive control on the shipped connection: it rejects malformed
    results without rejecting an ``OrderSet`` that simply delegates.
    """
    _seed_genres("C", "A", "B")
    monkeypatch.setattr(GenreOrder, "apply_sync", classmethod(_override_passthrough))

    data = assert_graphql_success(_GENRE_CONNECTION_ORDER_QUERY)

    names = [edge["node"]["name"] for edge in data["allLibraryGenresConnection"]["edges"]]
    assert names == ["A", "B", "C"]


#: The schema the async mount serves for the request in flight, resolved by the
#: view at request time. A module-level one-shot cache cannot be used here: the
#: acceptance harness reloads every contributing app schema around each test
#: (``examples/fakeshop/test_query/conftest.py``,
#: ``examples/fakeshop/schema_reload.py``), so a schema built during an earlier
#: test holds type objects no longer registered. Each test therefore builds the
#: schema after that reload, publishes it here for the duration of its request,
#: and clears the slot in a ``finally``.
_ASYNC_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


async def _async_genres_resolver(root: object, info: strawberry.Info[object, object]):
    """An ``async def`` consumer resolver - the shape that selects ``_pipeline_async``."""
    return library_models.Genre.objects.all()


def _async_genre_connection_schema():
    """Build a schema whose genre connection runs the ASYNC pipeline.

    ``connection.py::_build_connection_resolver`` commits sync-vs-async dispatch
    per construction: the async branch is selected only when the field is given
    an ``is_async_callable`` ``resolver=``. The shipped
    ``allLibraryGenresConnection`` declares none, so its wrapped resolver is the
    sync one; this field supplies an ``async def`` resolver over the same
    ``GenreType`` and therefore carries the async half of the seal.

    Built per request rather than cached, so the field is composed from the
    types the current reload registered.
    """
    # The composed project schema is imported first so the sidecar input
    # classes this field's synthesized signature forward-references have
    # been materialized by ``finalize_django_types``.
    importlib.import_module("config.schema")
    from apps.library.schema import GenreType

    @strawberry.type
    class Query:
        genres = DjangoConnectionField(GenreType, resolver=_async_genres_resolver)

    return DjangoSchema(query=Query, config=strawberry_config())


async def _async_genre_graphql_view(request: HttpRequest):
    """The test-local async-resolver schema on an async view."""
    schema = _ASYNC_CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [
    path("graphql-async/", _async_genre_graphql_view),
]


async def _post_async_genres(query: str) -> JSONObject:
    """POST ``query`` against the async-resolver genre connection over ``/graphql-async/``.

    ``graphql_client.py`` is sync-only, so the async rows take the documented
    exemption and drive ``AsyncTestClient`` against a mount this module owns.
    The schema is built here, inside the test, so it is composed from the types
    the autouse reload just registered, and published through ``_ASYNC_CURRENT``
    for the view to read.
    """
    _ASYNC_CURRENT["schema"] = _async_genre_connection_schema()
    try:
        with override_settings(ROOT_URLCONF=__name__, **_ERROR_POLICY_PASS_THROUGH):
            clear_url_caches()
            result = await AsyncTestClient().query(
                query,
                assert_no_errors=False,
                url="/graphql-async/",
            )
    finally:
        _ASYNC_CURRENT["schema"] = None
        clear_url_caches()
    assert result.response.status_code == 200
    return result.response.json()


_GENRE_ASYNC_CONNECTION_ORDER_QUERY = (
    "{ genres(orderBy: [{ name: ASC }]) { edges { node { name } } } }"
)


def _assert_residual_awaitable_disposed(holder: _ResidualHolder, body_ran: list[str]) -> None:
    """Assert the refused second awaitable was closed, never awaited.

    ``utils/querysets.py::_dispose_sync_awaitable`` closes a never-started
    coroutine rather than awaiting it, so the seal cannot be walked down an
    unbounded chain of awaitables. Both halves are needed: the closed state is
    what disposal leaves behind, and the absent sentinel is what says the body
    never ran.
    """
    coro = holder["coro"]
    assert coro is not None
    assert inspect.getcoroutinestate(coro) == inspect.CORO_CLOSED
    assert body_ran == []


#: Names of the overrides ``apply_async`` actually entered during one request.
#: An override that is never called cannot append to it, so an empty list after
#: a request means the field never took the async pipeline.
_ASYNC_APPLY_CALLS: list[str] = []


_GENRE_ORDER_ASYNC_SHAPE_PREFIX = (
    "GenreOrder.apply_async must return an unevaluated, unsliced QuerySet of Genre rows; got "
)


async def _override_async_evaluated(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    [genre async for genre in queryset]
    _ASYNC_APPLY_CALLS.append("evaluated")
    return queryset


async def _override_async_sliced(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("sliced")
    return queryset.order_by("name")[:1]


async def _override_async_combined_duplicates(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("combined-duplicates")
    return queryset.union(queryset, all=True)


async def _override_async_wrong_model(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("wrong-model")
    return library_models.Book.objects.all()


async def _override_async_in_place_routing(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    set_queryset_hints(queryset, {"tenant": 2})
    _ASYNC_APPLY_CALLS.append("routing-rewritten-in-place")
    return queryset


async def _override_async_materialized_list(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    rows = [genre async for genre in queryset]
    _ASYNC_APPLY_CALLS.append("materialized-list")
    return rows


async def _override_async_none(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("none")
    return None


async def _override_async_projection(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("projection")
    return queryset.values("name")


async def _override_async_untrusted(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("malformed-deferred-filter")
    return _untrusted_genre_queryset()


def _override_async_non_awaitable(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("non-awaitable")
    return queryset


#: The coroutine object the ORDER arm's residual-awaitable override hands back,
#: and the sentinel its body appends if anything ever advances it. The seal
#: disposes of a second awaitable instead of awaiting it, so after the request
#: the coroutine is closed and the sentinel list is still empty - a never-awaited
#: coroutine and a closed one are only distinguishable by reading that state.
_ORDER_RESIDUAL_AWAITABLE: _ResidualHolder = {"coro": None}
_ORDER_RESIDUAL_BODY_RAN: list[str] = []


async def _order_residual_inner():
    _ORDER_RESIDUAL_BODY_RAN.append("ran")


async def _override_async_residual_awaitable(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ORDER_RESIDUAL_BODY_RAN.clear()
    coro = _order_residual_inner()
    _ORDER_RESIDUAL_AWAITABLE["coro"] = coro
    _ASYNC_APPLY_CALLS.append("residual-awaitable")
    return coro


async def _override_async_passthrough(
    cls: type[GenreOrder],
    order_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
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
#: names was entered rather than bypassed. The fifth member is the residual
#: holder pair a row that returns a SECOND awaitable owns, and ``None`` for
#: every row that returns a value directly.
_CONNECTION_MALFORMED_APPLY_ASYNC_ROWS: tuple[
    tuple[str, _OrderApplyAsyncOverride, str, tuple[str, ...], _ResidualHolders | None],
    ...,
] = (
    (
        "evaluated",
        _override_async_evaluated,
        _GENRE_ORDER_ASYNC_SHAPE_PREFIX + "evaluated defect",
        (),
        None,
    ),
    (
        "materialized-list",
        _override_async_materialized_list,
        _GENRE_ORDER_ASYNC_SHAPE_PREFIX + "type defect",
        (),
        None,
    ),
    (
        "none",
        _override_async_none,
        _GENRE_ORDER_ASYNC_SHAPE_PREFIX + "type defect",
        (),
        None,
    ),
    (
        "projection",
        _override_async_projection,
        _GENRE_ORDER_ASYNC_SHAPE_PREFIX + "projection defect",
        (),
        None,
    ),
    (
        "wrong-model",
        _override_async_wrong_model,
        _GENRE_ORDER_ASYNC_SHAPE_PREFIX + "table defect",
        (),
        None,
    ),
    (
        "sliced",
        _override_async_sliced,
        _GENRE_ORDER_ASYNC_SHAPE_PREFIX + "sliced defect",
        (),
        None,
    ),
    (
        "combined-duplicates",
        _override_async_combined_duplicates,
        "GenreOrder.apply_async returned a combined queryset; the visibility boundary serves "
        "a combined queryset as the set of Genre primary keys it selects",
        ("union: union(all=True) keeps duplicate rows, which a primary-key set cannot",),
        None,
    ),
    (
        "routing-rewritten-in-place",
        _override_async_in_place_routing,
        "GenreOrder.apply_async changed database routing intent",
        ("expected db=None, hints={}", "got db=None, hints={'tenant': 2}"),
        None,
    ),
    (
        "malformed-deferred-filter",
        _override_async_untrusted,
        _GENRE_ORDER_ASYNC_SHAPE_PREFIX + "untrusted defect",
        ("deferred filter negate is a int",),
        None,
    ),
    (
        "non-awaitable",
        _override_async_non_awaitable,
        "GenreOrder.apply_async returned a non-awaitable value",
        ("expected an awaitable coroutine or Future.",),
        None,
    ),
    (
        "residual-awaitable",
        _override_async_residual_awaitable,
        "GenreOrder.apply_async returned a residual awaitable value",
        ("expected a QuerySet.",),
        (_ORDER_RESIDUAL_AWAITABLE, _ORDER_RESIDUAL_BODY_RAN),
    ),
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "override",
        "message_start",
        "substrings",
        "residual",
    ),
    [row[1:] for row in _CONNECTION_MALFORMED_APPLY_ASYNC_ROWS],
    ids=[row[0] for row in _CONNECTION_MALFORMED_APPLY_ASYNC_ROWS],
)
async def test_connection_async_branches_a_malformed_apply_async_result_names_its_own_defect(
    monkeypatch: pytest.MonkeyPatch,
    override: _OrderApplyAsyncOverride,
    message_start: str,
    substrings: tuple[str, ...],
    residual: _ResidualHolders | None,
):
    """Each malformed ``apply_async`` result names its exact defect over ``/graphql-async/``.

    The async pipeline awaits the SAME post-``OrderSet`` seal the sync one
    calls, so every defect class the sync matrix pins has to arrive here too;
    unsealed, the Relay window would be taken on whatever the override handed
    back. The field carries an ``async def`` consumer resolver, which is what
    puts the request on that pipeline. Each row asserts the typed rejection,
    that the override was entered, and that no raw exception text reaches the
    payload. The residual row additionally reads the disposal: the refused
    second awaitable is CLOSED and its body never ran, so the seal released it
    instead of awaiting an unbounded chain.
    """
    await library_models.Genre.objects.acreate(name="A")
    monkeypatch.setattr(GenreOrder, "apply_async", classmethod(override))

    _ASYNC_APPLY_CALLS.clear()

    payload = await _post_async_genres(_GENRE_ASYNC_CONNECTION_ORDER_QUERY)

    assert _ASYNC_APPLY_CALLS, payload
    assert payload["data"] is None, payload
    message = payload["errors"][0]["message"]
    _assert_async_rejection_message(message, message_start, substrings)
    if residual is not None:
        _assert_residual_awaitable_disposed(*residual)


@pytest.mark.django_db(transaction=True)
async def test_connection_async_healthy_apply_async_override_still_returns_ordered_edges(
    monkeypatch: pytest.MonkeyPatch,
):
    """A ``super()`` pass-through ``apply_async`` is ACCEPTED and the ordered page is served.

    The async seal's positive control on the async-resolver connection: it
    rejects malformed results without rejecting an ``OrderSet`` that simply
    delegates, and the sentinel shows the accepted result came through
    ``apply_async``.
    """
    await _aseed_genres("C", "A", "B")
    monkeypatch.setattr(GenreOrder, "apply_async", classmethod(_override_async_passthrough))

    _ASYNC_APPLY_CALLS.clear()

    payload = await _post_async_genres(_GENRE_ASYNC_CONNECTION_ORDER_QUERY)

    assert _ASYNC_APPLY_CALLS == ["passthrough"], payload
    assert "errors" not in payload, payload
    names = [edge["node"]["name"] for edge in payload["data"]["genres"]["edges"]]
    assert names == ["A", "B", "C"]


@pytest.mark.django_db(transaction=True)
async def test_connection_async_serves_a_combined_apply_async_result_as_its_primary_key_set(
    monkeypatch: pytest.MonkeyPatch,
):
    """An ``apply_async`` returning an ordered union is served as the rows it selects, in order."""

    async def _combined(
        cls: type[GenreOrder],
        order_input: object,
        queryset: models.QuerySet[library_models.Genre],
        info: object,
    ):
        _ASYNC_APPLY_CALLS.append("combined")
        return queryset.filter(name="C").union(queryset.filter(name="A")).order_by("-name")

    await _aseed_genres("C", "A", "B")
    monkeypatch.setattr(GenreOrder, "apply_async", classmethod(_combined))

    _ASYNC_APPLY_CALLS.clear()

    payload = await _post_async_genres(_GENRE_ASYNC_CONNECTION_ORDER_QUERY)

    assert _ASYNC_APPLY_CALLS == ["combined"], payload
    assert "errors" not in payload, payload
    names = [edge["node"]["name"] for edge in payload["data"]["genres"]["edges"]]
    assert names == ["C", "A"]


_GENRE_ASYNC_CONNECTION_FILTER_QUERY = (
    '{ genres(filter: {name: {iContains: "b"}}) { edges { node { name } } } }'
)

_GENRE_FILTER_ASYNC_SHAPE_PREFIX = (
    "GenreFilter.apply_async must return an unevaluated, unsliced QuerySet of Genre rows; got "
)


async def _filter_override_async_evaluated(
    cls: type[GenreFilter],
    filter_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    [genre async for genre in queryset]
    _ASYNC_APPLY_CALLS.append("filter-evaluated")
    return queryset


async def _filter_override_async_sliced(
    cls: type[GenreFilter],
    filter_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("filter-sliced")
    return queryset.order_by("name")[:1]


async def _filter_override_async_combined_duplicates(
    cls: type[GenreFilter],
    filter_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("filter-combined-duplicates")
    return queryset.union(queryset, all=True)


async def _filter_override_async_wrong_model(
    cls: type[GenreFilter],
    filter_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("filter-wrong-model")
    return library_models.Book.objects.all()


async def _filter_override_async_in_place_routing(
    cls: type[GenreFilter],
    filter_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    set_queryset_hints(queryset, {"tenant": 2})
    _ASYNC_APPLY_CALLS.append("filter-routing-rewritten-in-place")
    return queryset


async def _filter_override_async_materialized_list(
    cls: type[GenreFilter],
    filter_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    rows = [genre async for genre in queryset]
    _ASYNC_APPLY_CALLS.append("filter-materialized-list")
    return rows


async def _filter_override_async_none(
    cls: type[GenreFilter],
    filter_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("filter-none")
    return None


async def _filter_override_async_projection(
    cls: type[GenreFilter],
    filter_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("filter-projection")
    return queryset.values("name")


async def _filter_override_async_untrusted(
    cls: type[GenreFilter],
    filter_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("filter-malformed-deferred-filter")
    return _untrusted_genre_queryset()


def _filter_override_async_non_awaitable(
    cls: type[GenreFilter],
    filter_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("filter-non-awaitable")
    return queryset


#: The FILTER arm's own residual holder pair; see ``_ORDER_RESIDUAL_AWAITABLE``.
#: The arms keep separate holders so neither row can read the other's disposal.
_FILTER_RESIDUAL_AWAITABLE: _ResidualHolder = {"coro": None}
_FILTER_RESIDUAL_BODY_RAN: list[str] = []


async def _filter_residual_inner():
    _FILTER_RESIDUAL_BODY_RAN.append("ran")


async def _filter_override_async_residual_awaitable(
    cls: type[GenreFilter],
    filter_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _FILTER_RESIDUAL_BODY_RAN.clear()
    coro = _filter_residual_inner()
    _FILTER_RESIDUAL_AWAITABLE["coro"] = coro
    _ASYNC_APPLY_CALLS.append("filter-residual-awaitable")
    return coro


async def _filter_override_async_passthrough(
    cls: type[GenreFilter],
    filter_input: object,
    queryset: models.QuerySet[library_models.Genre],
    info: object,
):
    _ASYNC_APPLY_CALLS.append("filter-passthrough")
    return await super(GenreFilter, cls).apply_async(filter_input, queryset, info)


#: Defect rows the post-sidecar seal names on the ASYNC connection pipeline for
#: the FILTER arm: ``(id, override, expected message start, required
#: substrings)``. The filter step runs before ordering, the optimizer plan and
#: the Relay window, so an unsealed return would hand every one of those a
#: widened, re-routed, sliced or already-evaluated queryset. Each request
#: carries a real ``filter:`` argument, which is what makes the pipeline invoke
#: ``GenreFilter.apply_async`` at all, and every override records itself in
#: ``_ASYNC_APPLY_CALLS`` so a row proves the seal it names was entered. The
#: fifth member is the residual holder pair the second-awaitable row owns, and
#: ``None`` for every row that returns a value directly.
_CONNECTION_MALFORMED_FILTER_APPLY_ASYNC_ROWS: tuple[
    tuple[str, _FilterApplyAsyncOverride, str, tuple[str, ...], _ResidualHolders | None],
    ...,
] = (
    (
        "evaluated",
        _filter_override_async_evaluated,
        _GENRE_FILTER_ASYNC_SHAPE_PREFIX + "evaluated defect",
        (),
        None,
    ),
    (
        "materialized-list",
        _filter_override_async_materialized_list,
        _GENRE_FILTER_ASYNC_SHAPE_PREFIX + "type defect",
        (),
        None,
    ),
    (
        "none",
        _filter_override_async_none,
        _GENRE_FILTER_ASYNC_SHAPE_PREFIX + "type defect",
        (),
        None,
    ),
    (
        "projection",
        _filter_override_async_projection,
        _GENRE_FILTER_ASYNC_SHAPE_PREFIX + "projection defect",
        (),
        None,
    ),
    (
        "wrong-model",
        _filter_override_async_wrong_model,
        _GENRE_FILTER_ASYNC_SHAPE_PREFIX + "table defect",
        (),
        None,
    ),
    (
        "sliced",
        _filter_override_async_sliced,
        _GENRE_FILTER_ASYNC_SHAPE_PREFIX + "sliced defect",
        (),
        None,
    ),
    (
        "combined-duplicates",
        _filter_override_async_combined_duplicates,
        "GenreFilter.apply_async returned a combined queryset; the visibility boundary serves "
        "a combined queryset as the set of Genre primary keys it selects",
        ("union: union(all=True) keeps duplicate rows, which a primary-key set cannot",),
        None,
    ),
    (
        "routing-rewritten-in-place",
        _filter_override_async_in_place_routing,
        "GenreFilter.apply_async changed database routing intent",
        ("expected db=None, hints={}", "got db=None, hints={'tenant': 2}"),
        None,
    ),
    (
        "malformed-deferred-filter",
        _filter_override_async_untrusted,
        _GENRE_FILTER_ASYNC_SHAPE_PREFIX + "untrusted defect",
        ("deferred filter negate is a int",),
        None,
    ),
    (
        "non-awaitable",
        _filter_override_async_non_awaitable,
        "GenreFilter.apply_async returned a non-awaitable value",
        ("expected an awaitable coroutine or Future.",),
        None,
    ),
    (
        "residual-awaitable",
        _filter_override_async_residual_awaitable,
        "GenreFilter.apply_async returned a residual awaitable value",
        ("expected a QuerySet.",),
        (_FILTER_RESIDUAL_AWAITABLE, _FILTER_RESIDUAL_BODY_RAN),
    ),
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "override",
        "message_start",
        "substrings",
        "residual",
    ),
    [row[1:] for row in _CONNECTION_MALFORMED_FILTER_APPLY_ASYNC_ROWS],
    ids=[row[0] for row in _CONNECTION_MALFORMED_FILTER_APPLY_ASYNC_ROWS],
)
async def test_connection_async_branches_a_malformed_filter_apply_async_result_names_its_defect(
    monkeypatch: pytest.MonkeyPatch,
    override: _FilterApplyAsyncOverride,
    message_start: str,
    substrings: tuple[str, ...],
    residual: _ResidualHolders | None,
):
    """Each malformed ``FilterSet.apply_async`` result names its defect over ``/graphql-async/``.

    The filter arm of the async pipeline awaits the SAME post-sidecar seal the
    ordering arm does (``utils/querysets.py::apply_filterset_async``), so every
    defect shape that matrix pins has to arrive here too. Each row asserts the
    typed rejection, that the override was entered, and that no raw exception
    text reaches the payload. The residual row additionally reads the disposal:
    the refused second awaitable is CLOSED and its body never ran.
    """
    await library_models.Genre.objects.acreate(name="B")
    monkeypatch.setattr(GenreFilter, "apply_async", classmethod(override))

    _ASYNC_APPLY_CALLS.clear()

    payload = await _post_async_genres(_GENRE_ASYNC_CONNECTION_FILTER_QUERY)

    assert _ASYNC_APPLY_CALLS, payload
    assert payload["data"] is None, payload
    message = payload["errors"][0]["message"]
    _assert_async_rejection_message(message, message_start, substrings)
    if residual is not None:
        _assert_residual_awaitable_disposed(*residual)


@pytest.mark.django_db(transaction=True)
async def test_connection_async_healthy_filter_apply_async_override_still_filters(
    monkeypatch: pytest.MonkeyPatch,
):
    """A ``super()`` pass-through ``apply_async`` is ACCEPTED and the filtered page is served.

    The filter seal's positive control on the async-resolver connection: it
    rejects malformed results without rejecting a ``FilterSet`` that simply
    delegates, and the sentinel shows the served page came through
    ``apply_async``.
    """
    await _aseed_genres("Alpha", "Bravo", "Charlie")
    monkeypatch.setattr(
        GenreFilter,
        "apply_async",
        classmethod(_filter_override_async_passthrough),
    )

    _ASYNC_APPLY_CALLS.clear()

    payload = await _post_async_genres(_GENRE_ASYNC_CONNECTION_FILTER_QUERY)

    assert _ASYNC_APPLY_CALLS == ["filter-passthrough"], payload
    assert "errors" not in payload, payload
    names = [edge["node"]["name"] for edge in payload["data"]["genres"]["edges"]]
    assert names == ["Bravo"]


# =============================================================================
# Offset cursor decoding. ``utils/connections.py::decode_offset_cursor`` is the
# one validator of an ``after`` / ``before`` offset cursor; these rows drive it
# through every source shape a connection slices, under the default
# (``DEBUG=False``) error policy, so each rejection is asserted as the exact
# wire message a client reads.
# =============================================================================

#: The rows each cursor-decoding page is cut from: enough that a wrapped
#: negative slice is visibly wider than the ``max_page_size`` cap below.
_CURSOR_ROW_COUNT = 40

#: The schema the cursor mounts serve for the request in flight (the same
#: per-test publication discipline as ``_ASYNC_CURRENT``).
_CURSOR_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


def _cursor(payload: str) -> str:
    """An ``arrayconnection`` cursor carrying ``payload`` verbatim."""
    return relay.to_base64("arrayconnection", payload)


def _cursor_rows() -> list[library_models.Genre]:
    return list(library_models.Genre.objects.order_by("pk"))


def _list_genres(root: object, info: strawberry.Info[object, object]):
    return _cursor_rows()


def _tuple_genres(root: object, info: strawberry.Info[object, object]):
    return tuple(_cursor_rows())


def _generator_genres(root: object, info: strawberry.Info[object, object]):
    return (genre for genre in _cursor_rows())


#: The text a consumer source or a hydrating column fails with. Shaped like what a
#: real exception carries by accident, so its absence from the body is a claim
#: about disclosure.
_SOURCE_SECRET = "internal tenant secret /srv/private/tenant-42.key"


def _failing_genres(error: Exception) -> Iterator[library_models.Genre]:
    """A consumer generator that fails on its first ``next``, the way a source lookup fails."""
    yield from ()
    raise error


def _key_error_genres(root: object, info: strawberry.Info[object, object]):
    return _failing_genres(KeyError(_SOURCE_SECRET))


def _value_error_genres(root: object, info: strawberry.Info[object, object]):
    return _failing_genres(ValueError(_SOURCE_SECRET))


async def _async_list_genres(root: object, info: strawberry.Info[object, object]):
    return await sync_to_async(_cursor_rows)()


async def _async_tuple_genres(root: object, info: strawberry.Info[object, object]):
    return tuple(await sync_to_async(_cursor_rows)())


async def _async_queryset_genres(root: object, info: strawberry.Info[object, object]):
    return library_models.Genre.objects.all()


def _cursor_schema() -> DjangoSchema:
    """One consumer-resolver connection per source shape, capped at three rows a page.

    Built per request after the harness reload (see ``_ASYNC_CURRENT``). The
    ``max_page_size`` policy is the cap a wrapped negative slice would
    otherwise widen a page past. The two failing generator sources are plain
    ``def`` resolvers that touch no database, so both mounts serve them.
    """
    importlib.import_module("config.schema")
    from apps.library.schema import GenreType

    @strawberry.type
    class Query:
        list_genres = DjangoConnectionField(GenreType, resolver=_list_genres)
        tuple_genres = DjangoConnectionField(GenreType, resolver=_tuple_genres)
        generator_genres = DjangoConnectionField(GenreType, resolver=_generator_genres)
        async_list_genres = DjangoConnectionField(GenreType, resolver=_async_list_genres)
        async_tuple_genres = DjangoConnectionField(GenreType, resolver=_async_tuple_genres)
        async_queryset_genres = DjangoConnectionField(GenreType, resolver=_async_queryset_genres)
        key_error_genres = DjangoConnectionField(GenreType, resolver=_key_error_genres)
        value_error_genres = DjangoConnectionField(GenreType, resolver=_value_error_genres)

    return DjangoSchema(
        query=Query,
        config=strawberry_config(),
        resource_policy={"max_page_size": 3},
    )


def _cursor_graphql_view(request: HttpRequest):
    schema = _CURSOR_CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


async def _async_cursor_graphql_view(request: HttpRequest):
    schema = _CURSOR_CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


# Appended here so the mounts sit beside the only rows that use them.
urlpatterns += [
    path("graphql-cursor/", _cursor_graphql_view),
    path("graphql-cursor-async/", _async_cursor_graphql_view),
]


def _cursor_page_query(field: str) -> str:
    return (
        "query($after: String, $before: String, $first: Int, $last: Int) {"
        f" {field}(after: $after, before: $before, first: $first, last: $last) {{"
        " edges { cursor node { name } } } }"
    )


def _post_local_sync(query: str, variables: JSONObject) -> JSONObject:
    _CURSOR_CURRENT["schema"] = _cursor_schema()
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            return graphql_payload(query, variables=variables, url="/graphql-cursor/")
    finally:
        _CURSOR_CURRENT["schema"] = None
        clear_url_caches()


async def _post_local_async(query: str, variables: JSONObject) -> JSONObject:
    _CURSOR_CURRENT["schema"] = await sync_to_async(_cursor_schema)()
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            result = await AsyncTestClient().query(
                query,
                variables=variables,
                assert_no_errors=False,
                url="/graphql-cursor-async/",
            )
    finally:
        _CURSOR_CURRENT["schema"] = None
        clear_url_caches()
    assert result.response.status_code == 200
    return result.response.json()


def _post_cursor_sync(field: str, variables: JSONObject) -> JSONObject:
    return _post_local_sync(_cursor_page_query(field), variables)


async def _post_cursor_async(field: str, variables: JSONObject) -> JSONObject:
    return await _post_local_async(_cursor_page_query(field), variables)


def _assert_cursor_rejected(payload: JSONObject, argument: str) -> None:
    assert payload["data"] is None, payload
    assert {error["message"] for error in payload["errors"]} == {
        f"Argument '{argument}' contains a non-existing value.",
    }, payload


#: ``(id, argument the cursor rides on, variables)``. ``before:-2, first:3``
#: would slice ``rows[0:-1]`` (39 of 40 rows past a three-row cap);
#: ``after:-2`` decodes to start -1, which slices from the last row and mints
#: an ``arrayconnection:-1`` cursor for it.
_NEGATIVE_CURSOR_ROWS = [
    ("before-first", "before", {"before": _cursor("-2"), "first": 3}),
    ("after-no-page", "after", {"after": _cursor("-2")}),
    ("after-last", "after", {"after": _cursor("-2"), "last": 2}),
]


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["listGenres", "tupleGenres"])
@pytest.mark.parametrize(
    ("argument", "variables"),
    [row[1:] for row in _NEGATIVE_CURSOR_ROWS],
    ids=[row[0] for row in _NEGATIVE_CURSOR_ROWS],
)
def test_negative_offset_cursor_on_a_sequence_resolver_is_a_cursor_error(
    field: str,
    argument: str,
    variables: JSONObject,
):
    """A list or tuple consumer resolver never serves a negative cursor as a wrapped slice."""
    library_models.Genre.objects.bulk_create(
        [library_models.Genre(name=f"g{index:02d}") for index in range(_CURSOR_ROW_COUNT)],
    )

    _assert_cursor_rejected(_post_cursor_sync(field, variables), argument)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("field", ["asyncListGenres", "asyncTupleGenres"])
@pytest.mark.parametrize(
    ("argument", "variables"),
    [row[1:] for row in _NEGATIVE_CURSOR_ROWS],
    ids=[row[0] for row in _NEGATIVE_CURSOR_ROWS],
)
async def test_negative_offset_cursor_on_an_async_sequence_resolver_is_a_cursor_error(
    field: str,
    argument: str,
    variables: JSONObject,
):
    """The async colour of the sequence-resolver rows, over ``/graphql-cursor-async/``."""
    await library_models.Genre.objects.abulk_create(
        [library_models.Genre(name=f"g{index:02d}") for index in range(_CURSOR_ROW_COUNT)],
    )

    _assert_cursor_rejected(await _post_cursor_async(field, variables), argument)


@pytest.mark.django_db
def test_negative_offset_cursor_on_a_generator_resolver_is_a_cursor_error():
    """A generator source is rejected with the package message, not ``islice``'s text."""
    library_models.Genre.objects.create(name="g00")

    payload = _post_cursor_sync("generatorGenres", {"after": _cursor("-2"), "first": 2})

    _assert_cursor_rejected(payload, "after")


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("argument", ["after", "before"])
async def test_negative_offset_cursor_on_an_async_queryset_resolver_is_a_cursor_error(
    argument: str,
):
    """A ``QuerySet`` from an async resolver gets the same message as the sync path.

    ``ListConnection`` slices an async-iterable source inside the coroutine it
    returns, so the cursor is decoded before that coroutine exists; otherwise
    Django's negative-index ``ValueError`` would surface as the policy's masked
    message.
    """
    await library_models.Genre.objects.acreate(name="g00")

    payload = await _post_cursor_async("asyncQuerysetGenres", {argument: _cursor("-2")})

    _assert_cursor_rejected(payload, argument)


_ROOT_GENRE_PAGE_QUERY = (
    "query($after: String, $before: String, $first: Int, $last: Int) {"
    " allLibraryGenresConnection(after: $after, before: $before, first: $first, last: $last) {"
    " edges { cursor node { name } } totalCount"
    " pageInfo { hasNextPage hasPreviousPage endCursor } } }"
)


@pytest.mark.django_db
def test_after_minus_one_on_the_root_connection_is_a_cursor_error():
    """``after:-1`` decodes to start 0; it is still a cursor no connection minted.

    The shipped root ``allLibraryGenresConnection`` (default resolver, ``QuerySet``
    source, ``totalCount`` variant) rejects it instead of serving page one.
    """
    library_models.Genre.objects.create(name="g00")

    payload = graphql_payload(
        _ROOT_GENRE_PAGE_QUERY,
        variables={"after": _cursor("-1"), "first": 2},
    )

    _assert_cursor_rejected(payload, "after")


#: ``(id, cursor)``: every shape that is not ``arrayconnection:<canonical index>``.
_MALFORMED_CURSOR_ROWS = [
    ("not-base64", "not-base64!"),
    ("no-colon", base64.b64encode(b"arrayconnection").decode()),
    ("foreign-prefix", relay.to_base64("GenreType", "1")),
    ("letters", _cursor("abc")),
    ("empty-index", _cursor("")),
    ("plus-sign", _cursor("+1")),
    ("negative-zero", _cursor("-0")),
    ("leading-zero", _cursor("01")),
    ("leading-space", _cursor(" 1")),
    ("underscore", _cursor("1_0")),
    ("non-ascii-digit", _cursor(chr(0x0661))),  # ARABIC-INDIC DIGIT ONE
    ("five-thousand-digits", _cursor("9" * 5000)),
]


@pytest.mark.django_db
@pytest.mark.parametrize("argument", ["after", "before"])
@pytest.mark.parametrize(
    "cursor",
    [row[1] for row in _MALFORMED_CURSOR_ROWS],
    ids=[row[0] for row in _MALFORMED_CURSOR_ROWS],
)
def test_malformed_offset_cursor_is_a_cursor_error(argument: str, cursor: str):
    """Only the minted form decodes; every other cursor is one message, no parser text."""
    library_models.Genre.objects.create(name="g00")

    payload = graphql_payload(_ROOT_GENRE_PAGE_QUERY, variables={argument: cursor})

    _assert_cursor_rejected(payload, argument)


def _root_genre_payload(variables: JSONObject) -> JSONObject:
    return graphql_payload(_ROOT_GENRE_PAGE_QUERY, variables=variables)


def _list_genre_payload(variables: JSONObject) -> JSONObject:
    return _post_cursor_sync("listGenres", variables)


#: The two source shapes the index bound is read on: a ``QuerySet`` (SQL
#: ``OFFSET``) behind the shipped root connection and a list consumer resolver
#: (Python slicing).
_BOUND_SOURCES: dict[str, Callable[[JSONObject], JSONObject]] = {
    "root-queryset": _root_genre_payload,
    "list-resolver": _list_genre_payload,
}


@pytest.mark.django_db
@pytest.mark.parametrize("argument", ["after", "before"])
@pytest.mark.parametrize("source", list(_BOUND_SOURCES))
def test_offset_cursor_index_sys_maxsize_is_a_cursor_error(source: str, argument: str):
    """``sys.maxsize`` is past the largest index a row can have, so it is no cursor.

    ``SliceMetadata`` reserves ``sys.maxsize`` as its unbounded-end sentinel and
    ``after`` adds one, so on a ``QuerySet`` this index would ask SQLite for an
    ``OFFSET`` past 64 bits.
    """
    library_models.Genre.objects.create(name="Alpha")

    payload = _BOUND_SOURCES[source]({argument: _cursor(str(sys.maxsize)), "first": 2})

    _assert_cursor_rejected(payload, argument)


@pytest.mark.django_db
@pytest.mark.parametrize("source", list(_BOUND_SOURCES))
def test_offset_cursor_index_below_sys_maxsize_is_an_ordinary_cursor(source: str):
    """The largest accepted index pages like any cursor past the last row.

    ``after: sys.maxsize - 1`` is an empty past-the-end page and
    ``before: sys.maxsize - 1`` bounds nothing, so it serves the first page.
    """
    for name in ("Alpha", "Bravo", "Charlie"):
        library_models.Genre.objects.create(name=name)
    largest = _cursor(str(sys.maxsize - 1))

    past_end = _BOUND_SOURCES[source]({"after": largest, "first": 2})
    before_end = _BOUND_SOURCES[source]({"before": largest, "first": 2})

    assert "errors" not in past_end, past_end
    assert "errors" not in before_end, before_end
    (past_end_page,) = past_end["data"].values()
    (before_end_page,) = before_end["data"].values()
    assert past_end_page["edges"] == []
    assert [edge["node"]["name"] for edge in before_end_page["edges"]] == ["Alpha", "Bravo"]


def _root_genre_page(variables: JSONObject) -> JSONObject:
    payload = _root_genre_payload(variables)
    assert "errors" not in payload, payload
    return payload["data"]["allLibraryGenresConnection"]


@pytest.mark.django_db
def test_minted_offset_cursors_still_page():
    """The positive controls: index 0, a cursor the connection minted, and an empty cursor.

    ``arrayconnection:0`` is canonical and pages past the first row; the
    ``endCursor`` the first page mints opens the second page; ``after: ""`` is
    absent (the engine's truthiness), so it serves page one.
    """
    for name in (
        "Alpha",
        "Bravo",
        "Charlie",
        "Delta",
    ):
        library_models.Genre.objects.create(name=name)

    first_page = _root_genre_page({"first": 2})
    after_zero = _root_genre_page({"after": _cursor("0"), "first": 2})
    second_page = _root_genre_page({"after": first_page["pageInfo"]["endCursor"], "first": 2})
    empty_after = _root_genre_page({"after": "", "first": 2})

    names = [edge["node"]["name"] for edge in first_page["edges"]]
    assert names == ["Alpha", "Bravo"]
    assert [edge["node"]["name"] for edge in after_zero["edges"]] == ["Bravo", "Charlie"]
    assert after_zero["pageInfo"]["hasPreviousPage"] is True
    assert [edge["node"]["name"] for edge in second_page["edges"]] == ["Charlie", "Delta"]
    assert second_page["edges"][0]["cursor"] == _cursor("2")
    assert empty_after == first_page


#: ``(id, variables, message)``: one row per ``first`` / ``last`` bound message,
#: under the mounts' three-row ``max_page_size``.
_PAGE_BOUND_ROWS = [
    ("first-negative", {"first": -1}, "Argument 'first' must be a non-negative integer."),
    ("first-over-cap", {"first": 4}, "Argument 'first' cannot be higher than 3."),
    ("last-negative", {"last": -1}, "Argument 'last' must be a non-negative integer."),
    ("last-over-cap", {"last": 4}, "Argument 'last' cannot be higher than 3."),
]


def _assert_rejected_with(payload: JSONObject, message: str) -> None:
    assert payload["data"] is None, payload
    assert [error["message"] for error in payload["errors"]] == [message], payload


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("variables", "message"),
    [row[1:] for row in _PAGE_BOUND_ROWS],
    ids=[row[0] for row in _PAGE_BOUND_ROWS],
)
def test_offset_page_bound_is_the_exact_pagination_message(variables: JSONObject, message: str):
    """Each page-size rejection reaches a ``DEBUG=False`` client as its own exact message."""
    library_models.Genre.objects.create(name="g00")

    _assert_rejected_with(_post_cursor_sync("listGenres", variables), message)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("variables", "message"),
    [row[1:] for row in _PAGE_BOUND_ROWS],
    ids=[row[0] for row in _PAGE_BOUND_ROWS],
)
async def test_async_offset_page_bound_is_the_exact_pagination_message(
    variables: JSONObject,
    message: str,
):
    """The async colour of the page-size rows, over ``/graphql-cursor-async/``."""
    await library_models.Genre.objects.acreate(name="g00")

    _assert_rejected_with(await _post_cursor_async("asyncListGenres", variables), message)


# =============================================================================
# Source and hydration failures are masked, never pagination messages. Only the
# package's own argument validation constructs a client-facing pagination
# error; an exception a consumer source or a hydrating row raises inside the
# slicer travels as itself, and the default (``DEBUG=False``) error policy
# masks it.
# =============================================================================

#: 32 lowercase hex characters and nothing else - the pinned correlation id shape.
_CORRELATION_ID = re.compile(r"\A[0-9a-f]{32}\Z")


def _assert_masked(payload: JSONObject) -> None:
    """The policy's masked shape on every error, with the exception's text nowhere in the body.

    One error per failing parent: a nullable nested connection fails once per
    parent, a non-null one once for the whole list, so the count is not the claim.
    """
    assert payload["errors"], payload
    for error in payload["errors"]:
        assert error["message"] == DEFAULT_ERROR_POLICY.message, error
        correlation_id = error["extensions"][DEFAULT_ERROR_POLICY.correlation_extension_key]
        assert _CORRELATION_ID.fullmatch(correlation_id), error
    body = json.dumps(payload)
    assert _SOURCE_SECRET not in body, body
    assert "tenant-42" not in body, body


def _fail_hydrating(
    monkeypatch: pytest.MonkeyPatch,
    model: type[models.Model],
    field_name: str,
) -> None:
    """Make every fetched row of ``model`` fail to hydrate ``field_name`` while ``monkeypatch`` holds.

    A field-level ``from_db_value`` is the converter Django runs on each fetched
    value of that column, on every database vendor, so the failure is raised
    while the slicer iterates rows - exactly where a corrupt stored value fails -
    without writing anything un-hydratable to the database.
    """

    def from_db_value(value: object, expression: object, connection: object) -> object:
        raise ValueError(_SOURCE_SECRET)

    monkeypatch.setattr(
        model._meta.get_field(field_name),
        "from_db_value",
        from_db_value,
        raising=False,
    )


def _assert_served(payload: JSONObject, *values: str) -> None:
    """The unpatched control: the same request serves its rows, so the path is live."""
    assert "errors" not in payload, payload
    body = json.dumps(payload["data"])
    for value in values:
        assert json.dumps(value) in body, payload


#: ``(genre, book)`` pairs the nested rows read: TWO parents, so a planned window
#: (one ``library_book`` statement for both) and the per-parent pipeline (one per
#: parent) are told apart by statement count.
_NESTED_ROWS = (("g00", "Dune"), ("g01", "Emma"))


def _shelve_nested_rows() -> None:
    branch = library_models.Branch.objects.create(name="Central", city="Boston")
    shelf = library_models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    for genre_name, title in _NESTED_ROWS:
        book = library_models.Book.objects.create(title=title, shelf=shelf)
        book.genres.add(library_models.Genre.objects.create(name=genre_name))


_ROOT_HYDRATION_QUERY = "{ allLibraryGenresConnection(first: 2) { edges { node { name } } } }"


@pytest.mark.django_db
def test_a_root_row_that_fails_to_hydrate_is_masked():
    """A row failing to hydrate on the shipped root connection is masked over ``/graphql/``.

    The failure is raised inside Strawberry's ``ListConnection`` slicer; it is
    the row's exception, not the client's argument, so the client reads the
    policy message rather than the converter's text.
    """
    library_models.Genre.objects.create(name="g00")
    _assert_served(graphql_payload(_ROOT_HYDRATION_QUERY), "g00")
    with pytest.MonkeyPatch.context() as monkeypatch:
        _fail_hydrating(monkeypatch, library_models.Genre, "name")
        payload = graphql_payload(_ROOT_HYDRATION_QUERY)

    _assert_masked(payload)


@pytest.mark.django_db(transaction=True)
async def test_an_async_root_row_that_fails_to_hydrate_is_masked():
    """The async colour: a ``QuerySet`` from an async resolver, iterated in the slicer's coroutine."""
    await library_models.Genre.objects.acreate(name="g00")
    query = "{ asyncQuerysetGenres(first: 2) { edges { node { name } } } }"
    _assert_served(await _post_local_async(query, {}), "g00")
    with pytest.MonkeyPatch.context() as monkeypatch:
        _fail_hydrating(monkeypatch, library_models.Genre, "name")
        payload = await _post_local_async(query, {})

    _assert_masked(payload)


#: The nested selection the hydration rows read: the BOOK's title is the column
#: that fails, so the root rows hydrate.
_NESTED_SELECTION = (
    "edges { node { name booksConnection(first: 2) { edges { node { title } } } } }"
)


def _nested_on_shipped_root() -> JSONObject:
    # The shipped schema installs the optimizer, so the nested connection is a
    # planned window prefetched while the root slicer iterates its rows.
    return graphql_payload(f"{{ allLibraryGenresConnection(first: 2) {{ {_NESTED_SELECTION} }} }}")


def _nested_on_list_resolver() -> JSONObject:
    # No optimizer on the local mount, and the list resolver has already
    # materialized the genres: the nested connection runs the per-parent
    # pipeline and its own slicer hydrates the books.
    return _post_local_sync(f"{{ listGenres(first: 2) {{ {_NESTED_SELECTION} }} }}", {})


#: ``source -> (request, library_book statements its unpatched control issues)``.
#: One statement is the planned window serving both parents; two is the
#: per-parent pipeline fetching each parent's page, so each row proves which
#: path its failure was raised on.
_NESTED_SOURCES: dict[str, tuple[Callable[[], JSONObject], int]] = {
    "planned-window": (_nested_on_shipped_root, 1),
    "per-parent": (_nested_on_list_resolver, 2),
}


@pytest.mark.django_db
@pytest.mark.parametrize("source", list(_NESTED_SOURCES))
def test_a_nested_connection_row_that_fails_to_hydrate_is_masked(source: str):
    """A nested connection's row failing to hydrate under an offset root is masked."""
    _shelve_nested_rows()
    request, book_statements = _NESTED_SOURCES[source]
    with CaptureQueriesContext(connection) as captured:
        control = request()
    _assert_served(control, "g00", "Dune", "g01", "Emma")
    book_sql = [
        entry["sql"] for entry in captured.captured_queries if "library_book" in entry["sql"]
    ]
    assert len(book_sql) == book_statements, book_sql
    with pytest.MonkeyPatch.context() as monkeypatch:
        _fail_hydrating(monkeypatch, library_models.Book, "title")
        payload = request()

    _assert_masked(payload)


@pytest.mark.django_db(transaction=True)
async def test_an_async_nested_connection_row_that_fails_to_hydrate_is_masked():
    """The async colour of the nested row, under a ``QuerySet`` from an async resolver."""
    await sync_to_async(_shelve_nested_rows)()
    query = f"{{ asyncQuerysetGenres(first: 2) {{ {_NESTED_SELECTION} }} }}"
    _assert_served(await _post_local_async(query, {}), "g00", "Dune", "g01", "Emma")
    with pytest.MonkeyPatch.context() as monkeypatch:
        _fail_hydrating(monkeypatch, library_models.Book, "title")
        payload = await _post_local_async(query, {})

    _assert_masked(payload)


#: ``field -> the exception type its generator raises``.
_FAILING_SOURCES: dict[str, type[Exception]] = {
    "keyErrorGenres": KeyError,
    "valueErrorGenres": ValueError,
}

_PACKAGE_LOGGER = "django_strawberry_framework"


def _assert_logged_source_failure(caplog: pytest.LogCaptureFixture, field: str) -> None:
    """The masked error's server-side record is the generator's own exception.

    The policy logs the ORIGINAL exception under the correlation id it handed
    the client, so this is what proves the mask covered the source's failure
    and not some other error on the same path.
    """
    records = [
        record
        for record in caplog.records
        if record.name == _PACKAGE_LOGGER and record.levelno == logging.ERROR
    ]
    assert len(records) == 1, caplog.records
    assert records[0].exc_info is not None, records[0]
    original = records[0].exc_info[1]
    assert isinstance(original, _FAILING_SOURCES[field]), original
    assert type(original) is _FAILING_SOURCES[field], original
    assert original.args == (_SOURCE_SECRET,), original


@pytest.mark.django_db
@pytest.mark.parametrize("field", list(_FAILING_SOURCES))
def test_a_consumer_source_that_raises_is_masked(caplog: pytest.LogCaptureFixture, field: str):
    """A consumer generator raising ``KeyError`` / ``ValueError`` mid-slice is masked.

    Nothing between the slicer and the client catches either one: the
    consumer's exception is not a statement for the client, so it reaches the
    policy as itself rather than as a ``GraphQLError`` carrying its text.
    """
    caplog.set_level(logging.ERROR, logger=_PACKAGE_LOGGER)

    _assert_masked(_post_cursor_sync(field, {"first": 2}))
    _assert_logged_source_failure(caplog, field)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("field", list(_FAILING_SOURCES))
async def test_an_async_view_consumer_source_that_raises_is_masked(
    caplog: pytest.LogCaptureFixture,
    field: str,
):
    """The same generator sources over ``/graphql-cursor-async/``."""
    caplog.set_level(logging.ERROR, logger=_PACKAGE_LOGGER)

    _assert_masked(await _post_cursor_async(field, {"first": 2}))
    _assert_logged_source_failure(caplog, field)
