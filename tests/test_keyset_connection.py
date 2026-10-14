"""Package-side keyset connection tests for class-cached cursor state, defensive window fallbacks, order-state derivation, and nested-planner helpers.

Consumer-visible keyset behaviour lives in
``examples/fakeshop/test_query/test_keyset_api.py`` (root and nested
round-trips, resolver-contract refusals over HTTP, and the async slicer colour
on ``/graphql-async/``). Pagination bound errors on the shipped keyset field
live in ``examples/fakeshop/test_query/test_connection_pagination_api.py``.

This module keeps claims no GraphQL request can express:

- The generated connection class's ``_dst_keyset_state`` slot (identity cache
  and the offset-type ``None`` sentinel). The live sibling is
  ``test_root_keyset_first_page_orders_by_cursor_field``. A ``cursor_field``
  type with no ``Meta.connection`` still resolves as keyset-mode here:
  live ``IssueType`` always declares ``connection``, and a live module cannot
  register a second ``DjangoType`` after finalize.
- ``declared_cursor_state_for_definition`` lookup, including a ``None``
  definition.
- Defensive ``_WindowedConnectionRows`` arms the walker never plans: ``last``
  over a window wrapper, and a counted keyset window missing the seek-count
  annotation. Nested ``last:`` / ``before:`` over HTTP fall back before a
  wrapper is built
  (``test_nested_keyset_backward_falls_back_per_parent_with_same_cursors``).
- ``_keyset_order_state`` derivation (``plans.py::effective_cursor_state``)
  with hand-built states: column-object
  reuse, and rejection of expression / nulls-positioning / nullable / JSON /
  optional-or-multivalued related orders. ``IssueOrder`` only publishes
  non-null local and required-FK paths, so those error arms are not reachable
  on the shipped schema. Related-path acceptance is live
  (``test_root_keyset_order_by_related_path_seeks_via_annotation``).
- A ``ForeignObject`` ``orderBy:`` term paged by a seek over its carrier
  columns, on the test-local ``LnkPairChild``: the fakeshop link
  (``ShelfLabel.shelf``) has a relation carrier and a target type that hides
  rows, so a keyset connection refuses its term.
- Pure ``plans.py`` helpers ``_keyset_order_ref`` and ``_resolve_order_path_field``
  (including detached / virtual fields, and the ``LendingDesk.venue_ptr``
  parent link no keyset type orders through).
- Nested-planner ``_keyset_window_slice_from_arguments`` returning ``None`` /
  ``UnwindowableConnection`` (the walker swallows those internally). Live
  nested first/after/last rows pin the consumer consequence.
- ``_extend_only_projection`` passthrough arms. The consumer-visible restore
  of a deferred cursor column is live
  (``test_nested_keyset_unselected_cursor_column_is_not_lazy_loaded_per_edge``)
  and on the async holder
  (``test_async_keyset_deferred_cursor_column_is_loaded``).
"""

from types import SimpleNamespace

import pytest
import strawberry
from apps.library.models import Book, Issue, LendingDesk, Patron, Periodical
from apps.scalars.models import ScalarSpecimen
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.db.models import Count, F, Model, QuerySet
from django.http import HttpRequest
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from graphql import GraphQLError
from strategy_schemas import make_django_type
from strawberry.schema.config import StrawberryConfig

from django_strawberry_framework import DjangoConnectionField, DjangoType, finalize_django_types
from django_strawberry_framework.connection import (
    DjangoConnection,
    _connection_type_for,
    _keyset_connection_context,
    _keyset_order_state,
    _resolve_from_window,
    _WindowedConnectionRows,
)
from django_strawberry_framework.keyset import (
    CursorState,
    cursor_columns_for,
    declared_cursor_state_for_definition,
    order_fingerprint,
)
from django_strawberry_framework.optimizer.nested_planner import (
    _extend_only_projection,
    _keyset_window_slice_from_arguments,
)
from django_strawberry_framework.optimizer.plans import (
    WINDOW_ROW_NUMBER,
    WINDOW_TOTAL_COUNT,
    _keyset_order_ref,
    _resolve_order_path_field,
    deferred_loading_of,
)
from django_strawberry_framework.orders import Ordering, OrderSet, RelatedOrder
from django_strawberry_framework.utils.connections import UnwindowableConnection
from tests._info import make_info
from tests.optimizer._link_models import LnkPairChild, link_fixture_tables

ISSUE_ORDER = ("-number", "id")


pytestmark = pytest.mark.usefixtures("isolate_global_registry")


def _make_issue_type(name: str = "KeysetIssueNode", **meta_extra: object) -> type[DjangoType]:
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


def _issue_connection_of(node_type: type[DjangoType]) -> type[DjangoConnection[DjangoType]]:
    """The generated connection class over ``node_type``, an ``Issue`` node."""
    return _connection_type_for(node_type, node_type.__django_strawberry_definition__)


def _issue_state(issue_type: type):
    finalize_django_types()
    return _keyset_connection_context(_issue_connection_of(issue_type))


# =============================================================================
# keyset-mode resolution + class cache
# =============================================================================


def test_keyset_connection_context_resolves_and_caches():
    issue_type = _make_issue_type()
    finalize_django_types()
    connection_type = _issue_connection_of(issue_type)
    state = _keyset_connection_context(connection_type)
    assert state is not None
    assert state.cursor_field == ISSUE_ORDER
    assert state.fingerprint == order_fingerprint(ISSUE_ORDER)
    # Second read serves the class-cached state object.
    assert _keyset_connection_context(connection_type) is state


def test_keyset_connection_context_is_none_for_offset_types():
    plain_type = make_django_type("PlainIssueNode", Issue, ("id", "number"))
    finalize_django_types()
    connection_type = _issue_connection_of(plain_type)
    assert _keyset_connection_context(connection_type) is None
    # The negative result is cached too (the ``False`` sentinel round-trip).
    assert _keyset_connection_context(connection_type) is None


def test_keyset_connection_context_resolves_without_connection_opt_in():
    """A ``cursor_field`` type with no ``Meta.connection`` is still keyset-mode.

    ``Meta.connection`` only opts into ``totalCount``. Keyset vocabulary is
    ``cursor_field``. The minted prefix on default-order shipped ``IssueType``
    is ``test_root_keyset_first_page_orders_by_cursor_field``. A live module
    cannot register a second ``DjangoType`` after finalize, so the
    ``connection=None`` generation path stays here.
    """
    issue_type = _make_issue_type("BareKeysetNode", connection=None)
    finalize_django_types()
    connection_type = _issue_connection_of(issue_type)
    state = _keyset_connection_context(connection_type)
    assert state is not None
    assert state.cursor_field == ISSUE_ORDER


def test_declared_cursor_state_for_definition_resolves_the_declared_vocabulary():
    issue_type = _make_issue_type()
    definition = issue_type.__django_strawberry_definition__
    state = declared_cursor_state_for_definition(definition)
    assert state is not None
    assert state.definition is definition
    assert state.cursor_field == ISSUE_ORDER
    assert state.columns == cursor_columns_for(Issue, ISSUE_ORDER)
    assert state.fingerprint == order_fingerprint(ISSUE_ORDER)


def test_declared_cursor_state_for_definition_none_without_cursor_field():
    plain_type = make_django_type("PlainIssueNode2", Issue, ("id", "number"))
    assert (
        declared_cursor_state_for_definition(plain_type.__django_strawberry_definition__) is None
    )
    assert declared_cursor_state_for_definition(None) is None


# =============================================================================
# the defensive backward-window arm (never planned by the walker)
# =============================================================================


@pytest.mark.django_db
def test_backward_args_over_a_window_wrapper_fall_back_to_the_keyset_slicer():
    issue_type = _make_issue_type("KeysetBackwardWindowNode")
    finalize_django_types()
    connection_type = _issue_connection_of(issue_type)
    periodical = Periodical.objects.create(name="P")
    for number in (1, 2, 3):
        Issue.objects.create(periodical=periodical, number=number, title=f"i{number}")
    wrapper = _WindowedConnectionRows(
        rows=[],
        fallback=Issue.objects.all,
        keyset_state=_keyset_connection_context(connection_type),
    )
    # ``edges`` selected so the slicer's edge-resolution gate
    # (``should_resolve_list_connection_edges``) actually slices.
    info = make_info(
        field_name="issues",
        selections="{ edges }",
        config=StrawberryConfig(relay_max_results=100),
    )
    connection_payload = connection_type.resolve_connection(wrapper, info=info, last=2)
    # ``last`` over a window wrapper cannot be served by the (forward-only)
    # keyset window - the wrapper's fallback queryset routes through the
    # keyset slicer instead, backward semantics intact.
    assert isinstance(connection_payload, DjangoConnection)
    # The connection is typed over its DjangoType; the rows it pages are Issue rows.
    nodes = [edge.node for edge in connection_payload.edges]
    assert [node.title for node in nodes if isinstance(node, Issue)] == ["i2", "i1"]
    assert len(nodes) == 2
    assert connection_payload.page_info.has_previous_page is True


@pytest.mark.django_db
@pytest.mark.parametrize("seek", [False, True], ids=["first-page", "after-page"])
def test_keyset_window_without_a_published_vocabulary_is_served_per_parent(seek: bool):
    """A keyset wrapper carrying no planned vocabulary never mints from its rows.

    The window rows (one decoy row here) were ordered and seeked under a
    vocabulary the resolver cannot see, so the fallback queryset runs through
    the keyset slicer instead, on a first page and on an ``after:`` page alike,
    even where the window could serve the forward page.
    """
    from django_strawberry_framework.keyset import encode_keyset_cursor

    issue_type = _make_issue_type("KeysetUnpublishedWindowNode")
    finalize_django_types()
    connection_type = _issue_connection_of(issue_type)
    state = _keyset_connection_context(connection_type)
    assert state is not None
    periodical = Periodical.objects.create(name="P")
    newest = None
    for number in (1, 2, 3):
        newest = Issue.objects.create(periodical=periodical, number=number, title=f"i{number}")
    assert newest is not None
    decoy = Issue(id=99, number=99, title="decoy")
    vars(decoy).update({WINDOW_ROW_NUMBER: 1, WINDOW_TOTAL_COUNT: 1})
    wrapper = _WindowedConnectionRows(rows=[decoy], fallback=Issue.objects.all)
    info = make_info(
        field_name="issues",
        selections="{ edges }",
        config=StrawberryConfig(relay_max_results=100),
    )
    after = (
        encode_keyset_cursor(state.columns, newest, fingerprint=state.fingerprint)
        if seek
        else None
    )
    connection_payload = connection_type.resolve_connection(
        wrapper,
        info=info,
        first=2,
        after=after,
    )
    assert isinstance(connection_payload, DjangoConnection)
    nodes = [edge.node for edge in connection_payload.edges]
    titles = [node.title for node in nodes if isinstance(node, Issue)]
    assert titles == (["i2", "i1"] if seek else ["i3", "i2"])
    assert len(nodes) == 2


@pytest.mark.django_db
def test_counted_keyset_window_without_seek_count_falls_back():
    issue_type = _make_issue_type("KeysetCountDriftNode")
    state = _issue_state(issue_type)
    connection_type = _issue_connection_of(issue_type)
    row = Issue(id=1, number=1)
    # The window columns arrive as annotations: attributes Django sets on each row it builds.
    vars(row).update({WINDOW_ROW_NUMBER: 1, WINDOW_TOTAL_COUNT: 3})
    info = make_info(field_name="issues", selections="{ pageInfo { hasNextPage } }")
    window = _WindowedConnectionRows(rows=[row], fallback=Issue.objects.all)
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
    state = _issue_state(issue_type)
    assert state is not None
    return state


def _state_stub(model: type[Model], cursor_field: tuple[str, ...]) -> CursorState:
    """A hand-built declared state over a directly built definition of ``model``."""
    from tests._definition import make_definition

    return CursorState(
        definition=make_definition(model, cursor_field=cursor_field),
        cursor_field=cursor_field,
        columns=cursor_columns_for(model, cursor_field),
        fingerprint=order_fingerprint(cursor_field),
    )


@pytest.mark.django_db
def test_keyset_order_state_default_order_reuses_declared_columns():
    state = _issue_order_state()
    columns, fingerprint, _queryset = _keyset_order_state(
        state,
        Issue.objects.order_by(*ISSUE_ORDER),
    )
    assert state is not None
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
    state_stub = _state_stub(Book, ("title", "id"))
    with pytest.raises(GraphQLError, match="'subtitle' is nullable"):
        _keyset_order_state(state_stub, Book.objects.order_by("subtitle", "id"))


@pytest.mark.django_db
def test_keyset_order_state_rejects_json_columns():
    state_stub = _state_stub(ScalarSpecimen, ("label",))
    with pytest.raises(GraphQLError, match="ordering differs between database backends"):
        _keyset_order_state(
            state_stub,
            ScalarSpecimen.objects.order_by("payload", "id"),
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "order",
    [("card__barcode", "id"), ("loans__note", "id")],
    ids=["optional-o2o", "multivalued-reverse"],
)
def test_keyset_order_state_rejects_optional_or_multivalued_related_paths(order: tuple[str, str]):
    state_stub = _state_stub(Patron, ("name",))
    with pytest.raises(GraphQLError, match="cannot anchor stable cursors"):
        _keyset_order_state(state_stub, Patron.objects.order_by(*order))


@pytest.mark.django_db
@pytest.mark.parametrize("spelling", ["flat", "nested"])
@pytest.mark.parametrize("hides", [True, False], ids=["hiding-target", "identity-target"])
def test_keyset_order_state_rejects_a_related_value_read_through_a_hiding_type(
    hides: bool,
    spelling: str,
):
    """A related ``orderBy:`` value through a type that hides rows is nullable, so refused.

    ``OrderSet`` reads ``periodical__name`` as ``NULL`` for a periodical the
    periodical type hides; a value cursor cannot anchor that. Through a type
    keeping the identity hook the path stays the plain non-null column.
    """
    attrs: dict[str, object] = {
        "Meta": type("Meta", (), {"model": Periodical, "fields": "__all__"}),
    }
    if hides:

        def _hide_secret(
            _cls: type[DjangoType],
            queryset: QuerySet[Periodical],
            _info: object,
            **_kwargs: object,
        ) -> QuerySet[Periodical]:
            return queryset.exclude(name="secret")

        attrs["get_queryset"] = classmethod(_hide_secret)
    type("KeysetPeriodicalNode", (DjangoType,), attrs)
    state = _issue_order_state()

    class PeriodicalNameOrder(OrderSet):
        class Meta:
            model = Periodical
            fields = ["name"]

    class IssuePeriodicalOrder(OrderSet):
        periodical = RelatedOrder(PeriodicalNameOrder, field_name="periodical")

        class Meta:
            model = Issue
            fields = ["number", "periodical__name"]

    periodical_term = (
        {"periodical_name": Ordering.ASC}
        if spelling == "flat"
        else {"periodical": {"name": Ordering.ASC}}
    )

    request = HttpRequest()
    request.user = AnonymousUser()
    ordered = IssuePeriodicalOrder.apply_sync(
        [periodical_term, {"number": Ordering.DESC}],
        Issue.objects.all(),
        SimpleNamespace(context=SimpleNamespace(request=request)),
    )
    if hides:
        with pytest.raises(GraphQLError, match="'periodical__name' is nullable"):
            _keyset_order_state(state, ordered)
    else:
        columns, _fingerprint, _queryset = _keyset_order_state(state, ordered)
        assert [column.name for column in columns] == ["periodical__name", "number"]


@pytest.mark.django_db(transaction=True)
def test_keyset_pages_a_foreign_object_term_by_seeking_over_its_carriers():
    """A ``ForeignObject`` ``orderBy:`` term pages by value cursors over each carrier column.

    ``LnkPairChild.parent`` is held in ``p_tenant`` and ``p_code``, so the term
    is two non-null columns and the cursor seeks over both, then the
    ``cursor_field`` pk tiebreaker. The live ``ShelfLabel.shelf`` cannot carry
    this row: one of its carriers is the ``branch`` key, a relation no keyset
    order accepts, and its target ``ShelfType`` hides rows, which makes the
    term nullable. ``z9`` names no parent and sorts first by its carriers,
    although it is inserted last. A cursor minted under the ``parent`` order is
    refused under another order.
    """

    class KeysetPairOrder(OrderSet):
        class Meta:
            model = LnkPairChild
            fields = ["parent", "name"]

    pair_type = make_django_type(
        "KeysetPairNode",
        LnkPairChild,
        ("id", "name"),
        meta_extra={"cursor_field": ("id",), "orderset_class": KeysetPairOrder},
    )
    finalize_django_types()

    @strawberry.type
    class Query:
        children = DjangoConnectionField(pair_type)

    schema = strawberry.Schema(query=Query)

    def page(order: str, after: str | None = None):
        cursor = "" if after is None else f', after: "{after}"'
        with CaptureQueriesContext(connection) as captured:
            result = schema.execute_sync(
                f"{{ children(first: 2{cursor}, orderBy: [{{{order}: ASC}}]) "
                "{ edges { node { name } } pageInfo { hasNextPage endCursor } } }",
                context_value={"request": RequestFactory().get("/")},
            )
        return result, [entry["sql"] for entry in captured.captured_queries]

    with link_fixture_tables(connection):
        LnkPairChild.objects.create(p_tenant=0, p_code="Z", name="z9")
        first, _sql = page("parent")
        assert first.errors is None, first.errors
        assert first.data is not None
        first_page = first.data["children"]
        assert [edge["node"]["name"] for edge in first_page["edges"]] == ["z9", "a1"]
        second, second_sql = page("parent", first_page["pageInfo"]["endCursor"])
        replayed, _sql = page("name", first_page["pageInfo"]["endCursor"])

    assert second.errors is None, second.errors
    assert second.data is not None
    assert [edge["node"]["name"] for edge in second.data["children"]["edges"]] == ["a2", "a3"]
    assert second.data["children"]["pageInfo"]["hasNextPage"] is True
    (seek,) = [sql for sql in second_sql if "ORDER BY" in sql]
    where = seek.split(" WHERE ", 1)[1].split(" ORDER BY ", 1)[0]
    assert '"p_tenant"' in where, seek
    assert '"p_code"' in where, seek
    assert replayed.errors is not None
    assert "invalid cursor" in str(replayed.errors[0]), replayed.errors


def test_keyset_order_ref_parses_strings_and_rejects_nulls():
    assert _keyset_order_ref("-number") == ("-number", "number", True)
    assert _keyset_order_ref(F("number").asc()) == ("number", "number", False)
    assert _keyset_order_ref(F("number").desc(nulls_first=True)) is None
    assert _keyset_order_ref(SimpleNamespace(expression=None, descending=False)) is None


def _resolved_name(model: type[Model], path: str) -> str:
    """Resolve ``path`` on ``model`` and return the terminal field's name, failing on ``None``."""
    field = _resolve_order_path_field(model, path)
    assert field is not None
    return field.name


def test_resolve_order_path_field_arms(monkeypatch: pytest.MonkeyPatch):
    # Local column; pk alias; related path terminal.
    assert _resolved_name(Issue, "number") == "number"
    assert _resolved_name(Issue, "pk") == "id"
    assert _resolved_name(Issue, "periodical__name") == "name"
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

    def _detached_relation(_name: str) -> object:
        return detached_relation

    monkeypatch.setattr(Issue._meta, "get_field", _detached_relation)
    assert _resolve_order_path_field(Issue, "relation__value") is None

    virtual_field = SimpleNamespace(
        is_relation=False,
        concrete=False,
        related_model=None,
    )

    def _virtual_field(_name: str) -> object:
        return virtual_field

    monkeypatch.setattr(Issue._meta, "get_field", _virtual_field)
    assert _resolve_order_path_field(Issue, "virtual") is None


def test_resolve_order_path_field_accepts_mti_parent_link():
    """A concrete auto-created parent link is a safe non-null forward hop."""
    parent_link = LendingDesk._meta.pk
    assert parent_link.name == "venue_ptr"

    assert _resolved_name(LendingDesk, "venue_ptr__name") == "name"


# =============================================================================
# nested-planner helpers
# =============================================================================


@pytest.mark.django_db
def test_keyset_window_slice_from_arguments_arms():
    issue_type = _make_issue_type("KeysetWalkerSliceNode")
    finalize_django_types()
    state = declared_cursor_state_for_definition(issue_type.__django_strawberry_definition__)
    assert state is not None
    columns, fingerprint = state.columns, state.fingerprint
    info = make_info(config=StrawberryConfig(relay_max_results=100))._raw_info

    # No cursor: a plain forward window, no seek.
    sliced = _keyset_window_slice_from_arguments(
        {"first": 2},
        info,
        columns=columns,
        fingerprint=fingerprint,
    )
    assert sliced is not None
    window, seek = sliced
    assert (window.offset, window.limit, window.reverse) == (0, 2, False)
    assert seek is None

    # A valid minted cursor decodes into the seek.
    periodical = Periodical.objects.create(name="P")
    issue = Issue.objects.create(periodical=periodical, number=1, title="one")
    from django_strawberry_framework.keyset import encode_keyset_cursor

    cursor = encode_keyset_cursor(columns, issue, fingerprint=fingerprint)
    sliced = _keyset_window_slice_from_arguments(
        {"first": 2, "after": cursor},
        info,
        columns=columns,
        fingerprint=fingerprint,
    )
    assert sliced is not None
    window, seek = sliced
    assert (window.offset, window.limit, window.reverse) == (0, 2, False)
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
def test_extend_only_projection_passthrough_arms():
    """Identity / no-op arms of ``_extend_only_projection`` have no wire shape.

    Restoring a deferred or ``only()``-masked cursor column is live:
    ``test_nested_keyset_unselected_cursor_column_is_not_lazy_loaded_per_edge``
    (optimizer ``only()``) and
    ``test_async_keyset_deferred_cursor_column_is_loaded`` (async ``defer()``).
    """
    sentinel = object()
    # basedpyright: the non-queryset sentinel is the input under test (passed through
    # untouched); _extend_only_projection types the parameter as QuerySet
    assert _extend_only_projection(sentinel, ("number",)) is sentinel  # pyright: ignore[reportArgumentType]

    plain = Issue.objects.all()
    assert _extend_only_projection(plain, ("number",)) is plain
    only_empty = Issue.objects.only()
    assert _extend_only_projection(only_empty, ("number",)) is only_empty
    deferred = Issue.objects.defer("title")
    assert _extend_only_projection(deferred, ("number",)) is deferred
    masked_deferred = Issue.objects.defer("number", "title")
    extended_deferred = _extend_only_projection(masked_deferred, ("number",))
    loading = deferred_loading_of(extended_deferred)
    assert loading is not None
    names, defer_flag = loading
    assert defer_flag is True
    assert names == frozenset({"title"})
    covered = Issue.objects.only("number", "id")
    assert _extend_only_projection(covered, ("number",)) is covered
    only_qs = Issue.objects.only("title")
    extended_only = _extend_only_projection(only_qs, ("number",))
    loading = deferred_loading_of(extended_only)
    assert loading is not None
    names, defer_flag = loading
    assert defer_flag is False
    assert names == frozenset({"number", "title"})
