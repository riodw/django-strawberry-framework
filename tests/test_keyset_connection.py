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
- ``_keyset_order_state`` derivation with hand-built states: column-object
  reuse, and rejection of expression / nulls-positioning / nullable / JSON /
  optional-or-multivalued related orders. ``IssueOrder`` only publishes
  non-null local and required-FK paths, so those error arms are not reachable
  on the shipped schema. Related-path acceptance is live
  (``test_root_keyset_order_by_related_path_seeks_via_annotation``).
- Pure helpers ``_keyset_order_ref`` and ``_resolve_order_path_field``
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
from apps.library.models import Book, Issue, LendingDesk, Patron, Periodical
from apps.scalars.models import ScalarSpecimen
from django.db.models import Count, F
from graphql import GraphQLError
from strategy_schemas import make_django_type

from django_strawberry_framework import finalize_django_types
from django_strawberry_framework.connection import (
    _connection_type_for,
    _keyset_connection_context,
    _keyset_order_ref,
    _keyset_order_state,
    _resolve_from_window,
    _resolve_order_path_field,
    _WindowedConnectionRows,
)
from django_strawberry_framework.keyset import (
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
    deferred_loading_of,
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
    return _keyset_connection_context(
        _connection_type_for(issue_type, issue_type.__django_strawberry_definition__),
    )


# =============================================================================
# keyset-mode resolution + class cache
# =============================================================================


def test_keyset_connection_context_resolves_and_caches():
    issue_type = _make_issue_type()
    finalize_django_types()
    connection_type = _connection_type_for(issue_type, issue_type.__django_strawberry_definition__)
    state = _keyset_connection_context(connection_type)
    assert state is not None
    assert state.cursor_field == ISSUE_ORDER
    assert state.fingerprint == order_fingerprint(ISSUE_ORDER)
    # Second read serves the class-cached state object.
    assert _keyset_connection_context(connection_type) is state


def test_keyset_connection_context_is_none_for_offset_types():
    plain_type = make_django_type("PlainIssueNode", Issue, ("id", "number"))
    finalize_django_types()
    connection_type = _connection_type_for(plain_type, plain_type.__django_strawberry_definition__)
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
    connection_type = _connection_type_for(issue_type, issue_type.__django_strawberry_definition__)
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
    connection_type = _connection_type_for(issue_type, issue_type.__django_strawberry_definition__)
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
    connection_type = _connection_type_for(issue_type, issue_type.__django_strawberry_definition__)
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
@pytest.mark.parametrize(
    "order",
    [("card__barcode", "id"), ("loans__note", "id")],
    ids=["optional-o2o", "multivalued-reverse"],
)
def test_keyset_order_state_rejects_optional_or_multivalued_related_paths(order):
    state_stub = SimpleNamespace(
        definition=SimpleNamespace(model=Patron),
        cursor_field=("name",),
        columns=cursor_columns_for(Patron, ("name",)),
        fingerprint=order_fingerprint(("name",)),
    )
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


def test_resolve_order_path_field_accepts_mti_parent_link():
    """A concrete auto-created parent link is a safe non-null forward hop."""
    parent_link = LendingDesk._meta.pk
    assert parent_link.name == "venue_ptr"

    assert _resolve_order_path_field(LendingDesk, "venue_ptr__name").name == "name"


# =============================================================================
# nested-planner helpers
# =============================================================================


class _FakeInfo:
    schema = SimpleNamespace(config=SimpleNamespace(relay_max_results=100))


@pytest.mark.django_db
def test_keyset_window_slice_from_arguments_arms():
    issue_type = _make_issue_type("KeysetWalkerSliceNode")
    finalize_django_types()
    state = declared_cursor_state_for_definition(issue_type.__django_strawberry_definition__)
    assert state is not None
    columns, fingerprint = state.columns, state.fingerprint
    info = _FakeInfo()

    # No cursor: a plain forward window, no seek.
    window, seek = _keyset_window_slice_from_arguments(
        {"first": 2},
        info,
        columns=columns,
        fingerprint=fingerprint,
    )
    assert (window.offset, window.limit, window.reverse) == (0, 2, False)
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
    assert _extend_only_projection(sentinel, ("number",)) is sentinel

    plain = Issue.objects.all()
    assert _extend_only_projection(plain, ("number",)) is plain
    only_empty = Issue.objects.only()
    assert _extend_only_projection(only_empty, ("number",)) is only_empty
    deferred = Issue.objects.defer("title")
    assert _extend_only_projection(deferred, ("number",)) is deferred
    masked_deferred = Issue.objects.defer("number", "title")
    extended_deferred = _extend_only_projection(masked_deferred, ("number",))
    names, defer_flag = deferred_loading_of(extended_deferred)
    assert defer_flag is True
    assert names == frozenset({"title"})
    covered = Issue.objects.only("number", "id")
    assert _extend_only_projection(covered, ("number",)) is covered
    only_qs = Issue.objects.only("title")
    extended_only = _extend_only_projection(only_qs, ("number",))
    names, defer_flag = deferred_loading_of(extended_only)
    assert defer_flag is False
    assert names == frozenset({"number", "title"})
