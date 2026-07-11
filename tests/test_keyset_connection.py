"""Keyset-connection resolve-side tests: mode routing, slicer guards, order state.

The live acceptance surface (round-trips, stability, nested windows,
permission-aware decode) runs in
``examples/fakeshop/test_query/test_keyset_api.py``. These stay package-side
per the README's "genuinely unreachable from a live query" clause: the
generated-class keyset-state cache, the slicer's structural guards (the
non-queryset source, the pre-sliced source), the ``orderBy``-derivation error
arms driven with hand-built order states, the async execution color (the live
``/graphql/`` view is sync-only), and the defensive backward-window arm the
walker never plans.
"""

from types import SimpleNamespace

import pytest
import strawberry
from apps.library.models import Book, Issue, Patron, Periodical
from apps.scalars.models import ScalarSpecimen
from django.db.models import Count, F
from graphql import GraphQLError
from strategy_schemas import make_django_type

from django_strawberry_framework import (
    DjangoConnectionField,
    finalize_django_types,
)
from django_strawberry_framework.connection import (
    _connection_type_for,
    _keyset_connection_context,
    _keyset_order_ref,
    _keyset_order_state,
    _resolve_from_window,
    _resolve_order_path_field,
    _WindowedConnectionRows,
)
from django_strawberry_framework.keyset import cursor_columns_for, order_fingerprint
from django_strawberry_framework.optimizer.plans import WINDOW_ROW_NUMBER, WINDOW_TOTAL_COUNT
from django_strawberry_framework.optimizer.walker import (
    _extend_only_projection,
    _keyset_cursor_context,
    _keyset_window_slice_from_arguments,
)
from django_strawberry_framework.utils.connections import UnwindowableConnection

ISSUE_ORDER = ("-number", "id")


@pytest.fixture(autouse=True)
def _registry(isolate_global_registry):
    """Registry + connection-type-cache isolation around every test here."""
    return isolate_global_registry


def _make_issue_type(name: str = "KeysetIssueNode", **meta_extra):
    return make_django_type(
        name,
        Issue,
        ("id", "number", "title"),
        meta_extra={
            "cursor_field": ISSUE_ORDER,
            "connection": {"total_count": True},
            **meta_extra,
        },
    )


def _issue_state(issue_type):
    finalize_django_types()
    return _keyset_connection_context(_connection_type_for(issue_type))


# =============================================================================
# keyset-mode resolution + class cache
# =============================================================================


def test_keyset_connection_context_resolves_and_caches():
    issue_type = _make_issue_type()
    finalize_django_types()
    connection_type = _connection_type_for(issue_type)
    state = _keyset_connection_context(connection_type)
    assert state is not None
    assert state.cursor_field == ISSUE_ORDER
    assert state.fingerprint == order_fingerprint(ISSUE_ORDER)
    # Second read serves the class-cached state object.
    assert _keyset_connection_context(connection_type) is state


def test_keyset_connection_context_is_none_for_offset_types():
    plain_type = make_django_type("PlainIssueNode", Issue, ("id", "number"))
    finalize_django_types()
    connection_type = _connection_type_for(plain_type)
    assert _keyset_connection_context(connection_type) is None
    # The negative result is cached too (the ``False`` sentinel round-trip).
    assert _keyset_connection_context(connection_type) is None


def test_walker_keyset_cursor_context_none_without_cursor_field():
    plain_type = make_django_type("PlainIssueNode2", Issue, ("id", "number"))
    assert _keyset_cursor_context(plain_type) is None
    assert _keyset_cursor_context(None) is None


# =============================================================================
# the slicer's structural guards (through-schema)
# =============================================================================


@pytest.mark.django_db
def test_keyset_connection_rejects_non_queryset_source():
    issue_type = _make_issue_type("KeysetListSourceNode")

    def _list_resolver(root, info):
        return list(Issue.objects.all())

    @strawberry.type
    class Query:
        issues = DjangoConnectionField(issue_type, resolver=_list_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    periodical = Periodical.objects.create(name="P")
    Issue.objects.create(periodical=periodical, number=1, title="one")
    result = schema.execute_sync("{ issues(first: 1) { edges { cursor } } }")
    assert result.errors
    assert "must return a QuerySet" in str(result.errors[0])


@pytest.mark.django_db
def test_keyset_connection_rejects_pre_sliced_source():
    issue_type = _make_issue_type("KeysetSlicedSourceNode")

    def _sliced_resolver(root, info):
        return Issue.objects.all()[:5]

    @strawberry.type
    class Query:
        issues = DjangoConnectionField(issue_type, resolver=_sliced_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ issues(first: 1) { edges { cursor } } }")
    assert result.errors
    assert "already-sliced" in str(result.errors[0])


@pytest.mark.django_db
def test_bare_keyset_connection_routes_through_keyset_slicer():
    issue_type = _make_issue_type("BareKeysetNode", connection=None)

    @strawberry.type
    class Query:
        issues = DjangoConnectionField(issue_type)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    periodical = Periodical.objects.create(name="P")
    Issue.objects.create(periodical=periodical, number=1, title="one")
    result = schema.execute_sync("{ issues(first: 1) { edges { cursor } } }")
    assert not result.errors, result.errors
    assert len(result.data["issues"]["edges"]) == 1


@pytest.mark.django_db
def test_keyset_connection_validates_page_sizes_and_sync_count_only():
    issue_type = _make_issue_type("KeysetValidationNode")

    @strawberry.type
    class Query:
        issues = DjangoConnectionField(issue_type)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    negative = schema.execute_sync("{ issues(first: -1) { edges { cursor } } }")
    assert negative.errors
    assert "non-negative" in str(negative.errors[0])

    over_cap = schema.execute_sync("{ issues(first: 101) { edges { cursor } } }")
    assert over_cap.errors
    assert "cannot be higher than 100" in str(over_cap.errors[0])

    count_only = schema.execute_sync("{ issues { totalCount } }")
    assert not count_only.errors, count_only.errors
    assert count_only.data["issues"]["totalCount"] == 0


@pytest.mark.django_db(transaction=True)
async def test_keyset_connection_async_execution_slices_and_counts():
    """The async color: coroutine slicing via the async engine + ``acount``."""
    issue_type = _make_issue_type("KeysetAsyncNode")

    async def _async_resolver(root, info):
        return Issue.objects.all()

    @strawberry.type
    class Query:
        issues = DjangoConnectionField(issue_type, resolver=_async_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    periodical = await Periodical.objects.acreate(name="P")
    for number in (1, 2, 3):
        await Issue.objects.acreate(periodical=periodical, number=number, title=f"i{number}")
    result = await schema.execute(
        """
        { issues(first: 2) { totalCount
            pageInfo { hasNextPage endCursor }
            edges { node { title } } } }
        """,
    )
    assert not result.errors, result.errors
    connection_payload = result.data["issues"]
    assert connection_payload["totalCount"] == 3
    assert connection_payload["pageInfo"]["hasNextPage"] is True
    assert [e["node"]["title"] for e in connection_payload["edges"]] == ["i3", "i2"]
    # Round-trip the minted cursor on the async path too.
    result = await schema.execute(
        """
        query($c: String!) { issues(first: 2, after: $c) { edges { node { title } } } }
        """,
        variable_values={"c": connection_payload["pageInfo"]["endCursor"]},
    )
    assert not result.errors, result.errors
    assert [e["node"]["title"] for e in result.data["issues"]["edges"]] == ["i1"]


@pytest.mark.django_db(transaction=True)
async def test_keyset_connection_async_total_count_only_uses_acount():
    """A totalCount-only async query must not call synchronous ``QuerySet.count()``."""
    issue_type = _make_issue_type("KeysetAsyncCountOnlyNode")

    async def _async_resolver(root, info):
        return Issue.objects.all()

    @strawberry.type
    class Query:
        issues = DjangoConnectionField(issue_type, resolver=_async_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    periodical = await Periodical.objects.acreate(name="P")
    for number in (1, 2, 3):
        await Issue.objects.acreate(periodical=periodical, number=number, title=f"i{number}")
    result = await schema.execute("{ issues { totalCount } }")
    assert not result.errors, result.errors
    assert result.data["issues"]["totalCount"] == 3


@pytest.mark.django_db(transaction=True)
async def test_keyset_connection_async_deferred_cursor_column_is_loaded():
    """Cursor minting must not lazy-load a deferred order column in async execution."""
    issue_type = _make_issue_type("KeysetAsyncDeferredCursorNode")

    async def _async_resolver(root, info):
        return Issue.objects.defer("number", "title")

    @strawberry.type
    class Query:
        issues = DjangoConnectionField(issue_type, resolver=_async_resolver)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    periodical = await Periodical.objects.acreate(name="P")
    await Issue.objects.acreate(periodical=periodical, number=1, title="one")
    result = await schema.execute("{ issues(first: 1) { edges { cursor } } }")
    assert not result.errors, result.errors
    assert len(result.data["issues"]["edges"]) == 1


# =============================================================================
# the defensive backward-window arm (never planned by the walker)
# =============================================================================


@pytest.mark.django_db
def test_backward_args_over_a_window_wrapper_fall_back_to_the_keyset_slicer():
    issue_type = _make_issue_type("KeysetBackwardWindowNode")
    finalize_django_types()
    connection_type = _connection_type_for(issue_type)
    periodical = Periodical.objects.create(name="P")
    for number in (1, 2, 3):
        Issue.objects.create(periodical=periodical, number=number, title=f"i{number}")
    wrapper = _WindowedConnectionRows(rows=[], fallback=lambda: Issue.objects.all())
    info = SimpleNamespace(
        # ``edges`` selected so the slicer's edge-resolution gate
        # (``should_resolve_list_connection_edges``) actually slices.
        selected_fields=[
            SimpleNamespace(
                name="issues",
                selections=[SimpleNamespace(name="edges", selections=[])],
            ),
        ],
        _raw_info=SimpleNamespace(field_nodes=[]),
        schema=SimpleNamespace(config=SimpleNamespace(relay_max_results=100)),
    )
    connection_payload = connection_type.resolve_connection(wrapper, info=info, last=2)
    # ``last`` over a window wrapper cannot be served by the (forward-only)
    # keyset window - the wrapper's fallback queryset routes through the
    # keyset slicer instead, backward semantics intact.
    assert [edge.node.title for edge in connection_payload.edges] == ["i2", "i1"]
    assert connection_payload.page_info.has_previous_page is True


@pytest.mark.django_db
def test_counted_keyset_window_without_seek_count_falls_back():
    issue_type = _make_issue_type("KeysetCountDriftNode")
    state = _issue_state(issue_type)
    connection_type = _connection_type_for(issue_type)
    row = SimpleNamespace(
        id=1,
        number=1,
        **{WINDOW_ROW_NUMBER: 1, WINDOW_TOTAL_COUNT: 3},
    )
    info = SimpleNamespace(
        selected_fields=[
            SimpleNamespace(
                name="issues",
                selections=[
                    SimpleNamespace(
                        name="pageInfo",
                        selections=[SimpleNamespace(name="hasNextPage", selections=[])],
                    ),
                ],
            ),
        ],
    )
    window = _WindowedConnectionRows(rows=[row], fallback=lambda: Issue.objects.all())
    assert (
        _resolve_from_window(
            connection_type,
            window,
            info=info,
            offset=0,
            limit=2,
            want_count=False,
            keyset_state=state,
            keyset_after="cursor",
        )
        is None
    )


# =============================================================================
# order-state derivation error arms (hand-built states)
# =============================================================================


def _issue_order_state():
    issue_type = _make_issue_type("KeysetOrderStateNode")
    return _issue_state(issue_type)


@pytest.mark.django_db
def test_keyset_order_state_default_order_reuses_declared_columns():
    state = _issue_order_state()
    columns, fingerprint, _queryset = _keyset_order_state(
        state,
        Issue.objects.order_by(*ISSUE_ORDER),
    )
    assert columns is state.columns
    assert fingerprint == state.fingerprint
    # The defensive no-order shape gets the declared order applied.
    _columns, fingerprint2, ordered = _keyset_order_state(state, Issue.objects.all())
    assert fingerprint2 == state.fingerprint
    assert tuple(ordered.query.order_by) == ISSUE_ORDER


@pytest.mark.django_db
def test_keyset_order_state_rejects_expression_orders():
    state = _issue_order_state()
    aggregated = Issue.objects.annotate(loan_count=Count("periodical")).order_by("loan_count")
    with pytest.raises(GraphQLError, match="cannot anchor stable cursors"):
        _keyset_order_state(state, aggregated)


@pytest.mark.django_db
def test_keyset_order_state_rejects_explicit_nulls_positioning():
    state = _issue_order_state()
    positioned = Issue.objects.order_by(F("title").asc(nulls_last=True))
    with pytest.raises(GraphQLError, match="cannot anchor stable cursors"):
        _keyset_order_state(state, positioned)


@pytest.mark.django_db
def test_keyset_order_state_rejects_nullable_columns():
    # A hand-built state over Book (whose ``subtitle`` is nullable) - the
    # arm is unreachable over Issue, whose columns are all non-null.
    state_stub = SimpleNamespace(
        definition=SimpleNamespace(model=Book),
        cursor_field=("title", "id"),
        columns=cursor_columns_for(Book, ("title", "id")),
        fingerprint=order_fingerprint(("title", "id")),
    )
    with pytest.raises(GraphQLError, match="'subtitle' is nullable"):
        _keyset_order_state(state_stub, Book.objects.order_by("subtitle", "id"))


@pytest.mark.django_db
def test_keyset_order_state_rejects_json_columns():
    state_stub = SimpleNamespace(
        definition=SimpleNamespace(model=ScalarSpecimen),
        cursor_field=("label",),
        columns=cursor_columns_for(ScalarSpecimen, ("label",)),
        fingerprint=order_fingerprint(("label",)),
    )
    with pytest.raises(GraphQLError, match="ordering differs between database backends"):
        _keyset_order_state(
            state_stub,
            ScalarSpecimen.objects.order_by("payload", "id"),
        )


@pytest.mark.django_db
def test_keyset_order_state_annotates_related_paths():
    state = _issue_order_state()
    columns, fingerprint, queryset = _keyset_order_state(
        state,
        Issue.objects.order_by("periodical__name", "id"),
    )
    assert fingerprint == "periodical__name,id"
    assert columns[0].value_source == "_dst_cursor_value_0"
    assert "_dst_cursor_value_0" in queryset.query.annotations


@pytest.mark.django_db
def test_keyset_order_state_rejects_optional_or_multivalued_related_paths():
    state_stub = SimpleNamespace(
        definition=SimpleNamespace(model=Patron),
        cursor_field=("name",),
        columns=cursor_columns_for(Patron, ("name",)),
        fingerprint=order_fingerprint(("name",)),
    )
    for order in (("card__barcode", "id"), ("loans__note", "id")):
        with pytest.raises(GraphQLError, match="cannot anchor stable cursors"):
            _keyset_order_state(state_stub, Patron.objects.order_by(*order))


def test_keyset_order_ref_parses_strings_and_rejects_nulls():
    assert _keyset_order_ref("-number") == ("-number", "number", True)
    assert _keyset_order_ref(F("number").asc()) == ("number", "number", False)
    assert _keyset_order_ref(F("number").desc(nulls_first=True)) is None
    assert _keyset_order_ref(SimpleNamespace(expression=None, descending=False)) is None


def test_resolve_order_path_field_arms():
    # Local column; pk alias; related path terminal.
    assert _resolve_order_path_field(Issue, "number").name == "number"
    assert _resolve_order_path_field(Issue, "pk").name == "id"
    assert _resolve_order_path_field(Issue, "periodical__name").name == "name"
    # Unknown segment; relation terminal; a path THROUGH a non-relation;
    # optional reverse-one and multi-valued reverse paths.
    assert _resolve_order_path_field(Issue, "nope") is None
    assert _resolve_order_path_field(Issue, "periodical") is None
    assert _resolve_order_path_field(Issue, "title__x") is None
    assert _resolve_order_path_field(Patron, "card__barcode") is None
    assert _resolve_order_path_field(Patron, "loans__note") is None

    detached_relation = SimpleNamespace(
        is_relation=True,
        auto_created=False,
        many_to_many=False,
        one_to_many=False,
        null=False,
        related_model=None,
    )
    detached_model = SimpleNamespace(
        _meta=SimpleNamespace(get_field=lambda _name: detached_relation),
    )
    assert _resolve_order_path_field(detached_model, "relation__value") is None

    virtual_field = SimpleNamespace(
        is_relation=False,
        concrete=False,
        related_model=None,
    )
    virtual_model = SimpleNamespace(
        _meta=SimpleNamespace(get_field=lambda _name: virtual_field),
    )
    assert _resolve_order_path_field(virtual_model, "virtual") is None


# =============================================================================
# walker helpers
# =============================================================================


class _FakeInfo:
    schema = SimpleNamespace(config=SimpleNamespace(relay_max_results=100))


@pytest.mark.django_db
def test_keyset_window_slice_from_arguments_arms():
    issue_type = _make_issue_type("KeysetWalkerSliceNode")
    finalize_django_types()
    columns, fingerprint = _keyset_cursor_context(issue_type)
    info = _FakeInfo()

    # No cursor: a plain forward window, no seek.
    window, seek = _keyset_window_slice_from_arguments(
        {"first": 2},
        info,
        columns=columns,
        fingerprint=fingerprint,
    )
    assert window == (0, 2, False)
    assert seek is None

    # A valid minted cursor decodes into the seek.
    periodical = Periodical.objects.create(name="P")
    issue = Issue.objects.create(periodical=periodical, number=1, title="one")
    from django_strawberry_framework.keyset import encode_keyset_cursor

    cursor = encode_keyset_cursor(columns, issue, fingerprint=fingerprint)
    window, seek = _keyset_window_slice_from_arguments(
        {"first": 2, "after": cursor},
        info,
        columns=columns,
        fingerprint=fingerprint,
    )
    assert window == (0, 2, False)
    assert seek is not None
    assert seek.cursor.values == (1, issue.pk)

    # Malformed pagination and malformed cursors both map to ``None``,
    # including backward shapes that would otherwise be unwindowable.
    assert (
        _keyset_window_slice_from_arguments(
            {"first": -1},
            info,
            columns=columns,
            fingerprint=fingerprint,
        )
        is None
    )
    assert (
        _keyset_window_slice_from_arguments(
            {"before": "garbage", "last": 2},
            info,
            columns=columns,
            fingerprint=fingerprint,
        )
        is None
    )
    assert (
        _keyset_window_slice_from_arguments(
            {"after": "garbage", "last": 2},
            info,
            columns=columns,
            fingerprint=fingerprint,
        )
        is None
    )
    assert (
        _keyset_window_slice_from_arguments(
            {"first": 2, "after": "garbage"},
            info,
            columns=columns,
            fingerprint=fingerprint,
        )
        is None
    )

    # Backward shapes propagate the fallback signal.
    with pytest.raises(UnwindowableConnection):
        _keyset_window_slice_from_arguments(
            {"last": 2},
            info,
            columns=columns,
            fingerprint=fingerprint,
        )


@pytest.mark.django_db
def test_extend_only_projection_arms():
    from django_strawberry_framework.optimizer.plans import deferred_loading_of

    # Unreadable/non-queryset state: defensive passthrough.
    sentinel = object()
    assert _extend_only_projection(sentinel, ("number",)) is sentinel

    # No projection: untouched.
    plain = Issue.objects.all()
    assert _extend_only_projection(plain, ("number",)) is plain
    # Explicit empty only() state: untouched.
    only_empty = Issue.objects.only()
    assert _extend_only_projection(only_empty, ("number",)) is only_empty
    # defer() mode that does not mask a cursor column is untouched.
    deferred = Issue.objects.defer("title")
    assert _extend_only_projection(deferred, ("number",)) is deferred
    # A deferred cursor column is restored while unrelated defers survive.
    masked_deferred = Issue.objects.defer("number", "title")
    extended_deferred = _extend_only_projection(masked_deferred, ("number",))
    names, defer_flag = deferred_loading_of(extended_deferred)
    assert defer_flag is True
    assert names == frozenset({"title"})
    # Already-covered names: untouched.
    covered = Issue.objects.only("number", "id")
    assert _extend_only_projection(covered, ("number",)) is covered
    # A missing cursor column joins the load-only set.
    masked = Issue.objects.only("title")
    extended = _extend_only_projection(masked, ("number",))
    names, defer_flag = deferred_loading_of(extended)
    assert defer_flag is False
    assert "number" in names and "title" in names
